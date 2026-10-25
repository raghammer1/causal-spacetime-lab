"""Independent review of Experiment 3 integration and registered decisions."""
import hashlib
import json

import numpy as np
import pytest

from causal_lab import adversarial_study as study
from causal_lab.adversarial_detectors import evaluate_detectors, fit_model, wilson_interval


@pytest.fixture(scope="module")
def reviewed_result():
    config=study.StudyConfig(dimensions=(2,3),counts=(12,),fits=2,
                            calibration=10,development=10,validation=12,repeats=2,
                            search_steps=4,bootstrap=32,seed=101)
    return config,study.run_study(config)


def test_reviewed_partition_counts_and_global_disjointness(reviewed_result):
    config,result=reviewed_result
    assert len(result["raw"]) == 204
    assert len(result["searches"]) == 8
    ids=[row["sample_id"] for row in result["raw"]]
    assert len(ids)==len(set(ids))
    for fit in range(config.fits):
        rows=[r for r in result["raw"] if r["fit"]==fit]
        assert sum(r["phase"]=="calibration" for r in rows)==20
        assert sum(r["phase"]=="development" for r in rows)==20
        assert sum(r["phase"]=="validation" for r in rows)==24
        assert sum(r["phase"]=="test" for r in rows)==38
        test_ids={r["sample_id"] for r in rows if r["phase"]=="test"}
        for other_fit in range(config.fits):
            if other_fit != fit:
                assert test_ids.isdisjoint({r["sample_id"] for r in result["raw"] if r["fit"]==other_fit})


def test_stream_keys_exactly_follow_registered_canonical_JSON():
    values=["adversarial-v1",101,1,"test","dag_4",0,12,7,4]
    expected=hashlib.sha256(json.dumps(values,separators=(",",":"),ensure_ascii=True).encode("ascii")).hexdigest()
    assert study.identity(101,1,"test","dag_4",0,12,7,4)==expected
    streams=[study.identity(101,fit,phase,"genuine",2,12,0)
             for fit in range(3) for phase in ("calibration","development","validation","test")]
    assert len(set(streams))==12


def test_model_can_be_reconstructed_without_development_or_test_rows(reviewed_result):
    _,result=reviewed_result
    for fit in range(2):
        calibration=[r for r in result["raw"] if r["fit"]==fit and r["phase"]=="calibration"]
        validation=[r for r in result["raw"] if r["fit"]==fit and r["phase"]=="validation"]
        rebuilt=fit_model(calibration,validation)
        archived={k:v for k,v in result["models"][str(fit)]["12"].items() if k!="adversary_parameters"}
        assert rebuilt==archived
        assert rebuilt["calibration_ids_sha256"]!=rebuilt["validation_ids_sha256"]


def test_every_holdout_decision_replays_without_truth_or_family(reviewed_result):
    _,result=reviewed_result
    for row in result["raw"]:
        if row["phase"]!="test": continue
        fitted=result["models"][str(row["fit"])][str(row["count"])]
        poisoned={**row,"true_dimension":999,"dimension_label":-999,"family":"wrong_label",
                  "classification":"fabricated","estimated_dimension":-500}
        for target in study.TARGETS:
            replay=evaluate_detectors(poisoned,fitted,target=target)
            assert row["accepted"][str(target)]==[replay[name]["accepted"] for name in study.DETECTORS]
            assert row["scores"]==[replay[name]["score"] for name in study.DETECTORS]
            assert row["candidate_dimensions"]==[replay[name]["candidate_dimension"] for name in study.DETECTORS]


def test_summaries_reconcile_rates_Wilson_and_unclassified_denominators(reviewed_result):
    _,result=reviewed_result
    for summary in result["summary"]:
        i=study.DETECTORS.index(summary["detector"])
        all_rates=[]
        for fit in summary["per_fit"]:
            rows=[r for r in result["raw"] if r["phase"]=="test" and r["fit"]==fit["fit"]
                  and study.group_key(r)==(summary["family"],summary["dimension_label"],summary["count"])]
            successes=sum(r["accepted"][str(summary["target"])][i] for r in rows)
            assert fit["n"]==len(rows)
            assert fit["accepted"]==successes
            assert fit["rate"]==successes/len(rows)
            all_rates.append(fit["rate"])
            if summary["family"] in study.EXACT:
                assert fit["n"]==1
                assert fit["wilson_low"] is None and fit["wilson_high"] is None
            else:
                assert (fit["wilson_low"],fit["wilson_high"])==wilson_interval(successes,len(rows))
            unclassified=next(x for x in summary["accepted_unclassified_per_fit"] if x["fit"]==fit["fit"])
            assert unclassified["count"]==sum(r["classification"]=="unclassified"
                                                and r["accepted"][str(summary["target"])][i] for r in rows)
        assert summary["mean_acceptance"]==np.mean(all_rates)
        assert "wilson_low" not in summary  # Repeated fits are never one binomial trial set.


def test_all_paired_tables_reconcile_same_order_decisions(reviewed_result):
    _,result=reviewed_result
    for comparison in result["paired"]:
        left=study.DETECTORS.index(comparison["left"])
        right=study.DETECTORS.index(comparison["right"])
        for per_fit in comparison["per_fit"]:
            rows=[r for r in result["raw"] if r["phase"]=="test" and r["fit"]==per_fit["fit"]
                  and study.group_key(r)==(comparison["family"],comparison["dimension_label"],comparison["count"])]
            decisions=[r["accepted"][str(comparison["target"])] for r in rows]
            expected=[sum(a[left] and a[right] for a in decisions),
                      sum(a[left] and not a[right] for a in decisions),
                      sum(not a[left] and a[right] for a in decisions),
                      sum(not a[left] and not a[right] for a in decisions)]
            actual=[per_fit[k] for k in ("both_accepted","left_only","right_only","both_rejected")]
            assert actual==expected
            assert sum(actual)==len(rows)
            assert per_fit["mean_difference"]==(expected[1]-expected[2])/len(rows)


def test_search_target_is_development_only_and_checkpoints_remain_linked(reviewed_result):
    _,result=reviewed_result
    indexed={r["sample_id"]:r for r in result["raw"]}
    for search in result["searches"]:
        target=indexed[search["target_sample_id"]]
        assert target["phase"]=="development"
        assert target["fit"]==search["fit"]
        assert target["count"]==search["count"]
        assert target["true_dimension"]==search["dimension"]
        checkpoints=[r for r in result["raw"] if r.get("search_id")==search["search_id"]]
        assert {r["family"] for r in checkpoints}=={"height_matched","multi_matched"}
        assert len(checkpoints)==2
        assert all(r["target_sample_id"]==target["sample_id"] for r in checkpoints)
        assert all(r["longest_chain"]==target["longest_chain"] for r in checkpoints)


def cell(family, *, detector="D", dimension=2, low=.95, high=.99, maximum=.97):
    return {"family":family,"detector":detector,"dimension_label":dimension,"count":64,
            "target":.95,"max_acceptance":maximum,
            "per_fit":[{"fit":i,"wilson_low":low,"wilson_high":high} for i in range(3)]}


def comparison(family, *, low=.1, high=.2, dimension=2):
    return {"family":family,"dimension_label":dimension,"count":64,"target":.95,
            "left":"B","right":"D","mean_difference":(low+high)/2,"ci_low":low,"ci_high":high}


def test_advancement_treats_overlap_as_positive_and_boundary_as_stress():
    good=cell("genuine")
    overlap=cell("rank_overlap",low=.8,high=.85)
    boundary=cell("box",low=0,high=.01)
    result=study.advancement([good,overlap,boundary],[])
    cells=result["primary"]["D"]["cells"]
    assert next(c for c in cells if c["family"]=="rank_overlap")["status"]=="failed"
    assert not any(c["family"]=="box" for c in cells)


def test_advancement_requires_every_fit_and_distinguishes_inconclusive():
    genuine=cell("genuine")
    genuine["per_fit"][2].update(wilson_low=.88,wilson_high=.93)
    negative=cell("dag_4",low=.01,high=.04)
    result=study.advancement([genuine,negative],[])
    assert result["primary"]["D"]["status"]=="inconclusive"
    negative["per_fit"][0].update(wilson_low=.06,wilson_high=.1)
    result=study.advancement([genuine,negative],[])
    assert result["primary"]["D"]["status"]=="failed"


def test_advancement_exact_controls_reject_all_fits():
    exact=cell("antichain",low=None,high=None,maximum=0)
    result=study.advancement([exact],[])
    assert result["primary"]["D"]["cells"][0]["status"]=="supported"
    exact["max_acceptance"]=1
    result=study.advancement([exact],[])
    assert result["primary"]["D"]["cells"][0]["status"]=="failed"


def test_meaningful_gain_needs_practical_lower_bound_and_genuine_guard():
    genuine=cell("genuine")
    gain=comparison("multi_matched",low=.051,high=.15)
    deterioration=comparison("genuine",low=-.01,high=.02)
    result=study.advancement([genuine],[gain,deterioration])
    assert result["paired_gains"][0]["meaningful_local_gain"]
    gain["ci_low"]=.05
    assert not study.advancement([genuine],[gain,deterioration])["paired_gains"][0]["meaningful_local_gain"]
    gain["ci_low"]=.1; deterioration["ci_high"]=.021
    assert not study.advancement([genuine],[gain,deterioration])["paired_gains"][0]["genuine_gate"]
    deterioration["ci_high"]=.01; genuine["per_fit"][0]["wilson_low"]=.89
    assert not study.advancement([genuine],[gain,deterioration])["paired_gains"][0]["genuine_gate"]


def test_adverse_regressions_retained_independently_of_genuine_gate():
    bad=comparison("unseen_interval",low=-.12,high=-.021)
    result=study.advancement([cell("genuine")],[bad,comparison("genuine")])
    assert result["paired_gains"][0]["supported_adverse_regression"]
    bad["ci_high"]=-.02
    result=study.advancement([cell("genuine")],[bad,comparison("genuine")])
    assert not result["paired_gains"][0]["supported_adverse_regression"]
