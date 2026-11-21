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

Keep books in `in/` and results in `out/`. Git ignores both folders, so book material stays local. For example:

```text
in/
  my-book.pdf
  my-book/                 # a book as page images, one folder per chapter
    01_introduction/
      page001.jpg
      page002.jpg
    02_chapter_two/
out/                       # scanscribe writes here
```

scanscribe doesn't create missing folders, so create the output folder first:

```bash
mkdir -p out
```

Examples:

```bash
# A PDF
uv run scanscribe in/my-book.pdf -o out/my-book.txt

# One chapter of page images
uv run scanscribe in/my-book/01_introduction -o out/01_introduction.txt

# Pages with two columns, read left column first, then right
uv run scanscribe in/my-book/02_chapter_two --columns 2 -o out/02_chapter_two.txt

# A Spanish chapter
uv run scanscribe in/mi-libro/capitulo_01 --lang es -o out/capitulo_01.txt

# A small or low-quality scan: render PDF pages at a higher resolution
uv run scanscribe in/old-scan.pdf --dpi 300 -o out/old-scan.txt

# Force the CPU, for example while the GPU is busy
uv run scanscribe in/my-book.pdf --device cpu -o out/my-book.txt

# Every chapter of a book, one text file per chapter in out/my-book/
mkdir -p out/my-book
for ch in in/my-book/*/; do
  uv run scanscribe "$ch" -o "out/my-book/$(basename "$ch").txt"
done

# Keep the progress log, for example on a long run
uv run scanscribe in/my-book.pdf -o out/my-book.txt 2> out/my-book.log
```

Without `-o`, the output goes next to the input: `in/my-book.pdf` writes `in/my-book.txt`, and the folder `in/my-book/01_introduction/` writes `in/my-book/01_introduction.txt`.

Tips:
- **Columns:** `--columns` cuts every page into equal-width strips at the exact middle; it doesn't look for the gap between columns. Run single-column pages, such as a chapter opening, separately without it.
- **Language:** `--lang` takes a PaddleOCR language code such as `en`, `es`, `fr`, `de` or `pt`. The default is `en`, so set it for other languages.
- **Page order:** a folder's pages are read in natural order, so `page2.png` comes before `page10.png`. Files starting with `.` are skipped.

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

## Use as a library

scanscribe can also be called from Python, for example by an MCP server. Load the engine once and reuse it for every input:

```python
from pathlib import Path

from scanscribe import UsageError, InputError, load_engine, transcribe

engine = load_engine("en", None, on_device=lambda device: print("OCR on", device))


def progress(page: int, total: int) -> None:
    print(f"page {page}/{total}")  # raise any exception here to stop between pages


try:
    text = transcribe(Path("in/my-book.pdf"), engine, dpi=200, columns=1, on_page=progress)
except (UsageError, InputError) as exc:
    print("cannot OCR:", exc)
```

`transcribe` returns the same page-marked text the command writes, with the same defaults. It never prints or writes a file, although PaddleOCR itself logs to stderr. Bad arguments or a missing input raise `UsageError`, and an unreadable page raises `InputError`, both before any OCR. For more control, open the input with `open_source(path, dpi, columns)`, then call `ocr_source(source, engine, on_page)` to get each page's lines.

The public API is exactly the names in `scanscribe.__all__`:

- functions: `transcribe`, `ocr_source`, `open_source`, `format_pages` and `load_engine`;
- types: `PageSource`, `OcrEngine`, `PageImage`, `EngineFactory` and `ProgressCallback`;
- the constant `IMAGE_EXTENSIONS`;
- errors: `ScanscribeError`, with its subclasses `UsageError`, `InputError` and `EngineMissingError`.

It follows [semantic versioning](https://semver.org) from `v0.1.0`; everything else is internal. The package ships `py.typed`.

Limits:

- **One OCR job per process at a time.** While it runs, the PaddleOCR engine sends the whole process's stdout to stderr, and PDF rendering (pdfium) isn't safe from two threads.
- **No progress during the pre-check.** Every page is checked before the first progress call, so a large folder of images takes a while before page 1.

To depend on scanscribe from another uv project, pin a tag, then copy the PaddlePaddle settings from this repository's `pyproject.toml`: the two extras, the `[tool.uv] conflicts` rule, the `paddlepaddle-cu126` index and its `[tool.uv.sources]` entry. uv doesn't inherit those from a dependency.

```toml
dependencies = ["scanscribe @ git+https://github.com/geosp/scanscribe@v0.1.0"]
```

## Book material

Inputs and outputs are usually copyrighted books. `in/`, `out/`, PDFs and images are ignored by Git; keep them local.
