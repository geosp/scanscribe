"""Page sources: the ordered, pre-checked pages of a folder of images or a PDF."""

from __future__ import annotations

import re
from pathlib import Path

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


def list_image_files(folder: Path) -> list[Path]:
    """The folder's page images in natural order (R1).

    Pages are regular files directly inside the folder, not hidden, with a supported extension in
    any case.
    """
    pages = [
        path
        for path in folder.iterdir()
        if not path.name.startswith(".")
        and path.suffix.lower() in IMAGE_EXTENSIONS
        and path.is_file()
    ]
    return sorted(pages, key=lambda path: natural_key(path.name))
