"""
s05_openalex_nonpmc.py — Source 5: open-access articles that are NOT in PubMed Central (OpenAlex -> publisher/repository PDF)

Why: PMC covers mostly biomedical-adjacent journals. Civil/environmental-engineering OA venues (e.g. Water
Research X, Journal of Water Process Engineering OA articles, IWA Water Science & Technology OA, Springer
Applied Water Science, repository copies) are reached through OpenAlex's best_oa_location.pdf_url.

Pipeline
  1. OpenAlex /works search ("wastewater treatment plant" + diagram terms), filter is_oa:true and no PMCID,
     select OA pdf_url + licence.  (https://api.openalex.org, polite pool, no key)
  2. Download the PDF from the OA location *only when the server returns a real PDF to our honest
     User-Agent* (publishers that block automated access, e.g. MDPI/Elsevier HTML challenge pages, are skipped
     and logged — no header spoofing).
  3. pdf_figures.extract() -> caption-matched embedded images + page renders -> provenance.
  Licence: taken from OpenAlex (cc-by, cc-by-nc, ...); tier B when unknown.

Usage: python s05_openalex_nonpmc.py --max 400
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from common import (RAW, PROV, make_session, download, provenance_record, append_jsonl, already_done,
                    licence_tier, get_logger, safe_name, RateLimiter)
import pdf_figures

SOURCE = "openalex_nonpmc"
OUT = RAW / SOURCE
PDFS = OUT / "_pdf"
FIGS = OUT / "figures"
PROV_FILE = PROV / f"{SOURCE}.jsonl"
log = get_logger(SOURCE)
OA = "https://api.openalex.org/works"

SEARCHES = [
    '"wastewater treatment plant" "process flow diagram"',
    '"wastewater treatment plant" flowsheet',
    '"wastewater treatment plant" "schematic diagram" "full-scale"',
    '"sewage treatment plant" "flow diagram"',
    '"wastewater treatment plant" "treatment train" configuration',
    '"water resource recovery facility" "process flow"',
]


CAND_FILE = OUT / "_candidates.jsonl"


def openalex_candidates(session, max_n: int) -> list[dict]:
    """Query OpenAlex once and cache the candidate list (the API is intermittently unavailable)."""
    from common import read_jsonl, append_jsonl as _append
    if CAND_FILE.exists():
        cands = read_jsonl(CAND_FILE)
        log.info("loaded %d cached candidates from %s", len(cands), CAND_FILE)
        return cands[:max_n]
    seen, out = set(), []
    for q in SEARCHES:
        cursor = "*"
        while cursor and len(out) < max_n:
            try:
                r = session.get(OA, params={
                    "search": q, "filter": "is_oa:true,ids.pmcid:null,has_fulltext:true|false",
                    "select": "id,doi,title,publication_year,primary_location,best_oa_location,authorships,type",
                    "per-page": 200, "cursor": cursor}, timeout=120)
            except Exception as e:
                log.warning("openalex request failed for %r: %r", q, e)
                break
            if r.status_code != 200:
                log.warning("openalex %s -> %s", q, r.status_code)
                break
            d = r.json()
            for w in d["results"]:
                bo = w.get("best_oa_location") or {}
                pdf = bo.get("pdf_url")
                if not pdf or w["id"] in seen:
                    continue
                seen.add(w["id"])
                out.append({
                    "openalex_id": w["id"], "doi": w.get("doi"), "title": w.get("title"),
                    "year": w.get("publication_year"), "pdf_url": pdf, "landing": bo.get("landing_page_url"),
                    "license": bo.get("license"), "venue": (bo.get("source") or {}).get("display_name"),
                    "authors": "; ".join(a["author"]["display_name"] for a in (w.get("authorships") or [])[:6]),
                    "query": q,
                })
            cursor = d.get("meta", {}).get("next_cursor")
            time.sleep(0.5)
        log.info("query %r -> cumulative %d candidates with OA pdf", q, len(out))
    if out:
        for c in out:
            _append(CAND_FILE, c)
    return out[:max_n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=400)
    args = ap.parse_args()
    session = make_session()
    session.headers["Accept"] = "application/pdf, */*;q=0.5"
    done = already_done(PROV_FILE)
    PDFS.mkdir(parents=True, exist_ok=True)
    rl = RateLimiter(1.5)
    cands = openalex_candidates(session, args.max)
    n_pdf = n_fig = n_block = 0
    hosts_blocked: dict[str, int] = {}
    for c in cands:
        tag = safe_name((c["doi"] or c["openalex_id"]).replace("https://doi.org/", ""))
        pdf = PDFS / f"{tag}.pdf"
        rl.wait()
        ok = download(session, c["pdf_url"], pdf, timeout=180, min_bytes=20_000)
        if ok:
            with open(pdf, "rb") as f:
                head = f.read(5)
            if head != b"%PDF-":          # HTML challenge page or similar -> not usable
                ok = False
                pdf.unlink(missing_ok=True)
        if not ok:
            host = c["pdf_url"].split("/")[2]
            hosts_blocked[host] = hosts_blocked.get(host, 0) + 1
            n_block += 1
            continue
        n_pdf += 1
        figs = pdf_figures.extract(pdf, FIGS / tag, tag, max_pages=60)
        for fg in figs:
            rid = f"{SOURCE}:{tag}:{fg['path'].name}"
            if rid in done:
                continue
            rec = provenance_record(
                source=SOURCE, tier=licence_tier(c["license"]), image_path=fg["path"],
                acquisition_method="OpenAlex works API (best_oa_location.pdf_url) -> HTTP GET PDF -> PyMuPDF caption-matched extraction",
                file_url=c["pdf_url"], landing_url=c["landing"] or c["doi"],
                license=c["license"], license_url=None, rights_holder=c["authors"],
                doc_id=c["doi"] or c["openalex_id"], title=c["title"], venue=c["venue"], year=c["year"],
                figure_label=fg["label"], caption=fg["caption"], query=c["query"],
                filter_rule=f"caption_tier={fg['tier']};kind={fg['kind']}",
                extra={"page": fg["page"], "kind": fg["kind"], "caption_tier": fg["tier"], "openalex_id": c["openalex_id"]},
            )
            rec["record_id"] = rid
            append_jsonl(PROV_FILE, rec)
            n_fig += 1
        if n_pdf % 25 == 0:
            log.info("pdfs ok %d, blocked/non-pdf %d, figures %d", n_pdf, n_block, n_fig)
    log.info("DONE candidates=%d pdfs=%d blocked=%d figures=%d", len(cands), n_pdf, n_block, n_fig)
    log.info("blocked hosts: %s", dict(sorted(hosts_blocked.items(), key=lambda kv: -kv[1])[:15]))


if __name__ == "__main__":
    main()
