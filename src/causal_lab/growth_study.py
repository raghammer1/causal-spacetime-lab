"""Registered fixed-p histories, paired thinning, and explicit iid controls.

Run with ``--pilot`` before selecting a workload; ``--smoke`` is a bounded
integration check, not a scientific experiment. No primary outcome tunes a law.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import subprocess
import time

import numpy as np

from .dimension import invert_ordering_fraction
from .growth import thin_order
from .growth_controls import MATCHED_EDGE_PROBABILITY, generate_history, order_hash
from .growth_observables import growth_observables
from .growth_random import identity, rng_for
from .growth_statistics import PREFIXES, THIN_SOURCES, summary_per_family, summarize_primary
from .local_statistics import build_reference
from .local_structure import motif_counts


@dataclass(frozen=True)
class GrowthConfig:
    seed: int = 20261027
    reference_seed: int = 20261028
    probabilities: tuple[float, ...] = (.005, .01, .02, .05, .1, .3)
    batches: int = 3
    histories: int = 32
    reference4: int = 5000
    reference8: int = 2000
    motif_draws: int = 4096
    bootstrap_draws: int = 2000
    workers: int = 3
    wall_seconds: float = 2700.
    smoke: bool = False

    def validate(self):
        for name in ("seed", "reference_seed", "batches", "histories", "reference4",
                     "reference8", "motif_draws", "bootstrap_draws", "workers"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < (0 if "seed" in name else 1):
                raise ValueError(f"invalid {name}")
        if self.workers > 3 or min(self.motif_draws, self.bootstrap_draws) < 2:
            raise ValueError("at most three workers; at least two motif/bootstrap draws")
        if (not self.probabilities or len(set(self.probabilities)) != len(self.probabilities)
                or any(isinstance(p, bool) or not isinstance(p, (int, float))
                       or not math.isfinite(p) or not 0 < p < 1 for p in self.probabilities)):
            raise ValueError("unique stochastic probabilities strictly between zero and one required")
        if (isinstance(self.wall_seconds, bool) or not isinstance(self.wall_seconds, (int, float))
                or not math.isfinite(self.wall_seconds) or self.wall_seconds <= 0):
            raise ValueError("positive finite wall budget required")
        if not isinstance(self.smoke, bool):
            raise ValueError("smoke must be Boolean")
        if self.seed == self.reference_seed:
            raise ValueError("growth and reference seeds must be independently reserved")
        return self


def families(config):
    return ([("percolation", p) for p in config.probabilities]
            + [("minkowski", d) for d in (2, 3, 4)]
            + [("semiorder", .25), ("matched_bipartite", MATCHED_EDGE_PROBABILITY)])


def _peak_bytes(who=resource.RUSAGE_SELF):
    peak = resource.getrusage(who).ru_maxrss
    return int(peak if platform.system() == "Darwin" else 1024 * peak)


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def _write_lines(path, rows):
    with Path(path).open("wb") as file:
        with gzip.GzipFile(fileobj=file, filename="", mode="wb", mtime=0) as stream:
            for row in rows:
                stream.write(_json_bytes(row) + b"\n")


def _record(matrix, config, batch, family, parameter, history_number, history_id,
            source_count, thinning_rep=None, retained_indices=None, *, phase="primary"):
    stage = "prefix" if thinning_rep is None else "thinned"
    replica = "prefix" if thinning_rep is None else thinning_rep
    row = {"family": family, "parameter": parameter, "batch": batch, "fit": batch,
           "history_id": history_id, "history_number": history_number,
           "stage": stage, "source_count": source_count, "thinning_rep": thinning_rep,
           "sample_id": identity(config.seed, batch, phase + "_record", family,
                                 parameter, history_number, source_count, replica),
           "order_sha256": order_hash(matrix)}
    if retained_indices is not None:
        row["retained_indices"] = [int(index) for index in retained_indices]
    row.update(growth_observables(matrix))
    row["r"] = row["ordering_fraction"]
    try:
        row["global_dimension"] = float(invert_ordering_fraction(row["r"]))
    except (ValueError, TypeError):
        row["global_dimension"] = None
    row["motifs"] = motif_counts(matrix, rng_for(config.seed, batch, phase + "_motifs",
                 family, parameter, history_number, source_count, replica), draws=config.motif_draws)
    return row


def one_history(config, family, parameter, batch, history_number, *, phase="primary"):
    """Construct one 17-row dependent cluster and its exact reconstruction data."""
    generation_phase = "generation" if phase == "primary" else phase + "_generation"
    key = identity(config.seed, batch, generation_phase, family, parameter, history_number)
    matrix, reconstruction = generate_history(family, parameter, 512,
             rng_for(config.seed, batch, generation_phase, family, parameter, history_number))
    history = {"family": family, "parameter": parameter, "batch": batch,
               "history_id": key, "history_number": history_number, "count": 512,
               "order_sha256": order_hash(matrix), **reconstruction}
    rows = [_record(matrix[:n, :n], config, batch, family, parameter, history_number,
                    key, n, phase=phase) for n in PREFIXES]
    for n in THIN_SOURCES:
        for replica in range(4):
            thinned, indices = thin_order(matrix[:n, :n], n // 2,
                   rng_for(config.seed, batch, phase + "_thinning", family, parameter,
                           history_number, n, replica))
            rows.append(_record(thinned, config, batch, family, parameter, history_number,
                                key, n, replica, indices, phase=phase))
    return rows, history


def _references(config):
    return [build_reference(d, batch, config.reference_seed,
                            m4_count=config.reference4, m8_count=config.reference8)
            for batch in range(config.batches) for d in (2, 3, 4)]


def _family_job(config, family, parameter, references, output, deadline):
    start = time.monotonic()
    rows, histories, trajectories = [], [], []
    phase = "smoke" if config.smoke else "primary"
    try:
        for batch in range(config.batches):
            for number in range(config.histories):
                if time.monotonic() > deadline:
                    raise TimeoutError("registered primary wall budget exceeded")
                cluster, history = one_history(config, family, parameter, batch, number, phase=phase)
                rows.extend(cluster)
                histories.append(history)
                if batch == 0 and number < 8:
                    trajectories.extend(row for row in cluster if row["stage"] == "prefix")
    except Exception as error:
        prefix = Path(output) / "raw" / f"{family}-{parameter}.partial"
        _write_lines(str(prefix) + ".jsonl.gz", rows)
        _write_lines(str(prefix) + ".histories.jsonl.gz", histories)
        Path(str(prefix) + ".failure.json").write_text(json.dumps({
            "family": family, "parameter": parameter, "error": type(error).__name__,
            "message": str(error), "completed_histories": len(histories),
            "completed_rows": len(rows)}, indent=2) + "\n")
        raise
    extraction_seconds = time.monotonic() - start
    filename = f"raw/{family}-{parameter}.jsonl.gz"
    _write_lines(Path(output) / filename, rows)
    # Persistent intermediates also survive an unrelated worker's failure.
    _write_lines(Path(output) / "_reconstruction" / f"{family}-{parameter}.jsonl.gz", histories)
    try:
        summary, bundle = summary_per_family(rows, references, seed=config.seed,
                                             bootstrap_draws=config.bootstrap_draws)
    except Exception:
        _write_lines(Path(output) / "raw" / f"{family}-{parameter}.partial.histories.jsonl.gz", histories)
        raise
    return {"family": family, "parameter": parameter, "summary": summary,
            "bundle": bundle, "histories": histories, "trajectories": trajectories,
            "raw_file": filename, "row_count": len(rows),
            "performance": {"family": family, "parameter": parameter, "pid": os.getpid(),
                "extraction_seconds": extraction_seconds, "total_seconds": time.monotonic() - start,
                "peak_rss_bytes": _peak_bytes()}}


def _provenance():
    root = Path(__file__).resolve().parents[2]
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()
    sources = sorted(root.glob("src/causal_lab/*.py"))
    documents = [root / "docs" / name for name in
                 ("BACKGROUND_FREE_GROWTH_PROTOCOL.md", "BACKGROUND_FREE_GROWTH_THEORY.md",
                  "BACKGROUND_FREE_GROWTH_WORKLOAD.md")]
    return {"source_commit": git("rev-parse", "HEAD"), "source_dirty": bool(git("status", "--porcelain")),
            "source_sha256": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in sources + documents if path.exists()},
            "python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform(),
            "rng": "PCG64(SHA256(canonical compact ASCII growth-v1 identity))",
            "reference_rng": "verified local-v1 constructor; independent reserved reference_seed"}


def run_study(config, output):
    from .growth_artifacts import write_artifacts
    config.validate()
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("output directory must be empty; preserve earlier runs")
    (output / "raw").mkdir(parents=True, exist_ok=True)
    (output / "_reconstruction").mkdir()
    start = time.monotonic()
    provenance = _provenance()
    references = _references(config)
    reference_seconds = time.monotonic() - start
    tasks = families(config)
    results = {}
    deadline = start + config.wall_seconds
    try:
        if config.workers == 1:
            for family, parameter in tasks:
                results[(family, parameter)] = _family_job(config, family, parameter, references, output, deadline)
        else:
            # Parameter-keyed RNG makes scheduling independent of all samples.
            with ProcessPoolExecutor(max_workers=config.workers) as pool:
                futures = {pool.submit(_family_job, config, family, parameter, references, output, deadline):
                           (family, parameter) for family, parameter in tasks}
                for future in as_completed(futures):
                    result = future.result()
                    results[(result["family"], result["parameter"])] = result
    except Exception as error:
        _write_lines(output / "completed_histories.jsonl.gz",
                     [history for result in results.values() for history in result["histories"]])
        (output / "RESOURCE_FAILURE.json").write_text(json.dumps({
            "config": asdict(config), "provenance": provenance, "error": type(error).__name__,
            "message": str(error), "completed_families": [list(key) for key in results],
            "elapsed_seconds": time.monotonic() - start}, indent=2) + "\n")
        raise
    ordered = [results[key] for key in tasks]
    endpoints, endpoint_histories = [], []
    for probability in (0., 1.):
        rows, history = one_history(config, "percolation", probability, 0, 0,
                                    phase="smoke" if config.smoke else "primary")
        endpoints.extend(rows)
        endpoint_histories.append(history)
    _write_lines(output / "raw/endpoints.jsonl.gz", endpoints)
    primary = {"growth": summarize_primary([result["bundle"] for result in ordered
                                             if result["family"] == "percolation"],
                                            bootstrap_draws=config.bootstrap_draws),
               "controls": [summarize_primary([result["bundle"]], bootstrap_draws=config.bootstrap_draws)
                            for result in ordered if (result["family"], result["parameter"]) in
                            (("minkowski", 2), ("matched_bipartite", MATCHED_EDGE_PROBABILITY))],
               "endpoints": endpoints}
    performance = [result["performance"] for result in ordered]
    root_peak = _peak_bytes()
    child_peak = _peak_bytes(resource.RUSAGE_CHILDREN)
    worker_peak = max([item["peak_rss_bytes"] for item in performance] + [child_peak])
    # Completed-child peaks also cover worker result serialization. Using the
    # largest worker peak for EVERY worker is intentionally conservative.
    aggregate = root_peak + (config.workers * worker_peak if config.workers > 1 else child_peak)
    elapsed = time.monotonic() - start
    metadata = {"run_kind": "smoke" if config.smoke else "primary", "config": asdict(config),
                "provenance": provenance, "row_count": sum(result["row_count"] for result in ordered) + 34,
                "stochastic_history_count": len(tasks) * config.batches * config.histories,
                "deterministic_endpoint_history_count": 2,
                "performance": {"reference_seconds": reference_seconds, "compute_seconds": elapsed,
                    "workers": performance, "root_peak_rss_bytes": root_peak,
                    "completed_child_peak_rss_bytes": child_peak,
                    "memory_bound_method": "root peak plus worker count times largest completed/reported child peak; serial root plus child peak",
                    "conservative_aggregate_peak_rss_bytes": aggregate,
                    "within_wall_budget": elapsed <= config.wall_seconds,
                    "within_memory_budget": aggregate < 4 * 1024 ** 3}}
    if not metadata["performance"]["within_wall_budget"] or not metadata["performance"]["within_memory_budget"]:
        (output / "RESOURCE_FAILURE.json").write_text(json.dumps(metadata, indent=2) + "\n")
        raise RuntimeError("registered resource budget exceeded; raw shards preserved")
    report = write_artifacts(output, [result["summary"] for result in ordered], primary,
                 references, [history for result in ordered for history in result["histories"]]
                 + endpoint_histories, [result["raw_file"] for result in ordered] + ["raw/endpoints.jsonl.gz"],
                 metadata, [row for result in ordered for row in result["trajectories"]]
                 + [row for row in endpoints if row["stage"] == "prefix"])
    # Include serialization and plotting in the reported memory/time envelope.
    root_peak = _peak_bytes()
    aggregate = root_peak + (config.workers * worker_peak if config.workers > 1 else child_peak)
    total_seconds = time.monotonic() - start
    report["performance"].update(root_peak_rss_bytes=root_peak,
        conservative_aggregate_peak_rss_bytes=aggregate,
        total_seconds=total_seconds, artifact_seconds=total_seconds - elapsed,
        within_memory_budget=aggregate < 4 * 1024 ** 3,
        within_total_wall_budget=total_seconds <= config.wall_seconds)
    metadata_path = output / "metadata.json"
    metadata_path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    entry = next(item for item in manifest["artifacts"] if item["name"] == "metadata.json")
    entry.update(bytes=metadata_path.stat().st_size,
                 sha256=hashlib.sha256(metadata_path.read_bytes()).hexdigest())
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n")
    if not report["performance"]["within_memory_budget"] or not report["performance"]["within_total_wall_budget"]:
        (output / "RESOURCE_FAILURE.json").write_text(json.dumps(report, indent=2) + "\n")
        raise RuntimeError("full execution resource budget exceeded; complete artifacts preserved")
    # These exact records now exist in the manifest-owned histories.jsonl.gz.
    for path in (output / "_reconstruction").glob("*.jsonl.gz"):
        path.unlink()
    (output / "_reconstruction").rmdir()
    return report


def run_pilot(config, output):
    """Timing-only run. Scientific values are discarded without inspection."""
    config = replace(config, seed=20261024, reference_seed=20261023, histories=1)
    config.validate()
    timings = []
    for family, parameter in families(config) + [("percolation", 0.), ("percolation", 1.)]:
        start = time.monotonic()
        rows, history = one_history(config, family, parameter, 0, 0, phase="pilot")
        timings.append({"family": family, "parameter": parameter,
                        "seconds": time.monotonic() - start, "peak_rss_bytes": _peak_bytes()})
        del rows, history
    start = time.monotonic()
    # Exact d2 construction separately timed; stochastic references scale by sample count.
    build_reference(2, 0, config.reference_seed, m4_count=32, m8_count=16)
    exact_seconds = time.monotonic() - start
    start = time.monotonic()
    references = [build_reference(d, batch, config.reference_seed, m4_count=100, m8_count=40)
                  for batch in range(3) for d in (3, 4)]
    stochastic_seconds = time.monotonic() - start
    reference_projection = exact_seconds + stochastic_seconds * max(config.reference4 / 100, config.reference8 / 40)
    references += [build_reference(2, batch, config.reference_seed, m4_count=32, m8_count=16)
                   for batch in range(3)]
    # Fabricated complete-chain clusters exercise array/bootstrap resource use only.
    template, _ = one_history(replace(config, motif_draws=32), "percolation", 1., 0, 0, phase="pilot")
    fabricated = []
    for batch in range(3):
        for number in range(64):
            for original in template:
                row = dict(original, family="semiorder", parameter=.25, batch=batch, fit=batch,
                           history_number=number, history_id=f"fabricated:{batch}:{number}",
                           sample_id=f"fabricated:{batch}:{number}:{original['sample_id']}")
                fabricated.append(row)
    start = time.monotonic()
    summary_per_family(fabricated, references, seed=config.seed, bootstrap_draws=config.bootstrap_draws)
    bootstrap_seconds = time.monotonic() - start
    stochastic_history_seconds = sum(row["seconds"] for row in timings[:-2])
    endpoint_seconds = sum(row["seconds"] for row in timings[-2:])
    projections = [{"histories_per_batch": r,
                    "projected_seconds": 1.5 * (3 * r * stochastic_history_seconds / 2
                                               + endpoint_seconds + reference_projection + 180)}
                   for r in (64, 32, 16)]
    selected = next((row["histories_per_batch"] for row in projections if row["projected_seconds"] <= 1500), None)
    report = {"pilot_seed": config.seed, "reference_seed": config.reference_seed,
              "timing_only": True, "scientific_values_retained": False,
              "history_timings": timings, "exact_reference_seconds": exact_seconds,
              "small_stochastic_reference_seconds": stochastic_seconds,
              "projected_reference_seconds": reference_projection,
              "fabricated_bootstrap_seconds": bootstrap_seconds,
              "projection_formula": "1.5 * (3*R*sum(stochastic history seconds)/2 + endpoint seconds + reference projection +180)",
              "projections": projections, "selected_histories_per_batch": selected,
              "peak_rss_bytes": _peak_bytes()}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise ValueError("pilot output already exists")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--histories", type=int, default=32, help="per batch and stochastic family")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(argv)
    if args.pilot and args.smoke:
        parser.error("pilot and smoke are distinct modes")
    config = GrowthConfig(histories=args.histories, workers=args.workers)
    if args.smoke:
        config = replace(config, seed=20261021, reference_seed=20261022,
                         probabilities=(.01, .1), batches=1, histories=1,
                         reference4=16, reference8=8, motif_draws=32, bootstrap_draws=16, smoke=True)
    result = run_pilot(config, args.output) if args.pilot else run_study(config, args.output)
    if args.pilot:
        print(json.dumps({"selected_histories_per_batch": result["selected_histories_per_batch"],
                          "projections": result["projections"]}, indent=2))
    else:
        print(json.dumps({"output": str(args.output), "scientific_sha256": result.get("scientific_sha256")}, indent=2))


if __name__ == "__main__":
    main()
