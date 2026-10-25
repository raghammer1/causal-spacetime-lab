"""Run a deterministic benchmark that generates CSV and figures."""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .core import sprinkle, longest_chain_fast, inferred_duration


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconstruct proper time from causal chains")
    parser.add_argument("--seed", type=int, default=20261025)
    parser.add_argument("--repeats", type=int, default=100)
    parser.add_argument("--duration", type=float, default=1.0)
    parser.add_argument("--densities", type=float, nargs="+", default=[30, 100, 300, 1000, 4000])
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()
    if args.repeats < 2:
        parser.error("At least 2 repeats are required")
    if args.seed < 0:
        parser.error("seed must be nonnegative")
    if not np.isfinite(args.duration) or args.duration <= 0:
        parser.error("duration must be finite and positive")
    if any(not np.isfinite(d) or d <= 0 for d in args.densities):
        parser.error("densities must be finite and positive")
    rng = np.random.default_rng(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for density in args.densities:
        estimates = []
        for _ in range(args.repeats):
            diamond = sprinkle(args.duration, density, rng)
            chain = longest_chain_fast(diamond)
            estimates.append(inferred_duration(len(chain), density))
        rows.append({
            "density": density,
            "repeats": args.repeats,
            "true_duration": args.duration,
            "mean_estimate": float(np.mean(estimates)),
            "standard_deviation": float(np.std(estimates, ddof=1)),
            "standard_error": float(np.std(estimates, ddof=1) / np.sqrt(args.repeats)),
            "bias": float(np.mean(estimates) - args.duration),
            "seed": args.seed,
        })
    with (args.out / "time_reconstruction.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(
        [r["density"] for r in rows],
        [r["mean_estimate"] for r in rows],
        yerr=[r["standard_deviation"] for r in rows],
        fmt="o-", capsize=3, label="Mean ± 1 standard deviation",
    )
    ax.axhline(args.duration, linestyle="--", label="True duration")
    ax.set(xscale="log", xlabel="Sprinkling density", ylabel="Inferred proper time",
           title="1+1D causal-set time reconstruction (known geometry)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.out / "time_reconstruction.png", dpi=160)
    plt.close(fig)
    print("Density   Estimated duration   Bias")
    for r in rows:
        print(f'{r["density"]:7g}   {r["mean_estimate"]:17.4f}   {r["bias"]:+.4f}')
    print(f"Saved results to {args.out.resolve()}")


if __name__ == "__main__":
    main()
