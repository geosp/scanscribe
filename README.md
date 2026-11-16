# scanscribe

OCR scanned PDFs and folders of page images (for example, phone or Kindle screenshots of a book) into page-marked plain text, using [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR). It runs on an NVIDIA GPU when one is available and falls back to the CPU otherwise.

> **Status:** under construction. The project skeleton is in place; the command-line tool is built by the first implementation plan.

## Install

Requires [uv](https://docs.astral.sh/uv/) and Python 3.10 to 3.12. Install exactly one OCR engine build:

```bash
uv sync --extra gpu   # NVIDIA GPU, CUDA 12.6+ driver (Linux or Windows, x86_64)
uv sync --extra cpu   # any machine; slower
```

The two extras conflict on purpose: the GPU and CPU builds of PaddlePaddle cannot be installed together.

## Book material

Inputs and outputs are usually copyrighted books. `in/`, `out/`, PDFs and images are ignored by Git; keep them local.
