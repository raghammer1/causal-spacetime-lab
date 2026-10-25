"""Small independent-audit fixtures; no primary study data are generated here."""
import gzip
import hashlib
import json
import math

import numpy as np
import pytest

from causal_lab.growth import thin_order
from causal_lab.growth_artifacts import scientific_digest, write_gzip
from causal_lab.growth_audit import (
    audit_growth_archive, independent_closure, independent_counts,
    main, reconstruct_history, unpack_order,
)
from causal_lab.growth_controls import (
    MATCHED_EDGE_PROBABILITY, generate_history, order_hash, pack_order,
)
from causal_lab.growth_observables import growth_observables
from causal_lab.growth_random import identity, rng_for
from causal_lab.local_structure import enumerate_unlabeled_posets, motif_counts
from causal_lab.order_observables import total_order


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")


def read_rows(path):
    with gzip.open(path, "rt") as stream:
        return [json.loads(line) for line in stream]


def refresh_manifest(directory):
    metadata = json.loads((directory / "metadata.json").read_text())
    raw_files = metadata["raw_files"]
    digest = scientific_digest(directory, [], {}, [], "histories.jsonl.gz", raw_files)
    metadata["scientific_sha256"] = digest
    metadata["artifact_sha256"] = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                                    for name in [*raw_files, "histories.jsonl.gz", "references.json.gz",
                                                 "summary.json", "primary.json"]}
    write_json(directory / "metadata.json", metadata)
    artifacts = [{"name": name, "bytes": (directory / name).stat().st_size,
                  "sha256": hashlib.sha256((directory / name).read_bytes()).hexdigest()}
                 for name in [*metadata["artifact_sha256"], "metadata.json"]]
    write_json(directory / "manifest.json", {"scientific_sha256": digest, "artifacts": artifacts})


@pytest.fixture
def archive(tmp_path):
    (tmp_path / "raw").mkdir()
    seed, histories, rows = 809, [], []
    families = [("percolation", p) for p in (0., .3, 1.)]
    families += [("minkowski", d) for d in (2, 3, 4)]
    families += [("semiorder", .25), ("matched_bipartite", MATCHED_EDGE_PROBABILITY)]
    for family, parameter in families:
        key = identity(seed, 0, "generation", family, parameter, 0)
        order, evidence = generate_history(family, parameter, 8,
                                          rng_for(seed, 0, "generation", family, parameter, 0))
        history = {"family": family, "parameter": parameter, "batch": 0, "history_number": 0,
                   "history_id": key, "count": 8, "order_sha256": order_hash(order), **evidence}
        histories.append(history)
        thinned, indices = thin_order(order, 4, rng_for(seed, 0, "primary_thinning", family, parameter, 0, 8, 0))
        for matrix, source, replica, retained in ((order[:4, :4], 4, None, None),
                                                  (order, 8, None, None), (thinned, 8, 0, indices)):
            stage = "prefix" if replica is None else "thinned"
            operation_replica = "prefix" if replica is None else replica
            row = {"family": family, "parameter": parameter, "batch": 0, "fit": 0,
                   "history_number": 0, "history_id": key, "stage": stage,
                   "source_count": source, "thinning_rep": replica,
                   "sample_id": identity(seed, 0, "primary_record", family, parameter, 0, source, operation_replica),
                   "order_sha256": order_hash(matrix), **growth_observables(matrix)}
            if retained is not None:
                row["retained_indices"] = retained.tolist()
            row["r"] = row["ordering_fraction"]
            row["motifs"] = motif_counts(matrix, rng_for(seed, 0, "primary_motifs", family,
                                        parameter, 0, source, operation_replica), draws=32)
            rows.append(row)
    write_gzip(tmp_path / "raw/small.jsonl.gz", rows)
    write_gzip(tmp_path / "histories.jsonl.gz", histories)
    write_gzip(tmp_path / "references.json.gz", [], lines=False)
    write_json(tmp_path / "summary.json", [])
    write_json(tmp_path / "primary.json", {})
    write_json(tmp_path / "metadata.json", {"config": {"seed": seed, "motif_draws": 32},
               "raw_files": ["raw/small.jsonl.gz"], "history_records": len(histories), "row_count": len(rows)})
    refresh_manifest(tmp_path)
    return tmp_path


def test_small_archive_all_families_reconstructs_and_replays(archive):
    report = audit_growth_archive(archive)
    assert report["status"] == "passed", report["failures"]
    assert report["history_records"] == report["selected_histories"] == report["regenerated_histories"] == 8
    assert report["raw_records"] == report["selected_raw_records"] == report["independent_count_checks"] == 24
    assert report["regenerated_thinnings"] == 8
    assert report["regenerated_motif_samples"] == 24
    assert report["four_subsets_checked"] == 8 * (1 + math.comb(8, 4) + 1)
    assert report["records_per_history"] == [3]
    assert report["bootstrap_intervals_recomputed"] is False
    json.dumps(report, allow_nan=False)


def test_resealed_wrong_observable_is_rejected_independently(archive):
    path = archive / "raw/small.jsonl.gz"
    rows = read_rows(path)
    rows[0]["n31"] += 1
    write_gzip(path, rows)
    refresh_manifest(archive)  # Passing checksums alone must not pass this audit.
    report = audit_growth_archive(archive)
    assert report["status"] == "failed"
    assert any("independent n22/n31/relation/height mismatch" in item for item in report["failures"])
    assert not any("checksum" in item or "digest" in item for item in report["failures"])


def test_resealed_wrong_growth_metadata_is_rejected(archive):
    path = archive / "histories.jsonl.gz"
    records = read_rows(path)
    records[0]["metadata"]["primitive_edge_count"] += 1
    write_gzip(path, records)
    refresh_manifest(archive)
    report = audit_growth_archive(archive)
    assert report["status"] == "failed"
    assert any("primitive growth metadata mismatch" in item for item in report["failures"])


def test_changed_seed_fails_replay_even_when_checksums_resealed(archive):
    metadata = json.loads((archive / "metadata.json").read_text())
    metadata["config"]["seed"] += 1
    write_json(archive / "metadata.json", metadata)
    refresh_manifest(archive)
    report = audit_growth_archive(archive)
    assert report["status"] == "failed"
    assert any("same-seed" in item for item in report["failures"])
    without_replay = audit_growth_archive(archive, verify_regeneration=False)
    assert without_replay["status"] == "passed", without_replay["failures"]


def test_unsealed_tampering_and_missing_rows_are_detected(archive):
    path = archive / "raw/small.jsonl.gz"
    rows = read_rows(path)
    write_gzip(path, rows[:-1])
    report = audit_growth_archive(archive)
    assert report["status"] == "failed"
    assert any("checksum" in item for item in report["failures"])
    assert "independent scientific digest mismatch" in report["failures"]
    assert "raw record count differs from metadata" in report["failures"]


def test_duplicate_raw_identity_is_rejected(archive):
    path = archive / "raw/small.jsonl.gz"
    rows = read_rows(path)
    rows[1]["sample_id"] = rows[0]["sample_id"]
    write_gzip(path, rows)
    refresh_manifest(archive)
    report = audit_growth_archive(archive)
    assert report["status"] == "failed"
    assert any("duplicate sample_id" in item for item in report["failures"])


def test_missing_archive_and_nonfinite_json_fail_as_machine_readable_reports(tmp_path, archive):
    missing = audit_growth_archive(tmp_path / "missing")
    assert missing["status"] == "failed" and missing["failure_count"] == 1
    (archive / "metadata.json").write_text('{"seed":NaN}')
    nonfinite = audit_growth_archive(archive)
    assert nonfinite["status"] == "failed"
    assert "nonfinite JSON" in nonfinite["failures"][0]


def test_every_small_order_independent_counts_match_tested_production_counts():
    for n in range(6):
        for order in enumerate_unlabeled_posets(n):
            counts = independent_counts(order)
            row = growth_observables(order)
            assert all(row[name] == value for name, value in counts.items())
            np.testing.assert_array_equal(independent_closure(order), order)


def test_packed_matrix_roundtrip_canonical_padding_and_shape():
    order = total_order(3)
    packed = pack_order(order)
    np.testing.assert_array_equal(unpack_order(packed), order)
    invalid = dict(packed, packed_hex=packed["packed_hex"][:-2] + "80")
    with pytest.raises(ValueError, match="padding"):
        unpack_order(invalid)
    for invalid in (dict(packed, shape=[3, 4]), dict(packed, bitorder="big"),
                    dict(packed, shape=[513, 513]), dict(packed, packed_hex="00")):
        with pytest.raises(ValueError):
            unpack_order(invalid)
    np.testing.assert_array_equal(unpack_order(pack_order(np.zeros((0, 0), dtype=bool))), np.zeros((0, 0)))


def test_reconstruction_rejects_nonbirth_growth_edges_and_bad_reference_points():
    matrix, evidence = generate_history("percolation", .5, 4, np.random.default_rng(5))
    record = {"family": "percolation", "parameter": .5, "count": 4,
              "order_sha256": order_hash(matrix), **evidence}
    record["primitive_edges"] = pack_order(total_order(4).T)
    with pytest.raises(ValueError, match="forward"):
        reconstruct_history(record)
    matrix, evidence = generate_history("minkowski", 3, 4, np.random.default_rng(5))
    record = {"family": "minkowski", "parameter": 3, "count": 4,
              "order_sha256": order_hash(matrix), **evidence}
    record["coordinates"]["x"][0] = [100, 100]
    with pytest.raises(ValueError, match="outside unit diamond"):
        reconstruct_history(record)
    with pytest.raises(ValueError, match="cyclic"):
        independent_closure(np.ones((2, 2), dtype=bool))


def test_manifest_external_path_rejected(archive):
    manifest = json.loads((archive / "manifest.json").read_text())
    manifest["artifacts"][0]["name"] = "../outside"
    write_json(archive / "manifest.json", manifest)
    report = audit_growth_archive(archive)
    assert report["status"] == "failed"
    assert "within the archive" in report["failures"][0]


def test_cli_writes_external_report_and_reports_failure_exit_status(archive, capsys):
    output = archive.parent / (archive.name + "-audit.json")
    assert main([str(archive), "--output", str(output)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "passed" and summary["selected_raw_records"] == 24
    assert json.loads(output.read_text())["failure_count"] == 0
    (archive / "manifest.json").write_text("{}")
    assert main([str(archive), "--output", str(output)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "failed"
    assert json.loads(output.read_text())["failure_count"] > 0


def test_cli_refuses_report_inside_the_archived_directory(archive):
    output = archive / "audit.json"
    with pytest.raises(SystemExit) as error:
        main([str(archive), "--output", str(output)])
    assert error.value.code == 2
    assert not output.exists()
