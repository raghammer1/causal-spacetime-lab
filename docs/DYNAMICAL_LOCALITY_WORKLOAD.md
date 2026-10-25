# Frozen Experiment 7 workload

This record precedes primary generation. The [protocol](DYNAMICAL_LOCALITY_PROTOCOL.md)
was first committed at5b71924. Resource-only amendments A1 and A2 and every rejected
pilot are visible in history. The final scientific implementation is9afe2cf;
the forthcoming workload commit adds this record and its machine-readable freeze.

[Final feasibility record](experiments/dynamical-locality-workload.json)
contains exact source hashes, all cost terms, choices and the N6 censor. The
resource-check script is `scripts/freeze_dynamical_workload.py`.

| Quantity | Frozen value |
|---|---:|
| Matter vertices |4,5|
| Total matter/link qubits |10,15|
| Parameter cells per size |6|
| E batches |3|
| E preparations per batch/cell |4|
| Independent E preparations per cell |12|
| Total independent E preparations |144|
| Symmetric Splus/Sempty preparations |24|
| Ground-state preparations |12|
| Exact N4 Gibbs laws |12|
| Independent-link controls |36|
| Full coherent/dephased N4 measurement comparisons |6|
| Unselected draws per full/perturbed age and equilibrium law |8|
| Worker/BLAS threads |1|
| Precision |complex128/float64|
| Peak RSS cap |2GiB|
| Hard primary/replay cap |45 minutes each|

The maximum bundle times retained across all three complete pilots are
.462274209 seconds at N4 and11.544828583 seconds at N5. Maximum fixed costs are
7.500291835 and49.726938626 seconds; separately recorded postprocessing costs reach
10.947195125 seconds. Applying the registered factor2 yields:

| E preparations per batch | Complete mandatory projection |
|---|---:|
|12|5611.587724 seconds|
|8|3882.564922 seconds|
|4|2153.542120 seconds|

Only R4 fits A2's2400-second planning allowance. Slower old-implementation timing
is retained in this worst-case calculation. None of these numbers ranks scientific
outcomes. All pilot scientific arrays/figures were temporary and discarded.

N6's quantum timing was censored after14.344800333 seconds, exceeding the
14.335714286-second threshold. Its conservative minimum-cohort planning contribution
alone is already2409.926456 seconds. This rejects admission under the selected
resource policy; it does not prove that every N6 case, a different optimized
implementation, or other hardware is intrinsically infeasible. No partial N6
quantum result is retained. Exact N6 classical graph counterexamples remain a
separate mathematical calculation.

With12 independent E units per cell, an all-success cell cannot certify joint
success probability>.8 with the registered multiplicity adjustment. The design can
still establish sufficiently large failures; any unresolved cell remains
inconclusive. This power limitation is explicit before primary generation and is
not repaired by counting dependent pairs, times or Born draws as extra units.

No Hamiltonian, observable, parameter, scientific margin, precision or decision
threshold was changed by resource selection. The source passed1,129 tests and an
end-to-end CLI; the first pilot, optimization, A1 rejection and A2 reuse remain
reviewable in the computational plan and three machine-readable timing records.
