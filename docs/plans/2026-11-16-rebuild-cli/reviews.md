# Reviews · Rebuild the scanscribe CLI from the ocr-pdf prototype

## 2026-11-16 · design-review · plan · round 1 · changes-requested
Reviewers: fresh reader ✅ · codebase fit ✅ · zoom out ✅ (commit 283b8f4; reports in docs/reviews/2026-11-16-rebuild-cli/raw/)

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F1 | Major | codebase fit, zoom out | Output that is an existing directory or not writable still fails only at the final write; `OSError` there prints a traceback; the write is not atomic (R10, D6, D7) | open |
| F2 | Major | codebase fit, zoom out | Fake-module tests leave `scanscribe.paddle_engine` cached, and the R14 test relies on Paddle being absent, so it fails on a machine with an extra (phase 02 1.2, 1.3; Risks) | open |
| F3 | Major | codebase fit, zoom out | The R13 subprocess test imports `paddle_engine`, contradicting D2, and argparse's `--help` exits before the assertion (phase 02 1.4) | open |
| F4 | Major | zoom out, codebase fit | PDF rendering can yield BGR (`to_numpy()`); the adapter flip would then send RGB for PDFs; there is no colour test (phase 01 2.2, D4) | open |
| F5 | Major | fresh reader, codebase fit, zoom out | R12 "one line" conflicts with argparse's two-line usage error (R9); whether `run` catches `SystemExit` is unstated (R9, R12, D7, task 4.1) | open |
| F6 | Major | fresh reader | Summary says inputs stay the same and errors come before OCR (R5–R12), but R1 skips dotfiles, R6 renames dotted-folder output, and R8/R12 cover failures during OCR; the prototype's options are never listed | open |
| F7 | Major | fresh reader | It is not said where the device is chosen (R15) or how `Using device:` reaches stderr (R16), given the factory takes `(lang, device)` (D1, D2) | open |
| F8 | Major | fresh reader, codebase fit | Where and when the R5 width check runs, and how it gets the page label, is unstated (R5, D6, tasks 2.3, 4.3) | open |
| F9 | Major | fresh reader | R4 says "±1 px" but not the rule for where the remainder goes | open |
| F10 | Major | fresh reader, zoom out | The manual check records a diff count but has no pass/fail rule; "newer locked versions" is wrong (only pypdfium2 differs) (Summary, Risks, phase 02 3.1) | open |
| F11 | Major | fresh reader | PaddleX, MKL-DNN (and why it is off on CPU), and the fake Paddle modules are used but never defined (D3, R17, Risks) | open |
| F12 | Major | fresh reader | The Phases table does not say which requirements each phase delivers | open |
| F13 | Major | fresh reader, codebase fit | D8 cites pypdfium2 5.13, but `uv.lock` has 5.15.2 | open |
| F14 | Nit | codebase fit, zoom out | R7 "text file as input" scenario hits R10 if the file is named `*.txt` with no `-o` | open |
| F15 | Nit | codebase fit | Pillow writes RGB PDFs as JPEG, so exact `rgb{r},{g},{b}` from the fake engine won't match 255 (notes D9) | open |
| F16 | Nit | codebase fit, zoom out | The truncated-image fixture is ambiguous and unused; `Image.verify()` would catch it in the pre-check (task 1.2, Assumptions) | open |
| F17 | Nit | zoom out | Header pre-check must close each image, or folders over ~1024 pages run out of file descriptors (task 2.2) | open |
| F18 | Nit | zoom out | Ctrl-C prints a `KeyboardInterrupt` traceback; map it or exempt it from R12 | open |
| F19 | Nit | zoom out | Two overlapping first runs may race on the model download cache; README could say so | open |
| F20 | Nit | structure | plan.md has 291 body lines (budget 250) | open |
| F21 | Nit | fresh reader | R3 "nothing follows the last page" reads as contradicting the example's final `\n`; "lines `a`,`b` and none" is hard to parse | open |
| F22 | Nit | fresh reader | R1, R3, R6, R7, R10, R11 each hold several conditions | open |
| F23 | Nit | fresh reader | Facts stated twice: exit codes (Terms, D7), hidden files (R1, Assumptions), PDF-only file input (Non-goals, R2), empty input (R7, D8) | open |
| F24 | Nit | fresh reader | Minor gaps: Summary cites D1 for lazy import; "the owner", `rec_texts`, "which sources" undefined; `a.png`/`A.png` order unstated; empty Decision log | open |
