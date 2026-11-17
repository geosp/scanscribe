"""Page sources: the ordered, pre-checked pages of a folder of images or a PDF."""

from __future__ import annotations

import math
import re
from collections.abc import Iterator
from itertools import pairwise
from pathlib import Path
from types import TracebackType

import numpy as np
import pypdfium2 as pdfium
from PIL import Image

from scanscribe.engine import InputError, PageImage

IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"})

_DIGITS = re.compile(r"(\d+)")


def natural_key(name: str) -> tuple[tuple[tuple[int, int | str], ...], str]:
    """Sort key: text parts case-folded, digit runs as numbers, the exact name as tiebreaker (R1).

    Each part is tagged so text and numbers never compare with each other.
    """
    parts: list[tuple[int, int | str]] = []
    for i, part in enumerate(_DIGITS.split(name)):
        if i % 2:
            parts.append((0, int(part)))
        elif part:
            parts.append((1, part.casefold()))
    return tuple(parts), name


def is_page_name(name: str) -> bool:
    """Whether a file with this name in a folder input is a page: not hidden, and a supported
    image extension in any case (R1)."""
    return not name.startswith(".") and Path(name).suffix.lower() in IMAGE_EXTENSIONS


def list_image_files(folder: Path) -> list[Path]:
    """The folder's page images in natural order (R1).

    Pages are regular files directly inside the folder, not hidden, with a supported extension in
    any case.
    """
    pages = [path for path in folder.iterdir() if is_page_name(path.name) and path.is_file()]
    return sorted(pages, key=lambda path: natural_key(path.name))


class PageSource:
    """The pre-checked pages of one input. Use it as a context manager.

    Creating a source checks every page before any OCR (D6): each one must be readable and at
    least `columns` pixels wide (R5, R7, R8). `images()` then yields the pages as RGB arrays (D4).
    """

    path: Path
    labels: list[str]
    """Each page's name for messages: the file name, or `page N` in a PDF."""

    def __len__(self) -> int:
        return len(self.labels)

    def images(self) -> Iterator[PageImage]:
        raise NotImplementedError

    def close(self) -> None:
        """Release anything the source holds open."""

    def __enter__(self) -> PageSource:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def _check_width(label: str, width: int, columns: int) -> None:
    if width < columns:
        raise InputError(f"{label} is {width} px wide, narrower than --columns {columns}")


class ImageFolderSource(PageSource):
    """A folder of page images. Each image is opened only while it is read."""

    def __init__(self, folder: Path, columns: int) -> None:
        self.path = folder
        self.files = list_image_files(folder)
        if not self.files:
            raise InputError(f"no page images found in {folder}")
        self.labels = [path.name for path in self.files]
        for path in self.files:
            _check_width(str(path), self._decoded_width(path), columns)

    @staticmethod
    def _decoded_width(path: Path) -> int:
        # `load()` decodes the whole image; `verify()` misses truncated JPEGs (notes.md#d6).
        try:
            with Image.open(path) as image:
                image.load()
                return int(image.width)
        except Exception as exc:
            raise InputError(f"cannot read page image {path}: {exc}") from exc

    def images(self) -> Iterator[PageImage]:
        for path in self.files:
            try:
                with Image.open(path) as image:
                    array = np.array(image.convert("RGB"), dtype=np.uint8)
            except Exception as exc:
                raise InputError(f"cannot read page image {path}: {exc}") from exc
            yield array


def _open_pdf(path: Path) -> pdfium.PdfDocument:
    return pdfium.PdfDocument(path)


class PdfSource(PageSource):
    """A PDF rendered at `dpi`. The document stays open until `close()`."""

    def __init__(self, path: Path, dpi: int, columns: int) -> None:
        self.path = path
        self.scale = dpi / 72
        try:
            self.document = _open_pdf(path)
        except Exception as exc:
            raise InputError(f"cannot open {path} as a PDF: {exc}") from exc
        try:
            count = len(self.document)
            if count == 0:
                raise InputError(f"{path} has no pages")
            self.labels = [f"page {n}" for n in range(1, count + 1)]
            for index, label in enumerate(self.labels):
                _check_width(f"{path} {label}", self._rendered_width(index, label), columns)
        except BaseException:
            self.close()
            raise

    def _rendered_width(self, index: int, label: str) -> int:
        # The width `render()` will produce: ceil(width × scale), as pypdfium2 computes it.
        try:
            page = self.document[index]
            try:
                return int(math.ceil(page.get_width() * self.scale))
            finally:
                page.close()
        except Exception as exc:
            raise InputError(f"cannot read {self.path} {label}: {exc}") from exc

    def images(self) -> Iterator[PageImage]:
        for index, label in enumerate(self.labels):
            try:
                page = self.document[index]
                try:
                    bitmap = page.render(scale=self.scale)
                    try:
                        # to_pil() gives true RGB; the raw buffer is BGR (D4).
                        array = np.array(bitmap.to_pil().convert("RGB"), dtype=np.uint8)
                    finally:
                        bitmap.close()
                finally:
                    page.close()
            except Exception as exc:
                raise InputError(f"cannot render {self.path} {label}: {exc}") from exc
            yield array

    def close(self) -> None:
        document = getattr(self, "document", None)
        if document is not None:
            document.close()
            self.document = None


def open_source(path: Path, dpi: int, columns: int) -> PageSource:
    """Open and pre-check an input: a folder of images, or any file as a PDF (R2)."""
    if path.is_dir():
        return ImageFolderSource(path, columns)
    return PdfSource(path, dpi, columns)


def split_columns(image: PageImage, n: int) -> list[PageImage]:
    """Cut a page into n vertical slices, left to right, with edges at round(i × width / n) (R4).

    Python's round() sends halves to even, as the prototype did. With n = 1 the page is returned
    unchanged.
    """
    if n <= 1:
        return [image]
    width = image.shape[1]
    edges = [round(i * width / n) for i in range(n + 1)]
    return [image[:, left:right] for left, right in pairwise(edges)]
