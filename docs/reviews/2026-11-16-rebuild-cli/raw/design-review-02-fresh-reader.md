I read `/home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/plan.md` and nothing else. For Pass 1 I read the Summary, which is lines 13–33 including the pipeline diagram. The first read also showed me lines 35–40, the opening of "Why". I wrote my Pass 1 answer from the Summary alone.

## From the Summary
The repo has a project skeleton but no working command, and this plan rebuilds the `ocr-pdf` prototype as a `scanscribe` command. It keeps the prototype's options and its `--- Page N ---` output format. The OCR engine moves behind an interface and Paddle is imported only when OCR starts, so CI and the tests can run without PaddlePaddle. Bad arguments and inputs are caught before OCR, a failed run leaves the output file untouched, the tool picks and prints the device, images are passed to PaddleOCR in BGR order, and two input rules change. The main risk is that the BGR fix changes the recognized text, so the owner's manual check on GPU and CPU can block phase 02.

## From the whole plan
The plan builds a tested `scanscribe` CLI in `src/scanscribe/`: page sources (an image folder or a PDF rendered at a chosen DPI), equal-width column slicing, output formatting, and a one-method `OcrEngine` protocol passed into `cli.run`. A PaddleOCR adapter is loaded lazily through `load_engine`. The reason is that the prototype only works on the owner's GPU machine, has no tests, can't run in CI, and fails badly on some inputs: `Vol.2` writes `Vol.txt`, empty folders give empty files, and an unwritable output crashes only after the whole book is OCR'd. Everything is checked before OCR. Output goes to a temp file that is renamed onto the target at the end. Exit codes are 0, 1, 2 and 130. Phase 01 builds everything against a fake engine; phase 02 adds the real adapter, device selection, MKL-DNN handling, the BGR flip and the console script.

## How the existing system works, per this plan
The prototype `ocr-pdf` lives outside the repo. It takes a PDF or a folder of images with `-o`, `--lang`, `--dpi`, `--device` and `--columns`, and it only works with the GPU build of Paddle. It passes RGB arrays to PaddleOCR, which reads them as BGR. It names a folder's output with `with_suffix`, writes an empty file for empty inputs, and fails on an unwritable output only after OCR. It apparently writes the output directly, so the old file is truncated first. It sets three PaddleOCR flags to `False`. The scanscribe repo already has CI, review rules, mutually exclusive `gpu`/`cpu` extras, a decision log and a README that says "under construction", but no command yet. The plan does not say how the prototype picks a device, whether it disables MKL-DNN, how it orders or filters folder files, or where it prints progress.

## Summary vs plan
- **Major**, Summary vs What changes: the Summary says "Two input rules change" (R1, R6). The plan lists five breaking changes: BGR (D4), `--columns`/`--dpi` below 1 rejected (R9), empty inputs become errors (R7), hidden files skipped (R1), and `Vol.2.txt` (R6). R7 is also an input rule change. A Summary reader would not know the other three break prototype behavior.
- **Nit**, Summary diagram line 32: "rename temp onto output" sits on the "per page:" line, which reads as a rename after every page. D6 and the Non-goals say one rename at the end.
- **Nit**, Summary: "unreadable inputs … are caught before OCR starts" is stronger than the Assumptions. `Image.verify()` misses some damaged JPEGs, which then fail during OCR (R8).
- **Nit**, Summary: R17 (MKL-DNN off on CPU) and R14 (the missing-engine message naming the install commands) are not mentioned, though both are user-visible.
- **Nit**, Summary: it leans on R/D IDs that mean nothing before you read further, for example "(R5–R12, R20, D6)".

## Sections I couldn't paraphrase (Blockers)
None. Every section could be paraphrased.

## Undefined project-specific terms
- **Major**, D1/D2 `load_engine` and `main()`: the plan never says which module they live in. The `What changes` module list doesn't include them, and D2 says `load_engine` is *not* in `scanscribe.paddle_engine`. R13 depends on where it lives.
- **Major**, Risks and Phases: "phase 02 task 1.1", "tasks 1.2, 1.3" and the Phases table task counts (0/12, 0/8) point to phase documents that are never linked or located.
- **Major**, R1 "natural filename order": the plan never says whether the comparison ignores case. The examples (`page1.PNG` before `page2.png`; `a.png` and `A.png` treated as a tie) imply it does, but the rule doesn't state it.
- **Nit**, Terms/MKL-DNN: "PP-OCRv6" and "the locked version" (of which package?) are not explained.
- **Nit**, R1: "hidden" is not defined. The example `._page1.jpg` suggests a leading dot, but the rule doesn't say.
- **Nit**, D8: "pypdfium2 (5.13.0, and 5.15.2 as locked)" never says what 5.13.0 is, presumably the prototype's version.
- **Nit**, D9: "JPEG shifts in Pillow-written PDFs" and "palette" are only half explained.
- **Nit**, Summary/Risks: "the owner's manual check" is defined only in notes.md#manual-check.

## Places where the parts don't connect
- **Major**, R10 vs D7 vs D6: R10 makes an unwritable output directory a usage error with exit 2. D7 says exit 2 comes from argparse's `SystemExit`, and that after parsing every `Exception` returns 1. No step explains how the post-parse path checks in R10 produce exit 2 in argparse's format (for example via `parser.error`). Writability is also only exercised when the temp file is created (D6 step 4, after the page pre-check), and a failure there would exit 1.
- **Major**, Risks bullet 1 and Summary: the main risk's mitigation depends on notes.md. "Reads worse" has no criterion, and nothing says what happens after phase 02 is blocked: revisit D4, fix, or accept.
- **Nit**, D7/R20: D7 catches `Exception`, which doesn't include `KeyboardInterrupt`. The plan states exit 130 but not how Ctrl-C is caught or how the temp file is cleaned up then. "Any failure deletes the temp file" covers that only by implication.
- **Nit**, R11 vs R19: "All progress and messages go to stderr … stdout stays empty", but `--help` (R19) prints to stdout through argparse.
- **Nit**, R10: the rule says "before any page is read", but the write-permission example only says "before the engine loads".
- **Nit**, R4: `round(...)` doesn't say whether halves round to even (Python's default) or away from zero.
- **Nit**, R3: there's no example where the last page has lines, which would show the file has no trailing newline in that case.
- **Nit**, Impact vs What changes: `docs/decision-log.md` changes are listed only under Impact.

## Readability
- **Major**, D6 first sentence: about 50 words, seven steps in one semicolon list with nested parentheticals. It needs a numbered list.
- **Major**, requirements that hold more than one rule: R1 (file type, hidden, depth, extensions, case, order, tie-break), R3, R7, R8 (error plus output untouched), R10 (four path conditions), R11, R12, R19, R20 (exit code, message, file untouched, no temp file).
- **Nit**, R1 statement: about 35 words and dense. Not over 40, but I had to reread it.
- **Nit**, R10 statement: about 37 words with four conditions. I had to reread it.
- **Nit**, R1 second example: "a subfolder named `x.png`, `notes.txt` and `._page1.jpg`" reads as if all three are subfolders. I had to reread it.
- **Nit**, D4: "as the prototype did, since pypdfium2's raw buffer is BGR" has unclear causality (it means: don't use the raw buffer). I had to reread it.
- **Nit**, Risks bullet 1: the "→" in the middle of a sentence ("mostly measures D4 → the owner reads…") is confusing.
- **Nit**, duplication: "found/raised before any page is read" appears in both Terms/Usage error and R10.
- **Nit**, duplication: "output untouched" is stated in the Summary, R8, R20 and D6, and "Paddle only in `load_engine`" in D1, D2 and R13. Acceptable, but they could drift apart.
