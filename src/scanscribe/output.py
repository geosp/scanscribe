"""The output text and where it goes."""

from __future__ import annotations

from pathlib import Path


def format_pages(pages: list[list[str]]) -> str:
    """Join pages in the prototype's format (R3).

    Each page is `--- Page N ---` and a newline, then its lines joined by newlines; pages are
    joined by one blank line.
    """
    return "\n\n".join(
        f"--- Page {number} ---\n" + "\n".join(lines) for number, lines in enumerate(pages, 1)
    )


def default_output_path(input_path: Path) -> Path:
    """The output used when `-o` isn't given (R6, D5).

    A folder's output is the sibling `<folder name>.txt`, keeping any dots in the name; a file's
    output is the file with its suffix replaced by `.txt`.
    """
    resolved = input_path.resolve()
    if resolved.is_dir():
        return resolved.parent / (resolved.name + ".txt")
    return input_path.with_suffix(".txt")
