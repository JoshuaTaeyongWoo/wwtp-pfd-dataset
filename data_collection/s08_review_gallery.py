"""
s08_review_gallery.py — build HTML contact sheets for manual triage of the collected candidates.

Automatic caption/keyword filters only produce *candidates*. Before annotation a human must decide, per
image, whether it is a usable process diagram. This script renders one HTML page per source (and one
for the canonical catalog) with thumbnails, caption, licence tier, and a checkbox state that is saved to
localStorage and can be exported as CSV (keep / reject / unsure) from the page.

Outputs: data/review/<source>.html, data/review/index.html

Usage: python s08_review_gallery.py [--thumb 320]
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path

import pandas as pd
from PIL import Image

from common import DATA, ROOT

REVIEW = DATA / "review"
THUMBS = REVIEW / "thumbs"


def thumb(src: Path, size: int) -> Path | None:
    dst = THUMBS / (src.parent.name + "__" + src.stem + ".jpg")
    if dst.exists():
        return dst
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((size, size))
            dst.parent.mkdir(parents=True, exist_ok=True)
            im.save(dst, "JPEG", quality=80)
        return dst
    except Exception:
        return None


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<style>
body{{font-family:sans-serif;margin:16px;background:#fafafa}} .card{{display:inline-block;width:{w}px;vertical-align:top;margin:6px;padding:6px;border:1px solid #ddd;background:#fff;border-radius:6px}}
.card img{{max-width:{w}px;max-height:{w}px;display:block;margin:auto}} .cap{{font-size:11px;color:#333;height:70px;overflow:auto;margin-top:4px}}
.meta{{font-size:10px;color:#777}} .A{{border-left:5px solid #2a9d8f}} .B{{border-left:5px solid #e76f51}}
.btns button{{font-size:11px;margin-right:3px}} .keep{{background:#c8f7c5}} .reject{{background:#f7c5c5}} .unsure{{background:#f7f0c5}}
#bar{{position:sticky;top:0;background:#fff;padding:8px;border-bottom:1px solid #ccc;z-index:9}}
</style></head><body>
<div id="bar"><b>{title}</b> — {n} images. Tier A = redistributable licence, B = research-only.
<button onclick="exportCsv()">Export decisions CSV</button> <span id="cnt"></span></div>
{cards}
<script>
const key='review_{slug}';let st=JSON.parse(localStorage.getItem(key)||'{{}}');
function mark(id,v){{st[id]=v;localStorage.setItem(key,JSON.stringify(st));paint();}}
function paint(){{let k=0,r=0,u=0;document.querySelectorAll('.card').forEach(c=>{{const v=st[c.dataset.id];c.classList.remove('keep','reject','unsure');if(v){{c.classList.add(v);if(v=='keep')k++;else if(v=='reject')r++;else u++;}}}});document.getElementById('cnt').textContent=` keep ${{k}} / reject ${{r}} / unsure ${{u}}`;}}
function exportCsv(){{let s='record_id,decision\\n';for(const [i,v] of Object.entries(st))s+=`"${{i}}",${{v}}\\n`;const a=document.createElement('a');a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(s);a.download='decisions_{slug}.csv';a.click();}}
paint();
</script></body></html>"""

CARD = """<div class="card {tier}" data-id="{rid}"><a href="{full}" target="_blank"><img src="{thumb}" loading="lazy"></a>
<div class="cap"><b>{label}</b> {caption}</div><div class="meta">{source} · {tier} · {ctier} · {venue} {year}<br>{doc}</div>
<div class="btns"><button onclick="mark('{rid}','keep')">keep</button><button onclick="mark('{rid}','reject')">reject</button><button onclick="mark('{rid}','unsure')">unsure</button></div></div>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thumb", type=int, default=320)
    args = ap.parse_args()
    cat = DATA / "catalog_canonical.csv"
    if not cat.exists():
        raise SystemExit("run s07_dedup_catalog.py first")
    df = pd.read_csv(cat, dtype=str).fillna("")
    REVIEW.mkdir(parents=True, exist_ok=True)
    index = ["<h2>Review galleries</h2><ul>"]
    for source, g in list(df.groupby("source")) + [("ALL_canonical", df)]:
        cards = []
        for _, r in g.iterrows():
            src = ROOT / r["image_path"]
            t = thumb(src, args.thumb)
            if t is None:
                continue
            cards.append(CARD.format(
                tier=r["tier"], rid=html.escape(r["record_id"]), full=html.escape(src.resolve().as_uri()),
                thumb=html.escape(t.resolve().as_uri()), label=html.escape(r["figure_label"]),
                caption=html.escape(r["caption"][:400]), source=r["source"], ctier=r["caption_tier"],
                venue=html.escape(r["venue"][:40]), year=r["year"][:4], doc=html.escape(r["doc_id"][:60])))
        out = REVIEW / f"{source}.html"
        out.write_text(PAGE.format(title=source, w=args.thumb, n=len(cards), cards="\n".join(cards), slug=source),
                       encoding="utf-8")
        index.append(f'<li><a href="{out.name}">{source}</a> ({len(cards)})</li>')
        print(source, len(cards))
    index.append("</ul>")
    (REVIEW / "index.html").write_text("\n".join(index), encoding="utf-8")


if __name__ == "__main__":
    main()
