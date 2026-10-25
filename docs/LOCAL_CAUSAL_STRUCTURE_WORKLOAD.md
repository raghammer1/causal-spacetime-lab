# Experiment 4: workload frozen before primary outcomes

Protocol commit: `e92c6e4`. Baseline: `8dccf043991db552d93e5b3a1429841ef25571dc`,
Experiment 3 PR #3 merged, with the post-merge Python 3.10/3.14 CI successful:
[run 40160786346](https://github.com/raghammer1/causal-spacetime-lab/actions/runs/40160786346).

The timing-only pilot used seed 20261024, distinct from primary seed 20261025.
It generated at most two orders per region/dimension/count and two search donors
per dimension/count. Synthetic generation and exact reference enumeration were
also timed. No scientific values, match rates, search acceptance counts or unseen
family outcomes were printed, retained or inspected. Timing measurements and
source hashes are in [resource_pilot.json](experiments/local-causal-structure-v1/resource_pilot.json).
The pilot ran after implementation integration tests and before primary sampling.

The aggregate per-repetition serial times were 0.663419 seconds for the complete
27-cell region grid, 0.615051 seconds for all synthetic orders and exact pairs,
and 7.954380 seconds for the complete nine-cell search grid including all three
feature-extraction checkpoints. Reference work projected to 5.099283 seconds.
An outcome-independent 180-second analysis allowance is included. A separate
benchmark on fabricated categorical records took about 0.40 seconds per full
three-fit/600-parent/2,000-bootstrap conditional summary.

The committed selection rule gives, in seconds,

```
1.5 * [3 * {R*(0.663418666+0.615051289) + F*7.954380354}/2
       + 5.099283447 + 180].
```

For **R=200, F=32**, this is **1425.676 seconds (23.761 minutes)**, below the
30-minute planning ceiling. It is the first eligible choice in the registered
descending R, then F ordering; all smaller candidates were also eligible.
Select the full workload without changing any scientific criterion:

- Three independent fits; dimensions 2, 3, 4; event counts 64, 128, 256.
- 200 independent parent orders or exact pairs per applicable cell.
- 32 fresh diamond search donors per fit/dimension/count.
- 64, 256, 1024 switch attempts per donor at those sizes, respectively.
- Each d3/d4 fit has 5,000 four-event and 2,000 eight-event reference orders.
  d2 uses complete 24/40,320 permutation tables, with no fitted-reference noise.
- 4,096 sampled global four-subsets per parent; exact interval statistics.
- 2,000 bootstrap replicates; whole-parent, independent-reference and fit levels
  as defined in the protocol. No intervals are treated as independent parents.
- Expected records: 31,392 parents/checkpoints, 3,600 exact pairs, 864 searches,
  and 42,000 independently sampled reference orders.

Three workers, a 45-minute primary computation budget and conservative aggregate
peak RSS below 4 GiB remain fixed. Outputs must report resource overruns rather
than substituting a favourable partial run. Publication and figure rendering
overhead is reported separately from the primary computation.

## Implementation interpretation fixed before execution

“Existing replacement edge” in the switch proposal means an edge already in the
current **Hasse adjacency**, not any transitive relation in the order. A replacement
that is an existing transitive but non-cover relation is allowed as an adjacency
proposal; explicit closure then determines whether it is unchanged, cyclic or
violates the old signature. Every proposal gets one outcome without resampling.
This is a specified bounded search, not a proof of irreducibility or mixing.

Global descriptive correlations use complete parent records and are exploratory;
they do not constitute independent evidence or a trained discriminant. Undefined
dimension inversions remain missing and their counts are reported. Synthetic
orders are compared with each candidate reference law, without selecting a label.
Covariance/correlation matrices use complete cases across all listed global/local
quantities. Two selected correlation pairs are fixed here before outcomes:
global n22 density versus normalized overlap variance, and the per-parent size8
connected fraction versus mean size8 n22 density. Their pointwise hierarchical
whole-parent bootstrap retains missing-parent counts and uses pairwise complete
cases; missing or zero-variance resamples are not silently discarded. Global
scalar means explicitly condition on a defined value. Pooled search Wilson
intervals are descriptive; the registered movement evidence uses per-fit Wilson
intervals and paired whole-donor changes.
Conditional primary declarations remain restricted to diamond/slab N=256 cells;
boxes are valid flat geometries outside the causal-convexity theorem's scope.

## Frozen execution and independent replay

```
python -m causal_lab.local_structure_study --workers 3 --output results/local-causal-structure-v1
python scripts/audit_local_structure.py results/local-causal-structure-v1
python -m causal_lab.local_structure_study --workers 3 --output results/local-causal-structure-repeat
```

Compare deterministic scientific digests across complete runs. Preserve failures,
all checkpoints, rejection categories and inconclusive/insufficient-support cells.
The results report will distinguish derivations, measurements and unresolved
questions. This note and the verified implementation must be committed before
the first primary run.
