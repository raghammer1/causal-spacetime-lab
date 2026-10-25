"""Stream, cohort and end-to-end smoke archive integrity checks."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from causal_lab import dynamical_artifacts, dynamical_study
from causal_lab.dynamical_statistics import summarize


def cohort(sizes=(4,5),cells=2,repeats=12):
    return [dict(N=n,cell=cell,preparation='E',batch=batch,replicate=rep,status='ok',
                 gate={key:False for key in ('C','L','T','D','joint')},degree_null_event=False)
            for n in sizes for cell in range(cells) for batch in range(3) for rep in range(repeats)]


def test_semantic_streams_replay_and_separate_every_registered_namespace():
    # Deliberately impossible scientific coordinates: this never consumes a real
    # primary preparation stream while checking the namespace derivation itself.
    values={stream:dynamical_study.rng_for(stream,99,99,99,99,999).integers(0,2**32,8).tolist()
            for stream in dynamical_study.STREAMS}
    assert len({tuple(value) for value in values.values()})==len(values)
    assert values['audit']==dynamical_study.rng_for('audit',99,99,99,99,999).integers(0,2**32,8).tolist()
    assert values['audit']!=dynamical_study.rng_for('audit',99,99,99,99,1000).integers(0,2**32,8).tolist()
    with pytest.raises(KeyError):dynamical_study.rng_for('unknown',99,99,99,99,999)


def test_initial_factors_have_registered_support_and_no_hidden_graph():
    plus,phases=dynamical_study.initial_factors(5,'Splus',None)
    np.testing.assert_array_equal(plus,np.full(10,.5));np.testing.assert_array_equal(phases,0)
    empty,phases=dynamical_study.initial_factors(5,'Sempty',None)
    np.testing.assert_array_equal(empty,0);np.testing.assert_array_equal(phases,0)
    first=dynamical_study.initial_factors(5,'E',dynamical_study.rng_for('smoke',5,0,0,0,901))
    second=dynamical_study.initial_factors(5,'E',dynamical_study.rng_for('smoke',5,0,0,0,901))
    for a,b in zip(first,second):np.testing.assert_array_equal(a,b)
    assert np.all((first[0]>=.25)&(first[0]<=.75))
    assert np.all((first[1]>=0)&(first[1]<2*np.pi))
    assert np.ptp(first[0])>0
    with pytest.raises(ValueError):dynamical_study.initial_factors(5,'ring',None)


def test_complete_failed_cohorts_eliminate_all_candidate_settings():
    result=summarize(cohort(),[4,5],cells=2,expected_per_cell=36)
    assert result['complete_expected_cohorts']
    assert result['decision']=='NO-GO'
    assert result['eliminated_parameter_settings']==[0,1]


def test_missing_row_or_entire_cell_cannot_establish_no_go():
    rows=cohort()
    result=summarize(rows[:-1],[4,5],cells=2,expected_per_cell=36)
    assert not result['complete_expected_cohorts']
    assert result['decision']=='INCONCLUSIVE'
    rows=[r for r in rows if not(r['N']==5 and r['cell']==1)]
    result=summarize(rows,[4,5],cells=2,expected_per_cell=36)
    assert not result['complete_expected_cohorts']
    assert result['decision']=='INCONCLUSIVE'


def test_duplicate_preparation_cannot_replace_a_missing_independent_unit():
    rows=cohort()
    rows[-1]=dict(rows[-2])
    result=summarize(rows,[4,5],cells=2,expected_per_cell=36)
    assert not result['complete_expected_cohorts']
    assert result['decision']=='INCONCLUSIVE'


def test_wrong_batch_identity_and_numerical_failures_invalidate_model_decision():
    rows=cohort();rows[-1]['batch']=9
    result=summarize(rows,[4,5],cells=2,expected_per_cell=36)
    assert not result['complete_expected_cohorts']
    assert result['decision']=='INCONCLUSIVE'
    rows=cohort();rows[-1]['status']='failed'
    result=summarize(rows,[4,5],cells=2,expected_per_cell=36)
    assert result['decision']=='INCONCLUSIVE'


@pytest.fixture(scope='module')
def smoke_archives(tmp_path_factory):
    root=tmp_path_factory.mktemp('dynamical-smoke-replay')
    patch=pytest.MonkeyPatch()
    # Rendering and full coverage grids are separately validated. This test runs
    # every quantum/control/serialization path of a one-cell N4 smoke twice.
    def figure_stub(out,*args):
        (Path(out)/'figure-smoke.txt').write_text('Rendering is exercised by the CLI smoke.\n')
    patch.setattr(dynamical_artifacts,'write_figures',figure_stub)
    full_calibration=dynamical_study.calibrate_cp
    patch.setattr(dynamical_study,'calibrate_cp',lambda rng:full_calibration(rng,trials=(12,),families=(12,)))
    outputs=[]
    try:
        for label in ('first','second'):
            output=root/label
            summary=dynamical_study.run(output,mode='smoke',sizes=(4,),repeats=1,cells=(0,))
            assert summary['independent_control_validation_passed']
            outputs.append(output)
    finally:
        patch.undo()
    return outputs


def test_smoke_replay_scientific_files_match_exactly(smoke_archives):
    first,second=smoke_archives
    digest=dynamical_study.verify_manifest(first)
    assert dynamical_study.verify_manifest(second)==digest
    manifest=json.loads((first/'manifest.json').read_text())
    for name in manifest['scientific_files']:
        assert (first/name).read_bytes()==(second/name).read_bytes(),name
    for output in smoke_archives:
        raw=(output/'raw.json.gz').read_bytes()
        assert raw[4:8]==b'\x00\x00\x00\x00'
        assert not raw[3]&8
        rows=json.loads(gzip.decompress(raw))
        assert len(rows)==3
        assert {r['preparation'] for r in rows}=={'Splus','Sempty','E'}
        for row in rows:
            assert row['status']=='ok'
            with np.load(output/row['array_file']) as arrays:
                assert arrays['full_born'].shape==(6,64)
                assert arrays['full_response'].shape==(7,4,4)
                assert arrays['static_born_conditional_response'].shape==(7,4,4)
                mixture=arrays['static_born_mixture_response']
                conditional=arrays['static_born_conditional_response']
                assert np.all(mixture<=conditional+2e-9)


def minimal_archive(out):
    out.mkdir()
    (out/'arrays').mkdir()
    dynamical_study.write_npz(out/'arrays/state.npz',{'x':np.arange(4)})
    dynamical_study.write_raw(out/'raw.json.gz',[{'state':'fixture'}])
    dynamical_study.write_json(out/'metadata.json',{'elapsed':1})
    dynamical_study.archive_manifest(out)
    return out


@pytest.mark.parametrize('filename',['raw.json.gz','arrays/state.npz','metadata.json'])
def test_manifest_detects_raw_array_and_provenance_tampering(tmp_path,filename):
    out=minimal_archive(tmp_path/'artifact')
    path=out/filename
    path.write_bytes(path.read_bytes()+b'changed')
    with pytest.raises(ValueError,match='hash mismatch'):
        dynamical_study.verify_manifest(out)


@pytest.mark.parametrize('field',['sha256','scientific_files'])
def test_manifest_rejects_both_hash_and_scientific_path_escape(tmp_path,field):
    out=minimal_archive(tmp_path/'artifact')
    manifest=json.loads((out/'manifest.json').read_text())
    (tmp_path/'outside').write_text('outside')
    if field=='sha256':manifest['sha256']['../outside']='invalid'
    else:manifest['scientific_files']=['../outside']
    (out/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='external'):
        dynamical_study.verify_manifest(out)


def test_manifest_requires_correct_scientific_digest(tmp_path):
    out=minimal_archive(tmp_path/'artifact')
    manifest=json.loads((out/'manifest.json').read_text())
    manifest['scientific_digest']=hashlib.sha256(b'wrong').hexdigest()
    (out/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='scientific digest'):
        dynamical_study.verify_manifest(out)


def test_nonempty_output_is_preserved(tmp_path):
    existing=tmp_path/'existing';existing.mkdir()
    (existing/'keep.txt').write_text('preserve')
    with pytest.raises(ValueError,match='new or empty'):
        dynamical_study.run(existing,mode='smoke',sizes=(4,),repeats=1,cells=(0,))
    assert (existing/'keep.txt').read_text()=='preserve'
