"""Control laws, isolated test streams, and bounded history/artifact integration."""
from dataclasses import replace
import gzip
import itertools
import json
import math
import time

import numpy as np
import pytest

from causal_lab.dimension import validate_order
from causal_lab.growth_controls import (
    MATCHED_EDGE_PROBABILITY, generate_history, order_hash, pack_order,
)
from causal_lab.growth_observables import induced_three_plus_one
from causal_lab.growth_random import identity, rng_for
from causal_lab.growth_statistics import PREFIXES, THIN_SOURCES
from causal_lab import growth_study
from causal_lab.growth_study import GrowthConfig, one_history
from causal_lab.local_structure import induced_two_plus_two
from causal_lab.order_observables import transitive_closure


def config(**kwargs):
    base = GrowthConfig(seed=101, reference_seed=102, batches=1, histories=1,
                        motif_draws=16, bootstrap_draws=8, reference4=8, reference8=4,
                        workers=1, smoke=True)
    return replace(base, **kwargs)


def unpack(packed):
    shape = tuple(packed["shape"])
    bits = np.unpackbits(np.frombuffer(bytes.fromhex(packed["packed_hex"]), dtype=np.uint8),
                         bitorder=packed["bitorder"])
    return bits[:math.prod(shape)].reshape(shape).astype(bool)


@pytest.mark.parametrize("family,parameter", [
    ("percolation", .02), ("minkowski", 2), ("minkowski", 3), ("minkowski", 4),
    ("semiorder", .25), ("matched_bipartite", MATCHED_EDGE_PROBABILITY),
])
def test_control_generation_preserves_every_seeded_prefix(family, parameter):
    def sample(n):
        return generate_history(family, parameter, n,
                                rng_for(101, 0, "test_generation", family, parameter, 0))
    full, reconstruction = sample(64)
    validate_order(full)
    assert unpack(pack_order(full)).tolist() == full.tolist()
    for n in (0, 1, 7, 32, 64):
        prefix, _ = sample(n)
        np.testing.assert_array_equal(prefix, full[:n, :n])
    if family == "percolation":
        primitive = unpack(reconstruction["primitive_edges"])
        np.testing.assert_array_equal(transitive_closure(primitive), full)
        assert "coordinates" not in reconstruction
    else:
        assert reconstruction["metadata"]["intrinsic_growth"] is False
    if family == "matched_bipartite":
        marks = np.asarray(reconstruction["layers"])
        assert not full[marks == 1].any()
        assert not full[:, marks == 0].any()
        assert not (full.astype(int) @ full).any()


def test_matched_control_has_exact_four_event_probability_without_sampling():
    q = MATCHED_EDGE_PROBABILITY
    assert (3 / 4) * q ** 2 * (1 - q) ** 2 == pytest.approx(1 / 24, abs=1e-16)
    total = hit = 0.
    for marks in itertools.product((0, 1), repeat=4):
        allowed = [(a, b) for a in range(4) for b in range(4)
                   if marks[a] == 0 and marks[b] == 1]
        for mask in range(1 << len(allowed)):
            matrix = np.zeros((4, 4), dtype=bool)
            selected = mask.bit_count()
            for bit, pair in enumerate(allowed):
                matrix[pair] = bool(mask & (1 << bit))
            probability = q ** selected * (1 - q) ** (len(allowed) - selected) / 16
            total += probability
            # Independent characterization of 2+2, not the production counter.
            two_disjoint_edges = matrix.sum() == 2 and np.all(matrix.sum(axis=0) + matrix.sum(axis=1) == 1)
            hit += probability * two_disjoint_edges
    assert total == pytest.approx(1, abs=2e-15)
    assert hit == pytest.approx(1 / 24, abs=2e-16)


@pytest.mark.parametrize("threshold", [0., .25, 1.])
def test_equal_width_interval_control_has_neither_forbidden_motif(threshold):
    order, reconstruction = generate_history(
        "semiorder", threshold, 48, rng_for(101, 0, "test_generation", "semiorder", threshold, 0))
    assert induced_two_plus_two(order) == 0
    assert induced_three_plus_one(order) == 0
    utilities = np.asarray(reconstruction["utilities"])
    np.testing.assert_array_equal(order, utilities[None, :] - utilities[:, None] > threshold)


def test_random_identity_is_canonical_phase_separated_and_has_no_terminal_size():
    key = identity(101, 2, "test_generation", "percolation", .02, 7)
    assert json.loads(key) == ["growth-v1", 101, 2, "test_generation", "percolation", .02, 7, None, None]
    first = rng_for(101, 2, "test_generation", "percolation", .02, 7).random(16)
    assert np.array_equal(first, rng_for(101, 2, "test_generation", "percolation", .02, 7).random(16))
    alternatives = [
        rng_for(101, 3, "test_generation", "percolation", .02, 7),
        rng_for(101, 2, "test_motifs", "percolation", .02, 7),
        rng_for(101, 2, "test_generation", "percolation", .05, 7),
        rng_for(101, 2, "test_generation", "percolation", .02, 8),
        rng_for(101, 2, "test_thinning", "percolation", .02, 7, 128, 0),
        rng_for(101, 2, "test_thinning", "percolation", .02, 7, 128, 1),
    ]
    arrays = [first] + [rng.random(16) for rng in alternatives]
    assert len({array.tobytes() for array in arrays}) == len(arrays)


@pytest.mark.parametrize("change", [
    {"seed": True}, {"seed": -1}, {"reference_seed": 101}, {"batches": 0},
    {"histories": -1}, {"reference4": 0}, {"reference8": False}, {"workers": 4},
    {"motif_draws": 1}, {"bootstrap_draws": 1}, {"probabilities": ()},
    {"probabilities": (.01, .01)}, {"probabilities": (0.,)}, {"probabilities": (1.,)},
    {"probabilities": (float("nan"),)}, {"probabilities": (True,)},
    {"wall_seconds": 0.}, {"wall_seconds": float("inf")},
    {"wall_seconds": True}, {"wall_seconds": "ten"}, {"smoke": "yes"},
])
def test_invalid_configuration_is_rejected(change):
    with pytest.raises(ValueError):
        config(**change).validate()


def test_registered_configuration_grid_and_independent_reference_reservation():
    registered = GrowthConfig().validate()  # Validate only; never sample primary seeds.
    assert registered.probabilities == (.005, .01, .02, .05, .1, .3)
    assert registered.batches == 3
    assert registered.histories in (64, 32, 16)
    assert registered.seed != registered.reference_seed
    assert len(growth_study.families(registered)) == 11


def test_one_history_records_full_grid_and_keeps_relations_through_deleted_events():
    cfg = config()
    rows, history = one_history(cfg, "percolation", .02, 0, 0, phase="test")
    assert len(rows) == 17
    assert len({row["sample_id"] for row in rows}) == 17
    assert {row["history_id"] for row in rows} == {history["history_id"]}
    assert json.loads(history["history_id"])[3] == "test_generation"
    primitive = unpack(history["primitive_edges"])
    full = transitive_closure(primitive)
    assert order_hash(full) == history["order_sha256"]
    prefixes = [row for row in rows if row["stage"] == "prefix"]
    assert [row["count"] for row in prefixes] == list(PREFIXES)
    for row in prefixes:
        n = row["count"]
        assert row["source_count"] == n
        assert row["order_sha256"] == order_hash(full[:n, :n])
    retained_external_paths = False
    for n in THIN_SOURCES:
        thinnings = [row for row in rows if row["stage"] == "thinned" and row["source_count"] == n]
        assert {row["thinning_rep"] for row in thinnings} == {0, 1, 2, 3}
        for row in thinnings:
            indices = np.asarray(row["retained_indices"])
            assert len(indices) == row["count"] == n // 2
            assert np.array_equal(indices, np.unique(indices))
            assert 0 <= indices.min() < indices.max() < n
            induced = full[np.ix_(indices, indices)]
            assert order_hash(induced) == row["order_sha256"]
            pruned = transitive_closure(primitive[np.ix_(indices, indices)])
            retained_external_paths |= bool(np.any(induced & ~pruned))
    assert retained_external_paths
    json.dumps({"rows": rows, "history": history}, allow_nan=False)


def test_gzip_scientific_shards_are_byte_reproducible_and_round_trip(tmp_path):
    rows = [{"history_id": "test", "count": 4, "value": None}, {"value": .125, "count": 8}]
    first, second = tmp_path / "first.gz", tmp_path / "second.gz"
    growth_study._write_lines(first, rows)
    growth_study._write_lines(second, rows)
    assert first.read_bytes() == second.read_bytes()
    with gzip.open(first, "rt") as file:
        assert [json.loads(line) for line in file] == rows


def test_existing_output_is_preserved_without_starting_an_experiment(tmp_path, monkeypatch):
    sentinel = tmp_path / "keep.txt"
    sentinel.write_text("previous result")
    monkeypatch.setattr(growth_study, "_references", lambda cfg: pytest.fail("must not generate references"))
    with pytest.raises(ValueError, match="empty"):
        growth_study.run_study(config(), tmp_path)
    assert sentinel.read_text() == "previous result"


def test_failed_family_preserves_completed_raw_history_and_reconstruction(tmp_path, monkeypatch):
    (tmp_path / "raw").mkdir()
    def simulated_history(cfg, family, parameter, batch, number, *, phase):
        assert cfg.seed == 101 and cfg.reference_seed == 102
        assert phase == "smoke"
        if number:
            raise TimeoutError("injected validation failure")
        return [{"stage": "prefix", "value": 42}], {"history_number": 0, "identity": "test"}
    monkeypatch.setattr(growth_study, "one_history", simulated_history)
    with pytest.raises(TimeoutError, match="injected"):
        growth_study._family_job(config(histories=2), "percolation", .02, [],
                                 tmp_path, time.monotonic() + 60)
    with gzip.open(tmp_path / "raw/percolation-0.02.partial.jsonl.gz", "rt") as file:
        assert [json.loads(line) for line in file] == [{"stage": "prefix", "value": 42}]
    with gzip.open(tmp_path / "raw/percolation-0.02.partial.histories.jsonl.gz", "rt") as file:
        assert [json.loads(line) for line in file] == [{"history_number": 0, "identity": "test"}]
    failure = json.loads((tmp_path / "raw/percolation-0.02.partial.failure.json").read_text())
    assert failure["error"] == "TimeoutError"
    assert failure["completed_histories"] == failure["completed_rows"] == 1


def test_failed_study_records_failure_manifest_without_hiding_error(tmp_path, monkeypatch):
    monkeypatch.setattr(growth_study, "_references", lambda cfg: [])
    monkeypatch.setattr(growth_study, "_provenance", lambda: {"test_only": True})
    monkeypatch.setattr(growth_study, "families", lambda cfg: [("percolation", .02)])
    def fail(*args):
        raise TimeoutError("injected worker error")
    monkeypatch.setattr(growth_study, "_family_job", fail)
    with pytest.raises(TimeoutError, match="injected"):
        growth_study.run_study(config(), tmp_path)
    failure = json.loads((tmp_path / "RESOURCE_FAILURE.json").read_text())
    assert failure["error"] == "TimeoutError"
    assert failure["config"]["seed"] == 101
    assert failure["completed_families"] == []


def test_reconstruction_survives_failure_after_complete_family_extraction(tmp_path, monkeypatch):
    (tmp_path / "raw").mkdir()
    (tmp_path / "_reconstruction").mkdir()
    monkeypatch.setattr(growth_study, "one_history", lambda *args, **kwargs:
                        ([{"stage": "prefix", "value": 42}], {"history_number": 0, "identity": "test"}))
    def fail_summary(*args, **kwargs):
        raise ValueError("injected analysis failure")
    monkeypatch.setattr(growth_study, "summary_per_family", fail_summary)
    with pytest.raises(ValueError, match="injected analysis"):
        growth_study._family_job(config(), "percolation", .02, [], tmp_path, time.monotonic() + 60)
    with gzip.open(tmp_path / "_reconstruction/percolation-0.02.jsonl.gz", "rt") as file:
        assert [json.loads(line) for line in file] == [{"history_number": 0, "identity": "test"}]
    assert (tmp_path / "raw/percolation-0.02.jsonl.gz").exists()


def test_cli_smoke_uses_reserved_validation_seeds_not_primary_seeds(tmp_path, monkeypatch):
    captured = []
    monkeypatch.setattr(growth_study, "run_study", lambda cfg, output:
                        captured.append(cfg) or {"scientific_sha256": "test-only"})
    growth_study.main(["--smoke", "--output", str(tmp_path)])
    cfg = captured[0]
    assert cfg.smoke is True
    assert (cfg.seed, cfg.reference_seed) == (20261021, 20261022)
    assert cfg.seed != GrowthConfig().seed
    assert cfg.reference_seed != GrowthConfig().reference_seed
    assert cfg.batches == cfg.histories == 1
