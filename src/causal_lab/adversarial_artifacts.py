"""Tables, deterministic archives and scientific figures for Experiment 3."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FormatStrFormatter
import numpy as np

from .adversarial_features import exact_counterexamples, nondual_pair
from .scaling import _peak_rss_bytes

COLORS = ("#2563eb", "#d97706", "#059669", "#dc2626", "#9333ea", "#0891b2")
LABELS = ("A: fraction", "B: height", "C: fraction + height", "D: five RMS", "E: five maximum", "F: interval abundance")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def scientific_digest(result):
    digest = hashlib.sha256()
    config = {k: v for k, v in result["config"].items() if k != "workers"}
    for key, value in (("config", config), *((k, result[k]) for k in
                        ("raw", "searches", "models", "examples", "summary", "paired", "classification", "search_effects", "advancement"))):
        digest.update(key.encode("ascii")+b"\n")
        if isinstance(value, list):
            for row in value:
                digest.update(canonical(row)+b"\n")
        else:
            digest.update(canonical(value)+b"\n")
    return digest.hexdigest()


def _json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")


def _gzip_lines(path, rows):
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:
            for row in rows:
                stream.write(canonical(row)+b"\n")


def _csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted({key for row in rows for key in row}))
        writer.writeheader()
        writer.writerows(rows)


def _save(fig, path):
    fig.savefig(path, dpi=160, bbox_inches="tight", metadata={"Software": "causal-spacetime-lab"})
    plt.close(fig)


def make_figures(result, out):
    primary = [r for r in result["summary"] if r["target"] == .95]
    counts = sorted(result["config"]["counts"])
    dimensions = sorted(result["config"]["dimensions"])
    names = "ABCDEF"
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.facecolor": "white"})
    fig, axes = plt.subplots(1, len(counts), figsize=(4.2*len(counts), 4), squeeze=False)
    for ax, n in zip(axes[0], counts):
        for i, name in enumerate(names):
            genuine = [r["mean_acceptance"] for r in primary if r["detector"] == name and r["count"] == n and r["family"] == "genuine"]
            negative = [r["mean_acceptance"] for r in primary if r["detector"] == name and r["count"] == n and r["family"] not in {"genuine", "rank_overlap", "box"}]
            ax.scatter(min(genuine), max(negative), color=COLORS[i], marker="os^vDP"[i], s=55, label=LABELS[i])
            offsets = ((-48, 22), (-16, 36), (-56, -16), (-24, 24), (-62, 20), (-28, 4))
            ax.annotate(name, (min(genuine), max(negative)), xytext=offsets[i], textcoords="offset points",
                        color=COLORS[i], arrowprops={"arrowstyle": "-", "lw": .7, "color": COLORS[i]})
        ax.axvline(.9, color="grey", ls=":")
        ax.axhline(.05, color="grey", ls=":")
        ax.set(xlim=(0, 1.02), ylim=(-.07, 1.15), title=f"N={n}",
               xlabel="Worst genuine dimension: mean acceptance", ylabel="Worst negative cell: mean acceptance")
    axes[0, -1].legend(fontsize=7, loc="lower left")
    fig.suptitle(f"Worst-cell overview across {result['config']['fits']} fits; dashed lines are targets, not CI tests")
    fig.tight_layout()
    _save(fig, out/"acceptance_tradeoff.png")

    fig, axes = plt.subplots(1, len(counts), figsize=(4.4*len(counts), 4), squeeze=False)
    for ax, n in zip(axes[0], counts):
        for j, d in enumerate(dimensions):
            rows = [next(r for r in primary if r["family"] == "genuine" and r["dimension_label"] == d and r["count"] == n and r["detector"] == name) for name in names]
            means = np.array([r["mean_acceptance"] for r in rows])
            error = np.array([[r["mean_acceptance"]-r["min_acceptance"] for r in rows],
                              [r["max_acceptance"]-r["mean_acceptance"] for r in rows]])
            ax.errorbar(np.arange(6)+(j-1)*.12, means, yerr=error, fmt="o-", capsize=3, label=f"d={d}", alpha=.85)
        ax.axhline(.90, color="grey", ls=":")
        ax.axhline(.95, color="grey", ls="--", alpha=.5)
        ax.set(xticks=range(6), xticklabels=list(names), ylim=(0, 1.02), title=f"N={n}",
               ylabel="Genuine acceptance", xlabel="Detector")
        ax.legend()
    fig.suptitle("Genuine acceptance: mean and observed fit range (not confidence intervals)")
    fig.tight_layout()
    _save(fig, out/"genuine_acceptance.png")

    families = sorted({(r["family"], r["dimension_label"]) for r in primary if r["family"] != "genuine"})
    fig, axes = plt.subplots(1, len(counts), figsize=(4.2*len(counts)+2, max(5, len(families)*.29)), squeeze=False)
    for ax, n in zip(axes[0], counts):
        values = np.array([[next(r["mean_acceptance"] for r in primary if r["family"] == family and r["dimension_label"] == d and r["count"] == n and r["detector"] == name)
                            for name in names] for family, d in families])
        im = ax.imshow(values, vmin=0, vmax=1, cmap="viridis", aspect="auto")
        ax.set(xticks=range(6), xticklabels=list(names), yticks=range(len(families)),
               yticklabels=[f"{f}"+(f" d={d}" if d else "") for f, d in families], title=f"N={n}")
        for j in range(len(families)):
            for k in range(6):
                ax.text(k, j, f"{values[j,k]:.2f}", ha="center", va="center", fontsize=7,
                        color="black" if values[j,k] > .55 else "white")
    fig.suptitle("Mean acceptance by family; rank_overlap is positive, box is boundary stress")
    fig.tight_layout(rect=(0, 0, .95, .96))
    cax = fig.add_axes((.96, .15, .012, .65))
    fig.colorbar(im, cax=cax, label=f"Acceptance ({result['config']['fits']} fits)")
    _save(fig, out/"detector_comparison.png")

    fig, axes = plt.subplots(2, 3, figsize=(11, 6), squeeze=False)
    for ax, name, label in zip(axes.flat, names, LABELS):
        for fit, models in sorted(result["models"].items()):
            ax.plot(counts, [models[str(n)]["thresholds"]["0.95"][name] for n in counts], "o-", label=f"fit {fit}")
        ax.set(title=label, xlabel="N", ylabel="95% validation score threshold", xticks=counts)
        ax.legend(fontsize=7)
    fig.suptitle("Independent calibration-fit sensitivity; score scales differ between panels")
    fig.tight_layout()
    _save(fig, out/"calibration_sensitivity.png")

    fig, axes = plt.subplots(2, len(dimensions), figsize=(4.3*len(dimensions), 6), squeeze=False)
    for column, d in enumerate(dimensions):
        for index, n in enumerate(counts):
            rows = [r for r in result["searches"] if r["dimension"] == d and r["count"] == n]
            if not rows:
                continue
            initial = np.array([r["initial_objective"] for r in rows])
            final = np.array([r["best_objective"] for r in rows])
            axes[0, column].plot([0, 1], [np.median(initial), np.median(final)], "o-", label=f"N={n}")
            for offset, key, label, color in ((-.17, "height_fraction_match", "r/height tolerance", COLORS[0]),
                                               (.17, "multifeature_match", "all 15 within 1 SD", COLORS[1])):
                successes = sum(r[key] for r in rows)
                rate = successes/len(rows)
                axes[1, column].bar(index+offset, rate, width=.32, color=color,
                                    label=label if index == 0 else None)
                axes[1, column].text(index+offset, rate+.02, f"{successes}/{len(rows)}",
                                     ha="center", va="bottom", fontsize=7, rotation=90 if rate > .8 else 0)
        axes[0, column].set(title=f"Target d={d}", ylabel="Median standardized RMS residual")
        axes[0, column].yaxis.set_major_locator(MaxNLocator(nbins=5))
        axes[0, column].yaxis.set_major_formatter(FormatStrFormatter("%.2g"))
        axes[0, column].set(xticks=(0, 1), xticklabels=("r/height checkpoint", "full search"), ylim=(0, None))
        axes[1, column].set(ylabel="Fraction meeting stage-specific tolerance", ylim=(-.03, 1.3),
                            xticks=range(len(counts)), xticklabels=[str(n) for n in counts], xlabel="N")
        axes[0, column].legend(fontsize=8)
    handles, labels = axes[1, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, fontsize=8)
    fig.suptitle("All searches retained; stage tolerances differ and do not certify geometry")
    fig.tight_layout(rect=(0, .06, 1, 1))
    _save(fig, out/"matching_quality.png")

    first, second = nondual_pair()
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, matrix, title in zip(axes[:2], (first, second), ("P: connected interior", "Q: disconnected interior")):
        # Discover extrema/layers from the order so the drawing does not depend on labels.
        levels = matrix.sum(axis=0)
        unique = sorted(set(levels.tolist()))
        positions = {}
        for level, value in enumerate(unique):
            indices = np.flatnonzero(levels == value)
            for offset, i in enumerate(indices):
                positions[int(i)] = (offset-(len(indices)-1)/2, level)
        for i, j in zip(*np.nonzero(matrix)):
            if not np.any(matrix[i] & matrix[:, j]):
                x, y = positions[int(i)]; xx, yy = positions[int(j)]
                ax.annotate("", xy=(xx, yy-.08), xytext=(x, y+.08), arrowprops={"arrowstyle": "->", "color": "#64748b", "lw": .9})
        ax.scatter(*np.array(list(positions.values())).T, s=70, color="#2563eb", zorder=3)
        ax.set(title=title, xlim=(-2.2, 2.2), ylim=(-.4, 3.4))
        ax.axis("off")
    from .adversarial_features import extract_features
    histogram = extract_features(first)["interval_histogram"]
    axes[2].bar(range(len(histogram)), histogram, color="#059669")
    axes[2].set(title="Identical full abundance histogram", xlabel="Number of internal events", ylabel="Related endpoint pairs", xticks=range(len(histogram)))
    fig.suptitle("Exact nonisomorphic, nondual orders: N=10, R=25, height=4")
    fig.tight_layout()
    _save(fig, out/"exact_degeneracy.png")


def write_outputs(result, output):
    start = perf_counter()
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    _gzip_lines(out/"raw.jsonl.gz", result["raw"])
    _gzip_lines(out/"searches.jsonl.gz", result["searches"])
    _gzip_lines(out/"paired.jsonl.gz", result["paired"])
    _json(out/"search_effects.json", result["search_effects"])
    for key in ("models", "summary", "advancement", "examples"):
        _json(out/(key+".json"), result[key])
    _json(out/"exact_counterexamples.json", {name: [order.astype(int).tolist() for order in pair]
                                          for name, pair in exact_counterexamples().items()})
    _csv(out/"classification.csv", result["classification"])
    rates = []
    for row in result["summary"]:
        for fit in row["per_fit"]:
            rates.append({k: row[k] for k in ("family", "dimension_label", "count", "detector", "target")} |
                         fit | {"false_rejection": 1-fit["rate"] if row["family"] in {"genuine", "rank_overlap"} else None,
                                "false_acceptance": fit["rate"] if row["family"] not in {"genuine", "rank_overlap", "box"} else None})
    _csv(out/"rates.csv", rates)
    _csv(out/"resources.csv", result["resources"])
    make_figures(result, out)
    root = Path(__file__).resolve().parents[2]
    try:
        parent = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True))
    except (OSError, subprocess.CalledProcessError):
        parent, dirty = None, None
    protocol = root/"docs/ADVERSARIAL_GEOMETRY_PROTOCOL.md"
    source_paths = sorted(Path(__file__).parent.glob("*.py"))
    metadata = {"config": result["config"], "scientific_sha256": scientific_digest(result),
                "recorded_orders": len(result["raw"]), "searches": len(result["searches"]),
                "candidate_evaluations": sum(r["evaluations"] for r in result["searches"]),
                "elapsed_seconds": result["elapsed_seconds"], "summary_seconds": result["summary_seconds"],
                "output_seconds": perf_counter()-start, "peak_parent_rss_bytes": _peak_rss_bytes(),
                "fit_resources": result["fit_resources"], "git_parent": parent, "git_dirty": dirty,
                "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest() if protocol.exists() else None,
                "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
                "versions": {"python": platform.python_version(), "numpy": np.__version__, "matplotlib": matplotlib.__version__},
                "platform": {"system": platform.system(), "machine": platform.machine()},
                "random_stream": "SHA256 compact ASCII JSON [adversarial-v1,seed,fit,phase,family,d,N,repeat,parameter] -> PCG64",
                "uncertainty": "Per-fit Wilson; hierarchical fits then whole orders; only three primary fits; pointwise intervals.",
                "resource_scope": "Wall timers exclude interpreter/import startup. Worker RSS values are per-process peaks, not simultaneous sums. Timing is excluded from scientific digest.",
                "artifact_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())
                                    if p.is_file() and p.name != "metadata.json"}}
    _json(out/"metadata.json", metadata)
    return metadata
