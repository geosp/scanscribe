Review of /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli (plan.md, phases 01 and 02, notes.md)

Scope note: phase 01 is implemented and ticked 12/12, so I checked its claims against the code in src/scanscribe/ and tests/. Phase 02 is not started, so I checked its claims against the code it builds on. PaddleOCR, PaddleX and PaddlePaddle are not installed in this repository's .venv; the lock pins paddleocr 3.7.0, paddlex 3.7.2 and paddlepaddle(-gpu) 3.3.1. That means I could not check the D3 source references or the Paddle logging behavior below. Phase 02 task 1.1 already re-checks D3 and D4.

Checked and correct: every phase 01 name the plan uses exists and does what the plan says:
- `OcrEngine`, `EngineFactory`, `ScanscribeError`/`UsageError`/`InputError` (engine.py:19-38)
- `run(argv, engine_factory)`, the `SystemExit` handling, `parser.error`, the one line of at most 300 characters, `SCANSCRIBE_DEBUG`, and 130 on Ctrl-C (cli.py:136-190)
- the R10 checks, including the page-of-folder rule (cli.py:78-102)
- `write_atomic` with `.<name>.<random>.tmp`, keeping the old mode, and `os.replace` (output.py:79-115)
- the natural sort, dotfiles skipped, full `load()` pre-check, `ceil(width × scale)` width check, `to_pil().convert("RGB")` and `split_columns` (pages.py)

The notes' pypdfium2 evidence also matches the installed 5.15.2: `render()` computes `math.ceil(self.get_width() * scale)` at page.py:458, there is a `rev_byteorder` note at :453 and its default is at :520. There are no ADRs. I found no reuse opportunities: nothing in the repository already does what phase 02 builds.

## Findings

**F1 · Major · phases/02-paddleocr-adapter.md › Task 1.2 (fixture) and Task 1.3; plan.md › Risks (last bullet)**

The way the tests "clear the cached adapter module" is incomplete. Depending on how `load_engine` imports the adapter, the R14 test and the "either order" device tests can depend on test order.

The plan says the fixture "removes `scanscribe.paddle_engine` from `sys.modules` before and after each test". After the first successful import, Python also stores the submodule as an attribute on the `scanscribe` package. If `load_engine` is written `from scanscribe import paddle_engine`, then `_handle_fromlist` sees `hasattr(scanscribe, "paddle_engine")` and returns the stale module without importing it again. In that case:
- the R14 test (`sys.modules["paddle"] = None`) does not raise when it runs after a fake-module test;
- the device tests reuse a module bound to an earlier test's fake `paddle`.

I confirmed this with the stdlib in the repository's Python:
- after `del sys.modules['json.tool']` and `sys.modules['argparse'] = None`, `from json import tool` returned the stale module with no error;
- `importlib.import_module('json.tool')` raised `ModuleNotFoundError` with `e.name == 'argparse'`.

Fix: task 1.3 should say `load_engine` uses `importlib.import_module("scanscribe.paddle_engine")` (or `import scanscribe.paddle_engine`), or the fixture should also run `monkeypatch.delattr(scanscribe, "paddle_engine", raising=False)`.

The same check confirmed that `None` in `sys.modules` gives `ModuleNotFoundError.name == "paddle"`, so D2's exact-name rule works with the planned R14 test.

**F2 · Major · plan.md › R13 (scenario "or a machine with an extra installed"); phases/02 › Tasks 2.2, 3.1, 3.2**

No task runs the test suite with an extra installed, so half of R13's Given/When/Then is never exercised. This is the case finding F2 of design round 1 was about (fake-module and R14 tests breaking when real Paddle is present).
- Task 2.2 runs the suite "from a clean clone with only `uv sync --locked`", which is the base install.
- The AGENTS.md checks start with `uv sync --locked`, which removes extras.
- Tasks 3.1 and 3.2 install the `gpu` and `cpu` extras but only run the CLI, not `uv run pytest`.
- Task 1.3 says the R14 test passes "on any install", but nothing checks it.

Fix: in 3.1 and 3.2, after `uv sync --extra gpu|cpu`, add "`uv run pytest` passes and the session-end check reports no real paddle import", or add the same step to 2.2.

**F3 · Major (unverified risk) · plan.md › R11; phases/02 › Task 1.1, Task 3.1; notes.md › Manual check**

The only check that real Paddle keeps stdout empty comes at the very end (`test ! -s out/gpu.stdout` in the manual check). No task finds out whether PaddleOCR or PaddleX logs to stdout, and no task plans what to do if it does. As I remember it, PaddleX's logger (`paddlex/utils/logging.py`) writes through `logging.StreamHandler(sys.stdout)`, and PaddleOCR 3.x prints model-creation and download messages at load time. I could not confirm this because neither package is installed in this repository.

If it is true, R11 fails during the owner's manual check, after every implementation task is done, and nothing in the plan covers the fix (for example, pointing the `paddlex`/`paddleocr` loggers at stderr, or redirecting stdout around engine creation and `predict`).

Fix: add the logging destination to task 1.1's source re-check, and add a fix and a fake-module test to 1.2 if needed.

## Nits

- phases/01-pipeline-and-cli.md › Task 4.2: "an existing 0644 output keeps its mode" is out of date. F46 changed the test to 0600 under umask 022 (tests/test_cli.py:341-348), so the plan text no longer describes the test that runs.
- plan.md front matter vs phases/02 front matter: the plan has `design_review: { status: changes-requested, rounds: 2 }`, while phase 02 has `{ status: passed, rounds: 2 }` for the same review. Commit fee7682 saves a round 3 report (raw/design-review-03-fresh-reader.md) that reviews.md doesn't record yet, so the gate status is unclear.
- phases/02 › Task 1.4 (session-end check): the plan doesn't say how a failure in a `conftest.py` session hook fails the run. A bare `assert` in `pytest_sessionfinish` becomes an INTERNALERROR rather than a test failure. Setting `session.exitstatus` or using a final autouse check would be clearer.
- phases/02 › Task 1.3: the plan doesn't say whether `Using device:` is printed before or after `PaddleOCR(...)` is built. Printing it before keeps R16's line visible during a slow first-run model download, and it is what the user sees if a bad `--device` makes construction fail.
- cli.py:64-71 `resolve_output` docstring: it lists the R10 cases but leaves out the page-of-folder rule added in 39c0eeb. This is documentation only.

## Files referenced
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/plan.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/phases/01-pipeline-and-cli.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/phases/02-paddleocr-adapter.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/notes.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/reviews.md
- /home/geo/develop/projects/scanscribe/src/scanscribe/cli.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/engine.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/output.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/pages.py
- /home/geo/develop/projects/scanscribe/tests/conftest.py
- /home/geo/develop/projects/scanscribe/tests/test_cli.py
- /home/geo/develop/projects/scanscribe/pyproject.toml
