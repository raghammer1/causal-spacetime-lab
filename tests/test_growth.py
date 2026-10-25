"""Independent finite-law verification of intrinsic transitive percolation."""
from collections import defaultdict
import itertools
import json
import math

import numpy as np
import pytest

from causal_lab.dimension import validate_order
from causal_lab.growth import (
    complete_order_log_weight, cover_relation_count, path_log_probability,
    thin_order, transitive_percolation, transition_log_probability,
    transition_probability,
)
from causal_lab.local_structure import enumerate_unlabeled_posets
from causal_lab.order_observables import antichain, total_order


def floyd_warshall(edges):
    """Independent boolean closure; deliberately no production bitsets."""
    result = edges.copy()
    for middle in range(len(result)):
        for a in range(len(result)):
            for c in range(len(result)):
                result[a, c] |= result[a, middle] and result[middle, c]
    return result


def brute_cover_count(order):
    return sum(order[a, c] and not any(order[a, b] and order[b, c]
                                     for b in range(len(order)))
               for a in range(len(order)) for c in range(len(order)))


def downsets(order):
    n = len(order)
    return [tuple(v for v in range(n) if mask & (1 << v))
            for mask in range(1 << n)
            if all(not order[a, c] or not (mask & (1 << c)) or (mask & (1 << a))
                   for a in range(n) for c in range(n))]


class PrescribedCoins(np.random.Generator):
    """Expose every finite primitive DAG to the actual generator algorithm."""

    def __init__(self, edges):
        super().__init__(np.random.PCG64(0))
        self.edges = edges
        self.birth = 0

    def random(self, size=None):
        assert size == self.birth
        coins = np.where(self.edges[:self.birth, self.birth], .25, .75)
        self.birth += 1
        return coins


@pytest.mark.parametrize("n,expected", list(enumerate([1, 1, 2, 7, 40, 357])))
def test_every_forward_dag_closure_and_grouped_bernoulli_law(n, expected):
    pairs = list(itertools.combinations(range(n), 2))
    probabilities = (0.0, .2, .5, .8, 1.0)
    mass = {p: defaultdict(float) for p in probabilities}
    closures = {}
    for mask in range(1 << len(pairs)):
        edges = np.zeros((n, n), dtype=bool)
        for bit, pair in enumerate(pairs):
            edges[pair] = bool(mask & (1 << bit))
        expected_order = floyd_warshall(edges)
        history = transitive_percolation(n, PrescribedCoins(edges), .5)
        np.testing.assert_array_equal(history.primitive_edges, edges)
        np.testing.assert_array_equal(history.order, expected_order)
        validate_order(history.order)
        key = expected_order.tobytes()
        closures[key] = expected_order
        selected = int(edges.sum())
        for p in probabilities:
            mass[p][key] += p ** selected * (1 - p) ** (len(pairs) - selected)
    assert len(closures) == expected
    for p in probabilities:
        assert sum(mass[p].values()) == pytest.approx(1, abs=2e-14)
        for key, order in closures.items():
            covers = int(brute_cover_count(order))
            incomparable = len(pairs) - int(order.sum())
            expected_weight = p ** covers * (1 - p) ** incomparable
            assert cover_relation_count(order) == covers
            assert mass[p][key] == pytest.approx(expected_weight, abs=2e-14)
            assert math.exp(complete_order_log_weight(order, p)) == pytest.approx(
                expected_weight, abs=2e-14)


def test_every_small_precursor_transition_normalizes_and_matches_selection_law():
    for n in range(6):
        for order in enumerate_unlabeled_posets(n):
            valid = downsets(order)
            for p in (0.0, .2, .5, .8, 1.0):
                mass = defaultdict(float)
                for mask in range(1 << n):
                    chosen = {v for v in range(n) if mask & (1 << v)}
                    past = chosen | {a for a in range(n)
                                     if any(order[a, c] for c in chosen)}
                    mass[tuple(sorted(past))] += p ** len(chosen) * (1 - p) ** (n - len(chosen))
                assert sum(transition_probability(order, s, p) for s in valid) == pytest.approx(1)
                for s in valid:
                    expected = mass[tuple(sorted(s))]
                    assert transition_probability(order, s, p) == pytest.approx(expected)
                    assert transition_probability(order, tuple(reversed(s)), p) == pytest.approx(expected)


def test_covariance_across_every_natural_labeling_of_small_orders():
    valid_histories = 0
    rejected_histories = 0
    for n in range(6):
        for order in enumerate_unlabeled_posets(n):
            for births in itertools.permutations(range(n)):
                ordered = order[np.ix_(births, births)]
                natural = not np.tril(ordered).any()
                if not natural:
                    rejected_histories += 1
                    with pytest.raises(ValueError, match="linear extension"):
                        path_log_probability(order, .23, birth_order=births)
                    continue
                valid_histories += 1
                for p in (0.0, .23, .7, 1.0):
                    actual = path_log_probability(order, p, birth_order=births)
                    expected = complete_order_log_weight(order, p)
                    assert actual == pytest.approx(expected)
                    assert path_log_probability(ordered, p) == pytest.approx(expected)
    assert valid_histories > 357 and rejected_histories > 1000


def test_bell_spectator_factor_and_ratio_for_all_small_precursor_pairs():
    p = .37
    for n in range(6):
        for order in enumerate_unlabeled_posets(n):
            valid = downsets(order)
            for first, second in itertools.combinations_with_replacement(valid, 2):
                active = sorted(set(first) | set(second))
                restricted = order[np.ix_(active, active)]
                first_active = [active.index(v) for v in first]
                second_active = [active.index(v) for v in second]
                full = [transition_probability(order, s, p) for s in (first, second)]
                reduced = [transition_probability(restricted, s, p)
                           for s in (first_active, second_active)]
                spectator_factor = (1 - p) ** (n - len(active))
                assert full == pytest.approx(np.array(reduced) * spectator_factor)
                assert full[0] / full[1] == pytest.approx(reduced[0] / reduced[1])


@pytest.mark.parametrize("p", [0.0, .005, .02, .3, 1.0])
def test_seeded_birth_prefixes_and_metadata_at_registered_ceiling(p):
    full = transitive_percolation(512, np.random.default_rng(41005), p)
    for n in (0, 1, 2, 32, 64, 128, 256, 512):
        prefix = transitive_percolation(n, np.random.default_rng(41005), p)
        np.testing.assert_array_equal(prefix.order, full.order[:n, :n])
        np.testing.assert_array_equal(prefix.primitive_edges, full.primitive_edges[:n, :n])
        assert prefix.metadata["selected_parent_counts"] == full.metadata["selected_parent_counts"][:n]
        assert prefix.metadata["primitive_edge_count"] == int(prefix.primitive_edges.sum())
        assert prefix.metadata["relation_count"] == int(prefix.order.sum())
        assert set(prefix.metadata) == {"model", "count", "probability", "selected_parent_counts",
                                        "primitive_edge_count", "relation_count", "closure_strategy"}
        json.dumps(prefix.metadata, allow_nan=False)
    validate_order(full.order)
    assert not np.tril(full.primitive_edges).any()
    assert not np.any(full.primitive_edges & ~full.order)
    if p in (0, 1):
        np.testing.assert_array_equal(full.order, antichain(512) if p == 0 else total_order(512))


def test_endpoint_generators_consume_the_same_registered_random_draw_budget():
    states = []
    for p in (0.0, .3, 1.0):
        rng = np.random.default_rng(17)
        transitive_percolation(20, rng, p)
        states.append(rng.random())
    assert len(set(states)) == 1
    rng = np.random.default_rng(17)
    rng.random(math.comb(20, 2))
    assert states[0] == rng.random()


def test_four_birth_forbidden_motif_probabilities_from_all_primitive_dags():
    pairs = list(itertools.combinations(range(4), 2))
    for p in (.1, .37, .8):
        probability22 = probability31 = 0.0
        for mask in range(1 << len(pairs)):
            edges = np.zeros((4, 4), dtype=bool)
            for bit, pair in enumerate(pairs):
                edges[pair] = bool(mask & (1 << bit))
            order = floyd_warshall(edges)
            degrees = order.sum(axis=0) + order.sum(axis=1)
            selected = int(edges.sum())
            weight = p ** selected * (1 - p) ** (6 - selected)
            if int(order.sum()) == 2 and np.all(degrees == 1):
                probability22 += weight
            if int(order.sum()) == 3 and sorted(degrees) == [0, 2, 2, 2]:
                probability31 += weight
        assert probability22 == pytest.approx(3 * p ** 2 * (1 - p) ** 4)
        assert probability31 == pytest.approx(4 * p ** 2 * (1 - p) ** 3)


def test_varying_birth_parameter_breaks_covariance_and_size_retuning_breaks_prefix_law():
    # Completed three-event order: a<b and isolated c. Both listed births are
    # linear extensions. This is an analytic counterexample, not a new model.
    p1, p2 = .2, .7
    births_a_b_c = p1 * (1 - p2) ** 2
    births_a_c_b = (1 - p1) * p2 * (1 - p2)
    assert births_a_b_c != pytest.approx(births_a_c_b)
    # Separately sampled fixed-p_N ensembles have first-pair probability p_N:
    # restrictions of an N=3 ensemble cannot equal an N=2 ensemble if p3!=p2.
    p_n2, p_n3 = .2, .7
    assert p_n2 != p_n3
    first_pair_related_mass = sum(
        p_n3 ** (1 + int(x) + int(y)) * (1 - p_n3) ** (2 - int(x) - int(y))
        for x, y in itertools.product((False, True), repeat=2))
    assert first_pair_related_mass == pytest.approx(p_n3)
    assert first_pair_related_mass != pytest.approx(p_n2)


def test_thinning_is_closed_restriction_preserving_deleted_mediators():
    chain = total_order(3)
    seen = set()
    for seed in range(32):
        thinned, indices = thin_order(chain, 2, np.random.default_rng(seed))
        seen.add(tuple(indices))
        np.testing.assert_array_equal(thinned, total_order(2))
        np.testing.assert_array_equal(thinned, chain[np.ix_(indices, indices)])
        assert np.all(np.diff(indices) > 0)
    assert (0, 2) in seen
    assert seen == {(0, 1), (0, 2), (1, 2)}
    first = thin_order(chain, 2, np.random.default_rng(100))
    second = thin_order(chain, 2, np.random.default_rng(100))
    for left, right in zip(first, second):
        np.testing.assert_array_equal(left, right)
    empty, indices = thin_order(chain, 0, np.random.default_rng(0))
    assert empty.shape == (0, 0) and indices.shape == (0,)
    complete, indices = thin_order(chain, 3, np.random.default_rng(0))
    np.testing.assert_array_equal(complete, chain)
    np.testing.assert_array_equal(indices, np.arange(3))
    complete[0, 1] = False
    assert chain[0, 1]  # No shared mutable storage.


@pytest.mark.parametrize("p", [-.1, 1.1, float("nan"), float("inf"), True, "0.2", None])
def test_invalid_probability_rejected(p):
    for function in (
        lambda: transitive_percolation(3, np.random.default_rng(0), p),
        lambda: transition_probability(antichain(2), [], p),
        lambda: complete_order_log_weight(antichain(2), p),
        lambda: path_log_probability(antichain(2), p),
    ):
        with pytest.raises(ValueError):
            function()


@pytest.mark.parametrize("n", [-1, True, 2.5, 513])
def test_invalid_generator_count_rejected(n):
    with pytest.raises(ValueError):
        transitive_percolation(n, np.random.default_rng(0), .2)


@pytest.mark.parametrize("precursor", [[1], [0, 0], [-1], [2], [True], [0.0], [[0]], "0"])
def test_invalid_precursor_rejected(precursor):
    with pytest.raises(ValueError):
        transition_log_probability(total_order(2), precursor, .2)


@pytest.mark.parametrize("births", [[0], [0, 0], [0, 2], [1, 0], [False, True], [0.0, 1.0]])
def test_invalid_birth_order_rejected(births):
    with pytest.raises(ValueError):
        path_log_probability(total_order(2), .2, birth_order=births)


def test_public_caps_rng_and_malformed_orders():
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError):
        transitive_percolation(2, rng, .2, max_count=1)
    with pytest.raises(ValueError):
        transitive_percolation(0, rng, .2, max_count=513)
    for function in (
        lambda: transitive_percolation(2, 123, .2),
        lambda: thin_order(total_order(2), 1, 123),
        lambda: thin_order(total_order(2), 3, rng),
        lambda: thin_order(total_order(2), 1, rng, max_count=1),
        lambda: complete_order_log_weight(antichain(513, max_count=513), .2),
    ):
        with pytest.raises(ValueError):
            function()
    invalid = (np.eye(2), np.ones((2, 2)), np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]]),
               np.array([[0, .5], [0, 0]]), np.zeros((2, 3)))
    for order in invalid:
        for function in (
            lambda: transition_probability(order, [], .2),
            lambda: cover_relation_count(order),
            lambda: complete_order_log_weight(order, .2),
            lambda: path_log_probability(order, .2),
            lambda: thin_order(order, 0, rng),
        ):
            with pytest.raises(ValueError):
                function()
