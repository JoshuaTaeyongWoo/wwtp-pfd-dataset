"""
s25_test_split.py — draw the FIXED TEST SET for the incremental-training protocol
(annotation_taxonomy_plan.md §5 4b / §5 7).

The test set is chosen BEFORE the first main-annotation batch, double-annotated as that first
batch, and then frozen: it is never used for training, validation or pre-annotation. Fixing it
up front is what makes the per-round scores (learning curve) comparable.

Pool   : triage_final.csv rows with split == main, MINUS
           * the 60 pilot images and every other image from the same documents (pilot = val),
           * whole-page renders of non-patent sources (A4/Letter aspect, h > 1400 px) that are
             still waiting for a crop — annotation of those happens after cropping,
           * record_ids listed in --exclude (one per line, '#' comments allowed).
Strata : source (6) x language proxy (en / non-en) x category, one image per document (a second image
         from an already-drawn document is taken only when a source has fewer documents than slots —
         EPA manuals and Korean municipal sites — and this is reported).
         Visual form is not in the catalog (it is read off the contact sheets afterwards), so
         the draw is checked post hoc: fill `visual_form_prelim` in test_fixed.csv and, if a
         form is badly under-represented, re-run with --swap <csv of record_id,reason> to replace
         listed items by an unused image of the same source / language / category.
Alloc  : proportional to the pool size per source, with a floor of --min-per-source so that
         the small sources (Wikimedia, Korean municipal) still yield a per-source estimate.
         (`--alloc sqrt` reproduces the pilot's square-root allocation instead.)

Outputs (data/splits/):
  test_fixed.csv            test_no, record_id, source, lang_proxy, category, tier, doc_id, image_path,
                            caption (200 chars), visual_form_prelim (empty, filled by hand)
  val_pilot60.csv           the pilot 60 as the validation set (copied from data/pilot/pilot60.csv)
  test_fixed_allocation.md  strata table actually drawn + exclusions
  sheets_test/test_00k.jpg  contact sheets (20 per sheet) for the visual-form check
  test_images/              copies named test_NNN__<stem>.ext (with --copy-images; input for s18 --images)

Usage: python s25_test_split.py [--seed 20261123] [--n 150] [--min-per-source 8] [--alloc proportional|sqrt]
                                [--exclude ids.txt] [--swap swaps.csv] [--copy-images]
Re-running with the same seed and the same pool reproduces the same list.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import shutil
from collections import Counter
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from common import DATA, ROOT
from s09_make_sheets import load_image
from s15_pilot_sample import SOURCE_ORDER, draw_source, lang_proxy, page_like, sqrt_allocation

SPLITS = DATA / "splits"
PILOT_CSV = DATA / "pilot" / "pilot60.csv"
PAGE_RENDER_SOURCES = {"epa_manuals", "openalex_nonpmc", "europepmc_pmc", "wikimedia_commons", "korean_municipal"}  # patents: full-page drawings are the figure


def proportional_allocation(counts: dict[str, int], n: int, floor: int) -> dict[str, int]:
    """Largest-remainder proportional allocation with a per-source floor (capped at the pool size)."""
    alloc = {k: min(counts[k], floor) for k in counts if counts[k] > 0}
    rest = n - sum(alloc.values())
    if rest < 0:
        raise SystemExit(f"--n {n} is smaller than the floors ({sum(alloc.values())}); lower --min-per-source")
    free = {k: counts[k] - alloc[k] for k in alloc}
    tot = sum(free.values())
    extra = {k: int(rest * free[k] / tot) for k in alloc} if tot else {k: 0 for k in alloc}
    rem = {k: rest * free[k] / tot - extra[k] for k in alloc} if tot else {}
    for k in sorted(rem, key=rem.get, reverse=True):
        if sum(extra.values()) >= rest:
            break
        if extra[k] < free[k]:
            extra[k] += 1
    return {k: alloc[k] + extra[k] for k in alloc}


def build_pool(df: pd.DataFrame, exclude_ids: set[str]) -> tuple[pd.DataFrame, dict]:
    main_df = df[df["split"] == "main"].copy()
    main_df["lang_proxy"] = main_df.apply(lang_proxy, axis=1)
    notes = {"main": len(main_df)}

    pilot = pd.read_csv(PILOT_CSV, dtype=str, encoding="utf-8-sig").fillna("")
    pilot_ids, pilot_docs = set(pilot["record_id"]), set(pilot["doc_id"])
    is_pilot_doc = main_df["doc_id"].isin(pilot_docs) | main_df["record_id"].isin(pilot_ids)
    notes["pilot_images"] = int(main_df["record_id"].isin(pilot_ids).sum())
    notes["same_doc_as_pilot"] = int(is_pilot_doc.sum()) - notes["pilot_images"]

    is_page = main_df["source"].isin(PAGE_RENDER_SOURCES) & main_df["image_size"].map(page_like)
    notes["page_renders_pending_crop"] = int((is_page & ~is_pilot_doc).sum())
    notes["page_renders_by_source"] = {s: int((is_page & ~is_pilot_doc & (main_df["source"] == s)).sum()) for s in SOURCE_ORDER}

    is_excl = main_df["record_id"].isin(exclude_ids)
    notes["excluded_by_list"] = int((is_excl & ~is_pilot_doc & ~is_page).sum())

    pool = main_df[~is_pilot_doc & ~is_page & ~is_excl].copy()
    notes["pool"] = len(pool)
    notes["pool_docs"] = int(pool["doc_id"].nunique())
    return pool, notes


def top_up_same_doc(got: list[dict], g: pd.DataFrame, quota: int, rng: random.Random) -> list[dict]:
    """Fill a source's quota when it has fewer documents than slots: take further images from the
    documents already drawn, spreading them over the documents (fewest drawn first). Only used for
    sources whose distinct documents < quota; never crosses into pilot documents (not in the pool)."""
    used_ids = {r["record_id"] for r in got}
    per_doc = Counter(r["doc_id"] for r in got)
    rest = g[~g["record_id"].isin(used_ids)].sample(frac=1.0, random_state=rng.randint(0, 2**31 - 1)).to_dict("records")
    extra: list[dict] = []
    while len(got) + len(extra) < quota and rest:
        rest.sort(key=lambda r: per_doc[r["doc_id"]])
        r = rest.pop(0)
        extra.append(r)
        per_doc[r["doc_id"]] += 1
    return extra


def apply_swaps(chosen: list[dict], pool: pd.DataFrame, swaps: pd.DataFrame, rng: random.Random) -> list[dict]:
    """Replace listed record_ids by an unused image of the same source / language / category (new document)."""
    used_docs = {r["doc_id"] for r in chosen}
    used_ids = {r["record_id"] for r in chosen}
    log = {}
    for rid, reason in zip(swaps["record_id"], swaps.get("reason", [""] * len(swaps))):
        idx = next((i for i, r in enumerate(chosen) if r["record_id"] == rid), None)
        if idx is None:
            print(f"swap: {rid} is not in the current draw, skipped")
            continue
        r = chosen[idx]
        src_pool = pool[(pool["source"] == r["source"]) & (~pool["record_id"].isin(used_ids))]
        base = src_pool[~src_pool["doc_id"].isin(used_docs)]
        relax = ""
        if not len(base):  # source has no unused document left (EPA manuals): allow an already-drawn document
            base, relax = src_pool, " (same document allowed: no unused document left)"
        same = base[(base["category"] == r["category"]) & (base["lang_proxy"] == r["lang_proxy"])]
        cand_pool = same if len(same) else base
        if not len(cand_pool):
            print(f"swap: no replacement left for {rid} in {r['source']}, kept")
            continue
        new = cand_pool.sample(n=1, random_state=rng.randint(0, 2**31 - 1)).iloc[0].to_dict()
        reason = reason + relax
        new["test_no"] = r["test_no"]
        used_docs.add(new["doc_id"]); used_ids.add(new["record_id"])
        chosen[idx] = new
        log[r["test_no"]] = {"old": rid, "new": new["record_id"], "reason": reason}
    (SPLITS / "test_swaps.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"swapped {len(log)} items")
    return chosen


def flat_image(path: Path) -> Image.Image | None:
    """Load any catalog image (SVG rendered, WebP decoded) and flatten transparency onto white.
    PDF-extracted PNGs sometimes carry an alpha layer whose RGB underneath is black, so a plain
    convert('RGB') would bury black lines; compositing on white keeps them."""
    im = load_image(path)
    if im is None:
        return None
    if "A" in im.getbands():
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.getchannel("A"))
        return bg
    return im.convert("RGB")


def make_sheets(rows: list[dict], font, out: Path, prefix: str = "test") -> None:
    cols, nrows, cell = 5, 4, 360
    per = cols * nrows
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    mapping = {}
    for k in range(0, len(rows), per):
        chunk = rows[k:k + per]
        sheet = Image.new("RGB", (cols * cell, nrows * cell), "white")
        d = ImageDraw.Draw(sheet)
        for i, r in enumerate(chunk):
            im = flat_image(ROOT / r["image_path"])
            x, y = (i % cols) * cell, (i // cols) * cell
            if im is not None:
                im.thumbnail((cell - 8, cell - 8))
                sheet.paste(im, (x + 4, y + 4))
            d.rectangle([x, y, x + 72, y + 26], fill="darkblue")
            d.text((x + 5, y + 2), f"{r['test_no']:03d}", fill="white", font=font)
            d.text((x + 78, y + 2), r["source"][:14], fill="black", font=font)
            d.rectangle([x, y, x + cell - 1, y + cell - 1], outline="#cccccc")
        name = f"{prefix}_{k // per:03d}.jpg"
        sheet.save(out / name, "JPEG", quality=85)
        mapping[name] = [r["test_no"] for r in chunk]
    (out / "sheets.json").write_text(json.dumps(mapping, indent=1), encoding="utf-8")


def load_base(path: Path, main_df: pd.DataFrame) -> list[dict]:
    """Re-create the drawn list from an earlier test_fixed.csv so that --swap only replaces the
    listed items and every other item (and its test_no) stays exactly as reviewed."""
    base = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    by_id = main_df.set_index("record_id")
    chosen = []
    for _, b in base.iterrows():
        if b["record_id"] not in by_id.index:
            raise SystemExit(f"--base item {b['record_id']} is no longer in main")
        r = by_id.loc[b["record_id"]].to_dict()
        r["record_id"] = b["record_id"]
        r["test_no"] = int(b["test_no"])
        r["visual_form_prelim"] = b.get("visual_form_prelim", "")   # carried over from the reviewed list
        chosen.append(r)
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261123)
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--min-per-source", type=int, default=8)
    ap.add_argument("--alloc", choices=["proportional", "sqrt"], default="proportional")
    ap.add_argument("--exclude", default="", help="text file of record_ids to leave out of the pool")
    ap.add_argument("--swap", default="", help="CSV record_id,reason: replace these drawn items (same source/lang/category)")
    ap.add_argument("--copy-images", action="store_true", help="copy the drawn images to data/splits/test_images/ (SVG rasterised, alpha flattened)")
    ap.add_argument("--base", default="", help="existing test_fixed.csv: keep its items and numbering, apply --swap only (no new draw)")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    SPLITS.mkdir(parents=True, exist_ok=True)

    exclude_ids: set[str] = set()
    if a.exclude:
        exclude_ids = {ln.strip() for ln in Path(a.exclude).read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")}

    df = pd.read_csv(DATA / "triage_final.csv", dtype=str, encoding="utf-8-sig").fillna("")
    pool, notes = build_pool(df, exclude_ids)
    counts = {s: int((pool["source"] == s).sum()) for s in SOURCE_ORDER}
    alloc = sqrt_allocation(counts, a.n) if a.alloc == "sqrt" else proportional_allocation(counts, a.n, a.min_per_source)

    chosen: list[dict] = []
    topped_up: dict[str, int] = {}
    if a.base:
        main_all = df[df["split"] == "main"].copy()
        main_all["lang_proxy"] = main_all.apply(lang_proxy, axis=1)
        chosen = load_base(Path(a.base), main_all)
        print(f"base: {len(chosen)} items kept from {a.base}")
    else:
        for s in SOURCE_ORDER:
            got = draw_source(pool[pool["source"] == s], alloc[s], rng)
            if len(got) < alloc[s]:  # source has fewer documents than its quota (EPA manuals, Korean municipal)
                extra = top_up_same_doc(got, pool[pool["source"] == s], alloc[s], rng)
                topped_up[s] = len(extra)
                got += extra
            chosen += got
        rng.shuffle(chosen)  # numbering must not reveal the source order
        for i, r in enumerate(chosen, 1):
            r["test_no"] = i

    swapped_nos: list[int] = []
    if a.swap:
        before = {r["test_no"]: r["record_id"] for r in chosen}
        chosen = apply_swaps(chosen, pool, pd.read_csv(a.swap, dtype=str, encoding="utf-8-sig").fillna(""), rng)
        swapped_nos = [r["test_no"] for r in chosen if before[r["test_no"]] != r["record_id"]]

    assert len({r["record_id"] for r in chosen}) == len(chosen), "duplicate record"
    n_docs = len({r["doc_id"] for r in chosen})
    if not a.base:
        assert n_docs == len(chosen) - sum(topped_up.values()), "unexpected document repeat outside the top-up"

    cols = ["test_no", "record_id", "source", "lang_proxy", "category", "tier", "doc_id", "image_path", "caption"]
    out = pd.DataFrame(chosen)[cols].copy()
    out["caption"] = out["caption"].str.slice(0, 200)
    out["visual_form_prelim"] = [r.get("visual_form_prelim", "") for r in chosen]
    out = out.sort_values("test_no")
    out.to_csv(SPLITS / "test_fixed.csv", index=False, encoding="utf-8-sig")

    val = pd.read_csv(PILOT_CSV, dtype=str, encoding="utf-8-sig").fillna("")
    val.to_csv(SPLITS / "val_pilot60.csv", index=False, encoding="utf-8-sig")

    if a.copy_images:
        img_dir = SPLITS / "test_images"
        if img_dir.exists():
            shutil.rmtree(img_dir)
        img_dir.mkdir()
        for r in chosen:
            src = ROOT / r["image_path"]
            dst = img_dir / f"test_{r['test_no']:03d}__{src.stem[:60]}"
            im = Image.open(src) if src.suffix.lower() in (".png", ".jpg", ".jpeg") else None
            if im is not None and "A" not in im.getbands() and src.suffix.lower() != ".webp":
                shutil.copy2(src, dst.with_suffix(src.suffix.lower()))   # plain raster: byte-for-byte copy
            else:  # SVG, WebP or alpha PNG -> flattened PNG (Label Studio shows these reliably)
                flat = flat_image(src)
                if flat is None:
                    raise SystemExit(f"cannot load {src}")
                flat.save(dst.with_suffix(".png"))

    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
    make_sheets(sorted(chosen, key=lambda r: r["test_no"]), font, SPLITS / "sheets_test")
    if swapped_nos:
        make_sheets(sorted((r for r in chosen if r["test_no"] in swapped_nos), key=lambda r: r["test_no"]),
                    font, SPLITS / "sheets_swapped", prefix="swapped")

    lines = [f"# Fixed test set allocation (seed {a.seed}, n = {len(chosen)}, alloc = {a.alloc}, floor = {a.min_per_source}, drawn {pd.Timestamp.now():%Y-%m-%d})", "",
             f"Pool: main {notes['main']} - pilot images {notes['pilot_images']} (of 60; the rest moved to crop_pending by s16, their documents still excluded)"
             f" - other images of pilot documents {notes['same_doc_as_pilot']} (val/test document-disjoint)"
             f" - page renders pending crop {notes['page_renders_pending_crop']} - excluded by list {notes['excluded_by_list']} = **{notes['pool']}** images in {notes['pool_docs']} documents.",
             f"Page renders pending crop by source: " + ", ".join(f"{k} {v}" for k, v in notes["page_renders_by_source"].items() if v),
             ("Quota filled with a second image from an already-drawn document (source has fewer documents than slots): "
              + ", ".join(f"{k} +{v}" for k, v in topped_up.items() if v)) if any(topped_up.values()) else "Every drawn image comes from a distinct document.", "",
             "| source | pool | share | quota | drawn | non-en | categories |", "|---|---|---|---|---|---|---|"]
    for s in SOURCE_ORDER:
        g = [r for r in chosen if r["source"] == s]
        cats = ", ".join(f"{k} {v}" for k, v in Counter(r["category"] for r in g).most_common())
        share = counts[s] / max(1, notes["pool"])
        lines.append(f"| {s} | {counts[s]} | {share:.1%} | {alloc[s]} | {len(g)} | {sum(r['lang_proxy'] == 'non-en' for r in g)} | {cats} |")
    pool_cats = Counter(pool["category"])
    lines += ["", "| category | pool | drawn |", "|---|---|---|"]
    for c, v in pool_cats.most_common():
        lines.append(f"| {c} | {v} | {sum(r['category'] == c for r in chosen)} |")
    lines += ["", f"docs: {n_docs} distinct documents; tier A {sum(r['tier'] == 'A' for r in chosen)}, tier B {sum(r['tier'] == 'B' for r in chosen)};"
              f" non-en {sum(r['lang_proxy'] == 'non-en' for r in chosen)} (pool {int((pool['lang_proxy'] == 'non-en').sum())}).",
              "", "Validation set = pilot 60 (`val_pilot60.csv`). Train = every other main image, accumulated as batches arrive.",
              "Visual form (A box / B symbol / C pictorial / D simulator / E page) is filled in `test_fixed.csv` after inspecting `sheets_test/`;",
              "items to replace go in a CSV `record_id,reason` and the script is re-run with `--swap` (same seed)."]
    (SPLITS / "test_fixed_allocation.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
