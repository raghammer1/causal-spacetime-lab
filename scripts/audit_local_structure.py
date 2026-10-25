"""Independent arithmetic audit of an Experiment 4 artifact directory.

Usage: python scripts/audit_local_structure.py PATH [--allow-explicit-search-budgets]

The audit reconstructs motif classes and exact rank references independently of
the extraction/statistics modules. It does not rerun stochastic parent generation
or bootstrap confidence intervals. Missing required artifacts and inconsistent
records fail explicitly; smoke budgets require the named command-line exception.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np


def require(condition, context):
    if not condition:
        raise ValueError(context)


def equal(actual, expected, context):
    require(actual == expected, f"{context}: got {actual!r}; expected {expected!r}")


def close(actual, expected, context):
    if actual is None or expected is None:
        equal(actual, expected, context)
    else:
        require(math.isclose(actual, expected, rel_tol=2e-12, abs_tol=2e-14), context)


def integer(value, context, minimum=0):
    require(isinstance(value, int) and not isinstance(value, bool) and value >= minimum,
            f"{context}: expected integer >= {minimum}")
    return value


def finite_tree(value, context="root"):
    if isinstance(value, float):
        require(math.isfinite(value), f"{context}: nonfinite value")
    elif isinstance(value, dict):
        for key, item in value.items():
            finite_tree(item, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            finite_tree(item, f"{context}[{index}]")


def load(path, *, lines=False):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        result = [json.loads(line) for line in stream if line.strip()] if lines else json.load(stream)
    finite_tree(result, path.name)
    return result


def flatten(record):
    """Accept flat records or documented metadata/observables wrappers."""
    result = {}
    for name in ("metadata", "observables", "features"):
        if isinstance(record.get(name), dict):
            for key, value in record[name].items():
                if key in result:
                    equal(result[key], value, f"conflicting wrapped field {key}")
                result[key] = value
    for key, value in record.items():
        if key not in ("metadata", "observables", "features"):
            if key in result:
                equal(result[key], value, f"conflicting outer field {key}")
            result[key] = value
    return result


OFF4 = tuple((i, j) for i in range(4) for j in range(4) if i != j)
PERM4 = tuple(itertools.permutations(range(4)))


def canonical4(order):
    return min(sum(int(order[p[i], p[j]]) << bit for bit, (i, j) in enumerate(OFF4))
               for p in PERM4)


def components(order):
    remaining = set(range(len(order)))
    count = 0
    while remaining:
        count += 1
        queue = [remaining.pop()]
        while queue:
            vertex = queue.pop()
            adjacent = {j for j in remaining if order[vertex, j] or order[j, vertex]}
            remaining.difference_update(adjacent)
            queue.extend(adjacent)
    return count


@lru_cache(maxsize=1)
def independent_catalog():
    """Exhaust three orientations of each unordered pair, independently."""
    unordered = tuple(itertools.combinations(range(4), 2))
    representatives = {}
    labeled_count = 0
    for states in itertools.product((-1, 0, 1), repeat=6):
        order = np.zeros((4, 4), dtype=bool)
        for (a, b), state in zip(unordered, states):
            if state:
                order[(a, b) if state > 0 else (b, a)] = True
        # Check every implication, including cycles, rather than using package validation.
        if any(order[a, b] and order[b, c] and not order[a, c]
               for a in range(4) for b in range(4) for c in range(4)):
            continue
        labeled_count += 1
        representatives.setdefault(canonical4(order), order)
    equal(labeled_count, 219, "independent labeled four-poset enumeration")
    equal(len(representatives), 16, "independent unlabeled four-poset enumeration")
    result = []
    for index, code in enumerate(sorted(representatives)):
        order = representatives[code]
        n22 = int(order.sum() == 2 and np.all(order.sum(axis=0) + order.sum(axis=1) == 1))
        result.append(dict(id=index, canonical_code=code, components=components(order), n22=n22))
    return result


@lru_cache(maxsize=1)
def exact_rank_reference():
    """Independent d2 enumeration; 2+2 is the permutation pattern 3412."""
    ids = {entry["canonical_code"]: entry["id"] for entry in independent_catalog()}
    counts4 = [0] * 16
    for rank in PERM4:
        order = np.array([[i < j and rank[i] < rank[j] for j in range(4)] for i in range(4)])
        counts4[ids[canonical4(order)]] += 1
    choices = tuple(itertools.combinations(range(8), 4))
    joint = Counter()
    for rank in itertools.permutations(range(8)):
        # Connectivity via union/find, independent of the extractor's bitset BFS.
        roots = list(range(8))
        def root(vertex):
            while roots[vertex] != vertex:
                vertex = roots[vertex]
            return vertex
        for i in range(8):
            for j in range(i + 1, 8):
                if rank[i] < rank[j]:
                    roots[root(j)] = root(i)
        connected = int(len({root(i) for i in range(8)}) == 1)
        n22 = sum(rank[k] < rank[l] < rank[i] < rank[j] for i, j, k, l in choices)
        joint[(connected, n22)] += 1
    return counts4, joint


def signature(row):
    return row["count"], row["relations"], row["longest_chain"], tuple(row["interval_histogram"])


def audit_row(row, catalog):
    context = f"row {row['sample_id']}"
    n = integer(row["count"], context + " count")
    r = integer(row["relations"], context + " relations")
    height = integer(row["longest_chain"], context + " height")
    pairs = math.comb(n, 2)
    require(r <= pairs and height <= n, context + " finite order bounds")
    require(height >= int(n > 0), context + " nonempty order height")
    histogram = row["interval_histogram"]
    equal(len(histogram), max(n - 1, 1), context + " histogram length")
    for count in histogram:
        integer(count, context + " histogram count")
    equal(sum(histogram), r, context + " relation histogram")
    equal(histogram[0], row["link_count"], context + " links")
    close(row["ordering_fraction"], r / pairs if pairs else None, context + " ordering fraction")
    close(row["chain_fraction"], height / n if n else 0., context + " chain fraction")
    c3 = sum(m * count for m, count in enumerate(histogram))
    equal(row["chains3"], c3, context + " chain3 histogram identity")
    degree_profile = row["joint_degree_profile"]
    seen_degrees = set()
    for past, future, count in degree_profile:
        integer(past, context + " past degree")
        integer(future, context + " future degree")
        integer(count, context + " degree multiplicity", 1)
        require(past + future < n and (past, future) not in seen_degrees,
                context + " valid unique degree cell")
        seen_degrees.add((past, future))
    equal(sum(count for past, future, count in degree_profile), n, context + " degree population")
    equal(sum(past * count for past, future, count in degree_profile), r, context + " past degree sum")
    equal(sum(future * count for past, future, count in degree_profile), r, context + " future degree sum")
    equal(sum(past * future * count for past, future, count in degree_profile), c3,
          context + " degree chain3 identity")
    equal(sum(math.comb(past * future, 2) * count for past, future, count in degree_profile),
          row["overlap_sum"], context + " independent O1 degree identity")
    equal(row["chains4"] + row["diamonds4"],
          sum(math.comb(m, 2) * count for m, count in enumerate(histogram)),
          context + " chain4/diamond identity")
    for name in ("chains3", "chains4", "diamonds4", "n22", "overlap_sum", "overlap_choose2_sum"):
        integer(row[name], context + " " + name)
    require(row["n22"] <= math.comb(n, 4) if n >= 4 else row["n22"] == 0,
            context + " induced pattern bound")
    interval_pairs = math.comb(r, 2)
    o1, o2 = row["overlap_sum"], row["overlap_choose2_sum"]
    close(row["overlap_mean"], o1 / interval_pairs if interval_pairs else None, context + " overlap mean")
    numerator = (o1 + 2 * o2) * interval_pairs - o1 * o1
    require(numerator >= 0, context + " nonnegative overlap variance")
    close(row["overlap_variance"], numerator / interval_pairs**2 if interval_pairs else None,
          context + " overlap variance")
    if not interval_pairs:
        equal((o1, o2), (0, 0), context + " no interval pairs")
    profile = Counter()
    seen = set()
    for m, k, count in row["interval_component_profile"]:
        integer(m, context + " interval size")
        integer(k, context + " component count")
        integer(count, context + " profile count", 1)
        require(m < len(histogram) and ((m == k == 0) or 1 <= k <= m), context + " component bounds")
        require((m, k) not in seen, context + " duplicate component cell")
        seen.add((m, k))
        profile[(m, k)] = count
    equal([sum(value for (size, k), value in profile.items() if size == m)
           for m in range(len(histogram))], histogram, context + " component marginal")
    for m in (2, 4, 8):
        equal(row[f"interval_m{m}_count"], histogram[m] if m < len(histogram) else 0,
              context + f" size{m} count")
    equal(row["interval_m2_connected"], profile[(2, 1)], context + " connected2")
    motifs4 = row["interval_m4_motif_counts"]
    equal(len(motifs4), 16, context + " local motif count length")
    for value in motifs4:
        integer(value, context + " local motif count")
    equal(sum(motifs4), row["interval_m4_count"], context + " local motif marginal")
    for k in range(1, 5):
        equal(sum(motifs4[entry["id"]] for entry in catalog if entry["components"] == k),
              profile[(4, k)], context + f" local motif component{k}")
    joint = row["interval_m8_joint"]
    seen = set()
    for k, n22, count in joint:
        integer(k, context + " joint components", 1)
        integer(n22, context + " joint n22")
        integer(count, context + " joint count", 1)
        require(k <= 8 and n22 <= 70 and (k, n22) not in seen, context + " joint bounds/uniqueness")
        seen.add((k, n22))
    equal(sum(count for k, value, count in joint), row["interval_m8_count"], context + " m8 joint marginal")
    equal(sum(count for k, value, count in joint if k == 1), row["interval_m8_connected"], context + " m8 connected")
    equal(sum(value * count for k, value, count in joint), row["interval_m8_n22_sum"], context + " m8 n22")
    equal(sum(value * count for k, value, count in joint if k == 1), row["interval_m8_connected_n22_sum"], context + " m8 joint moment")
    for k in range(1, 9):
        equal(sum(count for components8, value, count in joint if components8 == k), profile[(8, k)],
              context + f" m8 component{k}")
    motifs = row.get("motifs", row.get("global_motifs"))
    require(isinstance(motifs, dict), context + " missing global motif record")
    counts = motifs["counts"]
    equal(len(counts), 16, context + " global motif length")
    for value in counts:
        integer(value, context + " global motif count")
    draws = integer(motifs["draws"], context + " motif draws")
    equal(sum(counts), draws, context + " motif sample sum")
    if n < 4:
        equal((draws, motifs["frequencies"], motifs["mc_variance"]), (0, None, None), context + " undefined motifs")
    else:
        require(draws > 0, context + " positive motif denominator")
        equal(len(motifs["frequencies"]), 16, context + " frequency length")
        equal(len(motifs["mc_variance"]), 16, context + " variance length")
        require(motifs["method"] in ("exact", "sampled"), context + " motif method")
        for count, p, variance in zip(counts, motifs["frequencies"], motifs["mc_variance"]):
            close(p, count / draws, context + " motif frequency")
            close(variance, 0. if motifs["method"] == "exact" else p * (1 - p) / (draws - 1),
                  context + " conditional motif variance")
        if motifs["method"] == "exact":
            equal(draws, math.comb(n, 4), context + " exact subset denominator")
            equal(sum(counts[entry["id"]] * entry["n22"] for entry in catalog), row["n22"], context + " exact motif22 identity")


def references_in(value):
    if isinstance(value, dict):
        if all(name in value for name in ("dimension", "fit", "m4", "m8")):
            yield value
        else:
            for item in value.values():
                yield from references_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from references_in(item)


def audit_reference(reference):
    d, fit = reference["dimension"], reference["fit"]
    context = f"reference fit{fit}/d{d}"
    require(d in (2, 3, 4), context + " dimension")
    integer(fit, context + " fit")
    equal(reference["exact"], d == 2, context + " exact flag")
    n4, n8 = reference["m4"]["count"], reference["m8"]["count"]
    integer(n4, context + " n4", 1)
    integer(n8, context + " n8", 1)
    ids = reference["m4"]["outcomes"]
    equal(len(ids), n4, context + " raw m4 count")
    require(all(isinstance(i, int) and not isinstance(i, bool) and 0 <= i < 16 for i in ids), context + " motif IDs")
    equal([ids.count(i) for i in range(16)], reference["m4"]["counts"], context + " m4 frequencies")
    joint = {}
    for connected, n22, count in reference["m8"]["joint_counts"]:
        require(connected in (0, 1) and isinstance(connected, int), context + " connectivity indicator")
        integer(n22, context + " reference n22")
        integer(count, context + " reference cell count", 1)
        require(n22 <= 70 and (connected, n22) not in joint, context + " unique valid reference cells")
        joint[(connected, n22)] = count
    equal(sum(joint.values()), n8, context + " m8 denominator")
    probability = math.gamma(d + 1) * math.gamma(d / 2) / (2 * math.gamma(3 * d / 2))
    close(reference["connected2"], probability, context + " analytic p(d)")
    if d == 2:
        counts4, joint8 = exact_rank_reference()
        equal((n4, n8), (24, 40320), context + " exact enumeration sizes")
        equal(reference["m4"]["counts"], counts4, context + " exact m4 distribution")
        equal(joint, dict(joint8), context + " exact m8 distribution")
        equal(reference["m8"]["outcomes"], None, context + " grouped exact outcomes")
    else:
        outcomes = reference["m8"]["outcomes"]
        equal(len(outcomes), n8, context + " raw m8 count")
        equal(dict(Counter(map(tuple, outcomes))), joint, context + " raw m8 outcomes")


def audit_artifacts(directory: Path, *, allow_explicit_search_budgets=False):
    raw_file = load(directory / "raw_orders.jsonl.gz", lines=True)
    pair_file = load(directory / "pairs.jsonl.gz", lines=True)
    search_file = load(directory / "searches.jsonl.gz", lines=True)
    reference_file = load(directory / "references.json.gz")
    raw = [flatten(row) for row in raw_file]
    pairs = [flatten(row) for row in pair_file]
    searches = [flatten(row) for row in search_file]
    references = list(references_in(reference_file))
    metadata = load(directory / "metadata.json")
    summary = load(directory / "summary.json")
    require(raw, "archive contains no parent records")
    ids = [row["sample_id"] for row in raw]
    equal(len(set(ids)), len(raw), "globally unique sample IDs")
    config = metadata["config"]
    def identity(fit, phase, family, dimension, count, repeat, parameter=None):
        payload = ["local-v1", config["seed"], fit, phase, family, dimension, count, repeat, parameter]
        return hashlib.sha256(json.dumps(payload, separators=(",", ":"), ensure_ascii=True,
                                        allow_nan=False).encode("ascii")).hexdigest()
    expected_ids = set()
    for fit in range(config["fits"]):
        for count in config["counts"]:
            families = [(family, dimension) for dimension in config["dimensions"]
                        for family in ("diamond", "slab", "box")]
            families += [("rank2", 2), ("rank3", 0), ("interval", 0)]
            families += [(f"lex_{scaling}_{member}", 0) for scaling in ("fixed", "inflated")
                         for member in ("connected", "split")]
            for family, dimension in families:
                for repeat in range(config["repeats"]):
                    expected_ids.add(identity(fit, "final", family, dimension, count, repeat))
            for dimension in config["dimensions"]:
                for repeat in range(config["fiber_repeats"]):
                    for checkpoint in ("initial", "midpoint", "final"):
                        expected_ids.add(identity(fit, "final", "fiber_" + checkpoint,
                                                  dimension, count, repeat))
    equal(set(ids), expected_ids, "complete configured final grid")
    catalog = independent_catalog()
    by_pair, by_search = defaultdict(list), defaultdict(list)
    for row in raw:
        equal(row["sample_id"], identity(row["fit"], "final", row["family"], row["dimension"],
                                        row["count"], row["repeat"], row.get("parameter")),
              "parameter-keyed sample identity")
        audit_row(row, catalog)
        if row.get("pair_id") is not None:
            by_pair[row["pair_id"]].append(row)
        if row.get("search_id") is not None:
            by_search[row["search_id"]].append(row)
    pair_ids = [pair["pair_id"] for pair in pairs]
    equal(len(set(pair_ids)), len(pairs), "unique exact pair IDs")
    equal(set(pair_ids), set(by_pair), "pair metadata/row coverage")
    for pair in pairs:
        context = f"pair {pair['pair_id']}"
        members = by_pair[pair["pair_id"]]
        equal(len(members), 2, context + " member count")
        equal(signature(members[0]), signature(members[1]), context + " exact old signature")
        equal(members[0]["joint_degree_profile"], members[1]["joint_degree_profile"], context + " joint degrees")
        equal(members[0]["overlap_sum"], members[1]["overlap_sum"], context + " equal O1")
        q, s = integer(pair["base_count"], context + " q", 1), integer(pair["blowup"], context + " s", 1)
        equal(members[0]["count"], 8 * q * s, context + " event count")
        expected = 4 * q * s**4
        equal(pair["expected_n22_difference"], expected, context + " derived difference")
        equal(abs(members[0]["n22"] - members[1]["n22"]), expected, context + " measured difference")
        by_id = {row["sample_id"]: row for row in members}
        first, second = by_id[pair["first_sample_id"]], by_id[pair["second_sample_id"]]
        equal((first["member"], second["member"]), ("first", "second"), context + " named members")
        equal(second["n22"] - first["n22"], expected, context + " directed pair contrast")
        equal(signature(flatten(pair["old_signature"])), signature(members[0]), context + " saved signature")
        if pair["scaling"] == "fixed":
            equal(s, 1, context + " fixed module size")
        elif pair["scaling"] == "inflated":
            equal(q, 4, context + " fixed base size")
        else:
            raise ValueError(context + " unknown scaling")
    search_ids = [search["search_id"] for search in searches]
    equal(len(set(search_ids)), len(searches), "unique search IDs")
    equal(set(search_ids), set(by_search), "search metadata/row coverage")
    for search in searches:
        context = f"search {search['search_id']}"
        members = by_search[search["search_id"]]
        equal(len(members), 3, context + " checkpoint count")
        checkpoints_by_name = {row["checkpoint"]: row for row in members}
        equal(set(checkpoints_by_name), {"initial", "midpoint", "final"}, context + " named checkpoints")
        old = signature(flatten(search["old_signature"]))
        for row in members:
            equal(signature(row), old, context + " invariant fiber")
        steps = integer(search["steps"], context + " budget", 1)
        if not allow_explicit_search_budgets:
            equal(steps, search["count"]**2 // 64, context + " quadratic budget")
        outcomes = search["outcomes"]
        equal(set(outcomes), {"no_cover_pair", "shared_endpoint", "existing_replacement", "cycle",
                              "unchanged_order", "old_statistics_changed", "accepted"}, context + " outcome categories")
        for count in outcomes.values():
            integer(count, context + " outcome count")
        equal(sum(outcomes.values()), steps, context + " all attempts retained")
        equal(search["midpoint_step"], steps // 2, context + " midpoint")
        checkpoints = search["checkpoints"]
        equal([entry["attempt"] for entry in checkpoints], [0, steps // 2, steps], context + " checkpoint times")
        for checkpoint in checkpoints:
            equal(sum(checkpoint["outcomes"].values()), checkpoint["attempt"], context + " checkpoint accounting")
        equal(checkpoints[-1]["outcomes"], outcomes, context + " final outcomes")
        equal(search["any_accepted_move"], bool(outcomes["accepted"]), context + " accepted flag")
        equal(search["final_matrix_changed"], search["final_matrix_difference"] > 0, context + " final movement")
        equal(search["old_signature_preserved"], True, context + " preservation flag")
        if search["final_matrix_changed"]:
            require(outcomes["accepted"] > 0, context + " movement requires acceptance")
        fields = ("n22", "chains4", "overlap_sum", "overlap_choose2_sum", "interval_component_profile",
                  "interval_m4_motif_counts", "interval_m8_joint")
        initial = checkpoints_by_name["initial"]
        for checkpoint in ("midpoint", "final"):
            changed = any(initial[name] != checkpoints_by_name[checkpoint][name] for name in fields)
            equal(search[checkpoint + "_local_changed"], changed, context + " local invariant change")
    reference_ids = [(row["fit"], row["dimension"]) for row in references]
    require(references, "archive contains no reference fits")
    equal(len(reference_ids), len(set(reference_ids)), "unique fit/dimension references")
    for reference in references:
        audit_reference(reference)
    equal(set(reference_ids), {(fit, d) for fit in range(config["fits"]) for d in config["dimensions"]},
          "complete independent reference grid")
    for key, value in (("row_count", len(raw)), ("pair_count", len(pairs)), ("search_count", len(searches))):
        equal(metadata[key], value, "metadata " + key)
    digest = hashlib.sha256()
    for name, value in (("raw_orders", raw_file), ("references", reference_file), ("summary", summary),
                        ("pairs", pair_file), ("searches", search_file)):
        digest.update(name.encode("ascii") + b"\n")
        for entry in value if isinstance(value, list) else [value]:
            digest.update(json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                                     allow_nan=False).encode("utf-8") + b"\n")
    equal(digest.hexdigest(), metadata["scientific_sha256"], "independent scientific digest")
    for name, expected in metadata["artifact_sha256"].items():
        require(Path(name).name == name, "artifact hash paths must be archive basenames")
        equal(hashlib.sha256((directory / name).read_bytes()).hexdigest(), expected, "artifact hash " + name)
    return {"status": "passed", "parent_records": len(raw), "exact_pairs": len(pairs),
            "fiber_searches": len(searches), "reference_fits": len(references),
            "independent_motif_classes": len(catalog),
            "explicit_search_budget_exception": bool(allow_explicit_search_budgets),
            "bootstrap_intervals_recomputed": False,
            "checks": ["finite JSON", "unique records", "histogram and chain identities",
                       "connectivity and conditional-pattern margins", "overlap arithmetic",
                       "global motif sampling arithmetic", "exact pair invariants",
                       "fiber checkpoints and attempt accounting", "reference raw outcomes",
                       "independently enumerated exact d2 references", "complete configured grid",
                       "independent scientific and file digests"],
            "metadata_present": isinstance(metadata, dict), "summary_present": summary is not None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-explicit-search-budgets", action="store_true",
                        help="allow explicitly recorded smoke budgets instead of N²//64")
    args = parser.parse_args()
    result = audit_artifacts(args.directory,
                             allow_explicit_search_budgets=args.allow_explicit_search_budgets)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
