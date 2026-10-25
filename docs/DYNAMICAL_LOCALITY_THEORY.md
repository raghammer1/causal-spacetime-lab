# Experiment 7: theory of dynamical quantum links and operational locality

This document precedes the primary experiment. It distinguishes published findings,
exact deductions for the specified finite model, numerical questions, and unresolved
physical interpretation. The model is a graphity-inspired test, not a proposed
replacement for quantum gravity. No novelty or priority claim is made for these
mechanisms or elementary deductions. The protocol fixes the workload and decision
rules; equations below do not depend on favorable numerical outcomes.

## 1. What the original literature establishes

The four requested papers were examined in their original full-text arXiv versions.
Their Hamiltonians, approximations and meanings of locality differ from ours.

- **Konopka, Markopoulou and Severini (2008).** Their valence energy explicitly
  favors a chosen degree, while weighted closed-path terms favor specified loop
  scales. The honeycomb example selects degree three and compares candidate graphs
  and local perturbations; Section III calls the true-ground-state identification
  a conjecture. Narrow periodic arrangements can gain energy from winding loops.
  Their graph-changing moves themselves have local-path restrictions. These are
  evidence and stability calculations for selected regimes, not a theorem that
  generic permutation-invariant quantum dynamics selects a spatial manifold.
  [Original paper, Sections II–III](https://arxiv.org/pdf/0801.0861).

- **Hamma et al. (2010).** This model makes bosonic hopping links quantum degrees
  of freedom and exchanges particles with links. Its hard-core numerical study
  uses four vertices and examines matter–graph entanglement and observable
  relaxation. Equation 18 restricts link exchange to endpoints joined by another
  short path, with length two subsequently chosen: preservation of locality
  partly enters through that rule. Section IV's classical transition analysis
  is distinct from the quantum unitary calculation and identifies random-graph
  behavior. Trapping analogies use specially constructed graph sectors and
  additional assumptions; they do not derive Einstein dynamics or resolve a
  physical black-hole singularity. Our unconditional edge flips and Ising matter
  are different microscopic laws. [Original paper, Sections II–IV](https://arxiv.org/pdf/0911.5075),
  [journal DOI](https://doi.org/10.1103/PhysRevD.81.104032).

- **Caravelli and Markopoulou (2011).** Mapping edges to sites of the line graph
  turns graph occupation interactions into an Ising-like problem. Their
  low-temperature treatment uses a dominant valence coupling, truncated loop
  terms and mean-field approximations. The preferred low-temperature valence is
  supplied by the Hamiltonian parameter; it is not a derived spatial dimension.
  Equilibrium with a bath is assumed. Their discussion of the singular
  large-size, zero-temperature limit is not an exact phase diagram for our
  finite closed system. We use the incidence mapping as an algebraic observation,
  not their approximations as evidence for our dynamics.
  [Original paper, Sections IV–VI](https://arxiv.org/pdf/1008.1340),
  [journal DOI](https://doi.org/10.1103/PhysRevD.84.024002).

- **Wilkinson and Greentree (2015).** One-edge, nonunitary epitaxial optimization
  produces disconnected grains. Explicit energy comparisons show isolated cubes
  beating the tested extended honeycomb configurations for the original chosen
  parameters. A new hypervalence term rewards populations at several graph
  distances and changes those comparisons; even then, the optimization does not
  find the proposed honeycomb minimum. These results expose both energetic bias
  and optimizer limitations. They do not prove that every graphity Hamiltonian,
  or our full quantum evolution, must disconnect. We will not repair an adverse
  result by adding their connectivity preference.
  [Original paper, Sections II–V](https://arxiv.org/pdf/1506.07588),
  [journal DOI](https://doi.org/10.1103/PhysRevD.92.084007).

The older graphity statistical-mechanics analysis also distinguishes graph-counting
entropy from low-energy candidate comparisons; it gives reasons to include matter
when seeking extended configurations, not a universal guarantee that doing so is
sufficient. [Konopka (2008)](https://arxiv.org/abs/0805.2283).

Propagation bounds require assumptions about interaction supports and strengths.
An application to a specified topologically ordered spin model is not a generic
light cone theorem for arbitrary fluctuating links. In particular, the dimension
extrapolation in that paper is identified as a conjecture.
[Hamma et al. (2009)](https://arxiv.org/abs/0808.2495).
Our conclusions below instead follow directly from this experiment's operators.

## 2. Exact model and supplied microscopic structure

For N labeled matter qubits and M=N(N−1)/2 unordered link qubits,

\[
\mathcal H=(\mathbb C^2)^{\otimes N}\otimes
             (\mathbb C^2)^{\otimes M},\quad Q=N+M,
\qquad n_{ij}=(I-Z^e_{ij})/2,\qquad D_i=\sum_{j\ne i}n_{ij}.
\]

The labels identify subsystems; they are not coordinates. With all omitted tensor
factors equal to the identity, the only primary Hamiltonian is

\[
H=-h\sum_i X_i-g\sum_{i<j}n_{ij}Z_iZ_j
  -\Gamma\sum_{i<j}X^e_{ij}+\mu\sum_{i<j}n_{ij}
  +U\sum_i\frac{D_i(D_i-1)}2 . \tag{1}
\]

We take real coefficients, h,g,Γ,U≥0, and allow either sign of μ. We set ℏ=1;
time and energy have reciprocal simulation units. No physical length, light speed,
Newton constant or Planck scale is assigned.

Each n is a Hermitian projector; different occupations commute. Every product in
(1) consists of commuting Hermitian factors, so H is Hermitian. In the joint Z
basis it has a real diagonal and single-bit-flip matrix elements −h or −Γ.
An independently assembled dense matrix must verify this sign and tensor convention.

The model supplies more than an abstract collection of indistinguishable bits:
it supplies the tensor factorization, a distinction between matter and links,
which two matter factors each link addresses, and the incidence structure. Indeed,

\[
\sum_i {D_i\choose2}
=\sum_{\substack{e<f\\e\cap f\ne\varnothing}}n_en_f. \tag{2}
\]

Thus the congestion interaction is an interaction on the fixed line graph L(K_N).
It carries no spatial coordinates but is still a specified microscopic relation.
Setting g=0 alone does **not** make the links independent when U≠0. The genuinely
independent-link control sets both g=0 and U=0.

Sparsity, degree regularity and suppression of hubs can follow directly from μ and
U. Those effects must be described as energetic preferences, even when the quantum
state realizing them is computed rather than inserted.

## 3. Symmetry, conservation and the finite ground state

Let P_π simultaneously permute matter factors i→π(i) and link factors
{ i,j }→{ π(i),π(j) }. Relabeling each complete sum gives

\[
P_\pi H P_\pi^\dagger=H. \tag{3}
\]

This proves covariance and gives a numerical check independent of graph drawings.
The global matter flip F=∏_i X_i also commutes with H: it changes each Z_i's sign,
so every product Z_iZ_j is unchanged. Matter magnetization and individual link
occupations are not generally conserved. With L=Σ_e n_e,

\[
\dot n_e=i[H,n_e]=\Gamma Y^e_e,
\qquad \dot L=\Gamma\sum_eY^e_e. \tag{4}
\]

For e={i,j}, define the operator on its other factors

\[
A_e=\mu-gZ_iZ_j+U\sum_{k\ne i,j}(n_{ik}+n_{jk}).
\]

The terms containing n_e are exactly A_e n_e. Since A_e commutes with every
operator on e,

\[
\ddot n_e=2\Gamma^2 Z^e_e-\Gamma A_eX^e_e. \tag{5}
\]

Equations (4)–(5) test the sign convention. At Γ=0 each n_e is conserved and graph
sectors are frozen. At h=0 each matter Z_i is conserved. At g=0 the entire matter
sector evolves independently of the links, even if the links interact via U.
These special conservations must not be attributed to the generic model.

For time-independent H, unitary evolution conserves norm, every moment of H,
energy expectation and variance, global entropy, and probabilities in conserved
symmetry sectors. Subsystem entropy and link number may change. H is real, so
complex conjugation is an antiunitary invariance with K H K=H and K U(t)K=U(−t);
this is not an identification with the physical time-reversal law of real spins.

**Finite-ground-state theorem.** If h>0 and Γ>0, all off-diagonal entries of H
are nonpositive and the allowed flips connect every computational basis state.
Choose c greater than the largest diagonal entry. The nonnegative matrix cI−H
is irreducible. Perron–Frobenius therefore gives a unique largest eigenvector
with strictly positive entries; equivalently H has a unique strictly positive
ground vector. Its permutations and F transform it to positive ground vectors,
so uniqueness and normalization imply P_π|Ω⟩=|Ω⟩ and F|Ω⟩=|Ω⟩.

Consequences are exact for finite N: every labeled link has the same ground-state
occupation, every matter site has the same reduced state, and ⟨Z_i⟩=0. The Born
probability of every graph is strictly positive, because it sums positive squared
amplitudes over matter states. This last fact does not say that disconnected graphs
have appreciable probability. There is no exact sparse support at finite h,Γ>0.
At h=0 or Γ=0 irreducibility fails; the uniqueness conclusion need not hold.

A canonical finite-temperature state ρ_β=e^(−βH)/Tr(e^(−βH)) is likewise invariant
under permutations and F, and is full rank for finite β. Equilibrium state selection
is a separate assumption, not the destination of every quench.

## 4. What permutation symmetry does and does not forbid

If [ρ(0),P_π]=0, equations (1) and (3) imply [ρ(t),P_π]=0 for all t. Because the
permutation group acts transitively on links, p_ij(t)=Tr(ρ(t)n_ij) is independent
of the pair. A simultaneous covariant response experiment also gives identical
responses for every ordered distinct source–target pair. Therefore this symmetric
finite closed system cannot spontaneously acquire distinguishable **labeled**
expectation-value neighborhoods.

This is not a theorem that the graph distribution is independent-edge, uncorrelated
or disconnected. For example, the uniform classical mixture over all labeled
N-cycles is permutation invariant, has p_ij=2/(N−1), and is supported entirely on
connected degree-two graphs. The uniform coherent superposition over those basis
graphs has the same Born probabilities. Such ensembles differ from G(N,p), despite
having the same one-link expectations. Higher joint probabilities must be studied.
This example is a mathematical counterexample, not a permitted primary preparation.

An exchangeable ensemble of independent but nonidentical randomly drawn link states
is invariant in distribution, while an individual preparation usually is not.
A labeled response pattern in one such preparation can inherit that asymmetry.
A graph observed by a measurement, a deliberately asymmetric preparation, a small
Hamiltonian perturbation, and spontaneous symmetry breaking in an infinite-system
limit are four different concepts. The first three cannot demonstrate the fourth.

## 5. Energy bounds and exactly solvable graph sectors

Write a basis configuration as matter signs s_i=±1 and graph G. Its diagonal energy is

\[
V(s,G)=\sum_{\{i,j\}\in E(G)}(\mu-gs_is_j)
         +U\sum_i {d_i\choose2}.
\]

For ferromagnetic g≥0, independently aligning each connected component attains

\[
\min_sV(s,G)=(\mu-g)|E(G)|+U\sum_i{d_i\choose2}=:v(G). \tag{6}
\]

For g>0 the minimizing matter assignments have 2^c choices, including isolated
vertices in the component count c. At g=0 every matter assignment minimizes V.
Let v_min=min_G v(G), W_max=N(N−1)(N−2)/2. Operator inequalities and basis-state
trial vectors give

\[
v_{\min}-hN-\Gamma M\le E_0\le v_{\min},
\quad \|H\|\le hN+\Gamma M+(g+|\mu|)M+UW_{\max}. \tag{7}
\]

The trial state |+⟩_matter^N⊗|0⟩_links^M also gives E_0≤−hN. The all-plus trial
state gives E_0≤−hN−ΓM+μM/2+UW_max/4. These are bounds, not eigenvalue certificates.
A small numerical residual establishes proximity to some eigenpair; identifying
the lowest one additionally requires the eigensolver's spectral targeting and
independent small-system checks.

At h=Γ=0, (6) is the exact classical ground optimization. Put a=μ−g. For U>0,

\[
v(G)=\sum_i\left[\frac a2d_i+\frac U2d_i(d_i-1)\right],
\quad \phi(d+1)-\phi(d)=a/2+Ud. \tag{8}
\]

An integer degree k is the unique pointwise minimizer when
−2Uk<a<−2U(k−1), provided 1≤k≤N−1. Realizability of the degree sequence matters.
For a>0 the empty graph is the unique minimizer. For −U<a<0, an edge incident
to a degree≥2 vertex can be removed to lower v, so ground graphs are maximum
matchings. For even N the matching conclusion also follows throughout −2U<a<0
from the attainable pointwise degree-one minimum. Equality endpoints permit ties.

For −4U<a<−2U and N≥3, every degree-two graph attains the pointwise lower bound.
A simple degree-two graph is a disjoint union of cycles of length at least three.
On **N=4 or5**, degree two forces C4 or C5. At N=6, C6 and C3⊔C3 have exactly equal
energy 6a+6U, although the latter is disconnected. Their Laplacian spectra differ:
C6 has {0,1,1,3,3,4}; two triangles have {0,0,3,3,3,3}. A ring on the smallest
sizes can therefore be forced by the supplied cost and the lack of alternative
small graphs. Neither its appearance nor its layout demonstrates a chosen physical
dimension. The classical equality need not persist once transverse terms are added.

Even the equilibrium graph weighting depends on the matter sector. At N=6 there
are (6−1)!/2=60 labeled six-cycles and (1/2)choose(6,3)=10 pairs of triangles.
For g>0 their aligned-matter multiplicities are two and four respectively.
Consequently the canonical β→∞ Gibbs state at h=Γ=0 in this strict degree-two
regime has connectivity probability 120/(120+40)=3/4. N=4,5 instead give one.
This is a derived classical-limit example, not the primary finite-field result.

### A stronger matching theorem at finite matter field

At Γ=0, fix a graph and diagonalize only its matter Hamiltonian. Removing edge ij
from degrees d_i,d_j changes the corresponding sector Hamiltonians by

\[
H_G-H_{G\setminus ij}=
 -gZ_iZ_j+[\mu+U(d_i+d_j-2)]I.
\]

If the edge touches a degree≥2 vertex, d_i+d_j−2≥1. Thus when μ+U>g, this difference
is positive definite. Its lowest energy is strictly greater, so no ground graph
can contain such an edge: all minimizing sectors are matchings, at any h≥0.
A dimer has matter ground energy −√(g²+4h²), while two isolated spins have −2h.
A matching with m edges consequently has

\[
E_m=-hN+m[\mu+2h-\sqrt{g^2+4h^2}]. \tag{9}
\]

If also μ<√(g²+4h²)−2h, maximum matchings minimize the full Γ=0 energy. With
h=g=U=1 and μ=.1 both strict inequalities hold. For N≥3 these graphs are
fragmented. Their number is N!/[2^m m!(N−2m)!], m=⌊N/2⌋. This is an exact,
all-N obstruction for this limiting regime, not an assertion about every Γ>0
state. Positive Γ coherently mixes graph sectors and restores the finite unique
symmetric ground state.

Likewise, μ>g and U≥0 imply the empty graph is the unique minimizing graph at
Γ=0, at any h. At U=0 and μ<−g, every added edge strictly lowers the sector
Hamiltonian, so the complete graph uniquely minimizes the graph sector.

### Independent links and large transverse fields

For g=U=0 the matter and each link factorize. A link has
H_e=μI/2−ΓX−(μ/2)Z, with Ω=√(Γ²+μ²/4). Its ground occupation and thermal occupation are

\[
p_0=\frac12\left(1-\frac{\mu}{\sqrt{\mu^2+4\Gamma^2}}\right),
\quad
p_\beta=\frac12\left(1-\frac{\mu}{2\Omega}\tanh(\beta\Omega)\right). \tag{10}
\]

The Born graph is exactly G(N,p) in those product equilibrium states. Starting
with all links off gives p(t)=(Γ²/Ω²)sin²(Ωt). With arbitrary product link states,
links remain independent but can have different probabilities; the appropriate
baseline is then a product Bernoulli graph, not necessarily homogeneous G(N,p).
Matter signalling between different vertices is identically zero in this control.

For fixed finite N, Γ→∞ makes link X polarization dominant and occupations tend
to 1/2; the limit is not a sparse classical graph. The joint large h,Γ limit
approaches the corresponding plus product. These are finite-N limiting statements.
At infinite temperature the full state is proportional to I and its Born graphs
are exactly G(N,1/2), regardless of the finite Hamiltonian coefficients.

## 6. The pre-outcome grid and its limitations

The analytically motivated primary grid holds h=g=U=1, takes μ∈{2,.1,−2}, and
Γ∈{.25,1}. This is six cells, not an optimization search.

| μ | Analytical reference | What is supplied |
|---|---|---|
| 2 | Empty graph at Γ=0 for every h | Cost suppresses all links |
| .1 | Exact maximum matchings at Γ=0,h=1 | Reward for isolated pair interactions plus congestion |
| −2 | Degree-two minimum at h=Γ=0 | A degree preference, including forced tiny rings |

None of these labels asserts the full finite-Γ result. In particular, .25 need not
be perturbatively small compared with the lowest sector energy difference. All
cells must remain in the registered cohort even if the labels poorly describe
the resulting state. Independent-link, frozen-graph and supplied-locality controls
are separate experiments with explicitly changed terms, not alternative primary
models selected after results.

The fixed coefficients do not define an established thermodynamic normalization.
There are O(N²) edge flips and a maximal O(N³) congestion term. A perturbation
small at fixed N need not be uniformly small as N increases. For example, the
norm of −ΓΣ_e X_e is ΓM, so a simple norm-based perturbation bound around frozen
graphs requires control of a growing quantity. Sparse occupation alone does not
supply that control. N=4,5, and any feasible N=6 cohort can test finite mechanisms,
not establish a continuum phase or a reliable dimension exponent.

## 7. Operational response is distinct from correlation

For an aged state ρ at a declared preparation time, apply a local unitary V_i to
matter source i, use exactly the same subsequent H in both branches, and define

\[
\rho_j^{(0)}(t)=\operatorname{Tr}_{\bar j}(U(t)\rho U(t)^\dagger),
\quad
\rho_j^{(V)}(t)=\operatorname{Tr}_{\bar j}
 (U(t)V_i\rho V_i^\dagger U(t)^\dagger),
\]
\[
R_{i\to j}(t)=\tfrac12\|\rho_j^{(V)}(t)-\rho_j^{(0)}(t)\|_1. \tag{11}
\]

For a qubit this is half the Euclidean separation of the two Bloch vectors, lies
in [0,1], and quantifies distinguishability of the intervention with access to j.
It is not mutual information and is not caused merely by initial entanglement.
For i≠j, invariance of the partial trace under V_i gives R(0)=0 even for entangled
states. At g=0 the matter evolution factorizes, so R(t)=0 for all t and i≠j.
These are required no-signalling sanity checks. A zero response for one selected
V or state does not rule out a signal using another intervention.

For identical local interventions and a permutation-invariant aged ρ, relabeling
both branches of (11) proves equality of all off-diagonal ordered-pair responses.
This equality survives nontrivial matter–link entanglement. It prohibits a labeled
unconditioned response neighborhood in that symmetric state, while leaving open
relational information in conditional joint observables.

### Direct operator influence and the quantum link factor

Using [Z,X]=2iY, the Heisenberg expansion gives, for i≠j,

\[
[X_i(t),X_j]=it[[H,X_i],X_j]+O(t^2)
           =4igt\,n_{ij}Y_iY_j+O(t^2). \tag{12}
\]

No expectation value may replace n_ij before taking this operator commutator.
Since n is a projector and the matter Pauli product is unitary,

\[
\|[X_i(t),X_j]\|=4|g||t|+O(t^2),
\quad
\operatorname{Tr}\rho\,[X_i(t),X_j]^\dagger[X_i(t),X_j]
 =16g^2t^2p_{ij}+O(t^3). \tag{13}
\]

The norm's leading coefficient is the same for every potential pair. The full
microscopic matter interaction support is complete, even if some state-dependent
responses are small. The state-RMS coefficient is 4|g|√p_ij; it is not 4|g|p_ij.
These diagnostics and the operational trace distance (11) have different meanings.
An effective low-energy locality bound would need a justified subspace or state
family and controlled leakage; it cannot be inferred from a sparse picture.

### Exact first derivative for the registered Pauli-Y intervention

For V_i=Y_i, define the Hermitian target operator
A_j=Tr_{\bar j}(n_ij Z_i ρ). Terms not involving i and j cancel after the partial
trace, and Y_i Z_i Y_i=−Z_i, giving

\[
\left.\frac{d}{dt}(\rho_j^{(Y)}-\rho_j^{(0)})\right|_0
 =-2ig[Z_j,A_j].
\]

Writing A_j=(a_0I+a_xX_j+a_yY_j+a_zZ_j)/2 yields

\[
R_{i\to j}(t)=2|g||t|\sqrt{
 \langle n_{ij}Z_iX_j\rangle_\rho^2+
 \langle n_{ij}Z_iY_j\rangle_\rho^2}+O(t^2). \tag{14}
\]

This exact formula uses the aged joint state, not merely its one-link occupation.
For a product preparation it reduces to
|g|p_ij|Δ⟨Z_i⟩|√(r_jx²+r_jy²)|t|. With every matter Bloch vector
(1/√2,0,1/√2), Y gives an orthogonal source state and the coefficient is |g|p_ij.
After aging, matter–link and matter–matter correlations generally invalidate this
last simplification. Joint correlators in (14), or an explicit qualification of
an occupation-only approximation, are needed for the direct-interaction control.
All-plus matter with X intervention would be an identity intervention; Z-polarized
targets can suppress the linear response. Neither is a useful generic locality test.

For initially all-off product links, the product coefficient vanishes. Two link
flips are needed to survive the link partial trace, followed by one matter-link
interaction. The first possible response is cubic. Equivalently, in the leading
Duhamel term p_ij(s)=Γ²s²+O(s³), and ∫_0^t p_ij(s)ds=Γ²t³/3+O(t⁴). For the tilted
matter product and Y intervention,

\[
R_{i\to j}(t)=|g|\Gamma^2|t|^3/3+O(t^4). \tag{15}
\]

This is an unaged t=0 product-state identity, not a prediction for intervention
after the registered aging period. Every pair has the same coefficient. A delayed
threshold crossing in this state is therefore not a distance-dependent light cone.

More generally, suppose a link-basis measurement or an explicit preparation gives
|G⟩ and the matter is the same independent tilted product. For an absent edge ij,
the direct edge-birth process contributes (2/3)gΓ²t³ to the target Bloch-Y difference.
If i and j are at graph distance at least three, or disconnected, no static path
can contribute at that order, so (15) is again the leading trace distance. To see
the support constraint, a static Ising path of length d needs d successive ZZ
commutators and d−1 intervening X-field commutators: a newly reached factor is Z,
which commutes with all further ZZ terms until the field rotates it. Its first
possible response order is therefore 2d−1. For distance two, both the new direct
edge and an existing two-step path can contribute at order three. The Γ-driven
process thus bypasses long distances in the measured snapshot.

This conclusion is conditional on the stated product matter preparation. Aged
conditional matter states generally are correlated. For them, the direct-birth
contribution is proportional to [Z_j,Tr_{other matter}(Z_iρ_m|G)] and can vanish;
its isolated trace-distance coefficient is
(2|g|Γ²/3)√(⟨Z_iX_j⟩²+⟨Z_iY_j⟩²). Other path contributions must be combined at the
density-matrix level, not by adding trace distances. A fresh link measurement,
conditioned continuation and frozen-Γ comparison are distinct operational protocols.

## 8. Closed evolution, ground states and link measurement

A closed finite system evolves by phases in its energy eigenbasis. It cannot
universally cool to its ground state: energy probabilities are fixed and unitary
maps preserve distances between full states. Observable relaxation, entanglement
with unobserved factors, and finite-time plateaus can occur without cooling. A
prepared ground state is stationary up to phase; its structural properties belong
to an independently selected equilibrium state, not a graph built by its own
subsequent unperturbed evolution. Simulation t is external throughout.

For a pure state expanded as Σ_{s,G}ψ(s,G)|s,G⟩, the exact graph Born probability is

\[
p(G)=\sum_s|\psi(s,G)|^2. \tag{16}
\]

Expected edge count, component distributions and other diagonal graph statistics
can be summed over this finite distribution without Monte Carlo measurement error.
Saved sampled configurations are additional illustrations or specified finite-shot
measurements. They must not replace the exact distribution when it is feasible.
The variance of the number of active links includes covariances:
Var(L)=Σ_e p_e(1−p_e)+2Σ_{e<f}(⟨n_en_f⟩−p_ep_f).
It is not generally binomial.

Conditioning on outcome G projects the joint state and renormalizes it. Ignoring
the outcome produces dephasing Σ_G Π_GρΠ_G. Neither operation generally preserves
future dynamics when Γ≠0. Conditioning may also alter the matter state through
matter–link entanglement. A frozen-graph continuation is a further intervention
changing the Hamiltonian; it is not the original unconditional experiment.

Independent graph measurements on separately prepared copies at times t and t'
do not track one graph's history. Their expected edge overlap is
Σ_e p_e(t)p_e(t'), which need not measure memory. Claims of quantum temporal
persistence require a defined two-time correlator or an explicit sequential
measurement instrument including its backaction. Stability of one-time probability
distributions should be described only as ensemble stability.

Von Neumann entropy of a reduced state is different from Shannon entropy of a
chosen measurement. Pure |+⟩_links^M has zero quantum entropy but uniform graph
measurement entropy M bits. For a pure joint matter–link state, Schmidt
singular values give S(matter)=S(links); there is no need to construct the full
link density matrix. Pair mutual information measures total correlation, not
signalling or solely entanglement. Experiment 6's Bell/GHZ counterexamples and
calibration failures remain applicable; changing the model does not erase them.

## 9. Controls, statistical units and geometric limits

A static chain is a supplied-locality positive control. Nested commutators under
its finite-range Hamiltonian can reach a target only after sufficient support
expansion; extra cancellations can delay a selected observable further. Validation
must distinguish this combinatorial support statement from a fitted physical
velocity. A complete homogeneous fixed graph tests uniform direct influence.
Disconnected fixed components give exactly zero cross-component response under
a factorized Hamiltonian, yet must fail coherent-structure requirements.

Frozen random graphs require a specified ensemble: matched density, exact edge
count, or exact degree sequence are different nulls. At these tiny sizes, exact
enumeration may be preferable to a poorly mixing edge-swap process. A degree-matched
null can have only one isomorphism class, especially the degree-two N=4,5 cases;
then it has no discriminatory power for claims about higher geometry. A difference
from a density-only null can be explained entirely by supplied degree preferences.

Graph Laplacian zero-eigenvalue multiplicity equals the component count. Distances,
balls, clustering, loops and spectra are combinatorial observables. No short fit
across two or three radii can identify a continuum spectral or spatial dimension.
Disconnected components cannot be reinterpreted as a single connected manifold
by arranging them nearby on a page. Thresholding homogeneous occupation weights
can create arbitrary graphs from roundoff or a tie-breaking rule.

The independent stochastic unit is a newly sampled preparation or a separately
specified disorder draw. Source–target pairs, time points, measurement shots,
perturbations and matched controls within it are dependent observations. A
deterministic symmetric state has no independent ensemble uncertainty merely
because it has many vertices. Exact sums over Born outcomes have numerical error,
not a fictitious sampling standard error. Finite-shot error and between-preparation
uncertainty must be reported separately.

Experiment 6's nominal 95% bootstrap covered only 365/400 independent calibration
means. Reusing that procedure without a new justification cannot support a formal
GO. Any selected uncertainty method must be independently calibrated or bounded
analytically, use complete cohorts, and preserve failed calibration. Repeating a
seeded computation checks reproducibility, not independent physical evidence.

## 10. Predictions and unresolved questions before computation

Exact checks include Hermiticity; joint permutation covariance; norm, energy and
F conservation; nonconservation (4); symmetric one-link expectations and ordered-pair
responses; the Γ=0 matching and degree-two counterexamples; independent-link formula
(10); no-signalling at g=0; commutator coefficients (12)–(13); and the correct
state-specific operational slopes (14)–(15). These derive from the selected law
and must not be advertised as discoveries of spacetime.

Numerical questions remain: the full correlated Born distribution at finite Γ;
fragmentation, regularity and preparation dependence; stable windows of ensemble
structure; conditional versus unconditional operational response; and comparison
with precisely matched frozen/random controls. No theorem above determines these
finite outcomes. A successful finite comparison would still need a controlled
large-N state family, an independent operational notion of distance, suppression
bounds uniform on relevant scales, persistent structure without post-selection,
and a justified coarse-graining before it could support geometric emergence.

The available sizes cannot establish thermodynamic symmetry breaking, broad
scale-dependent propagation, continuum dimension, Lorentz invariance or a
Lorentzian metric. Einstein dynamics additionally requires an effective action or
field equations, suitable conserved stress-energy, symmetries and an empirical
mapping of units. This model contains no controlled black-hole sector, horizons,
semiclassical gravity or singularity calculation. It offers no substantive result
about physical black holes. The seven-experiment synthesis must close the program
according to the registered evidence, without automatically inventing a next model.

## 11. Pre-primary audit of the tiny-size degree-null gate

Exhaustive graph classification and an independent counting argument identified a
limitation of the registered extra GO condition before primary generation. At N4,
conditioning on the full labeled degree vector fixes connectivity. At N5 the only
degree classes allowing both connected and disconnected realizations have degree
multiset (2,2,2,1,1). For each fixed assignment of its two degree-one vertices,
there are six labeled P5 paths (the three internal vertices can be ordered in3!
ways) and one C3 disjoint union K2. The degree-preserving uniform null consequently
has connectivity6/7 in each such class. Other classes have fixed connectivity:
a disconnected five-vertex graph with no isolated vertex has component sizes2+3;
K2 union P3 has only three edges and cannot also realize a connected graph.

It follows for any law P that

    P(connected) − Q_degree(connected) = [P(P5) − 6 P(C3 union K2)] / 7 <= 1/7.

The registered connectivity advantage >=.1 therefore requires P(P5)>=.7. This
is a strong finite-size path-selection constraint imposed by the GO screen, not
a discovery of dimension or a neutral universal definition of geometric order.
The threshold is preserved; the limitation is disclosed before outcomes. The
primary C/L/T/D necessary-screen failure does not depend on this additional gate.
No observed failure of the path-selective gate can establish a general physical
no-go. At larger N the degree classes have different combinatorial freedom.
