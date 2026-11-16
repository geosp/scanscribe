# Reviews

Plans in [docs/plans/](../plans/README.md) are reviewed with Skill Central's `design-review` skill before implementation and `impl-review` after each phase. Both skills log each round in the plan's `reviews.md`. This file adds the project rules: what makes a review count as a gate, where the full reports go, and how to keep reviews within a usage budget.

- **Informal review:** a stress-test at any time. Findings go to chat and the plan's `reviews.md`; it is not gate evidence.
- **Gate review:** approves a plan or phase for implementation (design review), or closes a phase (implementation review). Gate reviews follow every rule below.

## Gate rules

1. **Fresh reviewers.** Reviewers are subagents that start with a fresh context. Any session may coordinate them, including the one that wrote the work. The coordinator passes only the rule 3 inputs, saves every report verbatim and never edits a verdict or finding.
2. **Pinned revision.** Review a committed revision only.
   - Record `git rev-parse HEAD` as `commit_sha`.
   - The reviewed paths have no uncommitted changes: `git status --porcelain -- <paths>` is empty.
   - Implementation review diffs `<base>..<commit_sha>`, not the working tree.
3. **Inputs only.** Reviewers receive the plan, the relevant phase file, the ADRs in force and the pinned revision. They never receive the author's reasoning, the session transcript, or another reviewer's verdict.
4. **Saved reports.** Each reviewer's report is copied by tool, never re-typed: on Claude Code with `plan-tool.py save-report` (see the `design-review` skill), otherwise with `cp` from the file the reviewer wrote. Paths:
   - raw reports, unchanged: `docs/reviews/<plan-folder>/raw/<review>-<round>-<lens>.md`, for example `raw/design-review-01-fresh-reader.md` or `raw/impl-review-phase-01-round-02-scope.md`;
   - one summary per round from [template.md](template.md): `docs/reviews/<plan-folder>/<review>-<round>.md`. It is the provenance record: inputs, `commit_sha`, reviewers, findings and verdict.
5. **Verdict.**
   - **FAIL** if any Blocker is open or any reviewer did not complete.
   - Every Major is fixed or contested with evidence before a PASS.
   - Nits do not block.
6. **No fixing by reviewers.** Reviewers never change the work. The coordinator applies fixes, then starts new fresh reviewers for the re-check, or labels the round a targeted follow-up.
7. **One subagent at a time.** See the token budget below.
8. **No book text.** Reviewers, reports and PR descriptions never quote book content. Describe inputs instead ("a 12-page two-column Spanish scan").

A review verdict never authorizes a merge. The required `ci-ok` check on the latest head still applies, and only the owner merges.

## Closing a phase

There is no separate verifier agent. A phase that changes OCR behavior ends with a manual check by the owner on real input: the command run, the device used (GPU or CPU), and what was observed, recorded in the PR description without quoting book text. The implementation review and that check together close the phase.

## Token budget

| Rule | Why |
| --- | --- |
| Run reviewers one at a time; save and commit each report before starting the next | A usage limit costs only the reviewer in flight, and work resumes from the last commit |
| A targeted follow-up round runs one reviewer: the lens that raised the reopened findings | Follow-up rounds are most of the rounds |
| One line per Nit: location, what, why | Most findings are Nits; long ones inflate every report |
| Save reports by tool (`save-report` or `cp`), never re-type them | A re-typed report costs its length in output and stays in context for every later turn |
| Run the test suite once from a clean checkout, with only the documented setup, before the first review round | Catches failures that only your own environment hides |
| Start each phase in a fresh session | The plan files hold all state; a long session's history is paid for on every turn |
| Keep `AGENTS.md` short and load phase files on demand | Always-loaded text is paid for on every turn of every session |

## Session roles and permissions

Separation between roles comes from sessions and subagents, not credentials: every session uses the owner's GitHub login.

| Role | Runs | May | May not |
| --- | --- | --- | --- |
| Implementer | A normal session; `impl-plan apply` | Edit files, run tests, commit, push a feature branch, open and update its PR | Push to `main`, merge, change repository settings, protection or secrets |
| Reviewer | `design-review` / `impl-review`; agents `design-reader`, `design-reviewer`, `impl-reviewer` | Read the inputs and code; run read-only commands; write its own report to the scratch path it is given | Edit repository files, commit, push, write to GitHub, fix what it finds |
| Coordinator | The session that runs a review skill | Choose inputs, save reports, write the round summary, apply fixes between rounds | Edit a reviewer's report or verdict, merge, change protection |
| Owner (a human) | - | Merge PRs, change repository settings, rulesets, secrets and security features; run the manual OCR check | - |

**What enforces it:**

- **Claude Code sessions and their subagents:** `.claude/settings.json` denies pushes to `main`, force pushes, `gh repo edit/delete/rename/archive`, `gh api` writes, `gh secret`/`gh variable` changes, `gh workflow disable` and `gh auth token`, and asks before `gh pr merge`. Deny rules match the command as written, so they are a guardrail, not a wall.
- **Reviewer agents:** the Skill Central reviewer definitions give them no Edit or Write tools.
- **GitHub:** the owner's ruleset on `main` requires a pull request and a passing `ci-ok`, whatever the session.

When a repository setting needs changing, an agent gives the owner the exact command to run.
