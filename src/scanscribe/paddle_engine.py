"""The PaddleOCR engine.

Importing this module imports Paddle, so only `scanscribe.engine.load_engine` imports it, and only
when OCR starts (D2).
"""

from __future__ import annotations

import contextlib
import sys
from typing import Any

import numpy as np
import paddle
from paddleocr import PaddleOCR

from scanscribe.engine import PageImage


def resolve_device(requested: str | None) -> str:
    """`--device` when given; else `gpu:0` on a CUDA build that sees a GPU; else `cpu` (R15, D3).

    This is the check PaddleX uses for its own default device (notes.md#d3).
    """
    if requested:
        return requested
    if paddle.device.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0:
        return "gpu:0"
    return "cpu"


class PaddleOcrEngine:
    """An `OcrEngine` backed by PaddleOCR, with the prototype's settings."""

    def __init__(self, lang: str, device: str) -> None:
        kwargs: dict[str, Any] = {
            "lang": lang,
            "device": device,
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
        }
        if device.startswith("cpu"):
            # MKL-DNN (oneDNN) crashes with the PP-OCRv6 detection model on the CPU (R17).
            kwargs["enable_mkldnn"] = False
        # Paddle logs to stderr; this keeps any stray print off stdout too (R11, notes.md#d3).
        with contextlib.redirect_stdout(sys.stderr):
            self._ocr = PaddleOCR(**kwargs)

    def recognize(self, image: PageImage) -> list[str]:
        # PaddleOCR reads NumPy arrays as BGR (D4, R18).
        bgr = np.ascontiguousarray(image[:, :, ::-1])
        with contextlib.redirect_stdout(sys.stderr):
            results = self._ocr.predict(bgr)
        lines: list[str] = []
        for result in results:
            lines.extend(str(text) for text in result.get("rec_texts", []))
        return lines
