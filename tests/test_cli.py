import csv
import sys

import pytest

from causal_lab.cli import main


@pytest.mark.parametrize("arguments", [
    ["--repeats", "1"], ["--seed", "-1"], ["--duration", "nan"],
    ["--duration", "0"], ["--densities", "inf"], ["--densities", "-2"],
])
def test_invalid_cli_arguments_fail_before_writing(arguments, tmp_path, monkeypatch):
    out = tmp_path / "output"
    monkeypatch.setattr(sys, "argv", ["causal_lab.cli", "--out", str(out), *arguments])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert not out.exists()


def test_cli_reproduces_csv_and_creates_png(tmp_path, monkeypatch):
    outputs = [tmp_path / "a", tmp_path / "b"]
    for out in outputs:
        monkeypatch.setattr(sys, "argv", [
            "causal_lab.cli", "--seed", "17", "--repeats", "8",
            "--densities", "5", "20", "--out", str(out),
        ])
        main()
        assert (out / "time_reconstruction.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert ((outputs[0] / "time_reconstruction.csv").read_bytes()
            == (outputs[1] / "time_reconstruction.csv").read_bytes())
    with (outputs[0] / "time_reconstruction.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2
    assert all(float(row["standard_error"]) > 0 for row in rows)
