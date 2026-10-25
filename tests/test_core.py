import numpy as np
import pytest

from causal_lab import (
    CausalDiamond, sprinkle, causal_order, longest_chain_order, longest_chain_fast,
    inferred_duration, comparable_pair_fraction,
)


def test_sprinkling_is_reproducible():
    a = sprinkle(1.0, 80, np.random.default_rng(123))
    b = sprinkle(1.0, 80, np.random.default_rng(123))
    assert np.array_equal(a.u, b.u)
    assert np.array_equal(a.v, b.v)


def test_causal_order_is_acyclic_and_consistent():
    diamond = sprinkle(1.0, 200, np.random.default_rng(9))
    order = causal_order(diamond)
    assert not np.any(np.diag(order))
    assert not np.any(order & order.T)
    i, j = np.where(order)
    assert np.all(diamond.t[i] < diamond.t[j])
    assert np.all((diamond.t[j] - diamond.t[i]) > np.abs(diamond.x[j] - diamond.x[i]))


def test_order_only_matches_fast_longest_chain():
    for seed in range(10):
        d = sprinkle(1.0, 180, np.random.default_rng(seed))
        chain_order = longest_chain_order(causal_order(d))
        chain_fast = longest_chain_fast(d)
        assert len(chain_order) == len(chain_fast)
        order = causal_order(d)
        assert all(order[i, j] for i, j in zip(chain_order[:-1], chain_order[1:]))


def test_negative_controls_have_distinct_pair_fractions():
    n = 20
    total_order = np.triu(np.ones((n, n), dtype=bool), k=1)
    antichain = np.zeros((n, n), dtype=bool)
    assert comparable_pair_fraction(total_order) == 1.0
    assert comparable_pair_fraction(antichain) == 0.0
    assert len(longest_chain_order(total_order)) == n
    assert len(longest_chain_order(antichain)) == 1


def test_ordered_fraction_close_to_half_for_large_sprinkling():
    d = sprinkle(1.0, 800, np.random.default_rng(42))
    frac = comparable_pair_fraction(causal_order(d))
    assert 0.40 < frac < 0.60  # deliberately broad finite-sample bound


def test_inferred_duration_has_correct_scale():
    assert inferred_duration(14, 98) == pytest.approx(1.0)


def test_invalid_params_rejected():
    with pytest.raises(ValueError):
        sprinkle(-1.0, 1.0, np.random.default_rng(1))
    with pytest.raises(ValueError):
        inferred_duration(1, 0)
    with pytest.raises(ValueError):
        longest_chain_order(np.zeros((2, 3), dtype=bool))


@pytest.mark.parametrize("order", [
    np.eye(3, dtype=bool),
    np.array([[0, 1], [1, 0]], dtype=bool),
    np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], dtype=bool),
    np.array([[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [1, 0, 0, 0]], dtype=bool),
    np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=bool),
])
def test_order_only_rejects_non_posets(order):
    # Includes cycles longer than two (which previously could hang) and a
    # Hasse adjacency matrix missing its required transitive relation.
    with pytest.raises(ValueError):
        longest_chain_order(order)


def test_order_only_is_invariant_under_relabeling():
    order = np.triu(np.ones((6, 6), dtype=bool), k=1)
    permutation = np.array([5, 2, 0, 4, 1, 3])
    relabeled = order[np.ix_(permutation, permutation)]
    chain = longest_chain_order(relabeled)
    assert len(chain) == 6
    assert all(relabeled[i, j] for i, j in zip(chain[:-1], chain[1:]))


@pytest.mark.parametrize("u,v,expected", [
    ([0.2, 0.2, 0.6], [0.1, 0.3, 0.7], 2),
    ([0.1, 0.3, 0.7], [0.2, 0.2, 0.6], 2),
    ([0.2, 0.2, 0.2], [0.1, 0.3, 0.7], 1),
    ([0.2, 0.2], [0.3, 0.3], 1),
    ([], [], 0),
])
def test_fast_chain_respects_strict_coordinate_ties(u, v, expected):
    diamond = CausalDiamond(np.array(u), np.array(v), 1.0, 1.0)
    order = causal_order(diamond)
    chain = longest_chain_fast(diamond)
    assert len(chain) == len(longest_chain_order(order)) == expected
    assert all(order[i, j] for i, j in zip(chain[:-1], chain[1:]))


@pytest.mark.parametrize("density", [0, -1, np.nan, np.inf, -np.inf])
def test_duration_estimate_rejects_invalid_density(density):
    with pytest.raises(ValueError):
        inferred_duration(1, density)


@pytest.mark.parametrize("length", [-1, 1.5, np.nan, np.inf, True])
def test_duration_estimate_requires_integer_event_count(length):
    with pytest.raises(ValueError):
        inferred_duration(length, 1.0)


def test_duration_estimate_handles_empty_chain_and_large_finite_density():
    assert inferred_duration(0, 1.0) == 0.0
    assert inferred_duration(2, 1e308) == pytest.approx(np.sqrt(2.0) * 1e-154, rel=1e-14, abs=0)


@pytest.mark.parametrize("order", [np.array(0), np.ones((2, 3)), np.eye(2)])
def test_comparability_rejects_invalid_shape_or_self_relations(order):
    with pytest.raises(ValueError):
        comparable_pair_fraction(order)


@pytest.mark.parametrize("duration,density,expected_mean", [(1.0, 10.0, 5.0), (2.0, 10.0, 20.0), (0.5, 8.0, 1.0)])
def test_sprinkling_uses_physical_diamond_volume(duration, density, expected_mean):
    class EmptyRecordingGenerator:
        def poisson(self, mean):
            self.mean = mean
            return 0

        def uniform(self, low, high, size):
            assert (low, high, size) == (0, duration, 0)
            return np.empty(0)

    rng = EmptyRecordingGenerator()
    diamond = sprinkle(duration, density, rng)
    assert rng.mean == expected_mean
    assert diamond.count == 0
