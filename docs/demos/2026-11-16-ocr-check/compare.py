"""Compare two OCR outputs of the same input without printing any of their text.

    uv run python docs/demos/2026-11-16-ocr-check/compare.py <baseline.txt> <new.txt>

Real inputs are usually copyrighted books, so this prints counts and similarity only: pages,
lines, words, lines that differ, and how many words appear in only one of the outputs.
"""

from __future__ import annotations

import difflib
import re
import sys
from collections import Counter
from pathlib import Path


def pages(text: str) -> list[str]:
    return re.split(r"^--- Page \d+ ---\n?", text, flags=re.MULTILINE)[1:]


def main(baseline_path: Path, new_path: Path) -> None:
    base_text = baseline_path.read_text("utf-8")
    new_text = new_path.read_text("utf-8")
    base_pages, new_pages = pages(base_text), pages(new_text)
    base_lines, new_lines = base_text.splitlines(), new_text.splitlines()
    differing = sum(
        1
        for line in difflib.unified_diff(base_lines, new_lines, lineterm="", n=0)
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    )
    base_words, new_words = Counter(base_text.split()), Counter(new_text.split())
    changed_pages = sum(1 for a, b in zip(base_pages, new_pages, strict=False) if a != b)
    ratio = difflib.SequenceMatcher(a=base_text, b=new_text, autojunk=False).ratio()
    print(f"pages: {len(base_pages)} vs {len(new_pages)}; pages that differ: {changed_pages}")
    print(f"lines: {len(base_lines)} vs {len(new_lines)}; differing lines (diff +/-): {differing}")
    print(f"words: {sum(base_words.values())} vs {sum(new_words.values())}")
    print(f"words only in baseline: {sum((base_words - new_words).values())}")
    print(f"words only in new: {sum((new_words - base_words).values())}")
    print(f"character similarity: {ratio:.4f}")
    print(f"byte-identical: {base_text == new_text}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
