"""State diagnostics and independent evaluation, never coordinates as inference input."""
from __future__ import annotations
from itertools import combinations
import numpy as np
from .quantum import entropy, reduced_density, pair_observables
from .quantum_geometry import infer_geometry, geometry_metrics, evaluate_inputs, epsilon_agreement, shuffle_weights


def balanced_cuts(n, rng):
    # Complementary balanced cuts represent the same bipartition: anchor qubit 0.
    choices = [(0,*other) for other in combinations(range(1,n),n//2-1)]
    return [list(choices[i]) for i in rng.choice(len(choices),size=min(4,len(choices)),replace=False)]


def cut_diagnostics(state, mi, cuts):
    n=len(mi);records=[]
    for kind, regions in (("singleton",[[i] for i in range(n)]),("balanced",cuts)):
        for region in regions:
            complement=[i for i in range(n) if i not in region]
            s=entropy(reduced_density(state,region))
            prediction=float(mi[np.ix_(region,complement)].sum()/2)
            defect=s-prediction
            records.append(dict(kind=kind,region=region,entropy=s,pair_prediction=prediction,
                defect=defect,normalized_defect=0. if max(s,prediction)<=1e-10 else defect/max(s,prediction,1e-12),
                numerically_zero_cut=max(s,prediction)<=1e-10))
    metrics={}
    for kind in ("singleton","balanced"):
        selected=[r for r in records if r["kind"]==kind]
        metrics[f"cut_{kind}_mean_abs_defect"]=float(np.mean([abs(r["defect"]) for r in selected]))
        metrics[f"cut_{kind}_mean_abs_normalized_defect"]=float(np.mean([abs(r["normalized_defect"]) for r in selected]))
    return records,metrics


def measure_state(state, cuts, *, couplings=None, true_adjacency=None, shuffle_rng=None, nulls=0):
    obs=pair_observables(state);mi=obs["mi"];n=len(mi);idx=np.triu_indices(n,1)
    inferred={}
    for eps in (1e-12,1e-9,1e-6):
        inferred[str(eps)]=infer_geometry(mi,epsilon=eps)
    main=inferred[str(1e-9)]
    metrics=geometry_metrics(main)
    metrics.update(evaluate_inputs(mi,couplings,true_adjacency=true_adjacency,
        connected_zz=obs["connected_zz"],negativity=obs["negativity"]))
    metrics.update(epsilon_agreement(mi))
    for name in ("mi","negativity","connected_zz"):
        metrics[f"{name}_mean"]=float(obs[name][idx].mean())
        metrics[f"{name}_max"]=float(obs[name][idx].max())
        metrics[f"{name}_min"]=float(obs[name][idx].min())
    metrics["mi_contrast"]=float(np.ptp(mi[idx]))
    metrics["single_entropy_mean"]=float(np.mean(obs["single_entropy"]))
    metrics["entangled_pair_fraction"]=float(np.mean(obs["negativity"][idx]>1e-10))
    cut_records,cut_metrics=cut_diagnostics(state,mi,cuts);metrics.update(cut_metrics)
    null_records=[]
    for _ in range(nulls):
        if shuffle_rng is None: raise ValueError("nulls need an explicit stream")
        null_records.append(geometry_metrics(infer_geometry(shuffle_weights(mi,shuffle_rng))))
    if null_records:
        for name in ("stress_d1","stress_d2","stress_d3","positive_participation_rank"):
            if name in null_records[0]:
                metrics[f"shuffle_{name}_mean"]=float(np.mean([r[name] for r in null_records]))
        metrics["shuffle_minus_stress_d3"]=metrics["shuffle_stress_d3_mean"]-metrics["stress_d3"]
    return dict(observables=obs,inference=inferred,cuts=cut_records,nulls=null_records,metrics=metrics)
