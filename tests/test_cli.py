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


# --- End to end (R3, R4, R6, R11, D6) ------------------------------------------------------


def temp_files(directory: Path) -> list[str]:
    return [p.name for p in directory.iterdir() if p.name.endswith(".tmp")]


def test_folder_end_to_end(
    fx: Fixtures, tmp_path: Path, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = fx.image_folder("Vol.2", {"p10.png": ["blue"], "p2.jpg": ["green"], "p1.png": ["red"]})
    assert run([str(folder)], factory) == 0

    output = tmp_path / "Vol.2.txt"
    assert output.read_text(encoding="utf-8") == (
        "--- Page 1 ---\nred\n\n--- Page 2 ---\ngreen\n\n--- Page 3 ---\nblue"
    )
    assert factory.calls == [("en", None)]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.splitlines() == [
        "Processing page 1...",
        "Processing page 2...",
        "Processing page 3...",
        f"Extracted text written to {output.resolve()}",
    ]
    assert temp_files(tmp_path) == []


def test_pdf_end_to_end_with_options(
    fx: Fixtures, tmp_path: Path, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    pdf = fx.pdf("book.pdf", [["red"], ["yellow"]])
    output = tmp_path / "out.txt"
    argv = [str(pdf), "-o", str(output), "--lang", "es", "--device", "cpu", "--dpi", "144"]
    assert run(argv, factory) == 0

    assert output.read_text(encoding="utf-8") == "--- Page 1 ---\nred\n\n--- Page 2 ---\nyellow"
    assert factory.calls == [("es", "cpu")]
    assert factory.engine.shapes == [(144, 144, 3), (144, 144, 3)]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.splitlines() == [
        "Processing page 1...",
        "Processing page 2...",
        f"Extracted text written to {output}",
    ]
    assert temp_files(tmp_path) == []


def test_pdf_default_output_replaces_the_suffix(fx: Fixtures, factory: FakeFactory) -> None:
    pdf = fx.pdf("book.v2.pdf", [["red"]])
    assert run([str(pdf)], factory) == 0
    assert pdf.with_name("book.v2.txt").read_text(encoding="utf-8") == "--- Page 1 ---\nred"


def test_columns_are_read_left_to_right_page_by_page(
    fx: Fixtures, tmp_path: Path, factory: FakeFactory
) -> None:
    folder = fx.image_folder(
        "book", {"p1.png": ["red", "blue"], "p2.png": ["green", "yellow"]}, width=61
    )
    output = tmp_path / "out.txt"
    assert run([str(folder), "-o", str(output), "--columns", "2"], factory) == 0
    assert output.read_text(encoding="utf-8") == (
        "--- Page 1 ---\nred\nblue\n\n--- Page 2 ---\ngreen\nyellow"
    )
    assert [shape[1] for shape in factory.engine.shapes] == [30, 31, 30, 31]


def test_pdf_columns_split_each_rendered_page(
    fx: Fixtures, tmp_path: Path, factory: FakeFactory
) -> None:
    pdf = fx.pdf("book.pdf", [["red", "green", "blue"], ["white", "black", "yellow"]], width=90)
    output = tmp_path / "out.txt"
    assert run([str(pdf), "-o", str(output), "--columns", "3", "--dpi", "72"], factory) == 0
    assert output.read_text(encoding="utf-8") == (
        "--- Page 1 ---\nred\ngreen\nblue\n\n--- Page 2 ---\nwhite\nblack\nyellow"
    )


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_existing_output_is_replaced_and_keeps_its_mode(
    fx: Fixtures, tmp_path: Path, factory: FakeFactory
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    output = tmp_path / "out.txt"
    output.write_text("old text\n", encoding="utf-8")
    output.chmod(0o644)
    assert run([str(folder), "-o", str(output)], factory) == 0
    assert output.read_text(encoding="utf-8") == "--- Page 1 ---\nred"
    assert output.stat().st_mode & 0o777 == 0o644
    assert temp_files(tmp_path) == []


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_new_output_gets_the_umask_default_mode(
    fx: Fixtures, tmp_path: Path, factory: FakeFactory
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    output = tmp_path / "out.txt"
    old_umask = os.umask(0o027)
    try:
        assert run([str(folder), "-o", str(output)], factory) == 0
    finally:
        os.umask(old_umask)
    assert output.stat().st_mode & 0o777 == 0o640
