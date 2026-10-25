# Codex task — Causal Spacetime Lab: reproduce, test, extend, publish

You are my research engineer and rigorous scientific collaborator. Work in this repository as a reproducible computational physics experiment, not a scientific marketing project.

**Project:** Causal Spacetime Lab
**Target GitHub repository:** `raghammer1/causal-spacetime-lab` (PUBLIC)
**Scientific question:** Can geometric observables such as elapsed proper time be reconstructed from discrete causal order? Can we distinguish continuum-like causal orders from arbitrary directed acyclic structures? Ultimately, could a geometric description emerge from a genuinely background-free rule?

The seed project already includes Python package code, a notebook, experiments, tests, CI, and research documentation. Inspect them before making changes. Do NOT replace working code just to restructure it.

## Phase 1 — Audit and reproduce
1. Check repository status, Python version, package configuration, and notebook claims. Do not touch unrelated repositories.
2. Set up dependencies in a local virtual environment (`python -m pip install -e '.[dev]'`). Run tests (`python -m pytest -q`). Run `python -m causal_lab.cli --seed 20261025 --repeats 100 --out results` and verify that CSV and PNG files were created.
3. Investigate numerical assumptions and references: 1+1D Minkowski Poisson sprinkling, correct density-to-event-count relation, longest causal chain, proper-time asymptotics, finite-density bias, and origin of the `sqrt(2*rho)` estimator. Check the normalization carefully before expanding.
4. Create a baseline audit with successes, failures, mathematical assumptions, limitations and performance. Make small fixes only when supported by tests.

## Phase 2 — Run one serious new experiment
Create an experiment branch named `experiment/finite-density-scaling-v1` from the clean baseline. Do not rewrite or force-push `main`.

Build a first reproducible study of finite-density reconstruction:
- Sweep at least 6 logarithmically spaced densities and multiple physical durations with at least 100 fixed-seed repetitions for affordable settings; increase sampling if practical.
- Report mean, standard deviation, standard error, bootstrap confidence intervals (if supported), normalized bias and wall-clock/peak-memory benchmarks.
- Include order-only vs embedding-based algorithms on small cases and check their agreement. Do not claim coordinate independence for the fast algorithm.
- Include negative controls (total order and antichain); compare with expected chain scaling.
- Add plots with labelled axes and uncertainty, tables in CSV/JSON, documentation with a mathematical derivation and clear interpretation.
- Write tests and failure cases; run the full suite, then document limitations. Keep runtime manageable on a laptop.

## Phase 3 — Roadmap, NOT premature claims
Plan—but do not automatically implement an entire speculative theory—the next milestones:
A. Dimension-sensitive order statistics and a properly derived causal-set dimension estimator with verified references.
B. Background-free sequential growth rules; check whether apparent spacetime-like properties emerge without embedding positions or predetermined metric.
C. Later, toy curved spacetime / horizon analogues with explicit warnings that a causal horizon is NOT a black-hole solution.
D. Only much later, a demonstrably consistent route to Einstein's dynamics, gravitational time dilation, black-hole limits, and observational constraints.

Explain which observed output would REFUTE a hypothesis, not only what would confirm it. Separate mathematical possibility from a hypothesis about our universe.

## Phase 4 — Publish to GitHub
- If `raghammer1/causal-spacetime-lab` already exists and is the intended repository, inspect its branches/remote before pushing; never overwrite unrelated history.
- If it does not exist, use authenticated GitHub CLI on my machine to create it as PUBLIC. Do not expose or log tokens. If `gh` is missing, install with Homebrew if allowed. If unauthenticated, request my interactive `gh auth login` and stop publication until authenticated. Do not invent success.
- Before first push, inspect `git status`, `.gitignore` and tracked files for secrets, private data, huge outputs or machine-specific paths. Initial baseline commit on `main`; create remote and push with the documented CLI equivalent of:
  `gh repo create raghammer1/causal-spacetime-lab --public --source=. --remote=origin --push`
  (only after a local git init/commit and verification, and only if this repository does not already exist).
- For the NEW experiment, push the `experiment/finite-density-scaling-v1` branch and open a GitHub pull request into `main`; DO NOT auto-merge.
- Add a useful README with exact install/run steps and a prominent disclaimer that simulations do not prove new physics. Include LICENSE, tests and GitHub Actions workflow.
- Verify the repo URL, default-branch files, experiment PR URL and CI result. If unable, provide exact blocker and commands needed from me.

## Handover
Return: links to the PUBLIC GitHub repository and PR (only if actually created), commands to reproduce, how many tests pass, experiment tables/plots, major scientific assumptions, falsification attempts, and the next 3 research questions. No fabricated findings, simulated tool results, or unsupported claims of scientific novelty.
