"""Output format, default output path and the atomic write (R3, R6, D6)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest

from scanscribe.output import default_output_path, format_pages, write_atomic

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


# --- Atomic write (D6, R12, R20) -----------------------------------------------------------


def temp_files(directory: Path) -> list[str]:
    return [p.name for p in directory.iterdir() if p.name.endswith(".tmp")]


def test_interrupt_right_after_the_temp_file_is_created_removes_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "out.txt"
    output.write_text("old", encoding="utf-8")
    real_open = os.open

    def open_then_interrupt(path: Any, flags: int, mode: int = 0o777, **kw: Any) -> int:
        fd = real_open(path, flags, mode, **kw)
        if str(path).endswith(".tmp"):
            os.close(fd)
            raise KeyboardInterrupt
        return fd

    monkeypatch.setattr(os, "open", open_then_interrupt)
    with pytest.raises(KeyboardInterrupt):
        write_atomic(output, "new")
    assert temp_files(tmp_path) == []
    assert output.read_text(encoding="utf-8") == "old"


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_new_file_gets_the_umask_default_without_changing_the_umask(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old_umask = os.umask(0o027)
    try:

        def no_umask(mask: int) -> int:
            raise AssertionError("write_atomic must not change the process umask")

        monkeypatch.setattr(os, "umask", no_umask)
        write_atomic(tmp_path / "out.txt", "text")
    finally:
        monkeypatch.undo()
        os.umask(old_umask)
    assert (tmp_path / "out.txt").stat().st_mode & 0o777 == 0o640


def test_failed_cleanup_keeps_the_original_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_replace(src: object, dst: object) -> None:
        raise OSError(28, "No space left on device")

    def fail_unlink(path: object) -> None:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(os, "replace", fail_replace)
    monkeypatch.setattr(os, "unlink", fail_unlink)
    with pytest.raises(OSError, match="No space left on device"):
        write_atomic(tmp_path / "out.txt", "text")
