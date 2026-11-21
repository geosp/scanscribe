---
status: accepted
date: 2026-11-21
supersedes: null
plan: docs/plans/2026-11-21-library-api
---

# ADR-0002: The public library API is exactly `scanscribe.__all__`, versioned with semver

## Context

scanscribe started as a command only. The planned `scanscribe-mcp` server needs to call it from Python: load the engine once, get the page-marked text back, follow progress per page and stop between pages. Code in another repository, pinned to a tag, has to be able to tell which names it may rely on, and the type checker has to check its calls. Without a stated boundary, every module-level name would in practice be part of the API, and any refactor could break a caller.

Alternatives:
- **No stated boundary:** callers import whatever they find, so internal helpers such as `split_columns`, `natural_key` or `write_atomic` would become frozen by accident.
- **A separate `scanscribe.api` entry point only:** longer imports, with no gain over the package root.
- **Export more helpers now:** no caller needs them, and each one exported is one more name semver freezes.

## Decision

We will treat exactly the names in `scanscribe.__all__` as the public API, ship `py.typed`, and version that API with semantic versioning from `v0.1.0`. Everything else in the package is internal and may change in any release.

## Consequences

- Adding, removing or renaming a name in `__all__`, or changing a public signature or behavior, is an API change: it needs a decision-log line and a new tag that follows semver.
- A test pins `sorted(__all__)` to the agreed list, so a change to the public names can't slip in unnoticed. Update that test and the README's "Use as a library" section together.
- The CLI runs on the same functions (`open_source`, `load_engine`, `ocr_source`), so the command's output and the library's stay the same; a test compares them directly.
- A pushed tag is never moved: a fix ships as a new patch version.
- `__version__` stays a module attribute outside `__all__`.
- Internal helpers can still be refactored freely, as long as the public names keep their behavior.
- The API inherits the engine's limit: one OCR job per process at a time. It is documented, not enforced.
