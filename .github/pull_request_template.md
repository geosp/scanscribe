## Summary

> [!TIP]
> 2-5 sentences: what changed and why. Write for a reviewer who has not seen the work.

## Issue

> [!TIP]
> `Closes #N` only if this PR fully resolves the issue; otherwise `Part of #N`. Never use closing keywords (closes/fixes/resolves) for any other issue.

Closes #

## Plan trace

- **Implementation plan and phase:** <!-- docs/plans/<plan>/ and phase NN, or n/a -->
- **ADR:** <!-- docs/adrs/..., or n/a -->

## Changes

-

## Testing

> [!TIP]
> List only the checks actually run, with their result.

| Check | Command | Result |
| --- | --- | --- |
| Lint and format | `uv run ruff check . && uv run ruff format --check .` | |
| Types | `uv run mypy` | |
| Tests | `uv run pytest` | |

## Manual OCR check

> [!TIP]
> Required when this PR changes OCR behavior (engine, device selection, rendering, column split, output format). Describe the input without quoting book text, the command, the device used (GPU model or CPU) and what you observed. Delete this section otherwise.

## Notes for reviewers

> [!TIP]
> New dependencies or `uv.lock` changes (especially the `cpu`/`gpu` extras), output format changes that affect downstream tools, CLI changes, known limitations. Delete if none.

## Checklist

- [ ] No secrets, credentials or session transcripts committed
- [ ] No book material (PDFs, page images or OCR text of books) in the diff, fixtures or this description
- [ ] Decision log or plan updated if constraints, the CLI or the output format changed
- [ ] Plan task boxes checked only for work whose tests pass
- [ ] Generated agent files in sync (`uv run .agents/sync_agents.py --check`)
