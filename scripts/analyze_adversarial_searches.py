"""Post-run descriptive search audit; writes only an ignored results artifact."""
from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from causal_lab.adversarial_features import extract_features, feature_vector, SEARCH_FEATURES
from causal_lab.adversarial_generators import optimize_order
from causal_lab.adversarial_study import rng_for
from causal_lab.adversarial_detectors import wilson_interval


def lines(path):
    with gzip.open(path, "rt") as source:
        return [json.loads(line) for line in source]


def distribution(values):
    values = np.asarray(values, dtype=float)
    return dict(count=len(values), mean=float(values.mean()), minimum=float(values.min()),
                median=float(np.median(values)), maximum=float(values.max()),
                q25=float(np.quantile(values, .25)), q75=float(np.quantile(values, .75)))


def binomial(successes, count):
    low, high = wilson_interval(successes, count)
    return dict(successes=successes, count=count,
                rate=successes/count if count else None, wilson_low=low, wilson_high=high)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--out", type=Path, default=Path("results/adversarial-search-analysis.json"))
    args = parser.parse_args()
    raw = lines(args.data/"raw.jsonl.gz")
    searches = lines(args.data/"searches.jsonl.gz")
    models = json.loads((args.data/"models.json").read_text())
    metadata = json.loads((args.data/"metadata.json").read_text())
    effects = json.loads((args.data/"search_effects.json").read_text())
    by_id = {row["sample_id"]: row for row in raw}
    checkpoint = {(row["search_id"], row["family"]): row for row in raw if "search_id" in row}
    by_cell = defaultdict(list)
    seeds = metadata["config"]
    assert len(searches) == 5400
    assert len(checkpoint) == 10800
    assert len({row["search_id"] for row in searches}) == len(searches)
    for search in searches:
        assert search["evaluations"] == 64
        assert search["phase_one_evaluations"] == 12
        assert search["phase_two_evaluations"] == 52
        assert search["post_search_integrity_evaluations"] == 2
        donor = by_id[search["target_sample_id"]]
        assert donor["phase"] == "development"
        assert donor["fit"] == search["fit"] and donor["count"] == search["count"]
        assert donor["true_dimension"] == search["dimension"]
        assert np.array_equal(feature_vector(donor), search["target_vector"])
        for family, key in (("height_matched", "height_fraction_vector"),
                            ("multi_matched", "multifeature_vector")):
            row = checkpoint[search["search_id"], family]
            assert row["longest_chain"] == search["target_height"] == donor["longest_chain"]
            assert np.array_equal(feature_vector(row), search[key])
        goal, scales = np.asarray(search["target_vector"]), np.asarray(search["scale_vector"])
        initial = (np.asarray(search["height_fraction_vector"]) - goal) / scales
        final = (np.asarray(search["multifeature_vector"]) - goal) / scales
        assert search["initial_objective"] == float(np.sqrt(np.mean(initial**2)))
        assert search["best_objective"] == float(np.sqrt(np.mean(final**2)))
        assert search["best_objective"] <= search["initial_objective"]
        assert search["multifeature_match"] == bool(np.max(np.abs(final)) <= 1)
        assert search["height_fraction_match"] == bool(abs(search["height_fraction_vector"][0] - goal[0]) <= .02)
        by_cell[search["dimension"], search["count"], search["fit"]].append(search)

    cells = []
    for (d, n, fit), rows in sorted(by_cell.items()):
        assert len(rows) == 200
        accepted = {}
        for family, flag in (("height_matched", "height_fraction_match"),
                             ("multi_matched", "multifeature_match")):
            decision_rows = [checkpoint[s["search_id"], family] for s in rows]
            failures = [i for i, s in enumerate(rows) if not s[flag]]
            successes = [i for i, s in enumerate(rows) if s[flag]]
            accepted[family] = {}
            for j, detector in enumerate("ABCDEF"):
                flags = [r["accepted"]["0.95"][j] for r in decision_rows]
                accepted[family][detector] = dict(
                    all_orders=binomial(sum(flags), len(flags)),
                    failed_matches=binomial(sum(flags[i] for i in failures), len(failures)),
                    successful_matches=binomial(sum(flags[i] for i in successes), len(successes)))
        before = np.array([(np.asarray(s["height_fraction_vector"])-s["target_vector"])/s["scale_vector"] for s in rows])
        after = np.array([(np.asarray(s["multifeature_vector"])-s["target_vector"])/s["scale_vector"] for s in rows])
        feature_residuals = [dict(feature=name,
                                  initial_abs_z=distribution(np.abs(before[:, j])),
                                  final_abs_z=distribution(np.abs(after[:, j])),
                                  initial_within_one=int(np.sum(np.abs(before[:, j]) <= 1)),
                                  final_within_one=int(np.sum(np.abs(after[:, j]) <= 1)))
                             for j, name in enumerate(SEARCH_FEATURES)]
        all_six = [checkpoint[s["search_id"], "multi_matched"] for s in rows
                   if all(checkpoint[s["search_id"], "multi_matched"]["accepted"]["0.95"])]
        cells.append(dict(dimension=d, count=n, fit=fit, searches=len(rows),
                          height_fraction_match=binomial(sum(s["height_fraction_match"] for s in rows), len(rows)),
                          multifeature_match=binomial(sum(s["multifeature_match"] for s in rows), len(rows)),
                          outside_bounds=sum(s["target_r_outside_attainable_bounds"] for s in rows),
                          no_mutable_edges=sum(s["no_mutable_edges"] for s in rows),
                          no_change_proposals=sum(s["no_change_proposals"] for s in rows),
                          search_with_improvement=sum(s["best_objective"] < s["initial_objective"] for s in rows),
                          initial_objective=distribution([s["initial_objective"] for s in rows]),
                          final_objective=distribution([s["best_objective"] for s in rows]),
                          initial_max_abs_z=distribution([s["initial_max_abs_z"] for s in rows]),
                          final_max_abs_z=distribution([s["best_max_abs_z"] for s in rows]),
                          initial_fraction_error=distribution([s["fraction_error"] for s in rows]),
                          final_fraction_error=distribution([abs(s["multifeature_vector"][0]-s["target_vector"][0]) for s in rows]),
                          selected_q=distribution([s["selected_probability"] for s in rows]),
                          feature_residuals=feature_residuals, acceptance=accepted,
                          all_six_accepted_multifeature_checkpoint_count=len(all_six),
                          first_all_six_accepted_sample_id=all_six[0]["sample_id"] if all_six else None))

    reconstructed = []
    counts = sorted({s["count"] for s in searches})
    for d in (2, 3, 4):
        for ni, n in enumerate(counts):
            fit = (d + ni) % 3
            search = next(s for s in searches if s["dimension"] == d and s["count"] == n
                          and s["fit"] == fit and s["repeat"] == 0)
            development = sorted([r for r in raw if r["phase"] == "development" and
                                  r["fit"] == fit and r["count"] == n and r["true_dimension"] == d],
                                 key=lambda r: r["repeat"])
            rng = rng_for(seeds["seed"], fit, "test", "search", d, n, 0)
            donor = development[int(rng.integers(len(development)))]
            assert donor["sample_id"] == search["target_sample_id"]
            parameters = next(p for p in models[str(fit)][str(n)]["adversary_parameters"] if p["dimension"] == d)
            assert parameters["search_scales"] == search["scale_vector"]
            again = optimize_order(n, rng, donor, parameters["search_scales"], steps=64)
            assert all(search[key] == value for key, value in again.metadata.items())
            hashes = {}
            for family, order in (("height_matched", again.height_fraction_order),
                                  ("multi_matched", again.multifeature_order)):
                record = checkpoint[search["search_id"], family]
                measured = extract_features(order)
                assert all(record[key] == value for key, value in measured.items())
                hashes[family] = hashlib.sha256(np.packbits(order, axis=1, bitorder="little").tobytes()).hexdigest()
            reconstructed.append(dict(fit=fit, dimension=d, count=n, repeat=0,
                                      search_id=search["search_id"], matrix_sha256=hashes,
                                      metadata_equal=True, all_features_and_histograms_equal=True))
    bipartite = [dict(fit=int(fit), count=int(n), **params)
                 for fit, group in models.items() for n, model in group.items()
                 for params in model["adversary_parameters"]]
    result = dict(
        note="Descriptive audit of every retained search; per-fit intervals condition on development and calibration pools. No new detector or threshold was fitted. Subgroup intervals are descriptive, selected after the search outcome.",
        searches=len(searches), candidate_evaluations=sum(s["evaluations"] for s in searches),
        all_search_integrity_checks_passed=True,
        height_fraction_successes=sum(s["height_fraction_match"] for s in searches),
        multifeature_successes=sum(s["multifeature_match"] for s in searches),
        unattainable_fraction_targets=sum(s["target_r_outside_attainable_bounds"] for s in searches),
        total_no_change_proposals=sum(s["no_change_proposals"] for s in searches),
        no_mutable_searches=sum(s["no_mutable_edges"] for s in searches),
        improved_searches=sum(s["best_objective"] < s["initial_objective"] for s in searches),
        cells=cells, bipartite_parameters=bipartite,
        bipartite_saturations=sum(p["saturated"] for p in bipartite),
        paired_search_effects=[r for r in effects if r["target"] == .95],
        reconstructed=reconstructed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps({key: result[key] for key in result if key not in
                     {"cells", "bipartite_parameters", "paired_search_effects", "reconstructed"}}, indent=2))
    print("Independently reconstructed", len(reconstructed), "first-search cases.")


if __name__ == "__main__":
    main()
