# Notes · Rebuild the scanscribe CLI from the ocr-pdf prototype

Evidence behind the plan. Nobody needs this file to understand [plan.md](plan.md). All checks below
were run on 2026-11-16 against the prototype's `.venv` (read only), with no book material opened.

## Prototype

What the prototype (`ocr-pdf`, `src/ocr_pdf/cli.py`, ~150 lines) does, and how this plan treats it:

| Prototype behavior | This plan |
| --- | --- |
| Folder pages: `iterdir()` filtered by suffix, natural sort on `path.name` | Same (R1), plus files only, no dotfiles, ties broken by exact name |
| File input always opened with pypdfium2, rendered at `scale = dpi / 72` | Same (R2). Open failures become input errors (R7) |
| `--columns N`: edges at `round(i * width / N)`; `N <= 1` means no split | Same edges (R4). `N < 1` is a usage error (R9). A page narrower than N px is an error (R5) |
| `"--- Page N ---\n" + "\n".join(lines)`, pages joined by `"\n\n"`, written once at the end | Same (R3, D6) |
| Default output `input.with_suffix(".txt")` for files and folders | Same for files. Folders use the full folder name (R6, D5) |
| `PaddleOCR(lang, device=None or --device, three use_* flags False, enable_mkldnn=False)` | Same flags. Device resolved by us (D3). `enable_mkldnn=False` only on the CPU (R17) |
| PDF pages via `page.render(scale).to_pil().convert("RGB")`; images via Pillow `convert("RGB")` | Same conversions (D4) |
| `ocr.predict(rgb_array)`, then `result.get("rec_texts", [])` for each result | Same calls, but the array is BGR (D4) |
| `Processing page N...` and `Extracted text written to <path>` on stderr | Same, plus the device line (R11, R16) |
| Missing input → `parser.error` (exit 2). Every other failure → traceback | Exit codes 2, 1 and 130, one-line errors (D7, R12, R20) |
| Writes the output with `write_text` at the end | Temp file and `os.replace` (D6) |
| Depends on `paddlepaddle-gpu` only; imports `paddleocr` inside `extract_text` | Two exclusive extras (already in `pyproject.toml`); lazy loader (D2) |

Installed versions in the prototype's environment: paddleocr 3.7.0, paddlex 3.7.2,
paddlepaddle-gpu 3.3.1, pypdfium2 5.13.0. scanscribe's `uv.lock` has pypdfium2 5.15.2.

## D3: Device detection in the installed Paddle

- `paddlex/utils/device.py:55-60`, `get_default_device()`: returns `gpu:0` when
  `paddle.device.is_compiled_with_cuda()` and `paddle.device.cuda.device_count() > 0`, else `cpu`.
  This is what the prototype got with `device=None`.
- `paddle/device/cuda/__init__.py:165`, `device_count()`: returns
  `core.get_cuda_device_count()` when the core has it, else 0. On a CPU build it returns 0, and
  `is_compiled_with_cuda()` is `False`.
- `paddleocr/_common_args.py:91`: `enable_mkldnn` is read only when the device type is `cpu`. On
  the GPU, `run_mode` comes from the GPU branch. Not passing it on the GPU (R17) leaves PaddleOCR's
  default (`DEFAULT_ENABLE_MKLDNN = True`, `paddleocr/_constants.py:18`), which is unused there.
- The prototype's comment on why MKL-DNN is off on the CPU: a paddlepaddle/oneDNN bug
  ("ConvertPirAttribute2RuntimeAttribute not support ...") with the PP-OCRv6 detection model.

Re-check these paths against the version in `uv.lock` when phase 02 starts.

**Re-checked 2026-11-16 (phase 02 task 1.1)** against paddleocr 3.7.0, paddlex 3.7.2 and
paddlepaddle-gpu 3.3.1, the versions in `uv.lock`, read in the prototype's environment:

- D3 holds. `get_default_device()` is now at `paddlex/utils/device.py:55-62`; `device_count()` is at
  `paddle/device/cuda/__init__.py:165`; `enable_mkldnn` is read at `paddleocr/_common_args.py:91`;
  `DEFAULT_ENABLE_MKLDNN = True` is at `paddleocr/_constants.py:18`.
- D4 holds. `ReadImage(format="BGR")` is at `paddlex/inference/pipelines/ocr/pipeline.py:148`; the
  NumPy branch of `read()` is at `paddlex/inference/common/reader/image_reader.py:51-55`.
- Output streams (R11): PaddleX's logger writes through `logging.StreamHandler(sys.stderr)`
  (`paddlex/utils/logging.py:138`). PaddleOCR's logger uses `logging.StreamHandler()`, which defaults to
  stderr (`paddleocr/_utils/logging.py:32`). Model downloads print progress to stderr
  (`paddlex/utils/download.py:42-49`). Nothing on the OCR path prints to stdout from Python. The
  adapter still redirects stdout to stderr around construction and `predict`, as a cheap guard; a
  native write to file descriptor 1 would escape it, and the manual check's empty-stdout test would
  catch that.

## D4: PaddleOCR reads arrays as BGR

- `paddlex/inference/pipelines/ocr/pipeline.py:148`: the OCR pipeline builds
  `ReadImage(format="BGR")`.
- `paddlex/inference/common/reader/image_reader.py:51-55`: for a NumPy array, `read()` converts
  only when `format == "RGB"`. With `"BGR"` the array is used as given, so it is assumed to be BGR
  already.
- The per-model predictors then convert BGR to RGB for their own input (`ReadImage(format="RGB")` in
  the text detection and recognition predictors).
- PDF pages: pypdfium2's raw bitmap is BGR(x). `render()` has `rev_byteorder=False` by default
  (`pypdfium2/_helpers/page.py`, around lines 453 and 520 in 5.15.2), and `to_numpy()` returns that
  buffer as is. `to_pil()` builds a correct RGB image, which the prototype used. So the prototype's
  PDF pages were RGB, like its images. The codebase-fit reviewer saw a red page come back as
  `[0 0 254]` from `to_numpy()` and `(254, 0, 0)` from `to_pil()`.
- So the prototype's RGB arrays were read with red and blue swapped. For black text on white the
  effect should be small. Phase 02's manual check measures it.

## D6: What Pillow's verify checks

Found in the design review (round 2, zoom-out reviewer) on the locked Pillow:

- `PIL/Image.py`, `Image.verify` is `pass`; `PIL/ImageFile.py`, the base `verify()` only closes
  the file. Only `PngImagePlugin.py` overrides it with a real check.
- Images cut to half their length:

| Format | `verify()` | `convert("RGB")` |
| --- | --- | --- |
| JPEG | passes | `OSError: image file is truncated` |
| TIFF | passes | `OSError: image file is truncated` |
| BMP | passes | `OSError: image file is truncated` |
| PNG | `OSError` | `OSError` |
| WebP | `OSError` | `OSError` |

So the pre-check decodes each image fully with `load()`, then closes it. Decoding each image twice costs
seconds per few hundred pages, against hours of lost OCR. Phone and camera scans
are usually JPEG, so `verify()` alone would miss the common case.

## D8: Zero-page PDFs in pypdfium2

Observed with pypdfium2 5.13.0 (no OCR, no device involved). The design review's codebase-fit
reviewer repeated the first and third checks on the locked 5.15.2, with the same results.

- `PdfDocument.new()` then `.save()` writes a file that `PdfDocument(path)` refuses to open:
  `PdfiumError: Failed to load document (PDFium: Success)`.
- A hand-written PDF with `/Type /Pages /Kids [] /Count 0` fails the same way.
- A non-PDF file (plain text) also raises `PdfiumError` on open.
- A one-page PDF written by Pillow (`Image.save(path, "PDF")`) opens with `len(doc) == 1`.

So the zero-page case reaches the user as an open failure. R7 maps both that and `len(doc) == 0`
to the same input error. The `len == 0` branch is tested by substituting a fake document.

## D9: Fake engine and fixtures

- Page images are solid-color RGB images made with Pillow in `tmp_path`, using a small palette of
  well-separated colors (for example red, green, blue, black, white). For column tests, each slice
  is a different color.
- `FakeEngine.recognize(image)` returns the name of the palette color nearest to the image's center
  pixel (for example `["red"]`), and records each image's shape. Pillow saves RGB PDF pages as JPEG,
  so a red page can come back as (254, 0, 0); the nearest-color rule absorbs that.
- PDFs are written by Pillow (`save_all=True, append_images=[...]`, `resolution=72.0`), so a
  72 × 72 px image is a 1-inch page and `--dpi 144` must render it at 144 px.
- A corrupt image is a file with a `.png` extension and random bytes; `Image.open` rejects it.
- A truncated image is a valid PNG cut to its first 60 bytes. The codebase-fit reviewer saw
  `Image.open` accept it and `convert` raise `OSError`. The pre-check's full decode must reject it;
  phase 01 task 1.2 confirms that `load()` rejects it.
- The plain-text input is `notes.dat`, so its default output (`notes.txt`) isn't the input itself.
- No fixture file is committed. `.gitignore` already allows `tests/fixtures/**`; it stays unused.

## Manual check

Phase 02 ends with the owner running both tools on the same local input (from `in/`, never
committed), once with each extra:

```bash
# outputs go to out/, which Git ignores
# prototype, once per device, each into its own baseline
IN=/absolute/path/to/folder  # page images with at least one color page; absolute, because of the cd
(cd ../ocr-pdf && uv run ocr-pdf "$IN" -o ../scanscribe/out/proto-gpu.txt)
(cd ../ocr-pdf && uv run ocr-pdf "$IN" --device cpu -o ../scanscribe/out/proto-cpu.txt)
# scanscribe, once per extra; stdout must stay empty
uv sync --extra gpu && uv run scanscribe "$IN" -o out/gpu.txt > out/gpu.stdout && test ! -s out/gpu.stdout
uv sync --extra cpu && uv run scanscribe "$IN" -o out/cpu.txt > out/cpu.stdout && test ! -s out/cpu.stdout
diff out/proto-gpu.txt out/gpu.txt | grep -c '^[<>]'   # a count only; never paste book lines
diff out/proto-cpu.txt out/cpu.txt | grep -c '^[<>]'
```

Pass rule: the owner reads the differing lines locally. A page reads worse when a word the
prototype got right is wrong in scanscribe's output. Such a page gets its own issue (described, not
quoted), and phase 02 stays blocked until the owner either reverses D4 through a plan update or
accepts the result. A grayscale-only input can't show the D4 effect, so the input includes at least one color page (for example, a highlighted or sepia screenshot). Use a
folder of page images: a PDF also goes through the newer pypdfium2, so its diff wouldn't measure D4
alone.

Then start one more run on each device and press Ctrl-C during page 2 or later: it must exit 130,
leave any existing output unchanged, and leave no `.*.tmp` file behind.

Record in the PR: the input described without quoting it (for example "a 12-page two-column
scan"), the command, the device line printed, the run time, page count, and how many lines differ
from the prototype. Run the prototype on the CPU too if it can't use the GPU.
