"""
pdf_figures.py — shared helper: extract candidate diagram figures from a PDF (used by s03, s05).

Strategy (PyMuPDF):
  * For every page, read the text and look for figure captions ("Figure 3-2. Process flow diagram ...").
    A caption line is any line starting with Fig/Figure/FIGURE/그림/図 followed by a number.
  * If a caption on the page passes common.caption_tier(), the page is a hit.
  * On a hit page we save BOTH
      - every embedded raster image on that page larger than MIN_PX (born-digital PDFs), and
      - a 200-dpi render of the full page (scanned/vector PDFs where the figure is not an image object).
    The page render is always kept because flow diagrams in EPA manuals are frequently vector drawings.
  Returns a list of dicts: {path, page, caption, tier, kind}  (kind = 'embedded' | 'page_render')
"""
from __future__ import annotations

import re
from pathlib import Path

import pymupdf

from common import caption_tier

CAP_RX = re.compile(r"^\s*(fig(?:ure)?\.?|그림|図|figura)\s*([0-9]+[-.0-9A-Za-z]*)\s*[.:\-–—]?\s*(.+)$", re.I)
MIN_PX = 350


def page_captions(page) -> list[tuple[str, str]]:
    """(label, caption_text) for caption-looking lines on the page, joining the next line if short."""
    lines = [l.strip() for l in page.get_text("text").splitlines()]
    caps = []
    for i, l in enumerate(lines):
        m = CAP_RX.match(l)
        if not m:
            continue
        text = m.group(3)
        # captions often wrap: append the following line(s) if they do not start a new caption
        j = i + 1
        while j < len(lines) and j < i + 3 and lines[j] and not CAP_RX.match(lines[j]):
            text += " " + lines[j]
            j += 1
        caps.append((f"{m.group(1)} {m.group(2)}", text[:600]))
    return caps


def extract(pdf_path: Path, out_dir: Path, doc_tag: str, max_pages: int | None = None,
            render_dpi: int = 200) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    try:
        doc = pymupdf.open(pdf_path)
    except Exception:
        return results
    for pno in range(len(doc) if max_pages is None else min(len(doc), max_pages)):
        page = doc[pno]
        hits = [(lab, cap, caption_tier(cap)) for lab, cap in page_captions(page)]
        hits = [h for h in hits if h[2]]
        if not hits:
            continue
        lab, cap, tier = hits[0]
        # 1) embedded images
        n_emb = 0
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                pix = pymupdf.Pixmap(doc, xref)
                if pix.width < MIN_PX or pix.height < MIN_PX:
                    continue
                if pix.n - pix.alpha >= 4:  # CMYK -> RGB
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                p = out_dir / f"{doc_tag}_p{pno + 1:04d}_img{xref}.png"
                pix.save(p)
                results.append({"path": p, "page": pno + 1, "caption": cap, "label": lab, "tier": tier, "kind": "embedded"})
                n_emb += 1
            except Exception:
                continue
        # 2) full-page render (always; vector drawings are not image objects)
        try:
            pix = page.get_pixmap(dpi=render_dpi)
            p = out_dir / f"{doc_tag}_p{pno + 1:04d}_page.png"
            pix.save(p)
            results.append({"path": p, "page": pno + 1, "caption": cap, "label": lab, "tier": tier, "kind": "page_render"})
        except Exception:
            pass
    doc.close()
    return results
