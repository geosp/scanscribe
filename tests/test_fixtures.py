"""Smoke tests for the generated fixtures and the fake engine (D9)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
import pytest
from conftest import FakeEngine, Fixtures, nearest_color
from PIL import Image


def test_image_folder_writes_each_page(fx: Fixtures) -> None:
    folder = fx.image_folder("book", {"p1.png": ["red"], "p2.jpg": ["green", "blue"]})
    assert sorted(p.name for p in folder.iterdir()) == ["p1.png", "p2.jpg"]
    with Image.open(folder / "p2.jpg") as image:
        image.load()
        array = np.asarray(image.convert("RGB"))
    assert nearest_color(array[20, 10]) == "green"
    assert nearest_color(array[20, 50]) == "blue"


def test_pdf_has_one_page_per_entry_at_72_dpi(fx: Fixtures) -> None:
    path = fx.pdf("two.pdf", [["red"], ["blue"]])
    document = pdfium.PdfDocument(path)
    try:
        assert len(document) == 2
        assert document[0].get_size() == pytest.approx((72, 72))
    finally:
        document.close()


def test_red_pdf_opens(fx: Fixtures) -> None:
    document = pdfium.PdfDocument(fx.red_pdf())
    try:
        assert len(document) == 1
    finally:
        document.close()


def test_zero_page_pdf_is_refused_by_pdfium(fx: Fixtures) -> None:
    # notes.md#d8: pypdfium2 won't open a zero-page PDF.
    with pytest.raises(pdfium.PdfiumError):
        pdfium.PdfDocument(fx.zero_page_pdf())


def test_notes_dat_is_not_a_pdf(fx: Fixtures) -> None:
    with pytest.raises(pdfium.PdfiumError):
        pdfium.PdfDocument(fx.notes_dat())


def test_corrupt_image_is_refused_on_open(fx: Fixtures, tmp_path: Path) -> None:
    with pytest.raises(OSError):
        Image.open(fx.corrupt_image(tmp_path))


@pytest.mark.parametrize("builder", ["truncated_png", "truncated_jpeg"])
def test_truncated_images_open_but_fail_to_load(fx: Fixtures, tmp_path: Path, builder: str) -> None:
    path = getattr(fx, builder)(tmp_path)
    with Image.open(path) as image, pytest.raises(OSError):
        image.load()


def test_fake_engine_names_the_center_color_and_can_fail() -> None:
    engine = FakeEngine(fail_on_call=2, error=ValueError("boom"))
    red = np.zeros((4, 4, 3), dtype=np.uint8)
    red[..., 0] = 254  # JPEG-shifted red still reads as red
    assert engine.recognize(red) == ["red"]
    with pytest.raises(ValueError, match="boom"):
        engine.recognize(red)
    assert engine.shapes == [(4, 4, 3), (4, 4, 3)]
