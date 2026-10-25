"""Whole histories, shared calibration and degeneracy safeguards, not classifiers."""
from copy import deepcopy
import json
import math

import numpy as np
import pytest

from causal_lab.growth_random import rng_for
from causal_lab.growth_statistics import (
    CELLS, P22_NAMES, summary_per_family, summarize_primary,
)
from causal_lab.local_statistics import build_reference


@pytest.fixture(scope="module")
def refs():
    return [build_reference(3, batch, 8021, m4_count=47, m8_count=31)
            for batch in range(3)]


def records(sizes=(3, 3, 3), *, sparse=False):
    rows = []
    for batch, histories in enumerate(sizes):
        for history in range(histories):
            density = (history % 2) / 2
            a2 = history + 1
            b2 = history
            if sparse:
                a2 = int(history == 0)
                b2 = a2
            for stage, source, count in CELLS:
                for replica in ([None] if stage == "prefix" else range(4)):
                    motifs = [0] * 16
                    motifs[history % 2] = 2
                    rows.append({
                        "family": "minkowski", "parameter": 3, "batch": batch, "fit": batch,
                        "history_id": f"history-{batch}-{history}", "history_number": history,
                        "stage": stage, "source_count": source, "count": count,
                        "thinning_rep": replica, "sample_id": f"{batch}-{history}-{stage}-{source}-{replica}",
                        "ordering_fraction": .2 + .1 * history, "longest_chain": history + 1,
                        "n22": int(density * math.comb(count, 4)), "n31": 0,
                        "global_dimension": None if history == 0 else 2. + history,
                        "overlap_mean": None, "overlap_variance": None,
                        "motifs": {"frequencies": [1.] + [0.] * 15},
                        "interval_m2_count": a2, "interval_m2_connected": b2,
                        "interval_m4_count": 2, "interval_m4_motif_counts": motifs,
                        "interval_m8_count": 1, "interval_m8_connected": history % 2,
                        "interval_m8_n22_sum": 0, "interval_m8_connected_n22_sum": 0,
                    })
    return rows


def summarize(rows, refs, **kwargs):
    return summary_per_family(rows, refs, seed=123, bootstrap_draws=80,
                              min_positive_histories=1, min_interval_exposure=1, **kwargs)


def metric(report, name, *, cell=0, conditional=False):
    section = report["conditional_cells"] if conditional else report["global_cells"]
    entries = section[cell]["pooled"] if conditional else section[cell]["metrics"]
    return next(item for item in entries if item["metric"] == name)


def test_one_history_weight_is_shared_by_prefixes_and_cloned_thinnings(refs):
    report, bundle = summarize(records(), refs)
    assert report["history_count"] == 9
    assert len(report["global_cells"]) == 8
    assert len(report["global_contrasts"]) == 5
    assert len(report["conditional_contrasts"]) == 3
    assert np.array_equal(bundle["bootstrap"][:, 3:], np.zeros((80, 5)))
    assert np.array_equal(bundle["observations"][:, 3:], np.zeros((9, 5)))
    # Four identical thinning replicas preserve the matched prefix uncertainty.
    for name in ("t22", "height", "global_dimension"):
        assert metric(report, name, cell=1)["ci95"] == metric(report, name, cell=5)["ci95"]
    for contrast in report["conditional_contrasts"]:
        for row in contrast["metrics"]:
            assert row["estimate"] == 0
            assert row["ci95"] == [0., 0.]
        assert contrast["reference_cancels"] is True


def test_bootstrap_is_stratified_by_independent_batches_without_outer_resampling(refs):
    rows = records((2, 3, 4))
    report, bundle = summarize(rows, refs)
    expected = []
    for batch, n in enumerate((2, 3, 4)):
        weights = rng_for(123, batch, "bootstrap_history", "minkowski", 3, 0).multinomial(
            n, np.full(n, 1 / n), size=80)
        density = (np.arange(n) % 2) / 2
        expected.append(weights @ (density - 1 / 24) / n)
    assert np.allclose(bundle["bootstrap"][:, 0], np.mean(expected, axis=0), atol=1e-15)
    assert bundle["estimate"][0] == pytest.approx(np.mean([.25, 1 / 6, .25]) - 1 / 24)
    assert report["batch_count"] == 3
    assert "no outer batch" in report["method"]


def test_integer_thinning_counts_are_averaged_before_pooling_and_support(refs):
    rows = records()
    for row in rows:
        if row["stage"] == "thinned" and row["source_count"] == 128:
            row["interval_m2_count"] = int(row["thinning_rep"] == 0)
            row["interval_m2_connected"] = row["interval_m2_count"]
    report, _ = summarize(rows, refs)
    result = metric(report, "connected2", cell=5, conditional=True)
    assert result["estimate"] == 1
    support = result["support"]
    assert support["history_count"] == 9
    assert support["positive_histories"] == 9
    assert support["mean_interval_exposure"] == 9 / 4
    assert all(item["mean_interval_exposure"] == 3 / 4 for item in support["by_batch"])
    assert result["status"] == "insufficient_information"


def test_pooled_counts_are_not_mean_parent_ratios_and_inverse_is_reference_free(refs):
    rows = records((2, 2, 2))
    for row in rows:
        row["interval_m2_count"] = 1 if row["history_number"] == 0 else 9
        row["interval_m2_connected"] = int(row["history_number"] == 0)
    report, _ = summarize(rows, refs)
    result = metric(report, "connected2", conditional=True)
    assert result["estimate"] == pytest.approx(.1)
    # Candidate reference is d3; the inversion of .1 nevertheless gives d4.
    dimension = report["conditional_cells"][0]["local_dimension"]
    assert dimension["estimate"] == pytest.approx(4)
    assert dimension["uses_true_dimension"] is False


def test_missing_resamples_are_retained_and_dimensions_remain_missing(refs):
    report, _ = summarize(records(sparse=True), refs)
    result = metric(report, "connected2", conditional=True)
    assert result["undefined_bootstrap_draws"] > 0
    assert result["ci95"] is None
    dim = metric(report, "global_dimension")
    assert dim["estimate"] == pytest.approx(3.5)
    assert all(s["defined_histories"] == 2 for s in dim["support"])
    rows = records()
    for row in rows:
        row["global_dimension"] = None
        row["interval_m2_count"] = 0
        row["interval_m2_connected"] = 0
    report, _ = summarize(rows, refs)
    assert metric(report, "global_dimension")["estimate"] is None
    assert report["conditional_cells"][0]["local_dimension"]["status"] == "undefined"
    assert metric(report, "connected2", conditional=True)["status"] == "insufficient_information"


def test_conditional_contrast_calibration_cancels_and_shared_reference_is_replayed(refs):
    rows = records()
    for row in rows:
        if row["stage"] == "thinned":
            row["interval_m4_motif_counts"] = [0, 0, 2] + [0] * 13
    one, _ = summarize(rows, refs)
    replacement = [build_reference(3, batch, 8191, m4_count=47, m8_count=31) for batch in range(3)]
    two, _ = summarize(rows, replacement)
    assert one["conditional_contrasts"] == two["conditional_contrasts"]
    # Same reference is shared across cells: its reported uncertainty is equal.
    for name in ("motif22_4", "connected4", "connected8", "joint8"):
        a = metric(one, name, cell=0, conditional=True)
        b = metric(one, name, cell=5, conditional=True)
        assert a["reference"] == b["reference"]
        assert a["reference_ci95"] == b["reference_ci95"]
    repeat, _ = summarize(rows, refs)
    assert one == repeat


def test_changing_one_calibration_fit_leaves_other_fit_estimates_and_intervals_unchanged(refs):
    one, _ = summarize(records(), refs)
    replacement = [*refs[:2], build_reference(3, 2, 9231, m4_count=47, m8_count=31)]
    two, _ = summarize(records(), replacement)
    for left, right in zip(one["conditional_cells"], two["conditional_cells"]):
        assert left["fits"][:2] == right["fits"][:2]
        assert left["local_dimension"] == right["local_dimension"]
    assert one["conditional_cells"][0]["fits"][2] != two["conditional_cells"][0]["fits"][2]
    assert one["conditional_contrasts"] == two["conditional_contrasts"]


def test_input_record_order_does_not_change_the_joint_bootstrap(refs):
    rows = records()
    first, bundle = summarize(rows, refs)
    second, repeated = summarize(list(reversed(rows)), list(reversed(refs)))
    assert first == second
    assert np.array_equal(bundle["bootstrap"], repeated["bootstrap"])


def test_local_dimension_zero_probability_is_out_of_domain_not_clipped(refs):
    rows = records()
    for row in rows:
        row["interval_m2_count"] = 1
        row["interval_m2_connected"] = 0
    report, _ = summarize(rows, refs)
    dimension = report["conditional_cells"][0]["local_dimension"]
    assert dimension["probability"] == 0
    assert dimension["estimate"] is None
    assert dimension["status"] == "out_of_domain"


def test_tv_is_mean_of_batchwise_values_and_report_is_json_safe(refs):
    rows = records()
    for row in rows:
        counts = [0] * 16
        counts[(row["batch"] * 5) % 16] = 2
        row["interval_m4_motif_counts"] = counts
    report, _ = summarize(rows, refs)
    tv = metric(report, "tv4", conditional=True)
    fits = report["conditional_cells"][0]["fits"]
    fit_tv = [next(m["estimate"] for m in fit["metrics"] if m["metric"] == "tv4") for fit in fits]
    assert tv["estimate"] == pytest.approx(np.mean(fit_tv))
    json.dumps(report, allow_nan=False)


def _bundle(parameter=.01, histories=192, draws=80, value=0.):
    raw = np.zeros((histories, 8))
    raw[:, :3] = value - 1 / 24
    return {"family": "percolation", "parameter": parameter,
            "estimate": raw.mean(axis=0), "bootstrap": np.tile(raw.mean(axis=0), (draws, 1)),
            "observations": raw, "batch_means": np.tile(raw.mean(axis=0), (3, 1))}


def test_zero_density_and_zero_contrast_guards_use_the_registered_48_entry_budget():
    bundles = [_bundle(p) for p in (.005, .01, .02, .05, .1, .3)]
    result = summarize_primary(bundles, bootstrap_draws=80)
    assert result["entry_count"] == 48
    expected = 1 - (.025 / 48) ** (1 / 192)
    levels = result["families"][0]["entries"]
    assert levels[0]["band"][1] == pytest.approx(expected - 1 / 24)
    assert levels[3]["band"] == pytest.approx([-expected, expected])
    assert levels[0]["zero_event_upper_bound"] == pytest.approx(expected)
    assert levels[3]["status"] == "inconclusive"
    assert result["families"][0]["status"] != "finite_window_compatible"
    json.dumps(result, allow_nan=False)


def test_control_band_has_separate_eight_entry_budget_and_constants_are_not_certain():
    bundle = _bundle(value=.02)
    bundle["family"] = "matched_bipartite"
    bundle["parameter"] = .38
    result = summarize_primary([bundle], bootstrap_draws=80)
    assert result["entry_count"] == 8
    assert result["zero_guard_alpha_per_entry"] == .025 / 8
    entry = result["families"][0]["entries"][0]
    assert entry["band"] == [-1 / 24, 1 - 1 / 24]
    assert entry["status"] == "inconclusive"
    assert "full known range" in entry["degeneracy_guard"]
    bundle["observations"][:, 3] = .1
    bundle["estimate"][3] = .1
    bundle["bootstrap"][:, 3] = .1
    bundle["batch_means"][:, 3] = .1
    guarded = summarize_primary([bundle], bootstrap_draws=80)["families"][0]["entries"][3]
    assert guarded["band"] == [-1., 1.]
    assert guarded["status"] == "inconclusive"


def test_max_centered_band_uses_all_entries_and_preserves_pairing():
    bundle = _bundle(histories=2, draws=4)
    observations = np.array([[-.01] * 8, [.01] * 8])
    bundle.update(observations=observations, estimate=np.zeros(8), batch_means=np.zeros((3, 8)))
    boot = np.zeros((4, 8))
    boot[:, -1] = [.001, .002, .003, .004]
    bundle["bootstrap"] = boot
    result = summarize_primary([bundle], bootstrap_draws=4)
    width = np.quantile([.001, .002, .003, .004], .975)
    assert result["common_half_width"] == width
    assert all(item["band"] == [-width, width] for item in result["families"][0]["entries"])


@pytest.mark.parametrize("damage", ["duplicate", "missing", "replica", "fractional", "history_batch", "fit"])
def test_malformed_history_units_are_rejected(refs, damage):
    rows = records()
    if damage == "duplicate":
        rows.append(deepcopy(rows[0]))
    elif damage == "missing":
        rows.pop()
    elif damage == "replica":
        next(row for row in rows if row["thinning_rep"] == 3)["thinning_rep"] = 2
    elif damage == "fractional":
        rows[0]["interval_m2_count"] = .5
    elif damage == "history_batch":
        for row in rows:
            if row["batch"] == 1:
                row["history_id"] = "history-0-0"
    else:
        rows[0]["fit"] = 10
    with pytest.raises(ValueError):
        summarize(rows, refs)


def test_default_support_is_not_relaxed_for_small_workload(refs):
    report, _ = summary_per_family(records(), refs, seed=123, bootstrap_draws=10)
    assert report["minimum_positive_histories_per_batch"] == 30
    assert report["minimum_mean_interval_exposure_per_batch"] == 100
    assert all(row["status"] == "insufficient_information"
               for cell in report["conditional_cells"] for row in cell["pooled"])


def test_declared_eight_comparisons_are_stable():
    assert P22_NAMES == ("level_128", "level_256", "level_512", "drift_128_256",
                         "drift_256_512", "thin_128_64", "thin_256_128", "thin_512_256")
