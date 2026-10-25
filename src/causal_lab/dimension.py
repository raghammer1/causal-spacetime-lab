"""Flat-spacetime generators and order-only Myrheim--Meyer reconstruction.

The generator assumes a Minkowski background. The estimator consumes only a
transitive strict-order matrix; a plausible inferred dimension does not establish
that an arbitrary order approximates a spacetime.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


def _positive_real(value, name: str) -> float:
    if (not isinstance(value, (int, float, np.integer, np.floating))
            or isinstance(value, (bool, np.bool_)) or not math.isfinite(value)
            or value <= 0):
        raise ValueError(f"{name} must be finite and positive")
    return float(value)


def _generator_dimension(dimension: int) -> int:
    if (not isinstance(dimension, (int, np.integer))
            or isinstance(dimension, (bool, np.bool_)) or dimension not in (2, 3, 4)):
        raise ValueError("spacetime dimension must be the integer 2, 3 or 4")
    return int(dimension)


@dataclass(frozen=True)
class MinkowskiInterval:
    """Coordinates used for generation and independent evaluation, not estimation.

    ``x`` has shape ``(N, dimension - 1)`` and ``t`` has shape ``(N,)``. The
    generator's endpoints are (0, 0) and (duration, 0), with c=1. Manually supplied
    coordinates can be translated or Lorentz transformed for validation tests.
    """

    t: np.ndarray
    x: np.ndarray
    dimension: int
    duration: float
    density: float | None = None

    @property
    def count(self) -> int:
        return len(self.t)


def interval_volume(dimension: int, duration: float) -> float:
    """Physical volume of a flat d-dimensional Alexandrov interval.

    Integrating spatial balls of radius min(t, T-t) gives
    V = B_(d-1) T**d / (d * 2**(d-1)), where B_k is unit k-ball volume.
    In d=2,3,4 this is T²/2, pi*T³/12, pi*T⁴/24, respectively.
    """
    dimension = _generator_dimension(dimension)
    duration = _positive_real(duration, "duration")
    spatial = dimension - 1
    ball = math.pi ** (spatial / 2) / math.gamma(spatial / 2 + 1)
    try:
        volume = ball * duration**dimension / (dimension * 2**spatial)
    except OverflowError as exc:
        raise ValueError("interval volume must be finite and positive") from exc
    if not math.isfinite(volume) or volume <= 0:
        raise ValueError("interval volume must be finite and positive")
    return float(volume)


def sprinkle_minkowski(
    dimension: int,
    duration: float,
    rng: np.random.Generator,
    *,
    count: int | None = None,
    density: float | None = None,
) -> MinkowskiInterval:
    """Uniform events in a known flat Alexandrov interval in d=2,3,4.

    Specify exactly one of fixed ``count`` or Poisson ``density``. Fixed counts
    condition the Poisson process on N, isolating dimension from count effects.
    With q=min(t,T-t), q/(T/2) has CDF z**d. Conditional on t, spatial positions
    are uniform in the (d-1)-ball: radius/q has CDF z**(d-1), with an independent
    uniform sphere direction. A uniform bounding-box or radial draw is incorrect.
    """
    dimension = _generator_dimension(dimension)
    duration = _positive_real(duration, "duration")
    if (count is None) == (density is None):
        raise ValueError("specify exactly one of count or density")
    if count is not None:
        if (not isinstance(count, (int, np.integer)) or isinstance(count, (bool, np.bool_))
                or count < 0):
            raise ValueError("count must be a nonnegative integer")
        count = int(count)
    else:
        density = _positive_real(density, "density")
        mean = density * interval_volume(dimension, duration)
        if not math.isfinite(mean) or mean <= 0:
            raise ValueError("expected Poisson count must be finite and positive")
        count = int(rng.poisson(mean))
    spatial = dimension - 1
    if count == 0:
        return MinkowskiInterval(np.empty(0), np.empty((0, spatial)), dimension, duration, density)
    q = (duration / 2) * rng.random(count) ** (1 / dimension)
    t = np.where(rng.integers(0, 2, count) == 0, q, duration - q)
    directions = rng.normal(size=(count, spatial))
    norm = np.linalg.norm(directions, axis=1)
    # A zero Gaussian vector has probability zero in the continuous model but
    # can be returned by a finite PRNG; redraw rather than divide by zero.
    while np.any(norm == 0):
        zero = norm == 0
        directions[zero] = rng.normal(size=(int(zero.sum()), spatial))
        norm[zero] = np.linalg.norm(directions[zero], axis=1)
    directions /= norm[:, None]
    radius = q * rng.random(count) ** (1 / spatial)
    x = directions * radius[:, None]
    return MinkowskiInterval(t, x, dimension, duration, density)


def minkowski_order(interval: MinkowskiInterval) -> np.ndarray:
    """Strict timelike precedence from coordinates, O(N²) space.

    A[i,j] is true iff t[j]-t[i] > ||x[j]-x[i]||. Null ties are excluded,
    consistent with the original 1+1D code; they have zero probability under the
    ideal continuous generator. This function is part of the embedding pipeline.
    """
    dimension = _generator_dimension(interval.dimension)
    t = np.asarray(interval.t)
    x = np.asarray(interval.x)
    if (t.ndim != 1 or x.ndim != 2 or x.shape != (len(t), dimension - 1)
            or t.dtype.kind not in "biuf" or x.dtype.kind not in "biuf"
            or not np.all(np.isfinite(t)) or not np.all(np.isfinite(x))):
        raise ValueError("coordinates must be finite arrays with shapes (N,) and (N,d-1)")
    t, x = t.astype(float, copy=False), x.astype(float, copy=False)
    try:
        with np.errstate(over="raise", invalid="raise"):
            dt = t[None, :] - t[:, None]
            spatial_distance = np.zeros_like(dt)
            # hypot accumulation avoids overflow in squaring large finite coordinates.
            for axis in range(dimension - 1):
                spatial_distance = np.hypot(spatial_distance, x[None, :, axis] - x[:, None, axis])
    except FloatingPointError as exc:
        raise ValueError("coordinate differences exceed the supported floating-point range") from exc
    return dt > spatial_distance


def validate_order(order: np.ndarray) -> np.ndarray:
    """Validate a transitive strict order; never coerce arbitrary numbers to True.

    Binary numeric matrices are accepted. This validates O(N²) stored relations,
    including transitivity, using integer bitsets for successor-set containment.
    It does not establish geometric embeddability. A DAG adjacency/Hasse matrix
    needs its transitive closure before it is a valid input.
    """
    array = np.asarray(order)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("order must be a square matrix")
    if array.dtype.kind not in "biuf" or not np.all(np.isfinite(array)):
        raise ValueError("order must be a finite Boolean or binary numeric matrix")
    if not np.all((array == 0) | (array == 1)):
        raise ValueError("order entries must be zero or one")
    array = array.astype(bool, copy=False)
    if np.any(np.diag(array)) or np.any(array & array.T):
        raise ValueError("order must be irreflexive and asymmetric")
    packed = np.packbits(array, axis=1, bitorder="little")
    rows = [int.from_bytes(row.tobytes(), "little") for row in packed]
    for i, successors in enumerate(rows):
        remaining = successors
        while remaining:
            bit = remaining & -remaining
            j = bit.bit_length() - 1
            if rows[j] & ~successors:
                raise ValueError("order must be transitive and acyclic")
            remaining ^= bit
    return array


def ordering_probability(dimension: float) -> float:
    """Flat-interval comparable-pair probability p(d), for real d >= 1.

    R / binom(N,2) uses denominator 2*Gamma(3d/2), not the denominator 4
    appropriate to the large-N R/N² convention. This formula is a flat-space
    expectation, not a finite-sample identity or manifoldlikeness criterion.
    """
    dimension = _positive_real(dimension, "dimension")
    if dimension < 1:
        raise ValueError("analytic dimension must be at least one")
    # Exact known values also avoid treating analytic domain endpoints as
    # out-of-range solely because of cancellation in the lgamma expression.
    anchors = {1.0: 1.0, 2.0: 0.5, 3.0: 8 / 35, 4.0: 0.1}
    if dimension in anchors:
        return anchors[dimension]
    try:
        log_p = (math.lgamma(dimension + 1) + math.lgamma(dimension / 2)
                 - math.log(2) - math.lgamma(1.5 * dimension))
        probability = math.exp(log_p)
    except (OverflowError, ValueError) as exc:
        raise ValueError("dimension is outside the numerically supported range") from exc
    if not math.isfinite(probability) or probability <= 0:
        raise ValueError("dimension is outside the numerically supported range")
    return probability


def _inversion_domain(d_min: float, d_max: float) -> tuple[float, float, float, float]:
    d_min = _positive_real(d_min, "d_min")
    d_max = _positive_real(d_max, "d_max")
    if d_min < 1 or d_min >= d_max:
        raise ValueError("inversion domain requires 1 <= d_min < d_max")
    p_max = ordering_probability(d_min)
    p_min = ordering_probability(d_max)
    if p_min >= p_max:
        raise ValueError("inversion domain is not numerically resolvable")
    return d_min, d_max, p_min, p_max


def invert_ordering_fraction(r: float, d_min: float = 1, d_max: float = 10) -> float:
    """Invert p(d) by bounded bisection; invalid/out-of-domain values raise.

    No clipping occurs, including for antichains (r=0). The default interval is
    d in [1,10], with the d=1 endpoint available for total orders. Statistical
    uncertainty must be estimated across independent orders, not pairs.
    """
    d_min, d_max, p_min, p_max = _inversion_domain(d_min, d_max)
    if (not isinstance(r, (int, float, np.integer, np.floating))
            or isinstance(r, (bool, np.bool_)) or not math.isfinite(r) or not 0 <= r <= 1):
        raise ValueError("ordering fraction must be finite and between zero and one")
    r = float(r)
    if not p_min <= r <= p_max:
        raise ValueError("ordering fraction is outside the inversion domain")
    if r == p_max:
        return d_min
    if r == p_min:
        return d_max
    lower, upper = d_min, d_max
    for _ in range(80):
        midpoint = (lower + upper) / 2
        if midpoint == lower or midpoint == upper:
            break
        if ordering_probability(midpoint) > r:
            lower = midpoint
        else:
            upper = midpoint
    return float((lower + upper) / 2)


@dataclass(frozen=True)
class DimensionEstimate:
    count: int
    relations: int
    ordering_fraction: float | None
    dimension: float | None
    status: str


def estimate_dimension(order: np.ndarray, d_min: float = 1, d_max: float = 10) -> DimensionEstimate:
    """Order-only dimension estimate with explicit undefined/out-of-domain status.

    Coordinates, density and the generating dimension are neither accepted nor
    inspected. ``None`` is preserved for N<2 or unresolved inversion, rather than
    silently clamping or assigning a misleading dimension to sparse orders.
    """
    d_min, d_max, p_min, p_max = _inversion_domain(d_min, d_max)
    order = validate_order(order)
    count = len(order)
    relations = int(np.count_nonzero(order))
    if count < 2:
        return DimensionEstimate(count, relations, None, None, "undefined")
    fraction = relations / math.comb(count, 2)
    if not p_min <= fraction <= p_max:
        return DimensionEstimate(count, relations, fraction, None, "out_of_domain")
    dimension = invert_ordering_fraction(fraction, d_min, d_max)
    return DimensionEstimate(count, relations, fraction, dimension, "ok")
