"""
s11_apply_rules.py — apply the inclusion rules decided on 2026-11-16 to the AI triage and produce the dataset splits.

Rules (see TRIAGE_CRITERIA.md, section "Splits"):
  keep                                   -> main
  unsure / single unit + ancillaries     -> aux_unit        (unit-level auxiliary set, not in the benchmark)
  unsure / 3D-pictorial                  -> aux_pictorial   (robustness / domain-shift test set)
  unsure / crop needed                   -> crop_pending    (becomes main after cropping with s12/s13)
  unsure / layout, mass balance, control -> excluded
  unsure / other-domain process diagram  -> aux_other_domain (chemical / refinery / power PFDs)
  unsure / unspecified or render failed  -> manual_review
  reject                                 -> excluded

Outputs: data/triage_final.csv (triage_ai + group + split), data/triage_final_stats.md,
         data/review/manual_review.html (gallery of the manual_review split, decisions pre-filled as 'unsure')
Usage: python s11_apply_rules.py
"""
from __future__ import annotations

import html
import re

import pandas as pd

from common import DATA, ROOT
import s08_review_gallery as g8

RX = {
    "G5_render_fail": r"no render|render issue|blank",
    "G2_pictorial": r"3d|pictorial|cartoon|isometric|illustration|photo-icon",
    "G3_crop_needed": r"panel|crop|page render|fragment|rotated|dense|unreadable|low res",
    "G1_single_unit": r"single|one unit|one vessel|ancillar|cross-?section|single apparatus|cutaway|one reactor|operating cycle|cycle|same tank|rig",
    "G4_layout_massbalance": r"layout|plan view|top view|no flow|no lines|mass|balance|box diagram|block overview|sankey|control",
}
SPLIT = {"G1_single_unit": "aux_unit", "G2_pictorial": "aux_pictorial", "G3_crop_needed": "crop_pending",
         "G4_layout_massbalance": "excluded", "G5_render_fail": "manual_review", "G6_other_domain": "aux_other_domain",
         "G7_unspecified": "manual_review"}


def group(r) -> str:
    if r["decision"] != "unsure":
        return ""
    n = (r["note"] + " " + r["category"]).lower()
    for g, rx in RX.items():            # order matters: render-fail first, then pictorial, crop, single, layout
        if re.search(rx, n):
            return g
    return "G6_other_domain" if r["category"] == "other" else "G7_unspecified"


def main():
    df = pd.read_csv(DATA / "triage_ai.csv", dtype=str).fillna("")
    df["group"] = df.apply(group, axis=1)
    df["split"] = df.apply(lambda r: "main" if r["decision"] == "keep" else ("excluded" if r["decision"] == "reject" else SPLIT[r["group"]]), axis=1)
    df.to_csv(DATA / "triage_final.csv", index=False, encoding="utf-8-sig")

    lines = ["# Dataset splits after the 2026-11-16 inclusion decisions", ""]
    t = pd.crosstab(df["source"], df["split"]); t["total"] = t.sum(axis=1); t.loc["TOTAL"] = t.sum()
    lines += ["## split by source", "", t.to_markdown(), ""]
    m = df[df["split"] == "main"]
    lines += ["## main split: licence tier x category", "", pd.crosstab(m["tier"], m["category"]).to_markdown(), ""]
    lines += ["## unsure groups", "", df[df["decision"] == "unsure"].groupby("group").size().rename("n").to_frame().to_markdown(), ""]
    (DATA / "triage_final_stats.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))

    # manual-review gallery
    sub = df[df["split"] == "manual_review"]
    cards = []
    for _, r in sub.iterrows():
        src = ROOT / r["image_path"]
        t_ = g8.thumb(src, 320)
        if t_ is None:
            continue
        cards.append(g8.CARD.format(
            tier=r["tier"], rid=html.escape(r["record_id"]), full=html.escape(src.resolve().as_uri()),
            thumb=html.escape(t_.resolve().as_uri()), label=html.escape(r["figure_label"]),
            caption=html.escape((r["caption"] or r["title"])[:400]), source=r["source"], ctier=r["caption_tier"],
            venue=html.escape(r["venue"][:40]), year=r["year"][:4], doc=html.escape(r["doc_id"][:60] + " | AI note: " + r["note"][:80])))
    out = DATA / "review" / "manual_review.html"
    out.write_text(g8.PAGE.format(title="manual_review (unsure, unspecified or render failed)", w=320, n=len(cards),
                                  cards="\n".join(cards), slug="manual_review"), encoding="utf-8")
    print("manual_review gallery:", len(cards), "cards ->", out)


if __name__ == "__main__":
    main()
