"""The OCR engine interface and scanscribe's error types.

The CLI only talks to an engine through `OcrEngine`, so tests can pass a fake engine and never
import PaddlePaddle (D1).
"""

from __future__ import annotations

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
