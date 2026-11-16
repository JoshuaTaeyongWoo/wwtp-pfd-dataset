"""
s15_pilot_sample.py — draw the 60-image stratified pilot sample for the annotation pilot
(annotation_taxonomy_plan.md §5.1).

Strata available in the catalog: source (6), language proxy (en / non-en), category
(wwtp / pilot / sludge / wtp / other), licence tier. Visual form (A-E) is not in the
catalog; it is checked afterwards on the contact sheets and recorded in the
`visual_form_prelim` column by hand.

Allocation: square-root allocation across sources (so small sources still get several
images), then within each source a seeded random draw that
  * takes at most one image per document (doc_id),
  * reserves at least one non-English image per source when available,
  * spreads categories (every category present in the source gets at least one slot
    when the source quota allows, remainder proportional).

Outputs (data/pilot/):
  pilot60.csv                 record_id, pilot_no, source, lang_proxy, category, tier, doc_id, image_path, visual_form_prelim (empty)
  images/pilot_NN__<stem>.ext copies of the 60 images (for CVAT upload)
  sheets/pilot_00k.jpg        3 contact sheets (20 per sheet) for the visual-form check
  allocation.md               the strata table actually drawn

Usage: python s15_pilot_sample.py [--seed 20261116] [--n 60]
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from common import DATA, ROOT
from s09_make_sheets import load_image

PILOT = DATA / "pilot"
CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯]")
SOURCE_ORDER = ["patents_google", "europepmc_pmc", "openalex_nonpmc", "epa_manuals", "wikimedia_commons", "korean_municipal"]


def lang_proxy(r: pd.Series) -> str:
    if r["source"] == "korean_municipal":
        return "non-en"
    if r["source"] == "patents_google":
        m = re.match(r"patents_google:([A-Z]{2})", r["record_id"])
        cc = m.group(1) if m else ""
        return "non-en" if cc in {"CN", "JP", "KR", "TW", "RU", "DE", "FR", "ES"} else "en"
    text = f"{r.get('caption', '')} {r.get('title', '')}"
    return "non-en" if CJK.search(text) else "en"


def sqrt_allocation(counts: dict[str, int], n: int) -> dict[str, int]:
    w = {k: math.sqrt(v) for k, v in counts.items() if v > 0}
    tot = sum(w.values())
    alloc = {k: max(1, int(n * v / tot)) for k, v in w.items()}
    # fix rounding so the total is exactly n (add to the largest remainders)
    rem = {k: n * w[k] / tot - alloc[k] for k in alloc}
    for k in sorted(rem, key=rem.get, reverse=True):
        if sum(alloc.values()) >= n:
            break
        alloc[k] += 1
    while sum(alloc.values()) > n:
        k = max(alloc, key=alloc.get)
        alloc[k] -= 1
    return {k: min(alloc[k], counts[k]) for k in alloc}


def draw_source(g: pd.DataFrame, quota: int, rng: random.Random) -> list[dict]:
    """Seeded draw inside one source honouring doc uniqueness, language and category spread."""
    rows = g.sample(frac=1.0, random_state=rng.randint(0, 2**31 - 1)).to_dict("records")
    chosen, used_docs = [], set()

    def take(pred) -> bool:
        for r in rows:
            if r["doc_id"] in used_docs or r in chosen:
                continue
            if pred(r):
                chosen.append(r)
                used_docs.add(r["doc_id"])
                return True
        return False

    # 1) one non-English image if the source has any
    if quota >= 2:
        take(lambda r: r["lang_proxy"] == "non-en")
    # 2) one image per category present (ordered by category size, big first)
    cat_counts = Counter(r["category"] for r in rows)
    for cat, _ in cat_counts.most_common():
        if len(chosen) >= quota:
            break
        if not any(c["category"] == cat for c in chosen):
            take(lambda r, cat=cat: r["category"] == cat)
    # 3) remainder proportional to category size
    while len(chosen) < quota:
        target = max(cat_counts, key=lambda c: cat_counts[c] - sum(1 for x in chosen if x["category"] == c) * len(rows) / quota)
        if not take(lambda r, cat=target: r["category"] == cat):
            if not take(lambda r: True):
                break
    return chosen[:quota]


SIM_RX = re.compile(r"GPS-?X|BioWin|SUMO|\bWEST\b|simulat|flowsheet model", re.I)


def page_like(size_str: str) -> bool:
    """True for images that are most likely a rendered document page (tall, A4/Letter aspect).
    In main this flags ~64/90 EPA, ~109/178 OpenAlex and ~68/342 patent images (2026-11-16)."""
    try:
        w, h = (int(x) for x in re.findall(r"\d+", size_str)[:2])
    except Exception:
        return False
    return h > 1400 and 1.25 <= h / w <= 1.5


def replace_page_renders(chosen: list[dict], main_df: pd.DataFrame, prelim: dict[int, str], rng: random.Random) -> list[dict]:
    """Second pass: swap items whose provisional visual form is E (page render / multi-panel page,
    which the pilot excludes by design, plan §5.1) for an unused image of the same source,
    language and category. Up to two replacements prefer simulator screenshots (form D) so that
    form D is represented. The swap list is written to replacements.json for reproducibility."""
    used_docs = {r["doc_id"] for r in chosen}
    used_ids = {r["record_id"] for r in chosen}
    swaps, sim_quota = {}, 2
    for r in chosen:
        if prelim.get(r["pilot_no"]) != "E":
            continue
        base = main_df[(main_df["source"] == r["source"]) & (~main_df["record_id"].isin(used_ids))]
        not_page = ~base["image_size"].map(page_like)  # skip whole-page renders (A4/Letter aspect, tall)
        # fallback chain: new doc + figure-sized -> same doc allowed + figure-sized -> new doc, any size
        pool = base[(~base["doc_id"].isin(used_docs)) & not_page]
        relax = ""
        if not len(pool):
            pool, relax = base[not_page], "same-document allowed (source has few documents)"
        if not len(pool):
            pool, relax = base[~base["doc_id"].isin(used_docs)], "page-like allowed (no figure-sized image left)"
        pool = pool.sample(frac=1.0, random_state=rng.randint(0, 2**31 - 1))
        cand = None
        if sim_quota:
            sim = pool[pool["caption"].str.contains(SIM_RX) | pool["title"].str.contains(SIM_RX)]
            if len(sim):
                cand, sim_quota = sim.iloc[0], sim_quota - 1
        if cand is None:
            same = pool[(pool["category"] == r["category"]) & (pool["lang_proxy"] == r["lang_proxy"])]
            cand = same.iloc[0] if len(same) else pool.iloc[0]
        new = cand.to_dict()
        new["pilot_no"] = r["pilot_no"]
        swaps[r["pilot_no"]] = {"old": r["record_id"], "new": new["record_id"],
                                "reason": "provisional visual form E (page render) -> same source/category/language" + (f"; {relax}" if relax else "")}
        used_docs.add(new["doc_id"]); used_ids.add(new["record_id"])
        chosen[chosen.index(r)] = new
    (PILOT / "replacements.json").write_text(json.dumps(swaps, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"replaced {len(swaps)} page-render items")
    return chosen


def make_sheets(rows: list[dict], font) -> None:
    cols, nrows, cell = 5, 4, 360
    per = cols * nrows
    (PILOT / "sheets").mkdir(parents=True, exist_ok=True)
    mapping = {}
    for k in range(0, len(rows), per):
        chunk = rows[k:k + per]
        sheet = Image.new("RGB", (cols * cell, nrows * cell), "white")
        d = ImageDraw.Draw(sheet)
        for i, r in enumerate(chunk):
            im = load_image(ROOT / r["image_path"])
            x, y = (i % cols) * cell, (i // cols) * cell
            if im is not None:
                im.thumbnail((cell - 8, cell - 8))
                sheet.paste(im, (x + 4, y + 4))
            d.rectangle([x, y, x + 64, y + 26], fill="red")
            d.text((x + 5, y + 2), f"{r['pilot_no']:02d}", fill="white", font=font)
            d.text((x + 70, y + 2), r["source"][:14], fill="black", font=font)
            d.rectangle([x, y, x + cell - 1, y + cell - 1], outline="#cccccc")
        name = f"pilot_{k // per:03d}.jpg"
        sheet.save(PILOT / "sheets" / name, "JPEG", quality=85)
        mapping[name] = [r["pilot_no"] for r in chunk]
    (PILOT / "sheets" / "sheets.json").write_text(json.dumps(mapping, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261116)
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--prelim", default="", help="CSV pilot_no,visual_form_prelim from the first draw; E items get replaced")
    a = ap.parse_args()
    rng = random.Random(a.seed)

    df = pd.read_csv(DATA / "triage_final.csv", dtype=str, encoding="utf-8-sig").fillna("")
    main_df = df[df["split"] == "main"].copy()
    main_df["lang_proxy"] = main_df.apply(lang_proxy, axis=1)
    counts = {s: int((main_df["source"] == s).sum()) for s in SOURCE_ORDER}
    alloc = sqrt_allocation(counts, a.n)

    chosen: list[dict] = []
    for s in SOURCE_ORDER:
        chosen += draw_source(main_df[main_df["source"] == s], alloc[s], rng)
    rng.shuffle(chosen)  # pilot numbering must not reveal the source order
    for i, r in enumerate(chosen, 1):
        r["pilot_no"] = i

    PILOT.mkdir(parents=True, exist_ok=True)
    prelim: dict[int, str] = {}
    if a.prelim:
        pre = pd.read_csv(a.prelim, dtype=str).fillna("")
        prelim = {int(k): v for k, v in zip(pre["pilot_no"], pre["visual_form_prelim"])}
        chosen = replace_page_renders(chosen, main_df, prelim, rng)
    img_dir = PILOT / "images"
    if img_dir.exists():
        shutil.rmtree(img_dir)
    img_dir.mkdir()
    for r in chosen:
        src = ROOT / r["image_path"]
        dst = img_dir / f"pilot_{r['pilot_no']:02d}__{src.stem[:60]}{src.suffix.lower()}"
        shutil.copy2(src, dst)
        r["pilot_image"] = str(dst.relative_to(ROOT)).replace("\\", "/")

    out = pd.DataFrame(chosen)[["pilot_no", "record_id", "source", "lang_proxy", "category", "tier", "doc_id", "image_path", "pilot_image", "caption"]]
    out["caption"] = out["caption"].str.slice(0, 200)
    out["visual_form_prelim"] = [("" if prelim.get(int(n)) == "E" else prelim.get(int(n), "")) for n in out["pilot_no"]]
    out = out.sort_values("pilot_no")
    out.to_csv(PILOT / "pilot60.csv", index=False, encoding="utf-8-sig")

    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
    make_sheets(sorted(chosen, key=lambda r: r["pilot_no"]), font)

    # allocation report
    lines = [f"# Pilot sample allocation (seed {a.seed}, n = {len(chosen)}, drawn {pd.Timestamp.now():%Y-%m-%d})", "",
             "| source | main images | quota | drawn | non-en | categories |", "|---|---|---|---|---|---|"]
    for s in SOURCE_ORDER:
        g = [r for r in chosen if r["source"] == s]
        cats = ", ".join(f"{k} {v}" for k, v in Counter(r["category"] for r in g).most_common())
        lines.append(f"| {s} | {counts[s]} | {alloc[s]} | {len(g)} | {sum(r['lang_proxy'] == 'non-en' for r in g)} | {cats} |")
    lines += ["", f"docs: {len({r['doc_id'] for r in chosen})} distinct documents; tier A {sum(r['tier'] == 'A' for r in chosen)}, tier B {sum(r['tier'] == 'B' for r in chosen)}",
              "", "Visual form (A box / B symbol / C pictorial / D simulator / E page) is filled in `pilot60.csv` after inspecting `sheets/`."]
    (PILOT / "allocation.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
