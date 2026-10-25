"""Experiment 2: dimension reconstruction and adversarial order diagnostics.

Generators assume flat geometry; estimators and features consume only the order.
The joint detector is an exploratory classifier against calibrated known families,
not a test proving that arbitrary causal orders approximate a manifold.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import gzip
import hashlib
from importlib.metadata import version
import io
import json
import math
from pathlib import Path
import platform
import subprocess
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .dimension import (estimate_dimension, interval_volume, invert_ordering_fraction,
                        minkowski_order, ordering_probability, sprinkle_minkowski)
from .order_observables import (antichain, bipartite_order, indistinguishable_pair,
                               layered_order, order_observables, random_dag_order,
                               total_order)
from .scaling import _bootstrap_means, _measure, _peak_rss_bytes

FEATURES = ("ordering_fraction", "chain_fraction", "link_fraction",
            "interval_mean_fraction", "interval_ge4_fraction")
SD_FLOOR = 1e-9


@dataclass(frozen=True)
class StudyConfig:
    dimensions: tuple[int, ...] = (2, 3, 4)
    counts: tuple[int, ...] = (64, 128, 256)
    repeats: int = 200
    calibration_repeats: int = 100
    seed: int = 20261025
    bootstrap: int = 2000
    duration: float = 1.0
    benchmark_repeats: int = 3
    max_count: int = 512

    def validate(self) -> None:
        for name, minimum in (("repeats", 2), ("calibration_repeats", 10), ("seed", 0),
                              ("bootstrap", 2), ("benchmark_repeats", 1), ("max_count", 4)):
            value = getattr(self, name)
            if (not isinstance(value, (int, np.integer)) or isinstance(value, (bool, np.bool_))
                    or value < minimum):
                raise ValueError(f"{name} must be an integer >= {minimum}")
        for name in ("dimensions", "counts"):
            values = getattr(self, name)
            if not values or len(set(values)) != len(values):
                raise ValueError(f"{name} must be nonempty and unique")
            if any(not isinstance(v, (int, np.integer)) or isinstance(v, (bool, np.bool_)) for v in values):
                raise ValueError(f"{name} must contain integers")
        if any(d not in (2, 3, 4) for d in self.dimensions):
            raise ValueError("dimensions must be chosen from 2, 3 and 4")
        if any(n < 4 or n > self.max_count for n in self.counts):
            raise ValueError("study counts must be between 4 and max_count")
        if self.max_count > 512:
            raise ValueError("this study has an explicit maximum of 512 events")
        if (not isinstance(self.duration, (int, float, np.integer, np.floating))
                or isinstance(self.duration, (bool, np.bool_))
                or not math.isfinite(self.duration) or self.duration <= 0):
            raise ValueError("duration must be finite and positive")
        for d in self.dimensions:
            interval_volume(d, self.duration)


def _identity(seed: int, dimension: int, count: int, repeat: int, stream: str,
              duration: float = 1.0) -> str:
    text = f"dimension-v1|{int(seed)}|{int(dimension)}|{int(count)}|{int(repeat)}|{float(duration).hex()}|{stream}"
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def rng_for(seed: int, dimension: int, count: int, repeat: int, stream: str,
            duration: float = 1.0) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(int(_identity(seed, dimension, count, repeat, stream, duration), 16)))


def _rng(config: StudyConfig, dimension: int, count: int, repeat: int, stream: str):
    return rng_for(config.seed, dimension, count, repeat, stream, config.duration)


def wilson_interval(successes: int, count: int) -> tuple[float | None, float | None]:
    """Two-sided 95% Wilson score interval for independent-order binary outcomes."""
    if not isinstance(count, (int, np.integer)) or not isinstance(successes, (int, np.integer)):
        raise ValueError("successes and count must be integers")
    if count < 0 or successes < 0 or successes > count:
        raise ValueError("require 0 <= successes <= count")
    if count == 0:
        return None, None
    z = 1.959963984540054
    p = successes / count
    denominator = 1 + z*z / count
    center = (p + z*z / (2*count)) / denominator
    half = z * math.sqrt(p*(1-p)/count + z*z/(4*count*count)) / denominator
    return (0.0 if successes == 0 else max(0.0, center-half),
            1.0 if successes == count else min(1.0, center+half))


def summarize(values, rng: np.random.Generator, bootstrap: int, *, binary: bool = False) -> dict:
    """Across-order uncertainty; None observations are counted explicitly.

    A singleton deterministic control has no empirical variance/SE or bootstrap
    interval. Invalid estimates are not replaced by boundary values.
    """
    values = list(values)
    valid = np.asarray([float(v) for v in values if v is not None], dtype=float)
    if not np.all(np.isfinite(valid)):
        raise ValueError("summary values must be finite or None")
    if (not isinstance(bootstrap, (int, np.integer)) or isinstance(bootstrap, (bool, np.bool_))
            or bootstrap < 2):
        raise ValueError("bootstrap must be an integer >= 2")
    count = len(valid)
    result = {"count": len(values), "valid_count": count, "invalid_count": len(values)-count,
              "mean": None, "variance": None, "sd": None, "se": None, "ci_low": None, "ci_high": None}
    if count:
        result["mean"] = float(valid.mean())
    if count >= 2:
        variance = float(valid.var(ddof=1))
        low, high = np.quantile(_bootstrap_means(valid, rng, bootstrap), [0.025, 0.975])
        result.update(variance=variance, sd=math.sqrt(variance), se=math.sqrt(variance/count),
                      ci_low=float(low), ci_high=float(high))
    if binary:
        if np.any((valid != 0) & (valid != 1)):
            raise ValueError("binary summary values must be zero or one")
        low, high = wilson_interval(int(valid.sum()), count)
        result.update(successes=int(valid.sum()), wilson_low=low, wilson_high=high)
    return result


def classify_dimension(value: float | None) -> str:
    """Nearest label 2/3/4 only inside [1.5,4.5]; no out-of-range clamping."""
    if value is None or not math.isfinite(value) or value < 1.5 or value > 4.5:
        return "unclassified"
    # Ties go to the lower label; this deterministic convention is recorded.
    return str(min((2, 3, 4), key=lambda d: (abs(value-d), d)))


def _measure_order(order: np.ndarray, config: StudyConfig) -> tuple[dict, list[int]]:
    # Neither function accepts coordinates or true/target dimension.
    estimate = estimate_dimension(order)
    observables = order_observables(order, max_count=config.max_count)
    if (estimate.count != observables["count"] or estimate.relations != observables["relations"]
            or estimate.ordering_fraction != observables["ordering_fraction"]):
        raise RuntimeError("estimator and observable relation-count consistency check failed")
    record = {"count": estimate.count, "relations": estimate.relations,
              "ordering_fraction": estimate.ordering_fraction,
              "estimated_dimension": estimate.dimension, "estimate_status": estimate.status,
              "classification": classify_dimension(estimate.dimension),
              "longest_chain": observables["longest_chain"],
              "chain_fraction": observables["chain_fraction"],
              "link_count": observables["link_count"], "link_fraction": observables["link_fraction"],
              "interval_mean": observables["interval_mean"],
              "interval_mean_fraction": observables["interval_mean_fraction"],
              "interval_ge4_fraction": observables["interval_ge4_fraction"]}
    return record, observables["interval_histogram"]


def _feature_vector(row: dict) -> np.ndarray | None:
    if any(row[name] is None for name in FEATURES):
        return None
    return np.asarray([row[name] for name in FEATURES], dtype=float)


def _scores(row: dict, model: dict) -> tuple[float | None, float | None]:
    r = row["ordering_fraction"]
    vector = _feature_vector(row)
    single = []
    joint = []
    for template in model["templates"]:
        if r is not None:
            single.append(abs((r-template["centroid"][0])/template["scale"][0]))
        if vector is not None:
            joint.append(float(np.sqrt(np.mean(((vector-np.asarray(template["centroid"]))
                                                 /np.asarray(template["scale"]))**2))))
    return min(single) if single else None, min(joint) if joint else None


def _fit_models(config: StudyConfig, calibration: list[dict]) -> dict:
    models = {}
    split = config.calibration_repeats // 2
    for n in sorted(config.counts):
        templates = []
        for d in sorted(config.dimensions):
            fit = [row for row in calibration if row["count"] == n and row["true_dimension"] == d
                   and row["repeat"] < split]
            vectors = [_feature_vector(row) for row in fit]
            valid = np.asarray([v for v in vectors if v is not None])
            if len(valid) < 2:
                raise ValueError("insufficient defined calibration features for a template")
            scale = valid.std(axis=0, ddof=1)
            templates.append({"dimension": d, "fit_count": len(fit), "defined_fit_count": len(valid),
                              "excluded_undefined_fit_count": len(fit)-len(valid),
                              "centroid": valid.mean(axis=0).tolist(),
                              "raw_sd": scale.tolist(), "scale": np.maximum(scale, SD_FLOOR).tolist()})
        model = {"count": n, "templates": templates, "features": list(FEATURES), "sd_floor": SD_FLOOR,
                 "fit_repeats_per_dimension": split,
                 "threshold_repeats_per_dimension": config.calibration_repeats-split}
        threshold_rows = [row for row in calibration if row["count"] == n and row["repeat"] >= split]
        scores = [_scores(row, model) for row in threshold_rows]
        single = [a for a, _ in scores if a is not None]
        joint = [b for _, b in scores if b is not None]
        if len(single) < 2 or len(joint) < 2:
            raise ValueError("insufficient calibration threshold scores")
        model.update(r_threshold=float(np.quantile(single, 0.95)), joint_threshold=float(np.quantile(joint, 0.95)),
                     threshold_count=len(threshold_rows), defined_r_threshold_count=len(single),
                     defined_joint_threshold_count=len(joint),
                     excluded_undefined_joint_threshold_count=len(threshold_rows)-len(joint),
                     threshold_quantile=0.95)
        models[str(n)] = model
    return models


def _score_record(row: dict, model: dict) -> None:
    single, joint = _scores(row, model)
    row.update(r_score=single, joint_score=joint,
               r_accepted=single is not None and single <= model["r_threshold"],
               joint_accepted=joint is not None and joint <= model["joint_threshold"],
               r_rejection_reason=("undefined ordering fraction" if single is None else
                                   "score exceeds calibrated threshold" if single > model["r_threshold"] else None),
               joint_rejection_reason=("undefined conditional interval features" if joint is None else
                                       "score exceeds calibrated threshold" if joint > model["joint_threshold"] else None))


def _new_record(order, config, dimension, n, repeat, stream, family, phase, *, parameter=None):
    measured, histogram = _measure_order(order, config)
    sample_id = _identity(config.seed, dimension, n, repeat, stream, config.duration)
    row = {"sample_id": sample_id, "phase": phase, "family": family,
           "true_dimension": dimension if family == "genuine" else None,
           "target_dimension": dimension if family == "matched_bipartite" else None,
           "repeat": repeat, "seed": config.seed, "parameter": parameter,
           **measured}
    return row, {"sample_id": sample_id, "phase": phase, "family": family, "count": n,
                 "interval_histogram": histogram}


def _calibrate(config: StudyConfig) -> tuple[list[dict], list[dict], dict]:
    calibration, histograms = [], []
    for n in sorted(config.counts):
        for d in sorted(config.dimensions):
            for repeat in range(config.calibration_repeats):
                sample = sprinkle_minkowski(d, config.duration, _rng(config, d, n, repeat, "calibration"), count=n)
                row, histogram = _new_record(minkowski_order(sample), config, d, n, repeat,
                                             "calibration", "genuine", "calibration")
                row["calibration_role"] = "fit" if repeat < config.calibration_repeats//2 else "threshold"
                calibration.append(row)
                histograms.append(histogram)
    models = _fit_models(config, calibration)
    adversary_parameters = []
    for n in sorted(config.counts):
        capacity = (n//2)*(n-n//2)/(n*(n-1)/2)
        for d in sorted(config.dimensions):
            values = [row["ordering_fraction"] for row in calibration
                      if row["count"] == n and row["true_dimension"] == d]
            target = float(np.mean(values))
            raw_q = target/capacity
            q = min(1.0, max(0.0, raw_q))
            adversary_parameters.append({"count": n, "target_dimension": d,
                                         "calibration_count": len(values), "target_mean_fraction": target,
                                         "capacity_fraction": capacity, "raw_probability": raw_q,
                                         "edge_probability": q, "saturated": raw_q != q,
                                         "saturation_reason": "target outside balanced bipartite capacity" if raw_q != q else None})
    for row in calibration:
        _score_record(row, models[str(row["count"])])
    return calibration, histograms, {"models": models, "adversary_parameters": adversary_parameters,
                                    "split": "first half fit centroids/scales; second half calibrates 95th-percentile thresholds; all calibration rows fit bipartite probability",
                                    "holdout_used_for_calibration": False}


def _holdout(config: StudyConfig, calibrated: dict):
    raw, histograms = [], []
    probabilities = {(p["count"], p["target_dimension"]): p["edge_probability"]
                     for p in calibrated["adversary_parameters"]}
    for n in sorted(config.counts):
        for d in sorted(config.dimensions):
            for repeat in range(config.repeats):
                sample = sprinkle_minkowski(d, config.duration, _rng(config, d, n, repeat, "primary"), count=n)
                order = minkowski_order(sample)
                row, hist = _new_record(order, config, d, n, repeat, "primary", "genuine", "primary")
                _score_record(row, calibrated["models"][str(n)])
                raw.append(row); histograms.append(hist)
                q = probabilities[(n, d)]
                order = bipartite_order(n, _rng(config, d, n, repeat, "matched_bipartite"), edge_probability=q)
                row, hist = _new_record(order, config, d, n, repeat, "matched_bipartite", "matched_bipartite", "control", parameter=q)
                _score_record(row, calibrated["models"][str(n)])
                raw.append(row); histograms.append(hist)
        for family in ("random_dag", "layered", "total_order", "antichain"):
            repetitions = 1 if family in ("total_order", "antichain") else config.repeats
            for repeat in range(repetitions):
                generator = _rng(config, 0, n, repeat, family)
                parameter = None
                if family == "random_dag":
                    parameter = 2/n
                    order = random_dag_order(n, generator, edge_probability=parameter)
                elif family == "layered":
                    parameter = 3
                    order = layered_order(n, generator, layers=3)
                elif family == "total_order":
                    order = total_order(n)
                else:
                    order = antichain(n)
                row, hist = _new_record(order, config, 0, n, repeat, family, family, "control", parameter=parameter)
                _score_record(row, calibrated["models"][str(n)])
                raw.append(row); histograms.append(hist)
    # Canonical ordering makes serialized data independent of caller grid traversal.
    raw.sort(key=lambda r: (r["count"], r["family"], r["true_dimension"] or r["target_dimension"] or 0, r["repeat"]))
    histograms.sort(key=lambda r: r["sample_id"])
    return raw, histograms


def _group_key(row):
    return row["family"], row["true_dimension"] or row["target_dimension"] or 0, row["count"]


def _summary(config: StudyConfig, raw: list[dict]) -> list[dict]:
    groups = {}
    for row in raw:
        groups.setdefault(_group_key(row), []).append(row)
    summary = []
    metrics = ("ordering_fraction", "estimated_dimension", "longest_chain", "link_fraction",
               "interval_mean_fraction", "interval_ge4_fraction", "r_accepted", "joint_accepted")
    for (family, d, n), rows in sorted(groups.items()):
        item = {"family": family, "dimension_label": d or None, "count": n, "repeats": len(rows),
                "deterministic_control": family in ("total_order", "antichain"),
                "invalid_estimates": sum(r["estimate_status"] != "ok" for r in rows)}
        for metric in metrics:
            stats = summarize([r[metric] for r in rows], _rng(config, d, n, 0, f"summary:{family}:{metric}"),
                              config.bootstrap, binary=metric in ("r_accepted", "joint_accepted"))
            if item["deterministic_control"] and metric in ("r_accepted", "joint_accepted"):
                stats["wilson_low"] = stats["wilson_high"] = None
            item.update({f"{metric}_{k}": v for k, v in stats.items()})
        mean_r = item["ordering_fraction_mean"]
        try:
            item["dimension_of_mean_fraction"] = invert_ordering_fraction(mean_r)
        except ValueError:
            item["dimension_of_mean_fraction"] = None
        if d:
            stats = summarize([int(row["classification"] == str(d)) for row in rows],
                              _rng(config, d, n, 0, f"summary:{family}:accuracy"), config.bootstrap, binary=True)
            item.update({f"classification_accuracy_{k}": v for k, v in stats.items()})
            for suffix in ("mean", "ci_low", "ci_high"):
                value = item[f"estimated_dimension_{suffix}"]
                item[f"dimension_bias_{suffix}"] = None if value is None else value-d
        else:
            for suffix in ("count", "valid_count", "invalid_count", "mean", "variance", "sd", "se", "ci_low", "ci_high", "successes", "wilson_low", "wilson_high"):
                item[f"classification_accuracy_{suffix}"] = None
            for suffix in ("mean", "ci_low", "ci_high"):
                item[f"dimension_bias_{suffix}"] = None
        summary.append(item)
    return summary


def _contrast(a: list[float], b: list[float], rng, bootstrap: int) -> dict:
    a, b = np.asarray(a), np.asarray(b)
    samples = _bootstrap_means(b, rng, bootstrap)-_bootstrap_means(a, rng, bootstrap)
    low, high = np.quantile(samples, [0.025, 0.975])
    return {"difference": float(b.mean()-a.mean()), "ci_low": float(low), "ci_high": float(high)}


def _diagnostics(config: StudyConfig, raw: list[dict], summary: list[dict]) -> dict:
    recovery, fraction_checks, matched, detector = [], [], [], []
    for row in summary:
        family, d, n = row["family"], row["dimension_label"], row["count"]
        if family == "genuine":
            expected = ordering_probability(d)
            se = row["ordering_fraction_se"]
            difference = row["ordering_fraction_mean"]-expected
            z = difference/se if se else None
            fraction_checks.append({"dimension": d, "count": n, "expected_fraction": expected,
                                    "observed_mean": row["ordering_fraction_mean"], "standard_error": se,
                                    "mean_minus_reference": difference, "z": z,
                                    "investigate_five_se": z is None or abs(z)>5})
            lower = row["classification_accuracy_wilson_low"]
            upper = row["classification_accuracy_wilson_high"]
            accuracy = "supports" if lower >= 0.90 else "fails" if upper < 0.90 else "inconclusive"
            low, high = row["dimension_bias_ci_low"], row["dimension_bias_ci_high"]
            bias = ("undefined" if low is None else "supports" if low >= -0.1 and high <= 0.1
                    else "fails" if low > 0.1 or high < -0.1 else "inconclusive")
            recovery.append({"dimension": d, "count": n, "primary_decision_cell": n == 256,
                             "accuracy_wilson_outcome": accuracy, "bias_tolerance_outcome": bias,
                             "accuracy_threshold": 0.90, "absolute_bias_tolerance": 0.1})
        if family == "matched_bipartite":
            genuine = [r["ordering_fraction"] for r in raw if r["family"] == "genuine" and r["true_dimension"] == d and r["count"] == n]
            adversary = [r["ordering_fraction"] for r in raw if r["family"] == family and r["target_dimension"] == d and r["count"] == n]
            contrast = _contrast(genuine, adversary, _rng(config, d, n, 0, "matched-contrast"), config.bootstrap)
            matched.append({"target_dimension": d, "count": n, **contrast,
                            "contrast": "matched_adversary_minus_genuine_ordering_fraction",
                            "within_absolute_0_02": abs(contrast["difference"]) <= 0.02})
        rows = [r for r in raw if _group_key(r) == (family, d or 0, n)]
        # A rejected adversary is a correct rejection. For genuine inputs this
        # same difference is additional rejection of genuine orders, not benefit.
        change = [int(r["r_accepted"])-int(r["joint_accepted"]) for r in rows]
        stats = summarize(change, _rng(config, d or 0, n, 0, f"paired:{family}"), config.bootstrap)
        genuine_acceptance = [s["joint_accepted_mean"] for s in summary if s["family"] == "genuine" and s["count"] == n]
        minimum_genuine = min(genuine_acceptance)
        outcome = ("deterministic_control" if len(rows) == 1 else
                   "supports_exploratory_improvement" if stats["ci_low"] > 0 and minimum_genuine >= 0.85 else
                   "genuine_acceptance_below_0_85" if minimum_genuine < 0.85 else
                   "worse" if stats["ci_high"] < 0 else "inconclusive")
        detector.append({"family": family, "dimension_label": d, "count": n,
                         "paired_joint_minus_r_rejection": stats,
                         "minimum_genuine_joint_acceptance_at_count": minimum_genuine,
                         "outcome": outcome if family != "genuine" else "genuine_acceptance_diagnostic"})
    confusion = []
    for n in sorted(config.counts):
        for d in sorted(config.dimensions):
            group = [r for r in raw if r["family"] == "genuine" and r["count"] == n and r["true_dimension"] == d]
            for label in ("2", "3", "4", "unclassified"):
                number = sum(r["classification"] == label for r in group)
                lo, hi = wilson_interval(number, len(group))
                confusion.append({"count": n, "true_dimension": d, "predicted_dimension": label,
                                  "samples": number, "total": len(group), "fraction": number/len(group),
                                  "wilson_low": lo, "wilson_high": hi})
    first, second = indistinguishable_pair()
    left = order_observables(first, max_count=config.max_count)
    right = order_observables(second, max_count=config.max_count)
    if left != right:
        raise RuntimeError("declared indistinguishable-observable example does not match")
    return {"recovery_decisions": recovery, "ordering_fraction_checks": fraction_checks,
            "matched_fraction_contrasts": matched, "detector_comparisons": detector,
            "failed_estimate_counts": {status: sum(r["estimate_status"] == status for r in raw)
                                       for status in sorted({r["estimate_status"] for r in raw})},
            "indistinguishable_example": {"description": "Nonisomorphic three-event V order and its dual Λ share every selected symmetric observable. Distinct minimal/maximal-element counts distinguish them, but were not selected features.",
                                          "first_order": first.astype(int).tolist(), "second_order": second.astype(int).tolist(),
                                          "shared_observables": left},
            "confusion": confusion,
            "uncertainty_note": "Pointwise across-independent-order percentile bootstrap mean intervals; stochastic binary rates additionally have Wilson score intervals. Deterministic controls have no sampling intervals. Detector intervals condition on the frozen fitted calibration model and do not integrate calibration uncertainty. No independent-pair binomial inference or simultaneous coverage is claimed."}


def _benchmarks(config: StudyConfig) -> list[dict]:
    rows = []
    for n in sorted(config.counts):
        for d in sorted(config.dimensions):
            for repeat in range(config.benchmark_repeats):
                rngs = iter((_rng(config, d, n, repeat, "benchmark"), _rng(config, d, n, repeat, "benchmark")))
                sample, seconds, peak = _measure(lambda: sprinkle_minkowski(d, config.duration, next(rngs), count=n))
                base = {"dimension": d, "count": n, "repeat": repeat,
                        "sample_id": _identity(config.seed, d, n, repeat, "benchmark", config.duration)}
                rows.append({**base, "phase": "generation", "seconds": seconds, "traced_peak_bytes": peak})
                order, seconds, peak = _measure(lambda: minkowski_order(sample))
                rows.append({**base, "phase": "order_construction", "seconds": seconds, "traced_peak_bytes": peak})
                _, seconds, peak = _measure(lambda: _measure_order(order, config))
                rows.append({**base, "phase": "order_only_analysis", "seconds": seconds, "traced_peak_bytes": peak})
    return rows


def _metadata(config: StudyConfig) -> dict:
    package = Path(__file__).resolve().parent
    root = package.parents[1]
    names = ("core.py", "scaling.py", "dimension.py", "order_observables.py", "dimension_study.py")
    hashes = {f"src/causal_lab/{name}": hashlib.sha256((package/name).read_bytes()).hexdigest() for name in names}
    commit, dirty = None, None
    if (root/".git").exists():
        try:
            commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True).stdout.strip())
        except (OSError, subprocess.CalledProcessError):
            pass
    protocol = root/"docs/DIMENSION_RECONSTRUCTION_PROTOCOL.md"
    return {"schema_version": 1, "config": asdict(config),
            "versions": {"python": platform.python_version(), "numpy": np.__version__, "matplotlib": matplotlib.__version__, "package": version("causal-spacetime-lab")},
            "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
            "source_sha256": hashes, "git_commit": commit, "git_worktree_dirty": dirty,
            "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest() if protocol.exists() else None,
            "rng": "Generator(PCG64(int(SHA256(identity).hexdigest(),16)))",
            "seed_identity": "ASCII dimension-v1|master_seed|dimension_or_zero_for_untargeted_control|count|repeat|float(duration).hex()|purpose; independent purposes calibration, primary, matched_bipartite, random_dag, layered, benchmark, summary/contrast",
            "bootstrap": {"resamples": config.bootstrap, "confidence": 0.95, "method": "percentile", "sampling_unit": "whole independent order", "coverage": "pointwise"},
            "estimator": {"domain": [1, 10], "undefined_or_outside_domain": "None and explicit status, never clamped", "classification": "nearest integer label 2/3/4 for estimates in [1.5,4.5], lower label breaks exact ties, otherwise unclassified"},
            "detector": {"features": list(FEATURES), "score": "minimum RMS standardized distance to fitted known-dimension templates", "threshold": "95th percentile of separate threshold-calibration scores", "scope": "exploratory discrimination among calibrated families, not manifoldlikeness proof"},
            "timing_scope": "perf_counter untraced calls; RNG setup excluded from generator; matrix construction separate; order-only analysis includes validation, MM inversion and all interval/chain features",
            "allocation_scope": "Separate tracemalloc passes on same deterministic samples; peak newly tracked allocations excludes retained inputs; not RSS and may miss native allocations",
            "process_peak_rss_bytes": _peak_rss_bytes(),
            "rss_scope": "Process lifetime including imports, calibration, holdouts, bootstrap and benchmarks, before output plotting; Darwin bytes or Linux KiB converted to bytes",
            "scientific_status": "Reconstruction inside a prescribed flat spacetime and adversarial order tests; no dynamical emergence or observational evidence about physical spacetime"}


def run_study(config: StudyConfig) -> dict:
    config.validate()
    config = StudyConfig(dimensions=tuple(map(int, config.dimensions)), counts=tuple(map(int, config.counts)),
                         **{name: float(getattr(config, name)) if name == "duration" else int(getattr(config, name))
                            for name in ("repeats", "calibration_repeats", "seed", "bootstrap", "duration", "benchmark_repeats", "max_count")})
    start = perf_counter()
    calibration, calibration_hist, calibrated = _calibrate(config)
    raw, holdout_hist = _holdout(config, calibrated)
    summary = _summary(config, raw)
    diagnostics = _diagnostics(config, raw, summary)
    benchmarks = _benchmarks(config)
    result = {"calibration": calibration, "calibration_model": calibrated, "raw": raw,
              "interval_histograms": sorted(calibration_hist+holdout_hist, key=lambda r: r["sample_id"]),
              "summary": summary, "diagnostics": diagnostics, "confusion": diagnostics["confusion"],
              "benchmarks": benchmarks}
    metadata = _metadata(config)
    metadata["study_wall_seconds"] = perf_counter()-start
    scientific = {k: v for k, v in result.items() if k != "benchmarks"}
    metadata["scientific_digest"] = hashlib.sha256(json.dumps(scientific, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    result["metadata"] = metadata
    return result


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=160, metadata={"Software": "causal-spacetime-lab"})
    plt.close(fig)


def _intervals(ax, x, means, lows, highs, **kwargs):
    ax.plot(x, means, **kwargs)
    color = ax.lines[-1].get_color()
    for xx, lo, hi in zip(x, lows, highs):
        if lo is not None and hi is not None:
            ax.vlines(xx, lo, hi, color=color, linewidth=1.5)


def _plots(result: dict, out: Path) -> None:
    primary = [s for s in result["summary"] if s["family"] == "genuine"]
    counts = sorted({s["count"] for s in primary})
    dimensions = sorted({s["dimension_label"] for s in primary})
    markers = ("o", "s", "^")
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for k, n in enumerate(counts):
        rows = sorted((s for s in primary if s["count"] == n), key=lambda s: s["dimension_label"])
        _intervals(ax, [s["dimension_label"]+0.035*(k-(len(counts)-1)/2) for s in rows],
                   [s["ordering_fraction_mean"] for s in rows], [s["ordering_fraction_ci_low"] for s in rows],
                   [s["ordering_fraction_ci_high"] for s in rows], marker=markers[k%3], label=f"N={n}")
    ax.plot(dimensions, [ordering_probability(d) for d in dimensions], "kx", markersize=9, label="Analytic p(d)")
    ax.set(xlabel="Known spacetime dimension d (evaluation only)", ylabel="Mean ordering fraction R / C(N,2)",
           xticks=dimensions, title="Ordering fraction: pointwise 95% bootstrap mean intervals")
    ax.legend(); _save(fig, out/"ordering_fraction.png")

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for k, n in enumerate(counts):
        rows = sorted((s for s in primary if s["count"] == n), key=lambda s: s["dimension_label"])
        _intervals(ax, [s["dimension_label"]+0.035*(k-(len(counts)-1)/2) for s in rows],
                   [s["estimated_dimension_mean"] for s in rows], [s["estimated_dimension_ci_low"] for s in rows],
                   [s["estimated_dimension_ci_high"] for s in rows], marker=markers[k%3], label=f"N={n}")
    ax.plot([min(dimensions)-.2, max(dimensions)+.2], [min(dimensions)-.2, max(dimensions)+.2], "k--", label="Known dimension")
    ax.set(xlabel="Known spacetime dimension d (evaluation only)", ylabel="Mean per-order inferred dimension",
           xticks=dimensions, title="Order-only recovery: pointwise 95% mean intervals")
    ax.legend(); _save(fig, out/"dimension_recovery.png")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4))
    for d in dimensions:
        rows = sorted((s for s in primary if s["dimension_label"] == d), key=lambda s: s["count"])
        _intervals(axes[0], [s["count"] for s in rows], [s["dimension_bias_mean"] for s in rows],
                   [s["dimension_bias_ci_low"] for s in rows], [s["dimension_bias_ci_high"] for s in rows], marker="o", label=f"d={d}")
        axes[1].plot([s["count"] for s in rows], [s["estimated_dimension_sd"] for s in rows], "o-", label=f"d={d}")
    axes[0].axhline(0, color="black", linewidth=.8)
    axes[0].axhspan(-.1, .1, color="gray", alpha=.12, label="Registered ±0.10 tolerance")
    for ax in axes: ax.set(xscale="log", xlabel="Events per order N"); ax.legend(fontsize=8)
    axes[0].set(ylabel="Mean inferred dimension − known d", title="Bias and pointwise 95% mean intervals")
    axes[1].set(ylabel="Sample SD of inferred dimension", title="Across-order spread (not mean uncertainty)")
    _save(fig, out/"bias_vs_count.png")

    fig, axes = plt.subplots(1, len(counts), figsize=(4.0*len(counts), 3.8), squeeze=False)
    for ax, n in zip(axes[0], counts):
        table = np.zeros((len(dimensions), 4))
        for i, d in enumerate(dimensions):
            for j, label in enumerate(("2", "3", "4", "unclassified")):
                table[i, j] = next(r["fraction"] for r in result["confusion"] if r["count"] == n and r["true_dimension"] == d and r["predicted_dimension"] == label)
        ax.imshow(table, vmin=0, vmax=1, cmap="Blues", aspect="auto")
        for i in range(len(dimensions)):
            for j in range(4): ax.text(j, i, f"{table[i,j]:.1%}", ha="center", va="center", color="white" if table[i,j]>.5 else "black", fontsize=9)
        ax.set(xticks=range(4), xticklabels=["2", "3", "4", "unclass."], yticks=range(len(dimensions)), yticklabels=dimensions,
               xlabel="Predicted dimension label", ylabel="Known dimension", title=f"N={n}; independent orders")
    _save(fig, out/"confusion.png")

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.9))
    largest = max(counts)
    rows = [s for s in result["summary"] if s["count"] == largest]
    labels = [f"{s['family'].replace('_',' ')}"+(f" d={s['dimension_label']}" if s["dimension_label"] else "") for s in rows]
    xx = np.arange(len(rows))
    for k, metric in enumerate(("r_accepted", "joint_accepted")):
        values = [s[f"{metric}_mean"] for s in rows]
        axes[0].barh(xx+(k-.5)*.32, values, height=.3, label="r only" if k == 0 else "joint features")
        for y, s in zip(xx+(k-.5)*.32, rows):
            # Deterministic controls have no sampling interval; stochastic rates
            # use Wilson intervals, including when all observed outcomes agree.
            if not s["deterministic_control"]:
                axes[0].hlines(y, s[f"{metric}_wilson_low"], s[f"{metric}_wilson_high"], color="black", linewidth=.8)
    axes[0].set(yticks=xx, yticklabels=labels, xlabel="Accepted as calibrated genuine-family order", xlim=(0,1.05), title=f"Holdout acceptance, N={largest}; 95% Wilson bars")
    axes[0].tick_params(axis="y", labelsize=8); axes[0].legend(fontsize=8)
    for d in dimensions:
        genuine = [r for r in result["raw"] if r["count"] == largest and r["family"] == "genuine" and r["true_dimension"] == d]
        matched = [r for r in result["raw"] if r["count"] == largest and r["family"] == "matched_bipartite" and r["target_dimension"] == d]
        color = plt.get_cmap("tab10")(d-2)
        axes[1].scatter([r["ordering_fraction"] for r in genuine], [r["longest_chain"] for r in genuine], s=12, alpha=.45, color=color, marker="o", label=f"genuine d={d}")
        axes[1].scatter([r["ordering_fraction"] for r in matched], [r["longest_chain"] for r in matched], s=18, alpha=.5, color=color, marker="x", label=f"matched target={d}")
    axes[1].set(xlabel="Order fraction r", ylabel="Longest chain [events]", title="One fraction can conceal a different chain structure")
    axes[1].legend(fontsize=7)
    _save(fig, out/"adversaries.png")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
    for phase, label, marker, color in (("generation", "coordinates", "o", "tab:blue"), ("order_construction", "construct order", "s", "tab:orange"), ("order_only_analysis", "validate + infer + features", "^", "tab:green")):
        for n in counts:
            group = [r for r in result["benchmarks"] if r["phase"] == phase and r["count"] == n]
            for ax, field, scale in ((axes[0], "seconds", 1000), (axes[1], "traced_peak_bytes", 1/1024)):
                values = np.array([r[field]*scale for r in group])
                ax.plot(n, values.mean(), marker=marker, color=color, linestyle="none", label=label if n == counts[0] else None)
                ax.vlines(n, values.min(), values.max(), color=color, linewidth=1)
    for ax in axes: ax.set(xscale="log", yscale="log", xlabel="Events per order N"); ax.legend(fontsize=8)
    axes[0].set(ylabel="Untraced wall time [ms]", title="Mean; min–max over dimensions and trials")
    axes[1].set(ylabel="Peak newly traced allocations [KiB]", title="Separate memory passes; retained inputs excluded")
    _save(fig, out/"resources.png")


def _csv_text(rows: list[dict]) -> str:
    stream = io.StringIO(newline="")
    fields = list(dict.fromkeys(key for row in rows for key in row))
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(v, separators=(",", ":")) if isinstance(v, (list, dict)) else v for k, v in row.items()})
    return stream.getvalue()


def write_outputs(result: dict, out: Path | str) -> None:
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    start = perf_counter()
    for name in ("raw", "calibration", "summary", "confusion", "benchmarks"):
        (out/f"{name}.csv").write_text(_csv_text(result[name]), encoding="utf-8")
    for name in ("summary", "calibration_model", "diagnostics", "confusion"):
        (out/f"{name}.json").write_text(json.dumps(result[name], sort_keys=True, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    # Full interval histograms are losslessly compressed, with deterministic gzip
    # headers; neither raw orders nor redundant image/notebook outputs are stored.
    with (out/"interval_histograms.csv.gz").open("wb") as destination:
        with gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as compressed:
            compressed.write(_csv_text(result["interval_histograms"]).encode())
    _plots(result, out)
    metadata = dict(result["metadata"])
    deterministic = ("raw.csv", "calibration.csv", "summary.csv", "confusion.csv", "summary.json",
                     "calibration_model.json", "diagnostics.json", "confusion.json", "interval_histograms.csv.gz",
                     "ordering_fraction.png", "dimension_recovery.png", "bias_vs_count.png", "confusion.png", "adversaries.png")
    metadata["artifact_sha256"] = {name: hashlib.sha256((out/name).read_bytes()).hexdigest() for name in deterministic}
    metadata["output_wall_seconds"] = perf_counter()-start
    metadata["process_peak_rss_after_outputs_bytes"] = _peak_rss_bytes()
    metadata["nondeterministic_artifacts"] = ["benchmarks.csv", "resources.png", "metadata.json"]
    metadata["reproduction_command"] = "python -m causal_lab.dimension_study " + " ".join(
        ["--dimensions", *map(str, metadata["config"]["dimensions"]), "--counts", *map(str, metadata["config"]["counts"]),
         "--repeats", str(metadata["config"]["repeats"]), "--calibration-repeats", str(metadata["config"]["calibration_repeats"]),
         "--seed", str(metadata["config"]["seed"]), "--bootstrap", str(metadata["config"]["bootstrap"]),
         "--duration", str(metadata["config"]["duration"]), "--benchmark-repeats", str(metadata["config"]["benchmark_repeats"]),
         "--max-count", str(metadata["config"]["max_count"]), "--out", "results/dimension-reconstruction-v1"])
    (out/"metadata.json").write_text(json.dumps(metadata, sort_keys=True, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def main() -> None:
    defaults = StudyConfig()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dimensions", nargs="+", type=int, default=defaults.dimensions)
    parser.add_argument("--counts", nargs="+", type=int, default=defaults.counts)
    for name in ("repeats", "calibration_repeats", "seed", "bootstrap", "benchmark_repeats", "max_count"):
        parser.add_argument("--"+name.replace("_", "-"), type=int, default=getattr(defaults, name))
    parser.add_argument("--duration", type=float, default=defaults.duration)
    parser.add_argument("--out", type=Path, default=Path("results/dimension-reconstruction-v1"))
    options = vars(parser.parse_args())
    out = options.pop("out")
    options["dimensions"] = tuple(options["dimensions"]); options["counts"] = tuple(options["counts"])
    config = StudyConfig(**options)
    try:
        config.validate()
    except ValueError as exc:
        parser.error(str(exc))
    result = run_study(config)
    write_outputs(result, out)
    primary = sum(r["family"] == "genuine" for r in result["raw"])
    controls = len(result["raw"])-primary
    print(f"Completed {primary} primary, {len(result['calibration'])} calibration and {controls} control orders in {result['metadata']['study_wall_seconds']:.3f}s (outputs excluded).")
    print(f"Scientific SHA256: {result['metadata']['scientific_digest']}")
    print(f"Saved tables, diagnostics, full interval histograms and six figures to {out}")


if __name__ == "__main__":
    main()
