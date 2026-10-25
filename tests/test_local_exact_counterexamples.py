"""Tests for the explicitly post-registration analytic extension."""
import importlib.util
import itertools
from pathlib import Path

import numpy as np

from causal_lab.local_structure import local_observables, motif_counts


source = Path(__file__).resolve().parents[1] / "scripts" / "local_exact_counterexamples.py"
spec = importlib.util.spec_from_file_location("local_exact_counterexamples", source)
extension = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extension)


def test_full_vector_collision_is_independently_verified():
    report = extension.verify()
    assert report["registration_status"].startswith("post-registration")
    assert report["global_comparability_component_sizes"] == [[12], [6, 6]]
    assert report["independent_bruteforce_n22"] == [42, 42]


def test_collision_orders_are_height_two_degree_two_without_four_cycles():
    for order in extension.collision_pair():
        assert not np.any(order.astype(int) @ order.astype(int))
        assert np.all(order.sum(axis=0) + order.sum(axis=1) == 2)
        for lower in itertools.combinations(range(6), 2):
            for upper in itertools.combinations(range(6, 12), 2):
                assert not np.all(order[np.ix_(lower, upper)])


def test_collision_does_not_depend_on_labels_or_duality():
    rng = np.random.default_rng(20261025)
    first, second = extension.collision_pair()
    expected = local_observables(first)
    expected_motifs = motif_counts(first)
    for order in (first, second):
        for candidate in (order, order.T):
            permutation = rng.permutation(12)
            relabeled = candidate[np.ix_(permutation, permutation)]
            assert local_observables(relabeled) == expected
            assert motif_counts(relabeled) == expected_motifs
