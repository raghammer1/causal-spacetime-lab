"""Independent audit anchors and deliberately corrupted archive checks."""
from copy import deepcopy
import gzip
import hashlib
from itertools import combinations
import json

import numpy as np
import pytest

from causal_lab.quantum_audit import (
    _Checks, _audit_pairing, audit_archive, basis_groups, bit_hamiltonian_action,
    expected_schedule, explicit_negativity, explicit_reduction, schmidt_entropy,
)


def ghz_record():
    n = 6
    state = np.zeros(2**n)
    state[[0, -1]] = 1/np.sqrt(2)
    zero = np.zeros((n, n))
    mi = np.ones((n, n))-np.eye(n)
    cuts = []
    regions = [("singleton", (i,)) for i in range(n)]
    regions += [("balanced", (0, *rest)) for rest in list(combinations(range(1, n), 2))[:4]]
    for kind, region in regions:
        prediction = len(region)*(n-len(region))/2
        cuts.append(dict(kind=kind, region=list(region), entropy=1., pair_prediction=prediction,
                         defect=1-prediction, normalized_defect=(1-prediction)/max(1, prediction),
                         numerically_zero_cut=False))
    return dict(sample_id="analytic-ghz", unit_id="analytic-ghz", family="GHZ", n=n,
                batch=0, rep=-1, h=0., preparation="control", delta=0., time=0., status="ok",
                state={"real": state.tolist(), "imag": np.zeros_like(state).tolist()},
                cuts=cuts, observables=dict(single_entropy=np.ones(n).tolist(),
                    pair_entropy=np.ones((n, n)).tolist(), mi=mi.tolist(),
                    negativity=zero.tolist(), log_negativity=zero.tolist(), connected_zz=mi.tolist()))


def archive(tmp_path, row):
    with gzip.open(tmp_path/"raw.jsonl.gz", "wt") as handle:
        handle.write(json.dumps(row)+"\n")
    (tmp_path/"metadata.json").write_text(json.dumps({"repeats": 8, "source_commit": "a"*40}))
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in tmp_path.iterdir() if p.name != "manifest.json"}
    (tmp_path/"manifest.json").write_text(json.dumps({"sha256": files}))


def test_explicit_basis_groups_preserve_requested_bit_order():
    groups = basis_groups(3, (2, 0))
    np.testing.assert_array_equal(groups, [[0, 2], [4, 6], [1, 3], [5, 7]])
    state = np.zeros(8)
    state[1] = 1
    np.testing.assert_array_equal(explicit_reduction(state, 3, (2, 0)), np.diag([0, 0, 1, 0]))
    with pytest.raises(ValueError):
        basis_groups(3, (0, 0))


def test_w_state_partial_traces_and_singular_value_entropy():
    state = np.zeros(8)
    state[[1, 2, 4]] = 1/np.sqrt(3)
    expected = np.zeros((4, 4))
    expected[0, 0] = 1/3
    expected[1:3, 1:3] = 1/3
    np.testing.assert_allclose(explicit_reduction(state, 3, (0, 1)), expected, atol=1e-15)
    np.testing.assert_allclose(explicit_reduction(state, 3, (0,)), np.diag([2/3, 1/3]), atol=1e-15)
    entropy = -(1/3)*np.log2(1/3)-(2/3)*np.log2(2/3)
    assert schmidt_entropy(state, 3, (0,)) == pytest.approx(entropy)
    assert schmidt_entropy(state, 3, (0, 1)) == pytest.approx(entropy)


def test_explicit_partial_transpose_bell_and_separable_mixture():
    bell = np.array([1, 0, 0, 1])/np.sqrt(2)
    assert explicit_negativity(np.outer(bell, bell)) == pytest.approx(.5)
    assert explicit_negativity(np.diag([.5, 0, 0, .5])) == 0


def test_direct_bit_hamiltonian_matches_separate_pauli_tensor_construction():
    n = 3
    X, Z, identity = np.array([[0, 1], [1, 0]]), np.diag([1, -1]), np.eye(2)
    def local(operator, site):
        result = np.ones((1, 1))
        for i in range(n):
            result = np.kron(result, operator if i == site else identity)
        return result
    coupling = np.array([[0, .7, -.2], [.7, 0, .3], [-.2, .3, 0]])
    state = np.arange(1, 9)+1j*np.arange(8, 0, -1)
    state /= np.linalg.norm(state)
    H = -sum(.4*local(X, i) for i in range(n))
    for i, j in combinations(range(n), 2):
        H -= coupling[i, j]*local(Z, i)@local(Z, j)
    np.testing.assert_allclose(bit_hamiltonian_action(state, coupling, .4), H@state, atol=1e-15)


def test_full_registered_schedule_counts_independent_of_runner():
    schedule = expected_schedule(8)
    assert len(schedule) == 1818
    assert sum(row[5] == "ground" for row in schedule) == 873
    assert sum(row[5] == "phase_scrambled" for row in schedule) == 648
    assert sum(row[5].startswith("quench") for row in schedule) == 144
    assert all(sum(row[1] == n for row in schedule) == 606 for n in (6, 8, 10))


def test_analytic_archive_independently_recomputes_every_pair_and_cut(tmp_path):
    archive(tmp_path, ghz_record())
    result = audit_archive(tmp_path, verify_schedule=False)
    assert result["passed"] and result["all_scheduled_states_ok"]
    assert result["counts"]["states_audited"] == 1
    assert result["counts"]["pair_reductions"] == 15
    assert result["counts"]["cut_svd_entropies"] == 10
    assert max(result["max_absolute_errors"].values()) < 1e-12


@pytest.mark.parametrize("damage", ["mi", "cut_entropy", "norm", "nonfinite"])
def test_numerical_corruption_is_reported_even_with_valid_file_hashes(tmp_path, damage):
    row = ghz_record()
    if damage == "mi":
        row["observables"]["mi"][0][1] = .3
    elif damage == "cut_entropy":
        row["cuts"][0]["entropy"] = .5
    elif damage == "norm":
        row["state"]["real"][0] = .8
    else:
        row["state"]["real"][0] = float("nan")
    archive(tmp_path, row)
    result = audit_archive(tmp_path, verify_schedule=False)
    assert not result["passed"]
    assert result["failures"]


def test_missing_schedule_and_bad_manifest_are_retained(tmp_path):
    archive(tmp_path, ghz_record())
    (tmp_path/"metadata.json").write_text(json.dumps({"repeats": 8, "source_commit": "b"*40}))
    result = audit_archive(tmp_path)
    assert not result["passed"]
    assert {failure["check"] for failure in result["failures"]} >= {"artifact_hash", "registered_schedule"}


def test_missing_numerical_values_are_failures_not_silent_skips():
    checks = _Checks(1e-9)
    checks.compare("damaged", "missing", None, 0.)
    checks.compare("damaged", "invalid", "unavailable", 0.)
    assert len(checks.failures) == 2
    assert checks.counts["nonfinite_failures"] == 1


def test_archived_ground_energy_is_checked_by_independent_operator_action(tmp_path):
    row = ghz_record()
    row.update(family="B", preparation="ground", h=1., rep=0,
               couplings=np.zeros((6, 6)).tolist(), solver={"energy": -6.})
    row["state"]["real"] = np.full(64, 1/8).tolist()
    for key, value in row["observables"].items():
        row["observables"][key] = np.zeros_like(value).tolist()
    for cut in row["cuts"]:
        for key in ("entropy", "pair_prediction", "defect", "normalized_defect"):
            cut[key] = 0.
        cut["numerically_zero_cut"] = True
    archive(tmp_path, row)
    result = audit_archive(tmp_path, verify_schedule=False)
    assert result["passed"] and result["counts"]["ground_hamiltonian_actions"] == 1
    row["solver"]["energy"] = -5.
    archive(tmp_path, row)
    result = audit_archive(tmp_path, verify_schedule=False)
    assert not result["passed"]
    assert {failure["check"] for failure in result["failures"]} >= {"ground_energy", "ground_scaled_residual"}


def test_shared_phase_corruption_is_detected_without_dividing_by_zero():
    state = np.array([1, 0, 0, 1], dtype=complex)/np.sqrt(2)
    phases = np.array([1, 1j, -1, -1j])
    common = dict(n=2, family="B", connected=np.array([[0, 1], [1, 0]]),
                  couplings=np.zeros((2, 2)), cuts=[], noise=None)
    states = {
        "base": dict(common, state=state, preparation="ground", delta=0.,
                     source_state_id=None, baseline_id=None),
        "phase": dict(common, state=state*phases, preparation="phase_scrambled", delta=0.,
                      source_state_id="base", baseline_id=None),
        "pert": dict(common, state=state, preparation="ground", delta=.01,
                     source_state_id=None, baseline_id="base"),
        "pertphase": dict(common, state=state*phases, preparation="phase_scrambled", delta=.01,
                          source_state_id="pert", baseline_id="phase")}
    states["pert"]["noise"] = np.zeros((2, 2))
    checks = _Checks(1e-9)
    _audit_pairing(states, checks)
    assert not checks.failures
    changed = deepcopy(states)
    changed["pertphase"]["state"][-1] *= -1
    checks = _Checks(1e-9)
    _audit_pairing(changed, checks)
    assert any(row["check"] == "shared_phase_vector" for row in checks.failures)
