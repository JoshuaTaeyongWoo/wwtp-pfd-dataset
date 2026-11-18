"""
s20_practice_set.py — five practice images for annotator training (not in the pilot sample).

One image per style proxy: PMC symbol diagram, US patent block diagram, EPA cropped figure,
Korean municipal pictorial, OpenAlex paper figure. Whole-page renders are excluded.
Outputs data/pilot/practice/{images/, practice5.csv, practice_sheet.jpg}.

Usage: python s20_practice_set.py [--seed 7]
"""
from __future__ import annotations

import argparse
import random
import re
import shutil
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from common import DATA, ROOT
from s09_make_sheets import load_image

OUT = DATA / "pilot" / "practice"


def page_like(s: str) -> bool:
    try:
        w, h = (int(x) for x in re.findall(r"\d+", s)[:2])
    except Exception:
        return True
    return h > 1400 and 1.25 <= h / w <= 1.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    df = pd.read_csv(DATA / "triage_final.csv", dtype=str, encoding="utf-8-sig").fillna("")
    pilot = set(pd.read_csv(DATA / "pilot" / "pilot60.csv", dtype=str, encoding="utf-8-sig")["record_id"])
    m = df[(df["split"] == "main") & (~df["record_id"].isin(pilot)) & (~df["image_size"].map(page_like))]
    specs = [("europepmc_pmc", lambda r: r["category"] == "wwtp"),
             ("patents_google", lambda r: r["record_id"].startswith("patents_google:US")),
             ("epa_manuals", lambda r: "#crop" in r["record_id"]),
             ("korean_municipal", lambda r: True),
             ("openalex_nonpmc", lambda r: r["category"] == "wwtp")]
    picks = []
    for src, cond in specs:
        g = m[(m["source"] == src) & m.apply(cond, axis=1)]
        picks.append(g.iloc[rng.randrange(len(g))])
    shutil.rmtree(OUT, ignore_errors=True)
    (OUT / "images").mkdir(parents=True)
    rows = []
    for i, r in enumerate(picks, 1):
        src = ROOT / r["image_path"]
        dst = OUT / "images" / f"practice_{i:02d}__{src.stem[:50]}{src.suffix.lower()}"
        shutil.copy2(src, dst)
        rows.append({"practice_no": i, "record_id": r["record_id"], "source": r["source"], "category": r["category"],
                     "image": dst.relative_to(ROOT).as_posix(), "caption": r["caption"][:200]})
    pd.DataFrame(rows).to_csv(OUT / "practice5.csv", index=False, encoding="utf-8-sig")
    cell = 620
    sheet = Image.new("RGB", (cell * 3, cell * 2), "white")
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("arial.ttf", 26)
    for i, r in enumerate(rows):
        im = load_image(ROOT / r["image"])
        x, y = (i % 3) * cell, (i // 3) * cell
        if im is not None:
            im.thumbnail((cell - 10, cell - 40))
            sheet.paste(im, (x + 5, y + 35))
        d.rectangle([x, y, x + cell - 1, y + cell - 1], outline="#cccccc")
        d.text((x + 8, y + 4), f"{r['practice_no']}  {r['source']}", fill="black", font=font)
    sheet.save(OUT / "practice_sheet.jpg", "JPEG", quality=85)
    for r in rows:
        print(r["practice_no"], r["source"], r["category"], "|", r["caption"][:90])


if __name__ == "__main__":
    main()
