---
phase: 2
title: PaddleOCR adapter and the scanscribe command
status: approved
branch: null
base: null
delivers: [R13, R14, R15, R16, R17, R18, R19]
design_review: { status: passed, rounds: 2, last: 2026-11-16 }
impl_review: { status: none, rounds: 0, last: null }
approved: 2026-11-16
---

# Phase 02 · PaddleOCR adapter and the scanscribe command

## Goal

`uv run scanscribe <input>` OCRs real input with PaddleOCR. It uses the GPU when one is available and
the CPU otherwise. On the base install it gives a clear error instead. The owner has compared its
output with the prototype's on both devices.

## Tasks

### 1. Adapter and loader

- [ ] 1.1 Re-check the D3 and D4 source references ([notes.md](../notes.md#d3-device-detection-in-the-installed-paddle))
  against the PaddleOCR and PaddlePaddle versions in `uv.lock`. Record any difference in notes.md
  and propose a plan `update` if a decision changes. Verify: notes.md names the versions checked.
- [ ] 1.2 Add `src/scanscribe/paddle_engine.py`. It imports `paddle` and `paddleocr` at its top
  (D2). It has `resolve_device(requested)` (R15, D3) and `PaddleOcrEngine(lang, device)`. The engine:
  - passes the prototype's three `use_*=False` flags;
  - adds `enable_mkldnn=False` only on `cpu*` (R17);
  - flips RGB to BGR in `recognize` with `np.ascontiguousarray(image[:, :, ::-1])` (R18, D4);
  - collects each result's `rec_texts`.

  Add mypy overrides for `paddle` and `paddleocr`. Add a test fixture that installs fake Paddle
  modules with `monkeypatch.setitem(sys.modules, ...)` and removes `scanscribe.paddle_engine` from
  `sys.modules` before and after each test. Verify these unit tests:
  - the three device cases, run in either order;
  - the kwargs passed on `cpu` and on `gpu:0`;
  - the BGR pixel;
  - multiple results.

  `uv run mypy` passes on the base install.
- [ ] 1.3 Add `load_engine(lang, device)` to `engine.py`. It imports `scanscribe.paddle_engine`
  inside the function (D2) and turns a `ModuleNotFoundError` for exactly `paddle` or
  `paddleocr` into `EngineMissingError`, an `InputError` with the R14 message. It then resolves the device and prints
  `Using device: <d>` to stderr (R16). Verify these tests:
  - with `sys.modules["paddle"]` and `["paddleocr"]` set to `None`, it raises the R14 message on any
    install;
  - with fake modules, the device line appears before `Processing page 1...`;
  - an `ImportError` named `paddle.base.core` (a broken install) is not reported as a missing engine.
- [ ] 1.4 Add `main()` (`sys.exit(run(sys.argv[1:], load_engine))`) and
  `[project.scripts] scanscribe = "scanscribe.cli:main"` (R19). Add the R13 tests:
  - a subprocess imports every scanscribe module except `paddle_engine`, then calls
    `run(["--help"], load_engine)`, which returns 0;
  - it then asserts `paddle` and `paddleocr` are not in `sys.modules`;
  - a session-end check in `conftest.py` asserts that no real `paddle` or `paddleocr` was imported.

  Verify: `uv run scanscribe --help` exits 0, and `uv run scanscribe <generated folder>` on the base
  install exits 1 with the R14 message.

### 2. Docs and checks

- [ ] 2.1 Replace the README's "under construction" status with a Usage section covering:
  - the commands and options;
  - the output format;
  - the exit codes;
  - the first-run model download, and that two simultaneous first runs can collide on it.

  Add a line to `docs/decision-log.md` for the BGR change and the new edge-case behavior, and update
  the Status line in `AGENTS.md`. Verify:
  the lychee links job passes in CI.
- [ ] 2.2 Run the AGENTS.md checks locally, then the suite once from a clean clone with only
  `uv sync --locked`. Verify: all commands exit 0.

### 3. Manual OCR check (owner)

- [ ] 3.1 Owner, GPU: run the prototype and `scanscribe` with the `gpu` extra on the same local
  input, which includes at least one color page, following
  [notes.md#manual-check](../notes.md#manual-check). Read the differing lines locally, then press
  Ctrl-C once during a second run. Verify:
  - no page reads worse, meaning no word the prototype got right is wrong. If one does, it gets its
    own issue, and this phase stays blocked until the owner reverses D4 through a plan update or
    accepts the result;
  - stdout stayed empty;
  - Ctrl-C exited 130 with the output untouched and no temp file left.

  The PR records the device line (`gpu:0`), page count, run time and the number of differing lines,
  with no book text.
- [ ] 3.2 Owner, CPU: repeat 3.1 with the `cpu` extra. Verify: the device line reads `cpu`, there is
  no oneDNN error, the same checks hold, and the PR records the same facts.
