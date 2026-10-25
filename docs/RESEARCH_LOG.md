# Research log

## 2026-10-25 — Initial baseline

**Question:** In a causal order sampled from a known 1+1D flat spacetime, can longest-chain length approximately recover elapsed proper time?

**Status:** Numerical demonstration of a known causal-set property; test and reproduce before interpretation.

**Key assumptions:** Minkowski geometry is used by the event generator; unit light speed c=1; independent Poisson sprinkling at uniform spacetime density; timelike boundary endpoints are not counted in the interior chain; large-density estimator is asymptotic.

**Prediction:** For fixed proper time, increased sprinkling density should improve the relative accuracy of `longest chain / sqrt(2*density)` in aggregate. At finite density there is stochastic scatter and systematic bias.

**Controls:** Compare order-only dynamic programming with fast embedding-based LIS; compare non-spacetime-like total orders and antichains.

**Potential falsification:** Wrong chain computation, inconsistent density scaling, convergence that fails over large parameter sweeps, or non-causal chains.

**What this does NOT demonstrate:** Microscopic discreteness of the physical universe, dynamical emergence of a metric, a quantum theory of gravity, or a resolution of black-hole singularities.

**Next:** Re-run benchmarks with recorded seeds, vary event density and endpoint proper time, investigate finite-size systematic error.
