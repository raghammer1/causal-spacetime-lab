"""Exact matter/link quantum dynamics with streamed operational response.

Tensor axes: matter vertices first, then lexicographic unordered links. Axis zero
is the most significant bit; amplitudes reshape as [2**N, 2**M]. The tensor
factorization, Hamiltonian and time parameter are supplied mathematical structure.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
import math
from numbers import Real
import inspect

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import ArpackNoConvergence, LinearOperator, eigsh, expm_multiply
from scipy.sparse.linalg import _expm_multiply as _scipy_expm


NORM_TOLERANCE = 2e-9
DRIFT_TOLERANCE = 2e-8


class DynamicalNumericalError(RuntimeError):
    """A retained numerical failure, never an instruction to substitute a seed."""

    def __init__(self, message: str, diagnostics: dict):
        super().__init__(message)
        self.diagnostics = diagnostics


def _vertex_count(N):
    if isinstance(N, (bool, np.bool_)) or not isinstance(N, (int, np.integer)) or not 1 <= N <= 6:
        raise ValueError("N must be an integer from 1 through 6")
    return int(N)


@dataclass(frozen=True)
class Parameters:
    N: int
    h: float
    g: float
    Gamma: float
    mu: float
    U: float

    def __post_init__(self):
        object.__setattr__(self, "N", _vertex_count(self.N))
        for name in ("h", "g", "Gamma", "mu", "U"):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real) or not math.isfinite(float(value)):
                raise ValueError(f"{name} must be a finite real scalar")
            object.__setattr__(self, name, float(value))
        if self.h < 0 or self.Gamma < 0 or self.U < 0:
            raise ValueError("h, Gamma and U must be nonnegative")

    @property
    def M(self):
        return self.N * (self.N - 1) // 2

    @property
    def Q(self):
        return self.N + self.M

    @property
    def dimension(self):
        return 1 << self.Q


@dataclass(frozen=True)
class Hamiltonian:
    params: Parameters
    operator: object
    diagonal: np.ndarray
    trace: float
    norm_bound: float
    representation: str
    centered_one_norm: float


@lru_cache(maxsize=1)
def _private_expm_contract():
    """Guard the existing SciPy Taylor-action kernel used without random norm probes.

    SciPy's public LinearOperator path calls a global-RNG norm estimator and
    offers no exact-norm argument. We retain its existing double-precision kernel
    and theta table, choosing degree/scaling from our exact analytic one-norm.
    This is an explicitly checked private-API dependency, not a new integrator.
    """
    kernel = getattr(_scipy_expm, "_expm_multiply_simple_core", None)
    table = getattr(_scipy_expm, "_theta", None)
    condition = getattr(_scipy_expm, "_condition_3_13", None)
    required = {"A", "B", "t", "mu", "m_star", "s", "tol", "balance"}
    valid = callable(kernel) and required <= set(inspect.signature(kernel).parameters)
    valid = valid and isinstance(table, dict) and 55 in table and callable(condition)
    if valid:
        valid = all(isinstance(m, int) and 1 <= m <= 55 and math.isfinite(float(theta)) and theta > 0
                    for m, theta in table.items()) and condition(60., 1, 55, 2)
    if not valid:
        raise RuntimeError("SciPy private exponential-action contract changed; independent revalidation required")
    return kernel, tuple(sorted((m, float(theta)) for m, theta in table.items()))


@lru_cache(maxsize=6)
def _basis(N):
    """Small exact integer tables; never cache full per-qubit flip permutations."""
    N = _vertex_count(N)
    edges = tuple(combinations(range(N), 2))
    M = len(edges)
    graphs = np.arange(1 << M, dtype=np.int64)
    occupations = np.empty((len(graphs), M), dtype=np.int16)
    degrees = np.zeros((len(graphs), N), dtype=np.int16)
    for edge, (i, j) in enumerate(edges):
        occupations[:, edge] = (graphs >> (M - 1 - edge)) & 1
        degrees[:, i] += occupations[:, edge]
        degrees[:, j] += occupations[:, edge]
    matter = np.arange(1 << N, dtype=np.int64)
    signs = np.array([1 - 2 * ((matter >> (N - 1 - i)) & 1) for i in range(N)]).T.astype(np.int16)
    pairs = np.empty((len(matter), M), dtype=np.int16)
    for edge, (i, j) in enumerate(edges):
        pairs[:, edge] = signs[:, i] * signs[:, j]
    for array in (occupations, degrees, signs, pairs):
        array.setflags(write=False)
    return edges, occupations, degrees, signs, pairs


def hamiltonian_diagonal(params: Parameters) -> np.ndarray:
    if not isinstance(params, Parameters):
        raise ValueError("explicit Parameters required")
    _, occupations, degrees, _, pairs = _basis(params.N)
    edge_cost = params.mu * occupations.sum(axis=1)
    edge_cost = edge_cost + params.U * (degrees * (degrees - 1)).sum(axis=1) / 2
    # Integer dot products are exact: at N<=6 their absolute values are <=15.
    diagonal = edge_cost[None, :] - params.g * (pairs @ occupations.T)
    return np.asarray(diagonal, dtype=np.float64).reshape(-1)


def hamiltonian_trace(params: Parameters) -> float:
    mean = params.mu * params.M / 2 + params.U * params.N * (params.N - 1) * (params.N - 2) / 8
    return float(params.dimension * mean)


def build_hamiltonian(params: Parameters, *, representation: str | None = None) -> Hamiltonian:
    """Prepare CSR at N<=5 or matrix-free at N=6, with an exact nonzero trace.

    Explicit representation selection is for independent small-system validation;
    a materialized N=6 CSR is intentionally prohibited by the resource design.
    """
    if not isinstance(params, Parameters):
        raise ValueError("explicit Parameters required")
    mode = representation or ("csr" if params.N <= 5 else "matrix_free")
    if mode not in ("csr", "matrix_free") or (mode == "csr" and params.N == 6):
        raise ValueError("use CSR only through N=5, or matrix_free")
    diagonal = hamiltonian_diagonal(params)
    diagonal.setflags(write=False)
    strengths = (params.h,) * params.N + (params.Gamma,) * params.M
    active = [(axis, strength) for axis, strength in enumerate(strengths) if strength != 0]
    dimension = params.dimension
    if mode == "csr":
        basis = np.arange(dimension, dtype=np.int32)
        rows = np.tile(basis, len(active) + 1)
        columns = [basis]
        values = [diagonal]
        for axis, strength in active:
            columns.append(basis ^ (1 << (params.Q - 1 - axis)))
            values.append(np.full(dimension, -strength))
        operator = csr_matrix((np.concatenate(values), (rows, np.concatenate(columns))),
                              shape=(dimension, dimension))
        operator.eliminate_zeros()
    else:
        def apply(vector):
            array = np.asarray(vector)
            if array.ndim not in (1, 2) or array.shape[0] != dimension:
                raise ValueError("operator input has wrong dimension")
            columns = 1 if array.ndim == 1 else array.shape[1]
            working = np.ascontiguousarray(array.reshape(dimension, columns))
            result = diagonal[:, None] * working
            for axis, strength in active:
                stride = 1 << (params.Q - 1 - axis)
                source = working.reshape(-1, 2, stride, columns)
                target = result.reshape(-1, 2, stride, columns)
                target[:, 0] -= strength * source[:, 1]
                target[:, 1] -= strength * source[:, 0]
            return result.reshape(array.shape)

        operator = LinearOperator((dimension, dimension), matvec=apply, rmatvec=apply,
                                  matmat=apply, rmatmat=apply, dtype=np.float64)
    bound = float(np.max(np.abs(diagonal)) + sum(strengths))
    trace = hamiltonian_trace(params)
    centered_norm = float(np.max(np.abs(diagonal - trace / dimension)) + sum(strengths))
    return Hamiltonian(params, operator, diagonal, trace, bound, mode, centered_norm)


def _state(state, N):
    N = _vertex_count(N)
    dimension = 1 << (N + N * (N - 1) // 2)
    vector = np.asarray(state, dtype=np.complex128)
    if vector.ndim != 1 or len(vector) != dimension or not np.all(np.isfinite(vector)):
        raise ValueError("state must be a finite full matter-link vector of the stated size")
    probability = float(np.vdot(vector, vector).real)
    if abs(probability - 1) > NORM_TOLERANCE:
        raise ValueError("state must already be normalized; no silent repair")
    return vector


def product_state(N, theta, link_probabilities, link_phases) -> np.ndarray:
    """Specified identical real matter tilt and independently specified edge factors.

    Scalars for probabilities/phases broadcast over all links. This routine draws
    no randomness; the caller must retain every supplied factor and stream identity.
    """
    N = _vertex_count(N)
    if not isinstance(theta, Real) or not math.isfinite(float(theta)):
        raise ValueError("matter tilt must be finite and real")
    M = N * (N - 1) // 2
    probability = np.asarray(link_probabilities, dtype=float)
    phases = np.asarray(link_phases, dtype=float)
    if probability.ndim == 0:
        probability = np.full(M, probability.item())
    if phases.ndim == 0:
        phases = np.full(M, phases.item())
    if (probability.shape != (M,) or phases.shape != (M,) or not np.all(np.isfinite(probability))
            or not np.all(np.isfinite(phases)) or np.any(probability < 0) or np.any(probability > 1)):
        raise ValueError("one finite probability in [0,1] and phase is required per link")
    state = np.ones(1, dtype=np.complex128)
    matter = np.array([math.cos(float(theta) / 2), math.sin(float(theta) / 2)])
    for _ in range(N):
        state = np.kron(state, matter)
    for p, phase in zip(probability, phases):
        state = np.kron(state, [math.sqrt(1 - p), np.exp(1j * phase) * math.sqrt(p)])
    return _state(state, N)


def born_probabilities(state, N) -> np.ndarray:
    """Exact marginal Born law on link masks, with no independent-edge approximation."""
    vector = _state(state, N)
    amplitudes = vector.reshape(1 << N, -1)
    probabilities = np.sum(np.abs(amplitudes) ** 2, axis=0)
    if not np.all(np.isfinite(probabilities)) or abs(float(probabilities.sum()) - 1) > NORM_TOLERANCE:
        raise DynamicalNumericalError("Born normalization failed",
                                      {"valid": False, "probability_sum": float(probabilities.sum())})
    return probabilities


def matter_bloch(state, N) -> np.ndarray:
    """One-site Bloch vectors [X,Y,Z], tracing every other matter/link subsystem."""
    vector = _state(state, N)
    Q = N + N * (N - 1) // 2
    answer = np.empty((N, 3))
    for site in range(N):
        blocks = vector.reshape(-1, 2, 1 << (Q - 1 - site))
        zero, one = blocks[:, 0].reshape(-1), blocks[:, 1].reshape(-1)
        coherence = np.vdot(zero, one)
        answer[site] = [2 * coherence.real, 2 * coherence.imag,
                        np.vdot(zero, zero).real - np.vdot(one, one).real]
    if np.max(np.linalg.norm(answer, axis=1)) > 1 + NORM_TOLERANCE:
        raise DynamicalNumericalError("invalid one-site Bloch vector", {"valid": False})
    return answer


def matter_parity(state, N) -> float:
    """Expectation of the conserved global matter-X product (links untouched)."""
    vector = _state(state, N)
    amplitudes = vector.reshape(1 << N, -1)
    return float(np.vdot(amplitudes, amplitudes[::-1]).real)


def y_kick(state, N, source) -> np.ndarray:
    vector = _state(state, N)
    if isinstance(source, (bool, np.bool_)) or not isinstance(source, (int, np.integer)) or not 0 <= source < N:
        raise ValueError("source must be a matter vertex index")
    Q = N + N * (N - 1) // 2
    blocks = vector.reshape(-1, 2, 1 << (Q - 1 - int(source)))
    result = np.empty_like(blocks)
    result[:, 0] = -1j * blocks[:, 1]
    result[:, 1] = 1j * blocks[:, 0]
    return result.reshape(-1)


def state_diagnostics(model: Hamiltonian, state, reference=None) -> dict:
    vector = _state(state, model.params.N)
    probability = float(np.vdot(vector, vector).real)
    energy_complex = np.vdot(vector, model.operator @ vector)
    energy, parity = float(energy_complex.real), matter_parity(vector, model.params.N)
    result = {"norm": math.sqrt(probability), "norm_error": abs(math.sqrt(probability) - 1),
              "probability_error": abs(probability - 1), "energy": energy, "parity": parity,
              "energy_imaginary_error": abs(float(energy_complex.imag)),
              "energy_drift": 0., "parity_drift": 0., "scaled_energy_drift": 0.,
              "scaled_parity_drift": 0., "valid": True}
    if reference is not None:
        result["energy_drift"] = abs(energy - reference["energy"])
        result["parity_drift"] = abs(parity - reference["parity"])
        result["scaled_energy_drift"] = result["energy_drift"] / max(1., abs(reference["energy"]))
        result["scaled_parity_drift"] = result["parity_drift"] / max(1., abs(reference["parity"]))
    if (result["probability_error"] > NORM_TOLERANCE or result["scaled_energy_drift"] > DRIFT_TOLERANCE
            or result["scaled_parity_drift"] > DRIFT_TOLERANCE
            or result["energy_imaginary_error"] > DRIFT_TOLERANCE * max(1., abs(energy))):
        result["valid"] = False
        raise DynamicalNumericalError("trajectory conservation check failed", result)
    return result


def evolve_state(model: Hamiltonian, state, dt) -> np.ndarray:
    """Apply exp(-i H dt) without SciPy's hidden global-random norm estimation.

    CSR steps have centered one-norm at most60 (below SciPy's guarded63.36
    threshold for one RHS). Matrix-free action reuses SciPy's existing Taylor
    kernel and theta table with exact analytic-norm degree/scaling selection.
    Both preserve the same2**-53 kernel tolerance. Negative dt verifies reversal.
    """
    vector = _state(state, model.params.N)
    if isinstance(dt, (bool, np.bool_)) or not isinstance(dt, Real) or not math.isfinite(float(dt)):
        raise ValueError("time increment must be finite and real")
    if dt == 0:
        return vector.copy()
    kernel, theta_table = _private_expm_contract()
    norm = abs(float(dt)) * model.centered_one_norm
    if model.representation == "csr":
        # This public path uses the exact sparse norm, then its nonrandom branch.
        steps = max(1, math.ceil(norm / 60.))
        step = float(dt) / steps
        result = vector
        for _ in range(steps):
            result = expm_multiply((-1j * step) * model.operator, result,
                                   traceA=-1j * step * model.trace)
    else:
        center = model.trace / model.params.dimension
        def centered_action(array):
            return model.operator @ array - center * array
        centered = LinearOperator(model.operator.shape, matvec=centered_action,
                                  rmatvec=centered_action, matmat=centered_action,
                                  rmatmat=centered_action, dtype=np.float64)
        if norm == 0:
            degree, scaling = 0, 1
        else:
            _, degree, scaling = min((m * max(1, math.ceil(norm / theta)), m,
                                      max(1, math.ceil(norm / theta)))
                                     for m, theta in theta_table)
        result = kernel((-1j * float(dt)) * centered, vector, t=1.,
                        mu=-1j * float(dt) * center, m_star=degree, s=scaling,
                        tol=2 ** -53, balance=False)
    probability = float(np.vdot(result, result).real)
    if not np.all(np.isfinite(result)) or not math.isfinite(probability) or abs(probability - 1) > NORM_TOLERANCE:
        raise DynamicalNumericalError("exponential action normalization failed",
                                      {"valid": False, "probability_error": abs(probability - 1)})
    return result


def _times(times):
    result = np.asarray(times, dtype=float)
    if (result.ndim != 1 or len(result) == 0 or not np.all(np.isfinite(result))
            or result[0] < 0 or np.any(np.diff(result) <= 0)):
        raise ValueError("times must be a nonempty strictly increasing nonnegative sequence")
    return result


def evolve_trajectory(model: Hamiltonian, state, times):
    """Yield time/state/diagnostic dictionaries; never retain all full states here."""
    times = _times(times)
    current = _state(state, model.params.N)
    reference = state_diagnostics(model, current)
    previous = 0.
    for time in times:
        current = evolve_state(model, current, float(time - previous))
        diagnostics = state_diagnostics(model, current, reference)
        yield {"time": float(time), "state": current, **diagnostics}
        previous = time


def direct_response_slopes(model: Hamiltonian, state) -> dict:
    """Exact aged-state right slopes for a Pauli-Y source operation.

    zx[i,j]=<n_ij Z_i X_j>, zy[i,j]=<n_ij Z_i Y_j>. Diagonals are zero because
    this propagation identity concerns distinct source/target sites only.
    """
    N = model.params.N
    vector = _state(state, N)
    edges, occupations, _, signs, _ = _basis(N)
    edge_index = {pair: index for index, pair in enumerate(edges)}
    M, Q = model.params.M, model.params.Q
    zx, zy = np.zeros((N, N)), np.zeros((N, N))
    matter_labels = np.arange(1 << N)
    for target in range(N):
        blocks = vector.reshape(-1, 2, 1 << (Q - 1 - target))
        cross = (blocks[:, 0].conj() * blocks[:, 1]).reshape(1 << (N - 1), 1 << M)
        lower = matter_labels[(matter_labels & (1 << (N - 1 - target))) == 0]
        for source in range(N):
            if source == target:
                continue
            index = edge_index[tuple(sorted((source, target)))]
            signed_sum = signs[lower, source] @ cross
            expectation = np.dot(signed_sum, occupations[:, index])
            zx[source, target] = 2 * expectation.real
            zy[source, target] = 2 * expectation.imag
    return {"slopes": 2 * abs(model.params.g) * np.hypot(zx, zy), "zx": zx, "zy": zy}


def response_trajectories(model: Hamiltonian, aged_state, delays, *, state_callback=None) -> dict:
    """Stream baseline then all source probes, retaining only reduced outputs.

    Output probe_bloch and response use [time,source,target,...]. Raw response
    diagonals retain source self-change; propagation scoring must exclude them.
    Optional callback(source_or_None,time,state,diagnostics) can hash/checkpoint
    selected full states without forcing this function to retain them.
    """
    N = model.params.N
    aged = _state(aged_state, N)
    times = _times(delays)
    baseline = np.empty((len(times), N, 3))
    probes = np.empty((len(times), N, N, 3))
    baseline_diagnostics, probe_diagnostics = [], [[] for _ in range(N)]
    maxima = {f"max_{key}": 0. for key in
              ("norm_error", "probability_error", "scaled_energy_drift", "scaled_parity_drift")}

    def consume(source, time_index, item):
        diagnostic = {key: value for key, value in item.items() if key != "state"}
        for key in maxima:
            maxima[key] = max(maxima[key], diagnostic[key.removeprefix("max_")])
        if state_callback is not None:
            state_callback(source, item["time"], item["state"], diagnostic)
        if source is None:
            baseline[time_index] = matter_bloch(item["state"], N)
            baseline_diagnostics.append(diagnostic)
        else:
            probes[time_index, source] = matter_bloch(item["state"], N)
            probe_diagnostics[source].append(diagnostic)

    for time_index, item in enumerate(evolve_trajectory(model, aged, times)):
        consume(None, time_index, item)
    global_distance = np.empty(N)
    for source in range(N):
        kicked = y_kick(aged, N, source)
        overlap_squared = float(abs(np.vdot(aged, kicked)) ** 2)
        if overlap_squared > 1 + 2 * NORM_TOLERANCE:
            raise DynamicalNumericalError("source overlap exceeds one", {"valid": False})
        global_distance[source] = math.sqrt(max(0., 1 - overlap_squared))
        for time_index, item in enumerate(evolve_trajectory(model, kicked, times)):
            consume(source, time_index, item)
    response = np.linalg.norm(probes - baseline[:, None, :, :], axis=-1) / 2
    if np.max(response) > 1 + NORM_TOLERANCE:
        raise DynamicalNumericalError("target trace distance exceeds one", {"valid": False})
    response = np.minimum(response, 1.)
    return {"times": times.copy(), "baseline_bloch": baseline, "probe_bloch": probes,
            "response": response, "global_source_distance": global_distance,
            "baseline_diagnostics": baseline_diagnostics, "probe_diagnostics": probe_diagnostics,
            "diagnostics": {**maxima, "valid": True, "trajectory_count": N + 1}}


def ground_state(model: Hamiltonian, rng: np.random.Generator) -> dict:
    """Generic-start lowest eigenpairs with recorded residual/gap diagnostics."""
    if not isinstance(rng, np.random.Generator):
        raise ValueError("an explicit Generator is required")
    dimension = model.params.dimension
    start = rng.normal(size=dimension)
    norm = float(np.linalg.norm(start))
    if not math.isfinite(norm) or norm == 0:
        raise DynamicalNumericalError("invalid eigensolver start", {"valid": False})
    start /= norm
    try:
        if dimension == 2:
            matrix = model.operator.toarray() if hasattr(model.operator, "toarray") else model.operator @ np.eye(2)
            values, vectors = np.linalg.eigh(matrix)
        else:
            values, vectors = eigsh(model.operator, k=2, which="SA", tol=1e-12,
                                   v0=start, maxiter=10000)
    except ArpackNoConvergence as error:
        raise DynamicalNumericalError("ground eigensolver did not converge",
            {"valid": False, "failure": "nonconvergence", "partial_eigenvalues": error.eigenvalues.tolist()}) from error
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(vectors)):
        raise DynamicalNumericalError("nonfinite eigenpairs", {"valid": False})
    order = np.argsort(values)
    values, vectors = values[order], vectors[:, order]
    residuals = np.linalg.norm(model.operator @ vectors - vectors * values, axis=0)
    state = np.asarray(vectors[:, 0], dtype=np.complex128)
    pivot = state[int(np.argmax(np.abs(state)))]
    state *= np.conj(pivot) / abs(pivot)
    residual = float(np.max(residuals))
    scaled = residual / max(1., abs(float(values[0])))
    norm_error = float(np.max(np.abs(np.linalg.norm(vectors, axis=0) - 1)))
    orthogonality = float(abs(np.vdot(vectors[:, 0], vectors[:, 1])))
    negative = float(np.linalg.norm(np.minimum(state.real, 0)))
    unique_positive = model.params.h > 0 and model.params.Gamma > 0
    diagnostics = {"energy": float(values[0]), "eigenvalues": values,
        "gap": float(values[1] - values[0]), "residuals": residuals,
        "residual": residual, "scaled_residual": scaled, "norm_error": norm_error,
        "orthogonality_error": orthogonality, "negative_amplitude_norm": negative,
        "positivity_required": unique_positive,
        "gap_resolved": bool(values[1] - values[0] > 100 * residual), "solver_tolerance": 1e-12}
    diagnostics["valid"] = bool(scaled <= 1e-9 and norm_error <= NORM_TOLERANCE
                                and orthogonality <= DRIFT_TOLERANCE
                                and (not unique_positive or negative <= DRIFT_TOLERANCE))
    if not diagnostics["valid"]:
        raise DynamicalNumericalError("ground eigenpair quality check failed", diagnostics)
    diagnostics["parity"] = matter_parity(state, model.params.N)
    return {"state": state, **diagnostics}


def vertex_axis_permutation(N, permutation) -> np.ndarray:
    """Tensor axis map: new vertex i is old permutation[i], including all edges."""
    N = _vertex_count(N)
    array = np.asarray(permutation)
    if (array.shape != (N,) or array.dtype.kind not in "iu" or np.any(array < 0)
            or np.any(array >= N) or len(np.unique(array)) != N):
        raise ValueError("a permutation of every matter vertex is required")
    edges = tuple(combinations(range(N), 2))
    lookup = {edge: N + index for index, edge in enumerate(edges)}
    return np.array([*array, *(lookup[tuple(sorted((int(array[i]), int(array[j]))))]
                               for i, j in edges)], dtype=int)


def permute_state(state, N, permutation) -> np.ndarray:
    vector = _state(state, N)
    axes = vertex_axis_permutation(N, permutation)
    return vector.reshape((2,) * len(axes)).transpose(axes).reshape(-1).copy()
