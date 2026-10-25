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

## 2026-10-25 — Dimension reconstruction v1

**Preparation:** fetched merged Experiment 1 at `7bfac9e`, verified its 81 tests
and archived checksums, and branched from that baseline. Committed the
[protocol](DIMENSION_RECONSTRUCTION_PROTOCOL.md) at `b9b5488` before the resource
pilot or main/calibration runs. The pilot supported the unchanged workload.

**Executed:** 1,800 fixed-N spacetime holdouts in d=2,3,4 at N=64,128,256;
900 independent calibration orders; 3,006 controls. All estimation and
observable analysis uses only strict order matrices. Primary seed 20261025,
2,000 whole-order bootstrap resamples; a complete repeat reproduced scientific
tables, models, diagnostics and compressed histograms exactly.

**Observed:** N=256 yielded 200/200 correct labels per dimension. N=128 was the
smallest tested count supporting the 90% accuracy target for all three classes.
d=4,N=64 remained inconclusive by that criterion despite observed accuracy 92.5%.
Bias intervals lay inside ±0.10, but one mean-dimension interval excluded the
known value and sample bias was not strictly monotonic across N.

**Falsification and limits:** all 1,800 calibrated two-layer controls fooled the
single dimension label and r-only detector. Joint features rejected them, yet
accepted 49/200 random-DAG controls at N=64, including 36 previously rejected by
r alone. Exact V/dual examples share all selected summaries. These are retained
limitations; no thresholds were retuned on holdout outcomes. Detector uncertainty
conditions on the frozen calibration and is not universal geometry evidence.

**Verification:** 253 tests pass; six plots and all raw/summary/calibration
relationships were independently reviewed. Final archived computation took 27.36 s and output
generation 1.95 s, with 151.8 MiB process peak RSS on the recorded platform.
See the [results report](DIMENSION_RECONSTRUCTION_RESULTS.md) for all uncertainty,
artifacts, source/protocol hashes and reproduction commands.

**Next:** harder held-out adversaries and calibration uncertainty, then a specified
background-free growth experiment; independently verified curvature benchmarks
remain a separate prerequisite before gravitational or black-hole modeling.
