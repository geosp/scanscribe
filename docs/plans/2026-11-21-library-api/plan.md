---
title: A public library API for scanscribe
status: draft
created: 2026-11-21
updated: 2026-11-21
design_review: { status: none, rounds: 0, last: null }
approved: null
adr_review: null
---

# A public library API for scanscribe

## Summary

scanscribe can be driven only as a command today. A separate MCP server, `scanscribe-mcp`, will
need to call it as a library: keep one engine loaded across jobs, get the text back, show
per-page progress and stop a job between pages. This plan adds a small public API: `transcribe`,
`ocr_source`, an `on_device` hook on `load_engine`, `__all__` and a `py.typed` marker. The CLI
moves onto the same API, so both paths run the same loop. The CLI's behavior doesn't change
(the rebuild-cli plan's twenty requirements), and its tests stay as they are. After the merge the owner tags
`v0.1.0` for the MCP repo to pin.

```text
scanscribe CLI ─┐
                ├─> transcribe / ocr_source ─> open_source ─> engine.recognize ─> format_pages
scanscribe-mcp ─┘          (on_page progress, stop by raising)
```

The main risk is that the refactor changes CLI behavior. The existing CLI tests are the guard.

## Why

The owner chose to expose scanscribe over MCP with
[mcp-service-kit](https://github.com/geosp/mcp-service-kit), in a separate repository that follows
[pandoc-mcp](https://github.com/geosp/pandoc-mcp) (D3). `cli.convert()` takes an argparse
`Namespace`, prints progress to stderr and writes the output file itself, so a server can't
reuse it. A server runs OCR as background jobs. It needs the text, progress per page and a way to
cancel. It loads the engine once, because loading PaddleOCR takes seconds to minutes. Without a
supported API, the MCP repo would import private functions that may change.

## What changes

- New public functions `transcribe` and `ocr_source`, re-exported from `scanscribe` (R1–R5, D1).
- `load_engine` gets an optional `on_device` callback (R6).
- `scanscribe.__all__` lists the public names. `src/scanscribe/py.typed` ships in the wheel (R7,
  R8, D2).
- `cli.convert()` runs its loop through `ocr_source`. The output and messages are unchanged.
- README gets a "Use as a library" section. The decision log records the public API and the
  separate MCP repo (D3).

### Non-goals

- Any MCP code: tools, jobs, uploads, HTTP, Docker. These belong to the `scanscribe-mcp` plan.
- New OCR behavior, options or output format.
- A test helper package (a fake engine) for other projects. The `OcrEngine` protocol has one
  method, so a dependent project writes its own fake.
- Thread safety. The API makes no promise about calling one engine from two threads; the server
  will run one job at a time per engine.

## Terms

- **Public API**: the names in `scanscribe.__all__`. Changes to them follow semantic versioning
  from `v0.1.0`; every other module attribute is internal.
- **Engine**: an object with `recognize(image) -> list[str]`, the `OcrEngine` protocol in
  `engine.py`. `load_engine(lang, device)` builds the PaddleOCR one.
- **Page source**: an opened, pre-checked input (`PageSource`) from `open_source`. Opening it
  checks every page before any OCR (the rebuild-cli plan's check-first rule).
- **Progress callback**: a function `on_page(page_number, total_pages)` called before each page.
- **The rebuild-cli plan**: [docs/plans/2026-11-16-rebuild-cli](../2026-11-16-rebuild-cli/plan.md),
  which defines the CLI's requirements and decisions. Its check-first rule: every page and path is checked before the engine loads, and the output is replaced only at the end.
- **scanscribe-mcp**: the planned MCP server repository that will depend on this API.

## Requirements

### R1 · `transcribe` returns the same text the CLI writes

`transcribe(path, engine, dpi=…, columns=…)` must return exactly the text the CLI would write for
the same input and options.
- **Given** a folder of three pages, **when** `transcribe` runs with the fake engine, **then** its
  result equals the file `scanscribe` writes for that folder.
- **Given** a two-page PDF and `columns=2`, **when** `transcribe` runs, **then** its result equals
  the CLI's output with `--columns 2`.

### R2 · The library never writes files or stdout

`transcribe` and `ocr_source` must never create files or write to stdout or stderr.
- **Given** a folder input in `tmp_path`, **when** `transcribe` runs, **then** stdout and stderr
  are empty and `tmp_path` holds the same files as before.

### R3 · Progress is reported before each page

`ocr_source` must call `on_page(n, total)` once per page, in order, before that page is
recognized.
- **Given** a three-page source, **when** `ocr_source` runs, **then** `on_page` receives `(1, 3)`,
  `(2, 3)`, `(3, 3)`, and each call comes before that page's first `recognize` call.

### R4 · An exception from the progress callback stops the run

If `on_page` raises, `ocr_source` must stop and let the exception propagate unchanged.
- **Given** `on_page` raises on page 2, **when** `ocr_source` runs, **then** page 2 is never
  recognized and the caller gets the same exception object.

### R5 · Invalid arguments are usage errors

`transcribe` and `ocr_source` must raise `UsageError` when `columns` or `dpi` is below 1, or when
the input path doesn't exist. They raise it before any page is read.
- **Given** `columns=0`, **when** `transcribe` runs, **then** it raises `UsageError` and the
  engine is never called.
- **Given** a path that doesn't exist, **when** `transcribe` runs, **then** it raises `UsageError`
  naming the path.

### R6 · `load_engine` can report the device to a callback

When `on_device` is given, `load_engine` must pass the resolved device to it instead of printing
`Using device: …`.
- **Given** fake Paddle modules with no GPU, **when** `load_engine("en", None, on_device=cb)` runs, **then** `cb` receives `"cpu"` and nothing is printed.
- **Given** no `on_device`, **when** `load_engine` runs, **then** `Using device: <device>` is
  printed to stderr, as today.

### R7 · `__all__` names the public API and importing it never imports Paddle

`import scanscribe` must expose every name in `scanscribe.__all__` without importing `paddle`,
`paddleocr` or `scanscribe.paddle_engine`.
- **Given** a fresh interpreter, **when** it runs `from scanscribe import *`, **then** every name
  in `__all__` is bound and none of those three modules is in `sys.modules`.

### R8 · The wheel is typed

The built wheel must contain `scanscribe/py.typed`.
- **Given** `uv build`, **when** the wheel's file list is read, **then** it includes
  `scanscribe/py.typed`.

## Decisions

### D1 · Two functions: `ocr_source` for control, `transcribe` for convenience

`ocr_source(source, engine, columns, on_page)` is the loop now in `cli.convert()` and returns
the pages' lines. `transcribe(path, engine, *, dpi, columns, on_page)` opens the source, runs
`ocr_source` and returns `format_pages(...)`. The CLI uses `ocr_source`, because it must open the
source before it loads the engine (the check-first rule). A server with a loaded engine calls
`transcribe`. Cancelling means raising from `on_page`, so no separate cancel token is needed.
Rejected: one `transcribe` that takes an engine factory (it hides the loaded-engine reuse a server
needs); a cancel-event argument (it's a second way to do what raising already does).

### D2 · The public API is `__all__` in `scanscribe/__init__.py`, typed with `py.typed`

`__init__.py` re-exports the public names from `api`, `engine`, `pages` and `output`, so callers
write `from scanscribe import transcribe`. `py.typed` lets the MCP repo's strict mypy check calls
against it. Rejected: a separate `scanscribe.api` namespace as the only entry point (longer
imports, with no gain); leaving it untyped (the MCP repo would need `ignore_missing_imports`).

### D3 · The MCP server lives in a separate repository

`scanscribe-mcp` depends on this package through a pinned Git tag. mcp-service-kit needs Python
3.11 or later, while scanscribe supports 3.10. The server also brings its own dependencies
(FastMCP, Starlette), a different security model and a Docker deployment. Rejected: an `mcp`
extra in this repository (Python markers, two test setups in CI, and server dependencies in the
CLI's lock file). It costs a tag per API change, and the dependent project must repeat the Paddle
index and `conflicts` settings, because uv doesn't inherit `[tool.uv.sources]` from a dependency.

## Assumptions

- uv_build includes every file in `src/scanscribe/`, so `py.typed` reaches the wheel with no
  config. Task 1.3 checks this.
- The version stays `0.1.0`. Nothing has been tagged or published, so the first tag can carry the
  API.
- R5's checks repeat argparse's `--columns`/`--dpi` check and the CLI's input path check. The CLI still checks first, so its messages and exit codes don't change.

## Risks

- The refactor changes CLI output or the check-first order → every existing `test_cli.py` test runs
  unchanged. R1 compares the library and the CLI directly.
- A later change breaks the public API without notice → `__all__` plus R7's test make the surface
  explicit; README states the semver promise.
- The MCP repo's pinned copy of the Paddle install settings drifts from this repo's → README
  documents the settings to copy (D3).

## Rollout & rollback

Merge, then the owner tags `v0.1.0` on the merge commit:
`git tag v0.1.0 <merge-sha> && git push origin v0.1.0`. Rollback is a revert of the PR. No one
depends on the API before the tag exists. The `study-book-chapter` skill reads the CLI's output
file, which doesn't change.

## Open questions

- None

## Impact

- Packages / directories: `src/scanscribe/` (new `api.py` and `py.typed`; `__init__.py`,
  `cli.py`, `engine.py`), `tests/`, `README.md`, `docs/decision-log.md`
- Data: none
- Jobs / APIs: the new Python API; the `scanscribe` command is unchanged

## Links

- Issue [#9](https://github.com/geosp/scanscribe/issues/9) — this work
- [ADR-0001](../../adrs/0001-ocr-engine-behind-an-interface.md) — the OCR engine sits behind a
  one-method interface and Paddle is imported only when OCR starts; this API keeps both
- [rebuild-cli plan](../2026-11-16-rebuild-cli/plan.md) — the CLI's requirements, which stay
  unchanged
- [pandoc-mcp](https://github.com/geosp/pandoc-mcp) — the layout the MCP server will follow

## Phases

| Phase | Title | Status | Tasks |
| --- | --- | --- | --- |
| 01 | [Library API and CLI on top of it](phases/01-library-api.md) | draft | 0/8 |

## Decision log
