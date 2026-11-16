## Implementation review: phase 01 (pipeline and CLI), diff 7594141..4d348a6

I read the plan, the phase file and notes.md, then all of `src/scanscribe/{engine,output,pages,cli}.py` and `tests/{conftest,test_fixtures,test_pages,test_output,test_cli}.py`. Nothing was built and no tests were run. I checked library behaviour by reading source: CPython 3.12.12 `pathlib.py` in the uv-managed interpreter, and pypdfium2 5.15.2 `_helpers/page.py` in `.venv`. The only thing I ran was one read-only `Path("/root/x/book.pdf").exists()`, which raised `PermissionError`.

Overall the contract is kept closely. There are two real findings: one is a code gap against R12/D7, the other is a test that can't see the promise it checks. The rest are Nits.

### Promise map (where each is enforced, and the test that would fail without it)

- **R1:** enforced at `pages.py:23-50`. Tests: `test_pages.py:30`, `:37`, `:51`, `:58` (skipped on case-insensitive file systems) and `:65`.
- **R2:** enforced at `pages.py:131,163`. Test: `test_pages.py:103` (144 px at `--dpi 144`).
- **R3:** enforced at `output.py:12-20` and `output.py:55` (UTF-8). Tests: `test_output.py:13-24` and the end-to-end tests in `test_cli.py`.
- **R4:** enforced at `pages.py:189-199`. Tests: `test_pages.py:206`, `:211`, `:217`, `:224`, `test_cli.py:177` and `test_cli.py:191`.
- **R5:** enforced at `pages.py:85-87,99-100,141-142`. The PDF width calculation matches pypdfium2 `page.py:458`. Tests: `test_pages.py:164`, `:177` and `test_cli.py:278` (engine never loaded, no output).
- **R6 / D5:** enforced at `output.py:23-32`. Tests: `test_output.py:30-55` and `test_cli.py:128`, `:171`.
- **R7 / D8:** enforced at `pages.py:96-97,132-139`. Tests: `test_pages.py:119`, `:127`, `:135` and `test_cli.py:251`, `:263`.
- **R8:** enforced at `pages.py:103-110` (`load()`), `pages.py:117-118,171-172` and `output.py:79-101`. Tests: `test_pages.py:155` and `test_cli.py:288`, `:306`.
- **R9:** enforced at `cli.py:16-24`. Test: `test_cli.py:40`.
- **R10:** enforced at `cli.py:64-84`, before `convert`. Tests: `test_cli.py:55-118`.
- **R11:** enforced at `cli.py:87-89,102,108`. Tests: `test_cli.py:128` and `:150`, which check exact stderr and an empty stdout.
- **R12 / D7:** enforced at `cli.py:118-166`. Tests: `test_cli.py:306`, `:324`, `:382`, `:395` and `:409` (debug re-raise).
- **R20:** enforced at `cli.py:159-161` and `output.py:98-101`. Tests: `test_cli.py:345` and `:361`.
- **D1:** `engine.py:19-26` and `cli.py:142`.
- **D2:** nothing in `src/` imports paddle.
- **D4:** `pages.py:116,166`. Test: `test_pages.py:112`.
- **D6 order:** `cli.py:98-107`.
- **D6 temp file and mode:** `output.py:79-101`. Tests: `test_cli.py:202` and `:216`; see Finding 2.
- **D9:** `conftest.py:31-58`.

### Findings

**1. Major: R12, D7. Errors raised during the path check bypass the one-line handler and print a traceback.**
- **Location:** `cli.py:149-156` calls `resolve_output` (`cli.py:64-84`) inside a `try` that catches only `SystemExit`. Inside `resolve_output`, `parser.error` only sees `UsageError`. The `except Exception` at `cli.py:162` covers only `convert`.
- **Contract:**
  - D7: "After parsing, it catches every `Exception` … prints the R12 line and returns 1."
  - R12: "Every error that is not a usage error is printed as one stderr line … never a traceback."
- **Evidence:** on Python 3.12, `Path.exists()` and `Path.is_dir()` swallow only ENOENT, ENOTDIR, EBADF and ELOOP (`pathlib.py:45,52-54,859-864,874-881`), so `PermissionError` propagates. Non-strict `Path.resolve()` raises `RuntimeError("Symlink loop …")` on a loop (`pathlib.py:1234-1252`).
- **Failure scenario A:** `run(["/root/x/book.pdf"], f)` as a normal user. `input_path.exists()` at `cli.py:71` raises `PermissionError: [Errno 13]` (I confirmed this with the venv's Python). It propagates out of `run` as a traceback with no `scanscribe: error:` line.
- **Failure scenario B:** `-o out.txt` where `out.txt` is a symlink to itself. `is_dir()` returns False (ELOOP is ignored), then `output.resolve()` at `cli.py:82` raises `RuntimeError`, again as a traceback.
- **Test that would expose it:**
  - Monkeypatch `Path.exists` (or `resolve_output`) to raise `PermissionError`.
  - Or create `out.txt` as a self-loop symlink and pass `-o out.txt`.
  - Assert exit 1, exactly one `scanscribe: error:` line, and no `Traceback`.
- **Possible fix:** treat any `OSError`/`RuntimeError` from `resolve_output` as a usage error (`parser.error`), or move the path check inside the `Exception` handler while keeping `UsageError` → 2.

**2. Major (test only; the code is correct): D6 "give it the old output's mode". The test can't tell the old mode from the umask default.**
- **Location:** `test_cli.py:202-213` sets the existing output to `0o644` and checks it stays `0o644`. The test doesn't set a umask.
- **Failure scenario:** a regression changes `output.py:86-89` to always call `_umask_default_mode()`. With the usual umask 022, `0o666 & ~0o022 == 0o644`, so the test still passes and the promise is unobserved. It only fails under some other ambient umask (for example 002), so whether it can observe the promise depends on the machine.
- **Test that would expose it:** make the existing output `0o600` (or set `os.umask(0o022)` and use `0o640`) and assert that mode is kept.

### Nits

- `cli.py:149-156` (R20): a Ctrl-C during parsing or the path check isn't caught, so it gives a traceback, not 130 plus one line. The window is tiny.
- `output.py:90-91` (R20, D6): a Ctrl-C between `mkstemp` returning and entering `try` leaves `.<name>.*.tmp` behind. The window is tiny.
- `output.py:97` and `cli.py:108` (R20): a Ctrl-C after `os.replace` succeeds, or during the final progress print, returns 130 even though the output was already replaced. That contradicts "neither created nor changed", though the file is complete.
- `output.py:73-76` (D6): `os.umask(0)` briefly changes the umask for the whole process. This is harmless single-threaded, but in phase 02 any live engine threads could create files with mode 0666 during that window.
- `pages.py:48` (R1): `is_file()` follows symlinks, so a symlink to an image counts as a "regular file". It's unclear whether that is intended.
- `test_cli.py:288`, `:263`, `:278`, `:382` (task 4.3): the task asks every error test to assert "no temp file left", but these don't call `temp_files()`. The code can't create one there, so this is low risk.
- `test_cli.py:55-118` (R10, "no page is read"): the tests only check that the factory wasn't called. They would still pass if the path check moved after `open_source`. Monkeypatching `cli.open_source` to fail would observe the promise.
- `test_cli.py` (R3, UTF-8): every OCR line is ASCII, so writing in the locale encoding would pass. A FakeEngine that returns a non-ASCII line would observe it.
- `test_cli.py:251-418` (R11): no error-path test asserts `captured.out == ""`. The code is correct (everything goes to stderr).
- `test_cli.py:288` (R8, first scenario): at CLI level only a corrupt PNG is the third file. The truncated PNG/JPEG cases are covered only through `open_source` in `test_pages.py:155`. Coverage is adequate structurally.
- `plan.md` Phases table: the diff changes phase 01 to `in-progress` but leaves Tasks at `0/12`, while all 12 tasks in the phase file are ticked.

### Files

- /home/geo/develop/projects/scanscribe/src/scanscribe/cli.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/output.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/pages.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/engine.py
- /home/geo/develop/projects/scanscribe/tests/test_cli.py
- /home/geo/develop/projects/scanscribe/tests/test_pages.py
- /home/geo/develop/projects/scanscribe/tests/test_output.py
- /home/geo/develop/projects/scanscribe/tests/conftest.py
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/plan.md
