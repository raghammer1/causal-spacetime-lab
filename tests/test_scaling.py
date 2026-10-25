"""Regression checks for the study's scientific and reproducibility contract."""

import csv
from dataclasses import replace
import hashlib
import json
import subprocess
import sys

import numpy as np
import pytest

from causal_lab import CausalDiamond, causal_order, longest_chain_fast, sprinkle
from causal_lab import scaling


@pytest.fixture(scope="module")
def small_config():
    return scaling.StudyConfig(
        densities=(2.0, 8.0), durations=(0.5, 1.0), repeats=8,
        seed=20261025, bootstrap=32, order_repeats=2,
        order_max_count=32, benchmark_repeats=1,
    )


@pytest.fixture(scope="module")
def small_result(small_config):
    return scaling.run_study(small_config)


def test_primary_grid_matches_registered_protocol():
    config = scaling.StudyConfig()
    config.validate()
    np.testing.assert_array_equal(config.densities, np.geomspace(32.0, 8192.0, 7))
    assert config.durations == (0.5, 1.0, 2.0)
    assert config.repeats == 200
    assert config.bootstrap == 2000
    assert config.seed == 20261025
    assert config.order_repeats == 20
    assert config.order_max_count == 256
    assert len(config.densities) * len(config.durations) * config.repeats == 4200


@pytest.mark.parametrize("change", [
    {"densities": ()}, {"durations": ()},
    {"densities": (0.0,)}, {"densities": (-1.0,)},
    {"densities": (float("nan"),)}, {"densities": (float("inf"),)},
    {"durations": (0.0,)}, {"durations": (-1.0,)},
    {"durations": (float("nan"),)}, {"durations": (float("inf"),)},
    {"densities": (2.0, 2.0)}, {"durations": (1.0, 1.0)},
    {"repeats": 1}, {"repeats": 2.5}, {"bootstrap": 1},
    {"seed": -1}, {"seed": True},
    {"order_repeats": -1}, {"order_repeats": 9},
    {"order_max_count": -1}, {"benchmark_repeats": 0},
])
def test_invalid_configuration_rejected(small_config, change):
    with pytest.raises(ValueError):
        replace(small_config, **change).validate()


def test_summary_matches_hand_calculated_statistics():
    result = scaling.summarize(
        np.array([1.0, 2.0, 3.0, 4.0]), 2.0, np.random.default_rng(7), 128,
    )
    assert result["mean_estimate"] == pytest.approx(2.5)
    assert result["standard_deviation"] == pytest.approx(np.sqrt(5.0 / 3.0))
    assert result["standard_error"] == pytest.approx(np.sqrt(5.0 / 12.0))
    assert result["bias"] == pytest.approx(0.5)
    assert result["normalized_bias"] == pytest.approx(0.25)
    assert 1.0 <= result["ci_low"] <= result["ci_high"] <= 4.0
    assert result["bias_ci_low"] == pytest.approx(result["ci_low"] / 2.0 - 1.0)
    assert result["bias_ci_high"] == pytest.approx(result["ci_high"] / 2.0 - 1.0)


def test_constant_sample_has_zero_sampling_spread():
    result = scaling.summarize(np.full(8, 4.0), 2.0, np.random.default_rng(8), 32)
    assert result["standard_deviation"] == 0.0
    assert result["standard_error"] == 0.0
    assert result["ci_low"] == result["ci_high"] == 4.0
    assert result["bias_ci_low"] == result["bias_ci_high"] == 1.0


@pytest.mark.parametrize("values", [[], [1.0], [1.0, np.nan], [1.0, np.inf], [[1.0, 2.0]]])
def test_summary_rejects_undefined_samples(values):
    with pytest.raises(ValueError):
        scaling.summarize(values, 1.0, np.random.default_rng(8), 32)


def test_rng_keys_are_stable_and_separate_purposes():
    def draw(duration=1.0, density=8.0, repeat=2, stream="sample"):
        return scaling.rng_for(17, duration, density, repeat, stream).integers(
            0, 2**31, size=16,
        )

    np.testing.assert_array_equal(draw(), draw(duration=1, density=8))
    for changed in (draw(repeat=3), draw(stream="bootstrap"), draw(density=16.0)):
        assert not np.array_equal(draw(), changed)


def _raw_by_id(result):
    rows = result["raw"]
    keyed = {row["sample_id"]: row for row in rows}
    assert len(keyed) == len(rows)
    return keyed


def test_physical_samples_do_not_depend_on_grid_order_or_bootstrap(
    small_config, small_result,
):
    reordered = scaling.run_study(replace(
        small_config, densities=tuple(reversed(small_config.densities)),
        durations=tuple(reversed(small_config.durations)), bootstrap=64,
    ))
    assert _raw_by_id(reordered) == _raw_by_id(small_result)
    subset = scaling.run_study(replace(small_config, densities=(8.0,), durations=(1.0,)))
    expected = {
        key: row for key, row in _raw_by_id(small_result).items()
        if row["density"] == 8.0 and row["duration"] == 1.0
    }
    assert _raw_by_id(subset) == expected


def test_scientific_digest_matches_records_and_ignores_timings(small_config, small_result):
    repeated = scaling.run_study(small_config)
    assert repeated["metadata"]["scientific_digest"] == small_result["metadata"]["scientific_digest"]
    content = {name: small_result[name] for name in ("raw", "summary", "agreement", "diagnostics")}
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert hashlib.sha256(canonical.encode()).hexdigest() == small_result["metadata"]["scientific_digest"]


def test_raw_samples_reconcile_with_every_summary_and_control(small_config, small_result):
    assert len(small_result["raw"]) == 4 * small_config.repeats
    assert len(small_result["summary"]) == 4 * 3
    fields = {
        "sprinkled": "chain_length",
        "total_order": "total_order_length",
        "antichain": "antichain_length",
    }
    empty_seen = False
    for row in small_result["raw"]:
        n = row["event_count"]
        empty_seen |= n == 0
        assert row["total_order_length"] == n
        assert row["antichain_length"] == int(n > 0)
        assert 0 <= row["chain_length"] <= n
        assert row["expected_count"] == pytest.approx(row["density"] * row["duration"]**2 / 2)
    assert empty_seen, "The low-count fixture must exercise empty sprinklings."
    for row in small_result["summary"]:
        raw = [r for r in small_result["raw"]
               if r["density"] == row["density"] and r["duration"] == row["duration"]]
        lengths = np.array([r[fields[row["model"]]] for r in raw])
        estimates = lengths / np.sqrt(2.0 * row["density"])
        assert row["repeats"] == len(raw) == small_config.repeats
        assert row["chain_mean"] == pytest.approx(lengths.mean())
        assert row["mean_estimate"] == pytest.approx(estimates.mean())
        assert row["standard_deviation"] == pytest.approx(estimates.std(ddof=1))
        assert row["standard_error"] == pytest.approx(estimates.std(ddof=1) / np.sqrt(len(raw)))
        assert row["normalized_bias"] == pytest.approx(estimates.mean() / row["duration"] - 1.0)
        if row["model"] == "total_order":
            assert row["analytic_chain_reference"] == pytest.approx(row["expected_count"])
        elif row["model"] == "antichain":
            assert row["analytic_chain_reference"] == pytest.approx(-np.expm1(-row["expected_count"]))


def test_small_cases_agree_and_identify_actual_checked_samples(small_config, small_result):
    checked = small_result["agreement"]
    assert len(checked) == 4 * small_config.order_repeats
    raw = _raw_by_id(small_result)
    for row in checked:
        assert row["agree"] and row["chain_valid"]
        assert row["fast_length"] == row["order_length"] == raw[row["sample_id"]]["chain_length"]
        assert row["repeat"] < small_config.order_repeats
        assert row["event_count"] <= small_config.order_max_count
        if row["event_count"] < 2:
            assert row["pair_fraction"] is None


def test_matrix_cap_skips_only_crosschecks_and_retains_physical_draws(small_config, small_result):
    capped = scaling.run_study(replace(small_config, order_max_count=0))
    assert _raw_by_id(capped) == _raw_by_id(small_result)
    expected_ids = {
        row["sample_id"] for row in capped["raw"]
        if row["repeat"] < small_config.order_repeats and row["event_count"] == 0
    }
    assert {row["sample_id"] for row in capped["agreement"]} == expected_ids
    accounting = capped["diagnostics"]["agreement_summary"]
    assert accounting["checked_primary_trials"] == len(expected_ids)
    assert accounting["candidate_primary_trials"] == 4 * small_config.order_repeats
    assert accounting["skipped_above_count_limit"] == 4 * small_config.order_repeats - len(expected_ids)
    assert all(row["event_count"] == 0 for row in capped["benchmarks"]
               if row["phase"] in ("order_matrix", "order_only"))


def test_disagreement_aborts_study(small_config, monkeypatch):
    diamond = CausalDiamond(np.array([0.1, 0.2]), np.array([0.1, 0.2]), 1.0, 2.0)
    monkeypatch.setattr(scaling, "sprinkle", lambda *args, **kwargs: diamond)
    monkeypatch.setattr(scaling, "longest_chain_order", lambda order: [])
    with pytest.raises(RuntimeError):
        scaling.run_study(replace(small_config, densities=(2.0,), durations=(1.0,)))


def test_equal_length_noncausal_chain_also_aborts_study(small_config, monkeypatch):
    diamond = CausalDiamond(np.array([0.1, 0.2]), np.array([0.1, 0.2]), 1.0, 2.0)
    monkeypatch.setattr(scaling, "sprinkle", lambda *args, **kwargs: diamond)
    monkeypatch.setattr(scaling, "longest_chain_fast", lambda *args: [1, 0])
    with pytest.raises(RuntimeError):
        scaling.run_study(replace(small_config, densities=(2.0,), durations=(1.0,)))


def test_coordinate_rescaling_preserves_order_and_relative_reconstruction():
    # This is an exact same-sample transformation, not an independent replication.
    a = sprinkle(1.0, 80.0, np.random.default_rng(61))
    b = sprinkle(2.0, 20.0, np.random.default_rng(61))
    assert a.count == b.count
    np.testing.assert_array_equal(b.u, 2.0 * a.u)
    np.testing.assert_array_equal(b.v, 2.0 * a.v)
    np.testing.assert_array_equal(causal_order(a), causal_order(b))
    assert longest_chain_fast(a) == longest_chain_fast(b)


def test_cli_writes_machine_readable_results_and_all_figures(tmp_path):
    subprocess.run([
        sys.executable, "-m", "causal_lab.scaling", "--densities", "2", "8",
        "--durations", "0.5", "1", "--repeats", "4", "--bootstrap", "16",
        "--order-repeats", "2", "--order-max-count", "32",
        "--benchmark-repeats", "1", "--out", str(tmp_path),
    ], check=True, capture_output=True, text=True, timeout=60)
    for name in ("raw", "summary", "agreement", "benchmarks"):
        with (tmp_path / f"{name}.csv").open() as stream:
            assert list(csv.DictReader(stream)), f"{name} table must contain data"
    for name in ("summary", "metadata", "diagnostics"):
        content = json.loads((tmp_path / f"{name}.json").read_text())
        # The JSON output must not contain NaN/Infinity, including optional diagnostics.
        json.dumps(content, allow_nan=False)
    metadata = json.loads((tmp_path / "metadata.json").read_text())
    for name, expected in metadata["artifact_sha256"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == expected
    assert "benchmarks.csv" in metadata["nondeterministic_artifacts"]
    for name in ("reconstruction", "bias_scaling", "chain_controls", "benchmarks"):
        assert (tmp_path / f"{name}.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
