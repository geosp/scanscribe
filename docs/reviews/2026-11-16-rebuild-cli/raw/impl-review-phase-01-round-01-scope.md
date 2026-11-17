## Phase 01 implementation review, scope lens (diff 7594141..4d348a6)

I checked every per-run, per-page and per-file mechanism against the scope the plan promises: page pre-check against yield, rendered-width pre-check against `render()`, file-handle lifetime, the temp file and mode, the error-catch scopes and the page/call counters. Almost all of them hold at their promised scope. One real problem: the path checks run outside the error handlers. There are also several Nits.

### Major

**M1. Path validation can raise errors that neither handler catches, so the user gets a traceback.** Concerns R12, R10 and D7.
- **Location:** `src/scanscribe/cli.py:149-156` together with `resolve_output` at `cli.py:71-83`.
- **Why it happens:** D7 says "After parsing, it catches every `Exception`". In the code, the catch-all `except Exception` (cli.py:162) only wraps `convert()`. `resolve_output` runs after parsing but sits in a `try` that catches only `UsageError`. The `pathlib` calls it makes raise errors that are not `UsageError`:
  - On the venv's Python 3.12, `Path.exists()` and `Path.is_dir()` re-raise any `OSError` whose errno is not ENOENT, ENOTDIR, EBADF or ELOOP. I confirmed this with the installed source: `pathlib._IGNORED_ERRNOS == (2, 20, 9, 40)`. I also ran `Path('/root/book.pdf').exists()` as a non-root user here and it raised `PermissionError [Errno 13]`.
  - `Path.resolve()` raises `RuntimeError("Symlink loop from ...")` on Python 3.10–3.12.
- **Failure scenarios:**
  1. `scanscribe /root/book.pdf` run by a non-root user on Fedora, where `/root` is `dr-xr-x---`. `input_path.exists()` at cli.py:71 raises `PermissionError`. Result: a full Python traceback and no `scanscribe: error:` line.
  2. `scanscribe book/ -o /root/out.txt`, or any `-o` inside a directory the user can't traverse. `output.is_dir()` at cli.py:75 raises `PermissionError`. Result: a traceback, where R10 promises exit 2 for an unwritable output directory.
  3. `-o out.txt` where `out.txt` is a symlink loop. `is_dir()` returns False because ELOOP is ignored, then `output.resolve()` at cli.py:82 raises `RuntimeError`. Result: a traceback.
- **Tests that would expose it:**
  - Make `locked = tmp_path/"locked"` with mode `0o000` and assert that `run([str(locked/"book.pdf")], factory)` returns 2 (or 1) with exactly one `scanscribe: error:` line and no `Traceback`. Today pytest sees `PermissionError` escape from `run`.
  - The same check with `-o str(locked/"out.txt")`.
  - A self-referencing symlink passed as `-o`.

### Nits

- **N1. The mode-preservation test can't tell "old mode" from "umask default".** `tests/test_cli.py:203-213`, D6 / task 4.2. The test chmods the old output to 0644. Under the usual umask 022, the umask default is also 0644, so the test still passes if the old-mode branch (`output.py` `os.stat(path).st_mode`) is deleted. The property is only tested where the two branches give the same result. Use 0600, or set umask 077 for the test.
- **N2. R20 window after the rename.** `output.py` `write_atomic` and `cli.py:107-108,159-161`. A Ctrl-C that arrives after `os.replace` succeeds but before `run` returns (for example during the "Extracted text written" print) still returns 130 and prints "interrupted". By then the output has been changed, which contradicts R20's "neither created nor changed". The window is tiny and inherent.
- **N3. R20 window before the cleanup starts.** `output.py:257-258`. The `try` that deletes the temp file starts after `mkstemp` returns. A Ctrl-C between `mkstemp` creating the file and entering the `try` leaves a `.<name>.*.tmp` behind, against R20's "no temp file remains". The window is tiny.
- **N4. Ctrl-C during parsing or path checks gives a traceback.** `cli.py:149-156`. `KeyboardInterrupt` there is caught by neither handler, so it prints a traceback instead of the one-line R20 message. The window is short and nothing has been written yet.
- **N5. Some unwritable outputs are still found only after the whole OCR run.** `cli.py:80` against R10 and the plan's "Why" ("crashes only after the whole book has been OCR'd"). `os.access(dir, W_OK|X_OK)` passes in these cases, but the final step fails with exit 1 after all pages are done:
  - a sticky directory such as `/tmp` where the existing output belongs to another user: `os.replace` fails with EPERM;
  - an output name close to NAME_MAX, so the temp name `.<name>.<random>.tmp` gets ENAMETOOLONG.

  R10 doesn't list these cases explicitly.
- **N6. "Output resolves to the input" compares `resolve()` strings.** `cli.py:82`, R10/D5. On a case-insensitive filesystem (exFAT or vfat USB drive, ext4 casefold), `-o BOOK.PDF` for the input `book.pdf` compares unequal. The PDF is then replaced by text after OCR. `os.path.samefile` would catch it when the output exists. The implementation follows D5 as written.
- **N7. The R10 input/output check only covers the folder itself.** `cli.py:82`, R10 scope. With a folder input, `-o book/p1.png` names one of the input's pages. That page is read, then overwritten with text at the end. R10 only promises "resolves to the input" (the folder), so this is outside the letter of the requirement, but it destroys input data.
- **N8. Images are pre-checked once and reopened later.** `pages.py:367-368` against `pages.py:380-387`, D6/R5. If a file changes between the pre-check and OCR (for example it gets narrower than `--columns`), `split_columns` can produce zero-width slices for the engine. A corrupt replacement is still caught as an `InputError` with the output untouched. This is a time-of-check-to-time-of-use (TOCTOU) gap and an unlikely one.
- **N9. PDF pages are only pre-checked for width.** `pages.py:415-424` against R8's "A page that can't be read is an input error". A PDF page that opens and reports a width but fails in `render()` fails mid-OCR, after the engine has loaded. The output is still untouched. D6 explicitly limits the PDF pre-check to the rendered width, so this matches the plan.
- **N10. The plan's phase table wasn't updated.** `plan.md:339`. It still shows `0/12` tasks for phase 01, while all 12 are ticked in the phase file. This is bookkeeping only.

### Checked and found to hold
- **PDF width pre-check:** `ceil(get_width()*scale)` matches pypdfium2 5.15.2's `render()` (`_helpers/page.py:458-465`, with default rotation 0 and no crop).
- **Column split:** a page at least N px wide never produces a zero-width slice.
- **File handles:** they are released per image in both the pre-check and `images()`. The RLIMIT test exercises both.
- **PDF document lifetime:** the document stays open for the whole run and closes on every error path, including `BaseException` in `__init__`.
- **Temp file:** it is a dotfile, so it is never listed as a page when the output sits inside the input folder.
- **Counters:** page numbering is per run, from 1. `FakeEngine.fail_on_call` counts per call, which equals per page in the columns=1 tests for R12 and R20.
- **Test coverage:** the R8 and R20 scenarios are tested at their promised scope: page 2 of a multi-page run, against an existing output checked byte-identical, with no temp file left.
- **Image modes:** every Pillow mode that `load()` accepts converts to RGB on the installed Pillow 13.0.0 (checked: I;16, I, F, CMYK, LA, PA, 1, YCbCr, LAB, HSV).

### Relevant files
- /home/geo/develop/projects/scanscribe/src/scanscribe/cli.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/output.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/pages.py
- /home/geo/develop/projects/scanscribe/tests/test_cli.py
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/plan.md
