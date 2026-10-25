"""Independent analytic, tensor, spectral and dynamical quantum-core checks."""
import itertools
import math

import numpy as np
import pytest
from scipy.linalg import expm
from scipy.sparse.linalg import ArpackNoConvergence

import causal_lab.quantum as quantum
from causal_lab.quantum import (
    QuantumNumericalError, and_state, bell_product, density_matrix, entropy,
    evolve_state, ghz_state, ground_state, haar_state, negativity, normalize_state,
    pair_observables, partial_trace, permute_state, plus_state,
    random_product_state, reduced_density, tfim_hamiltonian,
)


X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)


def tensor(operators):
    result = np.array([[1]], dtype=complex)
    for operator in operators:
        result = np.kron(result, operator)
    return result


def local(operator, i, n):
    return tensor([operator if j == i else np.eye(2) for j in range(n)])


def independent_hamiltonian(J, h):
    n = len(J)
    matrix = np.zeros((2 ** n, 2 ** n), dtype=complex)
    for i in range(n):
        matrix -= h * local(X, i, n)
        for j in range(i + 1, n):
            matrix -= J[i, j] * local(Z, i, n) @ local(Z, j, n)
    return matrix


def independent_trace(rho, keep):
    n = round(math.log2(len(rho)))
    complement = [i for i in range(n) if i not in keep]
    result = np.zeros((2 ** len(keep), 2 ** len(keep)), dtype=complex)
    for a, b in itertools.product(range(2 ** len(keep)), repeat=2):
        for environment in range(2 ** len(complement)):
            left = [0] * n
            right = [0] * n
            for position, site in enumerate(keep):
                left[site] = (a >> (len(keep) - 1 - position)) & 1
                right[site] = (b >> (len(keep) - 1 - position)) & 1
            for position, site in enumerate(complement):
                bit = (environment >> (len(complement) - 1 - position)) & 1
                left[site] = right[site] = bit
            row = sum(bit << (n - 1 - i) for i, bit in enumerate(left))
            col = sum(bit << (n - 1 - i) for i, bit in enumerate(right))
            result[a, b] += rho[row, col]
    return result


def couplings(n, seed=901):
    upper = np.triu(np.random.default_rng(seed).normal(size=(n, n)), 1)
    return (upper + upper.T) / math.sqrt(max(1, n - 1))


def h2(p):
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p) if 0 < p < 1 else 0.0


@pytest.mark.parametrize("factory,n", [(plus_state, 6), (ghz_state, 8), (bell_product, 10)])
def test_analytic_state_normalization(factory, n):
    state = factory(n)
    assert state.shape == (2 ** n,)
    assert np.vdot(state, state) == pytest.approx(1, abs=1e-14)


def test_normalization_is_explicit_and_robust_to_scale():
    state = normalize_state([1e300, 1j * 1e300])
    np.testing.assert_allclose(state, [1 / math.sqrt(2), 1j / math.sqrt(2)])
    with pytest.raises(ValueError, match="already be normalized"):
        density_matrix([2, 0])
    with pytest.raises(ValueError, match="already be normalized"):
        pair_observables([2, 0])


@pytest.mark.parametrize("state", [[0, 0], [1, 0, 0], [np.nan, 0], [[1, 0]], []])
def test_bad_normalizations_rejected(state):
    with pytest.raises(ValueError):
        normalize_state(state)


@pytest.mark.parametrize("n", [0, -1, 11, 2.5, True])
def test_invalid_qubit_counts_rejected(n):
    with pytest.raises(ValueError):
        plus_state(n)


@pytest.mark.parametrize("keep", [(), (0,), (3, 1), (2, 0, 3), (3, 2, 1, 0)])
def test_pure_and_mixed_partial_traces_match_independent_bit_enumeration(keep):
    rng = np.random.default_rng(1947)
    state = haar_state(4, rng)
    pure = density_matrix(state)
    other = density_matrix(haar_state(4, rng))
    mixed = .3 * pure + .7 * other
    expected = independent_trace(pure, keep)
    np.testing.assert_allclose(reduced_density(state, keep), expected, atol=2e-15)
    np.testing.assert_allclose(partial_trace(pure, keep), expected, atol=2e-15)
    np.testing.assert_allclose(reduced_density(mixed, keep), independent_trace(mixed, keep), atol=2e-15)
    assert np.trace(partial_trace(mixed, keep)) == pytest.approx(1)
    assert np.min(np.linalg.eigvalsh(partial_trace(mixed, keep))) >= -1e-14


@pytest.mark.parametrize("keep", [(0, 0), (-1,), (4,), (1.0,), (True,), [[0]]])
def test_invalid_partial_trace_indices_rejected(keep):
    with pytest.raises(ValueError):
        reduced_density(plus_state(4), keep)
    with pytest.raises(ValueError):
        partial_trace(density_matrix(plus_state(4)), keep)


def test_pure_complementary_entropies_and_repeated_partial_trace():
    state = haar_state(5, np.random.default_rng(843))
    assert entropy(reduced_density(state, (0, 3))) == pytest.approx(
        entropy(reduced_density(state, (1, 2, 4))), abs=1e-12)
    first = reduced_density(state, (4, 1, 0))
    np.testing.assert_allclose(partial_trace(first, (2, 0)),
                               reduced_density(state, (0, 4)), atol=1e-14)
    assert entropy(np.array([[1]])) == 0


@pytest.mark.parametrize("rho", [np.eye(2), np.diag([1.1, -.1]),
                                 np.array([[1, 1], [0, 0]]),
                                 np.array([[1, np.nan], [np.nan, 0]]), np.eye(3) / 3])
def test_invalid_density_matrices_rejected(rho):
    with pytest.raises(ValueError):
        entropy(rho)
    with pytest.raises(ValueError):
        partial_trace(rho, ())


def test_entropy_roundoff_is_bounded_and_not_arbitrarily_repaired():
    assert entropy(np.diag([1 + 1e-12, -1e-12])) == pytest.approx(0)
    with pytest.raises(ValueError, match="positive semidefinite"):
        entropy(np.diag([1 + 1e-8, -1e-8]))
    assert entropy(np.eye(8) / 8) == pytest.approx(3)


def test_product_state_has_no_pair_information_or_entanglement():
    state = random_product_state(6, np.random.default_rng(3121))
    values = pair_observables(state)
    for key in ("single_entropy", "pair_entropy", "mi", "negativity", "log_negativity", "connected_zz"):
        np.testing.assert_allclose(values[key], 0, atol=1e-12)
    assert values["max_roundoff_correction"] <= 1e-10


def test_bell_pair_and_bell_product_exact_information():
    values = pair_observables(bell_product(6))
    np.testing.assert_allclose(values["single_entropy"], 1, atol=1e-14)
    for i in range(6):
        for j in range(i + 1, 6):
            paired = i // 2 == j // 2
            assert values["mi"][i, j] == pytest.approx(2 if paired else 0, abs=1e-13)
            assert values["negativity"][i, j] == pytest.approx(.5 if paired else 0, abs=1e-13)
            assert values["log_negativity"][i, j] == pytest.approx(1 if paired else 0, abs=1e-13)
            assert values["connected_zz"][i, j] == pytest.approx(1 if paired else 0, abs=1e-13)
    assert -math.log(values["mi"][0, 1] / 2) == pytest.approx(0, abs=1e-13)
    with pytest.raises(ValueError):
        bell_product(3)


@pytest.mark.parametrize("n", [3, 6, 10])
def test_ghz_total_pair_correlation_is_not_pair_entanglement(n):
    state = ghz_state(n)
    values = pair_observables(state)
    off_diagonal = ~np.eye(n, dtype=bool)
    np.testing.assert_allclose(values["single_entropy"], 1)
    np.testing.assert_allclose(values["pair_entropy"], 1)
    np.testing.assert_allclose(values["mi"][off_diagonal], 1)
    np.testing.assert_allclose(values["negativity"], 0, atol=1e-14)
    for count in (1, n // 2):
        cut = tuple(range(count))
        defect = entropy(reduced_density(state, cut)) - .5 * values["mi"][:count, count:].sum()
        assert defect == pytest.approx(1 - count * (n - count) / 2)


def test_purified_and_is_an_exact_raw_log_mi_triangle_counterexample():
    state = and_state()
    assert np.count_nonzero(state) == 4
    assert np.vdot(state, state) == 1
    mi = pair_observables(state)["mi"]
    expected = h2(.25) - .5
    assert mi[0, 2] == pytest.approx(0, abs=1e-14)
    assert mi[0, 1] == pytest.approx(expected, abs=1e-14)
    assert mi[1, 2] == pytest.approx(expected, abs=1e-14)
    for epsilon in (1e-12, 1e-9, 1e-6):
        distance = -np.log(np.maximum(mi, epsilon) / 2)
        assert distance[0, 2] > distance[0, 1] + distance[1, 2]
    # AB and AC are classical mixtures despite the pure five-qubit purification.
    assert negativity(reduced_density(state, (0, 1))) == pytest.approx(0, abs=1e-14)


def test_local_unitaries_preserve_information_but_not_basis_dependent_zz():
    rng = np.random.default_rng(5281)
    state = haar_state(4, rng)
    unitaries = []
    for _ in range(4):
        q, _ = np.linalg.qr(rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2)))
        unitaries.append(q)
    rotated = tensor(unitaries) @ state
    before, after = pair_observables(state), pair_observables(rotated)
    for key in ("single_entropy", "pair_entropy", "mi", "negativity", "log_negativity"):
        np.testing.assert_allclose(before[key], after[key], atol=1e-12)
    assert np.max(np.abs(before["connected_zz"] - after["connected_zz"])) > .01


def test_pair_observables_mixed_state_and_relabel_covariance():
    state = haar_state(4, np.random.default_rng(7721))
    before = pair_observables(state)
    mixed_api = pair_observables(density_matrix(state))
    permutation = np.array([2, 0, 3, 1])
    after = pair_observables(permute_state(state, permutation))
    for key in ("single_entropy", "pair_entropy", "mi", "negativity", "log_negativity", "connected_zz"):
        np.testing.assert_allclose(before[key], mixed_api[key], atol=1e-13)
        expected = before[key][permutation] if before[key].ndim == 1 else before[key][np.ix_(permutation, permutation)]
        np.testing.assert_allclose(after[key], expected, atol=1e-13)
    with pytest.raises(ValueError):
        permute_state(state, (0, 1))


def test_random_states_reproduce_explicit_streams_and_obey_bounds():
    for factory in (haar_state, random_product_state):
        one = factory(6, np.random.default_rng(912))
        two = factory(6, np.random.default_rng(912))
        np.testing.assert_array_equal(one, two)
        assert abs(np.vdot(one, one) - 1) < 1e-14
        with pytest.raises(ValueError, match="Generator"):
            factory(2, None)
    values = pair_observables(one)
    assert np.all((values["mi"] >= 0) & (values["mi"] <= 2))
    assert np.all((values["negativity"] >= 0) & (values["negativity"] <= .5))


@pytest.mark.parametrize("n,h", [(1, .5), (2, 2), (3, .5), (4, 1)])
def test_sparse_hamiltonian_equals_independent_kronecker_construction(n, h):
    J = couplings(n)
    actual = tfim_hamiltonian(J, h)
    np.testing.assert_allclose(actual.toarray(), independent_hamiltonian(J, h), atol=1e-14)
    assert actual.format == "csr"
    np.testing.assert_array_equal(actual.toarray(), actual.toarray().conj().T)
    assert np.trace(actual.toarray()) == pytest.approx(0)


@pytest.mark.parametrize("J,h", [(np.ones((2, 2)), 1),
                                (np.array([[0, 1], [0, 0]]), 1),
                                (np.zeros((2, 2)), 0), (np.zeros((2, 2)), -1),
                                (np.zeros((2, 2)), np.nan),
                                (np.zeros((2, 2)), 1 + 0j),
                                (np.zeros((2, 2), dtype=complex), 1),
                                (np.zeros((11, 11)), 1)])
def test_invalid_hamiltonians_rejected(J, h):
    with pytest.raises(ValueError):
        tfim_hamiltonian(J, h)


@pytest.mark.parametrize("n,h", [(1, 1), (3, .5), (4, 1), (5, 2)])
def test_sparse_ground_and_gap_match_dense_independent_solver(n, h):
    J = couplings(n, seed=312)
    solution = ground_state(J, h, np.random.default_rng(981))
    energies, vectors = np.linalg.eigh(independent_hamiltonian(J, h))
    assert solution["valid"]
    assert solution["energy"] == pytest.approx(energies[0], abs=2e-11)
    assert solution["gap"] == pytest.approx(energies[1] - energies[0], abs=2e-11)
    assert abs(np.vdot(solution["state"], vectors[:, 0])) == pytest.approx(1, abs=1e-11)
    assert solution["scaled_residual"] < 1e-10
    assert solution["negative_amplitude_norm"] < 1e-12
    alternate = ground_state(J, h, np.random.default_rng(347))
    assert alternate["energy"] == pytest.approx(solution["energy"], abs=2e-11)
    assert alternate["gap"] == pytest.approx(solution["gap"], abs=2e-11)


@pytest.mark.parametrize("J,h", [(0, .5), (.8, 1), (-.8, 1), (8, .5)])
def test_exact_two_qubit_spectrum_entropy_negativity_and_small_gap(J, h):
    solution = ground_state([[0, J], [J, 0]], h, np.random.default_rng(9134))
    scale = math.sqrt(4 * h * h + J * J)
    q = (1 - 2 * h / scale) / 2
    assert solution["energy"] == pytest.approx(-scale, abs=1e-12)
    assert solution["gap"] == pytest.approx(scale - abs(J), abs=1e-12)
    values = pair_observables(solution["state"])
    assert values["mi"][0, 1] == pytest.approx(2 * h2(q), abs=1e-12)
    assert values["negativity"][0, 1] == pytest.approx(abs(J) / (2 * scale), abs=1e-12)


@pytest.mark.parametrize("n", [6, 8, 10])
def test_registered_size_cap_symmetric_ground_has_identical_pair_marginals(n):
    J = (np.ones((n, n)) - np.eye(n)) / (n - 1)
    solution = ground_state(J, 1, np.random.default_rng(3922))
    values = pair_observables(solution["state"])
    triangle = np.triu_indices(n, 1)
    for key in ("mi", "negativity", "connected_zz", "pair_entropy"):
        assert np.ptp(values[key][triangle]) < 1e-10


def test_x_sign_gauge_covariance_and_relabel_ground_state():
    n, h = 4, .7
    J = couplings(n, 591)
    signs = np.array([1, -1, -1, 1])
    gauge = tensor([np.eye(2) if s == 1 else X for s in signs])
    first = ground_state(J, h, np.random.default_rng(922))
    second = ground_state(J * np.outer(signs, signs), h, np.random.default_rng(142))
    assert second["energy"] == pytest.approx(first["energy"], abs=1e-12)
    assert abs(np.vdot(second["state"], gauge @ first["state"])) == pytest.approx(1)
    before, after = pair_observables(first["state"]), pair_observables(second["state"])
    np.testing.assert_allclose(before["mi"], after["mi"], atol=1e-12)
    np.testing.assert_allclose(before["negativity"], after["negativity"], atol=1e-12)
    np.testing.assert_allclose(before["connected_zz"] * np.outer(signs, signs), after["connected_zz"], atol=1e-12)
    permutation = np.array([3, 0, 2, 1])
    third = ground_state(J[np.ix_(permutation, permutation)], h, np.random.default_rng(1312))
    assert abs(np.vdot(third["state"], permute_state(first["state"], permutation))) == pytest.approx(1)


def test_j_zero_ground_and_first_excitation_do_not_stay_in_even_sector():
    n, h = 6, .8
    solution = ground_state(np.zeros((n, n)), h, np.random.default_rng(621))
    assert solution["energy"] == pytest.approx(-n * h, abs=1e-12)
    assert solution["gap"] == pytest.approx(2 * h, abs=1e-12)
    assert abs(np.vdot(solution["state"], plus_state(n))) == pytest.approx(1)


def test_failed_eigensolver_is_not_reseeded_and_retains_diagnostics(monkeypatch):
    calls = []

    def fail(*args, **kwargs):
        calls.append(kwargs["v0"].copy())
        raise ArpackNoConvergence("deliberate test failure", np.array([-1.]), np.zeros((4, 1)))

    monkeypatch.setattr(quantum, "eigsh", fail)
    with pytest.raises(QuantumNumericalError) as caught:
        ground_state([[0, 1], [1, 0]], 1, np.random.default_rng(424))
    assert len(calls) == 1
    assert caught.value.diagnostics["partial_eigenvalues"] == [-1.]
    assert not caught.value.diagnostics["valid"]


def test_wrong_or_unresolved_eigenpairs_are_rejected_with_retained_checks(monkeypatch):
    def wrong(*args, **kwargs):
        return np.array([-3., -3.]), np.eye(4)[:, :2]

    monkeypatch.setattr(quantum, "eigsh", wrong)
    with pytest.raises(QuantumNumericalError) as caught:
        ground_state([[0, 1], [1, 0]], 1, np.random.default_rng(424))
    assert "scaled_residual" in caught.value.diagnostics["failure"]
    assert "unresolved_gap" in caught.value.diagnostics["failure"]


def test_nonfinite_eigenpairs_are_rejected_instead_of_evading_comparisons(monkeypatch):
    monkeypatch.setattr(quantum, "eigsh", lambda *a, **k:
                        (np.array([np.nan, 1.]), np.eye(4)[:, :2]))
    with pytest.raises(QuantumNumericalError) as caught:
        ground_state([[0, 1], [1, 0]], 1, np.random.default_rng(424))
    assert caught.value.diagnostics["failure"] == "nonfinite_eigenpairs"


def test_sparse_unitary_evolution_matches_dense_exponential_and_reverses():
    J, h = couplings(4, 537), .8
    state = random_product_state(4, np.random.default_rng(813))
    matrix = independent_hamiltonian(J, h)
    for time in (.5, 1, 2):
        actual = evolve_state(J, h, state, time)
        np.testing.assert_allclose(actual, expm(-1j * time * matrix) @ state, atol=2e-13)
        np.testing.assert_allclose(evolve_state(J, h, actual, -time), state, atol=5e-13)
        assert np.vdot(actual, matrix @ actual) == pytest.approx(np.vdot(state, matrix @ state), abs=2e-12)
    np.testing.assert_array_equal(evolve_state(J, h, state, 0), state)
    with pytest.raises(ValueError):
        evolve_state(J, h, plus_state(3), 1)
    with pytest.raises(ValueError):
        evolve_state(J, h, state, np.inf)
    with pytest.raises(ValueError):
        evolve_state(J, h, state, 1 + 0j)


def test_infinitesimal_commutator_has_correct_sign_and_direct_coupling_coefficient():
    n, i, j = 3, 0, 2
    J, h = couplings(n, 127), .9
    H = independent_hamiltonian(J, h)
    Xi, Xj = local(X, i, n), local(X, j, n)
    coefficient = 4j * J[i, j] * local(Y, i, n) @ local(Y, j, n)
    first_derivative = 1j * (H @ Xi - Xi @ H)
    np.testing.assert_allclose(first_derivative @ Xj - Xj @ first_derivative,
                               coefficient, atol=1e-14)
    errors = []
    for time in (1e-3, 5e-4):
        unitary = expm(-1j * time * H)
        evolved = unitary.conj().T @ Xi @ unitary
        commutator = evolved @ Xj - Xj @ evolved
        errors.append(np.linalg.norm(commutator - time * coefficient))
    assert errors[1] / errors[0] == pytest.approx(.25, rel=.005)


def test_high_field_analytic_two_qubit_information_has_registered_leading_term():
    h = 1.0
    errors = []
    for J in (.08, .04):
        result = ground_state([[0, J], [J, 0]], h, np.random.default_rng(520))
        measured = pair_observables(result["state"])["mi"][0, 1]
        leading = J * J / (8 * h * h) * math.log2(16 * math.e * h * h / (J * J))
        errors.append(abs(measured - leading))
    assert errors[1] < .08 * errors[0]
