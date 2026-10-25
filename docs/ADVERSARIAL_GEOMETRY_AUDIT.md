# Experiment 3: independent audit of Experiment 2

2026-10-25. This audit precedes the Experiment 3 primary study. It examines
the archived Experiment 2 results and implementation, without changing their
scientific conclusions or regenerating their published artifacts.

## Checks and scope

The audit read the [results](DIMENSION_RECONSTRUCTION_RESULTS.md),
[theory](DIMENSION_THEORY.md), detector implementation, and archived
[raw records](experiments/dimension-reconstruction-v1/raw.csv),
[calibration records](experiments/dimension-reconstruction-v1/calibration.csv),
and [fitted model](experiments/dimension-reconstruction-v1/calibration_model.json).
All 172 Experiment 2 tests passed. Refitting the model from the 900 archived
calibration records reproduced its JSON exactly. Recomputing both scores and
decisions for all 4,806 evaluation records gave zero score differences and zero
decision mismatches. Calibration and evaluation sample IDs were disjoint.

No result-affecting implementation error was found. This is a bounded code and
artifact audit, not a proof that the entire package is free of errors. One minor
input-validation inconsistency is that the existing Wilson helper accepts Python
Boolean counts (`True` is an integer subclass). No published input used such a
count. Experiment 3 will reject Boolean counts in its statistics API; this does
not change the archived Experiment 2 analysis.

## Seven verified limitations

### 1. Matching ordering fraction fools dimension inference

All 1,800 matched two-layer controls passed the ordering-fraction detector and
received their target Myrheim–Meyer label. All were rejected by the five-feature
detector. Matching one ensemble mean neither matches the full distribution nor
establishes a geometric embedding. The controls show that ordering fraction alone
is insufficient for the proposed structural discrimination task.

### 2. Height already separates the easy matched controls

Every matched two-layer control had height exactly two. Genuine observed height
ranges were:

| N | d=2 | d=3 | d=4 |
|---:|---:|---:|---:|
| 64 | 10–17 | 4–9 | 3–6 |
| 128 | 14–24 | 6–12 | 4–7 |
| 256 | 23–34 | 9–14 | 5–9 |

Thus `height > 2` separates every observed matched control from every observed
genuine order. This is a post hoc audit observation, not a preregistered test of
a calibrated height detector. Independent Experiment 3 holdouts are necessary
to compare height alone with richer detectors at matched genuine-acceptance
targets. The previous rejection result does not demonstrate the necessity of
five features.

### 3. The joint detector accepts some random DAG controls

At N=64, the joint detector accepted 49/200 random-DAG controls: 24.5%, with
two-sided 95% Wilson interval [19.06%, 30.90%]. All 49 had an **unclassified**
Myrheim–Meyer label under the fixed [1.5,4.5] classification range. Structural
acceptance is distinct from dimensional classification. These acceptances are
failures against the chosen synthetic-control benchmark; construction without
coordinates does not prove a lack of every possible continuum embedding.

### 4. Score compensation admits previously rejected controls

The exact N=64 random-DAG decision table is:

| Ordering-fraction decision | Joint accepted | Joint rejected |
|---|---:|---:|
| Accepted | 13 | 122 |
| Rejected | 36 | 29 |

The 36 joint-only acceptances are genuine score compensation, not a code error.
For example, archived random-DAG repeat 193, sample ID
`4d3216ff4a4bb694d8deae91f20e21b677aa17cbc2b8d99779620e6d3b2d6376`,
has N=64, 62 relations, r=0.0307539683, height=4 and an inferred dimension of
5.37712212. Against the d=4 template its standardized residuals for r, height/N,
link fraction, normalized mean interval cardinality and fraction of intervals
containing at least four internal events are approximately
`[-2.58494, -0.43740, -0.63452, -1.00010, -1.69770]`.

The r score 2.58493931 exceeds its threshold 1.82249141, while the five-feature
root-mean-square score 1.49386924 is below its threshold 1.69422940. Averaging
squared residuals permits close features to compensate for a poor marginal
match. A maximum-residual detector removes this within-template compensation,
but its independently calibrated threshold need not equal the r-only threshold;
its accepted set is not automatically nested inside that of the r-only model.

### 5. Published uncertainty conditions on one frozen calibration fit

Each dimension/count cell used 50 samples to fit centroids and standard
deviations, and another 50 to fit thresholds. Pooling dimensions gave 150
threshold samples per N. The published Wilson intervals condition on the fitted
model; they do not propagate uncertainty in its centroid, scales, threshold or
fitted adversary parameters. Exact reproducibility does not establish robustness
to a new calibration sample. Experiment 3 therefore needs independently fitted
models with independent holdouts, per-fit intervals and an explicit assessment
of between-fit variation. Repeated decisions on shared orders must not be
treated as independent Bernoulli samples.

### 6. The selected summaries lose directed-order information

The three-event V order and its order dual have identical outputs from
`order_observables`, including the complete interval-cardinality histogram,
relation count, height and all five selected features. They are not isomorphic
as directed orders: they have respectively two and one minimal elements, a
quantity preserved by relabeling. This exact counterexample establishes that
these summaries are not a complete directed-poset invariant. It says neither
that every finite collection of statistics fails nor that a time-reversal
symmetric physical benchmark should distinguish opposite time orientations.

### 7. Larger DAGs become easier controls under the chosen edge rule

For p=2/N, mean inferred dimensions were 4.63163, 5.34023 and 6.08229 at
N=64,128,256. Both detectors rejected every sampled DAG at N=128 and N=256.
The controls move farther from the calibrated d=2–4 ensemble as N increases.
Improved rejection therefore does not isolate improved geometric discrimination
with size. Prespecified edge-probability sweeps and controls matching more than
ordering fraction provide a stronger falsification test.

## Consequences for Experiment 3

Preserve the original RMS detector as a benchmark, including its compensating
behavior. Compare it with height-only and two-feature baselines, a maximum-score
model, and interval-abundance information. Evaluate each against independently
generated controls while matching genuine-acceptance targets on validation data.
Retain paired decision changes, unsuccessful adversarial searches, out-of-domain
estimates and every holdout failure. Calibration repetition and harder controls
address demonstrated weaknesses; no classifier outcome proves physical spacetime,
emergent gravity or singularity resolution.
