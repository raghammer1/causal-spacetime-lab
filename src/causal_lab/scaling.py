"""Reproducible finite-density study of a known 1+1D Minkowski model.

The fast algorithm uses generating coordinates. This study tests a numerical
reconstruction in a prescribed geometry, not emergence of physical spacetime.
See docs/FINITE_DENSITY_PROTOCOL.md for the hypotheses fixed before execution.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import platform
import shlex
import subprocess
import sys
from time import perf_counter
import tracemalloc
from typing import Callable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .core import (
    causal_order, comparable_pair_fraction, inferred_duration,
    longest_chain_fast, longest_chain_order, sprinkle,
)


@dataclass(frozen=True)
class StudyConfig:
    densities: tuple[float, ...] = tuple(np.geomspace(32.0, 8192.0, 7))
    durations: tuple[float, ...] = (0.5, 1.0, 2.0)
    repeats: int = 200
    seed: int = 20261025
    bootstrap: int = 2000
    order_repeats: int = 20
    order_max_count: int = 256
    benchmark_repeats: int = 3

    def validate(self) -> None:
        for name in ("densities", "durations"):
            values = getattr(self, name)
            if not values:
                raise ValueError(f"{name} must not be empty")
            if any(not np.isscalar(v) or not np.isfinite(v) or v <= 0 for v in values):
                raise ValueError(f"{name} must be finite and positive")
            if len(set(values)) != len(values):
                raise ValueError(f"{name} must not contain duplicates")
        minimums = {
            "repeats": 2, "seed": 0, "bootstrap": 2, "order_repeats": 0,
            "order_max_count": 0, "benchmark_repeats": 1,
        }
        for name, minimum in minimums.items():
            value = getattr(self, name)
            if (not isinstance(value, (int, np.integer)) or isinstance(value, (bool, np.bool_))
                    or value < minimum):
                raise ValueError(f"{name} must be an integer >= {minimum}")
        if self.order_repeats > self.repeats:
            raise ValueError("order_repeats cannot exceed repeats")
        for duration in self.durations:
            for density in self.densities:
                try:
                    expected = float(density) * float(duration)**2 / 2
                except OverflowError as exc:
                    raise ValueError("expected count must be finite and positive") from exc
                if not math.isfinite(expected) or expected <= 0:
                    raise ValueError("expected count must be finite and positive")


def _seed_digest(seed: int, duration: float, density: float, repeat: int, stream: str) -> str:
    identity = f"{int(seed)}|{float(duration).hex()}|{float(density).hex()}|{int(repeat)}|{stream}"
    return hashlib.sha256(identity.encode("ascii")).hexdigest()


def rng_for(seed: int, duration: float, density: float, repeat: int, stream: str) -> np.random.Generator:
    """A parameter-keyed PCG64 stream independent of traversal and other purposes."""
    entropy = int(_seed_digest(seed, duration, density, repeat, stream), 16)
    return np.random.Generator(np.random.PCG64(entropy))


def _bootstrap_means(values: np.ndarray, rng: np.random.Generator, bootstrap: int) -> np.ndarray:
    # At most 131,072 indices per batch in ordinary settings, rather than a
    # bootstrap-by-repetition matrix for the whole calculation.
    batch_size = max(1, min(128, 131072 // len(values)))
    means = np.empty(bootstrap, dtype=float)
    for start in range(0, bootstrap, batch_size):
        stop = min(start + batch_size, bootstrap)
        indices = rng.integers(0, len(values), size=(stop - start, len(values)))
        means[start:stop] = values[indices].mean(axis=1)
    return means


def summarize(values, duration: float, rng: np.random.Generator, bootstrap: int) -> dict:
    """Sample spread and pointwise percentile 95% bootstrap intervals for a mean.

    bias_ci_low/high are intervals for normalized bias, not absolute bias.
    Whole independent repetitions are resampled; no within-sprinkling pair
    indicators are treated as independent observations.
    """
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.all(np.isfinite(values)):
        raise ValueError("values must be a finite one-dimensional sample of length >= 2")
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be finite and positive")
    if (not isinstance(bootstrap, (int, np.integer)) or isinstance(bootstrap, (bool, np.bool_))
            or bootstrap < 2):
        raise ValueError("bootstrap must be an integer >= 2")
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    low, high = np.quantile(_bootstrap_means(values, rng, bootstrap), [0.025, 0.975])
    return {
        "mean_estimate": mean, "standard_deviation": sd,
        "standard_error": sd / math.sqrt(len(values)),
        "ci_low": float(low), "ci_high": float(high),
        "bias": mean - duration, "normalized_bias": mean / duration - 1,
        "bias_ci_low": float(low / duration - 1),
        "bias_ci_high": float(high / duration - 1),
    }


def _valid_indices(chain, count: int) -> bool:
    return (len(chain) == len(set(chain))
            and all(isinstance(i, (int, np.integer)) and 0 <= i < count for i in chain)
            and (bool(chain) or count == 0))


def _check_fast_chain(diamond, chain) -> None:
    if not _valid_indices(chain, diamond.count) or not all(
        diamond.u[i] < diamond.u[j] and diamond.v[i] < diamond.v[j]
        for i, j in zip(chain[:-1], chain[1:])
    ):
        raise RuntimeError("invalid chain returned by the embedding-based algorithm")


def _agreement(diamond, chain, base: dict) -> dict:
    order = causal_order(diamond)
    order_chain = longest_chain_order(order)
    valid = _valid_indices(order_chain, diamond.count) and all(
        order[i, j] for i, j in zip(order_chain[:-1], order_chain[1:])
    )
    if not valid:
        raise RuntimeError("invalid chain returned by the order-only algorithm")
    if len(chain) != len(order_chain):
        raise RuntimeError("algorithm mismatch between order-only and embedding-based chains")
    # Independently compute the control chains from explicit small matrices.
    total = np.triu(np.ones((diamond.count, diamond.count), dtype=bool), k=1)
    anti = np.zeros_like(total)
    total_length = len(longest_chain_order(total))
    anti_length = len(longest_chain_order(anti))
    if total_length != diamond.count or anti_length != int(diamond.count > 0):
        raise RuntimeError("negative-control chain mismatch")
    return {
        **base, "fast_length": len(chain), "order_length": len(order_chain),
        "total_order_length": total_length, "antichain_length": anti_length,
        "chain_valid": True, "agree": True,
        "pair_fraction": comparable_pair_fraction(order) if diamond.count >= 2 else None,
    }


def _measure(call: Callable) -> tuple[object, float, int]:
    """Time an untraced call, then measure allocations in a separate call."""
    start = perf_counter()
    value = call()
    seconds = perf_counter() - start
    if tracemalloc.is_tracing():
        raise RuntimeError("benchmarks require tracemalloc to be inactive on entry")
    tracemalloc.start()
    try:
        memory_value = call()
        _, peak = tracemalloc.get_traced_memory()
        del memory_value
    finally:
        tracemalloc.stop()
    return value, float(seconds), int(peak)


def _benchmarks(config: StudyConfig, duration: float, density: float) -> list[dict]:
    rows = []
    for repeat in range(config.benchmark_repeats):
        # Recreate this same independent sample for the separate allocation pass.
        # RNG setup is outside sampling's timed/traced scope.
        sample_rng = rng_for(config.seed, duration, density, repeat, "benchmark")
        memory_rng = rng_for(config.seed, duration, density, repeat, "benchmark")
        generators = iter((sample_rng, memory_rng))
        diamond, seconds, peak = _measure(lambda: sprinkle(duration, density, next(generators)))
        base = {
            "density": density, "duration": duration,
            "expected_count": density * duration**2 / 2,
            "repeat": repeat, "event_count": diamond.count,
            "sample_id": _seed_digest(config.seed, duration, density, repeat, "benchmark"),
        }
        rows.append({**base, "phase": "sprinkle", "seconds": seconds, "traced_peak_bytes": peak})
        chain, seconds, peak = _measure(lambda: longest_chain_fast(diamond))
        _check_fast_chain(diamond, chain)
        rows.append({**base, "phase": "fast", "seconds": seconds, "traced_peak_bytes": peak})
        if diamond.count <= config.order_max_count:
            order, seconds, peak = _measure(lambda: causal_order(diamond))
            rows.append({**base, "phase": "order_matrix", "seconds": seconds, "traced_peak_bytes": peak})
            order_chain, seconds, peak = _measure(lambda: longest_chain_order(order))
            if (len(order_chain) != len(chain) or not _valid_indices(order_chain, diamond.count)
                    or not all(order[i, j] for i, j in zip(order_chain[:-1], order_chain[1:]))):
                raise RuntimeError("algorithm mismatch or invalid chain in benchmark")
            rows.append({**base, "phase": "order_only", "seconds": seconds, "traced_peak_bytes": peak})
    return rows


def _contrast(a: np.ndarray, b: np.ndarray, rng: np.random.Generator, bootstrap: int) -> dict:
    """Mean(b)-mean(a), resampling the independent cells separately."""
    draws = _bootstrap_means(b, rng, bootstrap) - _bootstrap_means(a, rng, bootstrap)
    low, high = np.quantile(draws, [0.025, 0.975])
    return {"difference": float(b.mean() - a.mean()), "ci_low": float(low), "ci_high": float(high)}


def _diagnostics(config: StudyConfig, samples: dict, summaries: list[dict], agreements: list[dict]) -> dict:
    primary = {(row["duration"], row["density"]): row for row in summaries if row["model"] == "sprinkled"}
    poisson = []
    for (duration, density), sample in sorted(samples.items()):
        counts = sample["counts"]
        expected = density * duration**2 / 2
        mean_se = math.sqrt(expected / config.repeats)
        # Exact variance of unbiased sample variance for Poisson observations:
        # Var(s²) = lambda/n + 2 lambda²/(n-1).
        variance_se = math.sqrt(expected / config.repeats + 2 * expected**2 / (config.repeats - 1))
        mean_z = (float(counts.mean()) - expected) / mean_se
        variance_z = (float(counts.var(ddof=1)) - expected) / variance_se
        poisson.append({
            "density": density, "duration": duration, "expected_count": expected,
            "count_mean": float(counts.mean()), "count_variance": float(counts.var(ddof=1)),
            "mean_standard_error_theory": mean_se,
            "variance_standard_error_theory": variance_se,
            "mean_z": mean_z, "variance_z": variance_z,
            "investigate_five_se": abs(mean_z) > 5 or abs(variance_z) > 5,
        })
    endpoints = []
    if len(config.densities) > 1:
        low_density, high_density = min(config.densities), max(config.densities)
        for duration in sorted(config.durations):
            low = primary[(duration, low_density)]
            high = primary[(duration, high_density)]
            result = _contrast(
                samples[(duration, low_density)]["estimates"] / duration,
                samples[(duration, high_density)]["estimates"] / duration,
                rng_for(config.seed, duration, low_density, 0, f"endpoint:{float(high_density).hex()}"),
                config.bootstrap,
            )
            negative = low["bias_ci_high"] < 0 and high["bias_ci_high"] < 0
            if high["bias_ci_low"] > low["bias_ci_high"]:
                pointwise = "supports_improvement" if negative else "bias_not_established_negative"
            elif high["bias_ci_high"] < low["bias_ci_low"]:
                pointwise = "reversed"
            else:
                pointwise = "inconclusive"
            endpoints.append({
                "duration": float(duration), "low_density": float(low_density),
                "high_density": float(high_density),
                "low_normalized_bias": low["normalized_bias"],
                "high_normalized_bias": high["normalized_bias"],
                "contrast": "high_minus_low_normalized_bias", **result,
                "negative_bias_supported": negative,
                "pointwise_interval_outcome": pointwise,
                "contrast_interval_outcome": (
                    "positive" if result["ci_low"] > 0 else "negative" if result["ci_high"] < 0 else "inconclusive"
                ),
            })
    equal_lambda = []
    keys = sorted(samples)
    for i, (duration_a, density_a) in enumerate(keys):
        expected = density_a * duration_a**2 / 2
        for duration_b, density_b in keys[i + 1:]:
            other_expected = density_b * duration_b**2 / 2
            if not math.isclose(expected, other_expected, rel_tol=1e-12, abs_tol=0):
                continue
            a = samples[(duration_a, density_a)]["estimates"] / duration_a
            b = samples[(duration_b, density_b)]["estimates"] / duration_b
            stream = f"equal-lambda:{float(duration_b).hex()}:{float(density_b).hex()}"
            result = _contrast(a, b, rng_for(config.seed, duration_a, density_a, 0, stream), config.bootstrap)
            se = float(np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)))
            z = result["difference"] / se if se else (0.0 if result["difference"] == 0 else None)
            equal_lambda.append({
                "duration_a": float(duration_a), "density_a": float(density_a),
                "duration_b": float(duration_b), "density_b": float(density_b),
                "expected_count": expected, "contrast": "relative_mean_b_minus_a", **result,
                "standard_error": se, "z": z,
                "investigate_five_se": z is None or abs(z) > 5,
            })
    candidates = len(config.densities) * len(config.durations) * config.order_repeats
    return {
        "poisson_moments": poisson, "endpoint_contrasts": endpoints,
        "equal_lambda_comparisons": equal_lambda,
        "agreement_summary": {
            "candidate_primary_trials": candidates, "checked_primary_trials": len(agreements),
            "skipped_above_count_limit": candidates - len(agreements),
            "mismatches": 0, "order_max_count": config.order_max_count,
            "selection": "first order_repeats per cell, retained only if realized N <= order_max_count",
        },
        "uncertainty_note": "Pointwise 95% percentile bootstrap intervals; no multiplicity correction. Endpoint and equal-lambda contrasts resample independent cells independently.",
    }


def _peak_rss_bytes() -> int | None:
    try:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return int(peak)
        if sys.platform.startswith("linux"):
            return int(peak * 1024)
    except (ImportError, AttributeError):
        pass
    return None


def _metadata(config: StudyConfig) -> dict:
    root = Path(__file__).resolve().parents[2]
    sources = {"src/causal_lab/core.py": Path(__file__).with_name("core.py"),
               "src/causal_lab/scaling.py": Path(__file__)}
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sources.items()}
    protocol = root / "docs/FINITE_DENSITY_PROTOCOL.md"
    protocol_hash = hashlib.sha256(protocol.read_bytes()).hexdigest() if protocol.is_file() else None
    try:
        if not (root / ".git").exists():
            raise OSError("package is not in a source checkout")
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                                capture_output=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=root, text=True,
                                    capture_output=True, check=True).stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    command = ["python", "-m", "causal_lab.scaling", "--densities", *map(str, config.densities),
               "--durations", *map(str, config.durations)]
    for name in ("repeats", "seed", "bootstrap", "order_repeats", "order_max_count", "benchmark_repeats"):
        command.extend(["--" + name.replace("_", "-"), str(getattr(config, name))])
    command.extend(["--out", "results/finite-density-v1"])
    return {
        "schema_version": 1, "config": asdict(config),
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "matplotlib": matplotlib.__version__, "package": version("causal-spacetime-lab")},
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "git_commit": commit, "git_worktree_dirty": dirty, "source_sha256": hashes,
        "protocol_sha256": protocol_hash,
        "reproduction_command": shlex.join(command),
        "rng": "NumPy Generator(PCG64(int(SHA256(identity).hexdigest(), 16)))",
        "seed_identity": "ASCII master_seed|float(duration).hex()|float(density).hex()|repeat|stream; decimal integers; physical stream='physical', independent benchmark and bootstrap purpose strings",
        "bootstrap": {"method": "percentile", "confidence": 0.95, "resamples": config.bootstrap,
                      "unit": "independent whole sprinkling repetition", "coverage": "pointwise"},
        "timing_scope": "perf_counter seconds for separate untraced calls; RNG setup excluded from sprinkle; fast uses coordinates; order_matrix builds relation; order_only includes strict transitivity validation and DP, excludes input matrix construction",
        "allocation_scope": "Separate tracemalloc pass of same deterministic benchmark sample; peak newly traced Python/NumPy allocations, excluding retained inputs; not total resident memory. Unsupported native allocations may be invisible.",
        "benchmark_selection": "Independent benchmark streams; matrix phases only when realized N <= order_max_count, so they are count-selected near the cap. No extrapolation of timings beyond measured sizes.",
        "process_peak_rss_bytes": _peak_rss_bytes(),
        "process_peak_rss_scope": "Process lifetime through study completion, including imports, bootstrap and benchmark passes; excludes subsequent output plotting. Darwin ru_maxrss bytes; Linux KiB converted to bytes; unavailable platforms null. Prior work in this process may contribute.",
        "scientific_status": "Numerical test in known Minkowski geometry; no evidence of microscopic physical discreteness, background-free emergence, gravitational dynamics or singularity resolution.",
    }


def run_study(config: StudyConfig) -> dict:
    """Run all requested cells; any chain/control inconsistency aborts the study."""
    config.validate()
    # Accept NumPy integer scalars while retaining standard JSON-compatible
    # Python values in all records. Validation occurs before conversion.
    options = asdict(config)
    for name in ("repeats", "seed", "bootstrap", "order_repeats", "order_max_count", "benchmark_repeats"):
        options[name] = int(options[name])
    options["densities"] = tuple(map(float, config.densities))
    options["durations"] = tuple(map(float, config.durations))
    config = StudyConfig(**options)
    start = perf_counter()
    raw, summary, agreement, benchmarks = [], [], [], []
    samples = {}
    # Canonical traversal gives stable scientific file ordering, while keyed
    # streams additionally preserve samples under grid subsetting/reordering.
    for duration in sorted(map(float, config.durations)):
        for density in sorted(map(float, config.densities)):
            expected = density * duration**2 / 2
            counts, lengths = [], []
            for repeat in range(config.repeats):
                diamond = sprinkle(duration, density, rng_for(config.seed, duration, density, repeat, "physical"))
                chain = longest_chain_fast(diamond)
                _check_fast_chain(diamond, chain)
                estimate = inferred_duration(len(chain), density)
                base = {
                    "density": density, "duration": duration, "repeat": repeat,
                    "event_count": diamond.count,
                    "sample_id": _seed_digest(config.seed, duration, density, repeat, "physical"),
                }
                raw.append({
                    **base, "expected_count": expected, "chain_length": len(chain),
                    "total_order_length": diamond.count, "antichain_length": int(diamond.count > 0),
                    "estimate": estimate, "relative_estimate": estimate / duration, "seed": config.seed,
                })
                counts.append(diamond.count)
                lengths.append(len(chain))
                if repeat < config.order_repeats and diamond.count <= config.order_max_count:
                    agreement.append(_agreement(diamond, chain, base))
            counts = np.asarray(counts, dtype=int)
            lengths = np.asarray(lengths, dtype=int)
            denominator = np.sqrt(2.0) * np.sqrt(density)
            estimates = lengths / denominator
            samples[(duration, density)] = {"counts": counts, "estimates": estimates}
            controls = {"sprinkled": lengths, "total_order": counts, "antichain": (counts > 0).astype(int)}
            references = {"sprinkled": 2 * math.sqrt(expected), "total_order": expected,
                          "antichain": float(-np.expm1(-expected))}
            for model, chain_lengths in controls.items():
                summary.append({
                    "model": model, "density": density, "duration": duration,
                    "expected_count": expected, "repeats": config.repeats,
                    "count_mean": float(counts.mean()), "count_standard_deviation": float(counts.std(ddof=1)),
                    "chain_mean": float(chain_lengths.mean()),
                    "chain_standard_deviation": float(chain_lengths.std(ddof=1)),
                    "analytic_chain_reference": references[model],
                    "analytic_reference_kind": "large-count asymptotic" if model == "sprinkled" else "exact expectation",
                    **summarize(chain_lengths / denominator, duration,
                                rng_for(config.seed, duration, density, 0, f"bootstrap:{model}"), config.bootstrap),
                })
            benchmarks.extend(_benchmarks(config, duration, density))
    diagnostics = _diagnostics(config, samples, summary, agreement)
    result = {"config": asdict(config), "raw": raw, "summary": summary,
              "agreement": agreement, "benchmarks": benchmarks, "diagnostics": diagnostics}
    metadata = _metadata(config)
    metadata["study_wall_seconds"] = perf_counter() - start
    content = {name: result[name] for name in ("raw", "summary", "agreement", "diagnostics")}
    metadata["scientific_digest"] = hashlib.sha256(
        json.dumps(content, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    result["metadata"] = metadata
    return result


def _save_figure(fig, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=160, metadata={"Software": "causal-spacetime-lab"})
    plt.close(fig)


def _plots(result: dict, out: Path) -> None:
    primary = [row for row in result["summary"] if row["model"] == "sprinkled"]
    durations = sorted({row["duration"] for row in primary})
    colors = plt.get_cmap("tab10").colors
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    for i, duration in enumerate(durations):
        rows = sorted((r for r in primary if r["duration"] == duration), key=lambda r: r["density"])
        x = [r["density"] for r in rows]
        ax.plot(x, [r["mean_estimate"] / duration for r in rows], "o-", color=colors[i % 10], label=f"T = {duration:g}")
        ax.vlines(x, [r["ci_low"] / duration for r in rows], [r["ci_high"] / duration for r in rows], color=colors[i % 10])
    ax.axhline(1, linestyle="--", color="black", linewidth=1, label="Known duration")
    ax.set(xscale="log", xlabel="Density ρ [events / spacetime volume, c=1]",
           ylabel="Mean reconstructed duration / true duration", title="Known Minkowski geometry: pointwise 95% mean intervals")
    ax.legend()
    _save_figure(fig, out / "reconstruction.png")

    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    for i, duration in enumerate(durations):
        rows = sorted((r for r in primary if r["duration"] == duration), key=lambda r: r["expected_count"])
        x = [r["expected_count"] for r in rows]
        ax.plot(x, [r["normalized_bias"] for r in rows], "o-", color=colors[i % 10], label=f"T = {duration:g}")
        ax.vlines(x, [r["bias_ci_low"] for r in rows], [r["bias_ci_high"] for r in rows], color=colors[i % 10])
    x = np.geomspace(min(r["expected_count"] for r in primary), max(r["expected_count"] for r in primary), 200)
    ax.plot(x, -1.7711 / (2 * np.cbrt(x)), "k--", linewidth=1, label="BDJ leading asymptotic guide (not a fit)")
    ax.axhline(0, color="gray", linewidth=0.7)
    ax.set(xscale="log", xlabel="Expected event count λ = ρT²/2",
           ylabel="Normalized bias (mean estimate − T) / T", title="Finite-density bias: pointwise 95% bootstrap intervals")
    ax.legend(fontsize=8)
    _save_figure(fig, out / "bias_scaling.png")

    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    markers = {"sprinkled": "o", "total_order": "s", "antichain": "^"}
    for i, model in enumerate(markers):
        rows = sorted((r for r in result["summary"] if r["model"] == model), key=lambda r: r["expected_count"])
        ax.scatter([r["expected_count"] for r in rows], [r["chain_mean"] for r in rows],
                   marker=markers[model], color=colors[i], s=22, label=model.replace("_", " "))
        lower = [r["ci_low"] * np.sqrt(2 * r["density"]) for r in rows]
        upper = [r["ci_high"] * np.sqrt(2 * r["density"]) for r in rows]
        ax.vlines([r["expected_count"] for r in rows], lower, upper, color=colors[i], alpha=0.6)
    ax.plot(x, 2 * np.sqrt(x), "--", color=colors[0], label="2√λ (asymptotic)")
    ax.plot(x, x, "--", color=colors[1], label="λ (exact total expectation)")
    ax.plot(x, -np.expm1(-x), "--", color=colors[2], label="1−exp(−λ) (exact anti expectation)")
    ax.set(xscale="log", xlabel="Expected event count λ = ρT²/2",
           ylabel="Mean chain length [events; linear scale below 1]", title="Matched-count controls: pointwise 95% mean intervals")
    ax.set_yscale("symlog", linthresh=1)
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=8)
    _save_figure(fig, out / "chain_controls.png")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
    labels = {"sprinkle": "sampling", "fast": "embedding LIS", "order_matrix": "order matrix", "order_only": "validate + order DP"}
    for i, (phase, label) in enumerate(labels.items()):
        rows = [r for r in result["benchmarks"] if r["phase"] == phase]
        cells = sorted({(r["duration"], r["density"]) for r in rows})
        groups = [[r for r in rows if (r["duration"], r["density"]) == cell] for cell in cells]
        for ax, field, scale in ((axes[0], "seconds", 1000), (axes[1], "traced_peak_bytes", 1 / 1024)):
            for j, group in enumerate(groups):
                n = np.mean([r["event_count"] for r in group])
                y = np.asarray([r[field] * scale for r in group])
                ax.scatter(n, y.mean(), s=20, color=colors[i], label=label if j == 0 else None)
                ax.vlines(n, y.min(), y.max(), color=colors[i])
            ax.set(xscale="symlog", yscale="log", xlabel="Mean realized event count N (separate samples)")
    axes[0].set(ylabel="Untraced wall time [ms]", title="Mean; bars show benchmark min–max")
    axes[1].set(ylabel="Peak newly traced allocations [KiB]", title="Separate memory passes; retained inputs excluded")
    axes[0].legend(fontsize=7)
    _save_figure(fig, out / "benchmarks.png")


def _write_csv(path: Path, rows: list[dict], empty_fields: tuple[str, ...] = ()) -> None:
    fields = list(rows[0]) if rows else list(empty_fields)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(result: dict, out: Path | str) -> None:
    """Write scientific records, separately variable benchmarks, and four plots."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    start = perf_counter()
    for name in ("raw", "summary", "agreement", "benchmarks"):
        _write_csv(out / f"{name}.csv", result[name], (
            "density", "duration", "repeat", "event_count", "sample_id", "fast_length",
            "order_length", "total_order_length", "antichain_length", "chain_valid", "agree", "pair_fraction",
        ))
    for name in ("summary", "diagnostics"):
        (out / f"{name}.json").write_text(json.dumps(result[name], indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    _plots(result, out)
    deterministic = ("raw.csv", "summary.csv", "summary.json", "agreement.csv", "diagnostics.json",
                     "reconstruction.png", "bias_scaling.png", "chain_controls.png")
    metadata = dict(result["metadata"])
    metadata["artifact_sha256"] = {name: hashlib.sha256((out / name).read_bytes()).hexdigest() for name in deterministic}
    metadata["output_wall_seconds"] = perf_counter() - start
    metadata["process_peak_rss_after_outputs_bytes"] = _peak_rss_bytes()
    metadata["process_peak_rss_after_outputs_scope"] = "Process lifetime through CSV/JSON and PNG generation, including plotting; not incremental memory for this study alone."
    metadata["nondeterministic_artifacts"] = ["benchmarks.csv", "benchmarks.png", "metadata.json"]
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def main() -> None:
    defaults = StudyConfig()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--densities", nargs="+", type=float, default=defaults.densities)
    parser.add_argument("--durations", nargs="+", type=float, default=defaults.durations)
    for name in ("repeats", "seed", "bootstrap", "order_repeats", "order_max_count", "benchmark_repeats"):
        parser.add_argument("--" + name.replace("_", "-"), type=int, default=getattr(defaults, name))
    parser.add_argument("--out", type=Path, default=Path("results/finite-density-v1"))
    args = parser.parse_args()
    options = vars(args).copy()
    out = options.pop("out")
    options["densities"] = tuple(options["densities"])
    options["durations"] = tuple(options["durations"])
    config = StudyConfig(**options)
    try:
        config.validate()
    except ValueError as exc:
        parser.error(str(exc))
    result = run_study(config)
    write_outputs(result, out)
    print(f"Completed {len(result['raw'])} primary sprinklings in {result['metadata']['study_wall_seconds']:.3f} s (output generation excluded).")
    print(f"Checked {len(result['agreement'])} small-case algorithm/control comparisons; zero mismatches.")
    print(f"Scientific SHA256: {result['metadata']['scientific_digest']}")
    print(f"Saved CSV, JSON and four PNG figures to {out}")


if __name__ == "__main__":
    main()
