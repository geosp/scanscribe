"""The scanscribe command line: arguments, path checks and the run itself."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from scanscribe.engine import EngineFactory, ScanscribeError, UsageError, load_engine
from scanscribe.output import default_output_path, format_pages, write_atomic
from scanscribe.pages import is_page_name, open_source, split_columns


def _at_least_one(value: str) -> int:
    """argparse type for `--columns` and `--dpi`: an integer of at least 1 (R9)."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid int value: {value!r}") from None
    if number < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {number}")
    return number


def build_parser() -> argparse.ArgumentParser:
    """The parser with the prototype's options and defaults (R19)."""
    parser = argparse.ArgumentParser(
        prog="scanscribe",
        description=(
            "OCR a scanned PDF or a folder of page images into page-marked plain text. "
            "Uses the GPU when one is available and the CPU otherwise."
        ),
    )
    parser.add_argument("input", type=Path, help="a PDF file, or a folder of page images")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output text file (default: next to the input, named after it, ending in .txt)",
    )
    parser.add_argument("--lang", default="en", help="OCR language (default: en)")
    parser.add_argument(
        "--dpi",
        type=_at_least_one,
        default=200,
        help="resolution for rendering PDF pages (default: 200)",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="OCR device, such as gpu:0 or cpu (default: the first GPU, else the CPU)",
    )
    parser.add_argument(
        "--columns",
        type=_at_least_one,
        default=1,
        help="split each page into N equal-width columns, read left to right (default: 1)",
    )
    return parser


def resolve_output(input_path: Path, output: Path | None) -> Path:
    """Check the input and output paths before any page is read (R10).

    Returns the output path; raises `UsageError` for a missing input, an output that is a
    directory, an output directory that is missing or not writable, an output that is the input,
    or an output inside a folder input whose name would be listed as a page. A path that can't
    be checked at all (no permission to look, a symlink loop) is a usage error too, never a
    traceback (R12).
    """
    try:
        return _check_paths(input_path, output)
    except (OSError, RuntimeError) as exc:
        raise UsageError(f"cannot check path: {exc}") from exc


def _check_paths(input_path: Path, output: Path | None) -> Path:
    if not input_path.exists():
        raise UsageError(f"input not found: {input_path}")
    if output is None:
        output = default_output_path(input_path)
    if output.is_dir():
        raise UsageError(f"output is a directory: {output}")
    directory = output.parent
    if not directory.is_dir():
        raise UsageError(f"output directory does not exist: {directory}")
    if not os.access(directory, os.W_OK | os.X_OK):
        raise UsageError(f"output directory is not writable: {directory}")
    # samefile also catches another name for the same file, such as BOOK.PDF for book.pdf on a
    # case-insensitive file system.
    if output.resolve() == input_path.resolve() or (
        output.exists() and os.path.samefile(output, input_path)
    ):
        raise UsageError(f"output would overwrite the input: {output}")
    if (
        input_path.is_dir()
        and output.resolve().parent == input_path.resolve()
        and is_page_name(output.name)
    ):
        raise UsageError(f"output would be a page of the input folder: {output}")
    return output


def _progress(message: str) -> None:
    """Progress and messages go to stderr; stdout stays empty (R11)."""
    print(message, file=sys.stderr, flush=True)


def convert(args: argparse.Namespace, output: Path, engine_factory: EngineFactory) -> None:
    """OCR every page and write the output once, in the D6 order.

    Pages are listed and pre-checked before the engine loads, so a bad page fails fast. The
    output is replaced only after every page has been read.
    """
    with open_source(args.input, args.dpi, args.columns) as source:
        engine = engine_factory(args.lang, args.device)
        pages: list[list[str]] = []
        for number, image in enumerate(source.images(), 1):
            _progress(f"Processing page {number}...")
            lines: list[str] = []
            for column in split_columns(image, args.columns):
                lines.extend(engine.recognize(column))
            pages.append(lines)
    write_atomic(output, format_pages(pages))
    _progress(f"Extracted text written to {output}")


MAX_ERROR_LENGTH = 300
"""Longest error message printed, in characters (D7)."""

DEBUG_ENV = "SCANSCRIBE_DEBUG"
"""Set to 1 to re-raise errors with a full traceback instead of the one-line message (D7)."""


def _one_line(exc: BaseException) -> str:
    """The error as one line of at most MAX_ERROR_LENGTH characters (R12).

    scanscribe's own errors print their message; anything else is prefixed with its type.
    """
    message = " ".join(str(exc).split())
    if not isinstance(exc, ScanscribeError):
        name = type(exc).__name__
        message = f"{name}: {message}" if message else name
    if len(message) > MAX_ERROR_LENGTH:
        message = message[: MAX_ERROR_LENGTH - 3] + "..."
    return message


def _error(message: str) -> None:
    print(f"scanscribe: error: {message}", file=sys.stderr, flush=True)


def _exit_code(exc: SystemExit) -> int:
    if exc.code is None:
        return 0
    return exc.code if isinstance(exc.code, int) else 1


def run(argv: Sequence[str], engine_factory: EngineFactory) -> int:
    """Run scanscribe with `argv` (without the program name) and return the exit code (D7).

    0 is success, 2 a usage error, 1 any other error and 130 Ctrl-C. Errors after parsing are
    printed as one `scanscribe: error:` line, and the output file is never created or changed.
    """
    try:
        return _run(argv, engine_factory)
    except KeyboardInterrupt:
        _error("interrupted")
        return 130


def _run(argv: Sequence[str], engine_factory: EngineFactory) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        try:
            output = resolve_output(args.input, args.output)
        except UsageError as exc:
            parser.error(str(exc))
    except SystemExit as exc:
        return _exit_code(exc)
    try:
        convert(args, output, engine_factory)
    except Exception as exc:
        if os.environ.get(DEBUG_ENV) == "1":
            raise
        _error(_one_line(exc))
        return 1
    return 0


def main() -> None:
    """The `scanscribe` console command (R19)."""
    sys.exit(run(sys.argv[1:], load_engine))
