"""Integration checks for keyed independence and complete experiment accounting."""
from dataclasses import replace
import json

import numpy as np
import pytest

from causal_lab.local_random import identity, rng_for
from causal_lab.local_structure_study import (StudyConfig, _degree_profile, _mean_ci,
                                               _run_fit, summarize)
from causal_lab.local_statistics import build_reference


def small_config():
    return StudyConfig(counts=(32,), dimensions=(2,), fits=1, repeats=1,
                       fiber_repeats=1, reference4=8, reference8=4,
                       motif_draws=32, bootstrap_draws=16, workers=1)


def test_streams_replay_and_separate_roles():
    key = (20261025, 1, "final", "diamond", 3, 64, 7)
    assert np.array_equal(rng_for(*key).integers(2**32, size=16),
                          rng_for(*key).integers(2**32, size=16))
    ids = {identity(20261025, fit, phase, family, d, n, repeat, parameter)
           for fit in (0, 1) for phase in ("final", "motif", "search", "reference4")
           for family in ("diamond", "slab") for d in (2, 3) for n in (64, 128)
           for repeat in (0, 1) for parameter in (None, "fixed")}
    assert len(ids) == 2*4*2*2*2*2*2


@pytest.mark.parametrize("changes", [{"counts": (16,)}, {"counts": (32, 32)},
    {"counts": (544,)}, {"dimensions": (2, 5)}, {"repeats": 0}, {"fits": True},
    {"motif_draws": 1}, {"bootstrap_draws": 1}, {"wall_seconds": float("inf")}])
def test_config_rejects_unregistered_or_undefined_shapes(changes):
    with pytest.raises(ValueError):
        replace(small_config(), **changes).validate()


def test_fit_replay_complete_pair_and_search_accounting():
    config = small_config()
    first, second = _run_fit(config, 0), _run_fit(config, 0)
    assert first[:3] == second[:3]
    rows, pairs, searches, _ = first
    assert len(rows) == 13  # three regions, three ranks/intervals, four pair members, three checkpoints
    assert len({row["sample_id"] for row in rows}) == len(rows)
    assert len(pairs) == 2 and len(searches) == 1
    by_id = {row["sample_id"]: row for row in rows}
    for pair in pairs:
        a, b = by_id[pair["first_sample_id"]], by_id[pair["second_sample_id"]]
        assert (a["relations"], a["longest_chain"], a["interval_histogram"]) == (
            b["relations"], b["longest_chain"], b["interval_histogram"])
        assert a["joint_degree_profile"] == b["joint_degree_profile"]
        assert b["n22"]-a["n22"] == pair["expected_n22_difference"]
    assert sum(searches[0]["outcomes"].values()) == 16
    json.dumps(first[:3], allow_nan=False)


def test_parent_streams_do_not_change_with_enumeration_order():
    config = replace(small_config(), dimensions=(2, 3))
    a = _run_fit(config, 0)[0]
    b = _run_fit(replace(config, dimensions=(3, 2)), 0)[0]
    assert {r["sample_id"]: r for r in a} == {r["sample_id"]: r for r in b}


def test_equal_fit_mean_and_constant_zero_uncertainty():
    result = _mean_ci([[1., 1.], [3.] * 20], np.random.default_rng(5), 1000)
    assert result["estimate"] == 2.
    zero = _mean_ci([[0.]*5]*3, np.random.default_rng(5), 100)
    assert zero["ci95"] == [0., 0.]
    missing = _mean_ci([[], [1.]], np.random.default_rng(5), 100)
    assert missing["estimate"] is None


def test_summary_retains_sparse_inconclusive_and_exact_pair_contrast():
    config = small_config()
    rows, pairs, searches, _ = _run_fit(config, 0)
    reference = build_reference(2, 0, config.seed)
    summary = summarize(config, rows, [reference], pairs, searches)
    assert len(summary["conditional"]) == 13
    assert all(metric["status"] == "insufficient_information" for report in summary["conditional"]
               for metric in report["pooled"] if metric["tolerance"] is not None)
    assert all(row["deterministic_contrast"] for row in summary["pairs"])
    assert summary["searches"][0]["search_count"] == 1
    json.dumps(summary, allow_nan=False)


def test_degree_profile_keeps_joint_not_only_separate_marginals():
    order = np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]], dtype=bool)
    assert _degree_profile(order) == [[0, 2, 1], [1, 1, 1], [2, 0, 1]]
