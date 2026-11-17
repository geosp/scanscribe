Contract review of phase 02 (diff 75c67e0..6fabbf3), checked against R13 to R19, D1 to D4, and tasks 1.1 to 3.2.

I found no Blocker. The code meets each delivered requirement, and every requirement except R13 has a unit test that would fail without its enforcing code. The gaps are in R13's observability and in how the task 3 owner check was recorded.

## Promise map (enforcing code, then the test that would fail without it)

- **R13 (no real Paddle import):**
  - Code: `src/scanscribe/engine.py:63` (the only import of the adapter, done inside `load_engine`).
  - Tests: `tests/test_entry_point.py:28` (subprocess runs `--help` and checks `sys.modules`) and the session-end check at `tests/conftest.py:260-274`. See F1 and F2.
- **R14 (missing engine names both install commands):**
  - Code: `engine.py:62-68`, with the message at `engine.py:47-50`.
  - Tests: `tests/test_engine.py:13` (both install commands named) and `:21` (exit 1, empty stdout, no traceback, no output file).
- **D2 (only `paddle` or `paddleocr` counts as missing):** `engine.py:66` checks `exc.name`; tested at `tests/test_engine.py:55`.
- **R15 / D3 (device choice):**
  - Code: `src/scanscribe/paddle_engine.py:21-30`.
  - Test: `tests/test_paddle_engine.py:20-36`. It covers the three device cases plus an explicit `--device`, and repeats the GPU case afterwards to cover order.
- **R16 (device line before page 1):**
  - Code: `engine.py:70-71`, printed before `PaddleOcrEngine` is built. In `cli.py:118` the factory is called before the page loop.
  - Tests: `test_engine.py:33` (line order) and `:46` (device line before the model is built).
- **R17 (`enable_mkldnn=False` only on cpu):** `paddle_engine.py:45-47`; tested at `test_paddle_engine.py:42` and `:56`. The three `use_*=False` flags are asserted at `:44-52`.
- **R18 / D4 (BGR at PaddleOCR):** `paddle_engine.py:52`; tested at `test_paddle_engine.py:66`. `paddle_engine.py:52` is the only flip in the code.
- **Results from every page are kept:** `paddle_engine.py:55-57`; tested at `test_paddle_engine.py:78`.
- **R11 (adapter output kept off stdout):** `paddle_engine.py:49` and `:53` redirect stdout to stderr; tested at `test_paddle_engine.py:84`.
- **R19 (the `scanscribe` command):**
  - Code: `pyproject.toml` `[project.scripts]` and `cli.py:194-196`.
  - Tests: `test_entry_point.py:35` and the phase 01 test `tests/test_cli.py:50-53`, which checks every option.
- **D1:** `cli.main` passes `load_engine`, and `cli.run` never touches Paddle.
- **mypy:** overrides added in `pyproject.toml`.

## Findings

**F1 · Major · R13, task 3.1 · No record of the suite or mypy run on an extra install.**
- R13's main scenario is "a machine with an extra installed … the real paddle and paddleocr were never imported".
- On the base install (CI, and the clean clone in task 2.2) neither check can fail: `paddle` can't be imported, so `test_import_path_and_help_never_import_paddle` and the session-end check pass trivially.
- The only setup that can observe R13 is task 3.1's "with the extra installed, `uv run pytest` and `uv run mypy` pass, and the session-end check reports no real Paddle import". Task 3.1 is ticked, but `docs/demos/2026-11-16-ocr-check/README.md` never mentions pytest, mypy or the session-end check.
- Commit 1edd22c records only the base-install run ("only uv sync --locked (148 tests)").
- Failure scenario: a later test calls `cli.main()` or `load_engine` without a fixture. CI stays green, and the leak shows only on an extra install, where nobody has a recorded run.
- mypy strict with the real, untyped `paddle` installed is also unverified. With the extra, `ignore_missing_imports` no longer applies once the module resolves.
- Fix: run `uv sync --locked --extra gpu && uv run pytest && uv run mypy` (and the same with `cpu`) and record the result.

**F2 · Major · R13, task 1.4 · The session-end check is never tested.**
- `pytest_sessionfinish` (`tests/conftest.py:260-274`) is the R13 guard, but no test proves it fails the run.
- Failure scenario: the check sets `session.exitstatus`, but a pytest change, a typo or a wrong condition makes it a no-op. No test fails, and on the base install it can't even be triggered.
- Fix: a `pytester` test that installs a non-None stand-in `sys.modules["paddle"]` with no fixture undoing it, then asserts the inner run's exit code is `TESTS_FAILED` and that its output contains "R13:".

**F3 · Nit · task 3.1, Terms ("Only the owner runs real OCR on book material"), notes.md#manual-check · The owner did not read the differing lines.**
- The pass rule says "the owner reads the differing lines locally". Per `docs/demos/2026-11-16-ocr-check/README.md:3`, "The owner delegated the run to the coding agent". The agent replaced reading with a mechanical letter edit-distance check.
- Rated Nit because the owner chose to delegate, and edit distance 0 does rule out wrong words.
- Two things are still unverified by a human: the reordered lines on the colour page, which affect reading order, and the owner's acceptance of the result.

**Further Nits, one line each:**

- **F4 · Nit · task 3.1:** the device line, page count, run time and differing-line count are recorded in a committed doc rather than in the PR, as the task text asks; I can't see the PR to check.
- **F5 · Nit · `tests/conftest.py:204-235`, task 1.2:** the task asks for a fake PaddleOCR that "prints and logs to stdout", but the fake only prints. `contextlib.redirect_stdout` would not catch a logging handler bound to `sys.stdout` at import. notes.md finds only stderr handlers, so the current risk is low.
- **F6 · Nit · `engine.py:63` and `paddle_engine.py:28`, R11:** the import of `paddle`/`paddleocr` and `resolve_device` run outside the stdout redirect. A print at import time would reach stdout. notes.md covers only "the OCR path", but the manual check saw 0 bytes on stdout on both devices.
- **F7 · Nit · `paddle_engine.py:26`, R15:** `if requested:` treats `--device ""` as not given and picks a device automatically, while R15 says "`--device` when given". This is an edge case with no test.
- **F8 · Nit · `tests/test_entry_point.py:16`, task 1.4:** the subprocess imports a hard-coded module list rather than every scanscribe module except `paddle_engine`. It matches today's modules, but a new module would not be covered.
- **F9 · Nit · `tests/test_engine.py:55`, task 1.3:** the broken-install test mocks `importlib.import_module` and raises `ModuleNotFoundError`, not a plain `ImportError` coming from inside the adapter's import. It still checks the `exc.name` filter, but not a real failure of a native library.
- **F10 · Nit · `pyproject.toml` `[project.scripts]`, R19:** no test runs the installed console script. `test_main_exits_with_runs_code` calls `cli.main` directly, so a wrong entry-point string would pass CI. The manual check ran `.venv/bin/scanscribe` successfully.

Relevant files:
- /home/geo/develop/projects/scanscribe/src/scanscribe/engine.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/paddle_engine.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/cli.py
- /home/geo/develop/projects/scanscribe/tests/conftest.py
- /home/geo/develop/projects/scanscribe/tests/test_engine.py
- /home/geo/develop/projects/scanscribe/tests/test_entry_point.py
- /home/geo/develop/projects/scanscribe/tests/test_paddle_engine.py
- /home/geo/develop/projects/scanscribe/docs/demos/2026-11-16-ocr-check/README.md
