"""Boundary controls, exact summary degeneracies and finite invariant-fiber search.

The constructions are mathematical controls, not certificates of geometric
embeddability. In particular, an accepted switch need not leave an isomorphism
class, and the switch process is not asserted to sample its fiber uniformly.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .adversarial_generators import _generator, _integer
from .dimension import MinkowskiInterval, minkowski_order, sprinkle_minkowski, validate_order
from .order_observables import (
    _bit_rows, _bounded_matrix, _count, order_observables, random_dag_order,
    transitive_closure,
)


def sprinkle_central_slab(count: int, rng: np.random.Generator, dimension: int,
                         *, max_count: int = 512) -> MinkowskiInterval:
    """Uniform fixed-count sample of the unit diamond intersected with .25<=t<=.75.

    Rejection from the existing uniform diamond generator changes only the
    outer region. The first N retained iid points have the conditional uniform
    law; no coordinate, metric or causal-relation transformation is applied.
    """
    n = _count(count, max_count)
    rng = _generator(rng)
    # This also validates dimension, including the empty-sample case.
    empty = sprinkle_minkowski(dimension, 1.0, rng, count=0)
    times, positions = [], []
    remaining = n
    while remaining:
        candidate = sprinkle_minkowski(dimension, 1.0, rng, count=max(32, 2 * remaining))
        keep = np.flatnonzero((candidate.t >= .25) & (candidate.t <= .75))[:remaining]
        times.append(candidate.t[keep])
        positions.append(candidate.x[keep])
        remaining -= len(keep)
    if not n:
        return empty
    return MinkowskiInterval(np.concatenate(times), np.concatenate(positions), dimension, 1.0)


def central_slab_order(count: int, rng: np.random.Generator, dimension: int,
                       *, max_count: int = 512) -> np.ndarray:
    """Return the strict flat order of a uniform central-slab sample."""
    return minkowski_order(sprinkle_central_slab(count, rng, dimension, max_count=max_count))


def bipartite_module(*, connected: bool, blowup: int = 1,
                     max_count: int = 512) -> np.ndarray:
    """C8 or two K2,2 components, with every vertex replaced by `blowup` twins.

    Both modules have 8s events, height 2, 8s^2 relations and the same joint
    predecessor/successor degree multiset. Their induced 2+2 counts are 12s^4
    and 16s^4. The twins are incomparable and have identical outside relations.
    """
    if not isinstance(connected, (bool, np.bool_)):
        raise ValueError("connected must be boolean")
    s = _integer(blowup, "blowup", 1)
    _count(8 * s, max_count)
    module = np.zeros((8, 8), dtype=bool)
    for i in range(4):
        if connected:
            module[i, 4 + i] = module[i, 4 + (i + 1) % 4] = True
        else:
            for j in range(4):
                module[i, 4 + j] = i // 2 == j // 2
    return np.kron(module, np.ones((s, s), dtype=bool))


def lexicographic_order(base, module, *, max_count: int = 512) -> np.ndarray:
    """Replace each base event by the same module, preserving complete cross orders."""
    base = validate_order(_bounded_matrix(base, max_count))
    module = validate_order(_bounded_matrix(module, max_count))
    q, m = len(base), len(module)
    _count(q * m, max_count)
    return (np.kron(base, np.ones((m, m), dtype=bool))
            | np.kron(np.eye(q, dtype=bool), module))


def old_signature(order, *, max_count: int = 512) -> tuple:
    """Exact Experiment 1--3 invariant (N,R,H,full interval histogram)."""
    row = order_observables(order, max_count=max_count)
    return (row["count"], row["relations"], row["longest_chain"],
            tuple(row["interval_histogram"]))


def _signature_dict(signature: tuple) -> dict:
    return dict(count=signature[0], relations=signature[1], longest_chain=signature[2],
                interval_histogram=list(signature[3]))


@dataclass(frozen=True)
class ExactPairResult:
    first_order: np.ndarray
    second_order: np.ndarray
    metadata: dict


def lexicographic_matched_pair(count: int, rng: np.random.Generator, *,
                              scaling: str = "fixed", max_count: int = 512) -> ExactPairResult:
    """Generate an exact old-summary collision in a registered scaling regime.

    ``fixed`` uses q=N/8,s=1; ``inflated`` uses q=4,s=N/32. A common base is a
    forward random DAG with p=min(1,2/q), followed by closure and relabeling.
    The same final event permutation is applied to both members. Their old
    signature is checked exactly; no geometric matching or fitting is claimed.
    """
    n = _count(count, max_count)
    rng = _generator(rng)
    if scaling == "fixed" and n >= 8 and n % 8 == 0:
        q, s = n // 8, 1
    elif scaling == "inflated" and n >= 32 and n % 32 == 0:
        q, s = 4, n // 32
    else:
        raise ValueError("scaling must be fixed with positive N divisible by 8, or inflated with N divisible by 32")
    probability = min(1.0, 2.0 / q)
    base = random_dag_order(q, rng, probability, max_count=max_count)
    first = lexicographic_order(base, bipartite_module(connected=True, blowup=s,
                                max_count=max_count), max_count=max_count)
    second = lexicographic_order(base, bipartite_module(connected=False, blowup=s,
                                 max_count=max_count), max_count=max_count)
    permutation = rng.permutation(n)
    first, second = first[np.ix_(permutation, permutation)], second[np.ix_(permutation, permutation)]
    signature = old_signature(first, max_count=max_count)
    if signature != old_signature(second, max_count=max_count):
        raise RuntimeError("lexicographic pair violated its exact old-signature identity")
    metadata = dict(scaling=scaling, count=n, base_count=q, blowup=s,
                    edge_probability=probability, base_order=base.astype(int).tolist(),
                    expected_n22_difference=4 * q * s ** 4,
                    old_signature=_signature_dict(signature))
    return ExactPairResult(first, second, metadata)


def _covers_unchecked(matrix: np.ndarray) -> np.ndarray:
    successors, predecessors = _bit_rows(matrix), _bit_rows(matrix.T)
    covers = np.zeros_like(matrix)
    for i in range(len(matrix)):
        for j in np.flatnonzero(matrix[i]):
            if not successors[i] & predecessors[int(j)]:
                covers[i, j] = True
    return covers


def cover_relations(order, *, max_count: int = 512) -> np.ndarray:
    """Transitive reduction of a validated finite strict partial order."""
    return _covers_unchecked(validate_order(_bounded_matrix(order, max_count)))


@dataclass(frozen=True)
class FiberSearchResult:
    initial_order: np.ndarray
    midpoint_order: np.ndarray
    final_order: np.ndarray
    metadata: dict


def microcanonical_switch_search(order, rng: np.random.Generator, *,
                                steps: int | None = None,
                                max_count: int = 512) -> FiberSearchResult:
    """Attempt cover-edge head switches while preserving the full old signature.

    Draw two distinct current cover edges once per attempt. Reject missing
    candidates, shared endpoints, existing replacement edges, cycles, unchanged
    closures and old-statistic changes without resampling. Accepted proposals
    depend on no local feature, coordinate or generating dimension. Default
    steps=N^2//64; small smoke orders can specify any positive explicit budget.
    Every attempt has exactly one recorded outcome. This is a finite search,
    not an assertion of ergodicity or a uniform microcanonical sampler.
    """
    current = validate_order(_bounded_matrix(order, max_count)).copy()
    rng = _generator(rng)
    n = len(current)
    if steps is None:
        steps = n * n // 64
        if not steps:
            raise ValueError("small searches require an explicit positive steps budget")
    steps = _integer(steps, "steps", 1)
    initial = current.copy()
    signature = old_signature(current, max_count=max_count)
    covers = _covers_unchecked(current)
    edges = np.argwhere(covers)
    outcomes = dict(no_cover_pair=0, shared_endpoint=0, existing_replacement=0,
                    cycle=0, unchanged_order=0, old_statistics_changed=0, accepted=0)
    mismatch = dict(relations=0, height=0, interval_histogram=0)
    midpoint = initial.copy()
    half = steps // 2

    def snapshot(attempt):
        return dict(attempt=attempt, outcomes=outcomes.copy(),
                    matrix_difference=int(np.count_nonzero(current != initial)))

    checkpoints = [snapshot(0)]
    if half == 0:
        checkpoints.append(snapshot(0))
    for attempt in range(1, steps + 1):
        if len(edges) < 2:
            outcome = "no_cover_pair"
        else:
            selected = rng.choice(len(edges), size=2, replace=False)
            (a, b), (c, d) = edges[selected]
            if len({int(a), int(b), int(c), int(d)}) != 4:
                outcome = "shared_endpoint"
            elif covers[a, d] or covers[c, b]:
                outcome = "existing_replacement"
            else:
                proposed = covers.copy()
                proposed[a, b] = proposed[c, d] = False
                proposed[a, d] = proposed[c, b] = True
                try:
                    candidate = transitive_closure(proposed, max_count=max_count)
                except ValueError:
                    outcome = "cycle"
                else:
                    if np.array_equal(candidate, current):
                        outcome = "unchanged_order"
                    elif int(candidate.sum()) != signature[1]:
                        outcome = "old_statistics_changed"
                        mismatch["relations"] += 1
                    else:
                        candidate_signature = old_signature(candidate, max_count=max_count)
                        if candidate_signature != signature:
                            outcome = "old_statistics_changed"
                            mismatch["height"] += int(candidate_signature[2] != signature[2])
                            mismatch["interval_histogram"] += int(candidate_signature[3] != signature[3])
                        else:
                            outcome = "accepted"
                            current = candidate
                            covers = _covers_unchecked(current)
                            edges = np.argwhere(covers)
        outcomes[outcome] += 1
        if attempt == half:
            midpoint = current.copy()
            checkpoints.append(snapshot(attempt))
    checkpoints.append(snapshot(steps))
    final = current.copy()
    for checkpoint in (initial, midpoint, final):
        if old_signature(checkpoint, max_count=max_count) != signature:
            raise RuntimeError("fiber-search checkpoint changed its old signature")
    if sum(outcomes.values()) != steps:
        raise RuntimeError("fiber-search attempt accounting failed")
    metadata = dict(count=n, steps=steps, midpoint_step=half,
                    attempts_per_n_squared=steps / (n * n) if n else None,
                    outcomes=outcomes, mismatch_reasons=mismatch,
                    checkpoints=checkpoints, old_signature=_signature_dict(signature),
                    old_signature_preserved=True,
                    final_matrix_changed=bool(np.any(final != initial)),
                    final_matrix_difference=int(np.count_nonzero(final != initial)),
                    any_accepted_move=bool(outcomes["accepted"]),
                    status="accepted_moves" if outcomes["accepted"] else "no_accepted_move")
    return FiberSearchResult(initial, midpoint, final, metadata)


def standard_example_s3() -> np.ndarray:
    """Six-event S3: a_i<b_j exactly when i!=j, a two-ranking obstruction."""
    order = np.zeros((6, 6), dtype=bool)
    order[:3, 3:] = ~np.eye(3, dtype=bool)
    return order


def standard_example_s3_embedding() -> MinkowskiInterval:
    """Explicit 2+1D flat embedding of S3 inside a duration-four diamond.

    Unit equilateral spatial vertices v_i give lower points (1.1,v_i) and
    upper points (2.6,-v_i). Cross distances are one off the diagonal and two
    on it; the time gap is 1.5. This obstructs d2, not flat geometry generally.
    """
    triangle = np.array([[1., 0.], [-.5, np.sqrt(3.) / 2], [-.5, -np.sqrt(3.) / 2]])
    return MinkowskiInterval(np.array([1.1] * 3 + [2.6] * 3),
                             np.concatenate((triangle, -triangle)), 3, 4.)
