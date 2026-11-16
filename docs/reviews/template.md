---
review: design            # design | implementation
plan: docs/plans/<plan-folder>
phase: <NN, or all>
round: <NN>
targeted_follow_up: false # true when only the lens that raised reopened findings ran
adrs: []
commit_sha: <full SHA reviewed>
diff_base: <SHA; implementation reviews only, else n/a>
date: <YYYY-MM-DD>
verdict: <PASS | FAIL>
reviewers:
  - { lens: <name>, agent: <design-reader | design-reviewer | impl-reviewer>, status: <completed | not run>, report: raw/<file>.md }
---

# <Design | Implementation> review <round>: <plan title>

## Inputs

<Exact paths given to the reviewers, and the revision. Nothing else was provided.>

## Fresh reader paraphrase

<Design reviews only: link to the fresh reader's raw report. Delete for implementation reviews.>

## Findings

| ID | Severity | Lens | Location | Scenario / evidence | Action | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | Blocker / Major / Nit | | | | Fix / Contest | open / fixed in <sha> / contested: <reason> |

## Verdict

<PASS or FAIL, with the rule that decided it (docs/reviews/README.md rule 5).>

## Open items

<Anything still open after this round.>
