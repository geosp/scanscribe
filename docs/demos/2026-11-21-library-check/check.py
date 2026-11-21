"""Check that the library API returns what the command writes, with the real engine.

Task 3.3 of docs/plans/2026-11-21-library-api. Uses only self-made pages from the phase 02 demo,
so nothing here is book material. Run from the repository root with an engine extra installed:

    uv sync --locked --extra gpu
    uv run python docs/demos/2026-11-16-ocr-check/make_pages.py <work folder>/pages
    uv run python docs/demos/2026-11-21-library-check/check.py <work folder>

It writes <work folder>/pages.pdf and <work folder>/cli.txt, and prints only the device, page
counts, timings and whether the two texts match: never the text itself.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

from scanscribe import load_engine, transcribe


def main(work: Path) -> int:
    pages = sorted((work / "pages").glob("page*.png"))
    if not pages:
        print(f"no page*.png in {work / 'pages'}; run make_pages.py first", file=sys.stderr)
        return 2
    pdf = work / "pages.pdf"
    images = [Image.open(path).convert("RGB") for path in pages]
    images[0].save(pdf, "PDF", save_all=True, append_images=images[1:], resolution=200.0)

    cli_out = work / "cli.txt"
    start = time.monotonic()
    subprocess.run(["scanscribe", str(pdf), "-o", str(cli_out)], check=True)
    cli_s = time.monotonic() - start

    devices: list[str] = []
    seen: list[int] = []
    engine = load_engine("en", None, on_device=devices.append)
    start = time.monotonic()
    text = transcribe(pdf, engine, on_page=lambda n, total: seen.append(n))
    lib_s = time.monotonic() - start

    same = text == cli_out.read_text(encoding="utf-8")
    print(f"device: {devices[0]}")
    print(f"pages: {len(pages)}, progress calls: {len(seen)}")
    print(f"command: {cli_s:.1f} s (includes engine load); transcribe: {lib_s:.1f} s")
    print(f"transcribe equals the command's output: {'yes' if same else 'NO'}")
    return 0 if same and seen == list(range(1, len(pages) + 1)) else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: check.py <work folder>")
    sys.exit(main(Path(sys.argv[1])))
