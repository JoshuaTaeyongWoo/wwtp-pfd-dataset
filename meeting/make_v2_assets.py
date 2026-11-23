"""
make_v2_assets.py — image assets for the v2 meeting deck (crops of the Theisen paper pages, real pilot images,
and the hand-labelled ground-truth overlay on pilot image 44 panel A).
Inputs: meeting/figures/_src/max_page{1,8}.png (rendered from Ref/ with PyMuPDF), data/pilot/images/*.
Outputs: meeting/figures/v2/*.png
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "meeting" / "figures" / "_src"
PIL_IMG = ROOT / "data" / "pilot" / "images"
OUT = ROOT / "meeting" / "figures" / "v2"
OUT.mkdir(parents=True, exist_ok=True)

FONT = "C:/Windows/Fonts/arial.ttf"
FONT_B = "C:/Windows/Fonts/arialbd.ttf"


def crop(src: Path, box, dst: Path, scale: float = 1.0):
    im = Image.open(src).convert("RGB").crop(box)
    if scale != 1.0:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    im.save(dst)
    print(dst.name, im.size)


def paper_crops():
    # page 1 (1406 x 1875 @170 dpi): journal header .. affiliation line
    crop(SRC / "max_page1.png", (80, 80, 1330, 570), OUT / "max_page1_header.png")
    # page 8: Table 3 (overall AP) and Table 4 (per-class AP)
    crop(SRC / "max_page8.png", (85, 790, 690, 905), OUT / "max_table3.png")
    crop(SRC / "max_page8.png", (715, 790, 1325, 1235), OUT / "max_table4.png")


def real_examples():
    # KR patent, box-form (tall drawing: keep the upper two thirds)
    crop(PIL_IMG / "pilot_35__KR100653676B1_D01.png", (0, 0, 1965, 1560), OUT / "ex_kr_patent_box.png", 0.6)
    # EN paper, symbol-form (panel A of a two-panel figure)
    crop(PIL_IMG / "pilot_44__11356_2016_8211_Fig1_HTML.jpg", (0, 0, 761, 238), OUT / "ex_en_paper_symbol.png", 1.6)
    # US EPA manual, box + symbol mix
    crop(PIL_IMG / "pilot_39__EPA-832-R-10-005_p0167_img2069.png", (0, 0, 1405, 406), OUT / "ex_epa_manual.png")
    # OA paper, pictorial (icons / 3-D)
    crop(PIL_IMG / "pilot_45__10.1016_j.jclepro.2016.07.209_p0015_img62.png", (0, 0, 1187, 836), OUT / "ex_pictorial.png")
    # box-form English with explicit internal / external recycle (AAO) — used on the "what is drawn" column
    crop(PIL_IMG / "pilot_10__10.1038_s41545-025-00513-y_p0009_img147.png", (0, 0, 1450, 513), OUT / "ex_aao_recycles.png")


# ------------------------------------------------------------------ hand-labelled GT on pilot 44, panel A
# coordinates in the original 761 x 447 image (panel A = y 0..238)
NODES = {  # id: (class, box x0,y0,x1,y1, kind)   kind: unit | zone | parent | terminal
    "inf": ("io_terminal (influent)", (6, 110, 80, 152), "terminal"),
    "pc": ("primary_clarifier", (144, 96, 220, 174), "unit"),
    "bio": ("process_unit_generic + l1_hint=secondary (parent tank)", (264, 94, 459, 162), "parent"),
    "anx": ("anoxic_zone", (268, 98, 330, 158), "zone"),
    "aer": ("aerobic_zone", (331, 98, 455, 158), "zone"),
    "mbr": ("mbr_unit", (470, 74, 570, 162), "unit"),
    "hold": ("storage_tank (holding)", (602, 94, 728, 162), "unit"),
    "eff": ("io_terminal (effluent)", (730, 116, 760, 140), "terminal"),
    "sl": ("io_terminal (primary sludge)", (170, 176, 196, 196), "terminal"),
}
EDGES = [  # src, dst, evidence, medium, role
    ("inf", "pc", "arrowhead", "liquid", "influent"),
    ("pc", "anx", "arrowhead", "liquid", "primary_effluent"),
    ("anx", "aer", "inferred (zones, no line)", "mixed_liquor", "internal"),
    ("aer", "mbr", "arrowhead", "mixed_liquor", "internal"),
    ("mbr", "anx", "arrowhead", "mixed_liquor", "internal_recycle"),
    ("mbr", "hold", "arrowhead", "liquid", "effluent"),
    ("hold", "eff", "arrowhead", "liquid", "effluent"),
    ("pc", "sl", "arrowhead", "sludge", "primary_sludge"),
]
PARENTS = [("bio", "anx"), ("bio", "aer")]
COL = {"unit": (0, 102, 204), "zone": (0, 150, 60), "parent": (120, 120, 120), "terminal": (220, 120, 0)}


def center(b):
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


def edge_anchor(b, towards):
    """point on the box border facing `towards`"""
    cx, cy = center(b)
    tx, ty = towards
    dx, dy = tx - cx, ty - cy
    if abs(dx) * (b[3] - b[1]) > abs(dy) * (b[2] - b[0]):
        x = b[2] if dx > 0 else b[0]
        y = cy + dy * (x - cx) / dx if dx else cy
    else:
        y = b[3] if dy > 0 else b[1]
        x = cx + dx * (y - cy) / dy if dy else cx
    return (x, y)


def arrow(d, p, q, color, w, s):
    import math
    d.line([p, q], fill=color, width=w)
    ang = math.atan2(q[1] - p[1], q[0] - p[0]); L = 7 * s
    a1 = (q[0] - L * math.cos(ang - 0.45), q[1] - L * math.sin(ang - 0.45))
    a2 = (q[0] - L * math.cos(ang + 0.45), q[1] - L * math.sin(ang + 0.45))
    d.polygon([q, a1, a2], fill=color)


def gt_overlay(s: int = 3):
    im = Image.open(PIL_IMG / "pilot_44__11356_2016_8211_Fig1_HTML.jpg").convert("RGB").crop((0, 0, 761, 238))
    im = im.resize((im.width * s, im.height * s), Image.LANCZOS)
    canvas = Image.new("RGB", (im.width, im.height + 70 * s), "white"); canvas.paste(im, (0, 0)); im = canvas
    d = ImageDraw.Draw(im, "RGBA")
    f = ImageFont.truetype(FONT_B, 11 * s); fs = ImageFont.truetype(FONT, 10 * s)
    S = lambda b: tuple(v * s for v in b)
    # parent first (dashed grey), zones dashed green, units solid blue, terminals orange
    for nid, (cls, b, kind) in NODES.items():
        B = S(b); c = COL[kind]
        if kind in ("parent", "zone"):
            dash(d, B, c, 2 * s, 8 * s)
        else:
            d.rectangle(B, outline=c, width=2 * s)
        label = cls.split(" (")[0].split(" +")[0]
        tx, ty = B[0], B[1] - 13 * s
        if kind == "zone":
            ty = B[3] + 2 * s
        if kind == "parent":
            tx, ty = B[0], B[1] - 26 * s; label = "parent tank (generic, stage = secondary)"
        if nid == "eff":
            tx = B[2] - d.textlength(label, font=fs) - 2
        if nid == "sl":
            tx, ty = B[2] + 4 * s, B[1]
        d.rectangle([tx - 2, ty - 1, tx + d.textlength(label, font=fs) + 4, ty + 12 * s], fill=(255, 255, 255, 215))
        d.text((tx, ty), label, fill=c, font=fs)
    for src, dst, ev, med, role in EDGES:
        bs, bd = NODES[src][1], NODES[dst][1]
        if (src, dst) == ("mbr", "anx"):  # draw the recycle along the top, as in the drawing
            p = ((bs[0] + 40) * s, bs[1] * s); q = ((bd[0] - 6) * s, (bd[1] + 30) * s)
            mid1 = (p[0], 52 * s); mid2 = (q[0] - 14 * s, 52 * s); mid3 = (q[0] - 14 * s, q[1])
            col = (200, 0, 120, 230)
            d.line([p, mid1, mid2, mid3], fill=col, width=2 * s); arrow(d, mid3, q, col, 2 * s, s)
            lx, ly = (bd[0] + 110) * s, 38 * s
            d.text((lx, ly), "edge: mbr → anoxic | arrowhead | mixed liquor | internal recycle", fill=col, font=fs)
            continue
        col = (200, 0, 120, 230) if med != "sludge" else (120, 60, 0, 230)
        if ev.startswith("inferred"):
            col = (0, 150, 60, 230)
        p = edge_anchor(S(bs), center(S(bd))); q = edge_anchor(S(bd), center(S(bs)))
        arrow(d, p, q, col, 2 * s, s)
    # legend
    lg = [("unit (box + class)", COL["unit"]), ("zone box inside a parent tank", COL["zone"]), ("terminal (in / out)", COL["terminal"]),
          ("edge: src → dst, direction evidence, medium, role", (200, 0, 120)), ("edge inferred between zones (no line drawn)", (0, 150, 60))]
    x0, y0 = 8 * s, 243 * s
    d.rectangle([x0 - 4, y0 - 4, x0 + 330 * s, y0 + 5 * 12 * s + 2], fill=(255, 255, 255, 225))
    for i, (t, c) in enumerate(lg):
        y = y0 + i * 12 * s
        d.rectangle([x0, y + 2 * s, x0 + 10 * s, y + 10 * s], outline=c, width=2 * s)
        d.text((x0 + 14 * s, y), t, fill=(30, 30, 30), font=fs)
    im.save(OUT / "gt_overlay_pilot44.png"); print("gt_overlay_pilot44.png", im.size)


def dash(d, B, c, w, seg):
    x0, y0, x1, y1 = B
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    import math
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, int(L // seg))
        for k in range(0, n, 2):
            t0, t1 = k / n, min((k + 1) / n, 1)
            d.line([(ax + (bx - ax) * t0, ay + (by - ay) * t0), (ax + (bx - ax) * t1, ay + (by - ay) * t1)], fill=c, width=w)


if __name__ == "__main__":
    paper_crops(); real_examples(); gt_overlay()
