# Architecture decision records

ADRs record decisions that should outlive the plan that made them. `impl-plan` proposes them when a plan closes and writes them from its ADR template as `NNNN-<slug>.md`, numbered one past the highest existing ADR.

- Never edit an accepted ADR. A changed decision gets a new ADR that supersedes it.
- Smaller decisions, and decisions made outside a plan, go in the [decision log](../decision-log.md).

- [ADR-0001](0001-ocr-engine-behind-an-interface.md): keep the OCR engine behind an interface and import it only when OCR starts.
- [ADR-0002](0002-public-library-api.md): the public library API is exactly `scanscribe.__all__`, versioned with semver from `v0.1.0`.
- [ADR-0003](0003-mcp-server-in-a-separate-repository.md): the MCP server lives in a separate `scanscribe-mcp` repository that pins a scanscribe tag.
