# OCR check: prototype vs scanscribe, GPU and CPU

The manual OCR check that closes phase 02 of [the rebuild-cli plan](../../plans/2026-11-16-rebuild-cli/plan.md): tasks 3.1 and 3.2, following [notes.md#manual-check](../../plans/2026-11-16-rebuild-cli/notes.md#manual-check). The owner delegated the run to the coding agent on 2026-11-16.

**Result: pass on both devices.**
- **Accuracy:** no page reads worse than with the prototype. On self-made colour pages with known text, both tools read all 868 words correctly. On real chapters, old and new differ only in line order on one page and in spaces or punctuation elsewhere; no word changed.
- **Output and errors:** stdout stayed empty, and the CPU build gave no oneDNN error.
- **Ctrl-C:** exits 130 with one line, leaves the output unchanged and leaves no temp file.

## Setup

| | |
| --- | --- |
| Machine | AMD Ryzen 9 8945HS (16 threads), NVIDIA GeForce RTX 3060 12 GB, driver 610.43.03, Linux |
| Old | `ocr-pdf` prototype at `1f5d35d`, in its own environment (`paddlepaddle-gpu` 3.3.1, `paddleocr` 3.7.0); run with `--device cpu` for the CPU comparison |
| New | `scanscribe` at `ff98690` (PR #7), with `uv sync --locked --extra gpu` and then `--extra cpu` (`paddlepaddle` 3.3.1), same `paddleocr` 3.7.0 |
| Options | defaults for both: `--lang en`, `--dpi 200`, `--columns 1` |

Both tools use the same Paddle and PaddleOCR versions, so differences come from scanscribe's changes. For image folders that means mainly the BGR channel order (D4).

## 1. Colour pages with known text

[make_pages.py](make_pages.py) renders 14 self-made pages (English and Spanish sentences, 868 words):
- coloured inks;
- coloured and highlighted backgrounds;
- four low-contrast pages where swapping red and blue changes how hard the text is to read.

[score.py](score.py) scores each output word by word against the known text.

```bash
uv run python docs/demos/2026-11-16-ocr-check/make_pages.py /tmp/colour
uv run python docs/demos/2026-11-16-ocr-check/score.py /tmp/colour/truth.json proto.txt new.txt
```

| Device | Prototype correct | scanscribe correct | Pages worse in scanscribe | Prototype time | scanscribe time | `Using device` |
| --- | --- | --- | --- | --- | --- | --- |
| GPU | 868 / 868 (100%) | 868 / 868 (100%) | 0 | 4.5 s | 5.7 s | `gpu:0` |
| CPU | 868 / 868 (100%) | 868 / 868 (100%) | 0 | 98.9 s | 104.5 s | `cpu` |

Every page, including the low-contrast ones, read perfectly in both tools. On clean rendered text the channel order makes no measurable difference.

## 2. Real input

Two chapters of page images from the owner's local `in/` folder, never committed:

- a **Spanish chapter of 23 pages**, 2960×1848 Kindle screenshots, one page with a little colour;
- an **English chapter of 9 pages**, 1848×2960 Kindle screenshots, grayscale.

Book text never leaves the machine. [compare.py](compare.py) prints only counts and similarity. Each differing word was then checked mechanically, again without printing it: same letters ignoring spaces and punctuation, the letter edit distance, and whether the lines were only reordered.

| Chapter | Device | Prototype time | scanscribe time | Pages that differ | Lines that differ | Character similarity | What differs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Spanish, 23 p. | GPU | 26.6 s | 27.1 s | 2 of 23 | 4 of 1,075 | 0.9998 | Page 1 (the colour page): same lines, different order. Page 11: one space joined, same letters |
| Spanish, 23 p. | CPU | 1,246 s | 1,348 s | 2 of 23 | 4 of 1,075 | 0.9998 | The same two differences |
| English, 9 p. | GPU | 14.1 s | 14.4 s | 1 of 9 | 2 of 463 | 1.0000 | One space joined, same letters |
| English, 9 p. | CPU | 630 s | 663 s | 2 of 9 | 4 of 463 | 0.9999 | Spaces or punctuation only, same letters |

**Pass rule** (plan Risks): a page reads worse when a word the prototype got right is wrong. No case changes a letter: the letter edit distance is 0 in every differing span. So no page reads worse.

For scale, each tool differs more between its own GPU and CPU runs than old differs from new:

| Chapter | Prototype GPU vs CPU | scanscribe GPU vs CPU |
| --- | --- | --- |
| Spanish | 8 lines differ | 8 lines differ |
| English | 4 lines differ | 6 lines differ |

In every run stdout was empty (0 bytes), the device line read `Using device: gpu:0` or `Using device: cpu`, and the CPU build logged no oneDNN error.

## 3. Ctrl-C

[ctrlc.sh](ctrlc.sh) starts a run over an existing output file and waits for `Processing page 2...`. It then sends SIGINT to the run's whole process group, as a terminal Ctrl-C does. It does this twice per build: once through `uv run scanscribe`, and once with `.venv/bin/scanscribe` directly. Input: the English chapter.

| Build | Launched with | Exit | Stopped after | Output unchanged | Temp files left | stdout | Last stderr line | Tracebacks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GPU | `uv run` | 130 | 0.4 s | yes | 0 | empty | `scanscribe: error: interrupted` | 0 |
| GPU | direct | 130 | 0.5 s | yes | 0 | empty | `scanscribe: error: interrupted` | 0 |
| CPU | `uv run` | 130 | 24.7 s | yes | 0 | empty | `scanscribe: error: interrupted` | 0 |
| CPU | direct | 130 | 24.8 s | yes | 0 | empty | `scanscribe: error: interrupted` | 0 |

On the CPU the run stops only when the page in progress finishes. Python can't act on Ctrl-C while PaddleOCR is inside native code, and one large page takes about 25 s on this CPU.

A first attempt sent SIGINT with `kill -INT -- -PID` from a script without job control. The PID didn't lead a process group, so no process received the signal and the run completed normally. This was a fault in the test harness: sending SIGINT inside the process raised `KeyboardInterrupt` at once, and the corrected harness above uses `set -m`.

## Not covered

- **PDF input.** The PDF path also changes pypdfium2 (5.13.0 to 5.15.2), so the plan uses an image folder to isolate D4. PDF rendering is covered by the unit tests.
- **`--columns` above 1 on real pages.** The column split is covered by the unit tests.
- **The GPU build on a machine without a GPU.** Not available here.
