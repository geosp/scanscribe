"""The OCR engine interface and scanscribe's error types.

The CLI only talks to an engine through `OcrEngine`, so tests can pass a fake engine and never
import PaddlePaddle (D1).
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

PageImage = NDArray[np.uint8]
"""An RGB image as a height × width × 3 array of bytes."""


class OcrEngine(Protocol):
    """Turns one RGB slice into its text lines, top to bottom."""

    def recognize(self, image: PageImage) -> list[str]: ...


EngineFactory = Callable[[str, "str | None"], OcrEngine]
"""Builds an engine from `(lang, device)`; `device` is None when `--device` isn't given."""


class ScanscribeError(Exception):
    """Base class for errors scanscribe reports itself."""


class UsageError(ScanscribeError):
    """A problem with the arguments or paths, found before any page is read (exit 2)."""


class InputError(ScanscribeError):
    """A problem with the input's content, the output write or the engine (exit 1)."""


class EngineMissingError(InputError):
    """PaddleOCR or PaddlePaddle isn't installed (R14)."""


ENGINE_MISSING_MESSAGE = (
    "the OCR engine is not installed; install one build: "
    "`uv sync --extra gpu` (NVIDIA GPU) or `uv sync --extra cpu`"
)

_ENGINE_MODULES = frozenset({"paddle", "paddleocr"})


def load_engine(lang: str, device: str | None) -> OcrEngine:
    """Load the PaddleOCR engine, choose its device and print it (D2, R14, R15, R16).

    Paddle is imported here and only here, so the CLI and the tests never import it otherwise.
    """
    try:
        # import_module, not `from scanscribe import ...`: a stale package attribute would hide
        # a cleared module.
        adapter = importlib.import_module("scanscribe.paddle_engine")
    except ModuleNotFoundError as exc:
        if exc.name in _ENGINE_MODULES:
            raise EngineMissingError(ENGINE_MISSING_MESSAGE) from exc
        raise
    resolved: str = adapter.resolve_device(device)
    # Printed before the engine is built, so it shows during a first-run model download.
    print(f"Using device: {resolved}", file=sys.stderr, flush=True)
    engine: OcrEngine = adapter.PaddleOcrEngine(lang, resolved)
    return engine
