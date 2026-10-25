"""Intrinsic fixed-parameter transitive percolation and exact finite laws.

Birth labels describe a natural history, not additional physical observables.
The probabilities below concern a specified precursor or one natural-label
history. An unlabeled order probability also requires its history multiplicity.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .adversarial_generators import _generator
from .dimension import validate_order
from .order_observables import _bit_rows, _bounded_matrix, _count, _probability


def _cap(max_count: int) -> int:
    """The registered public growth workload has a hard 512-event ceiling."""
    return _count(max_count, 512)


def _order(order, max_count: int) -> np.ndarray:
    return validate_order(_bounded_matrix(order, _cap(max_count)))


@dataclass(frozen=True)
class GrowthHistory:
    """Closed birth-labeled order, primitive selection edges, and provenance."""

    order: np.ndarray
    primitive_edges: np.ndarray
    metadata: dict


def transitive_percolation(count: int, rng: np.random.Generator,
                          probability: float, *, max_count: int = 512) -> GrowthHistory:
    """Grow a fixed-p order by independent Bernoulli selections at each birth.

    Birth j consumes exactly j uniform draws, even for p=0 or p=1. Therefore
    equal initial RNG states give identical prefixes at different terminal N.
    Primitive selections are retained separately from ancestral reachability.
    The generator uses no embedding, target statistic, or external geometry.
    """
    n = _count(count, _cap(max_count))
    rng = _generator(rng)
    p = _probability(probability)
    primitive = np.zeros((n, n), dtype=bool)
    order = np.zeros_like(primitive)
    ancestors: list[int] = []
    selected_counts = []
    width = (n + 7) // 8
    for j in range(n):
        selected = rng.random(j) < p
        primitive[:j, j] = selected
        selected_counts.append(int(np.count_nonzero(selected)))
        past = 0
        for parent in np.flatnonzero(selected):
            parent = int(parent)
            past |= ancestors[parent] | (1 << parent)
        ancestors.append(past)
        packed = np.frombuffer(past.to_bytes(width, "little"), dtype=np.uint8)
        order[:, j] = np.unpackbits(packed, bitorder="little")[:n]
    metadata = {
        "model": "transitive_percolation", "count": n, "probability": p,
        "selected_parent_counts": selected_counts,
        "primitive_edge_count": int(np.count_nonzero(primitive)),
        "relation_count": int(np.count_nonzero(order)),
        "closure_strategy": "birthwise_ancestor_bitset_union",
    }
    return GrowthHistory(order, primitive, metadata)


def _indices(values, n: int, name: str, *, permutation: bool = False) -> np.ndarray:
    array = np.asarray(values)
    if array.ndim != 1 or (array.size and array.dtype.kind not in "iu"):
        raise ValueError(f"{name} must be a one-dimensional integer index sequence")
    # Check before conversion to signed indices, which could overflow uint64.
    if np.any(array < 0) or np.any(array >= n) or len(np.unique(array)) != len(array):
        raise ValueError(f"{name} must contain distinct valid event indices")
    if permutation and len(array) != n:
        raise ValueError(f"{name} must be a permutation of all events")
    return array.astype(int, copy=True)


def _log_monomial(p: float, p_exponent: int, q_exponent: int) -> float:
    if (p == 0 and p_exponent) or (p == 1 and q_exponent):
        return -math.inf
    first = p_exponent * math.log(p) if p_exponent else 0.0
    second = q_exponent * math.log1p(-p) if q_exponent else 0.0
    return first + second


def _precursor_exponents(matrix: np.ndarray, indices: np.ndarray) -> tuple[int, int]:
    selected = np.zeros(len(matrix), dtype=bool)
    selected[indices] = True
    if np.any(matrix[np.ix_(~selected, selected)]):
        raise ValueError("precursor must be a down-set of the parent order")
    internal = matrix[np.ix_(indices, indices)]
    maxima = int(np.count_nonzero(~internal.any(axis=1)))
    return maxima, len(matrix) - len(indices)


def transition_log_probability(order, precursor, probability: float, *,
                               max_count: int = 512) -> float:
    """Log probability for a specified down-set: m log(p)+(n-s) log(1-p).

    ``precursor`` lists parent event indices, in any order. Empty sets are
    allowed; duplicates, invalid indices and subsets that are not down-sets
    are rejected. Endpoint probabilities follow the convention x**0=1.
    """
    matrix = _order(order, max_count)
    p = _probability(probability)
    indices = _indices(precursor, len(matrix), "precursor")
    maxima, outside = _precursor_exponents(matrix, indices)
    return _log_monomial(p, maxima, outside)


def transition_probability(order, precursor, probability: float, *,
                           max_count: int = 512) -> float:
    """Probability of one specified precursor, not an unlabeled transition."""
    return math.exp(transition_log_probability(order, precursor, probability,
                                               max_count=max_count))


def cover_relation_count(order, *, max_count: int = 512) -> int:
    """Count covers of a validated strict order with arbitrary event labels."""
    matrix = _order(order, max_count)
    future, past = _bit_rows(matrix), _bit_rows(matrix.T)
    return sum(not (future[a] & past[int(c)])
               for a in range(len(matrix)) for c in np.flatnonzero(matrix[a]))


def complete_order_log_weight(order, probability: float, *, max_count: int = 512) -> float:
    """Invariant weight of each natural-label history: L log(p)+I log(1-p).

    L is the cover count and I is the incomparable-pair count. This is not the
    probability of the unlabeled isomorphism class, which needs multiplicities.
    The same weight applies to every valid natural birth labeling of the order.
    """
    matrix = _order(order, max_count)
    p = _probability(probability)
    covers = cover_relation_count(matrix, max_count=max_count)
    incomparable = math.comb(len(matrix), 2) - int(np.count_nonzero(matrix))
    return _log_monomial(p, covers, incomparable)


def path_log_probability(order, probability: float, *, birth_order=None,
                         max_count: int = 512) -> float:
    """Sum elementary transition log weights along a specified natural history.

    ``birth_order`` is a permutation of the completed matrix's event indices.
    Its default is the matrix index order. It must be a linear extension;
    merely permuting a completed matrix is not a natural-label covariance test.
    """
    matrix = _order(order, max_count)
    p = _probability(probability)
    n = len(matrix)
    indices = (np.arange(n) if birth_order is None else
               _indices(birth_order, n, "birth_order", permutation=True))
    ordered = matrix[np.ix_(indices, indices)]
    if np.any(np.tril(ordered)):
        raise ValueError("birth_order must be a linear extension of the completed order")
    total = 0.0
    for j in range(n):
        precursor = np.flatnonzero(ordered[:j, j])
        maxima, outside = _precursor_exponents(ordered[:j, :j], precursor)
        total += _log_monomial(p, maxima, outside)
    return total


def thin_order(order, count: int, rng: np.random.Generator, *,
               max_count: int = 512) -> tuple[np.ndarray, np.ndarray]:
    """Uniform fixed-size induced order and sorted retained original indices.

    Restrict the closed relation directly: precedence remains even when its
    primitive paths pass through deleted events. This is not graph pruning.
    """
    matrix = _order(order, max_count)
    count = _count(count, len(matrix))
    rng = _generator(rng)
    indices = np.sort(rng.choice(len(matrix), size=count, replace=False))
    return matrix[np.ix_(indices, indices)].copy(), indices
