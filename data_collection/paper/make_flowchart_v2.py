"""
make_flowchart_v2.py — methods overview figure, journal style.

Design choices (after Nature/Science/Water Research methods figures):
  * strict top-down flow in three stage bands (Harvesting -> Curation -> Triage & splits), each with a numbered chip
  * muted, colour-blind-safe palette; colour is used only to encode *role* (source type, automated step,
    human step, data product) — not decoration
  * rounded white process boxes with thin borders; data products as filled boxes; one accent per stage
  * the data funnel (56,617 -> 3,300 -> 3,114 -> 952) runs as number callouts on the left margin
  * the AI-triage loop drawn as a compact cycle with a decision diamond, not a separate zoom panel
  * final splits drawn as a proportional stacked bar so the reader sees the outcome at a glance
Output: paper/figures/Fig1_pipeline_v2.{png,svg,pdf}   (180 mm wide, double-column)
Usage : python make_flowchart_v2.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle, FancyArrowPatch, Circle

plt.rcParams["font.family"] = "Arial"
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- palette (role-coded, muted)
INK = "#1F2933"          # text
LINE = "#52606D"         # borders / arrows
PANEL = "#F5F7FA"        # stage band fill
PANEL_EC = "#CBD2D9"
CHIP = "#323F4B"         # stage number chip
AUTO = "#2F6F9F"         # automated computation (blue)
HUMAN = "#C77A1F"        # human-in-the-loop step (amber)
DATA = "#1E7F6B"         # data product (teal)
FINAL = "#2E7D32"        # final benchmark (green)
SRC = {"lit": "#5B7DB1", "doc": "#7A9E7E", "web": "#B0866B", "wiki": "#8E7CC3", "pat": "#A05A6E"}
GREY = "#9AA5B1"

W, H = 180, 236
fig = plt.figure(figsize=(W / 25.4, H / 25.4))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")


# ---------------------------------------------------------------- primitives
def rbox(x, y, w, h, text="", fc="white", ec=LINE, tc=INK, fs=7.2, bold=False, lw=0.8, r=1.8, align="center", ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, ls=ls))
    if text:
        if align == "center":
            ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc,
                    fontweight="bold" if bold else "normal", linespacing=1.25)
        else:
            ax.text(x + 2.2, y + h / 2, text, ha="left", va="center", fontsize=fs, color=tc,
                    fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(x0, y0, x1, y1, color=LINE, lw=0.9, style="-|>", ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=9, lw=lw, color=color,
                                 ls=ls, shrinkA=0, shrinkB=0, connectionstyle=f"arc3,rad={rad}"))


def chip(x, y, n, label):
    ax.add_patch(Circle((x, y), 3.2, fc=CHIP, ec="none"))
    ax.text(x, y, str(n), ha="center", va="center", fontsize=8, color="white", fontweight="bold")
    ax.text(x + 4.5, y, label, ha="left", va="center", fontsize=8.5, color=CHIP, fontweight="bold")


def callout(x, y, big, small):
    ax.text(x, y + 1.6, big, ha="center", va="center", fontsize=9.5, color=INK, fontweight="bold")
    ax.text(x, y - 2.2, small, ha="center", va="center", fontsize=5.8, color=LINE, linespacing=1.15)


def diamond(cx, cy, w, h, text, fs=6.4):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], closed=True,
                         fc="#FFF4E0", ec=HUMAN, lw=0.9))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.15)


def doc_icon(x, y, color):
    """small document glyph"""
    ax.add_patch(Polygon([(x, y), (x + 3.2, y), (x + 4.4, y + 1.2), (x + 4.4, y + 5.4), (x, y + 5.4)], closed=True,
                         fc="white", ec=color, lw=0.8))
    for k in range(3):
        ax.plot([x + 0.8, x + 3.6], [y + 1.3 + k * 1.2] * 2, color=color, lw=0.5)


# ---------------------------------------------------------------- stage bands
bands = {1: (150, 232), 2: (112, 146), 3: (6, 108)}
for n, (y0, y1) in bands.items():
    ax.add_patch(FancyBboxPatch((22, y0), 154, y1 - y0, boxstyle="round,pad=0,rounding_size=3", fc=PANEL, ec=PANEL_EC, lw=0.8))
chip(27.5, 228, 1, "Harvesting with provenance")
chip(27.5, 142, 2, "Curation")
chip(27.5, 104, 3, "Visual triage and split assignment")

# ---------------------------------------------------------------- stage 1: sources
srcs = [("Open-access\nliterature", "Europe PMC → PMC-OA\nbucket; OpenAlex PDFs", SRC["lit"]),
        ("Public agency\ndocuments", "US EPA design manuals\n(NEPIS, epa.gov)", SRC["doc"]),
        ("Operator\nweb pages", "Korean municipal\nWWTP sites", SRC["web"]),
        ("Wikimedia\nCommons", "MediaWiki API,\nmultilingual queries", SRC["wiki"]),
        ("Patent\ndrawings", "Google Patents,\nCPC C02F3/9/11", SRC["pat"])]
sx0, sw, sg = 30, 27, 2.6
for i, (t, sub, col) in enumerate(srcs):
    x = sx0 + i * (sw + sg)
    rbox(x, 206, sw, 16.5, fc="white", ec=PANEL_EC, lw=0.7)
    ax.add_patch(Rectangle((x, 220.4), sw, 2.1, fc=col, ec="none"))   # colour strip
    doc_icon(x + 2, 214.2, col)
    ax.text(x + 7.5, 217.6, t, ha="left", va="center", fontsize=6.6, color=INK, fontweight="bold", linespacing=1.15)
    ax.text(x + 1.8, 209.6, sub, ha="left", va="center", fontsize=5.3, color=LINE, linespacing=1.15)
    arrow(x + sw / 2, 206, x + sw / 2, 201.5)

# discovery / acquisition
rbox(30, 193, 146, 8.5, "Candidate discovery through official indexes and APIs (identifying User-Agent, fixed rate limits; no access-control circumvention)", fs=6.6)
arrow(103, 193, 103, 188.5)
rbox(30, 176.5, 70, 12, "Acquisition of metadata and figure containers\nJATS XML + figure files, PDF pages, HTML <img>,\ndrawing sheets", fs=6.3)
rbox(106, 176.5, 70, 12, "Caption-tier filter (Algorithm 2)\nT1 whole-plant caption · T2 treatment-related\ncaption · otherwise not downloaded", fs=6.3, fc="#EAF1F8", ec=AUTO)
arrow(100, 182.5, 106, 182.5)
arrow(65, 176.5, 65, 171.5); arrow(141, 176.5, 141, 171.5)
rbox(30, 155, 146, 16.5, fc="white", ec=DATA, lw=0.9)
ax.text(32.5, 169, "Provenance record  (one per file, append-only JSONL)", fontsize=6.8, color=DATA, fontweight="bold", va="center")
ax.text(32.5, 161.5, "source · document identifiers · file URL · landing URL · rights holder · figure label · caption · query · filter rule\n"
        "licence → tier A (CC0 / CC BY / CC BY-SA / public domain / patent: redistributable) or tier B (NC / ND / unknown: research only)\n"
        "SHA-256 (exact duplicates) · 64-bit perceptual hash (near duplicates) · acquisition time and method",
        fontsize=5.8, color=INK, va="center", linespacing=1.35)

# ---------------------------------------------------------------- stage 2
rbox(30, 126, 70, 12, "De-duplication\nSHA-256 identity, then pHash Hamming distance ≤ 6;\ncanonical = tier A first, then earliest acquisition", fs=6.3, fc="#EAF1F8", ec=AUTO)
arrow(100, 132, 106, 132)
rbox(106, 126, 70, 12, "Canonical catalogue\n3,114 images from 1,877 documents\n(catalog.csv · provenance/*.jsonl)", fs=6.5, fc=DATA, ec=DATA, tc="white", bold=True)
arrow(103, 150, 65, 150, style="-"); arrow(65, 150, 65, 138)

# ---------------------------------------------------------------- stage 3: triage loop
arrow(141, 126, 141, 112); arrow(141, 112, 65, 112, style="-"); arrow(65, 112, 65, 98)
rbox(30, 86, 70, 12, "Contact-sheet rendering\n20 thumbnails per sheet, numbered; transparent\nimages composited on white", fs=6.3)
arrow(65, 86, 65, 80)
rbox(30, 68, 70, 12, "Vision-LLM first pass (7 parallel agents)\ndecision: keep / unsure / reject;\ncategory: wwtp / sludge / wtp / pilot / other", fs=6.3, fc="#EAF1F8", ec=AUTO)
arrow(65, 68, 65, 62)
diamond(65, 52, 40, 15, "Human spot-check\nprecision ≥ target?")
ax.text(84, 53.5, "yes", fontsize=6, color=HUMAN, fontstyle="italic", fontweight="bold")
ax.text(44, 54, "no", fontsize=6, color=HUMAN, fontstyle="italic", fontweight="bold")
# "no" loop: left side back to criteria
arrow(45, 52, 36, 52, style="-", color=HUMAN); arrow(36, 52, 36, 74, style="-", color=HUMAN); arrow(36, 74, 30, 74, color=HUMAN, style="-")
rbox(23.5, 70, 6.5, 8, "", fc="#FFF4E0", ec=HUMAN, lw=0.8)
ax.text(26.75, 74, "refine\ncriteria", ha="center", va="center", fontsize=4.6, color=HUMAN, rotation=90, linespacing=1.1)
arrow(85, 52, 106, 52)
rbox(106, 46, 70, 12, "Human validation and inclusion rules\nkeep precision ≈ 0.90 on a random sample; 0 missed\nin the reject sample; unsure grouped by reason", fs=6.3, fc="#FFF4E0", ec=HUMAN)
arrow(141, 46, 141, 40)
rbox(106, 28, 70, 12, "Split assignment and cropping\nmain · aux_unit · aux_pictorial · aux_other_domain ·\ncrop_pending → main after manual crop · manual_review", fs=6.3, fc="#FFF4E0", ec=HUMAN)
arrow(141, 28, 141, 23)

# outcome as a proportional stacked bar (3,114 canonical images)
segs = [("Main benchmark 993", 993, FINAL), ("Crop pending 99", 99, "#66BB6A"), ("Auxiliary sets 403", 403, DATA),
        ("Manual review 33", 33, HUMAN), ("Excluded 1,621", 1621, GREY)]
bx, bw, by, bh = 30, 146, 16, 6.5
tot = sum(s[1] for s in segs); cur = bx; k_small = 0
for label, n, col in segs:
    w = bw * n / tot
    ax.add_patch(Rectangle((cur, by), w, bh, fc=col, ec="white", lw=0.6))
    if w > 22:
        ax.text(cur + w / 2, by + bh / 2, label, ha="center", va="center", fontsize=5.8,
                color="white" if col != GREY else INK, fontweight="bold")
    else:  # small segment: label below with a leader line, staggered
        yy = by - 3.2 - 3.4 * (k_small % 2); k_small += 1
        ax.plot([cur + w / 2, cur + w / 2], [by, yy + 1.2], color=col, lw=0.6)
        ax.text(cur + w / 2, yy, label, ha="center", va="center", fontsize=5.4, color=col, fontweight="bold")
    cur += w
ax.text(bx, by + bh + 1.6, "Outcome (3,149 images incl. 35 crops)  ·  main benchmark: 776 of 993 redistributable (tier A)",
        fontsize=6, color=INK, va="bottom")

# ---------------------------------------------------------------- left margin: data funnel callouts
ax.plot([11, 11], [20, 226], color=PANEL_EC, lw=1.0)
for y, big, small in [(214, "6", "source\ntypes"), (182, "56,617", "figures\ninspected"), (160, "3,300", "files with\nprovenance"),
                      (132, "3,114", "canonical\nimages"), (52, "1,584", "keep +\nunsure"), (16, "993", "main\nbenchmark")]:
    ax.add_patch(Circle((11, y), 1.3, fc=CHIP, ec="none"))
    callout(11, y + 6.5, big, small)

# ---------------------------------------------------------------- legend
lx, ly = 96, 232.5
for i, (lab, fc, ec) in enumerate([("automated step", "#EAF1F8", AUTO), ("human-in-the-loop step", "#FFF4E0", HUMAN),
                                   ("data product", DATA, DATA)]):
    x = lx + [0, 24, 58][i]
    ax.add_patch(FancyBboxPatch((x, ly - 1.2), 3.2, 2.4, boxstyle="round,pad=0,rounding_size=0.5", fc=fc, ec=ec, lw=0.7))
    ax.text(x + 4, ly, lab, fontsize=5.6, va="center", color=INK)

for ext in ("png", "svg", "pdf"):
    fig.savefig(OUT / f"Fig1_pipeline_v2.{ext}", dpi=400, facecolor="white")
print("saved", OUT / "Fig1_pipeline_v2.png")
