"""
s04_patents.py — Source 4: patent drawings (Google Patents)

Pipeline
  1. Google Patents query endpoint (https://patents.google.com/xhr/query?url=<encoded query>) —
     the same JSON the public search page uses; filtered by CPC C02F3 (biological water treatment) /
     C02F1 / C02F9 / C02F11 (sludge) and English full-text terms "wastewater treatment plant" + "flow diagram".
  2. Each result's public patent page (https://patents.google.com/patent/<pubno>/en) lists the full-size
     drawing images in <meta itemprop="full" content="...">  (patentimages.storage.googleapis.com).
  3. Download drawings; record publication number, title, assignee, filing/publication date, CPC codes.
  Patent drawings are published government documents; in the US they are not subject to copyright
  restriction for reproduction (USPTO terms of use) -> tier A, with a note that non-US patents may differ.

  The request rate is deliberately slow (1 request / 2 s) and the run is capped (--max-patents).

Usage: python s04_patents.py --max-patents 300
"""
from __future__ import annotations

import argparse
import re
import time
import urllib.parse
from pathlib import Path

from common import (RAW, PROV, make_session, download, provenance_record, append_jsonl,
                    already_done, get_logger, safe_name, RateLimiter)

SOURCE = "patents_google"
OUT = RAW / SOURCE
OUT.mkdir(parents=True, exist_ok=True)
PROV_FILE = PROV / f"{SOURCE}.jsonl"
log = get_logger(SOURCE)

QUERIES = [
    # (label, query string as typed in Google Patents search box)
    ("C02F3 wwtp flow diagram", '("wastewater treatment plant" OR "sewage treatment plant") "flow diagram"', "C02F3"),
    ("C02F11 sludge flow diagram", '("wastewater treatment" OR "sewage treatment") sludge "flow diagram"', "C02F11"),
    ("C02F9 wwtp process flow", '("wastewater treatment plant" OR "sewage treatment plant") "process flow"', "C02F9"),
    ("C02F3 activated sludge schematic", '"activated sludge" ("treatment plant" OR "sewage plant") schematic', "C02F3"),
]


def gp_query(session, q: str, cpc: str, page: int) -> dict:
    inner = urllib.parse.urlencode({"q": q, "cpc": cpc, "language": "ENGLISH", "num": 100, "page": page})
    url = "https://patents.google.com/xhr/query?url=" + urllib.parse.quote(inner, safe="") + "&exp="
    r = session.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def drawings_from_page(session, pubno: str) -> tuple[list[str], dict]:
    url = f"https://patents.google.com/patent/{pubno}/en"
    r = session.get(url, timeout=60)
    if r.status_code != 200:
        return [], {}
    html = r.text
    imgs = re.findall(r'<meta itemprop="full" content="([^"]+)"', html)
    meta = {
        "title": (re.search(r'<meta name="DC.title" content="([^"]*)"', html) or [None, None])[1],
        "assignee": (re.search(r'<dd itemprop="assigneeOriginal">([^<]*)</dd>', html) or [None, None])[1],
        "pub_date": (re.search(r'<meta name="DC.date" content="([^"]*)"', html) or [None, None])[1],
        "cpc": sorted(set(re.findall(r'<span itemprop="Code">([A-H][0-9]{2}[A-Z][0-9/ ]+)</span>', html)))[:12],
    }
    return imgs, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-patents", type=int, default=300)
    ap.add_argument("--max-drawings-per-patent", type=int, default=6)
    args = ap.parse_args()
    session = make_session()
    session.headers["Accept"] = "application/json, text/html"
    done = already_done(PROV_FILE)
    rl = RateLimiter(2.0)

    seen: dict[str, str] = {}
    for label, q, cpc in QUERIES:
        for page in range(0, 10):
            rl.wait()
            try:
                d = gp_query(session, q, cpc, page)
            except Exception as e:
                log.warning("query failed %s p%d: %s", label, page, e)
                break
            res = d.get("results", {})
            clusters = res.get("cluster", [])
            items = [x["patent"] for c in clusters for x in c.get("result", [])]
            if page == 0:
                log.info("%s: total_num_results=%s", label, res.get("total_num_results"))
            for p in items:
                seen.setdefault(p["publication_number"], f"{label} | {q} | cpc={cpc}")
            if not items or len(seen) >= args.max_patents:
                break
        if len(seen) >= args.max_patents:
            break
    log.info("%d unique publications collected from queries", len(seen))

    n_pat = n_img = 0
    for pubno, how in list(seen.items())[: args.max_patents]:
        rl.wait()
        imgs, meta = drawings_from_page(session, pubno)
        if not imgs:
            continue
        n_pat += 1
        for k, u in enumerate(imgs[: args.max_drawings_per_patent]):
            dest = OUT / safe_name(pubno) / f"{safe_name(pubno)}_D{k:02d}.png"
            rid = f"{SOURCE}:{pubno}:{dest.name}"
            if rid in done:
                continue
            rl.wait()
            if not download(session, u, dest, min_bytes=2000):
                continue
            rec = provenance_record(
                source=SOURCE, tier="A", image_path=dest,
                acquisition_method="Google Patents xhr/query JSON -> patent page <meta itemprop=full> drawing URLs -> GET",
                file_url=u, landing_url=f"https://patents.google.com/patent/{pubno}/en",
                license="Patent drawing (published patent document; US: no copyright restriction on reproduction)",
                license_url="https://www.uspto.gov/terms-use-uspto-websites",
                rights_holder=meta.get("assignee"),
                doc_id=pubno, title=meta.get("title"), venue="Google Patents",
                year=(meta.get("pub_date") or "")[:4] or None,
                figure_label=f"drawing sheet {k}", caption=None, query=how,
                filter_rule="all drawing sheets (no caption available); manual triage needed",
                extra={"cpc": meta.get("cpc"), "pub_date": meta.get("pub_date")},
            )
            rec["record_id"] = rid
            append_jsonl(PROV_FILE, rec)
            n_img += 1
        if n_pat % 20 == 0:
            log.info("patents with drawings %d, images %d", n_pat, n_img)
    log.info("DONE patents=%d drawings=%d", n_pat, n_img)


if __name__ == "__main__":
    main()
