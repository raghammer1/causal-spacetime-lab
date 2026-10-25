# Experiment 2 mathematical foundations

These are calculations in a specified flat geometry. They justify a reconstruction
test; they do not assert a microscopic ontology or a theory of gravity.

## Volume and independent sampling

Use `ds²=dt²−|dx|²`, c=1, with endpoints `(0,0)` and `(T,0)` in spacetime
dimension d. At time t the allowed spatial ball has radius q=min(t,T−t).
Writing `B_k=pi^(k/2)/Gamma(k/2+1)` for unit k-ball volume gives

$$
V_d(T)=2B_{d-1}\int_0^{T/2}q^{d-1}dq
=\frac{B_{d-1}T^d}{d2^{d-1}}.
$$

Thus V₂=T²/2, V₃=pi*T³/12 and V₄=pi*T⁴/24. This matches the flat-volume
coefficient in Eq. (4) of [Roy, Sinha and Surya, PRD 87, 044046 (2013)](https://arxiv.org/abs/1212.0631).
Fixed N means independent uniform positions conditional on the Poisson count.
Optional density sampling draws `N~Poisson(rho*V_d)`, with rho measured per
d-dimensional physical spacetime volume. N fixed is not itself a Poisson count.

For uniform spacetime volume, q has CDF `(2q/T)^d`. Draw U uniformly and set
`q=(T/2)*U^(1/d)`, then independently choose t=q or T−q with equal probabilities.
Conditional on q, radius has CDF `(r/q)^(d−1)`: use another independent W and
`r=q*W^(1/(d−1))`. Normalize an isotropic Gaussian vector in d−1 dimensions
for the independent sphere direction. In one spatial dimension this is a random
sign. Uniform radius in dimensions greater than one, uniform time, or a spatial
bounding-box draw would all give the wrong measure.

Independent moment checks follow directly:

$$
E[t]=T/2,\quad \operatorname{Var}(t)=\frac{T^2}{2(d+1)(d+2)},\quad
E[x_i]=0,\quad E[x_i^2]=\frac{dT^2}{4(d+1)(d+2)}.
$$

The variables `(2q/T)^d` and `(r/q)^(d−1)` should be uniform; sphere directions
have zero means and covariance `I/(d−1)`. These checks are independent of the
dimension estimator. The d=2 implementation is also compared to the existing
uniform-null-coordinate generator. The two algorithms need not produce identical
coordinates from the same seed, because they consume different random variables.

## Pair probability and the factor of two

For uniformly independent points X,Y, let R count each comparable unordered pair
once. With strict timelike relations, null ties have probability zero in the
ideal sampling law. A matrix entry `A[i,j]` is true when
`t[j]−t[i] > |x[j]−x[i]|`. Hence `R=sum(A)` for a valid strict order.

Let C_d=V_d(1), S the area of the unit (d−2)-sphere, and I the full interval.
The probability that Y lies to the future of X inside I is the future subinterval
volume averaged over X. Both possible time orientations give

$$
p(d)=\frac{2}{V^2}\int_I d^dx\,V_d\left(\sqrt{(T-t)^2-r^2}\right).
$$

This integral can be evaluated independently. Use radial measure S*r^(d−2)dr dt,
then u=t−r, v=t+r, with `0<u<v<T`, and `dt dr=du dv/2`.
Writing a=(T−v)/T, b=(T−u)/T gives `0<a<b<1`. Its dimensionless integral is

$$
\int_0^1 db\int_0^b da\,(b-a)^{d-2}a^{d/2}b^{d/2}
=\frac{B(d/2+1,d-1)}{2d},
$$

where the inner substitution a=bz produces the beta integral and the remaining
integral is of b^(2d−1). Since `C_d=S/[2^(d−1)*d*(d−1)]`, restoring coefficients gives

$$
p(d)=(d-1)B(d/2+1,d-1)
=\frac{\Gamma(d+1)\Gamma(d/2)}{2\Gamma(3d/2)}.
$$

This yields p(2)=1/2, p(3)=8/35 and p(4)=1/10. The code evaluates the gamma
expression through logarithms; independent deterministic quadrature checks the
geometric integral. The dimension formula is the Myrheim–Meyer construction;
[Roy, Sinha and Surya, Eqs. (6), (11), (12)](https://arxiv.org/pdf/1212.0631)
record the relevant chain-count convention. Their relation-count/mean-count²
normalization is p(d)/2. Our `R/binom(N,2)` is p(d); confusing them would introduce
a factor-of-two error. Historical attribution and original thesis links are in
[THEORY.md](THEORY.md).

At fixed N≥2, linearity of expectation gives `E[R/binom(N,2)]=p(d)` exactly under
this sampling model, even though pair indicators sharing an event are correlated.
The nonlinear inverse generally has finite-sample bias:
`E[p_inverse(r)] != p_inverse(E[r])`. Report both ensemble quantities separately.

## Inversion, uncertainty and interpretation

Use bounded bisection on real d∈[1,10], checking monotone decrease over the
implemented interval and exact known values. N<2 has no ordering fraction. r=0
lies outside this finite domain; r=1 returns the boundary d=1. No invalid fraction
is clamped into the range. Malformed or nontransitive structures are rejected;
an acyclic adjacency matrix must first receive its transitive closure.

The estimator takes only the order matrix. It neither reads nor guesses the
coordinates or generating dimension from metadata. Truth labels are used only
by separate training/evaluation procedures. Absolute density or duration is not
needed to invert the dimensionless fraction, unlike proper-time reconstruction.

Ensemble bootstrap intervals resample independent orders, not pairs within an
order. Wilson intervals supplement binary accuracy estimates, especially at
100% observed accuracy. Pointwise intervals do not establish simultaneous coverage,
and bootstrap uncertainty does not quantify model misspecification or validate
a spacetime interpretation for arbitrary orders.

## Why adversaries are possible

In a balanced two-layer partial order, the only possible relations are a*b
lower-to-upper pairs. Independent inclusion with probability q gives
`E[r]=q*a*b/binom(N,2)` while the height cannot exceed two. Choosing q using
separate calibration data can imitate a spacetime's expected fraction without
encoding its full interval or chain structure. This construction is a deliberate
counterexample to using r alone as evidence of geometric resemblance.

For any related pair i≺j, the internal interval is the set of k with i≺k≺j.
Its cardinality counts elements, not paths. The abundance of zero-cardinality
intervals counts links. These are invariant under relabeling and involve no
coordinates. Their exact definitions can be tested independently; whether a
particular collection distinguishes specified ensembles is a separate numerical
question. The V order and its dual Λ have identical selected summaries yet
different numbers of minimal elements, demonstrating that these summaries are
not a complete invariant of an order.

Passing finitely many observables cannot prove manifoldlikeness. A background-free
model still needs a generative law on orders, label-invariant predictions,
appropriate limits and stable continuum behavior. A curved-background extension
needs correct invariant volume and independent continuum comparisons; the flat
dimension formula alone is insufficient in general curvature. A black-hole model
would additionally require consistent dynamics and controlled gravitational limits.
Neither is implemented in this experiment.
