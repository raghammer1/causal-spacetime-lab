# Experiment 4 preregistration: local causal structure and identifiability

2026-10-25. Branch `experiment/local-causal-structure-v1` starts at `8dccf04`.
PR #3 was verified merged; post-merge main CI
[40160786346](https://github.com/raghammer1/causal-spacetime-lab/actions/runs/40160786346)
passed Python 3.10/3.14 before implementation. Baseline: 506 tests and the
Experiment 3 smoke CLI. Preserve every previous result and source module.
Commit this protocol before new primary samples. A resource-only pilot may select
the final workload by the rule below, never by favorable scientific outcomes.

## Objective and scope

Explain which finite local relationships are absent from global summaries, which
are algebraically redundant, and when conditional interval laws remove outer
boundary dependence. This is not a seventh acceptance classifier. No learned
acceptance threshold, aggregate recognition accuracy, or geometry certificate is
introduced. “Local” means an order-defined open interval or small induced pattern;
a random small subset need not be nearby in any continuum metric.

Established mathematical sampling models, derived finite identities, numerical
checks and physical speculation must remain distinct. Flat geometry is supplied
to reference generators. Passing their conditional laws is not evidence that a
network is physical spacetime or that gravitational dynamics has emerged.

## Primary mathematical questions and falsification

H1 (exact nonredundancy): exhibit orders with identical
S=(N,R,H,full interval-cardinality histogram) but different induced 2+2 counts,
open-interval connectivity or overlap structure. Validate identities against
complete unlabeled-poset enumeration through five events. Any mismatch with brute
force is an implementation failure, requiring correction before primary inference.
Explicit nondual witnesses must avoid conflating new information with time reversal.

H2 (conditional local law): for iid uniform samples in any finite-volume causally
convex flat region, conditioning on related endpoints and m interior events gives
the usual m-event Alexandrov-interval order law. Test diamonds and central-time
slabs of diamonds in d=2,3,4. Spatial boxes are separate clipping controls, not
examples of absent geometry. An expected-zero residual is
`B_g,m - p_g(d,m)*A_m`; never assume `E[B/A]=p` for a random per-order denominator.

H3 (geometric reconstruction): use the pooled probability that a two-event open
interval is connected to infer dimension through the already derived p(d)
inverse. This estimator uses no test dimension. Its theoretical scope is uniform,
causally convex flat sampling. Compare it with global MM inference across regions,
with uncertainty and undefined cells retained. Do not infer a physical dimension
for synthetic controls merely by returning a number.

H4 (joint information and limits): measure joint size/component/pattern profiles,
overlap moments and correlations, explicitly deriving their dependencies. Exact
summary degeneracy and identical rank/geometric order laws remain limits even
if additional observables resolve particular examples. No claim of a controlled
continuum limit follows from finite separability.

H5 (scaled matching): test whether finite searches inside an EXACT old-statistic
fiber can change local invariants. Count every failed or frozen search. A changed
local invariant proves distinct isomorphism classes; a changed labeled matrix
alone does not. The search is neither uniform sampling of the fiber nor a proof
that the changed order is nonembeddable.

## Definitions and exact checks

Use strict transitive orders and open intervals I(a,b), excluding endpoints.
The comparability graph on an open interval defines its component count; closed
intervals are trivially connected via endpoints and are not the intended statistic.
Store sparse A[m,k], numbers of related endpoint pairs with m interior events and
k components. Its m-marginal must exactly equal the old full histogram a_m.

For incomparable minima a,c, count induced 2+2 by
`sum (|F(a)|-|F(a) intersect F(c)|)*(|F(c)|-|F(a) intersect F(c)|)`.
Validate against the dual predecessor identity and direct four-subset enumeration.
With q_v=|Past(v)|*|Future(v)| and
c_uv=|Past(u) intersect Past(v)|*|Future(u) intersect Future(v)|, derive and test
`O1=sum_v binom(q_v,2)` and `O2=sum_{u<v} binom(c_uv,2)` for the first two
factorial overlap moments over distinct unordered pairs of open intervals.

Also verify `C3=sum_m m*a_m=sum_v q_v`,
`C4_chain=sum_{b<c}|Past(b)|*|Future(c)|`, and
`C4_chain+diamond4=sum_m binom(m,2)*a_m`.
In/out-degree covariance equals C3/N-(R/N)^2 and is therefore old information.
Overlap mean is a degree-product moment, not an independent source of evidence.

Canonical directed four-event isomorphism classes have stable sorted bit-code IDs.
Dual classes are retained separately; report their duality map rather than claiming
every directed motif frequency is dual invariant. Exhaust all forward transitive
relation masks and all relabelings through N=5 (expected counts 1,1,2,5,16,63 for
N=0..5), then compare independent brute-force interval/overlap/motif counts.
Global four-motif frequencies use 4,096 uniform four-subsets with replacement for
large orders; small orders up to 16 use exact enumeration. Retain conditional
Monte Carlo variances separately; exact n22 is the principal global motif statistic.

Within every parent order, count ALL size-two, size-four and size-eight intervals:
size2 connectivity; size4 full 16-motif distribution; size8 connectivity, exact
n22, and their joint distribution. Specifically store sums of n22 and of
connected*n22. Normalize n22 at size8 by binom(8,4), not by independent intervals.

Exact d2 anchors: p22=1/24 from the 24 uniform second-coordinate permutations;
connectedness at m2/m3/m4 is 1/2,1/2,13/24. The d2 reference at m8 is obtained
by all 8! permutations, with connectedness independently checked by the
indecomposable-permutation recurrence. Include the old ten-event nondual pair
(n22=12 versus16), the four-event 2+2/V-plus-isolate pair, and exact rank-two law
equivalence. A six-event standard example S3 provides an explicit obstruction
to a two-ranking/1+1D flat embedding, with a separately verified 2+1D embedding;
individual four-event motifs alone cannot supply that obstruction.

## Independent reference fits and final ensembles

Master seed **20261025**, namespace `local-v1`. Three independent fit indices 0,1,2.
Canonical compact ASCII JSON `[namespace,seed,fit,phase,family,d,N,repeat,parameter]`
is SHA256-hashed into PCG64. Distinct streams for reference4, reference8, final,
motif sampling, search, bootstrap, pilot and benchmark. Loop order/workers cannot
change samples. No final adversary outcomes may tune features or reference fits.

For d3 and d4 in EACH fit, independently sample 5,000 standalone four-event
diamonds and 2,000 eight-event diamonds. Retain reference categorical records and
the complete fit. d2 uses exact permutation reference distributions, not fitted
probabilities. The size2 connectivity probability is analytic p(d) for all d.
These are reference-law calibrations, not trained recognition models.

Proposed full test grid: d=(2,3,4), N=(64,128,256), three fits, R=200 independent
parent orders per cell for each region:

- Uniform Alexandrov diamond of duration one.
- Uniform central slab of that diamond with t in [1/4,3/4], obtained by rejection
  sampling at fixed count. It is causally convex and has a different outer shape.
- Uniform spacetime box t in [0,1], spatial coordinates in [-1/2,1/2]^(d-1).
  It can clip causal intervals and is excluded from the convex-law equivalence gate.

For each fit/N also sample R rank-two orders (positive law overlap), R random
interval orders (known construction with new held-out samples), and R intersections
of three random rankings (**unseen construction held out from development**).
Three rankings are not identified with three-dimensional Minkowski spacetime.
Compare synthetic summaries with every candidate reference dimension descriptively;
do not select a favored candidate using a hidden generating label or turn this
comparison into an acceptance classifier.

Exact matched-summary pairs use C8 and 2K2,2 bipartite modules over a common base
poset. Generate R independent bases for each fit/N in both regimes below, using
forward DAG edges p=min(1,2/q), explicit closure and random relabeling:

- Fixed module size: q=N/8 base events, each replaced by an eight-event module.
- Inflated modules: q=4, replace each original module event by s=N/32 incomparable
  twins, so each module has 8s events.

All cross-module relations follow the base. Prove and verify exact equality of S,
joint past/future-degree distributions and O1 in each pair. The n22 difference is
4q*s^4. At fixed module size, normalized difference is O(N^-3); at fixed q it has
a nonzero limit. This is a controlled information-loss demonstration, not a claim
that either family matches uniform Minkowski sampling. Do not mistake the fixed
contrast for independent noisy evidence repeated R times.

## Exact-fiber search with size-dependent budgets

Use F=32 fresh independent diamond donors per fit/d/N, separate from all reference
and ordinary final streams. Default attempted switches B(N)=N^2/64, hence
64,256,1024 at the three counts. This fixes attempts per possible adjacency edge;
it does not guarantee mixing or equal effective power. For smoke counts use an
explicit positive small budget. Every proposal draws two distinct current cover
edges once; shared endpoints, missing candidates, existing replacement edges,
cycles and unchanged closures are retained rejection categories, not resampled.

Swap the upper endpoints, form explicit transitive closure, and accept only when
the exact old signature S is unchanged. Recompute the Hasse graph after accepted
moves. No new local statistic, detector score, reference dimension or coordinates
enters acceptance. Store initial, floor(B/2) and final orders' features and search
metadata, preserving within-donor pairing. Record nontrivial accepted moves,
all rejection categories, old-invariant equality, matrix movement, and local
invariant changes. No movement means an uninformative/frozen finite search, not
rigidity. No local change does not establish isomorphism. Retain all donors.

At R=200,F=32 the main data contain 31,392 parent/checkpoint records: 16,200 region
orders, 5,400 rank/interval controls, 7,200 exact-pair members and 2,592 fiber
checkpoints from 864 searches. Reference Monte Carlo contributes 42,000 small
orders separately; the exact d2 tables are deterministic, with no fake uncertainty.

## Estimands, uncertainty and prespecified decisions

The main estimand is the ratio of ensemble sums, sum(B)/sum(A), compared with the
reference probability/expectation. Report it alongside mean centered per-parent
counts `[B-p*A]/binom(N,2)`. A missing interval size gives zero centered counts,
not a fabricated conditional probability. Parent orders with no such interval
remain in uncertainty resampling and denominators for parent counts.

Bootstrap 2,000 times using independent whole parent orders and independently
resampled reference orders within each fit. Across fits use the equal-weight mean
of fitwise pooled-ratio deviations (and fitwise TV), not one ratio that weights
fits by their interval abundance. Additionally resample fits for hierarchical
results; retain per-fit estimates and observed fit ranges. Paired region
or generator observations are paired only when explicitly constructed from the
same base/donor. Otherwise resample the two samples independently within their
shared fit. Overlapping intervals, sampled motifs and search proposals are never
independent sampling units. Three fits give limited between-fit inference;
intervals are pointwise, not simultaneous universal coverage.

Primary checks concern N=256 diamond and convex slab for each d. Practical
equivalence margins on conditional probabilities/expectations are:
size2 connected ±.02; size4 2+2 ±.01; size4 connected ±.03; size8 connected ±.05;
size8 n22 density ±.01; size8 connected*n22 density ±.01. For the entire size4
profile use total variation margin .08, with reference-calibration uncertainty.
A 95% difference interval wholly inside the margin supports this finite numerical
equivalence check; wholly outside contradicts it; overlap is inconclusive. Require
at least 30 parents containing the interval size and at least 100 intervals within
EACH fit before a pooled equivalence declaration; otherwise mark insufficient
information. A confidence interval merely containing zero is not support.

Secondary checks: all smaller N; global22 d2 diamond/rank expectation1/24; local
dimension estimates with interval propagation and optional ±.25 dimension-unit
equivalence at N256; box/clipping effects; all16 directed motif frequencies;
size/component joint tables; joint size8 connectedness and n22; covariance and
correlation matrices of declared global/local quantities. Describe algebraic
dependencies explicitly and never invert a singular covariance to manufacture
independent evidence. Keep all correlations descriptive with pointwise intervals
for selected pairs, not a search for favorable significance.

For exact pairs, any old-signature mismatch is a code failure. Test predicted
n22 differences exactly, and retain unexpected equalities of the new summaries.
For fiber searches report per-fit Wilson intervals for movement and invariant
change, and paired whole-donor bootstrap changes. Zero successes still have
nonzero upper bounds. No empirical threshold becomes an embedding definition.

## Resource pilot, fixed selection rule and publication

No new dependency beyond Python/NumPy/Matplotlib/pytest. Cap public matrices at
512, primary at256, three worker processes, total primary wall budget45minutes
and conservative sum of process peak RSS below4GiB. Use seed20261024, phasepilot,
at most two orders per d/N/region and two fiber donors per d/N. Measure generation,
full extraction including global motif sampling, search and reference-enumeration
costs. Do not inspect scientific values, match rates or unseen-family outcomes.

Select the largest R in (200,100,50), then largest F in (32,16,8), for which
timing-only extrapolation with a1.5 safety factor and assumed twofold speedup on
three workers projects at most30minutes, including reference work. Preserve all
three counts/dimensions/fits and every observable. Record the arithmetic and
commit a workload-selection note BEFORE primary outcomes. If no candidate fits,
record a resource amendment before any primary run; never silently truncate.
Implementation performance fixes may precede primary execution but may not select
scientifically favorable seeds or constructions. Benchmark standalone statistics
and search separately; timing is not part of the deterministic scientific digest.

Keep machine-readable parent/reference records, full old histograms, joint local
counts, reference fits, bootstrap summaries, exact-pair and search metadata, fixed
counterexamples, six or more clear figures, source/protocol/workload hashes and
versions. Use compressed artifacts rather than every candidate matrix. Verify a
complete repeat and independent reconstruction checks. Run all tests and one
end-to-end CLI before commits; add only a smoke workload to CI. Review secrets
and private paths before pushing the branch and creating a PR; never merge it.

If new features give no interpretable structural insight, recommend stopping
classifier optimization and studying explicitly exploratory causal dynamics.
If useful identities/local laws survive verification, specify missing assumptions
for continuum reconstruction: sampling/density, causal convexity, curvature and
scale control, faithful embeddings/uniqueness, and dynamics. Do not equate this
finite study with a controlled continuum limit.

Primary foundations: [Fewster et al. (2021)](https://arxiv.org/abs/2011.02965),
[Glaser and Surya (2013)](https://arxiv.org/abs/1309.3403),
[Brinkmann and McKay (2002)](https://users.cecs.anu.edu.au/~bdm/papers/posets.pdf),
and [Fishburn (1970)](https://doi.org/10.1016/0022-2496(70)90062-3).
Full derivations distinguish source results from identities derived in this lab.
