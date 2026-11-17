---
review: design
plan: docs/plans/2026-11-16-rebuild-cli
phase: all
round: 03
targeted_follow_up: false
adrs: []
commit_sha: 3131345efdff8345b5abc7ff5dc87ecde1f1b83c
diff_base: n/a
date: 2026-11-16
verdict: FAIL
reviewers:
  - { lens: fresh reader, agent: design-reader, status: completed, report: raw/design-review-03-fresh-reader.md }
  - { lens: codebase fit, agent: design-reviewer, status: completed, report: raw/design-review-03-codebase-fit.md }
  - { lens: zoom out, agent: design-reviewer, status: completed, report: raw/design-review-03-zoom-out.md }
---

# Design review 03: Rebuild the scanscribe CLI from the ocr-pdf prototype

## Inputs

Reopened because impl review F55 changed R10 after approval. Reviewers received only:

- fresh reader: `docs/plans/2026-11-16-rebuild-cli/plan.md`;
- codebase fit: the plan, both phase files, `notes.md`, `AGENTS.md`, `CLAUDE.md` and the repository;
- zoom out: the plan, both phase files, `notes.md` and the repository.

No ADRs are in force. Revision: `3131345`.

## Fresh reader paraphrase

See [raw/design-review-03-fresh-reader.md](raw/design-review-03-fresh-reader.md).

## Findings

The table uses the reviews.md layout: ID, severity, lens, finding, resolution.

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F62 | Major | codebase fit, zoom out | R11 relies on Paddle not writing to stdout; no phase 02 task checks where the `paddlex`/`paddleocr` loggers write or routes them to stderr (R11; phase 02 1.1, 1.2) | open |
| F63 | Major | codebase fit | Clearing `sys.modules` isn't enough: `from scanscribe import paddle_engine` returns the stale package attribute, so R14 and device tests depend on order (phase 02 1.2, 1.3; Risks) | open |
| F64 | Major | codebase fit | No task runs `pytest` with an extra installed, so R13's "machine with an extra" scenario is never exercised (R13; phase 02 2.2, 3.1, 3.2) | open |
| F65 | Major | fresh reader | "Five behaviors break parity" can't be checked: the plan never says which other new behaviors (R5, R10–R12, R15, R16, R20, D6) only add to the prototype (Summary, What changes) | open |
| F66 | Major | fresh reader | Ctrl-C has no stated mechanism: D7 catches `Exception`, which excludes `KeyboardInterrupt`; message and `SCANSCRIBE_DEBUG` behavior unstated (R20, D7) | open |
| F67 | Major | fresh reader | R3 doesn't settle whether an empty page that isn't last is followed by two blank lines (R3) | open |
| F68 | Major | fresh reader | PDF pre-check: whether "rendered width" means rendering twice or computing it, and that a render failure surfaces only during OCR, is unstated (R5, R8, D6) | open |
| F69 | Major | fresh reader | R8 holds two rules: unreadable pages and failures during OCR | open |
| F70 | Major | fresh reader | D1 names `cli.main()` and `load_engine`, but nothing says they arrive in phase 02 (D1, Phases) | open |
| F71 | Major | fresh reader | The manual check that gates the main risk is described only in notes.md (Summary, Risks) | open |
| F72 | Nit | fresh reader | Summary says the manual check "blocks phase 02"; Risks says the owner can lift it (Summary) | open |
| F73 | Nit | fresh reader | Terms used but not defined: "the R12 line", "F55", `study-book-chapter`, "PP-OCRv6", the AGENTS.md Status line, phase task references | open |
| F74 | Nit | fresh reader | D5's title says "resolved input name" but the file rule uses unresolved `with_suffix`; R10 doesn't say it covers the default output (D5, R10) | open |
| F75 | Nit | fresh reader | R10 doesn't say how writability is checked; the mode kept for a symlink output is ambiguous (R10, Assumptions) | open |
| F76 | Nit | fresh reader | Readability: R1, R10, R4 long sentences; R5, R6, R7, R11 hold two rules; D1, D4, D9, Risks need rereading; BGR and MKL-DNN restated | open |
| F77 | Nit | codebase fit | Task 4.2 still says "an existing 0644 output keeps its mode"; the test now uses 0600 (phase 01 4.2) | open |
| F78 | Nit | codebase fit | A bare `assert` in `pytest_sessionfinish` gives INTERNALERROR, not a failure (phase 02 1.4) | open |
| F79 | Nit | codebase fit | Not stated whether `Using device:` prints before `PaddleOCR(...)` is built (phase 02 1.3, R16) | open |
| F80 | Nit | codebase fit | `resolve_output` docstring omits the page-of-folder rule (`cli.py`) | open |
| F81 | Nit | zoom out | The CPU comparison overwrites the GPU baseline `out/proto.txt` (notes Manual check; phase 02 3.2) | open |
| F82 | Nit | zoom out | A PDF diff also measures the pypdfium2 upgrade; the colour page should come from an image folder (Risks) | open |
| F83 | Nit | zoom out | On the base install, R14's message appears only after the whole pre-check decodes every image (R14) | open |
| F84 | Nit | zoom out | mypy is checked only on the base install; an extra's `py.typed` could change the result locally (phase 02 1.2) | open |

## Verdict

FAIL: ten Majors (F62–F71) are open (docs/reviews/README.md rule 5). All three reviewers completed.

## Open items

F62–F84, pending the owner's choice of fixes.
