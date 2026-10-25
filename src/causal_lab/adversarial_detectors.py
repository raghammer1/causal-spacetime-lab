"""Registered Experiment 3 detectors and repeated-calibration uncertainty.

These are comparisons with finite, calibrated flat-interval ensembles. Their
acceptance does not establish manifoldlikeness. Detector D deliberately preserves
the compensating RMS score used in Experiment 2. All inference consumes order
features only; dimension labels are required solely when fitting templates.
"""
from __future__ import annotations

import hashlib
import json
import math

import numpy as np

FEATURES = ("ordering_fraction", "chain_fraction", "link_fraction",
            "interval_mean_fraction", "interval_ge4_fraction")
DETECTORS = ("A", "B", "C", "D", "E", "F")
SD_FLOOR = 1e-9


def _integer(value, name: str, minimum: int = 0) -> int:
    if (not isinstance(value, (int, np.integer)) or isinstance(value, (bool, np.bool_))
            or value < minimum):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def _target_key(target) -> str:
    if (not isinstance(target, (int, float, np.integer, np.floating))
            or isinstance(target, (bool, np.bool_)) or not math.isfinite(target)
            or not 0 < target < 1):
        raise ValueError("acceptance target must be finite and strictly between zero and one")
    return str(float(target))


def _feature_values(row: dict) -> list[float | None]:
    values = []
    for name in FEATURES:
        if name not in row:
            raise ValueError(f"missing feature {name}")
        value = row[name]
        if value is not None:
            if (not isinstance(value, (int, float, np.integer, np.floating))
                    or isinstance(value, (bool, np.bool_)) or not math.isfinite(value)
                    or not 0 <= value <= 1):
                raise ValueError(f"feature {name} must be finite in [0,1] or None")
            value = float(value)
        values.append(value)
    return values


def _abundance(row: dict) -> np.ndarray:
    if "abundance_vector" not in row:
        raise ValueError("missing abundance_vector")
    raw = np.asarray(row["abundance_vector"])
    if (raw.shape != (10,) or raw.dtype.kind not in "iuf" or not np.all(np.isfinite(raw))
            or np.any(raw < 0) or np.any(raw > 1)
            or not math.isclose(float(raw.sum()), 1.0, rel_tol=0, abs_tol=1e-12)):
        raise ValueError("abundance_vector must contain ten nonnegative probabilities summing to one")
    return raw.astype(float, copy=False)


def _partition(rows: list[dict], name: str) -> tuple[int, set[str]]:
    if not rows:
        raise ValueError(f"{name} partition must not be empty")
    counts = {_integer(row.get("count"), "count", 2) for row in rows}
    if len(counts) != 1:
        raise ValueError("a detector model must have one event count")
    sample_ids = [row.get("sample_id") for row in rows]
    if any(not isinstance(s, str) or not s for s in sample_ids):
        raise ValueError(f"{name} rows require nonempty sample_id strings")
    if len(set(sample_ids)) != len(sample_ids):
        raise ValueError(f"duplicate sample IDs in {name} partition")
    for row in rows:
        dimension = _integer(row.get("true_dimension"), "true_dimension", 2)
        if dimension not in (2, 3, 4):
            raise ValueError("calibration dimensions must be 2, 3 or 4")
        _feature_values(row)
        _abundance(row)
    return counts.pop(), set(sample_ids)


def _id_hash(ids: set[str]) -> str:
    return hashlib.sha256(json.dumps(sorted(ids), separators=(",", ":")).encode("ascii")).hexdigest()


def fit_model(calibration_rows, validation_rows, *, target_rates=(0.9, 0.95, 0.975)) -> dict:
    """Fit one count/fit model, using calibration templates and validation cutoffs.

    Both partitions must have unique, disjoint IDs and the same candidate
    dimensions. Five-feature centroids use complete rows, just as Experiment 2;
    exclusions and achieved validation acceptance (including undefined rejections)
    are recorded. F uses every valid abundance vector. No adversary or test
    outcomes enter this function.
    """
    calibration, validation = list(calibration_rows), list(validation_rows)
    n, fit_ids = _partition(calibration, "calibration")
    validation_n, validation_ids = _partition(validation, "validation")
    if n != validation_n or fit_ids & validation_ids:
        raise ValueError("calibration and validation must have equal counts and disjoint IDs")
    dimensions = sorted({int(row["true_dimension"]) for row in calibration})
    if set(dimensions) != {int(row["true_dimension"]) for row in validation}:
        raise ValueError("calibration and validation must cover the same candidate dimensions")
    targets = [_target_key(t) for t in target_rates]
    if not targets or len(set(targets)) != len(targets):
        raise ValueError("acceptance targets must be nonempty and unique")
    templates = []
    for d in dimensions:
        rows = [r for r in calibration if r["true_dimension"] == d]
        vectors = [_feature_values(row) for row in rows]
        complete = np.asarray([v for v in vectors if all(x is not None for x in v)], dtype=float)
        if len(complete) < 2:
            raise ValueError("each dimension needs at least two complete calibration feature vectors")
        raw_sd = complete.std(axis=0, ddof=1)
        templates.append({"dimension": d, "fit_count": len(rows),
                          "defined_fit_count": len(complete),
                          "excluded_undefined_fit_count": len(rows)-len(complete),
                          "centroid": complete.mean(axis=0).tolist(),
                          "raw_sd": raw_sd.tolist(),
                          "scale": np.maximum(raw_sd, SD_FLOOR).tolist(),
                          "abundance_centroid": np.mean([_abundance(r) for r in rows], axis=0).tolist()})
    model = {"count": n, "features": list(FEATURES), "sd_floor": SD_FLOOR,
             "templates": templates, "thresholds": {}, "validation": {},
             "calibration_count": len(calibration), "validation_count": len(validation),
             "calibration_ids_sha256": _id_hash(fit_ids),
             "validation_ids_sha256": _id_hash(validation_ids),
             "holdout_used_for_calibration": False,
             "threshold_method": "pooled genuine validation np.quantile(method=linear); scores <= threshold"}
    scored = [score_detectors(row, model) for row in validation]
    for target in targets:
        thresholds, diagnostics = {}, {}
        for detector in DETECTORS:
            scores = [row[detector]["score"] for row in scored]
            defined = [score for score in scores if score is not None]
            if not defined:
                raise ValueError(f"no defined validation scores for detector {detector}")
            threshold = float(np.quantile(defined, float(target), method="linear"))
            thresholds[detector] = threshold
            accepted = [score is not None and score <= threshold for score in scores]
            diagnostics[detector] = {
                "defined_count": len(defined), "undefined_count": len(scores)-len(defined),
                "accepted": sum(accepted), "total": len(scores),
                "achieved_acceptance": sum(accepted)/len(scores),
                "by_dimension": {str(d): {
                    "accepted": int(sum(a for a, r in zip(accepted, validation) if r["true_dimension"] == d)),
                    "total": int(sum(r["true_dimension"] == d for r in validation)),
                    "achieved_acceptance": float(np.mean([a for a, r in zip(accepted, validation)
                                                           if r["true_dimension"] == d]))}
                    for d in dimensions}}
        model["thresholds"][target] = thresholds
        model["validation"][target] = diagnostics
    return model


def score_detectors(feature_row: dict, model: dict, *, detectors=DETECTORS) -> dict:
    """Order-feature scores and minimizing candidate labels; true labels ignored.

    Each detector chooses ONE candidate template independently. E is a maximum
    within a template, followed by a minimum across templates, not the maximum
    of separately minimized feature scores. F is the normalized Hellinger metric.
    An optional nonempty detector subset evaluates only its necessary score
    formulas, allowing separate cost measurements; input validation is included.
    """
    try:
        requested = tuple(detectors)
    except TypeError as error:
        raise ValueError("detectors must be a nonempty unique subset of A through F") from error
    if (not requested or any(name not in DETECTORS for name in requested)
            or len(set(requested)) != len(requested)):
        raise ValueError("detectors must be a nonempty unique subset of A through F")
    required = set()
    if "A" in requested or "C" in requested:
        required.add(0)
    if "B" in requested or "C" in requested:
        required.add(1)
    if "D" in requested or "E" in requested:
        required.update(range(5))
    values = _feature_values(feature_row) if required else None
    abundance = _abundance(feature_row) if "F" in requested else None
    if _integer(feature_row.get("count"), "count", 2) != model["count"]:
        raise ValueError("feature event count differs from fitted model")
    templates = model.get("templates", [])
    if not templates:
        raise ValueError("model needs at least one template")
    candidates = {name: [] for name in requested}
    for template in templates:
        dimension = _integer(template["dimension"], "template dimension", 2)
        if dimension not in (2, 3, 4):
            raise ValueError("template dimension must be 2, 3 or 4")
        z = [None]*5
        if required:
            centroid = np.asarray(template["centroid"], dtype=float)
            scale = np.asarray(template["scale"], dtype=float)
            if (centroid.shape != (5,) or scale.shape != (5,)
                    or not np.all(np.isfinite(centroid)) or not np.all(np.isfinite(scale))
                    or np.any(centroid < 0) or np.any(centroid > 1)
                    or np.any(scale < SD_FLOOR)):
                raise ValueError("model centroids must be in [0,1] and scales must be >= the registered floor")
            for j in required:
                if values[j] is not None:
                    z[j] = (values[j]-centroid[j])/scale[j]
        if "A" in requested and z[0] is not None:
            candidates["A"].append((abs(z[0]), dimension))
        if "B" in requested and z[1] is not None:
            candidates["B"].append((abs(z[1]), dimension))
        if "C" in requested and z[0] is not None and z[1] is not None:
            candidates["C"].append((float(np.sqrt(np.mean(np.square(z[:2])))), dimension))
        if all(value is not None for value in z):
            if "D" in requested:
                candidates["D"].append((float(np.sqrt(np.mean(np.square(z)))), dimension))
            if "E" in requested:
                candidates["E"].append((float(np.max(np.abs(z))), dimension))
        if "F" in requested:
            q = _abundance({"abundance_vector": template["abundance_centroid"]})
            candidates["F"].append((float(np.sqrt(np.sum((np.sqrt(abundance)-np.sqrt(q))**2)/2)), dimension))
    result = {}
    for detector in requested:
        score, dimension = min(candidates[detector]) if candidates[detector] else (None, None)
        result[detector] = {"score": None if score is None else float(score), "candidate_dimension": dimension}
    return result


def evaluate_detectors(feature_row: dict, model: dict, *, target=0.95) -> dict:
    key = _target_key(target)
    if key not in model.get("thresholds", {}):
        raise ValueError("target was not fitted on validation data")
    result = score_detectors(feature_row, model)
    for detector, outcome in result.items():
        threshold = model["thresholds"][key][detector]
        if not math.isfinite(threshold) or threshold < 0:
            raise ValueError("threshold must be finite and nonnegative")
        score = outcome["score"]
        accepted = score is not None and score <= threshold
        outcome.update(accepted=accepted, rejection_reason=(None if accepted else
                       "undefined required order features" if score is None else
                       "score exceeds calibrated threshold"))
    return result


def wilson_interval(successes: int, count: int) -> tuple[float | None, float | None]:
    """Pointwise two-sided 95% Wilson interval on independent orders of one fit."""
    successes, count = _integer(successes, "successes"), _integer(count, "count")
    if successes > count:
        raise ValueError("successes cannot exceed count")
    if not count:
        return None, None
    z = 1.959963984540054
    p = successes/count
    denominator = 1+z*z/count
    center = (p+z*z/(2*count))/denominator
    half = z*math.sqrt(p*(1-p)/count+z*z/(4*count*count))/denominator
    return (0.0 if successes == 0 else max(0.0, center-half),
            1.0 if successes == count else min(1.0, center+half))


def _binary_groups(decisions_by_fit: dict) -> tuple[list, list[np.ndarray]]:
    if not isinstance(decisions_by_fit, dict) or not decisions_by_fit:
        raise ValueError("decisions must be a nonempty dictionary by fit")
    keys = sorted(decisions_by_fit, key=lambda key: (type(key).__name__, str(key)))
    arrays = []
    for key in keys:
        if not isinstance(key, (str, int)) or isinstance(key, bool):
            raise ValueError("fit identifiers must be strings or integers")
        array = np.asarray(decisions_by_fit[key])
        if (array.ndim != 1 or not len(array) or array.dtype.kind not in "biuf"
                or not np.all(np.isfinite(array)) or np.any((array != 0) & (array != 1))):
            raise ValueError("every fit needs a nonempty one-dimensional binary decision vector")
        arrays.append(array.astype(float, copy=False))
    return keys, arrays


def _hierarchical_means(arrays: list[np.ndarray], rng: np.random.Generator, bootstrap: int) -> np.ndarray:
    """Resample fits, then whole-order scalar outcomes within selected fits.

    Drawing multinomial counts from the empirical scalar distribution is exactly
    equivalent in law to drawing individual order indices with replacement. It
    avoids allocating bootstrap-by-N index arrays. Paired callers pass per-order
    differences, preserving their joint decisions in every resample.
    """
    bootstrap = _integer(bootstrap, "bootstrap", 2)
    k = len(arrays)
    selected = rng.integers(k, size=(bootstrap, k))
    draws = np.zeros((bootstrap, k), dtype=float)
    for i, array in enumerate(arrays):
        values, counts = np.unique(array, return_counts=True)
        probabilities = counts/len(array)
        mask = selected == i
        number = int(mask.sum())
        if number:
            draws[mask] = rng.multinomial(len(array), probabilities, size=number) @ values / len(array)
    return draws.mean(axis=1)


def summarize_fits(decisions_by_fit: dict, rng: np.random.Generator, bootstrap: int = 2000,
                   *, deterministic: bool = False) -> dict:
    """Per-fit Wilson intervals plus explicitly exploratory hierarchical bounds.

    There is no pooled Wilson interval. With only three fits, between-fit
    inference is weak. Constant bootstrap outcomes can have degenerate bounds;
    the nondegenerate per-fit Wilson intervals remain the advancement criterion.
    Exact controls use deterministic=True and have no per-fit binomial interval.
    """
    if not isinstance(deterministic, bool):
        raise ValueError("deterministic must be Boolean")
    keys, arrays = _binary_groups(decisions_by_fit)
    if deterministic and any(len(array) != 1 for array in arrays):
        raise ValueError("exact deterministic controls must occur once per fit")
    per_fit = []
    for key, array in zip(keys, arrays):
        accepted = int(array.sum())
        low, high = (None, None) if deterministic else wilson_interval(accepted, len(array))
        per_fit.append({"fit": key, "n": len(array), "accepted": accepted,
                        "rate": float(array.mean()), "wilson_low": low, "wilson_high": high})
    rates = np.asarray([row["rate"] for row in per_fit])
    low, high = np.quantile(_hierarchical_means(arrays, rng, bootstrap), [0.025, 0.975])
    return {"fit_count": len(arrays), "total_orders": sum(len(array) for array in arrays),
            "per_fit": per_fit, "mean_acceptance": float(rates.mean()),
            "between_fit_sd": float(rates.std(ddof=1)) if len(rates) >= 2 else None,
            "min_acceptance": float(rates.min()), "max_acceptance": float(rates.max()),
            "hierarchical_ci_low": float(low), "hierarchical_ci_high": float(high),
            "all_lower_at_least_0_90": None if deterministic else all(r["wilson_low"] >= .90 for r in per_fit),
            "all_upper_at_most_0_05": None if deterministic else all(r["wilson_high"] <= .05 for r in per_fit),
            "deterministic": deterministic}


def paired_comparison(left_by_fit: dict, right_by_fit: dict, rng: np.random.Generator,
                      bootstrap: int = 2000) -> dict:
    """Paired acceptance difference left-minus-right, with fit clustering.

    Inputs must list the same orders in the same order within each fit. For a
    simple left and complex right detector, a positive difference means improved
    adversary rejection, but increased false rejection on genuine orders.
    """
    keys, left = _binary_groups(left_by_fit)
    right_keys, right = _binary_groups(right_by_fit)
    if keys != right_keys or any(len(a) != len(b) for a, b in zip(left, right)):
        raise ValueError("paired decisions require the same fit IDs and order counts")
    differences = [a-b for a, b in zip(left, right)]
    per_fit = []
    for key, a, b, delta in zip(keys, left, right, differences):
        per_fit.append({"fit": key, "n": len(a), "mean_difference": float(delta.mean()),
                        "both_accepted": int(np.sum((a == 1) & (b == 1))),
                        "left_only": int(np.sum((a == 1) & (b == 0))),
                        "right_only": int(np.sum((a == 0) & (b == 1))),
                        "both_rejected": int(np.sum((a == 0) & (b == 0)))})
    means = np.asarray([d.mean() for d in differences])
    low, high = np.quantile(_hierarchical_means(differences, rng, bootstrap), [0.025, 0.975])
    return {"fit_count": len(left), "per_fit": per_fit, "mean_difference": float(means.mean()),
            "between_fit_sd": float(means.std(ddof=1)) if len(means) >= 2 else None,
            "ci_low": float(low), "ci_high": float(high)}
