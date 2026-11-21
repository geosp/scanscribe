---
phase: 1
title: Library API and CLI on top of it
status: done
branch: feat/9-library-api
base: 49ecda09ad69340c5f02e869c0e0f7bca725aa27
delivers: [R1, R2, R3, R4, R5, R6, R7, R8, R9, R10]
design_review: { status: passed, rounds: 1, last: 2026-11-21 }
impl_review: { status: passed, rounds: 1, last: 2026-11-21 }
approved: 2026-11-21
---

# Phase 01 · Library API and CLI on top of it

## Goal

`from scanscribe import transcribe, load_engine` works and is typed. The CLI uses the same loop,
every existing test passes unchanged, and the README documents the API.

## Tasks

### 1. The API

- [x] 1.1 In `pages.py`, store `columns` on `PageSource`, and make `open_source` raise
  `UsageError` for `columns` or `dpi` below 1 and for a missing or uncheckable path (R5, R6, D4).
  Write the tests first in a new `tests/test_api.py`, using the fixture builders in
  `tests/conftest.py`. Verify: R5 and R6 tests pass; `tests/test_pages.py` passes, with one test now creating
  the file it passes to `open_source` (Decision log).
- [x] 1.2 Add `src/scanscribe/api.py` with `ProgressCallback`, `ocr_source` and `transcribe`
  (R2, R3, R4, R7, D1). It imports only `engine`, `pages` and `output`. Tests use `FakeEngine`.
  Verify: R2, R3, R4, R7 tests pass; `uv run mypy` clean.
- [x] 1.3 Add the `on_device` keyword to `engine.load_engine` (R8). Verify: two tests with the
  `fake_paddle` fixture from `tests/conftest.py`, one with and one without `on_device`.
- [x] 1.4 Set `__all__` in `scanscribe/__init__.py` to D2's list, and add an empty
  `src/scanscribe/py.typed` (R9, R10, D2). Add `scanscribe.api` and `from scanscribe import *` to
  the no-Paddle script in `tests/test_entry_point.py`, and assert `sorted(__all__)` equals D2's
  list. Verify: that test passes; by hand, `uv build` then the wheel's file list shows
  `scanscribe/py.typed`.

### 2. The CLI on the API

- [x] 2.1 Change `cli.convert()` to call `open_source`, the engine factory, then `ocr_source`
  with an `on_page` that prints `Processing page N...` to stderr (D1). Verify: every test in
  `tests/test_cli.py` passes unchanged.
- [x] 2.2 Add the R1 tests: `transcribe` on a folder and on a two-column PDF equals the CLI's
  output file for the same input. Verify: `uv run pytest tests/test_api.py`.

### 3. Docs and checks

- [x] 3.1 README: a "Use as a library" section with a `transcribe` example, the public names
  (D2), the semver promise from `v0.1.0`, one OCR job per process (Assumptions), and the Paddle
  install settings a dependent project must copy (D3). Verify: the example's names are in
  `__all__`.
- [x] 3.2 `docs/decision-log.md`: one line for the public API and the separate MCP repo (D3).
  Verify: the line links this plan.
- [x] 3.3 Run every check in AGENTS.md, then a manual run on the GPU machine with `--extra gpu`:
  `transcribe` on a small self-made PDF equals `uv run scanscribe` on it. Record the device.
  Verify: all checks pass; the device and result are noted in the PR.
