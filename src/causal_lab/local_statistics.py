"""Conditional interval-law references and whole-parent uncertainty.

The estimand is a pooled interval ratio WITHIN each fit. Across independent
fits we average those ratios/deviations equally. No function here classifies
an order as geometric or fits an acceptance threshold.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
from itertools import permutations
import math

import numpy as np

from .dimension import (invert_ordering_fraction, minkowski_order,
                        ordering_probability, sprinkle_minkowski)
from .local_random import rng_for
from .local_structure import (canonical_poset_code, motif_catalog,
                              small_order_signature)


METRICS = ("connected2", "motif22_4", "connected4", "connected8",
           "motif22_8", "joint8")
TOLERANCES = dict(zip(METRICS, (.02, .01, .03, .05, .01, .01)))
TOLERANCES["tv4"] = .08
MOTIF_METRICS = tuple(f"motif4_{i:02d}" for i in range(16))
ALL_METRICS = METRICS + MOTIF_METRICS + ("tv4",)
_SIZES = np.asarray([2, 4, 4, 8, 8, 8] + [4] * 16)


def _integer(value, name: str, minimum: int = 0) -> int:
    if (not isinstance(value, (int, np.integer))
            or isinstance(value, (bool, np.bool_)) or value < minimum):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def _dimension(value) -> int:
    value = _integer(value, "dimension", 2)
    if value not in (2, 3, 4):
        raise ValueError("dimension must be 2, 3 or 4")
    return value


@lru_cache(maxsize=1)
def _catalog_vectors() -> tuple[np.ndarray, np.ndarray, dict[int, int]]:
    catalog = motif_catalog()
    if len(catalog) != 16 or [entry["id"] for entry in catalog] != list(range(16)):
        raise ValueError("four-event motif catalog must have stable IDs 0..15")
    connected = np.asarray([entry["components"] == 1 for entry in catalog], dtype=float)
    two_plus_two = np.asarray([entry["n22"] for entry in catalog], dtype=float)
    lookup = {entry["canonical_code"]: entry["id"] for entry in catalog}
    return connected, two_plus_two, lookup


def connected_permutation_count(count: int) -> int:
    """Exact connected comparability-graph count among count! rank orders."""
    count = _integer(count, "count", 1)
    values = [0] * (count + 1)
    values[1] = 1
    for n in range(2, count + 1):
        values[n] = math.factorial(n) - sum(
            values[j] * math.factorial(n - j) for j in range(1, n))
    return values[count]


@lru_cache(maxsize=1)
def _exact_rank_tables() -> tuple[tuple[int, ...], tuple[tuple[int, int, int], ...]]:
    """Exhaust permutations, not merely samples from the rank-order law."""
    _, _, lookup = _catalog_vectors()
    ids = []
    indices4 = np.arange(4)
    forward4 = indices4[:, None] < indices4[None, :]
    for permutation in permutations(range(4)):
        ranks = np.asarray(permutation)
        order = forward4 & (ranks[:, None] < ranks[None, :])
        ids.append(lookup[canonical_poset_code(order)])
    joint = Counter()
    indices8 = np.arange(8)
    forward8 = indices8[:, None] < indices8[None, :]
    for permutation in permutations(range(8)):
        ranks = np.asarray(permutation)
        order = forward8 & (ranks[:, None] < ranks[None, :])
        components, n22 = small_order_signature(order)
        joint[(int(components == 1), n22)] += 1
    table = tuple((connected, n22, number)
                  for (connected, n22), number in sorted(joint.items()))
    if sum(c * number for c, _, number in table) != connected_permutation_count(8):
        raise AssertionError("exhaustive connectivity disagrees with recurrence")
    if sum(n22 * number for _, n22, number in table) * 24 != math.factorial(8) * 70:
        raise AssertionError("exhaustive 2+2 mean disagrees with the four-subset law")
    return tuple(ids), table


def build_reference(dimension: int, fit: int, seed: int, *,
                    m4_count: int = 5000, m8_count: int = 2000) -> dict:
    """Generate an independent reference fit with auditable outcome records.

    d=2 uses complete permutation tables and has no calibration sampling error.
    d=3,4 retain each independently seeded small order's categorical outcome;
    grouped counts are sufficient for an exactly equivalent outcome bootstrap.
    """
    dimension = _dimension(dimension)
    fit = _integer(fit, "fit")
    seed = _integer(seed, "seed")
    m4_count = _integer(m4_count, "m4_count", 1)
    m8_count = _integer(m8_count, "m8_count", 1)
    _, _, lookup = _catalog_vectors()
    if dimension == 2:
        exact_ids, table = _exact_rank_tables()
        ids = list(exact_ids)
        joint_table = [list(row) for row in table]
        outcomes8 = None
        m4_count, m8_count = math.factorial(4), math.factorial(8)
    else:
        ids, outcomes8 = [], []
        for repeat in range(m4_count):
            rng = rng_for(seed, fit, "reference4", "diamond", dimension, 4, repeat)
            order = minkowski_order(sprinkle_minkowski(dimension, 1., rng, count=4))
            ids.append(lookup[canonical_poset_code(order)])
        for repeat in range(m8_count):
            rng = rng_for(seed, fit, "reference8", "diamond", dimension, 8, repeat)
            order = minkowski_order(sprinkle_minkowski(dimension, 1., rng, count=8))
            components, n22 = small_order_signature(order)
            outcomes8.append([int(components == 1), n22])
        counts8 = Counter(map(tuple, outcomes8))
        joint_table = [[c, n22, number] for (c, n22), number in sorted(counts8.items())]
    return {
        "dimension": dimension, "fit": fit, "seed": seed,
        "exact": dimension == 2, "connected2": ordering_probability(dimension),
        "m4": {"count": m4_count, "outcomes": ids,
               "counts": np.bincount(ids, minlength=16).tolist()},
        "m8": {"count": m8_count, "outcomes": outcomes8, "joint_counts": joint_table},
        "method": ("all 4! and 8! rank permutations" if dimension == 2 else
                   "independent fixed-count diamond orders; one keyed stream per repeat"),
    }


def _reference_arrays(reference: dict) -> tuple[np.ndarray, np.ndarray]:
    dimension = _dimension(reference["dimension"])
    _integer(reference["fit"], "reference fit")
    if not isinstance(reference.get("exact"), bool) or reference["exact"] != (dimension == 2):
        raise ValueError("only the registered d=2 references are exact")
    counts4 = np.asarray(reference["m4"]["counts"])
    n4 = _integer(reference["m4"]["count"], "reference4 count", 1)
    if (counts4.shape != (16,) or counts4.dtype.kind not in "iu"
            or np.any(counts4 < 0) or int(counts4.sum()) != n4):
        raise ValueError("reference4 counts must be 16 nonnegative integers summing to count")
    ids4 = np.asarray(reference["m4"]["outcomes"])
    if (ids4.shape != (n4,) or ids4.dtype.kind not in "iu" or np.any(ids4 < 0)
            or np.any(ids4 >= 16) or not np.array_equal(np.bincount(ids4, minlength=16), counts4)):
        raise ValueError("reference4 categorical records disagree with counts")
    table8 = np.asarray(reference["m8"]["joint_counts"])
    n8 = _integer(reference["m8"]["count"], "reference8 count", 1)
    if (table8.ndim != 2 or table8.shape[1] != 3 or len(table8) == 0
            or table8.dtype.kind not in "iu" or np.any(table8 < 0)
            or np.any(table8[:, 0] > 1) or np.any(table8[:, 1] > 70)
            or np.any(table8[:, 2] == 0) or int(table8[:, 2].sum()) != n8
            or len({tuple(row[:2]) for row in table8.tolist()}) != len(table8)):
        raise ValueError("reference8 joint counts are invalid")
    if not reference["exact"]:
        outcomes = np.asarray(reference["m8"]["outcomes"])
        if (outcomes.shape != (n8, 2) or outcomes.dtype.kind not in "iu"
                or Counter(map(tuple, outcomes.tolist())) != {
                    (int(c), int(n22)): int(n) for c, n22, n in table8}):
            raise ValueError("reference8 categorical records disagree with counts")
    else:
        exact_ids, exact_table = _exact_rank_tables()
        if (n4 != 24 or n8 != math.factorial(8)
                or not np.array_equal(counts4, np.bincount(exact_ids, minlength=16))
                or {(int(c), int(n22)): int(n) for c, n22, n in table8}
                != {(c, n22): n for c, n22, n in exact_table}):
            raise ValueError("d=2 exact reference disagrees with complete permutation enumeration")
    if not math.isclose(reference["connected2"], ordering_probability(dimension), abs_tol=1e-15):
        raise ValueError("connected2 reference must equal the analytic law")
    return counts4.astype(float), table8.astype(float)


def _reference_vectors(reference: dict, rng: np.random.Generator,
                       draws: int) -> tuple[np.ndarray, np.ndarray]:
    counts4, table8 = _reference_arrays(reference)
    connected4, n22_4, _ = _catalog_vectors()
    probs4 = counts4 / counts4.sum()
    probs8 = table8[:, 2] / table8[:, 2].sum()
    if reference["exact"]:
        boot4 = np.broadcast_to(probs4, (draws, 16))
        boot8 = np.broadcast_to(probs8, (draws, len(probs8)))
    else:
        boot4 = rng.multinomial(int(counts4.sum()), probs4, size=draws) / counts4.sum()
        boot8 = rng.multinomial(int(table8[:, 2].sum()), probs8, size=draws) / table8[:, 2].sum()
    values8 = np.column_stack((table8[:, 0], table8[:, 1] / 70,
                              table8[:, 0] * table8[:, 1] / 70))
    point = np.concatenate(([reference["connected2"], probs4 @ n22_4,
                             probs4 @ connected4], probs8 @ values8, probs4))
    boot = np.column_stack((np.full(draws, reference["connected2"]), boot4 @ n22_4,
                            boot4 @ connected4, boot8 @ values8, boot4))
    return point, boot


def _parent_arrays(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    connected4, n22_4, _ = _catalog_vectors()
    outcomes, denominators, supports = [], [], []
    for row in rows:
        counts = np.asarray([_integer(row[f"interval_m{m}_count"], f"m{m} interval count")
                             for m in (2, 4, 8)])
        if int(counts.sum()) > math.comb(_integer(row["count"], "parent count", 2), 2):
            raise ValueError("parent interval counts exceed the number of endpoint pairs")
        if "interval_histogram" in row:
            histogram = row["interval_histogram"]
            if any(counts[i] != (histogram[m] if m < len(histogram) else 0)
                   for i, m in enumerate((2, 4, 8))):
                raise ValueError("parent interval counts disagree with full histogram")
        conn2 = _integer(row["interval_m2_connected"], "m2 connected")
        conn8 = _integer(row["interval_m8_connected"], "m8 connected")
        sum22 = _integer(row["interval_m8_n22_sum"], "m8 n22 sum")
        joint22 = _integer(row["interval_m8_connected_n22_sum"], "m8 joint n22 sum")
        motifs = np.asarray(row["interval_m4_motif_counts"])
        if (motifs.shape != (16,) or motifs.dtype.kind not in "iu" or np.any(motifs < 0)
                or int(motifs.sum()) != counts[1]):
            raise ValueError("parent m4 motif counts disagree with interval count")
        if (conn2 > counts[0] or conn8 > counts[2] or sum22 > 70 * counts[2]
                or joint22 > sum22 or joint22 > 70 * conn8):
            raise ValueError("parent local numerators exceed their denominators")
        if "interval_m8_joint" in row:
            table = row["interval_m8_joint"]
            totals = [0, 0, 0, 0]
            for components, n22, number in table:
                components = _integer(components, "m8 joint components", 1)
                n22 = _integer(n22, "m8 joint n22")
                number = _integer(number, "m8 joint count", 1)
                if components > 8 or n22 > 70:
                    raise ValueError("m8 joint outcome is outside its range")
                totals[0] += number
                totals[1] += int(components == 1) * number
                totals[2] += n22 * number
                totals[3] += int(components == 1) * n22 * number
            if totals != [counts[2], conn8, sum22, joint22]:
                raise ValueError("parent m8 joint table disagrees with scalar sums")
        outcomes.append(np.concatenate(([conn2, motifs @ n22_4, motifs @ connected4,
                                          conn8, sum22 / 70, joint22 / 70], motifs)))
        denominators.append(np.asarray([counts[{2: 0, 4: 1, 8: 2}[m]] for m in _SIZES]))
        supports.append(counts)
    return np.asarray(outcomes, dtype=float), np.asarray(denominators, dtype=float), np.asarray(supports)


def _ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    return np.divide(numerator, denominator, out=np.full_like(numerator, np.nan, dtype=float),
                     where=denominator != 0)


def _finite(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None


def _ci(values: np.ndarray) -> list[float] | None:
    # Dropping undefined replicates would silently condition on interval presence.
    if not np.all(np.isfinite(values)):
        return None
    return np.quantile(values, [.025, .975], method="linear").tolist()


def _status(ci: list[float] | None, tolerance: float | None,
            sufficient: bool, *, total_variation: bool = False) -> str:
    if not sufficient:
        return "insufficient_information"
    if ci is None:
        return "inconclusive"
    if tolerance is None:
        return "descriptive"
    low, high = ci
    if total_variation:
        return "equivalent" if high < tolerance else "contradicts" if low > tolerance else "inconclusive"
    if low > -tolerance and high < tolerance:
        return "equivalent"
    if high < -tolerance or low > tolerance:
        return "contradicts"
    return "inconclusive"


def _dimension_summary(probability: float, bootstrap: np.ndarray) -> dict:
    interval = _ci(bootstrap)
    def invert(value):
        if value is None or not math.isfinite(value):
            return None
        try:
            return invert_ordering_fraction(float(value))
        except ValueError:
            return None
    estimate = invert(probability)
    bounds = None if interval is None else [invert(interval[1]), invert(interval[0])]
    complete_bounds = bounds is not None and all(value is not None for value in bounds)
    return {"estimate": estimate, "ci95": bounds,
            "probability": _finite(probability), "probability_ci95": interval,
            "status": ("undefined" if not math.isfinite(probability) else
                       "out_of_domain" if estimate is None else
                       "interval_out_of_domain" if not complete_bounds else "ok"),
            "inversion_domain": [1, 10], "uses_true_dimension": False}


def _metric_rows(estimate: np.ndarray, reference: np.ndarray, boot_estimate: np.ndarray,
                 boot_reference: np.ndarray, support: dict, centered: np.ndarray,
                 centered_boot: np.ndarray, sufficient: dict) -> list[dict]:
    delta = estimate - reference
    boot_delta = boot_estimate - boot_reference
    tv = .5 * np.sum(np.abs(delta[6:22]))
    boot_tv = .5 * np.sum(np.abs(boot_delta[:, 6:22]), axis=1)
    result = []
    for index, name in enumerate(ALL_METRICS):
        is_tv = name == "tv4"
        size = 4 if is_tv else int(_SIZES[index])
        values = boot_tv if is_tv else boot_delta[:, index]
        interval = _ci(values)
        row = {"metric": name, "interval_size": size,
               "estimate": _finite(tv if is_tv else estimate[index]),
               "reference": 0. if is_tv else _finite(reference[index]),
               "difference": _finite(tv if is_tv else delta[index]), "ci95": interval,
               "estimate_ci95": _ci(boot_tv if is_tv else boot_estimate[:, index]),
               "reference_ci95": [0., 0.] if is_tv else _ci(boot_reference[:, index]),
               "tolerance": TOLERANCES.get(name),
               "status": _status(interval, TOLERANCES.get(name), sufficient[size],
                                 total_variation=is_tv),
               "support": support[size],
               "undefined_bootstrap_draws": int(np.count_nonzero(~np.isfinite(values)))}
        if not is_tv:
            row["mean_centered_count_per_pair"] = _finite(centered[index])
            row["centered_ci95"] = _ci(centered_boot[:, index])
        result.append(row)
    return result


def summarize_conditional(parent_rows, reference_fits, *, rng: np.random.Generator,
                          bootstrap_draws: int = 2000,
                          min_positive_parents: int = 30,
                          min_intervals: int = 100) -> dict:
    """Compare one family/count with one candidate dimension's reference fits.

    ``reference_fits`` is a list with one reference dictionary per fit. The
    dimension is a candidate reference, never used by local-dimension inversion.
    Parent and calibration draws are independent. The same resampled parent
    weights preserve correlations among its overlapping interval observables.
    """
    draws = _integer(bootstrap_draws, "bootstrap_draws", 2)
    min_positive_parents = _integer(min_positive_parents, "min_positive_parents", 1)
    min_intervals = _integer(min_intervals, "min_intervals", 1)
    rows, refs = list(parent_rows), list(reference_fits)
    if not rows or not refs or not isinstance(rng, np.random.Generator):
        raise ValueError("nonempty parent/reference rows and a NumPy Generator are required")
    counts = {_integer(row["count"], "parent count", 2) for row in rows}
    if len(counts) != 1:
        raise ValueError("conditional summary requires one parent event count")
    count = counts.pop()
    fit_ids = sorted({_integer(row["fit"], "parent fit") for row in rows})
    reference_map = {_integer(ref["fit"], "reference fit"): ref for ref in refs}
    if len(reference_map) != len(refs) or set(reference_map) != set(fit_ids):
        raise ValueError("one unique reference is required for each parent fit")
    dimensions = {_dimension(ref["dimension"]) for ref in refs}
    if len(dimensions) != 1:
        raise ValueError("references must specify one candidate dimension")
    if all("sample_id" in row for row in rows):
        if len({row["sample_id"] for row in rows}) != len(rows):
            raise ValueError("duplicate parent sample IDs")
    dimension = dimensions.pop()
    reports, internals = [], []
    k = len(fit_ids)
    # Reserve independent within-fit draws for each hierarchical fit occurrence,
    # in addition to the first `draws` used for the per-fit reports. This avoids
    # approximating the hierarchical law by resampling a finite bootstrap pool.
    draws_per_fit = draws * (k + 1)
    for fit in fit_ids:
        parents = [row for row in rows if row["fit"] == fit]
        numerator, denominator, size_counts = _parent_arrays(parents)
        n = len(parents)
        reference, boot_reference = _reference_vectors(reference_map[fit], rng, draws_per_fit)
        estimate = _ratio(numerator.sum(axis=0), denominator.sum(axis=0))
        weights = rng.multinomial(n, np.full(n, 1 / n), size=draws_per_fit)
        boot_numerator, boot_denominator = weights @ numerator, weights @ denominator
        boot_estimate = _ratio(boot_numerator, boot_denominator)
        pair_count = math.comb(count, 2)
        centered = np.mean(numerator - denominator * reference, axis=0) / pair_count
        boot_centered = (boot_numerator - boot_denominator * boot_reference) / (n * pair_count)
        support = {m: {"positive_parents": int(np.count_nonzero(size_counts[:, i])),
                       "parent_count": n, "interval_count": int(size_counts[:, i].sum())}
                   for i, m in enumerate((2, 4, 8))}
        sufficient = {m: s["positive_parents"] >= min_positive_parents
                      and s["interval_count"] >= min_intervals for m, s in support.items()}
        reports.append({"fit": fit, "metrics": _metric_rows(
            estimate, reference, boot_estimate[:draws], boot_reference[:draws], support,
            centered, boot_centered[:draws], sufficient),
            "local_dimension": _dimension_summary(estimate[0], boot_estimate[:draws, 0])})
        internals.append((estimate, reference, boot_estimate, boot_reference,
                          centered, boot_centered, support, sufficient))
    # Each occurrence of a selected fit gets an independently selected within-fit
    # bootstrap replicate. Repeated fit selections do not share parent resamples.
    selected_fits = rng.integers(0, k, size=(draws, k))
    selected_draws = draws + np.arange(draws * k).reshape(draws, k)
    estimates = np.asarray([item[0] for item in internals])
    references = np.asarray([item[1] for item in internals])
    boot_estimates = np.asarray([item[2] for item in internals])
    boot_references = np.asarray([item[3] for item in internals])
    centered = np.asarray([item[4] for item in internals])
    boot_centered = np.asarray([item[5] for item in internals])
    pooled_boot_estimate = boot_estimates[selected_fits, selected_draws].mean(axis=1)
    pooled_boot_reference = boot_references[selected_fits, selected_draws].mean(axis=1)
    pooled_boot_centered = boot_centered[selected_fits, selected_draws].mean(axis=1)
    support = {m: {"by_fit": [{"fit": fit, **item[6][m]} for fit, item in zip(fit_ids, internals)],
                   "positive_parents": sum(item[6][m]["positive_parents"] for item in internals),
                   "parent_count": len(rows),
                   "interval_count": sum(item[6][m]["interval_count"] for item in internals)}
               for m in (2, 4, 8)}
    sufficient = {m: all(item[7][m] for item in internals) for m in (2, 4, 8)}
    pooled = _metric_rows(estimates.mean(axis=0), references.mean(axis=0),
                          pooled_boot_estimate, pooled_boot_reference, support,
                          centered.mean(axis=0), pooled_boot_centered, sufficient)
    # TV is nonlinear: its registered across-fit estimand is the mean of fitwise
    # TVs, not the TV of the mean deviation (which permits cancellation).
    fit_tv = .5 * np.sum(np.abs(estimates[:, 6:22] - references[:, 6:22]), axis=1)
    boot_tv = .5 * np.sum(np.abs(boot_estimates[:, :, 6:22] - boot_references[:, :, 6:22]), axis=2)
    pooled_tv = boot_tv[selected_fits, selected_draws].mean(axis=1)
    tv_row = pooled[-1]
    tv_row.update(estimate=_finite(fit_tv.mean()), difference=_finite(fit_tv.mean()),
                  ci95=_ci(pooled_tv), estimate_ci95=_ci(pooled_tv),
                  undefined_bootstrap_draws=int(np.count_nonzero(~np.isfinite(pooled_tv))))
    tv_row["status"] = _status(tv_row["ci95"], .08, sufficient[4], total_variation=True)
    for index, row in enumerate(pooled):
        values = fit_tv if row["metric"] == "tv4" else estimates[:, index] - references[:, index]
        row["fit_difference_range"] = ([float(values.min()), float(values.max())]
                                        if np.all(np.isfinite(values)) else None)
        row["fit_difference_sd"] = (float(np.std(values, ddof=1))
                                     if len(values) > 1 and np.all(np.isfinite(values)) else None)
    return {"dimension": dimension, "count": count, "parent_count": len(rows),
            "fit_count": k, "bootstrap_draws": draws, "fits": reports, "pooled": pooled,
            "local_dimension": _dimension_summary(estimates[:, 0].mean(), pooled_boot_estimate[:, 0]),
            "method": "within-fit sum(B)/sum(A); equal-weight fit means; hierarchical whole-parent and independent reference bootstrap",
            "tv_method": "equal-weight mean of within-fit total variations",
            "minimum_positive_parents_per_fit": min_positive_parents,
            "minimum_intervals_per_fit": min_intervals,
            "intervals_are_independent_units": False,
            "confidence_intervals": "pointwise percentile 95%; undefined resamples are retained"}
