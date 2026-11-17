---
status: accepted
date: 2026-11-16
supersedes: null
plan: docs/plans/2026-11-16-rebuild-cli
---

# ADR-0001: Keep the OCR engine behind an interface and import it only when OCR starts

## Context

scanscribe uses PaddleOCR, which needs PaddlePaddle. Paddle comes in two builds, GPU and CPU, that can't be installed together. Both are large downloads, and CI should install neither. The tests must still cover the whole pipeline, and anyone without an engine installed should get a clear error rather than a crash.

Alternatives:
- **Import Paddle at the top of the modules:** every run and every test would need it installed.
- **Engine plugins through entry points:** a mechanism one engine doesn't need.
- **Pass PaddleOCR's result objects through the pipeline:** that would tie the tests to Paddle's result format.

## Decision

The CLI talks to OCR only through the `OcrEngine` protocol in `scanscribe.engine`, which has one method, `recognize(image) -> list[str]`, and receives an engine factory. Only `scanscribe.paddle_engine` imports Paddle, and only `engine.load_engine` imports that module, inside the function, when OCR starts.

## Consequences

- CI and the tests run on the base install with a fake engine. A session-end check fails the test run if the real `paddle` or `paddleocr` is ever imported.
- A missing engine is reported as one error line naming the two install commands, `uv sync --extra gpu` and `uv sync --extra cpu`.
- Another engine can be added by writing an `OcrEngine` and a factory, without touching the pipeline.
- New modules must not import `paddle`, `paddleocr` or `scanscribe.paddle_engine` at module level.
- New tests that reach `load_engine` must use the fake Paddle fixtures. The subprocess test in `tests/test_entry_point.py` lists the modules it imports; add new modules to it.
- Engine-specific concerns stay inside the adapter: the BGR channel order, the device choice, and keeping stdout clean.
