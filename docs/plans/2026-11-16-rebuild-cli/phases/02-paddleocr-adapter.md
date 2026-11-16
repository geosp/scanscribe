---
phase: 2
title: PaddleOCR adapter and the scanscribe command
status: draft
branch: null
base: null
delivers: [R13, R14, R15, R16, R17, R18, R19]
design_review: { status: none, rounds: 0, last: null }
impl_review: { status: none, rounds: 0, last: null }
approved: null
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
- [ ] 1.2 Add `src/scanscribe/paddle_engine.py` with `resolve_device(requested)` (R15, D3) and
  `PaddleOcrEngine(lang, device)`. The engine passes the prototype's three `use_*=False` flags, adds
  `enable_mkldnn=False` only on `cpu*` (R17), flips RGB to BGR in `recognize` (R18, D4), and collects
  each result's `rec_texts`. Add mypy overrides for `paddle` and `paddleocr`. Verify: unit tests that
  inject fake `paddle` and `paddleocr` modules through `monkeypatch.setitem(sys.modules, ...)` cover
  the three device cases, the passed kwargs on `cpu` and `gpu:0`, the BGR pixel, and multiple
  results; `uv run mypy` passes on the base install.
- [ ] 1.3 Add `load_engine(lang, device)` to `engine.py`. It imports `scanscribe.paddle_engine`
  inside the function (D2), turns an `ImportError` for `paddle`/`paddleocr` into
  `EngineMissingError` (an `InputError`, exit 1) with the R14 message, resolves the device, and prints `Using device: <d>` to
  stderr (R16). Verify: on the base install, the test gets the R14 message; a fake-module test sees the
  device line; an unrelated `ImportError` propagates.
- [ ] 1.4 Add `main()` (`sys.exit(run(sys.argv[1:], load_engine))`) and
  `[project.scripts] scanscribe = "scanscribe.cli:main"` (R19). Add R13 tests: a subprocess that imports every scanscribe module and runs
  `run(["--help"], load_engine)`, then asserts `paddle` and `paddleocr` are not in `sys.modules`;
  and a session-end check in `conftest.py` that neither was imported for real. Verify: `uv run scanscribe --help` exits 0;
  `uv run scanscribe <generated folder>` on the base install exits 1 with the R14 message.

### 2. Docs and checks

- [ ] 2.1 Replace the README's "under construction" status with a Usage section: the commands, the
  options, the output format, the exit codes, and the first-run model download. Add a line to
  `docs/decision-log.md` for the BGR change and the new edge-case behavior. Verify: the lychee
  links job passes in CI.
- [ ] 2.2 Run the AGENTS.md checks locally, then the suite once from a clean clone with only
  `uv sync --locked`. Verify: all commands exit 0.

### 3. Manual OCR check (owner)

- [ ] 3.1 Owner, GPU: run the prototype and `scanscribe` on the same local input with the `gpu`
  extra, following [notes.md#manual-check](../notes.md#manual-check). Verify: the PR records the
  device line (`gpu:0`), page count, run time and the number of differing lines, with no book text.
- [ ] 3.2 Owner, CPU: repeat with the `cpu` extra. Verify: the device line reads `cpu`, there is no
  oneDNN error, and the same facts are recorded in the PR.
