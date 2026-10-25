"""Deterministic archives and scientific figures for intrinsic-growth histories.

Plots distinguish whole-history uncertainty, prescribed controls and the
necessary finite signature from any claim of geometric emergence. Undefined
values remain absent. The scientific digest excludes provenance and rendering.
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
from matplotlib.colors import LogNorm
from matplotlib.ticker import MaxNLocator
import numpy as np


PARAMETERS = (.005, .01, .02, .05, .1, .3)
PREFIXES = (32, 64, 128, 256, 512)
COLORS = ("#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00", "#4C5578")
CONTROL_COLORS = {2: "#0072B2", 3: "#009E73", 4: "#CC79A7",
                  "semiorder": "#707070", "matched_bipartite": "#D55E00"}
CONDITIONAL_LABELS = {
    "connected2": "m=2: connected probability",
    "motif22_4": "m=4: 2+2 probability",
    "connected4": "m=4: connected probability",
    "connected8": "m=8: connected probability",
    "motif22_8": "m=8: mean 2+2 density",
    "joint8": "m=8: connected × 2+2 density",
    "tv4": "m=4: full-profile total variation",
}
PRIMARY_LABELS = {
    "level_128": "N128 − 1/24", "level_256": "N256 − 1/24",
    "level_512": "N512 − 1/24", "drift_128_256": "N256 − N128",
    "drift_256_512": "N512 − N256", "thin_128_64": "Thin128→64 − prefix64",
    "thin_256_128": "Thin256→128 − prefix128",
    "thin_512_256": "Thin512→256 − prefix256",
}


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def _json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True,
                                    ensure_ascii=True, allow_nan=False) + "\n",
                          encoding="utf-8")


def write_gzip(path, value, *, lines=True):
    """Write reproducible gzip: no filename, zero timestamp, canonical JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        with gzip.GzipFile(filename="", fileobj=file, mode="wb", mtime=0) as stream:
            if lines:
                for row in value:
                    stream.write(canonical(row) + b"\n")
            else:
                stream.write(canonical(value) + b"\n")


def _csv(path, rows):
    rows = list(rows)
    fields = sorted({key for row in rows for key in row})
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        if not fields:
            stream.write("\n")
            return
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: canonical(value).decode("utf-8")
                         if isinstance(value, (dict, list, tuple)) else value
                         for key, value in row.items()} for row in rows)


def _relative_file(out, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("artifact names must be relative paths within the output directory")
    result = out / path
    if not result.is_file() or not result.resolve().is_relative_to(out.resolve()):
        raise ValueError(f"missing or external artifact: {name}")
    return result


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _history_rows(out, records):
    if isinstance(records, (str, Path)):
        with gzip.open(_relative_file(out, records), "rt", encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    yield json.loads(line)
    else:
        yield from records


def scientific_digest(output_dir, summaries, primary, references, history_records,
                      raw_files):
    """Hash scientific values and exact raw-shard bytes; omit runtime metadata.

    History records can be an in-memory sequence or an existing relative gzip
    JSON-lines filename. Their canonical record stream has the same digest in
    either representation. Reference values are the decoded JSON structures.
    """
    out = Path(output_dir)
    digest = hashlib.sha256()
    for name, value in (("summaries", summaries), ("primary", primary),
                        ("references", references)):
        digest.update(name.encode("ascii") + b"\n" + canonical(value) + b"\n")
    digest.update(b"histories\n")
    for row in _history_rows(out, history_records):
        digest.update(canonical(row) + b"\n")
    for name in sorted(map(str, raw_files)):
        path = _relative_file(out, name)
        digest.update(b"raw:" + name.encode("utf-8") + b"\n")
        digest.update(str(path.stat().st_size).encode("ascii") + b"\n")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\n")
    return digest.hexdigest()


def _finite(value):
    return value is not None and isinstance(value, (int, float, np.number)) and math.isfinite(value)


def _bounds(value):
    return value if isinstance(value, (list, tuple)) and len(value) == 2 and all(map(_finite, value)) else None


def _label(group):
    family, parameter = group["family"], group["parameter"]
    if family == "percolation":
        return f"p={float(parameter):g}"
    if family == "minkowski":
        return f"Minkowski d={int(parameter)}"
    if family == "semiorder":
        return "Semiorder c=0.25"
    if family == "matched_bipartite":
        return "Matched 2+2, height ≤2"
    return f"{family}: {parameter}"


def _sort_key(group):
    family = group["family"]
    return ({"percolation": 0, "minkowski": 1, "semiorder": 2,
             "matched_bipartite": 3}.get(family, 4), float(group["parameter"]))


def _color(group):
    if group["family"] == "percolation":
        parameter = float(group["parameter"])
        return COLORS[PARAMETERS.index(parameter)] if parameter in PARAMETERS else "#444444"
    return CONTROL_COLORS.get(int(group["parameter"]) if group["family"] == "minkowski"
                              else group["family"], "#444444")


def _marker(group):
    return {"percolation": "o", "minkowski": "s", "semiorder": "^",
            "matched_bipartite": "D"}.get(group["family"], "o")


def _metric(cell, name):
    return next((row for row in cell.get("metrics", []) if row["metric"] == name), {})


def _interval(ax, estimate, bounds, position, *, color, marker="o", horizontal=True,
              hollow=False, label=None, size=4):
    if not _finite(estimate):
        return False
    ci = _bounds(bounds)
    if ci is not None:
        if horizontal:
            ax.plot(ci, [position, position], color=color, lw=1.1, alpha=.85)
            ax.plot(ci, [position, position], "|", color=color, ms=4)
        else:
            ax.plot([position, position], ci, color=color, lw=1.1, alpha=.85)
            ax.plot([position, position], ci, "_", color=color, ms=4)
    x, y = (estimate, position) if horizontal else (position, estimate)
    ax.plot(x, y, marker=marker, linestyle="", ms=size, color=color,
            mec=color, mfc="white" if hollow else color, label=label)
    return True


def _empty(ax, message="No defined observations"):
    ax.text(.5, .5, message, ha="center", va="center", transform=ax.transAxes,
            color="#64748b", fontsize=9)


def _save(fig, out, name, run_label=""):
    if run_label:
        fig.text(.995, .995, run_label, ha="right", va="top", fontsize=8,
                 color="#9a3412")
    fig.savefig(out / name, dpi=180, bbox_inches="tight",
                metadata={"Software": "causal-spacetime-lab",
                          "Description": "Experiment 5 intrinsic-growth study"})
    plt.close(fig)
    return name


def _prefix_axis(ax):
    ax.set_xscale("log", base=2)
    ax.set_xticks(PREFIXES, [str(n) for n in PREFIXES])
    ax.set_xlabel("Prefix event count N")
    ax.grid(alpha=.15)


def _plot_metric(ax, groups, metric):
    for group in groups:
        cells = sorted((cell for cell in group.get("global_cells", [])
                        if cell["stage"] == "prefix"), key=lambda cell: cell["count"])
        x = [cell["count"] for cell in cells]
        values = [_metric(cell, metric) for cell in cells]
        y = [row.get("estimate") if _finite(row.get("estimate")) else np.nan for row in values]
        color = _color(group)
        ax.plot(x, y, color=color, lw=1.2, alpha=.9, label=_label(group),
                marker=_marker(group), ms=3)
        for n, row in zip(x, values):
            _interval(ax, row.get("estimate"), row.get("ci95"), n,
                      color=color, marker=_marker(group), horizontal=False, size=3)
    _prefix_axis(ax)
    if not groups:
        _empty(ax)


def _history_figure(out, trajectories, run_label=""):
    fig, axes = plt.subplots(2, 3, figsize=(13.8, 8.0), sharex=True, sharey=True)
    for ax, parameter, color in zip(axes.flat, PARAMETERS, COLORS):
        by_history = defaultdict(list)
        for row in trajectories:
            if (row.get("family") == "percolation" and float(row["parameter"]) == parameter
                    and row.get("stage") == "prefix" and row.get("batch") == 0
                    and row.get("history_number", 99) < 8):
                by_history[row["history_id"]].append(row)
        for rows in by_history.values():
            rows.sort(key=lambda row: row["count"])
            ax.plot([row["count"] for row in rows],
                    [row.get("n22_density", row["n22"] / math.comb(row["count"], 4)) for row in rows],
                    color=color, alpha=.5, lw=.9, marker="o", ms=2)
        ax.axhline(1 / 24, color="#333333", ls="--", lw=1)
        ax.set(title=f"Fixed p={parameter:g}", ylabel="Exact induced 2+2 density")
        _prefix_axis(ax)
        if not by_history:
            _empty(ax)
    fig.suptitle("Individual intrinsic-growth histories: a prescribed selection", fontsize=14)
    fig.text(.5, .02, "Histories 0–7 in batch 0; no outcome selection. Dashed: d=2 diamond expectation 1/24.\n"
             "Fixed positive p has an almost-sure chain sampling limit; finite agreement does not establish emergence.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .09, 1, .95), h_pad=2)
    return _save(fig, out, "selected_history_22.png", run_label)


def _dynamics_figure(out, groups, run_label=""):
    growth = [g for g in groups if g["family"] == "percolation"]
    controls = [g for g in groups if g["family"] != "percolation"]
    fig, axes = plt.subplots(2, 3, figsize=(15, 9.4))
    for i, subset in enumerate((growth, controls)):
        for ax, metric, label in zip(axes[i], ("ordering_fraction", "height_fraction", "global_dimension"),
                                     ("Ordering fraction r", "Maximum chain / N",
                                      "Global reference-equivalent dimension")):
            _plot_metric(ax, subset, metric)
            ax.set_ylabel(label)
            ax.set_title(("Intrinsic growth" if i == 0 else "Prescribed references and controls") + " — " + label)
        axes[i, 0].legend(fontsize=7.5, ncol=2, loc="best")
    fig.suptitle("Changing relation density, height and reference-equivalent diagnostics", fontsize=14)
    fig.text(.5, .018, "Pointwise 95% whole-history bootstrap intervals. Undefined inversions are absent; diagnostic values are not physical dimensions.\n"
             "Minkowski prefixes are nested iid samples, not natural birth histories. Controls do not define candidate growth laws.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .08, 1, .95), w_pad=2, h_pad=2.4)
    return _save(fig, out, "ensemble_dynamics.png", run_label)


def _ensemble_figure(out, groups, run_label=""):
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.5), sharey=True)
    for ax, subset, title in zip(axes, ([g for g in groups if g["family"] == "percolation"],
                                       [g for g in groups if g["family"] != "percolation"]),
                                 ("Fixed-p growth laws", "Independent prescribed controls")):
        _plot_metric(ax, subset, "t22")
        ax.axhline(1 / 24, ls="--", color="#333333", lw=1, label="d=2 diamond: 1/24")
        ax.set(title=title, ylabel="Exact induced 2+2 density")
        ax.legend(fontsize=8, ncol=2)
    fig.suptitle("Ensemble 2+2 density across all registered sizes", fontsize=14)
    fig.text(.5, .018, "Pointwise 95% history-bootstrap intervals. The height-two control matches 1/24 analytically at every size.\n"
             "Matching this single necessary statistic neither certifies geometry nor evades the fixed-p asymptotic obstruction.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .11, 1, .94))
    return _save(fig, out, "ensemble_22.png", run_label)


def _joint_figure(out, groups, run_label=""):
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 6.4))
    for ax, metric, label in zip(axes, ("t22", "t31"), ("Induced 2+2 density", "Induced 3+1 density")):
        for group in groups:
            cells = sorted((cell for cell in group.get("global_cells", [])
                            if cell["stage"] == "prefix"), key=lambda cell: cell["count"])
            points = [(_metric(cell, "ordering_fraction").get("estimate"),
                       _metric(cell, metric).get("estimate"), cell["count"]) for cell in cells]
            points = [p for p in points if _finite(p[0]) and _finite(p[1])]
            if points:
                ax.plot([p[0] for p in points], [p[1] for p in points], color=_color(group),
                        marker=_marker(group), ms=4, lw=1, label=_label(group),
                        ls="-" if group["family"] == "percolation" else "--")
                ax.scatter(points[-1][0], points[-1][1], s=55, facecolors="none",
                           edgecolors=_color(group), linewidths=1)
        ax.set(xlabel="Mean ordering fraction", ylabel=label,
               title=f"{label} versus relation density")
        ax.grid(alpha=.18)
    axes[0].axhline(1 / 24, ls=":", color="#555555", lw=1)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=8,
               bbox_to_anchor=(.5, .075))
    fig.suptitle("Joint structural trajectories; increasing N follows each connected series", fontsize=14)
    fig.text(.5, .015, "Open outer rings mark N=512; lines connect ensemble means, not independent features.\n"
             "Controls show why ordering fraction and one forbidden motif do not identify geometry.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .20, 1, .94))
    return _save(fig, out, "forbidden_motif_joint.png", run_label)


def _screen_reports(primary):
    """Accept one screen or a named collection of primary/control screens."""
    if isinstance(primary, dict) and isinstance(primary.get("families"), list):
        yield "screen", primary
    elif isinstance(primary, dict):
        for name, value in primary.items():
            if name in {"endpoints", "metadata"}:
                continue
            if isinstance(value, dict) and isinstance(value.get("families"), list):
                yield name, value
            elif isinstance(value, (dict, list)):
                for child_name, child in _screen_reports(value):
                    yield f"{name}/{child_name}", child
    elif isinstance(primary, list):
        for index, value in enumerate(primary):
            for child_name, child in _screen_reports(value):
                yield f"{index}/{child_name}", child


def _primary_figure(out, primary, run_label=""):
    reports = list(_screen_reports(primary))
    growth_reports = [report for _, report in reports
                      if any(f["family"] == "percolation" for f in report["families"])]
    families = [family for report in growth_reports for family in report["families"]
                if family["family"] == "percolation"]
    entry_count = sum(report["entry_count"] for report in growth_reports)
    fig, axes = plt.subplots(2, 3, figsize=(15.8, 9.5))
    labels = list(PRIMARY_LABELS.values())
    for ax, p, color in zip(axes.flat, PARAMETERS, COLORS):
        ax.axvspan(-.005, .005, color="#cbd5e1", alpha=.6)
        ax.axvline(0, color="#555555", lw=.7)
        group = next((g for g in families if float(g["parameter"]) == p), None)
        if group:
            by_name = {row["name"]: row for row in group["entries"]}
            for y, name in enumerate(PRIMARY_LABELS):
                row = by_name.get(name, {})
                _interval(ax, row.get("estimate"), row.get("band"), y, color=color,
                          hollow=bool(row.get("degeneracy_guard")))
            title = group["status"].replace("finite_window_compatible", "finite-window compatible").replace(
                "finite_signature_failure", "finite signature fails")
        else:
            title = "screen unavailable"
            _empty(ax)
        ax.set(title=f"p={p:g}: {title}", yticks=range(8), yticklabels=labels,
               ylim=(7.6, -.6), xlabel="Density difference")
        ax.tick_params(axis="y", labelsize=7)
        ax.grid(axis="x", alpha=.16)
        ax.xaxis.set_major_locator(MaxNLocator(4))
    fig.suptitle("Registered necessary signature: eight contrasts for each fixed p", fontsize=14)
    fig.text(.5, .02, f"Bars: simultaneous {entry_count}-entry bands with registered degeneracy safeguards; shading: ±0.005. Hollow points have a safeguard.\n"
             "Coverage is approximate. This is a finite-window diagnostic, not a spacetime classifier or continuum test.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .09, 1, .95), w_pad=2.1, h_pad=2.2)
    return _save(fig, out, "primary_signature.png", run_label)


def _thinning_figure(out, groups, run_label=""):
    fig, axes = plt.subplots(3, 3, figsize=(15.6, 13.8))
    labels = [_label(g) for g in groups]
    for i, source in enumerate((128, 256, 512)):
        for j, (metric, name) in enumerate((("ordering_fraction", "Ordering fraction"),
                                          ("height_fraction", "Height / N"), ("t22", "2+2 density"))):
            ax = axes[i, j]
            ax.axvline(0, color="#555555", lw=.8)
            for y, group in enumerate(groups):
                contrast = next((c for c in group.get("global_contrasts", [])
                                 if c["right"]["stage"] == "thinned"
                                 and c["right"]["source_count"] == source), {})
                row = _metric(contrast, metric)
                _interval(ax, row.get("estimate"), row.get("ci95"), y,
                          color=_color(group), marker=_marker(group))
            ax.set(title=f"{source}→{source // 2}: {name}",
                   yticks=range(len(groups)), yticklabels=labels,
                   ylim=(len(groups) - .4, -.6), xlabel="Thinned − same-size prefix")
            ax.tick_params(axis="y", labelsize=7)
            ax.grid(axis="x", alpha=.15)
            ax.xaxis.set_major_locator(MaxNLocator(4))
    fig.suptitle("Paired thinning-minus-prefix contrasts: one history remains one sampling unit", fontsize=14)
    fig.text(.5, .012, "Four thinnings are averaged within each history; bars are pointwise 95% paired history-bootstrap intervals.\n"
             "Induced thinning is motif-unbiased conditional on ANY parent, but a thinned growth order need not share a smaller birth-prefix law.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .065, 1, .96), w_pad=2, h_pad=2.1)
    return _save(fig, out, "thinning_contrasts.png", run_label)


def _largest_conditional(groups):
    result = []
    for group in groups:
        dimension = int(group["parameter"]) if group["family"] == "minkowski" else 2
        cells = [cell for cell in group.get("conditional_cells", [])
                 if cell["stage"] == "prefix" and cell["dimension"] == dimension]
        if cells:
            result.append((group, max(cells, key=lambda cell: cell["count"])))
    return result


def _conditional_figure(out, groups, run_label=""):
    selected = _largest_conditional(groups)
    labels = [f"{_label(g)} → d={c['dimension']}" for g, c in selected]
    fig, axes = plt.subplots(2, 4, figsize=(19.6, 10.5))
    for ax, (name, title) in zip(axes.flat, CONDITIONAL_LABELS.items()):
        ax.axvline(0, color="#555555", lw=.7)
        tolerance = None
        for y, (group, cell) in enumerate(selected):
            row = next((m for m in cell["pooled"] if m["metric"] == name), {})
            tolerance = row.get("tolerance", tolerance)
            defined = _interval(ax, row.get("difference"), row.get("ci95"), y,
                                color=_color(group), marker=_marker(group),
                                hollow=row.get("status") == "insufficient_information")
            if not defined:
                ax.text(.98, y, "undefined", transform=ax.get_yaxis_transform(),
                        ha="right", va="center", fontsize=7, color="#777777")
        if tolerance is not None:
            ax.axvspan(0 if name == "tv4" else -tolerance, tolerance,
                       color="#cbd5e1", alpha=.5, zorder=-5)
        ax.set(title=title, yticks=range(len(selected)), yticklabels=labels,
               ylim=(len(selected) - .4, -.6), xlabel="Estimate − reference" if name != "tv4"
               else "Mean batchwise TV")
        ax.tick_params(axis="y", labelsize=6.8)
        ax.grid(axis="x", alpha=.16)
        ax.xaxis.set_major_locator(MaxNLocator(4))
    axes.flat[-1].axis("off")
    axes.flat[-1].text(0, .97,
        "Interpretation\n\nLargest recorded prefix in each family.\n"
        "Growth/artificial controls: d=2 reference.\nMinkowski: its supplied dimension.\n"
        "All other comparisons remain in tables.\n\n"
        "Bars: pointwise 95% intervals; parent\nhistories and calibration are independent.\n"
        "Hollow: registered support rule not met.\nMissing estimates remain undefined.\n\n"
        "Shading: Experiment 4 practical margins.\nTV bootstrap has nonsmooth limitations.\n"
        "Agreement is not an embedding certificate.",
        va="top", fontsize=9, linespacing=1.4, transform=axes.flat[-1].transAxes)
    fig.suptitle("Conditional flat-reference laws at the largest prefix", fontsize=14)
    fig.tight_layout(rect=(0, .01, 1, .95), w_pad=2.0, h_pad=2.1)
    return _save(fig, out, "conditional_laws.png", run_label)


def _support_figure(out, groups, run_label=""):
    selected = _largest_conditional(groups)
    positive, exposure = [], []
    for _, cell in selected:
        pos, exp = [], []
        for size in (2, 4, 8):
            row = next((m for m in cell["pooled"] if m.get("interval_size") == size), {})
            support = row.get("support", {}).get("by_batch", [])
            pos.append(min((x["positive_histories"] for x in support), default=np.nan))
            exp.append(min((x["mean_interval_exposure"] for x in support), default=np.nan))
        positive.append(pos)
        exposure.append(exp)
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 7.8))
    labels = [_label(g) for g, _ in selected]
    for ax, data, title, threshold in zip(axes, (positive, exposure),
                                         ("Minimum positive histories per batch", "Minimum interval exposure per batch"),
                                         (30, 100)):
        if data:
            matrix = np.asarray(data, dtype=float)
            # A positive offset permits true zero support without treating it
            # as missing; annotations always display the untransformed value.
            displayed = np.ma.masked_invalid(matrix + 1)
            finite = matrix[np.isfinite(matrix)]
            maximum = max(2, float(finite.max()) + 1) if len(finite) else 2
            im = ax.imshow(displayed, cmap="Blues", aspect="auto",
                           norm=LogNorm(vmin=1, vmax=maximum))
            for y in range(len(data)):
                for x in range(3):
                    value = matrix[y, x]
                    label = "undefined" if not np.isfinite(value) else f"{value:,.0f}"
                    ax.text(x, y, label, ha="center", va="center", fontsize=8,
                            color="#b91c1c" if np.isfinite(value) and value < threshold else "#111111",
                            bbox={"facecolor": "white", "alpha": .8, "edgecolor": "none", "pad": 1})
            colorbar = fig.colorbar(im, ax=ax, fraction=.035, pad=.025)
            colorbar.set_label("Support + 1 (log color scale)", fontsize=8)
        else:
            _empty(ax)
        ax.set(title=f"{title}\nRequired ≥{threshold} in every batch", xticks=[0, 1, 2],
               xticklabels=["m=2", "m=4", "m=8"], yticks=range(len(labels)), yticklabels=labels,
               xlabel="Open-interval cardinality")
        ax.tick_params(axis="y", labelsize=8)
    fig.suptitle("Interval support at the largest prefix; minimum across independent batches", fontsize=14)
    fig.text(.5, .015, "Red numbers fail a registered threshold. Zero support is a real count; undefined quantities remain blank.\n"
             "Many intervals from one order do not replace independent parent histories.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .08, 1, .94), w_pad=3)
    return _save(fig, out, "interval_support.png", run_label)


def _dimension_figure(out, groups, run_label=""):
    selected = _largest_conditional(groups)
    fig, ax = plt.subplots(figsize=(11.5, 7.4))
    for d in (2, 3, 4):
        ax.axvline(d, color="#b0b0b0", ls=":", lw=.8)
    for y, (group, cell) in enumerate(selected):
        global_cell = next((c for c in group["global_cells"]
                            if c["stage"] == "prefix" and c["count"] == cell["count"]), {})
        local = cell.get("local_dimension", {})
        glob = _metric(global_cell, "global_dimension")
        for value, offset, color, marker, label in ((glob, -.12, "#D55E00", "s", "Global MM diagnostic"),
                                                   (local, .12, "#0072B2", "o", "Local m=2 diagnostic")):
            defined = _interval(ax, value.get("estimate"), value.get("ci95"), y + offset,
                                color=color, marker=marker, label=label if y == 0 else None)
            if not defined:
                ax.text(.99, y + offset, label.split()[0] + " undefined", fontsize=7,
                        color=color, transform=ax.get_yaxis_transform(), ha="right", va="center")
    ax.set(yticks=range(len(selected)), yticklabels=[_label(g) for g, _ in selected],
           ylim=(len(selected) - .5, -.5), xlabel="Reference-equivalent dimension",
           title="Global and local inversions at the largest prefix")
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.60, .075),
               ncol=2, fontsize=9)
    ax.grid(axis="x", alpha=.17)
    fig.text(.5, .015, "Pointwise 95% intervals and original inversion domains; undefined estimates are not replaced or clipped.\n"
             "A reference-equivalent value is a sampling diagnostic, not evidence that a growth order has that physical dimension.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .15, 1, .97))
    return _save(fig, out, "reference_equivalent_dimensions.png", run_label)


def make_figures(output_dir, summaries, primary, trajectories, *, run_label=""):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    groups = sorted(summaries, key=_sort_key)
    with plt.rc_context({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "white", "savefig.facecolor": "white"}):
        return [_history_figure(out, trajectories, run_label), _dynamics_figure(out, groups, run_label),
                _ensemble_figure(out, groups, run_label), _joint_figure(out, groups, run_label),
                _primary_figure(out, primary, run_label), _thinning_figure(out, groups, run_label),
                _conditional_figure(out, groups, run_label), _support_figure(out, groups, run_label),
                _dimension_figure(out, groups, run_label)]


def _tables(summaries, primary):
    tables = {name: [] for name in ("global", "global_contrasts", "conditional",
                                   "conditional_contrasts", "primary")}
    for group in summaries:
        identity = {key: group[key] for key in ("family", "parameter", "history_count")}
        for cell in group.get("global_cells", []):
            base = identity | {key: value for key, value in cell.items() if key != "metrics"}
            tables["global"].extend(base | row for row in cell["metrics"])
        for contrast in group.get("global_contrasts", []):
            base = identity | {key: value for key, value in contrast.items() if key != "metrics"}
            tables["global_contrasts"].extend(base | row for row in contrast["metrics"])
        for cell in group.get("conditional_cells", []):
            base = identity | {key: cell[key] for key in ("cell", "stage", "source_count", "count", "dimension")}
            tables["conditional"].extend(base | {"scope": "equal_batch_mean"} | row for row in cell["pooled"])
            for fit in cell.get("fits", []):
                tables["conditional"].extend(base | {"scope": "within_batch", "batch": fit["batch"]} | row
                                             for row in fit["metrics"])
        for contrast in group.get("conditional_contrasts", []):
            base = identity | {key: value for key, value in contrast.items() if key != "metrics"}
            tables["conditional_contrasts"].extend(base | row for row in contrast["metrics"])
    for scope, report in _screen_reports(primary):
        for family in report["families"]:
            base = {"scope": scope, "family": family["family"], "parameter": family["parameter"],
                    "family_status": family["status"], "screen_entry_count": report["entry_count"]}
            tables["primary"].extend(base | row for row in family["entries"])
    return tables


def write_artifacts(output_dir, summaries, primary, references, history_records,
                    raw_files, metadata, trajectories):
    """Write tables, figures and manifest around pre-existing raw family shards.

    ``references`` and ``history_records`` may be in-memory sequences or existing
    relative gzip filenames. The latter avoids keeping reconstruction records
    in memory. Supplied sequences are written here using deterministic gzip.
    Metadata and figures are archived but excluded from the scientific digest.
    Existing files not named as inputs or outputs are neither removed nor added
    silently to the manifest. CSV files use LF line terminators on every OS.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_files = sorted(map(str, raw_files))
    if len(raw_files) != len(set(raw_files)):
        raise ValueError("duplicate raw artifact paths")
    for name in raw_files:
        _relative_file(out, name)
    if isinstance(references, (str, Path)):
        reference_name = str(references)
        with gzip.open(_relative_file(out, reference_name), "rt", encoding="utf-8") as stream:
            references = json.load(stream)
    else:
        reference_name = "references.json.gz"
        write_gzip(out / reference_name, references, lines=False)
    if isinstance(history_records, (str, Path)):
        history_name = str(history_records)
        _relative_file(out, history_name)
    else:
        history_name = "histories.jsonl.gz"
        write_gzip(out / history_name, history_records, lines=True)
    history_count = sum(1 for _ in _history_rows(out, history_name))
    _json(out / "summary.json", summaries)
    _json(out / "primary.json", primary)
    write_gzip(out / "selected_trajectories.jsonl.gz", trajectories, lines=True)
    table_names = []
    for name, rows in _tables(summaries, primary).items():
        filename = name + ".csv"
        _csv(out / filename, rows)
        table_names.append(filename)
    config = metadata.get("config", {})
    smoke = metadata.get("run_kind") == "smoke" or config.get("smoke", False)
    run_label = "SMOKE CHECK — reduced workload; not primary evidence" if smoke else ""
    figures = make_figures(out, summaries, primary, trajectories, run_label=run_label)
    owned = sorted(set([*raw_files, reference_name, history_name, "summary.json", "primary.json",
                        "selected_trajectories.jsonl.gz", *table_names, *figures]))
    digest = scientific_digest(out, summaries, primary, references, history_name, raw_files)
    result = dict(metadata)
    result.update(scientific_sha256=digest, figures=figures, history_records=history_count,
                  family_summaries=len(summaries), raw_files=raw_files,
                  scientific_digest_scope="canonical summaries, primary screens, references and history records; exact raw gzip bytes; excludes timings, provenance, tables derived from summaries, selected-trajectory copies and rendered figures",
                  artifact_sha256={name: _sha256(out / name) for name in owned})
    _json(out / "metadata.json", result)
    entries = [{"name": name, "bytes": (out / name).stat().st_size, "sha256": _sha256(out / name),
                "kind": "figure" if name.endswith(".png") else "metadata" if name == "metadata.json"
                else "scientific_data"} for name in sorted([*owned, "metadata.json"])]
    _json(out / "manifest.json", {"scientific_sha256": digest, "artifacts": entries,
                                  "manifest_scope": "all declared input shards and writer-owned outputs; manifest does not hash itself"})
    return result
