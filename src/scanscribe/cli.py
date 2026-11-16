"""The scanscribe command line: arguments, path checks and the run itself."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from scanscribe.engine import EngineFactory, UsageError
from scanscribe.output import default_output_path, format_pages, write_atomic
from scanscribe.pages import open_source, split_columns


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
    directory, an output directory that is missing or not writable, or an output that is the
    input.
    """
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
    if output.resolve() == input_path.resolve():
        raise UsageError(f"output would overwrite the input: {output}")
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


def _exit_code(exc: SystemExit) -> int:
    if exc.code is None:
        return 0
    return exc.code if isinstance(exc.code, int) else 1


def run(argv: Sequence[str], engine_factory: EngineFactory) -> int:
    """Run scanscribe with `argv` (without the program name) and return the exit code."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        try:
            output = resolve_output(args.input, args.output)
        except UsageError as exc:
            parser.error(str(exc))
    except SystemExit as exc:
        return _exit_code(exc)
    convert(args, output, engine_factory)
    return 0
