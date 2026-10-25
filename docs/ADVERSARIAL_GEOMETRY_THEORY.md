# Experiment 3: what causal summaries can identify

This lab compares finite probability models of causal orders. Its mathematical
identities, numerical comparisons, and possible interpretations are different
claims. A detector that accepts an order has established compatibility with its
selected calibrated summaries, not physical spacetime, a gravitational law, or
a microscopic ontology.

## Interval abundance and fixed-count sampling

For a strict partial order P on N events, define

$$
a_m(P)=\#\{(x,y):x\prec y,\;|\{z:x\prec z\prec y\}|=m\}.
$$

Endpoints are excluded. Thus a₀ is the number of links and
`sum(a_m)=R`, where R is the number of comparable unordered pairs counted once.
The interval counts elements, not directed paths. The expectation calculations
and proposed geometric use of these observables have a primary foundation in
[Glaser and Surya, *Towards a Definition of Locality in a Manifoldlike Causal
Set*, PRD 88, 124026 (2013)](https://arxiv.org/abs/1309.3403). Their flat-space
interval-abundance calculation and numerical tests motivate this experiment;
their sufficient-rigidity statement is a conjecture, not a theorem establishing
that a matching finite histogram guarantees a continuum interpretation.

Here the genuine samples contain exactly N independent uniform points inside
a flat Alexandrov interval I of volume V. Conditional on two specified related
endpoints x≺y, each of the other N−2 points lies in their interval independently
with probability `v=V_xy/V`. Counting ordered choices of the two labels gives
the following fixed-count identity, derived for this lab:

$$
\mathbb E[a_m]
=\frac{N(N-1)}{V^2}\binom{N-2}{m}
\int_{x\prec y\;\mathrm{in}\;I}
\left(\frac{V_{xy}}V\right)^m
\left(1-\frac{V_{xy}}V\right)^{N-2-m}\,dx\,dy.
$$

Summing over m uses the binomial theorem and yields
`sum(E[a_m])=binom(N,2)*p(d)`, with p(d) derived in
[DIMENSION_THEORY.md](DIMENSION_THEORY.md). Pair and interval counts within one
order are dependent. Neither Poisson errors for the bins nor independent-pair
binomial errors describe whole-order sampling variability.

This expression conditions on N. Replacing the binomial probability by a
Poisson probability at density N/V would be a different finite-count model.
Likewise the large-count interval-abundance ratios in Glaser and Surya are not
treated as exact finite-N predictions; their analysis discusses slow
convergence. The detectors use independent finite-count calibration examples.

### An exact d=2 check

Rescale the two null coordinates to the unit square. For comparable endpoints,
let a,b be their positive coordinate gaps; their interval volume fraction is
`ab`. Integrating over allowed lower endpoints supplies the weight
`(1-a)*(1-b)`. Therefore

$$
\mathbb E[a_m]=N(N-1)\binom{N-2}{m}
\int_0^1\!\int_0^1
(1-a)(1-b)(ab)^m(1-ab)^{N-2-m}\,da\,db.
$$

Set z=ab and integrate over a first. The resulting weight is
`−(1+z)*log(z)−2*(1−z)`. Differentiating the beta integral gives the exact
closed form

$$
\boxed{\mathbb E[a_m]
=N(h_{N-1}-h_m)
 +(m+1)(h_N-h_{m+1})
 -2(N-1-m)},\qquad 0\le m\le N-2,
$$

where `h_k=sum(1/j,j=1..k)` and h₀=0. The h symbols denote harmonic numbers,
not interval counts. Checks include `E[a_0]=1/2` for N=2,
`E[a_(N−2)]=1/[N(N−1)]`, and the sum `N(N−1)/4`. The implementation is bounded
to the lab's supported event counts to control cancellation and memory. Tests
compare this identity with independent tensor Gauss–Legendre integration of
the polynomial two-gap integral, not a rearrangement of the harmonic formula.
At N<2 there are no endpoint pairs and the returned abundance array is zero.

## The interval-abundance detector

Detector F uses the ten categories

`incomparable, 0, 1, 2, 3, 4–7, 8–15, 16–31, 32–63, 64+`.

Each category count is divided by `binom(N,2)`. The incomparable category has
count `binom(N,2)−R`, so the vector sums to one for N≥2. This includes the
overall relation abundance; dividing only by R would discard that information.
It is defined for an antichain: its vector is `(1,0,...,0)`. It is undefined
when N<2 because there are no unordered pairs.

For every calibrated candidate dimension d, let μ_d be the calibration mean
of these vectors at the same N. The score is the minimum Hellinger distance

$$
S_F(P)=\min_d\left[\frac12\sum_j
  (\sqrt{p_j(P)}-\sqrt{\mu_{d,j}})^2\right]^{1/2}.
$$

Distances remain defined at zero probabilities and lie in [0,1]. This is a
chosen engineering detector, not a likelihood ratio or a confidence level.
The independent validation procedure sets its acceptance threshold. Comparing
with candidate dimensions does not expose the true dimension of a test order.
Candidate classification and structural acceptance are separate outputs.

The five older features are the ordering fraction, height/N, link fraction
conditional on related pairs, mean interval cardinality divided by N−2, and
the fraction of related pairs whose interval cardinality is at least four.
For N<3 the mean denominator is `max(N−2,1)`. Conditional features remain
undefined when R=0; they are not silently replaced by plausible finite values.
The richer search vector concatenates those five features with the ten
abundance probabilities. Some entries are redundant and correlated. Matching
them is a constrained numerical objective, not independent evidence from
fifteen different physical measurements.

## Exact information loss

Relabeling maps each relation, chain and interval to a corresponding object.
Consequently all six detectors' selected summaries are label invariant.
Reversing every relation maps each interval (x,y) to the interval (y,x) of
the dual order with unchanged cardinality. It also preserves R and height.
Thus the selected summaries, including the full unbinned abundance histogram,
are invariant under order duality. Directional counts of minimal and maximal
events swap under duality and can be reported separately; they are not added
to the preregistered detector definitions after seeing holdouts.

The existing three-event V and its dual Λ already show that the selected
summaries are not complete invariants of directed orders. The following
stronger counterexample is not explained merely by reversing time.

Start with lower vertices u₀,...,u₃ and upper vertices v₀,...,v₃. Define P by
`u_i ≺ v_i` and `u_i ≺ v_(i+1 mod 4)`. Define Q by `u_i ≺ v_j` whenever
`floor(i/2)=floor(j/2)`. Add a unique bottom event below all eight vertices and
a unique top event above all eight vertices to both orders. Both then have

| Quantity | P and Q |
| --- | ---: |
| N | 10 |
| R | 25 |
| Longest-chain height | 4 |
| Full abundance histogram a₀,...,a₈ | (16,0,8,0,0,0,0,0,1) |
| Link fraction | 16/25 |
| Mean interval cardinality | 24/25 |
| Minimal / maximal counts | 1 / 1 |

Their existing five-feature vectors and every interval-abundance statistic
are identical. They are neither isomorphic nor dual-isomorphic: remove the
unique minimum and maximum. P's remaining undirected comparability graph is
one eight-cycle, whereas Q's has two disconnected four-cycles. Connectivity
is preserved by both an isomorphism and a dual isomorphism. This also shows
what the histogram has lost: it records how many intervals have each size,
but not which endpoint pairs possess them, how they overlap, or their internal
order types.

This proves insufficiency of these particular summaries to determine an
arbitrary finite order. It does not prove that no finite set of statistics can
characterize geometry under explicit assumptions, nor that the two example
orders settle an asymptotic continuum conjecture.

## An exact overlap of geometric and rank-based constructions

Take two independent uniformly random rankings of N labeled events. Relate
i≺j precisely when i precedes j in both rankings. This is a strict partial
order, the intersection of two total orders. It can be generated without
assigning spacetime coordinates.

Now sample N independent points uniformly in a two-dimensional Minkowski
Alexandrov interval. Its rescaled null coordinates U,V are independent uniform
variables on the unit square. With probability one there are no ties. The U
rank permutation is uniform, the V rank permutation is independently uniform,
and causality is exactly simultaneous increase in both coordinates. Hence
the rank construction and the d=2 fixed-count geometric construction induce
**the same probability law on labeled causal orders**. Fixing the first
ranking and then uniformly relabeling restores the same labeled law; even
without that relabeling, all label-invariant statistics have the same law.

For any measurable order-only detector f, equality of the input distributions
implies equality of the distribution of f(P). It therefore cannot distinguish
these two generating procedures from an observed order. The rank-two family
is an exact-overlap positive control, not a false-acceptance benchmark for an
allegedly nongeometric family. This argument makes no claim that a generic
intersection of three or more rankings has the law of a higher-dimensional
Minkowski interval.

## What the calibration does and does not cover

The finite-N reference distribution depends on the sampling law and region.
All genuine primary samples are uniform inside flat Alexandrov intervals.
Different boundaries, nonuniform sampling, curvature, or selecting special
subintervals can change the summaries. Such changes cannot automatically be
interpreted as evidence against all continuum geometry. Conversely, matching
the summaries does not establish a faithful embedding or reproduce joint
distributions of unmeasured order invariants.

Each order, rather than each pair or interval, is an independent sampling
unit. Repeating independent calibration fits measures some calibration
sensitivity; three fits remain a small sample of that variability. A fixed
list of adversarial generators also cannot establish universal discrimination.
The full protocol records the evaluated populations and confidence criteria.

A coordinate-free growth experiment would require a separately defined law
on orders and tests of its scaling, homogeneity, geometry and dynamics. It may
be worth studying such a law even when these detectors fail, provided their
failure is not converted into evidence for emergence. Gravitational dynamics
would need additional physical assumptions and controlled continuum tests;
claims about black-hole interiors require more still. Nothing here supplies
those assumptions or results.
