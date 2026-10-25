"""Structural controls, deterministic search budgets, and exact small references."""
import itertools
import json

import numpy as np
import pytest

from causal_lab import adversarial_generators as generators
from causal_lab.adversarial_features import extract_features, feature_vector
from causal_lab.dimension import MinkowskiInterval, minkowski_order, validate_order
from causal_lab.order_observables import antichain, total_order


def _rng(seed=73):
    return np.random.default_rng(seed)


class PrescribedPermutations(np.random.Generator):
    """Exact reference enumerations, not stochastic final-study samples."""

    def __init__(self, permutations):
        super().__init__(np.random.PCG64(0))
        self.permutations = iter(permutations)

    def permutation(self, x, axis=0):
        value = np.asarray(next(self.permutations), dtype=int)
        assert len(value) == x
        return value


def _brute_height(order):
    n = len(order)
    for height in range(n, 0, -1):
        for events in itertools.permutations(range(n), height):
            if all(order[events[i], events[j]] for i in range(height)
                   for j in range(i + 1, height)):
                return height
    return 0


@pytest.mark.parametrize("n", [0, 1, 2, 5, 9])
@pytest.mark.parametrize("family", ["interval", "rank", "box"])
def test_controls_are_strict_orders_with_deterministic_labels(n, family):
    def draw():
        if family == "interval":
            return generators.random_interval_order(n, _rng())
        if family == "rank":
            return generators.rank_intersection_order(n, _rng())
        return generators.uniform_box_order(n, _rng(), 3)
    order = draw()
    assert order.dtype == bool and order.shape == (n, n)
    assert np.array_equal(validate_order(order), order)
    assert np.array_equal(order, draw())
    if n >= 2:
        perm = _rng(91).permutation(n)
        left, right = extract_features(order), extract_features(order[np.ix_(perm, perm)])
        assert np.array_equal(feature_vector(left), feature_vector(right), equal_nan=True)


def test_interval_probability_exact_endpoint_enumeration():
    comparable = 0
    for permutation in itertools.permutations(range(4)):
        order = generators.random_interval_order(2, PrescribedPermutations([permutation]))
        comparable += int(order.any())
    assert comparable == 8  # 8/24 = 1/3, counting each endpoint permutation once.


def test_interval_relation_exact_known_endpoints():
    # Intervals [0,1], [2,4], [3,5]: first precedes both, last two overlap.
    order = generators.random_interval_order(3, PrescribedPermutations([[0, 1, 2, 4, 3, 5]]))
    assert np.array_equal(order, [[0, 1, 1], [0, 0, 0], [0, 0, 0]])


def test_all_four_interval_pairings_exclude_induced_two_plus_two():
    def pairings(endpoints):
        if not endpoints:
            yield []
            return
        first = endpoints[0]
        for i in range(1, len(endpoints)):
            remainder = endpoints[1:i] + endpoints[i+1:]
            for rest in pairings(remainder):
                yield [(first, endpoints[i])] + rest

    enumerated = 0
    for pairing in pairings(list(range(8))):
        flat = [rank for pair in pairing for rank in pair]
        order = generators.random_interval_order(4, PrescribedPermutations([flat]))
        degree = order.sum(axis=0) + order.sum(axis=1)
        assert not (order.sum() == 2 and np.all(degree == 1))
        enumerated += 1
    assert enumerated == 105


def test_two_plus_two_occurs_in_an_open_region_of_d2_diamond_configurations():
    null = np.array([[.2, .6], [.4, .8], [.6, .2], [.8, .4]])
    expected = np.zeros((4, 4), dtype=bool)
    expected[0, 1] = expected[2, 3] = True
    # All coordinate gaps have magnitude >=.2. Independent perturbations
    # of magnitude <=.01 cannot change any coordinate comparison.
    for signs in itertools.product((-1, 1), repeat=8):
        perturbed = null + .01 * np.asarray(signs).reshape(4, 2)
        t = perturbed.mean(axis=1)
        x = ((perturbed[:, 0] - perturbed[:, 1]) / 2)[:, None]
        assert np.all((perturbed > 0) & (perturbed < 1))
        order = minkowski_order(MinkowskiInterval(t, x, 2, 1.))
        assert np.array_equal(order, expected)


def test_two_rank_order_equals_null_coordinate_rank_construction():
    u, v = np.array([2, 0, 3, 1]), np.array([1, 0, 2, 3])
    actual = generators.rank_intersection_order(4, PrescribedPermutations([u, v]))
    # Monotone ranks are sufficient: timelike precedence is u_i<u_j and v_i<v_j.
    interval = MinkowskiInterval((u + v).astype(float), (u - v)[:, None].astype(float), 2, 1.)
    expected = minkowski_order(interval)
    assert np.array_equal(actual, expected)


def test_single_rank_is_a_total_order():
    order = generators.rank_intersection_order(7, _rng(), ranks=1)
    assert order.sum() == 21
    assert extract_features(order)["longest_chain"] == 7


@pytest.mark.parametrize("dimension", [2, 3, 4])
def test_box_relation_matches_independent_coordinate_distance(dimension):
    n = 7
    rng = _rng()
    t = rng.random(n)
    x = rng.random((n, dimension - 1)) - .5
    expected = t[None, :] - t[:, None] > np.linalg.norm(x[None, :, :] - x[:, None, :], axis=2)
    actual = generators.uniform_box_order(n, _rng(), dimension)
    assert np.array_equal(actual, expected)


@pytest.mark.parametrize("height", [1, 2, 4, 6])
@pytest.mark.parametrize("probability", [0., .23, 1.])
def test_backbone_guarantees_exact_height_by_brute_force(height, probability):
    order = generators.layered_backbone_order(6, _rng(), height, probability)
    validate_order(order)
    assert _brute_height(order) == height


def test_probability_zero_leaves_only_backbone_relations():
    order = generators.layered_backbone_order(9, _rng(), 5, 0)
    assert order.sum() == 5 * 4 // 2


@pytest.mark.parametrize("steps", [4, 16, 64])
def test_search_budget_height_objective_and_reproducibility(steps):
    donor = generators.layered_backbone_order(12, _rng(51), 4, .25)
    target = extract_features(donor)
    scale = np.full(15, .05)
    first = generators.optimize_order(12, _rng(), target, scale, steps=steps)
    second = generators.optimize_order(12, _rng(), target, scale, steps=steps)
    for name in ("height_fraction_order", "multifeature_order"):
        order = getattr(first, name)
        validate_order(order)
        assert extract_features(order)["longest_chain"] == 4
        assert np.array_equal(order, getattr(second, name))
    assert first.metadata == second.metadata
    meta = first.metadata
    assert meta["evaluations"] == steps
    assert meta["phase_one_evaluations"] + meta["phase_two_evaluations"] == steps
    assert meta["best_objective"] <= meta["initial_objective"]
    assert meta["post_search_integrity_evaluations"] == 2
    assert 0 <= meta["no_change_proposals"] <= meta["phase_two_evaluations"]
    assert 0 <= meta["selected_probability"] <= 1
    assert meta["minimum_attainable_r"] <= meta["height_fraction_vector"][0] <= meta["maximum_attainable_r"]
    measured = feature_vector(extract_features(first.multifeature_order))
    assert np.array_equal(measured, meta["multifeature_vector"])
    z = (measured - feature_vector(target)) / scale
    assert meta["best_objective"] == pytest.approx(np.sqrt(np.mean(z*z)))
    assert meta["multifeature_match"] == bool(np.max(np.abs(z)) <= 1)
    assert meta["height_fraction_match"] == (abs(meta["height_fraction_vector"][0] - target["ordering_fraction"]) <= .02)
    json.dumps(meta, allow_nan=False)


def test_search_evaluates_each_proposal_even_when_no_edges_are_mutable(monkeypatch):
    target = extract_features(total_order(2))
    original = generators.extract_features
    calls = []
    def count_features(order, **kwargs):
        calls.append(1)
        return original(order, **kwargs)
    monkeypatch.setattr(generators, "extract_features", count_features)
    result = generators.optimize_order(2, _rng(), target, np.ones(15))
    assert len(calls) == 64 + 2
    assert result.metadata["no_mutable_edges"]
    assert result.metadata["no_change_proposals"] == 52
    assert result.metadata["height_fraction_match"]
    assert result.metadata["multifeature_match"]
    assert result.metadata["best_objective"] == 0


def test_failed_search_is_returned_with_finite_metadata():
    target = extract_features(total_order(8))
    # A valid vector-shaped target can be unattainable within the prescribed
    # H=8 search; no attempt is made to conceal this mismatch or discard it.
    target["ordering_fraction"] = .25
    result = generators.optimize_order(8, _rng(), target, np.full(15, .01), steps=4)
    assert result.metadata["target_r_outside_attainable_bounds"]
    assert not result.metadata["height_fraction_match"]
    assert not result.metadata["multifeature_match"]
    assert result.metadata["status"] == "failed_match_within_budget"
    assert result.metadata["evaluations"] == 4
    json.dumps(result.metadata, allow_nan=False)


def test_attainable_endpoint_is_not_misclassified_by_subtractive_roundoff():
    # This layer composition has max r=16/45; computing 1-29/45 rounds
    # differently from relation_count/45 and must not create false infeasibility.
    donor = generators.layered_backbone_order(10, _rng(4), 2, 1.)
    target = extract_features(donor)
    result = generators.optimize_order(10, _rng(4), target, np.ones(15), steps=4)
    assert result.metadata["maximum_attainable_r"] == target["ordering_fraction"]
    assert not result.metadata["target_r_outside_attainable_bounds"]
    assert result.metadata["fraction_error"] == 0


@pytest.mark.parametrize("bad", [-1, 1.5, True, "4", np.nan])
def test_control_count_validation(bad):
    with pytest.raises(ValueError):
        generators.random_interval_order(bad, _rng())
    with pytest.raises(ValueError):
        generators.rank_intersection_order(bad, _rng())
    with pytest.raises(ValueError):
        generators.uniform_box_order(bad, _rng(), 2)


@pytest.mark.parametrize("family", [generators.random_interval_order,
                                   generators.rank_intersection_order])
def test_control_cap_and_generator_validation(family):
    with pytest.raises(ValueError, match="limit"):
        family(5, _rng(), max_count=4)
    with pytest.raises(ValueError, match="Generator"):
        family(4, 17)


@pytest.mark.parametrize("height", [0, -1, 7, 1.5, True, None])
def test_backbone_height_validation(height):
    with pytest.raises(ValueError):
        generators.layered_backbone_order(6, _rng(), height, .5)


@pytest.mark.parametrize("probability", [-.1, 1.1, np.nan, np.inf, True])
def test_backbone_probability_validation(probability):
    with pytest.raises(ValueError):
        generators.layered_backbone_order(6, _rng(), 3, probability)


@pytest.mark.parametrize("value", [0, -1, 65, 2.3, True])
def test_rank_count_validation(value):
    with pytest.raises(ValueError):
        generators.rank_intersection_order(4, _rng(), ranks=value)


@pytest.mark.parametrize("value", [1, 5, 2.3, True])
def test_box_dimension_validation(value):
    with pytest.raises(ValueError):
        generators.uniform_box_order(4, _rng(), value)


@pytest.mark.parametrize("scale", [np.ones(14), np.zeros(15), np.full(15, np.nan),
                                   np.full(15, np.inf), np.full(15, 1e-10),
                                   np.array(["x"] * 15), np.ones(15, dtype=bool)])
def test_search_scale_validation(scale):
    with pytest.raises(ValueError, match="scales"):
        generators.optimize_order(4, _rng(), extract_features(total_order(4)), scale)


@pytest.mark.parametrize("steps", [0, 3, True, 4.5])
def test_search_budget_validation(steps):
    with pytest.raises(ValueError, match="steps"):
        generators.optimize_order(4, _rng(), extract_features(total_order(4)), np.ones(15), steps=steps)


def test_search_rejects_undefined_donor_without_resampling():
    with pytest.raises(ValueError, match="height"):
        generators.optimize_order(4, _rng(), extract_features(antichain(4)), np.ones(15))


def test_search_rejects_inconsistent_and_malformed_target():
    target = extract_features(total_order(4))
    with pytest.raises(ValueError, match="count"):
        generators.optimize_order(5, _rng(), target, np.ones(15))
    target["chain_fraction"] = .5
    with pytest.raises(ValueError, match="height and chain"):
        generators.optimize_order(4, _rng(), target, np.ones(15))
    with pytest.raises(ValueError, match="dictionary"):
        generators.optimize_order(4, _rng(), None, np.ones(15))
    with pytest.raises(ValueError, match="at least two"):
        generators.optimize_order(1, _rng(), {}, np.ones(15))
