Review of /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/plan.md

Overall: the plan stands on its own. Every section could be paraphrased and there are no Blockers. The main problems are that the "five breaking changes" count can't be checked from the plan, R3 says two different things about the output format, Ctrl-C has no stated mechanism, and the PDF pre-check in R5/R8 is unclear.

## From the Summary
scanscribe has a project skeleton but no command yet. The plan rebuilds the `ocr-pdf` prototype's CLI as `scanscribe`, keeping its options and its `--- Page N ---` output. Along the way it puts the OCR engine behind an interface, imports Paddle only at OCR time so CI and tests never load it, picks and prints the device itself, and sends images to PaddleOCR in BGR. It also catches bad arguments, empty or unreadable inputs and unwritable outputs before OCR, and never leaves a half-written output. The main risk is that the BGR fix changes the OCR text. The owner's manual check on GPU and CPU blocks phase 02 if any page reads worse than the prototype's.

## From the whole plan
The plan rebuilds the prototype as a tested, CI-friendly `scanscribe` command. Phase 01 builds the page pipeline (folder/PDF page sources, column slicing, output formatting) and the CLI against a fake engine that reads colors from generated fixtures. Phase 02 adds a PaddleOCR adapter, which loads Paddle lazily, picks the device, turns MKL-DNN off on the CPU and flips images to BGR, plus the console command. The reason is that the prototype is GPU-only and untested, can't run in CI, and fails badly on some inputs: wrong output name for `Vol.2`, empty output for empty inputs, and a crash on an unwritable output only after the whole book has been OCR'd. Five intentional breaks with the prototype are listed. Everything else, including the output format, is meant to stay the same.

## How the existing system works, per this plan
The repository has CI, review rules, and exclusive `gpu`/`cpu` extras, but no command, and its README says "under construction". The prototype `ocr-pdf`, which lives outside the repo, takes a PDF or a folder of images with `-o`, `--lang`, `--dpi`, `--device` and `--columns`. It renders PDFs with pypdfium2 5.13.0, cuts pages into equal-width columns, passes RGB arrays to PaddleOCR (which expects BGR) with three orientation/unwarping flags off, and writes `--- Page N ---` blocks. In its edge cases it names a folder `Vol.2`'s output `Vol.txt`, writes empty files for empty inputs, accepts `--columns`/`--dpi` below 1, includes hidden files, and fails on an unwritable output only after all OCR is done. It only works on the GPU build. A downstream `study-book-chapter` skill reads its text output.

## Summary vs plan
- Major, Summary / What changes: "Five behaviors break parity" undercounts, or at least can't be checked. The plan also adds stderr-only progress (R11), one-line errors with no traceback (R12), exit 130 on Ctrl-C (R20), exit 2 for path problems (R10), a printed device line (R16), automatic device choice (R15), an error for pages narrower than the column count (R5), and an atomic replace instead of a truncating write (D6). The plan never says what the prototype did in these cases; it points to notes.md#prototype. So the reader can't tell whether these are also breaks, for example if the prototype printed progress to stdout.
- Nit, Summary vs Risks: the Summary says the manual check "blocks phase 02" outright, but Risks says the owner can lift the block by accepting the result or by reversing D4.
- Nit, Summary: it says the tests never import Paddle, but R13 also covers importing the non-adapter modules and `scanscribe --help`.
- Nit, Summary: "caught before OCR starts" covers R10 and the pre-checks, but R14 (missing engine) and D7 (exit codes) aren't mentioned. That's acceptable for a summary.

## Sections I couldn't paraphrase
- None. No Blockers.

## Terms used but never explained
- Nit, frontmatter: `design_review: changes-requested` sits next to `approved: 2026-11-16`, so it's unclear whether the plan is approved. `adr_review` is unexplained.
- Major, Summary / Risks: the "owner's manual check" gates the main risk, but the plan only gives fragments of it ("includes a color page", "a page reads worse when a word the prototype got right is wrong"). Which material it uses, how pages are compared, and what GPU vs CPU means for the result all live in notes.md#manual-check.
- Nit, D2 / D7 / Assumptions: "the R12 line" is shorthand for the `scanscribe: error:` line and is never defined as such.
- Nit, Decision log: "impl review F55" is unexplained.
- Nit, Rollout: the `study-book-chapter` skill is not introduced.
- Nit, Terms (MKL-DNN): "PP-OCRv6" is not introduced.
- Nit, Impact: "the Status line in `AGENTS.md`" is not explained.
- Nit, Risks: "phase 02 task 1.1 / 1.2 / 1.3" are references into phase files the reader can't see.

## Parts that don't connect
- Major, R20 / D7: D7 catches every `Exception`, but Ctrl-C raises `KeyboardInterrupt`, which is not an `Exception`. Nothing says what catches it, prints the one `scanscribe: error:` line, returns 130, or what the message text is. It's also unclear whether `SCANSCRIBE_DEBUG` applies. D6's "Any failure deletes the temp file" probably covers cleanup, but that isn't stated for interrupts.
- Major, R3: the rule says pages are "joined by one blank line", and a page with no lines renders as `--- Page N ---\n`. Joining that mechanically with `\n\n` leaves two blank lines after an empty page that isn't last. The only example puts the empty page last, so it doesn't settle which reading is meant. This is the format that has to match the prototype exactly.
- Major, R5 / R8 / D6 step 3: for PDFs, the pre-check only "read[s] each PDF page's rendered width". It's unclear whether that means rendering every page twice or computing the width from page size × DPI. If computed, rounding could differ from the real render that R4 splits. Also, a PDF page that fails to render is caught only during OCR, after the engine loads. R8's title and first bullet suggest unreadable pages are caught up front, which holds only for images.
- Major, R8: the second bullet (a page fails during OCR, so the existing output stays identical) is about engine failure, not an unreadable page. The requirement mixes two rules under one title.
- Major, D1 / Rollout / Phases: `cli.main()` passes `engine.load_engine`, but `load_engine` and the command belong to phase 02. The plan never says what `cli.main` is, or whether it exists, after phase 01.
- Nit, R10 / D5: it's unclear whether "an output that resolves to the input" also applies to the default output. For example, a file input `x.txt` would default to itself under `with_suffix(".txt")`.
- Nit, D5: the title says the output comes from the "resolved input name", but the file rule uses `input.with_suffix(".txt")`, which is not resolved.
- Nit, R10: the plan doesn't say how "not writable" is checked, for example `os.access` or a trial write.
- Nit, D6: it's unclear whether images decoded in the pre-check are kept or decoded again for OCR. Assumptions only covers keeping text in memory.
- Nit, Assumptions (symlink) vs D6: "the old output's mode" is ambiguous when the output is a symlink: the link's mode or its target's?
- Nit, Risks: "re-checks the source references in notes.md" only makes sense with notes.md.

## Readability
- Nit, R1: the main sentence is about 55 words and holds several rules (regular files, no dot prefix, extensions, case-insensitive natural sort, tie-break).
- Nit, R10: the main sentence is about 50 words and holds five separate rules.
- Nit, R4: about 38 words, with a nested parenthetical. I had to reread it.
- Nit, R5 / R6 / R7 / R11: each holds two rules (R11: progress goes to stderr, and only `--help` writes to stdout).
- Nit, D1: in "cli.main() passes engine.load_engine (D2), which also chooses and prints the device", "which" could refer to either function.
- Nit, D4: "Page sources yield RGB: images through Pillow's convert(...), PDF pages through to_pil().convert(...)". I had to reread it.
- Nit, D9: "which absorbs JPEG shifts in Pillow-written PDFs". I had to reread it, and it's unclear why the fixture PDFs are JPEG.
- Nit, Risks bullet 1: the definition "A page reads worse when..." sits between the mitigation and "Phase 02 then stays blocked", so "then" is hard to follow.
- Nit, repetition: the BGR change appears in the Summary, What changes, D4 and R18. The MKL-DNN crash appears in Terms and again implied in R17/D3. The phase 02 blocking appears in the Summary and Risks. Each is worded slightly differently.
