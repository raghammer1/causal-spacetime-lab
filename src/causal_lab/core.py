"""Minimal computational experiments in 1+1D flat causal sets.

These are validation experiments using a known Minkowski background,
NOT a demonstration that physical spacetime is discrete or emergent.
"""
from bisect import bisect_left
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class CausalDiamond:
    """Events Poisson-sprinkled into the causal diamond between (0,0) and (T,0).

    u=t+x, v=t-x, with c=1 and 0<u,v<T. The generating coordinates
    are retained for plotting/validation, not needed by order-only analysis.
    """

    u: np.ndarray
    v: np.ndarray
    duration: float
    density: float

    @property
    def count(self) -> int:
        return len(self.u)

    @property
    def t(self) -> np.ndarray:
        return (self.u + self.v) / 2

    @property
    def x(self) -> np.ndarray:
        return (self.u - self.v) / 2


def sprinkle(duration: float, density: float, rng: np.random.Generator) -> CausalDiamond:
    """Sample a Lorentz-invariant Poisson process in a 1+1D flat causal diamond.

    The diamond volume is T**2/2 in units c=1. Setting a seed makes
    the *simulation* reproducible, not individual sprinklings physical.
    """
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be finite and positive")
    if not np.isfinite(density) or density <= 0:
        raise ValueError("density must be finite and positive")
    n = int(rng.poisson(density * duration**2 / 2))
    return CausalDiamond(
        u=rng.uniform(0, duration, n),
        v=rng.uniform(0, duration, n),
        duration=float(duration),
        density=float(density),
    )


def causal_order(diamond: CausalDiamond) -> np.ndarray:
    """Return the strict timelike order (both null coordinates increase).

    Null-related ties are excluded; these have probability zero under the
    continuous sprinkling law. O(n^2) memory; intended for small trials.
    """
    u, v = diamond.u, diamond.v
    return (u[:, None] < u[None, :]) & (v[:, None] < v[None, :])


def longest_chain_order(order: np.ndarray) -> list[int]:
    """Longest chain using *only* the causal-order matrix, no coordinates.

    Input must be the transitive strict order matrix of a finite poset,
    not merely its adjacency or Hasse matrix. Invalid inputs raise ValueError.
    Full transitivity validation costs O(n^3) worst-case time; storage is O(n^2).
    """
    order = np.asarray(order, dtype=bool)
    if order.ndim != 2 or order.shape[0] != order.shape[1]:
        raise ValueError("order must be a square matrix")
    n = len(order)
    if not n:
        return []
    if np.any(np.diag(order)) or np.any(order & order.T):
        raise ValueError("order must be irreflexive and antisymmetric")
    # If i < j, every successor of j must also be a successor of i.
    # This also rules out cycles of length > 2 before parent pointers are built.
    for i in range(n):
        successors = np.flatnonzero(order[i])
        if successors.size and np.any(order[successors] & ~order[i]):
            raise ValueError("order must be transitive and acyclic")
    topological = np.argsort(order.sum(axis=0), kind="stable")
    length = np.ones(n, dtype=int)
    parent = np.full(n, -1, dtype=int)
    for j in topological:
        predecessors = np.flatnonzero(order[:, j])
        if predecessors.size:
            i = int(predecessors[np.argmax(length[predecessors])])
            length[j] = length[i] + 1
            parent[j] = i
    chain = []
    i = int(np.argmax(length))
    while i != -1:
        chain.append(i)
        i = int(parent[i])
    return chain[::-1]


def longest_chain_fast(diamond: CausalDiamond) -> list[int]:
    """O(n log n) longest chain from the *known* 1+1D embedding.

    This efficient algorithm is for high-density baseline simulation;
    do not describe it as coordinate-free emergence.
    """
    u, v = diamond.u, diamond.v
    n = len(u)
    if n == 0:
        return []
    # Descending v within equal-u groups prevents a strict LIS from using
    # two points whose u coordinates tie. bisect_left also excludes v ties.
    indices = np.lexsort((-v, u))
    tails: list[float] = []
    tail_index: list[int] = []
    parent = np.full(n, -1, dtype=int)
    for idx in indices:
        i = int(idx)
        j = bisect_left(tails, float(v[i]))
        if j:
            parent[i] = tail_index[j - 1]
        if j == len(tails):
            tails.append(float(v[i]))
            tail_index.append(i)
        else:
            tails[j] = float(v[i])
            tail_index[j] = i
    result = []
    i = tail_index[-1]
    while i != -1:
        result.append(i)
        i = int(parent[i])
    return result[::-1]


def inferred_duration(chain_length: int, density: float) -> float:
    """Asymptotic 1+1D Minkowski estimate, with finite-density bias."""
    if not np.isfinite(density) or density <= 0:
        raise ValueError("density must be finite and positive")
    if (not isinstance(chain_length, (int, np.integer))
            or isinstance(chain_length, (bool, np.bool_)) or chain_length < 0):
        raise ValueError("chain length must be a nonnegative integer")
    return float(chain_length / (np.sqrt(2.0) * np.sqrt(density)))


def comparable_pair_fraction(order: np.ndarray) -> float:
    """Fraction of unordered distinct pairs that are causally comparable.

    This is one coarse statistic, NOT a validated standalone dimension
    estimator or proof of any emergent geometry.
    """
    order = np.asarray(order, dtype=bool)
    if order.ndim != 2 or order.shape[0] != order.shape[1]:
        raise ValueError("order must be square")
    if np.any(np.diag(order)):
        raise ValueError("order must be irreflexive")
    n = len(order)
    if n < 2:
        return float("nan")
    return float(np.count_nonzero(order | order.T) / (n * (n - 1)))
