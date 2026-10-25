"""Independent-realization uncertainty, with conditional comparisons paired first."""
from __future__ import annotations
from collections import defaultdict
import numpy as np
from scipy.stats import beta, binom
from .quantum_random import rng_for


def stratified_mean_interval(values, batches, rng, *, resamples=3999, alpha=.05):
    x = np.asarray(values, dtype=float)
    b = np.asarray(batches)
    if x.ndim != 1 or b.shape != x.shape or not len(x) or not np.all(np.isfinite(x)):
        raise ValueError("finite nonempty independent values and matching batches required")
    if resamples < 10 or not 0 < alpha < 1:
        raise ValueError("invalid interval specification")
    if any(np.count_nonzero(b==label)==1 for label in np.unique(b)):
        # Singleton strata cannot estimate within-stratum sampling variation.
        return {"mean":float(x.mean()), "sd":float(x.std(ddof=1)) if len(x)>1 else None,
                "ci95":None,"lower":None,"alpha_lower":alpha,"n":len(x),
                "batch_means":{str(k):float(x[b==k].mean()) for k in np.unique(b)},
                "weak_small_sample":True,"interval_unavailable":"one or more singleton strata"}
    # Pool independent observations, resampling within the fixed batch strata.
    draws = np.zeros(resamples)
    means = {}
    for label in np.unique(b):
        a = x[b == label]
        draws += a[rng.integers(0, len(a), size=(resamples, len(a)))].sum(axis=1) / len(x)
        means[str(label)] = float(a.mean())
    return {"mean": float(x.mean()), "sd": float(x.std(ddof=1)) if len(x)>1 else None,
            "ci95": np.quantile(draws, [.025, .975]).tolist(),
            "lower": float(np.quantile(draws, alpha)), "alpha_lower": alpha,
            "n": len(x), "batch_means": means, "weak_small_sample": len(x)<12}


def binomial_lower(successes, count, alpha=.05):
    if (isinstance(count, bool) or not isinstance(count, (int, np.integer)) or count<1
            or not isinstance(successes, (int,np.integer)) or not 0<=successes<=count
            or not 0<alpha<1):
        raise ValueError("invalid binomial observations")
    return 0. if successes == 0 else float(beta.ppf(alpha, successes, count-successes+1))


def summarize(rows, *, resamples=3999):
    groups = defaultdict(list)
    keys = ("family", "n", "h", "preparation", "delta", "time")
    for row in rows:
        groups[tuple(row[k] for k in keys)].append(row)
    result = []
    for cell, records in sorted(groups.items(), key=lambda x: str(x[0])):
        valid = [r for r in records if r["status"] == "ok"]
        if len({r["unit_id"] for r in valid}) != len(valid):
            raise ValueError("duplicate independent units within a summary cell")
        entry = {**dict(zip(keys,cell)), "attempted":len(records), "valid":len(valid),
                 "failures":len(records)-len(valid), "metrics":{}, "undefined_metrics":{}}
        names = sorted({m for r in valid for m in r["metrics"]})
        for name in names:
            records_m = [r for r in valid if r["metrics"].get(name) is not None and np.isfinite(r["metrics"][name])]
            if not records_m:
                entry["undefined_metrics"][name]=len(valid)
                continue
            values = [r["metrics"][name] for r in records_m]
            if all(not r["stochastic"] for r in records_m):
                if len(values) != 1:
                    raise ValueError("deterministic controls must not be replicated")
                estimate = {"mean":float(values[0]), "n":1, "deterministic":True,
                            "ci95":None, "lower":None, "batch_means":{}}
            else:
                alpha = .05/6 if name in ("shuffle_minus_stress_d3", "phase_minus_stress_d3") else .05
                estimate = stratified_mean_interval(values, [r["batch"] for r in records_m],
                    rng_for("bootstrap",0,"summary",*cell,name), resamples=resamples,alpha=alpha)
            estimate["undefined"] = len(valid)-len(records_m)
            entry["metrics"][name] = estimate
        if cell[0]=="chain" and cell[2]==1 and cell[3]=="ground" and cell[4]==0:
            auc = [r["metrics"].get("edge_auc") for r in valid]
            auc = [v for v in auc if v is not None and np.isfinite(v)]
            if auc:
                successes = sum(v >= .75 for v in auc)
                entry["chain_success"] = {"successes":successes,"count":len(auc),"attempted":len(records),"undefined":len(records)-len(auc),
                    "lower":binomial_lower(successes,len(auc),alpha=.05/3),"alpha":.05/3,
                    "complete_cohort":len(auc)==len(records),
                    "gate_eligible":len(auc)==len(records)}
        result.append(entry)
    return result


def calibration():
    # Numerical uncertainty audit, independent of every scientific state stream.
    rng = rng_for("calibration",0,"normal-coverage")
    hits = 0
    for trial in range(400):
        x = rng.normal(size=24)
        ci = stratified_mean_interval(x,np.repeat(np.arange(3),8),
            rng_for("calibration",0,"coverage-bootstrap",trial),resamples=399)["ci95"]
        hits += ci[0] <= 0 <= ci[1]
    coverage = []
    for n in (6,12,24):
        for p in (.05,.2,.5,.8,.95):
            covered = sum(float(binom.pmf(k,n,p)) for k in range(n+1)
                          if binomial_lower(k,n,.05/3)<=p)
            coverage.append({"n":n,"p":p,"coverage":covered})
    return {"phase":"calibration","normal_trials":400,"normal_coverage":hits/400,
            "normal_coverage_mc_se":float(np.sqrt((hits/400)*(1-hits/400)/400)),
            "binomial_exact_coverage":coverage,
            "interpretation":"Coverage audit only; no threshold tuning or fitted classifier."}
