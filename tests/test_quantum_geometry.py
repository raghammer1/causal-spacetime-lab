"""Independent mathematical anchors for MI-only inference and withheld evaluation."""
import inspect
import math

import numpy as np
import pytest

from causal_lab.quantum_geometry import (
    EPSILONS, edge_auc, epsilon_agreement, evaluate_inputs, fractional_neighbors,
    geometry_metrics, infer_geometry, neighborhood_overlap, rank_correlation,
    shuffle_weights,
)


def symmetric(values, n):
    matrix = np.zeros((n, n))
    upper = np.triu_indices(n, 1)
    matrix[upper] = values
    matrix[(upper[1], upper[0])] = values
    return matrix


def distances(coordinates):
    return np.sqrt(((coordinates[:, None] - coordinates[None, :])**2).sum(axis=-1))


def test_inference_signature_excludes_withheld_inputs_and_target_dimension():
    assert tuple(inspect.signature(infer_geometry).parameters) == ("mi", "epsilon")


@pytest.mark.parametrize("n", [2, 4, 6, 8, 10])
def test_ghz_equilateral_spectrum_and_fractional_neighborhoods(n):
    mi = np.ones((n, n)) - np.eye(n)
    result = infer_geometry(mi)
    metrics = geometry_metrics(result)
    side = np.log(2)
    np.testing.assert_allclose(result["eigenvalues"][:-1], side**2 / 2, atol=1e-12)
    assert abs(result["eigenvalues"][-1]) < 1e-12
    assert metrics["positive_rank"] == n - 1
    assert metrics["positive_participation_rank"] == pytest.approx(n - 1)
    assert metrics["stress_full"] < 1e-12
    assert metrics["negative_eigenvalue_mass"] == 0
    assert metrics["triangle_violation_fraction"] == 0
    for k in (1, 2, 3):
        if k < n:
            np.testing.assert_allclose(result["neighbors"][f"k{k}"], (1-np.eye(n)) * k/(n-1))
            expected_tie = 0 if k == n-1 else 1
            assert metrics[f"neighbor_tie_fraction_k{k}"] == expected_tie
    if n > 4:
        assert metrics["stress_d3"] > 0.01
        assert metrics["stress_d3_ambiguous"] == 1


@pytest.mark.parametrize("epsilon", EPSILONS)
def test_product_regularization_is_explicit_not_a_link(epsilon):
    result = infer_geometry(np.zeros((6, 6)), epsilon)
    metrics = geometry_metrics(result)
    assert metrics["regularized_pair_fraction"] == 1
    assert metrics["zero_information_pairs"] == 15
    assert metrics["distance_max"] == pytest.approx(-np.log(epsilon / 2))
    assert metrics["threshold_0.25_edge_density"] == 0
    assert metrics["threshold_0.25_components"] == 6
    assert metrics["neighbor_tie_fraction_k2"] == 1
    assert epsilon_agreement(result["mi"])["epsilon_agreement_k2"] == 1


def test_bell_pair_identity_failure_and_undefined_entanglement_rank():
    mi = np.zeros((6, 6))
    for i in range(0, 6, 2):
        mi[i, i+1] = mi[i+1, i] = 2
    result = infer_geometry(mi)
    metrics = geometry_metrics(result)
    assert metrics["zero_distance_pairs"] == 3
    assert metrics["positive_rank"] == 2
    assert metrics["triangle_violation_fraction"] == 0
    assert metrics["stress_full"] < 1e-12
    assert metrics["threshold_0.5_components"] == 3
    assert np.isnan(evaluate_inputs(mi, negativity=np.zeros_like(mi))["spearman_mi_negativity"])


def test_purified_and_marginals_violate_triangle_and_closure_is_imposed():
    binary_entropy = lambda p: -p*math.log2(p) - (1-p)*math.log2(1-p)
    pair_information = binary_entropy(.25) - .5
    mi = symmetric([pair_information, 0, pair_information], 3)
    result = infer_geometry(mi)
    metrics = geometry_metrics(result)
    assert metrics["triangle_violation_fraction"] == pytest.approx(1/3)
    assert metrics["triangle_max_excess"] > 10
    assert metrics["negative_eigenvalue_mass"] > 0
    assert metrics["closure_triangle_violation_fraction"] == 0
    assert result["closure_distance"][0, 2] == pytest.approx(2*result["distance"][0, 1])
    assert metrics["closure_changed_pair_fraction"] == pytest.approx(1/3)


@pytest.mark.parametrize("coordinates,rank", [
    ([[0], [1], [2], [3]], 1),
    ([[0, 0], [1, 0], [0, 1], [1, 1]], 2),
    ([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], 3),
])
def test_full_mds_reconstructs_independently_given_euclidean_distances(coordinates, rank):
    exact_distance = distances(np.asarray(coordinates))
    mi = 2*np.exp(-exact_distance)
    np.fill_diagonal(mi, 0)
    result = infer_geometry(mi)
    metrics = geometry_metrics(result)
    assert result["coordinates"].shape == (4, rank)
    np.testing.assert_allclose(distances(result["coordinates"]), exact_distance, atol=1e-12)
    assert metrics["negative_rank"] == 0
    assert metrics[f"stress_d{rank}"] < 1e-12
    assert metrics["stress_full"] < 1e-12


def test_zero_pseudometric_has_zero_rank_and_finite_stress():
    result = infer_geometry(np.array([[0, 2], [2, 0]]))
    assert result["coordinates"].shape == (2, 0)
    metrics = geometry_metrics(result)
    assert metrics["positive_rank"] == 0
    assert metrics["positive_participation_rank"] == 0
    assert metrics["stress_full"] == 0


def test_ties_share_boundary_mass_without_vertex_index_breaking():
    mi = symmetric([1, .5, .5, .1, .3, .2], 4)
    neighbors = fractional_neighbors(mi, 2)
    np.testing.assert_allclose(neighbors[0], [0, 1, .5, .5])
    np.testing.assert_allclose(neighbors.sum(axis=1), 2)
    permutation = np.array([3, 1, 0, 2])
    permuted = fractional_neighbors(mi[np.ix_(permutation, permutation)], 2)
    np.testing.assert_allclose(permuted, neighbors[np.ix_(permutation, permutation)])
    assert neighborhood_overlap(neighbors, neighbors) == pytest.approx(1)


def test_numerical_ties_remain_ties_under_permutations():
    mi = symmetric([1, .5, .5+1e-11, .1, .3, .2], 4)
    np.testing.assert_allclose(fractional_neighbors(mi, 2)[0], [0, 1, .5, .5])


def test_overlap_is_intersection_mass_not_dot_product_of_ties():
    complete = (np.ones((4, 4))-np.eye(4))/3
    assert neighborhood_overlap(complete, complete) == pytest.approx(1)
    first = np.array([[0, 1, 0], [1, 0, 0], [1, 0, 0.]])
    second = np.array([[0, 0, 1], [0, 0, 1], [0, 1, 0.]])
    assert neighborhood_overlap(first, second) == 0


def test_regularization_changes_low_information_rankings():
    mi = symmetric([1e-8, 2e-8, 4e-8, 5e-8, 8e-8, 9e-8], 4)
    agreement = epsilon_agreement(mi)
    assert agreement["epsilon_agreement_k1"] < .95
    ordinary = symmetric([.1, .2, .4, .5, .8, .9], 4)
    assert all(value == pytest.approx(1) for value in epsilon_agreement(ordinary).values())


def test_threshold_components_and_instability_are_combinatorial():
    mi = symmetric([1, .1, .1, .5, .1, .9], 4)
    metrics = geometry_metrics(infer_geometry(mi))
    assert metrics["threshold_0.25_components"] == 1
    assert metrics["threshold_0.5_components"] == 1
    assert metrics["threshold_0.75_components"] == 2
    assert metrics["threshold_component_range"] == 1
    assert metrics["threshold_0.75_edge_density"] == pytest.approx(2/6)


def test_inference_preserves_inputs_and_full_geometry_is_relabel_equivariant():
    mi = symmetric([.3, .7, .2, .4, .9, .1], 4)
    before = mi.copy()
    result = infer_geometry(mi)
    permutation = [3, 0, 2, 1]
    changed = infer_geometry(mi[np.ix_(permutation, permutation)])
    np.testing.assert_array_equal(mi, before)
    np.testing.assert_allclose(changed["eigenvalues"], result["eigenvalues"], atol=1e-12)
    np.testing.assert_allclose(distances(changed["coordinates"]), distances(result["coordinates"])[np.ix_(permutation, permutation)], atol=1e-12)
    for key, value in geometry_metrics(result).items():
        assert geometry_metrics(changed)[key] == pytest.approx(value, abs=1e-12)


def test_shuffle_preserves_unordered_weight_multiset_and_replays():
    mi = symmetric(np.arange(1, 16)/10, 6)
    shuffled = shuffle_weights(mi, np.random.default_rng(17))
    repeated = shuffle_weights(mi, np.random.default_rng(17))
    np.testing.assert_array_equal(shuffled, shuffled.T)
    np.testing.assert_array_equal(shuffled, repeated)
    upper = np.triu_indices(6, 1)
    np.testing.assert_array_equal(np.sort(mi[upper]), np.sort(shuffled[upper]))
    assert not np.array_equal(mi, shuffled)
    np.testing.assert_array_equal(np.diag(shuffled), 0)


def test_paired_shuffle_uses_same_edge_permutation_when_seed_is_shared():
    first = symmetric(np.arange(1, 7)/10, 4)
    second = first*2
    shuffled_first = shuffle_weights(first, np.random.default_rng(19))
    shuffled_second = shuffle_weights(second, np.random.default_rng(19))
    np.testing.assert_array_equal(shuffled_second, 2*shuffled_first)


def test_auc_and_fractional_recall_against_enumerated_ties():
    adjacency = symmetric([1, 0, 0, 1, 0, 1], 4)
    mi = symmetric([.9, .3, .1, .9, .3, .3], 4)
    # Positives (.9,.9,.3) beat (.3,.1,.3): six + two half + one wins.
    assert edge_auc(mi, adjacency) == pytest.approx(8/9)
    evaluated = evaluate_inputs(mi, true_adjacency=adjacency)
    assert evaluated["edge_auc"] == pytest.approx(8/9)
    assert evaluated["edge_recall_top_n_minus_1"] == pytest.approx(7/9)
    assert evaluated["edge_recall_boundary_ambiguous"] == 1
    constant = np.ones((4,4))-np.eye(4)
    assert edge_auc(constant, adjacency) == .5
    assert evaluate_inputs(constant, true_adjacency=adjacency)["edge_recall_top_n_minus_1"] == .5


def test_auc_is_nan_without_both_classes():
    mi = symmetric([.2, .3, .4], 3)
    assert np.isnan(edge_auc(mi, np.zeros_like(mi)))
    assert np.isnan(edge_auc(mi, np.ones_like(mi)-np.eye(3)))


def test_rank_correlation_has_average_ties_and_undefined_constants():
    assert rank_correlation(np.array([1, 1, 2, 3]), np.array([3, 3, 2, 1])) == pytest.approx(-1)
    assert np.isnan(rank_correlation(np.ones(4), np.arange(4)))
    assert np.isnan(rank_correlation(np.ones(4)+np.arange(4)*1e-12, np.arange(4)))


def test_withheld_evaluator_uses_absolute_inputs_and_separate_normalization():
    mi = symmetric([.2, .3, .4, .5, .7, .9], 4)
    couplings = -mi*3
    evaluated = evaluate_inputs(mi, couplings, connected_zz=-mi/2, negativity=mi/10)
    for name in ("coupling", "zz", "negativity"):
        assert evaluated[f"spearman_mi_{name}"] == pytest.approx(1)
        assert evaluated[f"neighbor_overlap_{name}_k2"] == pytest.approx(1)
    expected = geometry_metrics(infer_geometry(mi*2/.9))
    assert evaluated["coupling_stress_d3"] == pytest.approx(expected["stress_d3"])
    assert evaluated["coupling_zero_distance_pairs"] == 1
    constant = evaluate_inputs(mi, np.zeros_like(mi))
    assert np.isnan(constant["spearman_mi_coupling"])


@pytest.mark.parametrize("bad", [np.ones(3), np.ones((2,3)), np.ones((1,1)),
    np.array([[0, np.nan],[np.nan,0]]), np.array([[0,.2],[.3,0]]),
    np.array([[0,-.1],[-.1,0]]), np.array([[0,2.1],[2.1,0]]),
    np.array([[0,1j],[1j,0]])])
def test_invalid_mi_rejected(bad):
    with pytest.raises(ValueError):
        infer_geometry(bad)


@pytest.mark.parametrize("epsilon", [0, -1, 2, np.nan, np.inf])
def test_invalid_regularization_rejected(epsilon):
    with pytest.raises(ValueError):
        infer_geometry(np.zeros((3,3)), epsilon)


def test_roundoff_is_clipped_but_large_violations_are_not():
    result = infer_geometry(np.array([[0,-1e-11],[-1e-11,0]]))
    assert result["mi"][0,1] == 0
    result = infer_geometry(np.array([[0,2+1e-11],[2+1e-11,0]]))
    assert result["mi"][0,1] == 2


@pytest.mark.parametrize("k", [0, 3, 1.5])
def test_invalid_neighbor_count_rejected(k):
    with pytest.raises(ValueError):
        fractional_neighbors(np.zeros((3,3)), k)


def test_mismatched_evaluator_and_overlap_inputs_rejected():
    mi = np.zeros((4,4))
    with pytest.raises(ValueError):
        evaluate_inputs(mi, np.zeros((3,3)))
    with pytest.raises(ValueError):
        evaluate_inputs(mi, true_adjacency=np.ones((4,4))*.5)
    with pytest.raises(ValueError):
        neighborhood_overlap(np.eye(3), np.ones((3,3)))
    with pytest.raises(ValueError):
        evaluate_inputs(mi, negativity=-(np.ones((4,4))-np.eye(4)))
