# Research roadmap and stopping criteria

**Programme closed after Experiment 7; overall conclusion B.** The
[final synthesis](FINAL_RESEARCH_SYNTHESIS.md) records what all seven experiments
establish and what remains unresolved. The sections below preserve the research
trajectory. They are not a queue for Experiment 8 or a new tuned Hamiltonian.
Further computation requires an independently justified physical principle,
controlled mathematical construction or discriminating prediction.

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

## A. Dimension-sensitive order statistics — initial study implemented

[Experiment 2](DIMENSION_RECONSTRUCTION_RESULTS.md) implements independent flat
d=2,3,4 generators, verified Myrheim–Meyer inversion and joint order statistics.
At N=256 all 600 genuine holdouts received their known dimension labels, while
all 1,800 matched artificial orders also received their target labels. Joint
observables reject those easy matched controls but accept 49/200 random-DAG
controls at N=64. The following requirements guide stronger follow-up work;
they are not all settled by that initial result.

**Question:** Can several order observables discriminate known continuum
dimensions from adversarial non-manifoldlike orders?

Derive and test the Myrheim–Meyer relation with an explicit convention:
`r = R / binom(N,2)` has expectation
`Gamma(d+1)*Gamma(d/2)/(2*Gamma(3*d/2))` in a flat Alexandrov interval.
For `R/N²`, the corresponding large-N expression is half this value. The
derivation and source equations are recorded in [THEORY.md](THEORY.md).
Independent generators and inversion are now validated in dimensions 2, 3 and 4;
follow-up work must propagate calibration uncertainty and test harder adversaries.
Do not substitute a heuristic based on one pair fraction.

**Controls:** total orders, antichains, layered orders, and non-manifoldlike
orders chosen to match a pair fraction. Measure interval abundances, chain length,
width and size dependence alongside inferred dimension. Use ensembles rather
than pretending correlated pairs are independent Bernoulli observations.

**Refutation:** failure to recover known dimension within calibrated uncertainty,
strong size drift, or inability to distinguish matched-statistic controls rejects
the estimator or the claim that these observables suffice. A plausible numerical
dimension alone does not establish continuum geometry.

The first study's selected features are also exactly equal for nonisomorphic V
and dual orders. Explore additional observables and ablations without interpreting
a successful finite feature list as a complete geometry test.

## A2. Adversarial geometry — implemented, advancement gate not met

[Experiment 3](ADVERSARIAL_GEOMETRY_RESULTS.md) compares six detectors across
three independent calibrations, multiple DAG probabilities, protected-height
searches and an unseen interval-order family. All 5,400 searches match height and
ordering fraction; none satisfies every one of the 15 full-match constraints.
Some failed searches still pass every detector. Every detector fails the primary
advancement benchmark. Complex models improve selected contrasts, but no primary
contrast meets the complete genuine-retention guard; the prespecified 97.5%
sensitivity target supports some local gains over the two-feature baseline.

**Follow-up implemented in A3:** induced 2+2 motifs, internal interval order
types, overlaps and joint structure, with exact-statistic adversaries and search
budgets scaled with N. It separates finite-search failure from mathematical
information loss and retains independent reference fits and an unseen family.
Three fits still provide limited calibration-uncertainty evidence. The follow-up
does not train a new detector or claim matched classifier acceptance rates.

**Exact boundary:** a rank-two abstract sampler has the same order distribution
as a d=2 flat diamond, so no order-only statistic can distinguish their provenance.
The selected full interval histogram also coincides for exact nondual finite
orders. Conversely, flat samples with different region boundaries can be rejected.
Validation must define the target sampling law, not equate rejection with absence
of geometry or coordinate-free generation with emergence.

**Stopping criterion:** retain the no-go for interpreting a growth experiment as
validated emergent geometry. Passing conditional local-law tests does not resolve
embedding and continuum-limit requirements. Exploratory growth remains possible
as a mathematical model with explicit failed controls; it must not treat these
comparisons as spacetime certificates.

## A3. Local causal structure — useful information, incomplete reconstruction

[Experiment 4](LOCAL_CAUSAL_STRUCTURE_RESULTS.md) replaces classifier escalation
with exact identities and conditional interval laws. The new observables
distinguish old-summary collisions, yet a post-registration exact example and
counting argument also establish collisions of the entire measured structural
vector on unrestricted orders. The rank-two/d2 provenance ambiguity persists
even when the full order is known.

All 42 primary diamond/slab comparisons satisfy their registered practical
equivalence margins. Local dimension estimates recover the generating dimension
in convex slabs despite large global-estimator boundary bias. Small-N d4 slabs
lack enough intervals; boxes can be practically compatible while retaining a
detectable dimension bias. The unseen rank-three construction remains partially
inconclusive against d3. All N256 switched ensembles meet the local-law margins,
even though all 96 d4 searches change a measured isomorphism invariant.

**Decision:** the structural findings improve understanding, but do not validate
geometric embeddability or a controlled continuum limit. Stop optimizing a
classifier leaderboard. The next geometric study should specify one convergence
target and test consistency from single growing orders, a mesoscopic scale
window, density variation and curvature/boundary bias with independent controls.
Embedding existence, approximate uniqueness, concentration/tightness and
universality remain separate mathematical requirements; see the
[continuum guide](LOCAL_CAUSAL_STRUCTURE_CONTINUUM.md).

**Stopping criterion:** if added statistics only recognize familiar samplers,
end that line of optimization. Background-free causal dynamics may proceed as
an exploratory mathematical program with fresh falsification criteria, while
retaining the unresolved reconstruction limits and negative controls below.
Neither a finite feature match nor a failed search is a spacetime certificate.

## B. Background-free growth — implemented, ordinary-CSG limit obstructed

**Question:** Can an explicitly specified rule on abstract orders produce stable
continuum-like statistics without supplied positions or metric?

[Experiment 5](BACKGROUND_FREE_GROWTH_RESULTS.md) implements intrinsic fixed-p
transitive percolation, verifies elementary birth-history covariance and follows
individual histories through N512 with paired thinning. All six registered
settings fail the necessary finite signature. Both the d2 reference and an
analytic height-two control pass, while conditional interval laws expose other
differences. The study preserves insufficient support and adverse control
results, including a false rejection by the small-N secondary TV rule.

The [mathematical foundations](BACKGROUND_FREE_GROWTH_THEORY.md), documented
before implementation, establish a fixed-p almost-sure chain sampling limit and
the wider Brightwell–Georgiou almost-semiorder obstruction for ordinary CSG.
These results concern specified global finite-suborder sampling limits, not all
possible intrinsic dynamics or local scaling limits. Dense chain sampling also
does not imply that almost all events lie in one chain.

**Decision:** no further parameter or classifier optimization of this baseline.
A limited next step is mathematical design under explicitly changed assumptions,
or a different precise convergence question. Before a new kernel is implemented,
establish normalization, compatible prefixes, genuine birth covariance and the
status of Bell causality. An order-and-measure limit, concentration, quantified
reconstruction/uniqueness, mesoscopic scale separation and universality remain
unverified. Merely making a rule depend on local motifs does not supply them.

**Refutation:** signatures disappear with increasing size, depend on birth labels,
require hidden coordinates, or cannot distinguish matched controls. Even success
would demonstrate properties of a mathematical model, not its relevance to our
universe, Lorentzian dynamics or quantum gravity.

## B2. Quantum information — useful proximity, no geometric advancement

[Experiment 6](QUANTUM_EMERGENCE_RESULTS.md) changes the foundational hypothesis;
the classical CSG obstruction does not automatically extend to quantum models.
Its finite transverse-field Ising laboratory recovers supplied chain edges at h=1
and finds stable rankings in random exchangeable interactions. The symmetric
finite ground state has an exact no-neighborhood theorem. The random model fails
the all-size physical-null comparison; raw distances violate metric conditions,
cut-law assumptions are not generally satisfied, and early-time propagation
explicitly follows supplied couplings. A fixed tensor factorization and external
time remain assumptions. No independent dynamical locality was established.

**Decision:** no limited GO for a geometric mechanism from these models. Stop
classifier, layout and favorable-parameter optimization. Preserve the useful
reconstruction result and the adverse field/control/uncertainty findings, including
91.25% calibration coverage for nominal 95% bootstrap intervals. A new study needs
a theoretical reason to alter the mechanism, not additional visually convincing
features or a reward for a selected dimension.

**Next mathematical prerequisites:** define operational subsystem algebras and
coarse-graining; specify a justified autonomous state/interaction law; identify its
symmetries and conserved quantities; derive a falsifiable propagation or entropy
consequence that is not already inserted through J. A potential quantum-edge model
would require its own derivation and controls; this experiment did not implement
or validate Quantum Graphity. Any external classical feedback must be labeled as
such and include measurement/backaction assumptions.

**Controlled-limit requirements:** a compatible sequence of states/observables,
metric nondegeneracy and approximate uniqueness, concentration/tightness,
mesoscopic scale separation, universality and local propagation bounds uniform
on the relevant scales. Lorentzian causality, a matter sector, conservation laws
and effective gravitational equations are separate obligations. Passing a sampled
cut law or reconstructing a fixed chain supplies none of these automatically.

**Refutation:** neighborhoods depend on arbitrary labels/ties, numerical floors or
convenient projections; physical nulls look equivalent; independent preparation
or perturbation destroys the proposed structure; a dimension drifts without a
controlled scaling law; or the proposed propagation simply copies supplied
interactions. Inconclusive finite evidence must remain inconclusive. Broader
quantum-information-first approaches are neither confirmed nor universally ruled
out by this small experiment.

## B3. Dynamical quantum locality — final test, finite benchmark NO-GO

[Experiment 7](DYNAMICAL_LOCALITY_RESULTS.md) promotes links to quantum degrees of
freedom and tests operational Y-intervention responses, exact Born laws, symmetry,
equilibrium, measurement backaction and density/degree-matched frozen controls.
All twelve parameter/size cells have 0/12 joint successes, with simultaneous exact
upper probability bound 0.402190 below the required 0.8. All required controls pass.
Independent state/statistical and graph/static implementations verify the result.

The law does produce correlations beyond independent links, favorable perturbation
rank stability in some diagnostics, and measurable dephasing effects. These are
not a controlled geometric mechanism. Symmetric states retain uniform labeled
responses. The complete microscopic interaction support, exact matching-sector
fragmentation and tiny-size degree-null restrictions expose supplied structure.
Conditional fresh-matter propagation on a recorded graph answers a different
question from the unconditioned quantum assay. Relational/thermodynamic continuum
interpretations remain unresolved, not universally excluded.

**Final decision:** stop this computational model-exploration programme. Preserve
all failures, audits, resource amendments and exact counterexamples. Do not
optimize another classifier, tune a connectivity reward, propose Experiment 8 or
choose a replacement Hamiltonian merely to continue. The overall conclusion is B:
useful mathematics and computation, insufficient physical evidence for further
simulation-led pursuit of the hypothesis.

**Conditions for a meaningful restart:** a new independently motivated principle,
a specified sequence with controlled coarse-graining and effective locality,
or a quantitative discriminating prediction. Energy normalization, relational
observables, concentration, geometric nondegeneracy/uniqueness, scale separation,
Lorentzian causality and gravitational dynamics are separate obligations. No
such restart is planned or authorized by this roadmap.

## C. Curved backgrounds and causal horizons — unimplemented prerequisites

These historical checks are prerequisites for any justified restart, not a next
experiment. Such a study would require a specified metric and invariant volume element. Compare recovered
proper time with an independent continuum calculation along known geodesics.
Separate density gradients, boundary effects and curvature. Flat-space recovery
must be regained in the appropriate limit. Observer-dependent causal horizons
can occur in flat spacetime: a causal horizon is **not a black-hole solution**.

**Refutation:** inconsistency with continuum benchmarks, failure of the flat limit,
or sensitivity to coordinate choices beyond numerical error. No claim of
singularity resolution follows from a finite graph or a missing divergent value.

## D. Gravitational dynamics and observation — unimplemented prerequisites

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
