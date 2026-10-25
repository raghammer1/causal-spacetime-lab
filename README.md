# Causal Spacetime Lab

A small, reproducible Python research sandbox for exploring how **geometric quantities can be inferred from causal order** in toy models. This is an educational computational lab and **not evidence** that spacetime is discrete, that General Relativity is incorrect, or that black-hole singularities have been resolved.

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

On `experiment/finite-density-scaling-v1`, run the preregistered study:

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

## Interpretation boundaries

- The longest-chain estimate is asymptotic in 1+1 dimensions. It has bias at finite event density.
- `longest_chain_order` uses only a Boolean partial order; `longest_chain_fast` uses *known* generating coordinates for efficiency. Do not conflate them.
- Pair comparability is a coarse sanity-check statistic, not proof of dimension or geometry.
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
