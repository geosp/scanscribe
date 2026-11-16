---
review: design
plan: docs/plans/2026-11-16-rebuild-cli
phase: all
round: 02
targeted_follow_up: false
adrs: []
commit_sha: d5f1a46841b35b59ac1c353f97d1791aecfdd91e
diff_base: n/a
date: 2026-11-16
verdict: FAIL
reviewers:
  - { lens: fresh reader, agent: design-reader, status: completed, report: raw/design-review-02-fresh-reader.md }
  - { lens: codebase fit, agent: design-reviewer, status: completed, report: raw/design-review-02-codebase-fit.md }
  - { lens: zoom out, agent: design-reviewer, status: completed, report: raw/design-review-02-zoom-out.md }
---

# Design review 02: Rebuild the scanscribe CLI from the ocr-pdf prototype

## Inputs

Revision `d5f1a46841b35b59ac1c353f97d1791aecfdd91e` on branch `docs/4-rebuild-cli-plan`, after the round 1 fixes. Each reviewer got the same inputs as in round 1, with no round 1 findings or reports:

- Fresh reader: `plan.md` only.
- Codebase fit: `plan.md`, both phase files, `notes.md`, `AGENTS.md`, `CLAUDE.md`, and the repository.
- Zoom out: `plan.md`, both phase files, `notes.md`, and the repository.

## Fresh reader paraphrase

See [raw/design-review-02-fresh-reader.md](raw/design-review-02-fresh-reader.md).

## Findings

Closed findings are not repeated. The fresh reader raised multi-rule requirements again; that is F22 from round 1, which was contested.

| ID | Severity | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F25 | Major | zoom out | Reopens F16: `Image.verify()` checks only PNG/WebP, so a damaged JPEG, TIFF or BMP passes the pre-check and fails hours into OCR (D6, Assumptions, phase 01 2.2) | fixed: D6 (full decode), Assumptions; phase 01 1.2, 2.2; notes D6 |
| F26 | Major | fresh reader | Summary says "two input rules change"; What changes lists five breaking changes | fixed: Summary |
| F27 | Major | fresh reader | The modules holding `load_engine` and `main()` are never named (D1, D2, R13) | fixed: D1, D2 |
| F28 | Major | fresh reader | Phase files are never linked, though Risks and the Phases table cite their tasks | fixed: Phases table links |
| F29 | Major | fresh reader, codebase fit | R1 never says the natural sort ignores case; task 2.1 doesn't fold case | fixed: R1; phase 01 2.1 |
| F30 | Major | fresh reader | How post-parse path checks (R10) give exit 2 in argparse's format is unstated; writability is only tested when the temp file is created (D6, D7) | fixed: D7 (`parser.error()`); phase 01 4.1 (`os.access`) |
| F31 | Major | fresh reader, zoom out | Reopens F10: "reads worse" has no criterion, nothing says what unblocks phase 02, and a grayscale input can't test D4 | fixed: Risks; notes Manual check; phase 02 3.1, 3.2 |
| F32 | Major | fresh reader | D6's first sentence is ~50 words of seven steps; needs a numbered list | fixed: D6 numbered list |
| F33 | Nit | codebase fit, zoom out | Multi-line exception messages (Paddle's C++ traceback) break R12's one line; there is no way to get a traceback for diagnosis | fixed: R12, D7 (one line, `SCANSCRIBE_DEBUG`); phase 01 4.3 |
| F34 | Nit | codebase fit, zoom out | Temp file name, timing and mode are unspecified: `mkstemp` makes the output 0600, and an early temp file can be orphaned by a hard kill (D6) | fixed: D6, Assumptions; phase 01 4.2 |
| F35 | Nit | codebase fit | R5 pre-check uses width × DPI / 72, but pypdfium2 renders `ceil(width × scale)` (phase 01 2.2) | fixed: phase 01 2.2 |
| F36 | Nit | codebase fit | The flipped array `image[:, :, ::-1]` isn't C-contiguous; use `np.ascontiguousarray` (phase 02 1.2) | fixed: phase 02 1.2 |
| F37 | Nit | codebase fit | The manual-check `<input>` resolves differently after `cd ../ocr-pdf`; use an absolute path (notes Manual check) | fixed: notes Manual check |
| F38 | Nit | codebase fit | The manual check doesn't confirm stdout stays empty with real Paddle (R11, phase 02 3.1–3.2) | fixed: notes Manual check; phase 02 3.1 |
| F39 | Nit | codebase fit | No test checks the option defaults or that `--help` lists every option (R19, phase 01 4.1) | fixed: phase 01 4.1 |
| F40 | Nit | codebase fit | Impact leaves out AGENTS.md, whose Status line goes stale when phase 02 merges | fixed: Impact; phase 02 2.1 |
| F41 | Nit | zoom out | D2 maps any `ImportError` under `paddle` to "install the extra", including a broken installed build; map only `ModuleNotFoundError` named exactly `paddle`/`paddleocr` | fixed: D2; phase 02 1.3 |
| F42 | Nit | zoom out | Rollout doesn't say whether the downstream consumer (`study-book-chapter`) is affected | fixed: Rollout & rollback |
| F43 | Nit | zoom out | Ctrl-C (R20) is never observed with real Paddle; add it to the manual check | fixed: notes Manual check; phase 02 3.1 |
| F44 | Nit | fresh reader | Small wording gaps: rename drawn on the per-page line, R11 vs `--help` on stdout, R4 half rounding, "PP-OCRv6"/"locked version", "hidden", 5.13.0's meaning, D4 causality, the Risks arrow, R10's two "before" points | fixed: Summary diagram, Terms, R1, R4, R10, R11, D4, D8, Risks |

## Verdict

FAIL. There are no Blockers, but 8 Majors are open: rule 5 in docs/reviews/README.md.

## Open items

None. The coordinator applied every fix after the round. This was the last round the design-review skill allows. No reviewer has re-checked the fixes; the implementation review checks the code against them.
