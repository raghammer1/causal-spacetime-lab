import numpy as np
import pytest
from causal_lab.quantum_random import rng_for, stream_key, SEEDS
from causal_lab.quantum_statistics import stratified_mean_interval, binomial_lower, calibration, summarize


def test_stream_isolation_replay():
    values = [rng_for(phase,0,"stream-isolation-test-only").normal(size=20) for phase in SEEDS]
    assert len({a.tobytes() for a in values}) == len(SEEDS)
    np.testing.assert_array_equal(values[0],rng_for("smoke",0,"stream-isolation-test-only").normal(size=20))
    assert stream_key("smoke",0,"A") != stream_key("smoke",0,"B")
    with pytest.raises(ValueError): rng_for("primary",4)
    with pytest.raises(ValueError): rng_for("unknown",0)


def test_stratified_linear_mean_constant_and_shift():
    a = np.arange(24,dtype=float);b=np.repeat(np.arange(3),8)
    first = stratified_mean_interval(a,b,np.random.default_rng(1),resamples=99)
    second = stratified_mean_interval(a+4,b,np.random.default_rng(1),resamples=99)
    assert first["mean"]==11.5
    np.testing.assert_allclose(np.array(first["ci95"])+4,second["ci95"])
    constant=stratified_mean_interval(np.ones(24),b,np.random.default_rng(1),resamples=99)
    assert constant["ci95"]==[1.,1.]
    assert binomial_lower(24,24,.05/3)==pytest.approx((.05/3)**(1/24))
    assert binomial_lower(0,24)==0
    assert binomial_lower(24,24)<1  # all successes are not certainty


def test_calibration_exact_coverage_and_finite_mc():
    result=calibration()
    assert all(r["coverage"] >= 1-.05/3-1e-12 for r in result["binomial_exact_coverage"])
    assert .86 <= result["normal_coverage"] <= .99


def test_no_pseudoreplication():
    row=dict(family="B",n=6,h=1,preparation="ground",delta=0,time=0,
             unit_id="x",batch=0,status="ok",stochastic=True,metrics={"mi_mean":.2})
    with pytest.raises(ValueError,match="duplicate"):
        summarize([row,row],resamples=10)
