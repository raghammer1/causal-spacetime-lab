"""Independent tensor-matrix and analytic verification of matter/link dynamics."""
from dataclasses import replace
from itertools import combinations, permutations
import math

import numpy as np
import pytest
from scipy.linalg import expm
from scipy.sparse.linalg import ArpackNoConvergence

import causal_lab.dynamical_core as core
from causal_lab.dynamical_core import (
    DynamicalNumericalError, Parameters, born_probabilities, build_hamiltonian,
    direct_response_slopes, evolve_state, evolve_trajectory, ground_state,
    hamiltonian_diagonal, hamiltonian_trace, matter_bloch, matter_parity,
    permute_state, product_state, response_trajectories, state_diagnostics,
    vertex_axis_permutation, y_kick,
)


X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1., -1.]).astype(complex)


def tensor(factors):
    answer = np.array([[1.]], dtype=complex)
    for factor in factors:
        answer = np.kron(answer, factor)
    return answer


def local(operator, axis, Q):
    return tensor([operator if i == axis else np.eye(2) for i in range(Q)])


def dense_hamiltonian(params):
    """Build separate tensor operators, including quadratic number operators."""
    identity = np.eye(params.dimension, dtype=complex)
    result = np.zeros_like(identity)
    degree = [np.zeros_like(identity) for _ in range(params.N)]
    for i in range(params.N):
        result -= params.h * local(X, i, params.Q)
    for edge, (i, j) in enumerate(combinations(range(params.N), 2)):
        number = (identity - local(Z, params.N + edge, params.Q)) / 2
        result -= params.g * number @ local(Z, i, params.Q) @ local(Z, j, params.Q)
        result += params.mu * number - params.Gamma * local(X, params.N + edge, params.Q)
        degree[i] += number
        degree[j] += number
    for number in degree:
        result += params.U * number @ (number - identity) / 2
    return result


def random_state(params, seed=721):
    rng = np.random.default_rng(seed)
    vector = rng.normal(size=params.dimension) + 1j * rng.normal(size=params.dimension)
    return vector / np.linalg.norm(vector)


def parameters(N=3):
    return Parameters(N=N, h=.8, g=1.1, Gamma=.35, mu=-.7, U=.9)


def independent_density(state, site, Q):
    """Explicit bit-index partial trace, without production tensor reductions."""
    answer = np.zeros((2, 2), dtype=complex)
    mask = 1 << (Q - 1 - site)
    for index in range(len(state)):
        if not index & mask:
            amplitudes = [state[index], state[index | mask]]
            for a in range(2):
                for b in range(2):
                    answer[a, b] += amplitudes[a] * amplitudes[b].conjugate()
    return answer


def direct_basis_energy(params, basis):
    bits = [(basis >> (params.Q - 1 - i)) & 1 for i in range(params.Q)]
    degrees = [0] * params.N
    energy = 0.
    for edge, (i, j) in enumerate(combinations(range(params.N), 2)):
        active = bits[params.N + edge]
        energy += active * (params.mu - params.g * (1 - 2 * bits[i]) * (1 - 2 * bits[j]))
        degrees[i] += active
        degrees[j] += active
    return energy + params.U * sum(d * (d - 1) / 2 for d in degrees)


@pytest.mark.parametrize("N", [1, 2, 3])
@pytest.mark.parametrize("mode", ["csr", "matrix_free"])
def test_hamiltonian_matches_independent_dense_tensor_construction(N, mode):
    params = parameters(N)
    model = build_hamiltonian(params, representation=mode)
    expected = dense_hamiltonian(params)
    actual = model.operator @ np.eye(params.dimension)
    np.testing.assert_allclose(actual, expected, atol=2e-14)
    np.testing.assert_allclose(actual, actual.conj().T, atol=2e-14)
    np.testing.assert_allclose(model.diagonal, np.diag(expected).real, atol=2e-14)
    assert model.trace == pytest.approx(np.trace(expected).real, abs=2e-12)
    assert model.norm_bound >= np.max(np.abs(np.linalg.eigvalsh(expected))) - 1e-12


def test_matrix_free_complex_block_and_adjoint_actions():
    params = parameters()
    model = build_hamiltonian(params, representation="matrix_free")
    matrix = dense_hamiltonian(params)
    rng = np.random.default_rng(782)
    block = rng.normal(size=(params.dimension, 3)) + 1j * rng.normal(size=(params.dimension, 3))
    np.testing.assert_allclose(model.operator @ block, matrix @ block, atol=1e-13)
    np.testing.assert_allclose(model.operator.H @ block, matrix.conj().T @ block, atol=1e-13)
    first, second = block[:, 0], block[:, 1]
    assert np.vdot(first, model.operator @ second) == pytest.approx(np.vdot(model.operator @ first, second), abs=1e-12)


@pytest.mark.parametrize("N", [2, 3, 4, 5])
def test_trace_is_nonzero_and_analytically_correct(N):
    params = Parameters(N, 1., 1., .25, .1, 1.)
    model = build_hamiltonian(params)
    analytic_mean = .1 * params.M / 2 + N * (N - 1) * (N - 2) / 8
    assert model.trace == pytest.approx(params.dimension * analytic_mean)
    assert model.trace == pytest.approx(model.operator.diagonal().sum(), abs=2e-9)
    assert model.trace != 0


def test_n6_uses_bounded_matrix_free_storage_and_correct_bit_flips():
    params = parameters(6)
    model = build_hamiltonian(params)
    assert params.Q == 21 and params.dimension == 2097152
    assert model.representation == "matrix_free"
    assert model.diagonal.nbytes == 16 * 1024 ** 2
    basis = 12345
    vector = np.zeros(params.dimension)
    vector[basis] = 1
    actual = model.operator @ vector
    expected_indices = {basis}
    assert actual[basis] == pytest.approx(direct_basis_energy(params, basis))
    for axis in range(params.Q):
        target = basis ^ (1 << (params.Q - 1 - axis))
        expected_indices.add(target)
        assert actual[target] == pytest.approx(-params.h if axis < params.N else -params.Gamma)
    assert set(np.flatnonzero(actual)) == expected_indices
    with pytest.raises(ValueError, match="CSR"):
        build_hamiltonian(params, representation="csr")


@pytest.mark.parametrize("kwargs", [dict(N=0), dict(N=7), dict(N=True), dict(h=-1),
                                    dict(Gamma=-1), dict(U=-1), dict(mu=np.nan), dict(g=1j)])
def test_invalid_parameters_rejected(kwargs):
    specification = dict(N=3, h=1, g=1, Gamma=1, mu=1, U=1)
    specification.update(kwargs)
    with pytest.raises(ValueError):
        Parameters(**specification)


def test_product_factors_bloch_parity_and_exact_born_law():
    N, theta = 4, math.pi / 4
    probabilities = np.linspace(.2, .7, 6)
    phases = np.linspace(.1, 2., 6)
    state = product_state(N, theta, probabilities, phases)
    expected = np.array([1.], dtype=complex)
    for _ in range(N):
        expected = np.kron(expected, [math.cos(theta / 2), math.sin(theta / 2)])
    for p, phase in zip(probabilities, phases):
        expected = np.kron(expected, [math.sqrt(1 - p), np.exp(1j * phase) * math.sqrt(p)])
    np.testing.assert_allclose(state, expected, atol=2e-15)
    np.testing.assert_allclose(matter_bloch(state, N), np.tile([math.sin(theta), 0, math.cos(theta)], (N, 1)), atol=1e-14)
    assert matter_parity(state, N) == pytest.approx(math.sin(theta) ** N)
    born = np.array([1.])
    for p in probabilities:
        born = np.kron(born, [1 - p, p])
    np.testing.assert_allclose(born_probabilities(state, N), born, atol=1e-14)


@pytest.mark.parametrize("probabilities,phases", [([-1, .5, .5], [0, 0, 0]),
                                                  ([.5, .5], [0, 0]),
                                                  ([.5, .5, .5], [0, np.inf, 0])])
def test_product_state_rejects_invalid_factors(probabilities, phases):
    with pytest.raises(ValueError):
        product_state(3, math.pi / 4, probabilities, phases)


def test_entangled_state_reductions_match_explicit_bit_traces():
    params = parameters()
    state = random_state(params)
    bloch = matter_bloch(state, params.N)
    for site in range(params.N):
        rho = independent_density(state, site, params.Q)
        expected = [np.trace(rho @ operator).real for operator in (X, Y, Z)]
        np.testing.assert_allclose(bloch[site], expected, atol=1e-14)
        assert np.trace(rho) == pytest.approx(1)
    expected_born = np.zeros(1 << params.M)
    for basis, amplitude in enumerate(state):
        expected_born[basis % (1 << params.M)] += abs(amplitude) ** 2
    np.testing.assert_allclose(born_probabilities(state, params.N), expected_born, atol=1e-14)
    parity = tensor([X] * params.N + [np.eye(2)] * params.M)
    assert matter_parity(state, params.N) == pytest.approx(np.vdot(state, parity @ state).real)


def test_y_kick_has_correct_phase_and_no_instant_target_signal():
    params = parameters()
    state = random_state(params)
    before = matter_bloch(state, params.N)
    for source in range(params.N):
        kicked = y_kick(state, params.N, source)
        np.testing.assert_allclose(kicked, local(Y, source, params.Q) @ state, atol=1e-14)
        np.testing.assert_allclose(y_kick(kicked, params.N, source), state, atol=1e-14)
        after = matter_bloch(kicked, params.N)
        for target in range(params.N):
            if target != source:
                np.testing.assert_allclose(after[target], before[target], atol=1e-14)
    with pytest.raises(ValueError):
        y_kick(state, params.N, params.N)


@pytest.mark.parametrize("mode", ["csr", "matrix_free"])
def test_evolution_dense_agreement_reversal_semigroup_and_conservation(mode):
    params = parameters()
    model = build_hamiltonian(params, representation=mode)
    matrix = dense_hamiltonian(params)
    state = random_state(params)
    trajectory = list(evolve_trajectory(model, state, [0., .07, .2, .45]))
    for item in trajectory:
        np.testing.assert_allclose(item["state"], expm(-1j * item["time"] * matrix) @ state, atol=3e-13)
        assert item["valid"]
        assert item["probability_error"] < 1e-12
        assert item["scaled_energy_drift"] < 1e-12
        assert item["scaled_parity_drift"] < 1e-12
    np.testing.assert_allclose(evolve_state(model, trajectory[-1]["state"], -.45), state, atol=5e-13)
    np.testing.assert_allclose(evolve_state(model, evolve_state(model, state, .1), .2),
                               evolve_state(model, state, .3), atol=3e-13)


def test_csr_n5_short_propagation_and_frozen_born_conservation():
    params = Parameters(5, 1., 1., 0., .1, 1.)
    model = build_hamiltonian(params)
    state = product_state(5, math.pi / 4, .5, .2)
    result = evolve_state(model, state, .02)
    assert state_diagnostics(model, result, state_diagnostics(model, state))["valid"]
    np.testing.assert_allclose(born_probabilities(result, 5), born_probabilities(state, 5), atol=2e-14)


@pytest.mark.parametrize("times", [[], [-1], [0, 0], [.2, .1], [0, np.inf]])
def test_trajectory_rejects_invalid_time_grids(times):
    model = build_hamiltonian(parameters(2))
    state = product_state(2, math.pi / 4, .5, 0.)
    with pytest.raises(ValueError):
        list(evolve_trajectory(model, state, times))


def test_no_silent_state_normalization_and_drift_failures():
    model = build_hamiltonian(parameters(2))
    state = product_state(2, math.pi / 4, .5, 0.)
    with pytest.raises(ValueError, match="normalized"):
        evolve_state(model, 2 * state, .1)
    with pytest.raises(DynamicalNumericalError) as caught:
        state_diagnostics(model, state, {"energy": 100., "parity": 0.})
    assert not caught.value.diagnostics["valid"]
    assert caught.value.diagnostics["energy_drift"] > 1


def test_response_matches_independent_dense_reduced_matrix_trace_distance():
    params = parameters()
    model = build_hamiltonian(params)
    matrix = dense_hamiltonian(params)
    aged = expm(-.17j * matrix) @ product_state(3, math.pi / 4, [.2, .5, .7], [.2, 1., 2.])
    times = [0., .03, .15]
    calls = []
    result = response_trajectories(model, aged, times,
                                  state_callback=lambda source, time, state, diagnostics: calls.append((source, time)))
    assert result["baseline_bloch"].shape == (3, 3, 3)
    assert result["probe_bloch"].shape == (3, 3, 3, 3)
    assert result["response"].shape == (3, 3, 3)
    assert len(calls) == len(times) * (params.N + 1)
    for time_index, time in enumerate(times):
        U = expm(-1j * time * matrix)
        baseline = U @ aged
        for source in range(params.N):
            probe = U @ local(Y, source, params.Q) @ aged
            expected_global = math.sqrt(max(0., 1 - abs(np.vdot(aged, local(Y, source, params.Q) @ aged)) ** 2))
            assert result["global_source_distance"][source] == pytest.approx(expected_global)
            for target in range(params.N):
                difference = independent_density(probe, target, params.Q) - independent_density(baseline, target, params.Q)
                distance = np.abs(np.linalg.eigvalsh(difference)).sum() / 2
                assert result["response"][time_index, source, target] == pytest.approx(distance, abs=5e-13)
    off_diagonal = ~np.eye(params.N, dtype=bool)
    np.testing.assert_allclose(result["response"][0][off_diagonal], 0, atol=1e-14)
    assert np.max(np.diag(result["response"][0])) > .1
    assert result["diagnostics"]["max_scaled_energy_drift"] < 1e-12
    baseline_energy = result["baseline_diagnostics"][0]["energy"]
    assert any(abs(rows[0]["energy"] - baseline_energy) > .01 for rows in result["probe_diagnostics"])
    assert all(rows[0]["energy_drift"] == 0 for rows in result["probe_diagnostics"])


def test_aged_correlators_and_first_order_response_are_independently_verified():
    params = parameters()
    model = build_hamiltonian(params)
    matrix = dense_hamiltonian(params)
    state = expm(-.21j * matrix) @ random_state(params, 821)
    actual = direct_response_slopes(model, state)
    identity = np.eye(params.dimension)
    for edge, (i, j) in enumerate(combinations(range(params.N), 2)):
        number = (identity - local(Z, params.N + edge, params.Q)) / 2
        for source, target in ((i, j), (j, i)):
            expected = []
            for key, operator in (("zx", X), ("zy", Y)):
                correlation = np.vdot(state, number @ local(Z, source, params.Q) @ local(operator, target, params.Q) @ state).real
                expected.append(correlation)
                assert actual[key][source, target] == pytest.approx(correlation, abs=1e-14)
            assert actual["slopes"][source, target] == pytest.approx(2 * abs(params.g) * np.linalg.norm(expected), abs=1e-14)
    result = response_trajectories(model, state, [0., 1e-5])
    mask = ~np.eye(params.N, dtype=bool)
    np.testing.assert_allclose(result["response"][1][mask] / 1e-5,
                               actual["slopes"][mask], atol=3e-5)


def test_fresh_product_slope_and_all_off_cubic_coefficient():
    params = Parameters(2, 1., 1., .7, .1, 1.)
    model = build_hamiltonian(params)
    for probability in (0., .3, 1.):
        state = product_state(2, math.pi / 4, probability, .4)
        slopes = direct_response_slopes(model, state)["slopes"]
        assert slopes[0, 1] == pytest.approx(probability, abs=1e-14)
        assert slopes[1, 0] == pytest.approx(probability, abs=1e-14)
    off = product_state(2, math.pi / 4, 0., 0.)
    result = response_trajectories(model, off, [0., .005, .01])
    expected = params.g * params.Gamma ** 2 / 3
    assert result["response"][1, 0, 1] / .005 ** 3 == pytest.approx(expected, rel=.02)
    assert result["response"][2, 0, 1] / result["response"][1, 0, 1] == pytest.approx(8., rel=.02)


def test_first_order_operator_commutator_uses_quantum_link_projector():
    params = parameters()
    matrix = dense_hamiltonian(params)
    i, j, edge = 0, 2, 1
    Xi, Xj = local(X, i, params.Q), local(X, j, params.Q)
    derivative = 1j * (matrix @ Xi - Xi @ matrix)
    number = (np.eye(params.dimension) - local(Z, params.N + edge, params.Q)) / 2
    expected = 4j * params.g * number @ local(Y, i, params.Q) @ local(Y, j, params.Q)
    np.testing.assert_allclose(derivative @ Xj - Xj @ derivative, expected, atol=1e-14)


def test_independent_links_factorize_and_never_signal_between_matter_sites():
    params = Parameters(3, .8, 0., .4, -.7, 0.)
    model = build_hamiltonian(params)
    probabilities, phases = [.2, .5, .7], [.4, 1.2, 2.1]
    state = product_state(3, math.pi / 4, probabilities, phases)
    time = .43
    matter = np.array([math.cos(math.pi / 8), math.sin(math.pi / 8)])
    local_matter = expm(1j * time * params.h * X) @ matter
    edge_H = -params.Gamma * X + params.mu * (np.eye(2) - Z) / 2
    factors = [local_matter] * params.N
    for probability, phase in zip(probabilities, phases):
        factors.append(expm(-1j * time * edge_H) @
                       np.array([math.sqrt(1 - probability), np.exp(1j * phase) * math.sqrt(probability)]))
    expected = factors[0]
    for factor in factors[1:]:
        expected = np.kron(expected, factor)
    np.testing.assert_allclose(evolve_state(model, state, time), expected, atol=2e-13)
    response = response_trajectories(model, random_state(params), [0., .1, .5])["response"]
    np.testing.assert_allclose(response[:, ~np.eye(params.N, dtype=bool)], 0, atol=3e-13)


def independent_vertex_permutation(state, N, permutation):
    edges = list(combinations(range(N), 2))
    Q = N + len(edges)
    answer = np.empty_like(state)
    for new_basis in range(len(state)):
        new_bits = [(new_basis >> (Q - 1 - i)) & 1 for i in range(Q)]
        old_bits = [0] * Q
        for new_vertex, old_vertex in enumerate(permutation):
            old_bits[old_vertex] = new_bits[new_vertex]
        for new_edge, (a, b) in enumerate(edges):
            old_edge = edges.index(tuple(sorted((permutation[a], permutation[b]))))
            old_bits[N + old_edge] = new_bits[N + new_edge]
        old_basis = sum(bit << (Q - 1 - i) for i, bit in enumerate(old_bits))
        answer[new_basis] = state[old_basis]
    return answer


def test_joint_vertex_edge_permutation_covariance_for_every_three_vertex_permutation():
    params = parameters()
    model = build_hamiltonian(params)
    state = random_state(params, 812)
    evolved = evolve_state(model, state, .19)
    for permutation in permutations(range(params.N)):
        transformed = permute_state(state, params.N, permutation)
        np.testing.assert_allclose(transformed, independent_vertex_permutation(state, params.N, permutation), atol=0)
        np.testing.assert_allclose(evolve_state(model, transformed, .19),
                                   permute_state(evolved, params.N, permutation), atol=2e-13)
        np.testing.assert_allclose(matter_bloch(transformed, params.N), matter_bloch(state, params.N)[list(permutation)], atol=1e-14)
        assert sorted(vertex_axis_permutation(params.N, permutation)) == list(range(params.Q))


@pytest.mark.parametrize("probability", [0., .5])
def test_symmetric_initial_states_have_equal_unconditioned_operational_responses(probability):
    params = parameters()
    model = build_hamiltonian(params)
    initial = product_state(params.N, math.pi / 4, probability, 0.)
    aged = evolve_state(model, initial, .4)
    result = response_trajectories(model, aged, [0., .05, .3])
    mask = ~np.eye(params.N, dtype=bool)
    assert all(np.ptp(response[mask]) < 1e-12 for response in result["response"])
    for permutation in permutations(range(params.N)):
        np.testing.assert_allclose(permute_state(aged, params.N, permutation), aged, atol=1e-13)


@pytest.mark.parametrize("N,mode", [(1, "csr"), (2, "csr"), (3, "csr"), (3, "matrix_free")])
def test_ground_eigenpairs_match_independent_dense_spectrum(N, mode):
    params = parameters(N)
    model = build_hamiltonian(params, representation=mode)
    expected, vectors = np.linalg.eigh(dense_hamiltonian(params))
    result = ground_state(model, np.random.default_rng(772))
    assert result["valid"]
    np.testing.assert_allclose(result["eigenvalues"], expected[:2], atol=1e-11)
    assert result["gap"] == pytest.approx(expected[1] - expected[0], abs=1e-11)
    assert abs(np.vdot(result["state"], vectors[:, 0])) == pytest.approx(1, abs=1e-12)
    assert result["negative_amplitude_norm"] < 1e-12
    assert result["scaled_residual"] < 1e-10
    assert result["parity"] == pytest.approx(1, abs=1e-12)


def test_ground_start_includes_odd_matter_parity_excitation():
    params = Parameters(3, .1, 0., 1., 0., 0.)
    result = ground_state(build_hamiltonian(params), np.random.default_rng(312))
    assert result["energy"] == pytest.approx(-params.N * .1 - params.M, abs=1e-12)
    assert result["gap"] == pytest.approx(.2, abs=1e-12)


def test_failed_eigensolver_retains_failure_without_another_seed(monkeypatch):
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise ArpackNoConvergence("test", np.array([-1.]), np.zeros((8, 1)))

    monkeypatch.setattr(core, "eigsh", fail)
    with pytest.raises(DynamicalNumericalError) as caught:
        ground_state(build_hamiltonian(parameters(2)), np.random.default_rng(19))
    assert len(calls) == 1
    assert caught.value.diagnostics["partial_eigenvalues"] == [-1.]


def test_classical_degree_two_cycle_and_disconnected_triangles_are_degenerate():
    params = Parameters(6, 0., 1., 0., -2., 1.)
    edges = list(combinations(range(6), 2))
    cycle = {(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (0, 5)}
    triangles = {(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5)}
    diagonal = hamiltonian_diagonal(params)
    masks = [sum(1 << (params.M - 1 - edges.index(edge)) for edge in graph)
             for graph in (cycle, triangles)]
    assert diagonal[masks[0]] == diagonal[masks[1]] == -12


def assert_same_legacy_rng(before, after):
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


@pytest.mark.parametrize("mode", ["csr", "matrix_free"])
def test_exponential_action_preserves_global_rng_and_matches_dense_at_long_time(mode, monkeypatch):
    params = parameters()
    model = build_hamiltonian(params, representation=mode)
    matrix = dense_hamiltonian(params)
    state = random_state(params, 1729)
    assert model.centered_one_norm == pytest.approx(
        np.max(np.sum(np.abs(matrix - np.trace(matrix) * np.eye(params.dimension) / params.dimension), axis=0)))
    captured_norms = []
    original = core.expm_multiply

    def checked_public(A, vector, *, traceA):
        center = traceA / len(vector)
        centered = A.toarray() - center * np.eye(len(vector))
        captured_norms.append(np.max(np.sum(np.abs(centered), axis=0)))
        assert captured_norms[-1] <= 60 + 1e-12
        return original(A, vector, traceA=traceA)

    def forbidden_rng(*args, **kwargs):
        raise AssertionError("exponential action must never draw from the global RNG")

    monkeypatch.setattr(core, "expm_multiply", checked_public)
    monkeypatch.setattr(np.random, "randint", forbidden_rng)
    before = np.random.get_state()
    result = evolve_state(model, state, 13.)
    after = np.random.get_state()
    assert_same_legacy_rng(before, after)
    np.testing.assert_allclose(result, expm(-13j * matrix) @ state, atol=3e-12)
    assert state_diagnostics(model, result, state_diagnostics(model, state))["valid"]
    if mode == "csr":
        assert len(captured_norms) >= 2
    else:
        assert not captured_norms  # Existing private deterministic kernel, no public estimator.
    np.testing.assert_allclose(evolve_state(model, result, -13.), state, atol=4e-12)


def test_private_scipy_contract_changes_fail_explicitly(monkeypatch):
    core._private_expm_contract.cache_clear()
    try:
        with monkeypatch.context() as context:
            context.setattr(core._scipy_expm, "_theta", {55: -1.})
            with pytest.raises(RuntimeError, match="private exponential-action contract"):
                core._private_expm_contract()
    finally:
        core._private_expm_contract.cache_clear()
    core._private_expm_contract()


def test_matrix_free_zero_generator_and_replay_are_deterministic():
    params = Parameters(2, 0., 0., 0., 0., 0.)
    model = build_hamiltonian(params, representation="matrix_free")
    state = random_state(params, 382)
    np.testing.assert_array_equal(evolve_state(model, state, 2.), state)
    nonzero = build_hamiltonian(parameters(), representation="matrix_free")
    state = random_state(nonzero.params, 382)
    np.testing.assert_array_equal(evolve_state(nonzero, state, .42), evolve_state(nonzero, state, .42))


@pytest.mark.parametrize("mode", ["csr", "matrix_free"])
@pytest.mark.parametrize("mu,U", [(-.7, .9), (2., 1.), (.3, 0.)])
def test_frozen_sectors_match_full_dense_complex_entangled_evolution(mode, mu, U):
    params = replace(parameters(), Gamma=0., mu=mu, U=U)
    model = build_hamiltonian(params, representation=mode)
    state = random_state(params, 939)
    matrix = dense_hamiltonian(params)
    reference = state_diagnostics(model, state)
    born = born_probabilities(state, params.N)
    for dt in (.125, 2., -1.5, 13.):
        actual = evolve_state(model, state, dt)
        # Full complex amplitudes test the relative graph-sector phases too.
        np.testing.assert_allclose(actual, expm(-1j * dt * matrix) @ state, atol=8e-13)
        np.testing.assert_allclose(evolve_state(model, actual, -dt), state, atol=4e-14)
        np.testing.assert_allclose(born_probabilities(actual, params.N), born, atol=2e-15)
        assert state_diagnostics(model, actual, reference)["valid"]


def test_frozen_full_response_matches_independent_dense_reductions():
    params = replace(parameters(), Gamma=0.)
    matrix = dense_hamiltonian(params)
    model = build_hamiltonian(params)
    aged = random_state(params, 10229)
    delays = [0., .05, .5, 2.]
    result = response_trajectories(model, aged, delays)
    for t_index, time in enumerate(delays):
        evolution = expm(-1j * time * matrix)
        baseline = evolution @ aged
        for source in range(params.N):
            probe = evolution @ local(Y, source, params.Q) @ aged
            for target in range(params.N):
                difference = (independent_density(probe, target, params.Q)
                              - independent_density(baseline, target, params.Q))
                expected = np.abs(np.linalg.eigvalsh(difference)).sum() / 2
                assert result["response"][t_index, source, target] == pytest.approx(expected, abs=1e-13)
    assert result["diagnostics"]["valid"]
    assert result["diagnostics"]["max_scaled_energy_drift"] < 2e-13
    assert result["diagnostics"]["max_scaled_parity_drift"] < 2e-13


def test_frozen_cache_reuses_only_real_matter_eigenpairs_across_graph_costs(monkeypatch):
    core._frozen_matter_spectra.cache_clear()
    original = np.linalg.eigh
    calls = []

    def record(blocks):
        calls.append(blocks.shape)
        return original(blocks)

    monkeypatch.setattr(np.linalg, "eigh", record)
    params = replace(parameters(), Gamma=0.)
    state = random_state(params, 1987)
    for mu, U in ((-.7, .9), (2., 1.), (.1, .4)):
        evolve_state(build_hamiltonian(replace(params, mu=mu, U=U)), state, .37)
    assert calls == [(8, 8, 8)]
    values, vectors = core._frozen_matter_spectra(params.N, params.h, params.g)
    assert values.dtype == vectors.dtype == np.float64
    assert not values.flags.writeable and not vectors.flags.writeable
    assert core._frozen_matter_spectra.cache_info().maxsize == 2
    with pytest.raises(ValueError, match="N<=5"):
        core._frozen_matter_spectra(6, 1., 1.)


def test_n5_frozen_spectral_action_matches_sparse_action_without_global_rng(monkeypatch):
    params = Parameters(5, 1., 1., 0., 2., 1.)
    model = build_hamiltonian(params)
    state = random_state(params, 12721)
    # Independent Taylor action on the original sparse matrix at a safe norm.
    dt = .3
    expected = core.expm_multiply(-1j * dt * model.operator, state,
                                 traceA=-1j * dt * model.trace)

    def forbidden(*args, **kwargs):
        raise AssertionError("frozen propagation must not call random norm probes or the Taylor action")

    monkeypatch.setattr(np.random, "randint", forbidden)
    monkeypatch.setattr(core, "expm_multiply", forbidden)
    before = np.random.get_state()
    actual = evolve_state(model, state, dt)
    assert_same_legacy_rng(before, np.random.get_state())
    np.testing.assert_allclose(actual, expected, atol=2e-14)
    np.testing.assert_allclose(evolve_state(model, actual, -dt), state, atol=2e-14)
    np.testing.assert_allclose(born_probabilities(actual, 5), born_probabilities(state, 5), atol=2e-16)
    assert state_diagnostics(model, actual, state_diagnostics(model, state))["valid"]
    values, vectors = core._frozen_matter_spectra(5, 1., 1.)
    assert values.nbytes + vectors.nbytes == 8.25 * 1024 ** 2
    # Inspect selected blocks by an independent bit-based matter Hamiltonian.
    for graph in (0, 1, 137, 1023):
        block = np.zeros((32, 32))
        for matter in range(32):
            for site in range(5):
                block[matter, matter ^ (1 << (4 - site))] = -params.h
            block[matter, matter] = direct_basis_energy(replace(params, mu=0., U=0.), (matter << 10) | graph)
        np.testing.assert_allclose(block @ vectors[graph], vectors[graph] * values[graph], atol=3e-14)
        np.testing.assert_allclose(vectors[graph].T @ vectors[graph], np.eye(32), atol=3e-15)


def test_frozen_eigensolver_failure_is_explicit_without_retry(monkeypatch):
    core._frozen_matter_spectra.cache_clear()
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise np.linalg.LinAlgError("injected sector failure")

    monkeypatch.setattr(np.linalg, "eigh", fail)
    params = replace(parameters(2), Gamma=0.)
    with pytest.raises(DynamicalNumericalError) as caught:
        evolve_state(build_hamiltonian(params), random_state(params), .2)
    assert calls == [1]
    assert caught.value.diagnostics == {"valid": False, "failure": "sector_nonconvergence"}
