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
| F25 | Major | zoom out | Reopens F16: `Image.verify()` checks only PNG/WebP, so a damaged JPEG, TIFF or BMP passes the pre-check and fails hours into OCR (D6, Assumptions, phase 01 2.2) | open |
| F26 | Major | fresh reader | Summary says "two input rules change"; What changes lists five breaking changes | open |
| F27 | Major | fresh reader | The modules holding `load_engine` and `main()` are never named (D1, D2, R13) | open |
| F28 | Major | fresh reader | Phase files are never linked, though Risks and the Phases table cite their tasks | open |
| F29 | Major | fresh reader, codebase fit | R1 never says the natural sort ignores case; task 2.1 doesn't fold case | open |
| F30 | Major | fresh reader | How post-parse path checks (R10) give exit 2 in argparse's format is unstated; writability is only tested when the temp file is created (D6, D7) | open |
| F31 | Major | fresh reader, zoom out | Reopens F10: "reads worse" has no criterion, nothing says what unblocks phase 02, and a grayscale input can't test D4 | open |
| F32 | Major | fresh reader | D6's first sentence is ~50 words of seven steps; needs a numbered list | open |
| F33 | Nit | codebase fit, zoom out | Multi-line exception messages (Paddle's C++ traceback) break R12's one line; there is no way to get a traceback for diagnosis | open |
| F34 | Nit | codebase fit, zoom out | Temp file name, timing and mode are unspecified: `mkstemp` makes the output 0600, and an early temp file can be orphaned by a hard kill (D6) | open |
| F35 | Nit | codebase fit | R5 pre-check uses width × DPI / 72, but pypdfium2 renders `ceil(width × scale)` (phase 01 2.2) | open |
| F36 | Nit | codebase fit | The flipped array `image[:, :, ::-1]` isn't C-contiguous; use `np.ascontiguousarray` (phase 02 1.2) | open |
| F37 | Nit | codebase fit | The manual-check `<input>` resolves differently after `cd ../ocr-pdf`; use an absolute path (notes Manual check) | open |
| F38 | Nit | codebase fit | The manual check doesn't confirm stdout stays empty with real Paddle (R11, phase 02 3.1–3.2) | open |
| F39 | Nit | codebase fit | No test checks the option defaults or that `--help` lists every option (R19, phase 01 4.1) | open |
| F40 | Nit | codebase fit | Impact leaves out AGENTS.md, whose Status line goes stale when phase 02 merges | open |
| F41 | Nit | zoom out | D2 maps any `ImportError` under `paddle` to "install the extra", including a broken installed build; map only `ModuleNotFoundError` named exactly `paddle`/`paddleocr` | open |
| F42 | Nit | zoom out | Rollout doesn't say whether the downstream consumer (`study-book-chapter`) is affected | open |
| F43 | Nit | zoom out | Ctrl-C (R20) is never observed with real Paddle; add it to the manual check | open |
| F44 | Nit | fresh reader | Small wording gaps: rename drawn on the per-page line, R11 vs `--help` on stdout, R4 half rounding, "PP-OCRv6"/"locked version", "hidden", 5.13.0's meaning, D4 causality, the Risks arrow, R10's two "before" points | open |
