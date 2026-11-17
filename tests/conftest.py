"""Shared test doubles and fixture builders.

Every fixture is generated in `tmp_path`: no image or PDF is committed (D9). Pages are solid
colors, and `FakeEngine` names the palette color nearest to each slice's center pixel, so order
tests need no real OCR.
"""

from __future__ import annotations

import random
import sys
import types
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
import pytest
from numpy.typing import NDArray
from PIL import Image

import scanscribe

PALETTE: dict[str, tuple[int, int, int]] = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "yellow": (255, 255, 0),
}


def nearest_color(pixel: Sequence[int]) -> str:
    """Return the name of the palette color nearest to an RGB pixel."""
    r, g, b = (int(c) for c in pixel[:3])
    return min(
        PALETTE,
        key=lambda name: sum((a - c) ** 2 for a, c in zip(PALETTE[name], (r, g, b), strict=True)),
    )


@dataclass
class FakeEngine:
    """An `OcrEngine` that reads colors instead of text.

    `fail_on_call` makes the Nth `recognize` call (1-based) raise `error`.
    """

    lang: str = "en"
    device: str | None = None
    fail_on_call: int | None = None
    error: BaseException = field(default_factory=lambda: RuntimeError("engine failed"))
    shapes: list[tuple[int, ...]] = field(default_factory=list)

    def recognize(self, image: NDArray[np.uint8]) -> list[str]:
        self.shapes.append(image.shape)
        if self.fail_on_call is not None and len(self.shapes) == self.fail_on_call:
            raise self.error
        height, width = image.shape[:2]
        return [nearest_color(image[height // 2, width // 2])]


@dataclass
class FakeFactory:
    """An `EngineFactory` that records its calls and hands out one `FakeEngine`."""

    engine: FakeEngine = field(default_factory=FakeEngine)
    calls: list[tuple[str, str | None]] = field(default_factory=list)

    def __call__(self, lang: str, device: str | None) -> FakeEngine:
        self.calls.append((lang, device))
        self.engine.lang = lang
        self.engine.device = device
        return self.engine


def page_image(
    colors: Sequence[str], width: int = 60, height: int = 40, mode: str = "RGB"
) -> Image.Image:
    """A page split into len(colors) vertical slices, using the same edges as R4."""
    n = len(colors)
    array = np.zeros((height, width, 3), dtype=np.uint8)
    for i, name in enumerate(colors):
        left, right = round(i * width / n), round((i + 1) * width / n)
        array[:, left:right] = PALETTE[name]
    image = Image.fromarray(array, "RGB")
    return image if mode == "RGB" else image.convert(mode)


class Fixtures:
    """Builds input files and folders under one temporary directory."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def image_folder(
        self,
        name: str,
        pages: dict[str, Sequence[str]],
        width: int = 60,
        height: int = 40,
    ) -> Path:
        """A folder holding one image per file name, each with the given slice colors."""
        folder = self.root / name
        folder.mkdir(parents=True, exist_ok=True)
        for file_name, colors in pages.items():
            image = page_image(colors, width, height)
            if file_name.lower().endswith((".jpg", ".jpeg")):
                image.save(folder / file_name, quality=95)
            else:
                image.save(folder / file_name)
        return folder

    def pdf(
        self,
        name: str,
        pages: Sequence[Sequence[str]],
        width: int = 72,
        height: int = 72,
    ) -> Path:
        """A PDF with one page per entry, written at 72 DPI so 1 px is 1 point."""
        images = [page_image(colors, width, height) for colors in pages]
        path = self.root / name
        images[0].save(path, "PDF", save_all=True, append_images=images[1:], resolution=72.0)
        return path

    def red_pdf(self, name: str = "red.pdf") -> Path:
        return self.pdf(name, [["red"]])

    def zero_page_pdf(self, name: str = "empty.pdf") -> Path:
        path = self.root / name
        document = pdfium.PdfDocument.new()
        try:
            document.save(path)
        finally:
            document.close()
        return path

    def notes_dat(self, name: str = "notes.dat") -> Path:
        path = self.root / name
        path.write_text("These are plain-text notes, not a PDF.\n", encoding="utf-8")
        return path

    def corrupt_image(self, folder: Path, name: str = "corrupt.png") -> Path:
        path = folder / name
        path.write_bytes(random.Random(0).randbytes(256))
        return path

    def truncated_png(self, folder: Path, name: str = "truncated.png") -> Path:
        """A valid PNG cut to its first 60 bytes: `open` accepts it, decoding fails."""
        path = folder / name
        page_image(["red", "blue"]).save(path)
        path.write_bytes(path.read_bytes()[:60])
        return path

    def truncated_jpeg(self, folder: Path, name: str = "truncated.jpg") -> Path:
        """A noisy JPEG cut to half its length: `open` accepts it, decoding fails."""
        path = folder / name
        noise = np.random.default_rng(0).integers(0, 256, (64, 64, 3), dtype=np.uint8)
        Image.fromarray(noise, "RGB").save(path, quality=95)
        data = path.read_bytes()
        path.write_bytes(data[: len(data) // 2])
        return path


@pytest.fixture
def fx(tmp_path: Path) -> Fixtures:
    return Fixtures(tmp_path)


@pytest.fixture
def factory() -> FakeFactory:
    return FakeFactory()


@pytest.fixture
def make_factory() -> Callable[..., FakeFactory]:
    """Builds a `FakeFactory` whose engine takes `FakeEngine`'s keyword arguments."""

    def make(**engine_kwargs: object) -> FakeFactory:
        return FakeFactory(engine=FakeEngine(**engine_kwargs))

    return make


# --- Fake Paddle modules (phase 02) --------------------------------------------------------


@dataclass
class FakePaddle:
    """Controls and records the fake `paddle` and `paddleocr` modules."""

    cuda: bool = True
    gpus: int = 1
    results: list[dict[str, object]] = field(default_factory=lambda: [{"rec_texts": ["fake line"]}])
    chatter: bool = False
    """When True, the fake PaddleOCR prints to stdout while built and in `predict`."""
    created: list[dict[str, object]] = field(default_factory=list)
    inputs: list[NDArray[np.uint8]] = field(default_factory=list)


def _forget_adapter() -> None:
    sys.modules.pop("scanscribe.paddle_engine", None)
    if hasattr(scanscribe, "paddle_engine"):
        delattr(scanscribe, "paddle_engine")


@pytest.fixture
def fake_paddle(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakePaddle]:
    """Installs fake `paddle` and `paddleocr` modules and a fresh adapter import.

    The adapter is forgotten before and after each test, from `sys.modules` and from the package
    attribute, so no test sees a module bound to another test's fakes.
    """
    state = FakePaddle()

    paddle = types.ModuleType("paddle")
    paddle.device = types.SimpleNamespace(
        is_compiled_with_cuda=lambda: state.cuda,
        cuda=types.SimpleNamespace(device_count=lambda: state.gpus),
    )

    class FakePaddleOCR:
        def __init__(self, **kwargs: object) -> None:
            if state.chatter:
                print("Creating model: fake")
            state.created.append(kwargs)

        def predict(self, image: NDArray[np.uint8]) -> list[dict[str, object]]:
            if state.chatter:
                print("predicting")
            state.inputs.append(image)
            return state.results

    paddleocr = types.ModuleType("paddleocr")
    paddleocr.PaddleOCR = FakePaddleOCR

    _forget_adapter()
    monkeypatch.setitem(sys.modules, "paddle", paddle)
    monkeypatch.setitem(sys.modules, "paddleocr", paddleocr)
    yield state
    _forget_adapter()


@pytest.fixture
def no_paddle(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Makes `import paddle` and `import paddleocr` fail, whatever is installed (R14)."""
    _forget_adapter()
    monkeypatch.setitem(sys.modules, "paddle", None)
    monkeypatch.setitem(sys.modules, "paddleocr", None)
    yield
    _forget_adapter()


# --- No real Paddle (R13) ------------------------------------------------------------------


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Fail the run if any test imported the real `paddle` or `paddleocr` (R13).

    Fakes are removed after each test, so anything left in `sys.modules` is real. This sets the
    exit status instead of asserting, which pytest would report as an internal error.
    """
    leaked = sorted(name for name in ("paddle", "paddleocr") if sys.modules.get(name) is not None)
    if leaked:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        message = f"R13: the test run imported the real {', '.join(leaked)}"
        if reporter is not None:
            reporter.write_line(message, red=True)
        else:
            print(message, file=sys.stderr)
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
