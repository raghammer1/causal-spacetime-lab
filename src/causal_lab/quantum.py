"""Exact small-qubit information and supplied transverse-field Ising dynamics.

Qubit 0 is the most significant computational-basis bit (tensor axis 0).
Subsystem lists retain their requested order. The supplied tensor factorization,
Hamiltonian and time parameter are assumptions, not emergent spacetime.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import ArpackNoConvergence, eigsh, expm_multiply


MAX_QUBITS = 10
NUMERICAL_TOLERANCE = 1e-10


class QuantumNumericalError(RuntimeError):
    """A failed numerical check, with diagnostics retained for study archives."""

    def __init__(self, message: str, diagnostics: dict):
        super().__init__(message)
        self.diagnostics = diagnostics


def _qubits(n: int, *, allow_zero: bool = False) -> int:
    lower = 0 if allow_zero else 1
    if (isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer))
            or not lower <= n <= MAX_QUBITS):
        raise ValueError(f"qubit count must be an integer in [{lower},{MAX_QUBITS}]")
    return int(n)


def _dimension(d: int) -> int:
    if d < 1 or d & (d - 1):
        raise ValueError("Hilbert dimension must be a positive power of two")
    return _qubits(d.bit_length() - 1, allow_zero=True)


def _generator(rng: np.random.Generator) -> np.random.Generator:
    if not isinstance(rng, np.random.Generator):
        raise ValueError("an explicit numpy.random.Generator is required")
    return rng


def _vector(state, *, normalized: bool = True) -> tuple[np.ndarray, int]:
    value = np.asarray(state, dtype=np.complex128)
    if value.ndim != 1 or not np.all(np.isfinite(value)):
        raise ValueError("state must be a finite one-dimensional complex vector")
    n = _dimension(len(value))
    if normalized:
        norm_squared = float(np.vdot(value, value).real)
        if not math.isfinite(norm_squared) or abs(norm_squared - 1) > NUMERICAL_TOLERANCE:
            raise ValueError("state must already be normalized")
    return value, n


def normalize_state(state) -> np.ndarray:
    """Explicit normalization, rejecting zero/nonfinite/malformed vectors."""
    value, _ = _vector(state, normalized=False)
    scale = float(np.max(np.abs(value)))
    if scale == 0 or not math.isfinite(scale):
        raise ValueError("cannot normalize a zero or nonfinite state")
    scaled = value / scale
    return scaled / np.linalg.norm(scaled)


def density_matrix(state) -> np.ndarray:
    """Density matrix of an already normalized pure state."""
    vector, _ = _vector(state)
    return np.outer(vector, vector.conj())


def _density(rho) -> tuple[np.ndarray, int]:
    matrix = np.asarray(rho, dtype=np.complex128)
    if (matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]
            or not np.all(np.isfinite(matrix))):
        raise ValueError("density matrix must be finite and square")
    n = _dimension(len(matrix))
    if np.max(np.abs(matrix - matrix.conj().T)) > NUMERICAL_TOLERANCE:
        raise ValueError("density matrix must be Hermitian")
    if abs(np.trace(matrix) - 1) > NUMERICAL_TOLERANCE:
        raise ValueError("density matrix must have trace one")
    return (matrix + matrix.conj().T) / 2, n


def _spectrum(rho) -> tuple[np.ndarray, float]:
    matrix, _ = _density(rho)
    values = np.linalg.eigvalsh(matrix)
    negative_mass = float(-np.minimum(values, 0).sum())
    if negative_mass > NUMERICAL_TOLERANCE:
        raise ValueError("density matrix must be positive semidefinite")
    values = np.maximum(values, 0)
    correction = max(negative_mass, abs(float(values.sum()) - 1))
    if correction > NUMERICAL_TOLERANCE:
        raise ValueError("density eigenvalues require a material normalization correction")
    return values / values.sum(), correction


def _indices(keep, n: int, *, permutation: bool = False) -> tuple[int, ...]:
    array = np.asarray(keep)
    if array.ndim != 1 or (array.size and array.dtype.kind not in "iu"):
        raise ValueError("subsystems must be a one-dimensional integer sequence")
    if (np.any(array < 0) or np.any(array >= n)
            or len(np.unique(array)) != len(array)):
        raise ValueError("subsystems must be distinct valid qubit indices")
    if permutation and len(array) != n:
        raise ValueError("permutation must include every qubit")
    return tuple(int(i) for i in array)


def _pure_reduction(vector: np.ndarray, keep: tuple[int, ...], n: int) -> np.ndarray:
    complement = tuple(i for i in range(n) if i not in keep)
    matrix = vector.reshape((2,) * n).transpose(keep + complement).reshape(2 ** len(keep), -1)
    return matrix @ matrix.conj().T


def reduced_density(state, keep) -> np.ndarray:
    """Reduced density of a pure vector or mixed matrix, in ``keep`` order."""
    if np.asarray(state).ndim == 2:
        return partial_trace(state, keep)
    vector, n = _vector(state)
    indices = _indices(keep, n)
    return _pure_reduction(vector, indices, n)


def partial_trace(rho, keep) -> np.ndarray:
    """Trace mixed-state tensor axes directly, independently of pure reduction."""
    matrix, n = _density(rho)
    _spectrum(matrix)  # Reject a nonpositive input before partial tracing it.
    indices = _indices(keep, n)
    remaining = list(range(n))
    tensor = matrix.reshape((2,) * (2 * n))
    for original in reversed(range(n)):
        if original not in indices:
            axis = remaining.index(original)
            tensor = np.trace(tensor, axis1=axis, axis2=axis + len(remaining))
            remaining.pop(axis)
    permutation = tuple(remaining.index(i) for i in indices)
    axes = permutation + tuple(i + len(indices) for i in permutation)
    return tensor.transpose(axes).reshape(2 ** len(indices), 2 ** len(indices))


def _entropy(rho) -> tuple[float, float]:
    values, correction = _spectrum(rho)
    positive = values[values > 0]
    return float(-np.dot(positive, np.log2(positive))), correction


def entropy(rho) -> float:
    """Von Neumann entropy in bits, validating the density spectrum first."""
    return _entropy(rho)[0]


def _bounded(value: float, lower: float, upper: float, name: str) -> tuple[float, float]:
    if not lower - NUMERICAL_TOLERANCE <= value <= upper + NUMERICAL_TOLERANCE:
        raise ValueError(f"{name} violates its mathematical bounds")
    clipped = min(upper, max(lower, value))
    return clipped, abs(clipped - value)


def _negativity(rho: np.ndarray) -> tuple[float, float]:
    transposed = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    value = float((np.abs(np.linalg.eigvalsh(transposed)).sum() - 1) / 2)
    return _bounded(value, 0, .5, "two-qubit negativity")


def negativity(rho) -> float:
    """Two-qubit negativity; zero does not exclude multipartite entanglement."""
    matrix, n = _density(rho)
    if n != 2:
        raise ValueError("negativity requires a two-qubit density matrix")
    _spectrum(matrix)
    return _negativity(matrix)[0]


def pair_observables(state) -> dict:
    """All one-/two-site observables of a normalized pure or mixed state.

    MI, negativity, log-negativity and connected-ZZ matrices have zero diagonal.
    Pair entropy's diagonal equals single entropy. Connected ZZ is basis dependent.
    ``max_roundoff_correction`` records small clipping/trace corrections, which
    are bounded by 1e-10 and are not statistical uncertainty.
    """
    array = np.asarray(state)
    if array.ndim == 1:
        vector, n = _vector(array)
        reduction = lambda keep: _pure_reduction(vector, keep, n)
    else:
        matrix, n = _density(array)
        _spectrum(matrix)
        reduction = lambda keep: partial_trace(matrix, keep)
    singles = np.zeros(n)
    z_mean = np.zeros(n)
    pair_entropy = np.zeros((n, n))
    mutual = np.zeros((n, n))
    negative = np.zeros((n, n))
    connected = np.zeros((n, n))
    correction = 0.0
    for i in range(n):
        rho = reduction((i,))
        singles[i], error = _entropy(rho)
        correction = max(correction, error)
        z_mean[i] = float((rho[0, 0] - rho[1, 1]).real)
        pair_entropy[i, i] = singles[i]
    for i in range(n):
        for j in range(i + 1, n):
            rho = reduction((i, j))
            pair_value, error = _entropy(rho)
            pair_entropy[i, j] = pair_entropy[j, i] = pair_value
            correction = max(correction, error)
            mi, error = _bounded(singles[i] + singles[j] - pair_value,
                                 0, 2 * min(singles[i], singles[j]), "mutual information")
            correction = max(correction, error)
            mutual[i, j] = mutual[j, i] = mi
            value, error = _negativity(rho)
            correction = max(correction, error)
            negative[i, j] = negative[j, i] = value
            zz = float(np.dot(np.diag(rho).real, [1, -1, -1, 1]))
            connected[i, j] = connected[j, i] = zz - z_mean[i] * z_mean[j]
    return {"single_entropy": singles, "pair_entropy": pair_entropy, "mi": mutual,
            "negativity": negative, "log_negativity": np.log2(1 + 2 * negative),
            "connected_zz": connected, "max_roundoff_correction": correction}


def plus_state(n: int) -> np.ndarray:
    n = _qubits(n)
    return np.full(2 ** n, 2 ** (-n / 2), dtype=np.complex128)


def ghz_state(n: int) -> np.ndarray:
    n = _qubits(n)
    state = np.zeros(2 ** n, dtype=np.complex128)
    state[[0, -1]] = 1 / math.sqrt(2)
    return state


def bell_product(n: int) -> np.ndarray:
    """Tensor product of Bell pairs on (0,1), (2,3), ...; n must be even."""
    n = _qubits(n)
    if n % 2:
        raise ValueError("a Bell-pair product requires an even qubit count")
    pair = ghz_state(2)
    state = np.array([1], dtype=np.complex128)
    for _ in range(n // 2):
        state = np.kron(state, pair)
    return state


def haar_state(n: int, rng: np.random.Generator) -> np.ndarray:
    n, rng = _qubits(n), _generator(rng)
    return normalize_state(rng.normal(size=2 ** n) + 1j * rng.normal(size=2 ** n))


def random_product_state(n: int, rng: np.random.Generator) -> np.ndarray:
    n, rng = _qubits(n), _generator(rng)
    state = np.array([1], dtype=np.complex128)
    for _ in range(n):
        state = np.kron(state, haar_state(1, rng))
    return state


def and_state() -> np.ndarray:
    """Purified classical AND: sum |a,a AND c,c,a,c>/2 in A,B,C,R_A,R_C order."""
    state = np.zeros(32, dtype=np.complex128)
    state[[0, 5, 18, 31]] = .5
    return state


def permute_state(state, permutation) -> np.ndarray:
    """New tensor axis i is old axis permutation[i]."""
    vector, n = _vector(state)
    indices = _indices(permutation, n, permutation=True)
    return vector.reshape((2,) * n).transpose(indices).reshape(-1).copy()


def _couplings(J, h: float) -> tuple[np.ndarray, float]:
    array = np.asarray(J)
    if (array.ndim != 2 or array.shape[0] != array.shape[1]
            or np.iscomplexobj(array) or not np.all(np.isfinite(array))):
        raise ValueError("J must be a finite real square matrix")
    _qubits(len(array))
    matrix = np.asarray(array, dtype=float)
    if not np.array_equal(matrix, matrix.T) or np.any(np.diag(matrix) != 0):
        raise ValueError("J must be symmetric with zero diagonal")
    if (isinstance(h, (bool, np.bool_)) or not np.isscalar(h) or np.iscomplexobj(h)
            or not np.isreal(h) or not math.isfinite(float(h)) or float(h) <= 0):
        raise ValueError("h must be a finite positive scalar")
    return matrix, float(h)


def tfim_hamiltonian(J, h: float) -> csr_matrix:
    """Sparse H=-h sum X_i - sum_(i<j) J_ij Z_i Z_j, with no hidden geometry."""
    couplings, field = _couplings(J, h)
    n, dimension = len(couplings), 2 ** len(couplings)
    basis = np.arange(dimension, dtype=np.int64)
    spins = [1 - 2 * ((basis >> (n - 1 - i)) & 1) for i in range(n)]
    diagonal = np.zeros(dimension)
    for i in range(n):
        for j in range(i + 1, n):
            diagonal -= couplings[i, j] * spins[i] * spins[j]
    rows = [basis]
    columns = [basis]
    values = [diagonal]
    for i in range(n):
        rows.append(basis)
        columns.append(basis ^ (1 << (n - 1 - i)))
        values.append(np.full(dimension, -field))
    return csr_matrix((np.concatenate(values), (np.concatenate(rows), np.concatenate(columns))),
                      shape=(dimension, dimension))


def ground_state(J, h: float, rng: np.random.Generator) -> dict:
    """Lowest two eigenpairs and registered quality diagnostics.

    Generic seeded starts avoid restricting Lanczos to the all-plus parity sector.
    Diagnostics are numerical checks, not a rigorous global minimum certificate.
    A failed check raises QuantumNumericalError without substituting a new seed.
    """
    couplings, field = _couplings(J, h)
    rng = _generator(rng)
    matrix = tfim_hamiltonian(couplings, field)
    scale = max(1.0, len(couplings) * field + float(np.triu(np.abs(couplings), 1).sum()))
    start = rng.normal(size=matrix.shape[0])
    start_norm = float(np.linalg.norm(start))
    if not math.isfinite(start_norm) or start_norm == 0:
        raise QuantumNumericalError("invalid eigensolver starting vector",
                                    {"valid": False, "failure": "invalid_start"})
    start /= start_norm
    try:
        if matrix.shape[0] == 2:
            energies, vectors = np.linalg.eigh(matrix.toarray())
        else:
            energies, vectors = eigsh(matrix, k=2, which="SA", tol=1e-12,
                                     v0=start, maxiter=10000)
    except ArpackNoConvergence as error:
        diagnostics = {"valid": False, "failure": "eigensolver_nonconvergence",
                       "energy_scale": scale,
                       "partial_eigenvalues": np.asarray(error.eigenvalues).tolist()}
        raise QuantumNumericalError("ground eigensolver did not converge", diagnostics) from error
    if not np.all(np.isfinite(energies)) or not np.all(np.isfinite(vectors)):
        raise QuantumNumericalError("ground eigensolver returned nonfinite values",
                                    {"valid": False, "failure": "nonfinite_eigenpairs",
                                     "energy_scale": scale})
    ordering = np.argsort(energies)
    energies, vectors = energies[ordering], vectors[:, ordering]
    residuals = np.linalg.norm(matrix @ vectors - vectors * energies, axis=0)
    normalization = float(np.max(np.abs(np.sum(np.abs(vectors) ** 2, axis=0) - 1)))
    orthogonality = float(abs(np.vdot(vectors[:, 0], vectors[:, 1])))
    state = np.asarray(vectors[:, 0], dtype=np.complex128)
    pivot = state[int(np.argmax(np.abs(state)))]
    state *= np.conj(pivot) / abs(pivot)
    imaginary = float(np.linalg.norm(state.imag))
    negative = float(np.linalg.norm(np.minimum(state.real, 0)))
    gap = float(energies[1] - energies[0])
    residual = float(np.max(residuals))
    diagnostics = {
        "energy": float(energies[0]), "excited_energy": float(energies[1]),
        "gap": gap, "residual": residual, "scaled_residual": residual / scale,
        "residuals": residuals.tolist(), "energy_scale": scale,
        "normalization_error": normalization, "orthogonality_error": orthogonality,
        "negative_amplitude_norm": negative, "imaginary_amplitude_norm": imaginary,
        "solver_tolerance": 1e-12,
    }
    failures = []
    if residual / scale > 1e-9:
        failures.append("scaled_residual")
    if normalization > 1e-10:
        failures.append("normalization")
    if gap <= 100 * residual:
        failures.append("unresolved_gap")
    if orthogonality > 1e-10:
        failures.append("orthogonality")
    if negative > 1e-10 or imaginary > 1e-10:
        failures.append("positive_real_ground_state")
    diagnostics["valid"] = not failures
    if failures:
        diagnostics["failure"] = ",".join(failures)
        raise QuantumNumericalError("ground eigensolver quality check failed", diagnostics)
    return {"state": state, **diagnostics}


def evolve_state(J, h: float, state, t: float) -> np.ndarray:
    """Unitary exp(-i H t) on a normalized state; time is supplied externally."""
    matrix = tfim_hamiltonian(J, h)
    vector, _ = _vector(state)
    if len(vector) != matrix.shape[0]:
        raise ValueError("state and Hamiltonian dimensions differ")
    if (isinstance(t, (bool, np.bool_)) or not np.isscalar(t) or np.iscomplexobj(t)
            or not np.isreal(t) or not math.isfinite(float(t))):
        raise ValueError("time must be a finite real scalar")
    if float(t) == 0:
        return vector.copy()
    evolved = expm_multiply((-1j * float(t)) * matrix, vector, traceA=0.0)
    error = abs(float(np.vdot(evolved, evolved).real) - 1)
    if not np.all(np.isfinite(evolved)) or not math.isfinite(error) or error > 1e-10:
        raise QuantumNumericalError("unitary evolution failed normalization",
                                    {"valid": False, "normalization_error": error})
    return evolved
