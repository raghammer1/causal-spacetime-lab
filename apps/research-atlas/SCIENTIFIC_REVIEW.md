# Scientific editorial audit

The atlas editorial content is pinned to verified main commit
`9bc5984c656271c247354e0079fd900702642064`. It does not amend the scientific
implementations, reports, protocols or archived measurements. `src/data/editorial.ts`
contains five experiment narratives, eight scoped evidence-map claims and thirteen
educational concepts. Every entry links its supporting repository documents;
experiment pages additionally link raw artifacts and implementation modules.

The review read the five complete results reports, their registered protocols,
the equal-count follow-up plan, the theory and continuum documents, and the
research log. Generator contracts in `core.py`, `dimension.py` and `growth.py`
were checked against the explanatory rules. Archive conversion and numeric schema
checks are documented separately by the data pipeline.

## Evidence and interpretation checks

| Experiment | Numerical evidence retained | Exact result or established mathematics | Important adverse result / scope |
| --- | --- | --- | --- |
| 1 | 4,200 primary draws; 8,000 independent follow-up draws kept separate | Null-coordinate normalization V=T²/2; asymptotic chain estimator; exact controls | All 21 mean-bias intervals remain below zero. Original equal-count discrepancy is not erased by its nonreplication. |
| 2 | 200 orders per dimension/count; all three N=256 classifications 200/200 with Wilson lower bound 98.1% | Pair probability p(d), with unordered-pair normalization | All 1,800 matched two-layer controls fool the fraction detector; d3/N256 mean estimate remains biased. |
| 3 | Three separate fits; 52,218 records; all six detectors fail registered advancement | Nondual old-summary collision; rank-two/diamond full-law equivalence | Zero searches meet the full 15-component criterion. Some failed searches still pass detectors. Rank-two overlap is a positive control. |
| 4 | All 42 primary practical-equivalence checks; d4 slab global4.5813 versus local3.9948 | Conditional count identity, motif/overlap identities; exact extended-vector collision | Spatial boxes retain clipping bias; 528 searches never move; TV bootstrap bias; 12-event extension is postregistration. |
| 5 | 1,056 independent stochastic histories; 17,986 dependent records; all six fixed-p families fail | Fixed-p chain-sampling limit; ordinary-CSG almost-semiorder restriction | Matched height-two control passes the same finite screen; d2/N32 secondary TV falsely rejects a reference; sparse intervals remain missing. |

## Statistical definitions preserved

- Experiments 1–4 primarily report **pointwise** intervals. They are not universal
  simultaneous confidence bands and do not quantify model misspecification.
- Experiment 1 controls reuse event counts; they are paired, not new independent
  physical draws. The post hoc follow-up is a separate diagnostic.
- Experiment 2 whole orders are independent units. Pair indicators within an order
  are correlated. Mean inversions differ from an inverse of the mean.
- Experiment 3 per-fit Wilson bounds condition on their fit. Hierarchical bootstrap
  resamples fits and whole orders, maintaining detector/search-stage pairing.
  Observed fit ranges are not confidence intervals.
- Experiment 4 conditional estimates are fitwise ratios of pooled counts, averaged
  equally across fits. They are not mean per-parent ratios. Overlapping intervals
  are not independent observations.
- Experiment 5 prefixes and thinning replicas remain in the same history cluster.
  The registered primary screen has approximate simultaneous bands over 48 entries;
  secondary pointwise intervals are labeled separately. Reference-control screens
  have their own eight-entry bands. Seed batches are not resampled as populations.
- TV percentile intervals may have lower bounds above a point estimate. Do not
  silently recenter them or interpret them as validated exact-law tests.
- Missing interval support is unavailable, not zero, success, or agreement.

## Scope of the Experiment 5 no-go

The broader restriction is for the nonnegative-coupling classical sequential-growth
class with t₀ or t₁ positive in Brightwell and Georgiou, under their expected
finite uniformly sampled labeled-suborder convergence. Their approximation by
semiorders in expected o(N²) pair-edit distance forces induced 2+2 and 3+1 densities
to vanish; a nondegenerate Minkowski diamond in d≥2 has positive 2+2 probability.
This does not cover every altered dynamics, quantum model, local scaling limit or
Lorentzian metric limit. Fixed-p chain-sampling convergence also does not imply
that the infinite order is total or that H/N→1.

Primary sources checked online:

- [Rideout and Sorkin, Classical Sequential Growth Dynamics for Causal Sets](https://arxiv.org/abs/gr-qc/9904062).
- [Brightwell and Georgiou, Continuum Limits for Classical Sequential Growth Models](https://nicholasgeorgiou.webspace.durham.ac.uk/wp-content/uploads/sites/199/2021/04/contlim.pdf), definitions1.2–1.3 and theorems1.4–1.6.
- [Roy, Sinha and Surya, The Discrete Geometry of a Small Causal Diamond](https://arxiv.org/abs/1212.0631), supporting the dimension normalization and curved-versus-flat distinction.

- [Finkelstein, Past-Future Asymmetry of the Gravitational Field of a Point Particle](https://doi.org/10.1103/PhysRev.110.965), supporting the distinction between the regular Schwarzschild horizon and singular behavior.
- [Penrose, Gravitational Collapse and Space-Time Singularities](https://doi.org/10.1103/PhysRevLett.14.57), original singularity work linked for further reading.

The water comparison and microscopic spacetime drawing are analogies/speculation.
No experiment measures physical spacetime discreteness, derives gravitational
field equations, models a black-hole interior or resolves a singularity. The
classical event horizon must remain distinct from a curvature singularity.
