# Experiment 6: quantum information before spacetime — theory

This document records the pre-primary mathematical design of Experiment 6.
It separates mathematical deductions from the finite-system hypotheses
registered in [the protocol](QUANTUM_EMERGENCE_PROTOCOL.md). Numerical outcomes belong
in [the results](QUANTUM_EMERGENCE_RESULTS.md). The models are educational quantum
spin systems, with a supplied tensor factorization and Hamiltonian, not a theory of
quantum gravity. All entropies below are in bits; logarithms denoted `ln` are natural.
We set the energy scale and Planck's constant to one.

## 1. Four claims that require different evidence

1. **Correlation structure:** a state, together with specified subsystems, determines
   a weighted graph of statistical dependence. This is an exact construction.
2. **Geometric interpretation:** some of those graphs admit a stable, approximately
   low-dimensional metric representation. This requires tested assumptions about the
   state family, metric, coarse-graining and reconstruction ambiguities.
3. **Dynamical locality:** independently specified observables and dynamics propagate
   approximately locally in that geometry, with controlled errors across scales.
   Static proximity or a sparse drawing is insufficient.
4. **Physical spacetime:** the construction has a controlled continuum description,
   temporal and causal structure, appropriate symmetries, matter dynamics and empirical
   content. None of the finite calculations here establishes this claim.

The tensor product `H = (C²)^{⊗N}` already supplies distinguishable subsystems and the
meaning of a local operation. It supplies no coordinates, but is additional structure
beyond an abstract vector in a Hilbert space. Changing that factorization can change
entanglement. A global unitary can send any normalized pure vector to a chosen product
vector; interpreting this as a change of subsystem algebras illustrates why the
factorization cannot be inferred from a state vector alone without further conditions.

## 2. What the motivating literature establishes

**Holography.** Ryu and Takayanagi proposed the leading classical, static holographic
relation `S(A) = Area(γ_A)/(4 G_N)` in natural entropy units, with an appropriate bulk
minimal surface anchored on the boundary region. In bits the right-hand side is
divided by `ln 2`. Their 2006 paper checks the AdS₃/CFT₂ interval result and considers
higher dimensions and temperature. Its premises include a gravity dual and a bulk
geometric description; it is not an arbitrary-qubit embedding theorem.
[Ryu–Takayanagi, 2006, §§I–V](https://arxiv.org/abs/hep-th/0603001).
Later gravitational replica arguments support this prescription under their
semiclassical assumptions; time dependence and quantum corrections require additional
constructions. These are established results within specified holographic regimes,
not a derivation of gravity for this lab's spin models.
[Lewkowycz–Maldacena, 2013](https://arxiv.org/abs/1304.4926),
[Hubeny–Rangamani–Takayanagi, 2007](https://arxiv.org/abs/0705.0016),
[Faulkner–Lewkowycz–Maldacena, 2013](https://arxiv.org/abs/1307.2892).

**Entanglement and connected bulk geometry.** Van Raamsdonk's argument uses CFT
states with a holographic interpretation, including the thermofield double. It
combines an entropy/area relation with a heavy-operator geodesic approximation to
correlators. Decreasing entanglement then changes connectivity and separation in the
dual interpretation. The essay itself warns that a geometric description can fail
before entanglement reaches zero. This motivates a conditional relationship, not the
universal rule “entangled qubits make spacetime.” The inspected version is the 2010
essay with its July 2025 reference update.
[Van Raamsdonk, §§“Classical connectivity” and “A disentangling experiment”](https://arxiv.org/abs/1005.3035).

**Quantum Graphity.** Konopka, Markopoulou and Severini put quantum degrees of freedom
on possible **edges**, allowing adjacency itself to change. Valence and loop terms
favor particular graph structures. Their 2008 calculations compare candidate graph
energies and give heuristic stability evidence for a locally hexagonal state;
a proof of the global ground state, the transition and an extended three-dimensional
phase remain open in that paper. A wrapped tube can beat the flat candidate, illustrating
why local order does not determine global geometry. Their discussion also identifies
the unresolved interpretation of an external cooling reservoir. Our node-qubit models
have fixed numerical couplings and do not reproduce that mechanism.
[Konopka–Markopoulou–Severini, 2008, §§II, III, VI](https://arxiv.org/abs/0801.0861).

**Bulk-information reconstruction.** Cao, Carroll and Michalakis assume a tensor
factorization and special, approximately redundancy-constrained states. Their cut
relation is defined in §8 below. They choose an information-to-edge-length function,
take shortest paths, and examine embeddings; their construction explicitly need not
produce a smooth manifold for every state. Lorentz symmetry and a general physical
Hamiltonian are not derived. Consequently our direct-distance counterexamples test
an unrestricted ansatz, not a refutation of their conditional program. Their spatial
curvature argument should not be identified with verified Einstein dynamics here.
[Cao–Carroll–Michalakis, 2017, §§II–III, V–VI](https://arxiv.org/abs/1606.08444).

**Unverified in this experiment:** generic emergence of locality from entanglement,
an autonomous mechanism selecting manifold states, Lorentz invariance, a gravitational
continuum limit, and a relation to real black holes. Numerical resemblance cannot
promote any of these to an established claim.

## 3. States, reductions and entropy identities

For `ψ ∈ C^{2^N}`, normalization means `Σ_x |ψ_x|² = 1`. Its density matrix is
`ρ = |ψ⟩⟨ψ|`. A mixed density matrix is Hermitian, positive semidefinite and trace one.
For a retained subsystem A and complement R, use a fixed documented bit/tensor order:

```math
(\rho_A)_{a,a'} = \sum_r \rho_{ar,a'r}.
```

For a pure state, reshape its amplitudes into `M_{a,r}=ψ_{ar}` after the appropriate
axis permutation. Then `ρ_A = M M†`, which is a separate implementation route from
tracing a full density matrix. Positivity follows from `v†ρ_Av=||M†v||²≥0`; its trace
is the original norm. The nonzero eigenvalues of `MM†` and `M†M` coincide by the
singular-value decomposition. Therefore a pure bipartition obeys `S(A)=S(R)`.

The von Neumann entropy is

```math
S(\rho)=-\sum_a\lambda_a\log_2\lambda_a,\qquad 0\log_2 0:=0.
```

It lies in `[0, log₂ d]` for a density matrix on dimension d. Nonnegativity follows
from `0≤λ≤1`; the upper bound follows from the nonnegativity of relative entropy
against `I/d`. Roundoff clipping must use a declared tolerance; materially negative
eigenvalues or incorrect traces are numerical failures, not physical effects.

For two subsystems, define

```math
I(A:B)=S(A)+S(B)-S(AB)
      =D_2(\rho_{AB}\Vert\rho_A\otimes\rho_B),
\quad D_2(\rho\Vert\sigma)=\operatorname{Tr}\rho
       (\log_2\rho-\log_2\sigma).
```

The identity uses `log(ρ_A⊗ρ_B)=log ρ_A⊗I+I⊗log ρ_B` on the support and the
definition of a partial trace. The support of `ρ_AB` is contained in the product of
the marginal supports: a vector with zero marginal probability has zero joint
probability, and positivity then forces the corresponding matrix rows and columns
to vanish.

For completeness, let `p_i` diagonalize ρ, `q_j` diagonalize σ, and
`w_ij=|⟨i|j⟩|²`. Concavity of `ln` gives

```math
D_{\mathrm{nat}}(\rho\Vert\sigma)
 =\sum_i p_i\left(\ln p_i-\sum_j w_{ij}\ln q_j\right)
 \geq\sum_i p_i\ln\frac{p_i}{s_i}\geq0,
 \qquad s_i=\langle i|\sigma|i\rangle.
```

The last step is the classical log-sum inequality, with both distributions
normalized. Equality requires matching distributions and equality in the concavity
step on the support, hence `ρ=σ`. Singular cases follow by restriction to the support
or a positive regularization limit. Thus `I≥0`, and `I=0` exactly when the joint
state is a product; MI measures total dependence, including classical dependence.

To bound MI above, purify AB by C. Subadditivity, already implied by relative-entropy
positivity, gives `S(B)=S(AC)≤S(A)+S(C)=S(A)+S(AB)`. Interchange A and B to obtain
`S(AB)≥|S(A)−S(B)|`. Consequently

```math
0\leq I(A:B)\leq2\min\{S(A),S(B)\},\qquad 0\leq I(i:j)\leq2
```

for qubit pairs. An entropy `S(A)` measures entanglement with the complement when the
**whole** state is pure. A mixed two-qubit reduction can have positive MI and no
entanglement between those two qubits.

For bounded local operators define
`C(A,B)=⟨A⊗B⟩−⟨A⟩⟨B⟩`. Put `Δ=ρ_AB−ρ_A⊗ρ_B`. Hölder's inequality gives
`|C|≤||Δ||₁||A||||B||`. Combining with quantum Pinsker's inequality yields

```math
I(A:B)\geq\frac{\|\Delta\|_1^2}{2\ln2}
 \geq\frac{|C(A,B)|^2}{2\ln2\,\|A\|^2\|B\|^2}.
```

The factor `ln 2` converts natural logarithms to bits. This is a bound, not an equality
identifying distance with correlation. The lattice area-law results in the same
work assume lattice structure and appropriate interactions; they do not establish
a converse from an information graph to a spatial Hamiltonian.
[Wolf–Verstraete–Hastings–Cirac, 2008, Eq. (5)](https://arxiv.org/abs/0704.3906).

## 4. Pair entanglement and invariances

We use negativity as an independently informative pair quantity:

```math
(\rho^{T_B})_{ab,a'b'}=\rho_{ab',a'b},\qquad
\mathcal N(\rho)=\frac{\|\rho^{T_B}\|_1-1}{2}
 =\sum_{\mu_k<0}|\mu_k|.
```

The last equality follows because the partial transpose is Hermitian with trace one.
Logarithmic negativity, when reported, is `E_N=log₂(1+2𝒩)`. A separable state
`Σ_k p_k ρ_A^k⊗ρ_B^k` has positive partial transpose, so its negativity vanishes.
For **two qubits**, the converse holds by the positive-partial-transpose separability
theorem; it does not hold for arbitrary larger bipartitions.
[Vidal–Werner, 2002, Eqs. (1)–(2)](https://arxiv.org/abs/quant-ph/0102117),
[Horodecki–Horodecki–Horodecki, 1996](https://arxiv.org/abs/quant-ph/9605038).

A pure two-qubit state's Schmidt weights are `λ,1−λ`; its partial-transpose
eigenvalues are `λ,1−λ,±√(λ(1−λ))`. Hence `0≤𝒩≤1/2`. Convexity of the trace norm
extends that bound to mixtures. This supplies exact Bell/product unit checks.

Under a product of single-qubit unitaries, reductions transform by conjugation, so
their spectra, entropies and MI are invariant. For a pair, partial transposition
conjugates by `U_A⊗U_B*`; its spectrum and negativity are invariant as well.
Individual `ZZ` connected correlations need not be invariant: they depend on the
chosen operator axes. Relabeling qubits permutes every pair matrix, with no change
to scalar invariants. Arbitrarily resolving tied neighbor scores by label would
break this covariance and introduce structure absent from the state.

## 5. The Hamiltonians and what they supply

The common family is

```math
H(J,h)=-h\sum_{i=1}^{N}X_i-\sum_{i<j}J_{ij}Z_iZ_j,
\qquad h>0,\quad J_{ij}=J_{ji},\quad J_{ii}=0.
```

The prespecified field sweep is `h=0.5,1,2`, and sizes are `N=6,8,10`, subject to the
protocol's timing-only workload rule. These are transverse-field Ising Hamiltonians.
They introduce quantum kinematics, interactions and an external evolution parameter.

| Family | Supplied coupling information | Interpretation |
|---|---|---|
| A: symmetric all-to-all | `J_ij=1/(N−1)` | Exact permutation symmetry; no distinguished vertex pair. |
| B: heterogeneous all-to-all | Independent `G_ij~Normal(0,1)`, `J_ij=G_ij/√(N−1)` for `i<j` | No supplied spatial coordinates, but a nonuniform interaction matrix is present. |
| Positive control: chain | Positive adjacent bonds uniform on `[0.8,1.2]`, other bonds zero | Locality is supplied by the Hamiltonian, then labels/order are hidden from inference. |

The A normalization fixes each row sum to one; the B normalization fixes the expected
sum of squared couplings in a row to one. The chain has bounded coordination. These
choices avoid a trivial growth of the indicated interaction scales with N; they do
not make the three ensembles physically equivalent. Field/interaction competition
can differ. The registered sizes use independent coupling samples. Comparing their
summary distributions does not define a quantum growth process or a continuum limit.

Only quantum states or derived information matrices are supplied to reconstruction.
Known chain labels and J are retained for independent evaluation. Successful chain
recovery demonstrates reconstruction of supplied structure. In Model B, association
with `|J|` measures how much inferred proximity tracks already supplied interactions.
A weak association alone would not establish autonomous locality: multistep
correlations and frustration can also obscure direct couplings.

### 5.1 Finite-system symmetry theorem

In the computational basis, all off-diagonal matrix elements of H are either `−h`
(one-bit flips) or zero. Their support is a connected N-dimensional hypercube,
regardless of the signs of J. Choose `c>max_x H_xx`. The matrix `cI−H` is
nonnegative and irreducible. Perron–Frobenius gives a simple largest eigenvalue with
a strictly positive eigenvector, which is the unique ground state of H.

For Model A, every subsystem permutation P commutes with H. Uniqueness implies
`Pψ₀=e^{iθ_P}ψ₀`; choosing the ground vector strictly positive forces the phase to
one. A permutation sending any unordered pair to another therefore identifies the
two reduced states up to their tensor ordering. All pair MI and negativities are
equal. Model A's exact ground state has **no distinguished pair neighborhoods**.
The same conclusion holds during its unitary evolution from a permutation-invariant
initial density matrix, since the propagator commutes with each P.

This theorem is for finite N and `h>0`. It does not exclude symmetry breaking after
a suitable infinite-size limit, a symmetry-breaking field or conditioning on a
measurement. Those are different experiments. Numerical asymmetry within solver
error cannot be counted as spontaneous locality. The omitted `h=0` case can be
degenerate and does not satisfy the irreducibility argument.

Every family also commutes with the global bit flip `F=∏_iX_i`. Positivity forces
the unique ground state into the even sector. An iterative eigensolver started in
that sector cannot discover an odd-sector first excitation: a reported gap therefore
requires full-sector validation, not just a small residual for one eigenvector.

### 5.2 Exchangeability and an exact interaction ambiguity

Model B is permutation invariant **in distribution**. A particular random coupling
matrix and its ground state generally are not permutation symmetric. Ensemble
exchangeability does not forbid neighborhoods in individual realizations; neither
does it explain them geometrically.

For signs `s_i∈{−1,+1}`, let `U_s=∏_{i:s_i=−1}X_i`. Conjugation yields

```math
U_s H(J,h)U_s^\dagger=H(J',h),\qquad J'_{ij}=s_i s_j J_{ij}.
```

Thus gauge-related sign choices have locally unitarily equivalent unique ground
states and identical pair MI and negativities. These data cannot identify individual
bond signs without additional operator/basis information. Comparing with `|J|`
respects this ambiguity. Products of signs around loops are unchanged by this
transformation; the argument does not identify all frustrated coupling matrices.

### 5.3 A controlled weak-interaction limit

There is a direct interaction-copying mechanism even without an input geometry.
At fixed finite N and h, introduce a mathematical expansion parameter λ multiplying
all J. The unperturbed ground state is `|+⟩^{⊗N}`. A term `Z_iZ_j` flips two X-basis
spins, with excitation energy `4h`, so ordinary nondegenerate perturbation theory
gives

```math
|\psi_\lambda\rangle=|+\cdots+\rangle
 +\lambda\sum_{i<j}a_{ij}|-_{i},-_{j},+_{\mathrm{rest}}\rangle
 +O(\lambda^2),\qquad a_{ij}=J_{ij}/(4h).
```

Let `r_i=Σ_{k≠i}a_ik²`. The small one-qubit eigenvalue is `λ²r_i+O(λ³)`.
In a two-qubit reduction, the direct pair amplitude is coherent with the dominant
vector; the total weight of the eigenvalues generated by tracing out external spins
is `λ²(r_i+r_j−2a_ij²)+O(λ³)`. This follows by grouping the first-order amplitudes
by their external flipped spin: the single-flip block has diagonal weights
`Σ_{k≠i,j}a_ik²` and `Σ_{k≠i,j}a_jk²`. Its off-diagonal entries change its spectrum,
but not its trace. Consequently the leading logarithmic entropy terms give

```math
I_\lambda(i:j)=-2\lambda^2a_{ij}^2\log_2(\lambda^2)+O(\lambda^2).
```

This is an asymptotic statement as `λ→0`, at fixed N and couplings, with all energies
in the chosen units. Direct bond strengths determine the leading pair-MI hierarchy
when their squared magnitudes are distinct. If `J_ij=0`, the leading logarithmic
term vanishes, but indirect correlations can still enter the remainder. This
derivation does not assume that any registered h value is already in the asymptotic
regime, and its error is not claimed uniform in N. It explains why successful
recovery of an interaction graph can occur without the emergence of new locality.

## 6. Exact and stochastic controls

| Control | Exact information where available | What it tests |
|---|---|---|
| Pure product | All pair MI and negativity zero; every subsystem entropy zero. | An algorithm must not infer informative proximity from numerical noise or a regularizer. |
| Disjoint Bell pairs | Partner MI `2`, negativity `1/2`; other pair MI and negativity zero. | Maximal pair entanglement does not make a connected manifold. |
| GHZ, `N≥3` | Pair MI `1`, pair negativity `0`; every nonempty proper subsystem entropy `1`. | Classical pair dependence can accompany global entanglement. |
| Haar pure states | Exact ensemble entropy expectations below; no spatial Hamiltonian is supplied. | Global entanglement need not select strong pair neighborhoods. |
| Random phases in the computational basis | Amplitude probabilities and all diagonal-operator expectations remain fixed. | Separates diagonal correlations from coherence-dependent information. |
| Product local unitaries / label permutations | MI and negativity preserved, with appropriate index permutation. | Tests invariance, not a new independent physical realization. |

For a Bell state `( |00⟩+|11⟩ )/√2`, the one-qubit states are maximally mixed,
the pair is pure, and the partial-transpose eigenvalues are `1/2,1/2,1/2,−1/2`.
This proves the table's values. Tensor products factor all unrelated pair reductions.

For GHZ, tracing even one qubit annihilates the off-diagonal terms between
`|0…0⟩` and `|1…1⟩`. Every proper reduction is the equal mixture of those two
product basis vectors. Its entropy is one, and its two-qubit reduction is separable.
The fully classical mixture of the two global strings has exactly the same **every
proper-subsystem** density matrix as pure GHZ. Local data cannot distinguish their
global coherence, although the pure and mixed states have different total entropy
and global entanglement. This is an exact identifiability obstruction.

For a Haar pure state on dimension `ab`, with `a≤b`, the Page expectation is

```math
\mathbb E S_a=\frac{H_{ab}-H_b-(a-1)/(2b)}{\ln2},
\qquad H_m=\sum_{k=1}^m\frac1k.
```

Page proposed this formula and Sen proved it. For `N≥4`, linearity of expectation
therefore gives `E I(i:j)=2 E S_{2,2^{N−1}}−E S_{4,2^{N−2}}`. No independence
between those entropies is required. This is an ensemble expectation, not a promise
about each finite draw or a replacement for measured uncertainty. It allows a
calibration check whose answer was not fitted to the primary data.
[Page, 1993](https://arxiv.org/abs/gr-qc/9305007),
[Sen, 1996](https://arxiv.org/abs/hep-th/9601132).

Random phase scrambling is `ψ_x→e^{iθ_x}ψ_x` with independent phases. It is usually
a nonlocal diagonal unitary, not a local change of basis and not equivalent to
resampling a Haar state. It preserves `|ψ_x|²`, hence all Z-diagonal correlations,
but can alter reduced coherences and pair MI/negativity. Its effect must be measured;
there is no theorem that it always destroys geometric-looking structure.

## 7. Information distances: exact failures and valid constructions

The direct candidate for distinct vertices is

```math
d_{ij}=-\ln(I(i:j)/2),\quad d_{ii}=0.
```

It is symmetric and nonnegative where finite. The normalization two is the qubit
MI upper bound, not a fitted physical length. Multiplication by any overall length
scale leaves rank ordering unchanged and does not supply a calibrated ruler.

**Identity fails:** a Bell pair has `I=2`, hence `d_ij=0` for different qubits.
**Finiteness fails:** independent pairs have `I=0`, hence `d_ij=+∞`. Treating this
as a disconnected extended distance is possible, but must not silently insert
finite geometry. **Triangle inequality fails even for pure finite-qubit states.**

An explicit five-qubit witness, in order A,B,C,R₁,R₂, is

```math
|\Psi\rangle=\frac12\sum_{a,c\in\{0,1\}}
 |a,\,a\wedge c,\,c,\,a,\,c\rangle.
```

The four summands are orthogonal, so the state is normalized. Tracing R₁,R₂ leaves
independent fair A,C and the classical variable `B=A AND C`. Then

```math
S(A)=S(C)=1,\quad S(B)=h_2(1/4),\quad
S(AC)=2,\quad S(AB)=S(BC)=3/2,
```

because the AB and BC probability lists are `(1/2,1/4,1/4,0)`. Therefore

```math
I(A:C)=0,\qquad I(A:B)=I(B:C)=h_2(1/4)-1/2
 =0.311278124\ldots.
```

Thus `d_AC=∞` while `d_AB+d_BC` is finite. Padding with a product qubit gives
the same witness at N=6. This example requires no sampling, fitting or Hamiltonian.

For the regularization `d^ε_ij=−ln(max(I_ij,ε)/2)`, the AC triangle still fails
whenever `ε<[h₂(1/4)−1/2]²/2≈0.04845`. In particular it fails for every small
regularizer in the protocol. A regularizer cannot be interpreted as measured
correlation. Report floor hits, ties, triangle defects and sensitivity separately.

For any finite connected undirected graph with **strictly positive** edge lengths,
shortest-path distances are a metric: path reversal gives symmetry, positive edges
give positive distance between distinct vertices, and concatenating minimizing paths
gives the triangle inequality. Allowing zero edges gives only a pseudometric until
zero-distance vertices are quotiented. Disconnected components require infinite
distance or separate analysis. The shortest-path operation repairs triangle
inequalities by construction; that repair supplies no evidence of physical locality.

### 7.1 Euclidean embedding diagnostics

For a finite symmetric distance matrix D with zero diagonal, let
`C=I−11ᵀ/N`, `D²` denote entrywise squares, and

```math
B=-\frac12 C D^2 C.
```

If centered coordinates form the rows of X, then
`D²_ij=||x_i||²+||x_j||²−2 x_i·x_j`; centering kills the first two terms, giving
`B=XXᵀ`. Conversely, if B is positive semidefinite, its eigenfactorization supplies
coordinates whose squared distances reproduce D². To see uniqueness of that
reconstruction, double centering determines a symmetric matrix up to terms
`1aᵀ+a1ᵀ`; its prescribed zero diagonal fixes those terms. The number of positive
eigenvalues is the minimum exact Euclidean embedding dimension. Negative eigenvalues
exclude an exact Euclidean realization of the specified distances.

Classical multidimensional scaling keeps the leading positive eigenpairs. Its
optimality concerns the corresponding Gram-matrix approximation; it does **not**
generally minimize every possible raw-distance stress. Report the full eigenspectrum,
negative eigenmass, and direct distance distortion for prespecified dimensions.
A two-dimensional projection is a visualization choice, not an inferred spatial
dimension. Degenerate eigenspaces permit arbitrary rotations; coordinate arrays
need not remain identical under relabeling even when the distances do.

For GHZ, all direct off-diagonal distances are `a=ln 2`. Hence
`D²=a²(11ᵀ−I)` and `B=(a²/2)C`: the eigenvalue `a²/2` has multiplicity N−1.
The exact Euclidean geometry is an equilateral simplex, whose dimension grows with
N. A pleasant low-dimensional drawing discards known information. The same statement
holds for any strictly positive uniform off-diagonal distance, including Model A
when its pair MI lies strictly between zero and two.

## 8. Does pair information capture larger-region entropy?

The redundancy-constrained ansatz is

```math
S(B)\approx Q(B),\qquad
Q(B)=\frac12\sum_{i\in B,\ j\notin B}I(i:j),\qquad
\Delta(B)=S(B)-Q(B).
```

This is an extra structural assumption, not an entropy identity for arbitrary
many-qubit states. It is the cut relation discussed by Cao–Carroll–Michalakis above.
The experiment compares all singleton cuts and prespecified sampled balanced cuts,
transporting cuts under relabeling and reusing them for paired state perturbations.
The signed defect is retained along with absolute normalized defect
`|Δ|/max(S,Q,10^{-12})`. The floor defines a numerical convention, not a physical
entropy scale. If both terms are <=1e-10, their normalized defect is recorded as
zero with an explicit numerical-zero flag; raw values are retained. A small mean defect on sampled cuts cannot establish the law for all
cuts or at other coarse-grainings.

For pure product states, `S=Q=0`; the convention returns zero defect. For a tensor
product of Bell pairs, each Bell pair crossing the cut contributes one bit to S and
two bits to the MI sum, and each uncut pair contributes neither. Therefore `Δ=0`
for every cut. These disconnected controls show that the cut law alone does not
select connected or manifold geometry.

For GHZ and any nonempty proper B of size m, `S(B)=1` and each of the `m(N−m)`
crossing pairs has MI one. Thus

```math
\Delta(B)=1-\frac{m(N-m)}2.
```

At N=3 every such cut happens to satisfy the law; at the registered N≥6 even
singleton cuts fail. This exact size dependence is an additional control against
extrapolating success on the smallest systems. A cut's entropy is computed from
the state, not estimated from the pair matrix it is testing. Failure identifies
information absent from the pairwise ansatz, not a proof that no other geometric
description can exist.

## 9. Dynamics supply an independent locality question

For the given Hamiltonian and `X_i(t)=e^{itH}X_i e^{-itH}`, the small-t expansion is

```math
X_i(t)=X_i+it[H,X_i]+O(t^2),\qquad
[H,X_i]=-2i\sum_{k\ne i}J_{ik}Y_iZ_k.
```

Since `[Z_j,X_j]=2iY_j`, for `j≠i` this gives

```math
[X_i(t),X_j]=4itJ_{ij}Y_iY_j+O(t^2),\qquad
\lim_{t\to0}\frac{\|[X_i(t),X_j]\|}{|t|}=4|J_{ij}|.
```

Here the norm is the operator norm; `||Y_iY_j||=1`. The same leading coefficient
holds for Hilbert–Schmidt norm after division by `√(2^N)`. At fixed finite N the
remainder is controlled by the convergent nested-commutator series; for example
the remainder of X after first order is bounded by
`e^{2||H|| |t|}−1−2||H|| |t|`, with
`||H||≤Nh+Σ_{i<j}|J_ij|`. Commuting that remainder with X_j costs at most a factor
two. This is a finite-size bound, not a uniform continuum result.

Every nonzero direct bond therefore produces leading-order operator influence,
even if a state-dependent MI graph assigns it a long distance. For a chain,
nonneighbors have zero leading coefficient; for the dense ensembles almost all
pairs have a direct term. This calculation is independent of the chosen state.
It identifies the interaction support already present in the equations. It neither
proves nor rules out every possible coarse-grained locality limit of dense systems;
such a limit needs a scaling theorem beyond this first derivative.

Lieb–Robinson bounds give finite propagation estimates **assuming** suitable spatial
interaction structure; the original theorem assumes finite-range interactions on a
lattice. A nontrivial emergent-locality claim would need a comparable bound with
controlled constants relative to the inferred geometry, across sizes and observables.
Using a complete graph's unit graph distance would make “locality” vacuous for this
purpose. The external t in Schrödinger evolution is not reconstructed time, and a
commutator estimate is not Lorentz invariance.
[Lieb–Robinson, 1972, §§2–3](https://doi.org/10.1007/BF01645779).

The optional feedback phase is omitted before outcomes: no physically justified
autonomous law for changing J is supplied. Updating couplings from measured or
computed MI would introduce a classical controller and a chosen objective. A
state-dependent update is generally nonlinear in the state; it is not the fixed
unitary dynamics of this experiment. A later controlled study would have to specify
the controller, measurement/backaction or enlarged quantum system explicitly.

## 10. Interpretation, uncertainty and a controlled limit

Mathematical identities above hold without stochastic uncertainty. Eigensolver
residuals, entropy tolerances, gaps and invariance errors measure numerical quality.
Stochastic uncertainty concerns **whole independently drawn states or coupling
realizations**, not the correlated pairs within one quantum system. Sizes, fields,
scrambles and perturbations sharing a realization remain paired in resampling.
Calibration and primary randomness must be disjoint. Failed controls, ambiguous
gaps, degenerate embeddings and undefined rank statistics remain visible; none is
a license to retune the scientific criteria.

The registered experiment can establish reconstruction success or failure in the
supplied chain, diagnose deceptive proximity in nonspatial controls, and measure
robustness and interaction dependence. Its exact counterexamples and symmetry
obstructions remain meaningful regardless of classification performance. Three small
sizes cannot establish a phase transition, continuum dimension or universality.

A controlled continuum proposal would still need, at minimum:

- A specified sequence of state spaces, states and dynamics, with a physically
  motivated subsystem/coarse-graining prescription and consistent observables.
- Convergence of metric **and measure**, a nontrivial separation of microscopic,
  mesoscopic and macroscopic scales, and quantified reconstruction ambiguities.
- Stable dimensionality/topology and error control under perturbations and alternative
  admissible coarse-grainings; a finite embedding alone is insufficient.
- Local propagation of independently specified excitations, with bounds uniform in
  the relevant scaling limit, rather than locality inferred from the same correlations.
- A temporal/causal construction and the required relativistic symmetries, plus matter
  dynamics and a justified relation between information, geometry and stress-energy.
- A derivation and test of any gravitational field equation or observational prediction.

These are research requirements, not conditions verified here. The expected scientific
value is to identify which extra assumptions make reconstruction meaningful and which
ambiguities persist. No result in this finite lab establishes spacetime discreteness,
emergent gravity, Einstein equations or resolution of a black-hole singularity.
