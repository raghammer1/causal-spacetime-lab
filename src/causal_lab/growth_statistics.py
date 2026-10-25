"""Whole-history statistics for the registered intrinsic-growth experiment.

Birth prefixes and induced thinnings are correlated observations of ONE history.
Seed batches are strata, not a fitted random effect.  No outer batch resampling
is performed.  The finite-signature screen is not a spacetime classifier.
"""
from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

from .growth_random import rng_for
from .local_statistics import (
    METRICS, TOLERANCES, _SIZES, _ci, _dimension_summary,
    _finite, _metric_rows, _parent_arrays, _ratio, _reference_vectors, _status,
)


PREFIXES = (32, 64, 128, 256, 512)
THIN_SOURCES = (128, 256, 512)
CELLS = tuple(("prefix", n, n) for n in PREFIXES) + tuple(
    ("thinned", n, n // 2) for n in THIN_SOURCES)
GLOBAL_METRICS = (
    "ordering_fraction", "height", "height_fraction", "height_sqrt_count",
    "t22", "t31", "global_dimension", "overlap_mean", "overlap_variance",
) + tuple(f"motif4_{i:02d}" for i in range(16))
P22_NAMES = (
    "level_128", "level_256", "level_512", "drift_128_256", "drift_256_512",
    "thin_128_64", "thin_256_128", "thin_512_256",
)
_PAIRS = ((2, 3), (3, 4), (1, 5), (2, 6), (3, 7))


def _integer(value, name, minimum=0):
    if (isinstance(value, (bool, np.bool_))
            or not isinstance(value, (int, np.integer)) or value < minimum):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def _cell(index):
    stage, source, count = CELLS[index]
    return {"cell": f"{stage}_{source}_{count}", "stage": stage,
            "source_count": source, "count": count}


def _global_values(row):
    n = _integer(row["count"], "count", 4)
    height = _integer(row["longest_chain"], "height", 1)
    n22 = _integer(row["n22"], "n22")
    n31 = _integer(row["n31"], "n31")
    if height > n or max(n22, n31) > math.comb(n, 4):
        raise ValueError("global order statistic exceeds its finite range")
    r = float(row["ordering_fraction"])
    if not math.isfinite(r) or not 0 <= r <= 1:
        raise ValueError("ordering fraction must lie in [0,1]")
    motif = row["motifs"]["frequencies"]
    if (len(motif) != 16 or not np.all(np.isfinite(motif))
            or min(motif) < 0 or not math.isclose(sum(motif), 1., abs_tol=1e-10)):
        raise ValueError("sixteen normalized finite global motif frequencies required")
    values = [r, height, height / n, height / math.sqrt(n),
              n22 / math.comb(n, 4), n31 / math.comb(n, 4),
              row.get("global_dimension"), row.get("overlap_mean"),
              row.get("overlap_variance"), *motif]
    array = np.asarray([np.nan if value is None else float(value) for value in values])
    if np.any(np.isinf(array)):
        raise ValueError("undefined diagnostics must be None, not infinity")
    return array


def _clusters(rows):
    """Validate the 17-row grid; collapse thinnings without adding parents."""
    rows = list(rows)
    if not rows:
        raise ValueError("nonempty family rows required")
    family_parameters = {(row["family"], row["parameter"]) for row in rows}
    if len(family_parameters) != 1:
        raise ValueError("summary_per_family requires one family and parameter")
    family, parameter = family_parameters.pop()
    if family not in {"percolation", "minkowski", "semiorder", "matched_bipartite"}:
        raise ValueError("unknown growth-study family")
    if family == "percolation" and float(parameter) in (0., 1.):
        raise ValueError("analytic endpoints are not stochastic history samples")
    if family == "minkowski" and (isinstance(parameter, (bool, np.bool_))
                                  or parameter not in (2, 3, 4)):
        raise ValueError("Minkowski reference dimension must be 2, 3 or 4")
    ids = [row["sample_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate sample IDs")
    grouped = defaultdict(list)
    history_batches = {}
    for row in rows:
        batch = _integer(row["batch"], "batch")
        _integer(row["source_count"], "source_count", 4)
        _integer(row["count"], "count", 4)
        if row["thinning_rep"] is not None:
            replica = _integer(row["thinning_rep"], "thinning_rep")
            if replica > 3:
                raise ValueError("thinning replica must be 0, 1, 2 or 3")
        if "fit" in row and row["fit"] != batch:
            raise ValueError("fit alias must equal batch")
        history = row["history_id"]
        if not isinstance(history, str) or not history:
            raise ValueError("history_id must be a nonempty string")
        if history in history_batches and history_batches[history] != batch:
            raise ValueError("one history cannot belong to two independent batches")
        history_batches[history] = batch
        grouped[(batch, history)].append(row)
    by_batch = defaultdict(list)
    for (batch, history), records in sorted(grouped.items()):
        numbers = {_integer(row["history_number"], "history_number") for row in records}
        if len(numbers) != 1:
            raise ValueError("one history_id has inconsistent history numbers")
        selected = []
        for stage, source, count in CELLS:
            cell = [row for row in records if (row["stage"], row["source_count"], row["count"])
                    == (stage, source, count)]
            replicas = [row["thinning_rep"] for row in cell]
            expected = [None] if stage == "prefix" else [0, 1, 2, 3]
            if (len(cell) != len(expected)
                    or set(replicas) != set(expected)):
                raise ValueError("every history needs five prefixes and four thinnings per source")
            cell.sort(key=lambda row: -1 if row["thinning_rep"] is None else row["thinning_rep"])
            selected.append(cell)
        if len(records) != 17:
            raise ValueError("unexpected history rows outside the registered grid")
        numerator, denominator, exposure = [], [], []
        global_num, global_den = [], []
        for cell in selected:
            b, a, size = _parent_arrays(cell)  # Validate INTEGER raw data first.
            numerator.append(b.mean(axis=0))
            denominator.append(a.mean(axis=0))
            exposure.append(size.mean(axis=0))
            values = np.asarray([_global_values(row) for row in cell])
            finite = np.isfinite(values)
            global_num.append(np.where(finite, values, 0.).mean(axis=0))
            global_den.append(finite.mean(axis=0))
        by_batch[batch].append({
            "history_id": history, "history_number": numbers.pop(),
            "numerator": np.asarray(numerator), "denominator": np.asarray(denominator),
            "exposure": np.asarray(exposure), "global_num": np.asarray(global_num),
            "global_den": np.asarray(global_den),
        })
    result = []
    for batch, histories in sorted(by_batch.items()):
        histories.sort(key=lambda item: item["history_number"])
        if len({item["history_number"] for item in histories}) != len(histories):
            raise ValueError("history numbers must be unique within a batch")
        result.append({"batch": batch, "history_count": len(histories),
                       "history_ids": [item["history_id"] for item in histories],
                       **{key: np.asarray([item[key] for item in histories]) for key in
                          ("numerator", "denominator", "exposure", "global_num", "global_den")}})
    return family, parameter, result


def _weighted(weights, values):
    shape = values.shape[1:]
    return (weights @ values.reshape(len(values), -1)).reshape(len(weights), *shape)


def _scalar(estimate, bootstrap, *, batch_means, support=None):
    result = {"estimate": _finite(float(estimate)), "ci95": _ci(bootstrap),
              "batch_means": [_finite(float(value)) for value in batch_means],
              "undefined_bootstrap_draws": int(np.count_nonzero(~np.isfinite(bootstrap)))}
    if support is not None:
        result["support"] = support
    return result


def _p22_vector(values):
    return np.column_stack((values[:, 2:5] - 1 / 24,
                            values[:, 3] - values[:, 2], values[:, 4] - values[:, 3],
                            values[:, 5] - values[:, 1], values[:, 6] - values[:, 2],
                            values[:, 7] - values[:, 3]))


def _support(batches, cell, min_positive, min_intervals):
    result, enough = {}, {}
    for index, size in enumerate((2, 4, 8)):
        by_batch = []
        for batch in batches:
            values = batch["exposure"][:, cell, index]
            positive = int(np.count_nonzero(values))
            exposure = float(values.sum())
            by_batch.append({"batch": batch["batch"], "fit": batch["batch"],
                             "history_count": len(values), "parent_count": len(values),
                             "positive_histories": positive, "positive_parents": positive,
                             "mean_interval_exposure": exposure, "interval_count": exposure})
        result[size] = {"by_batch": by_batch, "by_fit": by_batch,
                        "history_count": sum(item["history_count"] for item in by_batch),
                        "parent_count": sum(item["parent_count"] for item in by_batch),
                        "positive_histories": sum(item["positive_histories"] for item in by_batch),
                        "positive_parents": sum(item["positive_parents"] for item in by_batch),
                        "mean_interval_exposure": sum(item["mean_interval_exposure"] for item in by_batch),
                        "interval_count": sum(item["interval_count"] for item in by_batch)}
        enough[size] = all(item["positive_histories"] >= min_positive
                           and item["mean_interval_exposure"] >= min_intervals for item in by_batch)
    return result, enough


def _global_report(batches):
    cells, contrasts = [], []
    for cell in range(8):
        metrics = []
        for index, name in enumerate(GLOBAL_METRICS):
            means = np.asarray([batch["global_estimate"][cell, index] for batch in batches])
            boot = np.mean([batch["global_boot"][:, cell, index] for batch in batches], axis=0)
            support = [{"batch": batch["batch"], "history_count": batch["history_count"],
                        "defined_histories": int(np.count_nonzero(batch["global_den"][:, cell, index])),
                        "mean_defined_replica_exposure": float(batch["global_den"][:, cell, index].sum())}
                       for batch in batches]
            metrics.append({"metric": name, **_scalar(means.mean(), boot, batch_means=means,
                                                      support=support)})
        cells.append({**_cell(cell), "metrics": metrics})
    for left, right in _PAIRS:
        metrics = []
        for index, name in enumerate(GLOBAL_METRICS):
            means, boots, supports = [], [], []
            for batch in batches:
                # Prefix denominator is 0 or 1.  A partly defined thinning has
                # its original mean replica exposure, never four new histories.
                prefix = _ratio(batch["global_num"][:, left, index], batch["global_den"][:, left, index])
                den = batch["global_den"][:, right, index] * batch["global_den"][:, left, index]
                num = np.where(den > 0, batch["global_num"][:, right, index]
                               - batch["global_den"][:, right, index] * prefix, 0.)
                means.append(_ratio(np.asarray(num.sum()), np.asarray(den.sum())))
                boots.append(_ratio(batch["weights"] @ num, batch["weights"] @ den))
                supports.append({"batch": batch["batch"], "history_count": len(num),
                                 "paired_defined_histories": int(np.count_nonzero(den)),
                                 "mean_defined_replica_exposure": float(den.sum())})
            metrics.append({"metric": name, **_scalar(np.mean(means), np.mean(boots, axis=0),
                                                      batch_means=means, support=supports)})
        contrasts.append({"left": _cell(left), "right": _cell(right),
                          "direction": "right minus left", "metrics": metrics})
    return cells, contrasts


def _conditional_report(batches, references, dimension, seed, draws, min_positive, min_intervals):
    reference_map = {ref["fit"]: ref for ref in references if ref["dimension"] == dimension}
    if set(reference_map) != {batch["batch"] for batch in batches}:
        raise ValueError("one reference fit per history batch and candidate dimension required")
    for batch in batches:
        rng = rng_for(seed, batch["batch"], "bootstrap_reference", "reference", dimension, 0)
        ref, refboot = _reference_vectors(reference_map[batch["batch"]], rng, draws)
        batch["reference"], batch["reference_boot"] = ref, refboot
    cells, contrasts = [], []
    for cell in range(8):
        support, sufficient = _support(batches, cell, min_positive, min_intervals)
        estimates = np.asarray([batch["estimate"][cell] for batch in batches])
        boot_estimates = np.asarray([batch["boot_estimate"][:, cell] for batch in batches])
        refs = np.asarray([batch["reference"] for batch in batches])
        refboots = np.asarray([batch["reference_boot"] for batch in batches])
        pairs = math.comb(CELLS[cell][2], 2)
        centered, centered_boot = [], []
        fit_reports = []
        for j, batch in enumerate(batches):
            b, a = batch["numerator"][:, cell], batch["denominator"][:, cell]
            center = np.mean(b - a * refs[j], axis=0) / pairs
            bootcenter = (batch["boot_numerator"][:, cell]
                          - batch["boot_denominator"][:, cell] * refboots[j]) / (len(b) * pairs)
            centered.append(center)
            centered_boot.append(bootcenter)
            fit_support = {m: support[m]["by_batch"][j] for m in (2, 4, 8)}
            fit_sufficient = {m: fit_support[m]["positive_histories"] >= min_positive
                              and fit_support[m]["mean_interval_exposure"] >= min_intervals
                              for m in (2, 4, 8)}
            fit_reports.append({"batch": batch["batch"], "fit": batch["batch"],
                                "metrics": _metric_rows(estimates[j], refs[j], boot_estimates[j],
                                                        refboots[j], fit_support, center, bootcenter,
                                                        fit_sufficient),
                                "local_dimension": _dimension_summary(estimates[j, 0], boot_estimates[j, :, 0])})
        pooled_boot = boot_estimates.mean(axis=0)
        pooled = _metric_rows(estimates.mean(axis=0), refs.mean(axis=0), pooled_boot,
                              refboots.mean(axis=0), support, np.mean(centered, axis=0),
                              np.mean(centered_boot, axis=0), sufficient)
        tv = .5 * np.sum(np.abs(estimates[:, 6:22] - refs[:, 6:22]), axis=1)
        tv_boot = (.5 * np.sum(np.abs(boot_estimates[:, :, 6:22] - refboots[:, :, 6:22]), axis=2)).mean(axis=0)
        pooled[-1].update(estimate=_finite(float(tv.mean())), difference=_finite(float(tv.mean())),
                          ci95=_ci(tv_boot), estimate_ci95=_ci(tv_boot),
                          undefined_bootstrap_draws=int(np.count_nonzero(~np.isfinite(tv_boot))))
        pooled[-1]["status"] = _status(pooled[-1]["ci95"], .08, sufficient[4], total_variation=True)
        for index, row in enumerate(pooled):
            values = tv if row["metric"] == "tv4" else estimates[:, index] - refs[:, index]
            row["batch_difference_means"] = [_finite(float(value)) for value in values]
        cells.append({**_cell(cell), "dimension": dimension, "fits": fit_reports,
                      "pooled": pooled, "local_dimension": _dimension_summary(
                          float(estimates[:, 0].mean()), pooled_boot[:, 0]),
                      "confidence_intervals": "pointwise percentile 95%; undefined replicates retained",
                      "tv_method": "mean of batchwise TVs; nonsmooth bootstrap coverage at zero unproved"})
    # Conditional-probability contrasts use their shared history weights.  The
    # identical calibration law cancels exactly and is not bootstrapped twice.
    for left, right in _PAIRS[2:]:
        support_left, sufficient_left = _support(batches, left, min_positive, min_intervals)
        support_right, sufficient_right = _support(batches, right, min_positive, min_intervals)
        means = np.asarray([batch["estimate"][right, :6] - batch["estimate"][left, :6]
                            for batch in batches])
        boot = np.mean([batch["boot_estimate"][:, right, :6] - batch["boot_estimate"][:, left, :6]
                        for batch in batches], axis=0)
        metrics = []
        for index, name in enumerate(METRICS):
            size = int(_SIZES[index])
            value = _scalar(means[:, index].mean(), boot[:, index], batch_means=means[:, index])
            value.update(metric=name, interval_size=size, difference=value["estimate"],
                         tolerance=TOLERANCES[name], support={"left": support_left[size], "right": support_right[size]},
                         status=_status(value["ci95"], TOLERANCES[name],
                                        sufficient_left[size] and sufficient_right[size]))
            metrics.append(value)
        contrasts.append({"left": _cell(left), "right": _cell(right), "dimension": dimension,
                          "direction": "thinned minus matched prefix", "reference_cancels": True,
                          "metrics": metrics})
    return cells, contrasts


def summary_per_family(rows, references, *, seed, bootstrap_draws=2000,
                       min_positive_histories=30, min_interval_exposure=100):
    """Return ``(JSON-safe report, private NumPy primary-screen bundle)``.

    ``references`` contains the independently fitted local-reference dictionaries.
    Only a Minkowski control's supplied dimension is used to select its reference;
    every other family is reported against all three candidate dimensions.
    """
    seed = _integer(seed, "seed")
    draws = _integer(bootstrap_draws, "bootstrap_draws", 2)
    min_positive = _integer(min_positive_histories, "min_positive_histories", 1)
    min_intervals = _integer(min_interval_exposure, "min_interval_exposure", 1)
    family, parameter, batches = _clusters(rows)
    references = list(references)
    ref_keys = [(ref["fit"], ref["dimension"]) for ref in references]
    if len(ref_keys) != len(set(ref_keys)):
        raise ValueError("duplicate reference fits")
    for batch in batches:
        n = batch["history_count"]
        rng = rng_for(seed, batch["batch"], "bootstrap_history", family, parameter, 0)
        batch["weights"] = rng.multinomial(n, np.full(n, 1 / n), size=draws)
        batch["global_estimate"] = _ratio(batch["global_num"].sum(axis=0), batch["global_den"].sum(axis=0))
        batch["global_boot"] = _ratio(_weighted(batch["weights"], batch["global_num"]),
                                      _weighted(batch["weights"], batch["global_den"]))
        batch["estimate"] = _ratio(batch["numerator"].sum(axis=0), batch["denominator"].sum(axis=0))
        batch["boot_numerator"] = _weighted(batch["weights"], batch["numerator"])
        batch["boot_denominator"] = _weighted(batch["weights"], batch["denominator"])
        batch["boot_estimate"] = _ratio(batch["boot_numerator"], batch["boot_denominator"])
        # t22 has no missing values and no motif Monte Carlo approximation.
        batch["p22_observations"] = _p22_vector(batch["global_num"][:, :, 4])
        batch["p22_mean"] = batch["p22_observations"].mean(axis=0)
        batch["p22_boot"] = batch["weights"] @ batch["p22_observations"] / n
    global_cells, global_contrasts = _global_report(batches)
    conditional_cells, conditional_contrasts = [], []
    dimensions = (int(parameter),) if family == "minkowski" else (2, 3, 4)
    if any(d not in (2, 3, 4) for d in dimensions):
        raise ValueError("Minkowski reference dimension must be 2, 3 or 4")
    for dimension in dimensions:
        cells, contrasts = _conditional_report(batches, references, dimension, seed, draws,
                                               min_positive, min_intervals)
        conditional_cells.extend(cells)
        conditional_contrasts.extend(contrasts)
    batch_means = np.asarray([batch["p22_mean"] for batch in batches])
    estimate = batch_means.mean(axis=0)
    bootstrap = np.mean([batch["p22_boot"] for batch in batches], axis=0)
    observations = np.concatenate([batch["p22_observations"] for batch in batches])
    p22 = [{"name": name, "kind": "level" if index < 3 else "contrast",
            "margin": .005, "reference": 1 / 24 if index < 3 else 0.,
            "constant_observed_sample": bool(np.ptp(observations[:, index]) == 0),
            **_scalar(estimate[index], bootstrap[:, index], batch_means=batch_means[:, index])}
           for index, name in enumerate(P22_NAMES)]
    report = {"family": family, "parameter": parameter, "bootstrap_draws": draws,
              "batch_count": len(batches), "history_count": len(observations),
              "batches": [{"batch": batch["batch"], "history_count": batch["history_count"]}
                          for batch in batches],
              "global_cells": global_cells, "global_contrasts": global_contrasts,
              "conditional_cells": conditional_cells, "conditional_contrasts": conditional_contrasts,
              "p22_vector": p22, "minimum_positive_histories_per_batch": min_positive,
              "minimum_mean_interval_exposure_per_batch": min_intervals,
              "method": "whole-history stratified bootstrap; equal batch means; no outer batch resampling",
              "conditional_method": "within-batch sum(B)/sum(A); four thinnings averaged before pooling",
              "dimension_interpretation": "reference-equivalent diagnostics, not physical dimensions",
              "independent_units": "histories; prefixes, intervals and thinning replicas are dependent"}
    bundle = {"family": family, "parameter": parameter, "estimate": estimate,
              "bootstrap": bootstrap, "observations": observations, "batch_means": batch_means}
    return report, bundle


def summarize_primary(family_results, *, bootstrap_draws=2000):
    """Simultaneous registered bands for six p families or one control family.

    Max-centered bootstrap bands use the 97.5th percentile.  A separate .025
    error allocation covers zero-event safeguards.  Coverage of the bootstrap
    portion remains approximate; constant stochastic samples never imply certainty.
    """
    draws = _integer(bootstrap_draws, "bootstrap_draws", 2)
    results = list(family_results)
    if not results:
        raise ValueError("at least one family bootstrap bundle required")
    keys = [(item["family"], item["parameter"]) for item in results]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate primary families")
    for item in results:
        if (np.shape(item["estimate"]) != (8,) or np.shape(item["bootstrap"]) != (draws, 8)
                or np.ndim(item["observations"]) != 2 or np.shape(item["observations"])[1] != 8
                or not len(item["observations"])):
            raise ValueError("invalid primary bootstrap bundle dimensions")
        if not all(np.all(np.isfinite(item[key])) for key in ("estimate", "bootstrap", "observations")):
            raise ValueError("primary exact-motif observations must be finite")
    estimate = np.concatenate([item["estimate"] for item in results])
    boot = np.concatenate([item["bootstrap"] for item in results], axis=1)
    width = float(np.quantile(np.max(np.abs(boot - estimate), axis=1), .975, method="linear"))
    entries = 8 * len(results)
    alpha = .025 / entries
    families = []
    for item in results:
        rows = []
        observations = item["observations"]
        q0 = -math.expm1(math.log(alpha) / len(observations))
        for index, name in enumerate(P22_NAMES):
            mean = float(item["estimate"][index])
            values = observations[:, index]
            band = [mean - width, mean + width]
            guard = None
            constant = bool(np.ptp(values) == 0)
            if constant:
                target = 1 / 24 if index < 3 else 0.
                if np.all(values == -target):
                    known = [-target, q0 - target] if index < 3 else [-q0, q0]
                    band = [min(band[0], known[0]), max(band[1], known[1])]
                    guard = "zero-density rare-event bound" if index < 3 else "zero-contrast rare-event bound"
                else:
                    band = [-1 / 24, 1 - 1 / 24] if index < 3 else [-1., 1.]
                    guard = "other constant stochastic sample: full known range"
            status = _status(band, .005, True)
            rows.append({"name": name, "estimate": mean, "band": band, "margin": .005,
                         "pointwise_ci95": _ci(item["bootstrap"][:, index]), "status": status,
                         "batch_means": [float(value) for value in item["batch_means"][:, index]],
                         "constant_observed_sample": constant, "degeneracy_guard": guard,
                         "zero_event_upper_bound": q0 if guard and guard.startswith("zero") else None,
                         "independent_history_count": len(observations)})
        statuses = [row["status"] for row in rows]
        overall = ("finite_window_compatible" if all(status == "equivalent" for status in statuses)
                   else "finite_signature_failure" if "contradicts" in statuses else "inconclusive")
        families.append({"family": item["family"], "parameter": item["parameter"],
                         "status": overall, "entries": rows})
    return {"entry_count": entries, "bootstrap_draws": draws, "max_centered_quantile": .975,
            "common_half_width": width, "zero_guard_total_alpha": .025,
            "zero_guard_alpha_per_entry": alpha, "families": families,
            "coverage": "approximate simultaneous bootstrap bands plus registered zero-event safeguards",
            "interpretation": "necessary finite signature only; fixed-p continuum obstruction remains"}
