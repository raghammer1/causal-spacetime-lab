"""Exact, independently counted checks for order diagnostics and adversaries."""
import itertools
import json

import numpy as np
import pytest

from causal_lab.core import longest_chain_order
from causal_lab.dimension import estimate_dimension, validate_order
from causal_lab.order_observables import (
    antichain, bipartite_order, indistinguishable_pair, layered_order,
    order_observables, random_dag_order, total_order, transitive_closure,
)


def brute_intervals(order):
    n = len(order)
    histogram = [0] * max(n - 1, 1)
    for i in range(n):
        for j in range(n):
            if order[i, j]:
                histogram[sum(bool(order[i, k] and order[k, j]) for k in range(n))] += 1
    return histogram


def brute_closure(adjacency):
    # An independent Boolean Floyd-Warshall reference, used only at tiny N.
    result = adjacency.copy()
    for k in range(len(result)):
        for i in range(len(result)):
            for j in range(len(result)):
                result[i, j] = result[i, j] or (result[i, k] and result[k, j])
    return result


@pytest.mark.parametrize("n", [0, 1, 2, 5, 10, 65])
def test_total_and_antichain_observables_exact(n):
    total = order_observables(total_order(n))
    anti = order_observables(antichain(n))
    assert total["longest_chain"] == n
    assert anti["longest_chain"] == int(n > 0)
    assert total["relations"] == n * (n - 1) // 2
    assert total["interval_histogram"] == ([n-k-1 for k in range(n-1)] if n >= 2 else [0])
    assert anti["relations"] == 0
    assert anti["interval_bins"] is None
    assert anti["link_fraction"] is None
    assert total["ordering_fraction"] == (1.0 if n >= 2 else None)
    assert anti["ordering_fraction"] == (0.0 if n >= 2 else None)
    if n >= 2:
        assert total["link_count"] == n - 1
        assert total["link_fraction"] == pytest.approx(2 / n)
        assert total["interval_mean"] == pytest.approx((n - 2) / 3)
        assert sum(total["interval_bins"]) == pytest.approx(1)
    if n > 2:
        assert total["interval_mean_fraction"] == pytest.approx(1 / 3)
    json.dumps(total, allow_nan=False)
    json.dumps(anti, allow_nan=False)


def test_exact_intervals_count_events_not_path_multiplicity():
    # The interval (0,4) contains {1,2,3}; there are two Hasse paths through it.
    adjacency = np.zeros((5, 5), dtype=bool)
    adjacency[0, [1, 2]] = True
    adjacency[[1, 2], 3] = True
    adjacency[3, 4] = True
    order = transitive_closure(adjacency)
    observed = order_observables(order)
    assert observed["interval_histogram"] == [5, 2, 1, 1]
    assert observed["interval_histogram"] == brute_intervals(order)
    assert observed["longest_chain"] == 4
    assert observed["relations"] == 9


def test_all_small_labeled_forward_dags_have_correct_closure_and_statistics():
    n = 4
    positions = list(zip(*np.triu_indices(n, k=1)))
    for bits in itertools.product([False, True], repeat=len(positions)):
        adjacency = np.zeros((n, n), dtype=bool)
        for edge, present in zip(positions, bits):
            adjacency[edge] = present
        order = transitive_closure(adjacency)
        np.testing.assert_array_equal(order, brute_closure(adjacency))
        observed = order_observables(order)
        assert observed["interval_histogram"] == brute_intervals(order)
        assert observed["longest_chain"] == len(longest_chain_order(order))
        assert sum(observed["interval_histogram"]) == observed["relations"]


def test_observables_and_closure_are_relabeling_invariant():
    adjacency = np.zeros((5, 5), dtype=bool)
    adjacency[0, [1, 2]] = True
    adjacency[[1, 2], 3] = True
    adjacency[3, 4] = True
    order = transitive_closure(adjacency)
    permutation = np.array([4, 2, 0, 3, 1])
    relabeled = order[np.ix_(permutation, permutation)]
    np.testing.assert_array_equal(
        transitive_closure(adjacency[np.ix_(permutation, permutation)]), relabeled,
    )
    assert order_observables(order) == order_observables(relabeled)


@pytest.mark.parametrize("matrix", [
    np.array(0), np.zeros((2, 3)), np.eye(2),
    np.array([[0, 1], [1, 0]]),
    np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]]),
    np.array([[0, 0.5], [0, 0]]),
    np.array([[0, np.nan], [0, 0]]),
    np.array([[0, np.inf], [0, 0]]),
    np.array([[0, -1], [0, 0]]), np.array([["0", "1"], ["0", "0"]]),
])
def test_malformed_or_cyclic_graphs_fail(matrix):
    with pytest.raises(ValueError):
        transitive_closure(matrix)
    with pytest.raises(ValueError):
        order_observables(matrix)


def test_hasse_matrix_requires_explicit_closure_before_observation():
    adjacency = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=bool)
    with pytest.raises(ValueError):
        order_observables(adjacency)
    assert order_observables(transitive_closure(adjacency))["longest_chain"] == 3


@pytest.mark.parametrize("n", [-1, 1.5, True, np.nan, 513])
def test_generators_reject_invalid_or_unbounded_counts(n):
    for generator in (total_order, antichain):
        with pytest.raises(ValueError):
            generator(n)
    rng = np.random.default_rng(5)
    for generator in (layered_order, random_dag_order, bipartite_order):
        with pytest.raises(ValueError):
            if generator is layered_order:
                generator(n, rng)
            else:
                generator(n, rng, 0.2)


@pytest.mark.parametrize("limit", [-1, 1.5, True])
def test_invalid_caps_rejected(limit):
    with pytest.raises(ValueError):
        order_observables(np.zeros((0, 0)), max_count=limit)
    with pytest.raises(ValueError):
        transitive_closure(np.zeros((0, 0)), max_count=limit)


def test_explicit_caps_are_enforced_before_analysis():
    order = np.zeros((33, 33), dtype=bool)
    with pytest.raises(ValueError, match="limit"):
        order_observables(order, max_count=32)
    with pytest.raises(ValueError, match="limit"):
        transitive_closure(order, max_count=32)


@pytest.mark.parametrize("probability", [-0.1, 1.1, np.nan, np.inf, True, "0.5"])
def test_adversary_probability_is_not_silently_clipped(probability):
    for generator in (bipartite_order, random_dag_order):
        with pytest.raises(ValueError):
            generator(10, np.random.default_rng(5), probability)


@pytest.mark.parametrize("layers", [0, -1, 2.5, True])
def test_invalid_layer_counts_rejected(layers):
    with pytest.raises(ValueError):
        layered_order(10, np.random.default_rng(5), layers)


@pytest.mark.parametrize("n", [0, 1, 2, 13])
def test_adversary_endpoints_and_reproducibility(n):
    for generator in (bipartite_order, random_dag_order):
        first = generator(n, np.random.default_rng(91), 0.4)
        second = generator(n, np.random.default_rng(91), 0.4)
        np.testing.assert_array_equal(first, second)
        validate_order(first)
        assert not generator(n, np.random.default_rng(91), 0).any()
    bip = order_observables(bipartite_order(n, np.random.default_rng(91), 1))
    assert bip["relations"] == (n // 2) * (n - n // 2)
    assert bip["longest_chain"] == min(n, 2)
    dag = order_observables(random_dag_order(n, np.random.default_rng(91), 1))
    assert dag["longest_chain"] == n
    assert dag["relations"] == n * (n - 1) // 2
    layers = layered_order(n, np.random.default_rng(91), 3)
    np.testing.assert_array_equal(layers, layered_order(n, np.random.default_rng(91), 3))
    validate_order(layers)
    assert order_observables(layers)["longest_chain"] <= 3
    assert not layered_order(n, np.random.default_rng(91), 1).any()


def test_bipartite_relation_expectation_and_low_height_are_separate_properties():
    # R is exactly Binomial(a*b,q) in this artificial model: aggregate across
    # independent seeded orders and check against its theoretical mean and SE.
    n, probability, repeats = 32, 0.2, 100
    relations = []
    for repeat in range(repeats):
        order = bipartite_order(n, np.random.default_rng(repeat), probability)
        observed = order_observables(order)
        relations.append(observed["relations"])
        assert observed["longest_chain"] == 2
        assert observed["link_fraction"] == 1
        assert observed["interval_mean"] == 0
    capacity = (n // 2) * (n - n // 2)
    se = np.sqrt(capacity * probability * (1 - probability) / repeats)
    assert abs(np.mean(relations) - capacity * probability) < 5 * se


def test_a_two_layer_nonspacetime_order_can_return_four_dimensions():
    # At N=20, 19 of190 possible unordered pairs gives exactly r=0.1.
    # A directed star has height2 and no nonempty intervals, despite d_hat=4.
    order = np.zeros((20, 20), dtype=bool)
    order[0, 1:] = True
    inferred = estimate_dimension(order)
    observed = order_observables(order)
    assert inferred.status == "ok"
    assert inferred.dimension == pytest.approx(4, abs=1e-9)
    assert observed["longest_chain"] == 2
    assert observed["link_fraction"] == 1
    assert observed["interval_mean"] == 0


def test_nonisomorphic_orders_share_all_selected_measurements():
    v, dual = indistinguishable_pair()
    assert np.count_nonzero(v.sum(axis=0) == 0) == 2
    assert np.count_nonzero(dual.sum(axis=0) == 0) == 1
    # Number of minimal elements is an isomorphism invariant, so these orders
    # differ, even though every statistic selected for the joint study agrees.
    assert order_observables(v) == order_observables(dual)
    assert estimate_dimension(v) == estimate_dimension(dual)
