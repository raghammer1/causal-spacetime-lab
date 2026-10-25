"""Bounded archive audit with independent reconstruction and counting methods.

All files are hashed; expensive reconstruction uses the fixed, outcome-blind
selection batch=0/history_number=0 in every family, including the endpoints.
This audit does not independently recompute bootstrap confidence intervals.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

from .growth_controls import generate_history
from .growth_observables import growth_observables
from .local_structure import motif_counts


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _constant(value):
    raise ValueError(f"nonfinite JSON constant: {value}")


def _load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as stream:
        result = json.load(stream, parse_constant=_constant)
    _canonical(result)  # Also reject exponent overflow parsed as an infinity.
    return result


def _rows(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line, parse_constant=_constant)
                _canonical(row)
                yield row


def _path(directory, name):
    name = Path(name)
    if name.is_absolute() or ".." in name.parts:
        raise ValueError("archive paths must stay within the archive")
    path = directory / name
    if not path.is_file() or not path.resolve().is_relative_to(directory.resolve()):
        raise ValueError(f"missing or external artifact: {name}")
    return path


def _file_hash(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _order_hash(order):
    return hashlib.sha256(np.asarray(order, dtype=np.uint8).tobytes()).hexdigest()


def unpack_order(packed):
    """Decode and validate a canonical flattened little-bit-order square matrix."""
    shape = packed["shape"]
    if (not isinstance(shape, list) or len(shape) != 2
            or any(type(n) is not int or not 0 <= n <= 512 for n in shape)
            or shape[0] != shape[1] or packed.get("bitorder", "little") != "little"):
        raise ValueError("invalid packed matrix shape or bit order")
    binary = bytes.fromhex(packed["packed_hex"])
    size = shape[0] * shape[1]
    if len(binary) != (size + 7) // 8:
        raise ValueError("packed matrix byte length does not match shape")
    bits = np.unpackbits(np.frombuffer(binary, dtype=np.uint8), bitorder="little")
    if np.any(bits[size:]):
        raise ValueError("nonzero packed-matrix padding")
    return bits[:size].reshape(shape).astype(bool)


def independent_closure(edges):
    """Boolean Floyd–Warshall, independent of the generator's ancestor bitsets."""
    matrix = np.asarray(edges, dtype=bool).copy()
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("relation must be square")
    for middle in range(len(matrix)):
        matrix |= matrix[:, middle, None] & matrix[None, middle, :]
    if np.any(np.diag(matrix)):
        raise ValueError("cyclic relation")
    return matrix


def reconstruct_history(record):
    """Recover a selected history from explicit primitive/reference evidence."""
    n, family = record["count"], record["family"]
    if type(n) is not int or not 0 <= n <= 512:
        raise ValueError("invalid history count")
    if family == "percolation":
        edges = unpack_order(record["primitive_edges"])
        if edges.shape != (n, n) or np.any(np.tril(edges)):
            raise ValueError("primitive growth edges must point forward in birth order")
        matrix = independent_closure(edges)
        metadata = record["metadata"]
        if (metadata["selected_parent_counts"] != edges.sum(axis=0).astype(int).tolist()
                or metadata["primitive_edge_count"] != int(edges.sum())
                or metadata["relation_count"] != int(matrix.sum())
                or metadata["count"] != n or metadata["probability"] != record["parameter"]):
            raise ValueError("primitive growth metadata mismatch")
    elif family == "minkowski":
        coordinates = record["coordinates"]
        t = np.asarray(coordinates["t"], dtype=float)
        x = np.asarray(coordinates["x"], dtype=float)
        d = coordinates["dimension"]
        if (d not in (2, 3, 4) or d != record["parameter"] or t.shape != (n,)
                or x.shape != (n, d - 1) or not np.all(np.isfinite(t))
                or not np.all(np.isfinite(x))):
            raise ValueError("invalid archived Minkowski coordinates")
        duration = coordinates["duration"]
        if duration != 1 or np.any(t < 0) or np.any(t > duration):
            raise ValueError("reference points outside unit diamond time range")
        if np.any(np.linalg.norm(x, axis=1) > np.minimum(t, duration - t) + 1e-13):
            raise ValueError("reference points outside unit diamond")
        dt = t[None, :] - t[:, None]
        distance2 = np.sum((x[None, :, :] - x[:, None, :]) ** 2, axis=2)
        matrix = (dt > 0) & (dt ** 2 > distance2)
    elif family == "semiorder":
        u = np.asarray(record["utilities"], dtype=float)
        if u.shape != (n,) or not np.all(np.isfinite(u)) or np.any((u < 0) | (u > 1)):
            raise ValueError("invalid archived semiorder utilities")
        matrix = u[None, :] - u[:, None] > record["parameter"]
    elif family == "matched_bipartite":
        layers = np.asarray(record["layers"])
        matrix = unpack_order(record["cross_edges"])
        if (layers.shape != (n,) or np.any((layers != 0) & (layers != 1))
                or matrix.shape != (n, n)
                or np.any(matrix & ~((layers[:, None] == 0) & (layers[None, :] == 1)))):
            raise ValueError("invalid height-two layer relation")
    else:
        raise ValueError(f"unknown reconstruction family: {family}")
    if not np.array_equal(independent_closure(matrix), matrix):
        raise ValueError("reconstructed matrix is not transitively closed")
    if _order_hash(matrix) != record["order_sha256"]:
        raise ValueError("reconstructed history hash mismatch")
    return matrix


def independent_counts(order):
    """Exact n22 via incomparable maxima, n31 via each possible isolated event.

    The production n22 algorithm uses minima; here the two exclusive pasts of
    incomparable maxima determine the two lower events. For n31, restrict to
    the isolated vertex's incomparable neighborhood and sum P(x)*F(x) there.
    """
    matrix = np.asarray(order, dtype=bool)
    n = len(matrix)
    # Build integer sets independently, without the production packbits helper.
    future = [sum(1 << int(c) for c in np.flatnonzero(matrix[a])) for a in range(n)]
    past = [sum(1 << int(a) for a in np.flatnonzero(matrix[:, c])) for c in range(n)]
    count22 = 0
    for b in range(n):
        for d in range(b + 1, n):
            if not (matrix[b, d] or matrix[d, b]):
                count22 += (past[b] & ~past[d]).bit_count() * (past[d] & ~past[b]).bit_count()
    count31 = 0
    for isolated in range(n):
        incomparable = ((1 << n) - 1) ^ (future[isolated] | past[isolated] | (1 << isolated))
        pending = incomparable
        while pending:
            bit = pending & -pending
            middle = bit.bit_length() - 1
            count31 += (past[middle] & incomparable).bit_count() * (future[middle] & incomparable).bit_count()
            pending ^= bit
    indegree = matrix.sum(axis=0).astype(int)
    heights = np.ones(n, dtype=int)
    pending = list(np.flatnonzero(indegree == 0))
    visited = 0
    while pending:
        a = int(pending.pop())
        visited += 1
        successors = np.flatnonzero(matrix[a])
        heights[successors] = np.maximum(heights[successors], heights[a] + 1)
        indegree[successors] -= 1
        pending.extend(successors[indegree[successors] == 0])
    if visited != n:
        raise ValueError("cycle found by independent height traversal")
    return {"n22": count22, "n31": count31, "relations": int(matrix.sum()),
            "longest_chain": int(heights.max()) if n else 0}


def _four_subset_checks(order):
    n = len(order)
    if n < 4:
        return 0
    if n <= 12:
        subsets = list(itertools.combinations(range(n), 4))
    else:
        rng = np.random.default_rng(240510)  # Fixed before inspecting any outcomes.
        subsets = [rng.choice(n, size=4, replace=False) for _ in range(32)]
    for subset in subsets:
        small = order[np.ix_(subset, subset)]
        degrees = sorted((small.sum(axis=0) + small.sum(axis=1)).tolist())
        count = independent_counts(small)
        brute22 = int(small.sum() == 2 and degrees == [1, 1, 1, 1])
        brute31 = int(small.sum() == 3 and degrees == [0, 2, 2, 2])
        if count["n22"] != brute22 or count["n31"] != brute31:
            raise ValueError("independent counting formula disagrees with four-subset classification")
    return len(subsets)


def _rng_identity(seed, record, phase, source=None, replica=None):
    # Rebuild the stable identity independently of growth_random.rng_for.
    return json.dumps(["growth-v1", seed, record["batch"], phase, record["family"],
                       record["parameter"], record["history_number"], source, replica],
                      ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _regeneration_rng(seed, record, phase="generation", source=None, replica=None):
    key = _rng_identity(seed, record, phase, source, replica)
    integer = int.from_bytes(hashlib.sha256(key.encode("ascii")).digest(), "big")
    return np.random.Generator(np.random.PCG64(integer))


def _scientific_digest(directory, raw_files):
    digest = hashlib.sha256()
    for label, name in (("summaries", "summary.json"), ("primary", "primary.json"),
                        ("references", "references.json.gz")):
        digest.update(label.encode("ascii") + b"\n" + _canonical(_load(_path(directory, name))) + b"\n")
    digest.update(b"histories\n")
    for row in _rows(_path(directory, "histories.jsonl.gz")):
        digest.update(_canonical(row) + b"\n")
    for name in sorted(raw_files):
        path = _path(directory, name)
        digest.update(b"raw:" + name.encode("utf-8") + b"\n")
        digest.update(str(path.stat().st_size).encode("ascii") + b"\n")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\n")
    return digest.hexdigest()


def audit_growth_archive(directory, *, verify_regeneration=True):
    """Return a machine-readable report; retain all discovered audit failures."""
    directory = Path(directory)
    report = {"status": "failed", "selection": "batch0/history_number0 in every available family, including endpoints",
              "bootstrap_intervals_recomputed": False, "failures": [], "artifact_files": 0,
              "history_records": 0, "raw_records": 0, "selected_histories": 0,
              "selected_raw_records": 0, "regenerated_histories": 0,
              "regenerated_thinnings": 0, "regenerated_motif_samples": 0,
              "independent_count_checks": 0, "four_subsets_checked": 0}
    failures = report["failures"]
    try:
        manifest = _load(_path(directory, "manifest.json"))
        metadata = _load(_path(directory, "metadata.json"))
        artifact_names = set()
        for artifact in manifest["artifacts"]:
            name = artifact["name"]
            if name in artifact_names:
                failures.append(f"duplicate manifest artifact: {name}")
            artifact_names.add(name)
            path = _path(directory, name)
            digest = _file_hash(path)
            if digest != artifact["sha256"] or path.stat().st_size != artifact["bytes"]:
                failures.append(f"artifact checksum/size mismatch: {name}")
            if name in metadata.get("artifact_sha256", {}) and digest != metadata["artifact_sha256"][name]:
                failures.append(f"metadata artifact checksum mismatch: {name}")
            report["artifact_files"] += 1
        if artifact_names != set(metadata.get("artifact_sha256", {})) | {"metadata.json"}:
            failures.append("manifest inventory differs from metadata artifact inventory")
        raw_files = metadata["raw_files"]
        if len(raw_files) != len(set(raw_files)):
            failures.append("duplicate raw files")
        discovered = sorted(path.relative_to(directory).as_posix() for path in (directory / "raw").glob("*.jsonl.gz"))
        if discovered != sorted(raw_files):
            failures.append("raw shard inventory differs from metadata")
        if any(name not in artifact_names for name in raw_files):
            failures.append("raw shard missing from manifest")
        digest = _scientific_digest(directory, raw_files)
        report["scientific_sha256"] = digest
        if digest != manifest["scientific_sha256"] or digest != metadata["scientific_sha256"]:
            failures.append("independent scientific digest mismatch")
        histories, selected = {}, {}
        config = metadata.get("config", {})
        seed = config.get("seed", metadata.get("seed"))
        phase = "smoke" if metadata.get("run_kind") == "smoke" else "primary"
        generation_phase = "smoke_generation" if phase == "smoke" else "generation"
        registered_grid = all(name in config for name in ("probabilities", "batches", "histories"))
        history_grid = set()
        for record in _rows(_path(directory, "histories.jsonl.gz")):
            key = record["history_id"]
            if key in histories:
                failures.append(f"duplicate history_id: {key}")
            histories[key] = {name: record[name] for name in ("family", "parameter", "batch", "history_number", "count")}
            history_grid.add((record["family"], record["parameter"], record["batch"], record["history_number"]))
            if registered_grid and (record["count"] != 512 or key != _rng_identity(seed, record, generation_phase)):
                failures.append(f"history count or seed identity mismatch: {key}")
            report["history_records"] += 1
            if record["batch"] == 0 and record["history_number"] == 0:
                try:
                    order = reconstruct_history(record)
                    if verify_regeneration:
                        if seed is None:
                            raise ValueError("seed missing for requested regeneration")
                        generated, evidence = generate_history(record["family"], record["parameter"],
                                                               record["count"], _regeneration_rng(seed, record, generation_phase))
                        if not np.array_equal(generated, order):
                            raise ValueError("same-seed history regeneration mismatch")
                        for name, value in evidence.items():
                            if value != record[name]:
                                raise ValueError(f"same-seed reconstruction evidence mismatch: {name}")
                        report["regenerated_histories"] += 1
                    selected[key] = order
                    report["selected_histories"] += 1
                except (ValueError, KeyError, TypeError, OverflowError) as error:
                    failures.append(f"history {key}: {error}")
        if metadata.get("history_records") != report["history_records"]:
            failures.append("history record count differs from metadata")
        if registered_grid:
            matched_p = (1 - math.sqrt(1 - 4 / (3 * math.sqrt(2)))) / 2
            families = ([("percolation", p) for p in config["probabilities"]]
                        + [("minkowski", d) for d in (2, 3, 4)]
                        + [("semiorder", .25), ("matched_bipartite", matched_p)])
            expected_grid = {(family, parameter, batch, number) for family, parameter in families
                             for batch in range(config["batches"]) for number in range(config["histories"])}
            expected_grid |= {("percolation", p, 0, 0) for p in (0., 1.)}
            if history_grid != expected_grid:
                failures.append("history grid differs from configured families/batches/history numbers")
        sample_ids, observed_history_counts, observed_grids = set(), Counter(), {}
        for name in raw_files:
            for row in _rows(_path(directory, name)):
                report["raw_records"] += 1
                sample_id, key = row["sample_id"], row["history_id"]
                if sample_id in sample_ids:
                    failures.append(f"duplicate sample_id: {sample_id}")
                sample_ids.add(sample_id)
                observed_history_counts[key] += 1
                grid_key = (row["stage"], row["source_count"], row["count"], row["thinning_rep"])
                observed_grids.setdefault(key, set()).add(grid_key)
                if key not in histories:
                    failures.append(f"raw row references missing history: {sample_id}")
                    continue
                if any(row[field] != histories[key][field]
                       for field in ("family", "parameter", "batch", "history_number")):
                    failures.append(f"raw history identity mismatch: {sample_id}")
                if registered_grid:
                    replica = "prefix" if row["stage"] == "prefix" else row["thinning_rep"]
                    expected_id = _rng_identity(seed, row, phase + "_record", row["source_count"], replica)
                    if sample_id != expected_id or row["fit"] != row["batch"]:
                        failures.append(f"raw sample seed identity mismatch: {sample_id}")
                if key not in selected:
                    continue
                try:
                    parent = selected[key]
                    n, source = row["count"], row["source_count"]
                    if not (type(n) is int and type(source) is int and 0 <= n <= source <= len(parent)):
                        raise ValueError("invalid raw source/count")
                    if row["stage"] == "prefix":
                        if n != source or row["thinning_rep"] is not None:
                            raise ValueError("invalid prefix identity")
                        order = parent[:n, :n]
                    elif row["stage"] == "thinned":
                        indices = row["retained_indices"]
                        if (len(indices) != n or any(type(i) is not int or not 0 <= i < source for i in indices)
                                or indices != sorted(set(indices))):
                            raise ValueError("invalid retained indices")
                        order = parent[np.ix_(indices, indices)]
                        if verify_regeneration:
                            rng = _regeneration_rng(seed, row, phase + "_thinning", source, row["thinning_rep"])
                            repeated = sorted(rng.choice(source, size=n, replace=False).tolist())
                            if repeated != indices:
                                raise ValueError("same-seed thinning indices mismatch")
                            report["regenerated_thinnings"] += 1
                    else:
                        raise ValueError("unknown raw stage")
                    if _order_hash(order) != row["order_sha256"]:
                        raise ValueError("prefix/thinning matrix hash mismatch")
                    counts = independent_counts(order)
                    if any(row[field] != value for field, value in counts.items()):
                        raise ValueError("independent n22/n31/relation/height mismatch")
                    measured = growth_observables(order)
                    if any(row[field] != value for field, value in measured.items()):
                        raise ValueError("recomputed local observable mismatch")
                    if "r" in row and row["r"] != measured["ordering_fraction"]:
                        raise ValueError("ordering fraction alias mismatch")
                    if verify_regeneration and "motifs" in row and "motif_draws" in config:
                        replica = "prefix" if row["stage"] == "prefix" else row["thinning_rep"]
                        motifs = motif_counts(order, _regeneration_rng(seed, row, phase + "_motifs", source, replica),
                                              draws=config["motif_draws"])
                        if motifs != row["motifs"]:
                            raise ValueError("same-seed global motif samples mismatch")
                        report["regenerated_motif_samples"] += 1
                    report["independent_count_checks"] += 1
                    report["four_subsets_checked"] += _four_subset_checks(order)
                    report["selected_raw_records"] += 1
                except (ValueError, KeyError, TypeError, IndexError, OverflowError) as error:
                    failures.append(f"sample {sample_id}: {error}")
        if set(histories) != set(observed_history_counts):
            failures.append("raw/archive history membership mismatch")
        if metadata.get("row_count", report["raw_records"]) != report["raw_records"]:
            failures.append("raw record count differs from metadata")
        if registered_grid:
            expected_rows = {("prefix", n, n, None) for n in (32, 64, 128, 256, 512)}
            expected_rows |= {("thinned", n, n // 2, replica) for n in (128, 256, 512) for replica in range(4)}
            if any(observed_grids[key] != expected_rows or observed_history_counts[key] != 17 for key in histories):
                failures.append("prefix/thinning grid differs from registered 17-row clusters")
        report["records_per_history"] = sorted(set(observed_history_counts.values()))
        if not selected:
            failures.append("fixed selection contains no successfully reconstructed history")
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as error:
        failures.append(f"archive: {error}")
    report["failure_count"] = len(failures)
    report["status"] = "passed" if not failures else "failed"
    return report


def main(argv=None):
    """Audit an existing archive and save the report outside that archive."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="completed growth archive directory")
    parser.add_argument("--output", type=Path, default=Path("results/growth-audit.json"),
                        help="report path outside the archive (default: results/growth-audit.json)")
    arguments = parser.parse_args(argv)
    if arguments.output.resolve().is_relative_to(arguments.directory.resolve()):
        parser.error("audit output must be outside the archived directory to preserve its manifest")
    report = audit_growth_archive(arguments.directory)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
                                encoding="utf-8")
    print(json.dumps({key: report.get(key) for key in
                      ("status", "history_records", "raw_records", "selected_raw_records",
                       "failure_count", "scientific_sha256")}, sort_keys=True, allow_nan=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
