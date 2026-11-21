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
