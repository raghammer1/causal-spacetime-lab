"""Archive integrity tests use fabricated values, not simulated outcomes."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json

import pytest

from causal_lab import growth_artifacts as artifacts


def _screen(family="percolation", parameter=.01):
    return {"entry_count": 8, "families": [{
        "family": family, "parameter": parameter, "status": "inconclusive",
        "entries": [{"name": "level_128", "estimate": None, "band": None,
                     "status": "insufficient_information", "margin": .005}],
    }]}


def _wrapper():
    return {"growth": _screen(), "controls": [_screen("minkowski", 2)],
            # Even a similarly named nested field must not turn an analytic
            # endpoint record into a stochastic confidence-screen family.
            "endpoints": [{"family": "percolation", "parameter": 0.,
                           "analytic": True, "nested": {"families": []}}]}


def _inputs(out):
    rows = [{"sample_id": "fabricated", "n22": 0, "missing": None}]
    histories = [{"history_id": "fabricated", "primitive": "00"}]
    refs = [{"dimension": 2, "fit": 0, "expectation": 1 / 24}]
    artifacts.write_gzip(out / "raw" / "one.jsonl.gz", rows)
    return [], _wrapper(), refs, histories, ["raw/one.jsonl.gz"]


def test_canonical_gzip_is_filename_and_time_independent(tmp_path):
    rows = [{"z": None, "a": [1, "μ"]}, {"a": -0.25}]
    first, second = tmp_path / "first.gz", tmp_path / "second.gz"
    artifacts.write_gzip(first, rows)
    artifacts.write_gzip(second, rows)
    assert first.read_bytes() == second.read_bytes()
    header = first.read_bytes()[:10]
    assert header[3] & 8 == 0  # No optional filename field.
    assert header[4:8] == b"\0" * 4
    with gzip.open(first, "rt", encoding="utf-8") as stream:
        assert [json.loads(line) for line in stream] == rows
    assert artifacts.canonical({"b": 2, "a": 1}) == artifacts.canonical({"a": 1, "b": 2})
    with pytest.raises(ValueError):
        artifacts.canonical({"undefined": float("nan")})


def test_csv_has_lf_and_preserves_missing_and_nested_fields(tmp_path):
    path = tmp_path / "table.csv"
    artifacts._csv(path, [{"estimate": None, "support": {"positive": 0}, "ci95": [0., 1.]}])
    assert b"\r" not in path.read_bytes()
    with path.open(newline="") as stream:
        row = next(csv.DictReader(stream))
    assert row["estimate"] == ""
    assert json.loads(row["support"]) == {"positive": 0}
    assert json.loads(row["ci95"]) == [0., 1.]


def test_scientific_digest_accepts_streamed_history_records(tmp_path):
    summaries, primary, references, histories, raw = _inputs(tmp_path)
    artifacts.write_gzip(tmp_path / "histories.jsonl.gz", histories)
    expected = artifacts.scientific_digest(tmp_path, summaries, primary, references, histories, raw)
    assert artifacts.scientific_digest(tmp_path, summaries, primary, references,
                                       "histories.jsonl.gz", raw) == expected


@pytest.mark.parametrize("component", ["summary", "primary", "reference", "history", "raw"])
def test_scientific_digest_detects_each_scientific_component(tmp_path, component):
    summaries, primary, references, histories, raw = _inputs(tmp_path)
    before = artifacts.scientific_digest(tmp_path, summaries, primary, references, histories, raw)
    if component == "summary":
        summaries.append({"changed": True})
    elif component == "primary":
        primary["growth"]["families"][0]["status"] = "finite_signature_failure"
    elif component == "reference":
        references[0]["expectation"] = .1
    elif component == "history":
        histories[0]["primitive"] = "01"
    else:
        artifacts.write_gzip(tmp_path / raw[0], [{"sample_id": "fabricated", "n22": 1}])
    after = artifacts.scientific_digest(tmp_path, summaries, primary, references, histories, raw)
    assert after != before


def test_screen_wrapper_keeps_endpoints_out_of_stochastic_classification():
    wrapper = _wrapper()
    assert [name for name, _ in artifacts._screen_reports(wrapper)] == ["growth", "controls/0/screen"]
    rows = artifacts._tables([], wrapper)["primary"]
    assert len(rows) == 2
    assert {(row["family"], row["parameter"]) for row in rows} == {
        ("percolation", .01), ("minkowski", 2)}
    assert all(row["estimate"] is None for row in rows)
    assert not any(row["parameter"] == 0 for row in rows)


def test_writer_manifest_and_digest_exclude_runtime_and_rendering(tmp_path, monkeypatch):
    summaries, primary, references, histories, raw = _inputs(tmp_path)
    labels = []

    def fake_figures(output_dir, _summaries, _primary, _trajectories, *, run_label=""):
        labels.append(run_label)
        (output_dir / "figure.png").write_bytes(b"fabricated rendering" + str(len(labels)).encode())
        return ["figure.png"]

    monkeypatch.setattr(artifacts, "make_figures", fake_figures)
    inputs = (tmp_path, summaries, primary, references, histories, raw)
    first = artifacts.write_artifacts(*inputs, {"run_kind": "smoke", "elapsed_seconds": 1.}, [])
    first_figure_hash = first["artifact_sha256"]["figure.png"]
    second = artifacts.write_artifacts(*inputs, {"run_kind": "smoke", "elapsed_seconds": 999.}, [])
    assert first["scientific_sha256"] == second["scientific_sha256"]
    assert first_figure_hash != second["artifact_sha256"]["figure.png"]
    assert all("SMOKE CHECK" in label for label in labels)
    assert second["history_records"] == 1
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    names = {row["name"] for row in manifest["artifacts"]}
    assert names == {str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*")
                     if path.is_file() and path.name != "manifest.json"}
    for row in manifest["artifacts"]:
        data = (tmp_path / row["name"]).read_bytes()
        assert row["bytes"] == len(data)
        assert row["sha256"] == hashlib.sha256(data).hexdigest()
    assert json.loads((tmp_path / "primary.json").read_text()) == primary
    assert all(b"\r" not in path.read_bytes() for path in tmp_path.glob("*.csv"))


def test_writer_stream_inputs_have_same_scientific_digest(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts, "make_figures", lambda *args, **kwargs: [])
    summaries, primary, references, histories, raw = _inputs(tmp_path)
    first = artifacts.write_artifacts(tmp_path, summaries, primary, references, histories, raw, {}, [])
    second = artifacts.write_artifacts(tmp_path, summaries, primary, "references.json.gz",
                                       "histories.jsonl.gz", raw, {}, [])
    assert first["scientific_sha256"] == second["scientific_sha256"]
    assert first["history_records"] == second["history_records"] == 1


def test_missing_duplicate_or_external_raw_paths_are_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts, "make_figures", lambda *args, **kwargs: [])
    summaries, primary, references, histories, raw = _inputs(tmp_path)
    for invalid in ([raw[0], raw[0]], ["missing.gz"], ["../external.gz"], [str(tmp_path / raw[0])]):
        with pytest.raises(ValueError):
            artifacts.write_artifacts(tmp_path, summaries, primary, references, histories,
                                      invalid, {}, [])


def test_smoke_figure_caption_uses_actual_screen_size(tmp_path, monkeypatch):
    captured = []

    def capture(fig, out, name, run_label=""):
        captured.extend(text.get_text() for text in fig.texts)
        artifacts.plt.close(fig)
        return name

    monkeypatch.setattr(artifacts, "_save", capture)
    artifacts._primary_figure(tmp_path, _wrapper(), "SMOKE CHECK")
    assert any("simultaneous 8-entry bands" in text for text in captured)
    assert not any("48-entry" in text for text in captured)


@pytest.mark.parametrize("overrun", [None, "wall", "memory"])
def test_postwrite_resource_envelope_refreshes_metadata_manifest(tmp_path, monkeypatch, overrun):
    """Publication overhead must be accounted for without changing science."""
    from causal_lab import growth_study as study

    state = {"clock": 0., "root_rss": 100, "writer_digest": None, "initial_metadata_hash": None}
    cfg = study.GrowthConfig(seed=101, reference_seed=102, workers=1, batches=1,
                             histories=1, bootstrap_draws=8, motif_draws=8,
                             wall_seconds=30. if overrun == "wall" else 60., smoke=True)
    monkeypatch.setattr(study.time, "monotonic", lambda: state["clock"])
    monkeypatch.setattr(study, "_peak_bytes", lambda who=study.resource.RUSAGE_SELF:
                        200 if who == study.resource.RUSAGE_CHILDREN else state["root_rss"])
    monkeypatch.setattr(study, "_provenance", lambda: {"fabricated_test": True})
    monkeypatch.setattr(study, "_references", lambda config: [])
    monkeypatch.setattr(study, "families", lambda config: [("percolation", .01)])
    monkeypatch.setattr(study, "summarize_primary", lambda *args, **kwargs: _screen())

    def fake_family(config, family, parameter, references, output, deadline):
        state["clock"] = 2.
        artifacts.write_gzip(output / "raw" / "test.jsonl.gz", [{"fabricated": True}])
        return {"family": family, "parameter": parameter, "bundle": {},
                "summary": {"family": family, "parameter": parameter, "history_count": 1},
                "histories": [{"history_id": "fabricated"}], "trajectories": [],
                "raw_file": "raw/test.jsonl.gz", "row_count": 1,
                "performance": {"peak_rss_bytes": 90, "pid": 12345}}

    monkeypatch.setattr(study, "_family_job", fake_family)
    monkeypatch.setattr(study, "one_history", lambda *args, **kwargs:
                        ([{"stage": "prefix", "fabricated_endpoint": True}],
                         {"history_id": "fabricated_endpoint"}))
    monkeypatch.setattr(artifacts, "make_figures", lambda *args, **kwargs: [])
    real_writer = artifacts.write_artifacts

    def expensive_writer(*args, **kwargs):
        report = real_writer(*args, **kwargs)
        state["writer_digest"] = report["scientific_sha256"]
        state["initial_metadata_hash"] = hashlib.sha256((tmp_path / "metadata.json").read_bytes()).hexdigest()
        state["clock"] = 40.
        state["root_rss"] = 5 * 1024 ** 3 if overrun == "memory" else 350
        return report

    monkeypatch.setattr(artifacts, "write_artifacts", expensive_writer)
    if overrun:
        with pytest.raises(RuntimeError, match="full execution resource budget exceeded"):
            study.run_study(cfg, tmp_path)
        assert (tmp_path / "RESOURCE_FAILURE.json").is_file()
    else:
        study.run_study(cfg, tmp_path)
        assert not (tmp_path / "RESOURCE_FAILURE.json").exists()
    data = (tmp_path / "metadata.json").read_bytes()
    metadata = json.loads(data)
    performance = metadata["performance"]
    assert performance["compute_seconds"] == 2.
    assert performance["total_seconds"] == 40.
    assert performance["artifact_seconds"] == 38.
    assert performance["root_peak_rss_bytes"] == state["root_rss"]
    assert performance["conservative_aggregate_peak_rss_bytes"] == state["root_rss"] + 200
    assert performance["within_total_wall_budget"] == (overrun != "wall")
    assert performance["within_memory_budget"] == (overrun != "memory")
    assert metadata["scientific_sha256"] == state["writer_digest"]
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    entry = next(row for row in manifest["artifacts"] if row["name"] == "metadata.json")
    assert entry["sha256"] == hashlib.sha256(data).hexdigest()
    assert entry["sha256"] != state["initial_metadata_hash"]
    assert entry["bytes"] == len(data)
    assert manifest["scientific_sha256"] == state["writer_digest"]
