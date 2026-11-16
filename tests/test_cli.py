"""The CLI end to end with the fake engine (R3–R12, R19, R20, D6, D7)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from conftest import FakeFactory, Fixtures

from scanscribe.cli import build_parser, run

# --- Arguments and paths (R9, R10, R19, D7) ------------------------------------------------


def test_defaults() -> None:
    args = build_parser().parse_args(["book.pdf"])
    assert (args.lang, args.dpi, args.columns, args.device, args.output) == (
        "en",
        200,
        1,
        None,
        None,
    )


def test_help_lists_every_option_on_stdout(
    factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(["--help"], factory) == 0
    out = capsys.readouterr().out
    assert out.startswith("usage: scanscribe")
    for option in ("input", "-o", "--output", "--lang", "--dpi", "--device", "--columns"):
        assert option in out
    assert factory.calls == []


@pytest.mark.parametrize(
    "argv",
    [["--columns", "0"], ["--dpi", "-5"], ["--dpi", "0"], ["--columns", "two"]],
)
def test_columns_and_dpi_below_1_are_usage_errors(
    fx: Fixtures, factory: FakeFactory, capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    assert run([str(folder), *argv], factory) == 2
    err = capsys.readouterr().err
    assert err.startswith("usage: scanscribe")
    assert "scanscribe: error:" in err
    assert factory.calls == []


def test_missing_input_is_a_usage_error(
    tmp_path: Path, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run([str(tmp_path / "missing.pdf")], factory) == 2
    assert "input not found" in capsys.readouterr().err
    assert factory.calls == []


def test_output_in_a_missing_directory_is_a_usage_error(
    fx: Fixtures, tmp_path: Path, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    output = tmp_path / "missing-dir" / "out.txt"
    assert run([str(folder), "-o", str(output)], factory) == 2
    assert "output directory does not exist" in capsys.readouterr().err
    assert factory.calls == []


def test_output_that_is_a_directory_is_a_usage_error(
    fx: Fixtures, tmp_path: Path, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    (tmp_path / "out").mkdir()
    assert run([str(folder), "-o", str(tmp_path / "out")], factory) == 2
    assert "output is a directory" in capsys.readouterr().err
    assert factory.calls == []


@pytest.mark.skipif(
    sys.platform == "win32" or os.geteuid() == 0, reason="needs POSIX permissions, not root"
)
def test_unwritable_output_directory_is_a_usage_error(
    fx: Fixtures, tmp_path: Path, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o555)
    try:
        assert run([str(folder), "-o", str(locked / "out.txt")], factory) == 2
    finally:
        locked.chmod(0o755)
    assert "output directory is not writable" in capsys.readouterr().err
    assert factory.calls == []
    assert not (locked / "out.txt").exists()


def test_output_that_is_the_input_is_a_usage_error(
    fx: Fixtures, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    pdf = fx.red_pdf("book.pdf")
    before = pdf.read_bytes()
    assert run([str(pdf), "-o", str(pdf)], factory) == 2
    assert "output would overwrite the input" in capsys.readouterr().err
    assert factory.calls == []
    assert pdf.read_bytes() == before


def test_input_named_txt_would_overwrite_itself_by_default(
    fx: Fixtures, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    text = fx.notes_dat("notes.txt")
    assert run([str(text)], factory) == 2
    assert "output would overwrite the input" in capsys.readouterr().err
