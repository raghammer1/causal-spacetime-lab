"""Independent archived-raw-data statistical reconstruction for Experiment 6.

No causal_lab imports: bootstrap seeds, weighting, order statistics and binomial
tail inversion are independently reconstructed. Does not draw quantum states.
Run only after the source archive's manifest exists.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import time

import numpy as np


FIELDS = ("family", "n", "h", "preparation", "delta", "time")
RESAMPLES = 3999
TOLERANCE = 2e-12


class Audit:
    def __init__(self):
        self.counts = Counter()
        self.max_errors = defaultdict(float)
        self.failures = []

    def exact(self, category, actual, expected, context):
        self.counts[category] += 1
        if actual != expected:
            self.failures.append(dict(category=category, context=context,
                                      actual=actual, expected=expected))

    def near(self, category, actual, expected, context):
        self.counts[category] += 1
        if actual is None or expected is None:
            if actual is not expected:
                self.failures.append(dict(category=category, context=context,
                                          actual=actual, expected=expected))
            return
        error = abs(float(actual) - float(expected))
        self.max_errors[category] = max(self.max_errors[category], error)
        if not math.isfinite(error) or error > TOLERANCE:
            self.failures.append(dict(category=category, context=context,
                                      actual=actual, expected=expected, absolute_error=error))


def finite(value):
    return value is not None and math.isfinite(float(value))


def mean(values):
    return math.fsum(float(value) for value in values) / len(values)


def lower_binomial(successes, count, alpha):
    if successes == 0:
        return 0.
    low, high = 0., 1.
    for _ in range(80):
        p = (low + high) / 2
        tail = math.fsum(math.comb(count, k) * p ** k * (1 - p) ** (count - k)
                         for k in range(successes, count + 1))
        if tail < alpha:
            low = p
        else:
            high = p
    return (low + high) / 2


def bootstrap_rng(cell, metric):
    # Independently reproduce the documented semantic stream; no random module import.
    payload = ["quantum-v1", "bootstrap", 61401, "summary", *cell, metric]
    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=True,
                         allow_nan=False).encode("ascii")
    words = struct.unpack("<8I", hashlib.sha256(encoded).digest())
    return np.random.default_rng(np.random.SeedSequence(words))


def order_statistic(sorted_values, probability):
    location = (len(sorted_values) - 1) * probability
    left = math.floor(location)
    right = math.ceil(location)
    fraction = location - left
    return (1 - fraction) * float(sorted_values[left]) + fraction * float(sorted_values[right])


def interval_reference(records, cell, metric):
    values = [float(record["metrics"][metric]) for record in records]
    center = mean(values)
    answer = {"mean": center, "n": len(values), "batch_means": {}}
    if all(not record["stochastic"] for record in records):
        answer.update(deterministic=True, ci95=None, lower=None)
        return answer
    groups = defaultdict(list)
    for record, value in zip(records, values):
        groups[record["batch"]].append(value)
    answer["sd"] = (math.sqrt(math.fsum((value - center) ** 2 for value in values)
                              / (len(values) - 1)) if len(values) > 1 else None)
    answer["batch_means"] = {str(batch): mean(sample) for batch, sample in groups.items()}
    alpha = .05 / 6 if metric in ("shuffle_minus_stress_d3", "phase_minus_stress_d3") else .05
    answer["alpha_lower"] = alpha
    answer["weak_small_sample"] = len(values) < 12
    if any(len(sample) == 1 for sample in groups.values()):
        answer.update(ci95=None, lower=None, weak_small_sample=True,
                      interval_unavailable="one or more singleton strata")
        return answer
    rng = bootstrap_rng(cell, metric)
    draws = np.zeros(RESAMPLES)
    # Reconstruct multiplicity weights and their dot product, rather than the
    # production routine's direct indexed sums. Preserve stream draw order.
    for batch in sorted(groups):
        sample = np.asarray(groups[batch])
        positions = rng.integers(0, len(sample), size=(RESAMPLES, len(sample)))
        multiplicities = np.zeros((RESAMPLES, len(sample)), dtype=np.int64)
        row_indices = np.arange(RESAMPLES)
        for column in range(len(sample)):
            np.add.at(multiplicities, (row_indices, positions[:, column]), 1)
        draws += multiplicities @ sample / len(values)
    ordered = np.sort(draws)
    answer["ci95"] = [order_statistic(ordered, .025), order_statistic(ordered, .975)]
    answer["lower"] = order_statistic(ordered, alpha)
    return answer


def independent_auc(mi, couplings):
    positives, negatives = [], []
    for i in range(len(mi)):
        for j in range(i + 1, len(mi)):
            (positives if couplings[i][j] != 0 else negatives).append(mi[i][j])
    if not positives or not negatives:
        return None
    wins = 0.
    for positive in positives:
        for negative in negatives:
            tolerance = 1e-10 + 1e-8 * max(abs(positive), abs(negative))
            wins += .5 if abs(positive - negative) <= tolerance else float(positive > negative)
    return wins / (len(positives) * len(negatives))


def read_archive(path, audit):
    rows = []
    seen = set()
    with gzip.open(path / "raw.jsonl.gz", "rt") as source:
        for line in source:
            record = json.loads(line)
            identity = record["sample_id"]
            audit.exact("unique_raw_sample", identity in seen, False, identity)
            seen.add(identity)
            if record["status"] == "ok":
                metrics = record["metrics"]
                nulls = record["nulls"]
                if nulls:
                    audit.exact("conditional_null_count", len(nulls), 31, identity)
                    for metric in ("stress_d1", "stress_d2", "stress_d3", "positive_participation_rank"):
                        expected = mean([draw[metric] for draw in nulls])
                        audit.near("conditional_null_mean", metrics[f"shuffle_{metric}_mean"], expected,
                                   f"{identity}/{metric}")
                    audit.near("shuffle_paired_effect", metrics["shuffle_minus_stress_d3"],
                               mean([draw["stress_d3"] for draw in nulls]) - metrics["stress_d3"], identity)
                if "edge_auc" in metrics:
                    audit.near("raw_edge_auc", metrics["edge_auc"],
                               independent_auc(record["observables"]["mi"], record["couplings"]), identity)
                for kind in ("singleton", "balanced"):
                    cuts = [cut for cut in record["cuts"] if cut["kind"] == kind]
                    for suffix, raw in (("defect", "defect"), ("normalized_defect", "normalized_defect")):
                        audit.near("cut_mean", metrics[f"cut_{kind}_mean_abs_{suffix}"],
                                   mean([abs(cut[raw]) for cut in cuts]), f"{identity}/{kind}/{suffix}")
            # Do not retain large states, embeddings or null replicas in memory.
            fields = (*FIELDS, "unit_id", "sample_id", "batch", "rep", "status", "stochastic", "metrics")
            rows.append({key: record[key] for key in fields})
    return rows


def run(path):
    started = time.perf_counter()
    if not (path / "manifest.json").exists():
        raise RuntimeError("audit requires a completed source manifest")
    audit = Audit()
    metadata = json.loads((path / "metadata.json").read_text())
    audit.exact("source_phase", metadata["phase"], "primary", "metadata")
    audit.exact("source_clean", metadata["tracked_dirty"], False, "metadata")
    audit.exact("source_complete", metadata["complete"], True, "metadata")
    rows = read_archive(path, audit)
    audit.exact("metadata_row_count", metadata["states"], len(rows), "metadata")
    grouped = defaultdict(list)
    for row in rows:
        grouped[tuple(row[field] for field in FIELDS)].append(row)
    summary = json.loads((path / "summary.json").read_text())
    stored = {tuple(cell[field] for field in FIELDS): cell for cell in summary}
    audit.exact("summary_unique_cells", len(stored), len(summary), "summary")
    audit.exact("summary_cell_grid", set(stored) == set(grouped), True, "summary")
    pair_index = {(row["unit_id"], row["h"], row["preparation"], row["delta"], row["time"]): row for row in rows}
    for row in rows:
        if "phase_minus_stress_d3" in row["metrics"]:
            key = (row["unit_id"], row["h"], "phase_scrambled", row["delta"], row["time"])
            counterpart = pair_index.get(key)
            audit.exact("phase_pair_exists", counterpart is not None, True, row["sample_id"])
            if counterpart:
                expected = counterpart["metrics"]["stress_d3"] - row["metrics"]["stress_d3"]
                audit.near("phase_paired_effect", row["metrics"]["phase_minus_stress_d3"],
                           expected, row["sample_id"])
    cohorts = []
    chain_decisions = []
    metric_count = 0
    for key, records in grouped.items():
        if key not in stored:
            continue
        published = stored[key]
        context = repr(key)
        good = [record for record in records if record["status"] == "ok"]
        audit.exact("independent_units", len({record["unit_id"] for record in good}), len(good), context)
        for name, expected in (("attempted", len(records)), ("valid", len(good)), ("failures", len(records) - len(good))):
            audit.exact("cohort_denominators", published[name], expected, f"{context}/{name}")
        names = {name for record in good for name in record["metrics"]}
        available = {name for name in names if any(finite(record["metrics"].get(name)) for record in good)}
        audit.exact("metric_grid", set(published["metrics"]) == available, True, context)
        missing = {name: len(good) for name in names - available}
        audit.exact("all_undefined_metrics", published["undefined_metrics"], missing, context)
        for name in sorted(available):
            relevant = [record for record in good if finite(record["metrics"].get(name))]
            reference = interval_reference(relevant, key, name)
            actual = published["metrics"][name]
            metric_count += 1
            for field in ("n", "deterministic", "weak_small_sample", "interval_unavailable"):
                audit.exact("metric_flags", actual.get(field), reference.get(field), f"{context}/{name}/{field}")
            audit.exact("undefined_count", actual["undefined"], len(good) - len(relevant), f"{context}/{name}")
            for field in ("mean", "sd", "lower", "alpha_lower"):
                audit.near(f"summary_{field}", actual.get(field), reference.get(field), f"{context}/{name}")
            if reference["ci95"] is None:
                audit.exact("unavailable_interval", actual["ci95"], None, f"{context}/{name}")
            else:
                for i in range(2):
                    audit.near("summary_ci95", actual["ci95"][i], reference["ci95"][i], f"{context}/{name}/{i}")
            audit.exact("batch_grid", set(actual["batch_means"]), set(reference["batch_means"]), f"{context}/{name}")
            for batch, value in reference["batch_means"].items():
                audit.near("batch_mean", actual["batch_means"][batch], value, f"{context}/{name}/{batch}")
        family, n, h, prep, delta, time_value = key
        if family in ("B", "chain") and prep == "ground" and delta == 0:
            audit.exact("registered_ground_count", len(records), 24, context)
            audit.exact("registered_ground_batch_grid", Counter(record["batch"] for record in records),
                        Counter({0: 8, 1: 8, 2: 8}), context)
            cohorts.append(dict(family=family, n=n, h=h, attempted=len(records), valid=len(good)))
        if family == "chain" and h == 1 and prep == "ground" and delta == 0:
            auc = [record["metrics"].get("edge_auc") for record in good]
            auc = [value for value in auc if finite(value)]
            successes = sum(value >= .75 for value in auc)
            expected = lower_binomial(successes, len(auc), .05 / 3)
            actual = published["chain_success"]
            for name, value in (("successes", successes), ("count", len(auc)), ("attempted", len(records)),
                                ("undefined", len(records) - len(auc)),
                                ("complete_cohort", len(auc) == len(records)),
                                ("gate_eligible", len(auc) == len(records))):
                audit.exact("chain_success_fields", actual[name], value, f"{context}/{name}")
            audit.near("binomial_lower", actual["lower"], expected, context)
            audit.near("binomial_alpha", actual["alpha"], .05 / 3, context)
            auc_lower = published["metrics"]["edge_auc"]["ci95"][0]
            chain_decisions.append(dict(n=n, successes=successes, count=len(auc),
                exact_lower=expected, mean_auc_lower=auc_lower,
                passed=bool(actual["gate_eligible"] and expected > .8 and auc_lower > .8)))
    result = dict(audit="independent quantum statistics reconstruction", source_commit=metadata["source_commit"],
        source_files_sha256={name: hashlib.sha256((path / name).read_bytes()).hexdigest()
                             for name in ("raw.jsonl.gz", "summary.json", "metadata.json", "manifest.json")},
        raw_rows=len(rows), summary_cells=len(summary), summary_metrics=metric_count,
        resamples=RESAMPLES, absolute_tolerance=TOLERANCE,
        total_checks=sum(audit.counts.values()), checks=dict(audit.counts),
        maximum_absolute_errors=dict(audit.max_errors), failure_count=len(audit.failures),
        failures=audit.failures, ground_cohorts=cohorts, chain_decisions=chain_decisions,
        elapsed_seconds=time.perf_counter() - started,
        limitations=["No quantum state, eigensolver, geometry or scientific model is recomputed here.",
                     "Bootstrap reconstruction verifies arithmetic, not nominal coverage.",
                     "Independent calibration retained 365/400=91.25% normal-mean coverage at nominal 95%.",
                     "The .05/6 bootstrap allocation is not a rigorous simultaneous-coverage guarantee."])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.archive)
    args.output.with_suffix(".json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    lines = ["# Independent Experiment 6 statistical archive audit", "",
             f"Source commit: `{result['source_commit']}`.", "",
             f"Checked {result['raw_rows']} raw rows, {result['summary_cells']} summary cells and "
             f"{result['summary_metrics']} metric estimates. Reconstructed 3999-draw bootstrap "
             "distributions through multiplicity weights and explicit order-statistic interpolation; "
             "recomputed binomial lower bounds by finite-tail bisection.", "",
             f"**{result['total_checks']} checks; {result['failure_count']} failures**, "
             f"absolute tolerance {TOLERANCE:g}.", "",
             "This verifies arithmetic, pairing, independent-unit counts and failure denominators. "
             "It does not establish nominal bootstrap coverage: the retained calibration covered "
             "365/400 normal means (91.25%) with nominal 95% intervals.", "",
             "## Chain reconstruction", "",
             "| n | Successes | Exact lower bound | Mean AUC 95% lower | Registered gate |",
             "|---|---:|---:|---:|---|"]
    for row in sorted(result["chain_decisions"], key=lambda x: x["n"]):
        lines.append(f"| {row['n']} | {row['successes']}/{row['count']} | {row['exact_lower']:.12g} | "
                     f"{row['mean_auc_lower']:.12g} | {'passes' if row['passed'] else 'does not pass'} |")
    lines.extend(["", "## Audit counts", ""])
    lines.extend(f"- {name}: {value}" for name, value in sorted(result["checks"].items()))
    lines.extend(["", "## Maximum absolute numerical differences", ""])
    lines.extend(f"- {name}: {value:.6g}" for name, value in sorted(result["maximum_absolute_errors"].items()))
    if result["failures"]:
        lines.extend(["", "## Failures", "", "```json", json.dumps(result["failures"], indent=2), "```"])
    args.output.with_suffix(".md").write_text("\n".join(lines) + "\n")
    print(json.dumps({key: result[key] for key in ("raw_rows", "summary_cells", "summary_metrics", "total_checks", "failure_count", "elapsed_seconds")}))
    raise SystemExit(bool(result["failure_count"]))


if __name__ == "__main__":
    main()
