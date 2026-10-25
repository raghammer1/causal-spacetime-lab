# Experiment 2: dimension reconstruction protocol

Recorded 2026-10-25 on `experiment/dimension-reconstruction-v1`, before primary
results or calibration data are examined. Parent: merged Experiment 1 commit
`7bfac9e`. The prior 81 tests pass and all archived Experiment 1 artifact hashes
were verified. No changes are made directly to `main`.

## Scope and hypotheses

This study reconstructs a property of **known flat spacetime generators**. The
estimator receives only a strict causal-order matrix, never coordinates or the
generating dimension. Generating labels are available to separate calibration
and evaluation code. Recovering dimension does not demonstrate background-free
emergence, a gravitational dynamics, or any physical claim about our universe.

Let R count comparable unordered pairs once and r=R/binom(N,2). For a flat
d-dimensional Alexandrov interval, the reference is
`p(d)=Gamma(d+1)*Gamma(d/2)/(2*Gamma(3*d/2))`. The generator, normalization,
independent integral checks and original source are detailed in
[DIMENSION_THEORY.md](DIMENSION_THEORY.md).

1. **Known-geometry reconstruction:** sample mean r should agree with p(d), and
   order-only dimension estimates should recover d=2,3,4 with improving precision
   as N increases. Nonlinear inversion can be biased at finite N.
2. **Single-statistic insufficiency:** calibrated non-spacetime controls can have
   approximately the same r as a known geometry and receive its dimension label.
   This is an expected limitation, not a failure to implement the estimator.
3. **Exploratory joint discrimination:** adding height and interval abundances
   should reject matched-fraction adversaries more reliably than r alone. This
   is a test against selected families, not a universal test of manifoldlikeness.
4. **Incomplete observables:** distinct orders can share all selected summaries.
   Include an explicit deterministic example rather than hiding this limitation.

## Fixed primary study

- Dimensions: **2, 3, 4** (spacetime dimension, including time).
- Fixed event counts: **64, 128, 256**.
- Duration: **T=1**, c=1; conditional uniform sampling in the interval.
- Independent repetitions: **200 per dimension/count**, **1,800 primary orders**.
- Master seed: **20261025**; NumPy PCG64 streams keyed by stable parameter values,
  repetition and purpose using SHA256, not Python's randomized hash.
- At least **2,000 percentile bootstrap resamples** for reported mean intervals.
  Resample entire independent orders, never individual correlated causal pairs.
- Matrix and observable limit: **N≤512**. The primary study uses at most 256.
- Preserve every failed inversion/status; do not drop difficult draws or select seeds.

Estimate d by bounded inversion on **[1,10]**. A total order gives the boundary
value d=1; an antichain's r=0 is outside this finite domain. N<2 is undefined.
Invalid/malformed/nontransitive matrices fail explicitly. Out-of-domain fractions
are reported, never silently clamped. Means over valid estimates must state the
valid count and cannot hide failures; classification counts failures as incorrect.

Classify a valid estimate into nearest d=2,3,4 only when it is in [1.5,4.5]; ties
use the lower class. Otherwise mark it unclassified. This classification rule is
an evaluation of these three candidate dimensions, not an assumption in inversion.

## Calibration and untouched holdout controls

Generate **100 separate calibration sprinklings per d/N cell**, 900 total, with
distinct streams. They do not contribute to primary accuracy or mean intervals.

For each target d and N, fit a balanced two-layer Bernoulli order: a=floor(N/2),
b=N−a, with independent lower-to-upper relations of probability q and no other
relations. Its height is at most two and `E[r]=q*a*b/binom(N,2)`. Set q from the
calibration sprinklings' mean r divided by this capacity. If the fitted value is
outside [0,1], record both the unconstrained value and explicit boundary saturation;
do not claim an exact match when the family cannot attain the target. This fitting
boundary is distinct from, and does not change, the estimator's no-clamping rule.

Holdout controls use independent, previously unused streams:

- Matched two-layer orders: **200 per target d/N**, 1,800 total.
- Random DAG-derived orders: **200 per N**, 600 total; iid forward edges with
  probability 2/N followed by explicit transitive closure and relabeling.
- Three-layer orders: **200 per N**, 600 total; iid uniform layer assignments,
  with all relations from lower to higher occupied layers. Assigning iid layers
  directly to event indices already makes the labeling exchangeable.
- Total orders and antichains: one exact deterministic example per N, six total.
  Do not count repeated copies as independent stochastic observations.

Thus the complete default workload is 1,800 primary spacetime orders, 900
calibration spacetime orders, and **3,006 control orders**. The artificial orders
have no assigned physical dimension. A matching estimated label means that the
single estimator was fooled, not that a spacetime embedding has been established.

## Observables and exploratory joint detector

Compute all observables from the order alone: r, longest-chain length, number of
relations, exact counts of internal interval cardinalities for every related pair,
link abundance (empty internal interval), mean interval cardinality, and binned
interval fractions. Internal cardinality counts elements, not directed paths.
Store raw histograms or a losslessly recoverable equivalent and whole-order records.

The preselected five features are r, height/N, fraction of relations that are links,
mean internal cardinality/max(N−2,1), and fraction of intervals with at least four
internal elements. Unit tests independently validate these observables; their
combination into a detector is **exploratory**. For no relations the conditional
interval features are undefined; detector handling must be explicit and retained.

At each N, use the first half of each dimension's calibration samples to estimate
feature means and sample SDs. A documented SD floor of 1e−9 avoids division by
zero. Score a holdout feature vector by its minimum RMS standardized distance to
the d=2,3,4 templates. Freeze a 95th-percentile acceptance threshold from the
remaining half of the calibration samples, pooled across the three dimensions.
Fit an otherwise identical r-only detector for comparison. No primary or adversary
holdout outcome may influence templates, thresholds, q or feature selection.

Report acceptance/rejection for each family and N, including genuine acceptance,
and paired bootstrap differences in rejection on the same holdout orders.
Calibration labels are permitted for this supervised reference comparison; the
inference step receives only order-derived features. Its limited family coverage,
correlated features, diagonal standardization and finite threshold calibration
preclude claims of a calibrated universal geometry classifier.

Use the three-element V order and its dual Λ as an exact example: they are
nonisomorphic as directed orders yet have the same r, height and interval-size
histogram, hence identical selected features. This is a small logical limitation,
not a claim that their full orders or all possible observables are identical.

## Independent checks and resource pilot

Verify interval volumes T²/2, pi*T³/12 and pi*T⁴/24. Check p(2)=1/2, p(3)=8/35,
p(4)=1/10 both analytically and by independent deterministic volume integrals.
Check the time/radius distributions, spatial rotational symmetry, Poisson mean
argument, coordinate boosts/rotations/translations, label permutations, the new
d=2 generator against the existing implementation, and repeat-seed reproduction.
Incorrect radial/box sampling and density normalization must be detectable by
these checks. Poisson mode is an API validation, not part of the fixed-N primary.

Before the primary study, run a resource pilot with seed **20261024**, dimensions
2,3,4, N=64,256, three holdout repetitions, ten calibration samples per cell,
100 bootstrap draws and one benchmark sample per cell. It tests completion,
schemas, memory, algorithm contracts and runtime; do not use its scientific
outcomes to select favorable features or seeds. Retain pilot metadata and costs.

```bash
python -m causal_lab.dimension_study --dimensions 2 3 4 --counts 64 256 --repeats 3 --calibration-repeats 10 --seed 20261024 --bootstrap 100 --benchmark-repeats 1 --out results/dimension-pilot
```

If projected runtime exceeds ten minutes or peak RSS approaches 1 GiB, investigate
implementation cost first and record any protocol revision before primary
analysis. Do not silently omit a cell. No larger-N extension is authorized by this
protocol alone; add a separately justified plan only if results and resources
warrant it. Keeping the initially requested grid is an acceptable outcome.

## Measurements and outcome rules

Report sample means, SD, variance, SE and pointwise percentile 95% intervals for
r and estimated d; dimension bias and failures; per-dimension/count accuracy and
confusion matrices; the inverse of mean r separately from the mean of inverse r;
control matching, detector rates, interval distributions, runtime and memory.
Add Wilson 95% intervals for independent-order classification rates, since a
100% observed success rate gives a degenerate percentile bootstrap interval.

- **Sampling failure:** wrong analytic identities, transform invariance or closure
  invalidates results until fixed. A primary mean r beyond five empirical SEs from
  p(d) triggers investigation. This is a diagnostic, not a simultaneous test.
- **Operational reconstruction target at N=256:** Wilson lower bound ≥90% for
  each class supports reasonably accurate classification. Upper bound <90%
  refutes that target; otherwise the result is inconclusive. Mean-bias bootstrap
  intervals wholly inside ±0.10 dimensions support the bias target, wholly outside
  refute it, and boundary overlap is inconclusive. Smaller-N outcomes determine
  how much information is needed by these stated criteria.
- **Size drift:** a higher-N absolute-bias interval moving away from zero beyond
  uncertainty, or decreasing classification performance, must be reported and
  investigated, not hidden by pooling. Finite fluctuations need not be monotonic.
- **Matched adversary:** |mean r_adversary−mean r_genuine|≤0.02 is the operational
  approximate-match tolerance. Report a bootstrap contrast as well. Frequent
  target-dimension labels on matched artificial orders refute sufficiency of r.
  A failed match is a failed adversarial construction, not evidence of robustness.
- **Joint features:** positive paired rejection-improvement intervals on matched
  controls, with genuine acceptance at least 85%, support improvement for that
  family/N. Zero-crossing improvements are inconclusive; worse rejection or poor
  genuine acceptance is adverse. Report every family, not only successes.
- **Numerical failures:** invalid chains, malformed closures, nonreproducible
  samples or broken independent checks invalidate affected analyses. Preserve
  diagnostic evidence and record any repair and rerun.

All intervals are pointwise and subject to Monte Carlo and calibration uncertainty;
no simultaneous coverage or uncertainty in the known generating dimension is
claimed. Performance timing and memory are separate from scientific outputs.
Time untraced calls, then measure allocations in separate tracemalloc passes;
record whole-process peak RSS with correct platform units, versions, source and
protocol hashes, parent commit and dirty status. Do not publish usernames, hostnames
or absolute machine paths. Retain compact curated scientific data and six labeled
plots; ordinary output stays gitignored.
