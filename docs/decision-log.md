# Decision log

Decisions about constraints, the CLI, the output format, tooling and process that are not recorded in an ADR. Newest first. Plans keep their own decision logs; add a line here only when a decision applies to the project as a whole.

| Date | Decision | Reason |
| --- | --- | --- |
| 2026-11-21 | scanscribe has a public library API, exactly the names in `scanscribe.__all__`, versioned with semver from `v0.1.0`; the MCP server is a separate `scanscribe-mcp` repository that pins a tag | mcp-service-kit needs Python 3.11+ while scanscribe supports 3.10, and the server brings its own dependencies, security model and Docker deployment. Details: `docs/plans/2026-11-21-library-api/` (D2, D3). |
| 2026-11-16 | Pass page images to PaddleOCR as BGR; reject empty inputs, `--columns`/`--dpi` below 1 and unusable output paths before OCR; skip hidden files; name a folder's output after the whole folder name; replace the output atomically | PaddleOCR reads NumPy arrays as BGR, and the prototype passed RGB. The edge-case rules stop failures after hours of OCR. Details: `docs/plans/2026-11-16-rebuild-cli/` (D4, R5-R10, D6). |
| 2026-11-16 | Add the Claude Code deny list (`.claude/settings.json`) in the first commit, before any other agent tooling | Guardrails should exist before agents work in the repository; the setup guide lists them last. |
| 2026-11-16 | Book material (PDFs, page images, OCR text of books) never enters Git, fixtures, review reports or logs; `in/` and `out/` are ignored | The inputs are usually copyrighted. Tests use small generated or self-made images. |
| 2026-11-16 | Commits use the owner's GitHub noreply address, set in the repository's local Git config | The repository is public; this keeps a personal address out of its history. |
| 2026-11-16 | No license is declared yet | Matches the owner's other public repositories. Revisit before inviting contributions or publishing a package. |
| 2026-11-16 | Claude Code is the only supported agent harness; `sync_agents.py` generates for Claude Code only (`ENABLED_HARNESSES`) | Owner's choice. Adding a harness is a one-line change plus the tooling table in `AGENTS.md`. |
| 2026-11-16 | Two mutually exclusive install extras: `gpu` (`paddlepaddle-gpu`, CUDA 12.6 index) and `cpu` (`paddlepaddle`); the tool picks the GPU when available and the CPU otherwise | The prototype depended only on the GPU build, which forced multi-GB CUDA downloads on every machine and cannot install on machines without CUDA wheels. CI uses neither: the OCR engine sits behind an interface and tests use a fake. |
| 2026-11-16 | Name the project `scanscribe` | It transcribes scans: PDFs and folders of page images, not only PDFs. |
| 2026-11-16 | Start a fresh repository rather than continue the `ocr-pdf` prototype's Git history | The prototype's only commit contained copyrighted page images and its remote pointed to a repository that does not exist. The prototype stays outside this repository as reference. |
