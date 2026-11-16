---
title: Rebuild the scanscribe CLI from the ocr-pdf prototype
status: draft
created: 2026-11-16
updated: 2026-11-16
design_review: { status: changes-requested, rounds: 1, last: 2026-11-16 }
approved: null
adr_review: null
---

# Rebuild the scanscribe CLI from the ocr-pdf prototype

## Summary

scanscribe has a project skeleton but no command. This plan rebuilds the `ocr-pdf` prototype's CLI
as `scanscribe`. Inputs, options and the `--- Page N ---` output format stay the same (R1–R4,
R19). The OCR engine moves behind an interface, and Paddle is imported lazily (D1, D2), so CI and
the tests never install PaddlePaddle. The device is chosen explicitly and printed (D3). Images
reach PaddleOCR in the BGR order it expects (D4). The prototype's tracebacks and silent mistakes
become clear errors, raised before OCR starts (R5–R12).

Phase 01 builds the pipeline and the CLI against a fake engine. Phase 02 adds the PaddleOCR
adapter, the `scanscribe` command and the owner's manual check on GPU and CPU. The main risk is
changed output: the BGR fix and newer Paddle versions can change the text. The manual check diffs
it against the prototype's output and records every difference.

```text
args ─▶ validate (R9, R10) ─▶ list pages (R1, R2) ─▶ pre-check pages (R7, R8) ─▶ load engine (D2, D3)
     ─▶ per page: split columns (R4) ─▶ engine.recognize ─▶ format (R3) ─▶ write once (D6)
```

## Why

The prototype works on the owner's GPU machine, but it depends on the GPU build only, has no
tests, and can't run in CI. Several inputs also fail badly. A folder named `Vol.2` writes to
`Vol.txt`. An empty folder writes an empty file. A missing output directory crashes only after the
whole book has been OCR'd. The repository's CI, review rules and `gpu`/`cpu` extras are now in
place, so the CLI comes next. The full behavior inventory is in [notes.md#prototype](notes.md#prototype).

## What changes

- New code in `src/scanscribe/`: page sources, column split, output formatting, the CLI, the
  engine interface and the PaddleOCR adapter, with tests in `tests/`.
- A console command, `scanscribe`, that works like the prototype's `ocr-pdf`.
- **BREAKING** (against the prototype): images are passed as BGR (D4). `--columns` or `--dpi`
  below 1 are rejected (R9). Empty inputs are errors (R7).
- The README gains a Usage section. `pyproject.toml` gains the script entry and mypy overrides.

### Non-goals

- Single image files as input. A file input is always opened as a PDF.
- EXIF rotation, multi-frame TIFFs and layout detection. Columns stay equal-width slices.
- Streaming output page by page, or resuming a partial run.
- A `python -m scanscribe` entry or a `--version` flag.
- Real OCR in CI. Real OCR stays a manual owner check (docs/reviews/README.md).

## Terms

- **Prototype**: the `ocr-pdf` tool, outside this repository. It is reference material only.
- **Page source**: the ordered pages of one input, from a folder of images or a PDF.
- **Page image**: one page as an RGB array of height × width × 3 bytes.
- **Slice**: one of the N equal-width vertical strips that `--columns N` cuts a page into.
- **Engine**: anything that turns a slice into a list of text lines (`OcrEngine`, D1).
- **Fake engine**: the test double for the engine. It never runs OCR.
- **Adapter**: the engine that wraps PaddleOCR (`PaddleOcrEngine`).
- **Base install**: `uv sync` with no extra, as in CI. It has no PaddlePaddle or PaddleOCR.
- **Extra**: the `gpu` or `cpu` optional dependency set. At most one is installed.
- **Device string**: PaddleOCR's `device` value, such as `gpu:0` or `cpu`.
- **Usage error**: a problem with the arguments, found before any page is read. It exits 2.
- **Input error**: a problem with the input's content or with the engine. It exits 1.

## Requirements

### R1 · Folder pages are image files in natural order

A folder's pages are only the regular, non-hidden files directly inside it with a supported extension (`.png .jpg .jpeg .tif .tiff .bmp .webp`, any case), in natural filename order.
- **Given** `page10.png`, `page2.png` and `page1.PNG`, **when** the folder is read, **then** the order is `page1.PNG`, `page2.png`, `page10.png`.
- **Given** a subfolder named `x.png`, `notes.txt` and `._page1.jpg`, **when** the folder is read, **then** none of them is a page.
- **Given** `a.png` and `A.png`, **when** the folder is read twice, **then** both runs give the same order.

### R2 · PDF pages are rendered at the requested DPI

A file input is opened as a PDF, and each page is rendered at `--dpi` (default 200) before OCR.
- **Given** a 1-inch-wide PDF page, **when** it is read with `--dpi 144`, **then** the page image is 144 px wide.

### R3 · Output keeps the prototype's format

Each page is written as `--- Page N ---` followed by its lines, pages are separated by one blank line, nothing follows the last page, and the file is UTF-8.
- **Given** two pages with lines `a`,`b` and none, **when** the run finishes, **then** the file is exactly `--- Page 1 ---\na\nb\n\n--- Page 2 ---\n`.

### R4 · Columns are read left to right

With `--columns N`, each page is cut into N slices of equal width (±1 px), and their lines are written left to right under one page marker.
- **Given** `--columns 2` and a page whose left half reads `L` and right half `R`, **when** it is OCR'd, **then** the page's lines are `L` then `R`.
- **Given** `--columns 3` and a 100 px page, **when** it is split, **then** the slice widths are 33, 34 and 33 px.

### R5 · A page narrower than its column count is an input error

A page narrower than `--columns` pixels ends the run with an input error that names the page.
- **Given** `--columns 4` and a 3 px wide `p1.png`, **when** the run starts, **then** it exits 1 naming `p1.png`, and no output file is written.

### R6 · The default output sits next to the input and keeps its name

Without `-o`, a PDF's output is its path with the suffix replaced by `.txt`, and a folder's output is the sibling file `<folder name>.txt`.
- **Given** `scans/book.v2.pdf`, **when** no `-o` is given, **then** the output is `scans/book.v2.txt`.
- **Given** the folder `scans/Vol.2/`, **when** no `-o` is given, **then** the output is `scans/Vol.2.txt`, not `scans/Vol.txt`.
- **Given** the input `.` run from `scans/ch1`, **when** no `-o` is given, **then** the output is `scans/ch1.txt`.

### R7 · An input with no pages is an input error

A folder with no page files, or a PDF that has no pages or can't be opened, ends the run with an input error and writes no output file.
- **Given** an empty folder, **when** the run starts, **then** it exits 1 with "no page images found", and no `.txt` exists.
- **Given** a zero-page PDF or a text file as input, **when** the run starts, **then** it exits 1 with a message naming the file.

### R8 · An unreadable page aborts the run and leaves the output untouched

A page that can't be read ends the run with an input error naming the page, and the output file is neither created nor changed.
- **Given** a folder whose third file is a corrupt `.png`, **when** the run starts, **then** it exits 1 naming that file before the engine is loaded.
- **Given** an existing output file and a page that fails during OCR, **when** the run aborts, **then** the existing file is byte-identical.

### R9 · `--columns` and `--dpi` must be at least 1

A `--columns` or `--dpi` value below 1 is a usage error.
- **Given** `--columns 0` or `--dpi -5`, **when** the command runs, **then** it exits 2 with argparse's usage message.

### R10 · Bad input or output paths are usage errors

A missing input, a missing output directory, or an output that resolves to the input is a usage error, raised before any page is read.
- **Given** `-o missing-dir/out.txt`, **when** the command runs, **then** it exits 2 and no page is read.
- **Given** `-o book.pdf` for the input `book.pdf`, **when** the command runs, **then** it exits 2 and the PDF is untouched.

### R11 · Progress goes to stderr, never stdout

All progress and messages go to stderr, including `Processing page N...` for each page and the output path at the end, and stdout stays empty.
- **Given** a 2-page run, **when** it finishes, **then** stdout is empty and stderr has `Processing page 1...` then `Processing page 2...`.

### R12 · Errors are one line, never a traceback

Every error is printed as one stderr line that starts with `scanscribe: error:`, and no traceback is shown.
- **Given** an engine that raises on page 2, **when** the run fails, **then** stderr ends with one `scanscribe: error:` line and contains no `Traceback`.

### R13 · The base install never imports Paddle

Importing scanscribe, running `scanscribe --help` and running the test suite never import `paddle` or `paddleocr`.
- **Given** the base install, **when** the test suite runs, **then** it passes and `paddle` and `paddleocr` were never imported.

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

## Decisions

### D1 · A one-method engine protocol, injected into the CLI

`OcrEngine` is a `typing.Protocol` with one method, `recognize(image) -> list[str]`, which takes an
RGB slice. `cli.run(argv, engine_factory)` takes a factory `(lang, device) -> OcrEngine`: tests pass
the fake engine, and `main()` passes the PaddleOCR loader. Rejected: an abstract base class (the
fake would have to inherit from it for no gain); passing PaddleOCR's result objects through (that
would tie the tests to Paddle's result shape).

### D2 · Paddle is imported only inside the loader

`load_engine` imports `scanscribe.paddle_engine` inside the function. An `ImportError` naming
`paddle`, `paddleocr` or one of their submodules becomes `EngineMissingError` (R14). Any other
import error propagates. Rejected: a guarded import at the top of a module (every run and every
test would attempt it); entry-point plugins (one engine doesn't need them).

### D3 · We choose the device ourselves, with PaddleX's own check

The check is `paddle.device.is_compiled_with_cuda()` and `paddle.device.cuda.device_count() > 0`,
the same one PaddleX uses for its default device. Choosing it ourselves lets us print it and set
`enable_mkldnn` (R15–R17). Rejected: `device=None`, which lets PaddleOCR choose silently;
`nvidia-smi`, which says nothing about the installed Paddle build. Details: [notes.md#d3](notes.md#d3-device-detection-in-the-installed-paddle)

### D4 · Pass BGR, not RGB (owner decision, 2026-11-16)

PaddleOCR's OCR pipeline reads NumPy input as BGR. The prototype passed RGB, which swapped red and
blue, so the adapter now flips the channels (R18). Rejected: keeping RGB for byte parity with the
prototype (that keeps a known bug). Details: [notes.md#d4](notes.md#d4-paddleocr-reads-arrays-as-bgr)

### D5 · The output path comes from the resolved input name

For a folder, the output is `resolved.parent / (resolved.name + ".txt")`. For a file, it is
`input.with_suffix(".txt")`. Paths are compared after `resolve()` (R6, R10). Rejected:
`with_suffix` for folders (it turns `Vol.2` into `Vol.txt`); writing inside the folder (that moves
the output away from where prototype users expect it).

### D6 · Check everything before OCR; write once at the end

The order is: validate arguments, list the pages, open every page's header, load the engine, then
OCR. The text is held in memory and written once after the last page, as the prototype did, so a
failed run never leaves a partial file. Rejected: writing page by page (it leaves a partial file);
skipping bad pages (the owner chose to abort, 2026-11-16).

### D7 · Exit codes 0, 1 and 2

0 means success, 2 a usage error (argparse's convention), and 1 an input error or any engine
failure. `run` catches `ScanscribeError` and the exceptions raised by Pillow, pypdfium2 and the
engine, then prints the R12 line. Rejected: letting exceptions escape as tracebacks, as the
prototype did.

### D8 · Empty inputs are errors

A run with no pages has nothing useful to write, and an empty output file looks like a success
downstream. pypdfium2 5.13 refuses to open a zero-page PDF, so both "can't open" and "0 pages" give
the R7 error. Rejected: writing an empty file, as the prototype did. Details: [notes.md#d8](notes.md#d8-zero-page-pdfs-in-pypdfium2)

### D9 · Fixtures are generated in tmp_path; the fake engine reads colors

Each slice is a solid color, and the fake engine returns a line naming that color, so the order
tests need no real OCR. Images and PDFs come from Pillow, and the zero-page PDF is hand-written
bytes. Rejected: committed binary fixtures (more to review, and real scans could slip in).
Details: [notes.md#d9](notes.md#d9-fake-engine-and-fixtures)

## Assumptions

- Keeping all the text in memory is fine: a few hundred pages make a few MB.
- An existing output file is overwritten without asking, as in the prototype.
- Hidden files such as macOS `._page1.jpg` are skipped (R1). The prototype included them and
  crashed.
- `--lang` and `--device` are passed to PaddleOCR unchecked. A bad value gives PaddleOCR's own
  message and exit 1 (D7).
- The adapter keeps the prototype's three PaddleOCR flags (`use_doc_orientation_classify`,
  `use_doc_unwarping`, `use_textline_orientation`), all `False`.
- The pre-check (D6) reads image headers only. A file truncated after its header still fails during
  OCR, and R8 covers that.

## Risks

- The output differs from the prototype's (D4, newer locked versions) → phase 02's manual check
  diffs them on the same input and device and records the result.
- Paddle APIs change (`device_count`, the `rec_texts` key) → `uv.lock` pins the versions, unit tests
  use fake modules, and phase 02 re-checks the sources.
- mypy strict fails on untyped libraries (pypdfium2 5.15.2 ships no `py.typed`) → narrow
  `ignore_missing_imports` overrides for those modules only.
- A test imports real Paddle on a machine that has an extra installed → the R13 test catches it.

## Rollout & rollback

No deployment. Each phase merges to `main` through its own PR. Until phase 02 merges, `main` has
the pipeline but no `scanscribe` command, and the README still says "under construction". To roll
back, revert the PR. The prototype stays usable outside this repository.

## Open questions

- None

## Impact

- Packages / directories: `src/scanscribe/`, `tests/`, `pyproject.toml`, `README.md`,
  `docs/decision-log.md`.
- Data: none. Book inputs and outputs stay local and ignored by Git.
- Jobs / APIs: the CLI surface (R19) and the output format (R3). The CI workflow doesn't change.

## Links

- [#4](https://github.com/geosp/scanscribe/issues/4): the issue this plan delivers.
- [docs/decision-log.md](../../decision-log.md): records the two exclusive extras, fake-engine CI
  and the no-book-material rule.
- [docs/reviews/README.md](../../reviews/README.md): the gate review rules and the manual OCR check
  that closes a phase.

## Phases

| Phase | Title | Status | Tasks |
| --- | --- | --- | --- |
| 01 | Page pipeline and CLI on a fake engine | draft | 0/12 |
| 02 | PaddleOCR adapter and the scanscribe command | draft | 0/8 |

## Decision log
