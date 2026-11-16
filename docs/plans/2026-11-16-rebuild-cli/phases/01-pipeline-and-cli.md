---
phase: 1
title: Page pipeline and CLI on a fake engine
status: draft
branch: null
base: null
delivers: [R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12]
design_review: { status: none, rounds: 0, last: null }
impl_review: { status: none, rounds: 0, last: null }
approved: null
---

# Phase 01 · Page pipeline and CLI on a fake engine

## Goal

`scanscribe.cli.run(argv, engine_factory)` turns a folder or a PDF into the prototype's output
format, with every edge case handled. It is fully tested with a fake engine. This phase adds no
Paddle code and no console command; phase 02 adds both.

## Tasks

### 1. Interface and test scaffolding

- [ ] 1.1 Add `src/scanscribe/engine.py` with the `OcrEngine` protocol, the `EngineFactory` type
  `(lang, device: str | None) -> OcrEngine`, and the error classes `ScanscribeError`, `UsageError`
  and `InputError` (D1, D7). Verify: `uv run mypy` passes.
- [ ] 1.2 Add `tests/conftest.py` with `FakeEngine` and fixture builders for image folders,
  multi-page PDFs, a zero-page PDF, and corrupt and truncated images, all in `tmp_path` (D9).
  Verify: a smoke test builds each fixture, and `git status` shows no new binary files.

### 2. Page sources (`src/scanscribe/pages.py`)

- [ ] 2.1 List a folder's pages: regular files only, supported extensions in any case, no dotfiles,
  natural order with the exact name as tiebreaker. Split on `\d+` and convert only the digit parts
  (R1). Verify: tests for `page2` before `page10`, upper-case extensions, a subfolder named `x.png`,
  `notes.txt`, `._page1.jpg`, and `a.png`/`A.png` in a stable order.
- [ ] 2.2 Build a page source for each input kind. It exposes the page count and labels (file name,
  or `page N` for PDFs) before any OCR, and yields RGB arrays. Images are header-checked up front
  with `Image.open`, then loaded with `convert("RGB")`. PDFs are opened once, counted, and rendered
  at `scale = dpi / 72` (R2, R7, R8, D6, D8). Verify: tests for RGBA, grayscale and palette images;
  `--dpi 144` on a 72 px page giving 144 px; an empty folder, a zero-page PDF, a text file and a
  corrupt image each raising `InputError` with the path; a fake document with `len == 0`.
- [ ] 2.3 Add `split_columns(image, n)` with the prototype's edges, raising `InputError` when the
  image is narrower than `n` px (R4, R5). Verify: widths 33/34/33 for 100 px and n=3; n=1 returns
  the image unchanged; a 3 px image with n=4 raises.
- [ ] 2.4 Add a mypy override (`ignore_missing_imports`) for `pypdfium2` only if mypy reports it
  untyped. Verify: `uv run mypy` passes.

### 3. Output (`src/scanscribe/output.py`)

- [ ] 3.1 Add `format_pages(pages: list[list[str]]) -> str` (R3). Verify: the exact string from R3's
  scenario; a single page; a page with no lines last.
- [ ] 3.2 Add `default_output_path(input)` (R6, D5). Verify: `book.v2.pdf`, the folder `Vol.2`,
  `.` inside a folder, and a trailing slash.

### 4. CLI (`src/scanscribe/cli.py`)

- [ ] 4.1 Build the argparse parser with the R19 options and defaults (`prog="scanscribe"`). Add
  validators that reject `--columns` and `--dpi` below 1, a missing input, a missing output directory,
  and an output that resolves to the input (R9, R10). Verify: tests for each, asserting exit 2 and that
  the engine factory is never called.
- [ ] 4.2 Add `run(argv, engine_factory) -> int` in the D6 order: validate, build the page source,
  load the engine, OCR each page slice by slice, format, then write once. Progress goes to stderr
  (R11). Verify: end-to-end tests with `FakeEngine` on a 3-image folder and a 2-page PDF, checking
  the exact output, page and slice order, `--columns 2`, an empty stdout, and the stderr lines.
- [ ] 4.3 Map errors to exit codes and one-line messages (D7, R12): `InputError` and engine exceptions
  give 1, usage errors give 2, and there is never a traceback. Never create or touch the output file
  on failure (R7, R8). Verify: tests for an empty folder, a corrupt third image (the factory is not
  called), a `FakeEngine` that raises on page 2 with an existing output file left byte-identical,
  and a slice narrower than `--columns`.

### 5. Phase checks

- [ ] 5.1 Run the AGENTS.md checks locally, then the suite once from a clean clone with only
  `uv sync --locked` (docs/reviews/README.md). Verify: all commands exit 0, and the clean-clone
  run's commit SHA is noted for the impl review.
