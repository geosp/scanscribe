"""The library API: argument checks, the page loop, progress and cancelling (library-api plan)."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import FakeEngine, FakeFactory, FakePaddle, Fixtures

from scanscribe import pages
from scanscribe.api import ocr_source, transcribe
from scanscribe.cli import run
from scanscribe.engine import PageImage, UsageError, load_engine
from scanscribe.pages import open_source

# --- Argument and path checks in open_source (R5, R6, D4) ----------------------------------


@pytest.mark.parametrize(("dpi", "columns"), [(200, 0), (200, -1), (0, 1), (-72, 1)])
def test_columns_or_dpi_below_1_is_a_usage_error(fx: Fixtures, dpi: int, columns: int) -> None:
    pdf = fx.red_pdf()
    with pytest.raises(UsageError, match="at least 1"):
        open_source(pdf, dpi=dpi, columns=columns)


def test_columns_below_1_is_a_usage_error_for_a_folder(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    with pytest.raises(UsageError, match="columns must be at least 1, got 0"):
        open_source(folder, dpi=200, columns=0)


def test_missing_input_is_a_usage_error_naming_it(tmp_path: Path) -> None:
    missing = tmp_path / "nope.pdf"
    with pytest.raises(UsageError, match="input not found") as caught:
        open_source(missing, dpi=200, columns=1)
    assert str(missing) in str(caught.value)


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


def test_input_in_an_unreadable_directory_is_a_usage_error(locked_dir: Path) -> None:
    with pytest.raises(UsageError) as caught:
        open_source(locked_dir / "book.pdf", dpi=200, columns=1)
    assert "book.pdf" in str(caught.value)


def test_a_folder_that_cannot_be_listed_is_a_usage_error(locked_dir: Path) -> None:
    with pytest.raises(UsageError, match="cannot list") as caught:
        open_source(locked_dir, dpi=200, columns=1)
    assert str(locked_dir) in str(caught.value)


def test_a_str_path_is_accepted(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    assert transcribe(str(folder), FakeEngine()) == "--- Page 1 ---\nred"
    with pytest.raises(UsageError, match="input not found"):
        open_source(str(folder / "nope.pdf"), dpi=200, columns=1)


def test_source_keeps_the_columns_it_was_opened_with(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red", "blue"]})
    with open_source(folder, dpi=200, columns=2) as source:
        assert source.columns == 2
    with open_source(fx.red_pdf(), dpi=200, columns=3) as source:
        assert source.columns == 3


# --- The page loop: ocr_source and transcribe (R2, R3, R4, R7, D1) --------------------------


class Stop(Exception):
    """Raised from a progress callback to cancel a run."""


def test_progress_comes_before_each_page_is_recognized(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"], "p2.png": ["green"], "p3.png": ["blue"]})
    engine = FakeEngine()
    events: list[object] = []
    original = engine.recognize

    def recognize(image: PageImage) -> list[str]:
        lines = original(image)
        events.append(("recognize", lines[0]))
        return lines

    engine.recognize = recognize  # type: ignore[method-assign]
    with open_source(folder, dpi=200, columns=1) as source:
        pages = ocr_source(source, engine, on_page=lambda n, total: events.append((n, total)))
    assert pages == [["red"], ["green"], ["blue"]]
    assert events == [
        (1, 3),
        ("recognize", "red"),
        (2, 3),
        ("recognize", "green"),
        (3, 3),
        ("recognize", "blue"),
    ]


def test_progress_comes_before_the_first_strip_of_each_pdf_page(fx: Fixtures) -> None:
    pdf = fx.pdf("book.pdf", [["red", "blue"], ["green", "yellow"]], width=144)
    engine = FakeEngine()
    events: list[object] = []
    original = engine.recognize

    def recognize(image: PageImage) -> list[str]:
        lines = original(image)
        events.append(lines[0])
        return lines

    engine.recognize = recognize  # type: ignore[method-assign]
    with open_source(pdf, dpi=144, columns=2) as source:
        ocr_source(source, engine, on_page=lambda n, total: events.append((n, total)))
    assert events == [(1, 2), "red", "blue", (2, 2), "green", "yellow"]


def test_an_exception_from_on_page_stops_the_run_unchanged(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"], "p2.png": ["green"], "p3.png": ["blue"]})
    engine = FakeEngine()
    stop = Stop("cancelled")

    def on_page(number: int, total: int) -> None:
        if number == 2:
            raise stop

    with open_source(folder, dpi=200, columns=1) as source, pytest.raises(Stop) as caught:
        ocr_source(source, engine, on_page=on_page)
    assert caught.value is stop
    assert len(engine.shapes) == 1


def test_transcribe_closes_the_source_when_on_page_raises(
    fx: Fixtures, monkeypatch: pytest.MonkeyPatch
) -> None:
    closed: list[bool] = []
    original_close = pages.PdfSource.close

    def close(self: pages.PdfSource) -> None:
        closed.append(True)
        original_close(self)

    monkeypatch.setattr(pages.PdfSource, "close", close)

    def on_page(number: int, total: int) -> None:
        raise Stop

    with pytest.raises(Stop):
        transcribe(fx.pdf("book.pdf", [["red"], ["blue"]]), FakeEngine(), on_page=on_page)
    assert closed


def test_pages_are_split_with_the_sources_columns(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red", "blue"], "p2.png": ["green", "yellow"]})
    engine = FakeEngine()
    with open_source(folder, dpi=200, columns=2) as source:
        assert ocr_source(source, engine) == [["red", "blue"], ["green", "yellow"]]
    assert len(engine.shapes) == 4


def test_transcribe_rejects_bad_columns_before_the_engine_runs(fx: Fixtures) -> None:
    engine = FakeEngine()
    with pytest.raises(UsageError):
        transcribe(fx.red_pdf(), engine, columns=0)
    assert engine.shapes == []


def test_transcribe_rejects_a_missing_input_naming_it(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    with pytest.raises(UsageError, match="input not found") as caught:
        transcribe(missing, FakeEngine())
    assert str(missing) in str(caught.value)


def test_transcribe_prints_nothing_and_writes_no_file(
    fx: Fixtures, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"], "p2.png": ["blue"]})
    pdf = fx.pdf("book.pdf", [["green"]])
    before = sorted(tmp_path.rglob("*"))
    assert transcribe(folder, FakeEngine()) == "--- Page 1 ---\nred\n\n--- Page 2 ---\nblue"
    assert transcribe(pdf, FakeEngine()) == "--- Page 1 ---\ngreen"
    assert sorted(tmp_path.rglob("*")) == before
    captured = capfd.readouterr()
    assert captured.out == ""
    assert captured.err == ""


# --- load_engine's device callback (R8) ----------------------------------------------------


def test_on_device_gets_the_device_before_the_engine_is_built(
    fake_paddle: FakePaddle, capsys: pytest.CaptureFixture[str]
) -> None:
    fake_paddle.gpus = 0
    seen: list[tuple[str, int]] = []
    load_engine(
        "en", None, on_device=lambda device: seen.append((device, len(fake_paddle.created)))
    )
    assert seen == [("cpu", 0)]
    assert len(fake_paddle.created) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_without_on_device_the_device_is_printed_to_stderr(
    fake_paddle: FakePaddle, capsys: pytest.CaptureFixture[str]
) -> None:
    load_engine("en", None)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.splitlines() == ["Using device: gpu:0"]


# --- transcribe matches the CLI (R1) -------------------------------------------------------


def cli_output(argv: list[str], output: Path) -> str:
    assert run([*argv, "-o", str(output)], FakeFactory()) == 0
    return output.read_text(encoding="utf-8")


def test_transcribe_on_a_folder_matches_the_cli(fx: Fixtures, tmp_path: Path) -> None:
    folder = fx.image_folder("book", {"p10.png": ["blue"], "p2.jpg": ["green"], "p1.png": ["red"]})
    expected = cli_output([str(folder)], tmp_path / "cli.txt")
    assert transcribe(folder, FakeEngine()) == expected


def test_transcribe_on_a_two_column_pdf_matches_the_cli(fx: Fixtures, tmp_path: Path) -> None:
    pdf = fx.pdf("book.pdf", [["red", "blue"], ["green", "yellow"]], width=144)
    expected = cli_output([str(pdf), "--columns", "2", "--dpi", "144"], tmp_path / "cli.txt")
    assert expected == "--- Page 1 ---\nred\nblue\n\n--- Page 2 ---\ngreen\nyellow"
    assert transcribe(pdf, FakeEngine(), dpi=144, columns=2) == expected


def test_transcribe_defaults_render_pdfs_like_the_cli(fx: Fixtures, tmp_path: Path) -> None:
    pdf = fx.red_pdf()
    factory = FakeFactory()
    assert run([str(pdf), "-o", str(tmp_path / "cli.txt")], factory) == 0
    engine = FakeEngine()
    assert transcribe(pdf, engine) == (tmp_path / "cli.txt").read_text(encoding="utf-8")
    assert engine.shapes == factory.engine.shapes == [(200, 200, 3)]
