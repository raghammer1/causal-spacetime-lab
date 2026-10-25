"""Exhaustive independent checks of Experiment 4 structural identities."""
from collections import Counter
import itertools
import json
import math

import numpy as np
import pytest

from causal_lab.adversarial_features import nondual_pair
from causal_lab.adversarial_generators import random_interval_order
from causal_lab.dimension import validate_order
from causal_lab.local_structure import (
    canonical_poset_code, component_count, enumerate_unlabeled_posets,
    induced_two_plus_two, local_observables, motif_catalog, motif_counts,
    small_order_signature,
)
from causal_lab.order_observables import antichain, order_observables, random_dag_order, total_order


def brute_components(order):
    remaining = set(range(len(order)))
    components = 0
    while remaining:
        pending = [remaining.pop()]
        components += 1
        while pending:
            vertex = pending.pop()
            neighbours = {j for j in remaining if order[vertex, j] or order[j, vertex]}
            remaining -= neighbours
            pending.extend(neighbours)
    return components


def brute_n22(order):
    result = 0
    for vertices in itertools.combinations(range(len(order)), 4):
        suborder = order[np.ix_(vertices, vertices)]
        # Exactly two directed relations and degree one at all four vertices.
        result += (int(suborder.sum()) == 2
                   and np.all(suborder.sum(axis=0) + suborder.sum(axis=1) == 1))
    return int(result)


def brute_intervals(order):
    intervals = []
    for a in range(len(order)):
        for b in range(len(order)):
            if order[a, b]:
                intervals.append({v for v in range(len(order)) if order[a, v] and order[v, b]})
    return intervals


def brute_overlap_moments(intervals):
    overlaps = [len(a & b) for a, b in itertools.combinations(intervals, 2)]
    return (sum(overlaps), sum(math.comb(size, 2) for size in overlaps),
            float(np.mean(overlaps)) if overlaps else None,
            float(np.var(overlaps)) if overlaps else None)


def brute_chain_counts(order, size):
    return sum(int(order[np.ix_(vertices, vertices)].sum()) == math.comb(size, 2)
               for vertices in itertools.combinations(range(len(order)), size))


def brute_diamonds(order):
    result = 0
    for vertices in itertools.combinations(range(len(order)), 4):
        suborder = order[np.ix_(vertices, vertices)]
        result += (int(suborder.sum()) == 5 and np.count_nonzero(~suborder.any(axis=0)) == 1
                   and np.count_nonzero(~suborder.any(axis=1)) == 1)
    return int(result)


@pytest.mark.parametrize("n,expected", list(enumerate([1, 1, 2, 5, 16, 63])))
def test_complete_unlabeled_enumeration_and_independent_arrays(n, expected):
    representatives = enumerate_unlabeled_posets(n)
    assert len(representatives) == expected
    codes = [canonical_poset_code(order) for order in representatives]
    assert codes == sorted(set(codes))
    for order in representatives:
        validate_order(order)
    # Cached enumeration cannot be corrupted by a caller mutating a returned matrix.
    if n >= 2:
        representatives[0][0, 1] = True
        assert not enumerate_unlabeled_posets(n)[0].any()


@pytest.mark.parametrize("n,expected", [(2, 3), (3, 19), (4, 219), (5, 4231)])
def test_unlabeled_orbits_have_the_known_complete_labeled_counts(n, expected):
    labeled = set()
    for order in enumerate_unlabeled_posets(n):
        for permutation in itertools.permutations(range(n)):
            labeled.add(order[np.ix_(permutation, permutation)].tobytes())
    assert len(labeled) == expected


def test_every_poset_through_five_events_against_brute_counts_and_overlap():
    rng = np.random.default_rng(20261025)
    for n in range(6):
        for order in enumerate_unlabeled_posets(n):
            row = local_observables(order)
            assert all(row[key] == value for key, value in order_observables(order).items())
            assert row["n22"] == brute_n22(order) == induced_two_plus_two(order.T)
            assert row["chains3"] == brute_chain_counts(order, 3)
            assert row["chains4"] == brute_chain_counts(order, 4)
            assert row["diamonds4"] == brute_diamonds(order)
            assert row["chains3"] == sum(m * a for m, a in enumerate(row["interval_histogram"]))
            assert small_order_signature(order) == (brute_components(order), brute_n22(order))
            assert component_count(order) == brute_components(order)
            intervals = brute_intervals(order)
            profile = Counter()
            for interval in intervals:
                vertices = sorted(interval)
                profile[(len(vertices), brute_components(order[np.ix_(vertices, vertices)]))] += 1
            assert row["interval_component_profile"] == [[m, k, a] for (m, k), a in sorted(profile.items())]
            marginal = [0] * len(row["interval_histogram"])
            for m, k, count in row["interval_component_profile"]:
                marginal[m] += count
            assert marginal == row["interval_histogram"]
            one, two, mean, variance = brute_overlap_moments(intervals)
            assert (row["overlap_sum"], row["overlap_choose2_sum"]) == (one, two)
            if mean is None:
                assert row["overlap_mean"] is row["overlap_variance"] is None
            else:
                assert row["overlap_mean"] == pytest.approx(mean)
                assert row["overlap_variance"] == pytest.approx(variance)
            permutation = rng.permutation(n)
            assert local_observables(order[np.ix_(permutation, permutation)]) == row
            json.dumps(row, allow_nan=False)


def test_n22_edge_identity_is_an_independent_double_count():
    for order in enumerate_unlabeled_posets(5):
        incidence = 0
        for a, b in zip(*np.nonzero(order)):
            unrelated = [v for v in range(5) if v not in (a, b)
                         and not (order[a, v] or order[v, a] or order[b, v] or order[v, b])]
            incidence += int(order[np.ix_(unrelated, unrelated)].sum())
        assert incidence == 2 * induced_two_plus_two(order)


@pytest.mark.parametrize("n", [0, 1, 2, 3, 4, 8, 16, 70, 256])
def test_chain_and_antichain_exact_extremes(n):
    for order in (total_order(n), antichain(n)):
        row = local_observables(order)
        assert row["n22"] == row["diamonds4"] == 0
        assert row["overlap_variance"] is None or row["overlap_variance"] >= 0
    chain = local_observables(total_order(n))
    assert chain["chains3"] == (math.comb(n, 3) if n >= 3 else 0)
    assert chain["chains4"] == (math.comb(n, 4) if n >= 4 else 0)
    assert all(k == (0 if m == 0 else 1) for m, k, count in chain["interval_component_profile"])


@pytest.mark.parametrize("left,right", [(2, 2), (3, 7), (40, 33)])
def test_two_disjoint_chains_have_exact_two_plus_two_count(left, right):
    order = np.zeros((left + right, left + right), dtype=bool)
    order[:left, :left] = total_order(left)
    order[left:, left:] = total_order(right)
    assert induced_two_plus_two(order) == math.comb(left, 2) * math.comb(right, 2)


def test_known_nondual_witness_including_joint_interval_information():
    first, second = map(local_observables, nondual_pair())
    assert first["interval_histogram"] == second["interval_histogram"]
    assert (first["n22"], second["n22"]) == (12, 16)
    assert first["overlap_sum"] == second["overlap_sum"] == 24
    assert (first["overlap_choose2_sum"], second["overlap_choose2_sum"]) == (8, 12)
    assert first["interval_m8_joint"] == [[1, 12, 1]]
    assert second["interval_m8_joint"] == [[2, 16, 1]]
    assert first["interval_m8_connected_n22_sum"] == 12
    assert second["interval_m8_connected_n22_sum"] == 0


def test_four_event_nonredundancy_witness_matches_entire_old_summary():
    matching = np.zeros((4, 4), dtype=bool)
    fork = matching.copy()
    matching[0, 1] = matching[2, 3] = True
    fork[0, 2] = fork[1, 2] = True
    assert order_observables(matching) == order_observables(fork)
    assert induced_two_plus_two(matching) == 1
    assert induced_two_plus_two(fork) == 0


def test_catalog_all_classes_and_duality_map():
    catalog = motif_catalog()
    assert len(catalog) == 16
    assert [row["id"] for row in catalog] == list(range(16))
    assert [row["canonical_code"] for row in catalog] == sorted(row["canonical_code"] for row in catalog)
    for row in catalog:
        matrix = np.asarray(row["order"], dtype=bool)
        assert canonical_poset_code(matrix) == row["canonical_code"]
        assert catalog[row["dual_id"]]["dual_id"] == row["id"]
        assert catalog[row["dual_id"]]["canonical_code"] == canonical_poset_code(matrix.T)
        exact = motif_counts(matrix)
        assert exact["method"] == "exact" and exact["draws"] == 1
        assert exact["counts"][row["id"]] == 1 and sum(exact["counts"]) == 1
        assert exact["mc_variance"] == [0] * 16
    assert any(row["dual_id"] != row["id"] for row in catalog)
    json.dumps(catalog, allow_nan=False)


def test_every_directed_four_event_relation_is_in_catalog_iff_a_poset():
    catalog_codes = {row["canonical_code"] for row in motif_catalog()}
    pairs = list(itertools.combinations(range(4), 2))
    valid = 0
    for states in itertools.product((-1, 0, 1), repeat=6):
        order = np.zeros((4, 4), dtype=bool)
        for (a, b), state in zip(pairs, states):
            if state == 1:
                order[a, b] = True
            elif state == -1:
                order[b, a] = True
        try:
            validate_order(order)
        except ValueError:
            continue
        valid += 1
        assert canonical_poset_code(order) in catalog_codes
    assert valid == 219


def test_exact_four_motifs_match_independent_canonical_enumeration():
    catalog = motif_catalog()
    ids = {row["canonical_code"]: row["id"] for row in catalog}
    for order in enumerate_unlabeled_posets(5):
        counts = [0] * 16
        for vertices in itertools.combinations(range(5), 4):
            counts[ids[canonical_poset_code(order[np.ix_(vertices, vertices)])]] += 1
        assert motif_counts(order)["counts"] == counts
        assert sum(counts[row["id"]] * row["n22"] for row in catalog) == induced_two_plus_two(order)


def test_interval_conditional_profiles_against_direct_suborder_extraction():
    order = random_dag_order(22, np.random.default_rng(2718), 0.18)
    row = local_observables(order)
    m4 = [0] * 16
    m8 = Counter()
    m2_count = m2_connected = 0
    for interval in brute_intervals(order):
        vertices = sorted(interval)
        suborder = order[np.ix_(vertices, vertices)]
        if len(vertices) == 2:
            m2_count += 1
            m2_connected += brute_components(suborder) == 1
        elif len(vertices) == 4:
            counts = motif_counts(suborder)["counts"]
            m4 = [a + b for a, b in zip(m4, counts)]
        elif len(vertices) == 8:
            m8[(brute_components(suborder), brute_n22(suborder))] += 1
    assert row["interval_m2_count"] == m2_count
    assert row["interval_m2_connected"] == m2_connected
    assert row["interval_m4_motif_counts"] == m4
    assert row["interval_m4_count"] == sum(m4)
    assert row["interval_m8_joint"] == [[k, n22, count] for (k, n22), count in sorted(m8.items())]
    assert row["interval_m8_count"] == sum(m8.values())
    assert row["interval_m8_n22_sum"] == sum(n22 * count for (k, n22), count in m8.items())


def test_all_sixteen_motifs_appear_as_exact_four_event_open_intervals():
    for entry in motif_catalog():
        order = np.zeros((6, 6), dtype=bool)
        order[0, 1:] = True
        order[:5, 5] = True
        order[1:5, 1:5] = np.asarray(entry["order"], dtype=bool)
        row = local_observables(order)
        assert row["interval_m4_count"] == 1
        assert row["interval_m4_motif_counts"][entry["id"]] == 1
        assert sum(row["interval_m4_motif_counts"]) == 1


def test_time_reversal_keeps_scalar_profiles_and_permutes_directed_motifs():
    order = random_dag_order(22, np.random.default_rng(2718), .18)
    original, dual = local_observables(order), local_observables(order.T)
    for key, value in original.items():
        if key != "interval_m4_motif_counts":
            assert dual[key] == value
    for entry in motif_catalog():
        assert (original["interval_m4_motif_counts"][entry["id"]]
                == dual["interval_m4_motif_counts"][entry["dual_id"]])


def test_sampled_four_motifs_are_reproducible_and_match_exact_frequencies():
    order = random_dag_order(12, np.random.default_rng(68), 0.18)
    exact = motif_counts(order)
    sampled = motif_counts(order, np.random.default_rng(905), draws=40000, exact_limit=0)
    assert sampled == motif_counts(order, np.random.default_rng(905), draws=40000, exact_limit=0)
    assert sampled["method"] == "sampled" and sampled["draws"] == 40000
    assert sum(sampled["counts"]) == 40000
    np.testing.assert_allclose(sampled["frequencies"], exact["frequencies"], atol=.01, rtol=0)
    p = np.asarray(sampled["frequencies"])
    np.testing.assert_allclose(sampled["mc_variance"], p * (1 - p) / 39999)
    json.dumps(sampled, allow_nan=False)


def test_exact_rank_four_expectations_and_interval_order_forbidden_pattern():
    n22 = connected = 0
    first = np.arange(4)
    for permutation in itertools.permutations(range(4)):
        second = np.asarray(permutation)
        order = (first[:, None] < first[None, :]) & (second[:, None] < second[None, :])
        components, count22 = small_order_signature(order)
        n22 += count22
        connected += components == 1
    assert n22 == 1 and connected == 13  # Exact d2 probabilities 1/24 and 13/24.
    for seed in range(5):
        assert induced_two_plus_two(random_interval_order(64, np.random.default_rng(seed))) == 0


@pytest.mark.parametrize("n", [0, 1, 2, 3])
def test_no_global_four_motif_distribution_below_four_events(n):
    row = motif_counts(antichain(n))
    assert row == {"method": "undefined", "draws": 0, "counts": [0] * 16,
                   "frequencies": None, "mc_variance": None}


@pytest.mark.parametrize("order", [np.eye(2), [[0, 1], [1, 0]], np.zeros((2, 3)),
                                  [[0, .5], [0, 0]], [[0, np.nan], [0, 0]],
                                  [[0, 1, 0], [0, 0, 1], [0, 0, 0]]])
def test_public_observables_preserve_order_validation(order):
    for function in (local_observables, induced_two_plus_two, component_count,
                     small_order_signature, motif_counts, canonical_poset_code):
        with pytest.raises(ValueError):
            function(order)


def test_caps_and_required_sampling_rng():
    for function in (local_observables, induced_two_plus_two, component_count,
                     small_order_signature, motif_counts):
        with pytest.raises(ValueError, match="limit"):
            function(antichain(8), max_count=7)
    with pytest.raises(ValueError, match="limit"):
        canonical_poset_code(antichain(6))
    with pytest.raises(ValueError, match="Generator"):
        motif_counts(antichain(17))
    for count in (-1, 6, True, 4.0):
        with pytest.raises(ValueError):
            enumerate_unlabeled_posets(count)
    for draws in (0, 1, True, 2.5):
        with pytest.raises(ValueError):
            motif_counts(antichain(4), draws=draws)
    with pytest.raises(ValueError):
        motif_counts(antichain(4), exact_limit=33)
