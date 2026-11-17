I found one Major problem and four Nits.

**Scope.** I read plan.md, both phase files, notes.md and the phase 01 code that is already in place: `src/scanscribe/{engine,cli,pages,output}.py`, `pyproject.toml`, `uv.lock` and the root-skip guards in the tests. I also read reviews.md so I would not repeat findings F1–F61 that are already closed. Paddle is not installed in this repository's `.venv`, and I stayed inside the repository, so I could not check any PaddleOCR or PaddleX source.

## Major

**M1. Nothing in the plan keeps PaddleOCR and PaddleX from writing to stdout, so R11 depends on library behaviour no one has checked.** (plan.md › R11, D2; phases/02 › 1.1, 1.2, 3.1; notes.md › Manual check)
- **What is wrong:** R11 promises "stdout stays empty". Phase 01 meets this only because `cli._progress` writes to stderr (`src/scanscribe/cli.py:143-145`) and the fake engine prints nothing. Phase 02 then builds `PaddleOCR(...)` and calls `predict` with no stdout handling. PaddleX's logger, as I recall it, writes through a `StreamHandler(sys.stdout)`. It prints the "Creating model: …" and model-download lines on every construction and on the first run. That recollection is unverified, because Paddle is not installed here.
- **Why nothing catches it earlier:** the first place this would show is the owner's manual check at the very end of phase 02. The step `uv run scanscribe "$IN" -o out/gpu.txt > out/gpu.stdout && test ! -s out/gpu.stdout` (notes.md lines 123-124; phase 02 › 3.1 "stdout stayed empty") would fail, and the plan has no remedy designed for that.
- **Task 1.1 does not cover it:** it re-checks only "the D3 and D4 source references". AGENTS.md says "Verify PaddleOCR, PaddlePaddle and pypdfium2 behavior against their current docs or installed source before relying on it."
- **Fix:**
  - Have task 1.1 check where the installed `paddlex` and `paddleocr` loggers write.
  - If they write to stdout, have the adapter send them to stderr: move the logger handlers, or wrap construction and `predict` in `contextlib.redirect_stdout(sys.stderr)`. Note that a Python-level redirect does not catch native writes to fd 1.
  - Add a fake-module test in which the fake `PaddleOCR` prints to stdout, and assert that `run` still leaves stdout empty.

## Nits

- **N1. notes.md › Manual check (lines 119-125) and phase 02 › 3.2:** the CPU comparison writes its baseline to the same `out/proto.txt` as the GPU run ("add --device cpu for the CPU comparison"), and only `diff out/proto.txt out/gpu.txt` is shown. Task 3.2's "the same checks hold" needs a separate `proto-cpu.txt` and a cpu diff. Otherwise the GPU baseline gets overwritten, or the CPU output is compared against the GPU baseline.
- **N2. plan.md › Risks, first bullet:** "a diff mostly measures D4" holds only for a folder input. A PDF input also changes the pypdfium2 version (5.13.0 to 5.15.2, notes.md line 26). Requiring the colour page to come from an image folder would make the pass rule test D4 alone.
- **N3. phases/02 › 1.4 and plan.md › R14:** `load_engine` runs only after the full pre-check, which decodes every image (`cli.py:154-155`, `pages.py:99-100`). On the base install, a user with a large folder waits through the whole decode before seeing "install the extra". A cheap `importlib.util.find_spec("paddleocr")` check before the pre-check would report R14 at once without importing Paddle.
- **N4. phases/02 › 1.2:** the plan only requires "`uv run mypy` passes on the base install". The owner runs the AGENTS.md checks locally with an extra installed. If the installed `paddle` ships a `py.typed` marker (unverified), mypy will type-check against it rather than ignore it, so the result can differ from CI's. Verify mypy on one extra install as well.

## Lenses with no findings

- **Root cause:** each problem under Why is handled at its cause, not a symptom:
  - the GPU-only dependency by the extras;
  - the lack of tests and CI by D1, D2 and D9;
  - `Vol.2` naming by D5;
  - an empty input writing a file by R7 and D8;
  - the late output failure by the R10 pre-check plus D6;
  - BGR by flipping once at the adapter (D4).
- **Simplicity:** I found nothing built for a need nobody stated. `_TEMP_ATTEMPTS = 100` (`output.py:234`) is more than needed but harmless.
- **Placement:** this matches the existing modules. One small point: `load_engine` in `engine.py` will print the device line itself, duplicating `cli._progress`. D1 chooses that on purpose.
- **Failure modes:** previous rounds covered and resolved or contested these: atomic replace, cleanup on Ctrl-C, overlapping runs (last rename wins), the model-cache race (documented in the README), and work lost on an engine error late in a long run (resume is a stated non-goal, and skipping pages was the owner's choice). The Risks mitigations for Paddle API drift, mypy and test-time imports would work as written.
- **Rollout:** it covers what this project needs: no deployment, data or backfill; one PR per phase; undo by reverting the PR; downstream format unchanged.

## Relevant files
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/plan.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/phases/02-paddleocr-adapter.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/notes.md
- /home/geo/develop/projects/scanscribe/src/scanscribe/cli.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/pages.py
- /home/geo/develop/projects/scanscribe/src/scanscribe/output.py
