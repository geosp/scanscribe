---
title: Rebuild the scanscribe CLI from the ocr-pdf prototype
status: draft
created: 2026-11-16
updated: 2026-11-16
design_review: { status: passed, rounds: 2, last: 2026-11-16 }
approved: null
adr_review: null
---

# Rebuild the scanscribe CLI from the ocr-pdf prototype

## Summary

scanscribe has a project skeleton but no command. This plan rebuilds the `ocr-pdf` prototype's CLI
as `scanscribe`, with the same options and the same `--- Page N ---` output format (R3, R19). The
OCR engine moves behind an interface (D1). Paddle is imported only when OCR starts (D2), so CI and
the tests never import PaddlePaddle. The tool chooses the device itself and prints it (D3). Images
reach PaddleOCR in the BGR order it expects (D4). Bad arguments, empty or unreadable inputs and
unwritable outputs are caught before OCR starts. A failure during OCR leaves the output file
untouched (R5–R12, R20, D6). Five behaviors break parity with the prototype; What changes lists
them.

Phase 01 builds the pipeline and the CLI against a fake engine. Phase 02 adds the PaddleOCR adapter,
the `scanscribe` command and the owner's manual check on GPU and CPU. The main risk is that the BGR
fix changes the OCR text. The manual check blocks phase 02 if any page reads worse than the
prototype's.

```text
validate args and paths (R9, R10) ─▶ list pages (R1, R2) ─▶ pre-check pages and widths (R5, R7, R8)
  ─▶ load engine, choose and print device (D2, D3) ─▶ for each page: split (R4), recognize
  ─▶ format all pages (R3) ─▶ write a temp file and rename it onto the output, once (D6)
```

## Why

The prototype takes a PDF or a folder of page images, with `-o/--output`, `--lang`, `--dpi`,
`--device` and `--columns`. It works on the owner's GPU machine, but it depends on the GPU build
only, has no tests, and can't run in CI. Several inputs also fail badly. A folder named `Vol.2`
writes to `Vol.txt`. An empty folder writes an empty file. An output path that can't be written
crashes only after the whole book has been OCR'd. The repository's CI, review rules and `gpu`/`cpu`
extras are now in place, so the CLI comes next. The full behavior inventory is in
[notes.md#prototype](notes.md#prototype).

## What changes

- New code in `src/scanscribe/`: page sources, column split, output formatting, the CLI, the
  engine interface and the PaddleOCR adapter, with tests in `tests/`.
- A console command, `scanscribe`, that works like the prototype's `ocr-pdf`.
- **BREAKING** (against the prototype):
  - images are passed as BGR (D4);
  - `--columns` or `--dpi` below 1 are rejected (R9);
  - empty inputs are errors (R7);
  - hidden files are skipped (R1);
  - `Vol.2/` writes `Vol.2.txt` (R6).
- The README gains a Usage section. `pyproject.toml` gains the script entry and mypy overrides.

### Non-goals

- Single image files as input (R2 opens every file input as a PDF).
- EXIF rotation, multi-frame TIFFs and layout detection. Columns stay equal-width slices.
- Streaming output page by page, or resuming a partial run.
- A `python -m scanscribe` entry or a `--version` flag.
- Real OCR in CI.

## Terms

- **Prototype**: the `ocr-pdf` tool, outside this repository. It is reference material only.
- **Owner**: the repository's maintainer. Only the owner runs real OCR on book material.
- **Page source**: the ordered pages of one input, from a folder of images or a PDF.
- **Page image**: one page as an RGB array of height × width × 3 bytes.
- **Slice**: one of the N vertical strips that `--columns N` cuts a page into.
- **Engine**: anything that turns a slice into a list of text lines (`OcrEngine`, D1).
- **Fake engine**: the test double for the engine. It never runs OCR.
- **Fake Paddle modules**: stand-in `paddle` and `paddleocr` modules that tests place in
  `sys.modules` so the adapter can be tested without PaddlePaddle.
- **Adapter**: the engine that wraps PaddleOCR (`PaddleOcrEngine`, in `scanscribe.paddle_engine`).
- **PaddleX**: the library PaddleOCR is built on. It does the image reading and device handling.
- **MKL-DNN**: Intel's CPU acceleration in PaddlePaddle (oneDNN). It crashes with PaddleOCR's
  PP-OCRv6 text detection model on the locked PaddlePaddle 3.3.1, so it is turned off on the CPU
  (notes.md#d3).
- **Base install**: `uv sync` with no extra, as in CI. It has no PaddlePaddle or PaddleOCR.
- **Extra**: the `gpu` or `cpu` optional dependency set. At most one is installed.
- **Device string**: PaddleOCR's `device` value, such as `gpu:0` or `cpu`.
- **Usage error**: a problem with the arguments or paths, found before any page is read.
- **Input error**: a problem with the input's content, the output write or the engine.

## Requirements

### R1 · Folder pages are image files in natural order

A folder's pages are the regular files directly inside it whose names don't start with `.` and end in a supported extension (`.png .jpg .jpeg .tif .tiff .bmp .webp`, any case), sorted by name with case ignored and digit runs compared as numbers, with ties broken by the exact name.
- **Given** `Page10.png`, `page2.png` and `page1.PNG`, **when** the folder is read, **then** the order is `page1.PNG`, `page2.png`, `Page10.png`.
- **Given** a subfolder named `x.png`, a file `notes.txt` and a file `._page1.jpg`, **when** the folder is read, **then** none of them is a page.
- **Given** `a.png` and `A.png`, **when** the folder is read, **then** `A.png` comes first on every run.

### R2 · PDF pages are rendered at the requested DPI

A file input is opened as a PDF, and each page is rendered at `--dpi` (default 200) before OCR.
- **Given** a 1-inch-wide PDF page, **when** it is read with `--dpi 144`, **then** the page image is 144 px wide.

### R3 · Output keeps the prototype's format

Each page is the line `--- Page N ---` and a newline, then its lines joined by newlines; pages are joined by one blank line, and the file is UTF-8.
- **Given** page 1 with lines `a` and `b`, and page 2 with no lines, **when** the run finishes, **then** the file is exactly `--- Page 1 ---\na\nb\n\n--- Page 2 ---\n`.

### R4 · Columns are read left to right

With `--columns N`, slice edges sit at Python's `round(i × width / N)` (halves to even, as in the prototype) for i = 0…N, and the slices' lines are written left to right under one page marker.
- **Given** `--columns 2` and a page whose left half reads `L` and right half `R`, **when** it is OCR'd, **then** the page's lines are `L` then `R`.
- **Given** `--columns 3` and a 100 px page, **when** it is split, **then** the slice widths are 33, 34 and 33 px.

### R5 · A page narrower than its column count is an input error

A page narrower than `--columns` pixels (for a PDF, at the requested DPI) is an input error found before the engine loads, and the message names the page.
- **Given** `--columns 4` and a 3 px wide `p1.png`, **when** the run starts, **then** it exits 1 naming `p1.png`, the engine is never loaded, and no output file is written.

### R6 · The default output sits next to the input and keeps its name

Without `-o`, a PDF's output is its path with the suffix replaced by `.txt`, and a folder's output is the sibling file `<folder name>.txt`.
- **Given** `scans/book.v2.pdf`, **when** no `-o` is given, **then** the output is `scans/book.v2.txt`.
- **Given** the folder `scans/Vol.2/`, **when** no `-o` is given, **then** the output is `scans/Vol.2.txt`, not `scans/Vol.txt`.
- **Given** the input `.` run from `scans/ch1`, **when** no `-o` is given, **then** the output is `scans/ch1.txt`.

### R7 · An input with no pages is an input error

A folder with no page files, or a PDF that has no pages or can't be opened, is an input error, and no output file is written.
- **Given** an empty folder, **when** the run starts, **then** it exits 1 with "no page images found", and no `.txt` exists.
- **Given** a zero-page PDF, or a plain-text file `notes.dat`, as input, **when** the run starts, **then** it exits 1 with a message naming the file.

### R8 · An unreadable page aborts the run and leaves the output untouched

A page that can't be read is an input error naming the page, and the output file is neither created nor changed.
- **Given** a folder whose third file is a corrupt `.png` or a truncated `.jpg`, **when** the run starts, **then** it exits 1 naming that file, before the engine is loaded.
- **Given** an existing output file and a page that fails during OCR, **when** the run aborts, **then** the existing file is byte-identical.

### R9 · `--columns` and `--dpi` must be at least 1

A `--columns` or `--dpi` value below 1 is a usage error.
- **Given** `--columns 0` or `--dpi -5`, **when** the command runs, **then** it exits 2 with argparse's usage message.

### R10 · Bad input or output paths are usage errors

A missing input, an output that is an existing directory, an output directory that is missing or not writable, or an output that resolves to the input is a usage error, raised before any page is read.
- **Given** `-o missing-dir/out.txt`, or `-o out` where `out/` is a directory, **when** the command runs, **then** it exits 2 and no page is read.
- **Given** an output directory without write permission, **when** the command runs, **then** it exits 2 and no page is read.
- **Given** `-o book.pdf` for the input `book.pdf`, **when** the command runs, **then** it exits 2 and the PDF is untouched.

### R11 · Progress goes to stderr, never stdout

All progress and messages go to stderr, including `Processing page N...` for each page and `Extracted text written to <path>` at the end, and stdout stays empty. Only `--help` prints to stdout, as argparse does.
- **Given** a 2-page run, **when** it finishes, **then** stdout is empty and stderr has `Processing page 1...` then `Processing page 2...`.

### R12 · Errors other than usage errors are one line, never a traceback

Every error that is not a usage error is printed as one stderr line that starts with `scanscribe: error:`, with no traceback, even when the underlying message spans several lines.
- **Given** an engine that raises on page 2, **when** the run fails, **then** stderr ends with one `scanscribe: error:` line and contains no `Traceback`.
- **Given** the final rename fails with an `OSError`, **when** the run fails, **then** it exits 1 with one such line.
- **Given** an engine error whose message has 5 lines, **when** the run fails, **then** stderr has exactly one `scanscribe: error:` line.

### R13 · The test suite and the CLI's import path never import Paddle

Importing scanscribe's modules other than the adapter, running `scanscribe --help` and running the test suite never import the real `paddle` or `paddleocr`, whatever is installed.
- **Given** the base install, or a machine with an extra installed, **when** the test suite runs, **then** it passes and the real `paddle` and `paddleocr` were never imported.

### R14 · A missing engine names the install commands

If PaddleOCR or PaddlePaddle can't be imported, the run ends with an input error that names `uv sync --extra gpu` and `uv sync --extra cpu`.
- **Given** the base install and a valid folder, **when** `scanscribe` runs, **then** it exits 1 with that message and writes no output file.

### R15 · The device is `--device`, else the first GPU, else the CPU

The device is `--device` when given; otherwise `gpu:0` when Paddle is a CUDA build that sees at least one GPU; otherwise `cpu`.
- **Given** a CUDA build with one visible GPU, **when** no `--device` is given, **then** the device is `gpu:0`.
- **Given** a CUDA build with no visible GPU, or a CPU build, **when** no `--device` is given, **then** the device is `cpu`.
- **Given** a CUDA build with a GPU, **when** `--device cpu` is given, **then** the device is `cpu`.

### R16 · The chosen device is printed

The chosen device string is printed to stderr before the first page is processed.
- **Given** the device `gpu:0`, **when** the run starts, **then** stderr shows `Using device: gpu:0` before `Processing page 1...`.

### R17 · MKL-DNN is disabled only on the CPU

PaddleOCR gets `enable_mkldnn=False` only when the device string starts with `cpu`.
- **Given** the device `cpu`, **when** the adapter is created, **then** `enable_mkldnn=False` is passed.
- **Given** the device `gpu:0`, **when** the adapter is created, **then** `enable_mkldnn` is not passed.

### R18 · Slices reach PaddleOCR in BGR order

The adapter reverses each slice's channels from RGB to BGR before calling PaddleOCR.
- **Given** a slice whose first pixel is RGB (255, 0, 0), **when** it is recognized, **then** PaddleOCR receives (0, 0, 255).

### R19 · The command is `scanscribe`

The package installs the command `scanscribe` with `input`, `-o/--output`, `--lang` (default `en`), `--dpi` (default 200), `--device` and `--columns` (default 1).
- **Given** the base install, **when** `uv run scanscribe --help` runs, **then** it lists those options and exits 0.

### R20 · Ctrl-C stops cleanly

An interrupted run exits 130 with one `scanscribe: error:` line, and the output file is neither created nor changed.
- **Given** an existing output file, **when** Ctrl-C arrives during page 2, **then** the run exits 130, the file is byte-identical and no temp file remains.

## Decisions

### D1 · A one-method engine protocol, injected into the CLI

`OcrEngine` is a `typing.Protocol` with one method, `recognize(image) -> list[str]`, which takes an
RGB slice. `cli.run(argv, engine_factory)` in `cli.py` takes a factory `(lang, device) -> OcrEngine`.
Tests pass the fake engine. `cli.main()` passes `engine.load_engine` (D2), which also chooses and prints the device
(R15, R16), so `cli.run` never touches Paddle. Rejected: an abstract base class (the fake would have
to inherit from it for no gain); passing PaddleOCR's result objects through (that would tie the
tests to Paddle's result shape).

### D2 · Paddle is imported only inside `load_engine`

`scanscribe.paddle_engine` imports `paddle` and `paddleocr` at its top. Only `load_engine`, in
`scanscribe/engine.py`, imports that module, inside the function. A `ModuleNotFoundError` whose name
is exactly `paddle` or `paddleocr` becomes `EngineMissingError` (R14). Any other import error, such
as a broken native library in an installed build, is reported on the R12 line. Rejected: a guarded
import at the top of a module (every run and every test would attempt it); entry-point plugins (one
engine doesn't need them).

### D3 · We choose the device ourselves, with PaddleX's own check

The check is `paddle.device.is_compiled_with_cuda()` and `paddle.device.cuda.device_count() > 0`,
the same one PaddleX uses for its default device. Choosing it ourselves lets us print it and set
`enable_mkldnn` (R15–R17). Rejected: `device=None`, which lets PaddleOCR choose silently;
`nvidia-smi`, which says nothing about the installed Paddle build. Details: [notes.md#d3](notes.md#d3-device-detection-in-the-installed-paddle)

### D4 · Pages are RGB inside scanscribe and BGR at PaddleOCR (owner decision, 2026-11-16)

PaddleOCR's pipeline reads NumPy input as BGR, and the prototype passed RGB. Page sources yield RGB:
images through Pillow's `convert("RGB")`, PDF pages through `to_pil().convert("RGB")`, as the
prototype did. pypdfium2's raw buffer is BGR, so it is never used directly. Only the adapter flips to BGR (R18). Rejected:
keeping RGB for byte parity (keeps a known bug). Details: [notes.md#d4](notes.md#d4-paddleocr-reads-arrays-as-bgr)

### D5 · The output path comes from the resolved input name

For a folder, the output is `resolved.parent / (resolved.name + ".txt")`. For a file, it is
`input.with_suffix(".txt")`. Paths are compared after `resolve()` (R6, R10). Rejected:
`with_suffix` for folders (it turns `Vol.2` into `Vol.txt`); writing inside the folder (that moves
the output away from where prototype users expect it).

### D6 · Check everything before OCR; replace the output atomically at the end

1. Validate arguments and paths (R9, R10).
2. List the pages.
3. Pre-check every page: fully decode each image and read its size; read each PDF page's rendered
   width (R5, R7, R8).
4. Load the engine and OCR every page.
5. Write the text to a temp file `.<name>.<random>.tmp` in the output's directory, give it the old
   output's mode (or the umask default), and `os.replace` it onto the output.

Any failure deletes the temp file. Rejected: `Image.verify()` (checks only PNG and WebP data);
writing page by page (partial file); `write_text` on the output (truncates the old file first);
skipping bad pages (owner's choice, 2026-11-16). Details: [notes.md#d6](notes.md#d6-what-pillows-verify-checks)

### D7 · Exit codes 0, 1, 2 and 130

0 means success. 2 means a usage error: argument and path checks call `parser.error()`, which
prints argparse's two-line format. 1 means any other error, and 130 means Ctrl-C (R20). `run`
catches argparse's `SystemExit` and returns its code. After parsing, it catches every `Exception`,
collapses the message to one line of at most 300 characters, prints the R12 line and returns 1.
With `SCANSCRIBE_DEBUG=1` it re-raises instead, for a full traceback. Rejected: listing the
exception types to catch (misses `OSError` and others).

### D8 · Empty inputs are errors

A run with no pages has nothing useful to write, and an empty output file looks like a success
downstream. pypdfium2 (5.13.0 in the prototype, 5.15.2 as locked here) refuses to open a zero-page PDF, so both "can't
open" and "0 pages" give the R7 error. Rejected: writing an empty file, as the prototype did.
Details: [notes.md#d8](notes.md#d8-zero-page-pdfs-in-pypdfium2)

### D9 · Fixtures are generated in tmp_path; the fake engine reads colors

Each slice is a solid color from a small palette. The fake engine returns the name of the palette
color nearest to the slice's center pixel, which absorbs JPEG shifts in Pillow-written PDFs, so
order tests need no real OCR. Rejected: committed binary fixtures (more to review, and real scans
could slip in). Details: [notes.md#d9](notes.md#d9-fake-engine-and-fixtures)

## Assumptions

- Keeping all the text in memory is fine: a few hundred pages make a few MB.
- An existing output file is replaced without asking, as in the prototype.
- `--lang` and `--device` are passed to PaddleOCR unchecked. A bad value gives PaddleOCR's own
  message on the R12 line.
- The adapter keeps the prototype's three PaddleOCR flags (`use_doc_orientation_classify`,
  `use_doc_unwarping`, `use_textline_orientation`), all `False`.
- An output path that is a symlink is replaced by a regular file, not written through.
- Two runs writing the same output each finish with a complete file; the last rename wins.

## Risks

- The OCR text differs from the prototype's. `uv.lock` pins the same Paddle versions as the
  prototype and only pypdfium2 differs, so a diff mostly measures D4. Mitigation: the manual check
  includes a color page. A page reads worse when a word the prototype got right is wrong. Phase 02
  then stays blocked until the owner reverses D4 through a plan update or accepts the result
  ([notes.md#manual-check](notes.md#manual-check)).
- Paddle APIs change (`device_count`, or `rec_texts`, the result key that holds recognized lines) →
  `uv.lock` pins the versions, and phase 02 task 1.1 re-checks the source references in notes.md.
- mypy strict fails on untyped libraries (pypdfium2 5.15.2 ships no `py.typed`) → narrow
  `ignore_missing_imports` overrides for those modules only.
- A test imports real Paddle on a machine with an extra → tests force the import to fail through
  `sys.modules` and clear the cached adapter module (phase 02 tasks 1.2, 1.3).

## Rollout & rollback

No deployment. Each phase merges to `main` through its own PR. Until phase 02 merges, `main` has
the pipeline but no `scanscribe` command, and the README still says "under construction". To roll
back, revert the PR. The prototype stays usable outside this repository. The downstream
`study-book-chapter` skill reads whatever text it is given, and the format (R3) is unchanged, so it
needs no change.

## Open questions

- None

## Impact

- Packages / directories: `src/scanscribe/`, `tests/`, `pyproject.toml`, `README.md`,
  `docs/decision-log.md` (one line for the BGR change and the new edge-case behavior), and the
  Status line in `AGENTS.md`.
- Data: none. Book inputs and outputs stay local and ignored by Git.
- Jobs / APIs: the CLI surface (R19) and the output format (R3). The CI workflow doesn't change.

## Links

- [#4](https://github.com/geosp/scanscribe/issues/4): the issue this plan delivers.
- [docs/decision-log.md](../../decision-log.md): records the two exclusive extras, fake-engine CI
  and that book material never enters Git, tests or logs.
- [docs/reviews/README.md](../../reviews/README.md): how reviews gate a phase, and the owner's
  manual OCR check that closes it.

## Phases

| Phase | Title | Status | Tasks | Delivers |
| --- | --- | --- | --- | --- |
| 01 | [Page pipeline and CLI on a fake engine](phases/01-pipeline-and-cli.md) | draft | 0/12 | R1–R12, R20 |
| 02 | [PaddleOCR adapter and the scanscribe command](phases/02-paddleocr-adapter.md) | draft | 0/8 | R13–R19 |

## Decision log

None yet. Changes made after approval are logged here.
