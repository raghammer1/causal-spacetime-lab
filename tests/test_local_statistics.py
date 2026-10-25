"""Independent anchors and statistical-unit checks for conditional local laws."""
from copy import deepcopy
import math

import numpy as np
import pytest

from causal_lab.dimension import ordering_probability
from causal_lab.local_statistics import (
    build_reference, connected_permutation_count, summarize_conditional,
)
from causal_lab.local_structure import motif_catalog


@pytest.fixture(scope="module")
def exact_reference():
    return build_reference(2, 0, 20261025)


@pytest.fixture(scope="module")
def stochastic_reference():
    return build_reference(3, 0, 20261025, m4_count=61, m8_count=37)


def parent(fit=0, *, count=16, a2=10, b2=5, a4=0, motif_id=0,
           a8=0, b8=0, n22=0, joint22=0):
    motifs = [0] * 16
    motifs[motif_id] = a4
    return {"fit": fit, "count": count, "interval_m2_count": a2,
            "interval_m2_connected": b2, "interval_m4_count": a4,
            "interval_m4_motif_counts": motifs, "interval_m8_count": a8,
            "interval_m8_connected": b8, "interval_m8_n22_sum": n22,
            "interval_m8_connected_n22_sum": joint22}


def summary(rows, refs, **kwargs):
    return summarize_conditional(rows, refs, rng=np.random.default_rng(7),
                                 bootstrap_draws=150, min_positive_parents=1,
                                 min_intervals=1, **kwargs)


def metric(report, name, fit=None):
    rows = report["pooled"] if fit is None else report["fits"][fit]["metrics"]
    return next(row for row in rows if row["metric"] == name)


def test_exact_reference_matches_independent_analytic_anchors(exact_reference):
    catalog = motif_catalog()
    counts4 = exact_reference["m4"]["counts"]
    assert sum(counts4) == math.factorial(4)
    assert sum(counts4[i] * entry["n22"] for i, entry in enumerate(catalog)) == 1
    assert sum(counts4[i] for i, entry in enumerate(catalog) if entry["components"] == 1) == 13
    table8 = exact_reference["m8"]["joint_counts"]
    assert sum(row[2] for row in table8) == math.factorial(8)
    assert sum(c * number for c, _, number in table8) == 29093
    assert sum(n22 * number for _, n22, number in table8) * 24 == 70 * math.factorial(8)
    assert exact_reference["m8"]["outcomes"] is None
    assert exact_reference["exact"] is True


@pytest.mark.parametrize("n,expected", [(1, 1), (2, 1), (3, 3), (4, 13),
                                       (5, 71), (6, 461), (7, 3447), (8, 29093)])
def test_connected_permutation_recurrence(n, expected):
    assert connected_permutation_count(n) == expected


def test_reference_seed_replay_and_independent_fit(stochastic_reference):
    assert stochastic_reference == build_reference(3, 0, 20261025, m4_count=61, m8_count=37)
    other = build_reference(3, 1, 20261025, m4_count=61, m8_count=37)
    assert other["m4"]["outcomes"] != stochastic_reference["m4"]["outcomes"]
    assert other["m8"]["outcomes"] != stochastic_reference["m8"]["outcomes"]
    assert len(stochastic_reference["m4"]["outcomes"]) == 61
    assert len(stochastic_reference["m8"]["outcomes"]) == 37
    assert stochastic_reference["connected2"] == ordering_probability(3)


def test_within_fit_estimator_pools_counts_and_inversion_ignores_reference_dimension(exact_reference):
    report = summary([parent(a2=1, b2=1), parent(a2=9, b2=0)], [exact_reference])
    result = metric(report, "connected2")
    assert result["estimate"] == .1  # Not the mean of the ratios, which is .5.
    assert result["difference"] == -.4
    assert result["mean_centered_count_per_pair"] == pytest.approx(-2 / math.comb(16, 2))
    assert report["local_dimension"]["estimate"] == pytest.approx(4)
    assert report["local_dimension"]["uses_true_dimension"] is False


def test_across_fits_have_equal_weight(exact_reference):
    other = deepcopy(exact_reference)
    other["fit"] = 1
    report = summary([parent(0, a2=1, b2=1), parent(1, a2=9, b2=0)],
                     [exact_reference, other])
    assert metric(report, "connected2")["estimate"] == .5
    assert metric(report, "connected2")["difference"] == 0
    assert metric(report, "connected2")["fit_difference_range"] == [-.5, .5]


def test_tv_does_not_cancel_across_fits(exact_reference):
    catalog = motif_catalog()
    anti = next(entry["id"] for entry in catalog if entry["relations"] == 0)
    chain = next(entry["id"] for entry in catalog if entry["relations"] == 6)
    other = deepcopy(exact_reference)
    other["fit"] = 1
    report = summary([parent(0, a4=100, motif_id=anti), parent(1, a4=100, motif_id=chain)],
                     [exact_reference, other])
    fit_mean = np.mean([metric(report, "tv4", fit=i)["estimate"] for i in (0, 1)])
    assert metric(report, "tv4")["estimate"] == fit_mean
    profile = np.zeros(16)
    profile[anti] = profile[chain] = .5
    tv_of_mean = .5 * np.abs(profile - np.asarray(exact_reference["m4"]["counts"]) / 24).sum()
    assert fit_mean > tv_of_mean


def test_zero_interval_parents_are_retained(exact_reference):
    rows = [parent(a2=0, b2=0), parent(a2=0, b2=0)]
    report = summary(rows, [exact_reference])
    result = metric(report, "connected2")
    assert result["estimate"] is None and result["ci95"] is None
    assert result["status"] == "insufficient_information"
    assert result["support"]["parent_count"] == 2
    assert result["undefined_bootstrap_draws"] == 150
    assert result["mean_centered_count_per_pair"] == 0
    assert result["centered_ci95"] == [0., 0.]
    assert report["local_dimension"]["status"] == "undefined"


def test_sparse_resamples_are_not_dropped(exact_reference):
    report = summary([parent(a2=0, b2=0), parent(a2=1, b2=1)], [exact_reference])
    result = metric(report, "connected2", fit=0)
    assert result["estimate"] == 1
    assert result["undefined_bootstrap_draws"] > 0
    assert result["ci95"] is None
    assert result["status"] == "inconclusive"


def test_whole_parent_uncertainty_is_not_independent_interval_uncertainty(exact_reference):
    report = summary([parent(count=256, a2=10000, b2=0),
                      parent(count=256, a2=10000, b2=10000)], [exact_reference])
    result = metric(report, "connected2", fit=0)
    assert result["estimate_ci95"] == [0., 1.]
    assert report["intervals_are_independent_units"] is False


def test_reference_calibration_uncertainty_is_present(stochastic_reference, exact_reference):
    rows = [parent(a4=30, a8=20, b8=10, n22=40, joint22=20)] * 4
    empirical = summary(rows, [stochastic_reference])
    exact = summary(rows, [exact_reference])
    intervals = [metric(empirical, name, fit=0)["reference_ci95"]
                 for name in ("connected4", "motif22_4", "connected8", "motif22_8", "joint8")]
    assert any(bounds[0] < bounds[1] for bounds in intervals)
    for name in ("connected2", "connected4", "motif22_4", "connected8", "motif22_8", "joint8"):
        bounds = metric(exact, name, fit=0)["reference_ci95"]
        assert bounds[0] == bounds[1]


def test_evidence_requires_each_fit_support(exact_reference):
    other = deepcopy(exact_reference)
    other["fit"] = 1
    rows = [parent(0)] * 40 + [parent(1)] * 2
    report = summarize_conditional(rows, [exact_reference, other], rng=np.random.default_rng(2),
                                   bootstrap_draws=100)
    assert metric(report, "connected2")["status"] == "insufficient_information"
    assert metric(report, "connected2", fit=0)["status"] == "equivalent"


def test_joint_statistic_retains_association(exact_reference):
    # Both examples have the same mean connectivity and mean n22, but different
    # connected*n22. These are deliberately constructed statistical records.
    low = summary([parent(a8=2, b8=1, n22=14, joint22=0)] * 3, [exact_reference])
    high = summary([parent(a8=2, b8=1, n22=14, joint22=14)] * 3, [exact_reference])
    for key in ("connected8", "motif22_8"):
        assert metric(low, key)["estimate"] == metric(high, key)["estimate"]
    assert metric(low, "joint8")["estimate"] == 0
    assert metric(high, "joint8")["estimate"] == pytest.approx(.1)


def test_reference_records_are_audited(stochastic_reference):
    altered = deepcopy(stochastic_reference)
    altered["m4"]["outcomes"][0] = (altered["m4"]["outcomes"][0] + 1) % 16
    with pytest.raises(ValueError, match="categorical records"):
        summary([parent()], [altered])
    altered = deepcopy(stochastic_reference)
    altered["m8"]["outcomes"][0][1] += 1
    with pytest.raises(ValueError, match="categorical records"):
        summary([parent()], [altered])


def test_exact_reference_cannot_be_replaced_by_an_empirical_table(exact_reference):
    altered = deepcopy(exact_reference)
    altered["m4"]["outcomes"] = [0] * 24
    altered["m4"]["counts"] = [24] + [0] * 15
    with pytest.raises(ValueError, match="complete permutation"):
        summary([parent()], [altered])


def test_local_dimension_domain_endpoints_are_not_clipped(exact_reference):
    total = summary([parent(a2=10, b2=10)] * 3, [exact_reference])["local_dimension"]
    assert total["estimate"] == 1 and total["ci95"] == [1, 1]
    assert total["status"] == "ok"
    anti = summary([parent(a2=10, b2=0)] * 3, [exact_reference])["local_dimension"]
    assert anti["estimate"] is None and anti["ci95"] == [None, None]
    assert anti["status"] == "out_of_domain"
    mixed = summary([parent(a2=10, b2=0), parent(a2=10, b2=10)],
                    [exact_reference])["local_dimension"]
    assert mixed["estimate"] == 2
    assert mixed["ci95"] == [1, None]
    assert mixed["status"] == "interval_out_of_domain"


def test_full_histogram_and_joint_records_are_cross_checked(exact_reference):
    row = parent()
    row["interval_histogram"] = [0] * 15
    with pytest.raises(ValueError, match="full histogram"):
        summary([row], [exact_reference])
    row = parent(a8=1, b8=1, n22=2, joint22=2)
    row["interval_m8_joint"] = [[2, 2, 1]]
    with pytest.raises(ValueError, match="joint table"):
        summary([row], [exact_reference])


@pytest.mark.parametrize("field,value", [("interval_m2_connected", 11),
                                        ("interval_m8_n22_sum", 1),
                                        ("interval_m4_motif_counts", [1] * 16)])
def test_invalid_parent_counts_fail(exact_reference, field, value):
    row = parent()
    row[field] = value
    with pytest.raises(ValueError):
        summary([row], [exact_reference])


def test_reference_fit_keys_are_unique_and_complete(exact_reference):
    with pytest.raises(ValueError, match="unique reference"):
        summary([parent()], [exact_reference, exact_reference])
    with pytest.raises(ValueError, match="unique reference"):
        summary([parent(fit=1)], [exact_reference])


@pytest.mark.parametrize("value", [0, -1, 1.5, True])
def test_invalid_permutation_count(value):
    with pytest.raises(ValueError):
        connected_permutation_count(value)


def test_bootstrap_is_reproducible(exact_reference):
    rows = [parent(a2=3, b2=1), parent(a2=7, b2=6)]
    assert summary(rows, [exact_reference]) == summary(rows, [exact_reference])
