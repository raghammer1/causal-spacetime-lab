"""Canonical archive replay, undefined values and manifest tamper checks."""
import gzip
import hashlib
import json

import numpy as np
import pytest

from causal_lab import quantum_artifacts
from causal_lab.quantum_artifacts import make_manifest, verify_manifest
from causal_lab.quantum_study import canonical, plain, save


def rows():
    common = dict(family="fixture",n=4,h=1.,preparation="control",delta=0.,time=0.,
                  stochastic=True,status="ok")
    return [dict(common,unit_id=f"audit/{i}",sample_id=f"audit/{i}",batch=i,
                 metrics={"value":float(i),"undefined_rank":np.nan if i == 0 else .5},
                 state=np.array([1+0j,0+1j])/np.sqrt(2),
                 couplings=np.array([[0,1],[1,0]])) for i in range(2)]


def write_archive(path,monkeypatch,metadata=None):
    path.mkdir()
    def figure_stub(out,records,summary):
        (out/"figure-test.txt").write_text("Scientific figures are independently smoke-rendered.\n")
    monkeypatch.setattr(quantum_artifacts,"write_figures",figure_stub)
    save(path,rows(),metadata or {"phase":"audit"},resamples=19)
    return path


def test_plain_and_canonical_preserve_complex_components_without_non_json_nan():
    value={"z":np.array([1+2j,3+4j]),"a":np.array([np.nan,np.inf,-np.inf]),"n":np.int64(3)}
    cleaned=plain(value)
    assert cleaned["z"] == {"real":[1.,3.],"imag":[2.,4.]}
    assert cleaned["a"] == [None,None,None]
    assert cleaned["n"] == 3
    encoded=canonical(value)
    assert b"NaN" not in encoded and b"Infinity" not in encoded
    assert encoded == canonical(dict(reversed(list(value.items()))))
    assert json.loads(encoded) == cleaned


def test_save_replays_scientific_bytes_and_canonical_gzip(tmp_path,monkeypatch):
    first=write_archive(tmp_path/"first",monkeypatch,{"elapsed_seconds":1.})
    second=write_archive(tmp_path/"second",monkeypatch,{"elapsed_seconds":2.})
    for name in ("raw.jsonl.gz","summary.json","summary.csv"):
        assert (first/name).read_bytes() == (second/name).read_bytes()
    assert (first/"metadata.json").read_bytes() != (second/"metadata.json").read_bytes()
    assert verify_manifest(first) == verify_manifest(second)
    raw=(first/"raw.jsonl.gz").read_bytes()
    assert raw[:2] == b"\x1f\x8b"
    assert raw[4:8] == b"\x00\x00\x00\x00"  # No wall-clock timestamp.
    assert raw[3] & 8 == 0  # No machine-specific filename header.
    parsed=[json.loads(line) for line in gzip.decompress(raw).splitlines()]
    assert parsed == plain(rows())
    summary=json.loads((first/"summary.json").read_text())
    undefined=summary[0]["metrics"]["undefined_rank"]
    assert undefined["n"] == 1
    assert undefined["undefined"] == 1
    assert undefined["mean"] == .5


@pytest.mark.parametrize("filename",["raw.jsonl.gz","summary.json","summary.csv","metadata.json","figure-test.txt"])
def test_manifest_detects_tampering_in_every_artifact_class(tmp_path,monkeypatch,filename):
    out=write_archive(tmp_path/"data",monkeypatch)
    path=out/filename
    path.write_bytes(path.read_bytes()+b"tampered")
    with pytest.raises(ValueError,match="artifact mismatch"):
        verify_manifest(out)


def test_manifest_is_stable_and_all_artifacts_are_hashed(tmp_path,monkeypatch):
    out=write_archive(tmp_path/"data",monkeypatch)
    before=(out/"manifest.json").read_bytes()
    manifest=make_manifest(out)
    assert (out/"manifest.json").read_bytes() == before
    assert "manifest.json" not in manifest["sha256"]
    for name,digest in manifest["sha256"].items():
        assert hashlib.sha256((out/name).read_bytes()).hexdigest() == digest
    assert verify_manifest(out) == manifest["scientific_digest"]


def test_manifest_rejects_path_escape(tmp_path,monkeypatch):
    out=write_archive(tmp_path/"data",monkeypatch)
    manifest=json.loads((out/"manifest.json").read_text())
    manifest["sha256"]["../outside.txt"]="unused"
    (out/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="external artifact path"):
        verify_manifest(out)


def test_manifest_rejects_scientific_path_escape(tmp_path,monkeypatch):
    out=write_archive(tmp_path/"data",monkeypatch)
    manifest=json.loads((out/"manifest.json").read_text())
    manifest["scientific_files"]=["../outside.txt"]
    (out/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="external scientific path"):
        verify_manifest(out)


def test_manifest_detects_wrong_scientific_digest_even_when_file_hashes_match(tmp_path,monkeypatch):
    out=write_archive(tmp_path/"data",monkeypatch)
    manifest=json.loads((out/"manifest.json").read_text())
    manifest["scientific_digest"]="0"*64
    (out/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="scientific digest mismatch"):
        verify_manifest(out)
