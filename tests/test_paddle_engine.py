"""The PaddleOCR adapter, against fake Paddle modules (R15, R17, R18, D3, D4)."""

from __future__ import annotations

import importlib
from types import ModuleType

import numpy as np
import pytest
from conftest import FakePaddle


def adapter() -> ModuleType:
    return importlib.import_module("scanscribe.paddle_engine")


# --- Device (R15, D3) ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cuda", "gpus", "requested", "expected"),
    [
        (True, 1, None, "gpu:0"),
        (True, 0, None, "cpu"),
        (False, 0, None, "cpu"),
        (True, 1, "cpu", "cpu"),
        (True, 2, "gpu:1", "gpu:1"),
        (True, 1, None, "gpu:0"),  # again after the CPU cases: no state leaks between tests
    ],
)
def test_resolve_device(
    fake_paddle: FakePaddle, cuda: bool, gpus: int, requested: str | None, expected: str
) -> None:
    fake_paddle.cuda, fake_paddle.gpus = cuda, gpus
    assert adapter().resolve_device(requested) == expected


# --- Engine settings (R17) -----------------------------------------------------------------


def test_cpu_disables_mkldnn(fake_paddle: FakePaddle) -> None:
    adapter().PaddleOcrEngine("es", "cpu")
    assert fake_paddle.created == [
        {
            "lang": "es",
            "device": "cpu",
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
            "enable_mkldnn": False,
        }
    ]


def test_gpu_leaves_mkldnn_alone(fake_paddle: FakePaddle) -> None:
    adapter().PaddleOcrEngine("en", "gpu:0")
    [kwargs] = fake_paddle.created
    assert kwargs["device"] == "gpu:0"
    assert "enable_mkldnn" not in kwargs


# --- Recognition (R18, D4) -----------------------------------------------------------------


def test_slices_reach_paddleocr_as_contiguous_bgr(fake_paddle: FakePaddle) -> None:
    engine = adapter().PaddleOcrEngine("en", "cpu")
    image = np.zeros((2, 3, 3), dtype=np.uint8)
    image[0, 0] = (255, 0, 0)
    engine.recognize(image)
    [sent] = fake_paddle.inputs
    assert tuple(sent[0, 0]) == (0, 0, 255)
    assert sent.flags["C_CONTIGUOUS"]
    assert tuple(image[0, 0]) == (255, 0, 0)  # the caller's slice is unchanged


def test_lines_from_every_result_are_kept_in_order(fake_paddle: FakePaddle) -> None:
    fake_paddle.results = [{"rec_texts": ["one", "two"]}, {}, {"rec_texts": ["three"]}]
    engine = adapter().PaddleOcrEngine("en", "cpu")
    assert engine.recognize(np.zeros((2, 2, 3), dtype=np.uint8)) == ["one", "two", "three"]


def test_paddle_prints_never_reach_stdout(
    fake_paddle: FakePaddle, capsys: pytest.CaptureFixture[str]
) -> None:
    fake_paddle.chatter = True
    engine = adapter().PaddleOcrEngine("en", "cpu")
    engine.recognize(np.zeros((2, 2, 3), dtype=np.uint8))
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Creating model: fake" in captured.err
    assert "predicting" in captured.err
