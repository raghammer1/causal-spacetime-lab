"""Independent auditor invariants; no production implementation imports."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts'/'audit_dynamical_primary.py'
spec=importlib.util.spec_from_file_location('independent_dynamical_audit',SCRIPT)
audit=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=audit
spec.loader.exec_module(audit)


def test_mathematical_constructions_and_coefficients():
    check=audit.Audit();audit.mathematical_audit(check)
    assert check.report()['passed'],check.failures


def test_cp_interval_interior_tail_equations():
    for n,k,family in ((12,4,12),(24,12,24),(36,31,36)):
        low,high=audit.cp_bounds(k,n,family)
        tail=.05/(2*family)
        assert sum(audit.binomial_mass(n,low)[k:])==pytest.approx(tail,abs=1e-14)
        assert sum(audit.binomial_mass(n,high)[:k+1])==pytest.approx(tail,abs=1e-14)


def test_degree_class_connectivity_obstruction():
    for n in (4,5):
        c=audit.graph_catalog(n)
        mixed=[]
        for identifier in set(c['classes']):
            members=c['classes']==identifier
            if 0 < c['connected'][members].sum() < members.sum():
                mixed.append(members)
        if n==4:
            assert not mixed
        else:
            assert len(mixed)==10
            for members in mixed:
                assert members.sum()==7 and c['connected'][members].sum()==6
                assert sorted(c['degrees'][members][0])==[1,1,2,2,2]


def test_graph_nulls_preserve_their_registered_statistics():
    c=audit.graph_catalog(4);p=np.arange(1,65,dtype=float);p/=sum(p)
    laws=audit.null_laws(p,c)
    assert laws['product']@c['graph_bits']==pytest.approx(p@c['graph_bits'])
    for name,key in [('count','edge_count'),('degree','classes')]:
        for value in set(c[key]):
            members=c[key]==value
            assert sum(laws[name][members])==pytest.approx(sum(p[members]))


def test_partials_joint_observables_and_kick_use_tensor_convention():
    psi=audit.prepare(2,[.37],[.8]);rho,bloch=audit.partials(psi,2)
    assert bloch==pytest.approx(np.array([[2**-.5,0,2**-.5]]*2))
    zx,zy=audit.joint_moments(psi,2)
    assert zx==pytest.approx(np.array([[0,.37/2],[.37/2,0]]))
    assert zy==pytest.approx(np.zeros((2,2)))
    kicked=audit.kick(psi,2,0)
    assert kicked==pytest.approx(audit.tensor_operator(3,{0:audit.Y})@psi)
    assert abs(np.vdot(psi,kicked))<1e-14
    assert np.linalg.eigvalsh(rho)==pytest.approx(np.array([[0,1],[0,1]]),abs=1e-14)


def test_reduced_trace_distance_and_fractional_ties():
    base=np.zeros((4,3));probe=np.zeros((4,4,3));probe[:,:,2]=.4
    distance=audit.distances_from_bloch(base,probe)
    assert distance==pytest.approx(np.full((4,4),.2))
    f,mean,weights=audit.finite_score(distance)
    assert f==pytest.approx(2/3)
    assert mean==pytest.approx(.2)
    assert weights.sum(1)==pytest.approx(np.full(4,2.))
    assert audit.finite_score(np.zeros((4,4)))[0] is None


def test_small_norm_drift_cannot_be_hidden_by_normalizing_born():
    check=audit.Audit();check.probability(np.array([.3,.8]),'bad')
    assert not check.report()['passed']
    assert check.failures[0]['category']=='probability_normalization'


def test_audit_reports_boolean_mismatch_and_nonfinite_values():
    check=audit.Audit();check.close([True,False],[True,True],'boolean','bad')
    check.close([np.nan],[0.],'finite','bad')
    assert len(check.failures)==2


def test_tensor_matrix_evolution_preserves_product_limit():
    n=2;params=dict(h=1.,g=0.,Gamma=.25,mu=.1,U=0.)
    state=audit.prepare(n,[.5],[.3]);matrix=audit.independent_hamiltonian(n,params)
    evolved=audit.advance(matrix,state,.25)
    for rho in audit.partials(evolved,n)[0]:
        assert np.trace(rho@rho).real==pytest.approx(1.)
