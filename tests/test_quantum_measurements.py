"""Exact cut-law, phase-scramble and local-gauge checks for measurement wiring."""
import numpy as np
import pytest

from causal_lab.quantum import (
    bell_product, ghz_state, haar_state, pair_observables, permute_state,
    plus_state, tfim_hamiltonian,
)
from causal_lab.quantum_measurements import balanced_cuts, cut_diagnostics, measure_state


@pytest.mark.parametrize("n", [6, 8, 10])
def test_balanced_cuts_are_distinct_unordered_bipartitions_and_replay(n):
    cuts = balanced_cuts(n, np.random.default_rng(301))
    assert cuts == balanced_cuts(n, np.random.default_rng(301))
    assert len(cuts) == 4
    assert len({tuple(cut) for cut in cuts}) == 4
    assert all(0 in cut and len(cut) == n//2 for cut in cuts)
    assert all(set(cut) != set(range(n))-set(other) for cut in cuts for other in cuts)


@pytest.mark.parametrize("n", [4, 6, 8])
def test_ghz_exact_cut_law_defect_for_every_recorded_region(n):
    state = ghz_state(n)
    cuts = balanced_cuts(n, np.random.default_rng(302))
    records, metrics = cut_diagnostics(state, pair_observables(state)["mi"], cuts)
    for record in records:
        size = len(record["region"])
        expected_prediction = size*(n-size)/2
        assert record["entropy"] == pytest.approx(1)
        assert record["pair_prediction"] == pytest.approx(expected_prediction)
        assert record["defect"] == pytest.approx(1-expected_prediction)
        assert record["normalized_defect"] == pytest.approx((1-expected_prediction)/max(1, expected_prediction))
    assert metrics["cut_singleton_mean_abs_defect"] == pytest.approx(abs(1-(n-1)/2))


@pytest.mark.parametrize("factory", [plus_state, bell_product])
def test_product_and_bell_cut_laws_hold_without_connected_geometry(factory):
    n = 6
    state = factory(n)
    records, metrics = cut_diagnostics(state, pair_observables(state)["mi"], balanced_cuts(n, np.random.default_rng(303)))
    for record in records:
        assert record["defect"] == pytest.approx(0, abs=1e-12)
    assert metrics["cut_balanced_mean_abs_defect"] < 1e-12
    if factory is plus_state:
        # The zero/zero convention must stay finite and exactly zero.
        assert all(record["normalized_defect"] == 0 for record in records)


def test_random_computational_phases_preserve_z_statistics_but_change_mi():
    n = 6
    state = plus_state(n)
    rng = np.random.default_rng(304)
    scrambled = state*np.exp(1j*rng.uniform(0, 2*np.pi, len(state)))
    np.testing.assert_allclose(np.abs(scrambled)**2, np.abs(state)**2, atol=1e-16)
    before, after = pair_observables(state), pair_observables(scrambled)
    np.testing.assert_allclose(before["connected_zz"], after["connected_zz"], atol=1e-12)
    assert np.max(after["mi"]-before["mi"]) > .01


def test_known_controlled_phase_creates_pair_entanglement_without_z_changes():
    n = 4
    state = plus_state(n)
    controlled_phase = np.ones(2**n)
    controlled_phase.reshape((2,)*n)[1,1] = -1
    scrambled = state*controlled_phase
    before, after = pair_observables(state), pair_observables(scrambled)
    np.testing.assert_allclose(before["connected_zz"], after["connected_zz"], atol=1e-12)
    assert after["mi"][0,1] == pytest.approx(2)
    assert after["negativity"][0,1] == pytest.approx(.5)
    assert before["mi"][0,1] == pytest.approx(0)


def test_shared_phase_scramble_preserves_state_pair_inner_product_and_distance():
    rng = np.random.default_rng(305)
    first, second = haar_state(4,rng), haar_state(4,rng)
    phases = np.exp(1j*rng.uniform(0,2*np.pi,len(first)))
    assert np.vdot(first*phases,second*phases) == pytest.approx(np.vdot(first,second))
    assert np.linalg.norm(first*phases-second*phases) == pytest.approx(np.linalg.norm(first-second))


def test_transported_cuts_and_pair_information_are_relabel_equivariant():
    state = haar_state(6,np.random.default_rng(306))
    permutation = np.array([5,1,3,0,4,2])
    inverse = np.argsort(permutation)
    cuts = balanced_cuts(6,np.random.default_rng(307))
    changed_cuts = [inverse[cut].tolist() for cut in cuts]
    before = measure_state(state,cuts)
    after = measure_state(permute_state(state,permutation),changed_cuts)
    before_balanced = [r for r in before["cuts"] if r["kind"] == "balanced"]
    after_balanced = [r for r in after["cuts"] if r["kind"] == "balanced"]
    for a,b in zip(before_balanced,after_balanced):
        for key in ("entropy","pair_prediction","defect","normalized_defect"):
            assert a[key] == pytest.approx(b[key],abs=1e-12)
    np.testing.assert_allclose(after["observables"]["mi"],before["observables"]["mi"][np.ix_(permutation,permutation)],atol=1e-12)


def test_local_x_gauge_changes_coupling_signs_without_changing_mi():
    n = 4
    rng = np.random.default_rng(308)
    upper = np.triu(rng.normal(size=(n,n)),1)
    couplings = upper+upper.T
    signs = np.array([-1,1,-1,1])
    gauged = couplings*signs[:,None]*signs[None,:]
    original_h = tfim_hamiltonian(couplings,1).toarray()
    changed_h = tfim_hamiltonian(gauged,1).toarray()
    unitary = np.array([[1.]])
    for sign in signs:
        unitary = np.kron(unitary,np.array([[0,1],[1,0]]) if sign == -1 else np.eye(2))
    np.testing.assert_allclose(changed_h,unitary@original_h@unitary.T,atol=1e-12)
    _, vectors = np.linalg.eigh(original_h)
    state = vectors[:,0]
    before, after = pair_observables(state), pair_observables(unitary@state)
    np.testing.assert_allclose(before["mi"],after["mi"],atol=1e-12)
    np.testing.assert_allclose(after["connected_zz"],before["connected_zz"]*signs[:,None]*signs[None,:],atol=1e-12)


def test_measurement_wiring_preserves_registered_diagnostics_and_null_denominator():
    state = ghz_state(6)
    result = measure_state(state,balanced_cuts(6,np.random.default_rng(309)),shuffle_rng=np.random.default_rng(310),nulls=3)
    assert set(result["inference"]) == {"1e-12","1e-09","1e-06"}
    assert len(result["nulls"]) == 3
    assert result["metrics"]["shuffle_minus_stress_d3"] == pytest.approx(0,abs=1e-12)
    assert result["metrics"]["shuffle_positive_participation_rank_mean"] == pytest.approx(5)
    assert result["metrics"]["entangled_pair_fraction"] == 0
    assert result["metrics"]["stress_d3_ambiguous"] == 1
    assert np.isnan(result["metrics"]["spearman_mi_negativity"])


def test_null_measurement_requires_explicit_random_stream():
    with pytest.raises(ValueError,match="explicit stream"):
        measure_state(ghz_state(4),[[0,1]],nulls=1)
