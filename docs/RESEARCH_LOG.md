# Research log

## 2026-10-25 — Initial baseline

**Question:** In a causal order sampled from a known 1+1D flat spacetime, can longest-chain length approximately recover elapsed proper time?

**Status:** Numerical demonstration of a known causal-set property; test and reproduce before interpretation.

**Key assumptions:** Minkowski geometry is used by the event generator; unit light speed c=1; independent Poisson sprinkling at uniform spacetime density; timelike boundary endpoints are not counted in the interior chain; large-density estimator is asymptotic.

**Prediction:** For fixed proper time, increased sprinkling density should improve the relative accuracy of `longest chain / sqrt(2*density)` in aggregate. At finite density there is stochastic scatter and systematic bias.

**Controls:** Compare order-only dynamic programming with fast embedding-based LIS; compare non-spacetime-like total orders and antichains.

**Potential falsification:** Wrong chain computation, inconsistent density scaling, convergence that fails over large parameter sweeps, or non-causal chains.

**What this does NOT demonstrate:** Microscopic discreteness of the physical universe, dynamical emergence of a metric, a quantum theory of gravity, or a resolution of black-hole singularities.

**Next:** Re-run benchmarks with recorded seeds, vary event density and endpoint proper time, investigate finite-size systematic error.

## 2026-10-25 — Finite-density scaling v1

**Protocol:** [Recorded in the baseline before execution](FINITE_DENSITY_PROTOCOL.md).
Seven densities, three durations, 200 repeats per cell, seed 20261025; uncertainty,
independent count checks, matrix/embedding agreement and matched-count controls.

**Observed:** 4,200 primary draws; all 208 eligible primary order comparisons
agreed. Normalized bias improved between density endpoints at every duration,
but remained negative. The primary numerical files reproduced byte for byte.

**Adverse diagnostic retained:** One of four equal-count contrasts excluded zero
pointwise at about 2.19 SEs. An [independently specified follow-up](EQUAL_COUNT_FOLLOWUP_PROTOCOL.md)
used seed 20261026 and 8,000 additional draws; the target contrast was then 0.054
SEs and its interval included zero. This did not reproduce a persistent difference;
it does not establish exact equality. Original and follow-up results remain separate.

**Verification and limits:** 81 tests pass, including injected numerical failures.
The generator still assumes Minkowski geometry and the fast algorithm still reads
coordinates. Bootstrap intervals are pointwise and do not remove finite-density
bias. The [results report](FINITE_DENSITY_RESULTS.md) contains tables, plots,
costs, source hashes, reproduction commands and all interpretation boundaries.

**Next:** Validate several dimension-sensitive observables against adversarial
orders before planning background-free growth experiments. No growth law,
curved-background model or gravitational dynamics was implemented in this study.
