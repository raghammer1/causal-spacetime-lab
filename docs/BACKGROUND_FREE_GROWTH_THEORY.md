# Experiment 5: mathematical foundations for intrinsic causal growth

This document precedes the primary experiment. It distinguishes cited theorems,
derivations given here, and questions for finite numerical measurements. It is
not a report of empirical findings. The registered design is in
[BACKGROUND_FREE_GROWTH_PROTOCOL.md](BACKGROUND_FREE_GROWTH_PROTOCOL.md).
Experiment 4's [continuum requirements](LOCAL_CAUSAL_STRUCTURE_CONTINUUM.md)
continue to apply.

The primary stochastic laws have fixed
`p = 0.005, 0.01, 0.02, 0.05, 0.1, 0.3`; `p=0,1` are deterministic checks.
The prefixes `N = 32,64,128,256,512` belong to individual histories. No
size-dependent parameter sequence is a primary growth law in this experiment.
The asymptotic restrictions below are known before any data are examined.

## 1. Order conventions and the growth law

An order is a strict, irreflexive, transitive relation. Write

$$
P(x)=\{y:y\prec x\},\quad F(x)=\{y:x\prec y\},\quad
I(a,c)=F(a)\cap P(c),\quad m_{ac}=|I(a,c)|.
$$

For an order on `N` events, `R` counts related unordered pairs, `L` counts cover
relations, `I=binomial(N,2)-R` counts incomparable unordered pairs, and
`r=R/binomial(N,2)`. The notation `I(a,c)` for an interval is distinguished from
the scalar `I` by its arguments. A cover `x≺y` has an empty open interval.
`H` is the maximum number of events in a chain. All motif counts below are
**induced** counts on unordered subsets; `a_F=n_F/binomial(N,k)` for a
`k`-event motif `F`.

Transitive percolation adds event `n` by selecting each earlier event
independently with probability `p`, placing the new event above every selected
event, and closing transitively. The selection coins contain no coordinates,
distances, dimension labels or target geometric statistics. Birth indices
implement a natural labeling: relations point from earlier to later births.

This is the established model of [Rideout and Sorkin (2000), §§2–4,
equation (6)](https://arxiv.org/pdf/gr-qc/9904062). Their elementary transition
probability for a specified down-set `S` of an `n`-event parent is

$$
T(C,S)=p^{m}q^{n-s},\qquad q=1-p,\quad s=|S|,\quad m=|\max S|.
\tag{1}
$$

Here a down-set contains the past of each of its elements. The probability
refers to that specified precursor, before summing precursors that give
isomorphic unlabeled children.

**Direct derivation.** Let `D` be the subset chosen by the independent coins.
Its downward closure is exactly `S` if and only if every maximal event of `S`
is selected and every event outside `S` is excluded. The remaining `s-m`
coins are unrestricted. Their summed weight is `(p+q)^(s-m)=1`, proving (1).
These closure fibers partition all `2^n` choices, so their probabilities sum to
one. Adding only a new maximal event preserves acyclicity and leaves the old
order unchanged. At `p=0` the result is an antichain; at `p=1` it is a chain.
Products with zero exponents use the usual empty-product convention, including
`0^0=1` when expressing these deterministic cases.

## 2. Three different label and consistency requirements

Permuting the rows and columns of an already completed matrix preserves
order-invariant observables. This checks an implementation, but does not prove
that the stochastic law assigns consistent probabilities to different birth
histories.

**Growth-path covariance.** Rideout–Sorkin's discrete general covariance
requires equal products of elementary transition probabilities along natural
birth histories producing the same final order. Their Bell causality condition
preserves ratios of competing transitions after deleting events outside both
precursors. These statements concern transition laws, not a coordinate
symmetry of a chosen matrix.

For the present law these properties have short independent verifications.
For a final naturally labeled order `C`, multiply (1) over its births. Every
cover is counted once among the precursor maxima; every incomparable pair is
counted once when its later-born event appears. Thus

$$
w(C)=\prod_{n=0}^{N-1}T(C_n,S_n)=p^{L(C)}q^{I(C)}.
\tag{2}
$$

Both exponents are intrinsic. Equivalently, in the primitive directed graph
every cover must be present, every incomparable pair must be absent, and
non-cover comparable edges may be either present or absent. Summing the latter
coins gives the same expression. An exhaustive test can independently sum
primitive-graph probabilities and compare every natural labeling's product.

If `e(C)` counts linear extensions of one fixed abstract order and
`Aut(C)` its automorphism group, the number of distinct naturally labeled
matrices is

$$
W(C)=\frac{e(C)}{|\mathrm{Aut}(C)|},\qquad
\Pr([C])=W(C)p^{L(C)}q^{I(C)}.
\tag{3}
$$

The automorphism action on labelings is free: fixing a bijective labeling fixes
every event. Hence division by the group size counts the equivalence classes.
For an antichain, `e=N!` and `|Aut|=N!`, so `W=1`, not `N!`. Aggregated
unlabeled transition probabilities require the corresponding precursor
multiplicities. Equation (3) is a finite-stage probability; it does not settle
which events of an infinite growth process are physically observable.

For two precursors `S_1,S_2`, let `B=S_1∪S_2`. For `0<p<1`,

$$
\frac{T(C,S_1)}{T(C,S_2)}
=p^{m_1-m_2}q^{s_2-s_1}
=\frac{T(B,S_1)}{T(B,S_2)}.
\tag{4}
$$

Deleting spectators changes neither precursor nor its maxima, and the parent
size cancels. This is the Bell ratio identity for this model. Ratios involving
zero probabilities at `p=0,1` are not justified by division; those endpoints
are tested directly. The original positive-probability ratio argument does
not automatically establish the axioms for a custom growth rule.

**Prefix consistency.** Assign one independent Bernoulli(`p`) variable to each
pair `i<j` of nonnegative birth indices. Restricting this construction to the
first `N` events gives the finite growth law. No path between old events can
use a later event because directed paths have increasing indices. Therefore
closing before or after prefix restriction gives the same relation. This
constructs consistent finite distributions and one infinite history. The
implementation must preserve this coupling when a requested maximum size
changes; a random stream identifier must not depend on that maximum size.

These statements fail in different ways for superficially similar procedures:

- Separate constant-`p_N` runs are valid percolation models individually, but
  their first two events are related with probability `p_N`. If this changes
  with final size, those ensembles are not the prefixes of one fixed law.
- Varying a coin probability with birth stage defines a coherent process, but
  generally loses growth-path covariance. Write `a` for the probability at the
  second birth and `b` at the third. A three-event order consisting of one edge
  and an isolated event has natural histories with weights
  `a(1-b)^2` and `(1-a)b(1-b)`. For interior parameters these agree only if
  `a=b`. Calling both procedures “running p” conceals this distinction.

## 3. Exact finite motif identities

### The four-event law

An induced `2+2` has two disjoint two-event chains. Its cover count is two,
its incomparable-pair count is four, it has six linear extensions and two
automorphisms. Equation (3) therefore gives

$$
\Pr(P_4=2+2)=3p^2q^4.
\tag{5}
$$

A `3+1` consists of a three-event chain and one isolated event. It has two
covers, three incomparable pairs, four linear extensions and only the identity
automorphism. Hence

$$
\Pr(P_4=3+1)=4p^2q^3.
\tag{6}
$$

These are laws for the **entire four-event percolation order**. A four-event
subset of a larger order can inherit relations through omitted events, so
substituting (5) or (6) for the large-order motif expectation is incorrect.
Exact enumeration of all primitive graphs through five events is feasible:
at five events there are only `2^10=1024` graphs. Enumerating graph subsets,
precursors and natural labelings supplies independent checks of different
parts of the implementation.

### An exact count of `3+1` in an arbitrary order

For each `a≺c`, select an interior event `b∈I(a,c)` to form `a≺b≺c`.
An event `d` is incomparable to both endpoints precisely when it lies outside
`F(a)∪P(c)`. This union contains the endpoints themselves, all events comparable
to either endpoint, and has cardinality `|F(a)|+|P(c)|-m_ac`.

Such a `d` is automatically incomparable to `b`: `d≺b` would imply `d≺c`,
and `b≺d` would imply `a≺d`. Conversely every induced `3+1` has a unique chain
and therefore one endpoint pair and one middle event in this count. It follows
that

$$
n_{31}(C)=\sum_{a\prec c}
m_{ac}\left[N-|F(a)|-|P(c)|+m_{ac}\right].
\tag{7}
$$

The bracket is a nonnegative integer. This identity provides an exact
algorithm without iterating all four-event subsets. It must agree with
exhaustive induced-subset classification on small orders, independently of
the probabilistic generator. The existing exact `2+2` and interval identities
from [Experiment 4](LOCAL_CAUSAL_STRUCTURE_THEORY.md) remain applicable.

## 4. What a single fixed-p history does asymptotically

The following elementary bounds are derived here; they do not rely on a fit
to simulation. Fix `0<p≤1`. For `i<j` with gap `g=j-i`, incomparability requires
an absent direct primitive edge and the absence of every two-edge path
`i→k→j`. The direct edge and the distinct pairs of edges for intermediate
events are independent. Longer paths can only increase comparability, giving

$$
\Pr(i\parallel j)\le q(1-p^2)^{g-1}.
\tag{8}
$$

Summing over gaps and extending a nonnegative geometric series,

$$
E I_N\le q\sum_{g=1}^{N-1}(N-g)(1-p^2)^{g-1}
\le \frac{Nq}{p^2},\qquad
E(1-r_N)\le\frac{2q}{(N-1)p^2}.
\tag{9}
$$

For a uniform four-event subset, the expected number of incomparable pairs is
`6(1-r_N)`. A `2+2` contributes four such pairs and a `3+1` contributes three.
Consequently, for every order, and then in expectation under this growth law,

$$
4a_{22}\le6(1-r_N),\quad3a_{31}\le6(1-r_N),
\qquad
E a_{22}\le\frac{3q}{(N-1)p^2},\quad
E a_{31}\le\frac{4q}{(N-1)p^2}.
\tag{10}
$$

Bounds exceeding one can be replaced by one. Their looseness at small `p` and
moderate `N` does not predict the crossover size accurately.

There is also a **single-history almost-sure statement**. Markov's inequality
at `N=2^k` gives

$$
\Pr\left(I_{2^k}/2^{2k}>\epsilon\right)
\le\frac{q}{p^2\epsilon 2^k}.
$$

The bounds are summable in `k`. Borel–Cantelli, first for each positive rational
`epsilon`, gives `I_(2^k)/2^(2k)→0` almost surely. The count `I_N` is
nondecreasing along a history, even though its density need not be. For
`2^k≤N<2^(k+1)`,

$$
\frac{I_N}{N^2}\le
4\frac{I_{2^{k+1}}}{2^{2(k+1)}}\longrightarrow0.
$$

Thus `r_N→1` almost surely. For any fixed `k`, a non-chain induced `k`-subset
has an incomparable pair, so a union bound gives

$$
1-a_{\mathrm{chain},k}(C_N)\le\binom{k}{2}(1-r_N)\longrightarrow0
\quad\text{almost surely}.
\tag{11}
$$

For countably many fixed `k` these conclusions hold simultaneously on an event
of probability one. This establishes convergence of all fixed-size uniform
sampled-suborder laws to the chain law, along one history. A specified labeled
`k`-chain has limiting probability `1/k!` under randomly assigned sample labels;
the unlabeled chain has probability one.

**What this convergence forgets.** For `0<p<1`, consider disjoint adjacent
birth pairs `(0,1),(2,3),…`. An adjacent pair has no possible intermediate birth,
so it is incomparable exactly when its primitive edge is absent. These are
independent Bernoulli(`q`) events. If `B_N` pairs fail, any chain must omit at
least one event from each failed pair, giving `H_N≤N-B_N`. The strong law gives

$$
\limsup_{N\to\infty}H_N/N\le1-q/2=(1+p)/2<1
\quad\text{almost surely}.
\tag{12}
$$

There are also infinitely many incomparable adjacent pairs almost surely.
Therefore the infinite order is not a total order, and the chain sampling
limit does not mean that a chain contains almost all events. Global dense
sampling can discard sparse but persistent structure. Neither finite
observables nor this particular full sampling limit establish a Lorentzian
metric limit. At `p=0` every prefix is exactly an antichain.

## 5. The wider classical sequential growth restriction

In [Brightwell and Georgiou (2010), definitions 1.2–1.3 and theorems
1.4–1.6](https://nicholasgeorgiou.webspace.durham.ac.uk/wp-content/uploads/sites/199/2021/04/contlim.pdf),
convergence means that expected probabilities of **every finite sampled
labeled order** approach those of an atomless ordered probability space.
Their CSG class uses nonnegative couplings with `t_0` or `t_1` positive.
Theorem 1.5 supplies, uniformly over these couplings, a semiorder `S_N` with
expected pair-edit distance `o(N²)` from `C_N`. It allows different couplings
at each `N`. Thus induced `2+2` and `3+1` densities vanish; any existing
sampling limit is an almost-semiorder. This does not cover arbitrary modified
dynamics or every possible local scaling limit.

For percolation put `h_N=log(1/p_N)/(N p_N)`. Theorem 1.4 gives a chain limit
if `h_N→0`, a semiorder on uniform `[0,1]` with
`x≺y iff y-x>c` if `h_N→c∈(0,1)`, and an antichain if
`liminf h_N≥1`. These are sampling-law statements, not Lorentzian metric
convergence.

**Consequences derived for this design.** A four-subset on which two orders
differ contains an edited pair. If their pair-edit distance is `D`, at most
`D binomial(N-2,2)` four-subsets differ. Since semiorders contain neither
forbidden motif, their vanishing expected densities follow after division by
`binomial(N,4)`. Existence of a full continuum limit is unnecessary for that
necessary condition. The cited uniform asymptotic statement supplies no claim
that `N≤512` is already in its limiting regime.

For a separate sequence `p_N=alpha log(N)/N`, direct substitution gives
`h_N→1/alpha`. If `alpha>1`, the limiting comparability probability is

$$
\Pr(|U-V|>1/\alpha)=(1-1/\alpha)^2,
\tag{13}
$$

for independent uniform `U,V`. If `alpha≤1` the limit is an antichain.
Both forbidden densities still tend to zero. Such a sequence can preserve a
nontrivial ordering fraction without approaching the Minkowski motif law.
It is not a fixed-parameter history, and is not part of the primary sweep.

For completeness, a semiorder with threshold `c>0` cannot contain `2+2`:
if `u_a+c<u_b` and `u_c+c<u_d`, choose the lower of `u_a,u_c`; it is also
below the opposite upper endpoint, producing an unwanted cross relation.
It cannot contain `3+1`: the outer utilities of a three-chain differ by more
than `2c`, while an event incomparable to both would have to be within `c`
of each. These elementary obstructions explain the four-event restriction.

## 6. Reference laws and a deliberately misleading matched control

The independent Minkowski references use fixed regions and uniform iid points
in dimensions 2, 3 and 4. Nested prefixes of a coordinate sample are nested
samples of the same law; they are **not** natural birth prefixes of an intrinsic
growth law. Their coordinates construct reference data only, never the
percolation dynamics. Report both the sampling convention and boundary shape.
Dimension inversions retain the domain and sampling assumptions established
in Experiments 1–4; an output near an integer is not an embedding certificate.

In a two-dimensional flat diamond, null coordinates are independent uniform
variables. Sorting one coordinate leaves a uniform permutation of the other.
Of the 24 four-event permutations, only `3412` gives exactly two disjoint
two-chains. Therefore

$$
\Pr(P_4^{\mathrm{diamond},2}=2+2)=1/24,\qquad
E a_{22}(C_N^{\mathrm{diamond},2})=1/24\quad(N\ge4).
\tag{14}
$$

The second equality follows because every four-subset of iid points has the
same four-point law. This is the exact rank-two/diamond equivalence retained
from [Experiment 4](LOCAL_CAUSAL_STRUCTURE_THEORY.md), not evidence that order
data can distinguish those two provenances. In higher-dimensional diamonds,
two short timelike pairs separated spacelike from one another can be chosen
strictly inside the region. Small neighborhoods preserve all inequalities and
have positive volume, so the `2+2` sampling probability is positive there too.
Its numerical value needs a separate derivation or independent reference fit.

A nonmanifold semiorder control uses iid uniform utilities and threshold
`c=0.25`, as an explicitly coordinate-defined mathematical reference, not an
intrinsic candidate dynamics. It has `a22=a31=0` exactly at every size and
expected ordering fraction `(1-c)^2=9/16`. This checks that a nontrivial
ordering fraction does not entail a positive forbidden-motif density.

A second control deliberately matches (14) while remaining structurally
different. Give each event an independent fair lower/upper label. Permit
relations only from lower to upper events, with independent edge probability
`p_b`; no nontrivial transitive closure is needed. A four-subset has two of
each label with probability `binomial(4,2)/16=3/8`. Conditional on that split,
exactly two of the possible two-edge patterns are disjoint perfect matchings,
each with probability `p_b²(1-p_b)²`. Thus, for every `N≥4`,

$$
E a_{22}=\frac34p_b^2(1-p_b)^2.
$$

Choose, **analytically before measurement**, the smaller solution

$$
p_b=\frac{1-\sqrt{1-4/(3\sqrt2)}}2,
\qquad p_b(1-p_b)=\frac1{3\sqrt2},
\qquad E a_{22}=1/24.
\tag{15}
$$

This control explicitly targets one geometric observable; it is not a proposed
growth model or evidence for spontaneous emergence. Its height is at most two,
all open intervals are empty, `a31=0`, and expected ordering fraction is
`p_b/2`. The all-`N` expectation requires **independent fair labels**, not
forcing exactly half of each finite sample into each class. Retaining empty
and imbalanced label groups preserves the stated law. Matching (14) therefore
cannot by itself establish geometry, even without fitting an empirical
parameter.

## 7. Thinning identities and dependence

Let `C` be a fixed `N`-event order and choose `S` uniformly from its `m`-event
subsets. The thinned order is the restriction of the **closed causal relation**.
Deleting events from the primitive graph and then closing would lose relations
whose paths used deleted events and describes a different operation.

For a `k`-event motif `F` with `m≥k`, each occurrence in `C` survives with
probability `binomial(N-k,m-k)/binomial(N,m)=binomial(m,k)/binomial(N,k)`.
Linearity of expectation gives

$$
E[n_F(C|S)\mid C]
=n_F(C)\frac{\binom m k}{\binom N k},\qquad
E[a_F(C|S)\mid C]=a_F(C).
\tag{16}
$$

This applies to `r` and all fixed-size induced motif densities in **every**
order, geometric or otherwise. It does not make the thinned order a fresh
percolation prefix of size `m`, nor imply invariance of height, interval-size
histograms, nonlinear dimension inversions or conditional interval averages.
Apparent motif-density stability under random thinning is consequently a
necessary implementation check, not selective evidence of geometric emergence.

Prefixes, thinnings and motif estimates from one history are dependent.
They must travel together when histories are resampled for uncertainty.
Independent fits or reference ensembles remain independent units. A conditional
interval average can have an undefined denominator and must retain that
missingness; treating it as zero creates evidence that the sample did not
contain. The fixed-size interior laws of Experiment 4 apply to uniform flat
sampling in causally convex regions, not automatically to percolation.

## 8. What the experiment can falsify

For the registered fixed positive probabilities, equations (9)–(11) already
rule out a persistent `1/24` limit under global uniform sampling. Measurements
can establish where finite histories resemble or depart from that value, how
other observables co-vary, whether prefixes have reached a stable range, and
whether the implementation respects the stated law. They cannot overturn a
proved asymptotic restriction by finding a finite-size agreement.

The protocol must therefore preserve mismatches, short-lived agreements,
uncertainty, unavailable intervals, and failures of any finite stability
criterion. It must not tune the growth probabilities after seeing geometric
scores or describe a finite observation as a new continuum theorem. The matched
height-two control makes the insufficiency of a single agreement explicit.

Motivating altered intrinsic dynamics would require specifying which model
assumptions change, proving or checking the new law's consistency and covariance,
and choosing a convergence notion with appropriate concentration, scale and
geometric reconstruction control. Classical covariance alone is neither
Lorentz invariance of an emergent spacetime nor a derivation of gravity.
No outcome here proves physical discreteness, quantum dynamics, emergence of
gravity or resolution of a singularity.

## Primary references

- D. P. Rideout and R. D. Sorkin, *Classical Sequential Growth Dynamics for
  Causal Sets*, Physical Review D **61**, 024002 (2000),
  [doi:10.1103/PhysRevD.61.024002](https://doi.org/10.1103/PhysRevD.61.024002),
  [author preprint](https://arxiv.org/abs/gr-qc/9904062).
- G. Brightwell and N. Georgiou, *Continuum Limits for Classical Sequential
  Growth Models*, Random Structures & Algorithms **36**(2), 218–250 (2010;
  first published online 11 June 2009),
  [doi:10.1002/rsa.20278](https://doi.org/10.1002/rsa.20278),
  [author manuscript](https://nicholasgeorgiou.webspace.durham.ac.uk/wp-content/uploads/sites/199/2021/04/contlim.pdf).

The remaining displayed counting, coupling, thinning and elementary probability
arguments are supplied explicitly above; they are mathematical checks, not
claims of novelty.
