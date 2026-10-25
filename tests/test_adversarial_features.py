"""Independent finite-order and finite-count checks for Experiment 3 features."""
import itertools
import json
import math

import numpy as np
import pytest

from causal_lab.adversarial_features import (
    ABUNDANCE_BIN_LABELS, FIVE_FEATURES, SEARCH_FEATURES, exact_counterexamples,
    expected_interval_abundance_2d, extract_features, feature_vector, nondual_pair,
)
from causal_lab.dimension import MinkowskiInterval, minkowski_order, validate_order
from causal_lab.dimension_study import FEATURES
from causal_lab.order_observables import (
    antichain, order_observables, random_dag_order, total_order, transitive_closure,
)


def brute_abundances(order):
    """Classify every unordered endpoint pair without using histogram helpers."""
    n = len(order)
    result = [0] * 10
    for i in range(n):
        for j in range(i + 1, n):
            if not order[i, j] and not order[j, i]:
                result[0] += 1
                continue
            before, after = (i, j) if order[i, j] else (j, i)
            size = sum(bool(order[before, k] and order[k, after]) for k in range(n))
            if size < 4:
                category = size + 1
            elif size < 8:
                category = 5
            elif size < 16:
                category = 6
            elif size < 32:
                category = 7
            elif size < 64:
                category = 8
            else:
                category = 9
            result[category] += 1
    return np.asarray(result) / math.comb(n, 2)


def component_count(order):
    """Undirected graph connectivity, independent of interval extraction."""
    graph = order | order.T
    remaining = set(range(len(order)))
    components = 0
    while remaining:
        components += 1
        pending = [remaining.pop()]
        while pending:
            i = pending.pop()
            neighbours = set(np.flatnonzero(graph[i])) & remaining
            pending.extend(neighbours)
            remaining -= neighbours
    return components


def test_registered_feature_names_preserve_the_historical_model():
    assert FIVE_FEATURES == FEATURES
    assert len(ABUNDANCE_BIN_LABELS) == 10
    assert len(SEARCH_FEATURES) == 15
    assert SEARCH_FEATURES[:5] == FIVE_FEATURES


@pytest.mark.parametrize("n", [0, 1, 2, 4, 16, 70])
def test_old_observable_values_are_preserved(n):
    for order in (total_order(n), antichain(n)):
        old = order_observables(order)
        new = extract_features(order)
        assert all(new[key] == value for key, value in old.items())
        json.dumps(new, allow_nan=False)
        if n >= 2:
            np.testing.assert_allclose(new["abundance_vector"], brute_abundances(order))
            assert sum(new["abundance_vector"]) == pytest.approx(1)
        else:
            assert new["abundance_vector"] is None


def test_all_four_event_forward_dags_against_pairwise_brute_force():
    pairs = list(zip(*np.triu_indices(4, 1)))
    for bits in itertools.product((False, True), repeat=len(pairs)):
        adjacency = np.zeros((4, 4), dtype=bool)
        for edge, present in zip(pairs, bits):
            adjacency[edge] = present
        order = transitive_closure(adjacency)
        row = extract_features(order)
        np.testing.assert_array_equal(row["abundance_vector"], brute_abundances(order))
        assert row["minimal_count"] == sum(not any(order[:, i]) for i in range(4))
        assert row["maximal_count"] == sum(not any(order[i]) for i in range(4))
        assert row["isolated_count"] == sum(not any(order[:, i]) and not any(order[i])
                                             for i in range(4))


def test_all_histogram_bin_boundaries_are_assigned_correctly():
    # A chain contains intervals of each size 0,...,68, with known abundance.
    n = 70
    row = extract_features(total_order(n))
    expected_counts = [0, 69, 68, 67, 66,
                       sum(69-k for k in range(4, 8)),
                       sum(69-k for k in range(8, 16)),
                       sum(69-k for k in range(16, 32)),
                       sum(69-k for k in range(32, 64)),
                       sum(69-k for k in range(64, 69))]
    np.testing.assert_array_equal(row["abundance_vector"], np.array(expected_counts) / 2415)


@pytest.mark.parametrize("seed", [1, 17, 92])
def test_relabeling_and_dual_invariance_with_directional_count_swap(seed):
    rng = np.random.default_rng(seed)
    order = random_dag_order(18, rng, 0.2)
    row = extract_features(order)
    permutation = rng.permutation(len(order))
    assert extract_features(order[np.ix_(permutation, permutation)]) == row
    dual = extract_features(order.T)
    np.testing.assert_array_equal(feature_vector(dual), feature_vector(row))
    assert dual["interval_histogram"] == row["interval_histogram"]
    assert dual["minimal_count"] == row["maximal_count"]
    assert dual["maximal_count"] == row["minimal_count"]
    assert dual["isolated_count"] == row["isolated_count"]


def test_antichain_features_are_explicitly_undefined_not_zero_imputed():
    row = extract_features(antichain(8))
    vector = feature_vector(row)
    assert row["abundance_vector"] == [1.0] + [0.0] * 9
    assert vector[0] == 0 and vector[1] == 1 / 8
    assert np.isnan(vector[2:5]).all()
    assert np.isfinite(vector[5:]).all()
    assert row["minimal_count"] == row["maximal_count"] == row["isolated_count"] == 8


def test_no_pair_distribution_for_fewer_than_two_events():
    for n in (0, 1):
        row = extract_features(antichain(n))
        assert row["abundance_vector"] is None
        assert np.isnan(feature_vector(row)[5:]).all()


def test_exact_nondual_pair_matches_even_the_full_histogram():
    first, second = nondual_pair()
    validate_order(first)
    validate_order(second)
    a, b = extract_features(first), extract_features(second)
    assert a == b
    assert a["count"] == 10 and a["relations"] == 25 and a["longest_chain"] == 4
    assert a["interval_histogram"] == [16, 0, 8, 0, 0, 0, 0, 0, 1]
    assert a["minimal_count"] == a["maximal_count"] == 1
    for order, expected in ((first, 1), (second, 2)):
        # Remove the unique extrema by their order properties, not their labels.
        internal = order.any(axis=0) & order.any(axis=1)
        interior_order = order[np.ix_(internal, internal)]
        assert component_count(interior_order) == expected
        assert component_count(interior_order.T) == expected


def test_both_exact_counterexample_families_are_independent_arrays():
    pairs = exact_counterexamples()
    assert set(pairs) == {"dual", "nondual"}
    for first, second in pairs.values():
        np.testing.assert_array_equal(feature_vector(extract_features(first)),
                                      feature_vector(extract_features(second)))
        assert not np.shares_memory(first, second)
    a, b = (extract_features(order) for order in pairs["dual"])
    assert a["minimal_count"] != b["minimal_count"]
    assert a["maximal_count"] != b["maximal_count"]


def test_feature_vector_does_not_consult_truth_or_generation_metadata():
    row = extract_features(total_order(8))
    expected = feature_vector(row)
    row.update(true_dimension="forbidden", target_dimension=1000, coordinates=None,
               sample_id="irrelevant")
    np.testing.assert_array_equal(feature_vector(row), expected)


@pytest.mark.parametrize("value", [math.nan, math.inf, -0.1, 1.1, True, "0.5"])
def test_feature_vector_rejects_malformed_scalars(value):
    row = extract_features(total_order(5))
    row["ordering_fraction"] = value
    with pytest.raises(ValueError, match="finite numbers"):
        feature_vector(row)


@pytest.mark.parametrize("abundance", [0.5, [], [0]*9, [0]*10, [1]+[0]*8+[None],
                                       [math.nan]+[0]*9, [2]+[0]*9])
def test_feature_vector_rejects_malformed_probability_vectors(abundance):
    row = extract_features(total_order(5))
    row["abundance_vector"] = abundance
    with pytest.raises(ValueError):
        feature_vector(row)


def test_feature_vector_rejects_missing_fields_and_nonmappings():
    for row in (None, [], {}, {"ordering_fraction": 0.5}):
        with pytest.raises(ValueError):
            feature_vector(row)


@pytest.mark.parametrize("order", [np.eye(2), [[0, 1], [1, 0]], np.zeros((2, 3)),
                                   [[0, 0.5], [0, 0]], [[0, np.nan], [0, 0]],
                                   [[0, 1, 0], [0, 0, 1], [0, 0, 0]]])
def test_extractor_preserves_strict_order_validation(order):
    with pytest.raises(ValueError):
        extract_features(order)


def test_extractor_applies_event_cap_before_feature_work():
    with pytest.raises(ValueError, match="limit"):
        extract_features(np.zeros((8, 8)), max_count=7)


@pytest.mark.parametrize("n", [0, 1, 2, 3, 8, 16, 64, 128, 256, 512])
def test_fixed_count_expectations_have_exact_sum_and_endpoints(n):
    expected = expected_interval_abundance_2d(n)
    assert expected.shape == (max(n - 1, 1),)
    assert np.all(np.isfinite(expected)) and np.all(expected >= 0)
    assert expected.sum() == pytest.approx(n * (n - 1) / 4, abs=2e-9)
    if n >= 2:
        assert expected[-1] == pytest.approx(1 / (n * (n - 1)), abs=3e-13)


@pytest.mark.parametrize("n", [2, 3, 8, 16, 64, 128, 256])
def test_fixed_count_formula_matches_independent_geometric_quadrature(n):
    # For each coordinate gap, the integrand is a polynomial of degree N-1.
    # Gauss-Legendre with ceil(N/2) nodes integrates it exactly in exact arithmetic.
    nodes, weights = np.polynomial.legendre.leggauss(max(8, (n + 1) // 2))
    gaps, weights = (nodes + 1) / 2, weights / 2
    volumes = gaps[:, None] * gaps[None, :]
    measure = (weights[:, None] * weights[None, :]
               * (1 - gaps[:, None]) * (1 - gaps[None, :]))
    integral = np.array([
        n * (n - 1) * math.comb(n - 2, m)
        * np.sum(measure * volumes**m * (1 - volumes)**(n - 2 - m))
        for m in range(n - 1)
    ])
    np.testing.assert_allclose(expected_interval_abundance_2d(n), integral,
                               atol=2e-9, rtol=2e-9)


@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_fixed_count_formula_matches_exact_rank_ensemble(n):
    # Independent rankings: fixing the first rank loses no label-invariant data.
    # Enumerating every second ranking gives an exact ensemble, without Monte Carlo.
    histograms = []
    first = np.arange(n)
    for permutation in itertools.permutations(range(n)):
        second = np.asarray(permutation)
        order = ((first[:, None] < first[None, :])
                 & (second[:, None] < second[None, :]))
        histograms.append(extract_features(order)["interval_histogram"])
    np.testing.assert_allclose(np.mean(histograms, axis=0),
                               expected_interval_abundance_2d(n), atol=1e-13, rtol=0)


def test_rank_intersection_matches_d2_null_coordinate_causality_exactly():
    # Exhaust every pair of four-event rankings; dyadic coordinates avoid ties
    # being perturbed by floating-point subtraction in this exact comparison.
    for first in itertools.permutations(range(4)):
        u = (np.asarray(first) + 0.5) / 4
        for second in itertools.permutations(range(4)):
            v = (np.asarray(second) + 0.5) / 4
            interval = MinkowskiInterval((u + v) / 2, ((v-u) / 2)[:, None], 2, 1.0)
            ranks = (u[:, None] < u[None, :]) & (v[:, None] < v[None, :])
            np.testing.assert_array_equal(minkowski_order(interval), ranks)


@pytest.mark.parametrize("n", [-1, 513, 1.5, True, math.nan, "4"])
def test_fixed_count_formula_rejects_invalid_or_unbounded_count(n):
    with pytest.raises(ValueError):
        expected_interval_abundance_2d(n)
