# Research roadmap

## Baseline (implemented)
- [x] Poisson sprinkling in a known 1+1D Minkowski causal diamond
- [x] Derive the causal order; reconstruct longest chain from order alone
- [x] Cross-check against efficient coordinate-aware longest-chain algorithm
- [x] Repeated trials, seed control, CSV and PNG with estimate bias and spread
- [x] Total order and antichain negative controls, basic tests and CI

## E1: Finite-density scaling (next)
**Question:** Does the chain-based elapsed-time estimator approach the true value as density grows?
**Null/comparison:** Finite-density error shrinks with increasing density within practical bounds.
**Protocol:** Keep proper time constant; sweep densities and seeds; report mean bias, variance, confidence intervals, number of events, execution cost. Fit cautiously; don't assert the precise convergence exponent without evidence.
**Failure mode:** Algorithmic bias, wrong normalisation, unjustified extrapolation.

## E2: Dimension-sensitive order statistics
**Question:** Do different classes of orders display different causal signatures?
**Protocol:** Evaluate order fraction on 1+1D sprinkled causal sets and total-order / antichain controls. Then research and correctly derive/implement a dimension estimator (e.g. Myrheim–Meyer) with literature-cited formulas, clear prerequisites, numerical validation and uncertainty. Don't call a naive heuristic a verified estimator.
**Failure mode:** Distinct structures can share one statistic.

## E3: Dynamics without a presupposed geometry
**Question:** Can a generative rule over events produce a nontrivial order resembling a continuum spacetime?
**Protocol:** Write down candidate background-free growth rules before simulation; verify partial-order axioms; measure longest chains, antichains, ordering fraction and stability across seeds/sizes. Compare against flat-space sprinkled orders and trivial orders. Record failures as valuable results.
**Failure mode:** The process has only recreated a geometry encoded implicitly in its initial rule or sampling.

## E4: Curvature and horizons (later, only after baseline validation)
Use a specified curved metric to generate an effective causal structure; distinguish embedding/background assumptions from emergent outcomes. A toy causal horizon is not a black-hole solution. Recovery of Einstein's equations and exterior black-hole phenomenology remains an open requirement.

## Research rigor
Each experiment must record: **question, fixed assumptions, measurement, controls, predicted outcome, falsification criteria, seed and parameter sweep, numerical results, uncertainties, and limitations**. No claim that a toy simulation resolves black-hole singularities or dark energy.
