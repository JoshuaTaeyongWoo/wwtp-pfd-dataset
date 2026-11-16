"""
make_flowchart.py — methods flowchart of the collection / triage pipeline in the "vertical boxes + data cylinders
+ zoomed loop panel" style (cf. the BPCI-fouling calibration figure): coloured filled boxes with bold labels,
grey data cylinders, black arrows, dotted connectors to a grey panel that expands the iterative step.

Output: paper/figures/Fig_pipeline_vertical.{png,svg,pdf}
Usage : python make_flowchart.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Ellipse, Rectangle, FancyArrowPatch

plt.rcParams["font.family"] = "Arial"
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# palette (same roles as the example figure)
C = {"green": "#00A651", "yellow": "#FFEB9C", "lgreen": "#C6E0B4", "blue": "#B4C7E7", "navy": "#1F3A93",
     "red": "#E60000", "dred": "#C00000", "orange": "#ED7D31", "peach": "#FBE5D6", "grey": "#D9D9D9",
     "panel": "#D0D0D0", "white": "#F2F2F2", "cyl": "#C8C8C8", "cyan": "#9DC3E6"}

fig, ax = plt.subplots(figsize=(13, 17))
ax.set_xlim(0, 130); ax.set_ylim(0, 170); ax.axis("off")


def box(x, y, w, h, text, fc, tc="black", bold=False, fs=12, ec="none", align="center"):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="square,pad=0", fc=fc, ec=ec, lw=1.2))
    ha = "center" if align == "center" else "left"
    tx = x if align == "center" else x - w / 2 + 1.5
    ax.text(tx, y, text, ha=ha, va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal",
            linespacing=1.25)


def cylinder(x, y, w, h, text, fs=12):
    body = Rectangle((x - w / 2, y - h / 2 + h * 0.12), w, h * 0.76, fc=C["cyl"], ec="black", lw=1.5)
    ax.add_patch(body)
    ax.add_patch(Ellipse((x, y - h / 2 + h * 0.12), w, h * 0.24, fc=C["cyl"], ec="black", lw=1.5))
    ax.add_patch(Ellipse((x, y + h / 2 - h * 0.12), w, h * 0.24, fc="#E6E6E6", ec="black", lw=1.5))
    ax.text(x, y - h * 0.05, text, ha="center", va="center", fontsize=fs, fontweight="bold", linespacing=1.25)


def arrow(x0, y0, x1, y1, style="-|>", lw=1.6, ls="-", color="black"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=16, lw=lw, color=color,
                                 linestyle=ls, shrinkA=0, shrinkB=0))


def diamond(x, y, w, h, text, fs=11):
    ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)], closed=True,
                         fc="#BDD7EE", ec="black", lw=1.2))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, linespacing=1.2)


# ----------------------------------------------------------------- main column (x = 55)
X = 55
cylinder(X, 161, 30, 10, "Source documents\n(6 source types)", fs=11)
box(X, 148, 56, 7, "Candidate discovery", C["green"], tc="white", bold=True, fs=13)
box(X, 136, 56, 10,
    "Official indexes and APIs: Europe PMC (10,323 OA articles),\nOpenAlex (453 OA PDFs), MediaWiki (1,173 files),\nGoogle Patents (300 patents), curated EPA / operator lists",
    C["yellow"], fs=10.5)
box(X, 123, 56, 9,
    "Acquisition of metadata and figure containers:\nJATS XML + figure files (PMC-OA bucket), PDF pages,\nHTML <img>, drawing sheets  →  56,617 figures inspected",
    C["yellow"], fs=10.5)
box(X, 111, 44, 7, "Caption-tier filter (Algorithm 2)", C["lgreen"], bold=False, fs=12.5)
box(X - 15, 100, 26, 8, "T1: whole-plant\ndiagram caption", C["yellow"], fs=11)
box(X + 15, 100, 26, 8, "T2: treatment-related\nschematic caption", C["yellow"], fs=11)
box(X, 86, 56, 13,
    "Provenance record for every file:\n- source, file URL, landing URL, document identifiers\n- licence → tier A (redistributable) / tier B (research only)\n- rights holder, figure label, caption, query, filter rule\n- SHA-256 and perceptual hash (pHash)",
    C["yellow"], fs=10.5, align="left")
box(X, 73, 44, 7, "De-duplication\n(SHA-256 exact; pHash Hamming ≤ 6)", C["blue"], fs=11.5)
box(X, 62.5, 44, 6, "Canonical catalogue (3,114 images)", C["navy"], tc="white", bold=True, fs=12.5)
box(X, 51, 44, 7, "AI-assisted first-pass\nvisual triage", C["blue"], fs=12)
box(X, 38, 56, 10,
    "Human validation and inclusion rules:\n- precision check on random keep / reject samples\n- transparent images re-rendered and re-judged\n- unsure images grouped by reason",
    C["yellow"], fs=10.5, align="left")
box(X, 26, 44, 6, "Split assignment", C["red"], tc="white", bold=True, fs=12.5)
box(X, 13, 60, 8,
    "Main benchmark: 952 images (tier A 747)\nAuxiliary sets: unit-level 233, pictorial 87, other-domain 83;\ncrop pending 99; manual review 89",
    C["dred"], tc="white", bold=True, fs=10.5)

for y0, y1 in [(156, 151.5), (144.5, 141), (131, 127.5), (118.5, 114.5), (82.5 - 3, 76.5), (69.5, 65.5), (59.5, 54.5), (47.5, 43), (33, 29), (23, 17)]:
    arrow(X, y0, X, y1)
# filter -> T1/T2 -> provenance
arrow(X, 107.5, X - 15, 104); arrow(X, 107.5, X + 15, 104)
arrow(X - 15, 96, X - 15, 92.5); arrow(X + 15, 96, X + 15, 92.5)

# ----------------------------------------------------------------- left column: criteria + rules
cylinder(14, 52, 24, 13, "Triage criteria\n(keep / unsure / reject;\ncategory)", fs=10)
box(14, 38, 26, 7, "Inclusion and split rules", C["orange"], tc="white", bold=True, fs=11.5)
box(14, 28.5, 26, 6, "aux_unit, aux_pictorial,\naux_other_domain, crop, review", C["peach"], fs=10)
arrow(14, 45.5, 14, 41.5); arrow(14, 34.5, 14, 31.5)
arrow(27, 26, 33, 26, ls="-")
arrow(26, 51, 33, 51, ls="--")

# ----------------------------------------------------------------- right panel: triage loop
P0, P1 = 86, 128   # panel x-range
ax.add_patch(Rectangle((P0, 20), P1 - P0, 64, fc=C["panel"], ec="black", lw=1.2))
# dotted connectors from the triage box to the panel corners
arrow(77, 54.5, P0, 84, style="-", ls=":", lw=1.3, color="#555555")
arrow(77, 47.5, P0, 20, style="-", ls=":", lw=1.3, color="#555555")
PX = (P0 + P1) / 2
box(PX, 78, 34, 7, "Render 20-image\ncontact sheets", C["white"], fs=11, ec="black")
box(PX, 66, 34, 8, "Vision-LLM agents assign\ndecision in {keep, unsure, reject}\nand category", C["white"], fs=10.5, ec="black")
box(PX, 54, 34, 7, "Merge decisions;\npre-fill review gallery", C["white"], fs=11, ec="black")
diamond(PX, 41, 30, 11, "Human spot-check:\nprecision ≥ 0.9 ?", fs=10.5)
box(PX, 26, 34, 6, "Accepted first-pass decisions", C["white"], fs=11, ec="black")
arrow(PX, 84, PX, 81.5); arrow(PX, 74.5, PX, 70); arrow(PX, 62, PX, 57.5); arrow(PX, 50.5, PX, 46.5); arrow(PX, 35.5, PX, 29)
# "No" loop back to the agents box via the panel's left edge
arrow(PX - 15, 41, P0 + 3, 41, style="-", lw=1.4)
arrow(P0 + 3, 41, P0 + 3, 66, style="-", lw=1.4)
arrow(P0 + 3, 66, PX - 17, 66, lw=1.4)
ax.text(P0 + 5.5, 43.5, "No", fontsize=11, fontstyle="italic", fontweight="bold")
ax.text(PX + 1.5, 32.5, "Yes", fontsize=11, fontstyle="italic", fontweight="bold")
ax.text(P0 + 4, 38.5, "refine\ncriteria", fontsize=8.5, color="#333333", ha="left", va="top", linespacing=1.1)

for ext in ("png", "svg", "pdf"):
    fig.savefig(OUT / f"Fig_pipeline_vertical.{ext}", dpi=300, bbox_inches="tight", facecolor="white")
print("saved", OUT / "Fig_pipeline_vertical.png")
