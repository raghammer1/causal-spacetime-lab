# Verification evidence

These files supplement the original primary manifest without modifying its data.

| File | Scope |
|---|---|
| `count_audit.json` | All file hashes/grids, independent reconstruction/counts for fixed batch0/history0 selection: 13 histories, 221 records, zero failures. |
| `provenance_audit.json` | Frozen configuration, 29 source/document hashes, reference fits and primary/smoke stream separation. |
| `statistics_audit.json` | 4,877 independently reconstructed points, bootstrap intervals and contrasts, zero discrepancies. |
| `statistics_review.md` | Complete numerical review, all candidate references and adverse/insufficient outcomes. |
| `visual_review.md` | All nine primary figures inspected; scope and calibration caveats retained. |
| `full_repeat.json` | Equal scientific digest and byte equality of 31 nonmetadata artifacts; both clean source commits and costs. |
| `repeat_metadata.json` | Complete metadata of the second full run. |
| `smoke_audit.json` | Corrected independent smoke streams; 153 records and zero failures. |
| `exact_d2_check.json` | Secondary exact enumeration: one 2+2 and two 3+1 patterns among 24 rank permutations. No primary rule changed. |

The [statistical audit source](../../../../scripts/review_growth_statistics.py)
does not import `growth_statistics`; it reconstructs the registered aggregation
and random weights independently. It shares the previously verified motif
catalog. The [count audit](../../../../src/causal_lab/growth_audit.py) uses independent
closure and counting formulas, and separately replays the production observables.
Neither an agreement between implementations nor a complete deterministic replay
proves the correctness of a continuum interpretation or exact bootstrap coverage.

The initial smoke reused the originally reserved streams. It was excluded before
primary sampling and the mechanical seed amendment is documented in the
[workload note](../../../BACKGROUND_FREE_GROWTH_WORKLOAD.md). This correction,
the false small-N TV rejection and dimension-interval coverage miss are retained.
