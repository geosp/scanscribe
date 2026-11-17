"""Generate colour test pages with known text for the phase 02 OCR check.

Every page and every sentence here is self-made, so the pages and their ground truth can be
committed and shared. Run from the repository root:

    uv run python docs/demos/2026-11-16-ocr-check/make_pages.py <output folder>

It writes page01.png ... page10.png and truth.json (the expected lines of each page).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SERIF = "/usr/share/fonts/liberation-serif-fonts/LiberationSerif-Regular.ttf"
SANS = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"

ENGLISH = [
    "The river carried seven paper boats past the old mill.",
    "Morning light fell across the kitchen table and the open map.",
    "She counted forty-two steps between the gate and the well.",
    "A quiet wind moved the wheat like a slow green tide.",
    "Every Tuesday the baker left a warm loaf by the door.",
    "The lantern swung twice before the storm reached the hill.",
]
SPANISH = [
    "El niño guardó la canción en una caja de cartón azul.",
    "La señora Núñez cruzó el puente antes del amanecer.",
    "Había ocho pájaros sobre el tejado de la estación vieja.",
    "Mañana iremos al mercado a comprar limones y café.",
    "El reloj de la plaza marcó las doce con un sonido grave.",
    "Aquí termina el camino y empieza el bosque de pinos.",
]

# (name, background RGB, ink RGB, highlight band RGB or None, font, sentences)
PAGES = [
    ("black on white (control)", (255, 255, 255), (0, 0, 0), None, SERIF, ENGLISH),
    ("black on yellow highlight", (255, 255, 255), (0, 0, 0), (255, 235, 59), SERIF, SPANISH),
    ("red ink on white", (255, 255, 255), (200, 20, 20), None, SERIF, ENGLISH),
    ("blue ink on cream", (250, 244, 225), (25, 50, 190), None, SANS, SPANISH),
    ("white ink on dark blue", (20, 40, 110), (255, 255, 255), None, SANS, ENGLISH),
    ("brown ink on sepia", (233, 214, 175), (90, 60, 30), None, SERIF, SPANISH),
    ("green ink on pink", (252, 220, 230), (20, 120, 50), None, SANS, ENGLISH),
    ("dark ink on orange highlight", (255, 255, 255), (30, 30, 30), (255, 170, 80), SANS, SPANISH),
    ("orange ink on light blue", (210, 230, 250), (220, 110, 0), None, SERIF, ENGLISH),
    ("magenta ink on pale green", (225, 245, 225), (170, 20, 140), None, SANS, SPANISH),
    # Low contrast, where swapping red and blue changes how far ink and paper differ in
    # brightness, so these pages are sensitive to the channel order (D4).
    ("red ink on blue (low contrast)", (60, 60, 220), (220, 40, 40), None, SANS, ENGLISH),
    ("blue ink on red (low contrast)", (220, 60, 60), (40, 40, 220), None, SERIF, SPANISH),
    ("orange ink on purple (low contrast)", (120, 60, 200), (230, 140, 40), None, SERIF, ENGLISH),
    ("teal ink on salmon (low contrast)", (240, 150, 130), (30, 150, 170), None, SANS, SPANISH),
]


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    truth = {}
    for number, (name, background, ink, band, font_path, sentences) in enumerate(PAGES, 1):
        font = ImageFont.truetype(font_path, 34)
        image = Image.new("RGB", (1240, 900), background)
        draw = ImageDraw.Draw(image)
        for i, line in enumerate(sentences):
            y = 90 + i * 120
            if band is not None:
                left, top, right, bottom = draw.textbbox((80, y), line, font=font)
                draw.rectangle((left - 10, top - 10, right + 10, bottom + 10), fill=band)
            draw.text((80, y), line, fill=ink, font=font)
        file_name = f"page{number:02d}.png"
        image.save(out / file_name)
        truth[file_name] = {"style": name, "lines": sentences}
    (out / "truth.json").write_text(json.dumps(truth, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
