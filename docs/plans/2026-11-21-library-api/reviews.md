# Reviews · A public library API for scanscribe

## 2026-11-21 · design-review · plan · round 1 · changes-requested
Reviewers: fresh reader ✅ · codebase fit ✅ · zoom out ✅ (commit 6ff8597; summary in docs/reviews/2026-11-21-library-api/design-review-01.md; reports in raw/). The owner chose a single round.

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F1 | Major | codebase fit, zoom out, fresh reader | R5 asks `ocr_source` to check `dpi` and the path, which D1's signature never receives (R5, D1) | fixed: R5, R6, D1 (no `dpi`/path on `ocr_source`), D4 |
| F2 | Major | codebase fit, zoom out | `columns` is passed to `open_source` and again to `ocr_source`; a larger second value skips the width pre-check and sends empty slices to the engine (D1) | fixed: R7, D1 (`columns` read from the source); task 1.1 |
| F3 | Major | codebase fit, zoom out, fresh reader | The public names that semver freezes are never listed; R7's "every name is bound" can't catch a missing name; `UsageError` etc. not said to be public (Terms, D2, R7) | fixed: D2 lists the names; R9 asserts equality; task 1.4 |
| F4 | Major | zoom out | Process-wide side effects are unstated: the real engine's `redirect_stdout` swaps global `sys.stdout`, pdfium isn't thread safe; R2's "never stderr" only holds for the fake engine (Non-goals, R2) | fixed: R2 scoped to scanscribe's code; Non-goals; Assumptions (one job per process); task 3.1 |
| F5 | Major | fresh reader | The Summary diagram shows the CLI calling `transcribe`, hiding that it opens the source before loading the engine (Summary, D1) | fixed: Summary diagram shows both call orders |
| F6 | Major | fresh reader | The Summary omits the no-Paddle import constraint and the new argument checks (Summary, R5, R7) | fixed: Summary (R9, argument checks) |
| F7 | Major | fresh reader, codebase fit | `transcribe` defaults, whether `on_page` is optional, and `ocr_source`'s return type are unstated (R1, D1) | fixed: R1, D1 (defaults, optional `on_page`, return types) |
| F8 | Major | fresh reader | What the library raises when a page fails the pre-check is unstated (R2, R5) | fixed: Terms › Page source (`InputError`) |
| F9 | Major | fresh reader, codebase fit | How the CLI's progress line comes from `on_page`, and whether `on_page` runs before or after a page is decoded, is unstated (What changes, R3) | fixed: R3 (after read, before recognize), D1, task 2.1 |
| F10 | Major | fresh reader | The check-first rule is defined twice in Terms, differently (Terms) | fixed: Terms (one definition of the check-first rule) |
| F11 | Major | fresh reader | R5 holds four rules over two functions (R5) | fixed: split into R5 and R6 |
| F12 | Nit | zoom out | Rollback doesn't cover the time after the tag: a fix means a new tag; a pushed tag is never moved (Rollout) | fixed: Rollout & rollback |
| F13 | Nit | zoom out, codebase fit | Argument checks belong in `open_source`, reusing the CLI's `OSError`→`UsageError` handling, not a third copy (R5, Assumptions) | fixed: D4 |
| F14 | Nit | zoom out | R6 should keep reporting the device before the engine is built, so it shows during a model download (R6) | fixed: R8 |
| F15 | Nit | zoom out | The folder pre-check decodes every image before progress or cancel starts; a known limit for the MCP plan (D1, R3) | fixed: Assumptions (handed to the scanscribe-mcp plan) |
| F16 | Nit | zoom out | R4 should also say `transcribe` closes the source when `on_page` raises (R4) | fixed: R4 second scenario |
| F17 | Nit | codebase fit | The fake Paddle fixture is `fake_paddle` in tests/conftest.py, not test_paddle_engine.py (task 1.2) | fixed: task 1.3 |
| F18 | Nit | codebase fit | The `py.typed` check is manual (`uv build`), not an automated test; say so (R8, task 1.3) | fixed: Assumptions, task 1.4 |
| F19 | Nit | fresh reader | Summary omits the README section, semver promise, decision-log line and two of three risks (Summary) | fixed: Summary (README, semver); accepted: one main risk in the Summary, the rest under Risks |
| F20 | Nit | fresh reader | Terms missing or thin: `format_pages`, `columns`, `dpi`, the fake engine, Paddle index/`conflicts`, `study-book-chapter`, "the owner", mcp-service-kit, pandoc-mcp (Terms) | fixed: Terms |
| F21 | Nit | fresh reader | R4, R6, R7 each hold two rules (Requirements) | contested: each states one rule with its conditions (as rebuild-cli F22) |
| F22 | Nit | fresh reader | Assumption 3 is a decision; "It" in D3 is ambiguous; D1 is dense; "unchanged CLI" repeated in six places; empty Decision log (Assumptions, D1, D3) | fixed: assumption moved to D4, D3 reworded, D1 bulleted, Decision log placeholder; accepted: the repeated "CLI unchanged" is each section's own claim |
| F23 | Nit | fresh reader | R2 and R5 scenarios don't cover `ocr_source` or `dpi`; later version tagging unstated (R2, R5, Rollout) | fixed: R5 `dpi` scenario, Rollout tagging; accepted: R2's scenario runs `ocr_source` through `transcribe` |

All fixes applied after the round; no Blocker or Major is open, so design_review is passed. The owner chose a single round, so no re-check round ran.

## 2026-11-21 · approved · plan (phase 01)

## 2026-11-21 · impl-review · phase 01 · round 1 · changes-requested
Diff base 49ecda0, reviewed commit 4c190ed. Reviewers: contract ✅ (the owner chose one reviewer, the contract lens; report in docs/reviews/2026-11-21-library-api/raw/impl-review-phase-01-round-01-contract.md).

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F24 | Major | contract | A folder input that exists but can't be listed (mode 0o000) escapes `open_source` as a raw `PermissionError` from `iterdir()`, not `UsageError`; the R6 test only covers a path inside a locked folder (R6, D4) | fixed: `test_a_folder_that_cannot_be_listed_is_a_usage_error`; `ImageFolderSource` wraps the listing (3c2e2a1) |
| F25 | Nit | contract | The R2 test uses `capsys`, which can't see output written straight to file descriptors; `capfd` would (R2) | fixed: `test_transcribe_prints_nothing_and_writes_no_file` uses `capfd` (3c2e2a1) |
| F26 | Nit | contract | The R3 order test covers only a one-column folder, not a PDF or `columns=2` (R3) | fixed: `test_progress_comes_before_the_first_strip_of_each_pdf_page` (3c2e2a1) |
| F27 | Nit | contract | The no-Paddle script imports `load_engine` and `run` before its `unbound` check, which adds little over the star import (R9) | accepted: the star import already fails on an unbound name; the explicit imports are what the CLI uses |
| F28 | Nit | contract | The `__all__` pin runs in-process, not in the fresh interpreter the scenario names (R9) | accepted: `__all__` is a literal, so in-process and fresh-interpreter values are the same |
| F29 | Nit | contract | No automated check that the wheel holds `py.typed`, and the by-hand result isn't recorded (R10) | accepted: the plan's Assumptions make it a by-hand check; the result goes in the PR |
| F30 | Nit | contract | "input not found" / "cannot check path" and "must be at least 1" are written in both `pages.py` and `cli.py`; the two copies can drift (D4, task 1.1) | accepted: D4 keeps the CLI's checks so its messages and exit codes don't change; the messages are each one short line |
| F31 | Nit | contract | The `locked_dir` fixture is copied from test_cli.py into test_api.py (task 1.1) | accepted: moving it to conftest.py would edit test_cli.py, which the plan keeps unchanged |
| F32 | Nit | contract | An input removed between the CLI's path check and `open_source` now gives a `UsageError` with exit 1, while `UsageError` is documented as exit 2 (D4) | accepted: only a race between two stat calls; the exit code, 1, is unchanged from before |
| F33 | Nit | contract | `transcribe("book.pdf", …)` with a `str` raises `AttributeError`, not `UsageError`; mypy catches it for typed callers (R6) | fixed: `test_a_str_path_is_accepted`; `open_source` and `transcribe` take `str | os.PathLike[str]` (3c2e2a1) |
| F34 | Nit | contract | A third-party `PageSource` subclass that doesn't set `columns` fails inside `ocr_source` (R7, D2) | accepted: `labels` already works this way; `PageSource` is exported to type sources, not to subclass |
| F35 | Nit | contract | The decision-log line gives the plan path in backticks, not a Markdown link (task 3.2) | accepted: every row in docs/decision-log.md cites plans by path in backticks |

The Major was fixed test first; no Blocker or Major is open, so impl_review is passed. The owner chose a single round.

## 2026-11-21 · ADR review
ADRs in force reviewed: [ADR-0001](../../adrs/0001-ocr-engine-behind-an-interface.md) (kept; this plan follows it). Created, with the owner's confirmation: [ADR-0002](../../adrs/0002-public-library-api.md) from D2 and [ADR-0003](../../adrs/0003-mcp-server-in-a-separate-repository.md) from D3. D1 and D4 are API-shape details covered by ADR-0002, so they need no ADR.
