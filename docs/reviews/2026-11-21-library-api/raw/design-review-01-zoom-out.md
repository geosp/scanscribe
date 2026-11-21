Review of /home/geo/develop/scanscribe/docs/plans/2026-11-21-library-api (plan.md, phases/01-library-api.md) against commit 6ff8597.

**Root cause:** the plan fixes the cause. `cli.convert()` takes an argparse Namespace, loads the engine inside, prints and writes the file (src/scanscribe/cli.py:111-127). Pulling the loop out into `ocr_source` and having the CLI call it removes the cause, not just a symptom. ADR-0001 is respected: Paddle is still imported only inside `load_engine`, and R7 extends the subprocess check.

## Major

**M1 · plan.md › D1 and R5: `columns` is passed twice, and R5 asks `ocr_source` to check arguments it never receives.**
- D1 gives the signature as `ocr_source(source, engine, columns, on_page)`. The source has already been opened and width-checked with its own `columns` (pages.py:93-101, 129-143; `_check_width` at pages.py:85-87).
- If a caller passes a different or larger `columns` to `ocr_source`, the check-first width check no longer covers the split. `split_columns` (pages.py:189-199) would then hand zero-width or near-empty slices to `engine.recognize`.
- R5 says "`transcribe` and `ocr_source` must raise `UsageError` when `columns` or `dpi` is below 1, or when the input path doesn't exist". But `ocr_source` takes no `dpi` and no path, so that requirement can't be met as written.
- Smaller and safer fix: store `columns` on `PageSource` (it is already an argument to both constructors) and have `ocr_source(source, engine, on_page=None)` read it. Then R5 applies to `transcribe` (or `open_source`) only.

**M2 · plan.md › Non-goals ("Thread safety") and R2: the library has process-wide side effects that the plan neither scopes nor documents.**
- **stdout redirect:** `PaddleOcrEngine.recognize` and `__init__` wrap their calls in `contextlib.redirect_stdout(sys.stderr)` (paddle_engine.py:47-48, 53-54). That swaps the global `sys.stdout` for the whole process, not just the calling thread.
  - A server will almost certainly run blocking OCR jobs in a worker thread, as the plan's own Why says ("A server runs OCR as background jobs").
  - While a page is recognized, anything the server's other threads write to stdout goes to stderr instead. With a stdio MCP transport, that would swallow protocol messages.
- **pdfium:** the plan says the server "will run one job at a time per engine", which implies jobs may run in parallel on separate engines. But PDF rendering goes through pdfium (pages.py:122-175), which pypdfium2 documents as unsafe to call from several threads at once, even on separate documents.
- **R2 as stated:** "`transcribe` and `ocr_source` must never ... write to stdout or stderr" holds only for the fake engine. With the real engine, Paddle logs to stderr (paddle_engine.py:46).
- **Fix:**
  - Scope R2 to scanscribe's own code.
  - State in the non-goal and in the README that the process runs one OCR job at a time, and that the real engine temporarily redirects the global stdout.
  - Or record this as a known constraint for the scanscribe-mcp plan.

**M3 · plan.md › D2, R7 and Terms "Public API": the plan never lists the public names.**
- The semver promise ("Changes to them follow semantic versioning from v0.1.0") applies to the names in `__all__`. D2 only says `__init__.py` "re-exports the public names from `api`, `engine`, `pages` and `output`".
- R7's test ("every name in `__all__` is bound") holds for any list, so it can't catch a missing or extra name.
- The implementer has to decide what becomes a permanent API. Unclear examples:
  - `open_source` and `PageSource`: needed for the open-then-load pattern D1 describes.
  - `format_pages`, `OcrEngine`, `PageImage`, `EngineFactory`.
  - The error types `ScanscribeError`, `UsageError`, `InputError` and `EngineMissingError`: a server must catch them, and a missing engine raises `EngineMissingError` (engine.py:239, 260-262).
  - `split_columns`, `natural_key`, `write_atomic`: probably not public.
- Under "Ask before any materially irreversible choice" in AGENTS.md, a tagged semver surface is exactly that kind of choice.
- **Fix:** list the exact names in D2 and make R7 assert equality with that list.

## Nits

- plan.md › Rollout & rollback: rollback only covers the time before the tag is pushed. After the tag is pushed, a PR revert doesn't move `v0.1.0`, which the MCP repo pins. Say that a fix after tagging means a new tag (`v0.1.1`), and that a pushed tag is never re-pointed.
- plan.md › R5 / Assumptions (placement): the checks for `columns`/`dpi` below 1 and for a missing path would sit more naturally in `pages.open_source`. Both the CLI and the library already go through it, and `dpi=0` currently gives scale 0 (pages.py:131) and `columns=0` passes `_check_width`. That avoids a third copy next to `_at_least_one` (cli.py:16-24) and `_check_paths` (cli.py:80-81).
- plan.md › R6: keep the current order, where the device is reported before `PaddleOcrEngine` is built so it shows during a model download (engine.py:265-267). Today R6 only says "instead of printing", so nothing stops the implementer from calling the callback after the build.
- plan.md › D1 / R3 (failure mode, timeouts): cancellation and progress start only after `open_source` returns. For a folder input, the pre-check fully decodes every image (`image.load()`, pages.py:103-110), so a large folder gives a server a long stretch with no progress and no way to cancel. Note this as a known limit for the MCP plan.
- plan.md › R4: it covers only `ocr_source`. Add that `transcribe` closes the source when `on_page` raises, which holds if it uses `with open_source(...)`, so a cancelled server job doesn't leak open PDF handles.

**Rollout:** no migration, backfill or added load applies. The deploy order (merge, then tag) is stated and correct. The only gap is the one in the first nit.

Files reviewed:
- /home/geo/develop/scanscribe/docs/plans/2026-11-21-library-api/plan.md
- /home/geo/develop/scanscribe/docs/plans/2026-11-21-library-api/phases/01-library-api.md
- /home/geo/develop/scanscribe/docs/adrs/0001-ocr-engine-behind-an-interface.md
- /home/geo/develop/scanscribe/src/scanscribe/cli.py
- /home/geo/develop/scanscribe/src/scanscribe/engine.py
- /home/geo/develop/scanscribe/src/scanscribe/pages.py
- /home/geo/develop/scanscribe/src/scanscribe/paddle_engine.py
- /home/geo/develop/scanscribe/src/scanscribe/output.py
- /home/geo/develop/scanscribe/tests/test_entry_point.py
