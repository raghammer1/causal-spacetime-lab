# Finite-density scaling v1: protocol recorded before execution

Date: 2026-10-25. Branch: `experiment/finite-density-scaling-v1`.
This document fixes the principal questions, sampling plan and interpretation
before inspecting the new study's output. Numerical outcomes belong in a separate
results report. Mathematical assumptions and references are in [THEORY.md](THEORY.md).

## Scope and hypotheses

The generator assumes a known 1+1D Minkowski diamond, `c=1`, uniform Poisson
spacetime density, independent events conditional on count, and no counted
boundary endpoints. It does not generate spacetime from a background-free rule.
Let `λ=ρT²/2`, `L` be longest interior chain length, and
`T_hat=L/√(2ρ)`.

1. **Normalization and finite-density hypothesis:** over the specified density
   range, the mean relative reconstruction error should be negative and should
   be closer to zero at the highest density than at the lowest for each duration.
   This is a finite-range operational prediction informed by established
   asymptotic mathematics, not a proposed new law of physics.
2. **Algorithm hypothesis:** order-only dynamic programming and the embedding-based
   longest-increasing-subsequence algorithm give identical chain lengths for
   every cross-checked sample, including empty and tied-coordinate test cases.
3. **Control hypothesis:** matched-count total orders and antichains exhibit
   `L=N` and `L=1[N>0]`, respectively, and therefore do not share the sprinkled
   order's square-root asymptotics.
4. **Scale check:** equal `λ` implies the same distribution of `T_hat/T` even when
   `ρ` and `T` differ. The primary grid contains some equal-`λ` pairs; small
   deterministic tests may also check this rescaling identity.

## Fixed primary sampling plan

- Master seed: **20261025**.
- Densities: **seven** values from `numpy.geomspace(32.0, 8192.0, 7)`.
- Physical durations: **0.5, 1.0, 2.0** in the chosen units.
- Repetitions: **200 independent draws per cell**, or **4,200 primary sprinklings**.
- Expected counts range from **4** to **16,384**. Retain empty draws; never
  condition on a sample being nonempty or on a successful chain calculation.
- Bootstrap: **2,000 resamples per cell**, sampling full repetitions with
  replacement; percentile **95%** intervals for the mean estimate and its
  normalized bias. Use a separate random stream from the physical draws.
- Derive deterministic streams from the master seed, stable parameter identity,
  repetition and stream purpose. Changing traversal order or bootstrap settings
  must not change the physical samples. Record the implemented mapping and
  generator in metadata. Avoid Python's randomized `hash()`.
- Retain raw repetition-level counts, chain lengths, parameters and identifiers,
  plus machine-readable summaries in CSV/JSON. Record package versions and the
  exact invocation. Runtime and memory observations are not bitwise reproducible.

This workload is intentionally bounded for a laptop. If a resource failure makes
any cell unaffordable, report the failed cell and revised protocol explicitly;
do not silently omit it or claim that the full plan ran.

## Independent controls and numerical checks

**Sampling:** compare measured count means with `λ` and count variances with the
Poisson prediction. The theoretical standard error of the count mean is
`√(λ/200)`. Report standardized deviations as diagnostics; do not call every
point outside an unadjusted 95% interval a failed generator in a 21-cell sweep.
A deviation exceeding five theoretical standard errors warrants investigation.
Small unit tests should independently verify the factor `T²/2` and a deterministic
seed, rather than testing the estimator against a copy of its own formula.

**Algorithms:** cross-check the first 20 repetitions of each primary cell when
the realized event count is at most 256 with both algorithms. Save parameters,
event counts, both lengths and agreement. Store timings and memory measures on
separately identified benchmark samples, linked by parameter cell. The order-only pipeline includes constructing the `N×N` Boolean
relation matrix; the fast pipeline uses the embedding. Compare reconstructed
chains against the relation, not just against each other's lengths. Include
relabeling, empty and singleton orders, total orders, antichains, equal-coordinate
cases, and invalid/cyclic/nontransitive input rejection tests as appropriate to
the documented API. Never allocate quadratic matrices at the largest primary
sizes just to add more repetitions.

**Matched-count negative controls:** for each primary draw, use the same `N` to
record total-order and antichain lengths. Their exact formulas avoid allocating
large matrices; independently verify them with explicit small order matrices.
Report `E[L_total]=λ`, `E[L_anti]=1−exp(−λ)` as analytic references. These control
rows share counts with the sprinkled samples and are not independent new draws.
Any comparisons of their differences must preserve that pairing.

**Pair comparability:** a small-case check against the two-dimensional expectation
`1/2` can supplement the chain checks. It is not a dimension measurement. Pair
indicators within a sprinkling are dependent; use variation across independent
sprinklings if estimating uncertainty.

## Measurements and figures

For each cell, report count and chain statistics and the estimate's mean, sample
standard deviation (`ddof=1`), standard error (`SD/√repeats`), percentile bootstrap
confidence interval, absolute bias, and normalized bias `(mean−T)/T`.

Plot the mean relative estimate or normalized bias against density and against
expected count `λ`, with labeled units and pointwise uncertainty. Distinguish
standard-deviation spread from uncertainty on a mean. Plot chain-length scaling
against `λ` with total-order and antichain controls; overlay `2√λ` only as a
large-count reference. The leading normalized-bias guide
`−1.7711/(2λ^(1/3))` is a cited asymptotic prediction, not a fit, correction, or
measured exponent. Do not infer a precise exponent from this seven-point sweep.

Use separate deterministic samples for algorithm benchmarks. Time calls without
`tracemalloc`, then make separate traced-allocation memory passes; record the
overall process peak resident set separately. Measure wall-clock time with a monotonic clock. State whether sampling, matrix
construction, analysis, bootstrap and plotting are included. Benchmark memory
with an explicitly named method: a traced-allocation peak is not the process's
resident-memory peak. Record units, scope, repeats and platform description
without usernames, hostnames or local absolute paths. Memory instrumentation can
alter timing; separate timing and memory trials where practical. Avoid claims
about performance outside the measured sizes and implementation.

## Predeclared failure and inconclusive outcomes

- **Any algorithm disagreement or invalid returned chain** invalidates the affected
  numerical analysis until explained and repaired with a regression test.
- **Wrong density-to-count normalization**, or persistent count departures beyond
  the sampling diagnostics, invalidates a physical interpretation of the output.
- **Bias fails to improve:** compare the highest and lowest density at each fixed
  `T`. Nonoverlapping pointwise intervals in the predicted direction support the
  stated finite-range trend; reversed intervals refute it for this range;
  overlapping intervals are inconclusive. If a bootstrap contrast is reported,
  use independent resampling of these independent endpoint cells and identify it
  as an additional diagnostic. Endpoint improvement is not proof of monotonicity
  at every intermediate density or of the infinite-density limit.
- **Persistently wrong high-count normalization** after independent algorithm and
  count checks would reject the implementation/model's claimed reconstruction.
  A finite sweep cannot refute an established asymptotic theorem or establish its
  limit by itself.
- **Control mismatch** with `N` or `1[N>0]`, or failure to distinguish their trends
  from the sprinkled order across the range, rejects the relevant control claim.
- **Equal-count inconsistency:** substantial differences between normalized means
  at equal `λ`, beyond estimated sampling uncertainty, require investigation of
  units, streams and code. Agreement is necessary but not sufficient evidence for
  correct reconstruction.
- **Unstable uncertainty or unavailable resources** produces an inconclusive result
  and a documented limitation, not a favorable claim.

All reported 95% bootstrap intervals are **pointwise**. They are not simultaneous
21-cell confidence bands, formal familywise tests, or uncertainty in the known
input duration. Bootstrap Monte Carlo error, finite repetitions, PRNG/version
choices and finite density remain limitations. The distinction between exact
identities, proven asymptotics, numerical observations and future hypotheses must
remain explicit in the results report.
