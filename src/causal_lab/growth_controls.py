"""Explicit reference ensembles, kept separate from intrinsic causal growth."""
from __future__ import annotations

import hashlib
import math

import numpy as np

from .dimension import MinkowskiInterval, minkowski_order, sprinkle_minkowski
from .growth import _cap, transitive_percolation
from .order_observables import _count, _probability


MATCHED_EDGE_PROBABILITY = (1 - math.sqrt(1 - 4 / (3 * math.sqrt(2)))) / 2


def pack_order(order):
    matrix = np.asarray(order, dtype=bool)
    return {"shape": list(matrix.shape), "bitorder": "little",
            "packed_hex": np.packbits(matrix, bitorder="little").tobytes().hex()}


def order_hash(order):
    """Hash row-major Boolean bytes, independently of archive compression."""
    return hashlib.sha256(np.asarray(order, dtype=np.uint8).tobytes()).hexdigest()


def generate_history(family, parameter, count, rng):
    """Return closed order and exact reconstruction data for an explicit family.

    Only percolation is a maximal-element birth process. Other families are
    independent reference ensembles with nested iid prefixes, not growth laws.
    Per-point sampling keeps reference prefixes identical when count extends.
    """
    n = _count(count, _cap(512))
    if family == "percolation":
        history = transitive_percolation(n, rng, parameter)
        return history.order, {"primitive_edges": pack_order(history.primitive_edges),
                               "metadata": history.metadata}
    if family == "minkowski":
        # Reuse the verified uniform-volume law, drawing one iid event at a time.
        points = [sprinkle_minkowski(parameter, 1., rng, count=1) for _ in range(n)]
        t = np.asarray([point.t[0] for point in points])
        x = np.asarray([point.x[0] for point in points]).reshape(n, parameter - 1)
        interval = MinkowskiInterval(t, x, parameter, 1.)
        return minkowski_order(interval), {"coordinates": {"t": t.tolist(), "x": x.tolist(),
                  "dimension": parameter, "duration": 1.},
                  "metadata": {"model": "iid_flat_diamond_reference", "intrinsic_growth": False}}
    if family == "semiorder":
        delta = _probability(parameter)
        utilities = rng.random(n)
        return utilities[None, :] - utilities[:, None] > delta, {
            "utilities": utilities.tolist(), "metadata": {"model": "iid_semiorder_control",
            "threshold": delta, "intrinsic_growth": False}}
    if family == "matched_bipartite":
        probability = _probability(parameter)
        layers = np.zeros(n, dtype=np.uint8)
        order = np.zeros((n, n), dtype=bool)
        for j in range(n):
            layers[j] = int(rng.integers(0, 2))
            selected = rng.random(j) < probability
            if layers[j]:
                order[:j, j] = selected & (layers[:j] == 0)
            else:
                order[j, :j] = selected & (layers[:j] == 1)
        return order, {"layers": layers.tolist(), "cross_edges": pack_order(order),
                       "metadata": {"model": "iid_matched_22_height_two_control",
                                    "edge_probability": probability, "intrinsic_growth": False}}
    raise ValueError("unknown study family")
