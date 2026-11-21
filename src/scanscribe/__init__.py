"""scanscribe: OCR scanned PDFs and folders of page images into page-marked text.

The names in `__all__` are the public library API and follow semantic versioning; everything
else is internal. Importing this package never imports Paddle: `load_engine` does, when called.
"""

from scanscribe.api import ProgressCallback, ocr_source, transcribe
from scanscribe.engine import (
    EngineFactory,
    EngineMissingError,
    InputError,
    OcrEngine,
    PageImage,
    ScanscribeError,
    UsageError,
    load_engine,
)
from scanscribe.output import format_pages
from scanscribe.pages import IMAGE_EXTENSIONS, PageSource, open_source

__version__ = "0.1.0"

__all__ = [
    "IMAGE_EXTENSIONS",
    "EngineFactory",
    "EngineMissingError",
    "InputError",
    "OcrEngine",
    "PageImage",
    "PageSource",
    "ProgressCallback",
    "ScanscribeError",
    "UsageError",
    "format_pages",
    "load_engine",
    "ocr_source",
    "open_source",
    "transcribe",
]
