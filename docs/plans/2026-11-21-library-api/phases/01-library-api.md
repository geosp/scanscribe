---
phase: 1
title: Library API and CLI on top of it
status: draft
branch: null
base: null
delivers: [R1, R2, R3, R4, R5, R6, R7, R8]
design_review: { status: none, rounds: 0, last: null }
impl_review: { status: none, rounds: 0, last: null }
approved: null
---

# Phase 01 · Library API and CLI on top of it

## Goal

`from scanscribe import transcribe, load_engine` works and is typed. The CLI uses the same loop,
every existing test passes unchanged, and the README documents the API.

## Tasks

### 1. The API

- [ ] 1.1 Add `src/scanscribe/api.py` with `ProgressCallback`, `ocr_source` and `transcribe`
  (R2–R5, D1). It imports only `engine`, `pages` and `output`. Write `tests/test_api.py` first,
  using `FakeEngine` and the fixture builders in `tests/conftest.py`. Verify: tests for R2, R3,
  R4, R5 pass; `uv run mypy` clean.
- [ ] 1.2 Add the `on_device` keyword to `engine.load_engine` (R6). Verify: two tests using the
  fake Paddle modules from `tests/test_paddle_engine.py`, one with and one without `on_device`.
- [ ] 1.3 Add `__all__` and the re-exports to `scanscribe/__init__.py`, and an empty
  `src/scanscribe/py.typed` (R7, R8, D2). Add `scanscribe.api` and `from scanscribe import *` to
  the no-Paddle script in `tests/test_entry_point.py`. Verify: that test passes and checks every
  `__all__` name is bound; `uv build` and the wheel's file list shows `scanscribe/py.typed`.

### 2. The CLI on the API

- [ ] 2.1 Change `cli.convert()` to call `ocr_source` with an `on_page` that prints
  `Processing page N...` to stderr. It still opens the source before it loads the engine
  (the check-first rule). Verify: every test in `tests/test_cli.py` passes unchanged.
- [ ] 2.2 Add the R1 tests: `transcribe` on a folder and on a two-column PDF equals the CLI's
  output file for the same input. Verify: `uv run pytest tests/test_api.py`.

### 3. Docs and checks

- [ ] 3.1 README: a "Use as a library" section with a `transcribe` example, the public names,
  the semver promise from `v0.1.0`, and the Paddle settings a dependent project must copy (D3).
  Verify: the example's names match `__all__`.
- [ ] 3.2 `docs/decision-log.md`: one line for the public API and the separate MCP repo (D3).
  Verify: the line links this plan.
- [ ] 3.3 Run every check in AGENTS.md, then a manual run on the GPU machine with `--extra gpu`:
  `transcribe` on a small self-made PDF equals `uv run scanscribe` on it. Record the device.
  Verify: all checks pass; the device and result are noted in the PR.
