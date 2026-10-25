"""End-to-end protocol, split and archive contracts for Experiment 3."""
from dataclasses import replace
import gzip
import hashlib
import json
import subprocess
import sys

import numpy as np
import pytest

from causal_lab import adversarial_study as study
from causal_lab.adversarial_artifacts import scientific_digest, write_outputs
from causal_lab.adversarial_detectors import evaluate_detectors


@pytest.fixture(scope="module")
def config():
    return study.StudyConfig(dimensions=(2, 3), counts=(12,), fits=2,
                             calibration=10, development=10, validation=12,
                             repeats=2, search_steps=4, bootstrap=32, seed=101)


@pytest.fixture(scope="module")
def result(config):
    return study.run_study(config)


def test_registered_grid_and_count():
    c = study.StudyConfig()
    c.validate()
    assert (c.dimensions, c.counts, c.fits, c.repeats, c.search_steps) == ((2, 3, 4), (64, 128, 256), 3, 200, 64)
    training = c.fits*len(c.counts)*len(c.dimensions)*(c.calibration+c.development+c.validation)
    test = c.fits*len(c.counts)*(len(c.dimensions)*c.repeats*5+8*c.repeats+2)
    assert training+test == 52218
    assert c.fits*len(c.counts)*len(c.dimensions)*c.repeats*c.search_steps == 345600


@pytest.mark.parametrize("changes", [
    {"counts": ()}, {"counts": (7,)}, {"counts": (257,)}, {"counts": (12, 12)},
    {"counts": (12.,)}, {"dimensions": (True,)}, {"dimensions": (5,)},
    {"dimensions": ()}, {"fits": 0}, {"fits": True}, {"seed": -1},
    {"workers": 4}, {"repeats": 1}, {"calibration": 1}, {"validation": 1},
    {"development": 1}, {"search_steps": 3}, {"bootstrap": 1},
])
def test_invalid_config(config, changes):
    with pytest.raises(ValueError):
        replace(config, **changes).validate()


def test_canonical_key_stream_partition_and_traversal():
    arguments = (15, 1, "calibration", "genuine", 3, 64, 7)
    expected = hashlib.sha256(b'["adversarial-v1",15,1,"calibration","genuine",3,64,7,null]').hexdigest()
    assert study.identity(*arguments) == expected
    draws = study.rng_for(*arguments).integers(2**30, size=20)
    np.testing.assert_array_equal(draws, study.rng_for(*arguments).integers(2**30, size=20))
    for index, value in ((0, 16), (1, 2), (2, "validation"), (3, "search"), (4, 2), (5, 128), (6, 8)):
        altered = list(arguments)
        altered[index] = value
        assert not np.array_equal(draws, study.rng_for(*altered).integers(2**30, size=20))


def test_counts_splits_and_search_pairing(result):
    raw = result["raw"]
    assert len(raw) == 204
    assert len({r["sample_id"] for r in raw}) == len(raw)
    assert len(result["searches"]) == 8
    donors = {r["sample_id"] for r in raw if r["phase"] == "development"}
    for search in result["searches"]:
        assert search["target_sample_id"] in donors
        pair = [r for r in raw if r.get("search_id") == search["search_id"]]
        assert {r["family"] for r in pair} == {"height_matched", "multi_matched"}
        assert all(r["longest_chain"] == search["target_height"] for r in pair)
        assert search["evaluations"] == 4
        assert search["best_objective"] <= search["initial_objective"]
    for row in raw:
        assert sum(row["interval_histogram"]) == row["relations"]
        assert row["interval_histogram"][0] == row["link_count"]
        assert sum(row["abundance_vector"]) == pytest.approx(1)


def test_decisions_match_api_and_truth_is_not_an_inference_feature(result):
    for row in result["raw"]:
        if row["phase"] != "test":
            continue
        model = result["models"][str(row["fit"])][str(row["count"])]
        for target in study.TARGETS:
            decisions = evaluate_detectors(row, model, target=target)
            poisoned = dict(row, true_dimension=999, dimension_label=-100, family="genuine")
            assert decisions == evaluate_detectors(poisoned, model, target=target)
            assert row["accepted"][str(target)] == [decisions[d]["accepted"] for d in study.DETECTORS]


def test_holdout_count_cannot_change_calibration_or_old_samples(config, result):
    extra = study.run_study(replace(config, repeats=3, dimensions=(3, 2)))
    assert result["models"] == extra["models"]
    by_id = {r["sample_id"]: r for r in extra["raw"]}
    assert all(r == by_id[r["sample_id"]] for r in result["raw"])


def test_per_fit_summary_reconciles_and_exact_has_no_wilson(result):
    for summary in result["summary"]:
        i = study.DETECTORS.index(summary["detector"])
        for fit in summary["per_fit"]:
            rows = [r for r in result["raw"] if r["phase"] == "test" and r["fit"] == fit["fit"]
                    and study.group_key(r) == (summary["family"], summary["dimension_label"], summary["count"])]
            assert len(rows) == fit["n"]
            assert sum(r["accepted"][str(summary["target"])][i] for r in rows) == fit["accepted"]
            if summary["family"] in study.EXACT:
                assert fit["wilson_low"] is fit["wilson_high"] is None
    assert sum(r["orders"] for r in result["classification"]) == sum(r["phase"] == "test" for r in result["raw"])


def test_scientific_reproduction_and_workers(config, result):
    repeated = study.run_study(replace(config, workers=2))
    assert scientific_digest(repeated) == scientific_digest(result)


def test_archive_json_finite_gzip_reproducible_and_six_figures(tmp_path, result):
    metadata = write_outputs(result, tmp_path/"one")
    again = write_outputs(result, tmp_path/"two")
    assert metadata["scientific_sha256"] == again["scientific_sha256"] == scientific_digest(result)
    assert metadata["recorded_orders"] == len(result["raw"])
    assert len(list((tmp_path/"one").glob("*.png"))) == 6
    for filename, key in (("raw.jsonl.gz", "raw"), ("searches.jsonl.gz", "searches"), ("paired.jsonl.gz", "paired")):
        first = tmp_path/"one"/filename
        assert first.read_bytes() == (tmp_path/"two"/filename).read_bytes()
        with gzip.open(first, "rt") as stream:
            assert [json.loads(line) for line in stream] == result[key]
    for p in (tmp_path/"one").glob("*.png"):
        assert p.read_bytes() == (tmp_path/"two"/p.name).read_bytes()
        assert p.stat().st_size > 1000
    assert json.loads((tmp_path/"one"/"exact_counterexamples.json").read_text())["nondual"]


def test_cli_end_to_end(tmp_path):
    command = [sys.executable, "-m", "causal_lab.adversarial_study", "--dimensions", "2", "3",
               "--counts", "12", "--fits", "2", "--calibration", "10", "--development", "10",
               "--validation", "12", "--repeats", "2", "--search-steps", "4", "--bootstrap", "32",
               "--seed", "101", "--out", str(tmp_path)]
    process = subprocess.run(command, capture_output=True, text=True, check=True)
    assert "Completed 204 recorded orders and 8 searches" in process.stdout
    assert json.loads((tmp_path/"metadata.json").read_text())["candidate_evaluations"] == 32
