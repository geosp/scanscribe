"""Check that the library API returns what the command writes, with the real engine.

Task 3.3 of docs/plans/2026-11-21-library-api, extended at plan close. Uses only self-made pages
from the phase 02 demo, so nothing here is book material. Run from the repository root with an
engine extra installed:

    uv sync --locked --extra gpu
    uv run python docs/demos/2026-11-16-ocr-check/make_pages.py <work folder>/pages
    uv run python docs/demos/2026-11-21-library-check/check.py <work folder>

It writes <work folder>/pages.pdf and <work folder>/cli.txt. With one loaded engine it then runs
`transcribe` twice, stops a third run by raising from `on_page`, and runs it once more. It prints
only the device, page counts, timings and whether each text matches the command's: never the text
itself.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

from scanscribe import load_engine, transcribe

STOP_AT = 5
"""The page whose progress call raises, in the stopped run."""


class Stop(Exception):
    """Raised from `on_page` to stop a run between pages."""


def yes(ok: bool) -> str:
    return "yes" if ok else "NO"


def main(work: Path) -> int:
    pages = sorted((work / "pages").glob("page*.png"))
    if len(pages) <= STOP_AT:
        print(f"need more than {STOP_AT} page*.png in {work / 'pages'}; run make_pages.py first")
        return 2
    pdf = work / "pages.pdf"
    images = [Image.open(path).convert("RGB") for path in pages]
    images[0].save(pdf, "PDF", save_all=True, append_images=images[1:], resolution=200.0)
    every_page = list(range(1, len(pages) + 1))

    cli_out = work / "cli.txt"
    start = time.monotonic()
    subprocess.run(["scanscribe", str(pdf), "-o", str(cli_out)], check=True)
    cli_s = time.monotonic() - start
    expected = cli_out.read_text(encoding="utf-8")

    devices: list[str] = []
    engine = load_engine("en", None, on_device=devices.append)
    stdout_before = sys.stdout

    # Run 1: the original task 3.3 check.
    seen: list[int] = []
    start = time.monotonic()
    first = transcribe(pdf, engine, on_page=lambda n, total: seen.append(n))
    lib_s = time.monotonic() - start
    same = first == expected
    ok = same and seen == every_page

    # Run 2: the same engine again.
    seen_again: list[int] = []
    start = time.monotonic()
    second = transcribe(pdf, engine, on_page=lambda n, total: seen_again.append(n))
    reuse_s = time.monotonic() - start
    reuse_ok = second == expected and seen_again == every_page

    # Run 3: stop between pages by raising from on_page.
    stopped_at: list[int] = []

    def stop_early(n: int, total: int) -> None:
        stopped_at.append(n)
        if n == STOP_AT:
            raise Stop

    stop_raised = False
    try:
        transcribe(pdf, engine, on_page=stop_early)
    except Stop:
        stop_raised = True
    stdout_restored = sys.stdout is stdout_before
    stop_ok = stop_raised and stopped_at == list(range(1, STOP_AT + 1)) and stdout_restored

    # Run 4: the same engine after the stopped run.
    seen_after: list[int] = []
    start = time.monotonic()
    after = transcribe(pdf, engine, on_page=lambda n, total: seen_after.append(n))
    after_s = time.monotonic() - start
    after_ok = after == expected and seen_after == every_page

    print(f"device: {devices[0]}")
    print(f"pages: {len(pages)}, progress calls: {len(seen)}")
    print(f"command: {cli_s:.1f} s (includes engine load); transcribe: {lib_s:.1f} s")
    print(f"transcribe equals the command's output: {yes(same)}")
    print(
        f"second run, same engine: {reuse_s:.1f} s, progress calls: {len(seen_again)}, "
        f"equals: {yes(second == expected)}"
    )
    print(
        f"stopped run: raised at page {STOP_AT}: {yes(stop_raised)}, "
        f"progress calls: {len(stopped_at)}, stdout restored: {yes(stdout_restored)}"
    )
    print(
        f"run after the stop: {after_s:.1f} s, progress calls: {len(seen_after)}, "
        f"equals: {yes(after == expected)}"
    )
    return 0 if ok and reuse_ok and stop_ok and after_ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: check.py <work folder>")
    sys.exit(main(Path(sys.argv[1])))
