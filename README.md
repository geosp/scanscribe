# scanscribe

OCR scanned PDFs and folders of page images (for example, phone or Kindle screenshots of a book) into page-marked plain text, using [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR). It runs on an NVIDIA GPU when one is available and falls back to the CPU otherwise.

## Install

Requires [uv](https://docs.astral.sh/uv/) and Python 3.10 to 3.12. Install exactly one OCR engine build:

```bash
uv sync --extra gpu   # NVIDIA GPU, CUDA 12.6+ driver (Linux or Windows, x86_64)
uv sync --extra cpu   # any machine; slower
```

The two extras conflict on purpose: the GPU and CPU builds of PaddlePaddle cannot be installed together.

## Usage

```bash
uv run scanscribe book.pdf                  # writes book.txt next to the PDF
uv run scanscribe scans/ch1/ -o ch1.txt     # a folder of page images
uv run scanscribe book.pdf --columns 2      # two-column pages, read left to right
```

| Option | Default | Meaning |
| --- | --- | --- |
| `input` | | A PDF, or a folder of page images (`.png .jpg .jpeg .tif .tiff .bmp .webp`, hidden files skipped, sorted in natural order: `page2` before `page10`) |
| `-o`, `--output` | next to the input | Output text file. A PDF `book.pdf` writes `book.txt`; a folder `Vol.2/` writes `Vol.2.txt` beside it |
| `--lang` | `en` | PaddleOCR language code |
| `--dpi` | `200` | Resolution for rendering PDF pages |
| `--device` | first GPU, else CPU | PaddleOCR device, such as `gpu:0` or `cpu` |
| `--columns` | `1` | Split each page into N equal-width columns, read left to right |

The chosen device is printed first (`Using device: gpu:0`). Progress and errors go to stderr; stdout stays empty.

### Output

Each page is a `--- Page N ---` line followed by its text lines, and pages are separated by one blank line, in UTF-8:

```text
--- Page 1 ---
first line
second line

--- Page 2 ---
...
```

Every page is checked before OCR starts, and the output file is replaced only after every page has been read, so a failed run leaves an existing output untouched.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | An input or engine error: no pages, an unreadable page, a page narrower than `--columns`, a missing OCR engine, or a failure during OCR. Printed as one `scanscribe: error:` line; set `SCANSCRIBE_DEBUG=1` for a full traceback |
| `2` | A usage error: a bad option value, a missing input, or an output path that can't be written or would overwrite the input or one of its pages |
| `130` | Interrupted with Ctrl-C |

### First run

The first run downloads PaddleOCR's models, which takes a while. Two first runs started at the same time can collide on that download; let one finish first.

## Book material

Inputs and outputs are usually copyrighted books. `in/`, `out/`, PDFs and images are ignored by Git; keep them local.
