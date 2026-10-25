# Experiment 5 primary figure and interpretation review

Reviewed all nine rendered PNGs in `results/growth-primary` and checked the corresponding primary and summary data. No blocking layout or scientific-label issue was found. This review did not modify the primary archive or tracked source. The independent full repeat was still running when the review was prepared; repeat agreement is not asserted here.

## Rendered figures

| Figure | Review finding |
| --- | --- |
| `selected_history_22.png` | All six fixed-p panels are legible, use shared axes, identify the target 1/24, and show the prespecified first eight histories in batch 0. These are selected trajectories rather than uncertainty intervals. The smallest-p trajectories are still rising at N=512; the figure does not establish monotone collapse throughout the observed range. |
| `ensemble_dynamics.png` | Ordering fraction, height fraction, and reference-equivalent global dimension are separated into growth and control panels. Labels identify reference equivalence rather than physical dimension. One legend covers a small segment of a growth ordering-fraction curve; this is a minor presentation issue, not a blocker or reason to regenerate the scientific archive. |
| `ensemble_22.png` | Growth and control panels, pointwise 95% intervals, and the 1/24 target are clear. The matched bipartite control is explicitly identified as a deliberately matched control. |
| `forbidden_motif_joint.png` | Joint 2+2 and 3+1 behavior versus ordering fraction is legible. Connected ensemble means and the N=512 outer rings are explained. The plot does not represent these correlated observables as independent evidence. |
| `primary_signature.png` | All six families and all eight contrasts per family are visible. The caption correctly identifies the 48-entry simultaneous band and the ±0.005 equivalence margin. Failed and inconclusive contrasts remain visible. |
| `thinning_contrasts.png` | Three source sizes and three observables are shown with readable family labels. Captions distinguish paired whole-history contrasts and pointwise uncertainty from the simultaneous primary screen. |
| `conditional_laws.png` | All seven selected diagnostics are legible. Growth and artificial controls use d=2 as the displayed reference, while Minkowski controls use their own dimensions; the other reference comparisons remain in the machine-readable tables. Insufficient low-p size-eight support is indicated, and undefined matched-control values are not drawn as zero. |
| `interval_support.png` | Minimum per-batch contributing-history and interval-exposure counts are visible for interval sizes 2, 4, and 8. The thresholds 30 and 100 and the logarithmic color scale are identified. Counts of zero are legitimate support counts. |
| `reference_equivalent_dimensions.png` | Global and local inversions are separated, uncertainty is visible, and the legend is outside the panels. Missing or out-of-domain inversions are identified as undefined. The scope statement prevents treating these inversions as reconstructed geometric dimensions. |

## Outcome checks

The registered growth screen has **48 entries: 23 contradict the specified signature, 19 meet the equivalence margin, and 6 are inconclusive**. Every one of the 18 level comparisons at N=128, 256, and 512 lies below the target by more than the margin with its simultaneous band. All six fixed-p families therefore have status `finite_signature_failure`.

| Fixed p | Mean t22 at N=512 | Pointwise 95% interval |
| --- | ---: | ---: |
| 0.005 | 0.00050553 | [0.00048642, 0.00052535] |
| 0.01 | 0.00695585 | [0.00677944, 0.00712082] |
| 0.02 | 0.00973045 | [0.00958021, 0.00986986] |
| 0.05 | 0.00103320 | [0.00100820, 0.00105915] |
| 0.1 | 0.00012149 | [0.00011885, 0.00012415] |
| 0.3 | 0.000001768 | [0.000001715, 0.000001818] |

The d=2 Minkowski and matched height-two controls each meet all eight margins in their **separate** control screens. Their N=512 means are respectively 0.04157918 and 0.04163650, near 1/24. These control screens are not part of the 48-entry growth coverage. The deliberately matched control has height at most two, no nonempty open intervals, and exactly zero 3+1 density. Its success confirms that this signature alone is insufficient for geometric identification. It is not a candidate intrinsic growth model.

All six growth families have large connected-size-two and four-motif-law residuals against the displayed d=2 reference at N=512. This supports a structural mismatch without implying that every individual feature rejects every family. The p=0.005 size-eight conditional diagnostics remain **insufficiently supported**: the minimum batch has only 16 contributing histories and exposure 38, below the registered thresholds 30 and 100. They must not be relabeled as agreement or rejection.

## Negative calibration findings and uncertainty limits to preserve

The Minkowski reference controls meet the seven practical conditional margins, but practical equivalence is weaker than exact agreement:

- For d=2 at N=512, the local reference-equivalent dimension is 2.01985 with pointwise 95% interval [2.00740, 2.03278], which excludes 2. The global inversion is 1.99981 with interval [1.99334, 2.00586]. These are reference-calibration diagnostics, not inconsistent physical dimensions.
- The d=2 connected-size-two residual is −0.007397 with interval [−0.012165, −0.002767], and the connected-size-eight residual is −0.005313 with interval [−0.009048, −0.001707]. Both meet the practical ±0.02 margin while their pointwise intervals exclude zero. Preserve this finite-sample calibration discrepancy rather than claiming exact conditional-law recovery.
- All three Minkowski four-motif total-variation percentile intervals have lower endpoints above their point estimates. The total-variation norm is nonsmooth at equality and bootstrap noise introduces positive bias. Do not use a positive percentile lower bound to claim exact-law rejection; the registered practical-margin comparison has a different interpretation.
- The semiorder control has structurally zero 2+2 and 3+1 density. Its observed absence of connected small open intervals must not be promoted to a theorem that every open interval in every finite semiorder is an antichain. The matched height-two control's empty open intervals, in contrast, are exact by construction.

## Scientific decision and scope

These results support stopping parameter optimization within ordinary classical sequential growth for the stated Minkowski uniform-sampling target. The decisive asymptotic restriction is mathematical: under the Brightwell–Georgiou hypotheses, the relevant finite-suborder limits are almost semiorders and have vanishing 2+2 and 3+1 densities. Positive-density Minkowski obstructions cannot be repaired by finite-window fitting or by switching to N-dependent coupling arrays within the theorem's scope.

For fixed p, the stronger elementary result is almost-sure convergence to the chain **sampling law** along a single coherent infinite history. This does not say that the entire infinite order becomes a chain or that height divided by N tends to one. Sparse incomparable pairs survive. The observed N≤512 trajectories are finite crossover evidence; the smallest-p cases have not visibly reached their asymptotic regime.

The useful outcome is an explicit obstruction and a diagnostic failure mode, not evidence of physical spacetime emergence. Further work should first specify a causal dynamics and convergence notion that can retain nonzero forbidden-motif densities while preserving coherent growth and clearly stated covariance requirements. A controlled continuum claim would also require a nondegenerate local limit, appropriate interval-volume and longest-chain scaling, stability under coarse graining, and an identifiable relation to continuum causal and volume structure. These are mathematical requirements to formulate and test, not a license to tune another recognizer.

## Run provenance checked

The primary archive records 1,056 stochastic histories, 17,952 stochastic rows, and 34 deterministic endpoint rows, totaling 17,986. There are three independent batches of 32 histories in each of 11 stochastic families. The primary seed is 20261027 and the independently generated reference seed is 20261028. Reported total runtime is 664.9714 seconds and the conservative memory envelope is 1,066,713,088 bytes; both satisfy the registered bounds. The scientific digest is `534c51d1745f4d370a87ced03b895b5ff935e3811a362f9349554b164f0a57da`.
