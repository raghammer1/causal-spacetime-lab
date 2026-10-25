"""Independent statistical audit; analytic/synthetic inputs, no quantum samples."""
import itertools
import math

import numpy as np
import pytest

from causal_lab.quantum_statistics import binomial_lower, stratified_mean_interval, summarize


class ExhaustiveBootstrapIndices:
    """Every ordered size-two resample in each of three strata, exactly once."""

    def __init__(self):
        self.patterns = list(itertools.product(range(4), repeat=3))
        self.call = 0

    def integers(self, low, high, size):
        assert low == 0 and high == 2 and size == (64, 2)
        selected = [row[self.call] for row in self.patterns]
        self.call += 1
        return np.array([[value // 2, value % 2] for value in selected])


class NeverDraw:
    def integers(self, *args, **kwargs):
        raise AssertionError("unestimable strata must not generate a confidence interval")


def row(unit, batch, value, *, status="ok", metric="value", family="B", stochastic=True):
    return dict(family=family, n=6, h=1., preparation="ground", delta=0., time=0.,
                unit_id=str(unit), batch=batch, status=status, stochastic=stochastic,
                metrics={metric: value} if status == "ok" else {})


def test_exact_bootstrap_distribution_from_all_ordered_resamples():
    # Stratum means are 1,12,24. The 64 ordered resamples are exhaustively
    # enumerated, so this is not a stochastic approximate-coverage assertion.
    data = np.array([0., 2., 10., 14., 20., 28.])
    batches = np.repeat(np.arange(3), 2)
    generator = ExhaustiveBootstrapIndices()
    result = stratified_mean_interval(data, batches, generator, resamples=64, alpha=.1)
    # Independent scalar convolution of the three exact resampled-mean laws.
    laws = [[a, (a + b) / 2, (a + b) / 2, b]
            for a, b in ((0., 2.), (10., 14.), (20., 28.))]
    possible = np.array([sum(means) / 3 for means in itertools.product(*laws)])
    assert generator.call == 3
    assert result["mean"] == pytest.approx(37 / 3)
    np.testing.assert_allclose(result["ci95"], np.quantile(possible, [.025, .975]))
    assert result["lower"] == pytest.approx(np.quantile(possible, .1))
    # Conditional Var(mean*) = sum_b n_b Var_empirical(X_b) / N^2.
    assert possible.var() == pytest.approx(sum((1., 4., 16.)) / 18)
    assert result["batch_means"] == {"0": 1., "1": 12., "2": 24.}
    assert result["n"] == 6 and result["weak_small_sample"]


@pytest.mark.parametrize("values,batches", [([1., 2., 3.], [0, 1, 2]),
                                             ([1.], [0]),
                                             ([1., 2., 3., 4., 5.], [0, 1, 1, 2, 2])])
def test_any_singleton_stratum_makes_stratified_interval_unavailable(values, batches):
    result = stratified_mean_interval(values, batches, NeverDraw(), resamples=99)
    assert result["ci95"] is None and result["lower"] is None
    assert result["mean"] == pytest.approx(np.mean(values))
    assert result["interval_unavailable"]
    assert result["weak_small_sample"]


def independent_binomial_lower(successes, count, alpha):
    """Invert P_p(X >= successes)=alpha using only finite binomial sums."""
    if successes == 0:
        return 0.
    left, right = 0., 1.
    for _ in range(70):
        midpoint = (left + right) / 2
        tail = math.fsum(math.comb(count, k) * midpoint ** k * (1 - midpoint) ** (count - k)
                         for k in range(successes, count + 1))
        if tail < alpha:
            left = midpoint
        else:
            right = midpoint
    return (left + right) / 2


@pytest.mark.parametrize("count", [1, 2, 6, 12, 24])
def test_clopper_pearson_matches_independent_finite_tail_inversion(count):
    alpha = .05 / 3
    for successes in range(count + 1):
        assert binomial_lower(successes, count, alpha) == pytest.approx(
            independent_binomial_lower(successes, count, alpha), abs=2e-14)
    assert binomial_lower(count, count, alpha) == pytest.approx(alpha ** (1 / count))


@pytest.mark.parametrize("count", [6, 12, 24])
def test_binomial_bound_coverage_over_complete_finite_outcome_space(count):
    alpha = .05 / 3
    bounds = [independent_binomial_lower(k, count, alpha) for k in range(count + 1)]
    for probability in (0., .01, .05, .2, .5, .8, .95, .99, 1.):
        coverage = math.fsum(math.comb(count, k) * probability ** k
                            * (1 - probability) ** (count - k)
                            for k in range(count + 1) if bounds[k] <= probability)
        assert coverage >= 1 - alpha - 1e-12


def test_summary_retains_planned_denominators_and_undefined_metrics():
    rows = [row(0, 0, 1.), row(1, 0, 2.), row(2, 1, None),
            row(3, 1, np.nan), row(4, 2, 9., status="failed"),
            row(5, 2, 0., status="blocked_or_unattempted")]
    result, = summarize(rows, resamples=99)
    assert (result["attempted"], result["valid"], result["failures"]) == (6, 4, 2)
    estimate = result["metrics"]["value"]
    assert estimate["mean"] == 1.5 and estimate["n"] == 2
    assert estimate["undefined"] == 2


@pytest.mark.parametrize("missing", [None, np.nan, np.inf])
def test_chain_success_excludes_missing_nonfinite_and_marks_incomplete_cohort(missing):
    rows = [row(i, i // 8, .9, metric="edge_auc", family="chain") for i in range(24)]
    rows[0]["metrics"]["edge_auc"] = missing
    result, = summarize(rows, resamples=99)
    assert result["attempted"] == 24
    assert result["chain_success"]["count"] == 23
    assert result["chain_success"]["successes"] == 23
    assert result["chain_success"]["complete_cohort"] is False
    assert result["chain_success"]["gate_eligible"] is False
    assert result["chain_success"]["undefined"] == 1
    # This lower bound describes observed valid outcomes only; it cannot promote
    # an incomplete registered cohort to a passed chain control.
    assert result["chain_success"]["lower"] == pytest.approx((.05 / 3) ** (1 / 23))


def test_chain_failed_solver_preserves_cohort_and_zero_successes_are_not_dropped():
    rows = [row(i, i // 8, .6, metric="edge_auc", family="chain") for i in range(24)]
    rows[0] = row(0, 0, None, status="failed", metric="edge_auc", family="chain")
    result, = summarize(rows, resamples=99)
    assert result["chain_success"]["successes"] == 0
    assert result["chain_success"]["lower"] == 0
    assert result["chain_success"]["count"] == 23
    assert result["chain_success"]["complete_cohort"] is False
    assert result["chain_success"]["gate_eligible"] is False
    assert result["failures"] == 1 and result["attempted"] == 24


def test_complete_chain_cohort_records_exact_bound_without_all_success_certainty():
    rows = [row(i, i // 8, .9, metric="edge_auc", family="chain") for i in range(24)]
    result, = summarize(rows, resamples=99)
    success = result["chain_success"]
    assert success["complete_cohort"] is True and success["count"] == 24
    assert success["gate_eligible"] is True
    assert success["lower"] == pytest.approx((.05 / 3) ** (1 / 24))
    assert success["lower"] < 1
    # Constant-value percentile intervals alone contain no analogous protection.
    np.testing.assert_allclose(result["metrics"]["edge_auc"]["ci95"], [.9, .9])


def test_paired_differences_are_one_value_per_independent_realization():
    baseline = np.arange(24) ** 2
    other = baseline + .125
    rows = [row(i, i // 8, other[i] - baseline[i], metric="phase_minus_stress_d3")
            for i in range(24)]
    result, = summarize(rows, resamples=99)
    metric = result["metrics"]["phase_minus_stress_d3"]
    assert metric["n"] == 24
    assert metric["ci95"] == [.125, .125]
    assert metric["lower"] == .125
    assert metric["alpha_lower"] == .05 / 6


def test_two_sided_95_lower_and_registered_one_sided_stress_lower_are_distinct():
    rows = [row(i, i // 8, float(i), metric="overlap_base_k2") for i in range(24)]
    result, = summarize(rows, resamples=3999)
    estimate = result["metrics"]["overlap_base_k2"]
    assert estimate["ci95"][0] < estimate["lower"]
    # A proximity gate documented as a 95% interval lower bound must consume
    # ci95[0], not the less conservative separately reported 5% quantile.
    stress_rows = [row(i, i // 8, float(i), metric="shuffle_minus_stress_d3") for i in range(24)]
    stress, = summarize(stress_rows, resamples=3999)
    assert stress["metrics"]["shuffle_minus_stress_d3"]["alpha_lower"] == .05 / 6


def test_deterministic_controls_have_no_sampling_interval_or_replicated_evidence():
    control = row(0, 0, .2, stochastic=False)
    result, = summarize([control], resamples=99)
    assert result["metrics"]["value"]["deterministic"]
    assert result["metrics"]["value"]["ci95"] is None
    with pytest.raises(ValueError, match="deterministic"):
        summarize([control, row(1, 1, .2, stochastic=False)], resamples=99)
