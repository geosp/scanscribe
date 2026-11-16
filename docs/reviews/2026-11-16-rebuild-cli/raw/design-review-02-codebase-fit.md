I found no Blockers and no Majors, plus 9 Nits.

**Scope.** I reviewed revision d5f1a46 (the plan files are the same at HEAD 2693c77; the only later change is a saved review report). There are no ADRs (docs/adrs/README.md: "There are no ADRs yet"), so check 4 does not apply.

**Claims I confirmed against the repository**
- **Locked versions** in uv.lock: paddleocr 3.7.0, paddlex 3.7.2, paddlepaddle and paddlepaddle-gpu 3.3.1, and pypdfium2 5.15.2. This matches notes.md › Prototype and plan Risks ("only pypdfium2 differs").
- **pypdfium2 has no type marker.** There is no `py.typed` anywhere under .venv/lib/python3.12/site-packages/pypdfium2*. So phase 01 task 2.4's mypy override will be needed, not just "only if".
- **The rendering facts are correct.** In pypdfium2/_helpers/page.py, `rev_byteorder=False` is the default at line 520, and `render()` sets the width to `ceil(width*scale)` (around line 465). I ran these checks in the scratchpad with the repo's .venv:
  - A 72 px Pillow PDF page renders at 144 px with `--dpi 144` (R2).
  - A red page comes back as (254, 0, 0) through `to_pil().convert("RGB")` (notes D4 and D9).
  - `PdfDocument.new().save()` and then reopening it raises `PdfiumError`, which is a RuntimeError ("Failed to load document (PDFium: Success)"), and `notes.dat` raises `PdfiumError` too (D8).
  - A PNG cut to 60 bytes fails `Image.verify()` with `OSError: Truncated File Read` (notes D9, task 1.2).
- **Repository facts are correct.** `.gitignore` has `!tests/fixtures/**`. pyproject has no `[project.scripts]` yet, has mypy `strict = true` with `packages = ["scanscribe"]`, and the cpu/gpu extras conflict. The README has the "under construction" status, and the decision-log entries cited in Links exist. CI installs only the base dependencies, so it needs no change.
- **I could not check** the PaddleX, PaddleOCR and Paddle source references (notes D3 and D4) or the prototype from inside the repository, because none of them is installed here. Phase 02 task 1.1 re-checks them, which is the right place.
- **Task counts and order are right.** The Phases table's 0/12 and 0/8 match the phase files. The tasks build in order, and between them the two phases cover every requirement and carry out D1–D9.

**Nits**

1. **plan.md › R1 vs phase 01 task 2.1: case handling in the sort is unstated.** R1 treats `a.png`/`A.png` as a tie broken by exact name, which only happens if the sort key ignores case. Task 2.1 ("Split on `\d+` and convert only the digit parts") never says to fold case, and without that I measured `['Page10.png', 'page1.PNG', 'page2.png']`. State whether the text parts are case-folded.

2. **plan.md › R12 and D7: messages that span several lines are not handled.** D7 prints "the R12 line" from the exception text as-is. Assumptions says "A bad value gives PaddleOCR's own message on the R12 line". Paddle errors usually span several lines, and some contain "C++ Traceback", which would break "one line … no Traceback". Say that newlines are collapsed or only the first line is kept, and add a test with a message that spans lines. I could not check the Paddle source here.

3. **plan.md › D6 / phase 01 task 4.2: output file permissions change.** The plan never says how the temp file is created. `tempfile.mkstemp` or `NamedTemporaryFile` creates it as 0600, so `os.replace` leaves the output owner-only. It also replaces an existing file's mode, and replaces a symlink at the output path instead of writing through it. The prototype's `write_text` gave a umask-default mode.

4. **phase 01 task 2.2: the R5 pre-check width can be off by one pixel.** The pre-check reads "width × DPI / 72", but the render uses `math.ceil(self.get_width() * scale)` (pypdfium2/_helpers/page.py, around line 465). Use the same ceil, or a fractional page width could falsely fail R5.

5. **phase 02 task 1.2 / R18: the flipped array is not contiguous.** `image[:, :, ::-1]` is not C-contiguous (verified: `C_CONTIGUOUS False`), and some cv2 calls reject such arrays. The fake-module test can't catch that. Say `np.ascontiguousarray`.

6. **notes.md › Manual check (lines 100–103): `<input>` may point at two different files.** The prototype command runs inside `cd ../ocr-pdf`, so a relative `<input>` such as `in/x.pdf` resolves against the prototype's folder, not scanscribe's `in/`. It could fail or quietly compare different files. Say to use an absolute path.

7. **plan.md › R11 vs phase 02 › 3: the empty-stdout rule is only tested with the fake engine.** The manual check doesn't confirm stdout stays empty when real PaddleOCR/PaddleX log while loading models. Add "stdout empty" to what 3.1 and 3.2 record. Where PaddleX writes its logs is unverified here.

8. **R19 / phase 01 task 4.1: option defaults are not tested.** No test checks the defaults (`--lang en`, `--dpi 200`, `--columns 1`) or that `--help` lists every option. Task 4.1 only checks that `--help` returns 0.

9. **Front matter and Impact are stale.**
   - plan.md:6 and both phase files (line 8) say `design_review: { status: passed, rounds: 1 }`, but docs/reviews/2026-11-16-rebuild-cli/design-review-01.md has `verdict: FAIL` and reviews.md has "round 1 · changes-requested". docs/reviews/README.md › Gate rules 5–6 need a fresh re-check before "passed".
   - plan.md › Impact leaves out AGENTS.md, whose Status line ("The first implementation plan, rebuilding the CLI, is next") goes stale once phase 02 merges.

**Files referenced**
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/plan.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/phases/01-pipeline-and-cli.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/phases/02-paddleocr-adapter.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/notes.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/reviews.md
- /home/geo/develop/projects/scanscribe/docs/reviews/2026-11-16-rebuild-cli/design-review-01.md
- /home/geo/develop/projects/scanscribe/docs/reviews/README.md
- /home/geo/develop/projects/scanscribe/pyproject.toml
- /home/geo/develop/projects/scanscribe/uv.lock
- /home/geo/develop/projects/scanscribe/.gitignore
- /home/geo/develop/projects/scanscribe/AGENTS.md
- /home/geo/develop/projects/scanscribe/.venv/lib/python3.12/site-packages/pypdfium2/_helpers/page.py
