"""Exact local finite-poset structure and explicitly sampled global motifs.

These are structural observables, not a test of physical spacetime.  Every
interval is open.  The definitions and double-counting identities are derived in
``docs/LOCAL_CAUSAL_STRUCTURE_THEORY.md``.  Sampling variance of global motifs
is conditional on a fixed order and is not ensemble uncertainty.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import itertools
import math

import numpy as np

from .dimension import validate_order
from .order_observables import _bit_rows, _bounded_matrix, order_observables


def _integer(value, name: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    if (not isinstance(value, (int, np.integer))
            or isinstance(value, (bool, np.bool_)) or value < minimum
            or (maximum is not None and value > maximum)):
        upper = "" if maximum is None else f" and at most {maximum}"
        raise ValueError(f"{name} must be an integer at least {minimum}{upper}")
    return int(value)


def _vertices(mask: int) -> list[int]:
    result = []
    while mask:
        bit = mask & -mask
        result.append(bit.bit_length() - 1)
        mask ^= bit
    return result


def _components(neighbours: list[int], mask: int) -> int:
    """Count components by bitset BFS, with empty graph convention zero."""
    remaining = mask
    components = 0
    while remaining:
        components += 1
        frontier = remaining & -remaining
        remaining ^= frontier
        while frontier and remaining:
            bit = frontier & -frontier
            frontier ^= bit
            found = neighbours[bit.bit_length() - 1] & remaining
            remaining ^= found
            frontier |= found
    return components


def _n22(successors: list[int], vertices: list[int], mask: int) -> int:
    """Each incomparable pair of minima determines exclusive successor sets."""
    rows = [successors[i] & mask for i in vertices]
    degrees = [row.bit_count() for row in rows]
    result = 0
    for index, a in enumerate(vertices):
        left = rows[index]
        for other in range(index + 1, len(vertices)):
            c = vertices[other]
            right = rows[other]
            if left & (1 << c) or right & (1 << a):
                continue
            common = (left & right).bit_count()
            result += (degrees[index] - common) * (degrees[other] - common)
    return result


def small_order_signature(order, *, max_count: int = 512) -> tuple[int, int]:
    """Return exact (comparability components, induced 2+2 count).

    The helper avoids extracting intervals when enumerating small reference
    orders. Empty and singleton orders have signatures (0,0) and (1,0).
    """
    matrix = validate_order(_bounded_matrix(order, max_count))
    successors = _bit_rows(matrix)
    predecessors = _bit_rows(matrix.T)
    mask = (1 << len(matrix)) - 1
    neighbours = [a | b for a, b in zip(successors, predecessors)]
    return (_components(neighbours, mask),
            _n22(successors, list(range(len(matrix))), mask))


def induced_two_plus_two(order, *, max_count: int = 512) -> int:
    """Count induced 2+2 exactly in O(N²) bounded-width bitset operations."""
    matrix = validate_order(_bounded_matrix(order, max_count))
    return _n22(_bit_rows(matrix), list(range(len(matrix))), (1 << len(matrix)) - 1)


def component_count(order, *, max_count: int = 512) -> int:
    """Number of components of the undirected comparability graph."""
    matrix = validate_order(_bounded_matrix(order, max_count))
    return _components(_bit_rows(matrix | matrix.T), (1 << len(matrix)) - 1)


@lru_cache(maxsize=6)
def _off_diagonal(n: int) -> tuple[tuple[int, int], ...]:
    return tuple((i, j) for i in range(n) for j in range(n) if i != j)


def _matrix_code(matrix: np.ndarray) -> int:
    return sum(int(matrix[i, j]) << bit
               for bit, (i, j) in enumerate(_off_diagonal(len(matrix))))


def _from_code(code: int, n: int) -> np.ndarray:
    matrix = np.zeros((n, n), dtype=bool)
    for bit, (i, j) in enumerate(_off_diagonal(n)):
        matrix[i, j] = bool(code & (1 << bit))
    return matrix


@lru_cache(maxsize=6)
def _permutations(n: int) -> np.ndarray:
    if not n:
        return np.empty((1, 0), dtype=int)
    return np.asarray(list(itertools.permutations(range(n))), dtype=int).reshape(-1, n)


def _canonical_unchecked(matrix: np.ndarray) -> int:
    n = len(matrix)
    if n <= 1:
        return 0
    permutations = _permutations(n)
    weights = np.zeros((n, n), dtype=np.uint64)
    for bit, (i, j) in enumerate(_off_diagonal(n)):
        weights[i, j] = 1 << bit
    relabeled = matrix[permutations[:, :, None], permutations[:, None, :]]
    return int(np.min(np.sum(relabeled * weights, axis=(1, 2), dtype=np.uint64)))


def canonical_poset_code(order) -> int:
    """Minimum row-major off-diagonal bit code over all permutations, N<=5.

    The direction is preserved: dual orders can have different codes. The event
    count must accompany a code when comparing orders of different sizes.
    """
    return _canonical_unchecked(validate_order(_bounded_matrix(order, 5)))


@lru_cache(maxsize=6)
def _unlabeled_codes(n: int) -> tuple[int, ...]:
    pairs = list(zip(*np.triu_indices(n, 1)))
    codes = set()
    for mask in range(1 << len(pairs)):
        matrix = np.zeros((n, n), dtype=bool)
        for bit, pair in enumerate(pairs):
            matrix[pair] = bool(mask & (1 << bit))
        integer = matrix.astype(np.uint8)
        if np.any((integer @ integer > 0) & ~matrix):
            continue
        codes.add(_canonical_unchecked(matrix))
    return tuple(sorted(codes))


def enumerate_unlabeled_posets(count: int) -> list[np.ndarray]:
    """Complete representatives for N<=5, returned as independent arrays.

    Every finite order has a topological labeling, so exhausting forward
    transitive relations and quotienting all relabelings is complete. The
    factorial canonicalization is deliberately capped at five events.
    """
    n = _integer(count, "count", maximum=5)
    return [_from_code(code, n) for code in _unlabeled_codes(n)]


@lru_cache(maxsize=1)
def _four_lookup() -> tuple[tuple[int, ...], np.ndarray]:
    codes = _unlabeled_codes(4)
    lookup = np.full(1 << 12, -1, dtype=np.int16)
    for index, code in enumerate(codes):
        matrix = _from_code(code, 4)
        for permutation in _permutations(4):
            lookup[_matrix_code(matrix[np.ix_(permutation, permutation)])] = index
    lookup.flags.writeable = False
    return codes, lookup


def motif_catalog() -> list[dict]:
    """JSON-native metadata for the 16 directed four-event isomorphism classes.

    IDs are the ascending canonical 12-bit codes. The explicit dual ID prevents
    conflating relabeling invariance with time-reversal invariance.
    """
    codes, lookup = _four_lookup()
    result = []
    for index, code in enumerate(codes):
        matrix = _from_code(code, 4)
        old = order_observables(matrix)
        components, n22 = small_order_signature(matrix)
        result.append({
            "id": index, "canonical_code": code, "order": matrix.tolist(),
            "relations": old["relations"], "height": old["longest_chain"],
            "minimal": int(np.count_nonzero(~matrix.any(axis=0))),
            "maximal": int(np.count_nonzero(~matrix.any(axis=1))),
            "components": components, "n22": n22,
            "dual_id": int(lookup[_matrix_code(matrix.T)]),
        })
    return result


def _four_codes(matrix: np.ndarray, subsets: np.ndarray) -> np.ndarray:
    pairs = np.asarray(_off_diagonal(4), dtype=int)
    values = matrix[subsets[:, pairs[:, 0]], subsets[:, pairs[:, 1]]]
    return np.sum(values.astype(np.uint16) << np.arange(12, dtype=np.uint16),
                  axis=1, dtype=np.uint16)


def motif_counts(order, rng: np.random.Generator | None = None, *, draws: int = 4096,
                 exact_limit: int = 16, max_count: int = 512) -> dict:
    """All four-event motif frequencies, exact or unbiased conditional samples.

    Larger orders use independent uniform four-subsets WITH replacement. Duplicate
    vertices within a proposed subset are rejected; repeated complete subsets
    remain valid draws. ``mc_variance`` is the unbiased estimated conditional
    variance p_hat*(1-p_hat)/(draws-1), not uncertainty between parent orders.
    Off-diagonal covariance is -p_hat[i]*p_hat[j]/(draws-1). Exact enumeration has
    zero Monte Carlo variance. N<4 has no distribution and returns None fields.
    """
    matrix = validate_order(_bounded_matrix(order, max_count))
    requested = _integer(draws, "draws", minimum=2)
    limit = _integer(exact_limit, "exact_limit", maximum=32)
    n = len(matrix)
    if n < 4:
        return {"method": "undefined", "draws": 0, "counts": [0] * 16,
                "frequencies": None, "mc_variance": None}
    if n <= limit:
        subsets = np.asarray(list(itertools.combinations(range(n), 4)), dtype=int)
        method = "exact"
    else:
        if not isinstance(rng, np.random.Generator):
            raise ValueError("sampling requires an explicit NumPy Generator")
        remaining = requested
        chunks = []
        while remaining:
            candidate = np.sort(rng.integers(0, n, size=(remaining, 4)), axis=1)
            valid = candidate[np.all(np.diff(candidate, axis=1) > 0, axis=1)]
            chunks.append(valid)
            remaining -= len(valid)
        subsets = np.concatenate(chunks, axis=0)
        method = "sampled"
    _, lookup = _four_lookup()
    classes = lookup[_four_codes(matrix, subsets)]
    if np.any(classes < 0):
        raise RuntimeError("validated order has an unrecognized four-event motif")
    counts = np.bincount(classes, minlength=16)
    sample_count = len(subsets)
    frequencies = counts / sample_count
    variance = (frequencies * (1 - frequencies) / (sample_count - 1)
                if method == "sampled" else np.zeros(16))
    return {"method": method, "draws": sample_count, "counts": counts.tolist(),
            "frequencies": frequencies.tolist(), "mc_variance": variance.tolist()}


def local_observables(order, *, max_count: int = 512) -> dict:
    """Return exact global and interval-local structure with historical fields.

    Sparse profiles contain [size,components,count] and, for size-eight intervals,
    [components,n22,count]. All related endpoint intervals contribute, including
    empty intervals. Size-specific counts are zero when absent; no conditional
    probability is fabricated. Overlap moments concern distinct unordered pairs
    of open intervals and their population variance is not a standard error.
    """
    row = order_observables(order, max_count=max_count)
    matrix = np.asarray(order, dtype=bool)  # Already validated by the old extractor.
    n = len(matrix)
    successors, predecessors = _bit_rows(matrix), _bit_rows(matrix.T)
    outgoing = [item.bit_count() for item in successors]
    incoming = [item.bit_count() for item in predecessors]
    neighbours = [a | b for a, b in zip(successors, predecessors)]
    membership = [a * b for a, b in zip(outgoing, incoming)]
    chains3 = sum(membership)
    chains4 = sum(incoming[b] * outgoing[int(c)]
                  for b in range(n) for c in np.flatnonzero(matrix[b]))
    diamonds4 = sum(math.comb(m, 2) * count
                    for m, count in enumerate(row["interval_histogram"])) - chains4
    overlap1 = sum(math.comb(value, 2) for value in membership)
    overlap2 = 0
    for i in range(n):
        for j in range(i + 1, n):
            both = ((successors[i] & successors[j]).bit_count()
                    * (predecessors[i] & predecessors[j]).bit_count())
            overlap2 += math.comb(both, 2)
    pairs = math.comb(row["relations"], 2)
    overlap_mean = overlap1 / pairs if pairs else None
    # Integer numerator avoids subtracting nearly equal floating-point moments.
    variance_numerator = (overlap1 + 2 * overlap2) * pairs - overlap1 * overlap1
    overlap_variance = variance_numerator / (pairs * pairs) if pairs else None
    profile = Counter()
    m8_joint = Counter()
    m2_count = m2_connected = m4_count = m8_count = m8_connected = 0
    m8_n22_sum = m8_connected_n22_sum = 0
    m4_motifs = [0] * 16
    _, lookup = _four_lookup()
    for a in range(n):
        for b in np.flatnonzero(matrix[a]):
            interval = successors[a] & predecessors[int(b)]
            size = interval.bit_count()
            components = _components(neighbours, interval)
            profile[(size, components)] += 1
            if size == 2:
                m2_count += 1
                m2_connected += components == 1
            elif size == 4:
                m4_count += 1
                vertices = _vertices(interval)
                motif = int(lookup[_matrix_code(matrix[np.ix_(vertices, vertices)])])
                if motif < 0:
                    raise RuntimeError("unrecognized interval motif")
                m4_motifs[motif] += 1
            elif size == 8:
                m8_count += 1
                connected = components == 1
                m8_connected += connected
                n22 = _n22(successors, _vertices(interval), interval)
                m8_n22_sum += n22
                m8_connected_n22_sum += int(connected) * n22
                m8_joint[(components, n22)] += 1
    row.update(
        n22=_n22(successors, list(range(n)), (1 << n) - 1),
        chains3=chains3, chains4=chains4, diamonds4=diamonds4,
        overlap_sum=overlap1, overlap_choose2_sum=overlap2,
        overlap_mean=overlap_mean, overlap_variance=overlap_variance,
        interval_component_profile=[[m, k, count] for (m, k), count in sorted(profile.items())],
        interval_m2_count=m2_count, interval_m2_connected=m2_connected,
        interval_m4_count=m4_count, interval_m4_motif_counts=m4_motifs,
        interval_m8_count=m8_count, interval_m8_connected=m8_connected,
        interval_m8_n22_sum=m8_n22_sum,
        interval_m8_connected_n22_sum=m8_connected_n22_sum,
        interval_m8_joint=[[k, count22, count] for (k, count22), count in sorted(m8_joint.items())],
    )
    return row
