# Experiment 5 archive

This is the complete primary output of clean source commit
`9fbf2d5f979693999b3aff50890b5d1dce1eb138`, with independent verification records
added afterward. See the [scientific report](../../BACKGROUND_FREE_GROWTH_RESULTS.md).

- `raw/*.jsonl.gz`: 17,986 dependent prefix/thinning records, including endpoints.
- `histories.jsonl.gz`: 1,056 stochastic and two deterministic reconstruction records.
  Primitive growth edges are packed row-major, little-bit-order, with matrix shape.
  References retain synthetic coordinates; explicit controls retain utilities or layers.
- `references.json.gz`: independent calibration outcomes and exact d2 tables.
- `summary.json`, `primary.json`, CSVs: all estimates, support, uncertainty and failures.
- Nine PNGs: scientific figures generated from the frozen summaries.
- `metadata.json`: configuration, clean source/hash provenance and full execution costs.
- `manifest.json`: original writer's 32 artifact checksums; it does not hash itself.
- `verification/`: independent numerical/statistical reviews and full-repeat evidence.
- `publication_manifest.json`: hashes every published archive file except itself,
  plus named audit source files relative to the repository root.

The full repeat has the same scientific digest and byte-identical copies of all
31 nonmetadata writer artifacts. Its differing runtime metadata is retained in
`verification/repeat_metadata.json`; duplicate scientific files are not stored twice.

```
534c51d1745f4d370a87ced03b895b5ff935e3811a362f9349554b164f0a57da
```

From the repository root:

```bash
python -m causal_lab.growth_audit docs/experiments/background-free-growth-v1 --output results/growth-audit.json
python scripts/review_growth_statistics.py docs/experiments/background-free-growth-v1 --output-prefix results/growth-statistics-review
```

The statistical review deliberately validates this registered full archive and
its scientific digest. It is not a general-purpose classifier or a new experiment.
Both audits write outside the archive and fail on detected discrepancies.
