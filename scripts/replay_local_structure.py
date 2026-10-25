"""Replay a prespecified Experiment 4 subset, including every search outcome.

Usage: python scripts/replay_local_structure.py ARCHIVE --output REPORT.json

Selection never consults outcomes: repeat zero, fit zero for every region/d/N,
synthetic family/N and lexicographic scaling/N; repeat zero for every fit/d/N
fiber search. Every selected raw record and pair/search metadata is compared in
full. Geometric relations and 2+2 counts have independent numerical checks.
This is a reconstruction audit, not additional primary sampling or inference.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from causal_lab.dimension import MinkowskiInterval, sprinkle_minkowski
from causal_lab.local_generators import (lexicographic_matched_pair,
    microcanonical_switch_search, sprinkle_central_slab)
from causal_lab.local_random import identity, rng_for
from causal_lab.local_structure_study import StudyConfig, _order, _record


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def load(path, lines=False):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()] if lines else json.load(stream)


def differences(actual, expected, path="record"):
    """Retain concrete mismatch locations, bounded to keep failure logs usable."""
    if actual == expected:
        return []
    if isinstance(actual, dict) and isinstance(expected, dict):
        result = []
        for key in sorted(set(actual) | set(expected)):
            if key not in actual or key not in expected:
                result.append({"path": f"{path}.{key}", "reason": "missing field",
                               "actual_present": key in actual, "expected_present": key in expected})
            else:
                result.extend(differences(actual[key], expected[key], f"{path}.{key}"))
            if len(result) >= 20:
                return result[:20]
        return result
    if isinstance(actual, list) and isinstance(expected, list) and len(actual) == len(expected):
        result = []
        for index, (a, b) in enumerate(zip(actual, expected)):
            result.extend(differences(a, b, f"{path}[{index}]"))
            if len(result) >= 20:
                return result[:20]
        return result
    return [{"path": path, "actual": actual, "expected": expected}]


def independent_geometry(interval):
    """Strict causality using squared separations, without norm/minkowski_order."""
    n = len(interval.t)
    result = np.zeros((n, n), dtype=bool)
    for a in range(n):
        for b in range(a + 1, n):
            dt = float(interval.t[b]) - float(interval.t[a])
            squared_distance = sum((float(interval.x[b, axis]) - float(interval.x[a, axis]))**2
                                   for axis in range(interval.dimension - 1))
            if dt * dt > squared_distance:
                if dt > 0:
                    result[a, b] = True
                elif dt < 0:
                    result[b, a] = True
    return result


def independent_n22(order):
    """Dual maxima-pair identity via integer matrices, not extractor bitsets."""
    integer = np.asarray(order, dtype=np.int64)
    common_past = integer.T @ integer
    past_degree = integer.sum(axis=0)
    exclusive_past = past_degree[None, :] - common_past
    incomparable = ~(np.asarray(order, dtype=bool) | np.asarray(order, dtype=bool).T
                     | np.eye(len(order), dtype=bool))
    return int(np.triu(exclusive_past * exclusive_past.T * incomparable, k=1).sum(dtype=np.int64))


def geometric_order(config, fit, family, dimension, count, *, donor=False):
    stream_family = "fiber_donor" if donor else family
    rng = rng_for(config.seed, fit, "final", stream_family, dimension, count, 0)
    if family == "diamond":
        coordinates = sprinkle_minkowski(dimension, 1., rng, count=count)
    elif family == "slab":
        coordinates = sprinkle_central_slab(count, rng, dimension)
    elif family == "box":
        coordinates = MinkowskiInterval(rng.random(count), rng.random((count, dimension - 1)) - .5,
                                        dimension, 1.)
    else:
        raise ValueError("not a geometric family")
    independent = independent_geometry(coordinates)
    standard = _order(family, count, dimension,
                      rng_for(config.seed, fit, "final", stream_family, dimension, count, 0))
    if not np.array_equal(independent, standard):
        raise ValueError(f"independent coordinate relation mismatch: {np.count_nonzero(independent != standard)} entries")
    return independent


def changed(first, second):
    fields = ("n22", "chains4", "overlap_sum", "overlap_choose2_sum", "interval_component_profile",
              "interval_m4_motif_counts", "interval_m8_joint")
    return any(first[name] != second[name] for name in fields)


def run_replay(directory):
    metadata = load(directory / "metadata.json")
    values = dict(metadata["config"])
    values["counts"], values["dimensions"] = tuple(values["counts"]), tuple(values["dimensions"])
    config = StudyConfig(**values).validate()
    raw = load(directory / "raw_orders.jsonl.gz", lines=True)
    pair_records = load(directory / "pairs.jsonl.gz", lines=True)
    search_records = load(directory / "searches.jsonl.gz", lines=True)
    by_sample = {row["sample_id"]: row for row in raw}
    by_pair = {row["pair_id"]: row for row in pair_records}
    by_search = {row["search_id"]: row for row in search_records}
    cases, rebuilt, selected_ids = [], [], []
    geometry_checks = 0
    root = Path(__file__).resolve().parents[1]
    source_mismatches = []
    for name, expected_hash in metadata["source_hashes"].items():
        if not name.startswith("src/"):
            continue
        path = root / name
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        if actual_hash != expected_hash:
            source_mismatches.append({"path": name, "actual": actual_hash, "expected": expected_hash})
    cases.append({"kind": "source", "id": "frozen_source_modules",
                  "status": "passed" if not source_mismatches else "failed", "differences": source_mismatches})

    def compare(kind, key, actual, expected):
        mismatch = differences(actual, expected)
        cases.append({"kind": kind, "id": key,
                      "status": "failed" if mismatch else "passed", "differences": mismatch})

    def record(order, fit, family, dimension, count, **extra):
        row = _record(order, config, fit, family, dimension, count, 0, **extra)
        sample_id = row["sample_id"]
        selected_ids.append(sample_id)
        rebuilt.append(row)
        compare("raw_record", sample_id, row, by_sample[sample_id])
        compare("independent_n22", sample_id, independent_n22(order), by_sample[sample_id]["n22"])
        return row

    def safe(kind, key, operation):
        try:
            operation()
        except Exception as error:
            cases.append({"kind": kind, "id": key, "status": "failed",
                          "differences": [{"reason": type(error).__name__, "message": str(error)}]})

    for count in config.counts:
        for dimension in config.dimensions:
            for family in ("diamond", "slab", "box"):
                key = f"fit0/{family}/d{dimension}/N{count}/repeat0"
                def region(family=family, dimension=dimension, count=count):
                    nonlocal geometry_checks
                    order = geometric_order(config, 0, family, dimension, count)
                    geometry_checks += 1
                    record(order, 0, family, dimension, count)
                safe("geometric_generation", key, region)
        for family, dimension in (("rank2", 2), ("rank3", 0), ("interval", 0)):
            def synthetic(family=family, dimension=dimension, count=count):
                order = _order(family, count, dimension,
                               rng_for(config.seed, 0, "final", family, dimension, count, 0))
                record(order, 0, family, dimension, count)
            safe("synthetic_generation", f"fit0/{family}/N{count}/repeat0", synthetic)
        for scaling in ("fixed", "inflated"):
            def exact_pair(scaling=scaling, count=count):
                family = "lex_" + scaling
                pair_id = identity(config.seed, 0, "final", family, 0, count, 0)
                pair = lexicographic_matched_pair(count, rng_for(config.seed, 0, "final", family, 0, count, 0),
                                                  scaling=scaling)
                first = record(pair.first_order, 0, family + "_connected", 0, count,
                               pair_id=pair_id, member="first")
                second = record(pair.second_order, 0, family + "_split", 0, count,
                                pair_id=pair_id, member="second")
                actual = dict(pair_id=pair_id, fit=0, repeat=0, first_sample_id=first["sample_id"],
                              second_sample_id=second["sample_id"], **pair.metadata)
                compare("exact_pair_metadata", pair_id, actual, by_pair[pair_id])
            safe("exact_pair_generation", f"fit0/lex_{scaling}/N{count}/repeat0", exact_pair)

    selected_search_outcomes = Counter()
    for fit in range(config.fits):
        for dimension in config.dimensions:
            for count in config.counts:
                def fiber(fit=fit, dimension=dimension, count=count):
                    nonlocal geometry_checks
                    search_id = identity(config.seed, fit, "search", "fiber", dimension, count, 0)
                    donor = geometric_order(config, fit, "diamond", dimension, count, donor=True)
                    geometry_checks += 1
                    result = microcanonical_switch_search(donor,
                        rng_for(config.seed, fit, "search", "fiber", dimension, count, 0))
                    checkpoints = []
                    for name, order in zip(("initial", "midpoint", "final"),
                                           (result.initial_order, result.midpoint_order, result.final_order)):
                        checkpoints.append(record(order, fit, "fiber_" + name, dimension, count,
                                                  search_id=search_id, checkpoint=name))
                    actual = dict(search_id=search_id, fit=fit, dimension=dimension, repeat=0,
                                  midpoint_local_changed=changed(checkpoints[0], checkpoints[1]),
                                  final_local_changed=changed(checkpoints[0], checkpoints[2]), **result.metadata)
                    compare("fiber_metadata", search_id, actual, by_search[search_id])
                    selected_search_outcomes.update(result.metadata["outcomes"])
                safe("fiber_replay", f"fit{fit}/d{dimension}/N{count}/repeat0", fiber)

    expected_records = len(config.counts) * (3 * len(config.dimensions) + 3 + 4
                                           + 3 * config.fits * len(config.dimensions))
    compare("coverage", "prespecified_raw_record_count", len(rebuilt), expected_records)
    compare("coverage", "unique_selected_records", len(set(selected_ids)), expected_records)
    regenerated_digest = hashlib.sha256()
    stored_digest = hashlib.sha256()
    for row in sorted(rebuilt, key=lambda row: row["sample_id"]):
        regenerated_digest.update(canonical(row) + b"\n")
        stored_digest.update(canonical(by_sample[row["sample_id"]]) + b"\n")
    compare("digest", "selected_raw_records", regenerated_digest.hexdigest(), stored_digest.hexdigest())
    failures = [case for case in cases if case["status"] == "failed"]
    return {"status": "failed" if failures else "passed", "seed": config.seed,
            "selection": "repeat0; fit0 all region/d/N, synthetic/N and exact-pair scaling/N; all fits/d/N fiber searches",
            "selected_raw_records": len(rebuilt), "expected_raw_records": expected_records,
            "independent_geometry_checks": geometry_checks,
            "independent_dual_n22_checks": sum(case["kind"] == "independent_n22" for case in cases),
            "fiber_searches_replayed": config.fits * len(config.dimensions) * len(config.counts),
            "selected_search_outcomes": dict(selected_search_outcomes),
            "selected_raw_sha256": regenerated_digest.hexdigest(),
            "stored_selected_raw_sha256": stored_digest.hexdigest(),
            "failure_count": len(failures), "failures": failures, "cases": cases,
            "bootstrap_intervals_recomputed": False,
            "all_selected_searches_retained_regardless_of_outcome": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_replay(args.directory)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n",
                               encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"},
                     sort_keys=True, indent=2, allow_nan=False))
    raise SystemExit(0 if report["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
