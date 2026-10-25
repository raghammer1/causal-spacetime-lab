"""Independent checks of boundary laws, exact collisions and search accounting."""
import itertools
import json

import numpy as np
import pytest

from causal_lab import local_generators as generators
from causal_lab.dimension import minkowski_order, validate_order
from causal_lab.order_observables import antichain, total_order, transitive_closure


def _rng(seed=2026102504):
    return np.random.default_rng(seed)


def _brute_n22(order):
    result = 0
    for subset in itertools.combinations(range(len(order)), 4):
        four = order[np.ix_(subset, subset)]
        result += int(four.sum() == 2 and np.all(four.sum(axis=0) + four.sum(axis=1) == 1))
    return result


def _degree_joint(order):
    return sorted(zip(order.sum(axis=0).tolist(), order.sum(axis=1).tolist()))


def _overlap_first(order):
    # Independent incidence construction, rather than the degree-product identity.
    intervals = [order[a] & order[:, b] for a, b in np.argwhere(order)]
    return sum(int(np.count_nonzero(left & right))
               for left, right in itertools.combinations(intervals, 2))


@pytest.mark.parametrize("dimension", [2, 3, 4])
def test_slab_membership_and_conditional_uniform_time_law(dimension):
    sample = generators.sprinkle_central_slab(12000, _rng(dimension), dimension,
                                               max_count=12000)
    assert np.all((sample.t >= .25) & (sample.t <= .75))
    q = np.minimum(sample.t, 1 - sample.t)
    assert np.all(np.linalg.norm(sample.x, axis=1) < q)
    # Conditional q^d is uniform on [.25^d,.5^d]. The broad fixed six-SE
    # margins are numerical generator checks, not a scientific fitted result.
    uniform = (q ** dimension - .25 ** dimension) / (.5 ** dimension - .25 ** dimension)
    assert abs(uniform.mean() - .5) < 6 * np.sqrt(1 / (12 * len(uniform)))
    assert abs(np.mean(sample.t < .5) - .5) < 6 * np.sqrt(.25 / len(uniform))
    for cut in (.25, .5, .75):
        assert abs(np.mean(uniform <= cut) - cut) < 6 * np.sqrt(cut * (1 - cut) / len(uniform))


@pytest.mark.parametrize("dimension", [2, 3, 4])
@pytest.mark.parametrize("n", [0, 1, 8, 17])
def test_slab_order_matches_coordinates_and_replays(n, dimension):
    sample = generators.sprinkle_central_slab(n, _rng(), dimension)
    order = generators.central_slab_order(n, _rng(), dimension)
    assert np.array_equal(order, minkowski_order(sample))
    assert np.array_equal(validate_order(order), order)
    assert np.array_equal(order, generators.central_slab_order(n, _rng(), dimension))


@pytest.mark.parametrize("blowup", [1, 2])
def test_modules_exact_invariants_and_induced_counts(blowup):
    first = generators.bipartite_module(connected=True, blowup=blowup)
    second = generators.bipartite_module(connected=False, blowup=blowup)
    n, relations, height, histogram = generators.old_signature(first)
    assert generators.old_signature(first) == generators.old_signature(second)
    assert (n, relations, height) == (8 * blowup, 8 * blowup ** 2, 2)
    assert histogram[0] == relations and sum(histogram[1:]) == 0
    assert _degree_joint(first) == _degree_joint(second)
    assert _brute_n22(first) == 12 * blowup ** 4
    assert _brute_n22(second) == 16 * blowup ** 4


@pytest.mark.parametrize("base", [antichain(0), antichain(2), total_order(2),
                                np.array([[0, 1, 1], [0, 0, 0], [0, 0, 0]], dtype=bool)])
def test_lexicographic_theorem_on_independent_bases(base):
    first = generators.lexicographic_order(base, generators.bipartite_module(connected=True))
    second = generators.lexicographic_order(base, generators.bipartite_module(connected=False))
    assert generators.old_signature(first) == generators.old_signature(second)
    assert _degree_joint(first) == _degree_joint(second)
    assert _overlap_first(first) == _overlap_first(second)
    assert _brute_n22(second) - _brute_n22(first) == 4 * len(base)
    assert generators.old_signature(first)[2] == 2 * generators.old_signature(base)[2]


@pytest.mark.parametrize("n,scaling", [(8, "fixed"), (16, "fixed"), (32, "inflated"),
                                     (64, "fixed"), (64, "inflated"),
                                     (128, "fixed"), (128, "inflated"),
                                     (256, "fixed"), (256, "inflated")])
def test_registered_exact_pair_scales_replay_and_match_full_signature(n, scaling):
    result = generators.lexicographic_matched_pair(n, _rng(), scaling=scaling)
    replay = generators.lexicographic_matched_pair(n, _rng(), scaling=scaling)
    first, second = result.first_order, result.second_order
    assert generators.old_signature(first) == generators.old_signature(second)
    assert _degree_joint(first) == _degree_joint(second)
    assert np.array_equal(first, replay.first_order)
    assert np.array_equal(second, replay.second_order)
    assert result.metadata == replay.metadata
    q, s = result.metadata["base_count"], result.metadata["blowup"]
    assert result.metadata["expected_n22_difference"] == 4 * q * s ** 4
    if n <= 16:
        assert _brute_n22(second) - _brute_n22(first) == 4 * q * s ** 4
    json.dumps(result.metadata, allow_nan=False)


def test_lexicographic_degree_and_interval_identities_survive_relabel_and_dual():
    result = generators.lexicographic_matched_pair(16, _rng())
    permutation = _rng(97).permutation(16)
    first = result.first_order[np.ix_(permutation, permutation)].T
    second = result.second_order[np.ix_(permutation, permutation)].T
    assert generators.old_signature(first) == generators.old_signature(result.first_order)
    assert generators.old_signature(first) == generators.old_signature(second)
    assert _brute_n22(second) - _brute_n22(first) == 8


@pytest.mark.parametrize("n", [0, 1, 4, 7])
def test_cover_reduction_independent_path_check(n):
    rng = _rng(n)
    adjacency = np.triu(rng.random((n, n)) < .45, 1)
    order = transitive_closure(adjacency)
    covers = generators.cover_relations(order)
    expected = order.copy()
    for a, b in np.argwhere(order):
        expected[a, b] = not any(order[a, v] and order[v, b] for v in range(n))
    assert np.array_equal(covers, expected)
    assert np.array_equal(transitive_closure(covers), order)


def test_search_known_accepted_switch_chain_and_odd_checkpoint():
    order = np.zeros((4, 4), dtype=bool)
    order[0, 2] = order[1, 3] = True
    other = np.zeros_like(order)
    other[0, 3] = other[1, 2] = True
    result = generators.microcanonical_switch_search(order, _rng(), steps=3)
    assert np.array_equal(result.initial_order, order)
    assert np.array_equal(result.midpoint_order, other)
    assert np.array_equal(result.final_order, other)
    meta = result.metadata
    assert meta["outcomes"]["accepted"] == 3
    assert sum(meta["outcomes"].values()) == 3
    assert meta["final_matrix_changed"]
    assert [point["attempt"] for point in meta["checkpoints"]] == [0, 1, 3]
    assert [point["outcomes"]["accepted"] for point in meta["checkpoints"]] == [0, 1, 3]
    assert _brute_n22(order) == _brute_n22(result.final_order) == 1
    assert np.array_equal(order, result.initial_order)  # input was not mutated
    result.final_order[:] = False
    assert np.array_equal(result.initial_order, order)
    assert np.array_equal(result.midpoint_order, other)


def test_search_single_step_and_accepted_return_to_initial():
    order = np.zeros((4, 4), dtype=bool)
    order[0, 2] = order[1, 3] = True
    single = generators.microcanonical_switch_search(order, _rng(), steps=1)
    assert np.array_equal(single.midpoint_order, order)
    assert [point["attempt"] for point in single.metadata["checkpoints"]] == [0, 0, 1]
    even = generators.microcanonical_switch_search(order, _rng(), steps=2)
    assert even.metadata["any_accepted_move"]
    assert not even.metadata["final_matrix_changed"]


def test_search_total_order_retains_shared_endpoint_and_cycle_failures():
    order = total_order(4)
    result = generators.microcanonical_switch_search(order, _rng(), steps=50)
    outcomes = result.metadata["outcomes"]
    assert outcomes["cycle"] > 0 and outcomes["shared_endpoint"] > 0
    assert outcomes["cycle"] + outcomes["shared_endpoint"] == 50
    assert np.array_equal(result.final_order, order)
    assert result.metadata["status"] == "no_accepted_move"


def test_search_missing_candidates_and_existing_replacements_are_counted():
    empty = generators.microcanonical_switch_search(antichain(5), _rng(), steps=7)
    assert empty.metadata["outcomes"]["no_cover_pair"] == 7
    complete_bipartite = np.zeros((4, 4), dtype=bool)
    complete_bipartite[:2, 2:] = True
    dense = generators.microcanonical_switch_search(complete_bipartite, _rng(), steps=50)
    outcomes = dense.metadata["outcomes"]
    assert outcomes["existing_replacement"] > 0
    assert outcomes["existing_replacement"] + outcomes["shared_endpoint"] == 50


@pytest.mark.parametrize("n", [8, 16, 32, 64])
def test_search_exact_signature_scaled_budget_and_replay(n):
    order = generators.central_slab_order(n, _rng(142), 3)
    result = generators.microcanonical_switch_search(order, _rng())
    replay = generators.microcanonical_switch_search(order, _rng())
    assert result.metadata["steps"] == n * n // 64
    assert sum(result.metadata["outcomes"].values()) == n * n // 64
    assert result.metadata == replay.metadata
    for name in ("initial_order", "midpoint_order", "final_order"):
        state = getattr(result, name)
        assert generators.old_signature(state) == generators.old_signature(order)
        assert np.array_equal(state, getattr(replay, name))
    json.dumps(result.metadata, allow_nan=False)


def test_s3_has_explicit_d3_embedding_but_no_two_ranking_realizer():
    expected = generators.standard_example_s3()
    interval = generators.standard_example_s3_embedding()
    assert np.array_equal(minkowski_order(interval), expected)
    assert np.all(np.linalg.norm(interval.x, axis=1) < np.minimum(interval.t, interval.duration - interval.t))
    extensions = []
    for permutation in itertools.permutations(range(6)):
        position = np.argsort(permutation)
        total = position[:, None] < position[None, :]
        if np.all(total[expected]):
            extensions.append(total)
    assert extensions
    assert not any(np.array_equal(left & right, expected)
                   for left, right in itertools.combinations_with_replacement(extensions, 2))


@pytest.mark.parametrize("bad", [-1, True, 2.5, "8", np.nan])
def test_invalid_counts_and_blowups_rejected(bad):
    with pytest.raises(ValueError):
        generators.central_slab_order(bad, _rng(), 2)
    with pytest.raises(ValueError):
        generators.lexicographic_matched_pair(bad, _rng())
    with pytest.raises(ValueError):
        generators.bipartite_module(connected=True, blowup=bad)


@pytest.mark.parametrize("n,scaling", [(0, "fixed"), (9, "fixed"), (8, "inflated"),
                                     (48, "inflated"), (32, "unknown")])
def test_invalid_scaling_regimes_rejected(n, scaling):
    with pytest.raises(ValueError):
        generators.lexicographic_matched_pair(n, _rng(), scaling=scaling)


@pytest.mark.parametrize("steps", [0, -1, True, 1.5, "4"])
def test_invalid_search_budgets_rejected(steps):
    with pytest.raises(ValueError):
        generators.microcanonical_switch_search(antichain(4), _rng(), steps=steps)


def test_caps_invalid_orders_rng_and_dimension_rejected():
    with pytest.raises(ValueError):
        generators.microcanonical_switch_search(antichain(4), _rng())
    with pytest.raises(ValueError):
        generators.central_slab_order(513, _rng(), 2)
    with pytest.raises(ValueError):
        generators.bipartite_module(connected=True, blowup=65)
    with pytest.raises(ValueError):
        generators.lexicographic_order(total_order(8), total_order(8), max_count=63)
    with pytest.raises(ValueError):
        generators.cover_relations([[0, 1, 0], [0, 0, 1], [0, 0, 0]])
    with pytest.raises(ValueError):
        generators.microcanonical_switch_search([[1]], _rng(), steps=1)
    with pytest.raises(ValueError):
        generators.central_slab_order(4, None, 2)
    with pytest.raises(ValueError):
        generators.central_slab_order(4, _rng(), 5)
    with pytest.raises(ValueError):
        generators.bipartite_module(connected=1)
