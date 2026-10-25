"""Scientific contracts for Experiment 3 scores, splits and uncertainty."""
from copy import deepcopy
import json
import math

import numpy as np
import pytest

from causal_lab import adversarial_detectors as det
from causal_lab.adversarial_features import extract_features
from causal_lab.dimension_study import _scores as previous_scores
from causal_lab.order_observables import antichain, random_dag_order


def feature_row(values=(.3, .2, .5, .1, .2), *, count=20, abundance=None, **extra):
    return {"count": count, **dict(zip(det.FEATURES, values)),
            "abundance_vector": list(abundance if abundance is not None else [.1]*10), **extra}


def template(dimension=2, centroid=(.3, .2, .5, .1, .2), scale=(.1,)*5,
             abundance=None):
    return {"dimension": dimension, "centroid": list(centroid), "scale": list(scale),
            "abundance_centroid": list(abundance if abundance is not None else [.1]*10)}


def model(templates=None):
    return {"count": 20, "templates": templates or [template()],
            "thresholds": {"0.95": dict.fromkeys(det.DETECTORS, 1.0)}}


@pytest.fixture
def partitions():
    fit, validation = [], []
    for d in (2, 3, 4):
        for i in range(10):
            # Different features correlated by construction, with nonzero SD.
            values = np.array([.7/d, .4/d, .15*d, .15/d, .25/d])+i*.002
            fit.append(feature_row(values, true_dimension=d, sample_id=f"fit-{d}-{i}"))
            validation.append(feature_row(values+.001, true_dimension=d, sample_id=f"validation-{d}-{i}"))
    return fit, validation


def test_six_scores_match_direct_arithmetic_and_original_D():
    row = feature_row((.5, .3, .5, .1, .2))
    fitted = model()
    scored = det.score_detectors(row, fitted)
    assert scored["A"]["score"] == pytest.approx(2)
    assert scored["B"]["score"] == pytest.approx(1)
    assert scored["C"]["score"] == pytest.approx(math.sqrt(2.5))
    assert scored["D"]["score"] == pytest.approx(1)
    assert scored["E"]["score"] == pytest.approx(2)
    assert scored["F"]["score"] == pytest.approx(0)
    old_a, old_d = previous_scores(row, fitted)
    assert scored["A"]["score"] == old_a
    assert scored["D"]["score"] == old_d


def test_compensation_is_preserved_as_benchmark_not_repaired():
    # Registered archived residuals; scale chosen so all physical features are valid.
    z = np.array([-2.5849393065856163, -.4373954058239033, -.6345231643697703,
                  -1.0000952151733686, -1.6977015360600642])
    fitted = model([template(4, centroid=[.5]*5, scale=[.1]*5)])
    fitted["thresholds"]["0.95"].update(A=1.8224914136711767, D=1.6942293968219286,
                                          E=1.6942293968219286)
    result = det.evaluate_detectors(feature_row(.5+.1*z), fitted)
    assert not result["A"]["accepted"]
    assert result["D"]["accepted"]
    assert not result["E"]["accepted"]
    assert result["D"]["score"] == pytest.approx(1.49386924132217)


def test_E_is_min_of_template_maxima_not_max_of_marginal_minima():
    row = feature_row([.5]*5)
    fitted = model([template(2, centroid=[.5,.2,.5,.5,.5]),
                    template(3, centroid=[.2,.5,.5,.5,.5])])
    scored = det.score_detectors(row, fitted)
    assert scored["A"]["score"] == scored["B"]["score"] == 0
    assert scored["E"]["score"] == pytest.approx(3)
    assert scored["E"]["candidate_dimension"] == 2


def test_ties_select_lower_dimension_independent_of_template_order():
    row = feature_row()
    scored = det.score_detectors(row, model([template(4),template(2),template(3)]))
    assert all(value["candidate_dimension"] == 2 for value in scored.values())


def test_detector_specific_cost_API_preserves_scores_without_computing_unused_features():
    row=feature_row((.5,.3,.5,.1,.2))
    fitted=model([template(2),template(3,centroid=[.4]*5)])
    full=det.score_detectors(row,fitted)
    for name in det.DETECTORS:
        assert det.score_detectors(row,fitted,detectors=(name,))=={name:full[name]}
    # Fraction-only evaluation needs no abundance vector; F needs no five-vector.
    without_abundance={k:v for k,v in row.items() if k!="abundance_vector"}
    assert det.score_detectors(without_abundance,fitted,detectors=("A",))=={"A":full["A"]}
    only_abundance={"count":20,"abundance_vector":row["abundance_vector"]}
    assert det.score_detectors(only_abundance,fitted,detectors=("F",))=={"F":full["F"]}


@pytest.mark.parametrize("subset", [(),("A","A"),("G",),True,None])
def test_invalid_detector_subset(subset):
    with pytest.raises(ValueError): det.score_detectors(feature_row(),model(),detectors=subset)


def test_hellinger_exact_disjoint_and_identical_distributions():
    point = [1.0]+[0.0]*9
    opposite = [0.0,1.0]+[0.0]*8
    fitted = model([template(abundance=point)])
    assert det.score_detectors(feature_row(abundance=point), fitted)["F"]["score"] == 0
    assert det.score_detectors(feature_row(abundance=opposite), fitted)["F"]["score"] == 1


def test_antichain_F_remains_defined_and_conditional_scores_reject():
    row = extract_features(antichain(20))
    result = det.evaluate_detectors(row, model())
    assert result["A"]["score"] is not None and result["B"]["score"] is not None
    assert result["C"]["score"] is not None and result["F"]["score"] is not None
    for name in ("D", "E"):
        assert result[name]["score"] is None
        assert not result[name]["accepted"]
        assert result[name]["rejection_reason"] == "undefined required order features"


def test_inference_ignores_true_dimension_target_and_other_metadata():
    fitted = model([template(2),template(3, centroid=[.2]*5)])
    a = feature_row(true_dimension=2, target_dimension=4, family="genuine")
    b = feature_row(true_dimension=999, target_dimension=-1, family="anything")
    assert det.evaluate_detectors(a, fitted) == det.evaluate_detectors(b, fitted)


def test_order_relabeling_does_not_change_any_detector():
    rng = np.random.default_rng(7)
    order = random_dag_order(20, rng, .1)
    permutation = rng.permutation(20)
    a = extract_features(order)
    b = extract_features(order[np.ix_(permutation,permutation)])
    assert det.evaluate_detectors(a, model()) == det.evaluate_detectors(b, model())


def test_fit_thresholds_use_validation_only_and_all_targets(partitions):
    fit, validation = partitions
    fitted = det.fit_model(fit, validation)
    assert set(fitted["thresholds"]) == {"0.9","0.95","0.975"}
    for target, thresholds in fitted["thresholds"].items():
        for detector, threshold in thresholds.items():
            scores = [det.score_detectors(r, fitted)[detector]["score"] for r in validation]
            assert threshold == float(np.quantile(scores,float(target)))
            achieved = sum(s <= threshold for s in scores)/len(scores)
            assert fitted["validation"][target][detector]["achieved_acceptance"] == achieved
    perturbed = deepcopy(validation)
    for row in perturbed:
        row["ordering_fraction"] += .05
    changed = det.fit_model(fit, perturbed)
    assert fitted["templates"] == changed["templates"]
    assert fitted["thresholds"]["0.95"]["A"] != changed["thresholds"]["0.95"]["A"]
    assert not fitted["holdout_used_for_calibration"]
    json.dumps(fitted, allow_nan=False)


def test_complete_row_exclusions_and_sd_floor_recorded(partitions):
    fit, validation = partitions
    fit[0]["link_fraction"] = None
    fitted = det.fit_model(fit, validation)
    assert fitted["templates"][0]["excluded_undefined_fit_count"] == 1
    assert fitted["templates"][0]["defined_fit_count"] == 9
    constant = [feature_row(true_dimension=2, sample_id=f"fit-{i}") for i in range(3)]
    val = [feature_row(true_dimension=2, sample_id=f"val-{i}") for i in range(3)]
    constant_model = det.fit_model(constant,val)
    assert constant_model["templates"][0]["scale"] == [1e-9]*5
    assert all(x["accepted"] for x in det.evaluate_detectors(feature_row(), constant_model).values())


def test_undefined_validation_scores_remain_in_acceptance_denominator(partitions):
    fit, validation = partitions
    validation[0]["link_fraction"] = None
    fitted = det.fit_model(fit,validation)
    report = fitted["validation"]["0.95"]["D"]
    assert report["undefined_count"] == 1
    assert report["defined_count"] == 29
    assert report["total"] == 30
    assert report["achieved_acceptance"] == report["accepted"]/30


@pytest.mark.parametrize("change", ["overlap","duplicate","count","missing_id","dimension","no_complete"])
def test_partition_failures(partitions,change):
    fit, validation = partitions
    if change == "overlap": validation[0]["sample_id"] = fit[0]["sample_id"]
    elif change == "duplicate": fit[0]["sample_id"] = fit[1]["sample_id"]
    elif change == "count": validation[0]["count"] = 21
    elif change == "missing_id": del fit[0]["sample_id"]
    elif change == "dimension": fit[0]["true_dimension"] = True
    else:
        for row in fit:
            if row["true_dimension"] == 2: row["link_fraction"] = None
    with pytest.raises(ValueError): det.fit_model(fit,validation)


@pytest.mark.parametrize("target", [-1,0,1,float("nan"),float("inf"),True,".95"])
def test_invalid_target(partitions,target):
    with pytest.raises(ValueError): det.fit_model(*partitions,target_rates=[target])
    with pytest.raises(ValueError): det.evaluate_detectors(feature_row(),model(),target=target)


@pytest.mark.parametrize("value", [float("nan"),float("inf"),-0.1,1.1,True,".5"])
def test_invalid_feature_values(value):
    row = feature_row()
    row["ordering_fraction"] = value
    with pytest.raises(ValueError): det.score_detectors(row,model())


@pytest.mark.parametrize("vector", [[.1]*9,[.2]*10,[float("nan")]+[0]*9,[-1]+[2]+[0]*8,[True]+[False]*9])
def test_invalid_abundance(vector):
    with pytest.raises(ValueError): det.score_detectors(feature_row(abundance=vector),model())


def test_missing_unfitted_and_malformed_models():
    row = feature_row()
    with pytest.raises(ValueError): det.score_detectors({k:v for k,v in row.items() if k != "link_fraction"},model())
    with pytest.raises(ValueError): det.score_detectors(feature_row(count=21),model())
    with pytest.raises(ValueError): det.evaluate_detectors(row,model(),target=.9)
    fitted=model(); fitted["templates"][0]["scale"][0]=0
    with pytest.raises(ValueError): det.score_detectors(row,fitted)


def test_wilson_known_values_and_nonzero_boundary_uncertainty():
    assert det.wilson_interval(200,200) == pytest.approx((.9811546736227335,1))
    assert det.wilson_interval(0,200) == pytest.approx((0,.01884532637726658))
    assert det.wilson_interval(49,200) == pytest.approx((.1905686808903718,.30904243556203415))
    assert det.wilson_interval(0,0) == (None,None)


@pytest.mark.parametrize("successes,count", [(True,1),(0,True),(1.0,2),(1,2.0),(-1,2),(3,2),(0,-1)])
def test_wilson_rejects_malformed_counts(successes,count):
    with pytest.raises(ValueError): det.wilson_interval(successes,count)


def test_repeated_fit_summary_never_pools_binomial_intervals():
    data = {0:[1]*200,1:[1]*190+[0]*10,2:[1]*180+[0]*20}
    result = det.summarize_fits(data,np.random.default_rng(3),500)
    assert result["mean_acceptance"] == pytest.approx(.95)
    assert result["between_fit_sd"] == pytest.approx(.05)
    assert result["total_orders"] == 600 and result["fit_count"] == 3
    assert "wilson_low" not in result
    assert result["per_fit"][0]["wilson_low"] == pytest.approx(.9811546736227335)
    assert not result["all_lower_at_least_0_90"]
    assert result["hierarchical_ci_low"] < .95 < result["hierarchical_ci_high"]
    assert result == det.summarize_fits(dict(reversed(list(data.items()))),np.random.default_rng(3),500)
    json.dumps(result,allow_nan=False)


def test_hierarchical_uncertainty_resamples_fits_not_only_orders():
    # Within every fit the data are constant. All uncertainty comes from fit choice.
    data = {0:[0]*200,1:[1]*200,2:[1]*200}
    result = det.summarize_fits(data,np.random.default_rng(2),5000)
    assert result["mean_acceptance"] == pytest.approx(2/3)
    assert result["hierarchical_ci_low"] == 0
    assert result["hierarchical_ci_high"] == 1
    assert result["between_fit_sd"] == pytest.approx(math.sqrt(1/3))


def test_hierarchical_bootstrap_empirical_variance_matches_exact_law():
    # One fit reduces to ordinary whole-order bootstrap: Var(mean)=p(1-p)/N.
    data = [np.array([0.,0.,1.,1.])]
    draws = det._hierarchical_means(data,np.random.default_rng(99),50000)
    assert draws.mean() == pytest.approx(.5,abs=.003)
    assert draws.var() == pytest.approx(.25/4,abs=.001)


def test_constant_bootstrap_does_not_replace_wilson_bounds():
    result = det.summarize_fits({0:[0]*200,1:[0]*200,2:[0]*200},np.random.default_rng(1),100)
    assert result["hierarchical_ci_low"] == result["hierarchical_ci_high"] == 0
    assert all(row["wilson_high"] > 0 for row in result["per_fit"])
    assert result["all_upper_at_most_0_05"]


def test_exact_controls_have_no_binomial_CI_and_no_fake_replication():
    result = det.summarize_fits({0:[0],1:[0],2:[1]},np.random.default_rng(1),100,deterministic=True)
    assert result["all_upper_at_most_0_05"] is None
    assert all(row["wilson_low"] is None and row["wilson_high"] is None for row in result["per_fit"])
    with pytest.raises(ValueError):
        det.summarize_fits({0:[0,0]},np.random.default_rng(1),100,deterministic=True)


def test_pairing_retains_disagreements_and_sign():
    left={0:[1]*13+[1]*122+[0]*36+[0]*29}
    right={0:[1]*13+[0]*122+[1]*36+[0]*29}
    result=det.paired_comparison(left,right,np.random.default_rng(5),1000)
    assert result["mean_difference"] == pytest.approx(.43)
    row=result["per_fit"][0]
    assert [row[k] for k in ("both_accepted","left_only","right_only","both_rejected")] == [13,122,36,29]
    assert result["ci_low"] > .05
    same=det.paired_comparison(left,left,np.random.default_rng(5),1000)
    assert same["mean_difference"] == same["ci_low"] == same["ci_high"] == 0


def test_pairing_equal_fit_weight_not_unbalanced_order_count_weight():
    left={0:[1]*2,1:[0]*20,2:[1]*200}
    right={0:[0]*2,1:[1]*20,2:[0]*200}
    result=det.paired_comparison(left,right,np.random.default_rng(5),100)
    assert result["mean_difference"] == pytest.approx(1/3)


@pytest.mark.parametrize("data", [{},{0:[]},{0:[float("nan")]},{0:[.5]},{0:[[0,1]]},{True:[0]}, {0:["0"]}])
def test_invalid_statistical_groups(data):
    with pytest.raises(ValueError): det.summarize_fits(data,np.random.default_rng(1),100)


def test_paired_alignment_and_bootstrap_count_validation():
    for right in ({1:[0,1]},{0:[0]}):
        with pytest.raises(ValueError): det.paired_comparison({0:[0,1]},right,np.random.default_rng(1),100)
    for count in (True,1,1.5):
        with pytest.raises(ValueError): det.summarize_fits({0:[0,1]},np.random.default_rng(1),count)
