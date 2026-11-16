I read /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/plan.md. In Pass 1 I read only lines 1-40, which hold the Summary (lines 13-30). In Pass 2 I read the rest of the file. I opened nothing else.

## From the Summary
The plan rebuilds the prototype `ocr-pdf` tool as a `scanscribe` command inside a repository that has a skeleton but no command yet. Inputs, options and the `--- Page N ---` output format stay the same. The OCR engine moves behind an interface and Paddle is imported only when needed, so CI and the tests never need PaddlePaddle. The device is chosen explicitly and printed. Images are sent to PaddleOCR in BGR order. Failures become clear errors before OCR starts. The main risk is that the output text changes, from the BGR fix and newer Paddle versions; a manual GPU/CPU comparison against the prototype's output is the mitigation.

## From the whole plan
The plan builds `scanscribe` in two phases. Phase 01 is a page pipeline: list the pages of a folder or PDF, render them, cut them into equal-width column slices, recognize each slice and format the result. It is driven by a CLI and tested against a fake engine that reads solid colors. Phase 02 adds a PaddleOCR adapter that is loaded lazily, picks the device, flips RGB to BGR and is checked by hand. The reasons: the prototype runs only on the owner's GPU build, has no tests and can't run in CI. It also mishandles inputs: `Vol.2` becomes `Vol.txt`, an empty folder gives an empty file, and a missing output directory crashes only after the whole OCR run. The new tool validates everything up front, keeps the text in memory, writes the file once at the end, and uses exit codes 0/1/2 with one-line errors.

## How the existing system works, per this plan
The prototype `ocr-pdf` lives outside this repository. It takes a folder of images or a PDF and renders PDFs at a DPI. It can split pages into columns and writes `--- Page N ---` blocks to a `.txt` next to the input. It passes RGB arrays to PaddleOCR, with three orientation/unwarping flags off. It only works with the GPU Paddle build. It derives a folder's output name with `with_suffix`, includes hidden files such as `._page1.jpg` and then crashes, and writes an empty file for an empty input. It shows tracebacks on errors, overwrites existing output without asking, and keeps the text in memory until one write at the end. The repository itself has CI, review rules and mutually exclusive `gpu`/`cpu` extras, but no CLI code.

## Summary vs plan
- Major, Summary vs R1/R6/Assumptions: "Inputs ... stay the same" is not accurate. R1 now skips hidden files, which the prototype included (Assumptions). R6/D5 change the default output name for dotted folders. Neither appears in the "BREAKING" list in What changes.
- Major, Summary vs R8/R12: "clear errors, raised before OCR starts (R5–R12)" is wrong for part of that range. R8's second example and R12's example are failures during OCR (an engine raising on page 2). R6 and R11 are not errors at all.
- Major, Summary vs R19/R15: the Summary says options stay the same. The plan never lists the prototype's options, so it's unclear whether `--device` is new. If it is new, the Summary is wrong and What changes leaves it out.
- Nit, Summary: it cites "(D1, D2)" for lazy import, but D1 is the engine protocol and only D2 covers lazy import.
- Nit, Summary: it says CI "never install[s] PaddlePaddle", while R13 is about never *importing* it, including on machines that have an extra installed (Risks).
- Nit, Summary: it leaves out exit codes (D7), the missing-engine message (R14) and the MKL-DNN rule (R17).
- Nit, Summary diagram: the R5 width check isn't placed anywhere in the flow.
- Nit, Summary: "records every difference" vs Risks "records the result". It's not clear which one applies.

## Sections I couldn't paraphrase
No findings. I could paraphrase every section. "Decision log" (the last heading) is empty, which is covered under item 7.

## Unexplained project-specific terms
- Major, D3: "PaddleX" is never introduced, and neither is its relation to PaddleOCR. The decision rests on "the same check PaddleX uses".
- Major, R17/D3: MKL-DNN / `enable_mkldnn`. Nothing says why it must be off on CPU and left alone on GPU (see item 6).
- Major, Risks: "unit tests use fake modules". Fake `paddle`/`paddleocr` modules are a separate test mechanism from the fake engine and are never described in Terms or D9.
- Nit, D2/D7: `ScanscribeError`, `EngineMissingError`, `load_engine`, `scanscribe.paddle_engine` and `cli.run`/`main()` are named but their module layout and error hierarchy aren't.
- Nit, D1 vs D2: "the PaddleOCR loader" (D1) and `load_engine` (D2) are probably the same thing, but the plan never says so.
- Nit, Risks: "the `rec_texts` key" isn't explained.
- Nit, Risks: "phase 02 re-checks the sources" doesn't say which sources.
- Nit, Summary/Non-goals: "the owner" and "the owner's manual check" are defined only by a link to docs/reviews/README.md.
- Nit, Links: "the no-book-material rule" and "gate review rules" aren't explained.
- Nit, front matter: `design_review` and `adr_review` are process fields with no explanation.

## Places where the parts don't connect
- Major, D1 vs R15/R16: the factory takes `(lang, device)`. The automatic device choice (R15) needs Paddle, so it has to live inside the loader. But `cli.run` must print "Using device: …" (R16). The plan never says where device detection happens or how the CLI learns the chosen device. It also doesn't say how R16 is tested with the fake engine.
- Major, R12 vs R9/D7: R12 says every error is one stderr line with no traceback. R9 requires argparse's usage message, which is several lines (`usage: …` then `scanscribe: error: …`). D7 catches only `ScanscribeError` and Pillow/pypdfium2/engine exceptions, so anything else still prints a traceback. An `OSError` on the final write would be one example. Assumptions also expects PaddleOCR's "own message", which may not be one line.
- Major, R5 vs D6: the plan doesn't say where the width check happens. D6's order (validate, list, header pre-check, load engine, OCR) and the diagram ("pre-check pages (R7, R8)") leave R5 out. For PDF pages the pixel width depends on DPI, and "open every page's header" isn't defined for PDF pages at all.
- Major, R4: the rule for where the extra pixels go isn't stated. The example 33/34/33 implies remainders go in the middle (rounded boundaries), but "±1 px" allows 34/33/33 too. An implementer would have to reverse-engineer the rule from the test.
- Major, Summary/Risks (main risk): the mitigation is to diff and record. Nothing says where the results are recorded, how large a difference is acceptable, or what happens if the diff is bad. The procedure lives in docs/reviews/README.md. The plan's main risk therefore has no stated acceptance criterion.
- Major, Phases: the table gives 12 and 8 tasks, but the plan doesn't list them, link to phase documents, or map R/D IDs to phases. From R19 and Rollout I can infer that R13–R19 belong to phase 02, but the plan doesn't say so. R13 tests `scanscribe --help`, which can't exist until phase 02.
- Major, D8 vs Risks: D8 cites "pypdfium2 5.13" refusing zero-page PDFs, but Risks names pypdfium2 5.15.2. It's unclear which version the R7 behavior was checked against.
- Major, R17: this is a mechanism with no stated goal (no reason for disabling MKL-DNN on CPU). The rationale may be in notes.md#d3.
- Nit, D4: the claim that PaddleOCR reads NumPy input as BGR is supported only by notes.md#d4. The decision is clear, but the evidence lives elsewhere.
- Nit, R13 vs Risks: inserting fake `paddle` modules into the tests may conflict with an R13 check that `paddle` was "never imported". The plan doesn't say how the two coexist.
- Nit, Impact: it lists `docs/decision-log.md`, but nothing says what entry is added there.
- Nit, Terms "Page image": nothing says how grayscale, RGBA or CMYK inputs (TIFFs, for example) are converted to RGB.
- Nit, R1: `a.png`/`A.png` must sort the same way every run, but the actual order is never stated.
- Nit, D5: there's no rule for a file input with no suffix.
- Nit, R11: the format of "the output path at the end" isn't given.

## Readability
- Nit, Summary: "The prototype's tracebacks and silent mistakes become clear errors, raised before OCR starts" had to be reread and is inaccurate (see Summary vs plan).
- Nit, R3: "pages are separated by one blank line, nothing follows the last page" conflicts on first read with the example ending in `--- Page 2 ---\n` (a trailing newline does follow).
- Nit, R3: "two pages with lines `a`,`b` and none" is hard to parse.
- Nit, D3 heading: "with PaddleX's own check" had to be reread because PaddleX is undefined.
- Nit: no sentence is over about 40 words. The longest is R1's statement, at about 30.
- Nit, R1: one requirement holds several rules (regular files, non-hidden, not recursive, extension list, any case, natural order).
- Nit, R3: holds four rules (marker, blank-line separator, nothing after the last page, UTF-8).
- Nit, R10: holds three rules (missing input, missing output dir, output equals input).
- Nit, R11: holds three rules (stderr only, per-page progress line, output path at the end).
- Nit, R6 and R7: each holds two rules (PDF vs folder).
- Nit, duplication: exit codes are defined in both Terms (Usage/Input error) and D7.
- Nit, duplication: "a file input is always opened as a PDF" appears in both Non-goals and R2.
- Nit, duplication: hidden files are skipped per both R1 and Assumptions.
- Nit, duplication: in-memory, write-once appears in D6, Assumptions and the Summary diagram.
- Nit, duplication: the empty-input error appears in both R7 and D8.
- Nit, duplication: the manual owner check appears in the Summary, Non-goals, Risks and Links.
- Nit, "Decision log": the final heading is empty.
- Nit, "Open questions": it says "None" as a list item.
