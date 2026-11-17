---
review: implementation
plan: docs/plans/2026-11-16-rebuild-cli
phase: 01
round: 01
targeted_follow_up: false
adrs: []
commit_sha: 4d348a692cf73dbfc7a8e22c00a152d546634d18
diff_base: 7594141b5dcc874b13cf03c8b7b80369fbb1b80a
date: 2026-11-16
verdict: FAIL
reviewers:
  - { lens: contract, agent: impl-reviewer, status: completed, report: raw/impl-review-phase-01-round-01-contract.md }
  - { lens: failure and retry, agent: impl-reviewer, status: completed, report: raw/impl-review-phase-01-round-01-failure.md }
  - { lens: scope and composition, agent: impl-reviewer, status: completed, report: raw/impl-review-phase-01-round-01-scope.md }
---

# Implementation review 01, phase 01: Rebuild the scanscribe CLI from the ocr-pdf prototype

## Inputs

Each reviewer got the same inputs, and nothing else:

- Diff: `git diff 7594141..4d348a6` in `/home/geo/develop/projects/scanscribe`.
- Contract: `docs/plans/2026-11-16-rebuild-cli/plan.md` and `phases/01-pipeline-and-cli.md`; delivers R1–R12, R20.
- Context: `docs/plans/2026-11-16-rebuild-cli/notes.md`.
- Guidance: `AGENTS.md`, `CLAUDE.md`. No ADRs are in force.

The test suite had passed from a clean clone of `c8448aa` (the last code commit in the range) with only `uv sync --locked` before the round.

## Findings

| ID | Severity | Lens | Location | Scenario / evidence | Action | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| F45 | Major | contract, failure, scope | `cli.py:149-156`, `cli.py:71-83` | `resolve_output` runs outside every handler but `UsageError`: a `PermissionError` from `Path.exists()`/`is_dir()` (input or `-o` under an untraversable dir) or `RuntimeError` from `resolve()` on a symlink loop escapes `run` as a traceback (R10, R12, D7) | Fix | fixed: `test_input_in_an_unreadable_directory…`, `test_output_in_an_unreadable_directory…`, `test_output_that_is_a_symlink_loop…`; `cli.resolve_output` (b922c63) |
| F46 | Major | contract, scope | `test_cli.py:202-213` | The keep-mode test uses 0644, which equals the umask-022 default, so deleting the old-mode branch still passes (D6) | Fix | fixed: `test_existing_output_is_replaced_and_keeps_its_mode` uses 0600 under umask 022 (f99c1a0) |
| F47 | Nit | contract, failure, scope | `cli.py:149-156` | Ctrl-C during parsing or the path check prints a traceback, not 130 and one line (R20) | Fix | fixed: `test_ctrl_c_during_the_path_check_exits_130`; `cli.run` (ad3329a) |
| F48 | Nit | contract, failure, scope | `output.py:90-91` | Ctrl-C between `mkstemp` and `try` leaves the temp file (R20) | Fix | fixed: `test_interrupt_right_after_the_temp_file_is_created_removes_it`; `output.write_atomic` (dc3aeda) |
| F49 | Nit | contract, failure, scope | `output.py:97`, `cli.py:108` | Ctrl-C after `os.replace` returns 130 though the output was replaced (R20) | Contest | contested: the rename and the return can't be made atomic against a signal; the output is complete when it happens |
| F50 | Nit | contract, failure | `output.py:73-76` | `os.umask(0)` changes the process umask briefly; an interrupt or a live engine thread there sees umask 0 (D6) | Fix | fixed: `test_new_file_gets_the_umask_default_without_changing_the_umask`; O_EXCL with mode 0666 (dc3aeda) |
| F51 | Nit | failure | `output.py:98-101` | A cleanup `unlink` failing with other than `FileNotFoundError` hides the original error and leaves the temp file (R12) | Fix | fixed: `test_failed_cleanup_keeps_the_original_error`; cleanup suppresses `OSError` (dc3aeda) |
| F52 | Nit | failure | `output.py` | SIGKILL or power loss after `mkstemp` leaves a temp no run cleans; no directory fsync after the rename (D6) | Contest | contested: R20 covers Ctrl-C only; hard kills and power loss are outside the contract |
| F53 | Nit | failure | `cli.py:89`, `cli.py:133` | A closed stderr pipe raises `BrokenPipeError` in progress and again in the error print (R11, R12) | Contest | contested: outside R11/R12's scope; a closed stderr pipe is rare for this CLI |
| F54 | Nit | failure, scope | `cli.py:77-83` | Some write failures surface only after OCR: temp name over NAME_MAX, sticky-dir EPERM, directory removed mid-run (R10) | Contest | contested: R10 lists the cases it checks; these are rare and fail with one R12 line |
| F55 | Nit | failure, scope | `cli.py:82` | `-o book/p1.png` for the folder `book` overwrites an input page with text (R10) | Fix (plan update) | fixed: R10 and Decision log (f34f9a9); `test_output_that_would_be_a_page_of_the_folder…`; `cli._check_paths` (39c0eeb) |
| F56 | Nit | scope | `cli.py:82` | On a case-insensitive file system `-o BOOK.PDF` for `book.pdf` compares unequal and replaces the PDF (R10, D5) | Fix | fixed: `test_output_that_is_the_same_file_under_another_name…`; `os.path.samefile` (5d2980f) |
| F57 | Nit | scope | `pages.py` | An image changed between the pre-check and OCR can yield zero-width slices (D6, R5) | Contest | contested: a file changed mid-run is unlikely; a corrupt replacement is still an input error and the output stays untouched |
| F58 | Nit | scope | `pages.py` | PDF pages are pre-checked for width only; a `render()` failure happens mid-OCR (R8) | Contest | contested: D6 limits the PDF pre-check to the rendered width |
| F59 | Nit | contract | `pages.py:48` | `is_file()` follows symlinks, so a symlink to an image is a page (R1) | Contest | contested: the prototype followed symlinks too, and a folder of symlinked pages is a legitimate use |
| F60 | Nit | contract | `test_cli.py` | Test gaps: error tests don't all assert no temp file or empty stdout; R10 "no page is read" checked only via the factory; UTF-8 never seen with non-ASCII text; truncated images only at `open_source` level (R3, R8, R10, R11) | Fix | fixed: `test_cli.py` autouse temp check, `pages_never_read`, empty stdout, truncated images end to end, UTF-8 bytes (2f583d8) |
| F61 | Nit | contract, failure, scope | `plan.md:339` | The Phases table shows 0/12 for phase 01 | Fix | fixed: Phases table (f34f9a9) |

## Verdict

FAIL: two Majors (F45, F46) were open when the round ended (docs/reviews/README.md rule 5). All three reviewers completed. Both Majors were then fixed test first; a re-check by fresh reviewers is due (rule 6).

## Open items

None open. Fixed: F45–F48, F50, F51, F55, F56, F60, F61. Contested: F49, F52–F54, F57–F59. F55 changed R10, so the plan's design review is due again.
