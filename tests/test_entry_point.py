"""The command and its import path never import Paddle (R13, R19)."""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from scanscribe import cli

NO_PADDLE_SCRIPT = textwrap.dedent(
    """
    import sys
    import scanscribe, scanscribe.cli, scanscribe.engine, scanscribe.output, scanscribe.pages
    from scanscribe.cli import run
    from scanscribe.engine import load_engine

    code = run(["--help"], load_engine)
    leaked = [m for m in ("paddle", "paddleocr", "scanscribe.paddle_engine") if m in sys.modules]
    print("RESULT", code, leaked, file=sys.stderr)
    """
)


def test_import_path_and_help_never_import_paddle() -> None:
    done = subprocess.run(
        [sys.executable, "-c", NO_PADDLE_SCRIPT], capture_output=True, text=True, check=True
    )
    assert "RESULT 0 []" in done.stderr
    assert "usage: scanscribe" in done.stdout


def test_main_exits_with_runs_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["scanscribe", "--help"])
    with pytest.raises(SystemExit) as caught:
        cli.main()
    assert caught.value.code == 0
