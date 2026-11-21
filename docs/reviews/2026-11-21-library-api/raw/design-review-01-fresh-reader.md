Review of /home/geo/develop/scanscribe/docs/plans/2026-11-21-library-api/plan.md (I read only this file).

## From the Summary
Today scanscribe can only be run as a command. A planned separate MCP server (`scanscribe-mcp`) needs to call it as a library: keep one OCR engine loaded across jobs, get the text back, report progress page by page, and stop a job between pages. The plan adds a small typed public API (`transcribe`, `ocr_source`, an `on_device` hook on `load_engine`, `__all__`, `py.typed`) and moves the CLI onto that API so both paths share one loop. After the merge the owner tags `v0.1.0` for the MCP repo to pin. The main risk is that the refactor changes how the CLI behaves; the existing CLI tests, which stay unchanged, are the guard.

## From the whole plan
The plan pulls the OCR page loop out of `cli.convert()` into a new `api.py`. `ocr_source` runs the loop on a source that is already open, takes an `on_page` progress callback, and stops if that callback raises. `transcribe` opens a path, runs `ocr_source` and returns the formatted text. It never writes files, stdout or stderr. `load_engine` gets an `on_device` callback so a server can get the chosen device without it being printed. `scanscribe/__init__.py` defines the public surface through `__all__` without importing Paddle, and `py.typed` ships in the wheel so the MCP repo's strict mypy works. The reason is that `cli.convert()` is tied to argparse, stderr and writing files. A server needs a stable, semver-covered API to reuse a loaded engine, track progress and cancel jobs. Without one it would import private functions. The MCP server itself stays in a separate repo because of the Python version (3.11+ vs 3.10), its dependencies and how it is deployed.

## How the existing system works, per this plan
`scanscribe` is a CLI. `cli.convert()` takes an argparse `Namespace`. It opens the input and checks every page and path first (the "check-first" rule from the rebuild-cli plan), and only then loads the engine. It runs each page through `engine.recognize`, prints progress to stderr, formats the result with `format_pages`, and writes the output file, replacing it only at the end. The engine sits behind a one-method `OcrEngine` protocol. `load_engine(lang, device)` builds the PaddleOCR engine, which takes seconds to minutes to load, and prints `Using device: …` to stderr. Paddle is imported only when OCR starts (ADR-0001). The package supports Python 3.10, uses uv with a Paddle index and `conflicts` settings, and is tested with a fake engine and fake Paddle modules in `test_cli.py`.

## Summary vs plan
- Major, Summary diagram / D1: The diagram shows the CLI and the MCP server both calling into `transcribe / ocr_source`, which then call `open_source`. Per D1 the CLI calls `open_source` itself, then loads the engine, then calls `ocr_source`. Only `transcribe` opens the source internally. "Both paths run the same loop" is true, but the diagram hides the ordering that check-first depends on.
- Major, Summary / R7: The Summary leaves out a hard constraint: `import scanscribe` must not import `paddle`, `paddleocr` or `scanscribe.paddle_engine` (R7, ADR-0001). An implementer reading only the Summary could easily break it.
- Major, Summary / R5 / Assumptions: The Summary says nothing about new argument validation (`UsageError` for `columns`/`dpi` below 1 or a missing path). It also omits that this repeats the CLI's own checks, which is behavior that has to stay consistent.
- Nit, Summary / D3: It leaves out the cost of the separate repo: the MCP repo must copy the Paddle index and `conflicts` settings, and README must document them.
- Nit, Summary / What changes: The README "Use as a library" section, the semver promise and the decision-log entry are not mentioned.
- Nit, Summary / Risks: It names one risk. Risks lists three (CLI regression, silent API breakage, drift in the Paddle settings).
- Nit, Summary: "twenty requirements" of the rebuild-cli plan are cited but never listed or summarized anywhere.

## Sections I couldn't paraphrase (Blockers)
No Blockers. Every section could be paraphrased. The empty trailing "## Decision log" section has nothing to paraphrase (see Nits).

## Terms used but never explained
- Major, R5 / D2, `UsageError`: The plan never says where it is defined or whether it is in `__all__`. A library caller has to catch it, so this is part of the public contract.
- Major, D2 / Terms "Public API": The full list of names in `__all__` is never given. From hints it may be `transcribe`, `ocr_source`, `load_engine`, `OcrEngine`, `open_source`, `PageSource`, `format_pages`, `UsageError`, but the plan doesn't say. The semver promise covers exactly this list.
- Nit, D1 / Summary, `format_pages`: used but never described (module, inputs).
- Nit, R1 / R3, `columns`: its meaning is never explained. R3's "that page's first `recognize` call" suggests several calls per page, apparently one per column, but this is never stated.
- Nit, R1 / R5, `dpi`: not explained. It seems to apply only to PDFs.
- Nit, R1, "the fake engine": the existing test fake is assumed but never introduced. It is mentioned only in Non-goals.
- Nit, R6, "fake Paddle modules" and "resolved device": how a device is resolved from `None` is not described.
- Nit, D3, "Paddle index" and "`conflicts` settings": uv config is named but its content is not described.
- Nit, Rollout, `study-book-chapter` skill: never explained.
- Nit, Why / Rollout, "the owner": who this is is not stated.
- Nit, Why / Links, mcp-service-kit and pandoc-mcp: external links only, with no one-line description of what "follows pandoc-mcp" means.

## Places where the parts don't connect
- Major, R5 vs D1: R5 says `ocr_source` raises `UsageError` when `dpi` is below 1 or the input path doesn't exist. But D1's `ocr_source(source, engine, columns, on_page)` takes neither a path nor `dpi`, only an already-opened `PageSource`. For `ocr_source`, R5 only makes sense for `columns`.
- Major, R1 / D1, signatures: `transcribe(path, engine, dpi=…, columns=…)` in R1 vs `transcribe(path, engine, *, dpi, columns, on_page)` in D1. The defaults are never stated. R1 ("same text as the CLI for the same options") assumes they match the CLI's defaults. It is also not stated whether `on_page` is optional, or what `ocr_source` returns ("the pages' lines": what type?).
- Major, R2 / R5, error behavior of `open_source`: The plan says `transcribe` opens the source and that opening it checks every page. It never says what the library raises when a page fails that check, or whether `open_source` prints anything (R2 forbids stderr output).
- Major, What changes / D1, CLI progress output: The CLI currently prints progress to stderr. After the refactor that printing must come from an `on_page` callback the CLI passes in, with the exact same text and timing. This is never stated. R3's "before each page" may or may not match when the CLI prints progress today.
- Nit, Risks 2-3 vs What changes: Risks rely on README stating the semver promise and documenting the Paddle settings to copy. What changes only says "Use as a library" section.
- Nit, Assumptions: "Task 1.3 checks this" and the Phases table (0/8 tasks) depend on `phases/01-library-api.md`, which isn't summarized here.
- Nit, Assumptions #3: This is a design decision (duplicated validation, CLI still checks first), not an assumption, and it has no D-number.
- Nit, R2 / R5 tests: R2's scenario covers only `transcribe`, not `ocr_source`. R5's scenarios don't cover `dpi` or `ocr_source`.
- Nit, "## Decision log": an empty section at the end. It is unclear whether it is a placeholder or should mirror `docs/decision-log.md`.
- Nit, Rollout: How later API changes get versioned and tagged after `v0.1.0` is not stated (D3 says "a tag per API change").

## Readability
- Nit, Summary: "The CLI's behavior doesn't change (the rebuild-cli plan's twenty requirements), and its tests stay as they are." I had to reread the parenthetical; it is unclear what it is referring to.
- Major, Terms: The check-first rule is defined twice in different words. The "Page source" entry says "checks every page before any OCR". The "rebuild-cli plan" entry says "every page and path is checked before the engine loads, and the output is replaced only at the end". These are not the same rule (before OCR vs before the engine loads, and output replacement is added). Pick one definition.
- Nit, Terms (rebuild-cli entry): one bullet holds two rules (check before load; replace output only at the end).
- Major, R5: one requirement holds four rules over two functions: `columns` below 1, `dpi` below 1, a missing path, and raising before any page is read. Combined with the D1 mismatch above, this is hard to implement or test cleanly. Consider splitting it.
- Nit, R6: two rules (pass the device to the callback and stay silent; print as today when there is no callback).
- Nit, R7: two rules (expose every `__all__` name; don't import Paddle).
- Nit, R4: two rules (stop; propagate the same exception object).
- Nit, D3: "It costs a tag per API change, and the dependent project must repeat…": "It" is ambiguous (it means the decision).
- Nit, D3: "Rejected: an `mcp` extra… (Python markers, two test setups in CI, and server dependencies in the CLI's lock file)" is too terse to follow without rereading.
- Nit, D1: a dense paragraph that mixes two signatures, the CLI's rationale, the cancel design and two rejected options. Splitting it would help.
- Nit, repetition: "CLI behavior/command unchanged" appears in the Summary, What changes, Risks, Rollout, Impact and Links. "Cancel by raising" appears in the Summary diagram, R4 and D1.
- No sentences over about 40 words found.
