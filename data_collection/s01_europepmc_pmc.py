"""
s01_europepmc_pmc.py — Source 1: open-access journal articles (PubMed Central Open Access Subset)

Pipeline
  1. Europe PMC REST search (full-text query, OPEN_ACCESS:y, HAS_FT:y) -> candidate article list
     with DOI, title, journal, year, licence.  (https://www.ebi.ac.uk/europepmc/webservices/rest/)
  2. For each PMCID, fetch the article package from the official PMC Open Access bucket on AWS
     (s3://pmc-oa-opendata, world-readable, no login; the PMC OA Web Service / FTP were retired in 2026):
        <PMCID>.<ver>/<PMCID>.<ver>.json  licence + metadata
        <PMCID>.<ver>/<PMCID>.<ver>.xml   JATS full text with <fig> captions and <graphic xlink:href>
        <PMCID>.<ver>/<figure files>      jpg/png/tif
  3. Parse every <fig>; keep figures whose caption matches the diagram/plant regexes in common.py
     (tier T1 = whole-plant diagram, T2 = treatment-related schematic) and download only those.
  4. Write one provenance record per downloaded figure (data/provenance/europepmc_pmc.jsonl).

Usage
  python s01_europepmc_pmc.py                 # full run (resumable)
  python s01_europepmc_pmc.py --max 50        # smoke test
  python s01_europepmc_pmc.py --query broad   # restrict to the narrower 'broad diagram' query
"""
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from common import (RAW, PROV, make_session, download, provenance_record, append_jsonl,
                    read_jsonl, caption_tier, licence_tier, get_logger, safe_name)

SOURCE = "europepmc_pmc"
OUT = RAW / SOURCE
OUT.mkdir(parents=True, exist_ok=True)
PROV_FILE = PROV / f"{SOURCE}.jsonl"
DONE_FILE = OUT / "_processed_pmcids.txt"
log = get_logger(SOURCE)

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
S3 = "https://pmc-oa-opendata.s3.amazonaws.com/"

PLANT_TERMS = ('BODY:"wastewater treatment plant" OR BODY:"sewage treatment plant" OR '
               'BODY:"water resource recovery facility" OR BODY:"wastewater treatment works" OR '
               'BODY:"sewage treatment works" OR BODY:"wastewater treatment facility"')
QUERIES = {
    # every OA full-text article that mentions a treatment plant (caption filter does the rest)
    "all": f"({PLANT_TERMS}) AND OPEN_ACCESS:y AND HAS_FT:y",
    # narrower: the article body also mentions a flow diagram / schematic
    "broad": (f"({PLANT_TERMS}) AND (BODY:\"process flow diagram\" OR BODY:\"flow sheet\" OR BODY:\"flowsheet\" "
              f"OR BODY:\"process flow\" OR BODY:\"schematic diagram\" OR BODY:\"schematic of the\" "
              f"OR BODY:\"treatment train\" OR BODY:\"plant layout\") AND OPEN_ACCESS:y AND HAS_FT:y"),
}

XLINK = "{http://www.w3.org/1999/xlink}href"


# ----------------------------------------------------------------------------- step 1
def search_candidates(session, query: str, max_n: int | None, qname: str) -> list[dict]:
    """Page through Europe PMC with cursorMark; cache to a per-query candidate file."""
    CAND_FILE = OUT / f"_candidates_{qname}.jsonl"
    if CAND_FILE.exists():
        cands = read_jsonl(CAND_FILE)
        log.info("loaded %d cached candidates from %s", len(cands), CAND_FILE)
        return cands[:max_n] if max_n else cands
    cands, cursor = [], "*"
    while True:
        r = session.get(EPMC, params={"query": query, "format": "json", "resultType": "core",
                                      "pageSize": 1000, "cursorMark": cursor}, timeout=120)
        r.raise_for_status()
        d = r.json()
        for x in d["resultList"]["result"]:
            if not x.get("pmcid"):
                continue
            cands.append({
                "pmcid": x["pmcid"], "pmid": x.get("pmid"), "doi": x.get("doi"),
                "title": x.get("title"), "year": x.get("pubYear"),
                "journal": ((x.get("journalInfo") or {}).get("journal") or {}).get("title"),
                "license": x.get("license"), "authors": x.get("authorString"),
                "query": query,
            })
            append_jsonl(CAND_FILE, cands[-1])
        nxt = d.get("nextCursorMark")
        log.info("search page done: total so far %d / hitCount %s", len(cands), d.get("hitCount"))
        if not nxt or nxt == cursor or (max_n and len(cands) >= max_n):
            break
        cursor = nxt
    return cands[:max_n] if max_n else cands


# ----------------------------------------------------------------------------- step 2/3
def s3_list(session, pmcid: str) -> list[tuple[str, int]]:
    r = session.get(S3, params={"list-type": "2", "prefix": f"{pmcid}.", "max-keys": "500"}, timeout=60)
    if r.status_code != 200:
        return []
    keys = re.findall(r"<Key>(.*?)</Key>", r.text)
    sizes = re.findall(r"<Size>(.*?)</Size>", r.text)
    return list(zip(keys, map(int, sizes)))


def parse_figs(xml_path: Path) -> list[dict]:
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError:
        return []
    figs = []
    for fig in root.iter("fig"):
        label = fig.findtext("label") or ""
        cap_el = fig.find("caption")
        caption = " ".join(" ".join(cap_el.itertext()).split()) if cap_el is not None else ""
        hrefs = [el.get(XLINK) for el in fig.iter() if el.get(XLINK)]
        figs.append({"label": label.strip(), "caption": caption, "hrefs": hrefs})
    return figs


def process_article(session, cand: dict) -> tuple[str, int, int]:
    """Returns (pmcid, n_figs_total, n_downloaded)."""
    pmcid = cand["pmcid"]
    objs = s3_list(session, pmcid)
    if not objs:
        return pmcid, 0, 0
    # choose highest version prefix
    vers = sorted({k.split("/")[0] for k, _ in objs}, key=lambda v: int(v.split(".")[1]))
    pref = vers[-1]
    adir = OUT / pmcid
    adir.mkdir(exist_ok=True)
    meta_key, xml_key = f"{pref}/{pref}.json", f"{pref}/{pref}.xml"
    ok_meta = download(session, S3 + meta_key, adir / "meta.json", min_bytes=10)
    ok_xml = download(session, S3 + xml_key, adir / "article.xml", min_bytes=200)
    if not ok_xml:
        return pmcid, 0, 0
    meta = {}
    if ok_meta:
        try:
            meta = json.loads((adir / "meta.json").read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    lic = (meta.get("license") or meta.get("License") or cand.get("license") or "")
    if isinstance(lic, dict):
        lic = lic.get("type") or lic.get("name") or json.dumps(lic)
    figs = parse_figs(adir / "article.xml")
    keymap = {k.split("/")[-1]: (k, s) for k, s in objs}
    n_dl = 0
    for fg in figs:
        tier = caption_tier(fg["caption"])
        if not tier:
            continue
        for href in fg["hrefs"]:
            base = href.split("/")[-1]
            # S3 key may carry an extension the href lacks
            match = [kv for name, kv in keymap.items() if name == base or name.rsplit(".", 1)[0] == base.rsplit(".", 1)[0]]
            for key, size in match:
                fname = key.split("/")[-1]
                dest = adir / fname
                if not download(session, S3 + key, dest, min_bytes=500):
                    continue
                rec = provenance_record(
                    source=SOURCE, tier=licence_tier(lic), image_path=dest,
                    acquisition_method="Europe PMC REST search -> PMC OA S3 bucket (pmc-oa-opendata) object GET",
                    file_url=S3 + key,
                    landing_url=f"https://europepmc.org/article/PMC/{pmcid}",
                    license=lic or None, license_url=None,
                    rights_holder=cand.get("authors"),
                    doc_id=pmcid, title=cand.get("title"), venue=cand.get("journal"), year=cand.get("year"),
                    figure_label=fg["label"], caption=fg["caption"], query=cand.get("query"),
                    filter_rule=f"caption_tier={tier}",
                    extra={"doi": cand.get("doi"), "pmid": cand.get("pmid"), "s3_version": pref,
                           "caption_tier": tier, "file_bytes": size},
                )
                append_jsonl(PROV_FILE, rec)
                n_dl += 1
    # remove the bulky xml/meta only if nothing matched (keeps disk small; caption decisions are logged)
    if n_dl == 0:
        for f in (adir / "article.xml", adir / "meta.json"):
            f.unlink(missing_ok=True)
        try:
            adir.rmdir()
        except OSError:
            pass
    return pmcid, len(figs), n_dl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", choices=list(QUERIES), default="all")
    ap.add_argument("--max", type=int, default=None, help="max candidate articles (smoke test)")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    session = make_session()
    cands = search_candidates(session, QUERIES[args.query], args.max, args.query)
    done = set(DONE_FILE.read_text().split()) if DONE_FILE.exists() else set()
    todo = [c for c in cands if c["pmcid"] not in done]
    log.info("candidates %d, already processed %d, to do %d", len(cands), len(done), len(todo))

    n_art = n_figs = n_dl = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex, open(DONE_FILE, "a") as donef:
        futs = {ex.submit(process_article, make_session(), c): c for c in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                pmcid, nf, nd = fut.result()
            except Exception as e:  # keep going; log the failure
                log.warning("article failed %s: %s", futs[fut]["pmcid"], e)
                continue
            n_art += 1; n_figs += nf; n_dl += nd
            donef.write(pmcid + "\n"); donef.flush()
            if i % 100 == 0 or nd:
                log.info("[%d/%d] %s figs=%d downloaded=%d | cumulative articles=%d figs_seen=%d downloaded=%d",
                         i, len(todo), pmcid, nf, nd, n_art, n_figs, n_dl)
    log.info("DONE articles=%d figures_seen=%d figures_downloaded=%d", n_art, n_figs, n_dl)


if __name__ == "__main__":
    main()
