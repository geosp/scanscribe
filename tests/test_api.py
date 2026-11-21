"""The library API: argument checks, the page loop, progress and cancelling (library-api plan)."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import Fixtures

from scanscribe.engine import UsageError
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


def test_source_keeps_the_columns_it_was_opened_with(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red", "blue"]})
    with open_source(folder, dpi=200, columns=2) as source:
        assert source.columns == 2
    with open_source(fx.red_pdf(), dpi=200, columns=3) as source:
        assert source.columns == 3
