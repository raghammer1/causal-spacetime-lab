# Experiment 4: local causal structure and identifiability

This document separates exact combinatorial statements, continuum statements
under explicit assumptions, and finite numerical tests. An order that agrees
with reference observables has not thereby acquired a faithful geometric
embedding. The experimental decisions and tolerances are specified in
[LOCAL_CAUSAL_STRUCTURE_PROTOCOL.md](LOCAL_CAUSAL_STRUCTURE_PROTOCOL.md).

## Definitions and information already present in the old summaries

Let P be a finite strict partial order on N events. Write P(v) and F(v) for
the strict past and future of v, and write I(x,y)=F(x) intersect P(y) for the
open interval of a related pair x<y. Its endpoints are excluded. The previous
experiments retain the relation count R, height H, and interval histogram

$$a_m=\#\{(x,y):x<y,\ |I(x,y)|=m\}.$$

The following are exact identities, not additional independent observables:

$$\sum_m a_m=R,\qquad
\sum_m m a_m=C_3=\sum_v |P(v)|\,|F(v)|,$$

where C3 counts three-event chains. The first equality partitions related
pairs by interval cardinality. For the second, count a chain x<v<y either
by its endpoints or by its middle event. Similarly,

$$\sum_m\binom m2a_m=C_4+D_4,\qquad
C_4=\sum_{b<c}|P(b)|\,|F(c)|.$$

Here C4 counts four-event chains and D4 counts induced four-event diamonds
with one minimum, one maximum, and two incomparable middle events. Choosing
two events inside an interval gives exactly one of those possibilities. A
four-chain has a unique ordered middle pair b<c, establishing the second
formula. These identities apply to induced subsets of events, not to paths
in a Hasse diagram.

For any fixed motif size k, motif counts also obey linear constraints. Their
sum is binomial(N,k); summing each motif's number of relations times its
abundance gives R*binomial(N-2,k-2). For k=4, weighting by the number of
three-chains gives C3*(N-3). Reporting several correlated statistics does not
create the same number of independent measurements.

## An exact induced 2+2 formula

An induced 2+2 is a four-element subset whose only relations are two disjoint
two-element chains. For incomparable minima a,c, a prospective upper event
b must belong to F(a) minus F(c), and the other upper event d must belong to
F(c) minus F(a). Such b,d are automatically incomparable: b<d would imply
a<d, while d<b would imply c<b, contradicting their membership. Neither can
be one of the two minima. Every induced 2+2 has a unique unordered pair of
minima, so

$$\boxed{n_{22}=\sum_{\{a,c\}:a\parallel c}
 |F(a)\setminus F(c)|\,|F(c)\setminus F(a)|.}$$

The dual formula replaces futures by pasts and sums over incomparable maxima.
The implementation can use intersections of integer bitsets; exhaustive
four-subset classification is an independent, slower validation method.

An interval order defined by real intervals, with a<b iff right(a)<left(b),
cannot contain a 2+2. For a<b and c<d, either right(a)<=right(c), forcing
a<d, or right(c)<right(a), forcing c<b. Fishburn's original representation
theorem identifies this axiom with interval representability for countable
orders: [Fishburn, *Intransitive indifference with unequal indifference
intervals* (1970)](https://doi.org/10.1016/0022-2496(70)90062-3).
The theorem concerns an order class, not general Minkowski embeddability.

## Interval intersections and their moment identities

Index every open interval by its related endpoint pair, retaining distinct
endpoint pairs even when their interiors happen to coincide. An event v is
inside exactly q(v)=|P(v)|*|F(v)| such intervals. Consequently,

$$O_1:=\sum_{\alpha<\beta}|I_\alpha\cap I_\beta|
 =\sum_v\binom{q(v)}2.$$

This double-counts an unordered interval pair and one shared interior event.
Thus the mean overlap, with the specified normalization by binomial(R,2),
contains only a degree-product moment. It does not retain which intervals
overlap. For two distinct events v,w, the number of intervals containing both
is

$$c(v,w)=|P(v)\cap P(w)|\,|F(v)\cap F(w)|.$$

Every choice of a common predecessor and common successor is a valid related
endpoint pair. Counting an interval pair and an unordered pair of shared
events yields the second factorial-moment identity

$$\boxed{O_2:=\sum_{\alpha<\beta}
 \binom{|I_\alpha\cap I_\beta|}2
 =\sum_{v<w}\binom{c(v,w)}2.}$$

The ordering v<w in this last sum is an arbitrary enumeration of unordered
distinct event pairs, not the causal relation. Empty intervals contribute
zero to both moments. When R<2, a normalized interval-pair mean is undefined;
the integer totals remain zero. Direct interval intersection enumeration
checks the identities on small orders. These moments do not replace the
joint distribution of interval sizes, internal patterns and overlaps.

## Exact equal-summary counterexamples

Take m lower events and m upper events, with a simple degree-k bipartite
relation graph, where 1<=k<=m. Add a unique bottom and top. All resulting
orders have N=2m+2, H=4, R=mk+4m+1, and histogram contributions

$$a_0\mathrel{+}=mk+2m,\qquad a_k\mathrel{+}=2m,
\qquad a_{2m}\mathrel{+}=1.$$

These are contributions to bins, so coincident indices must be added rather
than overwritten. The mk interior edges and 2m extremum-adjacent pairs are
links. Each bottom-to-upper and lower-to-top interval contains k events;
the bottom-to-top interval contains all 2m interior events.

Let t(i,j) be the number of common upper neighbors of two lower events and
let B4 count complete 2-by-2 bipartite subgraphs. Every 2+2 lies in the
bipartite interior. The exclusive-future identity gives

$$n_{22}=\sum_{i<j}(k-t(i,j))^2.$$

Regularity implies sum(t)=m*binomial(k,2), while
sum(binomial(t,2))=B4. Expanding the square proves

$$\boxed{n_{22}=\binom m2k^2-(2k-1)m\binom k2+2B_4.}$$

For m=4,k=2, choose one eight-cycle or two disjoint complete 2-by-2 graphs.
These are the Experiment 3 nondual pair. The first has B4=0 and n22=12;
the second has B4=2 and n22=16. Removing the unique extrema leaves respectively
a connected and a disconnected comparability graph. Neither isomorphism nor
order duality can identify the pair. They have the same complete histogram,
so n22 and internal connectivity contain information absent from the old
summaries.

There is also a useful exact limitation. Both examples have O1=24. In this
regular family,

$$O_2=2B_4+2m\binom k2.$$

Pairs on one bipartite side have c(v,w)=1+t(v,w); mixed-side pairs have
c(v,w)=1 and contribute zero. Applying the common-neighbor identities on
both sides proves the formula. Thus O2 is 8 versus 12 for the example pair,
and n22=O2+4. These two distinguishing observables measure the same B4
information in this family; they are not independent evidence.

### Scaling exact degeneracies by substitution

Given a base order B, replace every event i by a module M_i. Keep each module's
internal relations and relate every event in M_i below every event in M_j
iff i<j in B. This is the lexicographic sum. A within-module interval is
unchanged. For x in M_i and y in M_j with i<j,

$$|I(x,y)|=d^+_{M_i}(x)+d^-_{M_j}(y)
 +\sum_{i<\ell<j}|M_\ell|.$$

Replacing modules by alternatives with the same size, height, relation count,
full interval histogram, and separate in/out-degree multisets preserves
global N,R,H and the full interval histogram. Height is the maximum weighted
base-chain height; if all module heights equal h, it is h*H(B). Cross-module
histograms are convolutions of the relevant degree multisets shifted by the
total sizes of intermediate modules.

The unbounded eight-event C8 and two-K2,2 modules qualify. They also share the
joint degree multiset and all induced patterns on at most three events.
Indeed their pair counts and the V and inverted-V triple counts are fixed
by the degrees; their other triple counts follow from these and the total.
All contributions of four-subsets spanning several modules therefore agree.
Changing q such modules changes n22 by precisely 4q, while preserving the
global joint degree multiset and O1. With eight-event modules this difference
in the normalized global n22 density is of order N^-3. Local distinctions
can become difficult to see in aggregate densities even when their existence
is exact.

## Conditional flat-space interval laws

Let D be a finite-volume causally convex region of d-dimensional Minkowski
spacetime, and sample exactly N independent uniform events in D. Causal
convexity here means that the full Alexandrov interval between any related
pair in D lies in D. Fix two labeled endpoints x<y and condition on exactly
m other events lying in their open interval. Conditional on which labels
are inside, those m coordinates are independent uniform points in I(x,y).
Removing the labels does not change their induced-order law.

Every timelike flat Alexandrov interval is obtained from the standard diamond
by a translation, Lorentz transformation and scale change. These maps preserve
causality and transform volume by a constant factor. Therefore, conditional
on m, the interior order has the standard m-point, d-dimensional diamond law,
independently of the outer region and endpoint coordinates. Null-related
endpoints have probability zero under the continuous sampling law.

For a bounded internal-order statistic f, let mu(d,m)=E[f(P_m)] under this
reference law, and define

$$A_m=a_m,\qquad B_{f,m}=\sum_{x<y:\ |I(x,y)|=m}f(I(x,y)).$$

By conditioning each labeled endpoint pair and then summing,

$$\boxed{E[B_{f,m}-\mu(d,m)A_m]=0.}$$

This is an expectation identity for counts. It does **not** imply
E[B/A]=mu for the per-order ratio: A is random and correlated with B. The
experiment estimates the ratio of ensemble means with pooled counts
sum(B)/sum(A). A parent with A=0 contributes zero to both sums and is retained
in resampling. Independent parent orders are the statistical units;
overlapping intervals within them are not independent observations.

A different causally convex boundary is the central time slab of a diamond,
T/4<=t<=3T/4 in the generator's coordinates. A causal interval between points
of this region stays inside the original diamond and between their endpoint
times, hence inside the slab. Uniform rejection sampling from the diamond
produces its uniform law. A finite spatial box can clip Alexandrov intervals,
so the same theorem need not apply. Box disagreements test sensitivity to
this assumption, not failure of flat-spacetime embeddability.

The m=2 connectivity reference is exactly the flat-diamond ordering fraction

$$\mu_{\mathrm{connected}}(d,2)
 =\frac{\Gamma(d+1)\Gamma(d/2)}{2\Gamma(3d/2)}.$$

For m=4 the complete vector of 16 induced order types, connectivity, and 2+2
indicator can be compared. For m=8 the joint statistic
connected(P)*n22(P)/binomial(8,4) tests a pattern-connectivity association;
it cannot generally be replaced by the product of its marginal means.

## Exact two-dimensional reference laws and their limitations

Uniform points in a d=2 diamond have independent uniform rescaled null
coordinates U,V. Sort by U; the V ranks are a uniform permutation. Conversely
two independent uniform rankings, intersected as orders, give exactly this
law, including the labeled law when both rankings are randomized. Thus every
order-only observable has the same distribution under the two constructions.
This provenance ambiguity remains even if the entire finite order is known.

For four events, the sole V permutation producing two disjoint increasing
pairs and no other increasing pair is 3412. Hence

$$\Pr(P_4=2+2)=1/24,\qquad
E[n_{22}(P_m)/\binom m4]=1/24\quad(m\ge4).$$

The latter follows by averaging over four-subsets of independent points.
In particular E[B_22,4-a4/24]=0 in every causally convex uniform d=2 outer
region. It is not a claim that all such regions have the same unconditional
global four-event motif distribution.

Connected components of the comparability graph of a permutation order form
consecutive U blocks in decreasing V block order. Otherwise a component
would need a comparable edge across an event of another component, which
the cross-component incomparabilities forbid. If c_n counts permutations
whose comparability graph is connected, taking the first component gives

$$c_1=1,\qquad
c_n=n!-\sum_{j=1}^{n-1}c_j(n-j)!.$$

Thus c2/2!=1/2, c3/3!=1/2 and c4/4!=13/24. The same recurrence supplies an
exact m=8 connectivity reference. Enumerating the 8! permutations also gives
an exact joint connectivity/2+2 reference without Monte Carlo calibration
error. Exhaustive enumeration is finite arithmetic, not a stochastic fit.

The general permutation-multiplicity result is Proposition 16 of
[Fewster, Hawkins, Minz and Rejzner, *Local Structure of Sprinkled Causal
Sets*, PRD 103, 086020 (2021)](https://arxiv.org/abs/2011.02965). Their Section
IV also explains that every order through five events embeds in 1+1
Minkowski spacetime. Small-pattern occurrence alone therefore cannot reject
all d=2 embeddings. Frequencies under a specified uniform sampling law are
a different question.

### A six-event embedding obstruction with a higher-dimensional embedding

Define S3 on lower a1,a2,a3 and upper b1,b2,b3 by ai<bj iff i!=j. A d=2
embedding in null coordinates would represent it as the intersection of two
linear orders. To keep ai incomparable with bi, at least one linear order
must put bi before ai. One linear extension cannot do this for two distinct
indices: bi<ai<bj<aj<bi would be a cycle, using the required off-diagonal
relations. Three diagonal pairs therefore require at least three linear
orders. S3 has no d=2 Minkowski embedding.

This is dimension-specific. Let v1,v2,v3 be the unit-radius vertices of an
equilateral triangle in the two-dimensional spatial plane. Put ai=(1.1,vi)
and bi=(2.6,-vi). Every cross-level time difference is 1.5. The spatial
distance is 2 for matching indices and 1 for distinct indices. Thus precisely
the off-diagonal cross pairs are timelike. Equal-time pairs are spacelike.
All six points lie strictly inside the duration-4 d=3 diamond because their
radius 1 is less than min(t,4-t). This explicitly realizes S3 in flat d=3
spacetime. It is not a universally nongeometric negative control.

## Why a finite motif extension cannot identify all finite orders

For N labeled events split into two fixed layers, independently choosing each
cross-layer relation gives 2^floor(N^2/4) distinct height-at-most-two orders.
An isomorphism class contains at most N! labeled orders, so the number of
unlabeled orders is at least 2^floor(N^2/4)/N!, which is exp(Omega(N^2)).

The full interval histogram has at most N-1 entries, each at most binomial(N,2).
Together with R and H it has at most exp(O(N log N)) possible values. A fixed
finite collection of motif counts of bounded size, or integer overlap moments
of bounded order, adds only polynomially many possibilities in N. Therefore,
for sufficiently large N, such summaries necessarily collide on nonisomorphic
orders. This counting argument concerns unrestricted finite posets. It does
not rule out stronger reconstruction theorems with explicit geometric and
scaling assumptions, or observables whose amount of information grows faster.
In particular, the full size/component profile A[m,k] has a number of categories
that grows quadratically in N. The bound above does not establish collisions
for that full profile together with every new observable in this experiment.
Claims about such larger vectors require a separate proof or exact witness.

## Verification and continuum scope

The exhaustive small-order checks compare independent algorithms and known
enumeration totals. [Brinkmann and McKay, *Posets on up to 16 Points*, Order
19, 147–179 (2002)](https://users.cecs.anu.edu.au/~bdm/papers/posets.pdf), Table
1, gives 1,2,5,16,63,318 unlabeled orders on one through six events. Enumerating
forward-edge DAGs, taking transitive closures, and canonicalizing under all
relabelings is complete because every finite partial order has a linear
extension; it is not a uniform random-poset sampler.

Interval abundance has a primary causal-set foundation in
[Glaser and Surya, *Towards a Definition of Locality in a Manifoldlike Causal
Set* (2013)](https://arxiv.org/abs/1309.3403). Their proposed sufficiency of
rigidity is a conjecture. The exact conditional-law argument above adds
testable internal structure while retaining explicit sampling and boundary
assumptions.

A controlled continuum interpretation would still require a sequence of
orders and a precise limiting relation/volume structure; a candidate
Lorentzian manifold with appropriate causal regularity; concentration and
consistency across scales; control of boundary and sampling effects; and
uniqueness or quantified nonuniqueness of reconstruction. Matching a finite
list of local distributions supplies none of these conditions by itself.
Curvature, dynamics, and gravitational field equations require further work.
