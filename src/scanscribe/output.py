"""The output text and where it goes."""

from __future__ import annotations

import contextlib
import os
import stat
import tempfile
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


def _umask_default_mode() -> int:
    umask = os.umask(0)
    os.umask(umask)
    return 0o666 & ~umask


def write_atomic(path: Path, text: str) -> None:
    """Replace `path` with `text` in UTF-8, or leave it untouched if anything fails (D6).

    The text goes to a temp file `.<name>.<random>.tmp` in the same directory, which gets the old
    file's mode (or the umask default) and is renamed onto `path` with `os.replace`. Any failure,
    including Ctrl-C, deletes the temp file.
    """
    try:
        mode = stat.S_IMODE(os.stat(path).st_mode)
    except FileNotFoundError:
        mode = _umask_default_mode()
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as temp:
            temp.write(text.encode("utf-8"))
            temp.flush()
            os.fsync(temp.fileno())
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)
        raise
