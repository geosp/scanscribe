---
status: accepted
date: 2026-11-21
supersedes: null
plan: docs/plans/2026-11-21-library-api
---

# ADR-0003: The MCP server lives in a separate repository that pins a scanscribe tag

## Context

An MCP server, `scanscribe-mcp`, will expose scanscribe's OCR to agents. It is built on mcp-service-kit, which needs Python 3.11 or later, while scanscribe supports Python 3.10 to 3.12. The server also brings FastMCP and Starlette, a network-facing security model and a Docker deployment, none of which the command needs.

Alternatives:
- **An `mcp` extra in this repository:** it would need Python-version markers, CI on two setups, and server packages in the command's lock file. The repository already has two mutually exclusive engine extras, `gpu` and `cpu`.
- **A server package inside this repository:** the same lock file and CI cost, and the server's security review would cover this repository too.

## Decision

We will keep the MCP server in its own repository, `scanscribe-mcp`, which depends on scanscribe through a pinned Git tag and uses only the public API ([ADR-0002](0002-public-library-api.md)).

## Consequences

- This repository stays a Python 3.10+ command and library, with no server dependencies, network code or deployment files.
- Each API change the server needs reaches it only through a new scanscribe tag and a dependency bump in `scanscribe-mcp`.
- uv doesn't inherit `[tool.uv.sources]` from a dependency, so `scanscribe-mcp` must copy the PaddlePaddle settings: the two extras, the `[tool.uv] conflicts` rule, the `paddlepaddle-cu126` index and its source entry. The README lists them; when they change here, the server's copy must change as well.
- The server must run OCR jobs one at a time per process, as the public API documents.
- Server concerns such as authentication, transport, job queueing and containers are decided in `scanscribe-mcp`, not here.
