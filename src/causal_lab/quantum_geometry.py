"""Coordinate-free MI diagnostics and a deliberately separate input evaluator.

The returned MDS coordinates represent correlations, not physical locations.
Shortest-path closure imposes a (pseudo)metric and is only a comparator. All
entropies/MI supplied here are in bits; dissimilarities use natural logarithms.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np


SCORE_ATOL = 1e-10
SCORE_RTOL = 1e-8
EPSILONS = (1e-12, 1e-9, 1e-6)
PRIMARY_EPSILON = 1e-9


def _square(matrix: np.ndarray, *, nonnegative: bool = False) -> np.ndarray:
    """Copy a finite real symmetric matrix, discarding its unused diagonal."""
    raw = np.asarray(matrix)
    if np.iscomplexobj(raw):
        raise ValueError("scores must be real")
    result = np.array(raw, dtype=float, copy=True)
    if result.ndim != 2 or result.shape[0] != result.shape[1] or len(result) < 2:
        raise ValueError("scores must be a square matrix with at least two vertices")
    if not np.all(np.isfinite(result)):
        raise ValueError("scores must be finite")
    if not np.allclose(result, result.T, rtol=0, atol=SCORE_ATOL):
        raise ValueError("scores must be symmetric")
    result = (result + result.T) / 2
    np.fill_diagonal(result, 0)
    if nonnegative:
        if np.any(result < -SCORE_ATOL):
            raise ValueError("scores must be nonnegative")
        result = np.maximum(result, 0)
    return result


def _mi_matrix(mi: np.ndarray) -> np.ndarray:
    matrix = _square(mi, nonnegative=True)
    if np.max(matrix) > 2 + SCORE_ATOL:
        raise ValueError("two-qubit mutual information cannot exceed two bits")
    return np.minimum(matrix, 2)


def _close(a: np.ndarray | float, b: np.ndarray | float) -> np.ndarray:
    # Symmetric tolerance: exchanging arguments cannot change a tie decision.
    return np.abs(np.asarray(a) - np.asarray(b)) <= (
        SCORE_ATOL + SCORE_RTOL * np.maximum(np.abs(a), np.abs(b))
    )


def _fractional_top(scores: np.ndarray, count: int) -> tuple[np.ndarray, bool]:
    values = np.asarray(scores, dtype=float)
    if values.ndim != 1 or not 0 <= count <= len(values):
        raise ValueError("invalid number of selected scores")
    weights = np.zeros_like(values)
    if count == 0:
        return weights, False
    if count == len(values):
        return np.ones_like(values), False
    boundary = np.sort(values)[-count]
    tied = _close(values, boundary)
    above = (values > boundary) & ~tied
    remaining = count - int(above.sum())
    weights[above] = 1
    weights[tied] = remaining / int(tied.sum())
    return weights, bool(0 < remaining < int(tied.sum()))


def fractional_neighbors(scores: np.ndarray, k: int) -> np.ndarray:
    """Directed top-k memberships; boundary ties share the available mass.

    Each row sums to k, including constant rows. Constant rows describe complete
    ambiguity, not observed links. No vertex index resolves a tie.
    """
    matrix = _square(scores, nonnegative=True)
    n = len(matrix)
    if not isinstance(k, (int, np.integer)) or not 1 <= k < n:
        raise ValueError("k must be an integer between one and n-1")
    weights = np.zeros_like(matrix)
    for i in range(n):
        mask = np.arange(n) != i
        weights[i, mask], _ = _fractional_top(matrix[i, mask], k)
    return weights


def neighborhood_overlap(weights_a: np.ndarray, weights_b: np.ndarray) -> float:
    """Intersection mass divided by common total mass (one for identical ties)."""
    a, b = np.asarray(weights_a, dtype=float), np.asarray(weights_b, dtype=float)
    if a.shape != b.shape or a.ndim != 2 or a.shape[0] != a.shape[1]:
        raise ValueError("neighborhood matrices must have equal square shapes")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("neighborhood weights must be finite")
    if np.any(a < 0) or np.any(b < 0) or np.any(a > 1) or np.any(b > 1):
        raise ValueError("neighborhood weights must lie in [0,1]")
    if not np.allclose(a.sum(axis=1), b.sum(axis=1), rtol=0, atol=1e-10):
        raise ValueError("neighborhoods must have equal row masses")
    denominator = float(a.sum())
    return float(np.minimum(a, b).sum() / denominator) if denominator else float("nan")


def _components(adjacency: np.ndarray) -> int:
    unseen = set(range(len(adjacency)))
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            neighbors = set(np.flatnonzero(adjacency[stack.pop()])) & unseen
            unseen.difference_update(neighbors)
            stack.extend(neighbors)
    return count


def _distance_metrics(distance: np.ndarray) -> dict[str, float]:
    n = len(distance)
    upper = distance[np.triu_indices(n, 1)]
    violations = 0
    comparisons = 0
    max_excess = 0.0
    for i, j, k in combinations(range(n), 3):
        sides = (distance[i, j], distance[i, k], distance[j, k])
        for index in range(3):
            excess = float(sides[index] - sides[(index + 1) % 3] - sides[(index + 2) % 3])
            comparisons += 1
            tolerance = SCORE_ATOL + SCORE_RTOL * max(sides)
            violations += int(excess > tolerance)
            max_excess = max(max_excess, excess)
    return {
        "distance_symmetry_error": float(np.max(np.abs(distance - distance.T))),
        "distance_min": float(upper.min()),
        "distance_max": float(upper.max()),
        "zero_distance_pairs": float(np.count_nonzero(upper <= SCORE_ATOL)),
        "triangle_comparisons": float(comparisons),
        "triangle_violation_fraction": violations / comparisons if comparisons else 0.0,
        "triangle_max_excess": max_excess,
        "triangle_max_relative_excess": max_excess / float(upper.max()) if upper.max() else 0.0,
    }


def _mds(distance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    squared = distance**2
    gram = -0.5 * (
        squared - squared.mean(axis=0)[None, :] - squared.mean(axis=1)[:, None] + squared.mean()
    )
    gram = (gram + gram.T) / 2
    eigenvalues, vectors = np.linalg.eigh(gram)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues, vectors = eigenvalues[order], vectors[:, order]
    tolerance = 1e-12 * max(1.0, float(np.max(np.abs(eigenvalues))))
    positive = eigenvalues > tolerance
    return eigenvalues, vectors[:, positive] * np.sqrt(eigenvalues[positive])


def _spectrum_metrics(eigenvalues: np.ndarray) -> dict[str, float]:
    tolerance = 1e-12 * max(1.0, float(np.max(np.abs(eigenvalues))))
    positive = eigenvalues[eigenvalues > tolerance]
    negative = eigenvalues[eigenvalues < -tolerance]
    mass = float(np.abs(eigenvalues[np.abs(eigenvalues) > tolerance]).sum())
    # Repeated positive eigenvalues make individual embedding axes noncanonical.
    repeated = sum(bool(_close(a, b)) for a, b in zip(positive[:-1], positive[1:]))
    return {
        "positive_rank": float(len(positive)),
        "negative_rank": float(len(negative)),
        "negative_eigenvalue_mass": float(-negative.sum() / mass) if mass else 0.0,
        "positive_participation_rank": float(positive.sum()**2 / (positive @ positive)) if len(positive) else 0.0,
        "repeated_positive_eigenvalue_pairs": float(repeated),
    }


def infer_geometry(mi: np.ndarray, epsilon: float = PRIMARY_EPSILON) -> dict[str, Any]:
    """Infer only from MI; no interaction, coordinate, family or target dimension.

    Classical MDS returns every positive mode. Negative eigenvalues are retained
    in the spectrum; dropping them is an approximation whose stress is evaluated
    separately. Distinct nodes with MI=2 collide in the raw dissimilarity.
    """
    matrix = _mi_matrix(mi)
    if not np.isfinite(epsilon) or not 0 < epsilon < 2:
        raise ValueError("epsilon must lie strictly between zero and two")
    n = len(matrix)
    upper_indices = np.triu_indices(n, 1)
    upper = matrix[upper_indices]
    distance = -np.log(np.maximum(matrix, epsilon) / 2)
    np.fill_diagonal(distance, 0)
    closure = distance.copy()
    for k in range(n):
        closure = np.minimum(closure, closure[:, k, None] + closure[k, None, :])
    eigenvalues, coordinates = _mds(distance)
    closure_eigenvalues, closure_coordinates = _mds(closure)
    metrics = _distance_metrics(distance)
    metrics.update(_spectrum_metrics(eigenvalues))
    metrics.update({f"closure_{key}": value for key, value in _distance_metrics(closure).items()})
    metrics.update({f"closure_{key}": value for key, value in _spectrum_metrics(closure_eigenvalues).items()})
    metrics.update({
        "mi_mean": float(upper.mean()),
        "mi_contrast": float(np.ptp(upper)),
        "mi_std": float(upper.std()),
        "regularized_pair_fraction": float(np.mean(upper < epsilon)),
        "zero_information_pairs": float(np.count_nonzero(upper == 0)),
        "closure_changed_pair_fraction": float(np.mean(~_close(distance[upper_indices], closure[upper_indices]))),
    })
    neighbors = {}
    for k in (1, 2, 3):
        if k >= n:
            continue
        neighbors[f"k{k}"] = fractional_neighbors(matrix, k)
        ambiguous = []
        for i in range(n):
            _, tie = _fractional_top(matrix[i, np.arange(n) != i], k)
            ambiguous.append(tie)
        metrics[f"neighbor_tie_fraction_k{k}"] = float(np.mean(ambiguous))
    densities = []
    components = []
    maximum = float(upper.max())
    for threshold in (0.25, 0.5, 0.75):
        adjacency = (matrix >= threshold * maximum) if maximum else np.zeros_like(matrix, dtype=bool)
        np.fill_diagonal(adjacency, False)
        tag = f"{threshold:g}"
        density = float(adjacency[upper_indices].mean())
        component_count = _components(adjacency)
        densities.append(density)
        components.append(component_count)
        metrics[f"threshold_{tag}_edge_density"] = density
        metrics[f"threshold_{tag}_components"] = float(component_count)
    metrics["threshold_edge_density_range"] = float(np.ptp(densities))
    metrics["threshold_component_range"] = float(np.ptp(components))
    return {
        "epsilon": float(epsilon), "mi": matrix, "distance": distance,
        "closure_distance": closure, "eigenvalues": eigenvalues,
        "coordinates": coordinates, "closure_eigenvalues": closure_eigenvalues,
        "closure_coordinates": closure_coordinates, "neighbors": neighbors,
        "metrics": metrics,
    }


def _stress(distance: np.ndarray, coordinates: np.ndarray) -> float:
    upper = np.triu_indices(len(distance), 1)
    reconstructed = np.sqrt(np.maximum(0, ((coordinates[:, None] - coordinates[None, :])**2).sum(axis=2)))
    denominator = float(np.sum(distance[upper]**2))
    numerator = float(np.sum((distance[upper] - reconstructed[upper])**2))
    return float(np.sqrt(numerator / denominator)) if denominator else 0.0


def geometry_metrics(result: dict[str, Any]) -> dict[str, float]:
    """Evaluator projection diagnostics; all registered dimensions are reported."""
    metrics = dict(result["metrics"])
    for prefix in ("", "closure_"):
        distance, coordinates = result[f"{prefix}distance"], result[f"{prefix}coordinates"]
        eigenvalues = result[f"{prefix}eigenvalues"]
        for dimension in (1, 2, 3):
            metrics[f"{prefix}stress_d{dimension}"] = _stress(distance, coordinates[:, :dimension])
            metrics[f"{prefix}stress_d{dimension}_ambiguous"] = float(
                dimension < coordinates.shape[1]
                and bool(_close(eigenvalues[dimension - 1], eigenvalues[dimension]))
            )
        metrics[f"{prefix}stress_full"] = _stress(distance, coordinates)
    return metrics


def epsilon_agreement(mi: np.ndarray) -> dict[str, float]:
    """Minimum paired overlap of neighbors from epsilon-floored MI scores."""
    matrix = _mi_matrix(mi)
    metrics = {}
    for k in (1, 2, 3):
        if k >= len(matrix):
            continue
        neighborhoods = [fractional_neighbors(np.maximum(matrix, epsilon), k) for epsilon in EPSILONS]
        overlaps = [neighborhood_overlap(a, b) for a, b in combinations(neighborhoods, 2)]
        metrics[f"epsilon_agreement_k{k}"] = min(overlaps)
    return metrics


def shuffle_weights(mi: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Shuffle unordered edge weights; not necessarily realizable quantum MI."""
    matrix = _mi_matrix(mi)
    upper = np.triu_indices(len(matrix), 1)
    values = rng.permutation(matrix[upper])
    result = np.zeros_like(matrix)
    result[upper] = values
    result[(upper[1], upper[0])] = values
    return result


def _ranks(values: np.ndarray) -> np.ndarray:
    """Average ranks with anchored numerical tie groups, independent of labels."""
    order = np.argsort(values, kind="stable")
    ranks = np.zeros(len(values), dtype=float)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and bool(_close(values[order[start]], values[order[end]])):
            end += 1
        ranks[order[start:end]] = (start + end - 1) / 2
        start = end
    return ranks


def rank_correlation(first: np.ndarray, second: np.ndarray) -> float:
    """Spearman correlation with numerical ties; constants remain undefined."""
    a, b = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    if a.shape != b.shape or a.ndim != 1 or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("rank correlation needs equal finite vectors")
    if not len(a):
        return float("nan")
    ra, rb = _ranks(a), _ranks(b)
    ra, rb = ra - ra.mean(), rb - rb.mean()
    denominator = float(np.linalg.norm(ra) * np.linalg.norm(rb))
    return float(np.clip((ra @ rb) / denominator, -1, 1)) if denominator else float("nan")


def edge_auc(scores: np.ndarray, adjacency: np.ndarray) -> float:
    """Tie-aware pair ranking AUC, undefined without edges or without nonedges."""
    matrix = _square(scores, nonnegative=True)
    labels = _square(adjacency)
    if labels.shape != matrix.shape or not np.all((labels == 0) | (labels == 1)):
        raise ValueError("adjacency must be a matching binary symmetric matrix")
    upper = np.triu_indices(len(matrix), 1)
    positive = matrix[upper][labels[upper].astype(bool)]
    negative = matrix[upper][~labels[upper].astype(bool)]
    if not len(positive) or not len(negative):
        return float("nan")
    ties = _close(positive[:, None], negative[None, :])
    wins = (positive[:, None] > negative[None, :]) & ~ties
    return float(np.mean(wins + 0.5 * ties))


def evaluate_inputs(
    mi: np.ndarray,
    couplings: np.ndarray | None = None,
    *,
    true_adjacency: np.ndarray | None = None,
    connected_zz: np.ndarray | None = None,
    negativity: np.ndarray | None = None,
) -> dict[str, float]:
    """Independent evaluator receives withheld inputs; inference never does.

    Coupling disagreement is not independence from the complete Hamiltonian.
    Coupling-normalized MDS is a comparator with imposed normalization [0,2].
    """
    matrix = _mi_matrix(mi)
    n = len(matrix)
    upper = np.triu_indices(n, 1)
    metrics = {}
    if true_adjacency is not None:
        adjacency = _square(true_adjacency)
        if adjacency.shape != matrix.shape or not np.all((adjacency == 0) | (adjacency == 1)):
            raise ValueError("adjacency must be a matching binary symmetric matrix")
        metrics["edge_auc"] = edge_auc(matrix, adjacency)
        weights, ambiguous = _fractional_top(matrix[upper], n - 1)
        total = float(adjacency[upper].sum())
        metrics["edge_recall_top_n_minus_1"] = float(weights @ adjacency[upper] / total) if total else float("nan")
        metrics["edge_recall_boundary_ambiguous"] = float(ambiguous)
    for name, supplied in (("coupling", couplings), ("zz", connected_zz), ("negativity", negativity)):
        if supplied is None:
            continue
        scores = np.abs(_square(supplied, nonnegative=name == "negativity"))
        if scores.shape != matrix.shape:
            raise ValueError(f"{name} matrix must match MI shape")
        metrics[f"spearman_mi_{name}"] = rank_correlation(matrix[upper], scores[upper])
        for k in (1, 2, 3):
            if k < n:
                metrics[f"neighbor_overlap_{name}_k{k}"] = neighborhood_overlap(
                    fractional_neighbors(matrix, k), fractional_neighbors(scores, k)
                )
        if name == "coupling":
            maximum = float(scores.max())
            normalized = 2 * scores / maximum if maximum else scores
            metrics.update({f"coupling_{key}": value for key, value in geometry_metrics(infer_geometry(normalized)).items()})
    return metrics
