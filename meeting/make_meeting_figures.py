"""
make_meeting_figures.py — figures for the 2026-11-19 advisor meeting document (meeting/figures/*.png).
Data: data/triage_final.csv, data/pilot/pilot60.csv, evidence ledger D-01/D-03, annotation/classes.yaml.
Style: Arial, English labels, no in-figure titles, pastel categorical palette.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "meeting" / "figures"; FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "Arial", "font.size": 10, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
                     "legend.fontsize": 9.5, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 200, "savefig.dpi": 200})
PASTEL = ["#7FB3D5", "#F5B7B1", "#A9DFBF", "#F9E79F", "#D7BDE2", "#F8C471", "#AED6F1", "#A3E4D7"]
GREY = "#8A9BA8"

SRC = {"patents_google": "Patents (US/KR/CN)", "europepmc_pmc": "PMC OA papers", "openalex_nonpmc": "Other OA papers", "epa_manuals": "US EPA manuals",
       "wikimedia_commons": "Wikimedia Commons", "korean_municipal": "Korean municipal"}


def fig_sources():
    d = pd.read_csv(ROOT / "data" / "triage_final.csv", dtype=str, encoding="utf-8-sig").fillna("")
    d["grp"] = d["split"].map(lambda s: "main" if s == "main" else ("aux / crop pending" if s.startswith("aux") or s == "crop_pending" or s == "manual_review" else "excluded"))
    ct = pd.crosstab(d["source"], d["grp"]).reindex(list(SRC)).fillna(0)[["main", "aux / crop pending", "excluded"]]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axes[0]
    left = [0] * len(ct)
    for col, c in zip(ct.columns, [PASTEL[0], PASTEL[3], "#D5DBDB"]):
        ax.barh([SRC[s] for s in ct.index], ct[col], left=left, color=c, label=col, edgecolor="white")
        left = [l + v for l, v in zip(left, ct[col])]
    for y, (s, row) in enumerate(ct.iterrows()):
        ax.text(row.sum() + 8, y, f"{int(row['main'])} main / {int(row.sum())}", va="center", fontsize=9, color="#333")
    ax.invert_yaxis(); ax.set_xlabel("records after de-duplication (n = 3,273)"); ax.legend(loc="lower right", frameon=False)
    ax.set_xlim(0, ct.sum(axis=1).max() * 1.35)
    ax = axes[1]
    m = d[d["split"] == "main"]
    cat = m["category"].value_counts()
    labels = {"wwtp": "whole-plant WWTP", "pilot": "pilot / lab train", "sludge": "sludge line", "other": "other", "wtp": "water treatment"}
    wedges, _ = ax.pie(cat.values, colors=PASTEL[:5], startangle=90, counterclock=False, wedgeprops={"width": 0.45, "edgecolor": "white"})
    ax.legend(wedges, [f"{labels[k]}  {v}" for k, v in cat.items()], loc="lower center", bbox_to_anchor=(0.5, -0.22), frameon=False, ncol=2, fontsize=8.5)
    ax.text(0, 0, "main\n993", ha="center", va="center", fontsize=11, fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG / "fig_sources.png"); plt.close(fig)


def fig_visual_form():
    forms = ["A box-form\n(text names the unit)", "B symbol\n(ISO 10628-like)", "C pictorial\n(3-D / icons)", "D simulator\nscreenshot", "E page render\n(needs crop)"]
    sample40 = [40, 28, 22, 5, 12.5]      # D-01, 40 random main images, multi-label
    pilot60 = [48, 35, 15, 2, 0]           # pilot 60 (E excluded by design)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    x = range(len(forms)); w = 0.38
    ax.bar([i - w / 2 for i in x], sample40, w, color=PASTEL[0], label="random sample of main (n = 40, multi-label)")
    ax.bar([i + w / 2 for i in x], pilot60, w, color=PASTEL[2], label="pilot sample (n = 60)")
    for i, (a, b) in enumerate(zip(sample40, pilot60)):
        ax.text(i - w / 2, a + 1, f"{a:g}%", ha="center", fontsize=9); ax.text(i + w / 2, b + 1, f"{b:g}%", ha="center", fontsize=9)
    ax.set_xticks(list(x)); ax.set_xticklabels(forms, fontsize=9); ax.set_ylabel("share of images (%)"); ax.set_ylim(0, 58)
    ax.legend(frameon=False, loc="upper right")
    ax.annotate("shape carries no class information:\nthe unit is identified by its text", xy=(0.15, 48), xytext=(1.0, 42), fontsize=9, color="#C0392B",
                arrowprops={"arrowstyle": "->", "color": "#C0392B"})
    fig.tight_layout(); fig.savefig(FIG / "fig_visual_form.png"); plt.close(fig)


def fig_term_freq():
    terms = [("Aeration tank / bioreactor / oxidation ditch", 264), ("MBR", 83), ("Anoxic / anaerobic zone, nitrif./denitrif.", 75), ("Tank / storage", 67),
             ("Recycle (RAS / WAS / internal)", 60), ("Sand / media filtration", 40), ("Biofilm (TF, MBBR, RBC)", 38), ("Digester", 38), ("Disinfection (UV / Cl / O3)", 34),
             ("Pump / pump station", 33), ("UASB / anaerobic reactor", 32), ("Membrane (UF / RO / NF)", 28), ("DAF / flotation", 27), ("Instrument / control", 26),
             ("Screen", 24), ("Primary clarifier", 19), ("Dewatering", 19), ("SBR", 18), ("Wetland / pond", 17), ("Coagulation chemicals", 16),
             ("Biogas / CHP", 16), ("Secondary clarifier", 14), ("Grit chamber", 12), ("Blower", 12), ("Equalization", 10), ("Thickener", 9),
             ("Drying / incineration", 9), ("Heat exchanger", 1)]
    fig, ax = plt.subplots(figsize=(8, 6.2))
    names = [t for t, _ in terms][::-1]; vals = [v for _, v in terms][::-1]
    colors = [PASTEL[1] if n == "Heat exchanger" else PASTEL[0] for n in names]
    ax.barh(names, vals, color=colors)
    for i, v in enumerate(vals):
        ax.text(v + 2, i, str(v), va="center", fontsize=8.5)
    ax.set_xlabel("captions mentioning the term (main, n = 993; regex count, under-counts units absent from captions)")
    ax.annotate("core of chemical-engineering PFDs\n(heat exchangers, columns, compressors)\nalmost absent here", xy=(1, 0), xytext=(90, 2.5), fontsize=9, color="#C0392B",
                arrowprops={"arrowstyle": "->", "color": "#C0392B"})
    ax.tick_params(axis="y", labelsize=8.5)
    fig.tight_layout(); fig.savefig(FIG / "fig_term_freq.png"); plt.close(fig)


def fig_taxonomy_tree():
    tx = yaml.safe_load((ROOT / "data_collection" / "annotation" / "classes.yaml").read_text(encoding="utf-8"))
    l1_order = [("preliminary", "Preliminary"), ("primary", "Primary"), ("separation", "Separation\n(position-free)"), ("secondary", "Biological\n(secondary)"),
                ("sidestream", "Sidestream"), ("tertiary", "Tertiary /\ndisinfection"), ("sludge", "Sludge line"), ("ancillary", "Ancillary"), ("generic", "Generic /\nunknown")]
    groups = {k: [] for k, _ in l1_order}
    for name, c in tx["classes"].items():
        l3 = (c.get("l3") or {}).get("required") or []
        groups[c["l1"]].append(name + (f"  (/{len(l3)} sub-types)" if l3 else ""))
    conn = ["io_terminal", "junction_split", "junction_merge", "instrument", "arrowhead", "text_label", "stream_tag", "stream_label"]
    cols = [(t, groups[k], PASTEL[i % len(PASTEL)]) for i, (k, t) in enumerate(l1_order)] + [("Connection &\nannotation", conn, "#D5DBDB")]
    weights = [1.0, 1.0, 1.25, 1.9, 1.0, 1.0, 1.3, 1.2, 1.2, 1.0]
    fig, ax = plt.subplots(figsize=(15, 5.4)); ax.axis("off")
    tot = sum(weights); x = 0.0
    for (title, items, color), wgt in zip(cols, weights):
        cw = wgt / tot
        ax.add_patch(FancyBboxPatch((x + 0.004, 0.86), cw - 0.008, 0.10, boxstyle="round,pad=0.004", fc=color, ec="none", transform=ax.transAxes))
        ax.text(x + cw / 2, 0.91, f"{title} ({len(items)})", ha="center", va="center", fontsize=8.2, fontweight="bold", transform=ax.transAxes, linespacing=1.1)
        for j, it in enumerate(items):
            ax.text(x + 0.008, 0.80 - j * 0.073, it, fontsize=7.4, va="center", transform=ax.transAxes, family="Consolas")
        ax.plot([x + cw / 2] * 2, [0.86, 0.835], color=GREY, lw=0.8, transform=ax.transAxes)
        x += cw
    ax.text(0.5, 1.0, "L1: 7 process stages (+ ancillary, generic)      L2: 33 unit-process classes (31 + 2 generic)      L3 sub-types where the simulator model differs", ha="center", va="bottom", fontsize=9.5, transform=ax.transAxes, color="#333")
    fig.tight_layout(); fig.savefig(FIG / "fig_taxonomy_tree.png"); plt.close(fig)


def _box(ax, x, y, w, h, text, fc, fs=8.8, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01", fc=fc, ec="#5D6D7E", lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.25)


def _arrow(ax, p, q, color="#5D6D7E", style="-|>"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=12, color=color, lw=1.1))


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(13.5, 5.6)); ax.set_xlim(0, 13.5); ax.set_ylim(0, 5.6); ax.axis("off")
    # row 1: benchmark construction
    steps = [("1. Collection\n6 sources, 3,273 records\n(s01–s07)", PASTEL[0]), ("2. Screening\nAI-assisted + human\nmain 993 (s08–s11, s16)", PASTEL[0]),
             ("3. Taxonomy v1.1\n33 classes, 22 rules\nfrozen (git tag)", PASTEL[2]), ("4. Pilot annotation\n60 images x 2 annotators\nLabel Studio, remote", PASTEL[3]),
             ("5. Agreement & adjudication\nkappa, edge F1 (s17)\nguideline v2", PASTEL[3]), ("6. Main annotation\nindividual accounts\nlab server", PASTEL[3])]
    for i, (t, c) in enumerate(steps):
        _box(ax, 0.2 + i * 2.22, 4.2, 2.0, 1.1, t, c)
        if i < len(steps) - 1:
            _arrow(ax, (0.2 + i * 2.22 + 2.0, 4.75), (0.2 + (i + 1) * 2.22, 4.75))
    ax.text(0.2, 5.45, "Benchmark construction (done through step 4 setup; 5–6 pending)", fontsize=9.5, color="#333", fontweight="bold")
    # row 2: GT + evaluation
    _box(ax, 3.0, 2.35, 2.6, 1.0, "Ground truth\nCOCO (L2 + attributes)\n+ graph.json per image (s22)", PASTEL[2])
    _box(ax, 6.4, 2.35, 2.8, 1.0, "Evaluation (s23, plan §6)\nAP L2/L1, LVIS buckets, strata\nedge P/R/F1, direction, GED", PASTEL[2])
    ax.plot([11.3, 11.3, 4.3], [4.2, 3.8, 3.8], color="#5D6D7E", lw=1.1); _arrow(ax, (4.3, 3.8), (4.3, 3.37))
    _arrow(ax, (5.6, 2.85), (6.4, 2.85))
    _box(ax, 9.9, 2.35, 3.4, 1.0, "Downstream round-trip\npredicted graph -> QSDsan flowsheet\n(GPS-X / SUMO as secondary)", PASTEL[7])
    _arrow(ax, (9.2, 2.85), (9.9, 2.85))
    ax.text(3.0, 3.5, "Ground truth and scoring (built and verified on a synthetic dry run)", fontsize=9.5, color="#333", fontweight="bold")
    # row 3: models
    models = [("VLM zero-shot\n(Claude, no training)\n= no-label baseline", "#D5DBDB"), ("Faster R-CNN R50-FPN\n(Theisen 2023 reproduction)\nlocal training", PASTEL[4]),
              ("Modern detector\n(YOLO / DETR family)\nlocal training", PASTEL[4]), ("Graph recovery\npixel search (Theisen) vs learned\n+ rule-based medium (s19)", PASTEL[4]),
              ("Human upper bound\n(annotator agreement)", PASTEL[1])]
    for i, (t, c) in enumerate(models):
        _box(ax, 0.2 + i * 2.7, 0.35, 2.5, 1.05, t, c, fs=8.4)
        _arrow(ax, (0.2 + i * 2.7 + 1.25, 1.4), (7.8 - 0.0 if False else min(max(0.2 + i * 2.7 + 1.25, 6.5), 9.1), 2.35), color="#95A5A6")
    ax.text(0.2, 1.6, "Models scored on the same test split and metrics (local models are the deliverable; the VLM only sets the no-label floor)", fontsize=9.5, color="#333", fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG / "fig_pipeline.png"); plt.close(fig)


def fig_pilot_alloc():
    rows = [("patents_google", 342, 16, 11), ("europepmc_pmc", 325, 16, 0), ("openalex_nonpmc", 178, 11, 1), ("epa_manuals", 90, 8, 0), ("wikimedia_commons", 36, 5, 1), ("korean_municipal", 22, 4, 4)]
    fig, ax = plt.subplots(figsize=(8, 3.2))
    names = [SRC[r[0]] for r in rows]; x = range(len(rows)); w = 0.4
    ax.bar([i - w / 2 for i in x], [r[2] for r in rows], w, color=PASTEL[0], label="drawn (sqrt allocation, 60 total)")
    ax.bar([i + w / 2 for i in x], [r[3] for r in rows], w, color=PASTEL[1], label="of which non-English labels")
    for i, r in enumerate(rows):
        ax.text(i - w / 2, r[2] + 0.3, str(r[2]), ha="center", fontsize=9); ax.text(i + w / 2, r[3] + 0.3, str(r[3]), ha="center", fontsize=9)
        ax.text(i, -3.2, f"main {r[1]}", ha="center", fontsize=8, color=GREY)
    ax.set_xticks(list(x)); ax.set_xticklabels(names, fontsize=8.5); ax.set_ylabel("images"); ax.set_ylim(0, 20); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(FIG / "fig_pilot_alloc.png"); plt.close(fig)


def fig_timeline():
    import datetime as dt
    items = [("2026-11-12", "2026-11-16", "Collection, screening, catalog", PASTEL[0], True),
             ("2026-11-14", "2026-11-16", "Taxonomy v1.1 (3 reviews) -> freeze", PASTEL[2], True),
             ("2026-11-16", "2026-11-19", "Pilot package: sample, tools, manuals, training", PASTEL[3], True),
             ("2026-11-19", "2026-11-19", "Pipeline dry run, evaluation code, VLM baseline", PASTEL[2], True),
             ("2026-11-20", "2026-11-26", "Pilot labelling (2 annotators, 60 images)", PASTEL[3], False),
             ("2026-11-27", "2026-12-03", "Agreement, adjudication, guideline v2", PASTEL[3], False),
             ("2026-12-04", "2026-12-31", "Main annotation (lab server, individual accounts)", PASTEL[3], False),
             ("2026-12-08", "2027-01-15", "Baselines: VLM, Faster R-CNN, modern detector, graph", PASTEL[4], False),
             ("2027-01-05", "2027-01-31", "QSDsan round-trip, datasheet, manuscript draft", PASTEL[7], False)]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    t0 = dt.date(2026, 11, 10)
    for i, (a, b, lab, c, done) in enumerate(items):
        da, db = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
        ax.barh(i, max((db - da).days, 1), left=(da - t0).days, color=c, edgecolor="#5D6D7E" if done else "none", hatch=None if done else "//", alpha=1 if done else 0.75)
        ax.text((db - t0).days + 1.5, i, lab, va="center", fontsize=8.8)
    ax.axvline((dt.date(2026, 11, 19) - t0).days, color="#C0392B", lw=1, ls="--"); ax.text((dt.date(2026, 11, 19) - t0).days + 0.5, len(items) - 0.4, "today", color="#C0392B", fontsize=8.5)
    ticks = [dt.date(2026, 11, 10), dt.date(2026, 11, 20), dt.date(2026, 12, 1), dt.date(2026, 12, 15), dt.date(2027, 1, 1), dt.date(2027, 1, 15), dt.date(2027, 2, 1)]
    ax.set_xticks([(t - t0).days for t in ticks]); ax.set_xticklabels([t.strftime("%b %d") for t in ticks], fontsize=8.5)
    ax.set_yticks([]); ax.invert_yaxis(); ax.set_xlim(0, 100)
    ax.text(60, len(items) - 0.4, "solid = done, hatched = proposed", fontsize=8.5, color=GREY)
    fig.tight_layout(); fig.savefig(FIG / "fig_timeline.png"); plt.close(fig)


if __name__ == "__main__":
    for f in (fig_sources, fig_visual_form, fig_term_freq, fig_taxonomy_tree, fig_pipeline, fig_pilot_alloc, fig_timeline):
        f(); print("saved", f.__name__)
