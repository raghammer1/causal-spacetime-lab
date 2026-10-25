"""Deterministic Experiment 4 archives and figures of structural information.

Figures describe finite sampling laws and exact invariants. They do not report
classifier accuracy or certify geometric embeddability. Scientific digests omit
timings, provenance metadata and rendered figures.
"""
from __future__ import annotations

from collections import defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from matplotlib.ticker import MaxNLocator
import numpy as np


COLORS = {"diamond": "#0072B2", "slab": "#009E73", "box": "#D55E00"}
MARKERS = {"diamond": "o", "slab": "^", "box": "s"}
METRIC_LABELS = {
    "connected2": "Size 2: connected probability",
    "motif22_4": "Size 4: 2+2 probability",
    "connected4": "Size 4: connected probability",
    "connected8": "Size 8: connected probability",
    "motif22_8": "Size 8: mean 2+2 density",
    "joint8": "Size 8: connected × 2+2 density",
    "tv4": "Size 4: full-profile total variation",
}


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def scientific_digest(raw_rows, references, summary, pairs, searches) -> str:
    """Content digest independent of timing, provenance and rendering metadata."""
    digest = hashlib.sha256()
    for name, value in (("raw_orders", raw_rows), ("references", references),
                        ("summary", summary), ("pairs", pairs), ("searches", searches)):
        digest.update(name.encode("ascii") + b"\n")
        if isinstance(value, list):
            for row in value:
                digest.update(canonical(row) + b"\n")
        else:
            digest.update(canonical(value) + b"\n")
    return digest.hexdigest()


def _json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True,
                              ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")


def _gzip(path: Path, value, *, lines: bool) -> None:
    with path.open("wb") as file:
        with gzip.GzipFile(filename="", fileobj=file, mode="wb", mtime=0) as stream:
            if lines:
                for row in value:
                    stream.write(canonical(row) + b"\n")
            else:
                stream.write(canonical(value) + b"\n")


def _csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as stream:
        if not fields:
            stream.write("\n")
            return
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: canonical(value).decode() if isinstance(value, (list, dict)) else value
                         for key, value in row.items()} for row in rows)


def _region(family: str) -> str | None:
    if family in {"diamond", "genuine"}:
        return "diamond"
    if family in {"slab", "central_slab", "central-slab"}:
        return "slab"
    return "box" if family == "box" else None


def _family_label(family: str) -> str:
    region = _region(family)
    return {"diamond": "Diamond", "slab": "Convex slab", "box": "Box (clipped)"}.get(
        region, family.replace("_", " "))


def _finite(value) -> bool:
    return value is not None and isinstance(value, (int, float, np.number)) and math.isfinite(value)


def _bounds(value):
    return value if isinstance(value, (list, tuple)) and len(value) == 2 and all(map(_finite, value)) else None


def _interval(ax, value, bounds, position, *, color, marker="o", horizontal=True,
              hollow=False, size=5, label=None):
    """Draw percentile intervals directly, allowing them not to bracket the point."""
    if not _finite(value):
        return
    ci = _bounds(bounds)
    if ci is not None:
        if horizontal:
            ax.plot(ci, [position, position], color=color, lw=1.3, alpha=.85)
            ax.plot(ci, [position, position], "|", color=color, ms=5)
        else:
            ax.plot([position, position], ci, color=color, lw=1.3, alpha=.85)
            ax.plot([position, position], ci, "_", color=color, ms=5)
    x, y = (value, position) if horizontal else (position, value)
    ax.plot(x, y, marker=marker, ls="", ms=size, mec=color,
            mfc="white" if hollow else color, color=color, label=label)


def _save(fig, out: Path, filename: str) -> str:
    fig.savefig(out / filename, dpi=190, bbox_inches="tight",
                metadata={"Software": "causal-spacetime-lab", "Description": "Experiment 4 numerical physics figure"})
    plt.close(fig)
    return filename


def _empty(ax, message="No defined observations"):
    ax.text(.5, .5, message, ha="center", va="center", transform=ax.transAxes, color="#64748b")


def _conditional_figure(summary, out):
    source = [row for row in summary.get("conditional", [])
              if _region(row.get("family", "")) and row.get("dimension") in (2, 3, 4)
              and row.get("reference_dimension", row.get("dimension")) == row.get("dimension")]
    n = max((row["count"] for row in source), default=0)
    rows = sorted((row for row in source if row["count"] == n),
                  key=lambda row: (row["dimension"], ("diamond", "slab", "box").index(_region(row["family"]))))
    fig, axes = plt.subplots(2, 4, figsize=(17.5, 8.4), squeeze=False)
    labels = [f"d={row['dimension']}  {_family_label(row['family'])}" for row in rows]
    for ax, metric in zip(axes.flat, METRIC_LABELS):
        ax.axvline(0, color="#64748b", lw=.7)
        tolerance = None
        for y, group in enumerate(rows):
            result = next((m for m in group["pooled"] if m["metric"] == metric), None)
            if result is None:
                continue
            tolerance = result.get("tolerance", tolerance)
            region = _region(group["family"])
            _interval(ax, result.get("difference"), result.get("ci95"), y,
                      color=COLORS[region], marker=MARKERS[region],
                      hollow=result.get("status") == "insufficient_information")
            if not _finite(result.get("difference")):
                ax.text(.98, y, "undefined", va="center", ha="right", fontsize=7,
                        transform=ax.get_yaxis_transform(), color="#64748b")
        if tolerance is not None:
            ax.axvspan(0 if metric == "tv4" else -tolerance, tolerance,
                       color="#cbd5e1", alpha=.45, zorder=-5)
        ax.set(title=METRIC_LABELS[metric], yticks=range(len(rows)), yticklabels=labels,
               xlabel="Conditional estimate − reference" if metric != "tv4" else "Mean fitwise total variation")
        ax.tick_params(axis="y", labelsize=7)
        ax.xaxis.set_major_locator(MaxNLocator(4))
        ax.set_ylim(len(rows) - .5, -.5)
        ax.grid(axis="x", alpha=.16)
        if not rows:
            _empty(ax)
    axes.flat[-1].axis("off")
    axes.flat[-1].text(0, .97,
        "Reading these intervals\n\n"
        "Bars: pointwise 95% hierarchical bootstrap.\n"
        "Parents and reference samples resampled\nindependently; intervals are not iid units.\n\n"
        "Shading: registered practical margins.\n"
        "Hollow markers: insufficient interval support.\n\n"
        "Diamond and slab test the convex-flat law.\n"
        "Box is a clipping control, not evidence\nof absent flat geometry.\n\n"
        "These are conditional-law comparisons,\nnot embedding certificates.",
        transform=axes.flat[-1].transAxes, va="top", fontsize=10, linespacing=1.4)
    fig.suptitle(f"Local interval laws at the largest event count, N={n}", fontsize=15)
    fig.tight_layout(rect=(0, 0, 1, .96), w_pad=2.2, h_pad=2)
    return _save(fig, out, "conditional_laws.png")


def _metric(group, name):
    return next((row for row in group.get("metrics", []) if row.get("metric") == name), {})


def _dimension_figure(summary, out):
    groups = [row for row in summary.get("conditional", [])
              if _region(row.get("family", "")) and row.get("dimension") in (2, 3, 4)
              and row.get("reference_dimension", row.get("dimension")) == row.get("dimension")]
    n = max((row["count"] for row in groups), default=0)
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.7), squeeze=False, sharey=True)
    for ax, region in zip(axes[0], ("diamond", "slab", "box")):
        ax.plot([2, 4], [2, 4], color="#94a3b8", ls=":", label="Supplied reference dimension")
        undefined = []
        for d in (2, 3, 4):
            row = next((row for row in groups if row["count"] == n and row["dimension"] == d
                        and _region(row["family"]) == region), None)
            if row is not None:
                local = row.get("local_dimension", {})
                _interval(ax, local.get("estimate"), local.get("ci95"), d - .065,
                          color="#0072B2", horizontal=False, label="Local size-2 interval estimator" if d == 2 else None)
            global_group = next((row for row in summary.get("global", [])
                                 if row["count"] == n and row.get("dimension") == d
                                 and _region(row.get("family", "")) == region), {})
            global_dim = _metric(global_group, "global_dimension")
            _interval(ax, global_dim.get("estimate"), global_dim.get("ci95"), d + .065,
                      color="#D55E00", marker="s", horizontal=False,
                      label="Mean global MM estimate" if d == 2 else None)
            if global_dim.get("undefined", 0):
                undefined.append(f"d{d}: {global_dim['undefined']} undefined global")
            if row is not None and not _finite(row.get("local_dimension", {}).get("estimate")):
                undefined.append(f"d{d}: undefined local")
        ax.set(title=_family_label(region), xlabel="Supplied dimension (evaluation only)",
               ylabel="Inferred dimension", xticks=[2, 3, 4], xlim=(1.8, 4.2))
        ax.grid(alpha=.16)
        if undefined:
            ax.text(.02, .98, "\n".join(undefined), fontsize=7, va="top", transform=ax.transAxes)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8)
    fig.suptitle(f"Global and local dimension summaries, N={n}; pointwise 95% bootstrap intervals", fontsize=13)
    fig.tight_layout(rect=(0, .10, 1, .94))
    return _save(fig, out, "dimension_reconstruction.png")


def _pair_figure(summary, pairs, out):
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.5))
    for ax, scaling, color in zip(axes, ("fixed", "inflated"), ("#0072B2", "#D55E00")):
        groups = sorted((row for row in summary.get("pairs", []) if row.get("scaling") == scaling),
                        key=lambda row: row["count"])
        if not groups:
            # Metadata alone suffices for the exact analytic contrast.
            groups = [{"count": n, "density_difference": next(
                row["expected_n22_difference"] for row in pairs if row["count"] == n and row["scaling"] == scaling) / math.comb(n, 4)}
                for n in sorted({row["count"] for row in pairs if row.get("scaling") == scaling})]
        x = [row["count"] for row in groups]
        y = [row.get("density_difference") for row in groups]
        if x and all(_finite(v) and v > 0 for v in y):
            ax.plot(x, y, "o-", color=color, label="Verified exact difference")
            ax.set_xscale("log", base=2)
            ax.set_yscale("log")
            ax.set_xticks(x, [str(n) for n in x])
            if scaling == "fixed":
                expected = [12 / ((n - 1) * (n - 2) * (n - 3)) for n in x]
                ax.plot(x, expected, color="#64748b", ls=":", label="Exact fixed-module formula")
            else:
                ax.axhline(3 / (128 * 4 ** 3), color="#64748b", ls=":", label="Fixed-q limit, q=4")
            ax.legend(fontsize=8)
        else:
            _empty(ax)
        ax.set(title="Fixed eight-event modules" if scaling == "fixed" else "Inflated modules, four base events",
               xlabel="Total event count N", ylabel="Difference in n22 / C(N,4)")
        ax.grid(alpha=.18, which="both")
    fig.suptitle("Exactly matched old summaries can hide local structure", fontsize=14)
    fig.text(.5, .015, "Pairs share full interval histograms, height and ordering fraction. Contrasts are exact; repeated bases do not supply independent noisy evidence.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .07, 1, .94))
    return _save(fig, out, "exact_pair_scaling.png")


def _fiber_figure(summary, out):
    groups = summary.get("searches", [])
    counts = sorted({row["count"] for row in groups})
    dimensions = sorted({row["dimension"] for row in groups}) or [2, 3, 4]
    fig, axes = plt.subplots(2, len(dimensions), figsize=(4.2 * len(dimensions), 7), squeeze=False)
    fit_colors = ("#0072B2", "#D55E00", "#009E73", "#CC79A7")
    for column, d in enumerate(dimensions):
        for i, n in enumerate(counts):
            group = next((r for r in groups if r["dimension"] == d and r["count"] == n), None)
            if group is None:
                continue
            fits = group.get("by_fit", [group])
            for j, fit in enumerate(fits):
                offset = (j - (len(fits) - 1) / 2) * .15
                for row_index, key in enumerate(("moved", "local_changed")):
                    value = fit.get(key, {})
                    _interval(axes[row_index, column], value.get("rate"), value.get("ci95"), i + offset,
                              color=fit_colors[j % len(fit_colors)], horizontal=False,
                              label=f"Fit {fit.get('fit', j)}" if i == 0 else None)
        for row_index, ylabel in enumerate(("Final labeled matrix changed", "Final local invariant changed")):
            ax = axes[row_index, column]
            ax.set(title=f"Donor dimension d={d}", ylabel=ylabel,
                   xticks=range(len(counts)), xticklabels=[f"{n}\n{n*n//64} attempts" for n in counts],
                   xlim=(-.5, max(.5, len(counts) - .5)),
                   ylim=(-.035, 1.04), xlabel="N and registered switch budget")
            ax.grid(axis="y", alpha=.18)
            if not groups:
                _empty(ax)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    if handles:
        axes[0, 0].legend(handles, labels, fontsize=8)
    fig.suptitle("Search inside exact old-statistic fibers: per-fit rates and 95% Wilson intervals", fontsize=13)
    fig.text(.5, .015, "Every donor is retained. Matrix movement alone does not prove nonisomorphism; frozen searches do not prove rigidity or infeasibility.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .055, 1, .95))
    return _save(fig, out, "fiber_search.png")


def _global_figure(summary, out):
    groups = [row for row in summary.get("global", [])
              if _metric(row, "n22_density") and not any(
                  word in row.get("family", "") for word in ("lex", "fiber", "search", "pair"))]
    counts = sorted({row["count"] for row in groups}) or [0]
    categories = sorted({(row["family"], row.get("dimension")) for row in groups},
                        key=lambda value: (0 if _region(value[0]) else 1, value[1] or 0, value[0]))
    fig, axes = plt.subplots(1, len(counts), figsize=(4.7 * len(counts), max(4.5, .34 * len(categories) + 1.8)), squeeze=False, sharex=True)
    for ax, n in zip(axes[0], counts):
        for y, (family, d) in enumerate(categories):
            group = next((r for r in groups if r["family"] == family and r.get("dimension") == d and r["count"] == n), {})
            value = _metric(group, "n22_density")
            region = _region(family)
            _interval(ax, value.get("estimate"), value.get("ci95"), y,
                      color=COLORS.get(region, "#7B3294"), marker=MARKERS.get(region, "D"))
        ax.axvline(1 / 24, color="#64748b", ls=":", lw=1)
        labels = [f"{_family_label(f)}" + (f" · d={d}" if d else "") for f, d in categories]
        ax.set(title=f"N={n}", yticks=range(len(categories)), yticklabels=labels,
               xlabel="Exact induced 2+2 count / C(N,4)")
        ax.tick_params(axis="y", labelsize=8)
        ax.set_ylim(len(categories) - .5, -.5)
        ax.grid(axis="x", alpha=.16)
        if not categories:
            _empty(ax)
    fig.suptitle("Global four-event pattern density; pointwise 95% bootstrap intervals", fontsize=14)
    fig.text(.5, .015, "Dotted 1/24 anchor applies to d=2 diamonds and two-rank orders only. Construction labels do not determine geometric embeddability.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .065, 1, .95), w_pad=2)
    return _save(fig, out, "global_two_plus_two.png")


def _joint_figure(raw_rows, out):
    rows = [row for row in raw_rows if _region(row.get("family", "")) and row.get("dimension") in (2, 3, 4)]
    n = max((row["count"] for row in rows), default=0)
    fig, axes = plt.subplots(3, 3, figsize=(12, 9.1), squeeze=False)
    edges = np.asarray([0, 1, 2, 3, 4, 8, 16, 32])
    ticklabels = ["0", "1", "2", "3", "4–7", "8–15", "16–31", "32–70"]
    im = None
    for i, region in enumerate(("diamond", "slab", "box")):
        for j, d in enumerate((2, 3, 4)):
            ax = axes[i, j]
            group = [row for row in rows if row["count"] == n and row["dimension"] == d and _region(row["family"]) == region]
            by_fit = defaultdict(list)
            for row in group:
                by_fit[row["fit"]].append(row)
            probabilities = []
            total_intervals = 0
            undefined = not by_fit
            for parents in by_fit.values():
                table = np.zeros((4, 8))
                for parent in parents:
                    for components, count22, number in parent["interval_m8_joint"]:
                        table[min(components, 4) - 1, np.searchsorted(edges, count22, side="right") - 1] += number
                total_intervals += int(table.sum())
                if table.sum() == 0:
                    undefined = True
                else:
                    probabilities.append(table / table.sum())
            if undefined:
                data = np.full((4, 8), np.nan)
            else:
                data = np.mean(probabilities, axis=0)
            im = ax.imshow(data, aspect="auto", cmap="Blues", norm=PowerNorm(.5, vmin=0, vmax=1))
            ax.set(title=f"{_family_label(region)}, d={d}\n{len(group)} parents; {total_intervals:,} size-8 intervals",
                   xticks=range(8), xticklabels=ticklabels, yticks=range(4), yticklabels=["1", "2", "3", "4+"],
                   xlabel="Internal induced 2+2 count", ylabel="Components")
            ax.tick_params(axis="x", labelrotation=45, labelsize=7)
            ax.title.set_fontsize(9)
            if undefined:
                _empty(ax, "Undefined in at least one fit")
    fig.suptitle(f"Joint local structure at N={n}: equal-fit pooled size-8 interval distributions", fontsize=13)
    fig.tight_layout(rect=(0, .045, .91, .95))
    cax = fig.add_axes((.93, .22, .015, .55))
    fig.colorbar(im, cax=cax, label="Descriptive probability (square-root color scale)")
    fig.text(.5, .012, "Overlapping intervals are dependent. Heatmaps display joint distributions; color cells are not independent hypothesis tests.",
             ha="center", fontsize=8)
    return _save(fig, out, "interval_joint_structure.png")


def _correlation_figure(summary, out):
    groups = [r for r in summary.get("correlations", []) if _region(r.get("family", "")) == "diamond"]
    n = max((row["count"] for row in groups), default=0)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.7))
    image = None
    for ax, d in zip(axes, (2, 3, 4)):
        group = next((row for row in groups if row["count"] == n and row.get("dimension") == d), None)
        if group is None:
            _empty(ax)
            ax.set_title(f"Diamond d={d}")
            continue
        matrix = np.asarray([[np.nan if value is None else value for value in row]
                             for row in group["matrix"]], dtype=float)
        names = [str(name).replace("_", " ") for name in group["metrics"]]
        image = ax.imshow(matrix, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set(title=f"Diamond d={d}", xticks=range(len(names)), xticklabels=names,
               yticks=range(len(names)), yticklabels=names)
        ax.tick_params(axis="x", labelrotation=60, labelsize=7)
        ax.tick_params(axis="y", labelsize=7)
    fig.suptitle(f"Descriptive correlations of declared observables, N={n}", fontsize=14)
    fig.tight_layout(rect=(0, .12, .93, .94), w_pad=2)
    if image is not None:
        cax = fig.add_axes((.945, .30, .012, .40))
        fig.colorbar(image, cax=cax, label="Correlation")
    fig.text(.5, .025, "Some dependencies are exact algebraic identities. Correlation does not establish independent information or geometric reconstruction.\nUndefined correlations are left blank; no singular covariance inversion is used.",
             ha="center", fontsize=8)
    return _save(fig, out, "structural_correlations.png")


def _witness_figure(out):
    from .adversarial_features import nondual_pair
    from .local_generators import cover_relations
    from .local_structure import local_observables
    first, second = nondual_pair()
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.4))
    for ax, order, name in zip(axes[:2], (first, second), ("P: connected interior", "Q: disconnected interior")):
        positions = {0: (0., 0.), 9: (0., 3.)}
        positions.update({i + 1: (i - 1.5, 1.) for i in range(4)})
        positions.update({i + 5: (i - 1.5, 2.) for i in range(4)})
        for a, b in np.argwhere(cover_relations(order)):
            ax.annotate("", xy=positions[int(b)], xytext=positions[int(a)],
                        arrowprops={"arrowstyle": "->", "color": "#94a3b8", "lw": 1,
                                    "shrinkA": 6, "shrinkB": 6})
        ax.scatter(*np.asarray(list(positions.values())).T, color="#0072B2", s=65, zorder=3)
        row = local_observables(order)
        ax.set(title=f"{name}\nInduced 2+2 count = {row['n22']}", xlim=(-2, 2), ylim=(-.3, 3.3))
        ax.axis("off")
    row = local_observables(first)
    axes[2].bar(range(len(row["interval_histogram"])), row["interval_histogram"], color="#009E73")
    axes[2].set(title="Identical complete interval histogram", xlabel="Open-interval cardinality m",
                ylabel="Number of related endpoint pairs", xticks=range(9))
    fig.suptitle("An exact finite ambiguity resolved by local structure: N=10, R=25, H=4", fontsize=13)
    fig.text(.5, .015, "Removing the unique extrema leaves a connected eight-cycle versus two components. This demonstrates information loss, not a spacetime test.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .065, 1, .93))
    return _save(fig, out, "exact_structural_witness.png")


def make_figures(output_dir, raw_rows, summary, pairs) -> list[str]:
    """Render eight standalone figures without changing scientific records."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with plt.rc_context({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "white", "savefig.facecolor": "white"}):
        return [_conditional_figure(summary, out), _dimension_figure(summary, out),
                _pair_figure(summary, pairs, out), _fiber_figure(summary, out),
                _global_figure(summary, out), _joint_figure(raw_rows, out),
                _correlation_figure(summary, out), _witness_figure(out)]


def write_artifacts(output_dir, raw_rows, references, summary, pairs, searches,
                    metadata) -> dict:
    """Write auditable data, flattened tables, figures and an artifact manifest.

    The caller supplies run/source/resource provenance. It is retained in
    metadata.json but excluded from the scientific digest. Gzip headers have
    zero timestamps and no filenames, so equal scientific inputs yield equal
    archive bytes. No NaN or Infinity is silently coerced into JSON.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    _gzip(out / "raw_orders.jsonl.gz", raw_rows, lines=True)
    _gzip(out / "references.json.gz", references, lines=False)
    _gzip(out / "pairs.jsonl.gz", pairs, lines=True)
    _gzip(out / "searches.jsonl.gz", searches, lines=True)
    _json(out / "summary.json", summary)
    conditional = []
    for group in summary.get("conditional", []):
        keys = {key: group.get(key) for key in ("family", "dimension", "reference_dimension", "count", "fit_count", "parent_count")}
        conditional.extend(keys | {"scope": "across_fits"} | row for row in group["pooled"])
        for fit in group.get("fits", []):
            conditional.extend(keys | {"scope": "within_fit", "fit": fit["fit"]} | row for row in fit["metrics"])
    _csv(out / "conditional.csv", conditional)
    global_rows = []
    for group in summary.get("global", []):
        global_rows.extend({key: group.get(key) for key in ("family", "dimension", "count")} | row
                           for row in group["metrics"])
    _csv(out / "global.csv", global_rows)
    _csv(out / "pairs.csv", summary.get("pairs", []))
    _csv(out / "searches.csv", summary.get("searches", []))
    figure_names = make_figures(out, raw_rows, summary, pairs)
    owned_names = ["raw_orders.jsonl.gz", "references.json.gz", "pairs.jsonl.gz",
                   "searches.jsonl.gz", "summary.json", "conditional.csv", "global.csv",
                   "pairs.csv", "searches.csv", *figure_names]
    result = dict(metadata)
    result.update(scientific_sha256=scientific_digest(raw_rows, references, summary, pairs, searches),
                  parent_checkpoint_records=len(raw_rows), exact_pairs=len(pairs),
                  fiber_searches=len(searches), figures=figure_names,
                  scientific_digest_scope="canonical raw orders, references, summaries, exact-pair and search records; excludes timing/provenance metadata and figures",
                  artifact_sha256={name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                                   for name in sorted(owned_names)})
    _json(out / "metadata.json", result)
    entries = [{"name": path.name, "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "kind": "figure" if path.suffix == ".png" else "metadata" if path.name == "metadata.json" else "scientific_data"}
               for path in (out / name for name in sorted([*owned_names, "metadata.json"]))]
    _json(out / "manifest.json", {"scientific_sha256": result["scientific_sha256"], "artifacts": entries})
    return result
