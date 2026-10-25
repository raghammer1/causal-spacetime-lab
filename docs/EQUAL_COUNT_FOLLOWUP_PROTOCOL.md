# Equal-count follow-up protocol — 2026-10-25

This is a **post hoc diagnostic prompted by the primary study**, specified before
running the follow-up. It does not replace or amend the primary observations.

The primary comparison at expected count approximately 161.269894 had relative
mean difference (T=2 minus T=0.5) 0.0171271, with pointwise 95% bootstrap interval
[0.0013780, 0.0320886], about 2.19 estimated standard errors from zero. Three other
equal-count comparisons included zero. Pointwise intervals across multiple
comparisons permit chance exclusions; the observed discrepancy still warrants
investigation. Exact same-sample rescaling already passes the independent test.

## Hypothesis and independent controls

Under the specified generator the normalized chain distribution depends only on
expected count. A persistent difference at equal expected count would therefore
indicate a numerical or sampling problem, rather than a novel physical effect.
Use an independent seed and more trials to investigate the observed discrepancy.
Retain all draws and the same primary analysis code, count diagnostics, explicit
small order/negative-control checks and bootstrap procedure.

## Fixed follow-up plan

- Seed: **20261026**, independent of the primary study.
- Densities: **80.63494719327188** and **1290.1591550923501**.
- Durations: **0.5** and **2.0** (Cartesian grid, four cells).
- Repeats: **2,000 per cell**, 8,000 new primary draws in this diagnostic.
- Bootstrap: **5,000** resamples; order checks first 20 draws with N at most 256;
  three independent benchmark samples per cell.
- Primary diagnostic: equal-count relative mean contrast at expected count
  approximately 161.269894, T=2 minus T=0.5. The off-diagonal cells supply count
  and reconstruction controls; they are not additional confirmatory targets.
- No further seed selection or repeated follow-up runs based on the outcome.

```bash
python -m causal_lab.scaling --seed 20261026 --densities 80.63494719327188 1290.1591550923501 --durations 0.5 2 --repeats 2000 --bootstrap 5000 --out results/equal-count-followup
```

## Adverse and inconclusive outcomes

If the follow-up 95% contrast interval excludes zero in the original positive
direction, report a replicated discrepancy requiring further investigation. A
negative exclusion is also adverse to the distributional equality prediction,
but does not replicate the original direction. If the interval includes zero,
the follow-up does not resolve a persistent difference; this is not proof of
equality. Algorithm, chain, control or count failures invalidate interpretation.

Publish the original and follow-up outcomes together, without pooling them into
a supposedly preregistered confirmatory result. Both retain finite-sample and
bootstrap limitations. The standard CLI metadata's protocol hash identifies the
original method protocol; the follow-up archive also includes this plan's hash
in `followup_context.json` to distinguish the amended sampling plan.
