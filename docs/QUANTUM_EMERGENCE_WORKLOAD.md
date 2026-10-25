# Experiment 6 workload freeze and pre-primary audit

No primary states or outcomes have been generated at this freeze. Protocol commit
`ee9ece735642d9a818053f11e290a8450f403d90` preceded implementation. The theory document
was developed before implementation and completed during it; it is committed with
implementation rather than in the protocol commit. This corrects the protocol's
intended chronology without changing a scientific criterion. Its mathematical
arguments were available before any primary outcomes.

## Timing-only decision

The registered rule selects **R=8 per batch**, hence **24 independent realizations**
per size and stochastic family, with three seed batches, n=6,8,10, and h=.5,1,2.
No sizes, models, controls or perturbations were dropped. There are **1,818 planned
state records**: 18 deterministic Model-A/control records; 207R=1,656 independent-
realization branches/controls (correlated branches are not independent samples);
and 144 controlled-evolution records. Exactly 873 ground-state solves are planned.
The three all-plus evolutions of Model A at a given n,t are identical, so only one
is retained; random-product preparations remain independently sampled.

The first pilot timed state calculations only and selected R=8. Independent review
required a fuller pilot including archive/statistics/rendering overhead. The second
pilot executed one complete 47-state bundle at each size, then conservatively
replicated *pilot* values into 24 synthetic units in every cell for a worst-grid
postprocessing test. Those synthetic values are timing data, never scientific
samples, and their statistics/plots were neither inspected nor published.

| n | Full representative state-bundle seconds | Numerical failures |
|---|---:|---:|
| 6 | 1.11955 | 0 |
| 8 | 1.24822 | 0 |
| 10 | 1.92811 | 0 |

Worst-grid postprocessing took 73.1891 seconds, including serialization, uncertainty
calculations and rendering. The factor-two conservative full-runtime predictions
were 197.929, 249.479 and **352.580 seconds** for R=2,4,8 respectively. Peak pilot RSS
was 432,455,680 bytes (about 412 MiB), including the synthetic expanded grid. R=8
therefore fits the 20-minute planning budget and 2 GiB cap. BLAS/OpenMP threads are
one. The 45-minute cap is checked between bundles; the largest single operation is
bounded at 1,024 amplitudes. Postprocessing duration and RSS are separately recorded;
any resource overrun disqualifies an unqualified completed-study claim.

The pilot metadata records the then-current file hashes, which precede final
failure-handling/reporting fixes. These fixes do not change the scientific schedule
or select outcomes. The generating primary commit will be recorded automatically
with its full source hashes, versions and clean-tree status. SciPy is the only new
dependency, justified by sparse Hermitian eigensolvers and exponential action.

## Calibration failure retained

An independent stream tested the registered nominal percentile bootstrap intervals
on 400 normal-mean trials with 24 independent units in three equal strata. Coverage
was **0.9125**, Monte Carlo standard error **0.01413**, below the nominal 0.95.
This is an uncertainty-calibration failure, not a reason to change seeds, margins
or the interval algorithm after observing outcomes. Bootstrap intervals and the
planned lower-bound screens will therefore be described as **descriptive**; they
cannot alone support a formally calibrated significance claim or limited GO.
The small Monte Carlo audit does not establish coverage for the quantum observables.

The separately derived one-sided exact Clopper–Pearson bounds have their specified
coverage: exhaustive binomial checks at n=6,12,24 and p=.05,.2,.5,.8,.95 were all
at least 1-.05/3. The hidden-chain gate retains this check, and is only eligible
with all planned samples. An all-success cohort does not imply probability one.
Proximity lower bounds use the lower endpoint of the nominal two-sided 95% interval;
the six stress contrasts use the registered one-sided alpha=.05/6 bounds. No
statistical threshold was changed. Any stratum with a single usable observation
makes the bootstrap interval unavailable. The three-preparation secondary quench
cells have means, standard deviations and batch values, without invented intervals.

## Numerical and accounting clarifications

- Undefined constant rank correlations remain null in JSON, with usable/undefined
  counts in summaries; they are not zero correlations and are not dropped silently.
- If both cut entropy and the pair prediction are <=1e-10, the normalized cut defect
  is zero with an explicit numerical-zero flag. Raw values remain archived. This
  applies the registered roundoff tolerance rather than amplifying ~1e-15 error by
  the 1e-12 denominator into a false ~1e-3 product-state defect.
- All planned observations retain a row if failed, blocked by a failed baseline,
  or unattempted at a resource cap. No replacement seeds. Model-A ground states and
  evolution failures use the same policy. Incomplete cohorts cannot pass gates.
- Phase-scrambled baselines identify their source state. Shared phase vectors and
  identical edge-weight permutations are used for paired controls. Model-A cuts
  are shared from its single deterministic baseline; its marginal spectra depend
  only on cut size. Independent perturbations explicitly supply asymmetry.
- Truncated repeated MDS eigenspaces have noncanonical axes and potentially
  noncanonical projection stress. Ambiguity flags are retained. GHZ/symmetric
  examples and Bell coordinate collisions cannot support a geometric claim.
- The full positive spectrum is returned by inference; fixed 1D/2D/3D projections
  are evaluator reports. Only the evaluator sees J or chain truth.

## Reproduction commands

```sh
python -m pip install -e '.[dev]'
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
python -m pytest -q
python -m causal_lab.quantum_study --smoke --output results/quantum-smoke
python -m causal_lab.quantum_study --calibrate --output results/quantum-calibration
python -m causal_lab.quantum_study --pilot --output results/quantum-pilot
# From the clean, committed implementation/workload source:
python -m causal_lab.quantum_study --primary --repeats 8 --output results/quantum-primary
```

Each output directory must be empty. Pilot/smoke/calibration streams cannot coincide
with the primary streams. The full primary run is excluded from CI. After execution,
independent raw-state, statistical and artifact audits plus a full repeat from the
frozen commit will precede publication.
