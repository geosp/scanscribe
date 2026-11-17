Phase 01 impl review, failure lens (diff 7594141..4d348a6)

I found one Major and a set of Nits. The main path holds up when a run stops partway. Pages are checked before the engine loads (pages.py:93-100, 129-145). OCR results are kept in memory, and the output is written once at the end through mkstemp, fsync, chmod and os.replace (output.py:253-268). Every exception, including KeyboardInterrupt, deletes the temp file. A run that fails before the replace leaves the old output byte-identical. A rerun never reads anything an earlier run left behind: temp names are random, and they start with "." and end in ".tmp", so R1 never lists them as pages. Two runs at once each produce a complete file and the last rename wins, which the plan's Assumptions accept.

## Steps in order (run, then convert, then write_atomic)

1. `parse_args` (cli.py:150). SystemExit is caught.
2. `resolve_output` (cli.py:64-84): `input.exists()`, `default_output_path` (`resolve()`, `is_dir()`), `output.is_dir()`, `parent.is_dir()`, `os.access`, `output.resolve() == input.resolve()`. Only UsageError is caught here (cli.py:153).
3. `open_source` (pages.py:182):
   - folder: `iterdir`, then for each file `Image.open` and `load()`;
   - PDF: `PdfDocument(path)`, `len`, then each page's width. The document is closed on any BaseException (pages.py:143-145).
4. `engine_factory(lang, device)` (cli.py:99).
5. For each page:
   - folder images are opened again and closed before the yield (pages.py:113-119);
   - PDF pages are rendered, and the page and bitmap are closed in `finally` before the yield (pages.py:160-173), so an abandoned generator holds no handles;
   - `_progress` goes to stderr, then `recognize` runs on each slice.
6. The `with` block exits and the PDF document is closed.
7. `write_atomic`:
   - `os.stat` (old mode) or `_umask_default_mode` (output.py:241-242: `umask(0)`, then restore);
   - `mkstemp` (output.py:257, file created 0600);
   - inside the try: write, flush, fsync, `chmod` by name, `os.replace`;
   - `except BaseException`: unlink the temp (FileNotFoundError suppressed), then re-raise.
8. `_progress("Extracted text written to …")` (cli.py:108).
9. Error mapping: KeyboardInterrupt gives 130, Exception gives 1 (or re-raised under SCANSCRIBE_DEBUG).

## Major

**M1. Exceptions from the path checks escape `run` as a traceback.** Location: cli.py:151-156, cli.py:71-83. Concerns R12 and D7.

- `resolve_output` runs after parsing, but only UsageError and SystemExit are caught around it. Every non-UsageError exception it raises leaves `run` uncaught.
- D7 says: "After parsing, it catches every `Exception`, collapses the message to one line …". R12 says: "Every error that is not a usage error is printed as one stderr line … with no traceback".
- **Scenario 1 (symlink loop):** `ln -s loop.txt loop.txt; scanscribe book.pdf -o loop.txt`.
  - `output.is_dir()` returns False, because ELOOP is in pathlib's `_IGNORED_ERRNOS` (python3.12 pathlib.py:45, 870-883).
  - The parent directory passes the checks.
  - `output.resolve()` then raises `RuntimeError("Symlink loop from …")` (pathlib.py:1234-1252, Python 3.10-3.12 behavior).
  - Result: Python traceback, exit 1, no `scanscribe: error:` line.
- **Scenario 2 (permission denied):** `scanscribe /some/0700-dir-of-another-user/book.pdf`, or `-o` pointing into such a directory.
  - `Path.exists()` and `is_dir()` re-raise any errno outside ENOENT/ENOTDIR/EBADF/ELOOP (pathlib.py:852-867). EACCES is not on that list, so a PermissionError propagates as a traceback.
  - I could not reproduce this here: the sandbox made `/root/x.pdf` report False, and further probing was blocked. The finding rests on the stdlib source.
- **Test that would expose it:** create the self-symlink in tmp_path, run with `-o` pointing at it, and assert no "Traceback" in stderr and an exit code of 2 or 1. Alternatively, monkeypatch `Path.exists` to raise `PermissionError` and assert the same.
- **Fix direction:** in `resolve_output`, convert OSError and RuntimeError into a UsageError, or catch Exception around it.

## Nits

- **N1.** output.py:264-268 and cli.py:107-108 (R20). If Ctrl-C lands after `os.replace` succeeds, either before the try block exits or during the final `_progress`, the run returns 130 "interrupted" but the output has already been replaced. R20 says it is "neither created nor changed". The window is tiny.
- **N2.** output.py:257-258 (R20). If KeyboardInterrupt arrives inside or right after `mkstemp`, before the `try:`, the `.out.txt.XXXX.tmp` file is left behind. R20 says "no temp file remains". The window is tiny. Moving `mkstemp` inside the try with `temp_name = None` would close it.
- **N3.** output.py:241-242. If KeyboardInterrupt arrives between `os.umask(0)` and the restore, the process keeps umask 0. This is harmless for the CLI, but in-process callers and the test session would then create world-writable files. The window is tiny.
- **N4.** output.py:265-267. If the cleanup unlink raises something other than FileNotFoundError (for example, PermissionError after the directory's mode changed during OCR), that error replaces the original one in the R12 line and the temp file stays.
- **N5.** output.py:253-268 (D6). A run killed by SIGKILL, SIGTERM, SIGHUP or power loss after `mkstemp` leaves a hidden `.name.*.tmp` that no later run cleans up. Also, the directory is not fsynced after the rename, so a power loss can undo it. Outside the contract (R20 covers only Ctrl-C); noted for completeness.
- **N6.** cli.py:89 and cli.py:133 (R11, R12). If stderr is a closed pipe (`scanscribe book.pdf 2>&1 | head -1`), `_progress` raises BrokenPipeError and aborts the OCR. `_error` then raises again inside the except handler, so `run` raises out with no one-line message. If this happens after the write, the exit is non-zero even though the output was replaced.
- **N7.** cli.py:77-83 (R10, plan Summary "unwritable outputs caught before OCR"). Some write failures only appear after the whole OCR:
  - An output name of 242-255 bytes passes R10, but the temp name `.<name>.<8 chars>.tmp` exceeds NAME_MAX, so `mkstemp` fails with ENAMETOOLONG.
  - The same happens when the output directory is removed, unmounted or made read-only during a long run.
  - Exit 1, and the OCR is lost. The non-goal "resuming a partial run" covers the second case.
- **N8.** cli.py:82 (R10). Only output == input is rejected. `scanscribe scans -o scans/p1.png` replaces the source image p1.png with text after OCR, and the next run fails on "cannot read page image p1.png". The contract only scopes R10 to the input itself, so this matches the contract but loses data on a typo.
- **N9.** cli.py:149-156 (R20). Ctrl-C during parsing or `resolve_output` is not caught, so Python prints a traceback rather than the single `scanscribe: error:` line. The window is tiny and no output is involved.
- **N10.** docs/plans/2026-11-16-rebuild-cli/plan.md Phases table. It still says "0/12" for phase 01, while the phase file ticks all 12 tasks. This is bookkeeping, not code.

## Files

- /home/geo/develop/projects/scanscribe/src/scanscribe/cli.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/output.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/pages.py
- /home/geo/develop/projects/scanscribe/tests/test_cli.py
- /home/geo/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/lib/python3.12/pathlib.py (the stdlib behavior cited in M1)
