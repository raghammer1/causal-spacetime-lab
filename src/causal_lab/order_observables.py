"""Finite, order-only diagnostics and adversarial partial orders.

These observables describe a finite poset. Agreement with a sprinkled ensemble
does not prove that the poset is manifold-like. Every public matrix operation
has an explicit event cap; the study uses at most 256 events by default.
"""
from __future__ import annotations

import numpy as np

from .dimension import validate_order


INTERVAL_BIN_LABELS = ("0", "1", "2-3", "4-7", "8-15", "16-31", "32-63", "64+")


def _count(value: int, max_count: int) -> int:
    for name, number in (("max_count", max_count), ("count", value)):
        if (not isinstance(number, (int, np.integer))
                or isinstance(number, (bool, np.bool_)) or number < 0):
            raise ValueError(f"{name} must be a nonnegative integer")
    if value > max_count:
        raise ValueError(f"count exceeds the explicit limit of {max_count}")
    return int(value)


def _probability(value: float) -> float:
    if (not isinstance(value, (float, int, np.floating, np.integer))
            or isinstance(value, (bool, np.bool_)) or not np.isfinite(value)
            or not 0 <= value <= 1):
        raise ValueError("edge_probability must be finite and in [0, 1]")
    return float(value)


def _bounded_matrix(matrix, max_count: int) -> np.ndarray:
    array = np.asarray(matrix)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("matrix must be square")
    _count(len(array), max_count)
    return array


def _bit_rows(matrix: np.ndarray) -> list[int]:
    return [int.from_bytes(row.tobytes(), "little")
            for row in np.packbits(matrix, axis=1, bitorder="little")]


def order_observables(order, *, max_count: int = 512) -> dict:
    """Return exact finite-poset observables, without embedding information.

    ``interval_histogram[k]`` counts related endpoint pairs with exactly k
    intervening events. Endpoints are excluded. Its sum is R, the number of
    comparable unordered pairs, counted once in a strict order. ``interval_bins``
    gives fractions of related pairs in the eight documented cardinality bins;
    it and other conditional interval fractions are None when R=0.

    The mean interval fraction divides the mean cardinality by max(N-2,1).
    Validation, packed bit intersections and dynamic programming are bounded by
    ``max_count``; no cubic matrix product or coordinate lookup is used.
    """
    matrix = validate_order(_bounded_matrix(order, max_count))
    n = len(matrix)
    relations = int(np.count_nonzero(matrix))
    histogram = [0] * max(n - 1, 1)
    successors = _bit_rows(matrix)
    predecessors = _bit_rows(matrix.T)
    for i in range(n):
        for j in np.flatnonzero(matrix[i]):
            cardinality = (successors[i] & predecessors[int(j)]).bit_count()
            histogram[cardinality] += 1

    # In a transitive strict order, every predecessor has fewer predecessors.
    # Validation above makes this a topological order even after relabeling.
    heights = np.ones(n, dtype=int)
    for j in np.argsort(matrix.sum(axis=0), kind="stable"):
        earlier = np.flatnonzero(matrix[:, j])
        if len(earlier):
            heights[j] = int(np.max(heights[earlier])) + 1
    height = int(np.max(heights)) if n else 0
    if relations:
        mean = sum(k * abundance for k, abundance in enumerate(histogram)) / relations
        boundaries = np.array([0, 1, 2, 4, 8, 16, 32, 64])
        binned = [0] * len(boundaries)
        for k, abundance in enumerate(histogram):
            binned[int(np.searchsorted(boundaries, k, side="right")) - 1] += abundance
        bins = [abundance / relations for abundance in binned]
        link_fraction = histogram[0] / relations
        mean_fraction = mean / max(n - 2, 1)
        ge4_fraction = sum(histogram[4:]) / relations
    else:
        mean = bins = link_fraction = mean_fraction = ge4_fraction = None
    return {
        "count": n,
        "relations": relations,
        "ordering_fraction": relations / (n * (n - 1) / 2) if n >= 2 else None,
        "longest_chain": height,
        "chain_fraction": height / n if n else 0.0,
        "interval_histogram": histogram,
        "interval_bins": bins,
        "link_count": histogram[0],
        "link_fraction": link_fraction,
        "interval_mean": mean,
        "interval_mean_fraction": mean_fraction,
        "interval_ge4_fraction": ge4_fraction,
    }


# A descriptive spelling retained for callers constructing a study pipeline.
observe_order = order_observables


def total_order(count: int, *, max_count: int = 512) -> np.ndarray:
    n = _count(count, max_count)
    return np.triu(np.ones((n, n), dtype=bool), k=1)


def antichain(count: int, *, max_count: int = 512) -> np.ndarray:
    n = _count(count, max_count)
    return np.zeros((n, n), dtype=bool)


def layered_order(count: int, rng: np.random.Generator, layers: int = 3,
                  *, max_count: int = 512) -> np.ndarray:
    """Assign independent uniform layer labels and relate every earlier layer.

    Empty layers are allowed; events within a layer are incomparable. This is
    an abstract order generator with no prescribed spacetime metric.
    """
    n = _count(count, max_count)
    if (not isinstance(layers, (int, np.integer)) or isinstance(layers, (bool, np.bool_))
            or layers < 1):
        raise ValueError("layers must be a positive integer")
    labels = rng.integers(0, int(layers), size=n)
    return labels[:, None] < labels[None, :]


def transitive_closure(adjacency, *, max_count: int = 512) -> np.ndarray:
    """Return the strict reachability relation of a finite DAG.

    Reject self-relations, nonbinary/malformed data and every directed cycle.
    The input may be a Hasse or other DAG adjacency matrix; unlike an order
    matrix, it need not already contain its transitive relations. A topological
    traversal and explicit successor-bitset unions construct the closure.
    """
    array = _bounded_matrix(adjacency, max_count)
    if (array.dtype.kind not in "buif" or not np.all(np.isfinite(array))
            or not np.all((array == 0) | (array == 1))):
        raise ValueError("adjacency must contain only finite binary values")
    matrix = np.asarray(array, dtype=bool)
    if np.any(np.diag(matrix)):
        raise ValueError("adjacency must have no self-relations")
    n = len(matrix)
    indegree = matrix.sum(axis=0).astype(int)
    pending = [int(i) for i in np.flatnonzero(indegree == 0)]
    topological = []
    while pending:
        i = pending.pop()
        topological.append(i)
        for j in np.flatnonzero(matrix[i]):
            indegree[j] -= 1
            if indegree[j] == 0:
                pending.append(int(j))
    if len(topological) != n:
        raise ValueError("adjacency must be acyclic")
    rows = _bit_rows(matrix)
    for i in reversed(topological):
        reachable = rows[i]
        for j in np.flatnonzero(matrix[i]):
            reachable |= rows[int(j)]
        rows[i] = reachable
    result = np.zeros((n, n), dtype=bool)
    width = (n + 7) // 8
    for i, row in enumerate(rows):
        packed = np.frombuffer(row.to_bytes(width, "little"), dtype=np.uint8)
        result[i] = np.unpackbits(packed, bitorder="little")[:n]
    return result


def random_dag_order(count: int, rng: np.random.Generator, edge_probability: float,
                     *, max_count: int = 512) -> np.ndarray:
    """Independent forward edges, explicit transitive closure, then relabeling.

    The latent birth-label order makes the adjacency acyclic; returned labels
    are permuted so their order is not an observable shortcut.
    """
    n = _count(count, max_count)
    probability = _probability(edge_probability)
    edges = np.triu(rng.random((n, n)) < probability, k=1)
    order = transitive_closure(edges, max_count=max_count)
    permutation = rng.permutation(n)
    return order[np.ix_(permutation, permutation)]


def bipartite_order(count: int, rng: np.random.Generator, edge_probability: float,
                    *, max_count: int = 512) -> np.ndarray:
    """A balanced two-layer order with independent cross-layer relations.

    Its height is at most two. With a=floor(N/2), b=N-a, the mean ordering
    fraction for N>=2 is q*a*b/C(N,2). Thus a calibration set can determine q
    without using holdout samples. Any fitted parameter boundary must be
    reported by the external calibration code; this constructor never clips q.
    """
    n = _count(count, max_count)
    probability = _probability(edge_probability)
    lower = n // 2
    order = np.zeros((n, n), dtype=bool)
    order[:lower, lower:] = rng.random((lower, n - lower)) < probability
    permutation = rng.permutation(n)
    return order[np.ix_(permutation, permutation)]


def indistinguishable_pair() -> tuple[np.ndarray, np.ndarray]:
    """Nonisomorphic V and Lambda orders sharing every selected observable.

    V has two minimal elements and one maximal element; its dual has one
    minimal and two maximal elements, so no direction-preserving isomorphism
    exists. The selected symmetric summaries deliberately omit that distinction.
    This small counterexample is not a claim about spacetime dimensionality.
    """
    v = np.array([[0, 0, 1], [0, 0, 1], [0, 0, 0]], dtype=bool)
    return v, v.T.copy()
