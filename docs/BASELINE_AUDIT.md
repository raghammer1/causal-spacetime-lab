# Baseline audit — 2026-10-25

This is a numerical demonstration on a prescribed Minkowski background. It is
not measured evidence about the microscopic structure of our universe.

## Reproduction

The supplied directory had no Git history or remote. The intended public
repository did not exist when inspected with authenticated GitHub CLI. The
package, notebook, tests, research notes, MIT license and CI were inspected;
working code was retained.

Local verification used Python 3.14.4, NumPy 2.5.4, Matplotlib 3.11.2,
pytest 9.1.1 and JupyterLab 4.6.4 on macOS/Darwin arm64. No dependency was added.
The supported Python floor remains 3.10; CI tests 3.10 and 3.14.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
python -m causal_lab.cli --seed 20261025 --repeats 100 --out results
```

The original seven tests passed. After the small fixes below, **42 tests pass**.
All notebook code cells executed successfully with a noninteractive plotting
backend. The CLI wrote a five-row CSV and a valid PNG. The reviewed outputs are
retained in [baseline/](baseline/); ordinary runtime output remains ignored.

| Density | Mean estimated duration | SD | Bias (true duration = 1) |
|---:|---:|---:|---:|
| 30 | 0.71650 | 0.19538 | −0.28350 |
| 100 | 0.78772 | 0.11850 | −0.21228 |
| 300 | 0.86630 | 0.09277 | −0.13370 |
| 1000 | 0.90069 | 0.06325 | −0.09931 |
| 4000 | 0.94194 | 0.03877 | −0.05806 |

These are 100 seeded trials per density, not a proof of convergence. The plotted
bars are sample standard deviations, not confidence intervals for the mean.

## Supported corrections and failure cases

- The strict-order routine previously checked only self-relations and two-cycles.
  A longer cycle could produce a cyclic parent list and never finish. It now
  rejects nontransitive/cyclic input before reconstruction. A Hasse adjacency
  matrix must first be converted to its transitive strict order.
- Sorting only by increasing `u` could falsely chain equal-`u` events. Sorting
  ties by decreasing `v` makes the fast algorithm agree with the strict order.
  Continuous samples have ties with probability zero mathematically, but the
  public API must handle supplied finite arrays consistently.
- Invalid/nonfinite density and noninteger chain counts now fail explicitly.
  The denominator is evaluated as `sqrt(2)*sqrt(rho)` to avoid overflow for
  large finite density. This changes some final decimals at floating-point
  roundoff level (the density-300 mean changed by about 5e-16).
- CLI arguments are validated before output creation. Tests cover malformed
  inputs, exact volume normalization, relabeling, empty cases, tied coordinates,
  invalid orders and reproducible CSV/PNG generation.
- The notebook now calls tested package functions, distinguishes order-only
  reconstruction from coordinate-aware sweeps, and states that physical units
  require the independently supplied sprinkling density.

## Mathematics and limitations

With `u=t+x`, `v=t−x`, the Jacobian is `dt dx = du dv / 2`. Thus the diamond
volume is `T²/2` and `N ~ Poisson(rho*T²/2)`. Conditional on N, the increasing
chain problem is the longest increasing subsequence of a uniform random
permutation. Its leading length `2*sqrt(N)` gives `L/sqrt(2*rho)` as the
asymptotic time estimate. Interior events only are counted; endpoints are not
added. See [THEORY.md](THEORY.md) for original sources and finite-density terms.

The generator assumes flat 1+1D geometry, fixed physical density and independent
Poisson sampling. The implemented relation requires both null coordinates to
increase strictly; exact null ties are excluded. The fast algorithm reads the
embedding and is not coordinate independent. The order-only algorithm accepts
only the order but cannot establish that an arbitrary order is manifold-like.

The initial CLI run took 22.73 s including first-time font cache creation and
had peak RSS 104,562,688 bytes. A warm run after fixes took 1.07 s and peak RSS
85,131,264 bytes, measured by macOS `/usr/bin/time -l`. These are single-machine
observations, not controlled algorithm speed comparisons. Matplotlib/imports
are included. Fast LIS has O(N log N) time; constructing an order takes O(N²)
space and the defensive transitivity validation has O(N³) worst-case time.
Large order matrices must therefore remain limited to small validation cases.

The baseline has only one duration and five densities; it does not estimate
bootstrap intervals or establish a finite-size exponent. The original notebook
is a pedagogical demonstration, not the archived study. The next study's
[protocol](FINITE_DENSITY_PROTOCOL.md) is specified before collecting its data.

## Publication review

The notebook contains no saved outputs. The ignore rules exclude virtual
environments, runtime results, caches, `.env` files and key files. Reviewed
baseline artifacts are small, intentionally versioned scientific outputs.
Commit identity uses a public GitHub noreply address. No personal filesystem
paths, credentials or private repository material are intentionally included.
The initial baseline will be published on `main`; new experiments require a
branch and an unmerged pull request.
