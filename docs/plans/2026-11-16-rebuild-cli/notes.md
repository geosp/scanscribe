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
| `ocr.predict(rgb_array)`, then `result.get("rec_texts", [])` for each result | Same calls, but the array is BGR (D4) |
| `Processing page N...` and `Extracted text written to <path>` on stderr | Same, plus the device line (R11, R16) |
| Missing input → `parser.error` (exit 2). Every other failure → traceback | Usage and input errors with exit 2 and 1 (D7, R12) |
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

## D4: PaddleOCR reads arrays as BGR

- `paddlex/inference/pipelines/ocr/pipeline.py:148`: the OCR pipeline builds
  `ReadImage(format="BGR")`.
- `paddlex/inference/common/reader/image_reader.py:51-55`: for a NumPy array, `read()` converts
  only when `format == "RGB"`. With `"BGR"` the array is used as given, so it is assumed to be BGR
  already.
- The per-model predictors then convert BGR to RGB for their own input (`ReadImage(format="RGB")` in
  the text detection and recognition predictors).
- So the prototype's RGB arrays were read with red and blue swapped. For black text on white the
  effect should be small. Phase 02's manual check measures it.

## D8: Zero-page PDFs in pypdfium2

Observed with pypdfium2 5.13.0 (no OCR, no device involved):

- `PdfDocument.new()` then `.save()` writes a file that `PdfDocument(path)` refuses to open:
  `PdfiumError: Failed to load document (PDFium: Success)`.
- A hand-written PDF with `/Type /Pages /Kids [] /Count 0` fails the same way.
- A non-PDF file (plain text) also raises `PdfiumError` on open.
- A one-page PDF written by Pillow (`Image.save(path, "PDF")`) opens with `len(doc) == 1`.

So the zero-page case reaches the user as an open failure. R7 maps both that and `len(doc) == 0`
to the same input error. The `len == 0` branch is tested by substituting a fake document.

## D9: Fake engine and fixtures

- Page images are solid-color RGB images made with Pillow in `tmp_path`. For column tests, each
  slice is a different solid color.
- `FakeEngine.recognize(image)` returns `[f"rgb{r},{g},{b}"]` for the image's center pixel and
  records each image's shape. Tests then check page order, slice order and slice widths.
- PDFs are written by Pillow (`save_all=True, append_images=[...]`, `resolution=72.0`), so a
  72 × 72 px image is a 1-inch page and `--dpi 144` must render it at 144 px.
- A corrupt image is a file with a valid extension and random bytes. A "truncated" image keeps the
  PNG header and drops the rest.
- No fixture file is committed. `.gitignore` already allows `tests/fixtures/**`; it stays unused.

## Manual check

Phase 02 ends with the owner running both tools on the same local input (from `in/`, never
committed), once with each extra:

```bash
# outputs go to out/, which Git ignores
# prototype (its GPU build; add --device cpu for the CPU comparison)
(cd ../ocr-pdf && uv run ocr-pdf <input> -o ../scanscribe/out/proto.txt)
# scanscribe, once per extra
uv sync --extra gpu && uv run scanscribe <input> -o out/gpu.txt
uv sync --extra cpu && uv run scanscribe <input> -o out/cpu.txt
diff out/proto.txt out/gpu.txt | grep -c '^[<>]'   # a count only; never paste book lines
```

Record in the PR: the input described without quoting it (for example "a 12-page two-column
scan"), the command, the device line printed, the run time, page count, and how many lines differ
from the prototype. Run the prototype on the CPU too if it can't use the GPU.
