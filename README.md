# Causal Spacetime Lab

A small, reproducible Python research sandbox for exploring how **geometric quantities can be inferred from causal order** in toy models. This is an educational computational lab and **not evidence** that spacetime is discrete, that General Relativity is incorrect, or that black-hole singularities have been resolved.

## Interactive Research Atlas

Explore the first five experiments through an interactive React/TypeScript atlas:
causal diamonds, dimension guessing, adversarial orders, local structure,
background-free growth, a scientific evidence map and the archived data explorer.
All research implementations and historical archives remain unchanged.

- [Atlas application, run instructions and deployment](apps/research-atlas/README.md)
- [Scientific provenance and interpretation audit](apps/research-atlas/SCIENTIFIC_AUDIT.md)
- [Interactive atlas (GitHub Pages target; available after the atlas PR is merged and deployed)](https://raghammer1.github.io/causal-spacetime-lab/)

```bash
cd apps/research-atlas
npm ci
npm run dev
```

Browser demonstrations are illustrative; recorded results retain their source
links and uncertainty definitions. The tested classical growth route failed its
Minkowski target. The broader emergent-spacetime hypothesis remains open.

## First experiment: recover proper time from causal relationships

1. Create a 1+1D flat Minkowski causal diamond with known elapsed time `T`.
2. Poisson-sprinkle a finite number of events, preserving Lorentz-invariant sampling at fixed density.
3. Record which events causally precede which others.
4. Throw away coordinates for the **order-only** algorithm and compute the longest causal chain.
5. Compare the inferred elapsed time with known `T`, repeat at increasing densities, and record finite-density bias.
6. Compare against **negative controls** (total order, antichain), which should not produce the same geometric signatures.

**Crucial distinction:** The generator uses a known spacetime background. Successful reconstruction from that sample does **not** demonstrate spontaneous emergence of space or time from background-free dynamics.

## Setup

Python 3.10+ is required:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
python -m causal_lab.cli --repeats 100 --seed 20261025 --out results
jupyter lab
```

Open `notebooks/00_causal_reconstruction.ipynb` for the original interactive demonstration. CSV and PNG outputs from the CLI are written to `results/` (gitignored so changing seeds does not create noisy commits).

The [baseline audit](docs/BASELINE_AUDIT.md) records reproduced results, corrected
edge cases and performance. The [mathematical derivation](docs/THEORY.md) explains
the density normalization and finite-size limitations. Small reviewed scientific
artifacts are versioned under `docs/`; local runtime output remains ignored.

## Finite-density study

Experiment 1 is merged into `main`. Run its preregistered study with:

```bash
python -m causal_lab.scaling --seed 20261025 --repeats 200 --bootstrap 2000 --out results/finite-density-scaling-v1
```

The defaults sweep seven logarithmically spaced densities from 32 to 8192 at
durations 0.5, 1 and 2: 4,200 primary sprinklings. Outputs include raw trials,
summary CSV/JSON, pointwise 95% bootstrap intervals, negative controls,
small-case algorithm checks, separate performance measurements and four plots.
The [protocol](docs/FINITE_DENSITY_PROTOCOL.md) states adverse and inconclusive
outcomes in advance. The [results report](docs/FINITE_DENSITY_RESULTS.md) links
the reviewed tables and plots and explains the finite-density limitations.

For a quick smoke run:

```bash
python -m causal_lab.scaling --densities 8 32 --durations 0.5 1 --repeats 8 --bootstrap 100 --order-repeats 2 --benchmark-repeats 1 --out results/scaling-smoke
```

Physical samples use independent streams keyed by parameters and repetition;
changing grid traversal or bootstrap count does not change them. Reproduction
metadata records versions, source hashes and a scientific-data digest. Timings
and memory observations vary across runs and machines.

## Experiment 2: reconstruct spacetime dimension

Experiment 2, merged into `main`, adds independent flat-space
generators for spacetime dimensions 2, 3 and 4, and a Myrheim–Meyer estimator
that receives only the causal-order matrix. The [mathematical derivation](docs/DIMENSION_THEORY.md)
verifies the volume measure and ordering-fraction normalization. The
[protocol](docs/DIMENSION_RECONSTRUCTION_PROTOCOL.md) fixes calibration, untouched
holdout controls, uncertainty and failure criteria before primary results.

```bash
python -m causal_lab.dimension_study --seed 20261025 --counts 64 128 256 --repeats 200 --calibration-repeats 100 --bootstrap 2000 --out results/dimension-reconstruction-v1
```

This runs 1,800 primary spacetime samples, 900 separate calibration samples and
3,006 controls. A small smoke run is:

```bash
python -m causal_lab.dimension_study --dimensions 2 3 --counts 16 --repeats 3 --calibration-repeats 10 --bootstrap 100 --benchmark-repeats 1 --out results/dimension-smoke
```

The [results report](docs/DIMENSION_RECONSTRUCTION_RESULTS.md) links raw data,
summaries, six figures, runtime measurements and limitations. Artificial orders
are tested against both the single fraction and an exploratory combination of
chain and interval observables. No finite collection of these statistics proves
that a causal order is manifold-like. No black-hole model is included.

## Experiment 3: adversarial geometry and identifiability

The [registered protocol](docs/ADVERSARIAL_GEOMETRY_PROTOCOL.md) compares six
detectors: ordering fraction, height, their combination, the original five-feature
RMS score, a maximum-residual score, and interval abundance. Three independent
calibration fits have disjoint training, development, validation and final-test
streams. Controls include protected-height adversarial searches, an unseen
interval-order family, and a rank-based sampler with exactly the d=2 geometric
order law. The [theory](docs/ADVERSARIAL_GEOMETRY_THEORY.md) explains why the last
family is a positive control and gives exact information-loss counterexamples.

```bash
python -m causal_lab.adversarial_study --seed 20261025 --dimensions 2 3 4 --counts 64 128 256 --fits 3 --calibration 100 --development 100 --validation 200 --repeats 200 --search-steps 64 --bootstrap 2000 --workers 3 --out results/adversarial-geometry-v1
```

The full workload records 52,218 orders, including both checkpoints of 5,400
bounded searches. It takes substantially longer than the earlier experiments.
`--workers 1` runs serially without changing scientific streams or the digest.
For a small reproducible smoke run:

```bash
python -m causal_lab.adversarial_study --dimensions 2 3 --counts 12 --fits 2 --calibration 10 --development 10 --validation 12 --repeats 2 --search-steps 4 --bootstrap 32 --seed 101 --out results/adversarial-smoke
```

The [results report](docs/ADVERSARIAL_GEOMETRY_RESULTS.md) links compressed raw
features, complete interval histograms, every search including failed matches,
fitted models, per-fit Wilson intervals, hierarchical paired comparisons and six
figures. Nominal validation acceptance targets are shared across detectors;
discrete score ties and holdout variability can produce different achieved rates.
Three fits provide a limited assessment of calibration uncertainty. Acceptance
compares selected summaries with a specified sampling model; it is not a physical
spacetime certificate.

Verify the curated full archive with `python scripts/audit_adversarial.py`.
`python scripts/analyze_adversarial_searches.py docs/experiments/adversarial-geometry-v1`
also reconstructs nine seeded search cases. These audits deliberately require the
registered full grid; they write their reports to ignored `results/` files.

## Experiment 4: local causal structure and geometric identifiability

Local structure contains information that the earlier global summaries lose.
Exact counterexamples establish this without training another classifier.
For uniform sampling in a causally convex flat region, conditioning on an open
interval's event count gives an internal order law independent of the outer
boundary. We derive this law and test diamonds, central time slabs and spatial
boxes in dimensions 2, 3 and 4.

All 42 registered N=256 diamond/slab comparisons meet their finite equivalence
margins. In d4 slabs, the global dimension estimate is 4.581 while the local
estimate is 3.995 [3.948,4.040]. This is reconstruction under stated sampling
assumptions, not a certificate of geometric embeddability. Rank-two/diamond law
equivalence remains exact; boxes retain clipping bias; the unseen rank-three
construction is still close enough to d3 to leave several comparisons inconclusive.

The study records 31,392 parent/checkpoint orders, 3,600 exact matched pairs and
864 exact-statistic searches with budgets increasing as N². It preserves every
failed search, exact degeneracy, missing interval and uncertainty estimate.
The [results and complete derivations](docs/LOCAL_CAUSAL_STRUCTURE_RESULTS.md)
include eight figures, independent audits, full replay evidence and limitations.
The [protocol](docs/LOCAL_CAUSAL_STRUCTURE_PROTOCOL.md) and
[workload selection](docs/LOCAL_CAUSAL_STRUCTURE_WORKLOAD.md) preceded primary data.

```bash
python -m causal_lab.local_structure_study --workers 3 --output results/local-causal-structure-v1
python scripts/audit_local_structure.py results/local-causal-structure-v1
python scripts/replay_local_structure.py results/local-causal-structure-v1 --output results/local-replay.json
```

The full computation takes about 12 minutes on the recorded machine, plus output
creation. A small CLI run is also included in CI:

```bash
python -m causal_lab.local_structure_study --smoke --workers 1 --output results/local-structure-smoke
```

The [continuum requirements](docs/LOCAL_CAUSAL_STRUCTURE_CONTINUUM.md) separate
full causal-order reconstruction, volume/density assumptions, convergence and
dynamics. Further classifier optimization is not the next research objective.

## Experiment 5: background-free causal growth

Intrinsic transitive percolation generates consistent causal histories without
coordinates or target geometry, but all six registered fixed-p settings fail the
finite Minkowski signature. Both the d2 reference and an explicit height-two
control pass that signature, demonstrating its insufficiency. Ordinary classical
sequential growth also has a known almost-semiorder obstruction to the specified
Minkowski sampling limit; finite feature matches cannot overcome it.

The [results](docs/BACKGROUND_FREE_GROWTH_RESULTS.md) retain 1,056 independent
stochastic histories, 17,986 dependent records, nine figures, exact derivations,
all failed and inconclusive comparisons, and adverse reference-control results.
The full repeat reproduced all 31 data/table/figure artifacts byte for byte.
Independent counting and 4,877 statistical checks found no discrepancies.
The [protocol](docs/BACKGROUND_FREE_GROWTH_PROTOCOL.md),
[foundations](docs/BACKGROUND_FREE_GROWTH_THEORY.md) and
[workload amendment](docs/BACKGROUND_FREE_GROWTH_WORKLOAD.md) preceded primary data.

```bash
python -m causal_lab.growth_study --histories 32 --workers 3 --output results/growth-primary
python -m causal_lab.growth_audit docs/experiments/background-free-growth-v1 --output results/growth-audit.json
python scripts/review_growth_statistics.py docs/experiments/background-free-growth-v1
python -m causal_lab.growth_study --smoke --workers 1 --output results/growth-smoke
```

The full run takes about eleven minutes on the recorded machine. The decision is
to stop tuning this baseline. Further intrinsic dynamics needs an explicit changed
assumption, a justified convergence question, and fresh consistency/covariance
analysis. No physical spacetime or gravitational dynamics is established.

## Interpretation boundaries

- The longest-chain estimate is asymptotic in 1+1 dimensions. It has bias at finite event density.
- `longest_chain_order` uses only a Boolean partial order; `longest_chain_fast` uses *known* generating coordinates for efficiency. Do not conflate them.
- Pair comparability supports a dimension estimate under stated flat-interval
  assumptions; an arbitrary order can imitate it. It does not prove geometry.
- A discrete causal graph is not automatically physical spacetime; additional tests include locality, effective dimension, dynamics, Lorentz invariance, stability and ultimately agreement with GR.
- Simulating horizon-like behaviour is not experimental observation of a black hole.

## Research workflow

See [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) for next experiments, [docs/RESEARCH_LOG.md](docs/RESEARCH_LOG.md) for falsifiable hypotheses and [CODEX_PROMPT.md](CODEX_PROMPT.md) for agent instructions.

## Further reading

- [Causal set theory overview (arXiv)](https://arxiv.org/abs/gr-qc/0309009)
- [R. Sorkin's causal set bibliography](https://www.perimeterinstitute.ca/people/rafael-sorkin)
- [T. Jacobson, Thermodynamics of Spacetime (1995)](https://doi.org/10.1103/PhysRevLett.75.1260)
- [Gravitational Wave Open Science Center](https://gwosc.org/)

## Publishing

The intended repository is **`raghammer1/causal-spacetime-lab`**, public, with no private keys, tokens or personal information. See `CODEX_PROMPT.md` for the publication workflow. `scripts/publish.sh` is a guarded helper only for a directory with no commits and no existing remote repository. Once the baseline exists, push an experiment branch and open a pull request; do not run that initial-publication helper or merge automatically.

Licensed under the MIT License.
