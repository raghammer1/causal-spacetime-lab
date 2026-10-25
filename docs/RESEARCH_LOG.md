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

## 2026-10-25 — Adversarial geometry and identifiability v1

**Registration:** branched from merged Experiment 2 at `c121da2`; independently
replayed its seven reported limitations. Committed protocol/audit/theory as
`351c8b9`, then verified implementation and a resource-only pilot as `e4dfbc0`.
No previous result or detector implementation was altered.

**Executed:** three independent fits, d=2,3,4, N=64,128,256; 52,218 recorded
orders with separate calibration/development/validation/test streams; 5,400
bounded searches and 345,600 candidate evaluations. All six detectors use matched
nominal validation targets; discrete-height ties produce higher achieved rates.

**Primary finding:** no model meets the full registered advancement criterion.
Height alone rejects every matched bipartite control; all 5,400 fraction/height
search checkpoints match their targets, but none of the searches meets every
15-feature one-SD constraint. Some failed searches still pass all six detectors.
At N64,target-d2, F accepts 63.17% of full-search outputs, hierarchical interval
[57.33%,69.00%]. Its unseen-family acceptance is 23.33% [19.67%,27.17%].

**Adverse outcomes:** D admits 62.83 percentage points more sparse N64 DAGs than
C, paired interval [52.67,75.84]. No primary contrast passes the full meaningful
improvement gate; some prespecified 97.5%-target local contrasts do. Missing
genuine lower bounds are inconclusive, not proof of acceptance below 90%.
Increasing N also weakens the fixed-budget adversarial search, so rejection alone
does not establish asymptotic identifiability.

**Exact limits:** nondual orders share all selected summaries; rank-two sampling
and d2 geometric sampling have the same full order law. Flat box samples can be
rejected because of their different boundaries. These findings separate a
generator's provenance, reference-model compatibility and physical geometry.

**Verification:** 506 tests, complete archive replay, independent seed-based
search reconstructions, source/artifact hashes and visual figure review. The
[results report](ADVERSARIAL_GEOMETRY_RESULTS.md) gives uncertainties, costs,
reproduction evidence, retained failures and all six comparison figures.

**Decision:** no-go for advancing on a claim of validated emergent geometry.
Recommend a new preregistered diagnostic/adversarial study before interpreting
coordinate-free growth as geometric evidence. No gravitational dynamics,
Einstein-equation derivation or black-hole/singularity claim follows.

## 2026-10-25 — Local causal structure and geometric identifiability v1

**Gate and registration:** verified Experiment 3 PR #3 merged at `8dccf04` and
post-merge CI green before implementation. Created the experimental branch,
committed mathematical protocol/theory as `e92c6e4`, then committed verified
implementation and timing-only workload selection as `96234c5` before primary
sampling. The full R=200,F=32 choice followed the fixed resource rule.

**Executed:** three independent fits, d=2,3,4, N=64,128,256; 31,392 parent/checkpoint
records, 3,600 exact matched pairs, 864 searches and 387,072 attempted switches.
All 42 primary convex-region comparisons and their 126 per-fit counterparts
meet the registered practical-equivalence margins. The conditional interval-law
derivation explains why slabs retain local dimensional information despite
global boundary bias. The study adds no learned classifier or geometric label.

**Exact information and limits:** induced 2+2 counts, open-interval connectivity
and overlap moments distinguish old-summary collisions; several other quantities
are algebraically redundant. All exact pair predictions hold. A separately
labeled post-registration 12-event counterexample matches the entire measured
structural vector, and a restricted height-two counting argument proves that
such collisions are unavoidable. Two-ranking/d2-diamond full-law equivalence
remains exact; S3 obstructs d2 but has an explicit d3 embedding.

**Failures retained:** 528 searches accept no proposal. d2 searches detect no
local-invariant change; d4 changes are common, but neither motion nor stalling
certifies embeddability. At N256 every switched ensemble meets the local-law
margins, including d4 with 96/96 changed invariants. Small-N d4 slabs have sparse
or absent intervals; boxes retain dimension bias; rank-three/d3 comparisons
include four inconclusive margins. TV bootstrap bias and only three fits limit
the uncertainty interpretation.

**Verification:** 661 passing tests and an end-to-end CLI smoke run; exhaustive
poset and motif checks, full archive audit,
independent coordinate/dual-count reconstruction of a fixed 129-record subset
including 27 complete searches, complete scientific replay, and eight reviewed
figures. The results report records exact digests, test/CI evidence and costs.

**Decision:** useful structural progress, no claim of complete reconstruction.
Stop classifier optimization; prioritize specified continuum convergence,
embedding and scale-control conditions. Exploratory intrinsic causal dynamics
is a separate research direction, not evidence of emergent gravity.

## 2026-10-25 — Background-free causal growth v1

**Preparation:** verified Experiment 4 merged at `f841536`, its independent
reviews/archive replay and green post-merge CI. Committed mathematical protocol
and known continuum restrictions as `4268ad3`, before growth implementation.
The timing-only pilot selected R32 per batch, preserving every size/control.
Source and the workload amendment were frozen at `9fbf2d5` before primary data.
A smoke-stream overlap caught in review was corrected with fresh reserved
primary/reference seeds; the initial smoke was excluded from inference.

**Executed:** intrinsic transitive percolation at six fixed probabilities,
three independent batches, single-history prefixes N32..512 and four half-thinnings
per source size. Five independent comparison families include d2/3/4 diamonds,
a semiorder and an analytically matched height-two order law. There are 1,056
stochastic histories, two deterministic endpoints and 17,986 dependent records.
No coordinates, dimension or target features enter the intrinsic generator.

**Primary result:** every growth setting fails. All 18 late-size 2+2 level bands
contradict the d2 target beyond ±.005; all 54 batch-specific means are below its
lower practical band. Among 48 simultaneous entries, 23 contradict, 19 meet
their margins and six remain inconclusive. Both the d2 reference and matched
height-two control pass their separate eight-entry signatures. The latter has
no nonempty intervals and no 3+1, so the signature is demonstrably insufficient.

**Structural findings:** natural-label path weights equal `p^L(1-p)^I`; genuine
birth covariance, prefix consistency and induced thinning were independently
verified. For fixed 0<p<1, the almost-sure chain sampling limit coexists
with persistent incomparable adjacent births and a nonspanning longest chain.
At p=.3,N512, r=.981585 but H/N=.395609. Uniform thinning is motif-unbiased for
every parent; its contrast with a smaller birth prefix is a different question.
Global/local reference-equivalent dimensions and joint interval patterns can
disagree strongly even when a selected marginal agrees with a flat reference.

**Adverse controls and limits:** all 21 N512 own-reference conditional margins
pass, yet the d2 local-dimension interval excludes 2. At d2,N32 the secondary
TV rule falsely rejects the known reference, with an upward-biased percentile
interval. Sparse size-eight intervals remain insufficient at p=.005; missing
height-two intervals remain undefined. Low-p motif densities still rise in the
finite window. These outcomes are retained without retuning or corrective fits.

**Verification:** 813 tests, complete CLI smoke/audit, independently reconstructed
221 selected records, 4,877 separate statistical checks with zero discrepancies,
and nine visually reviewed figures. Two clean full runs reproduce all 31 data,
table and figure artifacts byte for byte, with scientific digest
`534c51d1745f4d370a87ced03b895b5ff935e3811a362f9349554b164f0a57da`.
Primary/repeat total times are 664.97/673.50 s; conservative aggregate memory is
1.067/1.073 GB, within the registered limits. See the
[complete report](BACKGROUND_FREE_GROWTH_RESULTS.md) and audited archive.

**Decision:** no-go for ordinary CSG as a Minkowski sampling-limit candidate,
consistent with the known almost-semiorder theorem. Stop tuning this baseline.
Further intrinsic dynamics requires a mathematical reason to change specified
assumptions, fresh covariance/consistency analysis and a precise convergence
target. No physical spacetime, gravity or singularity claim follows.
