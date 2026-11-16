"""
s02_wikimedia_commons.py — Source 2: Wikimedia Commons (free-licensed diagrams)

Pipeline
  1. MediaWiki API full-text search in the File namespace (ns=6) with several English/Korean/German/French
     queries + members of relevant categories (and their sub-categories, depth 1).
  2. For each file, `prop=imageinfo` gives the original URL, MIME, size, licence (extmetadata:
     LicenseShortName, LicenseUrl, Artist, Credit, Attribution).
  3. Keep raster images and SVG; skip PDF/DjVu scans (those are handled by s03-style page extraction later).
  4. Keep files whose title/description matches the diagram regex; download; write provenance.
  Attribution requirements (CC BY / CC BY-SA) are satisfied by keeping Artist + LicenseUrl in the record.

Usage: python s02_wikimedia_commons.py --contact "<project URL or e-mail>"

NOTE (2026-11-16 run): upload.wikimedia.org answered HTTP 429 with Retry-After 600 s to our generic User-Agent.
Wikimedia's User-Agent policy (https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy)
requires a contact (URL or e-mail) in the UA string for automated clients. Pass it with --contact; the script
refuses to run the download stage without one and sleeps >= 1 s between file downloads.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from common import (RAW, PROV, make_session, download, provenance_record, append_jsonl,
                    already_done, licence_tier, get_logger, safe_name)

SOURCE = "wikimedia_commons"
OUT = RAW / SOURCE
OUT.mkdir(parents=True, exist_ok=True)
PROV_FILE = PROV / f"{SOURCE}.jsonl"
log = get_logger(SOURCE)
API = "https://commons.wikimedia.org/w/api.php"

SEARCHES = [
    "wastewater treatment plant diagram", "wastewater treatment schematic", "sewage treatment process flow",
    "sewage treatment plant flow diagram", "activated sludge process diagram", "wastewater treatment flowchart",
    "water treatment plant process diagram", "sludge treatment diagram", "anaerobic digestion wastewater diagram",
    "membrane bioreactor diagram", "sequencing batch reactor diagram", "trickling filter diagram",
    "Kläranlage Schema", "Kläranlage Fließschema", "station d'épuration schéma", "depuradora esquema",
    "하수처리 공정도", "下水処理 フロー", "污水处理 工艺流程",
]
CATEGORIES = [
    "Category:Sewage treatment", "Category:Sewage treatment plants", "Category:Process flow diagrams",
    "Category:Wastewater treatment", "Category:Activated sludge", "Category:Water treatment",
    "Category:Diagrams of sewage treatment", "Category:Sewage treatment diagrams",
]
TITLE_RX = re.compile(r"(diagram|schem|flow|process|plant|anlage|station|treatment|sludge|공정|処理|流程|kläranlage|épuration|depuradora)", re.I)
IMAGE_MIME = ("image/png", "image/jpeg", "image/svg+xml", "image/gif", "image/tiff", "image/webp")


def api(session, **params):
    params.update({"format": "json"})
    for _ in range(3):
        r = session.get(API, params=params, timeout=60)
        if r.status_code == 200:
            return r.json()
        time.sleep(2)
    return {}


def search_titles(session) -> dict[str, str]:
    """title -> how it was found"""
    found: dict[str, str] = {}
    for q in SEARCHES:
        offset = 0
        while True:
            d = api(session, action="query", list="search", srsearch=q, srnamespace=6, srlimit=50, sroffset=offset)
            hits = d.get("query", {}).get("search", [])
            for h in hits:
                found.setdefault(h["title"], f"search:{q}")
            if "continue" in d and offset < 400:
                offset = d["continue"]["sroffset"]
            else:
                break
        log.info("search %r -> cumulative %d titles", q, len(found))
    for cat in CATEGORIES:
        subcats = [cat]
        d = api(session, action="query", list="categorymembers", cmtitle=cat, cmtype="subcat", cmlimit=200)
        subcats += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        for sc in subcats:
            cont = None
            while True:
                p = dict(action="query", list="categorymembers", cmtitle=sc, cmtype="file", cmlimit=500)
                if cont:
                    p["cmcontinue"] = cont
                d = api(session, **p)
                for m in d.get("query", {}).get("categorymembers", []):
                    found.setdefault(m["title"], f"category:{sc}")
                cont = d.get("continue", {}).get("cmcontinue")
                if not cont:
                    break
        log.info("category %r (+%d subcats) -> cumulative %d titles", cat, len(subcats) - 1, len(found))
    return found


def imageinfo(session, titles: list[str]) -> dict[str, dict]:
    out = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        d = api(session, action="query", titles="|".join(chunk), prop="imageinfo",
                iiprop="url|size|mime|extmetadata|sha1", iiextmetadatalanguage="en")
        for pg in d.get("query", {}).get("pages", {}).values():
            if "imageinfo" in pg:
                out[pg["title"]] = pg["imageinfo"][0]
    return out


def strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--contact", required=True, help="contact URL or e-mail for the User-Agent (Wikimedia policy)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between file downloads")
    args = ap.parse_args()
    session = make_session()
    session.headers["User-Agent"] = f"WWTP-PFD-collector/0.1 ({args.contact}) python-requests"
    done = already_done(PROV_FILE)
    found = search_titles(session)
    titles = [t for t in found if TITLE_RX.search(t)]
    log.info("%d candidate files after title filter (from %d found)", len(titles), len(found))
    infos = imageinfo(session, titles)
    n = 0
    for title, ii in infos.items():
        if ii.get("mime") not in IMAGE_MIME:
            continue
        if ii.get("width", 0) < 300:
            continue
        em = ii.get("extmetadata", {})
        lic = strip_html(em.get("LicenseShortName", {}).get("value", "")) or None
        lic_url = strip_html(em.get("LicenseUrl", {}).get("value", "")) or None
        artist = strip_html(em.get("Artist", {}).get("value", "")) or None
        desc = strip_html(em.get("ImageDescription", {}).get("value", ""))
        fname = safe_name(title.replace("File:", ""))
        dest = OUT / fname
        rid = f"{SOURCE}:{title}:{dest.name}"
        if rid in done:
            continue
        time.sleep(args.delay)
        if not download(session, ii["url"], dest, min_bytes=500):
            log.warning("download failed %s", title)
            continue
        rec = provenance_record(
            source=SOURCE, tier=licence_tier(lic), image_path=dest,
            acquisition_method="MediaWiki API (search/categorymembers -> imageinfo) -> original file URL",
            file_url=ii["url"], landing_url=ii.get("descriptionurl"),
            license=lic, license_url=lic_url, rights_holder=artist,
            doc_id=title, title=title.replace("File:", ""), venue="Wikimedia Commons", year=None,
            figure_label=None, caption=desc[:1000] or None, query=found[title], filter_rule="title_regex",
            extra={"mime": ii.get("mime"), "width": ii.get("width"), "height": ii.get("height"),
                   "commons_sha1": ii.get("sha1")},
        )
        rec["record_id"] = rid
        append_jsonl(PROV_FILE, rec)
        n += 1
    log.info("DONE downloaded %d files", n)


if __name__ == "__main__":
    main()
