"""
s09_make_sheets.py — render contact sheets (20 thumbnails each, numbered 0-19) for AI-assisted first-pass triage.

Each sheet is a 5 x 4 grid of 360-px thumbnails taken from catalog_canonical.csv, grouped by source.
The mapping sheet -> [record_id, ...] is written to data/review/sheets/sheets.json so decisions made on a
sheet can be joined back to catalog rows. SVG files (Wikimedia) are rasterised with PyMuPDF.

Usage: python s09_make_sheets.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from common import DATA, ROOT

SHEETS = DATA / "review" / "sheets"
COLS, ROWS, CELL = 5, 4, 360
PER_SHEET = COLS * ROWS


def load_image(p: Path) -> Image.Image | None:
    try:
        if p.suffix.lower() == ".svg":
            import pymupdf
            doc = pymupdf.open(p)
            pix = doc[0].get_pixmap(dpi=96)
            im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            doc.close()
            return im
        with Image.open(p) as im:
            if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                # transparent background -> composite on white (otherwise it renders black)
                rgba = im.convert("RGBA")
                bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                return Image.alpha_composite(bg, rgba).convert("RGB")
            return im.convert("RGB")
    except Exception:
        return None


def main():
    df = pd.read_csv(DATA / "catalog_canonical.csv", dtype=str).fillna("")
    SHEETS.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
    mapping = {}
    order = ["europepmc_pmc", "openalex_nonpmc", "epa_manuals", "korean_municipal", "wikimedia_commons", "patents_google"]
    for source in order:
        g = df[df["source"] == source]
        # literature first by caption tier so T1 sheets come first
        if "caption_tier" in g:
            g = g.sort_values(["caption_tier", "record_id"])
        rows = g.to_dict("records")
        for k in range(0, len(rows), PER_SHEET):
            chunk = rows[k:k + PER_SHEET]
            sheet = Image.new("RGB", (COLS * CELL, ROWS * CELL), "white")
            d = ImageDraw.Draw(sheet)
            ids = []
            for i, r in enumerate(chunk):
                im = load_image(ROOT / r["image_path"])
                x, y = (i % COLS) * CELL, (i // COLS) * CELL
                if im is not None:
                    im.thumbnail((CELL - 8, CELL - 8))
                    sheet.paste(im, (x + 4, y + 4))
                d.rectangle([x, y, x + 40, y + 26], fill="red")
                d.text((x + 5, y + 2), str(i), fill="white", font=font)
                d.rectangle([x, y, x + CELL - 1, y + CELL - 1], outline="#cccccc")
                ids.append(r["record_id"])
            name = f"{source}_{k // PER_SHEET:03d}.jpg"
            sheet.save(SHEETS / name, "JPEG", quality=82)
            mapping[name] = {"source": source, "record_ids": ids,
                             "captions": [(r.get("caption") or "")[:160] for r in chunk],
                             "caption_tier": [r.get("caption_tier") or "" for r in chunk]}
        print(source, len(rows), "images ->", (len(rows) + PER_SHEET - 1) // PER_SHEET, "sheets")
    (SHEETS / "sheets.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8")
    print("total sheets", len(mapping))


if __name__ == "__main__":
    main()
