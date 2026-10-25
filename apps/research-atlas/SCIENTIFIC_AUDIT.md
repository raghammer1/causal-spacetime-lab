# Scientific evidence and frontend data audit

The atlas transcribes archived research; it does not run a new research study. Its
browser toys are bounded illustrations of documented rules and must remain
visibly separate from archived ensemble measurements.

## Verified source and reproducible transformation

The scientific source is verified main commit
`9bc5984c656271c247354e0079fd900702642064`, which includes Experiment 5 (PR #5).
The existing Python CI on that main commit passed. Every input's local bytes
were independently compared with `git show <commit>:<path>` when establishing
`scripts/source-lock.json`. The converter rejects a hash mismatch instead of
silently pointing changed data at an immutable historical URL.

Run from the repository root:

```sh
python3 apps/research-atlas/scripts/generate_data.py
python3 apps/research-atlas/scripts/generate_data.py --check
python3 -m unittest discover -s apps/research-atlas/scripts -p 'test_*.py'
```

No NumPy, simulations, resampling or fits are used during this transformation.
CSV numeric values are parsed without rounding. Empty fields are `null`, never
zero. Existing two-endpoint uncertainty fields gain convenience endpoint columns;
the original fields remain. The generator retains negative outcomes, missing
support and uncertainty intervals which do not contain their point estimate.
Nested diagnostic support objects are omitted from some compact frontend tables,
with that selection disclosed in each dataset; immutable source links expose the
complete records. No observation is averaged or pooled by the conversion.

Generated JSON stores the column names once and each record as an aligned value
array. `src/data/hydrate.ts` restores the public `Dataset.rows` objects exactly,
rejecting mismatched row widths. This lossless transport reduces the 13-dataset
JSON payload from 7,890,736 to about 3,915,336 bytes (50.4%) without removing any
scalar, missingness marker, interval string or interval endpoint. Browser routes
continue to receive the same dataset API. `catalog.ts` supplies metadata and source
provenance without observations; `loader.ts` dynamically imports and hydrates only
the selected dataset, caches successful requests and permits retry after a failed
fetch. Time reconstruction therefore does not download the growth archive.
`index.ts` retains the eager compatibility API for tests. Python tests verify every packed row
round-trips exactly; Vitest verifies the runtime schema and scientific anchors.

The generated provenance manifest records reports, protocols, derivations and
table SHA256s from the explicit source lock. Each actual data input is checked
against its locked bytes on every build. Documentary references retain the
reviewed commit's hashes and URLs even when the current research log or roadmap
evolves; later experiment documents are not added to this first-five snapshot.
`local-dimensions` joins the archived local estimator from
`summary.json` and global estimator from `global.csv`; both hashes are retained.
These represent different nonlinear estimands, not interchangeable measurements.

## Claim-to-source ledger

All paths below are relative to the repository root. Frontend source links pin
them to the verified commit rather than to a moving branch.

| Claim and scientific status | Evidence | Necessary scope |
| --- | --- | --- |
| **Known mathematical reconstruction:** `T_hat=L/sqrt(2 rho)` is asymptotically normalized in the 1+1D model. | `docs/THEORY.md`; `src/causal_lab/core.py` | Known uniform Poisson density, flat diamond, `c=1`, interior chain count. Absolute time requires density calibration. The fast LIS implementation uses coordinates; order-only dynamic programming does not. |
| **Numerical observation:** bias decreases between density endpoints but remains negative in 4,200 trials. | `docs/FINITE_DENSITY_RESULTS.md`; `docs/experiments/finite-density-scaling-v1/summary.csv` | Seven densities, three durations, 200 independent sprinklings per cell; finite range, not a proof of an asymptotic limit. |
| **Adverse finding and independent diagnostic:** one equal-count primary contrast excluded zero; an 8,000-trial follow-up did not reproduce a persistent difference. | `docs/EQUAL_COUNT_FOLLOWUP_PROTOCOL.md`; primary `diagnostics.json`; follow-up `summary.csv` / `diagnostics.json` | Post hoc follow-up is separately seeded and not pooled with the preregistered study. An interval containing zero does not prove equality. |
| **Exact sampling expectation:** ordering probabilities are 1/2, 8/35 and 1/10 for dimensions 2, 3 and 4. | `docs/DIMENSION_THEORY.md`; `src/causal_lab/dimension.py` | `r=R/binom(N,2)` in uniform flat Alexandrov intervals. Another normalization gives half this value. Pair indicators are dependent. |
| **Numerical observation:** every dimension has 200/200 correct classifications at N=256. | `docs/DIMENSION_RECONSTRUCTION_RESULTS.md`; dimension `summary.csv` | Per-class 95% Wilson lower bound ≈98.1%; no claim of perfect population accuracy. N=128 is the smallest *tested* count meeting the all-class criterion. |
| **Falsified statistic-specific sufficiency:** all 1,800 matched two-layer controls pass the r-only detector. | Same report; dimension `summary.csv` / `raw.csv` | These artificial constructions have height ≤2. Their assigned target label is not a physical dimension. |
| **Numerical benchmark failure:** all six detectors fail the registered advancement gate. | `docs/ADVERSARIAL_GEOMETRY_RESULTS.md`; adversarial `advancement.json`, `rates.csv`, `summary.json` | Every designated positive/negative cell and fit must satisfy specified Wilson bounds. Some missed positive bounds are inconclusive, not proven poor retention. No aggregate winner. |
| **Numerical adverse finding:** detector F accepts 63.17% of full-search d2,N64 controls, hierarchical interval [57.33%,69.00%]. | Adversarial `summary.json`, target=.95, family=multi_matched, dimension_label=2, count=64, detector=F | Three fits ×200 orders; hierarchical pointwise uncertainty. Zero of 5,400 searches met all 15 one-SD donor-match constraints. A failed donor match can nevertheless pass a calibrated detector. |
| **Exact finite counterexample:** two nondual ten-event orders have equal old summaries, but induced 2+2 counts 12 versus16. | `docs/ADVERSARIAL_GEOMETRY_THEORY.md`; `docs/LOCAL_CAUSAL_STRUCTURE_THEORY.md`; adversarial `exact_counterexamples.json` | Selected summaries are not complete invariants of arbitrary finite orders. This does not prove either example nonembeddable in every geometry. |
| **Exact equality in law:** rank-two and d2 uniform-diamond sampling cannot be distinguished by any order-only statistic. | `docs/ADVERSARIAL_GEOMETRY_THEORY.md`; `docs/LOCAL_CAUSAL_STRUCTURE_THEORY.md` | These are two equivalent sampling procedures. Rank-two is a positive law-overlap control, not a required rejection. |
| **Derived conditional law:** conditioning on endpoint pair and internal count gives a standard diamond law. | `docs/LOCAL_CAUSAL_STRUCTURE_THEORY.md` | Uniform sampling in a causally convex flat region. The identity is `E[B-mu A]=0`, not `E[B/A]=mu`. A spatial box may clip intervals. |
| **Numerical observation:** all 42 primary N256 conditional-law checks meet practical margins. | `docs/LOCAL_CAUSAL_STRUCTURE_RESULTS.md`; local `conditional.csv` | Six diamond/slab cells ×seven observables. Whole-parent/reference hierarchical pointwise intervals; not 42 independent tests or simultaneous confidence. |
| **Numerical observation:** d4 slab global estimate 4.5813 versus local 3.9948 [3.9478,4.0401]. | Local `global.csv` (global_dimension) and `summary.json` (local_dimension) | Geometry remains flat; the global shift reflects boundary shape. Local estimator inverts pooled conditional probability; global means average per-parent inversions. |
| **Exact limitation, postregistration:** 12-cycle versus two 6-cycles match the entire measured structural vector. | `docs/LOCAL_CAUSAL_STRUCTURE_RESULTS.md#postregistration-analytic-extension-a-complete-selected-summary-collision`; local `exact_counterexample.json` | Both are height-two orders with empty intervals, n22=42 and matching motif profiles; whole-order components [12] versus [6,6] prove nonisomorphism. Postregistration derivation, not a primary outcome. |
| **Numerical no-go for tested finite signature:** all six fixed-p families fail. | `docs/BACKGROUND_FREE_GROWTH_RESULTS.md`; growth `primary.csv` / `primary.json` | p=.005,.01,.02,.05,.1,.3; N=32..512; 96 independent histories per family. Registered simultaneous bands differ from pointwise intervals. |
| **Exact fixed-p limit:** uniform finite sampled suborders approach chain law. | `docs/BACKGROUND_FREE_GROWTH_THEORY.md`, §§4–5 | Fixed 0<p<1; does not imply the infinite order is total or H/N→1. Sparse incomparable adjacent births persist. Finite motif trajectories need not be monotone. |
| **Known class-specific obstruction:** studied ordinary CSG cannot approach the nondegenerate Minkowski sampling target. | Same theory; Brightwell–Georgiou, definitions1.2–1.3 and theorems1.4–1.6 | Nonnegative couplings with t0 or t1 positive; expected finite uniformly sampled labeled-order convergence to an atomless ordered probability space. Almost-semiorder limit forbids positive induced2+2/3+1 density. Not every modified dynamics or local scaling limit. |
| **Exact insufficiency plus numerical illustration:** height-two control matches E[t22]=1/24 and passes its signature. | Growth theory §6, report, `primary.csv`, `global.csv` | iid fair lower/upper labels with q=(1-sqrt(1-4/(3sqrt2)))/2. Forced balanced layers would change the finite-N law. H≤2, no nonempty intervals, no3+1. |
| **Open or untested physical claims:** all emergent-spacetime theories are impossible; physical spacetime is discrete; singularities are resolved. | Interpretation boundaries in every report and `docs/LOCAL_CAUSAL_STRUCTURE_CONTINUUM.md` | None is established or tested by these numerical studies. The broader emergence hypothesis remains open. No Einstein dynamics or black-hole solution is implemented. |

## Dataset inventory and uncertainty

| Dataset ID | Rows | Independent unit and uncertainty |
| --- | ---: | --- |
| time-primary | 63 | 200 sprinklings per cell; 2,000-draw pointwise percentile mean intervals. Paired controls share N. |
| time-followup | 12 | 2,000 independent follow-up sprinklings per cell; 5,000-draw pointwise intervals. |
| dimension-summary | 30 | 200 whole orders per stochastic cell; percentile mean intervals and separate Wilson classification/rate intervals. |
| detector-summary | 1,350 | Three fitted detectors with independent samples; hierarchical pointwise intervals. |
| detector-rates | 4,050 | 200 orders per stochastic fit/cell; Wilson conditional intervals. Exact controls have no CI. |
| detector-advancement | 396 | The six detectors ×66 designated cells; classifications of registered criteria, not new samples. |
| local-global | 525 | Equal-fit whole-parent means; pointwise hierarchical intervals; valid/invalid counts retained. |
| local-primary | 42 | Registered six N256 geometric cells ×seven observables; pointwise practical-equivalence checks. |
| local-conditional | 2,691 | All across-fit conditional summaries, including motifs and unavailable intervals. |
| local-dimensions | 150 | Global and local nonlinear estimands transcribed separately; no invented interpolation. |
| growth-global | 2,200 | 96 histories per family; prefixes and four half-thinnings retain dependence. |
| growth-primary | 64 | 48 growth entries with shared simultaneous bands;16 control entries with separate eight-entry bands. |
| growth-conditional | 4,968 | Equal-batch pooled-count conditional ratios; whole-history uncertainty and independent reference uncertainty. |

Check row counts from generated data if the presentation selection is ever
intentionally revised. The immutable source tables remain the authority.

## Preserved adverse outcomes and display rules

- A mean confidence interval does not include systematic bias, model uncertainty,
  or uncertainty about the known input duration/dimension.
- Experimental t22, r and probability values are fractions in [0,1]; percentages
  multiply by100 for display only. Unclipped centered contrast bands can extend
  beyond a physical density range.
- Local/growth `ci95` belongs to the **difference** field; `estimate_ci95` belongs
  to the absolute estimate. TV is already a nonnegative distance.
- The nonsmooth TV bootstrap can put a lower bound above its estimate. Preserve
  that recorded limitation; do not repair error bars cosmetically.
- 17,986 growth records represent 1,056 independent stochastic histories plus
  deterministic endpoint records. Prefixes and thinnings are not fresh samples.
- The d2 growth reference's local estimate excludes2 pointwise, and its N32 TV
  secondary rule falsely rejects the known geometric control. This does not
  disprove the exact conditional law.
- Growth size-eight support at p=.005 is insufficient. Empty height-two intervals
  are unavailable rather than zero-probability agreement.
- Apply the exact1/24 reference only to d2 t22 comparisons. It is not the correct
  reference for all dimensions, metrics or boundary shapes.
- Abstract graph layouts and high-dimensional projections are visualization
  coordinates. They are not inferred physical positions.
- The event horizon is not the classical curvature singularity. Singularity
  motivation is educational context, not a result of a black-hole calculation.

## Primary scientific works cited by the archived derivations

- Bombelli, Lee, Meyer and Sorkin, *Space-time as a causal set* (1987),
  <https://doi.org/10.1103/PhysRevLett.59.521>.
- Brightwell and Gregory, *Structure of random discrete spacetime* (1991),
  <https://doi.org/10.1103/PhysRevLett.66.260>.
- Baik, Deift and Johansson, longest increasing subsequences (1999),
  <https://arxiv.org/abs/math/9810105>.
- Roy, Sinha and Surya, *The Discrete Geometry of a Small Causal Diamond* (2013),
  <https://arxiv.org/abs/1212.0631>.
- Glaser and Surya, *Towards a Definition of Locality in a Manifoldlike Causal
  Set* (2013), <https://arxiv.org/abs/1309.3403>.
- Fewster et al., *Local Structure of Sprinkled Causal Sets* (2021),
  <https://arxiv.org/abs/2011.02965>.
- Rideout and Sorkin, *A Classical Sequential Growth Dynamics for Causal Sets*
  (2000), <https://arxiv.org/abs/gr-qc/9904062>.
- Brightwell and Georgiou, *Continuum Limits for Classical Sequential Growth
  Models* (2010), <https://doi.org/10.1002/rsa.20278>.

The archived reports distinguish literature theorems, lab derivations and
numerical tests. The atlas should preserve those distinctions; statistical
compatibility never becomes a physical discovery by presentation.
