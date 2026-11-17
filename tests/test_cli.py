"""The CLI end to end with the fake engine (R3–R12, R19, R20, D6, D7)."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Iterator
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


def assert_usage_error(err: str, contains: str) -> None:
    assert "Traceback" not in err
    assert err.startswith("usage: scanscribe")
    assert contains in err


@pytest.fixture
def locked_dir(tmp_path: Path) -> Iterator[Path]:
    """A directory nobody but root can look inside."""
    if sys.platform == "win32" or os.geteuid() == 0:
        pytest.skip("needs POSIX permissions, not root")
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o000)
    yield locked
    locked.chmod(0o755)


def test_input_in_an_unreadable_directory_is_a_usage_error(
    locked_dir: Path, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run([str(locked_dir / "book.pdf")], factory) == 2
    assert_usage_error(capsys.readouterr().err, "book.pdf")
    assert factory.calls == []


def test_output_in_an_unreadable_directory_is_a_usage_error(
    fx: Fixtures, locked_dir: Path, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    assert run([str(folder), "-o", str(locked_dir / "out.txt")], factory) == 2
    assert_usage_error(capsys.readouterr().err, "out.txt")
    assert factory.calls == []


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX symlinks")
def test_output_that_is_a_symlink_loop_is_a_usage_error(
    fx: Fixtures, tmp_path: Path, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    loop = tmp_path / "loop.txt"
    loop.symlink_to(loop)
    assert run([str(folder), "-o", str(loop)], factory) == 2
    assert_usage_error(capsys.readouterr().err, "loop.txt")
    assert factory.calls == []


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


# --- Errors and exit codes (R5, R7, R8, R12, R20, D7) --------------------------------------


def error_lines(err: str) -> list[str]:
    return [line for line in err.splitlines() if line.startswith("scanscribe: error:")]


def assert_one_error_line(err: str, contains: str) -> None:
    assert "Traceback" not in err
    [line] = error_lines(err)
    assert err.rstrip("\n").endswith(line)
    assert contains in line


@pytest.fixture
def existing_output(tmp_path: Path) -> Path:
    output = tmp_path / "out.txt"
    output.write_bytes(b"previous run\n\xe2\x9c\x93\n")
    return output


def test_empty_folder_exits_1_without_output(
    tmp_path: Path, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = tmp_path / "empty"
    folder.mkdir()
    assert run([str(folder)], factory) == 1
    assert_one_error_line(capsys.readouterr().err, "no page images found")
    assert not (tmp_path / "empty.txt").exists()
    assert factory.calls == []
    assert temp_files(tmp_path) == []


@pytest.mark.parametrize("builder", ["zero_page_pdf", "notes_dat"])
def test_unopenable_pdf_exits_1_naming_it(
    fx: Fixtures,
    tmp_path: Path,
    factory: FakeFactory,
    capsys: pytest.CaptureFixture[str],
    builder: str,
) -> None:
    path = getattr(fx, builder)()
    assert run([str(path)], factory) == 1
    assert_one_error_line(capsys.readouterr().err, path.name)
    assert not path.with_suffix(".txt").exists()
    assert factory.calls == []


def test_narrow_page_exits_1_before_the_engine_loads(
    fx: Fixtures, tmp_path: Path, factory: FakeFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]}, width=3)
    assert run([str(folder), "--columns", "4"], factory) == 1
    assert_one_error_line(capsys.readouterr().err, "p1.png")
    assert factory.calls == []
    assert not (tmp_path / "book.txt").exists()


def test_corrupt_third_image_exits_1_before_the_engine_loads(
    fx: Fixtures,
    tmp_path: Path,
    factory: FakeFactory,
    existing_output: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"], "p2.png": ["blue"]})
    fx.corrupt_image(folder, "p3.png")
    before = existing_output.read_bytes()
    assert run([str(folder), "-o", str(existing_output)], factory) == 1
    err = capsys.readouterr().err
    assert_one_error_line(err, "p3.png")
    assert "Processing page" not in err
    assert factory.calls == []
    assert existing_output.read_bytes() == before


def test_engine_error_on_page_2_leaves_the_output_untouched(
    fx: Fixtures,
    tmp_path: Path,
    make_factory: Callable[..., FakeFactory],
    existing_output: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"], "p2.png": ["blue"], "p3.png": ["red"]})
    factory = make_factory(fail_on_call=2, error=RuntimeError("model crashed"))
    before = existing_output.read_bytes()
    assert run([str(folder), "-o", str(existing_output)], factory) == 1
    err = capsys.readouterr().err
    assert_one_error_line(err, "RuntimeError: model crashed")
    assert "Processing page 2..." in err
    assert existing_output.read_bytes() == before
    assert temp_files(tmp_path) == []


def test_failed_rename_exits_1_and_removes_the_temp_file(
    fx: Fixtures,
    tmp_path: Path,
    factory: FakeFactory,
    existing_output: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    before = existing_output.read_bytes()

    def fail(src: object, dst: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(os, "replace", fail)
    assert run([str(folder), "-o", str(existing_output)], factory) == 1
    assert_one_error_line(capsys.readouterr().err, "No space left on device")
    assert existing_output.read_bytes() == before
    assert temp_files(tmp_path) == []


def test_ctrl_c_during_page_2_exits_130_and_leaves_the_output_untouched(
    fx: Fixtures,
    tmp_path: Path,
    make_factory: Callable[..., FakeFactory],
    existing_output: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"], "p2.png": ["blue"]})
    factory = make_factory(fail_on_call=2, error=KeyboardInterrupt())
    before = existing_output.read_bytes()
    assert run([str(folder), "-o", str(existing_output)], factory) == 130
    assert_one_error_line(capsys.readouterr().err, "interrupted")
    assert existing_output.read_bytes() == before
    assert temp_files(tmp_path) == []


def test_ctrl_c_during_the_write_removes_the_temp_file(
    fx: Fixtures,
    tmp_path: Path,
    factory: FakeFactory,
    existing_output: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    before = existing_output.read_bytes()

    def interrupt(src: object, dst: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(os, "replace", interrupt)
    assert run([str(folder), "-o", str(existing_output)], factory) == 130
    assert_one_error_line(capsys.readouterr().err, "interrupted")
    assert existing_output.read_bytes() == before
    assert temp_files(tmp_path) == []


def test_multi_line_error_prints_one_line(
    fx: Fixtures,
    make_factory: Callable[..., FakeFactory],
    capsys: pytest.CaptureFixture[str],
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    message = "line one\nline two\nline three\nline four\nline five"
    factory = make_factory(fail_on_call=1, error=ValueError(message))
    assert run([str(folder)], factory) == 1
    err = capsys.readouterr().err
    assert_one_error_line(err, "ValueError: line one line two line three line four line five")


def test_long_error_is_cut_to_300_characters(
    fx: Fixtures,
    make_factory: Callable[..., FakeFactory],
    capsys: pytest.CaptureFixture[str],
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    factory = make_factory(fail_on_call=1, error=RuntimeError("x" * 1000))
    assert run([str(folder)], factory) == 1
    [line] = error_lines(capsys.readouterr().err)
    message = line.removeprefix("scanscribe: error: ")
    assert len(message) == 300
    assert message.endswith("...")


def test_debug_env_re_raises_the_engine_error(
    fx: Fixtures,
    make_factory: Callable[..., FakeFactory],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    factory = make_factory(fail_on_call=1, error=RuntimeError("model crashed"))
    monkeypatch.setenv("SCANSCRIBE_DEBUG", "1")
    with pytest.raises(RuntimeError, match="model crashed"):
        run([str(folder)], factory)
