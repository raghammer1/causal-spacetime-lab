"""Abstract-order controls and a fixed-budget, coordinate-free adversarial search.

Generator provenance is not a test of manifoldlikeness. In particular, the
intersection of two uniform permutations has the same fixed-count order law as
a uniform 1+1-dimensional Alexandrov-interval sample. Search failures establish
only failure to match a prescribed target within the recorded finite budget.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .adversarial_features import extract_features, feature_vector
from .dimension import MinkowskiInterval, minkowski_order
from .order_observables import _count, _probability, transitive_closure


def _generator(rng: np.random.Generator) -> np.random.Generator:
    if not isinstance(rng, np.random.Generator):
        raise ValueError("rng must be a NumPy Generator")
    return rng


def _integer(value, name: str, minimum: int, maximum: int | None = None) -> int:
    if (not isinstance(value, (int, np.integer))
            or isinstance(value, (bool, np.bool_)) or value < minimum
            or (maximum is not None and value > maximum)):
        upper = "" if maximum is None else f" and <= {maximum}"
        raise ValueError(f"{name} must be an integer >= {minimum}{upper}")
    return int(value)


def random_interval_order(count: int, rng: np.random.Generator, *,
                          max_count: int = 512) -> np.ndarray:
    """Pair a uniform permutation of 2N abstract endpoints into N intervals.

    Event i precedes j iff right_i < left_j. Endpoints are distinct integer
    ranks, not supplied spacetime coordinates. Transitivity follows directly
    from right_i < left_j < right_j < left_k. For two random intervals two of
    the six interleavings are disjoint, giving comparable-pair probability 1/3.
    """
    n = _count(count, max_count)
    rng = _generator(rng)
    endpoints = rng.permutation(2 * n).reshape(n, 2)
    left = endpoints.min(axis=1)
    right = endpoints.max(axis=1)
    return right[:, None] < left[None, :]


def rank_intersection_order(count: int, rng: np.random.Generator, *,
                            ranks: int = 2, max_count: int = 512) -> np.ndarray:
    """Intersect independent uniform total orders on the same event labels.

    The two-rank case is a law-overlap positive control, not a negative family.
    No coordinate-free construction label can distinguish it statistically
    from fixed-count uniform d=2 diamond orders.
    """
    n = _count(count, max_count)
    rng = _generator(rng)
    ranks = _integer(ranks, "ranks", 1, 64)
    order = ~np.eye(n, dtype=bool)
    for _ in range(ranks):
        positions = rng.permutation(n)
        order &= positions[:, None] < positions[None, :]
    return order


def uniform_box_order(count: int, rng: np.random.Generator, dimension: int, *,
                      max_count: int = 512) -> np.ndarray:
    """Flat Lorentzian order in a unit spacetime box, a boundary stress control.

    Times are uniform on [0,1), spatial coordinates on [-1/2,1/2). This is a
    valid flat spacetime sampling model with a boundary different from an
    Alexandrov interval, and is excluded from negative-control advancement.
    """
    n = _count(count, max_count)
    rng = _generator(rng)
    dimension = _integer(dimension, "dimension", 2, 4)
    interval = MinkowskiInterval(rng.random(n),
                                 rng.random((n, dimension - 1)) - 0.5,
                                 dimension, 1.0)
    return minkowski_order(interval)


def _layers(count: int, height: int, rng: np.random.Generator):
    """Return topologically sorted layer labels and protected backbone edges."""
    labels = np.concatenate((np.arange(height), rng.integers(height, size=count-height)))
    labels.sort(kind="stable")
    allowed = labels[:, None] < labels[None, :]
    # Every layer is nonempty because it received one reserved event.
    backbone = np.flatnonzero(np.r_[True, labels[1:] != labels[:-1]])
    protected = np.zeros((count, count), dtype=bool)
    protected[backbone[:-1], backbone[1:]] = True
    return labels, allowed, protected


def layered_backbone_order(count: int, rng: np.random.Generator, height: int,
                           edge_probability: float, *,
                           max_count: int = 512) -> np.ndarray:
    """Generate an order whose height is exactly the prescribed H.

    One event is reserved in each of H layers; other events receive iid uniform
    layer labels. All edges increase layer labels, bounding height by H. A
    protected consecutive-layer backbone realizes height H. Other cross-layer
    edges are Bernoulli draws; explicit closure precedes random relabeling.
    """
    n = _count(count, max_count)
    rng = _generator(rng)
    height = _integer(height, "height", 1, n)
    probability = _probability(edge_probability)
    _, allowed, protected = _layers(n, height, rng)
    adjacency = (allowed & (rng.random((n, n)) < probability)) | protected
    order = transitive_closure(adjacency, max_count=max_count)
    permutation = rng.permutation(n)
    return order[np.ix_(permutation, permutation)]


@dataclass(frozen=True)
class SearchResult:
    """Two paired checkpoints from one independent finite search."""

    height_fraction_order: np.ndarray
    multifeature_order: np.ndarray
    metadata: dict


def optimize_order(count: int, rng: np.random.Generator, target: dict,
                   scales, *, steps: int = 64, max_count: int = 512) -> SearchResult:
    """Match an order-only development target with the registered fixed search.

    The primary budget is 64 evaluations: q=0, q=1, ten coupled-uniform
    bisections; then 52 annealing proposals. Smaller budgets >=4 are supported
    only for tests/smokes: phase one has min(12,steps//2) evaluations. Scores in
    phase one affect only ordering-fraction matching. Phase two minimizes RMS
    standardized discrepancy of the five original features plus ten abundance
    probabilities. It protects the target height and retains every failed match.

    ``target`` is an extracted development-order row, not coordinates; ``scales``
    are 15 calibration-cell sample SDs already floored at 1e-9. A donor with
    undefined conditional features is explicitly rejected, never resampled here.
    """
    n = _count(count, max_count)
    if n < 2:
        raise ValueError("search requires at least two events")
    rng = _generator(rng)
    steps = _integer(steps, "steps", 4)
    if not isinstance(target, dict):
        raise ValueError("target must be an extracted feature dictionary")
    if target.get("count") != n:
        raise ValueError("target count must equal search count")
    height = _integer(target.get("longest_chain"), "target height", 2, n)
    try:
        goal = np.asarray(feature_vector(target), dtype=float)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("target must have 15 defined order features") from exc
    scale = np.asarray(scales)
    if (goal.shape != (15,) or not np.all(np.isfinite(goal))
            or np.any(goal < 0) or np.any(goal > 1)):
        raise ValueError("target must have 15 finite features in [0,1]")
    if (scale.shape != (15,) or scale.dtype.kind not in "iuf"
            or not np.all(np.isfinite(scale)) or np.any(scale < 1e-9)):
        raise ValueError("scales must be 15 finite values >= 1e-9")
    scale = scale.astype(float, copy=False)
    if not math.isclose(goal[1], height / n, rel_tol=0, abs_tol=1e-14):
        raise ValueError("target height and chain fraction disagree")
    labels, allowed, protected = _layers(n, height, rng)
    uniforms = rng.random((n, n))
    mutable = np.flatnonzero(allowed & ~protected)
    pairs = n * (n - 1) / 2
    layer_sizes = np.bincount(labels, minlength=height)
    minimum_r = height * (height - 1) / (2 * pairs)
    maximum_relations = (n * (n - 1) - int(np.sum(layer_sizes * (layer_sizes - 1)))) // 2
    maximum_r = maximum_relations / pairs
    bounds_infeasible = bool(goal[0] < minimum_r or goal[0] > maximum_r)

    def evaluate(adjacency):
        order = transitive_closure(adjacency, max_count=max_count)
        row = extract_features(order, max_count=max_count)
        vector = np.asarray(feature_vector(row), dtype=float)
        if (row["longest_chain"] != height or vector.shape != (15,)
                or not np.all(np.isfinite(vector))):
            raise RuntimeError("search violated its fixed-height/defined-feature invariant")
        z = (vector - goal) / scale
        return order, vector, float(np.sqrt(np.mean(z * z)))

    phase_one = min(12, steps // 2)
    low, high = 0.0, 1.0
    fraction_error = math.inf
    checkpoint = None
    selected_q = None
    for evaluation in range(phase_one):
        q = float(evaluation) if evaluation < 2 else (low + high) / 2
        adjacency = (allowed & (uniforms < q)) | protected
        order, vector, objective = evaluate(adjacency)
        error = abs(float(vector[0] - goal[0]))
        if error < fraction_error:
            fraction_error = error
            checkpoint = (adjacency.copy(), order, vector, objective)
            selected_q = q
        if evaluation >= 2:
            if vector[0] < goal[0]:
                low = q
            else:
                high = q
    assert checkpoint is not None
    current_adjacency, first_order, first_vector, initial_objective = checkpoint
    current_order = first_order
    current_objective = initial_objective
    best_order = first_order
    best_vector = first_vector
    best_objective = initial_objective
    accepted = improved = unchanged = 0
    phase_two = steps - phase_one
    for proposal, temperature in enumerate(np.geomspace(0.1, 0.01, phase_two)):
        proposed = current_adjacency.copy()
        changed_count = min((1, 2, 4, 8)[proposal % 4], len(mutable))
        if changed_count:
            locations = rng.choice(mutable, size=changed_count, replace=False)
            proposed.flat[locations] = ~proposed.flat[locations]
        order, vector, objective = evaluate(proposed)
        unchanged += int(np.array_equal(order, current_order))
        if objective <= current_objective or rng.random() < math.exp(
                (current_objective - objective) / float(temperature)):
            accepted += 1
            current_adjacency = proposed
            current_order = order
            current_objective = objective
        if objective < best_objective:
            improved += 1
            best_order, best_vector, best_objective = order, vector, objective

    permutation = rng.permutation(n)
    first_order = first_order[np.ix_(permutation, permutation)]
    best_order = best_order[np.ix_(permutation, permutation)]
    # These integrity checks are not search proposals and cannot change a result.
    for order, expected in ((first_order, first_vector), (best_order, best_vector)):
        actual = feature_vector(extract_features(order, max_count=max_count))
        if not np.array_equal(actual, expected):
            raise RuntimeError("relabeling changed an order-only search feature")
    z_first = (first_vector - goal) / scale
    z_best = (best_vector - goal) / scale
    first_match = fraction_error <= 0.02
    full_match = bool(np.max(np.abs(z_best)) <= 1)
    metadata = {
        "count": n, "target_height": height, "evaluations": steps,
        "phase_one_evaluations": phase_one, "phase_two_evaluations": phase_two,
        "post_search_integrity_evaluations": 2,
        "mutable_edges": int(len(mutable)), "no_mutable_edges": not bool(len(mutable)),
        "no_change_proposals": unchanged, "accepted_proposals": accepted,
        "best_objective_improvements": improved, "selected_probability": selected_q,
        "minimum_attainable_r": minimum_r, "maximum_attainable_r": maximum_r,
        "target_r_outside_attainable_bounds": bounds_infeasible,
        "fraction_error": fraction_error, "height_fraction_match": first_match,
        "multifeature_match": full_match, "initial_objective": initial_objective,
        "best_objective": best_objective,
        "initial_max_abs_z": float(np.max(np.abs(z_first))),
        "best_max_abs_z": float(np.max(np.abs(z_best))),
        "target_vector": goal.tolist(), "scale_vector": scale.tolist(),
        "height_fraction_vector": first_vector.tolist(),
        "multifeature_vector": best_vector.tolist(),
        "status": "matched" if full_match else "failed_match_within_budget",
    }
    return SearchResult(first_order, best_order, metadata)
