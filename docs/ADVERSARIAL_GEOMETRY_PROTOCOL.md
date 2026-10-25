# Experiment 3 preregistration: adversarial geometry and identifiability

2026-10-25. Register this file in Git before implementation of the new study or
inspection of its final holdouts. Starting baseline: `c121da2`; branch:
`experiment/adversarial-geometry-v1`. Previous results remain immutable.
The [independent audit](ADVERSARIAL_GEOMETRY_AUDIT.md) records the seven motivating
limitations. Baseline validation: 253 tests and an Experiment 2 CLI smoke run pass.

## Scope and hypotheses

This is an educational numerical study of specified finite-order distributions,
not measured physical evidence of discrete spacetime, emergence or gravity.
“Genuine” means iid uniform fixed-count samples from flat Alexandrov intervals;
“artificial” identifies a construction, not a proof of non-manifoldlikeness.

Primary H1: at nominal 95% genuine validation acceptance, at least one detector
accepts genuine samples with lower 95% Wilson bound >=90% and negative controls
with upper bound <=5%, in every designated cell of every independent fit.
Primary H2: a detector using more than height alone yields a practically meaningful
paired reduction in artificial acceptance, without unacceptable genuine rejection.
Primary falsification: height/fraction matching or multi-statistic search can leave
substantial acceptance even after the easy two-layer failure is repaired.

Secondary: investigate compensation, calibration variation, size dependence,
classification/acceptance disagreements, interval information and boundary changes.
The expected possibility of failure is a research result. No detector is presumed
best. Exact degeneracies test completeness of these summaries, not the impossibility
of every conceivable finite statistic or an asymptotic continuum conjecture.

## Fixed grid and independent partitions

Master seed **20261025**, study namespace `adversarial-v1`. Fixed T=1;
d=(2,3,4), N=(64,128,256), three independent complete fits numbered 0,1,2.
For EACH fit/d/N: 100 calibration orders (template fitting), 100 development
orders (adversary targets/parameters), 200 validation orders (thresholds only),
and 200 final genuine test orders. All are disjoint. No fit evaluates its own
training data; final sets are also disjoint across fits. All detectors within a
fit evaluate the SAME final orders, allowing paired comparisons. Development
outcomes cannot change registered features or algorithms; they supply only the
prespecified target distribution and means. Detector fitting never uses adversaries.

SHA256 of canonical JSON `["adversarial-v1",master_seed,fit,phase,family,d,N,
repeat,parameter]` seeds NumPy PCG64. JSON uses compact separators and ASCII;
parameters are JSON-native strings/numbers. Every sample retains this digest ID.
Distinct purposes include calibration, development, validation, test, bootstrap,
pilot and benchmark. Loop order must not affect a stream. Models receive order
features only at inference; true and target dimensions are evaluation metadata.

## Detectors and threshold matching

Let x=(r,H/N,links/R,mean_internal/max(N-2,1),fraction_internal>=4).
The first three partitions above give, for each candidate d and N, a calibration
mean mu and sample SD s, floored at 1e-9. Define z=(x-mu)/s. For each detector
take the minimum candidate-template score; ties select the lower dimension.

| Detector | Per-template score |
|---|---|
| A | abs(z_r), the existing ordering-fraction score |
| B | abs(z_height) |
| C | sqrt(mean(z_r^2,z_height^2)) |
| D | sqrt(mean(z_j^2)), five features, exactly the Experiment 2 score |
| E | max_j abs(z_j), an intersection of explicit constraints within ONE template |
| F | Hellinger distance to a calibrated interval-abundance probability vector |

D retains the original centering, sample SD floor, minimum RMS score and pooled
validation quantile definition. Its new training samples are independently refit;
it is not described as the frozen historical model. The archived historical
decisions are replayed separately in the audit. E disallows compensation inside
its score, but its separately calibrated threshold need not be narrower than A.

F uses ten categories: incomparable pairs; internal cardinality 0,1,2,3,4–7,
8–15,16–31,32–63,64+. Normalize by binom(N,2), including incomparable mass.
For vector p and calibration mean q, score sqrt(sum((sqrt(p)-sqrt(q))^2)/2).
No covariance inverse or small-probability division is used. This exploratory
finite-N diagnostic is motivated by interval-abundance theory, particularly
[Glaser and Surya (2013)](https://arxiv.org/abs/1309.3403); it is not their
conjecture promoted into a theorem. Full histograms are retained.

For every detector/fit/N, choose np.quantile(scores,target) using ONLY the 600
genuine validation orders pooled equally across d. Primary target=.95;
prespecified sensitivity targets=.90,.975. Scores <= threshold are accepted.
Undefined required features give rejection with a reason and remain in all
denominators. Antichain abundance probabilities are defined for F. Thresholds
match nominal pooled validation acceptance; finite discrete scores can cause ties,
so achieved validation and per-dimension test acceptance must be reported. We do
not force equal test acceptance, retune on test data, or claim per-dimension 95%
coverage. MM nearest-label classification uses the existing [1.5,4.5] gate and
is reported separately from detector acceptance and minimizing candidate dimension.

## Generator families and final sample counts

For EACH fit/N, unless a dimension is specified:

1. Easy controls: total and antichain once each (deterministic, no fake replication
   or binomial CI); iid two-layer and three-layer orders, 200 each.
2. Random DAG: forward Bernoulli edges p=c/N for c=1,2,4,8, explicit transitive
   closure and random relabeling; 200 per c. Each c is a separate family/cell.
3. Matched bipartite: 200 per target d. Set q=development mean r divided by
   floor(N/2)*ceil(N/2)/binom(N,2). Record any boundary saturation and raw q.
4. Hard matching: 200 independent searches per target d, EACH returning both an
   r/height checkpoint and a multi-statistic checkpoint. Same search links the
   two outputs; uncertainty comparisons preserve pairing. See fixed algorithm below.
5. **Unseen negative family:** 200 random interval orders. Uniformly shuffle 2N
   abstract endpoints, pair them into N intervals, order i<j iff right_i<left_j.
   This is transitive without closure; it has mean r=1/3 because two paired
   intervals are disjoint in two of six endpoint sequences. Its final outcomes
   must not be read until implementation/tests and the registered run begin.
6. **Law-overlap positive control:** 200 intersections of two independent uniform
   permutations. Sorting iid null coordinates in a d=2 diamond gives exactly
   this rank-order law. This coordinate-free sampler is NOT a negative family:
   requiring its rejection and d=2 acceptance would be logically contradictory.
7. Secondary boundary stress: 200 per d from uniform t in [0,1] and independent
   spatial coordinates in [-1/2,1/2]^(d-1), with the same flat Lorentzian relation.
   These valid flat samples have a box boundary rather than an Alexandrov interval;
   they are excluded from the primary genuine/negative advancement criterion.

Primary negative families are items 1–5, all listed cells. The known overlap and
boundary stress results cannot be reclassified as successful negative rejection.
This gives 28,800 stochastic negative orders, 1,800 overlap controls, 5,400 boundary
orders, 5,400 genuine final orders, 18 exact controls and 10,800 training/development/
validation orders: **52,218 recorded orders**, including paired search checkpoints.
Search proposals are computational candidates, not independent test observations.

## Fixed constrained-search algorithm

Each target is selected uniformly from its independent development cell. Take its
height H and full 15-vector (five x features plus ten abundance probabilities).
Create H ordered layers, reserve one backbone event per layer, and assign other
events iid to layers. Edges may only increase layer number. Protect consecutive
backbone edges; closure has height exactly H, regardless of other edges.

Use a single uniform value per allowed edge for coupled probability proposals.
Twelve evaluations (including q=0 and q=1 bounds, then ten bisections) select the
smallest absolute r error; ties keep the first. This is the r/height checkpoint.
Record target r outside the attainable bounds if present. The match criterion is
abs(r-r_target)<=.02 and exact H; failure is retained, not silently repaired.

Then perform 52 annealing proposals, toggling 1,2,4,8 allowed non-backbone edges
cyclically (without replacement, capped by available edges). Recompute closure and
features. Objective is RMS of the 15 differences from the target divided by
calibration-cell sample SDs (floor1e-9). Accept improvements, or Metropolis probability
exp((old-new)/temperature), temperature geometrically .1 to .01 over 52 proposals.
Return the best objective encountered, not just the final state. The stage-two
success criterion is max absolute standardized discrepancy<=1 across all 15
coordinates. Exactly 64 candidate evaluations, with explicit handling of no
mutable edges, no-change proposals and unattainable targets. Preserve budgets,
match flags, target/achieved features, objective and improvements for every search.
“Failed match within budget” never means a proof of infeasibility.
Random final relabeling must preserve all measured features. Donors supply no
coordinates, and their dimensions never enter a detector's inference API.

## Uncertainty, comparisons and decisions

Each stochastic cell has per-fit rates and two-sided 95% Wilson intervals on 200
independent orders, conditional on that fitted detector/development pool. Report
false rejection=1-genuine acceptance and false acceptance=negative acceptance.
Report each dimension, count, family, fit and target separately. No Wilson interval
is formed by treating all repeated calibrations as one iid binomial sample.

Across the three fits report equal-fit means, observed SD/range and 2,000 hierarchical
bootstrap resamples: resample fits with replacement, then whole orders within each
selected fit. For paired detector differences use identical sampled indices for
both decisions. Three fits give limited between-fit inference; bootstrap bounds
are pointwise exploratory, not universal guarantees or simultaneous coverage.

For H1, all three per-fit lower Wilson bounds must meet .90 for every genuine d/N
and overlap N cell, and all three upper bounds must meet .05 for every stochastic
negative family/cell; exact controls must all reject. Bounds overlapping a target
are inconclusive for that cell; bounds entirely on its failing side are failure.
A global pass is an intersection of these prespecified pointwise conditions, not
a claim of simultaneous 95% confidence. Report failed and inconclusive cells.

For H2 compare C,D,E,F to B and to A, and D/E/F to C, per negative family/N/d.
A meaningful local gain requires hierarchical lower bound on rejection gain >.05.
It is admissible only if all genuine cells at that N meet H1 and the paired upper
bound on added genuine rejection <=.02 in every d. Do not hide regressions in an
aggregate average. A complex model has no demonstrated general added value if B
performs equally well, if benefit is only easy two-layer rejection, or if a negative
family has an adverse regression >.02 supported by its paired interval. A ranking
by mean rates alone does not produce a winner under these criteria.

Paired 2x2 decision tables, including A-rejected/D-accepted and A-rejected/E-accepted,
are retained. Classification confusion, unclassified/out-of-domain counts and
accepted-but-unclassified counts are explicit. Parameter/seed selection and feature
selection cannot change after final-test outcomes are read.

## Mathematical and numerical controls

Validate strict partial orders, explicit closure, brute-force small-order features,
relabeling and duality, deterministic keyed streams, split separation, invalid
inputs, CI computations, search height/budget constraints and output digests.
Construct both V/dual and a nondual pair with identical full interval abundances.
Use the independently derived fixed-N d=2 expected abundance formula as a numerical
check. Equal marginal summaries do not establish equality of joint distributions;
target individual development vectors to preserve meaningful joint target structure.
Neither exact finite degeneracy nor an accepted artificial sample proves failure
of every possible geometric criterion.

## Resources, pilot, artifacts and deviations

A resource-only probe on existing generator/feature code used seeds 202610250300+N,
12 independent calls per N, DAG p=4/N. Median generation+feature times were
.001150/.002447/.005433 s at N64/128/256, maxima .003068/.002642/.006018 s.
No scientific outcomes were inspected. At 64 evaluations and 200 searches per
d/N/fit this projects 17.3 minutes from medians, 22.5 from maxima before search
overhead. Therefore retain the full requested grid. A new-code resource pilot,
namespace pilot and seed20261024, may measure at most two searches per d/N with
reduced fit/development/validation sizes. Do not inspect unseen final outcomes.

Budget: 45 minutes scientific wall time, <=4 GiB peak process RSS, N<=256 for the
primary grid (public functions cap512), no new dependencies. Up to three worker
processes may run independent fits; deterministic outputs must not depend on
scheduling. Resource overruns require a dated committed amendment BEFORE any
additional primary holdout evaluation; do not silently reduce repetitions or omit
failed searches. No resource-driven reduction is currently planned.

Retain compressed machine-readable feature/histogram rows and per-detector decisions,
model parameters, search diagnostics, summaries, paired tables, scientific digest,
versions, protocol/source hashes, parent commit and dirty-worktree status. Keep
timing/RSS separate from deterministic scientific digests. Benchmarks separate
generation/feature extraction from detector fitting/scoring and search; never call
per-proposal evaluations independent observations. Prefer a few compressed files
and six clear figures over many generated files. Verify repeat-run scientific
digests and inspect all figures. CI runs all tests plus a small smoke workload,
not the primary study. Publish reviewed artifacts, roadmap/log and a PR; never merge.

Any implementation correction must be documented. Scientific amendments require
dated rationale, which outcomes were already seen, and a new Git commit. Preserve
all adverse outcomes. No threshold changes after final evaluation.
