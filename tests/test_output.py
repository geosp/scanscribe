"""Output format and default output path (R3, R6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scanscribe.output import default_output_path, format_pages

# --- Format (R3) -------------------------------------------------------------------------


def test_format_matches_the_prototype() -> None:
    assert format_pages([["a", "b"], []]) == "--- Page 1 ---\na\nb\n\n--- Page 2 ---\n"


def test_single_page() -> None:
    assert format_pages([["only line"]]) == "--- Page 1 ---\nonly line"


def test_empty_last_page() -> None:
    assert format_pages([["a"], ["b"], []]) == (
        "--- Page 1 ---\na\n\n--- Page 2 ---\nb\n\n--- Page 3 ---\n"
    )


# --- Default output path (R6, D5) ----------------------------------------------------------


def test_pdf_output_replaces_only_the_last_suffix(tmp_path: Path) -> None:
    pdf = tmp_path / "scans" / "book.v2.pdf"
    pdf.parent.mkdir()
    pdf.write_bytes(b"%PDF")
    assert default_output_path(pdf) == tmp_path / "scans" / "book.v2.txt"


def test_folder_output_keeps_dots_in_the_folder_name(tmp_path: Path) -> None:
    folder = tmp_path / "scans" / "Vol.2"
    folder.mkdir(parents=True)
    assert default_output_path(folder) == (tmp_path / "scans" / "Vol.2.txt").resolve()


def test_dot_inside_a_folder_names_that_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = tmp_path / "scans" / "ch1"
    folder.mkdir(parents=True)
    monkeypatch.chdir(folder)
    assert default_output_path(Path(".")) == (tmp_path / "scans" / "ch1.txt").resolve()


def test_trailing_slash_is_ignored(tmp_path: Path) -> None:
    folder = tmp_path / "scans" / "Vol.2"
    folder.mkdir(parents=True)
    assert default_output_path(Path(f"{folder}/")) == (tmp_path / "scans" / "Vol.2.txt").resolve()
