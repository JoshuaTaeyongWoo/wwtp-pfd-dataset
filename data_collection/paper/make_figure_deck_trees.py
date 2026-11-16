"""
make_figure_deck_trees.py — adds two "algorithm tree" slides (top-down) to the figure deck and writes the 5-slide file.

  Slide 4  Style D "Hierarchical tree" — org-chart layout: root → three stages → step leaves; the screening decision
                                         branches into keep / unsure / reject and their subsets (monochrome slate)
  Slide 5  Style E "Decision tree"     — the path of one candidate figure: caption tests (diamonds) → provenance →
                                         duplicate test → visual screening → uncertainty reasons → subsets (teal / amber)

Output: paper/Fig_pipeline_styles.pptx (slides 1-3 from make_figure_deck.py + slides 4-5)
Usage : python make_figure_deck_trees.py
"""
from __future__ import annotations

from make_figure_deck import Canvas, OUT, blank, new_prs, slide_note, style_a, style_b, style_c


# =============================================================================== STYLE D — hierarchical tree
def style_d(prs):
    s = blank(prs); c = Canvas(s)
    INK, LINE = "1F2933", "7B8794"
    L0, L1, L2, L3 = "263238", "37474F", "FFFFFF", "ECEFF1"
    ACC = {"keep": "2E7D32", "unsure": "C77A1F", "reject": "9AA5B1"}
    c.text(0.5, 0.25, 6.5, 0.3, "Algorithm tree: collection and screening of treatment-plant process diagrams", fs=10, bold=True, color=INK)
    root = (3.75, 0.95)
    c.box(root[0] - 1.9, root[1] - 0.25, 3.8, 0.5, "Provenance-tracked collection and screening", fill=L0, line=None, fs=8.5, bold=True, color="FFFFFF", radius=0.08, name="root")
    stages = [("1  Harvest", 1.35), ("2  Curate", 3.75), ("3  Screen and assign", 6.15)]
    sy = 1.95
    c.arrow(root[0], root[1] + 0.25, root[0], 1.55, head=False, color=LINE)
    c.arrow(stages[0][1], 1.55, stages[2][1], 1.55, head=False, color=LINE)
    for name, x in stages:
        c.arrow(x, 1.55, x, sy - 0.2, color=LINE)
        c.box(x - 1.05, sy - 0.2, 2.1, 0.4, name, fill=L1, line=None, fs=8, bold=True, color="FFFFFF", radius=0.06, name=name.strip())
    leaves = {
        0: ["Query official indexes and APIs of five source types", "Retrieve metadata and figure containers (XML, PDF, web images, patent sheets)",
            "Caption screening: tier T1 (whole-plant) or T2 (treatment-related), else not downloaded", "Write one provenance record per file: identifiers, URLs, licence tier, SHA-256, pHash"],
        1: ["Merge identical files (same SHA-256)", "Merge near-identical copies (pHash distance ≤ 6 bits)", "Keep the redistributable copy as the unique image",
            "Unique catalogue: 3,114 images from 1,877 documents"],
        2: ["Render 20-image contact sheets", "Visual screening: keep / unsure / reject + category", "Quality check on random samples; revise criteria until precision ≥ 0.90",
            "Assign subsets; crop multi-panel figures and page scans"],
    }
    ly0, lh, lg = 2.75, 0.52, 0.12
    for k, (name, x) in enumerate(stages):
        bus = x - 1.05 + 0.12; bx = x - 1.05 + 0.25
        c.arrow(bus, sy + 0.2, bus, ly0 + 3 * (lh + lg) + lh / 2, head=False, color=LINE)
        for i, t in enumerate(leaves[k]):
            y = ly0 + i * (lh + lg)
            c.arrow(bus, y + lh / 2, bx, y + lh / 2, head=False, color=LINE)
            last = (k == 1 and i == 3)
            c.box(bx, y, 1.85, lh, t, fill=("1E7F6B" if last else L2), line=(None if last else "B0BEC5"), lw=0.6, fs=6.2,
                  color=("FFFFFF" if last else INK), bold=last, radius=0.05, align="left", name=f"leaf{k+1}_{i+1}")
    # outcome subtree
    oy = 5.55
    c.box(2.25, oy, 3.0, 0.42, "Screening decision (3,114 unique images)", fill=L1, line=None, fs=7.5, bold=True, color="FFFFFF", radius=0.06, name="decision")
    end_y = ly0 + 3 * (lh + lg) + lh
    c.arrow(6.15, end_y, 6.15, oy + 0.21, head=False, color=LINE); c.arrow(6.15, oy + 0.21, 5.25, oy + 0.21, color=LINE)
    kids = [("keep  952", ACC["keep"], 1.25), ("unsure  632", ACC["unsure"], 3.75), ("reject  1,530", ACC["reject"], 6.25)]
    ky = oy + 0.85
    c.arrow(3.75, oy + 0.42, 3.75, ky - 0.2, head=False, color=LINE); c.arrow(1.25, ky - 0.2, 6.25, ky - 0.2, head=False, color=LINE)
    for t, col, x in kids:
        c.arrow(x, ky - 0.2, x, ky, color=LINE)
        c.box(x - 0.8, ky, 1.6, 0.36, t, fill=col, line=None, fs=7.5, bold=True, color="FFFFFF", radius=0.18)
    out_leaves = {
        0: [("main benchmark  993", "776 tier A; incl. 35 crops + 6 reviewed")],
        1: [("unit-level set  233", "single unit process with ancillaries"), ("pictorial set  87", "3-D / cartoon plant drawings"),
            ("other-domain set  83", "chemical, refinery, power PFDs"), ("crop-pending  99", "→ main after manual crop"),
            ("manual review  33", "still undecided after human review"), ("excluded  41", "layouts, mass balances")],
        2: [("excluded  1,530", "charts, maps, photos, non-process figures")],
    }
    for k, (t, col, x) in enumerate(kids):
        items = out_leaves[k]; y = ky + 0.6; bus_x = x - 0.8 + 0.12
        if len(items) > 1:
            c.arrow(bus_x, ky + 0.36, bus_x, y + (len(items) - 1) * 0.5 + 0.2, head=False, color=LINE)
        else:
            c.arrow(x, ky + 0.36, x, y, color=LINE)
        for i, (lab, sub) in enumerate(items):
            yy = y + i * 0.5
            if len(items) > 1:
                c.arrow(bus_x, yy + 0.2, x - 0.8 + 0.25, yy + 0.2, head=False, color=LINE)
                bx, bw = x - 0.8 + 0.25, 2.0
            else:
                bx, bw = x - 1.0, 2.0
            c.box(bx, yy, bw, 0.4, "", fill=L3, line=col, lw=0.8, radius=0.05)
            c.text(bx + 0.08, yy + 0.03, bw - 0.16, 0.18, lab, fs=6.8, bold=True, color=INK)
            c.text(bx + 0.08, yy + 0.21, bw - 0.16, 0.18, sub, fs=5.6, color=LINE)
    slide_note(s, "Style D - hierarchical algorithm tree (org-chart layout): root -> three stages -> steps; screening decision -> subsets.")


# =============================================================================== STYLE E — decision tree
def style_e(prs):
    s = blank(prs); c = Canvas(s)
    INK, LINE, Q, QF, LEAF, LEAFT, STOP = "1F2933", "7B8794", "0E8C7F", "E6F4F1", "FFFFFF", "1F2933", "F3F4F6"
    c.text(0.5, 0.25, 6.5, 0.3, "Decision tree: the path of one candidate figure to its final subset", fs=10, bold=True, color=INK)
    c.text(0.5, 0.52, 6.5, 0.2, "Diamonds are tests; counts are from the 16 November 2026 run", fs=6.8, italic=True, color=LINE)

    def q(cx, cy, text, w=2.3, h=0.56):
        c.diamond(cx, cy, w, h, text, fill=QF, line=Q, fs=6.2)

    def leaf(x, y, w, text, fill=LEAF, line="B0BEC5", color=LEAFT, bold=False, fs=6.5, h=0.32):
        c.box(x, y - h / 2, w, h, text, fill=fill, line=line, lw=0.7, fs=fs, color=color, bold=bold, radius=0.05)

    def lab(x, y, t):
        c.text(x, y, 0.4, 0.15, t, fs=6, bold=True, italic=True, color=Q)

    X, RX, DY = 2.6, 4.9, 0.72          # trunk x, right-leaf x, spacing between tests
    c.box(X - 1.4, 0.85, 2.8, 0.42, "Candidate figure\n56,617 literature figures + web, patent and scanned-page images", fill="263238", line=None, fs=6.5, bold=True, color="FFFFFF", radius=0.06)
    ys = [1.72 + i * DY for i in range(5)]
    c.arrow(X, 1.27, X, ys[0] - 0.28, color=LINE)
    tests = [("Caption available?", 2.3, "no", "yes"), ("Contains a diagram word?", 2.3, "no", "yes"),
             ("Exclusion word and\nno strong diagram word?", 2.5, "yes", "no"), ("Plant word?\n(WWTP, STP, WRRF, treatment line …)", 2.9, "yes", "no"),
             ("Treatment word?\n(sludge, clarifier, digester, MBR …)", 2.9, "yes", "no")]
    rights = [("Download for visual screening\n(patents, web images, page scans)", LEAF, "B0BEC5", LEAFT, False),
              ("Not downloaded", STOP, None, LINE, False), ("Not downloaded (map, photo, chart, biology)", STOP, None, LINE, False),
              ("Tier T1 — whole-plant diagram caption", LEAF, "B0BEC5", LEAFT, True), ("Tier T2 — treatment-related schematic", LEAF, "B0BEC5", LEAFT, True)]
    for i, ((t, w, rlab, dlab), (rt, rf, rl, rc, rb)) in enumerate(zip(tests, rights)):
        y = ys[i]
        q(X, y, t, w=w)
        lab(X + w / 2 + 0.05, y - 0.18, rlab); c.arrow(X + w / 2, y, RX, y, color=LINE)
        leaf(RX, y, 2.1, rt, fill=rf, line=rl, color=rc, bold=rb, fs=6.2)
        if i < 4:
            lab(X + 0.05, y + 0.3, dlab); c.arrow(X, y + 0.28, X, ys[i + 1] - 0.28, color=LINE)
    # last test: "no" goes left
    lab(X - 1.8, ys[4] - 0.18, "no"); c.arrow(X - 1.45, ys[4], 1.75, ys[4], color=LINE); leaf(0.35, ys[4], 1.4, "Not downloaded", fill=STOP, line=None, color=LINE, fs=6.2)
    # right-hand bus collecting the three downloaded branches -> provenance node
    MX, BY = 7.1, ys[4] + 0.5
    c.arrow(MX, ys[0], MX, BY, head=False, color=LINE)
    for i in (0, 3, 4):
        c.arrow(RX + 2.1, ys[i], MX, ys[i], head=False, color=LINE)
    c.arrow(MX, BY, X, BY, head=False, color=LINE)
    PY = BY + 0.32
    c.arrow(X, BY, X, PY - 0.2, color=LINE)
    c.box(X - 1.4, PY - 0.2, 2.8, 0.4, "Downloaded with a provenance record  (3,300 files)", fill="1E7F6B", line=None, fs=6.8, bold=True, color="FFFFFF", radius=0.06)
    DQ = PY + 0.66
    c.arrow(X, PY + 0.2, X, DQ - 0.28, color=LINE)
    q(X, DQ, "Duplicate? (same SHA-256 or\npHash distance ≤ 6)", w=2.5)
    lab(X + 1.3, DQ - 0.18, "yes"); c.arrow(X + 1.25, DQ, RX, DQ, color=LINE); leaf(RX, DQ, 2.1, "Merged into the retained copy  (186)", fill=STOP, line=None, color=LINE, fs=6.2)
    SY = DQ + 0.68
    lab(X + 0.05, DQ + 0.3, "no"); c.arrow(X, DQ + 0.28, X, SY - 0.2, color=LINE)
    c.box(X - 1.4, SY - 0.2, 2.8, 0.4, "Visual screening on contact sheets  (3,114 unique images)", fill="263238", line=None, fs=6.8, bold=True, color="FFFFFF", radius=0.06)
    OY = SY + 0.7
    c.arrow(X, SY + 0.2, X, OY - 0.33, head=False, color=LINE); c.arrow(0.95, OY - 0.33, 6.3, OY - 0.33, head=False, color=LINE)
    outs = [("keep  952", "2E7D32", 0.95), ("unsure  632", "C77A1F", 2.6), ("reject  1,530", "9AA5B1", 6.3)]
    for t, col, x in outs:
        c.arrow(x, OY - 0.33, x, OY - 0.17, color=LINE)
        c.box(x - 0.65, OY - 0.17, 1.3, 0.34, t, fill=col, line=None, fs=7, bold=True, color="FFFFFF", radius=0.17)
    c.arrow(0.95, OY + 0.17, 0.95, OY + 0.48, color=LINE); leaf(0.3, OY + 0.66, 1.3, "main benchmark\n993 (776 tier A)", fill="E8F5E9", line="2E7D32", bold=True, fs=6.2, h=0.36)
    c.arrow(6.3, OY + 0.17, 6.3, OY + 0.48, color=LINE); leaf(5.65, OY + 0.66, 1.3, "excluded\n1,530", fill=STOP, line=None, color=LINE, fs=6.2, h=0.36)
    c.arrow(2.6, OY + 0.17, 2.6, OY + 0.48, color=LINE)
    c.box(1.75, OY + 0.48, 1.7, 0.3, "Reason for uncertainty", fill=QF, line=Q, fs=6.3, radius=0.05)
    reasons = [("unit-level set  233", "single unit process + ancillaries"), ("pictorial set  87", "3-D / cartoon plant drawing"), ("other-domain set  83", "chemical, refinery, power process"),
               ("crop-pending  99 → main", "multi-panel figure or page scan"), ("manual review  33", "still undecided after human review"), ("excluded  41", "layout or mass-balance diagram")]
    ry = OY + 1.05
    c.arrow(2.6, OY + 0.78, 2.6, ry - 0.08, head=False, color=LINE); c.arrow(1.45, ry - 0.08, 3.75, ry - 0.08, head=False, color=LINE)
    for col_i, cx in enumerate((1.45, 3.75)):
        c.arrow(cx, ry - 0.08, cx, ry + 2 * 0.36 + 0.1, head=False, color=LINE)
        for j in range(3):
            lab_, why = reasons[col_i * 3 + j]
            y = ry + j * 0.36
            c.arrow(cx, y + 0.17, cx + 0.12, y + 0.17, head=False, color=LINE)
            c.box(cx + 0.12, y, 2.05, 0.34, "", fill=LEAF, line="C77A1F", lw=0.7, radius=0.05)
            c.text(cx + 0.2, y + 0.02, 1.95, 0.16, lab_, fs=6.3, bold=True, color=INK)
            c.text(cx + 0.2, y + 0.18, 1.95, 0.15, why, fs=5.4, italic=True, color=LINE)
    slide_note(s, "Style E - decision tree followed by one candidate figure: caption tests, provenance, duplicate test, visual screening, uncertainty reasons -> subsets.")


def main():
    prs = new_prs()
    style_a(prs); style_b(prs); style_c(prs); style_d(prs); style_e(prs)
    prs.save(OUT)
    print("saved", OUT, "slides:", len(prs.slides))


if __name__ == "__main__":
    main()
