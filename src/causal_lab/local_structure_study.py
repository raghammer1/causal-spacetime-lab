"""Registered local causal structure experiment; no trained classifier.

Run ``python -m causal_lab.local_structure_study --help``. The resource pilot
reports timings only; primary samples have separate parameter-keyed streams.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from pathlib import Path
import platform
import resource
import subprocess
import time

import numpy as np

from .adversarial_generators import (random_interval_order, rank_intersection_order,
                                     uniform_box_order)
from .adversarial_detectors import wilson_interval
from .dimension import invert_ordering_fraction, minkowski_order, sprinkle_minkowski
from .local_generators import (central_slab_order, lexicographic_matched_pair,
                               microcanonical_switch_search)
from .local_random import identity, rng_for
from .local_statistics import build_reference, summarize_conditional
from .local_structure import local_observables, motif_counts


@dataclass(frozen=True)
class StudyConfig:
    seed: int = 20261025
    counts: tuple[int, ...] = (64, 128, 256)
    dimensions: tuple[int, ...] = (2, 3, 4)
    fits: int = 3
    repeats: int = 200
    fiber_repeats: int = 32
    reference4: int = 5000
    reference8: int = 2000
    motif_draws: int = 4096
    bootstrap_draws: int = 2000
    workers: int = 3
    wall_seconds: float = 2700.

    def validate(self):
        for key in ("seed", "fits", "repeats", "fiber_repeats", "reference4",
                    "reference8", "motif_draws", "bootstrap_draws", "workers"):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, int) or value < (0 if key == "seed" else 1):
                raise ValueError(f"invalid {key}")
        if self.motif_draws < 2 or self.bootstrap_draws < 2:
            raise ValueError("at least two sampling/bootstrap draws required")
        if not self.counts or len(set(self.counts)) != len(self.counts) or any(
                isinstance(n, bool) or not isinstance(n, int) or n < 32 or n > 512 or n % 32 for n in self.counts):
            raise ValueError("counts must be unique multiples of 32 in [32,512]")
        if not self.dimensions or len(set(self.dimensions)) != len(self.dimensions) or any(
                d not in (2, 3, 4) for d in self.dimensions):
            raise ValueError("dimensions must be unique members of 2,3,4")
        if not math.isfinite(self.wall_seconds) or self.wall_seconds <= 0:
            raise ValueError("wall_seconds must be positive")
        return self


def _order(family, count, dimension, rng):
    if family == "diamond":
        return minkowski_order(sprinkle_minkowski(dimension, 1., rng, count=count))
    if family == "slab":
        return central_slab_order(count, rng, dimension)
    if family == "box":
        return uniform_box_order(count, rng, dimension)
    if family in ("rank2", "rank3"):
        return rank_intersection_order(count, rng, ranks=int(family[-1]))
    if family == "interval":
        return random_interval_order(count, rng)
    raise ValueError(f"unknown family {family}")


def _dimension(value):
    if value is None:
        return None
    try:
        result = invert_ordering_fraction(value)
    except ValueError:
        return None
    return float(result) if result is not None and math.isfinite(result) else None


def _degree_profile(order):
    pairs = Counter(zip(order.sum(axis=0).tolist(), order.sum(axis=1).tolist()))
    return [[int(p), int(f), int(number)] for (p, f), number in sorted(pairs.items())]


def _record(order, config, fit, family, dimension, count, repeat, *, parameter=None, **extra):
    sample_id = identity(config.seed, fit, "final", family, dimension, count, repeat, parameter)
    row = dict(sample_id=sample_id, fit=fit, family=family, dimension=dimension,
               count=count, repeat=repeat, parameter=parameter, **extra)
    row.update(local_observables(order))
    row["r"] = row["ordering_fraction"]
    row["joint_degree_profile"] = _degree_profile(order)
    row["motifs"] = motif_counts(order, rng_for(config.seed, fit, "motif", family,
                                               dimension, count, repeat, parameter),
                                  draws=config.motif_draws)
    row["global_dimension"] = _dimension(row["r"])
    return row


def _local_changed(a, b):
    # A detected invariant difference proves non-isomorphism. Equality does not.
    fields = ("n22", "chains4", "overlap_sum", "overlap_choose2_sum",
              "interval_component_profile", "interval_m4_motif_counts", "interval_m8_joint")
    return any(a[key] != b[key] for key in fields)


def _run_fit(config, fit):
    start = time.monotonic()
    rows, pairs, searches = [], [], []
    for count in config.counts:
        for dimension in config.dimensions:
            for family in ("diamond", "slab", "box"):
                for repeat in range(config.repeats):
                    rng = rng_for(config.seed, fit, "final", family, dimension, count, repeat)
                    order = _order(family, count, dimension, rng)
                    rows.append(_record(order, config, fit, family, dimension, count, repeat))
        for family, dimension in (("rank2", 2), ("rank3", 0), ("interval", 0)):
            for repeat in range(config.repeats):
                order = _order(family, count, dimension,
                               rng_for(config.seed, fit, "final", family, dimension, count, repeat))
                rows.append(_record(order, config, fit, family, dimension, count, repeat))
        for scaling in ("fixed", "inflated"):
            for repeat in range(config.repeats):
                family = "lex_" + scaling
                pair_id = identity(config.seed, fit, "final", family, 0, count, repeat)
                pair = lexicographic_matched_pair(count, rng_for(config.seed, fit, "final", family,
                                                                0, count, repeat), scaling=scaling)
                first = _record(pair.first_order, config, fit, family + "_connected", 0, count, repeat,
                                pair_id=pair_id, member="first")
                second = _record(pair.second_order, config, fit, family + "_split", 0, count, repeat,
                                 pair_id=pair_id, member="second")
                assert first["joint_degree_profile"] == second["joint_degree_profile"]
                assert first["overlap_sum"] == second["overlap_sum"]
                assert second["n22"] - first["n22"] == pair.metadata["expected_n22_difference"]
                rows.extend((first, second))
                pairs.append(dict(pair_id=pair_id, fit=fit, repeat=repeat,
                                  first_sample_id=first["sample_id"], second_sample_id=second["sample_id"],
                                  **pair.metadata))
        for dimension in config.dimensions:
            for repeat in range(config.fiber_repeats):
                search_id = identity(config.seed, fit, "search", "fiber", dimension, count, repeat)
                donor = _order("diamond", count, dimension,
                               rng_for(config.seed, fit, "final", "fiber_donor", dimension, count, repeat))
                search = microcanonical_switch_search(donor, rng_for(config.seed, fit, "search", "fiber",
                                                                     dimension, count, repeat))
                checkpoint_rows = []
                for checkpoint, order in zip(("initial", "midpoint", "final"),
                                             (search.initial_order, search.midpoint_order, search.final_order)):
                    row = _record(order, config, fit, "fiber_" + checkpoint, dimension, count, repeat,
                                  search_id=search_id, checkpoint=checkpoint)
                    rows.append(row)
                    checkpoint_rows.append(row)
                searches.append(dict(search_id=search_id, fit=fit, dimension=dimension, repeat=repeat,
                                     midpoint_local_changed=_local_changed(*checkpoint_rows[:2]),
                                     final_local_changed=_local_changed(checkpoint_rows[0], checkpoint_rows[2]),
                                     **search.metadata))
        if time.monotonic() - start > config.wall_seconds:
            raise RuntimeError("fit exceeded registered wall budget; partial outcomes must not be substituted")
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if platform.system() != "Darwin":
        peak *= 1024
    return rows, pairs, searches, {"fit": fit, "seconds": time.monotonic() - start,
                                  "peak_rss_bytes": peak}


def _finite(value):
    return float(value) if np.isfinite(value) else None


def _mean_ci(values_by_fit, rng, draws):
    """Equal-fit mean, resampling fits then independent whole parent units."""
    arrays = [np.asarray(values, float) for values in values_by_fit]
    means = [_finite(a.mean()) if len(a) else None for a in arrays]
    if any(value is None for value in means):
        return dict(estimate=None, ci95=None, fit_means=means)
    k = len(arrays)
    boot = np.zeros(draws)
    selected = rng.integers(0, k, (draws, k))
    for slot in range(k):
        for index, array in enumerate(arrays):
            mask = selected[:, slot] == index
            if mask.any():
                boot[mask] += array[rng.integers(0, len(array), (int(mask.sum()), len(array)))].mean(axis=1) / k
    return dict(estimate=float(np.mean(means)), ci95=np.quantile(boot, [.025, .975]).tolist(), fit_means=means)


def _global_values(row):
    n = row["count"]
    disconnected = sum(number for size, components, number in row["interval_component_profile"]
                       if size >= 2 and components > 1)
    nontrivial = sum(number for size, _, number in row["interval_component_profile"] if size >= 2)
    return dict(r=row["r"], chain_fraction=row["chain_fraction"],
                n22_density=row["n22"] / math.comb(n, 4), global_dimension=row["global_dimension"],
                overlap_mean_scaled=None if row["overlap_mean"] is None else row["overlap_mean"] / n,
                overlap_variance_scaled=None if row["overlap_variance"] is None else row["overlap_variance"] / n**2,
                disconnected_interval_fraction=disconnected / nontrivial if nontrivial else None)


def _correlation_report(config, parents, family, dimension, count):
    names = ["r", "chain_fraction", "n22_density", "overlap_mean_scaled", "overlap_variance_scaled",
             "disconnected_interval_fraction", "local_connected2", "local_connected8", "local_n22_8"]
    values = []
    for row in parents:
        value = _global_values(row)
        for key, numerator, denominator in (("local_connected2", row["interval_m2_connected"], row["interval_m2_count"]),
                ("local_connected8", row["interval_m8_connected"], row["interval_m8_count"]),
                ("local_n22_8", row["interval_m8_n22_sum"], 70*row["interval_m8_count"])):
            value[key] = numerator / denominator if denominator else None
        values.append(value)
    data = np.array([[v[key] if v[key] is not None else np.nan for key in names] for v in values])
    complete = data[np.all(np.isfinite(data), axis=1)]
    correlations, covariances = [], []
    for a in range(len(names)):
        corr, cov = [], []
        for b in range(len(names)):
            cov.append(float(np.cov(complete[:, a], complete[:, b], ddof=1)[0, 1]) if len(complete) > 1 else None)
            if len(complete) < 2 or np.ptp(complete[:, a]) == 0 or np.ptp(complete[:, b]) == 0:
                corr.append(None)
            else:
                corr.append(float(np.corrcoef(complete[:, a], complete[:, b])[0, 1]))
        correlations.append(corr)
        covariances.append(cov)
    selected_reports = []
    selected_pairs = (("n22_density", "overlap_variance_scaled"), ("local_connected8", "local_n22_8"))
    for first, second in selected_pairs:
        rng = rng_for(config.seed, 0, "bootstrap", family, dimension, count, 0, ["correlation", first, second])
        pair = data[:, [names.index(first), names.index(second)]]
        good = np.all(np.isfinite(pair), axis=1)
        if good.any():
            # Fixed translation preserves correlation and avoids subtracting
            # nearly equal raw second moments; constant columns become zero.
            pair = pair - pair[good][0]
        groups = [pair[[row["fit"] == fit for row in parents]] for fit in range(config.fits)]
        # Whole-parent bootstrap retains rows missing either value as zero
        # sufficient-statistic contributions, with their complete-case count.
        sufficient = []
        for group in groups:
            good = np.all(np.isfinite(group), axis=1)
            safe = np.where(good[:, None], group, 0.)
            x, y = safe.T
            sufficient.append(np.column_stack((good, x, y, x*x, y*y, x*y)))
        def corr_from_sums(sums):
            number, sx, sy, sx2, sy2, sxy = sums.T
            covariance = number*sxy-sx*sy
            variance = np.maximum(number*sx2-sx*sx, 0.)*np.maximum(number*sy2-sy*sy, 0.)
            result = np.divide(covariance, np.sqrt(variance), out=np.full_like(covariance, np.nan),
                               where=(variance > 0) & (number >= 2))
            return np.clip(result, -1., 1.)  # correct only floating-point range drift
        point = corr_from_sums(np.sum([s.sum(axis=0) for s in sufficient], axis=0)[None, :])[0]
        selected = rng.integers(0, config.fits, (config.bootstrap_draws, config.fits))
        sums = np.zeros((config.bootstrap_draws, 6))
        for slot in range(config.fits):
            for index, stats in enumerate(sufficient):
                mask = selected[:, slot] == index
                if mask.any():
                    weights = rng.multinomial(len(stats), np.full(len(stats), 1/len(stats)), size=int(mask.sum()))
                    sums[mask] += weights @ stats
        boot = corr_from_sums(sums)
        selected_reports.append(dict(first=first, second=second, estimate=_finite(point),
            ci95=np.quantile(boot, [.025, .975]).tolist() if np.all(np.isfinite(boot)) else None,
            undefined_bootstrap_draws=int(np.count_nonzero(~np.isfinite(boot))),
            complete_parents=int(np.all(np.isfinite(pair), axis=1).sum())))
    return dict(family=family, dimension=dimension, count=count, metrics=names,
                matrix=correlations, covariance_matrix=covariances, complete_parents=len(complete),
                selected=selected_reports,
                method="matrices: complete cases across all listed quantities; selected pairs: pairwise complete cases, hierarchical whole-parent bootstrap; descriptive pointwise intervals")


def summarize(config, rows, references, pairs, searches):
    groups = defaultdict(list)
    for row in rows:
        groups[row["family"], row["dimension"], row["count"]].append(row)
    result = {"conditional": [], "global": [], "pairs": [], "searches": [], "correlations": []}
    for (family, dimension, count), parents in sorted(groups.items()):
        for candidate in (config.dimensions if not dimension or family == "rank2" else (dimension,)):
            refs = [ref for ref in references if ref["dimension"] == candidate]
            if not refs:
                continue
            report = summarize_conditional(parents, refs,
                      rng=rng_for(config.seed, 0, "bootstrap", family, candidate, count, 0, "conditional"),
                      bootstrap_draws=config.bootstrap_draws)
            result["conditional"].append(dict(report, family=family, dimension=dimension,
                                                reference_dimension=candidate,
                                                primary=family in ("diamond", "slab") and count == 256))
        metric_rows = []
        values = [_global_values(row) for row in parents]
        for metric in values[0]:
            by_fit = [[v[metric] for row, v in zip(parents, values)
                       if row["fit"] == fit and v[metric] is not None] for fit in range(config.fits)]
            report = _mean_ci(by_fit, rng_for(config.seed, 0, "bootstrap", family, dimension,
                                             count, 0, metric), config.bootstrap_draws)
            metric_rows.append(dict(metric=metric, defined=sum(map(len, by_fit)),
                                    undefined=len(parents) - sum(map(len, by_fit)),
                                    estimand="equal-fit parent mean conditional on a defined value", **report))
        result["global"].append(dict(family=family, dimension=dimension, count=count, metrics=metric_rows))
        result["correlations"].append(_correlation_report(config, parents, family, dimension, count))
    pair_groups = defaultdict(list)
    for pair in pairs:
        pair_groups[pair["scaling"], pair["count"]].append(pair)
    for (scaling, count), group in sorted(pair_groups.items()):
        differences = {p["expected_n22_difference"] for p in group}
        assert len(differences) == 1
        difference = differences.pop()
        result["pairs"].append(dict(scaling=scaling, count=count, pair_count=len(group),
                                    n22_difference=difference, density_difference=difference / math.comb(count, 4),
                                    old_signature_matches=len(group), deterministic_contrast=True))
    search_groups = defaultdict(list)
    for search in searches:
        search_groups[search["dimension"], search["count"]].append(search)
    checkpoints = defaultdict(dict)
    for row in rows:
        if "search_id" in row:
            checkpoints[row["search_id"]][row["checkpoint"]] = row
    def movement(group, key):
        number = sum(search[key] for search in group)
        return dict(count=number, rate=number / len(group), ci95=list(wilson_interval(number, len(group))))
    for (dimension, count), group in sorted(search_groups.items()):
        by_fit = []
        for fit in range(config.fits):
            subset = [s for s in group if s["fit"] == fit]
            by_fit.append(dict(fit=fit, searches=len(subset), moved=movement(subset, "final_matrix_changed"),
                               local_changed=movement(subset, "final_local_changed")))
        changes = []
        for metric in ("n22", "overlap_choose2_sum"):
            fit_values = [[checkpoints[s["search_id"]]["final"][metric] -
                           checkpoints[s["search_id"]]["initial"][metric]
                           for s in group if s["fit"] == fit] for fit in range(config.fits)]
            changes.append(dict(metric=metric, **_mean_ci(fit_values, rng_for(config.seed, 0, "bootstrap",
                                      "fiber_paired", dimension, count, 0, metric), config.bootstrap_draws)))
        result["searches"].append(dict(dimension=dimension, count=count, search_count=len(group),
            steps=count**2 // 64, moved=movement(group, "final_matrix_changed"),
            local_changed=movement(group, "final_local_changed"), by_fit=by_fit,
            paired_changes=changes, outcomes=dict(sum((Counter(s["outcomes"]) for s in group), Counter())),
            pooled_wilson_intervals="descriptive pooled-donor intervals; use by_fit for registered fitwise evidence"))
    return result


def _provenance():
    root = Path(__file__).resolve().parents[2]
    paths = list((root / "src" / "causal_lab").glob("*.py"))
    paths += [p for p in (root / "docs").glob("LOCAL_CAUSAL_STRUCTURE_*.md") if "RESULTS" not in p.name]
    hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    return dict(source_commit=commit, working_tree_dirty=dirty, source_hashes=hashes,
                python=platform.python_version(), numpy=np.__version__, platform=platform.system(),
                machine=platform.machine())


def run_study(config, output):
    config.validate()
    start = time.monotonic()
    references = [build_reference(d, fit, config.seed, m4_count=config.reference4, m8_count=config.reference8)
                  for fit in range(config.fits) for d in config.dimensions]
    reference_seconds = time.monotonic() - start
    print(f"Independent references complete ({reference_seconds:.1f}s)", flush=True)
    if config.workers == 1:
        fit_results = [_run_fit(config, fit) for fit in range(config.fits)]
    else:
        with ProcessPoolExecutor(max_workers=min(config.workers, config.fits)) as executor:
            futures = [executor.submit(_run_fit, config, fit) for fit in range(config.fits)]
            fit_results = []
            for future in futures:
                fit_results.append(future.result())
                print(f"Fit {fit_results[-1][3]['fit']} complete", flush=True)
    rows = [row for result in fit_results for row in result[0]]
    pairs = [row for result in fit_results for row in result[1]]
    searches = [row for result in fit_results for row in result[2]]
    parent_seconds = time.monotonic() - start - reference_seconds
    summary = summarize(config, rows, references, pairs, searches)
    elapsed = time.monotonic() - start
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if platform.system() == "Darwin" else 1024)
    peak_sum = peak + sum(result[3]["peak_rss_bytes"] for result in fit_results)
    metadata = dict(config=asdict(config), **_provenance(), row_count=len(rows), pair_count=len(pairs),
                    search_count=len(searches), reference_seconds=reference_seconds,
                    parent_seconds=parent_seconds, analysis_seconds=elapsed-reference_seconds-parent_seconds,
                    total_seconds=elapsed, fits=[result[3] for result in fit_results],
                    conservative_peak_rss_bytes=peak_sum,
                    resource_limits_satisfied=elapsed <= config.wall_seconds and peak_sum < 4 * 1024**3,
                    sampling_law_comparisons_are_not_embeddability_tests=True)
    from .local_structure_artifacts import write_artifacts
    written = write_artifacts(output, rows, references, summary, pairs, searches, metadata)
    print(json.dumps({key: written[key] for key in ("row_count", "pair_count", "search_count", "scientific_sha256")
                      if key in written}, sort_keys=True), flush=True)
    return written


def resource_pilot(output):
    """Timing-only, at most two parents/region/d/N and two fiber donors/d/N."""
    config = StudyConfig(seed=20261024)
    records = []
    for count in config.counts:
        for dimension in config.dimensions:
            for family in ("diamond", "slab", "box"):
                for repeat in range(2):
                    started = time.monotonic()
                    order = _order(family, count, dimension,
                                   rng_for(config.seed, 0, "pilot", family, dimension, count, repeat))
                    generated = time.monotonic()
                    _record(order, config, 0, family, dimension, count, repeat)
                    records.append(dict(kind="parent", count=count, dimension=dimension, family=family,
                                        generation_seconds=generated-started,
                                        feature_seconds=time.monotonic()-generated))
            for repeat in range(2):
                donor = _order("diamond", count, dimension,
                               rng_for(config.seed, 0, "pilot", "fiber_donor", dimension, count, repeat))
                started = time.monotonic()
                search = microcanonical_switch_search(donor, rng_for(config.seed, 0, "pilot", "fiber",
                                                                     dimension, count, repeat))
                search_seconds = time.monotonic()-started
                started = time.monotonic()
                for matrix in (search.initial_order, search.midpoint_order, search.final_order):
                    _record(matrix, config, 0, "fiber", dimension, count, repeat)
                records.append(dict(kind="search", count=count, dimension=dimension,
                                    search_seconds=search_seconds, checkpoint_seconds=time.monotonic()-started))
        # Bound synthetic extraction cost independently of its scientific outcomes.
        for scaling in ("fixed", "inflated"):
            started = time.monotonic()
            pair = lexicographic_matched_pair(count, rng_for(config.seed, 0, "pilot", "lex", 0, count, 0, scaling),
                                              scaling=scaling)
            for order in (pair.first_order, pair.second_order):
                _record(order, config, 0, "lex", 0, count, 0, parameter=scaling)
            records.append(dict(kind="pair", count=count, scaling=scaling, seconds=time.monotonic()-started))
        for family, dimension in (("rank2", 2), ("rank3", 0), ("interval", 0)):
            started = time.monotonic()
            order = _order(family, count, dimension, rng_for(config.seed, 0, "pilot", family, dimension, count, 0))
            _record(order, config, 0, family, dimension, count, 0)
            records.append(dict(kind="synthetic", count=count, family=family, seconds=time.monotonic()-started))
        print(f"Timing-only pilot N={count} complete", flush=True)
    reference_timings = []
    for dimension in config.dimensions:
        started = time.monotonic()
        build_reference(dimension, 0, config.seed, m4_count=100, m8_count=40)
        reference_timings.append(dict(dimension=dimension, seconds=time.monotonic()-started))
    reference_projection = reference_timings[0]["seconds"] + 3 * 50 * sum(r["seconds"] for r in reference_timings[1:])
    # A conservative analysis allowance is independent of observed outcomes.
    analysis_allowance = 180.
    parent_unit = sum(r["generation_seconds"]+r["feature_seconds"] for r in records if r["kind"] == "parent") / 2
    synthetic_unit = sum(r["seconds"] for r in records if r["kind"] in ("pair", "synthetic"))
    search_unit = sum(r["search_seconds"]+r["checkpoint_seconds"] for r in records if r["kind"] == "search") / 2
    candidates = []
    for repeats in (200, 100, 50):
        for fibers in (32, 16, 8):
            projected = 1.5 * (3 * (repeats*(parent_unit+synthetic_unit)+fibers*search_unit) / 2
                               + reference_projection + analysis_allowance)
            candidates.append(dict(repeats=repeats, fiber_repeats=fibers, projected_seconds=projected,
                                   eligible=projected <= 1800))
    selected = next((row for row in candidates if row["eligible"]), None)
    result = dict(seed=config.seed, purpose="timing-only; no pilot scientific outcomes retained or inspected",
                  timings=records, reference_timings=reference_timings,
                  reference_projection_seconds=reference_projection, analysis_allowance_seconds=analysis_allowance,
                  assumed_parallel_speedup=2., safety_factor=1.5, candidates=candidates, selected=selected,
                  **_provenance())
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output/"resource_pilot.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"selected": selected, "candidates": candidates}, indent=2), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--fiber-repeats", type=int)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    if args.pilot:
        resource_pilot(args.output)
        return
    config = (StudyConfig(counts=(32,), fits=2, repeats=2, fiber_repeats=1,
                          reference4=16, reference8=8, motif_draws=128, bootstrap_draws=32)
              if args.smoke else StudyConfig())
    config = replace(config, workers=args.workers,
                     repeats=args.repeats if args.repeats is not None else config.repeats,
                     fiber_repeats=args.fiber_repeats if args.fiber_repeats is not None else config.fiber_repeats)
    run_study(config, args.output)


if __name__ == "__main__":
    main()
