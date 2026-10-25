"""Experiment 3: independent calibration fits and adversarial order holdouts.

See the committed protocol. Inference consumes only extracted order statistics;
generator labels enter training and evaluation, never the detector's test score.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from .adversarial_features import extract_features, feature_vector
from .adversarial_generators import (optimize_order, random_interval_order,
                                     rank_intersection_order, uniform_box_order)
from .adversarial_detectors import (fit_model, score_detectors, summarize_fits,
                                    paired_comparison)
from .dimension import minkowski_order, sprinkle_minkowski, invert_ordering_fraction
from .dimension_study import classify_dimension
from .order_observables import (total_order, antichain, layered_order,
                                random_dag_order, bipartite_order)
from .scaling import _peak_rss_bytes

DETECTORS = tuple("ABCDEF")
TARGETS = (.9, .95, .975)
POSITIVE = {"genuine", "rank_overlap"}
EXACT = {"total", "antichain"}


@dataclass(frozen=True)
class StudyConfig:
    dimensions: tuple[int, ...] = (2, 3, 4)
    counts: tuple[int, ...] = (64, 128, 256)
    fits: int = 3
    calibration: int = 100
    development: int = 100
    validation: int = 200
    repeats: int = 200
    search_steps: int = 64
    bootstrap: int = 2000
    seed: int = 20261025
    workers: int = 1

    def validate(self):
        for name, minimum in (("fits", 1), ("calibration", 2), ("development", 2),
                              ("validation", 2), ("repeats", 2), ("search_steps", 4),
                              ("bootstrap", 2), ("seed", 0), ("workers", 1)):
            v = getattr(self, name)
            if not isinstance(v, (int, np.integer)) or isinstance(v, (bool, np.bool_)) or v < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")
        if self.workers > 3:
            raise ValueError("at most three worker processes are supported")
        for name in ("dimensions", "counts"):
            values = getattr(self, name)
            if not values or len(set(values)) != len(values):
                raise ValueError(f"{name} must be nonempty and unique")
            if any(not isinstance(v, (int, np.integer)) or isinstance(v, (bool, np.bool_)) for v in values):
                raise ValueError(f"{name} must contain integers")
        if any(d not in (2, 3, 4) for d in self.dimensions):
            raise ValueError("dimensions must be 2, 3 or 4")
        if any(n < 8 or n > 256 for n in self.counts):
            raise ValueError("study counts must lie in [8,256]")


def identity(seed, fit, phase, family, dimension, count, repeat, parameter=None):
    """Canonical parameter-keyed stream identity, independent of traversal."""
    values = ["adversarial-v1", int(seed), int(fit), phase, family, int(dimension),
              int(count), int(repeat), parameter]
    return hashlib.sha256(json.dumps(values, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()


def rng_for(seed, fit, phase, family, dimension, count, repeat, parameter=None):
    return np.random.Generator(np.random.PCG64(int(identity(
        seed, fit, phase, family, dimension, count, repeat, parameter), 16)))


def _record(order, config, fit, phase, family, d, n, repeat, parameter=None):
    measured = extract_features(order)
    if measured["count"] != n:
        raise RuntimeError("generator count differs from requested count")
    try:
        dimension = invert_ordering_fraction(measured["ordering_fraction"])
        status = "ok"
    except ValueError:
        dimension, status = None, "out_of_domain"
    return {"sample_id": identity(config.seed, fit, phase, family, d, n, repeat, parameter),
            "fit": fit, "phase": phase, "family": family, "dimension_label": d,
            "true_dimension": d if family in {"genuine", "box"} else None,
            "repeat": repeat, "parameter": parameter,
            "estimated_dimension": dimension, "estimate_status": status,
            "classification": classify_dimension(dimension), **measured}


def _run_fit(arguments):
    config, fit = arguments
    start = perf_counter()
    raw, searches, examples, models, resources = [], [], [], {}, []
    for n in sorted(config.counts):
        split = {phase: [] for phase in ("calibration", "development", "validation")}
        for phase, repetitions in (("calibration", config.calibration),
                                   ("development", config.development),
                                   ("validation", config.validation)):
            gen_time = feature_time = 0.0
            for d in sorted(config.dimensions):
                for repeat in range(repetitions):
                    rng = rng_for(config.seed, fit, phase, "genuine", d, n, repeat)
                    tic = perf_counter()
                    order = minkowski_order(sprinkle_minkowski(d, 1., rng, count=n))
                    gen_time += perf_counter()-tic
                    tic = perf_counter()
                    row = _record(order, config, fit, phase, "genuine", d, n, repeat)
                    feature_time += perf_counter()-tic
                    split[phase].append(row)
            raw.extend(split[phase])
            resources.append(dict(fit=fit, count=n, phase=phase, orders=len(split[phase]),
                                  generation_seconds=gen_time, feature_seconds=feature_time))
        tic = perf_counter()
        model = fit_model(split["calibration"], split["validation"], target_rates=TARGETS)
        model["adversary_parameters"] = []
        models[str(n)] = model
        resources.append(dict(fit=fit, count=n, phase="detector_fit", seconds=perf_counter()-tic))
        tests = []
        gen_time = feature_time = search_time = 0.0

        def add(order_factory, family, d, repeat, parameter=None, metadata=None):
            nonlocal gen_time, feature_time
            rng = rng_for(config.seed, fit, "test", family, d, n, repeat, parameter)
            tic = perf_counter()
            order = order_factory(rng)
            gen_time += perf_counter()-tic
            tic = perf_counter()
            row = _record(order, config, fit, "test", family, d, n, repeat, parameter)
            feature_time += perf_counter()-tic
            if metadata:
                row.update(metadata)
            tests.append(row)
            return row

        for d in sorted(config.dimensions):
            development = [r for r in split["development"] if r["true_dimension"] == d]
            fit_rows = [r for r in split["calibration"] if r["true_dimension"] == d]
            matrix = np.asarray([feature_vector(r) for r in fit_rows])
            if not np.all(np.isfinite(matrix)):
                raise ValueError("undefined calibration search features; no samples were discarded")
            scales = np.maximum(matrix.std(axis=0, ddof=1), 1e-9)
            raw_q = float(np.mean([r["ordering_fraction"] for r in development])) * (n*(n-1)/2) / ((n//2)*(n-n//2))
            q = min(1., max(0., raw_q))
            model["adversary_parameters"].append(dict(dimension=d, q=q, raw_q=raw_q,
                                                      saturated=q != raw_q,
                                                      search_scales=scales.tolist()))
            for repeat in range(config.repeats):
                add(lambda rng: minkowski_order(sprinkle_minkowski(d, 1., rng, count=n)), "genuine", d, repeat)
                add(lambda rng: uniform_box_order(n, rng, d), "box", d, repeat)
                add(lambda rng: bipartite_order(n, rng, q), "matched_bipartite", d, repeat,
                    metadata={"fitted_q": q})
                search_id = identity(config.seed, fit, "test", "search", d, n, repeat)
                rng = rng_for(config.seed, fit, "test", "search", d, n, repeat)
                donor = development[int(rng.integers(len(development)))]
                tic = perf_counter()
                result = optimize_order(n, rng, donor, scales, steps=config.search_steps)
                search_time += perf_counter()-tic
                search = {"search_id": search_id, "fit": fit, "count": n, "dimension": d,
                          "repeat": repeat, "target_sample_id": donor["sample_id"], **result.metadata}
                searches.append(search)
                for family, order in (("height_matched", result.height_fraction_order),
                                      ("multi_matched", result.multifeature_order)):
                    add(lambda rng, fixed=order: fixed, family, d, repeat,
                        metadata={"search_id": search_id, "target_sample_id": donor["sample_id"]})
                    if fit == 0 and repeat == 0 and n == min(config.counts):
                        examples.append(dict(sample_id=tests[-1]["sample_id"], family=family, dimension=d,
                                             count=n, packed_rows=[np.packbits(row, bitorder="little").tobytes().hex() for row in order]))

        for family, generator in (("total", total_order), ("antichain", antichain)):
            add(lambda rng, function=generator: function(n), family, 0, 0)
        for repeat in range(config.repeats):
            for layers in (2, 3):
                add(lambda rng, k=layers: layered_order(n, rng, layers=k), f"layers_{layers}", 0, repeat)
            for c in (1, 2, 4, 8):
                add(lambda rng, c=c: random_dag_order(n, rng, c/n), f"dag_{c}", 0, repeat, c)
            add(lambda rng: random_interval_order(n, rng), "unseen_interval", 0, repeat)
            add(lambda rng: rank_intersection_order(n, rng), "rank_overlap", 2, repeat)
        tic = perf_counter()
        for row in tests:
            # The detector ignores metadata, including every test truth/target label.
            scored = score_detectors(row, model)
            row["scores"] = [scored[name]["score"] for name in DETECTORS]
            row["candidate_dimensions"] = [scored[name]["candidate_dimension"] for name in DETECTORS]
            row["accepted"] = {str(target): [scored[name]["score"] is not None and
                                             scored[name]["score"] <= model["thresholds"][str(target)][name]
                                             for name in DETECTORS] for target in TARGETS}
            row["undefined_detectors"] = [name for name in DETECTORS if scored[name]["score"] is None]
        resources.append(dict(fit=fit, count=n, phase="test", orders=len(tests),
                              generation_seconds=gen_time, feature_seconds=feature_time,
                              search_seconds=search_time, scoring_seconds=perf_counter()-tic))
        raw.extend(tests)
        # Separate deterministic resource streams; these are not scientific test observations.
        for d in sorted(config.dimensions):
            for repeat in range(3):
                rng = rng_for(config.seed, fit, "benchmark", "genuine", d, n, repeat)
                tic = perf_counter()
                order = minkowski_order(sprinkle_minkowski(d, 1., rng, count=n))
                generation = perf_counter()-tic
                tic = perf_counter()
                features = extract_features(order)
                extraction = perf_counter()-tic
                resources.append(dict(fit=fit, count=n, phase="benchmark_features", dimension=d,
                                      repeat=repeat, generation_seconds=generation, feature_seconds=extraction))
                for name in DETECTORS:
                    tic = perf_counter()
                    for _ in range(100):
                        score_detectors(features, model, detectors=(name,))
                    resources.append(dict(fit=fit, count=n, phase="benchmark_score", dimension=d,
                                          repeat=repeat, detector=name, calls=100,
                                          seconds_per_call=(perf_counter()-tic)/100))
    return dict(raw=raw, searches=searches, models=models, examples=examples,
                resources=resources, fit=fit, elapsed_seconds=perf_counter()-start,
                peak_rss_bytes=_peak_rss_bytes())


def group_key(row):
    return row["family"], row["dimension_label"], row["count"]


def _summaries(raw, config):
    groups = {}
    for row in raw:
        if row["phase"] == "test":
            groups.setdefault(group_key(row), {}).setdefault(row["fit"], []).append(row)
    summaries, paired, classification = [], [], []
    for (family, d, n), fit_rows in sorted(groups.items()):
        base = dict(family=family, dimension_label=d, count=n)
        for fit, rows in sorted(fit_rows.items()):
            for label in ("2", "3", "4", "unclassified"):
                classification.append({**base, "fit": fit, "classification": label,
                                       "orders": sum(r["classification"] == label for r in rows),
                                       "out_of_domain": sum(r["estimate_status"] != "ok" and r["classification"] == label for r in rows)})
        for target in TARGETS:
            decisions = {name: {fit: [r["accepted"][str(target)][i] for r in rows]
                                for fit, rows in fit_rows.items()} for i, name in enumerate(DETECTORS)}
            for i, name in enumerate(DETECTORS):
                rng = rng_for(config.seed, 0, "bootstrap", family, d, n, i, str(target))
                stats = summarize_fits(decisions[name], rng, config.bootstrap, deterministic=family in EXACT)
                summary = {**base, "detector": name, "target": target, **stats}
                summary["accepted_unclassified_per_fit"] = [dict(fit=fit, count=sum(
                    r["classification"] == "unclassified" and r["accepted"][str(target)][i] for r in rows))
                    for fit, rows in sorted(fit_rows.items())]
                summaries.append(summary)
            for left, right in (("A", "B"), ("A", "C"), ("A", "D"), ("A", "E"), ("A", "F"),
                                ("B", "C"), ("B", "D"), ("B", "E"), ("B", "F"),
                                ("C", "D"), ("C", "E"), ("C", "F"), ("D", "E"), ("D", "F")):
                rng = rng_for(config.seed, 0, "bootstrap", family, d, n, 0, f"{target}:{left}:{right}")
                stats = paired_comparison(decisions[left], decisions[right], rng, config.bootstrap)
                paired.append({**base, "left": left, "right": right, "target": target, **stats})
    search_effects = []
    for (family, d, n), left_rows in sorted(groups.items()):
        if family != "height_matched":
            continue
        right_rows = groups[("multi_matched", d, n)]
        for target in TARGETS:
            for i, name in enumerate(DETECTORS):
                left, right = {}, {}
                for fit, rows in left_rows.items():
                    by_search = {r["search_id"]: r for r in right_rows[fit]}
                    if {r["search_id"] for r in rows} != set(by_search):
                        raise RuntimeError("search checkpoint pairing failed")
                    left[fit] = [r["accepted"][str(target)][i] for r in rows]
                    right[fit] = [by_search[r["search_id"]]["accepted"][str(target)][i] for r in rows]
                rng = rng_for(config.seed, 0, "bootstrap", "search_effect", d, n, i, str(target))
                stats = paired_comparison(left, right, rng, config.bootstrap)
                search_effects.append(dict(dimension_label=d, count=n, detector=name, target=target,
                                           difference="height checkpoint acceptance minus full-search acceptance", **stats))
    return summaries, paired, classification, search_effects


def advancement(summaries, paired):
    """Apply the frozen criteria without ranking by an aggregate accuracy."""
    result = {}
    primary = [s for s in summaries if s["target"] == .95]
    for name in DETECTORS:
        states = []
        for s in primary:
            if s["detector"] != name or s["family"] == "box":
                continue
            if s["family"] in EXACT:
                state = "supported" if s["max_acceptance"] == 0 else "failed"
            elif s["family"] in POSITIVE:
                state = ("supported" if all(p["wilson_low"] >= .90 for p in s["per_fit"]) else
                         "failed" if any(p["wilson_high"] < .90 for p in s["per_fit"]) else "inconclusive")
            else:
                state = ("supported" if all(p["wilson_high"] <= .05 for p in s["per_fit"]) else
                         "failed" if any(p["wilson_low"] > .05 for p in s["per_fit"]) else "inconclusive")
            states.append({"family": s["family"], "dimension_label": s["dimension_label"],
                           "count": s["count"], "status": state})
        result[name] = {"status": "supported" if states and all(s["status"] == "supported" for s in states) else
                       "failed" if any(s["status"] == "failed" for s in states) else "inconclusive",
                       "cells": states}
    gains = []
    for p in paired:
        if p["target"] != .95 or p["family"] in POSITIVE | EXACT | {"box"}:
            continue
        n, left, right = p["count"], p["left"], p["right"]
        genuine = [s for s in primary if s["family"] == "genuine" and s["count"] == n
                   and s["detector"] == right]
        deterioration = [x for x in paired if x["target"] == .95 and x["family"] == "genuine"
                         and x["count"] == n and x["left"] == left and x["right"] == right]
        admissible = (bool(genuine) and bool(deterioration)
                      and {s["dimension_label"] for s in genuine} == {x["dimension_label"] for x in deterioration}
                      and all(all(f["wilson_low"] >= .9 for f in s["per_fit"]) for s in genuine)
                      and all(x["ci_high"] <= .02 for x in deterioration))
        gains.append({k: p[k] for k in ("family", "dimension_label", "count", "left", "right", "mean_difference", "ci_low", "ci_high")} |
                     {"genuine_gate": admissible, "meaningful_local_gain": admissible and p["ci_low"] > .05,
                      "supported_adverse_regression": p["ci_high"] < -.02})
    return {"primary": result, "paired_gains": gains,
            "scope": "Pointwise criteria across only three fits; no universal or simultaneous coverage claim."}


def run_study(config: StudyConfig):
    config.validate()
    start = perf_counter()
    arguments = [(config, fit) for fit in range(config.fits)]
    if config.workers == 1:
        results = [_run_fit(arg) for arg in arguments]
    else:
        with ProcessPoolExecutor(max_workers=config.workers) as pool:
            results = list(pool.map(_run_fit, arguments))
    raw = [row for result in results for row in result["raw"]]
    ids = [r["sample_id"] for r in raw]
    if len(set(ids)) != len(ids):
        raise RuntimeError("duplicate sample IDs or partition leakage")
    summary_start = perf_counter()
    summaries, paired, classification, search_effects = _summaries(raw, config)
    result = dict(config=asdict(config), raw=raw, searches=[s for r in results for s in r["searches"]],
                  models={str(r["fit"]): r["models"] for r in results},
                  examples=[s for r in results for s in r["examples"]],
                  summary=summaries, paired=paired, classification=classification, search_effects=search_effects,
                  advancement=advancement(summaries, paired),
                  resources=[s for r in results for s in r["resources"]],
                  fit_resources=[{k: r[k] for k in ("fit", "elapsed_seconds", "peak_rss_bytes")} for r in results],
                  summary_seconds=perf_counter()-summary_start, elapsed_seconds=perf_counter()-start,
                  peak_rss_bytes=_peak_rss_bytes())
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dimensions", type=int, nargs="+", default=[2, 3, 4])
    parser.add_argument("--counts", type=int, nargs="+", default=[64, 128, 256])
    for name, default in (("fits", 3), ("calibration", 100), ("development", 100),
                          ("validation", 200), ("repeats", 200), ("search-steps", 64),
                          ("bootstrap", 2000), ("seed", 20261025), ("workers", 1)):
        parser.add_argument("--"+name, type=int, default=default)
    parser.add_argument("--out", type=Path, default=Path("results/adversarial-geometry-v1"))
    args = parser.parse_args(argv)
    values = vars(args).copy()
    out = values.pop("out")
    values["dimensions"], values["counts"] = tuple(values["dimensions"]), tuple(values["counts"])
    config = StudyConfig(**values)
    try:
        config.validate()
    except ValueError as error:
        parser.error(str(error))
    result = run_study(config)
    from .adversarial_artifacts import write_outputs
    metadata = write_outputs(result, out)
    print(f"Completed {len(result['raw'])} recorded orders and {len(result['searches'])} searches in {result['elapsed_seconds']:.3f}s.")
    print(f"Scientific SHA256: {metadata['scientific_sha256']}")
    print(f"Outputs: {out}")


if __name__ == "__main__":
    main()
