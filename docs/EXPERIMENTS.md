# Research roadmap and stopping criteria

This project is a numerical lab. Mathematical reconstruction in an assumed
geometry, emergence in an abstract model, and measured evidence about our
universe are different claims. No experiment below licenses skipping the next
validation step. Derivations and original references are in [THEORY.md](THEORY.md).

## Baseline and finite-density reconstruction

The [baseline audit](BASELINE_AUDIT.md) reproduces the original demonstration and
records tested corrections. The first extension follows the
[finite-density protocol](FINITE_DENSITY_PROTOCOL.md): multiple densities and
durations, retained empty draws, independent streams, uncertainty, matched-count
negative controls, small-case algorithm agreement, and explicit cost measurements.
The generator already assumes Minkowski geometry. This is a test of numerical
reconstruction and finite-size effects, not a background-free model.

An algorithm disagreement, noncausal returned chain, wrong event-count
normalization, or reversed high/low-density bias trend is a concrete adverse
result. Inconclusive intervals remain inconclusive. We do not fit a universal
exponent or invent a finite-density correction from this first sweep.

## A. Dimension-sensitive order statistics — next, not implemented

**Question:** Can several order observables discriminate known continuum
dimensions from adversarial non-manifoldlike orders?

Derive and test the Myrheim–Meyer relation with an explicit convention:
`r = R / binom(N,2)` has expectation
`Gamma(d+1)*Gamma(d/2)/(2*Gamma(3*d/2))` in a flat Alexandrov interval.
For `R/N²`, the corresponding large-N expression is half this value. The
derivation and source equations are recorded in [THEORY.md](THEORY.md).
First validate independent generators in dimensions 2, 3 and 4; numerical
inversion requires careful handling of finite samples and endpoint statistics.
Do not substitute a heuristic based on one pair fraction.

**Controls:** total orders, antichains, layered orders, and non-manifoldlike
orders chosen to match a pair fraction. Measure interval abundances, chain length,
width and size dependence alongside inferred dimension. Use ensembles rather
than pretending correlated pairs are independent Bernoulli observations.

**Refutation:** failure to recover known dimension within calibrated uncertainty,
strong size drift, or inability to distinguish matched-statistic controls rejects
the estimator or the claim that these observables suffice. A plausible numerical
dimension alone does not establish continuum geometry.

## B. Background-free growth — planned after observables are validated

**Question:** Can an explicitly specified rule on abstract orders produce stable
continuum-like statistics without supplied positions or metric?

Start with the transition rules in
[Rideout and Sorkin (2000)](https://arxiv.org/abs/gr-qc/9904062), including
transitive percolation as a control. Specify allowed transitions, probabilities,
transitive closure and relabeling invariance before running anything. Retain
failed parameter regions. Compare ensembles across event counts with prescribed
Minkowski sprinklings and trivial or layered orders. Predeclare which joint
statistics must persist as size increases; do not tune to one favorable plot.

**Refutation:** signatures disappear with increasing size, depend on birth labels,
require hidden coordinates, or cannot distinguish matched controls. Even success
would demonstrate properties of a mathematical model, not its relevance to our
universe, Lorentzian dynamics or quantum gravity.

## C. Curved backgrounds and causal horizons — later

Use a specified metric and its invariant volume element. Compare recovered
proper time with an independent continuum calculation along known geodesics.
Separate density gradients, boundary effects and curvature. Flat-space recovery
must be regained in the appropriate limit. Observer-dependent causal horizons
can occur in flat spacetime: a causal horizon is **not a black-hole solution**.

**Refutation:** inconsistency with continuum benchmarks, failure of the flat limit,
or sensitivity to coordinate choices beyond numerical error. No claim of
singularity resolution follows from a finite graph or a missing divergent value.

## D. Gravitational dynamics and observation — much later

Only a demonstrably consistent dynamics and continuum limit could motivate tests
of Einstein's equations, gravitational time dilation, exterior black-hole limits,
conservation laws and stability. A proposed physical theory must supply predictions
with units, a parameter-identification procedure and observational constraints.

**Refutation:** inconsistent dynamics, failure of an established gravitational
limit, or disagreement with a specified observation outside quantified theoretical
and measurement errors. No such theory or observational fit is implemented here.

## Required record for each future study

Before execution: question, assumptions, independent controls, expected outcomes,
adverse and inconclusive outcomes, parameter grid, seeds and resource limits.
After execution: raw data, uncertainty, failed trials, source/version provenance,
costs and a scope-limited interpretation. Use experiment branches and reviewed
pull requests; keep `main` a verified baseline.
