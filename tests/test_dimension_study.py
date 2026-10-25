"""Scientific, leakage, reproducibility and output contracts for Experiment 2."""
import csv
from dataclasses import replace
import gzip
import hashlib
import inspect
import json
import subprocess
import sys

import numpy as np
import pytest

from causal_lab import dimension_study as study


@pytest.fixture(scope="module")
def config():
    return study.StudyConfig(dimensions=(2, 3), counts=(12,), repeats=3,
                             calibration_repeats=10, bootstrap=32,
                             seed=101, benchmark_repeats=1)


@pytest.fixture(scope="module")
def result(config):
    return study.run_study(config)


def test_registered_grid_and_independent_sample_counts():
    config = study.StudyConfig()
    config.validate()
    assert config.dimensions == (2, 3, 4)
    assert config.counts == (64, 128, 256)
    assert config.repeats == 200
    assert config.calibration_repeats == 100
    assert config.bootstrap == 2000
    assert config.seed == 20261025
    assert len(config.dimensions)*len(config.counts)*config.repeats == 1800


@pytest.mark.parametrize("changed", [
    {"dimensions": ()}, {"dimensions": (1,)}, {"dimensions": (2, 2)},
    {"dimensions": (2.0,)}, {"dimensions": (True,)},
    {"counts": ()}, {"counts": (1,)}, {"counts": (12, 12)},
    {"counts": (12.5,)}, {"counts": (513,)},
    {"repeats": 1}, {"calibration_repeats": 9}, {"bootstrap": 1},
    {"seed": -1}, {"repeats": True}, {"seed": 1.5},
    {"duration": 0}, {"duration": float("nan")}, {"duration": float("inf")},
    {"benchmark_repeats": 0}, {"max_count": 1024}, {"max_count": 10},
])
def test_invalid_configuration(config, changed):
    with pytest.raises(ValueError):
        replace(config, **changed).validate()


def test_summary_arithmetic_and_explicit_invalid_count():
    stats = study.summarize([1, 2, 3, 4, None], np.random.default_rng(1), 128)
    assert stats["count"] == 5 and stats["valid_count"] == 4 and stats["invalid_count"] == 1
    assert stats["mean"] == 2.5
    assert stats["variance"] == pytest.approx(5/3)
    assert stats["sd"] == pytest.approx(np.sqrt(5/3))
    assert stats["se"] == pytest.approx(np.sqrt(5/12))
    assert 1 <= stats["ci_low"] <= stats["ci_high"] <= 4
    undefined = study.summarize([None, None], np.random.default_rng(1), 32)
    assert undefined["valid_count"] == 0 and undefined["mean"] is None
    singleton = study.summarize([1], np.random.default_rng(1), 32)
    assert singleton["mean"] == 1 and singleton["ci_low"] is None and singleton["se"] is None


def test_binary_wilson_preserves_uncertainty_at_perfect_observed_accuracy():
    stats = study.summarize([1]*200, np.random.default_rng(2), 128, binary=True)
    assert stats["ci_low"] == stats["ci_high"] == 1
    assert stats["wilson_low"] == pytest.approx(0.9811546736227335)
    assert stats["wilson_high"] == 1
    low, high = study.wilson_interval(0, 200)
    assert low == 0 and high > 0
    with pytest.raises(ValueError):
        study.wilson_interval(2, 1)
    with pytest.raises(ValueError):
        study.summarize([0, 2], np.random.default_rng(2), 32, binary=True)


@pytest.mark.parametrize("value,label", [(None,"unclassified"), (1,"unclassified"),
    (10,"unclassified"), (1.5,"2"), (2.5,"2"), (2.51,"3"), (4.5,"4"), (4.51,"unclassified")])
def test_dimension_classification_is_bounded_not_clamped(value, label):
    assert study.classify_dimension(value) == label


def test_rng_purpose_and_repeat_isolation():
    def values(**changes):
        arguments = dict(seed=15, dimension=3, count=64, repeat=0, stream="primary")
        arguments.update(changes)
        return study.rng_for(**arguments).integers(2**31, size=12)
    np.testing.assert_array_equal(values(), values())
    assert not np.array_equal(values(), values(stream="calibration"))
    assert not np.array_equal(values(), values(repeat=1))


def test_estimator_and_features_receive_only_order(monkeypatch, config):
    original_estimator, original_features = study.estimate_dimension, study.order_observables
    seen = []
    def estimator(order):
        assert isinstance(order, np.ndarray) and order.ndim == 2
        seen.append("estimate")
        return original_estimator(order)
    def features(order, *, max_count):
        assert isinstance(order, np.ndarray) and order.ndim == 2
        seen.append("features")
        return original_features(order, max_count=max_count)
    monkeypatch.setattr(study, "estimate_dimension", estimator)
    monkeypatch.setattr(study, "order_observables", features)
    study._measure_order(np.array([[0, 1], [0, 0]], dtype=bool), config)
    assert seen == ["estimate", "features"]
    assert "dimension" not in inspect.signature(study.estimate_dimension).parameters


def test_holdout_never_changes_calibration_or_adversary_fit(config, result):
    altered = study.run_study(replace(config, repeats=5, bootstrap=64,
                                     dimensions=tuple(reversed(config.dimensions))))
    assert altered["calibration"] == result["calibration"]
    assert altered["calibration_model"] == result["calibration_model"]
    by_id = {r["sample_id"]: r for r in altered["raw"]}
    assert all(by_id[r["sample_id"]] == r for r in result["raw"])
    calibration_ids = {r["sample_id"] for r in result["calibration"]}
    assert calibration_ids.isdisjoint({r["sample_id"] for r in result["raw"]})
    for model in result["calibration_model"]["models"].values():
        assert model["fit_repeats_per_dimension"] == 5
        assert model["threshold_repeats_per_dimension"] == 5
        assert model["threshold_count"] == 10


def test_raw_summary_and_histograms_reconcile(config, result):
    assert len(result["calibration"]) == 20
    assert sum(r["family"] == "genuine" for r in result["raw"]) == 6
    assert sum(r["family"] == "matched_bipartite" for r in result["raw"]) == 6
    assert len(result["raw"]) == 20
    records = {r["sample_id"]: r for r in result["raw"]+result["calibration"]}
    assert len(records) == 40
    for histogram in result["interval_histograms"]:
        raw = records[histogram["sample_id"]]
        assert len(histogram["interval_histogram"]) == raw["count"]-1
        assert sum(histogram["interval_histogram"]) == raw["relations"]
        assert histogram["interval_histogram"][0] == raw["link_count"]
    for summary in result["summary"]:
        rows = [r for r in result["raw"] if study._group_key(r) ==
                (summary["family"], summary["dimension_label"] or 0, summary["count"])]
        assert summary["repeats"] == len(rows)
        assert summary["ordering_fraction_mean"] == pytest.approx(np.mean([r["ordering_fraction"] for r in rows]))
        valid = [r["estimated_dimension"] for r in rows if r["estimated_dimension"] is not None]
        assert summary["estimated_dimension_valid_count"] == len(valid)
        assert summary["invalid_estimates"] == len(rows)-len(valid)
        if valid:
            assert summary["estimated_dimension_mean"] == pytest.approx(np.mean(valid))
        if summary["dimension_label"]:
            expected = np.mean([r["classification"] == str(summary["dimension_label"]) for r in rows])
            assert summary["classification_accuracy_mean"] == pytest.approx(expected)


def test_antichain_failure_preserved_and_not_imputed(result):
    anti = next(r for r in result["raw"] if r["family"] == "antichain")
    assert anti["estimate_status"] == "out_of_domain"
    assert anti["estimated_dimension"] is None
    assert anti["classification"] == "unclassified"
    assert anti["joint_score"] is None and not anti["joint_accepted"]
    assert anti["joint_rejection_reason"] == "undefined conditional interval features"
    summary = next(s for s in result["summary"] if s["family"] == "antichain")
    assert summary["invalid_estimates"] == 1
    assert summary["estimated_dimension_mean"] is None
    assert summary["ordering_fraction_se"] is None
    assert summary["joint_accepted_wilson_low"] is None
    assert summary["r_accepted_wilson_high"] is None


def test_counterexample_and_confusion_account_for_every_order(result):
    example = result["diagnostics"]["indistinguishable_example"]
    assert example["first_order"] != example["second_order"]
    for dimension in (2, 3):
        rows = [r for r in result["confusion"] if r["true_dimension"] == dimension]
        assert sum(r["samples"] for r in rows) == 3
        assert sum(r["fraction"] for r in rows) == pytest.approx(1)


def test_scientific_digest_excludes_nondeterministic_benchmarks(result):
    content = {name: result[name] for name in ("calibration", "calibration_model", "raw", "interval_histograms", "summary", "diagnostics", "confusion")}
    encoded = json.dumps(content, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    assert hashlib.sha256(encoded).hexdigest() == result["metadata"]["scientific_digest"]


def test_cli_outputs_complete_finite_and_hashed(tmp_path):
    subprocess.run([sys.executable, "-m", "causal_lab.dimension_study",
                    "--dimensions", "2", "3", "--counts", "12", "--repeats", "3",
                    "--calibration-repeats", "10", "--bootstrap", "32", "--seed", "101",
                    "--benchmark-repeats", "1", "--out", str(tmp_path)],
                   check=True, capture_output=True, text=True, timeout=60)
    for name in ("raw", "calibration", "summary", "confusion", "benchmarks"):
        with (tmp_path/f"{name}.csv").open() as stream:
            assert list(csv.DictReader(stream))
    with gzip.open(tmp_path/"interval_histograms.csv.gz", "rt") as stream:
        assert len(list(csv.DictReader(stream))) == 40
    for name in ("metadata", "summary", "calibration_model", "confusion", "diagnostics"):
        content = json.loads((tmp_path/f"{name}.json").read_text())
        json.dumps(content, allow_nan=False)
    for name in ("ordering_fraction", "dimension_recovery", "bias_vs_count", "confusion", "adversaries", "resources"):
        assert (tmp_path/f"{name}.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    metadata = json.loads((tmp_path/"metadata.json").read_text())
    for name, digest in metadata["artifact_sha256"].items():
        assert hashlib.sha256((tmp_path/name).read_bytes()).hexdigest() == digest
