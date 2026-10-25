"""Exhaustive induced 3+1 identities and order-only growth diagnostics."""
import itertools
import json
import math

import numpy as np
import pytest

from causal_lab.growth_observables import growth_observables, induced_three_plus_one
from causal_lab.local_structure import (
    canonical_poset_code, enumerate_unlabeled_posets, induced_two_plus_two,
    local_observables,
)
from causal_lab.order_observables import antichain, total_order


def brute_n31(order):
    result = 0
    for vertices in itertools.combinations(range(len(order)), 4):
        suborder = order[np.ix_(vertices, vertices)]
        degrees = suborder.sum(axis=0) + suborder.sum(axis=1)
        result += int(suborder.sum()) == 3 and sorted(degrees) == [0, 2, 2, 2]
    return int(result)


def test_every_poset_through_five_events_by_independent_subsets_and_canonical_class():
    template = antichain(4)
    template[:3, :3] = total_order(3)
    target = canonical_poset_code(template)
    rng = np.random.default_rng(501)
    for n in range(6):
        for order in enumerate_unlabeled_posets(n):
            expected = brute_n31(order)
            canonical_count = sum(canonical_poset_code(order[np.ix_(vertices, vertices)]) == target
                                  for vertices in itertools.combinations(range(n), 4))
            assert induced_three_plus_one(order) == expected == canonical_count
            assert induced_three_plus_one(order.T) == expected
            permutation = rng.permutation(n)
            relabeled = order[np.ix_(permutation, permutation)]
            assert induced_three_plus_one(relabeled) == expected
            row = growth_observables(order)
            assert row["n31"] == expected
            assert all(row[key] == value for key, value in local_observables(order).items())
            assert row == growth_observables(relabeled)
            if n < 4:
                assert row["n31_density"] is None and row["n22_density"] is None
            else:
                assert row["n31_density"] == expected / math.comb(n, 4)
                assert row["n22_density"] == induced_two_plus_two(order) / math.comb(n, 4)
            json.dumps(row, allow_nan=False)


@pytest.mark.parametrize("chain_count,isolates", [(0, 0), (1, 4), (2, 6), (3, 1), (5, 7), (40, 10)])
def test_chain_with_isolated_vertices_has_closed_form_count(chain_count, isolates):
    order = antichain(chain_count + isolates)
    order[:chain_count, :chain_count] = total_order(chain_count)
    expected = math.comb(chain_count, 3) * isolates if chain_count >= 3 else 0
    assert induced_three_plus_one(order) == expected


def test_uniform_induced_thinning_motif_expectation_exactly_for_every_five_event_order():
    # Enumerate every size-four subset, so this is an exact conditional identity
    # for each fixed parent and uses no stochastic or asymptotic approximation.
    for order in enumerate_unlabeled_posets(5):
        thinned22 = thinned31 = 0
        for selected in itertools.combinations(range(5), 4):
            thinned = order[np.ix_(selected, selected)]
            thinned22 += induced_two_plus_two(thinned)
            thinned31 += induced_three_plus_one(thinned)
        assert thinned22 / math.comb(5, 4) == induced_two_plus_two(order) / math.comb(5, 4)
        assert thinned31 / math.comb(5, 4) == induced_three_plus_one(order) / math.comb(5, 4)


@pytest.mark.parametrize("n", [0, 1, 4, 32, 512])
def test_chain_antichain_and_semiorder_forbidden_motifs(n):
    utilities = np.arange(n) / max(n, 1)
    semiorder = utilities[None, :] - utilities[:, None] > .25
    for order in (total_order(n), antichain(n), semiorder):
        assert induced_three_plus_one(order) == induced_two_plus_two(order) == 0


@pytest.mark.parametrize("order", [np.eye(2), np.ones((2, 2)), np.zeros((2, 3)),
                                     np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]])])
def test_order_validation_preserved(order):
    for function in (induced_three_plus_one, growth_observables):
        with pytest.raises(ValueError):
            function(order)


def test_observable_caps():
    for function in (induced_three_plus_one, growth_observables):
        with pytest.raises(ValueError):
            function(total_order(3), max_count=2)
        with pytest.raises(ValueError):
            function(antichain(0), max_count=513)
