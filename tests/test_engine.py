"""Loading the engine (D2, R14, R16)."""

from __future__ import annotations

import pytest
from conftest import FakePaddle, Fixtures

from scanscribe import engine
from scanscribe.cli import run
from scanscribe.engine import EngineMissingError, load_engine


def test_missing_engine_names_both_install_commands(no_paddle: None) -> None:
    with pytest.raises(EngineMissingError) as caught:
        load_engine("en", None)
    assert "uv sync --extra gpu" in str(caught.value)
    assert "uv sync --extra cpu" in str(caught.value)


def test_missing_engine_exits_1_without_output(
    no_paddle: None, fx: Fixtures, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]})
    assert run([str(folder)], load_engine) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "uv sync --extra gpu" in captured.err
    assert "Traceback" not in captured.err
    assert not folder.with_name("book.txt").exists()


def test_device_line_comes_before_the_first_page(
    fake_paddle: FakePaddle, fx: Fixtures, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"], "p2.png": ["blue"]})
    assert run([str(folder)], load_engine) == 0
    err = capsys.readouterr().err.splitlines()
    assert err[:3] == ["Using device: gpu:0", "Processing page 1...", "Processing page 2..."]
    assert folder.with_name("book.txt").read_text(encoding="utf-8") == (
        "--- Page 1 ---\nfake line\n\n--- Page 2 ---\nfake line"
    )


def test_device_is_printed_before_the_engine_is_built(
    fake_paddle: FakePaddle, capsys: pytest.CaptureFixture[str]
) -> None:
    fake_paddle.chatter = True  # the fake prints "Creating model" while it is built
    load_engine("en", "cpu")
    err = capsys.readouterr().err
    assert err.index("Using device: cpu") < err.index("Creating model: fake")


def test_a_broken_paddle_install_is_not_reported_as_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(name: str) -> object:
        raise ModuleNotFoundError("No module named 'paddle.base.core'", name="paddle.base.core")

    monkeypatch.setattr(engine.importlib, "import_module", broken)
    with pytest.raises(ModuleNotFoundError) as caught:
        load_engine("en", None)
    assert not isinstance(caught.value, EngineMissingError)
