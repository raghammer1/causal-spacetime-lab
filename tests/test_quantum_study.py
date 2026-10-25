"""Execution-level guards: planned denominators, paired controls, and replay."""
import gzip
import json
from pathlib import Path
import numpy as np
import pytest
from causal_lab import quantum_study as study
from causal_lab.quantum import QuantumNumericalError
from causal_lab.quantum_random import rng_for
from causal_lab.quantum_statistics import summarize, stratified_mean_interval


def test_exchangeable_and_chain_inputs_and_perturbations():
    for family in ("A","B","chain"):
        J=study.couplings_for(family,6,rng_for("smoke",0,"test-couplings",family))
        assert np.allclose(J,J.T) and np.all(np.diag(J)==0)
        changed,noise=study.perturb_couplings(J,family,.01,rng_for("smoke",0,"test-perturbation",family))
        np.testing.assert_allclose(changed,J+.01*noise)
        if family=="chain":
            assert np.count_nonzero(J)==10
            assert np.all(changed[J==0]==0)


def test_failed_baselines_preserve_all_planned_denominators(monkeypatch):
    def failed(*args,**kwargs):
        raise QuantumNumericalError("intentional audit failure",{"valid":False,"failure":"injected"})
    monkeypatch.setattr(study,"ground_state",failed)
    rows,timing=study.run("smoke",1,sizes=(6,),nulls=0)
    assert timing["complete"]
    assert len(rows)==47
    assert sum(r["status"]=="failed" for r in rows)==9
    assert sum(r["status"]=="ok" for r in rows)==5
    assert sum(r["status"]=="blocked_or_unattempted" for r in rows)==33
    assert len({r["sample_id"] for r in rows})==len(rows)


def test_constant_undefined_and_singleton_strata():
    data=[]
    for batch in range(3):
        data.append(dict(family="B",n=6,h=1.,preparation="quench",delta=0.,time=1.,
            unit_id=f"unit-{batch}",batch=batch,status="ok",stochastic=True,
            metrics={"constant_correlation":float("nan"),"value":batch+1.}))
    result=summarize(data,resamples=19)[0]
    assert "constant_correlation" not in result["metrics"]
    assert result["metrics"]["value"]["ci95"] is None
    assert result["metrics"]["value"]["n"]==3


def test_raw_stream_replay_and_fair_paired_phases():
    args=("smoke",0,"B",6,0)
    first=study.independent_bundle(*args,nulls=2,evolve=False)
    second=study.independent_bundle(*args,nulls=2,evolve=False)
    assert study.canonical(first)==study.canonical(second)
    base=next(r for r in first if r["preparation"]=="ground" and r["h"]==1 and r["delta"]==0)
    scrambled=next(r for r in first if r["preparation"]=="phase_scrambled" and r["delta"]==0)
    ratio=scrambled["state"]/base["state"]
    for delta in (.01,.05):
        pert=next(r for r in first if r["preparation"]=="ground" and r["delta"]==delta)
        phase=next(r for r in first if r["preparation"]=="phase_scrambled" and r["delta"]==delta)
        np.testing.assert_allclose(phase["state"],pert["state"]*ratio,atol=1e-14)
        np.testing.assert_allclose(phase["observables"]["connected_zz"],pert["observables"]["connected_zz"],atol=1e-12)
        assert phase["cuts"][6:][0]["region"]==base["cuts"][6:][0]["region"]


def test_primary_rejects_dirty_scientific_source(monkeypatch,tmp_path):
    monkeypatch.setattr(study,"source_metadata",lambda:{"tracked_dirty":True,"untracked_scientific_files":""})
    with pytest.raises(SystemExit):study.main(["--primary","--repeats","2","--output",str(tmp_path)])


def test_failure_archive_and_figures_remain_writable(monkeypatch,tmp_path):
    def failed(*args,**kwargs):
        raise QuantumNumericalError("intentional audit failure",{"valid":False,"failure":"injected"})
    monkeypatch.setattr(study,"ground_state",failed)
    rows,timing=study.run("smoke",1,sizes=(6,),nulls=0)
    study.save(tmp_path,rows,{"phase":"smoke",**timing},resamples=19)
    from causal_lab.quantum_artifacts import verify_manifest
    assert verify_manifest(tmp_path)
    with gzip.open(tmp_path/"raw.jsonl.gz","rt") as stream:
        loaded=[json.loads(line) for line in stream]
    assert len(loaded)==47
    assert sum(r["status"]!="ok" for r in loaded)==42
