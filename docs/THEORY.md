# Theory, normalization, and interpretation

This is an educational numerical validation of known mathematics. The generator
starts from a specified Minkowski metric. Recovering a quantity from the resulting
order does not show that a geometry emerges dynamically or that physical spacetime
is discrete. No gravitational field equation is simulated here.

## Proper-time reconstruction in 1+1 dimensions

Use units with light speed `c = 1`, metric `ds² = dt² − dx²`, and endpoints
`A = (0, 0)`, `B = (T, 0)`. Their continuum proper-time separation is `T`.
Introduce null coordinates

\[
u=t+x,\qquad v=t-x,\qquad t=(u+v)/2,\qquad x=(u-v)/2.
\]

The open Alexandrov interval is the square `0 < u,v < T`. The Jacobian is

\[
\left|\det\frac{\partial(t,x)}{\partial(u,v)}\right|=\frac12,
\qquad V=\int_0^T\int_0^T\frac12\,du\,dv=\frac{T^2}{2}.
\]

Thus density `ρ` means events per unit **physical spacetime volume**, not events
per unit area in the null-coordinate square. Poisson sprinkling requires

\[
N\sim\operatorname{Poisson}(\lambda),\quad
\lambda=\rho V=\frac{\rho T^2}{2},\quad
\mathbb E[N]=\operatorname{Var}(N)=\lambda.
\]

Conditional on `N`, draw all `u` and `v` independently and uniformly on `(0,T)`.
This produces a homogeneous Poisson process in the diamond. Its probability law
uses the invariant volume measure; an individual finite realization is not itself
invariant under every Lorentz transformation. The diamond's endpoints are part of
the experimental setup. The original causal-set construction is
[Bombelli, Lee, Meyer and Sorkin, *Space-time as a causal set*, PRL 59, 521 (1987)](https://doi.org/10.1103/PhysRevLett.59.521).
The Poisson law is also given explicitly in Eqs. (1)–(2) of
[Roy, Sinha and Surya, *The Discrete Geometry of a Small Causal Diamond*, PRD 87, 044046 (2013)](https://arxiv.org/abs/1212.0631).

For two sampled points, strict increase of both null coordinates is equivalent to
future timelike separation. We use this strict relation throughout. Exact null
separations or duplicate points have probability zero in the ideal continuous
sampling model. Deterministic tied-coordinate inputs still need explicit tests;
the code must not accidentally put tied `u` coordinates into a strict chain.

Sort the events by increasing `u`. Independence and continuity imply that the
ranks of their `v` coordinates are a uniformly random permutation of `N` labels.
A chain in the order is therefore an increasing subsequence of those ranks, and
the longest chain has the same length `L` as the longest increasing subsequence.
The asymptotic law is `L/(2√N) → 1`; its Poissonized counterpart uses `λ` in place
of `N`. Consequently,

\[
L\sim 2\sqrt{\lambda}=\sqrt{2\rho}\,T,
\qquad \widehat T=\frac{L}{\sqrt{2\rho}}.
\]

This derivation checks the factor of two. Replacing the Poisson mean by `ρT²`
while leaving the estimator unchanged would introduce a factor `√2` error.
`L` counts **interior sampled events only**. Neither deterministic endpoint is
counted, and there is no added endpoint correction. An empty interval has `L=0`.
The finite-sample estimator is not an exact identity.

Absolute time requires the density scale `ρ` in addition to the order. An
unscaled abstract order cannot determine a duration in seconds. `longest_chain_order`
uses only the supplied precedence matrix; `longest_chain_fast` uses the known
`u,v` embedding to compute the same observable more cheaply. The latter is not a
coordinate-independent reconstruction algorithm. See also
[Brightwell and Gregory, *Structure of random discrete spacetime*, PRL 66, 260 (1991)](https://doi.org/10.1103/PhysRevLett.66.260).

## Finite-density behavior: theorem versus a finite study

[Baik, Deift and Johansson, *On the Distribution of the Length of the Longest Increasing Subsequence of Random Permutations*, JAMS 12, 1119–1178 (1999)](https://arxiv.org/abs/math/9810105)
prove convergence in distribution and moments of `(L−2√N)/N^(1/6)` to the GUE
Tracy–Widom law (Theorems 1.1–1.2). The discussion after Eq. (1.11) states the
Poissonized result. Their numerical evaluation gives limiting mean approximately
`m = −1.7711` and variance approximately `0.8132`. These are literature constants,
not estimates measured by this repository.

Applying those results to the present normalization gives

\[
\mathbb E[L]=2\sqrt{\lambda}+m\lambda^{1/6}+o(\lambda^{1/6}),
\]
\[
\underbrace{\frac{\mathbb E[\widehat T]-T}{T}}_{\text{normalized bias}}
=\frac{m}{2}\lambda^{-1/3}+o(\lambda^{-1/3}).
\]

The corresponding standard deviation of `T_hat/T` is asymptotically
`√0.8132 / (2 λ^(1/3))`. Negative leading bias is therefore expected at large
`λ`. The leading curve is a reference guide, not a calibrated correction at small
`λ`, and not a promise of pointwise monotonic sample means. No convergence exponent
will be inferred merely by drawing a line through this finite sweep. Confidence
intervals for a Monte Carlo mean quantify sampling error, not finite-density bias,
model error, or the probability that an asymptotic theorem is true.

Rescaling `u,v` by `T` also shows directly that the distribution of
`T_hat/T = L/(2√λ)` depends only on `λ`. At equal expected counts, results at
different physical durations should therefore agree in distribution. This is an
independent dimensional check, not a claim of new scale invariance in nature.

## Negative controls and independent checks

For a fixed event count `N`, a total order has `L=N`; an antichain has `L=1` for
`N>0` and `L=0` for `N=0`. Their unordered comparable-pair fractions are `1` and
`0` when `N≥2`; the fraction is undefined for `N<2`.

For matched Poisson counts with mean `λ`, elementary expectation gives

\[
\mathbb E[L_{\rm total}]=\lambda,\qquad
\mathbb E[L_{\rm anti}]=1-e^{-\lambda}.
\]

If the Minkowski estimator is deliberately applied to these controls, its mean
ratio to `T` is `√λ/2` for a total order and
`(1−e^(−λ))/(2√λ)` for an antichain. These are diagnostic mismatches: no physical
duration is assigned to either arbitrary order by this exercise. Matching one
chain statistic at one count cannot establish manifoldlikeness.

At small sizes, a separately constructed precedence matrix and order-only dynamic
programming provide an algorithmic cross-check. Relabeling events must preserve
chain length. A finite DAG's adjacency matrix need not be a transitive order:
missing transitive relations must not silently be treated as a valid order input.
Poisson count moments and the exact two-dimensional comparable-pair expectation
`1/2` supply checks independent of chain-length normalization. The latter follows
because two independent points have concordant `u,v` rankings with probability
`1/2`; pairs sharing an event are correlated, so a binomial error bar for all pairs
would be unjustified.

## Planned dimension work: conventions first

Dimension estimation is a **future milestone**, not an implemented outcome of
this study. Let `R` count ordered relations `i≺j`, once per comparable unordered
pair. The repository's statistic is

\[
r=\frac{R}{\binom N2}=\frac{2R}{N(N-1)},\quad N\ge2.
\]

For independent uniform events in a flat `d`-dimensional Alexandrov interval, the
continuum pair probability is

\[
p_d=\frac{2}{V^2}\int_I d^d x\,\operatorname{Vol}(I(x,q))
=\frac{\Gamma(d+1)\Gamma(d/2)}{2\Gamma(3d/2)}.
\]

For example, `p_1=1`, `p_2=1/2`, `p_3=8/35`, and `p_4=1/10`.
Conditional on a fixed `N≥2`, linearity of expectation gives `E[r|N]=p_d`.
For a Poisson process, `E[R]=λ²p_d/2`. Therefore the literature convention
`E[R]/E[N]²` is `p_d/2`, with **4**, rather than **2**, in the denominator of the
gamma-function expression. It is not the same statistic as `R/binom(N,2)`.
This distinction is explicit in Eqs. (6), (11) and (12) of
[Roy, Sinha and Surya](https://arxiv.org/abs/1212.0631).

The integral can be evaluated by using `q=(T,0)`, radial measure
`Ω_(d−2) r^(d−2) dr dt`, radius bound `r<min(t,T−t)`, and
`Vol(I(x,q))=C_d[(T−t)²−r²]^(d/2)`, where
`C_d=Ω_(d−2)/(2^(d−1)d(d−1))` for `d≥2`. The planned implementation must reproduce
this beta/gamma integral and validate the dimension dependence with separate
sprinklings before numerically inverting `p_d`. Original attribution is to
J. Myrheim, *Statistical Geometry*, CERN-TH-2538 (1978), and
[D. A. Meyer, *The Dimension of Causal Sets*, MIT thesis](https://hdl.handle.net/1721.1/14328).
MIT's catalog dates the thesis to 1989; it is commonly cited as 1988. The verified
formula here is taken from the linked primary research paper, not an uninspected
copy of either historical work.

Prerequisites include a flat Alexandrov sampling region, uniform density, correct
relation counts, adequate event counts, and ensemble uncertainty. Curvature,
inhomogeneous sampling, boundaries, and non-manifoldlike orders can mislead the
inversion. Nonlinear inversion can be biased even when `r` is unbiased. A numerical
value resembling a dimension is insufficient: compare interval abundances,
height, width, and stability under size changes. Total orders and antichains are
useful endpoint controls, not examples of ordinary high-dimensional spacetime.

## Planned background-free dynamics and later gravity

[Rideout and Sorkin, *A Classical Sequential Growth Dynamics for Causal Sets*, PRD 61, 024002 (2000)](https://arxiv.org/abs/gr-qc/9904062)
provide a precise starting point for growth laws on orders. A future experiment
should specify transition probabilities, partial-order closure, label-invariant
observables, and controls before sampling. Transitive percolation is a tractable
baseline in their paper; a random DAG without its transitive closure is not the
same object. The existence of a background-free growth rule does not establish a
continuum limit, quantum dynamics, or Einstein's equations.

A future growth hypothesis fails if its proposed spacetime signatures disappear
with increasing size, depend on arbitrary labels, require hidden coordinates, or
remain indistinguishable from total orders, antichains, or layered-order controls.
Passing several tests would only motivate more discriminating tests.

Later curved-background simulations would still assume their generating metric.
An observer-dependent causal horizon can exist in flat spacetime and is not a
black-hole solution. A physical gravity proposal would need consistent dynamics,
a suitable continuum limit, gravitational time dilation, exterior black-hole
phenomenology, and observational constraints. None of these follows from the
finite-density reconstruction study.
