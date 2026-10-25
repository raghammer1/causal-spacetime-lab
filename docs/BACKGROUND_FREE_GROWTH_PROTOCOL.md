# Experiment 5: background-free causal growth — registered protocol

Status: register before growth implementation and primary sampling. This is an
exploratory mathematical study of a specified intrinsic stochastic law. It does
not test whether physical spacetime, gravity or quantum dynamics has emerged.

## Verified baseline and scope

Experiment 4 was published in PR #4 and merged into `main` at
`f84153683dd4769f041dad9f2a7181240059ddb2`. The post-merge Python 3.10/3.14
[CI run 40164911842](https://github.com/raghammer1/causal-spacetime-lab/actions/runs/40164911842)
passed before this branch was created. Its complete archive and independent
audit/replay records were rechecked. Prior mathematical, code and visual reviews
are documented; GitHub itself contains no submitted formal review. We distinguish
that fact from the verified independent computational review, without inventing
a new human-approval requirement.

Branch: `experiment/background-free-growth-v1`, from verified `origin/main`.
All previous experiments, code and archives remain intact. Read the accompanying
[mathematical foundations](BACKGROUND_FREE_GROWTH_THEORY.md) and Experiment 4's
[continuum analysis](LOCAL_CAUSAL_STRUCTURE_CONTINUUM.md) before implementation.

## Mathematical restrictions known before numerical work

The model is fixed-parameter transitive percolation, a special case of ordinary
Rideout–Sorkin classical sequential growth (CSG). No custom growth rule is used.
For each new birth j, independently select each older event with probability p,
then take the ancestral closure. Coordinates, dimension, distance, geometric
features and reference-model scores are absent from this generator.

For a specified precursor down-set S of an n-event order, with s events and m
maxima, the transition probability is p^m(1-p)^(n-s). For a particular natural
labeling of a final order it multiplies to p^L(1-p)^I, where L counts covers and
I counts incomparable pairs. Equal elementary path weights across valid natural
birth descriptions are the covariance test; arbitrary final-matrix relabeling
alone is not that test. An unlabeled probability also needs its multiplicity.

For fixed 0<p<1, a direct two-step-path bound gives

```
Pr(i || j) <= (1-p)*(1-p*p)^(j-i-1)
E[1-r_N] <= 2*(1-p)/((N-1)*p*p)
E[t22_N] <= 3*(1-p)/((N-1)*p*p) -> 0.
```

The foundation document strengthens this to a single-history almost-sure
chain-sampling limit. It does not imply H_N/N approaches one. Broader CSG limits
in Brightwell–Georgiou's expected finite-suborder sampling sense are almost
semiorders: induced 2+2 and 3+1 densities vanish. The precise nonnegative-coupling
hypotheses and convergence notion are recorded there. These facts already rule
out a nondegenerate Minkowski sampling limit in that sense. Finite numerical
agreement cannot overturn them, and finite disagreement is not a new theorem.

We test finite-size crossovers and consistency. We do not tune p(N), introduce
an ad hoc dynamics, or select favorable p values after observing outcomes.
Separately chosen constant-p(N) ensembles and a varying-p-at-birth process are
different objects; exact small examples will demonstrate their consistency and
covariance differences without treating either as a primary growth model.

## Hypotheses, controls and adverse outcomes

H1: the implementation reproduces the specified transition law, closure and
prefix process, and its elementary probabilities satisfy natural-label path
covariance and the spectator-removal probability-ratio identity. An exact
disagreement is an implementation failure; do not run the primary study until
resolved. No assertion about arbitrary custom dynamics follows.

H2: some finite windows may have t22 near 1/24, but a fixed-p Minkowski limit is
excluded. Register a necessary finite-signature screen below, preserving every
parameter and every failure. Finite nonmonotonicity is allowed: the theorem does
not claim a monotone curve over N=32..512 or a useful finite error bound there.

H3: uniform induced thinning is motif-unbiased for EVERY fixed parent order.
Its conditional expectation equals the parent's motif density. This is an
identity to verify, not special evidence for geometry. Compare thinned N-event
orders with the matched smaller birth prefix, and inspect height and conditional
interval laws. Growth need not be exchangeable or consistent under thinning.

H4: an explicitly supplied-layer height-two control matches E[t22]=1/24 at
every size and has exchangeable prefix/thinning laws, while H<=2 and every open
interval is empty. It falsifies the sufficiency of the single-motif screen even
if its finite comparisons pass. This control is not the intrinsic growth model.

H5: numerical convergence of selected summaries is not a continuum limit.
The investigation probes necessary finite-suborder sampling conditions, selected
history-level concentration/drift, and thinning behavior. It does not verify all
finite suborder probabilities, tightness in a metric reconstruction topology,
faithful embedding, approximate uniqueness, mesoscopic locality, curvature or
dynamical universality. The final recommendation must retain this separation.

## Frozen sample grid and random streams

Primary stochastic p grid: **.005, .01, .02, .05, .1, .3**.
Deterministic endpoints p=0 and p=1 are recorded once each, with analytic
antichain/chain behavior; repeated identical endpoints are not independent data.

Each stochastic history grows to 512 events. Record its prefixes at
**32,64,128,256,512**. For source sizes 128,256,512, independently select **four**
uniform subsets of exactly half the events. Retain the induced CLOSED relation
and sorted original indices. Do not delete primitive edges and recompute paths:
precedence mediated through a deleted event must remain in the induced order.
Sampling is without replacement within each subset, independently with possible
repetition across the four subsets.
There are five prefix records and twelve thinning records per history.

Use three named independent seed batches, initially **R=64 histories per batch
and stochastic family**. Batches are seed partitions, not three populations or
trained classifiers. Preserve each whole history as one resampling unit across
all prefixes and thinning replicas. The timing pilot may select R=64,32,16 by
the fixed rule below, before primary data are examined.

Independent comparison families, each with the same batches, histories and
prefix/thinning grid:

- Uniform Minkowski diamond samples in d=2,3,4. Nested iid sampling prefixes are
  reference ensembles, not maximal-element CSG birth histories. Their dimensions
  and coordinates are confined to reference generation and validation.
- A semiorder: independent U in [0,1], with a<b iff U_b-U_a>.25. These utilities
  define a mathematical control, not inferred spacetime coordinates or growth.
- The matched-22 height-two control: iid fair lower/upper marks, independent
  lower-to-upper relations of probability
  q=(1-sqrt(1-4/(3*sqrt(2))))/2. There are no within-layer relations. Its exact
  four-subset expectation is (3/4)*q^2*(1-q)^2=1/24. Parameters are chosen
  analytically for this deliberately misleading control, never fed to growth.

Thus there are eleven stochastic families. The proposed R=64 workload has
**35,904 stochastic parent/checkpoint records plus 34 deterministic endpoint
records**, representing 2,112 independent stochastic histories. Thinnings and
prefixes are not additional independent histories.

Master seed 20261025, namespace `growth-v1`. Parameter-keyed PCG64 streams use a
canonical compact ASCII JSON identity and SHA256. The generation identity omits
terminal size, so extending a fixed-p history preserves its earlier draws.
Separate phases distinguish generation, motifs, thinning, bootstrap and pilot;
thinning includes source size and replica number. Batches and history numbers
are explicit. Workers and loop order cannot change a sample.

Conditional-law calibration uses fresh independent small diamond orders via the
verified Experiment 4 reference constructor with reserved seed **20261026**:
three fits, 5,000 four-event and 2,000 eight-event orders per d=3,4 fit. Its
`local-v1` namespace is retained and documented; this seed differs from every
previous primary reference seed. d=2 uses the complete 24/40,320 permutation
tables, without artificial calibration error. Retain every stochastic reference
category and all fitted counts. No growth/control outcome tunes these fits.

## Observables and structural validation

Reuse ordering fraction, height, interval-cardinality histogram, exact n22,
chain/diamond counts, interval component profile, overlap moments and the
conditional size-2/4/8 laws from Experiment 4. Add exact induced 3+1 counting,
needed for the semiorder obstruction:

```
n31 = sum_{a<c} m_ac * (N - |F(a)| - |P(c)| + m_ac),
m_ac = |F(a) intersect P(c)|.
```

The isolated vertex must be incomparable with both chain endpoints; transitivity
then makes it incomparable with the middle event. Verify against exhaustive
four-subset classification on every poset through five events. Exact n22 and n31
are primary counting quantities; 4,096 independent uniform four-subset draws per
large recorded order estimate the full 16-motif vector. Store its conditional
Monte Carlo variance separately from history-level uncertainty. Small orders
may use exact motif enumeration. No composite classifier is fitted.

Myrheim–Meyer inversion and conditional local inversion retain their domain
restrictions and undefined values. On growth/control orders call them
**reference-equivalent diagnostics**, not physical dimensions. Report r, H,
H/N, and H/sqrt(N) (the latter explicitly a d2 scaling comparison), t22, t31,
all motif probabilities and local-law joint quantities. Missing intervals do
not become zeros or automatic compatibility.

Generator checks include independent Floyd–Warshall closure; every forward
primitive DAG through N=5; normalization of its Bernoulli weights grouped by
closure; valid-downset transition sums; elementary weights across all natural
labelings of small orders; spectator-removal ratios; p=0/1 limits; arbitrary
relabeling of observables; exact same-seed prefix identity; and rejection of
invalid birth permutations. At N=4, Pr(2+2)=3p^2(1-p)^4 and
Pr(3+1)=4p^2(1-p)^3. These formulas are not the four-subset laws inside a larger
order, whose relations may be mediated through omitted events.

## Primary finite-signature screen and uncertainty

For each of the six stochastic p settings, define eight whole-history values:

1. t22 at N=128,256,512, minus 1/24 (three values).
2. Paired changes 128→256 and 256→512 (two values).
3. Mean over four N→N/2 thinnings minus that same history's N/2 birth-prefix
   t22, for N=128,256,512 (three values).

The practical margin is **±.005 for each**. With 2,000 bootstrap replicates,
resample histories independently within each batch and parameter; reuse each
history weight across all eight values. Average batches equally. There is no
outer bootstrap of artificial seed batches for this primary statistic.
Take the 97.5th percentile of the maximum absolute centered bootstrap error over
all **48** registered entries to form common-width simultaneous bands. Report
pointwise bands and batch means as well, labeled separately.

Allocate the remaining .025 error budget to zero-event safeguards across those
48 entries. For an all-zero stochastic density observed in M independent
histories, q0=1-(.025/48)^(1/M) bounds the probability of a positive value, hence
its mean, since the density is bounded by one. Widen its band to include [0,q0]
before subtracting 1/24. For an all-zero contrast in [-1,1], widen to [-q0,q0].
Other constant stochastic cells must not receive false certainty: report the
full known range and an inconclusive degeneracy flag. Analytically deterministic
p=0/1 is treated separately. Bootstrap coverage is approximate; the safeguard
does not turn the joint procedure into a proven exact finite-sample interval.

All eight bands strictly inside their margins mean only **finite-window
compatibility of this necessary signature**. Any band wholly outside its margin
is a failure of that finite signature; otherwise it is inconclusive. Retain every
setting. No winner is selected, and even a finite-compatible p is not a continuum
candidate in defiance of the known fixed-p theorem. Apply the same descriptive
screen to the deliberately matched control and d2 reference to expose its limits.
Each such control has a separately labeled eight-entry band (maximum over its
own eight entries, with .025/8 for its zero-event safeguards). These exploratory
control families are not included in the primary 48-entry coverage claim.

## Secondary joint/history analysis

Summarize all prefix/thinning cells and paired thinning-minus-prefix contrasts
for r, height diagnostics, exact forbidden motifs and conditional local laws.
Keep conditional estimands as sum(B)/sum(A) within each batch, then equal batch
means. For each thinned-history cell, average its four numerator/denominator
arrays BEFORE pooling or bootstrapping; support is the summed MEAN interval
exposure, not four independent parents. Use the same history weights for all
cells, including missing-denominator rows.

For each candidate reference dimension, generate one independent calibration
bootstrap array per batch and reuse it across every family and cell sharing that
reference. Reference probabilities cancel in thinning-minus-prefix probability
contrasts; do not add calibration error twice. Preserve undefined resamples and
suppress an interval if its required bootstrap values are undefined. Support
requires at least 30 positive histories and mean interval exposure at least 100
in each batch. R=16 necessarily fails this support rule; do not relax it after
the pilot. All smaller-support outcomes remain recorded.

Reuse Experiment 4's seven pointwise conditional comparison margins (.02,.01,
.03,.05,.01,.01,.08), without claiming simultaneous coverage for this secondary
family. Average fitwise TV, not TV of averaged deviations. Preserve its known
nonsmooth-bootstrap limitation. Compare growth and artificial controls against
every d=2,3,4 reference descriptively; use the supplied dimension only to evaluate
the known Minkowski reference ensembles. No best-fitting geometric label.

Show prespecified histories numbered 0..7 in batch 0 (not favorable selections),
all-ensemble trajectories, forbidden-motif/ordering/height joint plots, thinning
contrasts, conditional-law residuals and interval support. Changes of r alone
can conceal vanishing 2+2 or inappropriate height. Correlation is not independent
evidence. No finite sample establishes every-Q sampling convergence.

## Resource-only pilot, execution and publication

No new dependencies beyond Python 3.10+, NumPy, Matplotlib and pytest. Public
event cap512; keep all five sizes, all parameters and all controls. Three worker
processes, primary computation limit45 minutes and conservative sum of process
peak RSS below4 GiB. Store bounded family shards if needed rather than retaining
every large record in every process.

Pilot seed20261024 in the distinct growth namespace/phase. Time at most one full
history per family plus deterministic endpoints, including all registered feature
extraction and four thinnings. Time reference construction on a small separate
seed and bootstrap on fabricated records. Do not retain or inspect pilot
scientific values, near-matches, favorable curves or control outcomes.

Select the largest R in **64,32,16** whose timing-only projection, with 1.5 safety
factor, assumed twofold speedup on three workers, reference cost and a fixed
180-second analysis allowance, is at most25 minutes. Commit the exact arithmetic
and workload choice BEFORE primary data. If none qualifies, document a resource
amendment before execution; do not silently drop N512 or favorable-select models.

Retain primitive growth edges or equivalent exact reconstruction records,
history/prefix/thinning identities, retained vertex indices, raw features,
all reference outcomes, unsuccessful signature cells, provenance and timings.
Audit invariants and a fixed, outcome-independent seeded subset. Repeat the full
selected run and compare deterministic scientific digests; timings are excluded.
Keep archive shards and checksum manifests machine-readable. Visually review
scientific figures. Add only a bounded smoke run to CI.

Run all old/new tests and an end-to-end reproducible CLI before commits. Publish
`docs/BACKGROUND_FREE_GROWTH_RESULTS.md`, update roadmap/log, push this branch and
open a PR into main. Do not merge automatically. Recommend a scoped scientific
go/no-go for further intrinsic dynamics: no-go for claiming Minkowski emergence
from this ordinary CSG limit; any future altered dynamics needs a mathematical
reason, an explicit changed assumption and fresh covariance/consistency analysis.
