"""
make_figures.py — Supplementary figures for the dataset-construction pipeline.

  Fig S1  pipeline schematic (sources -> acquisition -> candidate filter -> dedup -> triage -> dataset)
  Fig S2  triage outcome per source (stacked horizontal bars, counts)

Counts are read from data/stats.md / data/triage_stats.md where possible and otherwise from the
constants below (run of 2026-11-16). Output: data_collection/paper/figures/FigS1_pipeline.{pdf,svg,png},
FigS2_triage.{pdf,svg,png}. English + Arial, no titles (lab figure standard; figure_style.py).

Usage: python make_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from figure_style import PASTEL, MUTED, apply_style, figsize, lock_box_aspect, legend_outside  # noqa: E402

DATA = HERE.parent.parent / "data"
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)

# ----------------------------------------------------------------------------- numbers (2026-11-16 run)
SOURCES = [  # label, documents searched, documents used, files downloaded, canonical
    ("Open-access journals\n(PMC OA subset)", "10,323 articles", "56,617 figures screened", 1204, 1185),
    ("Open-access journals\n(OpenAlex, non-PMC)", "453 articles", "187 PDFs read", 332, 307),
    ("US EPA design manuals", "33 reports", "33 PDFs read", 238, 168),
    ("Patent drawings\n(Google Patents)", "300 patents", "189 with drawings", 796, 750),
    ("Wikimedia Commons", "4,702 files", "1,173 title matches", 635, 618),
    ("Korean municipal\noperators", "27 web pages", "20 reachable", 95, 86),
]
TOTAL_DL, TOTAL_CANON, DUP = 3300, 3114, 186
TRIAGE = {"keep": 952, "unsure": 632, "reject": 1530}
TIER_A_KEEP = 747


def load_triage_by_source() -> pd.DataFrame:
    p = DATA / "triage_ai.csv"
    if p.exists():
        df = pd.read_csv(p, dtype=str).fillna("")
        t = pd.crosstab(df["source"], df["decision"]).reindex(columns=["keep", "unsure", "reject"], fill_value=0)
        return t
    return pd.DataFrame({"keep": [307, 170, 87, 334, 36, 18], "unsure": [206, 40, 40, 200, 132, 14],
                         "reject": [672, 97, 41, 216, 450, 54]},
                        index=["europepmc_pmc", "openalex_nonpmc", "epa_manuals", "patents_google",
                               "wikimedia_commons", "korean_municipal"])


# ----------------------------------------------------------------------------- Fig S1: pipeline
def box(ax, x, y, w, h, text, fc, fs=9, bold_first=False, ec="#555555", lw=0.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15",
                                fc=fc, ec=ec, lw=lw))
    if bold_first:
        first, _, rest = text.partition("\n")
        ax.text(x + w / 2, y + h - 0.22, first, ha="center", va="top", fontsize=fs, fontweight="bold")
        ax.text(x + w / 2, y + h - 0.22 - 0.42, rest, ha="center", va="top", fontsize=fs - 1, linespacing=1.25)
    else:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, linespacing=1.25)


def arrow(ax, p, q, lw=1.0, color="#333333"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=10, lw=lw, color=color,
                                 shrinkA=0, shrinkB=0))


def fig_pipeline():
    apply_style(label=12, tick=10, legend=8)
    fig, ax = plt.subplots(figsize=figsize("16:9", long=10))
    ax.set_xlim(0, 33)
    ax.set_ylim(1.6, 17.8)
    ax.axis("off")

    # column x-positions / widths
    cx = {"src": 0.4, "acq": 7.0, "filt": 14.0, "dedup": 20.2, "triage": 24.4, "out": 29.0}
    cw = {"src": 6.0, "acq": 6.4, "filt": 5.6, "dedup": 3.6, "triage": 3.9, "out": 3.5}
    hdr_y = 17.2
    for key, label in [("src", "1  Sources"), ("acq", "2  Acquisition"), ("filt", "3  Candidate filter"),
                       ("dedup", "4  De-duplication"), ("triage", "5  Visual triage"), ("out", "6  Dataset")]:
        ax.text(cx[key] + cw[key] / 2, hdr_y, label, ha="center", va="center", fontsize=10, fontweight="bold")

    # --- sources (stacked)
    src_fc = PASTEL[0]
    n = len(SOURCES)
    top, bottom = 16.3, 3.0
    sh = (top - bottom) / n - 0.25
    src_mid = []
    for i, (name, searched, used, dl, canon) in enumerate(SOURCES):
        y = top - (i + 1) * (sh + 0.25) + 0.25
        box(ax, cx["src"], y, cw["src"], sh, f"{name}\n{searched}  |  {used}", src_fc, fs=8, bold_first=True)
        src_mid.append(y + sh / 2)

    # --- acquisition
    acq_text = ("Honest User-Agent,\nfixed rate limits\n\n"
                "PMC: JATS XML + figure files\nfrom the AWS Open Data bucket\n\n"
                "PDF: caption-anchored page\nextraction (PyMuPDF)\n\n"
                "Web: MediaWiki API,\nGoogle Patents, <img>\n\n"
                "Provenance record per file:\nsource, URLs, licence, caption,\nSHA-256, pHash, timestamp")
    box(ax, cx["acq"], 4.6, cw["acq"], 11.7, acq_text, "#F3F3F3", fs=7.5)
    for ym in src_mid:
        arrow(ax, (cx["src"] + cw["src"], ym), (cx["acq"], min(max(ym, 5.0), 15.9)), lw=0.7)

    # --- candidate filter
    filt_text = ("Literature & EPA: caption rule\n"
                 "  diagram word present AND no\n  exclusion word (unless strong\n  diagram word)\n"
                 "  T1 = plant-level words\n        (WWTP, STP, treatment line ...)\n"
                 "  T2 = treatment words only\n"
                 "Wikimedia: title regex\n"
                 "Patents, municipal: all kept\n"
                 "Licence tier: A = redistributable,\n  B = research-only")
    box(ax, cx["filt"], 4.6, cw["filt"], 11.7, filt_text, PASTEL[1], fs=7.5)
    arrow(ax, (cx["acq"] + cw["acq"], 10.6), (cx["filt"], 10.6))
    ax.text(cx["filt"] + cw["filt"] / 2, 3.95, f"{TOTAL_DL:,} files downloaded", ha="center", va="center", fontsize=8)

    # --- dedup
    dedup_text = ("Exact: SHA-256\n\nNear: pHash\n(64 bit),\nHamming ≤ 6\n\nkeep tier A /\nearliest copy")
    box(ax, cx["dedup"], 6.0, cw["dedup"], 9.0, dedup_text, PASTEL[2], fs=7.5)
    arrow(ax, (cx["filt"] + cw["filt"], 10.6), (cx["dedup"], 10.6))
    ax.text(cx["dedup"] + cw["dedup"] / 2, 5.3, f"{TOTAL_CANON:,} canonical\n({DUP} duplicates)", ha="center", va="top", fontsize=8)

    # --- triage
    tri_text = ("Contact sheets\n20 thumbnails\n\nVision-LLM\nfirst pass\n(criteria:\nkeep / unsure /\nreject)\n\nHuman spot\ncheck + review")
    box(ax, cx["triage"], 6.0, cw["triage"], 9.0, tri_text, PASTEL[3], fs=7.5)
    arrow(ax, (cx["dedup"] + cw["dedup"], 10.6), (cx["triage"], 10.6))
    ax.text(cx["triage"] + cw["triage"] / 2, 5.3, "keep precision ≈ 0.90\n(30-image sample)", ha="center", va="top", fontsize=8)

    # --- outputs
    oy = [12.4, 9.4, 6.4]
    labels = [f"keep\n{TRIAGE['keep']:,}\n(tier A {TIER_A_KEEP})", f"unsure\n{TRIAGE['unsure']:,}", f"reject\n{TRIAGE['reject']:,}"]
    fcs = [PASTEL[4], PASTEL[5], "#E0E0E0"]
    for y, lab, fc in zip(oy, labels, fcs):
        box(ax, cx["out"], y, cw["out"], 2.4, lab, fc, fs=8)
        arrow(ax, (cx["triage"] + cw["triage"], 10.6), (cx["out"], y + 1.2), lw=0.8)

    # --- bottom band: caption-tier precision
    ax.text(cx["acq"] + (cx["triage"] + cw["triage"] - cx["acq"]) / 2, 2.4,
            "Caption rule precision after triage (literature): T1 0.55 (n = 429), T2 0.23 (n = 972)",
            ha="center", va="center", fontsize=8, style="italic")
    for ext in ("pdf", "svg", "png"):
        fig.savefig(OUT / f"FigS1_pipeline.{ext}")
    plt.close(fig)


# ----------------------------------------------------------------------------- Fig S2: triage per source
def fig_triage():
    apply_style(label=12, tick=10, legend=9)
    t = load_triage_by_source()
    order = ["europepmc_pmc", "patents_google", "wikimedia_commons", "openalex_nonpmc", "epa_manuals", "korean_municipal"]
    names = {"europepmc_pmc": "OA journals (PMC)", "patents_google": "Patent drawings", "wikimedia_commons": "Wikimedia Commons",
             "openalex_nonpmc": "OA journals (non-PMC)", "epa_manuals": "US EPA manuals", "korean_municipal": "Korean municipal"}
    t = t.reindex(order)
    fig, ax = plt.subplots(figsize=figsize("4:3"))
    left = pd.Series(0, index=t.index)
    colors = {"keep": PASTEL[4], "unsure": PASTEL[5], "reject": "#D9D9D9"}
    for col in ["keep", "unsure", "reject"]:
        ax.barh([names[i] for i in t.index], t[col], left=left, color=colors[col], label=col)
        for i, (v, l) in enumerate(zip(t[col], left)):
            if v >= 60:
                ax.text(l + v / 2, i, f"{v:,}", ha="center", va="center", fontsize=8)
        left = left + t[col]
    ax.set_xlabel("Canonical candidate images (count)")
    ax.set_xlim(0, 1300)
    ax.invert_yaxis()
    lock_box_aspect(ax, "4:3")
    legend_outside(ax)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(OUT / f"FigS2_triage.{ext}")
    plt.close(fig)


if __name__ == "__main__":
    fig_pipeline()
    fig_triage()
    print("written to", OUT)
