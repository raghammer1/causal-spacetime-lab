"""Reproducible archives and plainly labelled correlation visualizations."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLORS={"chain":"#0072B2","B":"#D55E00","A":"#009E73","haar":"#CC79A7",
        "GHZ":"#888888","Bell":"#E69F00","product":"#444444","random_product":"#999955"}


def write_summary_csv(out,summary):
    fields=["family","n","h","preparation","delta","time","attempted","valid","metric",
            "mean","sd","ci_low","ci_high","independent_units","undefined"]
    with (out/"summary.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader()
        for cell in summary:
            for name,m in cell["metrics"].items():
                ci=m.get("ci95") or [None,None]
                w.writerow({**{k:cell[k] for k in fields[:8]},"metric":name,"mean":m["mean"],
                    "sd":m.get("sd"),"ci_low":ci[0],"ci_high":ci[1],"independent_units":m["n"],"undefined":m["undefined"]})


def _save(fig,out,name):
    fig.savefig(out/name,dpi=170,bbox_inches="tight",metadata={"Software":"causal-spacetime-lab Experiment 6"})
    plt.close(fig)


def _series(ax,summary,metric,*,families=("chain","B","A","haar","GHZ","Bell"),h=1.,delta=0.,prep=None):
    for family in families:
        cells=[s for s in summary if s["family"]==family and s["delta"]==delta
               and s["preparation"]==(prep or ("ground" if family in ("chain","B","A") else "control"))
               and (s["h"]==h if family in ("chain","B","A") else True) and metric in s["metrics"]]
        cells.sort(key=lambda s:s["n"])
        if not cells:continue
        x=np.array([s["n"] for s in cells]);y=np.array([s["metrics"][metric]["mean"] for s in cells])
        lo=np.array([(s["metrics"][metric].get("ci95") or [s["metrics"][metric]["mean"]]*2)[0] for s in cells])
        hi=np.array([(s["metrics"][metric].get("ci95") or [s["metrics"][metric]["mean"]]*2)[1] for s in cells])
        ax.plot(x,y,"o-",color=COLORS[family],label=family,markersize=4)
        ax.fill_between(x,lo,hi,color=COLORS[family],alpha=.13)
    ax.set_xticks(sorted({s["n"] for s in summary}));ax.set_xlabel("Qubits n")
    ax.spines[["top","right"]].set_visible(False)


def write_figures(out,rows,summary):
    plt.rcParams.update({"font.size":9,"axes.titlesize":10,"figure.titlesize":13})
    fig,axes=plt.subplots(2,3,figsize=(13,7.8),layout="constrained")
    for ax,metric,label in zip(axes.flat,
        ("mi_mean","entangled_pair_fraction","stress_d3","positive_participation_rank","cut_balanced_mean_abs_normalized_defect","edge_auc"),
        ("Mean pair mutual information (bits)","Pairs with negativity > 1e−10","3D projection: normalized distance stress",
         "Positive-spectrum participation rank","Balanced-cut law: mean normalized defect","Hidden-chain edge/nonedge AUC")):
        _series(ax,summary,metric);ax.set_title(label)
    axes[0,0].legend(ncol=3,fontsize=8)
    axes[1,2].set_ylim(0,1.03)
    fig.suptitle("Finite quantum correlations and reconstruction diagnostics\nh = 1; shading: nominal 95% percentile intervals (calibration undercovered)")
    _save(fig,out,"family_diagnostics.png")
    n=max(r["n"] for r in rows);selected=[]
    for family in ("chain","B","A","GHZ","Bell","haar"):
        candidates=[r for r in rows if r["family"]==family and r["n"]==n and r["status"]=="ok"
                    and r["delta"]==0 and r["preparation"] in ("ground","control")
                    and (r["h"]==1 if family in ("chain","B","A") else True)]
        if candidates:selected.append(candidates[0])
    fig,axes=plt.subplots(2,len(selected),figsize=(15,5.6),layout="constrained",squeeze=False)
    for col,row in enumerate(selected):
        mi=np.asarray(row["observables"]["mi"]);inferred=row["inference"][str(1e-9)]
        ax=axes[0,col];im=ax.imshow(mi,vmin=0,vmax=2,cmap="magma");ax.set_title(row["family"]);ax.set_xlabel("Subsystem label")
        coords=np.asarray(inferred["coordinates"]);xy=np.zeros((n,2));xy[:,:min(2,coords.shape[1])]=coords[:,:2]
        ax=axes[1,col];weights=np.asarray(inferred["neighbors"]["k2"])
        for i in range(n):
            for j in range(i+1,n):
                w=max(weights[i,j],weights[j,i])
                if w>0:ax.plot(xy[[i,j],0],xy[[i,j],1],color=COLORS[row["family"]],alpha=.12+.35*w,lw=.3+1.1*w)
        ax.scatter(xy[:,0],xy[:,1],s=20,color=COLORS[row["family"]]);ax.set_aspect("equal",adjustable="datalim")
        ax.set_title(f"2D correlation projection\nstress {row['metrics']['stress_d2']:.3f}",fontsize=9)
        ax.set_xticks([]);ax.set_yticks([])
    fig.colorbar(im,ax=axes[0,:].tolist(),label="Mutual information (bits)",shrink=.75)
    fig.suptitle(f"Correlation representations, not observed geometry (n={n})\nFirst registered realization; degenerate projections are noncanonical; edges are fractional k=2 choices")
    _save(fig,out,"correlation_representations.png")
    fig,axes=plt.subplots(1,3,figsize=(13,3.8),layout="constrained")
    for ax,delta in zip(axes[:2],(.01,.05)):
        _series(ax,summary,"overlap_base_k2",families=("chain","B","A"),delta=delta)
        ax.set_title(f"Ground-state k=2 overlap, δ={delta}");ax.set_ylim(0,1.03)
    _series(axes[2],summary,"spearman_mi_coupling",families=("chain","B","A"))
    axes[2].set_title("Direct |J| versus MI rank correlation")
    axes[0].legend();fig.suptitle("Stability and supplied-interaction diagnostics (h=1)")
    _save(fig,out,"robustness_and_couplings.png")
    fig,axes=plt.subplots(1,3,figsize=(13,3.7),layout="constrained")
    for ax,h in zip(axes,FIELDS):
        for family in ("chain","B"):
            chosen=[r for r in rows if r["family"]==family and r["n"]==n and r["h"]==h and r["delta"]==0 and r["preparation"]=="ground" and r["status"]=="ok"]
            for row in chosen:
                idx=np.triu_indices(n,1);ax.scatter(np.abs(row["couplings"])[idx],row["observables"]["mi"][idx],s=5,alpha=.2,color=COLORS[family])
        ax.set_title(f"h={h:g}, n={n}");ax.set_xlabel("Supplied |Jᵢⱼ|");ax.set_ylabel("Pair MI (bits)")
    fig.suptitle("Pairwise dependence on supplied couplings; dots are correlated within states")
    _save(fig,out,"coupling_scatter.png")
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),layout="constrained")
    for ax,name,label in zip(axes,("shuffle_minus_stress_d3","phase_minus_stress_d3"),
                            ("Shuffled-weight null minus ground stress","Paired phase-scramble minus ground stress")):
        _series(ax,summary,name,families=("chain","B","A"));ax.axhline(0,c="gray",ls="--",lw=.8);ax.set_title(label)
    axes[0].legend();fig.suptitle("3D projection contrasts: positive values favor the ground-state fit\nNominal percentile intervals; calibration undercovered: descriptive comparisons only")
    _save(fig,out,"null_contrasts.png")
    fig,axes=plt.subplots(1,3,figsize=(13,3.7),layout="constrained")
    for ax,family in zip(axes,("chain","B","A")):
        for prep,color in (("quench_plus","#0072B2"),("quench_random_product","#D55E00")):
            cells=[s for s in summary if s["family"]==family and s["n"]==n and s["preparation"]==prep and "overlap_ground_k2" in s["metrics"]]
            cells.sort(key=lambda s:s["time"])
            if cells:ax.plot([s["time"] for s in cells],[s["metrics"]["overlap_ground_k2"]["mean"] for s in cells],"o-",color=color,label=prep.removeprefix("quench_"))
        ax.set_title(f"{family}, n={n}");ax.set_ylim(0,1.03);ax.set_xlabel("External evolution parameter t")
    axes[0].set_ylabel("k=2 overlap with ground-state neighborhoods");axes[0].legend()
    fig.suptitle("Preparation dependence: three independent preparations per stochastic cell\nSymmetric all-plus evolution is a single deterministic control, not three samples")
    _save(fig,out,"preparation_dependence.png")


FIELDS=(.5,1.,2.)


def make_manifest(out):
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())
           if p.is_file() and p.name!="manifest.json"}
    science=hashlib.sha256()
    for name in ("raw.jsonl.gz","summary.json","summary.csv"):
        science.update(name.encode());science.update((out/name).read_bytes())
    result={"sha256":files,"scientific_digest":science.hexdigest(),
            "scientific_files":["raw.jsonl.gz","summary.json","summary.csv"]}
    (out/"manifest.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result


def verify_manifest(out):
    out=Path(out);manifest=json.loads((out/"manifest.json").read_text())
    for name,expected in manifest["sha256"].items():
        if Path(name).name!=name: raise ValueError("external artifact path")
        if hashlib.sha256((out/name).read_bytes()).hexdigest()!=expected:raise ValueError(f"artifact mismatch: {name}")
    science=hashlib.sha256()
    for name in manifest["scientific_files"]:
        if Path(name).name!=name:raise ValueError("external scientific path")
        science.update(name.encode());science.update((out/name).read_bytes())
    if science.hexdigest()!=manifest["scientific_digest"]:raise ValueError("scientific digest mismatch")
    return manifest["scientific_digest"]
