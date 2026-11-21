---
title: A public library API for scanscribe
status: closed
created: 2026-11-21
updated: 2026-11-21
design_review: { status: passed, rounds: 1, last: 2026-11-21 }
approved: 2026-11-21
adr_review: 2026-11-21
---

# A public library API for scanscribe

## Summary

scanscribe works only as a command today. A planned MCP server, `scanscribe-mcp`, in its own
repository, needs to call it as a library. It must keep one engine loaded across jobs, get the
text back, show per-page progress and stop a job between pages. This plan adds a small public API,
listed exactly in D2:
- `transcribe` and `ocr_source`, with a progress callback;
- argument checks in `open_source`;
- an `on_device` hook on `load_engine`;
- a `py.typed` marker.

Importing it must still never import Paddle (R9). The CLI's page loop moves onto `ocr_source`.
Its output, messages and exit codes stay as they are, and its tests stay unchanged. The README
documents the API and its semver promise. After the merge the owner tags `v0.1.0`.

```text
CLI:    open_source ──> load_engine ──> ocr_source ──> format_pages ──> write file
server: load_engine once;  per job: transcribe = open_source ─> ocr_source ─> format_pages
```

Main risk: the refactor changes CLI behavior. The unchanged CLI tests and R1 guard against it.

## Why

The owner chose to expose scanscribe over MCP from a separate repository (D3). `cli.convert()`
takes an argparse `Namespace`, prints progress to stderr and writes the output file itself, so a
server can't reuse it. A server runs OCR as background jobs. It needs the text back, progress per
page and a way to cancel. It loads the engine once, because loading PaddleOCR takes seconds to
minutes. Without a supported API, the MCP repo would import private functions that may change.

## What changes

- New public functions `transcribe` and `ocr_source` (R1–R4, R7, D1).
- `open_source` rejects bad arguments and a missing input with `UsageError` (R5, R6, D4).
- `PageSource` keeps the `columns` it was opened with, and `ocr_source` uses it (R7).
- `load_engine` gets an optional `on_device` callback (R8).
- `scanscribe.__all__` lists the public names. `py.typed` ships in the wheel (R9, R10, D2).
- `cli.convert()` runs its loop through `ocr_source` and prints its progress line from `on_page`.
- README gets a "Use as a library" section. `docs/decision-log.md` records the public API and the
  separate MCP repo (D3).

### Non-goals

- Any MCP code: tools, jobs, uploads, HTTP, Docker. These belong to the `scanscribe-mcp` plan.
- New OCR behavior, options or output format.
- A shared fake engine for other projects. `OcrEngine` has one method, so they write their own.
- Concurrency. One process runs one OCR job at a time (Assumptions).

## Terms

- **The owner**: the repository owner, who approves plans, merges and pushes tags.
- **Public API**: the names in `scanscribe.__all__` (D2). Changes to them follow semantic
  versioning from `v0.1.0`; every other module attribute is internal.
- **Engine**: an object with `recognize(image) -> list[str]` (the `OcrEngine` protocol).
  `load_engine(lang, device)` builds the PaddleOCR one. Tests use `FakeEngine` from
  `tests/conftest.py`, which names each slice's color instead of reading text.
- **Page source**: an opened input (`PageSource`) from `open_source(path, dpi, columns)`.
  Opening checks every page is readable and at least `columns` px wide; a failure raises
  `InputError`. This is the **check-first rule** from the rebuild-cli plan: bad input fails
  before the engine loads.
- **`columns`**: how many equal-width strips each page is cut into, read left to right; each
  strip is one `recognize` call. **`dpi`**: the resolution PDF pages are rendered at; images
  ignore it.
- **Page-marked text**: the output format, built by `format_pages`: `--- Page N ---` then the
  page's lines, pages separated by a blank line.
- **Progress callback**: `on_page(page_number, total_pages)`, called once per page.
- **The rebuild-cli plan**: [docs/plans/2026-11-16-rebuild-cli](../2026-11-16-rebuild-cli/plan.md),
  which defines the CLI's current behavior.
- **scanscribe-mcp**: the planned MCP server repository, built on mcp-service-kit (a small library
  for FastMCP servers with stdio and HTTP transports) in the layout of pandoc-mcp (the owner's MCP
  server for Pandoc conversions).
- **Paddle install settings**: the custom package index for `paddlepaddle-gpu` and the uv
  `conflicts` rule that keeps the `gpu` and `cpu` extras apart, in `pyproject.toml`.

## Requirements

### R1 · `transcribe` returns the same text the CLI writes

`transcribe(path, engine, dpi=200, columns=1)` must return exactly the text the CLI writes for
the same input and options.
- **Given** a folder of three pages, **when** `transcribe` runs with `FakeEngine`, **then** its result equals the file `scanscribe` writes for that folder.
- **Given** a two-page PDF and `columns=2`, **when** `transcribe` runs, **then** its result equals the CLI's output with `--columns 2`.

### R2 · scanscribe's own code never writes files or stdout

`transcribe`, `ocr_source` and `open_source` must never create files or print. An engine may log;
Paddle logs to stderr.
- **Given** a folder input in `tmp_path` and `FakeEngine`, **when** `transcribe` runs, **then** stdout and stderr are empty and `tmp_path` holds the same files as before.

### R3 · Progress is reported for each page before it is recognized

`ocr_source` must call `on_page(n, total)` once per page, in order, after the page is read and
before its first `recognize` call.
- **Given** a three-page source, **when** `ocr_source` runs, **then** `on_page` receives `(1, 3)`, `(2, 3)`, `(3, 3)`, each before that page's first `recognize` call.

### R4 · An exception from the progress callback stops the run

If `on_page` raises, the run must stop and the exception must reach the caller unchanged.
- **Given** `on_page` raises on page 2, **when** `ocr_source` runs, **then** page 2 is never recognized and the caller gets the same exception object.
- **Given** `on_page` raises during `transcribe` on a PDF, **when** the exception reaches the caller, **then** the source has been closed.

### R5 · `columns` or `dpi` below 1 is a usage error

`open_source` must raise `UsageError` when `columns` or `dpi` is below 1, before any page is read.
- **Given** `columns=0`, **when** `transcribe` runs, **then** it raises `UsageError` and the engine is never called.
- **Given** `dpi=0` and a PDF, **when** `open_source` runs, **then** it raises `UsageError`.

### R6 · A missing or uncheckable input is a usage error

`open_source` must raise `UsageError` naming the path when the input doesn't exist or can't be
checked, never a traceback.
- **Given** a path that doesn't exist, **when** `transcribe` runs, **then** it raises `UsageError` naming the path.
- **Given** an input inside a directory with no read permission, **when** `open_source` runs, **then** it raises `UsageError`.

### R7 · Pages are split with the `columns` the source was opened with

`ocr_source` must split pages with the source's own `columns`, so the width check always matches
the split.
- **Given** a source opened with `columns=2`, **when** `ocr_source` runs, **then** each page gives two `recognize` calls, left strip first.

### R8 · `load_engine` reports the device to a callback before it builds the engine

When `on_device` is given, `load_engine` must pass the resolved device to it instead of printing
`Using device: …`, before it builds the engine.
- **Given** the `fake_paddle` fixture with no GPU, **when** `load_engine("en", None, on_device=cb)` runs, **then** `cb` receives `"cpu"` before the fake PaddleOCR is constructed and nothing is printed.
- **Given** no `on_device`, **when** `load_engine` runs, **then** `Using device: <device>` is printed to stderr, as today.

### R9 · The public names are exactly D2's list, and importing them never imports Paddle

`scanscribe.__all__` must equal the list in D2. `from scanscribe import *` must never import
`paddle`, `paddleocr` or `scanscribe.paddle_engine`.
- **Given** a fresh interpreter, **when** it runs `from scanscribe import *`, **then** `sorted(__all__)` equals D2's list, every name is bound, and none of the three modules is in `sys.modules`.

### R10 · The wheel is typed

The built wheel must contain `scanscribe/py.typed`.
- **Given** `uv build`, **when** the wheel's file list is read, **then** it includes `scanscribe/py.typed`.

## Decisions

### D1 · Two functions: `ocr_source` for control, `transcribe` for convenience

- `ocr_source(source, engine, on_page=None) -> list[list[str]]` is the loop now in
  `cli.convert()`. It returns each page's lines.
- `transcribe(path, engine, *, dpi=200, columns=1, on_page=None) -> str` opens the source with
  `with`, runs `ocr_source` and returns `format_pages(...)`.

The CLI calls `open_source`, then loads the engine, then calls `ocr_source`, keeping the
check-first rule. Its `on_page` prints `Processing page N...`, the line it prints today at the
same point. Cancelling means raising from `on_page`. Rejected: a `transcribe` that takes an engine
factory (it hides the engine reuse a server needs); a cancel-event argument (a second way to do
what raising already does); a `columns` argument on `ocr_source` (it could differ from the
checked one, F2).

### D2 · The public API is `__all__` in `scanscribe/__init__.py`, typed with `py.typed`

`__all__` holds exactly these names:
- from `api`: `transcribe`, `ocr_source`, `ProgressCallback`;
- from `pages`: `open_source`, `PageSource`, `IMAGE_EXTENSIONS`;
- from `output`: `format_pages`;
- from `engine`: `load_engine`, `OcrEngine`, `PageImage`, `EngineFactory`, `ScanscribeError`,
  `UsageError`, `InputError`, `EngineMissingError`.

`__version__` stays a module attribute. `py.typed` lets the MCP repo's strict mypy check calls.
Rejected: also exporting `split_columns`, `natural_key` or `write_atomic` (no stated need, and each
would be frozen by semver); a `scanscribe.api`-only entry point (longer imports, no gain).

### D3 · The MCP server lives in a separate repository

`scanscribe-mcp` depends on this package through a pinned Git tag. mcp-service-kit needs Python
3.11 or later, while scanscribe supports 3.10. The server also brings FastMCP and Starlette, a
different security model and a Docker deployment. Rejected: an `mcp` extra in this repository. It
would need Python-version markers, CI on two setups, and server packages in the CLI's lock file.
The cost of this choice: each API change needs a new tag, and the MCP repo must copy the Paddle
install settings, because uv doesn't inherit `[tool.uv.sources]` from a dependency.

### D4 · Argument and path checks live in `open_source`

`open_source` checks `columns` and `dpi` (R5) and the input path (R6), turning `OSError` and
`RuntimeError` from the path check into `UsageError`, as `cli.resolve_output` does. The CLI keeps
its own earlier checks (argparse, `resolve_output`), so its messages and exit codes don't change;
the new checks never fire from the CLI. Rejected: checks in `transcribe` only (`open_source` is
public too, and `dpi=0` today gives a zero scale).

## Assumptions

- uv_build includes every file in `src/scanscribe/`, so `py.typed` reaches the wheel with no
  config. Task 1.3 checks this by hand; no automated test covers it.
- The version stays `0.1.0`. Nothing has been tagged or published, so the first tag carries the
  API.
- One process runs one OCR job at a time. The real engine swaps the process-wide `sys.stdout` for
  stderr while it runs, and pdfium isn't safe to call from two threads. README says so, and the
  scanscribe-mcp plan must run jobs one at a time per process.
- The folder pre-check decodes every image before the first `on_page` call, so a large folder has
  no progress or cancel until it finishes. The scanscribe-mcp plan handles that wait.

## Risks

- The refactor changes CLI output or the check-first order → every `test_cli.py` test runs
  unchanged, and R1 compares library and CLI output directly.
- A later change breaks the public API silently → R9's test pins `__all__` to D2's list.
- The MCP repo's copy of the Paddle install settings drifts from this repo's → README lists the
  settings to copy (D3).

## Rollout & rollback

Merge, then the owner tags `v0.1.0` on the merge commit:
`git tag v0.1.0 <merge-sha> && git push origin v0.1.0`. Before the tag, rollback is a PR revert.
After it, a pushed tag is never moved: a fix ships as `v0.1.1`. Later API changes get a new tag
following semver. The `study-book-chapter` skill (it turns the CLI's text output into a study
guide) reads the output file, which doesn't change.

## Open questions

- None

## Impact

- Packages / directories: `src/scanscribe/` (new `api.py` and `py.typed`; `__init__.py`,
  `cli.py`, `engine.py`, `pages.py`), `tests/`, `README.md`, `docs/decision-log.md`
- Data: none
- Jobs / APIs: the new Python API; the `scanscribe` command is unchanged

## Links

- Issue [#9](https://github.com/geosp/scanscribe/issues/9) — this work
- [ADR-0001](../../adrs/0001-ocr-engine-behind-an-interface.md) — the OCR engine sits behind a
  one-method interface and Paddle is imported only when OCR starts; this API keeps both
- [mcp-service-kit](https://github.com/geosp/mcp-service-kit) and
  [pandoc-mcp](https://github.com/geosp/pandoc-mcp) — the base library and the layout the MCP
  server will follow

## Phases

| Phase | Title | Status | Tasks |
| --- | --- | --- | --- |
| 01 | [Library API and CLI on top of it](phases/01-library-api.md) | done | 9/9 |

## Decision log

- 2026-11-21 · task 1.1 changed: `test_pdf_with_no_pages_is_an_input_error` mocks the PDF
  opener with a path that doesn't exist, which D4's missing-input check now rejects first. The
  test now creates the file; it still checks empty PDFs. Owner accepted.
- 2026-11-21 · at plan close the task 3.3 check also covers engine reuse and a run stopped from
  `on_page`; all passed on gpu:0. Owner requested. Results:
  [docs/demos/2026-11-21-library-check/README.md](../../demos/2026-11-21-library-check/README.md).
