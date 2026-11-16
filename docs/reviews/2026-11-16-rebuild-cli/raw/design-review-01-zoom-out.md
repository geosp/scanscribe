## Design review: docs/plans/2026-11-16-rebuild-cli (commit 283b8f4)

I found four Major issues and eight Nits. There are no Blockers.

**Summary by question**
- **Root cause:** mostly fixed. The Why says "A missing output directory crashes only after the whole book has been OCR'd". The real cause is that the output is only written, and only found to be bad, at the end of the run. The plan fixes the missing-directory case but not the others (M1).
- **Simplicity:** the design is already small. The one-method protocol and the factory injection are justified, and nothing is built for a future need.
- **Placement:** all the code is new, and the layout (`pages.py`, `output.py`, `cli.py`, `engine.py`, `paddle_engine.py`) is reasonable. `src/scanscribe/__init__.py` is the only existing module.
- **Rollout:** adequate for a local CLI. Each phase has its own PR, there is no data migration, and rollback is a revert. Nothing is missing.

### Major

**M1 · A late write failure still loses the whole run, prints a traceback, and the write is not atomic**
- **Where:** plan.md › Decisions › D6 (lines 217-222), D7 (lines 224-229) and R10 (lines 126-130); phase 01 › tasks 4.1 and 4.3.
- **What is wrong:**
  - R10 checks only for "a missing output directory". It does not catch an output path that is an existing directory, a directory you can't write to, or a full disk. Each of these fails at the final write, after every page has been OCR'd. That is the failure the Why sets out to remove.
  - D7 catches only "`ScanscribeError` and the exceptions raised by Pillow, pypdfium2 and the engine". An `OSError` from the write is none of these, so it prints a traceback, which breaks R12.
  - D6 says "a failed run never leaves a partial file". A plain `write_text` truncates the file first, so a failure or Ctrl-C during the write destroys an existing output. That breaks R8 ("byte-identical").
  - Two runs writing the same output can also interleave.
- **Fix:**
  - In the D6 pre-checks, reject an `-o` that is an existing directory.
  - Before loading the engine, create a temp file in the output directory. This proves the directory is writable.
  - Write the text to that temp file, then `os.replace` it onto the output.
  - Add `OSError` to the errors that `run` maps to exit 1.

**M2 · The R14 test imports real Paddle on any machine with an extra installed, and the Risk's mitigation only detects this**
- **Where:** phase 02 › task 1.3 Verify ("on the base install, the test gets the R14 message"); plan.md › Risks, bullet 4 (line 265: "A test imports real Paddle on a machine that has an extra installed → the R13 test catches it").
- **What is wrong:**
  - The test relies on Paddle being absent.
  - The owner's manual check runs `uv sync --extra gpu/cpu` (notes.md lines 89-90). `uv run` does not remove extras, so later `uv run pytest` runs on that machine have Paddle installed.
  - There, the R14 test calls `load_engine`, which imports real Paddle. That is slow and may start the GPU. The R14 assertion then fails, and so does the R13 session-end check.
  - So the mitigation catches the problem but does not prevent it, and the suite is red on the owner's machine.
- **Fix:** make the test independent of what is installed. Use `monkeypatch.setitem(sys.modules, "paddle", None)` (and the same for `paddleocr`), which makes the import fail with `ModuleNotFoundError` whose `.name` is set. The R14 test then passes on every install.

**M3 · The R13 subprocess test contradicts D2 as written**
- **Where:** phase 02 › task 1.4 ("a subprocess that imports every scanscribe module ... then asserts `paddle` and `paddleocr` are not in `sys.modules`"); plan.md › Decisions › D2 (lines 190-195).
- **What is wrong:**
  - D2 has `load_engine` import `scanscribe.paddle_engine` lazily, which implies `paddle_engine` imports Paddle at module level.
  - If "every scanscribe module" includes `paddle_engine`, the test cannot pass. On the base install the import raises `ImportError`. With an extra installed it imports real Paddle.
  - If `paddle_engine` instead imports Paddle inside its functions, the `ImportError` comes from `resolve_device` or the constructor. Task 1.3 does not say it maps errors from those calls.
- **Fix:** say where `paddle_engine` imports Paddle. Then either exclude `scanscribe.paddle_engine` from the R13 import list by name, or require `load_engine` to wrap `resolve_device` and the constructor too.

**M4 · PDF pages can reach the engine in the wrong channel order, and nothing tests it**
- **Where:** phase 01 › task 2.2 ("yields RGB arrays ... PDFs are opened ... and rendered at `scale = dpi / 72`"); plan.md › D4 and R18.
- **What is wrong:**
  - By default pypdfium2 renders BGR(x), not RGB. In `.venv/lib/python3.12/site-packages/pypdfium2/_helpers/page.py`, line 453 says "`rev_byteorder=True` will swap `BGR{A/x}` to `RGB{A/x}`", and line 520 sets `rev_byteorder = False` by default.
  - If the implementer uses `bitmap.to_numpy()`, PDF pages are BGR. The adapter's unconditional flip (R18) then gives Paddle RGB for PDFs only. That is the bug D4 fixes, still present on the PDF path.
  - Task 2.2's PDF test checks only the width ("`--dpi 144` ... giving 144 px"), not the colour.
  - This also casts doubt on the evidence in notes.md line 18 ("`ocr.predict(rgb_array)`"). If the prototype used `to_numpy()`, its PDF path was already BGR, and the D4 diff would mean something different for PDF inputs.
- **Fix:**
  - Specify the conversion: `render(..., rev_byteorder=True)`, or `to_pil().convert("RGB")`, which handles BGRx too.
  - Add a page-source test that renders a pure-red PDF page and asserts the pixel is (255, 0, 0).
  - Check how the prototype converted PDF pages before recording the D4 comparison.

### Nits
- **plan.md › Assumptions, last bullet:** the pre-check reads headers only, so a truncated image still wastes the whole run. `Image.verify()` is cheap and would catch it, and task 1.2 already builds a truncated-image fixture that no test listed in tasks 2.2 or 4.3 uses.
- **phase 01 › task 2.2:** `Image.open` keeps the file open until load or close. If the header check keeps those objects, a folder of more than about 1024 pages runs out of file descriptors. Close each image after the header check.
- **plan.md › R7, second scenario:** with "a text file as input" and no `-o`, a file named `x.txt` gets the default output `x.txt`, which is the input itself. R10 then exits 2, not R7's 1. The test fixture must use a name that doesn't end in `.txt`.
- **plan.md › R12 vs R9:** R12 says "every error is ... one stderr line", but R9 requires argparse's usage message, which is two lines (usage plus `scanscribe: error:`). Narrow R12 to non-usage errors.
- **phase 01 › task 4.1 and D1:** `run(argv, ...) -> int`, but argparse raises `SystemExit` for exit 2 and for `--help`. Say whether `run` catches it and returns the code, or the tests expect `SystemExit`.
- **plan.md › R12:** Ctrl-C during a long run prints a `KeyboardInterrupt` traceback. Map it to one line and exit 130, or exempt it from R12.
- **plan.md › Risks, bullet 1 and phase 02 › task 3.1:** the manual check records how many lines differ but sets no pass/fail rule for a large difference. Also, "newer locked versions" is inaccurate: `uv.lock` pins the same paddleocr 3.7.0, paddlex 3.7.2 and paddlepaddle 3.3.1 as the prototype (`uv.lock` lines 1518, 1534, 1565, 1608). Only pypdfium2 differs (5.15.2, line 2158), so the diff mostly isolates D4.
- **plan.md › Assumptions (first run):** PaddleOCR downloads its models on first use. Two overlapping first runs may race on the model cache, and the README Usage section (phase 02 task 2.1) could mention this.

### Relevant files
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/plan.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/phases/01-pipeline-and-cli.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/phases/02-paddleocr-adapter.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/notes.md
- /home/geo/develop/projects/scanscribe/uv.lock
- /home/geo/develop/projects/scanscribe/.venv/lib/python3.12/site-packages/pypdfium2/_helpers/page.py
