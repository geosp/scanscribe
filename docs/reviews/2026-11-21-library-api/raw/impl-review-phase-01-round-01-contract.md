Review of phase 01 (library-api), diff 49ecda0..4c190ed in /home/geo/develop/scanscribe

I found one Major issue and several Nits. There are no Blockers. I only read code; I ran no builds or tests.

## Major

**M1 · R6 / D4: a folder input that exists but can't be listed escapes `open_source` as a raw `PermissionError`.**
- **Location:** `/home/geo/develop/scanscribe/src/scanscribe/pages.py:191-202`, `:213-214`, `:49` and `:98`.
- **Scenario:** call `transcribe(Path("book"), engine)` where `book/` is the caller's own folder with mode 0o000 (or 0o300).
  - `_input_is_dir` calls `path.exists()` and `path.is_dir()`. Both only stat the folder itself, which needs search permission on its parent, not on the folder. Both succeed.
  - `ImageFolderSource.__init__` then calls `list_image_files`, and `folder.iterdir()` raises `PermissionError`.
  - That call sits outside the `try` in `_input_is_dir`, and `ImageFolderSource` has no wrapper for it. The caller gets a bare `PermissionError`, which is neither a `UsageError` nor an `InputError`.
- **Contract:** R6 says "`open_source` must raise `UsageError` naming the path when the input doesn't exist or can't be checked, never a traceback". The README example (`except (UsageError, InputError)`) would not catch this error.
- **Gap in the tests:** the R6 test at `/home/geo/develop/scanscribe/tests/test_api.py:54-57` passes `locked_dir / "book.pdf"`, a path inside the locked folder. It never passes the locked folder itself.
- **Exposing test:** `open_source(locked_dir, dpi=200, columns=1)` should raise `UsageError` (or at least a `ScanscribeError`). Today it raises `PermissionError`.
- **CLI:** the CLI already behaved this way before the diff ("PermissionError: …", exit 1), so its behavior has not changed.

## Promise map (enforcing code → test that fails without it)

- **R1:** `api.py:55-56` and `cli.py:118-123` share `ocr_source` and `format_pages`. Tests: `test_api.py:206-225`, covering a folder, a two-column PDF and the default dpi. OK.
- **R2:**
  - `api.py` has no print or write calls.
  - Test: `test_api.py:157-169`, using capsys and a `tmp_path` snapshot. Observability is limited (see Nits).
- **R3:** `api.py:31-33` calls `on_page` after `images()` yields and before `split_columns`/`recognize`. Test: `test_api.py:74-96`. It covers folders only, one column.
- **R4:**
  - `api.py:32-33` doesn't catch the exception; `transcribe` uses `with` at `api.py:55`.
  - Tests: `test_api.py:99-111` checks the same exception object and `len(shapes)==1`. `test_api.py:114-131` checks that the PDF is closed. OK.
- **R5:** `pages.py:211-212` runs before any path or page access. Tests:
  - `test_api.py:22-32` would fail without the check. `dpi=0` would otherwise give an `InputError` from the width check, and `columns=0` would pass the width check.
  - `test_api.py:142-146` checks the engine is never called. OK.
- **R6:** `pages.py:197-202`. Tests: `test_api.py:35-39`, `:54-57` and `:149-153`. Gap: M1.
- **R7:** `pages.py:97` and `:134` store `columns`; `api.py:35` uses it. Tests: `test_api.py:60-65` and `:134-139`. OK.
- **R8:** `engine.py:76-78` calls the callback before `PaddleOcrEngine`. Tests: `test_api.py:175-197`. Both scenarios are covered, and the first asserts `created == 0` at callback time. OK.
- **R9:** `__init__.py:8-39`. Tests: `test_entry_point.py:15-37`, a subprocess script with `from scanscribe import *` and a leak check, plus `:40-62`, which pins `__all__`. OK.
- **R10:** the file exists (`src/scanscribe/py.typed`). No automated test checks it; the plan's Assumptions allow that.
- **D1:**
  - Both signatures match the plan exactly (`api.py:21-23`, `:42-49`).
  - The CLI calls `open_source` → factory → `ocr_source` and prints "Processing page N..." (`cli.py:118-122`).
  - Rejected options are absent: `ocr_source` takes no `columns`.
  - Test: `test_cli.py` is unchanged in the diff. OK.
- **D2:** the 15 names match the plan's list exactly, and each is imported from the module D2 names.
- **D3:** decision-log line added and README install settings added.
- **D4:**
  - The checks are in `open_source`, and `OSError`/`RuntimeError` are converted to `UsageError` (`pages.py:201-202`).
  - The CLI keeps argparse and `resolve_output`, which run first, so the new checks don't fire from the CLI except in the race noted in the Nits.
  - Gap: M1.

## Nits

- **`test_api.py:157-169` (R2):** `capsys` only captures Python's `sys.stdout`/`sys.stderr`. Output that pypdfium2 or PIL writes directly to the file descriptors would go unseen, and so would files created outside `tmp_path`. Using `capfd` would observe the descriptor-level case.
- **`test_api.py:74-96` (R3):** the ordering test uses only a single-column folder. A PDF source, or `columns=2` ("before its *first* recognize call"), isn't covered. Low risk, because both paths share the same loop.
- **`test_entry_point.py:22-24` (R9):** the script imports `load_engine` and `run` explicitly before computing `unbound`. A missing `load_engine` binding would therefore be masked. Also, `from scanscribe import *` already raises if a name in `__all__` is unbound, so the `unbound` check adds little.
- **`test_entry_point.py:60-62` (R9):** the pin is checked in-process rather than in the fresh interpreter the scenario describes. It is equivalent in practice.
- **R10 / task 1.4:** no automated check that the wheel contains `py.typed`. The plan's Assumptions accept a by-hand check. I can't confirm it was done; nothing in the diff records the result.
- **`pages.py:191-202` vs `cli.py:74-82` (D4, reuse):** "input not found: …" and "cannot check path: …" are now written out twice, in `_input_is_dir` and `resolve_output`/`_check_paths`. D4 keeps them separate on purpose, but if one message is reworded the CLI and the library would report the same condition differently.
- **`pages.py:186-188` vs `cli.py:17-25` (task 1.1, reuse):** "must be at least 1, got N" is duplicated in `_check_at_least_one` and `_at_least_one`. The same risk applies: the two copies can drift.
- **`test_api.py:42-51` vs `test_cli.py:201-210` (task 1.1, reuse):**
  - The `locked_dir` fixture is copied verbatim, and the test name `test_input_in_an_unreadable_directory_is_a_usage_error` appears in both files.
  - Moving the fixture to `tests/conftest.py` would have meant editing `test_cli.py`, which the plan says to leave unchanged, so the copy is defensible.
- **`cli.py:118` (D4):** if the input disappears between `resolve_output` and `open_source`, the CLI now prints "input not found" with exit 1. Before, it printed an `InputError` or `FileNotFoundError` message, also exit 1.
  - This is a `UsageError` exiting with 1, while `engine.py:36` documents `UsageError` as exit 2.
  - It is a race only, and the exit code is unchanged.
- **`api.py:42-56` (R6):** `transcribe("book.pdf", engine)` with a `str` raises `AttributeError: 'str' object has no attribute 'exists'`, not `UsageError`. The parameter is typed `Path` and mypy strict catches this for typed callers, but a server passing JSON strings without type checking gets a traceback.
- **`pages.py:60-61` (R7, D2):** `PageSource` is now public, but `columns` is only an annotation on the base class. A third-party subclass that doesn't set it fails with `AttributeError` inside `ocr_source`. `labels` already worked this way before the diff.
- **`docs/decision-log.md:7` (task 3.2):** task 3.2's check is "the line links this plan". The line gives the path in backticks (`docs/plans/2026-11-21-library-api/`), not a Markdown link. Other rows use the same style.
- **Task 3.3:** still unticked; the GPU manual run and the device record are pending. The plan's phase table correctly shows 8/9.

## Reuse and placement

New code:
- `api.py`: `ProgressCallback`, `ocr_source`, `transcribe`.
- `pages.py`: `_check_at_least_one`, `_input_is_dir`.
- `engine.py`: `_print_device`.
- `test_api.py`: the `locked_dir` fixture, the `Stop` class, the `cli_output` helper.
- `test_entry_point.py`: `PUBLIC_API`.

Results:
- The old copy of the page loop was removed from `cli.py`, so the loop exists once.
- `ocr_source` reuses `split_columns`, and `transcribe` reuses `format_pages` and `open_source`.
- `_print_device` is a trivial echo of `cli._progress`. It sits in `engine.py` because that's where the message was printed before, so I don't count it as a finding.
- The only duplications are the three listed in the Nits above.
