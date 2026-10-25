# Experiment 7 preregistration: dynamical quantum locality

Status: committed before implementation/piloting and before any primary data.
The companion [theory](DYNAMICAL_LOCALITY_THEORY.md) contains the derivations.
This is the final computational experiment of this programme. No alternative
Hamiltonian, parameter optimization, post-result connectivity reward, or successor
experiment is authorized by this protocol.

## Baseline gate and question

Experiment 6 PR #7 merged into main at
`73baea299fb07d608bade8364d6cf66443e23166`. The post-merge push
[CI run](https://github.com/raghammer1/causal-spacetime-lab/actions/runs/40173493770)
succeeded. The inherited suite passed 1,001 tests. The research atlas is included
in that baseline. Work is isolated on `experiment/dynamical-quantum-locality-v1`.
The baseline scientific reports and their audits remain evidence, including
Experiment 6's failed bootstrap calibration. No prior archive is rewritten.

Question: can this one coordinate-free, but explicitly matter/link-factorized,
quantum law organize useful operational neighborhoods beyond preparation asymmetry,
supplied couplings, degree preferences, and selected graph measurements?
Finite symmetric states cannot distinguish labeled neighbors; this is an exact
restriction on that route, not a prohibition of relational graph correlations.

## Model, units and fixed grid

For N matter qubits and M=N(N−1)/2 link qubits, use

    H = −h Σ_i X_i − g Σ_(i<j) n_ij Z_i Z_j − Gamma Σ_e X_e
        + mu Σ_e n_e + U Σ_i D_i(D_i−1)/2,
    n_e=(I−Z_e)/2, D_i=Σ_(j!=i) n_ij, h=g=U=1.

The six cells are mu={2,0.1,−2} crossed with Gamma={0.25,1}.
The analytic reference regimes are empty, maximum-matching, and degree-two graphs;
the latter is a classical limit, not a prediction for finite fields. Mu and U
supply degree preferences and incidence interactions. No coordinates, preferred
spatial dimension, loop or connectivity reward are present. Set hbar=1; time is
external and has reciprocal energy units. There is no physical length unit.
Tensor axes are matter 0..N−1, then unordered links in lexicographic order;
axis zero is the most significant bit. Complex128/float64 throughout.

## Initial states, times and independent streams

All primary matter factors have Bloch vector (1/sqrt(2),0,1/sqrt(2)):
`cos(pi/8)|0>+sin(pi/8)|1>`.

* Splus: every link is |+>.
* Sempty: every link is |0>.
* E: independently for every link draw p uniform[.25,.75] and phase phi
  uniform[0,2pi); its factor is sqrt(1−p)|0>+exp(i phi)sqrt(p)|1>.
  Each realization supplies asymmetry; only its distribution is exchangeable.

No hidden graph initializes the primary model. Record every product factor.
Structure ages are [0,.5,1,2,3,4]. Intervene at age2 with Pauli Y on each matter
source, using a separate identically prepared copy for each source. Response delays
are [0,.05,.1,.25,.5,1,2]. The same initial factors are used for a paired scalar
Gamma -> 1.05 Gamma perturbation. This perturbation preserves the Hamiltonian's
permutation symmetry; it is not spontaneous symmetry breaking.

Seed entropy is `[20261025,7,stream,N,cell,batch,replicate,purpose]`, with stream
codes smoke=1, calibration=2, timing-pilot=3, primary=4, audit=5. Use NumPy
SeedSequence/default_rng; no global random state or Python randomized hash.
Distinct purposes separate preparation, Born draws, solver starts and control
permutations. Three independent primary E batches have the same pilot-selected
number R in {12,8,4}; total E units per cell are 3R. Splus and Sempty are exact
specified preparations, not three fictitious independent observations.

## Numerical procedures and feasibility selection

Use a diagonal plus bit-flip representation, CSR for N<=5 and matrix-free for N6.
Validate against independently assembled dense tensor matrices. SciPy exponential
matrix action propagates states; supply the actual trace (the Hamiltonian is not
traceless). Record norms, own-trajectory energy drift, conserved matter-X parity,
and solver diagnostics. A source kick can change energy: compare each branch to
its own initial energy. Tolerances: norm and probability normalization 2e−9;
energy/parity drift 2e−8 times max(1,|initial value|); ground residual relative to
max(1,|E0|) <=1e−9; independent dense agreement <=2e−8. Any failure is retained,
invalidates a positive decision, and triggers diagnosis rather than sample deletion.

N4 (Q10) and N5 (Q15) are mandatory. N6 (Q21) is optional only under this rule:
a timing-only pilot measures the full bundle (structure, all source responses,
perturbation, both frozen comparisons, reductions and serialization), covering all
six cells and Splus/Sempty/E. It records timings/memory and numerical validity,
not scientific summary rankings. Pilot scientific arrays are discarded. A partial
pilot may reject a size as soon as the maximum measured bundle time already
implies that its smallest COMPLETE workload cannot fit; no partial N6 cohort is
retained as primary evidence. Otherwise every pilot case is required for admission.

One worker and one BLAS thread. Limit peak RSS to2GiB. The conservative projected
full primary workload, including fixed controls and equilibrium, is twice the
measured maximum-per-size bundle cost times all required bundles, plus twice fixed
costs, and must fit20 minutes. Choose the largest R in {12,8,4} that fits N4+N5;
then admit N6 only if the entire same-R six-cell cohort also fits. If mandatory
R4 cannot fit, report infeasibility and amend computational scope openly before
primary, without looking at pilot scientific outcomes. Pilot hard cap20 minutes;
primary hard cap45 minutes and replay separate45 minutes. A timed-out or failed
case cannot be replaced by an easier parameter family. Store feasibility arithmetic,
rejection evidence, actual timing/RSS and source hash in a committed freeze manifest.

Compute a ground vector and two lowest eigenvalues independently for every
admitted N/cell with a generic seeded eigensolver start (not restricted to even
parity). Archive residuals/gap, ground Born law, and ground operational response.
These are equilibrium preparations, not endpoints of cooling. At N4 only, obtain
the full spectrum and exact Gibbs Born laws at beta=.5 and2, including energy and
entropy. At N5/6 a full dense thermal matrix is outside the resource design; no
approximate thermal claims or surrogate dynamics are substituted.

## Raw measurements and graph controls

Enumerate every classical labeled graph at admitted N (64,1024,32768). For each
state compute exact Born law P(G)=Σ_m |psi(m,G)|². Archive that full vector,
occupations, count variance/covariances, and graph catalog: degrees, components,
component sizes, largest-component fraction, isolation/hubs, triangles, clustering,
distances, connected diameter, ball sizes and Laplacian spectra. Disconnected
distances have an explicit sentinel, never a fabricated finite distance.
No dimension/power-law fit is allowed on these sizes. Report geometry beyond a
finite graph as unresolved. Exact sums have numerical error, not Monte Carlo CIs.
Draw eight unselected Born configurations per recorded state for reproducible
examples. Never redraw until a connected or attractive graph appears.

Compare exact laws and graph expectations to: (a) G(N,pbar) at the same density;
(b) product Bernoulli links with the same individual occupations; (c) uniform
conditional on edge count; (d) uniform conditional on the FULL labeled degree
vector, Q_deg(G)=P(deg G)/#{H:deg H=deg G}. The last is exact degree-preserving
rewiring without a mixing assumption. Record total variation and property contrasts.
Tiny degree classes may force graph topology; zero distinguishability there is
lack of identifiability, not evidence for a spatial law. Include the exact N6
C6 versus two-triangle classical degeneracy even if N6 quantum dynamics is excluded.

Stability means stability of the one-time Born distributions/expectations.
Independent Born draws at different ages are NOT a trajectory or edge persistence.
For N4 only, first E realization of each cell in batch0: exactly dephase links at
age2 by summing all64 projected pure branches, evolve each one further to age3,
and compare the weighted future Born law to the unmeasured continuation. Keep all
outcomes with their Born weights. This tests explicit nonselective measurement
backaction; it is not selection of a preferred branch.

## Operational assay and matched controls

R_ij(t)=1/2 ||rho_j[U(t)Y_i psi(2)]−rho_j[U(t)psi(2)]||_1 for i!=j.
Compute it as half the Bloch-vector difference and independently verify via reduced
matrix eigenvalues. Save baseline/intervened Bloch vectors, source global trace
distance, all ordered pair responses, and the exact aged first-order slopes
`2|g| sqrt(<n_ij Zi Xj>²+<n_ij Zi Yj>²)`.
This is target-only signalling distinguishability, distinct from correlation.
Do not substitute initial occupation-only slopes after entangling evolution.
Record earliest sampled crossing of response .01 and .05; noncrossings are
right-censored, not infinite physical speed. Only the supplied/static graph
controls have an independently specified distance for interpreting onset.

For every primary preparation/cell, also evolve the SAME initial state with
Gamma=0 throughout age and response (initial-frozen control), and separately freeze
Gamma=0 only after the actual age2 state (probe-frozen control). The former tests
organization beyond the initial conditions. The latter tests the role of continued
link fluctuations; it is not required to perform worse than a legitimately
organized frozen graph. Paired Gamma+5% evolution uses the full age and response.

Required separate controls:

* Static chain TFIM, h=g=1, the same fresh matter product and Y intervention.
  Randomly relabel the graph; graph truth is used only for evaluation. Validate
  zero response at delay0, early adjacent response, later distant response, and
  nested-commutator order. This is SUPPLIED locality.
* Complete homogeneous static interactions: equal off-diagonal responses.
* Independent quantum links: g=U=0 with the same h,mu,Gamma, all three preparation
  types. Exact one-qubit evolution validates Born factorization and zero cross-site
  signalling. One independently seeded E control per cell/size suffices for this
  exact identity; it is not a statistical organization cohort.
* Frozen random and rewired graphs: for every graph, compute fresh-matter static
  response under its N-qubit TFIM. Weight by the actual age2 Born law and each
  exact null above. The mean conditional response (graph record available) and
  response of the unobserved mixture are DIFFERENT: for the latter average Bloch
  vectors before taking distances. This changed preparation is explicitly labeled.
* Disconnected maximum matchings and (where available) triangle components:
  cross-component response zero, connectivity criterion failed.
* Layout/threshold control: fixed circular and spring-like or spectral drawings,
  and occupation thresholds .25,.5,.75, must leave raw quantum responses unchanged.
  No drawing/threshold enters the primary statistic. Selected connected conditional
  curves, if shown, include the selection probability and are secondary.

The short-time complete-support commutator and all-off cubic response are derived
in theory and independently checked on small systems. No physical light speed is
fitted. Direct matter-link couplings already supply possible influence channels.

## Prespecified advancement screen, uncertainty and decisions

This is a necessary-property test of this finite model, not a spacetime classifier.
For each response matrix and source, select the two largest responses with
fractional boundary ties (absolute tie tolerance1e−10); weights sum to2. Define
F as the source-average fraction of total off-diagonal response in those weights.
This is response concentration, not recovery of independently established neighbors.
Weights are recomputed separately at each delay. A zero total response has no
locality score and fails the screen; no undefined rows may be omitted. Uniform responses
have F=2/(N−1); also report (F−2/(N−1))/(1−2/(N−1)) as a descriptive
normalized excess, disclosing the size dependence of the raw .8 threshold.
Define neighborhood overlap as the source-average sum of minimum
weights divided by2. These quantities use no graph drawing or inferred distance.

One E realization passes the JOINT necessary screen only when all hold:

1. **C:** Born connectivity >=.8 at each of ages2,3,4.
2. **L:** F>=.8 and mean off-diagonal response>=.01 at BOTH delays .25 and .5.
3. **T:** TV(P2,P3)<=.1 and TV(P3,P4)<=.1; at BOTH response delays, neighborhood
   overlap between full dynamics and its Gamma+5% perturbation >=.8, and the
   perturbed F and mean response also meet L.
4. **D:** F_full−F_initial-frozen>=.1 at BOTH delays. A frozen control with no
   response does not provide a valid positive advantage. This is a demanding
   prespecified practical organization margin, not a theorem defining all locality.

Also tabulate every component failure; no favorable component rescues joint failure.
These thresholds are practical finite assay choices, not physical constants.
The static chain validates the operational assay, not the dynamical-organization D
condition. Symmetric preparations are checked separately against exact symmetry;
there can be relational Born structure even when their labeled L condition fails.

Independent units are complete E preparations, including all pairs, times and
perturbations. Compute exact two-sided Clopper–Pearson intervals on joint success
probabilities with total familywise alpha=.05 across K=6*number_of_admitted_sizes
cells (each tail .05/(2K)). Desired joint success probability is .8. With K12 and
36/36 successes the lower bound is about.842; Rtotal24 cannot certify .8 even if
all pass. This power loss is disclosed if the timing pilot selects a smaller R.
Report component counts and continuous distributions descriptively, not additional
unadjusted confirmatory tests. Bounded means may have Hoeffding bands with a stated
family size/range, never an unvalidated percentile bootstrap. Calibrate exact CP
coverage by binomial enumeration on an independent calibration stream, plus
synthetic no-signalling/symmetry/static-chain checks. Keep failures.

**Finite-model NO-GO:** each of the six parameter settings has at least one
required size with joint CP upper bound below .8 and assay/numerical validation passes; or an exact obstruction proves a specific claimed
route impossible. State the route and scope. This does not rule out all quantum
growth laws or conditional/thermodynamic relational locality.

**INCONCLUSIVE:** any potentially qualifying cell is unresolved by these bounds,
required controls fail, precision fails, or the claimed interpretation cannot be
distinguished from preparation/degree/null explanations. Geometry/continuum scaling
is independently unresolved at these sizes, even if this finite screen fails.

**LIMITED GO:** at least one fixed (mu,Gamma) cell has joint lower bound>.8 at
EVERY admitted size, with independently verified mechanism beyond supplied
asymmetry/costs. In addition, at N>=5 its age2 graph law must differ from the exact
degree null by TV>=.1 and connectivity advantage>=.1 in >=80% of preparations
(with the same conservative CP lower criterion, counted in an additional family
of K bounds, so GO uses tail .05/(4K) for BOTH families). Its observed operational
advantage must not be reproduced by fresh-probe density/degree-matched graph
mixtures. This last interpretive requirement cannot be established by visual
preference; unresolved evidence yields INCONCLUSIVE. Degree constraints at N4
can make the structural comparison unidentifiable and are not called geometry.
A GO could motivate theory only; it would not establish spacetime or gravity.

To avoid an inconsistent alpha change, primary archives include both the K-family
screen bounds and the stricter 2K-family GO bounds from the outset. No positive
claim may use the more favorable interval. No unregistered exploratory statistic
can change the registered decision. Preserve negative results and exact examples.

## Audit, artifacts and closure

Commit this protocol/theory before primary implementation; run inherited pytest
and a CLI first. Commit tested source and a timing-only feasibility manifest before
primary. Archive exact initial factors, parameters, semantic seeds, full Born and
reduced response arrays, graph catalog, calibration/pilot outcomes, numerical
failures, environment (no personal paths), source/protocol hashes, tables and
scientific figures. Full amplitudes are checkpointed for Splus/Sempty/ground and
first E per batch/cell at age2; other states are independently regenerable.

Independent audits must not import the production analysis helpers: dense tensor
Hamiltonian/response checks; reconstruction of decisive graph/statistical quantities
from archived arrays; and selected primary state regeneration from explicit factors.
Repeat the complete frozen workload when feasible, compare scientific file digests,
and distinguish replay from independent statistical evidence. Full tests and one
end-to-end CLI run precede every commit. Review secrets/private paths before push.

Report questions A–L in DYNAMICAL_LOCALITY_RESULTS.md, preserve all prior reports
and atlas, update README/roadmap/research log, and write FINAL_RESEARCH_SYNTHESIS.md
covering all seven experiments. Choose A/B/C from the user brief with evidence.
For NO-GO or INCONCLUSIVE, default to stopping computational exploration; do not
invent Experiment8 or a new Hamiltonian. Push and open the requested PR into main,
verify published CI, and do not merge automatically.

## Resource-only amendment A1, before primary generation

Two complete timing-only N4/N5 pilots rejected the minimum R4 cohort under the
original1200-second conservative projection. The first is retained at
[attempt1](experiments/dynamical-locality-pilot-attempt1.json); an exact frozen-sector
optimization was independently tested before
[attempt2](experiments/dynamical-locality-pilot-attempt2.json), which also exceeded
that target. No primary data exist at this amendment, and pilot scientific outcomes
were discarded rather than used to choose a workload.

For one final timing pilot, raise ONLY the conservative full-workload planning
allowance from20 to30 minutes (1800 seconds). Retain the factor2 safety margin,
45-minute hard primary cap, separate45-minute replay cap,20-minute pilot cap,
2GiB RSS limit, single worker/thread, complete cohorts, R candidates12/8/4, all
parameters/preparations/controls, precision and every scientific decision threshold.
The N6 censored timing bound consequently becomes1800/(2*84)+.05 seconds. Re-run
the complete timing pilot from committed source before selecting R and freezing
primary execution. This spends more computation; it does not relax a scientific
advancement rule. The original rejected projections and this amendment remain
visible in history and the final report.
