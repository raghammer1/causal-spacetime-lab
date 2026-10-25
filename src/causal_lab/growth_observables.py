"""Order-only growth diagnostics, including the exact semiorder obstruction."""
from __future__ import annotations

import math

import numpy as np

from .growth import _cap, _order
from .local_structure import local_observables
from .order_observables import _bit_rows


def _n31(matrix: np.ndarray) -> int:
    future, past = _bit_rows(matrix), _bit_rows(matrix.T)
    outgoing = [row.bit_count() for row in future]
    incoming = [row.bit_count() for row in past]
    n = len(matrix)
    result = 0
    for a in range(n):
        for c in np.flatnonzero(matrix[a]):
            c = int(c)
            middle = (future[a] & past[c]).bit_count()
            isolated = n - outgoing[a] - incoming[c] + middle
            result += middle * isolated
    return result


def induced_three_plus_one(order, *, max_count: int = 512) -> int:
    """Count induced 3+1 exactly, using chain endpoints and an isolated event.

    For a<c and m=|F(a) intersect P(c)|, each of the m middle vertices can be
    paired with any vertex outside F(a) union P(c). These vertices are
    incomparable with both endpoints and, by transitivity, with the middle.
    Thus n31=sum m*(N-|F(a)|-|P(c)|+m), with each four-subset counted once.
    """
    return _n31(_order(order, max_count))


def growth_observables(order, *, max_count: int = 512) -> dict:
    """Reuse local-order diagnostics and add exact forbidden-motif densities.

    Densities are undefined (None) for fewer than four events. These are finite
    structural summaries, not geometric dimensions or embedding certificates.
    """
    max_count = _cap(max_count)
    row = local_observables(order, max_count=max_count)
    matrix = np.asarray(order, dtype=bool)  # Validated by local_observables.
    row["n31"] = _n31(matrix)
    subsets = math.comb(row["count"], 4) if row["count"] >= 4 else 0
    row["n22_density"] = row["n22"] / subsets if subsets else None
    row["n31_density"] = row["n31"] / subsets if subsets else None
    return row
