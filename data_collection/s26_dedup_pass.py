"""
s26_dedup_pass.py — second de-duplication / image-quality pass over the MAIN set, run before the
first main-annotation batch (found during the 2026-11-24 test-set review, plan §5 4b).

Four checks, all restricted to split == main:
  A. crop/embedded twins — an s16 page-render crop ("..._pNNNN_page.png#cropK") and an embedded image
     of the SAME document and page ("..._pNNNN_imgNNN.png", or its s13 crop) are the same figure.
     s07 missed them because the two renderings differ in resolution / margins (pHash > 6).
  B. near-duplicates anywhere in main at pHash Hamming <= 8 (s07 used <= 6 and had no hash for SVG);
     plus Wikimedia files that are the same name in another format (SVG / PNG / JPG).
  C. alpha PNGs whose background turned black (PDF extraction dropped the soft mask): the drawing's
     black lines vanish, so the image is unusable.
  D. language proxy: s15 only detects CJK; a stopword heuristic flags French / German / Spanish /
     Italian / Portuguese / Dutch captions so the stratification sees them as non-English.

Pairs with Hamming <= 12 (A) / <= 4 (B) are marked `dup_sure`; the rest become `check` and are laid
out side by side in data/dedup/check_*.jpg with a decisions CSV (decision: dup / keep) to fill in.
Which twin survives: a member of the fixed test set or the pilot set always wins (those lists are
frozen); otherwise the embedded image wins unless it has < 50 % of the crop's pixels.

Report mode (default) writes data/dedup/{twins.csv, near.csv, alpha.csv, lang.csv, report.md} and the
check sheets. `--apply [--decisions data/dedup/check_decisions.csv]` backs triage_final.csv up to
data/triage_final_before_s26.csv and sets split=excluded, duplicate_of=<winner>, canonical=False and a
note on every loser / broken image.

Usage: python s26_dedup_pass.py [--apply] [--decisions check_decisions.csv]
"""
from __future__ import annotations

import argparse
import math
import re
import shutil
from collections import Counter
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from common import DATA, ROOT, phash_of
from s09_make_sheets import load_image

OUT = DATA / "dedup"
TEST_CSV = DATA / "splits" / "test_fixed.csv"
PILOT_CSV = DATA / "pilot" / "pilot60.csv"
PAGE_RX = re.compile(r"_p(\d{4})_")
STOP = {  # very common function words, lower-cased; a caption needs >= 2 distinct hits to count
    "fr": {"le", "la", "les", "des", "une", "du", "et", "est", "pour", "avec", "dans", "sur", "épuration", "eaux", "usées", "station", "schéma", "traitement", "boues"},
    "de": {"der", "die", "das", "und", "mit", "für", "von", "ein", "eine", "einer", "kläranlage", "abwasser", "schema", "belebung", "schlamm", "becken", "anlage", "verfahren"},
    "es": {"el", "los", "las", "una", "del", "por", "con", "para", "depuradora", "aguas", "residuales", "tratamiento", "lodos", "esquema", "planta"},
    "it": {"il", "gli", "della", "delle", "dei", "degli", "con", "per", "depurazione", "acque", "reflue", "impianto", "fanghi", "schema", "trattamento"},
    "pt": {"os", "as", "uma", "dos", "das", "com", "para", "não", "tratamento", "esgoto", "esgotos", "estação", "lodo", "lodos", "efluente", "esquema"},
    "nl": {"de", "het", "een", "van", "en", "met", "voor", "rioolwaterzuivering", "zuivering", "afvalwater", "slib", "schema", "installatie"},
}
AMBIG = {"de", "en", "con", "per", "as", "os", "die", "das", "del", "los", "las", "les", "des", "para", "para"}


def hamming(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def page_of(rid: str) -> str:
    m = PAGE_RX.search(rid)
    return m.group(1) if m else ""


def is_page_crop(rid: str) -> bool:
    return "_page.png#crop" in rid


def area(size_str: str) -> int:
    try:
        w, h = (int(x) for x in re.findall(r"\d+", size_str)[:2])
        return w * h
    except Exception:
        return 0


def lang_latin(text: str) -> str:
    words = set(re.findall(r"[a-zà-ÿ]+", text.lower()))
    best, best_n = "", 0
    for lang, sw in STOP.items():
        hits = {w for w in words & sw if w not in AMBIG}
        n = len(hits) + 0.5 * len(words & sw & AMBIG)
        if n >= 2 and n > best_n:
            best, best_n = lang, n
    return best


# ------------------------------------------------------------------ checks
def check_twins(m: pd.DataFrame, protected: set[str]) -> pd.DataFrame:
    rows = []
    crops = m[m["record_id"].str.contains("#crop", regex=False)]
    for _, c in crops.iterrows():
        pg = page_of(c["record_id"])
        if not pg:
            continue
        same = m[(m["doc_id"] == c["doc_id"]) & (m["record_id"] != c["record_id"]) & (m["record_id"].map(page_of) == pg)]
        for _, o in same.iterrows():
            if is_page_crop(o["record_id"]) and is_page_crop(c["record_id"]):
                continue  # two crops of the same page render are two figures on that page, not twins
            a, b = sorted([c["record_id"], o["record_id"]])
            rows.append((a, b))
    rows = sorted(set(rows))
    # a page crop matched by two or more embedded images is a composite of several figures (or of a
    # multi-panel figure whose panels were extracted separately): keep the crop, drop the parts
    crop_count = Counter(x for pair in rows for x in pair if is_page_crop(x))
    out = []
    for a, b in rows:
        ra, rb = m.loc[m["record_id"] == a].iloc[0], m.loc[m["record_id"] == b].iloc[0]
        h = hamming(ra["phash"], rb["phash"]) if ra["phash"] and rb["phash"] else 99
        status = "dup_sure" if h <= 12 else "check"
        keep = decide_keep(ra, rb, protected)
        for x, other in ((a, b), (b, a)):
            if is_page_crop(x) and crop_count[x] >= 2 and other not in protected:
                keep = x
        out.append({"kind": "twin", "a": a, "b": b, "hamming": h, "status": status, "keep": keep, "drop": b if keep == a else a,
                    "source": ra["source"], "doc_id": ra["doc_id"], "size_a": ra["image_size"], "size_b": rb["image_size"]})
    return pd.DataFrame(out)


def decide_keep(ra: pd.Series, rb: pd.Series, protected: set[str]) -> str:
    a, b = ra["record_id"], rb["record_id"]
    if a in protected and b not in protected:
        return a
    if b in protected and a not in protected:
        return b
    pa, pb = is_page_crop(a), is_page_crop(b)
    if pa != pb:  # one is the page-render crop, the other the embedded image (or its crop)
        emb, crop = (rb, ra) if pa else (ra, rb)
        if area(emb["image_size"]) >= 0.5 * area(crop["image_size"]):
            return emb["record_id"]
        return crop["record_id"]
    return a if area(ra["image_size"]) >= area(rb["image_size"]) else b


def check_near(m: pd.DataFrame, protected: set[str], twin_pairs: set[tuple[str, str]]) -> pd.DataFrame:
    """pHash <= 8 across the whole main set (SVGs hashed from a render) + Wikimedia same-name variants."""
    ph = {}
    for _, r in m.iterrows():
        h = r["phash"]
        if not h:
            im = load_image(ROOT / r["image_path"])
            if im is not None:
                import imagehash
                h = str(imagehash.phash(im.convert("L")))
        ph[r["record_id"]] = h
    ids = list(ph)
    out = []
    for i in range(len(ids)):
        if not ph[ids[i]]:
            continue
        for j in range(i + 1, len(ids)):
            if not ph[ids[j]]:
                continue
            h = hamming(ph[ids[i]], ph[ids[j]])
            if h <= 8:
                a, b = sorted([ids[i], ids[j]])
                if (a, b) in twin_pairs:
                    continue
                out.append((a, b, h, "near"))
    # Wikimedia same stem, different extension
    wm = m[m["source"] == "wikimedia_commons"].copy()
    wm["stem"] = (wm["record_id"].str.replace(r"^wikimedia_commons:File:", "", regex=True).str.split(":").str[0]
                  .str.replace(r"\.(svg|png|jpe?g|gif|webp)$", "", regex=True, case=False).str.lower())
    for stem, g in wm.groupby("stem"):
        if len(g) > 1:
            ids2 = sorted(g["record_id"])
            for k in range(1, len(ids2)):
                a, b = ids2[0], ids2[k]
                if not any(x[0] == a and x[1] == b for x in out):
                    out.append((a, b, hamming(ph[a], ph[b]) if ph[a] and ph[b] else 99, "wikimedia_variant"))
    rows = []
    for a, b, h, why in out:
        ra, rb = m.loc[m["record_id"] == a].iloc[0], m.loc[m["record_id"] == b].iloc[0]
        status = "dup_sure" if (h <= 4 or why == "wikimedia_variant") else "check"
        keep = decide_keep(ra, rb, protected)
        rows.append({"kind": why, "a": a, "b": b, "hamming": h, "status": status, "keep": keep, "drop": b if keep == a else a,
                     "source": ra["source"], "doc_id": ra["doc_id"], "size_a": ra["image_size"], "size_b": rb["image_size"]})
    return pd.DataFrame(rows)


def check_alpha(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in m.iterrows():
        p = ROOT / r["image_path"]
        if p.suffix.lower() != ".png":
            continue
        try:
            with Image.open(p) as im:
                if im.mode not in ("RGBA", "LA") and not (im.mode == "P" and "transparency" in im.info):
                    continue
                rgba = im.convert("RGBA")
        except Exception:
            continue
        white = Image.alpha_composite(Image.new("RGBA", rgba.size, (255, 255, 255, 255)), rgba).convert("L")
        hist = white.histogram()
        dark = sum(hist[:60]) / (rgba.width * rgba.height)
        alpha0 = sum(rgba.getchannel("A").histogram()[:8]) / (rgba.width * rgba.height)
        # dark after compositing on white = the background itself is opaque black; whether the drawing
        # survived (coloured boxes on black) or vanished (black lines on black) needs a human look
        rows.append({"record_id": r["record_id"], "dark_frac_on_white": round(dark, 3), "transparent_frac": round(alpha0, 3),
                     "status": "suspect" if dark > 0.5 else "ok", "image_path": r["image_path"]})
    return pd.DataFrame(rows)


def check_lang(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in m.iterrows():
        lang = lang_latin(f"{r.get('caption', '')} {r.get('title', '')}")
        if lang:
            rows.append({"record_id": r["record_id"], "source": r["source"], "lang_latin": lang, "caption": r.get("caption", "")[:120]})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ sheets
def pair_sheets(pairs: pd.DataFrame, m: pd.DataFrame, prefix: str, font) -> None:
    cell, per = 520, 6
    pairs = pairs.reset_index(drop=True)
    for k in range(0, len(pairs), per):
        chunk = pairs.iloc[k:k + per]
        sheet = Image.new("RGB", (2 * cell + 40, len(chunk) * (cell + 50)), "white")
        d = ImageDraw.Draw(sheet)
        for i, (_, p) in enumerate(chunk.iterrows()):
            y = i * (cell + 50)
            for col, rid in enumerate([p["a"], p["b"]]):
                r = m.loc[m["record_id"] == rid].iloc[0]
                im = load_image(ROOT / r["image_path"])
                x = col * (cell + 40)
                if im is not None:
                    im.thumbnail((cell - 8, cell - 8)); sheet.paste(im, (x + 4, y + 4))
                tag = "KEEP" if rid == p["keep"] else "drop"
                d.rectangle([x, y + cell, x + cell, y + cell + 46], fill=(0, 110, 0) if tag == "KEEP" else (160, 0, 0))
                d.text((x + 6, y + cell + 4), f"pair {k + i:03d} {tag}  h={p['hamming']}  {r['image_size']}", fill="white", font=font)
                d.text((x + 6, y + cell + 24), rid[-70:], fill="white", font=font)
        sheet.save(OUT / f"{prefix}_{k // per:03d}.jpg", "JPEG", quality=82)


def single_sheet(rows: pd.DataFrame, m: pd.DataFrame, name: str, font) -> None:
    cols, cell = 4, 400
    n = len(rows)
    if not n:
        return
    sheet = Image.new("RGB", (cols * cell, math.ceil(n / cols) * (cell + 30)), "white")
    d = ImageDraw.Draw(sheet)
    for i, (_, r) in enumerate(rows.iterrows()):
        im = load_image(ROOT / r["image_path"])
        x, y = (i % cols) * cell, (i // cols) * (cell + 30)
        if im is not None:
            im.thumbnail((cell - 8, cell - 8)); sheet.paste(im, (x + 4, y + 4))
        d.text((x + 4, y + cell + 4), f"{i:02d} dark={r['dark_frac_on_white']} {r['record_id'][-45:]}", fill="black", font=font)
    sheet.save(OUT / name, "JPEG", quality=82)


# ------------------------------------------------------------------ apply
def apply(df: pd.DataFrame, pairs: pd.DataFrame, alpha: pd.DataFrame, decisions: pd.DataFrame | None, protected: set[str]) -> pd.DataFrame:
    """decisions CSV columns: a, b, decision, keep (optional).
       pair rows   : decision dup | keep ; `keep` may name the record to keep (overrides the rule)
       alpha rows  : b empty, decision broken | keep"""
    dec, keep_override, broken = {}, {}, set()
    if decisions is not None:
        for _, r in decisions.iterrows():
            d = r["decision"].strip().lower()
            if not r["b"]:
                if d == "broken":
                    broken.add(r["a"])
                continue
            dec[(r["a"], r["b"])] = d
            if r.get("keep", ""):
                keep_override[(r["a"], r["b"])] = r["keep"]
    n_dup = n_broken = 0
    edges = []  # (winner, loser, pair row)
    for _, p in pairs.iterrows():
        d = dec.get((p["a"], p["b"]), "dup" if p["status"] == "dup_sure" else "keep")
        if d != "dup":
            continue
        keep = keep_override.get((p["a"], p["b"]), p["keep"])
        drop = p["b"] if keep == p["a"] else p["a"]
        if drop in protected:  # frozen test / pilot members always win, whatever the rule or override said
            if keep in protected:
                raise SystemExit(f"both members protected: {p['a']} | {p['b']}")
            keep, drop = drop, keep
        edges.append((keep, drop, p))
    # a loser is dropped only while its winner survives: if the winner itself loses another pair
    # (e.g. a composite page crop that also contains a pilot image), the loser stays as the only copy
    drops: dict[str, tuple] = {}
    while True:
        new = {loser: (keep, p) for keep, loser, p in edges if keep not in drops}
        if set(new) == set(drops):
            break
        drops = new
    for drop, (keep, p) in drops.items():
        i = df.index[df["record_id"] == drop][0]
        if df.at[i, "split"] != "main":
            continue
        df.at[i, "split"] = "excluded"; df.at[i, "duplicate_of"] = keep; df.at[i, "canonical"] = "False"
        df.at[i, "note"] = (str(df.at[i, "note"]).strip() + f"; duplicate (s26 {p['kind']}, h={p['hamming']}) of {keep}").strip("; ")
        n_dup += 1
    survived = [loser for keep, loser, _ in edges if loser not in drops]
    if survived:
        print(f"kept as the only remaining copy (their winner was dropped elsewhere): {len(survived)}")
        for s in survived:
            print("   ", s)
    for rid in broken:
        if rid in protected:
            raise SystemExit(f"refusing to drop protected item {rid}")
        i = df.index[df["record_id"] == rid][0]
        if df.at[i, "split"] != "main":
            continue
        df.at[i, "split"] = "excluded"
        df.at[i, "note"] = (str(df.at[i, "note"]).strip() + "; broken image (s26): alpha background lost, lines invisible").strip("; ")
        n_broken += 1
    print(f"applied: {n_dup} duplicates and {n_broken} broken images moved to excluded")
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--decisions", default="", help="CSV a,b,decision(dup|keep) for the `check` pairs")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()

    df = pd.read_csv(DATA / "triage_final.csv", dtype=str, encoding="utf-8-sig").fillna("")
    m = df[df["split"] == "main"].copy()
    protected = set(pd.read_csv(TEST_CSV, dtype=str, encoding="utf-8-sig")["record_id"]) | set(pd.read_csv(PILOT_CSV, dtype=str, encoding="utf-8-sig")["record_id"])

    twins = check_twins(m, protected)
    near = check_near(m, protected, {(p["a"], p["b"]) for _, p in twins.iterrows()})
    pairs = pd.concat([twins, near], ignore_index=True) if len(near) else twins
    alpha = check_alpha(m)
    lang = check_lang(m)

    twins.to_csv(OUT / "twins.csv", index=False, encoding="utf-8-sig")
    near.to_csv(OUT / "near.csv", index=False, encoding="utf-8-sig")
    alpha.to_csv(OUT / "alpha.csv", index=False, encoding="utf-8-sig")
    lang.to_csv(OUT / "lang.csv", index=False, encoding="utf-8-sig")
    chk = pairs[pairs["status"] == "check"].reset_index(drop=True)
    chk[["a", "b", "hamming", "kind", "keep"]].assign(decision="").to_csv(OUT / "check_decisions_template.csv", index=False, encoding="utf-8-sig")
    for f in OUT.glob("check_*.jpg"):
        f.unlink()
    pair_sheets(chk, m, "check", font)
    sure = pairs[pairs["status"] == "dup_sure"].reset_index(drop=True)
    for f in OUT.glob("sure_*.jpg"):
        f.unlink()
    pair_sheets(sure, m, "sure", font)
    if len(alpha):
        single_sheet(alpha[alpha["status"] == "suspect"], m, "alpha_suspect.jpg", font)

    lines = [f"# s26 dedup pass report ({pd.Timestamp.now():%Y-%m-%d})", "",
             f"main {len(m)} images; protected (test + pilot) {len(protected)}", "",
             f"A. crop/embedded twins: {len(twins)} pairs — dup_sure {int((twins['status'] == 'dup_sure').sum())}, check {int((twins['status'] == 'check').sum())}; by source {dict(Counter(twins['source']))}",
             f"B. near-duplicates (pHash <= 8, SVG hashed from render) + Wikimedia variants: {len(near)} pairs — {dict(Counter(near['kind'])) if len(near) else {}}; dup_sure {int((near['status'] == 'dup_sure').sum()) if len(near) else 0}",
             f"C. alpha PNGs: {len(alpha)} with transparency, suspect (dark > 50 % on white) {int((alpha['status'] == 'suspect').sum()) if len(alpha) else 0} -> alpha_suspect.jpg, decide broken|keep",
             f"D. Latin-script non-English captions (stopword heuristic): {len(lang)} — {dict(Counter(lang['lang_latin'])) if len(lang) else {}}",
             "", f"would drop from main: {int((pairs['status'] == 'dup_sure').sum())} sure duplicates (+ `check` pairs decided dup, + alpha decided broken)",
             f"protected items among losers: {int(pairs['drop'].isin(protected).sum())} (must be 0)"]
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))

    if a.apply:
        decisions = pd.read_csv(a.decisions, dtype=str, encoding="utf-8-sig").fillna("") if a.decisions else None
        bak = DATA / "triage_final_before_s26.csv"
        if not bak.exists():
            shutil.copy2(DATA / "triage_final.csv", bak)
        df = apply(df, pairs, alpha, decisions, protected)
        df.to_csv(DATA / "triage_final.csv", index=False, encoding="utf-8-sig")
        print("split counts now:", df["split"].value_counts().to_dict())


if __name__ == "__main__":
    main()
