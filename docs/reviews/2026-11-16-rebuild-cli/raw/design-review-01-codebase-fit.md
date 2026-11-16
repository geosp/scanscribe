Design review of the rebuild-cli plan at 283b8f4: 3 Majors, 7 Nits, no Blockers

I reviewed `plan.md`, `phases/01-pipeline-and-cli.md`, `phases/02-paddleocr-adapter.md` and `notes.md` under `/home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/`, checked against the repository at 283b8f4. There are no ADRs (`docs/adrs/` holds only a README). The only commit after 283b8f4 adds a review report.

**Claims I confirmed:**
- **`pyproject.toml`:** the `gpu`/`cpu` extras and their conflict, mypy strict with `packages = ["scanscribe"]`, and no `[project.scripts]` yet.
- **`.gitignore`:** it allows `tests/fixtures/**`.
- **Package:** `src/scanscribe/` holds only `__init__.py`. The README "under construction" status line exists.
- **`uv.lock` versions:** paddleocr 3.7.0, paddlex 3.7.2, paddlepaddle and paddlepaddle-gpu 3.3.1 match the versions in the notes. pypdfium2 is 5.15.2 and ships no `py.typed`; Pillow and numpy do.
- **Notes anchors:** all of them resolve.
- **D8 on the locked pypdfium2 5.15.2:** I tested in memory. A saved `PdfDocument.new()` still fails with "Failed to load document (PDFium: Success)", and plain text raises `PdfiumError`, a subclass of `RuntimeError`.
- **R2 scale:** a 72×72 pt page that Pillow writes renders at 144 px with `scale=2`.

**Not verifiable from inside the repository:** the prototype claims (it lives outside the repository) and the Paddle source line references in notes D3 and D4 (Paddle isn't installed in `.venv`). Phase 02 task 1.1 already re-checks the Paddle references.

## Majors

**M1. Phase 02 tasks 1.2 and 1.3 (R13, R14, D2): the fake-module tests leave `scanscribe.paddle_engine` cached, so test results depend on order.**
- Task 1.2 injects fake modules "through `monkeypatch.setitem(sys.modules, ...)`". D2 has `load_engine` import `scanscribe.paddle_engine`, which implies that module imports `paddle`/`paddleocr` at its top.
- After the first fake-module test, `scanscribe.paddle_engine` stays in `sys.modules`, still bound to that test's fakes. monkeypatch only restores the `paddle` and `paddleocr` entries.
- Two failures follow:
  - Later device tests (for example, a CPU-build fake after a CUDA fake) still see the first fake.
  - Task 1.3's "on the base install, the test gets the R14 message" no longer raises `ImportError`, because the cached module is reused.
- Task 1.3 also needs a really missing Paddle. If a developer runs pytest after `uv sync --extra gpu`, that test imports real Paddle and fails. The plan's Risks line ("A test imports real Paddle … → the R13 test catches it") only reports the problem; it doesn't prevent it.
- The plan should require each such test to:
  - remove `scanscribe.paddle_engine` from `sys.modules` (or reload it);
  - force a missing engine with `monkeypatch.setitem(sys.modules, "paddleocr", None)` rather than relying on the base install.

**M2. Phase 02 task 1.4 (R13): the R13 subprocess test is self-contradictory and can pass without checking anything.**
- It "imports every scanscribe module and runs `run(["--help"], load_engine)`, then asserts `paddle` and `paddleocr` are not in `sys.modules`". Two problems:
  - "Every scanscribe module" includes `scanscribe.paddle_engine`. Under D2 that module imports Paddle, so the test either fails with `ImportError` on the base install or imports Paddle, which defeats R13.
  - argparse's `--help` calls `sys.exit(0)`. Unless `run` catches `SystemExit`, the subprocess exits 0 before the assertion runs. A test that checks only the exit code then passes without asserting anything.
- The plan should exclude `paddle_engine` and state how `run` handles argparse's `SystemExit` (see N1), or put the assertion in a `finally`/`atexit`.

**M3. Plan › R10, D7, R12 and Why: an output path that is an existing directory, or can't be written, still fails only after all pages are OCR'd, and may show a traceback.**
- Why lists "A missing output directory crashes only after the whole book has been OCR'd" as a defect to fix. R10 checks only "a missing input, a missing output directory, or an output that resolves to the input".
- `-o out` where `out/` is a directory is likely, since notes › Manual check uses `out/`. It, and a read-only target, only fail at the D6 "write once at the end".
- D7 lists only "`ScanscribeError` and the exceptions raised by Pillow, pypdfium2 and the engine". The `IsADirectoryError`/`PermissionError` from the final write is not covered, so R12 ("Every error … no traceback") can break.
- The plan should add an "output is an existing directory or not writable" usage check to R10 and task 4.1. It should also make D7 cover `OSError` from the write, or catch `Exception` at the top level.

## Nits

- **N1. Plan › R9 vs R12 and D7; phase 01 tasks 4.1 and 4.2:** R9 expects "argparse's usage message", which is several lines, but R12 says every error is "one stderr line". `run(argv, …) -> int` also doesn't say whether it catches argparse's `SystemExit` or lets it escape. State both, because M2 and the "exit 2" tests depend on it.
- **N2. Plan › R7 vs R6 and R10:** the scenario "a text file as input … exits 1" collides with R10 if the file is named `*.txt` and no `-o` is given. The default output then resolves to the input, so the run exits 2. Name the fixture `notes.dat` or pass `-o`.
- **N3. notes › D9 and phase 01 task 4.2:** Pillow writes RGB PDFs as JPEG. In my in-memory test a red 72 px page came back as (254, 0, 0), so the "exact output" PDF test using `rgb{r},{g},{b}` of the center pixel won't match 255. The fake engine should snap colors to a palette, or the PDF fixtures should use black and white.
- **N4. Phase 01 task 2.2 (R2, D4):** pypdfium2's `bitmap.to_numpy()` returns BGR. The same red page gives `[0 0 254]` from `to_numpy()` but `(254, 0, 0)` from `to_pil()`. If PDFs are converted with `to_numpy()`, the adapter's RGB→BGR flip turns the colors back to the wrong order. The plan should require `to_pil()` (or `rev_byteorder=True`) and a red-page PDF test.
- **N5. Phase 01 task 1.2, notes › D9, Assumptions (last bullet):** the "truncated" fixture "keeps the PNG header" is ambiguous, and no Verify step uses it.
  - In my test, Pillow rejects a PNG cut to 8 or 33 bytes at `Image.open`; at 60 bytes it opens, then `convert` raises `OSError`.
  - Define the cut point so the fixture gets past the header check. Then add a test that it exits 1 with no traceback and leaves the output file unchanged.
- **N6. Plan › R5; phase 01 tasks 2.3 and 4.3:** R5 requires the error to name `p1.png` "when the run starts". However, `split_columns(image, n)` has no label, and task 4.3 doesn't check the name or say whether the check runs before or after the engine loads. Say where the label is added and when the check runs.
- **N7. Plan › D8 ("pypdfium2 5.13 refuses …"), notes › D8 ("Observed with pypdfium2 5.13.0"):** the evidence is for 5.13 but the lock has 5.15.2. I re-checked, and the behavior is the same on 5.15.2, so update the version cited.

Files referenced:
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/plan.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/phases/01-pipeline-and-cli.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/phases/02-paddleocr-adapter.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/notes.md
- /home/geo/develop/projects/scanscribe/pyproject.toml
- /home/geo/develop/projects/scanscribe/.gitignore
- /home/geo/develop/projects/scanscribe/uv.lock
