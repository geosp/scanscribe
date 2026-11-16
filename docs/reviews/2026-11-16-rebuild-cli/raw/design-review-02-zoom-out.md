Design review of the plan at /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli (revision d5f1a46). This uses the zoom-out lens and covers root cause, simplicity, placement, failure modes and rollout.

I found 1 Major and 6 Nits.

## Summary by question

1. **Root cause.** The plan fixes the causes listed under Why, with one exception.
   - The `Vol.2` naming is fixed by D5, empty inputs by R7/D8, the late unwritable-output crash by R10 and D6, the GPU-only dependency and lack of CI by D1–D3, and the missing tests by phase 01.
   - The exception is the "failed only after the whole book was OCR'd" problem. It stays open for unreadable images in every format except PNG and WebP (see M1).
2. **Simplicity.** Nothing material is over-built. The writability check is done twice, once by R10 and again by D6 creating the temp file early. That is folded into N1.
3. **Placement.** `src/scanscribe/` holds only `__init__.py`, so no existing code competes for this logic. The split is sound: `engine.py` for the protocol, errors and `load_engine`; `paddle_engine.py` for the adapter; plus `pages.py`, `output.py` and `cli.py`. No findings.
4. **Failure modes.** Data volume is fine: pages stream one at a time, and the plan states that the text is held in memory. Overlapping runs are fine: the temp files have unique names and the last rename wins. There are no timeouts to exceed. Findings M1, N1, N2, N4 and N5 cover the rest.
5. **Rollout.** "No deployment, one PR per phase, revert to undo" is accurate for a CLI with no data or migrations. N3 covers the downstream gap.

## Findings

### M1 · Major · Pre-check (plan.md › D6, Assumptions; phase 01 › task 2.2; notes.md › D9)

**What's wrong.** The page pre-check uses `Image.verify()`. In the locked Pillow, `verify()` checks the image data only for PNG; for JPEG, TIFF and BMP it does nothing. So a damaged JPEG, TIFF or BMP page gets past the pre-check. It fails during OCR, possibly hours into a run, and R8 then throws away every page already done.

That is exactly the failure Why complains about: "crashes only after the whole book has been OCR'd". It also defeats D6's goal, "Check everything before OCR". Folders of phone camera scans are usually JPEG, so this is the common case, not an edge case.

The plan understates the gap:
- plan.md:280–281 says "`Image.verify()` catches truncated PNGs but not every damaged JPEG".
- Phase 01 task 2.2 tests only "a corrupt image and a truncated PNG", so the gap would never show up in tests.

**Evidence.**
- `.venv/lib/python3.*/site-packages/PIL/ImageFile.py:287-293`: the base `ImageFile.verify()` only closes the file.
- `PIL/Image.py:1005-1014`: `Image.verify` is `pass`.
- Only `PngImagePlugin.py:872` overrides it.
- I ran a test in the scratchpad with Pillow 13.0.0 on images cut to half their length:

| Format | `verify()` | `convert("RGB")` |
| --- | --- | --- |
| JPEG | ok | `OSError: image file is truncated` |
| TIFF | ok | `OSError: image file is truncated` |
| BMP | ok | `OSError: image file is truncated` |
| PNG | `OSError` | `OSError` |
| WebP | `OSError` | `OSError` |

**Fix.** In the pre-check, fully decode each image with `im.load()` (or `convert("RGB")` and throw the result away) instead of calling `verify()`. This decodes every image twice. For a few hundred pages that costs seconds, against a possible loss of hours.

Then:
- add a truncated-JPEG fixture and test to phase 01 tasks 1.2 and 2.2;
- extend R8's first scenario to cover JPEG;
- drop or rewrite the Assumptions line.

### Nits

- **N1 · plan.md › D6 (lines 244–248); phase 01 › task 4.2.** The temp file is created before the engine loads, yet the text is written only at the end, and the temp file's name and mode are not specified.
  - A hard kill (SIGKILL, OOM, or SIGTERM, which nothing handles) leaves an orphan in the output folder. The first-run model download makes that window long.
  - `tempfile.mkstemp`/`NamedTemporaryFile` create the file with mode 0600, so after `os.replace` the output becomes 0600 instead of the umask default (usually 0644) that `write_text` gave.
  - Suggested fix: name the temp file `.<name>.*.tmp`, create it only at write time (R10 already checks writability), and `chmod` it to match the old output or the umask.
- **N2 · plan.md › D2 (lines 216–217); phase 02 › task 1.3.** "An `ImportError` naming `paddle`, `paddleocr` or a submodule becomes `EngineMissingError`" also catches a broken install. For example, a native-library load failure inside `paddle.base.*` raises an `ImportError` whose name is that submodule. The user is then told to run `uv sync --extra gpu` when the extra is already installed. Suggested fix: map only a `ModuleNotFoundError` whose `e.name` is exactly `paddle` or `paddleocr`, and let everything else go through the R12 path.
- **N3 · plan.md › Rollout & rollback (lines 297–301).** The section doesn't say how downstream consumers move over: AGENTS.md says the output feeds Skill Central's `study-book-chapter`. The "What changes" section lists breaking changes that affect consumers, such as `Vol.2/` → `Vol.2.txt` (line 55) and the command rename (`ocr-pdf` → `scanscribe`). Suggested fix: add one line on checking or updating the consumer, or state that it reads text from any path and is unaffected.
- **N4 · plan.md › Risks (lines 286–289); notes.md › D4 (lines 58–59), Manual check.** The BGR risk check can pass without testing anything. The notes expect almost no change for black text on white, and the owner chooses the input freely. A grayscale scan therefore yields "0 differing lines" and says nothing about D4. Suggested fix: require at least one colour page in the manual-check input, such as a sepia or highlighted Kindle screenshot. Also say what unblocks phase 02 if BGR reads worse: a plan `update` that reverses D4, or something else.
- **N5 · plan.md › R20 (lines 197–200); phase 02 › tasks 3.1–3.2.** Ctrl-C is tested only with `FakeEngine` raising `KeyboardInterrupt`. Whether real Paddle (C++ inference, its own signal handling) returns cleanly with exit 130 and leaves no temp file is never observed. Suggested fix: add one Ctrl-C mid-run to the owner's manual check on each device.
- **N6 · plan.md › R12 (line 155), D7 (line 255).** The plan doesn't say how a multi-line exception message becomes "one line"; Paddle errors often include a C++ traceback in their message. There is also no way to get the traceback when a real-engine failure needs diagnosing, which the prototype gave by default. Suggested fix: state the collapsing or truncation rule, and consider an env var that re-raises.

## Files referenced
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/plan.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/phases/01-pipeline-and-cli.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/phases/02-paddleocr-adapter.md
- /home/geo/develop/projects/scanscribe/docs/plans/2026-11-16-rebuild-cli/notes.md
- /home/geo/develop/projects/scanscribe/.venv/lib/python3.*/site-packages/PIL/ImageFile.py (lines 287-293)
- /home/geo/develop/projects/scanscribe/.venv/lib/python3.*/site-packages/PIL/Image.py (lines 1005-1014)
- /home/geo/develop/projects/scanscribe/AGENTS.md (downstream consumer statement)
- Test script, not part of the repository: /tmp/claude-1000/-home-geo-develop-projects-scanscribe/ddd143f4-42e7-4b6b-b49b-4aeb65c0ea1f/scratchpad/t.py
