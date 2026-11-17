"""The output text and where it goes."""

from __future__ import annotations

import contextlib
import os
import secrets
import stat
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


_TEMP_ATTEMPTS = 100


def write_atomic(path: Path, text: str) -> None:
    """Replace `path` with `text` in UTF-8, or leave it untouched if anything fails (D6).

    The text goes to a temp file `.<name>.<random>.tmp` in the same directory, which gets the old
    file's mode (or the umask default) and is renamed onto `path` with `os.replace`. Any failure,
    including Ctrl-C, deletes the temp file; a failed delete never hides the original error.
    """
    try:
        old_mode: int | None = stat.S_IMODE(os.stat(path).st_mode)
    except FileNotFoundError:
        old_mode = None
    # O_EXCL with mode 0666 lets the kernel apply the umask, so the process umask never changes.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    temp_name: Path | None = None
    try:
        for _ in range(_TEMP_ATTEMPTS):
            # Named before it is created, so a Ctrl-C right after creation still removes it.
            temp_name = path.parent / f".{path.name}.{secrets.token_hex(4)}.tmp"
            try:
                fd = os.open(temp_name, flags, 0o666)
                break
            except FileExistsError:
                temp_name = None
        else:
            raise FileExistsError(f"no free temp file name next to {path}")
        with os.fdopen(fd, "wb") as temp:
            temp.write(text.encode("utf-8"))
            temp.flush()
            os.fsync(temp.fileno())
        if old_mode is not None:
            os.chmod(temp_name, old_mode)
        os.replace(temp_name, path)
    except BaseException:
        if temp_name is not None:
            with contextlib.suppress(OSError):
                os.unlink(temp_name)
        raise
