"""Independent mathematical, geometric and failure checks for Experiment 2."""
from dataclasses import replace
import math

import numpy as np
import pytest

from causal_lab.core import causal_order, sprinkle
from causal_lab.dimension import (
    MinkowskiInterval, estimate_dimension, interval_volume,
    invert_ordering_fraction, minkowski_order, ordering_probability,
    sprinkle_minkowski, validate_order,
)


@pytest.mark.parametrize("dimension,probability", [(1, 1.0), (2, 0.5), (3, 8 / 35), (4, 0.1)])
def test_analytic_ordering_probabilities_and_inverse(dimension, probability):
    assert ordering_probability(dimension) == pytest.approx(probability, rel=1e-14)
    assert invert_ordering_fraction(probability) == pytest.approx(dimension, abs=1e-12)


@pytest.mark.parametrize("dimension,constant", [(2, 0.5), (3, math.pi / 12), (4, math.pi / 24)])
@pytest.mark.parametrize("duration", [0.5, 1.0, 2.0])
def test_interval_volumes_match_independent_formulas(dimension, constant, duration):
    assert interval_volume(dimension, duration) == pytest.approx(constant * duration**dimension)


@pytest.mark.parametrize("dimension,volume", [
    (2, 0.5), (3, math.pi / 12), (4, math.pi / 24),
    # Analytic continuation also independently tests non-anchor lgamma values
    # used during inversion; physical generators still use integer dimensions.
    (2.5, math.pi**0.75 / math.gamma(1.75) / (2.5 * 2**1.5)),
    (3.5, math.pi**1.25 / math.gamma(2.25) / (3.5 * 2**2.5)),
])
def test_pair_probability_by_independent_radial_quadrature(dimension, volume):
    # Integrate 2/V² int_I d^d x Vol(I(x,q)) in ordinary t,r coordinates.
    # This evaluates the geometric integral rather than another gamma quotient.
    nodes, weights = np.polynomial.legendre.leggauss(64)
    y, wy = (nodes + 1) / 2, weights / 2
    sphere_area = 2 * math.pi ** ((dimension - 1) / 2) / math.gamma((dimension - 1) / 2)
    integral = 0.0
    for left, right in [(0.0, 0.5), (0.5, 1.0)]:
        t = left + (right - left) * y
        wt = (right - left) * wy
        radius = np.minimum(t, 1 - t)
        # r=q*y² makes the origin's radial Jacobian smooth even for the
        # half-integer analytic continuations used to check inversion values.
        r = radius[:, None] * y[None, :] ** 2
        future_volume = volume * ((1 - t[:, None])**2 - r**2) ** (dimension / 2)
        radial = 2 * radius ** (dimension - 1) * (
            (future_volume * y[None, :] ** (2 * dimension - 3)) @ wy
        )
        integral += float(wt @ radial) * sphere_area
    assert 2 * integral / volume**2 == pytest.approx(ordering_probability(dimension), abs=2e-9)


def test_probability_is_monotone_on_inversion_domain_and_endpoints_are_exact():
    dimensions = np.linspace(1, 10, 100)
    assert np.all(np.diff([ordering_probability(d) for d in dimensions]) < 0)
    for d in [1.0, 1.25, 2.7, 6.25, 10.0]:
        assert invert_ordering_fraction(ordering_probability(d)) == pytest.approx(d, abs=2e-12)


@pytest.mark.parametrize("fraction", [-0.1, 1.1, np.nan, np.inf, True, "0.5", 0.0, 1e-20])
def test_inversion_refuses_invalid_or_out_of_domain_values(fraction):
    with pytest.raises(ValueError):
        invert_ordering_fraction(fraction)


@pytest.mark.parametrize("domain", [(0.5, 10), (2, 2), (4, 2), (1, np.inf)])
def test_invalid_inversion_domain_rejected(domain):
    with pytest.raises(ValueError):
        invert_ordering_fraction(0.5, *domain)


def test_custom_domain_does_not_clamp_total_or_antichain():
    total = np.triu(np.ones((10, 10), dtype=bool), 1)
    anti = np.zeros((10, 10), dtype=bool)
    assert estimate_dimension(total).dimension == 1.0
    assert estimate_dimension(total, d_min=2).status == "out_of_domain"
    result = estimate_dimension(anti)
    assert result.ordering_fraction == 0
    assert result.dimension is None
    assert result.status == "out_of_domain"
    assert invert_ordering_fraction(8 / 35, 3, 4) == 3
    assert invert_ordering_fraction(0.1, 3, 4) == 4


@pytest.mark.parametrize("n", [0, 1])
def test_empty_and_singleton_dimension_are_explicitly_undefined(n):
    result = estimate_dimension(np.zeros((n, n), dtype=bool))
    assert (result.count, result.relations, result.ordering_fraction, result.dimension, result.status) == (
        n, 0, None, None, "undefined",
    )


@pytest.mark.parametrize("matrix", [
    np.ones((2, 3)), np.array(1), np.ones(3), np.eye(3),
    [[0, 1], [1, 0]], [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
    [[0, 1, 0], [0, 0, 1], [0, 0, 0]],
    [[0, 0.3], [0, 0]], [[0, np.nan], [0, 0]],
    [[0, np.inf], [0, 0]], [["0", "1"], ["0", "0"]],
])
def test_malformed_orders_are_rejected(matrix):
    with pytest.raises(ValueError):
        validate_order(matrix)
    with pytest.raises(ValueError):
        estimate_dimension(matrix)


def test_binary_input_relabeling_and_coordinate_free_interface():
    interval = sprinkle_minkowski(3, 1.0, np.random.default_rng(17), count=80)
    order = minkowski_order(interval)
    result = estimate_dimension(order.astype(int))
    perm = np.random.default_rng(19).permutation(len(order))
    assert estimate_dimension(order[np.ix_(perm, perm)]) == result
    # The estimator accepts the matrix alone, without a dimension or embedding.
    assert result.relations == int(order.sum())
    assert result.ordering_fraction == result.relations / math.comb(80, 2)
    with pytest.raises(TypeError):
        estimate_dimension(order, coordinates=interval.x)


@pytest.mark.parametrize("dimension", [2, 3, 4])
def test_fixed_count_generator_is_reproducible_and_inside_diamond(dimension):
    a = sprinkle_minkowski(dimension, 2.0, np.random.default_rng(301), count=300)
    b = sprinkle_minkowski(dimension, 2.0, np.random.default_rng(301), count=300)
    assert a.count == 300
    assert a.x.shape == (300, dimension - 1)
    np.testing.assert_array_equal(a.t, b.t)
    np.testing.assert_array_equal(a.x, b.x)
    assert np.all(np.linalg.norm(a.x, axis=1) < np.minimum(a.t, 2 - a.t))
    validate_order(minkowski_order(a))


@pytest.mark.parametrize("dimension", [2, 3, 4])
@pytest.mark.parametrize("duration", [0.5, 2.0])
def test_generator_has_correct_time_radial_and_rotation_distributions(dimension, duration):
    # Probability-integral transforms are independent Uniform[0,1]. The fixed
    # seeds and six-SE bounds guard distribution mistakes, not statistical claims.
    n = 12000
    interval = sprinkle_minkowski(dimension, duration, np.random.default_rng(100 + dimension), count=n)
    q = np.minimum(interval.t, duration - interval.t)
    radial = np.linalg.norm(interval.x, axis=1)
    z_time = (2 * q / duration)**dimension
    z_radius = (radial / q)**(dimension - 1)
    uniform_tolerance = 6 / math.sqrt(12 * n)
    assert abs(z_time.mean() - 0.5) < uniform_tolerance
    assert abs(z_radius.mean() - 0.5) < uniform_tolerance
    assert abs(np.mean(z_time * z_radius) - 0.25) < 6 * math.sqrt(7 / (144 * n))
    time_variance = duration**2 / (2 * (dimension + 1) * (dimension + 2))
    assert abs(interval.t.mean() - duration / 2) < 6 * math.sqrt(time_variance / n)
    directions = interval.x / radial[:, None]
    spatial = dimension - 1
    assert np.all(np.abs(directions.mean(axis=0)) < 6 / math.sqrt(spatial * n))
    assert np.all(np.abs(np.mean(directions**2, axis=0) - 1 / spatial) < 6 / math.sqrt(n))
    for i in range(spatial):
        for j in range(i):
            assert abs(np.mean(directions[:, i] * directions[:, j])) < 6 / math.sqrt(n)


@pytest.mark.parametrize("dimension,volume", [(2, 0.5), (3, math.pi / 12), (4, math.pi / 24)])
def test_poisson_density_uses_physical_volume(dimension, volume):
    class EmptyPoisson:
        def poisson(self, mean):
            self.mean = mean
            return 0

    rng = EmptyPoisson()
    result = sprinkle_minkowski(dimension, 2.0, rng, density=30.0)
    assert rng.mean == pytest.approx(30 * volume * 2**dimension)
    assert result.count == 0
    assert result.x.shape == (0, dimension - 1)
    assert result.density == 30


def test_d2_order_matches_existing_null_coordinate_implementation():
    old = sprinkle(1.3, 400, np.random.default_rng(41))
    new_format = MinkowskiInterval(old.t, old.x[:, None], 2, 1.3)
    np.testing.assert_array_equal(minkowski_order(new_format), causal_order(old))


def test_independent_d2_generators_match_null_square_moments():
    # The established null-square generator supplies an independently coded
    # sampling construction. Equal law does not imply seed-by-seed equal points.
    new = sprinkle_minkowski(2, 1.0, np.random.default_rng(59), count=20000)
    old = sprinkle(1.0, 40000, np.random.default_rng(61))
    for u, v in [(new.t + new.x[:, 0], new.t - new.x[:, 0]), (old.u, old.v)]:
        tolerance = 6 / math.sqrt(12 * len(u))
        assert abs(u.mean() - 0.5) < tolerance
        assert abs(v.mean() - 0.5) < tolerance
        assert abs(np.mean(u * v) - 0.25) < 6 * math.sqrt(7 / (144 * len(u)))


@pytest.mark.parametrize("dimension", [2, 3, 4])
def test_lorentz_rotation_translation_and_scale_preserve_order(dimension):
    interval = sprinkle_minkowski(dimension, 1.0, np.random.default_rng(97), count=100)
    original = minkowski_order(interval)
    beta = 0.4
    gamma = 1 / math.sqrt(1 - beta**2)
    boosted_t = gamma * (interval.t - beta * interval.x[:, 0])
    boosted_x = interval.x.copy()
    boosted_x[:, 0] = gamma * (interval.x[:, 0] - beta * interval.t)
    np.testing.assert_array_equal(original, minkowski_order(replace(interval, t=boosted_t, x=boosted_x)))
    rotation, _ = np.linalg.qr(np.random.default_rng(103).normal(size=(dimension - 1, dimension - 1)))
    transformed = replace(interval, t=3 * interval.t + 0.7, x=3 * interval.x @ rotation + 0.2)
    np.testing.assert_array_equal(original, minkowski_order(transformed))


@pytest.mark.parametrize("dimension", [2, 3, 4])
def test_null_ties_and_spacelike_events_are_not_ordered(dimension):
    x = np.zeros((3, dimension - 1))
    x[:, 0] = [0, 1, 2]
    interval = MinkowskiInterval(np.array([0.0, 1.0, 1.5]), x, dimension, 3)
    assert not minkowski_order(interval).any()


@pytest.mark.parametrize("kwargs", [
    {}, {"count": 2, "density": 3}, {"count": -1}, {"count": 2.5},
    {"count": True}, {"density": 0}, {"density": np.inf}, {"density": np.nan},
])
def test_generator_rejects_ambiguous_or_invalid_count_parameters(kwargs):
    with pytest.raises(ValueError):
        sprinkle_minkowski(2, 1.0, np.random.default_rng(1), **kwargs)


@pytest.mark.parametrize("dimension,duration", [(1, 1), (5, 1), (2.0, 1), (True, 1), (2, 0), (2, np.inf)])
def test_generator_rejects_invalid_geometry(dimension, duration):
    with pytest.raises(ValueError):
        sprinkle_minkowski(dimension, duration, np.random.default_rng(1), count=3)


@pytest.mark.parametrize("t,x", [
    ([0, np.nan], [[0], [0]]), ([0, 1], [[0, 0], [0, 0]]),
    ([[0, 1]], [[0]]), ([0, 1], [[0], [np.inf]]),
])
def test_order_generator_rejects_malformed_coordinates(t, x):
    with pytest.raises(ValueError):
        minkowski_order(MinkowskiInterval(np.asarray(t), np.asarray(x), 2, 1))


def test_coordinate_difference_overflow_fails_explicitly():
    with pytest.raises(ValueError, match="floating-point range"):
        minkowski_order(MinkowskiInterval(np.array([-1e308, 1e308]), np.zeros((2, 1)), 2, 1))
