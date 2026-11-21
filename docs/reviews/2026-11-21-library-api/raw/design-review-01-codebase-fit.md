## Design review: docs/plans/2026-11-21-library-api (pinned at 6ff8597)

I checked the plan against src/scanscribe/{__init__,cli,engine,pages,output,paddle_engine}.py, tests/{conftest,test_cli,test_engine,test_entry_point,test_paddle_engine}.py, pyproject.toml, ADR-0001 and AGENTS.md. Most of what the plan says about the code is accurate:
- `cli.convert()` takes a Namespace, prints progress and writes the file itself (cli.py:114-130).
- `open_source` runs before `engine_factory` (cli.py:120-121).
- `PageSource.__len__` exists (pages.py:64).
- `format_pages` is in output.py:12.
- `UsageError` is in engine.py:234.
- The version is 0.1.0 (pyproject.toml, `__init__.py:3`).
- `load_engine` prints `Using device:` to stderr (engine.py:269).
- The no-Paddle subprocess script is in test_entry_point.py:14-25.
- `dist/` is gitignored.

I found no ADR conflict. ADR-0001 stays satisfied: api.py imports only engine, pages and output, and task 1.3 adds the new module to the subprocess script, as the ADR's Consequences require.

### Major

**M1. R5 and D1 contradict each other on `ocr_source`.** (plan.md › Requirements › R5; Decisions › D1)
- R5 says "`transcribe` and `ocr_source` must raise `UsageError` when `columns` or `dpi` is below 1, or when the input path doesn't exist."
- D1 gives the signature as `ocr_source(source, engine, columns, on_page)`. It takes an already-opened `PageSource` and has no `path` or `dpi` parameter.

So two of R5's three conditions cannot apply to `ocr_source`. The implementer has to guess what to test, and a reader of the API contract is misled. R5 should name only the `columns` check for `ocr_source`, or the signature should change.

There is a related gap for `transcribe`. Without an explicit check, a missing path never reaches a `UsageError`. `open_source` sends any non-directory to `PdfSource` (pages.py:183-186), which raises `InputError("cannot open … as a PDF")` (pages.py:135). The plan does say `transcribe` checks first (Assumptions), so this is only a note on where the check must sit.

**M2. `ocr_source` takes `columns` separately from the source, which lets a caller skip the width pre-check.** (plan.md › Decisions › D1; phase 01 › Task 1.1)
- `open_source(path, dpi, columns)` checks each page against the `columns` it was given (pages.py:85-87, 100, 142).
- `PageSource` does not store `columns` (pages.py:53-82).
- With D1's signature, a public caller can open with `columns=1` and then call `ocr_source(source, engine, columns=500, …)`. The narrow-page check (the rebuild-cli rule that every page is at least `columns` px wide, checked before OCR) is skipped, and `split_columns` returns empty slices (pages.py:197-199) that go to the engine.

Today the CLI passes `args.columns` to both calls, so it is safe. The public API is not. Either:
- store `columns` on `PageSource` and have `ocr_source` read it (so no `columns` parameter), or
- have `ocr_source` raise when the two values differ.

**M3. The public surface that the semver promise covers is never listed, and R7's test can't catch a missing name.** (plan.md › Terms "Public API"; Decisions › D2; R7; phase 01 › Task 1.3)
- D2 says only that `__init__.py` "re-exports the public names from `api`, `engine`, `pages` and `output`." The Summary names `transcribe`, `ocr_source` and `load_engine`.
- The plan never says whether any of these are in `__all__`: `OcrEngine`, `PageImage`, `PageSource`, `open_source`, `split_columns`, `format_pages`, `ScanscribeError`, `UsageError`, `InputError`, `EngineMissingError`, `EngineFactory`, `ProgressCallback` (which first appears in Task 1.1), `__version__`.
- R7's scenario only checks that "every name in `__all__` is bound", which is true of any `__all__`. A name the MCP repo needs could be left out and every test would still pass.

The plan's Terms say "Changes to them follow semantic versioning from `v0.1.0`", so this list is what gets frozen at the tag. The plan should list it, and the R7 test should assert it exactly.

### Nit

- plan.md › R2: "must never … write to stdout or stderr" holds only for the fake engine. The real `PaddleOcrEngine.recognize` sends stdout to stderr (paddle_engine.py:53-54), and Paddle logs to stderr. Scope R2 to scanscribe's own code, or say "stdout" only.
- plan.md › R5 / Assumptions: the missing-path check should reuse the CLI's handling. `resolve_output` turns `OSError`/`RuntimeError` from `Path.exists()` into `UsageError("cannot check path…")` (cli.py:76-84), for example a parent directory with no read permission on 3.10/3.11. A bare `exists()` in api.py would let a traceback through.
- plan.md › D1 / R1: no defaults are given for `transcribe`'s `dpi=…, columns=…`. R1 holds with defaults only if they are the CLI's 200 and 1 (cli.py:50, 61). State them.
- plan.md › R3 / R4: the plan doesn't say whether `on_page` runs before or after the page is decoded or rendered. Running it before `images()` yields avoids a wasted render when the job is cancelled. The current CLI prints after the page has been read (cli.py:123-124), and the CLI tests pass with either order.
- phase 01 › Task 1.2: the fake Paddle modules are the `fake_paddle` fixture in tests/conftest.py:274-308, not in tests/test_paddle_engine.py.
- phase 01 › Task 1.3 / R8: the `py.typed` check is a manual `uv build` step, not an automated test, so nothing would catch a later regression. That is acceptable, but say so explicitly.

### Files referenced
- /home/geo/develop/scanscribe/docs/plans/2026-11-21-library-api/plan.md
- /home/geo/develop/scanscribe/docs/plans/2026-11-21-library-api/phases/01-library-api.md
- /home/geo/develop/scanscribe/src/scanscribe/cli.py
- /home/geo/develop/scanscribe/src/scanscribe/pages.py
- /home/geo/develop/scanscribe/src/scanscribe/engine.py
- /home/geo/develop/scanscribe/src/scanscribe/paddle_engine.py
- /home/geo/develop/scanscribe/tests/conftest.py
- /home/geo/develop/scanscribe/tests/test_entry_point.py
