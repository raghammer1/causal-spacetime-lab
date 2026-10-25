"""Known finite examples for the explicitly secondary graph-conditioned table."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest

PATH=Path(__file__).resolve().parents[1]/'scripts/dynamical_conditioned_response.py'
spec=importlib.util.spec_from_file_location('dynamical_secondary',PATH)
secondary=importlib.util.module_from_spec(spec)
spec.loader.exec_module(secondary)


def test_fractional_ties_and_undefined_source_are_explicit():
    uniform=np.ones((5,5))-np.eye(5)
    F,totals=secondary.concentration(uniform)
    assert F==pytest.approx(.5)
    assert np.array_equal(totals,[4]*5)
    uniform[0]=0
    assert secondary.concentration(uniform)[0] is None
    tied=np.array([[0,5,3,3],[5,0,3,3],[3,3,0,5],[3,3,5,0.]])
    assert secondary.concentration(tied)[0]==pytest.approx(8/11)


def test_mean_conditioned_capture_is_not_capture_of_average():
    matchings=[]
    for pairs in [((0,1),(2,3)),((0,2),(1,3)),((0,3),(1,2))]:
        response=np.zeros((4,4))
        for i,j in pairs:response[i,j]=response[j,i]=1
        matchings.append(response)
    assert np.mean([secondary.concentration(a)[0] for a in matchings])==1
    assert secondary.concentration(np.mean(matchings,axis=0))[0]==pytest.approx(2/3)


def test_nulls_preserve_probability_and_labeled_degree_classes():
    bits,connected,groups=secondary.graphs(5)
    rng=np.random.default_rng(872033)
    p=rng.random(len(bits));p/=p.sum()
    q=secondary.laws(p,bits,groups)
    assert all(np.sum(v)==pytest.approx(1) for v in q.values())
    assert q['density']@bits.sum(axis=1)==pytest.approx(p@bits.sum(axis=1))
    for indices in groups:assert q['degree'][indices].sum()==pytest.approx(p[indices].sum())
    assert connected.sum()==728


def test_average_of_preparation_ratios_and_pooled_ratio_are_both_reported():
    rows=[]
    for rep,(mass,F) in enumerate([(.1,.9),(.9,.5)]):
        rows.append(dict(N=5,cell=0,preparation='E',law='Born',delay=.25,
            valid_graph_F_probability=mass,undefined_graph_F_probability=1-mass,
            zero_total_response_probability=0,partial_zero_source_probability=1-mass,
            mean_graph_conditioned_F_given_valid=F,graph_F_mass_weighted_sum=mass*F,
            F_of_average_conditional_response=.5,F_of_unobserved_mixture_response=.5,
            connected_probability=mass,valid_and_connected_probability=mass))
    group=secondary.aggregate(rows)[0]
    assert group['metrics']['mean_graph_conditioned_F_given_valid']['mean']==pytest.approx(.7)
    assert group['pooled_graph_conditioned_F_given_valid']==pytest.approx(.54)
    assert group['metrics']['mean_graph_conditioned_F_given_valid']['undefined_units']==0
