"""Page sources: listing, pre-checks, rendering and the column split (R1, R2, R4, R5, R7, R8)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from conftest import Fixtures, nearest_color, page_image

from scanscribe import pages
from scanscribe.engine import InputError
from scanscribe.pages import (
    ImageFolderSource,
    PdfSource,
    list_image_files,
    natural_key,
    open_source,
    split_columns,
)

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


# --- Page sources (R2, R5, R7, R8, D4, D6, D8) -------------------------------------------


@pytest.mark.parametrize("mode", ["RGBA", "L", "P"])
def test_images_in_other_modes_are_yielded_as_rgb(fx: Fixtures, tmp_path: Path, mode: str) -> None:
    folder = tmp_path / "book"
    folder.mkdir()
    page_image(["white", "black"], mode=mode).save(folder / "p1.png")
    with open_source(folder, dpi=200, columns=1) as source:
        [image] = list(source.images())
    assert image.shape == (40, 60, 3)
    assert image.dtype.name == "uint8"
    assert nearest_color(image[20, 10]) == "white"
    assert nearest_color(image[20, 50]) == "black"


def test_folder_source_labels_pages_by_file_name(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"p2.png": ["red"], "p1.png": ["blue"]})
    with open_source(folder, dpi=200, columns=1) as source:
        assert isinstance(source, ImageFolderSource)
        assert source.labels == ["p1.png", "p2.png"]
        assert len(source) == 2
        colors = [nearest_color(image[0, 0]) for image in source.images()]
    assert colors == ["blue", "red"]


def test_pdf_pages_render_at_the_requested_dpi(fx: Fixtures) -> None:
    path = fx.pdf("book.pdf", [["red"], ["blue"]])
    with open_source(path, dpi=144, columns=1) as source:
        assert isinstance(source, PdfSource)
        assert source.labels == ["page 1", "page 2"]
        images = list(source.images())
    assert [image.shape for image in images] == [(144, 144, 3), (144, 144, 3)]


def test_pdf_pages_are_rgb_not_bgr(fx: Fixtures) -> None:
    with open_source(fx.red_pdf(), dpi=72, columns=1) as source:
        [image] = list(source.images())
    height, width = image.shape[:2]
    assert nearest_color(image[height // 2, width // 2]) == "red"


def test_empty_folder_is_an_input_error(tmp_path: Path) -> None:
    folder = tmp_path / "empty"
    folder.mkdir()
    with pytest.raises(InputError, match="no page images found") as caught:
        open_source(folder, dpi=200, columns=1)
    assert str(folder) in str(caught.value)


@pytest.mark.parametrize("builder", ["zero_page_pdf", "notes_dat"])
def test_unopenable_pdf_is_an_input_error_naming_it(fx: Fixtures, builder: str) -> None:
    path = getattr(fx, builder)()
    with pytest.raises(InputError) as caught:
        open_source(path, dpi=200, columns=1)
    assert str(path) in str(caught.value)


def test_pdf_with_no_pages_is_an_input_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    closed = []

    class EmptyDocument:
        def __len__(self) -> int:
            return 0

        def close(self) -> None:
            closed.append(True)

    monkeypatch.setattr(pages, "_open_pdf", lambda path: EmptyDocument())
    path = tmp_path / "empty.pdf"
    path.touch()  # open_source rejects a missing path before it opens the PDF (library-api D4)
    with pytest.raises(InputError, match="has no pages") as caught:
        open_source(path, dpi=200, columns=1)
    assert str(path) in str(caught.value)
    assert closed == [True]


@pytest.mark.parametrize("builder", ["corrupt_image", "truncated_png", "truncated_jpeg"])
def test_unreadable_image_is_an_input_error_naming_it(fx: Fixtures, builder: str) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"], "p2.png": ["blue"]})
    bad = getattr(fx, builder)(folder, name="p3" + (".jpg" if "jpeg" in builder else ".png"))
    with pytest.raises(InputError) as caught:
        open_source(folder, dpi=200, columns=1)
    assert str(bad) in str(caught.value)


def test_image_narrower_than_columns_is_an_input_error(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]}, width=3)
    with pytest.raises(InputError, match="narrower than --columns 4") as caught:
        open_source(folder, dpi=200, columns=4)
    assert "p1.png" in str(caught.value)


def test_image_as_wide_as_columns_is_accepted(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"]}, width=4)
    with open_source(folder, dpi=200, columns=4) as source:
        assert len(source) == 1


def test_pdf_page_narrower_than_columns_at_the_dpi_is_an_input_error(fx: Fixtures) -> None:
    path = fx.pdf("narrow.pdf", [["red"], ["red"]], width=2, height=72)
    with pytest.raises(InputError, match="page 1 is 2 px wide") as caught:
        open_source(path, dpi=72, columns=3)
    assert str(path) in str(caught.value)
    with open_source(path, dpi=144, columns=3) as source:  # 4 px at 144 DPI
        assert len(source) == 2


@pytest.mark.skipif(sys.platform == "win32", reason="RLIMIT_NOFILE is POSIX only")
def test_many_images_do_not_exhaust_file_handles(fx: Fixtures) -> None:
    import resource

    folder = fx.image_folder(
        "book", {f"p{n}.png": ["red"] for n in range(1, 201)}, width=4, height=4
    )
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, hard))
    try:
        with open_source(folder, dpi=200, columns=1) as source:
            count = sum(1 for _ in source.images())
    finally:
        resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
    assert count == 200


# --- Column split (R4) ---------------------------------------------------------------------


def test_three_columns_of_100_px_are_33_34_33() -> None:
    image = np.zeros((10, 100, 3), dtype=np.uint8)
    assert [s.shape[1] for s in split_columns(image, 3)] == [33, 34, 33]


def test_one_column_returns_the_image_unchanged() -> None:
    image = np.zeros((10, 7, 3), dtype=np.uint8)
    [only] = split_columns(image, 1)
    assert only is image


def test_slices_run_left_to_right_and_cover_the_page() -> None:
    image = np.asarray(page_image(["red", "green", "blue"], width=10))
    slices = split_columns(image, 3)
    assert [nearest_color(s[0, 0]) for s in slices] == ["red", "green", "blue"]
    assert sum(s.shape[1] for s in slices) == 10


def test_halves_round_to_even() -> None:
    # 5 px in 2 columns: the edge 2.5 rounds to 2.
    image = np.zeros((1, 5, 3), dtype=np.uint8)
    assert [s.shape[1] for s in split_columns(image, 2)] == [2, 3]
