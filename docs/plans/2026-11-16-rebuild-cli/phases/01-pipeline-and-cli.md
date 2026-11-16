---
phase: 1
title: Page pipeline and CLI on a fake engine
status: in-progress
branch: feat/4-pipeline-and-cli
base: 7594141b5dcc874b13cf03c8b7b80369fbb1b80a
delivers: [R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R20]
design_review: { status: passed, rounds: 2, last: 2026-11-16 }
impl_review: { status: none, rounds: 0, last: null }
approved: 2026-11-16
---

# Phase 01 · Page pipeline and CLI on a fake engine

## Goal

`scanscribe.cli.run(argv, engine_factory)` turns a folder or a PDF into the prototype's output
format, with every edge case handled. It is fully tested with a fake engine. This phase adds no
Paddle code and no console command; phase 02 adds both.

## Tasks

### 1. Interface and test scaffolding

- [x] 1.1 Add `src/scanscribe/engine.py` with the `OcrEngine` protocol, the `EngineFactory` type
  `(lang, device: str | None) -> OcrEngine`, and the errors `ScanscribeError`, then `UsageError` and
  `InputError` under it (D1, D7). Verify: `uv run mypy` passes.
- [x] 1.2 Add `tests/conftest.py` with `FakeEngine`, which names the nearest palette color, and
  fixture builders in `tmp_path` (D9, [notes.md#d9](../notes.md#d9-fake-engine-and-fixtures)):
  image folders, multi-page PDFs, a red-page PDF, a zero-page PDF, `notes.dat`, a corrupt image, a
  truncated PNG and a truncated JPEG. Verify: a smoke test builds each fixture; `Image.load()` rejects
  both truncated images; `git status` shows no new binary files.

### 2. Page sources (`src/scanscribe/pages.py`)

- [ ] 2.1 List a folder's pages: regular files only, supported extensions in any case, no dotfiles,
  natural order: text parts case-folded, digit runs as numbers, the exact name as tiebreaker. Split on
  `\d+` and convert only the digit parts (R1). Verify: tests for `page2` before `Page10`, upper-case extensions, a subfolder named `x.png`,
  `notes.txt`, `._page1.jpg`, and `A.png` before `a.png`.
- [ ] 2.2 Build a page source for each input kind. Before any OCR it exposes each page's label (the
  file name, or `page N`) and checks every page (D6):
  - images: `Image.open`, `load()` to decode fully, read the size, then close;
  - PDFs: open once, count the pages, and read each page's rendered width,
    `ceil(width × DPI / 72)` as pypdfium2 computes it;
  - every page at least `--columns` px wide (R5).

  It then yields RGB arrays: images through `convert("RGB")`, PDF pages through
  `page.render(scale=dpi / 72).to_pil().convert("RGB")` (R2, R7, R8, D4, D8). Verify these tests:
  - RGBA, grayscale and palette images;
  - `--dpi 144` on a 72 px page gives 144 px;
  - the red-page PDF's center pixel is nearest to (255, 0, 0);
  - an empty folder, a zero-page PDF, `notes.dat`, a corrupt image, a truncated PNG and a truncated JPEG each raise
    `InputError` naming the path;
  - a fake document with `len == 0` raises `InputError`;
  - a page narrower than `--columns` raises `InputError` naming it;
  - 200 images under a lowered `RLIMIT_NOFILE` of 64 (POSIX only) don't exhaust file handles.
- [ ] 2.3 Add `split_columns(image, n)` with edges at `round(i * width / n)` (R4). Verify: widths
  33/34/33 for 100 px and n=3; n=1 returns the image unchanged.
- [ ] 2.4 Add a mypy override (`ignore_missing_imports`) for `pypdfium2` only if mypy reports it
  untyped. Verify: `uv run mypy` passes.

### 3. Output (`src/scanscribe/output.py`)

- [ ] 3.1 Add `format_pages(pages: list[list[str]]) -> str` (R3). Verify: the exact string from R3's
  scenario; a single page; an empty last page.
- [ ] 3.2 Add `default_output_path(input)` (R6, D5). Verify: `book.v2.pdf`, the folder `Vol.2`,
  `.` inside a folder, and a trailing slash.

### 4. CLI (`src/scanscribe/cli.py`)

- [ ] 4.1 Build the argparse parser with the R19 options and defaults (`prog="scanscribe"`). Add
  validators for `--columns` and `--dpi` below 1 (R9), and for the R10 path rules, each reported through `parser.error()`; writability is checked with
  `os.access`. `run` catches
  argparse's `SystemExit` and returns its code (D7). Verify: a test for each rule asserts that
  `run` returns 2 and the engine factory is never called; another asserts the defaults (`en`, 200, 1, no device) and that `--help` lists every R19 option
  and returns 0.
- [ ] 4.2 Add `run(argv, engine_factory) -> int` in the D6 order. After OCR, the text goes to a temp file
  `.<name>.<random>.tmp` in the output's directory, which gets the old output's mode (or the umask
  default) and is renamed with `os.replace`. Progress goes to stderr (R11). Verify:
  end-to-end tests with `FakeEngine` on a 3-image folder and a 2-page PDF check:
  - the exact output;
  - page and slice order with `--columns 2`;
  - an empty stdout and the stderr lines;
  - no temp file left behind;
  - an existing 0644 output keeps its mode;
  - an unwritable output directory returns 2 before the factory is called.
- [ ] 4.3 Map errors to exit codes (D7, R12, R20). After parsing, every `Exception` gives one
  `scanscribe: error:` line and 1; `KeyboardInterrupt` gives 130. The output is never created or
  changed on failure (R7, R8). Verify these tests:
  - an empty folder;
  - a corrupt third image, where the factory is never called;
  - a `FakeEngine` that raises on page 2, with an existing output left byte-identical;
  - `os.replace` patched to raise `OSError`;
  - a `FakeEngine` that raises `KeyboardInterrupt`;
  - a `FakeEngine` error with a 5-line message, which prints one line;

  each with no `Traceback` on stderr and no temp file left. A last test sets `SCANSCRIBE_DEBUG=1`
  and asserts the engine error is re-raised (D7).

### 5. Phase checks

- [ ] 5.1 Run the AGENTS.md checks locally, then the suite once from a clean clone with only
  `uv sync --locked` (docs/reviews/README.md). Verify: all commands exit 0; note the clean-clone
  run's commit SHA for the impl review.
