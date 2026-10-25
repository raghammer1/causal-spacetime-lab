# Experiment 6 protocol: quantum information before spacetime

Status: preregistration, written before implementation of the new numerical models
and before primary outcomes. The protocol and theory will be committed first;
a timing-only pilot will then choose repetitions by the rule below. A second
source/workload commit must precede primary execution. No post-outcome tuning.

## Baseline and scope

PR #5 was merged at `9bc5984c656271c247354e0079fd900702642064` on
2026-10-25. The post-merge push workflow [40169210699](https://github.com/raghammer1/causal-spacetime-lab/actions/runs/40169210699)
succeeded, and all 813 inherited tests passed. Work uses the isolated branch
`experiment/quantum-information-emergence-v1`; main will not be changed or merged.
This is an educational exact finite quantum experiment, not a quantum gravity model.
The preceding classical-growth obstruction does not apply automatically to quantum models.

The claim hierarchy is (1) correlation graph; (2) justified geometric interpretation;
(3) locality under an independently specified dynamical law; (4) physical spacetime.
Neither a layout nor a low-dimensional fit permits skipping levels.

## Questions and hypotheses

1. **Reconstruction:** can mutual information recover nearest-neighbor bonds of a
hidden, independently sampled one-dimensional spin chain? Predeclared practical
success is a mean edge/nonedge AUC whose pointwise 95% lower confidence bound
exceeds 0.8 in each size at h=1, and the exact one-sided Clopper–Pearson
lower bound for Pr(AUC >= .75) exceeds .8, at alpha=.05/3 per size. The latter
prevents an all-success bootstrap sample from implying certainty. Wide bounds
are inconclusive. Results at h=0.5 and 2 qualify regime dependence.
This only reconstructs supplied locality.
2. **Symmetry obstruction:** Model A's finite ground state cannot select different
neighborhoods. Perron–Frobenius uniqueness for h>0 and permutation invariance imply
identical pair marginals. Apparent differences above numerical error falsify the
implementation, not this theorem. Random asymmetric initial preparations supply
asymmetry rather than demonstrate spontaneous symmetry breaking.
3. **Geometry-free proximity:** does Model B produce nonuniform, reproducible
within-realization proximity that is robust to small coupling perturbations?
Independent exchangeable realizations are compared through invariant summaries,
never by matching their arbitrary vertex labels. Persistence over sizes means
persistence of these summary properties, not convergence to a continuum.
4. **Metric and inference failures:** raw log-MI dissimilarity is not generally a
metric (Bell-pair identity failure and purified-AND triangle failure). GHZ,
product, Haar and scrambled controls may have attractive embeddings. Test these
failures explicitly, retaining all controls and all fixed projections.
5. **Mechanism:** separate direct pair-coupling copying from collective dependence
on the whole Hamiltonian. Low correlation with direct |J| does not establish
independence from J. Evaluate a multipartite cut-entropy assumption independently
of pairwise patterns, and derive/test infinitesimal operator propagation. A
geometric mechanism requires more than ranking/embedding improvement.

## Fixed models and ensembles

The supplied Hilbert space is `(C^2)^tensor n`, with a fixed operational tensor
factorization. This is structure even when no coordinates are assigned. Units have
hbar=1 and coupling scale g=1. All models use

`H = -h sum_i X_i - sum_{i<j} J_ij Z_i Z_j`, n in {6,8,10}, h in {0.5,1,2}.

- **A:** J_ij=1/(n-1), a permutation-symmetric ferromagnet. One ground state per
(n,h), not repeated deterministic observations masquerading as samples.
- **B:** independent unordered pairs J_ij ~ Normal(0,1)/sqrt(n-1); symmetric,
zero diagonal, exchangeable and signed. No rejection or favorable seed selection.
- **Chain:** independent nearest-neighbor bonds Uniform[0.8,1.2] on an open chain,
all other J zero; independently permute vertices before measurement. Only the
separate evaluator receives J or the hidden true edge set.

Each size has independent realizations; the same realization is reused across h,
perturbations and paired controls. Each family/size has three independent batches
of R realizations. R is selected from {8,4,2} by timing only. All sizes, fields,
families and negative controls remain included. The normalizations define a
sequence of ensembles, not a demonstrated renormalization flow.

At h=1, use two independent standardized Gaussian coupling perturbations,
delta in {0.01,0.05}: B and A perturb every unordered edge at their corresponding
1/sqrt(n-1) and 1/(n-1) scale; chain perturbs existing bonds only at unit scale.
The zero pattern of a chain perturbation therefore supplies locality. Use one
noise draw per delta, retaining it with the coupling data. A gets 3R independent
perturbations per size around its deterministic baseline; do not assign its
baseline a stochastic confidence interval.

## State preparation and controls

Compute the ground state with sparse real-symmetric eigensolvers, generic seeded
starts (not a parity-restricted all-plus start), two lowest eigenpairs and recorded
absolute/scaled residuals and gap. Default tolerance 1e-12; reject rather than
silently normalize away a numerically unresolved calculation (scaled residual >1e-9,
normalization error >1e-10, or gap <=100 times absolute residual). Preserve failed
solves and denominators; no seed substitution. These checks are numerical diagnostics, not a rigorous global ground-state
certificate. Dense independent diagonalization checks small systems. The h>0 ground state has positive real amplitudes up to a
global phase; do not repair a wrong eigenvector by taking entrywise absolute values.

Controls at every n: all-plus product; GHZ; Bell-pair product with random relabeling;
3R independent Haar pure states and independent random product states. Bell pairing
and GHZ are supplied special state structure. At h=1, phase-scramble each B/chain/A
baseline and its perturbed counterpart with the **same** independent computational-
basis phase vector for each pair. Scrambling preserves all computational-basis
probabilities and all Z statistics, not generally entanglement. Shared phases avoid
an unfair stability penalty to the null. Record paired state identifiers.

Bounded secondary unitary preparation study: at h=1, use the first realization of each batch and size for B and chain, and the same number of
independent random product preparations for A. Evolve all-plus and random-product
states to externally specified t in {0.5,1,2}. This tests preparation sensitivity;
there is no inferred time or claim of relaxation from these few snapshots.

## Observables and leakage separation

Quantum-state routines return one-site entropy, pair entropy, MI in bits,
negativity `(||rho_ij^(Tj)||_1-1)/2`, log-negativity and connected ZZ correlations.
Nonnegative quantities may clip roundoff only within a documented 1e-10 tolerance;
large violations are failures. MI is total correlation, not pair entanglement.

The inference module receives only the symmetric MI matrix. It never receives J,
coordinates, true adjacency, target dimension or family names. Return the entire
classical-MDS spectrum and all positive-eigenvalue coordinates. A separate evaluator
reports every fixed projection dimension 1,2,3 (and full positive rank) equally for
all families; it does not choose a favorable dimension.

Primary dissimilarity: `d_ij=-ln(max(I_ij,epsilon)/2)`, off diagonal; diagonal zero.
Use epsilon in {1e-12,1e-9,1e-6}, with 1e-9 primary. Report regularized zero-information edges explicitly;
they are not demonstrated links. Test symmetry, nonnegativity, zero-distance
collisions, raw triangle violation fraction and largest excess. A shortest-path
closure is an explicitly imposed metric/pseudometric comparator, never a discovery.
Report all MDS eigenvalues, negative eigenvalue mass, positive-spectrum participation
rank, normalized distance stress at each fixed projection, and epsilon sensitivity.

For k in {1,2,3}, nearest-neighbor membership uses fractional boundary ties,
with score tolerance 1e-10 absolute plus 1e-8 relative; index tie-breaking is forbidden.
Report tie ambiguity and row-normalized overlap across perturbations and between
MI and direct |J|. Compare relative score thresholds {0.25,0.5,0.75} of each matrix's
maximum; zero matrices produce no edges. Record edge density, connected-component
count and threshold instability rather than treating threshold choice as physical.

Independent evaluator: tie-aware edge/nonedge AUC and fractional top-(n-1) edge
recall for chain; Spearman(MI,|J|), Spearman(MI,|connected ZZ|),
Spearman(MI,negativity), and neighborhood overlaps (undefined constant correlations
stay undefined). Compare the same MDS diagnostics for |J| normalized to [0,2]; this
normalization is an evaluator comparison, not a second inferred physical distance.

For each state record the redundancy-constrained cut-law defect
`D(B)=S(B)-0.5 sum_{i in B,j not in B} I_ij` for all singleton cuts and four
uniformly sampled distinct unordered balanced bipartitions. Share cuts within each
baseline/perturbation/scramble comparison; transport under relabeling. Report raw
and normalized defect `D/max(S,0.5 sum MI,1e-12)` with zero/zero set to zero.
This tests a condition in Cao–Carroll–Michalakis, not their whole construction;
a few cuts cannot establish their condition for all regions. Product/Bell states
can satisfy it without connected spatial geometry. GHZ gives the exact defect
`1-|B|(n-|B|)/2` for any nonempty proper cut.

Statistic-level null: independently shuffle the upper-triangle MI weights and
symmetrize, preserving the weight multiset. These matrices need not be quantum
marginals. Use 31 shuffles per baseline h=1 state (and Haar/GHZ/Bell controls),
with the same shuffle applied in paired comparisons. Compare stress and spectrum
against the conditional null mean; do not count null draws as independent states.

## Decisions and uncertainty

Report means, standard deviations, pointwise 95% percentile bootstrap intervals
(3999 resamples within each of three batches), and all batch means. The independent
unit is a coupling realization/state, with paired differences formed **before**
resampling. No pair, cut, perturbation or time snapshot is an independent quantum
sample. Different sizes are independent; no extrapolated dimension fit. Deterministic
controls get numerical error, not invented sampling intervals. Mark intervals with
fewer than 12 independent units as weak and descriptive. Test bootstrap code against
analytic cases and 400 fixed-seed normal-mean coverage trials at 24 independent
units (399 bootstrap draws per trial), and exact-binomial coverage on its finite
outcome space; do not promise
exact coverage for non-Gaussian small samples or nonlinear boundaries.

No trained classifier or selected fitting pipeline is used. Calibration uses its
own independent stream to validate uncertainty/numerical tolerances and conditional
null software, not to pick a Hamiltonian, dimension, epsilon, threshold or outcome.
Implementation smoke, calibration, pilot and primary namespaces never overlap.

For h=1 Model B, a **proximity-only candidate** requires all three sizes to show:
mean k=2 overlap >=0.8 after delta=.01 (95% lower bound), >=0.6 after delta=.05,
MI contrast (off-diagonal max-min) >1e-6, and full-regularization neighborhood
agreement >=.95 (using the floored MI scores at each epsilon). This says nothing about dimension or independent dynamics.
For a low-dimensional pattern additionally require mean 3D stress <=.25 and a
positive paired improvement over conditional shuffled-weight nulls AND physical
phase-scrambled controls at each size, with lower one-sided bootstrap bounds
using alpha=.05/6 across the six planned stress contrasts. Report all contrasts,
including negative effects. Thresholds are practical exploratory benchmarks, not
physical constants; do not combine them into a spacetime classifier.

A **limited GO for a geometric mechanism** further needs independently motivated
non-pair evidence and an explicitly stated mechanism with a falsifiable consequence
not already explained by the Hamiltonian/known correlations. Direct-J disagreement
alone never satisfies this. Record the leading commutator
`[X_i(t),X_j]=4 i t J_ij Y_i Y_j+O(t^2)` and verify it independently: all-to-all
nonzero J gives immediate direct interaction at first order. It neither supplies a
geometric light cone nor rules out every possible large-N effective description.
Without demonstrated dynamical locality/controlled geometric assumptions the
stronger claim is NO-GO or inconclusive, even if the proximity screen passes.

Failure: homogeneous symmetry, dependence on epsilon/ties, failed chain control,
negative controls with indistinguishable signatures, copying supplied adjacency,
unreliable perturbation response or size behavior. Inconclusive: inadequate power,
solver failures, mixed properties or absent mechanism. Never promote absence of
statistical significance into equality or a universal impossibility theorem.

## Feedback decision made before outcomes

Omit Phase 7. No independently justified autonomous feedback law is supplied by this
fixed-coupling TFIM model. Updating J from measured MI would introduce an external
classical controller, an unprovided measurement protocol/backaction and a nonlinear
state-dependent rule. There is no prespecified conservation law or new physical
mechanism to test. Adding one merely to encourage a graph would not answer this
experiment. This omission is independent of the primary results.

## Resources, streams and reproducibility

Master seeds: smoke 61001; pilot 61002; calibration 61003; primary batches
{61101,61201,61301}; bootstrap 61401; audit 61501. Derive separate SHA-256-keyed
NumPy SeedSequences using a versioned `quantum-v1` namespace plus phase, family,
n, realization, task and parameters. Never use Python's process-randomized hash.
No function defaults to a primary stream. Persist semantic stream keys and seeds.

Timing-only pilot: execute complete representative realization bundles at n=6,8,10
on the pilot stream (including solver, reductions, inference, perturbations,
scrambles and null calculation); record only elapsed times, peak memory, numerical
validity and operation counts. Do not print or inspect scientific observables.
Choose the largest R in {8,4,2} whose conservative projected complete primary
runtime, including a factor-two margin, is <=20 minutes on one worker. Hard cap
45 minutes, peak resident memory 2 GiB. If even R=2 fails, stop and amend the protocol
using resource evidence before primary data. No family/size dropping. Keep BLAS
thread count one. Timing variations do not authorize changing scientific criteria.

Use separate ignored pilot/smoke directories. Commit the workload decision and
implementation before primary execution; require a clean tracked tree. Archive
compressed machine-readable states/couplings/measurements, JSON metadata, CSV
summaries, figures and a SHA-256 manifest in `docs/experiments/quantum-information-v1`.
Record package/platform versions without personal paths, baseline/source/protocol
commits, source hashes, stream namespaces and runtime. Publication may add report
and audit code but must identify the exact generating commit. Re-run the full
scientific workload from its frozen source in an isolated environment; compare
scientific outputs excluding runtime/provenance fields, and document numerical
rather than byte equivalence where floating-point archives require it.

Tests: analytic normalization/partial traces/entropy; Bell/GHZ/AND; arbitrary local
unitary MI invariance; transported relabeling; Hamiltonian versus independent Kronecker
construction; dense versus sparse eigenpairs and residuals; infinitesimal commutator;
MDS/triangle/degeneracy; tie-safe permutation equivariance; stream isolation;
bootstrap algebra/coverage; artifact replay and hash validation. Preserve inherited
tests. Add bounded Experiment 6 CI smoke, never the full scientific workload.
Run the full test suite and one end-to-end reproducible CLI before each commit.

## Reporting and decision

Publish every registered model/control, numerical failure and failed criterion.
Answer the user's A–J questions explicitly, distinguishing established mathematics,
reproduced mechanisms, finite numerical evidence and any original deduction.
Update README, roadmap and research log; push the branch and open PR titled
**Experiment 6: Quantum information and emergent locality** into main; never merge.
