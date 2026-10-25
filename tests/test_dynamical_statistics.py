import numpy as np
import pytest
from causal_lab.dynamical_statistics import top_two,cp_interval,assess_unit,calibrate_cp,summarize

@pytest.mark.parametrize('n',[4,5,6])
def test_fractional_ties(n):
    r=np.ones((n,n));np.fill_diagonal(r,0)
    a=top_two(r)
    assert a['F']==pytest.approx(2/(n-1))
    assert np.allclose(a['weights'].sum(1),2)
    assert a['normalized_excess']==pytest.approx(0)
    assert np.isnan(top_two(r*0)['F'])

def test_top_two_not_label_tie_broken():
    r=np.array([[0,5,3,3],[5,0,3,3],[3,3,0,5],[3,3,5,0.]])
    out=top_two(r);assert np.allclose(out['weights'][0],[0,1,.5,.5])
    perm=[2,0,3,1]
    assert np.allclose(top_two(r[np.ix_(perm,perm)])['weights'],out['weights'][np.ix_(perm,perm)])

def test_cp_exact_endpoints_and_power():
    assert cp_interval(0,36,12)[1]==pytest.approx(1-(.05/24)**(1/36))
    assert cp_interval(36,36,12)[0]>.8
    assert cp_interval(24,24,12)[0]<.8
    assert cp_interval(36,36,24)[0]>.8
    assert cp_interval(0,12,12)[0]==0
    with pytest.raises(ValueError):cp_interval(4,3)

def test_gate_zero_and_uniform_do_not_pass():
    born=np.tile([0.,1.],(6,1));r=np.ones((7,4,4))*.1
    for a in r:np.fill_diagonal(a,0)
    g=assess_unit(born,[0,1],r,r,r,[0,.05,.1,.25,.5,1,2])
    assert g['C'] and g['T'] is False and not g['L'] and not g['D'] and not g['joint']
    g=assess_unit(born,[0,1],r*0,r*0,r*0,[0,.05,.1,.25,.5,1,2])
    assert not g['joint']

def test_decision_requires_each_parameter_eliminated_and_no_numerical_failure():
    gate={k:False for k in ['C','L','T','D','joint']}
    rows=[dict(N=n,cell=c,preparation='E',status='ok',gate=gate) for n in [4,5] for c in range(6) for _ in range(12)]
    assert summarize(rows,[4,5])['decision']=='NO-GO'
    rows[0]['status']='failed'
    assert summarize(rows,[4,5])['decision']=='INCONCLUSIVE'

def test_exact_binomial_coverage():
    assert calibrate_cp(np.random.default_rng(91),trials=(12,),families=(12,))['passed']
