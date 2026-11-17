# Reviews · Rebuild the scanscribe CLI from the ocr-pdf prototype

## 2026-11-16 · design-review · plan · round 1 · changes-requested
Reviewers: fresh reader ✅ · codebase fit ✅ · zoom out ✅ (commit 283b8f4; reports in docs/reviews/2026-11-16-rebuild-cli/raw/)

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F1 | Major | codebase fit, zoom out | Output that is an existing directory or not writable still fails only at the final write; `OSError` there prints a traceback; the write is not atomic (R10, D6, D7) | fixed: R10, R12, D6, D7; phase 01 4.1–4.3 |
| F2 | Major | codebase fit, zoom out | Fake-module tests leave `scanscribe.paddle_engine` cached, and the R14 test relies on Paddle being absent, so it fails on a machine with an extra (phase 02 1.2, 1.3; Risks) | fixed: phase 02 1.2, 1.3; Risks |
| F3 | Major | codebase fit, zoom out | The R13 subprocess test imports `paddle_engine`, contradicting D2, and argparse's `--help` exits before the assertion (phase 02 1.4) | fixed: D2, D7; phase 02 1.4 |
| F4 | Major | zoom out, codebase fit | PDF rendering can yield BGR (`to_numpy()`); the adapter flip would then send RGB for PDFs; there is no colour test (phase 01 2.2, D4) | fixed: D4; phase 01 1.2, 2.2; notes D4 |
| F5 | Major | fresh reader, codebase fit, zoom out | R12 "one line" conflicts with argparse's two-line usage error (R9); whether `run` catches `SystemExit` is unstated (R9, R12, D7, task 4.1) | fixed: R12, D7; phase 01 4.1 |
| F6 | Major | fresh reader | Summary says inputs stay the same and errors come before OCR (R5–R12), but R1 skips dotfiles, R6 renames dotted-folder output, and R8/R12 cover failures during OCR; the prototype's options are never listed | fixed: Summary, Why, What changes |
| F7 | Major | fresh reader | It is not said where the device is chosen (R15) or how `Using device:` reaches stderr (R16), given the factory takes `(lang, device)` (D1, D2) | fixed: D1; phase 02 1.3 |
| F8 | Major | fresh reader, codebase fit | Where and when the R5 width check runs, and how it gets the page label, is unstated (R5, D6, tasks 2.3, 4.3) | fixed: R5, D6; phase 01 2.2 |
| F9 | Major | fresh reader | R4 says "±1 px" but not the rule for where the remainder goes | fixed: R4 |
| F10 | Major | fresh reader, zoom out | The manual check records a diff count but has no pass/fail rule; "newer locked versions" is wrong (only pypdfium2 differs) (Summary, Risks, phase 02 3.1) | fixed: Summary, Risks; notes Manual check; phase 02 3.1, 3.2 |
| F11 | Major | fresh reader | PaddleX, MKL-DNN (and why it is off on CPU), and the fake Paddle modules are used but never defined (D3, R17, Risks) | fixed: Terms |
| F12 | Major | fresh reader | The Phases table does not say which requirements each phase delivers | fixed: Phases table (Delivers column) |
| F13 | Major | fresh reader, codebase fit | D8 cites pypdfium2 5.13, but `uv.lock` has 5.15.2 | fixed: D8; notes D8 |
| F14 | Nit | codebase fit, zoom out | R7 "text file as input" scenario hits R10 if the file is named `*.txt` with no `-o` | fixed: R7; notes D9 |
| F15 | Nit | codebase fit | Pillow writes RGB PDFs as JPEG, so exact `rgb{r},{g},{b}` from the fake engine won't match 255 (notes D9) | fixed: D9; notes D9 |
| F16 | Nit | codebase fit, zoom out | The truncated-image fixture is ambiguous and unused; `Image.verify()` would catch it in the pre-check (task 1.2, Assumptions) | fixed: D6, Assumptions; phase 01 1.2, 2.2; notes D9 |
| F17 | Nit | zoom out | Header pre-check must close each image, or folders over ~1024 pages run out of file descriptors (task 2.2) | fixed: phase 01 2.2 |
| F18 | Nit | zoom out | Ctrl-C prints a `KeyboardInterrupt` traceback; map it or exempt it from R12 | fixed: R20, D7; phase 01 4.3 |
| F19 | Nit | zoom out | Two overlapping first runs may race on the model download cache; README could say so | fixed: phase 02 2.1 |
| F20 | Nit | structure | plan.md has 291 body lines (budget 250) | accepted: the length is 20 testable requirements; evidence already lives in notes.md |
| F21 | Nit | fresh reader | R3 "nothing follows the last page" reads as contradicting the example's final `\n`; "lines `a`,`b` and none" is hard to parse | fixed: R3 |
| F22 | Nit | fresh reader | R1, R3, R6, R7, R10, R11 each hold several conditions | contested: each states one rule with its conditions listed; splitting adds length without adding clarity |
| F23 | Nit | fresh reader | Facts stated twice: exit codes (Terms, D7), hidden files (R1, Assumptions), PDF-only file input (Non-goals, R2), empty input (R7, D8) | fixed: Terms, Assumptions, Non-goals |
| F24 | Nit | fresh reader | Minor gaps: Summary cites D1 for lazy import; "the owner", `rec_texts`, "which sources" undefined; `a.png`/`A.png` order unstated; empty Decision log | fixed: Summary, Terms, Risks, R1, Decision log |

## 2026-11-16 · design-review · plan · round 2 · changes-requested
Reviewers: fresh reader ✅ · codebase fit ✅ · zoom out ✅ (commit d5f1a46; reports in docs/reviews/2026-11-16-rebuild-cli/raw/). Closed findings not repeated: the fresh reader again flagged multi-rule requirements (F22, contested).

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F25 | Major | zoom out | Reopens F16: `Image.verify()` checks only PNG/WebP, so a damaged JPEG, TIFF or BMP passes the pre-check and fails hours into OCR (D6, Assumptions, phase 01 2.2) | fixed: D6 (full decode), Assumptions; phase 01 1.2, 2.2; notes D6 |
| F26 | Major | fresh reader | Summary says "two input rules change"; What changes lists five breaking changes | fixed: Summary |
| F27 | Major | fresh reader | The modules holding `load_engine` and `main()` are never named (D1, D2, R13) | fixed: D1, D2 |
| F28 | Major | fresh reader | Phase files are never linked, though Risks and the Phases table cite their tasks | fixed: Phases table links |
| F29 | Major | fresh reader, codebase fit | R1 never says the natural sort ignores case; task 2.1 doesn't fold case | fixed: R1; phase 01 2.1 |
| F30 | Major | fresh reader | How post-parse path checks (R10) give exit 2 in argparse's format is unstated; writability is only tested when the temp file is created (D6, D7) | fixed: D7 (`parser.error()`); phase 01 4.1 (`os.access`) |
| F31 | Major | fresh reader, zoom out | Reopens F10: "reads worse" has no criterion, nothing says what unblocks phase 02, and a grayscale input can't test D4 | fixed: Risks; notes Manual check; phase 02 3.1, 3.2 |
| F32 | Major | fresh reader | D6's first sentence is ~50 words of seven steps; needs a numbered list | fixed: D6 numbered list |
| F33 | Nit | codebase fit, zoom out | Multi-line exception messages (Paddle's C++ traceback) break R12's one line; there is no way to get a traceback for diagnosis | fixed: R12, D7 (one line, `SCANSCRIBE_DEBUG`); phase 01 4.3 |
| F34 | Nit | codebase fit, zoom out | Temp file name, timing and mode are unspecified: `mkstemp` makes the output 0600, and an early temp file can be orphaned by a hard kill (D6) | fixed: D6, Assumptions; phase 01 4.2 |
| F35 | Nit | codebase fit | R5 pre-check uses width × DPI / 72, but pypdfium2 renders `ceil(width × scale)` (phase 01 2.2) | fixed: phase 01 2.2 |
| F36 | Nit | codebase fit | The flipped array `image[:, :, ::-1]` isn't C-contiguous; use `np.ascontiguousarray` (phase 02 1.2) | fixed: phase 02 1.2 |
| F37 | Nit | codebase fit | The manual-check `<input>` resolves differently after `cd ../ocr-pdf`; use an absolute path (notes Manual check) | fixed: notes Manual check |
| F38 | Nit | codebase fit | The manual check doesn't confirm stdout stays empty with real Paddle (R11, phase 02 3.1–3.2) | fixed: notes Manual check; phase 02 3.1 |
| F39 | Nit | codebase fit | No test checks the option defaults or that `--help` lists every option (R19, phase 01 4.1) | fixed: phase 01 4.1 |
| F40 | Nit | codebase fit | Impact leaves out AGENTS.md, whose Status line goes stale when phase 02 merges | fixed: Impact; phase 02 2.1 |
| F41 | Nit | zoom out | D2 maps any `ImportError` under `paddle` to "install the extra", including a broken installed build; map only `ModuleNotFoundError` named exactly `paddle`/`paddleocr` | fixed: D2; phase 02 1.3 |
| F42 | Nit | zoom out | Rollout doesn't say whether the downstream consumer (`study-book-chapter`) is affected | fixed: Rollout & rollback |
| F43 | Nit | zoom out | Ctrl-C (R20) is never observed with real Paddle; add it to the manual check | fixed: notes Manual check; phase 02 3.1 |
| F44 | Nit | fresh reader | Small wording gaps: rename drawn on the per-page line, R11 vs `--help` on stdout, R4 half rounding, "PP-OCRv6"/"locked version", "hidden", 5.13.0's meaning, D4 causality, the Risks arrow, R10's two "before" points | fixed: Summary diagram, Terms, R1, R4, R10, R11, D4, D8, Risks |

## 2026-11-16 · approved · plan (phases 01 and 02)

## 2026-11-16 · impl-review · phase 01 · round 1 · changes-requested
Diff base 7594141, reviewed commit 4d348a6. Reviewers: contract ✅ · failure and retry ✅ · scope and composition ✅ (summary in docs/reviews/2026-11-16-rebuild-cli/impl-review-phase-01-round-01.md; reports in raw/)

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F45 | Major | contract, failure, scope | `resolve_output` errors other than `UsageError` (`PermissionError`, symlink-loop `RuntimeError`) escape `run` as a traceback (R10, R12, D7) | fixed: `test_input_in_an_unreadable_directory…`, `test_output_in_an_unreadable_directory…`, `test_output_that_is_a_symlink_loop…`; `cli.resolve_output` (b922c63) |
| F46 | Major | contract, scope | Keep-mode test uses 0644, the umask-022 default, so it can't see the old-mode branch (D6) | fixed: `test_existing_output_is_replaced_and_keeps_its_mode` uses 0600 under umask 022 (f99c1a0) |
| F47 | Nit | contract, failure, scope | Ctrl-C during parsing or path checks prints a traceback (R20) | fixed: `test_ctrl_c_during_the_path_check_exits_130`; `cli.run` (ad3329a) |
| F48 | Nit | contract, failure, scope | Ctrl-C between `mkstemp` and `try` leaves the temp file (R20) | fixed: `test_interrupt_right_after_the_temp_file_is_created_removes_it`; `output.write_atomic` (dc3aeda) |
| F49 | Nit | contract, failure, scope | Ctrl-C after `os.replace` returns 130 though the output changed (R20) | contested: the rename and the return can't be made atomic against a signal; the output is complete when it happens |
| F50 | Nit | contract, failure | `os.umask(0)` briefly changes the process umask (D6) | fixed: `test_new_file_gets_the_umask_default_without_changing_the_umask`; O_EXCL with mode 0666 (dc3aeda) |
| F51 | Nit | failure | A failing cleanup `unlink` hides the original error (R12) | fixed: `test_failed_cleanup_keeps_the_original_error`; cleanup suppresses `OSError` (dc3aeda) |
| F52 | Nit | failure | SIGKILL or power loss leaves a temp file; no directory fsync (D6) | contested: R20 covers Ctrl-C only; hard kills and power loss are outside the contract |
| F53 | Nit | failure | A closed stderr pipe raises `BrokenPipeError` twice (R11, R12) | contested: outside R11/R12's scope; a closed stderr pipe is rare for this CLI |
| F54 | Nit | failure, scope | Some write failures surface only after OCR (NAME_MAX, sticky dir, dir removed) (R10) | contested: R10 lists the cases it checks; these are rare and fail with one R12 line |
| F55 | Nit | failure, scope | `-o` naming a page inside the input folder overwrites it (R10) | fixed: R10 and Decision log (f34f9a9); `test_output_that_would_be_a_page_of_the_folder…`; `cli._check_paths` (39c0eeb) |
| F56 | Nit | scope | Case-insensitive file systems defeat the output-is-input check (R10, D5) | fixed: `test_output_that_is_the_same_file_under_another_name…`; `os.path.samefile` (5d2980f) |
| F57 | Nit | scope | An image changed between pre-check and OCR can give zero-width slices (D6) | contested: a file changed mid-run is unlikely; a corrupt replacement is still an input error and the output stays untouched |
| F58 | Nit | scope | PDF render failures happen mid-OCR; pre-check reads width only (R8) | contested: D6 limits the PDF pre-check to the rendered width |
| F59 | Nit | contract | Symlinks to images count as pages (R1) | contested: the prototype followed symlinks too, and a folder of symlinked pages is a legitimate use |
| F60 | Nit | contract | Test gaps: temp/stdout asserts, "no page is read", non-ASCII UTF-8, truncated images at CLI level | fixed: `test_cli.py` autouse temp check, `pages_never_read`, empty stdout, truncated images end to end, UTF-8 bytes (2f583d8) |
| F61 | Nit | contract, failure, scope | Phases table shows 0/12 for phase 01 | fixed: Phases table (f34f9a9) |

## 2026-11-16 · design-review · plan · round 3 · changes-requested
Reopened by the R10 change from impl review F55. Reviewers: fresh reader ✅ · codebase fit ✅ · zoom out ✅ (commit 3131345; reports in docs/reviews/2026-11-16-rebuild-cli/raw/design-review-03-*.md). Closed findings not repeated: the plan.md line budget (F20, accepted); multi-rule requirements (F22, contested) are logged once more as F69 and F76 because the reviewer rated one Major.

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F62 | Major | codebase fit, zoom out | R11 relies on Paddle not writing to stdout; no phase 02 task checks where the `paddlex`/`paddleocr` loggers write or routes them to stderr (R11; phase 02 1.1, 1.2) | fixed: phase 02 1.1, 1.2 (logger check, stderr routing, fake-module test) |
| F63 | Major | codebase fit | Clearing `sys.modules` isn't enough: `from scanscribe import paddle_engine` returns the stale package attribute, so R14 and device tests depend on order (phase 02 1.2, 1.3; Risks) | fixed: phase 02 1.2 (fixture removes the package attribute), 1.3 (`importlib.import_module`) |
| F64 | Major | codebase fit | No task runs `pytest` with an extra installed, so R13's "machine with an extra" scenario is never exercised (R13; phase 02 2.2, 3.1, 3.2) | fixed: phase 02 3.1 (pytest and mypy with the extra; 3.2 repeats it) |
| F65 | Major | fresh reader | "Five behaviors break parity" can't be checked: the plan never says which other new behaviors (R5, R10–R12, R15, R16, R20, D6) only add to the prototype (Summary, What changes) | fixed: What changes (additions bullet) |
| F66 | Major | fresh reader | Ctrl-C has no stated mechanism: D7 catches `Exception`, which excludes `KeyboardInterrupt`; message and `SCANSCRIBE_DEBUG` behavior unstated (R20, D7) | fixed: D7 (`KeyboardInterrupt` around the whole run) |
| F67 | Major | fresh reader | R3 doesn't settle whether an empty page that isn't last is followed by two blank lines (R3) | fixed: R3 second scenario; phase 01 3.1; `test_empty_middle_page_is_followed_by_two_blank_lines` |
| F68 | Major | fresh reader | PDF pre-check: whether "rendered width" means rendering twice or computing it, and that a render failure surfaces only during OCR, is unstated (R5, R8, D6) | fixed: D6 step 3 |
| F69 | Major | fresh reader | R8 holds two rules: unreadable pages and failures during OCR | contested: same as F22; each requirement states one rule with its conditions |
| F70 | Major | fresh reader | D1 names `cli.main()` and `load_engine`, but nothing says they arrive in phase 02 (D1, Phases) | fixed: D1 |
| F71 | Major | fresh reader | The manual check that gates the main risk is described only in notes.md (Summary, Risks) | contested: the plan states the pass rule; the procedure belongs in notes.md (F10, F31) |
| F72 | Nit | fresh reader | Summary says the manual check "blocks phase 02"; Risks says the owner can lift it (Summary) | fixed: Summary |
| F73 | Nit | fresh reader | Terms used but not defined: "the R12 line", "F55", `study-book-chapter`, "PP-OCRv6", the AGENTS.md Status line, phase task references | accepted: terms are explained where they are defined (notes, phase files) or are self-evident in context |
| F74 | Nit | fresh reader | D5's title says "resolved input name" but the file rule uses unresolved `with_suffix`; R10 doesn't say it covers the default output (D5, R10) | fixed: D5 title; R10 (given or default) |
| F75 | Nit | fresh reader | R10 doesn't say how writability is checked; the mode kept for a symlink output is ambiguous (R10, Assumptions) | contested: phase 01 4.1 names `os.access`; the symlink case is listed under Assumptions |
| F76 | Nit | fresh reader | Readability: R1, R10, R4 long sentences; R5, R6, R7, R11 hold two rules; D1, D4, D9, Risks need rereading; BGR and MKL-DNN restated | contested: same as F22 |
| F77 | Nit | codebase fit | Task 4.2 still says "an existing 0644 output keeps its mode"; the test now uses 0600 (phase 01 4.2) | fixed: phase 01 4.2 |
| F78 | Nit | codebase fit | A bare `assert` in `pytest_sessionfinish` gives INTERNALERROR, not a failure (phase 02 1.4) | fixed: phase 02 1.4 |
| F79 | Nit | codebase fit | Not stated whether `Using device:` prints before `PaddleOCR(...)` is built (phase 02 1.3, R16) | fixed: phase 02 1.3 |
| F80 | Nit | codebase fit | `resolve_output` docstring omits the page-of-folder rule (`cli.py`) | fixed: `cli.resolve_output` docstring |
| F81 | Nit | zoom out | The CPU comparison overwrites the GPU baseline `out/proto.txt` (notes Manual check; phase 02 3.2) | fixed: notes Manual check (separate GPU and CPU baselines) |
| F82 | Nit | zoom out | A PDF diff also measures the pypdfium2 upgrade; the colour page should come from an image folder (Risks) | fixed: Risks; notes Manual check (image-folder input) |
| F83 | Nit | zoom out | On the base install, R14's message appears only after the whole pre-check decodes every image (R14) | accepted: the wait is the pre-check's decode time, seconds per few hundred pages |
| F84 | Nit | zoom out | mypy is checked only on the base install; an extra's `py.typed` could change the result locally (phase 02 1.2) | fixed: phase 02 3.1 (with F64) |

## 2026-11-16 · waiver · phase 01 · impl-review re-check
The owner waived the fresh-reviewer re-check of the round 1 fixes (docs/reviews/README.md rule 6): "Is time to implement. Too many reviews." Every round 1 Major (F45, F46) was fixed test first with a mutation check; all three reviewers had completed. impl_review set to passed.

## 2026-11-16 · impl-review · phase 02 · round 1 · passed
Diff base 75c67e0, reviewed commit 6fabbf3. Reviewers: contract ✅ (the owner chose one reviewer, the contract lens; report in docs/reviews/2026-11-16-rebuild-cli/raw/impl-review-phase-02-round-01-contract.md). The two Majors were fixed after the round.

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F85 | Major | contract | No recorded pytest or mypy run with an extra installed, the only setup where R13 can fail (R13, task 3.1) | fixed: ran both extras, 150 passed, mypy clean, no leak; docs/demos/2026-11-16-ocr-check/README.md section 4 |
| F86 | Major | contract | The session-end check is never tested (R13, task 1.4) | fixed: `test_session_check_fails_a_run_that_imported_paddle` (pytester, mutation-checked) (bdd1039) |
| F87 | Nit | contract | The owner didn't read the differing lines; the agent used a letter edit-distance check (task 3.1) | accepted: the owner delegated the check; edit distance 0 rules out wrong words |
| F88 | Nit | contract | Manual-check facts are in a committed doc, not yet in the PR (task 3.1) | accepted: the PR description will link the demo when PR #7 is updated |
| F89 | Nit | contract | The fake PaddleOCR prints but doesn't log to stdout (task 1.2) | accepted: Paddle's loggers write to stderr (notes.md D3 re-check) |
| F90 | Nit | contract | Paddle's import and `resolve_device` run outside the stdout redirect (R11) | accepted: no import-time prints found; real runs showed 0 bytes on stdout |
| F91 | Nit | contract | `--device ""` is treated as not given (R15) | accepted: an empty device isn't a usable value |
| F92 | Nit | contract | The subprocess R13 test lists modules by hand (task 1.4) | accepted: matches every current module; revisit when one is added |
| F93 | Nit | contract | The broken-install test mocks `import_module` rather than a real native failure (task 1.3) | accepted: it tests the `exc.name` filter, which is the rule |
| F94 | Nit | contract | No test runs the installed console script (R19) | accepted: the manual check ran `.venv/bin/scanscribe` on both builds |

## 2026-11-16 · ADR review
ADRs in force reviewed: none existed. Created: ADR-0001, the OCR engine behind an interface, imported only when OCR starts (from D1, D2). The other decisions (D3–D9) are tactical or recorded in docs/decision-log.md, so they need no ADR.
