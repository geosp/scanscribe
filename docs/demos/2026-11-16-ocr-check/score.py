"""Score OCR outputs against the ground truth from make_pages.py.

    uv run python docs/demos/2026-11-16-ocr-check/score.py <truth.json> <baseline.txt> <new.txt>

For each page it prints the word accuracy of both outputs and the words the baseline got right
but the new output got wrong ("reads worse", the plan's pass rule).
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path


def pages(text: str) -> list[list[str]]:
    parts = re.split(r"^--- Page \d+ ---\n?", text, flags=re.MULTILINE)[1:]
    return [part.split() for part in parts]


def correct_positions(truth: list[str], found: list[str]) -> set[int]:
    """Indexes of truth words that the output reproduced exactly, in order."""
    matcher = difflib.SequenceMatcher(a=truth, b=found, autojunk=False)
    hits: set[int] = set()
    for block in matcher.get_matching_blocks():
        hits.update(range(block.a, block.a + block.size))
    return hits


def main(truth_path: Path, baseline_path: Path, new_path: Path) -> int:
    truth = json.loads(truth_path.read_text("utf-8"))
    baseline = pages(baseline_path.read_text("utf-8"))
    new = pages(new_path.read_text("utf-8"))
    worse_pages = 0
    total = base_hits = new_hits = 0
    print("| Page | Style | Words | Baseline correct | New correct | Words worse in new |")
    print("| --- | --- | --- | --- | --- | --- |")
    for index, (name, page) in enumerate(sorted(truth.items())):
        words = " ".join(page["lines"]).split()
        base = correct_positions(words, baseline[index])
        got = correct_positions(words, new[index])
        worse = sorted(base - got)
        worse_pages += bool(worse)
        total += len(words)
        base_hits += len(base)
        new_hits += len(got)
        lost = ", ".join(words[i] for i in worse) or "none"
        print(f"| {name} | {page['style']} | {len(words)} | {len(base)} | {len(got)} | {lost} |")
    print(
        f"| all | | {total} | {base_hits} ({base_hits / total:.1%}) | "
        f"{new_hits} ({new_hits / total:.1%}) | {worse_pages} page(s) |"
    )
    return 1 if worse_pages else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
