"""The library API: OCR an input with an engine the caller already has.

Nothing here prints or writes files, so a server can call it while stdout carries its own
protocol. The engine may still log: PaddleOCR logs to stderr.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from scanscribe.engine import OcrEngine
from scanscribe.output import format_pages
from scanscribe.pages import PageSource, open_source, split_columns

ProgressCallback = Callable[[int, int], None]
"""Called as `on_page(page_number, total_pages)` once per page, after the page is read and
before it is recognized. Raise from it to stop the run; the exception reaches the caller."""


def ocr_source(
    source: PageSource, engine: OcrEngine, on_page: ProgressCallback | None = None
) -> list[list[str]]:
    """Recognize every page of an opened source and return each page's lines, in order.

    Each page is cut into `source.columns` strips, read left to right, so the split always
    matches the width the source was checked against.
    """
    total = len(source)
    pages: list[list[str]] = []
    for number, image in enumerate(source.images(), 1):
        if on_page is not None:
            on_page(number, total)
        lines: list[str] = []
        for column in split_columns(image, source.columns):
            lines.extend(engine.recognize(column))
        pages.append(lines)
    return pages


def transcribe(
    path: Path,
    engine: OcrEngine,
    *,
    dpi: int = 200,
    columns: int = 1,
    on_page: ProgressCallback | None = None,
) -> str:
    """OCR a PDF or a folder of page images and return its page-marked text.

    The defaults match the `scanscribe` command's. Raises `UsageError` for bad arguments or a
    missing input and `InputError` for a page that can't be read, both before any OCR. The
    source is closed however the run ends.
    """
    with open_source(path, dpi, columns) as source:
        return format_pages(ocr_source(source, engine, on_page))
