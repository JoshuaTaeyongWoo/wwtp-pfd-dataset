"""
make_figure_deck.py — editable PowerPoint with the pipeline figure in three different styles (one slide each).

All elements are native PowerPoint shapes / text boxes / connectors (no images), so every box, colour, font and
arrow can be edited in PowerPoint. Slide size is portrait 7.5 x 10 in (figure-like); copy the group into any deck.

  Slide 1  Style A "Stage bands"      — three horizontal stage panels, role-coded colours, data-funnel callouts,
                                        outcome bar (the v2 matplotlib design re-built as shapes)
  Slide 2  Style B "Vertical stepper" — one dark spine with numbered nodes; step cards on the right, data chips on
                                        the left; sources as a top row; KPI tiles at the bottom (navy / ice-blue / teal)
  Slide 3  Style C "Data funnel"      — a funnel of trapezoids whose widths follow the image counts, each level paired
                                        with the step that caused the reduction; split tiles at the bottom
                                        (slate / terracotta / sand)

Output: paper/Fig_pipeline_styles.pptx
Usage : python make_figure_deck.py
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt, Emu
from lxml import etree

HERE = Path(__file__).resolve().parent
OUT = HERE / "Fig_pipeline_styles.pptx"
FONT = "Arial"


def rgb(h: str) -> RGBColor:
    return RGBColor.from_string(h)


# =============================================================================== primitives
class Canvas:
    def __init__(self, slide):
        self.s = slide

    def box(self, x, y, w, h, text="", fill="FFFFFF", line="52606D", lw=0.75, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
            fs=8, bold=False, color="1F2933", align="center", anchor="middle", radius=0.12, italic=False, name=None,
            margin=0.05, line_dash=None):
        shp = self.s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        if name:
            shp.name = name
        if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
            shp.adjustments[0] = min(0.5, radius / max(min(w, h), 0.01))
        if fill is None:
            shp.fill.background()
        else:
            shp.fill.solid(); shp.fill.fore_color.rgb = rgb(fill)
        if line is None:
            shp.line.fill.background()
        else:
            shp.line.color.rgb = rgb(line); shp.line.width = Pt(lw)
            if line_dash:
                shp.line.dash_style = line_dash
        shp.shadow.inherit = False
        tf = shp.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(margin)
        tf.margin_top = tf.margin_bottom = Inches(0.03)
        tf.vertical_anchor = {"middle": MSO_ANCHOR.MIDDLE, "top": MSO_ANCHOR.TOP, "bottom": MSO_ANCHOR.BOTTOM}[anchor]
        self._text(tf, text, fs, bold, color, align, italic)
        return shp

    def text(self, x, y, w, h, text, fs=8, bold=False, color="1F2933", align="left", anchor="top", italic=False, name=None):
        tb = self.s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        if name:
            tb.name = name
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = {"middle": MSO_ANCHOR.MIDDLE, "top": MSO_ANCHOR.TOP, "bottom": MSO_ANCHOR.BOTTOM}[anchor]
        self._text(tf, text, fs, bold, color, align, italic)
        return tb

    @staticmethod
    def _text(tf, text, fs, bold, color, align, italic=False):
        """text may contain **bold** segments; lines separated by \\n"""
        lines = text.split("\n") if text else [""]
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {"center": PP_ALIGN.CENTER, "left": PP_ALIGN.LEFT, "right": PP_ALIGN.RIGHT}[align]
            parts = line.split("**")
            for j, part in enumerate(parts):
                if not part:
                    continue
                r = p.add_run(); r.text = part
                r.font.name = FONT; r.font.size = Pt(fs); r.font.bold = bold or (j % 2 == 1)
                r.font.italic = italic; r.font.color.rgb = rgb(color)

    def arrow(self, x1, y1, x2, y2, color="52606D", lw=1.0, head=True, dash=None):
        c = self.s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        c.line.color.rgb = rgb(color); c.line.width = Pt(lw)
        if dash:
            c.line.dash_style = dash
        if head:
            ln = c.line._get_or_add_ln()
            tail = etree.SubElement(ln, qn("a:tailEnd")); tail.set("type", "triangle"); tail.set("w", "med"); tail.set("len", "med")
        return c

    def elbow(self, pts, color="52606D", lw=1.0):
        """poly-line through points; arrow head on the last segment"""
        for i in range(len(pts) - 1):
            self.arrow(*pts[i], *pts[i + 1], color=color, lw=lw, head=(i == len(pts) - 2))

    def circle(self, cx, cy, d, text="", fill="323F4B", color="FFFFFF", fs=9, line=None):
        return self.box(cx - d / 2, cy - d / 2, d, d, text, fill=fill, line=line, shape=MSO_SHAPE.OVAL, fs=fs, bold=True, color=color, margin=0)

    def diamond(self, cx, cy, w, h, text, fill="FFF4E0", line="C77A1F", fs=7.5):
        return self.box(cx - w / 2, cy - h / 2, w, h, text, fill=fill, line=line, shape=MSO_SHAPE.DIAMOND, fs=fs, margin=0.02)


def new_prs():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(7.5), Inches(10)
    return prs


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def slide_note(slide, txt):
    slide.notes_slide.notes_text_frame.text = txt


# =============================================================================== STYLE A — stage bands
def style_a(prs):
    s = blank(prs); c = Canvas(s)
    INK, LINE, PANEL, PANEL_EC, CHIP = "1F2933", "52606D", "F5F7FA", "CBD2D9", "323F4B"
    AUTO, AUTO_F, HUM, HUM_F, DATA, FINAL, GREY = "2F6F9F", "EAF1F8", "C77A1F", "FFF4E0", "1E7F6B", "2E7D32", "9AA5B1"
    SRC = ["5B7DB1", "7A9E7E", "B0866B", "8E7CC3", "A05A6E"]
    L, R = 0.95, 7.2   # content x-range
    # bands
    for (y0, h, n, lab) in [(0.35, 3.55, 1, "Harvesting with provenance"), (4.05, 1.45, 2, "Curation"),
                            (5.65, 4.1, 3, "Visual triage and split assignment")]:
        c.box(L, y0, R - L, h, fill=PANEL, line=PANEL_EC, lw=0.75, radius=0.15, name=f"band{n}")
        c.circle(L + 0.28, y0 + 0.27, 0.3, str(n), fill=CHIP, fs=9)
        c.text(L + 0.5, y0 + 0.13, 4, 0.3, lab, fs=10.5, bold=True, color=CHIP)
    # legend
    for i, (lab, f, e) in enumerate([("automated step", AUTO_F, AUTO), ("human-in-the-loop step", HUM_F, HUM), ("data product", DATA, DATA)]):
        x = 4.0 + i * 1.1
        c.box(x, 0.1, 0.16, 0.12, fill=f, line=e, lw=0.75, radius=0.03)
        c.text(x + 0.2, 0.085, 1.0, 0.16, lab, fs=6, color=INK)
    # sources
    srcs = [("Open-access\nliterature", "Europe PMC → PMC-OA bucket;\nOpenAlex PDFs"), ("Public agency\ndocuments", "US EPA design manuals\n(NEPIS, epa.gov)"),
            ("Operator\nweb pages", "Korean municipal\nWWTP sites"), ("Wikimedia\nCommons", "MediaWiki API,\nmultilingual queries"),
            ("Patent\ndrawings", "Google Patents,\nCPC C02F3/9/11")]
    sw, gap, x0 = 1.13, 0.085, L + 0.25
    for i, (t, sub) in enumerate(srcs):
        x = x0 + i * (sw + gap)
        c.box(x, 0.75, sw, 0.78, fill="FFFFFF", line=PANEL_EC, lw=0.6, radius=0.06, name=f"source{i+1}")
        c.box(x + 0.06, 0.75, sw - 0.12, 0.07, fill=SRC[i], line=None, shape=MSO_SHAPE.RECTANGLE)
        c.text(x + 0.08, 0.86, sw - 0.14, 0.3, t, fs=7, bold=True, color=INK)
        c.text(x + 0.08, 1.2, sw - 0.14, 0.3, sub, fs=5.5, color=LINE)
        c.arrow(x + sw / 2, 1.53, x + sw / 2, 1.72)
    c.box(x0, 1.72, R - L - 0.5, 0.36, "Candidate discovery through official indexes and APIs (identifying User-Agent, fixed rate limits; no access-control circumvention)", fs=6.8, name="discovery")
    c.arrow(4.075, 2.08, 4.075, 2.27)
    c.box(x0, 2.27, 2.85, 0.6, "Acquisition of metadata and figure containers\nJATS XML + figure files, PDF pages, HTML <img>, drawing sheets", fs=6.5, name="acquisition")
    c.box(x0 + 3.1, 2.27, 2.85, 0.6, "Caption-tier filter (Algorithm 2)\nT1 whole-plant caption · T2 treatment-related caption · otherwise not downloaded", fs=6.5, fill=AUTO_F, line=AUTO, name="caption_filter")
    c.arrow(x0 + 2.85, 2.57, x0 + 3.1, 2.57)
    c.arrow(x0 + 1.42, 2.87, x0 + 1.42, 3.05); c.arrow(x0 + 4.52, 2.87, x0 + 4.52, 3.05)
    c.box(x0, 3.05, R - L - 0.5, 0.75, "", fill="FFFFFF", line=DATA, lw=0.9, name="provenance")
    c.text(x0 + 0.1, 3.09, 5.5, 0.18, "Provenance record  (one per file, append-only JSONL)", fs=7, bold=True, color=DATA)
    c.text(x0 + 0.1, 3.27, 5.75, 0.52, "source · document identifiers · file URL · landing URL · rights holder · figure label · caption · query · filter rule\nlicence → tier A (CC0 / CC BY / CC BY-SA / public domain / patent: redistributable) or tier B (NC / ND / unknown: research only)\nSHA-256 (exact duplicates) · 64-bit perceptual hash (near duplicates) · acquisition time and method", fs=5.8, color=INK)
    # stage 2
    c.elbow([(4.075, 3.8), (4.075, 3.93), (x0 + 1.42, 3.93), (x0 + 1.42, 4.5)])
    c.box(x0, 4.5, 2.85, 0.65, "De-duplication\nSHA-256 identity, then pHash Hamming distance ≤ 6; canonical = tier A first, then earliest acquisition", fs=6.5, fill=AUTO_F, line=AUTO, name="dedup")
    c.arrow(x0 + 2.85, 4.82, x0 + 3.1, 4.82)
    c.box(x0 + 3.1, 4.5, 2.85, 0.65, "Canonical catalogue\n3,114 images from 1,877 documents (catalog.csv · provenance/*.jsonl)", fs=6.8, bold=True, fill=DATA, line=DATA, color="FFFFFF", name="catalogue")
    # stage 3
    c.elbow([(x0 + 4.52, 5.15), (x0 + 4.52, 5.55), (x0 + 1.42, 5.55), (x0 + 1.42, 6.1)])
    c.box(x0, 6.1, 2.85, 0.6, "Contact-sheet rendering\n20 thumbnails per sheet, numbered; transparent images composited on white", fs=6.5, name="sheets")
    c.arrow(x0 + 1.42, 6.7, x0 + 1.42, 6.9)
    c.box(x0, 6.9, 2.85, 0.6, "Vision-LLM first pass (7 parallel agents)\ndecision: keep / unsure / reject; category: wwtp / sludge / wtp / pilot / other", fs=6.5, fill=AUTO_F, line=AUTO, name="llm_pass")
    c.arrow(x0 + 1.42, 7.5, x0 + 1.42, 7.72)
    c.diamond(x0 + 1.42, 8.1, 1.7, 0.75, "Human spot-check\nprecision ≥ target?", fs=6.8)
    c.text(x0 + 2.3, 7.93, 0.3, 0.15, "yes", fs=6.5, bold=True, italic=True, color=HUM)
    c.text(x0 + 0.5, 7.93, 0.3, 0.15, "no", fs=6.5, bold=True, italic=True, color=HUM)
    c.elbow([(x0 + 0.57, 8.1), (x0 + 0.1, 8.1), (x0 + 0.1, 7.2), (x0, 7.2)], color=HUM)
    c.text(L + 0.03, 7.0, 0.22, 0.4, "refine\ncriteria", fs=4.5, color=HUM, align="center")
    c.arrow(x0 + 2.27, 8.1, x0 + 3.1, 8.1)
    c.box(x0 + 3.1, 7.8, 2.85, 0.6, "Human validation and inclusion rules\nkeep precision ≈ 0.90 on a random sample; 0 missed in the reject sample; unsure grouped by reason", fs=6.5, fill=HUM_F, line=HUM, name="validation")
    c.arrow(x0 + 4.52, 8.4, x0 + 4.52, 8.6)
    c.box(x0 + 3.1, 8.6, 2.85, 0.6, "Split assignment and cropping\nmain · aux_unit · aux_pictorial · aux_other_domain · crop_pending → main after manual crop · manual_review", fs=6.5, fill=HUM_F, line=HUM, name="split")
    # outcome bar
    c.text(x0, 9.25, 5.9, 0.15, "Outcome (3,149 images incl. 35 crops)  ·  main benchmark: 776 of 993 redistributable (tier A)", fs=6, color=INK)
    segs = [("Main benchmark 993", 993, FINAL, "FFFFFF"), ("Crop 99", 99, "66BB6A", "FFFFFF"), ("Auxiliary 403", 403, DATA, "FFFFFF"),
            ("Review 33", 33, HUM, "FFFFFF"), ("Excluded 1,621", 1621, GREY, INK)]
    tot = sum(n for _, n, _, _ in segs); cur = x0; bw = R - L - 0.5
    for lab, n, col, tc in segs:
        w = bw * n / tot
        c.box(cur, 9.42, w, 0.26, lab if w > 0.7 else "", fill=col, line="FFFFFF", lw=0.5, shape=MSO_SHAPE.RECTANGLE, fs=5.8, bold=True, color=tc, margin=0)
        if w <= 0.7:
            c.text(cur - 0.25, 9.7, w + 0.5, 0.15, lab, fs=5.2, bold=True, color=col, align="center")
        cur += w
    # funnel callouts (left margin)
    c.arrow(0.5, 0.9, 0.5, 9.5, color=PANEL_EC, lw=1.0, head=False)
    for y, big, small in [(1.0, "6", "source types"), (2.3, "56,617", "figures inspected"), (3.3, "3,300", "files with provenance"),
                          (4.7, "3,114", "canonical images"), (7.9, "1,584", "keep + unsure"), (9.3, "993", "main benchmark")]:
        c.circle(0.5, y + 0.33, 0.1, fill=CHIP)
        c.text(0.05, y - 0.12, 0.9, 0.2, big, fs=9.5, bold=True, color=INK, align="center")
        c.text(0.05, y + 0.07, 0.9, 0.2, small, fs=5.5, color=LINE, align="center")
    slide_note(s, "Style A - stage bands (same design as Fig1_pipeline_v2). All shapes are native and editable.")


# =============================================================================== STYLE B — vertical stepper
def style_b(prs):
    s = blank(prs); c = Canvas(s)
    NAVY, ICE, TEAL, INK, MUTE, CARD, LINE = "1E2761", "CADCFC", "0E8C7F", "1F2933", "6B7A8F", "F6F8FC", "C9D3E6"
    SX = 1.55  # spine x
    # title row of sources (chips)
    c.text(0.5, 0.25, 6.5, 0.25, "Six source types, five official access routes", fs=9, bold=True, color=NAVY)
    chips = ["Open-access literature", "Public agency documents", "Operator web pages", "Wikimedia Commons", "Patent drawings"]
    cw = 1.28
    for i, t in enumerate(chips):
        c.box(0.5 + i * (cw + 0.03), 0.55, cw, 0.3, t, fill=NAVY, line=None, fs=6.5, bold=True, color="FFFFFF", radius=0.15, name=f"chip{i+1}")
    c.box(0.5, 0.95, 6.5, 0.02, fill=LINE, line=None, shape=MSO_SHAPE.RECTANGLE)
    # spine
    c.box(SX - 0.03, 1.25, 0.06, 8.2, fill=NAVY, line=None, shape=MSO_SHAPE.RECTANGLE, name="spine")
    steps = [
        ("Candidate discovery", "Official indexes and APIs (Europe PMC, OpenAlex, MediaWiki, Google Patents) and curated lists; identifying User-Agent and fixed rate limits.", "10,323 OA articles · 453 OA PDFs · 1,173 Commons files · 300 patents · 33 EPA documents · 27 operator pages", "6 source types"),
        ("Acquisition and caption-tier filter", "Figure containers (JATS XML + files, PDF pages, HTML images, drawing sheets). Captions are tiered: T1 whole-plant diagram, T2 treatment-related schematic; others are not downloaded.", "56,617 figures inspected → 3,300 files kept", "56,617 figures"),
        ("Provenance record", "One append-only record per file: identifiers, URLs, rights holder, caption, matching rule, licence → tier A (redistributable) / tier B (research only), SHA-256, perceptual hash.", "100 % of files traceable to source and licence", "3,300 files"),
        ("De-duplication", "SHA-256 identity, then 64-bit pHash with Hamming distance ≤ 6; one canonical file per cluster (tier A first, then earliest).", "186 duplicates removed", "3,114 images"),
        ("AI-assisted visual triage", "20-image contact sheets judged by vision-LLM agents: keep / unsure / reject and category (wwtp, sludge, wtp, pilot, other); transparent images re-judged on white.", "952 keep · 632 unsure · 1,530 reject", "1,584 keep + unsure"),
        ("Human validation and split rules", "Random keep / reject samples audited (keep precision ≈ 0.90, no misses); unsure grouped by reason and assigned to main, auxiliary, crop-pending or manual-review sets.", "776 of 993 main images redistributable", "993 benchmark"),
    ]
    y = 1.35; step_h = 1.3
    for i, (title, desc, metric, chip) in enumerate(steps, 1):
        cy = y + 0.3
        c.circle(SX, cy, 0.38, str(i), fill=NAVY, fs=10)
        # left data chip
        c.box(0.4, cy - 0.17, 0.9, 0.34, chip, fill=ICE, line=None, fs=6.5, bold=True, color=NAVY, radius=0.17, name=f"chip_left{i}")
        # card
        human = i == 6
        c.box(SX + 0.4, y, 5.3, step_h - 0.2, "", fill=CARD, line=LINE, lw=0.6, radius=0.1, name=f"card{i}")
        c.text(SX + 0.55, y + 0.08, 5.0, 0.25, title, fs=9, bold=True, color=NAVY)
        c.text(SX + 0.55, y + 0.34, 5.0, 0.5, desc, fs=6.8, color=INK)
        c.box(SX + 0.55, y + step_h - 0.47, 5.0, 0.2, metric, fill="FFFFFF", line=TEAL if not human else "C77A1F", lw=0.6, fs=6.3, bold=True,
              color=TEAL if not human else "C77A1F", radius=0.1, align="left")
        y += step_h
    # loop annotation between 5 and 6
    c.text(SX + 0.45, y - 0.22, 5.0, 0.16, "spot-check precision below target → refine triage criteria and re-run step 5", fs=5.8, italic=True, color=MUTE)
    # KPI tiles
    ty = 9.1
    tiles = [("993", "main benchmark images", TEAL), ("776", "redistributable (tier A)", TEAL), ("403", "auxiliary-set images", NAVY), ("33", "still in manual review", "C77A1F")]
    tw = 1.5
    for i, (big, lab, col) in enumerate(tiles):
        x = 0.5 + i * (tw + 0.17)
        c.box(x, ty, tw, 0.7, "", fill="FFFFFF", line=col, lw=1.0, radius=0.08, name=f"kpi{i+1}")
        c.text(x, ty + 0.06, tw, 0.35, big, fs=16, bold=True, color=col, align="center")
        c.text(x, ty + 0.44, tw, 0.2, lab, fs=6.3, color=MUTE, align="center")
    slide_note(s, "Style B - vertical stepper: spine with numbered nodes, step cards, data chips, KPI tiles.")


# =============================================================================== STYLE C — data funnel
def style_c(prs):
    s = blank(prs); c = Canvas(s)
    SLATE, TERRA, SAND, INK, MUTE, LIGHT = "36454F", "B85042", "E7E8D1", "1F2933", "6B7280", "F4F4EF"
    LEVELS = [("56,617", "figures inspected in 10,323 open-access articles and 1,877 further documents", 1.0),
              ("3,300", "files downloaded with a provenance record", 0.82),
              ("3,114", "unique images after de-duplication", 0.66),
              ("1,584", "keep + unsure after\nAI-assisted triage", 0.5),
              ("993", "main benchmark\n(776 tier A)", 0.36)]
    STEPS = [("Discovery and acquisition", "Official APIs and curated lists for six source types; JATS XML, PDF pages, HTML images and drawing sheets retrieved with an identifying User-Agent."),
             ("Caption-tier filter", "T1 = whole-plant diagram caption, T2 = treatment-related schematic; maps, photographs, spectra and community plots excluded. Each file receives licence tier, SHA-256 and pHash."),
             ("De-duplication", "Exact (SHA-256) and near (pHash Hamming ≤ 6) duplicates collapsed; tier A copy preferred."),
             ("Vision-LLM triage", "20-image contact sheets; decision keep / unsure / reject and category per image; parallel agents; transparent images re-judged."),
             ("Human validation and split rules", "Spot-check precision ≈ 0.90; unsure grouped by reason into auxiliary, crop-pending and manual-review sets.")]
    c.text(0.5, 0.25, 6.5, 0.3, "From 56,617 candidate figures to a 993-image benchmark", fs=11, bold=True, color=SLATE)
    c.text(0.5, 0.55, 6.5, 0.2, "Funnel width is proportional to the number of images retained at each stage", fs=7, color=MUTE, italic=True)
    FX, FW, y0, lh = 0.5, 3.2, 0.95, 1.45   # funnel column
    shades = ["36454F", "4A5A66", "5E6F7C", "7A8894", "B85042"]
    for i, (big, lab, frac) in enumerate(LEVELS):
        y = y0 + i * lh
        w_top = FW * frac
        w_bot = FW * (LEVELS[i + 1][2] if i + 1 < len(LEVELS) else frac * 0.9)
        # trapezoid: use the TRAPEZOID shape (narrow at top by default) -> flip via adjustment; simpler: freeform
        # freeform in EMU local units (scale=1.0); python-pptx multiplies local units by `scale`
        E = lambda v: int(Inches(v))
        ff = s.shapes.build_freeform(E(FX + (FW - w_top) / 2), E(y), scale=1.0)
        ff.add_line_segments([(E(FX + (FW + w_top) / 2), E(y)), (E(FX + (FW + w_bot) / 2), E(y + lh - 0.12)),
                              (E(FX + (FW - w_bot) / 2), E(y + lh - 0.12))], close=True)
        shp = ff.convert_to_shape(); shp.name = f"funnel{i+1}"
        shp.fill.solid(); shp.fill.fore_color.rgb = rgb(shades[i]); shp.line.fill.background()
        lw_ = min(w_top, w_bot) - 0.15          # label must stay inside the narrower edge of the trapezoid
        c.text(FX, y + 0.22, FW, 0.4, big, fs=18, bold=True, color="FFFFFF", align="center")
        c.text(FX + (FW - lw_) / 2, y + 0.64, lw_, 0.55, lab, fs=6.3, color="FFFFFF", align="center")
        # step box on the right (between levels: the step that causes the next reduction)
        t, d = STEPS[i]
        sx = FX + FW + 0.35
        c.box(sx, y + 0.12, 7.5 - 0.5 - sx, lh - 0.3, "", fill=LIGHT, line=None, radius=0.08, name=f"step{i+1}")
        c.circle(sx + 0.22, y + 0.34, 0.28, str(i + 1), fill=TERRA, fs=8)
        c.text(sx + 0.42, y + 0.2, 2.7, 0.3, t, fs=8.5, bold=True, color=SLATE)
        c.text(sx + 0.12, y + 0.52, 3.1, lh - 0.75, d, fs=6.5, color=INK)
        c.arrow(sx - 0.05, y + lh / 2 - 0.05, FX + (FW + max(w_top, w_bot)) / 2 + 0.05, y + lh / 2 - 0.05, color=TERRA, lw=0.8)
    # outcome tiles
    ty = y0 + 5 * lh + 0.15
    c.text(0.5, ty, 6.5, 0.2, "Dataset splits (3,149 images, incl. 35 manual crops)", fs=8, bold=True, color=SLATE)
    tiles = [("993", "main benchmark", TERRA, "FFFFFF"), ("99", "crop-pending parents\n(35 crops in main)", "D9826F", "FFFFFF"), ("403", "auxiliary sets\n(unit 233 · pictorial 87 · other 83)", SLATE, "FFFFFF"),
             ("33", "manual review", "7A8894", "FFFFFF"), ("1,621", "excluded", SAND, INK)]
    tw = 1.22; x = 0.5
    for big, lab, col, tc in tiles:
        c.box(x, ty + 0.25, tw, 0.75, "", fill=col, line=None, radius=0.06)
        c.text(x, ty + 0.3, tw, 0.32, big, fs=14, bold=True, color=tc, align="center")
        c.text(x + 0.05, ty + 0.6, tw - 0.1, 0.38, lab, fs=5.8, color=tc, align="center")
        x += tw + 0.1
    slide_note(s, "Style C - data funnel: trapezoid widths follow the retained-image counts; each level paired with the step causing the next reduction.")


def main():
    prs = new_prs()
    style_a(prs); style_b(prs); style_c(prs)
    prs.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
