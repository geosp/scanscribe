"""Page sources: listing, pre-checks, rendering and the column split (R1, R2, R4, R5, R7, R8)."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import Fixtures

from scanscribe.pages import list_image_files, natural_key

# --- Folder listing (R1) -------------------------------------------------------------------


def names(folder: Path) -> list[str]:
    return [path.name for path in list_image_files(folder)]


def test_digit_runs_sort_as_numbers_and_case_is_ignored(fx: Fixtures) -> None:
    folder = fx.image_folder(
        "book", {"Page10.png": ["red"], "page2.png": ["red"], "page1.PNG": ["red"]}
    )
    assert names(folder) == ["page1.PNG", "page2.png", "Page10.png"]


def test_upper_case_extensions_are_pages(fx: Fixtures) -> None:
    folder = fx.image_folder(
        "book",
        {
            "a.JPG": ["red"],
            "b.Jpeg": ["red"],
            "c.TIF": ["red"],
            "d.WEBP": ["red"],
            "e.BMP": ["red"],
        },
    )
    assert names(folder) == ["a.JPG", "b.Jpeg", "c.TIF", "d.WEBP", "e.BMP"]


def test_subfolders_other_files_and_dotfiles_are_not_pages(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"], "._page1.jpg": ["red"]})
    (folder / "x.png").mkdir()
    (folder / "notes.txt").write_text("notes", encoding="utf-8")
    assert names(folder) == ["p1.png"]


def test_exact_name_breaks_ties(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"a.png": ["red"], "A.png": ["red"]})
    if len(list(folder.iterdir())) < 2:
        pytest.skip("case-insensitive file system")
    assert names(folder) == ["A.png", "a.png"]


def test_natural_key_orders_numbers_before_text_without_type_errors() -> None:
    files = ["b.png", "10.png", "a2.png", "2.png", "a10.png", "A2.png"]
    assert sorted(files, key=natural_key) == [
        "2.png",
        "10.png",
        "A2.png",
        "a2.png",
        "a10.png",
        "b.png",
    ]
