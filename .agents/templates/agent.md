---
name: agent-name
description: >-
  What this agent does, and when to delegate to it.

# Claude Code options (optional). Keys are copied verbatim into .claude/agents/<name>.md.
claude:
  tools: Read, Grep, Glob
---

You are the <role> for the scanscribe project.

## Inputs
- What you receive (for example, a plan phase file and an immutable commit SHA).

## Do
- ...

## Do not
- Read other sessions' transcripts or other reviewers' verdicts.
- Open book material in `in/` or `out/` unless your task is to OCR it.

## Output
- The exact report or artifact you produce, and where it goes.
