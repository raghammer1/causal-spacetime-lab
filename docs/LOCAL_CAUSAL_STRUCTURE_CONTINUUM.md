# Experiment 4: what a controlled continuum limit would require

This is an interpretation guide, not an additional experimental result. Exact
finite identities and conditional sampling laws are derived in
[LOCAL_CAUSAL_STRUCTURE_THEORY.md](LOCAL_CAUSAL_STRUCTURE_THEORY.md).

## Established facts and their assumptions

**Continuum causal order can determine conformal geometry.** In the precise
four-dimensional setting of [Malament (1977), Theorem 2](https://doi.org/10.1063/1.523436),
take connected smooth manifolds without boundary, smooth Lorentzian metrics,
time orientations, and both past and future distinguishability. A bijection
preserving chronological precedence in both directions is a homeomorphism and
a smooth conformal isometry. This concerns the full continuum relation, not a
finite list of statistics. The result builds on
[Hawking, King and McCarthy (1976)](https://authors.library.caltech.edu/records/6apqj-ep466).
We do not silently extend its smoothness conclusion to d=2: strictly increasing
null-coordinate homeomorphisms can preserve chronology without being smooth.

**Volume supplies the conformal factor when its measure is known.** If two
smooth metrics are related by g'=Omega²g in dimension d, then their volume forms
satisfy dV'=Omega^d dV. Thus fixing the physical volume measure fixes the positive
conformal factor. This determinant identity is a continuum mathematical fact.
Counts estimate volume only under a sampling assumption: for a Poisson process
of known constant density rho, E[K(U)/rho]=V(U) and
Var[K(U)/rho]=V(U)/rho. Fixed-N uniform samples instead give binomial regional
counts and estimate volume fractions; their absolute scale needs V or rho.
Unknown or varying sampling density can be confused with volume variation.

**Small embeddability is weak evidence.**
[Hiraguti (1955), Theorems 7.4 and 8.3](https://scirep.w3.kanazawa-u.ac.jp/articles/04-01-001.pdf)
prove order dimension at most two through five events, and at most floor(N/2)
for N>=4. Two realizing linear orders supply distinct null-coordinate ranks,
which can be rescaled into a d=2 diamond. Every such small pattern is therefore
embeddable there. This does not identify its sampling probability, density, or
large-order geometry. S3 first supplies a six-event obstruction to that particular
embedding dimension, while the theory document explicitly embeds S3 in d=3.

## Requirements not established by this experiment

**Embedding and approximate uniqueness.** A candidate manifold must reproduce
the full order under an order-preserving-and-reflecting injection. Faithfulness
also requires a specified volume sampling law and separation between sampling
and geometric scales. Agreement of a few distributions proves neither existence
of such an embedding nor uniqueness up to controlled error. Exact summary
collisions and rank-two/diamond law equivalence survive our finite study. The
pigeonhole argument for fixed motifs plus the old histogram does not establish
noninjectivity of the entire growing size/component profile A[m,k].

**A convergence notion and control of limits.** Specify the sequence of order
laws, normalization of counting measure, candidate continuum class, and what
convergence means. Options need different hypotheses: distributions of sampled
suborders, measured causal structures, or reconstructed Lorentzian distances.
[Bombelli (2000)](https://arxiv.org/abs/gr-qc/0002053) constructs statistical
closeness from poset probabilities; [Noldus (2004)](https://arxiv.org/abs/gr-qc/0308074)
develops a Lorentzian distance for compact globally hyperbolic spacetimes.
Neither construction proves convergence of this lab's orders. A chosen framework
would need tightness or compactness, identification of subsequential limits,
control of nonmanifold limits, and uniqueness where reconstruction is claimed.
Matching finitely many moments is insufficient for those steps.

**Mesoscopic scales and bias control.** A prospective local flat approximation
needs a window rho^(-1/d) << ell << L, where L bounds relevant curvature,
curvature-variation and sampling-density-variation scales. Establish sufficient
counts, vanishing fluctuations and controlled bias together, including boundary
clipping, exceptional intervals and selection effects. The exact flat conditional
law assumes uniform density and causal convexity; extending it to curved or
inhomogeneous regions requires a new derivation. Fixed interior sizes 2,4,8 at
finite N do not demonstrate this scale hierarchy or convergence of curvature.
Our pooled-parent consistency tests also do not prove consistent reconstruction
from one increasingly dense order.
[Benincasa and Dowker (2010)](https://arxiv.org/abs/1001.2725) provide a distinct
operator/curvature construction with an explicit nonlocality scale and slowly
varying-field conditions; our motif comparisons do not validate that operator.

**Dynamics, universality and symmetry.** A background-free proposal must specify
a law on orders, label independence, scaling of its parameters and observables,
and whether coarse graining approaches a stable continuum regime. Universality
under controlled microscopic changes and gravitational field equations remain
separate requirements. [Rideout and Sorkin (2000)](https://arxiv.org/abs/gr-qc/9904062)
derive classical sequential-growth laws under stated covariance and causality
conditions; adopting one is not a derivation of general relativity.
[Bombelli, Henson and Sorkin (2009)](https://arxiv.org/abs/gr-qc/0605006) prove a
no-preferred-direction result for an equivariant measurable construction from
Poisson sprinklings in Minkowski space. That theorem does not automatically
cover an arbitrary growth rule or a chosen finite sampling window. A boundary
can select a frame; covariance requires transforming the region as well.

## Interpretation and speculative next work

Useful local identities can explain information lost by global summaries, and
conditional laws can separate boundary assumptions from geometric consistency.
Those are legitimate outcomes even if reconstruction remains underdetermined.
If further observables merely improve recognition of familiar ensembles, stop
classifier optimization. Exploratory intrinsic causal dynamics is a reasonable
next research direction, with its own falsifiable protocol and scaling tests.
Emergent geometry or gravity would be hypotheses for that future work. No result
here proves physical discreteness, a controlled continuum limit, or singularity
resolution.
