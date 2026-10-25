"""Registered exact-qubit experiment. Primary runs require a committed clean source."""
from __future__ import annotations
import argparse
import copy
from contextlib import contextmanager
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import matplotlib
import resource
import subprocess
import sys
import time
import numpy as np
import scipy
from .quantum_random import rng_for, stream_key, SEEDS
from .quantum import (ground_state, plus_state, ghz_state, bell_product, haar_state,
    random_product_state, permute_state, evolve_state, QuantumNumericalError)
from .quantum_geometry import neighborhood_overlap
from .quantum_measurements import balanced_cuts, measure_state
from .quantum_statistics import summarize, calibration

SIZES=(6,8,10)
FIELDS=(.5,1.,2.)
DELTAS=(.01,.05)
PROTOCOL_COMMIT="ee9ece7"
BASELINE_COMMIT="9bc5984c656271c247354e0079fd900702642064"


def plain(value):
    if isinstance(value,np.ndarray):
        if np.iscomplexobj(value): return {"real":plain(value.real),"imag":plain(value.imag)}
        return plain(value.tolist())
    if isinstance(value,(np.integer,np.floating,np.bool_)): return plain(value.item())
    if isinstance(value,float) and not np.isfinite(value): return None
    if isinstance(value,dict): return {str(k):plain(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)): return [plain(v) for v in value]
    return value


def canonical(value):
    return json.dumps(plain(value),sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def write_json(path,value):
    Path(path).write_text(json.dumps(plain(value),indent=2,sort_keys=True,allow_nan=False)+"\n")


def couplings_for(family,n,rng):
    if family=="A":
        return (np.ones((n,n))-np.eye(n))/(n-1)
    if family=="B":
        upper=np.zeros((n,n));idx=np.triu_indices(n,1)
        upper[idx]=rng.normal(size=len(idx[0]))/np.sqrt(n-1)
        return upper+upper.T
    if family=="chain":
        matrix=np.zeros((n,n));bonds=rng.uniform(.8,1.2,size=n-1)
        matrix[np.arange(n-1),np.arange(1,n)]=bonds
        matrix+=matrix.T
        permutation=rng.permutation(n)
        return matrix[np.ix_(permutation,permutation)]
    raise ValueError("unknown family")


def perturb_couplings(J,family,delta,rng):
    n=len(J);idx=np.triu_indices(n,1);noise=np.zeros_like(J)
    scale=1/(n-1) if family=="A" else 1/np.sqrt(n-1) if family=="B" else 1.
    noise[idx]=rng.normal(size=len(idx[0]))*scale
    if family=="chain": noise[J==0]=0
    noise+=noise.T
    return J+delta*noise,noise


def independent_bundle(phase,batch,family,n,rep,*,nulls=31,evolve=True,symmetric_cache=None):
    """One independent J/preparation unit, with all paired branches attached."""
    unit=f"{phase}/{batch}/{family}/{n}/{rep}"
    def rng(task,*params): return rng_for(phase,batch,family,n,rep,task,*params)
    J=couplings_for(family,n,rng("couplings"))
    cuts=balanced_cuts(n,rng("cuts"))
    if family=="A" and symmetric_cache is not None and (n,1.) in symmetric_cache:
        cuts=[r["region"] for r in symmetric_cache[n,1.]["cuts"] if r["kind"]=="balanced"]
    phase_angles=rng("phases").uniform(0,2*np.pi,size=2**n)
    phase_vector=np.exp(1j*phase_angles)
    true_adjacency=(J!=0) if family=="chain" else None
    records=[];ground={}
    def record(state,preparation,h=1.,delta=0.,t=0.,solver=None,current_J=J,stochastic=True):
        row=dict(sample_id=f"{unit}/{preparation}/{h}/{delta}/{t}",unit_id=unit,
            phase=phase,batch=batch,family=family,n=n,rep=rep,h=h,
            preparation=preparation,delta=delta,time=t,stochastic=stochastic,status="ok",
            stream_key=stream_key(phase,batch,family,n,rep),state=state,
            couplings=current_J,solver=solver)
        row.update(measure_state(state,cuts,couplings=current_J,true_adjacency=true_adjacency,
            shuffle_rng=rng("shuffle",h,delta,t),
            nulls=nulls if preparation in ("ground","phase_scrambled") and h==1 and delta==0 else 0))
        records.append(row);return row
    for h in FIELDS:
        if family=="A" and symmetric_cache is not None:
            ground[h]=symmetric_cache.get((n,h))
            continue
        try:
            solved=ground_state(J,h,rng("eigensolver",h))
            state=solved.pop("state")
            row=record(state,"ground",h=h,solver=solved,stochastic=family!="A")
            ground[h]=row
        except QuantumNumericalError as exc:
            row=dict(sample_id=f"{unit}/ground/{h}/0.0/0.0",unit_id=unit,phase=phase,
                batch=batch,family=family,n=n,rep=rep,h=h,preparation="ground",delta=0.,time=0.,
                stochastic=family!="A",status="failed",metrics={},solver=exc.diagnostics,
                couplings=J,stream_key=stream_key(phase,batch,family,n,rep))
            records.append(row)
    base=ground.get(1.)
    if base is None: return records
    phase_base=record(base["state"]*phase_vector,"phase_scrambled")
    phase_base["source_state_id"]=base["sample_id"]
    if family!="A":
        base["metrics"]["phase_minus_stress_d3"]=phase_base["metrics"]["stress_d3"]-base["metrics"]["stress_d3"]
    for delta in DELTAS:
        changed,noise=perturb_couplings(J,family,delta,rng("perturbation",delta))
        try:
            solved=ground_state(changed,1.,rng("eigensolver-perturbation",delta));state=solved.pop("state")
            pert=record(state,"ground",delta=delta,solver=solved,current_J=changed)
            scrambled=record(state*phase_vector,"phase_scrambled",delta=delta,current_J=changed)
            scrambled["source_state_id"]=pert["sample_id"]
            for a,b in ((pert,base),(scrambled,phase_base)):
                for k in (1,2,3):
                    a["metrics"][f"overlap_base_k{k}"]=neighborhood_overlap(
                        a["inference"][str(1e-9)]["neighbors"][f"k{k}"],
                        b["inference"][str(1e-9)]["neighbors"][f"k{k}"])
                a["metrics"]["relative_coupling_change"]=float(np.linalg.norm(changed-J)/np.linalg.norm(J))
                a["baseline_id"]=b["sample_id"]
            pert["perturbation_noise"]=noise
            pert["metrics"]["phase_minus_stress_d3"]=scrambled["metrics"]["stress_d3"]-pert["metrics"]["stress_d3"]
        except QuantumNumericalError as exc:
            records.append(dict(sample_id=f"{unit}/ground/1.0/{delta}/0.0",unit_id=unit,phase=phase,
                batch=batch,family=family,n=n,rep=rep,h=1.,preparation="ground",delta=delta,time=0.,
                stochastic=True,status="failed",metrics={},solver=exc.diagnostics,couplings=changed,
                perturbation_noise=noise,stream_key=stream_key(phase,batch,family,n,rep)))
    if evolve:
        for prep,initial in (("quench_plus",plus_state(n)),("quench_random_product",random_product_state(n,rng("initial-product")))):
            if family=="A" and prep=="quench_plus" and batch!=0: continue
            for t in (.5,1.,2.):
                try:
                    state=evolve_state(J,1.,initial,t)
                except QuantumNumericalError as exc:
                    records.append(dict(sample_id=f"{unit}/{prep}/1.0/0.0/{t}",unit_id=unit,phase=phase,
                        batch=batch,family=family,n=n,rep=rep,h=1.,preparation=prep,delta=0.,time=t,
                        stochastic=not(family=="A" and prep=="quench_plus"),status="failed",metrics={},
                        solver=exc.diagnostics,couplings=J,initial_state=initial))
                    continue
                row=record(state,prep,t=t,stochastic=not(family=="A" and prep=="quench_plus"))
                row["initial_state"]=initial
                row["metrics"]["overlap_ground_k2"]=neighborhood_overlap(
                    row["inference"][str(1e-9)]["neighbors"]["k2"],base["inference"][str(1e-9)]["neighbors"]["k2"])
    return records


def control_record(phase,batch,n,rep,family,state,*,stochastic,nulls=31):
    unit=f"{phase}/{batch}/{family}/{n}/{rep}"
    cuts=balanced_cuts(n,rng_for(phase,batch,family,n,rep,"cuts"))
    return dict(sample_id=unit,unit_id=unit,phase=phase,batch=batch,family=family,n=n,
        rep=rep,h=0.,preparation="control",delta=0.,time=0.,stochastic=stochastic,
        status="ok",state=state,stream_key=stream_key(phase,batch,family,n,rep),
        **measure_state(state,cuts,shuffle_rng=rng_for(phase,batch,family,n,rep,"shuffle"),
            nulls=nulls if family in ("haar","GHZ","Bell") else 0))


def run(phase,repeats,*,sizes=SIZES,nulls=31,progress=False,deadline=2700):
    started=time.perf_counter();rows=[];cache={}
    # Exactly nine unique Model-A ground states; stored once, reused only as reference.
    for n in sizes:
        for h in FIELDS:
            J=couplings_for("A",n,None)
            unit=f"{phase}/A/{n}"
            try:
                solved=ground_state(J,h,rng_for(phase,0,"A",n,"deterministic-eigensolver",h))
            except QuantumNumericalError as exc:
                rows.append(dict(sample_id=f"{unit}/{h}",unit_id=unit,phase=phase,batch=0,
                    family="A",n=n,rep=-1,h=h,preparation="ground",delta=0.,time=0.,
                    stochastic=False,status="failed",metrics={},solver=exc.diagnostics,couplings=J))
                continue
            state=solved.pop("state")
            row=dict(sample_id=f"{unit}/{h}",unit_id=unit,phase=phase,batch=0,family="A",n=n,rep=-1,
                h=h,preparation="ground",delta=0.,time=0.,stochastic=False,status="ok",state=state,
                couplings=J,solver=solved,stream_key=stream_key(phase,0,"A",n,"deterministic-eigensolver",h),
                **measure_state(state,balanced_cuts(n,rng_for(phase,0,"A",n,"deterministic-cuts")),
                    couplings=J,shuffle_rng=rng_for(phase,0,"A",n,"deterministic-shuffle",h),nulls=nulls if h==1 else 0))
            cache[n,h]=row;rows.append(row)
        for family,state in (("product",plus_state(n)),("GHZ",ghz_state(n)),
            ("Bell",permute_state(bell_product(n),rng_for(phase,0,"Bell",n,"permutation").permutation(n)))):
            rows.append(control_record(phase,0,n,-1,family,state,stochastic=False,nulls=nulls))
    for batch in range(len(SEEDS[phase])):
        for n in sizes:
            for rep in range(repeats):
                for family in ("chain","B","A"):
                    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    peak_bytes=peak if sys.platform=="darwin" else peak*1024
                    if time.perf_counter()-started>deadline or peak_bytes>2*1024**3:
                        return complete_planned_records(rows,phase,repeats,sizes),{"complete":False,"reason":"registered resource cap","elapsed_seconds":time.perf_counter()-started}
                    rows.extend(independent_bundle(phase,batch,family,n,rep,nulls=nulls,evolve=rep==0,symmetric_cache=cache))
                for family,state in (("haar",haar_state(n,rng_for(phase,batch,"haar",n,rep,"state"))),
                    ("random_product",random_product_state(n,rng_for(phase,batch,"random_product",n,rep,"state")))):
                    rows.append(control_record(phase,batch,n,rep,family,state,stochastic=True,nulls=nulls))
            if progress: print(f"Completed batch {batch+1}, n={n}; {len(rows)} state records",flush=True)
    return complete_planned_records(rows,phase,repeats,sizes),{"complete":True,"elapsed_seconds":time.perf_counter()-started}


def complete_planned_records(rows,phase,repeats,sizes):
    """Keep planned denominators even when a missing baseline blocks dependents."""
    observed={(r["family"],r["n"],r["batch"],r["rep"],r["h"],r["preparation"],r["delta"],r["time"]) for r in rows}
    if len(observed)!=len(rows): raise ValueError("duplicate planned state")
    expected=[]
    for n in sizes:
        expected.extend(("A",n,0,-1,h,"ground",0.,0.) for h in FIELDS)
        expected.extend((f,n,0,-1,0.,"control",0.,0.) for f in ("product","GHZ","Bell"))
        for batch in range(len(SEEDS[phase])):
            for rep in range(repeats):
                for family in ("A","B","chain"):
                    if family!="A":expected.extend((family,n,batch,rep,h,"ground",0.,0.) for h in FIELDS)
                    expected.append((family,n,batch,rep,1.,"phase_scrambled",0.,0.))
                    expected.extend((family,n,batch,rep,1.,prep,delta,0.) for delta in DELTAS for prep in ("ground","phase_scrambled"))
                    if rep==0:
                        expected.extend((family,n,batch,rep,1.,prep,0.,t) for prep in ("quench_plus","quench_random_product")
                            for t in (.5,1.,2.) if not(family=="A" and prep=="quench_plus" and batch!=0))
                expected.extend((f,n,batch,rep,0.,"control",0.,0.) for f in ("haar","random_product"))
    if not observed.issubset(set(expected)):raise ValueError("unexpected state outside registered schedule")
    for key in expected:
        if key not in observed:
            family,n,batch,rep,h,prep,delta,t=key;unit=f"{phase}/{batch}/{family}/{n}/{rep}"
            rows.append(dict(sample_id=f"{unit}/{prep}/{h}/{delta}/{t}",unit_id=unit,phase=phase,
                batch=batch,family=family,n=n,rep=rep,h=h,preparation=prep,delta=delta,time=t,
                stochastic=rep>=0,status="blocked_or_unattempted",metrics={},
                reason="planned record absent after upstream solver failure or resource cap"))
    return rows


def source_metadata():
    root=Path(__file__).resolve().parents[2]
    git=lambda *args:subprocess.check_output(["git",*args],cwd=root,text=True).strip()
    sources=sorted((root/"src/causal_lab").glob("quantum*.py"))
    return {"source_commit":git("rev-parse","HEAD"),"protocol_commit":PROTOCOL_COMMIT,
        "baseline_commit":BASELINE_COMMIT,"tracked_dirty":bool(git("status","--porcelain","--untracked-files=no")),
        "untracked_scientific_files":git("ls-files","--others","--exclude-standard","src","tests","docs","pyproject.toml"),
        "source_hashes":{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "versions":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,"matplotlib":matplotlib.__version__},
        "platform":{"system":platform.system(),"machine":platform.machine()},"seeds":SEEDS}


def save(out,rows,metadata,*,resamples=3999):
    post_started=time.perf_counter()
    with (out/"raw.jsonl.gz").open("wb") as file:
        with gzip.GzipFile(filename="",fileobj=file,mode="wb",mtime=0) as stream:
            for row in rows:stream.write(canonical(row)+b"\n")
    summary=summarize(rows,resamples=resamples);write_json(out/"summary.json",summary)
    from .quantum_artifacts import write_figures, write_summary_csv, make_manifest
    write_summary_csv(out,summary);write_figures(out,rows,summary)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    metadata["peak_rss_bytes"]=peak if sys.platform=="darwin" else peak*1024
    metadata["postprocessing_seconds"]=time.perf_counter()-post_started
    metadata["total_seconds"]=metadata.get("elapsed_seconds",0)+metadata["postprocessing_seconds"]
    metadata["resource_caps_satisfied"]=metadata["total_seconds"]<=2700 and metadata["peak_rss_bytes"]<=2*1024**3
    write_json(out/"metadata.json",metadata)
    make_manifest(out)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--smoke",action="store_true");group.add_argument("--pilot",action="store_true")
    group.add_argument("--primary",action="store_true");group.add_argument("--calibrate",action="store_true")
    parser.add_argument("--repeats",type=int,choices=(2,4,8));parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    if args.output.exists() and any(args.output.iterdir()):parser.error("output directory must be empty")
    args.output.mkdir(parents=True,exist_ok=True)
    if args.calibrate:
        write_json(args.output/"calibration.json",calibration());print("Independent calibration audit written");return
    if args.pilot:
        records=[];pilot_rows=[]
        for n in SIZES:
            start=time.perf_counter()
            # Full representative bundle including preparation/controls at each size.
            rows,runmeta=run("pilot",1,sizes=(n,),nulls=31,progress=False)
            records.append({"n":n,"seconds":time.perf_counter()-start,"states":len(rows),
                            "failed":sum(r["status"]!="ok" for r in rows)})
            pilot_rows.extend(rows)
        # Conservative full-size postprocessing/memory test: duplicate only pilot
        # values into 24 synthetic units per cell. Never inspect these outcomes.
        # Replicating even deterministic and first-only quench cells overstates work.
        synthetic=[]
        for batch in range(3):
            for rep in range(8):
                for original in pilot_rows:
                    row=copy.deepcopy(original)
                    row.update(batch=batch,rep=rep,stochastic=True,
                        unit_id=f"timing-only/{batch}/{rep}/{original['unit_id']}",
                        sample_id=f"timing-only/{batch}/{rep}/{original['sample_id']}")
                    synthetic.append(row)
        post_dir=args.output/"uninspected-postprocessing";post_dir.mkdir()
        post_started=time.perf_counter()
        save(post_dir,synthetic,{"phase":"pilot","synthetic_timing_only":True},resamples=3999)
        post_seconds=time.perf_counter()-post_started
        del synthetic,pilot_rows
        # A complete R=1 batch over all sizes costs sum(t). Linear scaling overestimates
        # repeated deterministic controls and the first-only unitary cohort.
        estimates={str(r):2*(3*r*sum(x["seconds"] for x in records)+post_seconds) for r in (8,4,2)}
        peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_bytes=peak if sys.platform=="darwin" else peak*1024
        feasible=[r for r in (8,4,2) if estimates[str(r)]<=1200 and peak_bytes<2*1024**3]
        choice=feasible[0] if feasible else None
        write_json(args.output/"pilot.json",dict(phase="pilot",timings=records,projected_seconds=estimates,
            selected_repeats=choice,peak_rss_bytes=peak_bytes,postprocessing_worst_grid_seconds=post_seconds,scientific_values_inspected=False,source=source_metadata()))
        print(f"Timing-only pilot complete; selected R={choice}; see pilot.json");return
    phase="primary" if args.primary else "smoke"
    meta=source_metadata()
    if args.primary and (meta["tracked_dirty"] or meta["untracked_scientific_files"]):
        parser.error("primary execution requires committed clean scientific source")
    if args.primary and args.repeats is None:parser.error("primary needs pilot-selected --repeats")
    rows,timing=run(phase,args.repeats if args.primary else 1,
        sizes=SIZES if args.primary else (6,),nulls=31 if args.primary else 3,progress=True)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    meta.update(timing,phase=phase,repeats=args.repeats if args.primary else 1,
                peak_rss_bytes=peak if sys.platform=="darwin" else peak*1024,
                states=len(rows),failed=sum(r["status"]!="ok" for r in rows))
    save(args.output,rows,meta,resamples=3999 if args.primary else 99)
    print(f"{phase}: {len(rows)} records; {meta['failed']} numerical failures; complete={meta['complete']}")


if __name__=="__main__":main()
