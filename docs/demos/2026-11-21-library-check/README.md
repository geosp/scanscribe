# Library check: `transcribe` vs the `scanscribe` command, on the GPU

Manual check for [docs/plans/2026-11-21-library-api](../../plans/2026-11-21-library-api/plan.md), task 3.3, extended at plan close to cover engine reuse and stopping a run. It runs the real PaddleOCR engine, which the unit tests replace with a fake.

**Result: pass.** With one loaded engine, `transcribe` returned exactly the text the command writes on every full run, including a run after a stopped one. Raising from `on_page` stopped the run at the requested page and left stdout restored.

## Setup

| | |
| --- | --- |
| Date | 2026-11-21 |
| Machine | NVIDIA GeForce RTX 3060, driver 610.43.03, Linux |
| Python | uv-managed 3.12.12, `uv sync --locked --extra gpu` |
| Input | the 14 self-made pages from [the phase 02 demo](../2026-11-16-ocr-check/make_pages.py), saved as one PDF; no book material |

From the repository root:

```bash
uv sync --locked --extra gpu
W=$(mktemp -d)
uv run python docs/demos/2026-11-16-ocr-check/make_pages.py "$W/pages"
uv run python docs/demos/2026-11-21-library-check/check.py "$W"
uv sync --locked   # back to the base install
```

## What `check.py` does

1. Runs the `scanscribe` command on the PDF, writing `cli.txt`.
2. Loads the engine once with `load_engine(..., on_device=...)`, then, with that same engine:
   - **run 1:** `transcribe` with a progress callback; the text must equal `cli.txt`, with one progress call per page;
   - **run 2:** `transcribe` again; same checks;
   - **stopped run:** `on_page` raises at page 5; the exception must reach the caller after exactly 5 progress calls, and `sys.stdout` must be the same object as before;
   - **run after the stop:** `transcribe` once more; same checks as run 1.
3. Prints only the device, counts, timings and yes or no for each check. It exits 0 only if every check passes.

## Result

`check.py` exited 0 and printed:

```text
device: gpu:0
pages: 14, progress calls: 14
command: 7.1 s (includes engine load); transcribe: 2.2 s
transcribe equals the command's output: yes
second run, same engine: 1.9 s, progress calls: 14, equals: yes
stopped run: raised at page 5: yes, progress calls: 5, stdout restored: yes
run after the stop: 1.9 s, progress calls: 14, equals: yes
```

The first task 3.3 run, earlier the same day on the same machine and recorded in PR #10, printed the same first four lines, apart from the command taking 8.1 s.

With the GPU extra installed, `uv run pytest -q` passed all 174 tests and the session check found no real Paddle import (R13); `uv run mypy` passed. After returning to the base install, every AGENTS.md check passed again.

## Not covered

- **The CPU.** The plan asked only for the GPU. The OCR itself is unchanged from phase 02, whose demo covered both devices.
- **Two jobs at once.** The API supports one OCR job per process at a time, as the README states; nothing here runs jobs concurrently.
- **Stopping during the folder pre-check.** The input is a PDF. A folder of images is checked in full before the first progress call, so it can't be stopped earlier.
- **`open_source` then `ocr_source` on the real engine.** `transcribe` runs `ocr_source`, so its loop is covered; calling the two functions directly is covered only by the fake-engine tests.
- **Long-running reuse.** Three full runs and one stopped run on one engine; memory growth over many jobs isn't measured.
