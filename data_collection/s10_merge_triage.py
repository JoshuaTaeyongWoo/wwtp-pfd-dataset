"""
s10_merge_triage.py — merge AI first-pass triage CSVs, join to the catalog, update the review galleries.

Inputs : data/review/decisions/*.csv   (columns: sheet,idx,record_id,decision,category,note)
Outputs: data/triage_ai.csv            (catalog_canonical + decision/category/note)
         data/triage_stats.md          (counts per source x decision)
         data/review/<source>.html     (galleries re-rendered with the AI decision pre-filled and shown as a badge;
                                        the human can override and export as before)

Usage: python s10_merge_triage.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from common import DATA

DEC = DATA / "review" / "decisions"
VALID = {"keep", "unsure", "reject"}


def main():
    frames = []
    for f in sorted(DEC.glob("*.csv")):
        d = pd.read_csv(f, dtype=str).fillna("")
        d["agent_file"] = f.name
        frames.append(d)
    if not frames:
        raise SystemExit("no decision files in " + str(DEC))
    dec = pd.concat(frames, ignore_index=True)
    dec["decision"] = dec["decision"].str.strip().str.lower()
    dec = dec[dec["decision"].isin(VALID)]
    dec = dec.drop_duplicates("record_id", keep="last")

    cat = pd.read_csv(DATA / "catalog_canonical.csv", dtype=str).fillna("")
    m = cat.merge(dec[["record_id", "decision", "category", "note", "agent_file"]], on="record_id", how="left")
    m["decision"] = m["decision"].fillna("")
    m.to_csv(DATA / "triage_ai.csv", index=False, encoding="utf-8-sig")

    lines = ["# AI first-pass triage statistics", ""]
    t = pd.crosstab(m["source"], m["decision"].replace("", "(none)"))
    t["total"] = t.sum(axis=1)
    t.loc["TOTAL"] = t.sum()
    lines += ["## decision by source", "", t.to_markdown(), ""]
    ku = m[m["decision"].isin(["keep", "unsure"])]
    if not ku.empty:
        lines += ["## category (keep + unsure)", "", pd.crosstab(ku["source"], ku["category"].replace("", "(none)")).to_markdown(), ""]
        lines += ["## keep by licence tier", "", pd.crosstab(m[m["decision"] == "keep"]["source"], m[m["decision"] == "keep"]["tier"]).to_markdown(), ""]
    lit = m[m["source"].isin(["europepmc_pmc", "openalex_nonpmc"]) & (m["decision"] != "")]
    if not lit.empty:
        lines += ["## caption-filter precision (literature): decision by caption tier", "",
                  pd.crosstab(lit["caption_tier"], lit["decision"]).to_markdown(), ""]
    (DATA / "triage_stats.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))

    # ---- inject into galleries: a JSON blob the page merges into localStorage if the id has no human decision yet
    pre = {r["record_id"]: {"d": r["decision"], "c": r["category"], "n": r["note"]} for _, r in m.iterrows() if r["decision"]}
    blob = json.dumps(pre, ensure_ascii=False)
    inject = ("<script>const AI=" + blob + ";"
              "for(const [k,v] of Object.entries(AI)){const c=document.querySelector(`.card[data-id=\"${k.replace(/\"/g,'\\\\\"')}\"]`);"
              "if(!c)continue;if(!st[k])st[k]=v.d;const b=document.createElement('div');b.className='meta';"
              "b.textContent='AI: '+v.d+(v.c?' / '+v.c:'')+(v.n?' — '+v.n:'');c.appendChild(b);}"
              "localStorage.setItem(key,JSON.stringify(st));paint();</script>")
    n = 0
    for html in (DATA / "review").glob("*.html"):
        if html.name == "index.html":
            continue
        s = html.read_text(encoding="utf-8")
        if "const AI=" in s:
            s = s[: s.index("<script>const AI=")] + "</body></html>"
        s = s.replace("</body></html>", inject + "</body></html>")
        html.write_text(s, encoding="utf-8")
        n += 1
    print("galleries updated:", n)


if __name__ == "__main__":
    main()
