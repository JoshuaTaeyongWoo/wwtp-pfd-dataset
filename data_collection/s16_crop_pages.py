"""
s16_crop_pages.py — semi-automatic figure cropping for whole-page renders in the main split.

Why: pdf_figures.py saved a 200-dpi render of the whole page whenever a caption matched (vector
figures are not image objects). About a quarter of main (EPA 64, OpenAlex 109 on 2026-11-16) are
therefore text pages with an embedded figure. Annotators must not label text pages.

How (PyMuPDF page layout, no OCR):
  1. open the source PDF (data/raw/<source>/_pdf/<doc>.pdf) at the page stored in extra_json;
  2. find the caption block (line starting with Fig/Figure ...) that best matches the record caption;
  3. classify text blocks as body text (>= 3 lines and wider than 45 % of the page, or 2 lines and
     wider than 60 %) or label-ish (everything else);
  4. take the vertical band directly above the caption (and, as an alternative, directly below)
     that is free of body-text blocks; the figure region = union of vector drawings, image blocks
     and label-ish text inside that band, padded by 6 pt; the side with more graphic content wins;
  5. sanity: region >= 120 x 60 pt and >= 5 % of the page area, else the page goes to the manual queue;
  6. convert to pixel coordinates of the page render (scale = image width / page width).

Outputs (data/review/):
  crops_auto.json        {record_id: [[x0,y0,x1,y1]]}   -> s13_apply_crops.py --json ... --method auto
  crops_auto_report.csv  record_id, source, page, status, method, box_px, reason
  crops_auto_manual.csv  pages that need the manual crop tool (s12)
  sheets_crops/          preview sheets: page with the box drawn + the crop, 8 per sheet

Usage: python s16_crop_pages.py [--sources openalex_nonpmc,epa_manuals] [--limit N]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import pandas as pd
import pymupdf
from PIL import Image, ImageDraw, ImageFont

from common import DATA, ROOT, RAW
from pdf_figures import CAP_RX

REVIEW = DATA / "review"
SHEETS = REVIEW / "sheets_crops"
PAD = 6.0


def page_like(size_str: str) -> bool:
    try:
        w, h = (int(x) for x in re.findall(r"\d+", size_str)[:2])
    except Exception:
        return False
    return h > 1400 and 1.25 <= h / w <= 1.5


def is_body_text(b: dict, pw: float) -> bool:
    n = len(b["lines"])
    w = b["bbox"][2] - b["bbox"][0]
    # two-column papers: a body paragraph is ~45 % of the page width, so 30 % with >= 3 lines counts
    return (n >= 3 and w >= 0.30 * pw) or (n >= 2 and w >= 0.6 * pw)


def block_text(b: dict) -> str:
    return " ".join(s["text"] for l in b["lines"] for s in l["spans"]).strip()


def find_caption(text_blocks: list[dict], caption: str) -> dict | None:
    cands = [b for b in text_blocks if CAP_RX.match(block_text(b))]
    if not cands:
        return None
    key = re.sub(r"\W+", " ", caption.lower())[:40].strip()
    for b in cands:
        if key and key[:25] in re.sub(r"\W+", " ", block_text(b).lower()):
            return b
    return cands[0]


def graphic_rects(page: pymupdf.Page) -> list[pymupdf.Rect]:
    pr = page.rect
    rects = []
    for d in page.get_drawings():
        r = d["rect"]
        if r.width > 0.92 * pr.width and r.height < 3:      # horizontal rules / header lines
            continue
        if r.width > 0.95 * pr.width and r.height > 0.95 * pr.height:  # page background box
            continue
        if r.is_empty or r.width < 1 and r.height < 1:
            continue
        rects.append(r)
    for info in page.get_image_info():
        r = pymupdf.Rect(info["bbox"])
        if r.width >= 8 and r.height >= 8 and not (r.width > 0.95 * pr.width and r.height > 0.95 * pr.height):
            rects.append(r)
    return rects


def band_region(page: pymupdf.Page, cap: dict, body: list[dict], labels: list[dict], gfx: list[pymupdf.Rect], above: bool):
    pr = page.rect
    cy0, cy1 = cap["bbox"][1], cap["bbox"][3]
    if above:
        top = max([pr.y0 + 20] + [b["bbox"][3] for b in body if b["bbox"][3] <= cy0 + 2])
        y0, y1 = top, cy0
    else:
        bottom = min([pr.y1 - 20] + [b["bbox"][1] for b in body if b["bbox"][1] >= cy1 - 2])
        y0, y1 = cy1, bottom
    if y1 - y0 < 40:
        return None, 0.0
    band = pymupdf.Rect(pr.x0, y0, pr.x1, y1)
    content = [r for r in gfx if r.intersects(band) and (r & band).height > 2]
    area = sum((r & band).get_area() for r in content)
    if not content:
        return None, 0.0
    region = pymupdf.Rect(content[0] & band)
    for r in content[1:]:
        region |= (r & band)
    for b in labels:  # short text inside the band (axis labels, unit names) stays in the crop
        rb = pymupdf.Rect(b["bbox"])
        if rb.intersects(band) and rb.width < 0.6 * pr.width and region.intersects(rb + (-15, -15, 15, 15)):
            region |= rb
    region = pymupdf.Rect(region.x0 - PAD, region.y0 - PAD, region.x1 + PAD, region.y1 + PAD) & pymupdf.Rect(pr.x0, y0, pr.x1, y1)
    return region, area


def band_bounds(page: pymupdf.Page, cap: dict, body: list[dict], above: bool):
    pr = page.rect
    cy0, cy1 = cap["bbox"][1], cap["bbox"][3]
    if above:
        top = max([pr.y0 + 20] + [b["bbox"][3] for b in body if b["bbox"][3] <= cy0 + 2])
        return top, cy0
    bottom = min([pr.y1 - 20] + [b["bbox"][1] for b in body if b["bbox"][1] >= cy1 - 2])
    return cy1, bottom


def ink_region(image_path: Path, page: pymupdf.Page, y0: float, y1: float, body: list[dict], cap: dict):
    """Scan mode: the page is one full-page raster + OCR text. Inside the caption band, mask the OCR
    body-text blocks and the caption, threshold the render, remove specks with an opening and take the
    bounding box of the remaining ink. Returns (Rect in pt, ink fraction) or (None, 0)."""
    import numpy as np
    from PIL import ImageFilter
    pr = page.rect
    im = Image.open(image_path).convert("L")
    s = im.width / pr.width
    x0p, y0p, x1p, y1p = int(10 * s), int(y0 * s), int((pr.width - 10) * s), int(y1 * s)
    if y1p - y0p < 60 * s:
        return None, 0.0
    band = im.crop((x0p, y0p, x1p, y1p))
    arr = np.array(band) < 160
    for b in body + [cap]:  # erase running text and the caption itself
        bx0, by0, bx1, by1 = (int(v * s) for v in b["bbox"])
        arr[max(0, by0 - y0p - 2):max(0, by1 - y0p + 2), max(0, bx0 - x0p - 2):max(0, bx1 - x0p + 2)] = False
    mask = Image.fromarray((arr * 255).astype("uint8")).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    ink = np.array(mask) > 0
    ys, xs = np.where(ink)
    if len(ys) < 200:
        return None, 0.0
    # trim stray specks: keep the 0.5-99.5 percentile extent
    ry0, ry1 = np.percentile(ys, [0.5, 99.5])
    rx0, rx1 = np.percentile(xs, [0.5, 99.5])
    region = pymupdf.Rect((rx0 + x0p) / s - PAD, (ry0 + y0p) / s - PAD, (rx1 + x0p) / s + PAD, (ry1 + y0p) / s + PAD)
    return region & pymupdf.Rect(pr.x0, y0, pr.x1, y1), float(ink.mean())


def crop_for(pdf: Path, pno: int, caption: str, img_w: int, image_path: Path | None = None):
    doc = pymupdf.open(pdf)
    page = doc[pno - 1]
    pr = page.rect
    tb = [b for b in page.get_text("dict")["blocks"] if b["type"] == 0 and b["lines"]]
    if len(page.get_text()) < 50:
        doc.close()
        return None, "no text layer (scanned page)"
    cap = find_caption(tb, caption)
    if cap is None:
        doc.close()
        return None, "caption block not found"
    body = [b for b in tb if is_body_text(b, pr.width) and b is not cap]
    labels = [b for b in tb if b not in body and b is not cap]
    gfx = graphic_rects(page)
    ra, aa = band_region(page, cap, body, labels, gfx, above=True)
    rb, ab = band_region(page, cap, body, labels, gfx, above=False)
    region, side = (ra, "above") if aa >= ab else (rb, "below")
    scan_note = ""
    if region is None and image_path is not None:
        # scanned page (full-page raster + OCR): fall back to pixel ink inside the OCR band
        best = (None, 0.0, "")
        for above in (True, False):
            y0, y1 = band_bounds(page, cap, body, above)
            r, frac = ink_region(image_path, page, y0, y1, body, cap)
            if r is not None and frac > best[1]:
                best = (r, frac, "above" if above else "below")
        region, _, side = best
        scan_note = "scan mode (pixel ink in OCR band); "
    if region is None:
        doc.close()
        return None, "no graphic content next to the caption"
    if region.width < 120 or region.height < 60 or region.get_area() < 0.05 * pr.get_area():
        doc.close()
        return None, f"region too small ({region.width:.0f}x{region.height:.0f} pt, {side})"
    # a region that is mostly running text is a mis-anchored band (wrong caption / rotated page)
    text_area = sum((pymupdf.Rect(b["bbox"]) & region).get_area() for b in tb if b is not cap)
    body_area = sum((pymupdf.Rect(b["bbox"]) & region).get_area() for b in body)
    doc.close()
    if body_area > 0.35 * region.get_area():
        return None, f"region mostly body text ({body_area / region.get_area():.0%}, {side})"
    if region.get_area() > 0.65 * pr.get_area():
        return "full_page", f"figure fills the page ({region.get_area() / pr.get_area():.0%}); keep uncropped"
    s = img_w / pr.width
    box = [int(region.x0 * s), int(region.y0 * s), int(region.x1 * s), int(region.y1 * s)]
    return box, f"{scan_note}caption-anchored band, figure {side} caption; text share {text_area / region.get_area():.0%}"


def preview(rows: list[dict], font) -> None:
    SHEETS.mkdir(parents=True, exist_ok=True)
    cell_w, cell_h, per = 500, 420, 8
    for k in range(0, len(rows), per):
        chunk = rows[k:k + per]
        sheet = Image.new("RGB", (4 * cell_w, 2 * cell_h), "white")
        d = ImageDraw.Draw(sheet)
        for i, r in enumerate(chunk):
            x, y = (i % 4) * cell_w, (i // 4) * cell_h
            try:
                im = Image.open(ROOT / r["image_path"]).convert("RGB")
            except Exception:
                continue
            b = r["box_px"]
            pg = im.copy()
            ImageDraw.Draw(pg).rectangle(b, outline="red", width=12)
            pg.thumbnail((cell_w // 2 - 8, cell_h - 40))
            sheet.paste(pg, (x + 4, y + 30))
            cr = im.crop(b)
            cr.thumbnail((cell_w // 2 - 8, cell_h - 40))
            sheet.paste(cr, (x + cell_w // 2 + 4, y + 30))
            d.rectangle([x, y, x + 60, y + 26], fill="red")
            d.text((x + 5, y + 2), str(r["idx"]), fill="white", font=font)
            d.text((x + 66, y + 4), r["record_id"][:48], fill="black", font=font)
            d.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], outline="#cccccc")
        sheet.save(SHEETS / f"crops_{k // per:03d}.jpg", "JPEG", quality=85)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="openalex_nonpmc,epa_manuals")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--reject", default="", help="text file with one record_id (or preview idx) per line to move to the manual queue after visual review")
    ap.add_argument("--only", default="", help="CSV with a record_id column: process only these rows (e.g. the manual queue of a previous run)")
    ap.add_argument("--tag", default="", help="suffix for the output files (crops_auto<tag>.json etc.)")
    a = ap.parse_args()
    rejects: set[str] = set()
    if a.reject and Path(a.reject).exists():
        rejects = {l.strip() for l in Path(a.reject).read_text(encoding="utf-8").splitlines() if l.strip()}
    df = pd.read_csv(DATA / "triage_final.csv", dtype=str, encoding="utf-8-sig").fillna("")
    if a.only:
        ids = pd.read_csv(a.only, dtype=str, encoding="utf-8-sig")["record_id"].tolist()
        sel = df[df["record_id"].isin(ids)]
    else:
        sel = df[(df["split"] == "main") & df["source"].isin(a.sources.split(",")) & df["image_size"].map(page_like)
                 & (~df["record_id"].str.contains("#crop"))]
    if a.limit:
        sel = sel.head(a.limit)
    global SHEETS
    SHEETS = REVIEW / f"sheets_crops{a.tag}"
    REVIEW.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    boxes, report, manual, ok_rows = {}, [], [], []
    for idx, (_, r) in enumerate(sel.iterrows(), 1):
        extra = json.loads(r["extra_json"] or "{}")
        doc = Path(r["image_path"]).parent.name
        pdf = RAW / r["source"] / "_pdf" / f"{doc}.pdf"
        img_w = int(re.findall(r"\d+", r["image_size"])[0])
        status, box, reason = "manual", None, ""
        if not pdf.exists():
            reason = "source PDF missing"
        elif not extra.get("page"):
            reason = "page number missing"
        else:
            try:
                box, reason = crop_for(pdf, int(extra["page"]), r["caption"], img_w, ROOT / r["image_path"])
            except Exception as e:  # noqa: BLE001
                box, reason = None, f"error: {e}"
        if box and (r["record_id"] in rejects or str(idx) in rejects):
            box, reason = None, "rejected in visual review"
        if box == "full_page":
            status, box = "full_page", None
        elif box:
            status = "auto"
            boxes[r["record_id"]] = [box]
            ok_rows.append({"idx": idx, "record_id": r["record_id"], "image_path": r["image_path"], "box_px": box})
        else:
            manual.append({"record_id": r["record_id"], "source": r["source"], "image_path": r["image_path"], "reason": reason})
        report.append({"idx": idx, "record_id": r["record_id"], "source": r["source"], "page": extra.get("page", ""),
                       "status": status, "box_px": json.dumps(box) if box else "", "reason": reason})
    (REVIEW / f"crops_auto{a.tag}.json").write_text(json.dumps(boxes, indent=1), encoding="utf-8")
    pd.DataFrame(report).to_csv(REVIEW / f"crops_auto{a.tag}_report.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(manual).to_csv(REVIEW / f"crops_auto{a.tag}_manual.csv", index=False, encoding="utf-8-sig")
    preview(ok_rows, font)
    n = len(report)
    print(f"{n} page renders: auto {len(boxes)}, manual {len(manual)}")
    print(pd.DataFrame(report).groupby(["source", "status"]).size())
    if manual:
        print(pd.DataFrame(manual)["reason"].str.slice(0, 40).value_counts().head(8))


if __name__ == "__main__":
    main()
