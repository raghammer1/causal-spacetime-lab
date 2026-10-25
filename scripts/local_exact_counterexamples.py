"""Post-registration analytic extension: a full measured-vector collision.

This exact finite counterexample does not modify primary sampling, observables,
calibration, thresholds or decisions. It concerns general height-two orders,
not uniqueness within a geometric or continuum-limit class.
"""
from __future__ import annotations

import argparse
from collections import Counter
import itertools
import json
import math
from pathlib import Path

import numpy as np

from causal_lab.local_structure import local_observables, motif_catalog, motif_counts


def collision_pair():
    """C12 versus C6 disjoint-union C6, with six minima and six maxima."""
    connected = np.zeros((12, 12), dtype=bool)
    disconnected = connected.copy()
    for i in range(6):
        connected[i, 6 + i] = True
        connected[i, 6 + (i + 1) % 6] = True
        block = 3 * (i // 3)
        disconnected[i, 6 + i] = True
        disconnected[i, 6 + block + (i + 1 - block) % 3] = True
    return connected, disconnected


def independent_component_sizes(order):
    remaining = set(range(len(order)))
    sizes = []
    while remaining:
        pending = [remaining.pop()]
        size = 0
        while pending:
            vertex = pending.pop()
            size += 1
            adjacent = {j for j in remaining if order[vertex, j] or order[j, vertex]}
            remaining.difference_update(adjacent)
            pending.extend(adjacent)
        sizes.append(size)
    return sorted(sizes)


def independent_four_motifs(order):
    """Brute force every four-set and every relabeling; no package classifier."""
    pairs = tuple((i, j) for i in range(4) for j in range(4) if i != j)
    permutations = tuple(itertools.permutations(range(4)))
    result = Counter()
    n22 = 0
    for vertices in itertools.combinations(range(len(order)), 4):
        matrix = order[np.ix_(vertices, vertices)]
        code = min(sum(int(matrix[p[i], p[j]]) << bit for bit, (i, j) in enumerate(pairs))
                   for p in permutations)
        result[code] += 1
        n22 += bool(matrix.sum() == 2 and np.all(matrix.sum(axis=0) + matrix.sum(axis=1) == 1))
    return result, n22


def degree_profile(order):
    counts = Counter(zip(order.sum(axis=0).tolist(), order.sum(axis=1).tolist()))
    return [[int(p), int(f), count] for (p, f), count in sorted(counts.items())]


def verify():
    first, second = collision_pair()
    records = [local_observables(order) for order in (first, second)]
    profiles = [degree_profile(order) for order in (first, second)]
    brute = [independent_four_motifs(order) for order in (first, second)]
    motifs = [motif_counts(order) for order in (first, second)]
    sizes = [independent_component_sizes(order) for order in (first, second)]
    assert records[0] == records[1]
    assert profiles[0] == profiles[1] == [[0, 2, 6], [2, 0, 6]]
    assert brute[0] == brute[1]
    assert motifs[0] == motifs[1]
    assert sizes == [[12], [6, 6]]
    assert brute[0][1] == records[0]["n22"] == math.comb(6, 2) * 4 - 3 * 6 == 42
    assert sum(brute[0][0].values()) == math.comb(12, 4) == 495
    catalog = motif_catalog()
    independent_counts = [brute[0][0][entry["canonical_code"]] for entry in catalog]
    assert independent_counts == motifs[0]["counts"]
    assert records[0]["relations"] == 12 and records[0]["longest_chain"] == 2
    assert records[0]["interval_component_profile"] == [[0, 0, 12]]
    for name in ("chains3", "chains4", "diamonds4", "overlap_sum", "overlap_choose2_sum"):
        assert records[0][name] == 0
    return {
        "status": "exact_counterexample_verified",
        "registration_status": "post-registration analytic extension; no primary data or analysis changed",
        "scope": "general finite height-two orders; no claim about uniqueness within geometric ensembles",
        "event_count": 12, "relations": 12, "height": 2,
        "global_comparability_component_sizes": sizes,
        "nonisomorphism_witness": "different numbers of connected comparability components, invariant also under duality",
        "local_observables_equal": True, "joint_degree_profiles_equal": True,
        "exact_global_four_motif_counts_equal": True,
        "enumerated_four_subsets_per_order": 495,
        "independent_bruteforce_n22": [item[1] for item in brute],
        "global_four_motif_counts": independent_counts,
        "canonical_four_motif_counts": [[entry["canonical_code"], independent_counts[entry["id"]]] for entry in catalog],
        "shared_local_observables": records[0], "shared_joint_degree_profile": profiles[0],
        "orders": [{"name": name, "matrix": order.astype(int).tolist()}
                   for name, order in zip(("C12_bipartite", "two_C6_bipartite"), (first, second))],
        "sampled_global_motif_scope": "Uniform independent four-subset draws have the same multinomial law; identical seeds need not produce identical draws for larger labeled realizations.",
        "counting_argument": {
            "family": "fixed N, nonempty orders whose relations run from a fixed balanced lower layer to an upper layer",
            "unlabeled_order_lower_bound": "(2^floor(N^2/4)-1)/N! = exp(Omega(N^2))",
            "degree_profile_support_bound": "2N-1 cells: (0,0), (p,0), (0,f), with 1<=p,f<=N-1",
            "observable_range_upper_bound": "(floor(N^2/4)+1)*(N+1)^(2N-1)*(binom(N,4)+1)^16 = exp(O(N log N))",
            "reason": "Every open interval is empty. Its entire size/component profile is [0,0,R]; chain and overlap moments and all selected conditional counts vanish. The 16 exact global four-motif counts and degree profile include the remaining measured deterministic information.",
            "conclusion": "For sufficiently large N, nonisomorphic height-two orders sharing the full measured deterministic vector are unavoidable. The explicit N=12 pair is independently verified rather than inferred from this asymptotic bound.",
            "adding_global_components": "Adding a single component-count feature cannot remove the counting obstruction. Even restricting to connected bipartite graphs leaves at least 2^((a-1)(b-1))/N! classes by forcing a spanning double-star; a+b=N.",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify()
    text = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "event_count", "relations", "height",
        "global_comparability_component_sizes", "global_four_motif_counts", "independent_bruteforce_n22")},
        sort_keys=True))


if __name__ == "__main__":
    main()
