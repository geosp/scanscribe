"""The import path never imports Paddle (R13, R19), and `__all__` is the public API."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import scanscribe
from scanscribe import cli

NO_PADDLE_SCRIPT = textwrap.dedent(
    """
    import sys
    import scanscribe, scanscribe.api, scanscribe.cli, scanscribe.engine, scanscribe.output
    import scanscribe.pages
    from scanscribe import *
    from scanscribe.cli import run
    from scanscribe.engine import load_engine

    code = run(["--help"], load_engine)
    unbound = [name for name in scanscribe.__all__ if name not in globals()]
    leaked = [m for m in ("paddle", "paddleocr", "scanscribe.paddle_engine") if m in sys.modules]
    print("RESULT", code, unbound, leaked, file=sys.stderr)
    """
)


def test_import_path_and_help_never_import_paddle() -> None:
    done = subprocess.run(
        [sys.executable, "-c", NO_PADDLE_SCRIPT], capture_output=True, text=True, check=True
    )
    assert "RESULT 0 [] []" in done.stderr
    assert "usage: scanscribe" in done.stdout


PUBLIC_API = [
    "EngineFactory",
    "EngineMissingError",
    "IMAGE_EXTENSIONS",
    "InputError",
    "OcrEngine",
    "PageImage",
    "PageSource",
    "ProgressCallback",
    "ScanscribeError",
    "UsageError",
    "format_pages",
    "load_engine",
    "ocr_source",
    "open_source",
    "transcribe",
]
"""The public names in the library-api plan's D2. Changing this list changes the semver API."""


def test_all_is_exactly_the_public_api() -> None:
    assert sorted(scanscribe.__all__) == sorted(PUBLIC_API)
    assert len(set(scanscribe.__all__)) == len(scanscribe.__all__)


def test_main_exits_with_runs_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["scanscribe", "--help"])
    with pytest.raises(SystemExit) as caught:
        cli.main()
    assert caught.value.code == 0


CONFTEST = Path(__file__).with_name("conftest.py")


@pytest.mark.parametrize(("leak", "expected"), [(True, 1), (False, 0)])
def test_session_check_fails_a_run_that_imported_paddle(
    pytester: pytest.Pytester, leak: bool, expected: int
) -> None:
    pytester.makeconftest(CONFTEST.read_text(encoding="utf-8"))
    body = 'sys.modules["paddle"] = types.ModuleType("paddle")' if leak else "pass"
    pytester.makepyfile(
        f"""
        import sys, types

        def test_it():
            {body}
        """
    )
    result = pytester.runpytest_subprocess()
    assert result.ret == expected
    assert ("R13: the test run imported the real paddle" in result.stdout.str()) is leak
