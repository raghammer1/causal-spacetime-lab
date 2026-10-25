# Independent Experiment 6 statistical archive audit

Source commit: `6dd659865973261ca4f2437d02f1f6bf4d088f69`.

Checked 1818 raw rows, 141 summary cells and 19630 metric estimates. Reconstructed 3999-draw bootstrap distributions through multiplicity weights and explicit order-statistic interpolation; recomputed binomial lower bounds by finite-tail bisection.

**289132 checks; 0 failures**, absolute tolerance 2e-12.

This verifies arithmetic, pairing, independent-unit counts and failure denominators. It does not establish nominal bootstrap coverage: the retained calibration covered 365/400 normal means (91.25%) with nominal 95% intervals.

## Chain reconstruction

| n | Successes | Exact lower bound | Mean AUC 95% lower | Registered gate |
|---|---:|---:|---:|---|
| 6 | 24/24 | 0.843160717157 | 1 | passes |
| 8 | 24/24 | 0.843160717157 | 1 | passes |
| 10 | 24/24 | 0.843160717157 | 1 | passes |

## Audit counts

- all_undefined_metrics: 141
- batch_grid: 19630
- batch_mean: 48977
- binomial_alpha: 3
- binomial_lower: 3
- chain_success_fields: 18
- cohort_denominators: 423
- conditional_null_count: 441
- conditional_null_mean: 1764
- cut_mean: 7272
- independent_units: 141
- metadata_row_count: 1
- metric_flags: 78520
- metric_grid: 141
- phase_pair_exists: 576
- phase_paired_effect: 576
- raw_edge_auc: 630
- registered_ground_batch_grid: 18
- registered_ground_count: 18
- shuffle_paired_effect: 441
- source_clean: 1
- source_complete: 1
- source_phase: 1
- summary_alpha_lower: 19630
- summary_cell_grid: 1
- summary_ci95: 19590
- summary_lower: 19630
- summary_mean: 19630
- summary_sd: 19630
- summary_unique_cells: 1
- unavailable_interval: 9835
- undefined_count: 19630
- unique_raw_sample: 1818

## Maximum absolute numerical differences

- batch_mean: 3.55271e-15
- binomial_alpha: 0
- binomial_lower: 1.11022e-16
- conditional_null_mean: 2.66454e-15
- cut_mean: 1.77636e-15
- phase_paired_effect: 0
- raw_edge_auc: 0
- shuffle_paired_effect: 1.66533e-16
- summary_alpha_lower: 0
- summary_ci95: 7.10543e-15
- summary_lower: 7.10543e-15
- summary_mean: 3.55271e-15
- summary_sd: 4.44089e-16
