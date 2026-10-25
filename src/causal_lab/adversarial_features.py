"""Order-only features and exact checks for the adversarial geometry study.

The abundance vector describes endpoint pairs, not independent observations.
Identical selected features do not imply isomorphic orders or continuum geometry.
"""
from __future__ import annotations

from collections.abc import Mapping
import math

import numpy as np

from .order_observables import indistinguishable_pair, order_observables


FIVE_FEATURES = ("ordering_fraction", "chain_fraction", "link_fraction",
                 "interval_mean_fraction", "interval_ge4_fraction")
ABUNDANCE_BIN_LABELS = ("incomparable", "0", "1", "2", "3", "4-7", "8-15",
                        "16-31", "32-63", "64+")
SEARCH_FEATURES = FIVE_FEATURES + tuple("abundance_" + name for name in ABUNDANCE_BIN_LABELS)


def extract_features(order, *, max_count: int = 512) -> dict:
    """Return validated finite-order observables and ten abundance probabilities.

    Existing observable names and definitions are preserved. For N>=2, the
    abundance categories are incomparable endpoint pairs followed by internal
    interval sizes 0,1,2,3,4-7,8-15,16-31,32-63,64+. All ten counts divide by
    binom(N,2), rather than the number of related pairs. Their sum is one.

    N<2 has no endpoint-pair probability distribution and yields None. For an
    antichain with N>=2 the abundance vector is [1,0,...,0], although the old
    conditional interval features remain None. All dict values are JSON native.
    Minimal/maximal counts are additional directional diagnostics, not detector
    inputs. They exchange under order duality.
    """
    row = order_observables(order, max_count=max_count)
    # The call above has already checked the original matrix and the event cap.
    matrix = np.asarray(order, dtype=bool)
    n = row["count"]
    if n >= 2:
        pairs = n * (n - 1) // 2
        counts = [pairs - row["relations"]] + [0] * 9
        boundaries = (0, 1, 2, 3, 4, 8, 16, 32, 64)
        for size, abundance in enumerate(row["interval_histogram"]):
            index = int(np.searchsorted(boundaries, size, side="right"))
            counts[index] += abundance
        probability = [number / pairs for number in counts]
    else:
        probability = None

    has_predecessor = matrix.any(axis=0)
    has_successor = matrix.any(axis=1)
    minimal = int(np.count_nonzero(~has_predecessor))
    maximal = int(np.count_nonzero(~has_successor))
    isolated = int(np.count_nonzero(~(has_predecessor | has_successor)))
    row.update(abundance_vector=probability, minimal_count=minimal,
               maximal_count=maximal, isolated_count=isolated,
               minimal_fraction=minimal / n if n else None,
               maximal_fraction=maximal / n if n else None)
    return row


def feature_vector(row: Mapping) -> np.ndarray:
    """Return the registered 15-dimensional search vector from an extracted row.

    Entries are the five historical features followed by the ten unconditional
    abundance probabilities. Undefined values become NaN for explicit handling
    by the caller; they are never imputed to zero. Malformed, nonfinite or
    out-of-range supplied values are rejected. Inference needs no truth labels,
    coordinates, generating dimension or RNG state.
    """
    if not isinstance(row, Mapping):
        raise ValueError("features must be supplied as a mapping")
    try:
        values = [row[name] for name in FIVE_FEATURES]
        abundance = row["abundance_vector"]
    except KeyError as error:
        raise ValueError(f"missing feature: {error.args[0]}") from error
    if abundance is None:
        abundance_values = [None] * len(ABUNDANCE_BIN_LABELS)
    else:
        try:
            abundance_values = list(abundance)
        except TypeError as error:
            raise ValueError("abundance_vector must contain ten probabilities") from error
        if len(abundance_values) != len(ABUNDANCE_BIN_LABELS):
            raise ValueError("abundance_vector must contain ten probabilities")
        if any(value is None for value in abundance_values):
            raise ValueError("abundance_vector must be wholly defined or None")

    def scalar(value):
        if value is None:
            return math.nan
        if (not isinstance(value, (int, float, np.integer, np.floating))
                or isinstance(value, (bool, np.bool_)) or not math.isfinite(value)
                or not 0 <= value <= 1):
            raise ValueError("defined feature values must be finite numbers in [0, 1]")
        return float(value)

    result = np.asarray([scalar(value) for value in values + abundance_values])
    if abundance is not None and not math.isclose(float(result[5:].sum()), 1.0,
                                                  rel_tol=0, abs_tol=1e-12):
        raise ValueError("abundance probabilities must sum to one")
    return result


def expected_interval_abundance_2d(count: int) -> np.ndarray:
    """Exact fixed-N d=2 expectation, evaluated in floating point for N<=512.

    For harmonic numbers h_k, the m-th entry is
      N*(h_(N-1)-h_m) + (m+1)*(h_N-h_(m+1)) - 2*(N-1-m).
    The derivation in ADVERSARIAL_GEOMETRY_THEORY.md conditions on the endpoint
    coordinates and uses a binomial law for the other N-2 events. It is not the
    Poisson-count expectation evaluated at its mean count. Direct harmonic-tail
    sums avoid subtracting two almost equal cumulative harmonic numbers.

    For N<2 return [0.0], matching the empty histogram convention of the order
    extractor. This expectation is specific to a uniform Alexandrov interval.
    """
    if (not isinstance(count, (int, np.integer)) or isinstance(count, (bool, np.bool_))
            or count < 0 or count > 512):
        raise ValueError("count must be an integer between 0 and 512")
    n = int(count)
    if n < 2:
        return np.array([0.0])
    return np.asarray([
        n * math.fsum(1 / k for k in range(m + 1, n))
        + (m + 1) * math.fsum(1 / k for k in range(m + 2, n + 1))
        - 2 * (n - 1 - m)
        for m in range(n - 1)
    ])


def nondual_pair() -> tuple[np.ndarray, np.ndarray]:
    """Two nonisomorphic, nondual ten-event orders with identical full histograms.

    Inside a unique bottom and top, the first order has an eight-cycle bipartite
    comparability graph; the second has two disjoint K2,2 graphs. Removing the
    unique extrema leaves different connected-component counts, an invariant
    under isomorphism and dual isomorphism. Both histograms are
    [16,0,8,0,0,0,0,0,1], R=25 and height=4. This finite example makes no claim
    about an asymptotic geometric rigidity conjecture.
    """
    first = np.zeros((10, 10), dtype=bool)
    second = first.copy()
    for order in (first, second):
        order[0, 1:] = True
        order[:9, 9] = True
    for i in range(4):
        first[1 + i, 5 + i] = True
        first[1 + i, 5 + (i + 1) % 4] = True
        for j in range(4):
            if i // 2 == j // 2:
                second[1 + i, 5 + j] = True
    return first, second


def exact_counterexamples() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Return independent dual and nondual example arrays for tests and figures."""
    return {"dual": indistinguishable_pair(), "nondual": nondual_pair()}
