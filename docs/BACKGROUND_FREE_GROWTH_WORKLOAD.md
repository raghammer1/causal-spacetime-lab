# Experiment 5: workload selection and pre-primary correction

This note is committed with the verified implementation **before primary data
generation**. The original mathematical protocol remains intact at commit
`4268ad3`; this note records the resource decision and a stream-isolation fix.

## Timing-only pilot

The registered pilot used seed 20261024, phase `pilot`, and reference seed 20261023.
It generated exactly one history per stochastic family and one per deterministic
endpoint, recording only elapsed time and memory. No pilot scientific values
were retained or inspected. All five prefixes and twelve thinnings were timed,
including exact local counts and 4096 sampled four-event motifs per record.
The machine-readable timing record is
[`background-free-growth-pilot.json`](experiments/background-free-growth-pilot.json).

The sum of the eleven stochastic-history times was 12.05120196 seconds; the two
endpoint times summed to 1.21776550 seconds. Projected reference construction was
5.12100702 seconds. The separate fabricated-chain bootstrap benchmark took
0.84699317 seconds. The registered projection retains its conservative fixed
180-second analysis allowance rather than replacing it with that favorable time:

```
projection(R) = 1.5 * (3*R*12.05120196/2 + 1.21776550 + 5.12100702 +180)
R64: 2014.881241s
R32: 1147.194700s
R16:  713.351429s
```

The largest option below the registered 1500-second planning threshold is
**R32 histories per batch**, with three batches and three workers. Preserve all
six stochastic p values, all controls and N=32,64,128,256,512. This gives 1,056
independent stochastic histories, 17,952 stochastic records and 34 deterministic
endpoint records: **17,986 total records**. Retain 2,000 bootstrap draws and the
original conditional-support threshold of 30 positive histories per batch and
100 mean interval exposures. No threshold is weakened for the smaller workload.
The actual primary budget remains 2,700 seconds and a conservative aggregate peak
RSS below 4 GiB. The timing pilot's peak RSS was 104,841,216 bytes.

## Independent-stream correction before primary sampling

Code review found that the first integration smoke used the initially reserved
primary seed 20261025 and reference seed 20261026, with primary operation phases.
It exercised one history per family and two stochastic p settings. Its figures
were inspected for layout; it was an implementation check, not held-out primary
evidence. Keeping those seeds would contaminate the intended separation.

Therefore reserve **primary seed 20261027 and reference seed 20261028** before the
primary run. These are the next unused pair, selected mechanically, without
comparing candidate outcomes. The model, p grid, sample count decision, margins,
uncertainty method and stopping criteria are unchanged. The original smoke is
excluded from all scientific estimates. Future smoke runs use seed 20261021,
reference seed 20261022, and separate `smoke_generation`, `smoke_record`,
`smoke_motifs` and `smoke_thinning` phases. Primary generation uses `generation`,
with `primary_record`, `primary_motifs` and `primary_thinning` phases. Generation
keys omit terminal N. Bootstrap and reference keys are independently addressed.
The pilot and all unit-test fixtures use other seeds and phases.

The original smoke digest was
`cb623de27e1ece08020539bcdfbb3a4c9402515740a42f19673b8c9ac7ab9124`.
Its role and exclusion are retained here as an implementation failure caught
before primary sampling, not silently erased. Partial completed families and
history reconstruction records are also preserved if a resource exception occurs.

## Frozen execution commands

```
python -m pytest -q
python -m causal_lab.growth_study --smoke --workers 1 --output results/growth-smoke-verified
python -m causal_lab.growth_study --histories 32 --workers 3 --output results/growth-primary
python -m causal_lab.growth_study --histories 32 --workers 3 --output results/growth-repeat
```

The two full runs must agree in their deterministic scientific digest. Timings,
process IDs, machine provenance and rendered image bytes are excluded from that
digest but retained in the artifact manifest. No primary outcome will alter the
registered workload or lead to parameter tuning.
