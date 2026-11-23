"""
build_meeting_deck.py — advisor-meeting deck in the EMSEL lab style, built on meeting/Ref/EMSEL/agentic_easm_261015.pptx
(its master gives the blue top/bottom bars and the Front A title layout). Slide 1 of the template is kept and re-texted;
every other slide is created on the '제목 및 내용' layout with the template's geometry: 32 pt bold title, 20 pt '•'/'▪'
bullets, centred figure, 10 pt 'Figure.' caption, red '➔' takeaway, footer text + page number.
Output: meeting/WWTP_vision_meeting_2026-11-19.pptx
"""
from __future__ import annotations

import copy
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.lang import MSO_LANGUAGE_ID
from pptx.util import Inches, Pt, Emu

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "meeting" / "Ref" / "EMSEL" / "agentic_easm_261015.pptx"
FIG = ROOT / "meeting" / "figures"
MF = ROOT / "data_collection" / "annotation" / "manual" / "figures"
OUT = ROOT / "meeting" / "WWTP_vision_meeting_2026-11-19.pptx"
FOOTER = "11.19.(Thu) Progress meeting"
DARK = RGBColor(0x22, 0x22, 0x22); RED = RGBColor(0xC0, 0x00, 0x00); WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def no_latin_break(para):
    para._p.get_or_add_pPr().set("latinLnBrk", "0")  # the ko-KR master allows breaking Latin words mid-word


def run_style(run, size, bold=False, color=DARK, font="Arial"):
    run.font.name = font; run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = color
    run.font.language_id = MSO_LANGUAGE_ID.ENGLISH_US  # the lab master is ko-KR: without this PowerPoint breaks Latin words mid-word


def textbox(slide, x, y, w, h, paras, size=20, color=DARK, align=None, anchor=None, name=None):
    """paras: list of (text, bold) or (text, bold, size)."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05); tf.margin_top = tf.margin_bottom = Inches(0.03)
    if anchor:
        tf.vertical_anchor = anchor
    for i, p in enumerate(paras):
        text, bold = p[0], p[1]; sz = p[2] if len(p) > 2 else size
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if align:
            para.alignment = align
        no_latin_break(para); r = para.add_run(); r.text = text; run_style(r, sz, bold, color)
    return tb


def bullets_box(slide, items, x=0.65, y=0.86, w=12.03, h=1.9):
    """items: list of (level, text). level 0 -> '• ' bold, 1 -> '▪ ', 2 -> '- '."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05); tf.margin_top = tf.margin_bottom = Inches(0.03)
    for i, (lvl, text) in enumerate(items):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        mark = {0: "• ", 1: "▪ ", 2: "- "}[lvl]
        ind = {0: 0.0, 1: 0.35, 2: 0.7}[lvl]
        pPr = para._p.get_or_add_pPr(); pPr.set("marL", str(int(Inches(ind + 0.3)))); pPr.set("indent", str(int(-Inches(0.3))))
        para.space_after = Pt(2); no_latin_break(para)
        r = para.add_run(); r.text = mark + text; run_style(r, {0: 18, 1: 16, 2: 14}[lvl], lvl == 0, DARK)
    return tb


def picture(slide, path, y, max_w=12.2, max_h=2.9, x=None):
    with Image.open(path) as im:
        W, H = im.size
    s = min(max_w / W, max_h / H); w, h = W * s, H * s
    if x is None:
        x = (13.333 - w) / 2
    slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
    return x, y, w, h


def caption(slide, text, y, x=0.52, w=12.29):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(0.34))
    tf = tb.text_frame; tf.word_wrap = True; tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; no_latin_break(p)
    r = p.add_run(); r.text = "Figure. "; run_style(r, 10, True)
    r = p.add_run(); r.text = text; run_style(r, 10, False)


def takeaway(slide, text, y=6.11):
    textbox(slide, 0.52, y, 12.29, 0.53, [("➔ " + text, True)], 20, RED, PP_ALIGN.CENTER)


def footer(slide, n):
    textbox(slide, 0.40, 7.15, 8.0, 0.30, [(FOOTER, True)], 8, WHITE, name="footer-text")
    textbox(slide, 12.0, 7.15, 1.07, 0.30, [(str(n), True)], 10, WHITE, PP_ALIGN.RIGHT, name="page-number")


def table(slide, header, rows, x, y, w, col_w=None, size=11, row_h=0.34):
    nrows, ncols = len(rows) + 1, len(header)
    shp = slide.shapes.add_table(nrows, ncols, Inches(x), Inches(y), Inches(w), Inches(row_h * nrows))
    t = shp.table
    tblPr = t._tbl.tblPr; tblPr.set("bandRow", "0"); tblPr.set("firstRow", "0")
    style = tblPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}tableStyleId")
    if style is not None:
        style.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # 'No Style, Table Grid' -> we clear borders below
    if col_w:
        for i, cw in enumerate(col_w):
            t.columns[i].width = Inches(cw)
    for ri, row in enumerate([header] + rows):
        t.rows[ri].height = Inches(row_h)
        for ci, val in enumerate(row):
            c = t.cell(ri, ci); c.margin_left = c.margin_right = Inches(0.06); c.margin_top = c.margin_bottom = Inches(0.02)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.background()
            tf = c.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; no_latin_break(p); r = p.add_run(); r.text = str(val); run_style(r, size, ri == 0 or ci == 0)
            if ri == 0:
                p.alignment = PP_ALIGN.CENTER
    # template look: three horizontal rules (top, under header, bottom)
    for yy in (y, y + row_h, y + row_h * nrows):
        ln = slide.shapes.add_connector(1, Inches(x), Inches(yy), Inches(x + w), Inches(yy))
        ln.line.color.rgb = DARK; ln.line.width = Pt(1.0 if yy != y + row_h else 0.75)
    return t


class Deck:
    def __init__(self):
        self.prs = Presentation(TEMPLATE)
        # keep slide 1 (Front A), drop the rest
        sldIdLst = self.prs.slides._sldIdLst
        for sldId in list(sldIdLst)[1:]:
            self.prs.part.drop_rel(sldId.rId); sldIdLst.remove(sldId)
        self.layout = next(l for l in self.prs.slide_layouts if l.name == "제목 및 내용")
        self.n = 1

    def title_slide(self, kicker, title, authors, date, lines):
        s = self.prs.slides[0]
        by = {sh.name: sh for sh in s.shapes}
        def set_text(shape, texts):
            tf = shape.text_frame
            for i, t in enumerate(texts):
                if i < len(tf.paragraphs):
                    p = tf.paragraphs[i]
                    if p.runs:
                        p.runs[0].text = t
                        for r in p.runs[1:]: r.text = ""
                    else:
                        p.add_run().text = t
            for p in tf.paragraphs[len(texts):]:
                for r in p.runs: r.text = ""
        set_text(by["TextBox 3"], [kicker]); set_text(by["TextBox 4"], [title]); set_text(by["TextBox 5"], [authors])
        set_text(by["TextBox 6"], [date]); set_text(by["TextBox 7"], lines); set_text(by["footer-text"], [FOOTER]); set_text(by["page-number"], ["1"])

    def slide(self, title, notes=""):
        s = self.prs.slides.add_slide(self.layout)
        for ph in list(s.placeholders):
            if ph.placeholder_format.idx == 0 and title:
                ph.left, ph.top, ph.width, ph.height = Inches(0.52), Inches(0.24), Inches(12.29), Inches(0.52)
                ph.text_frame.text = title
                p = ph.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.LEFT; no_latin_break(p)
                r = p.runs[0]; run_style(r, 32, True, RGBColor(0, 0, 0))
                ph.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            else:
                ph._element.getparent().remove(ph._element)
        self.n += 1; footer(s, self.n)
        if notes:
            s.notes_slide.notes_text_frame.text = notes
        return s

    def save(self):
        self.prs.save(OUT); print("saved", OUT, "slides", len(self.prs.slides))


def build():
    D = Deck()
    D.title_slide("Research in progress",
                  "A Public Benchmark for Wastewater-Treatment Process Flow Diagrams: Unit Detection, Connectivity Graphs and Local Vision Models",
                  "TaeYong Woo", "2026.11.19.(Thu)",
                  ["Dept. of Environmental Science and Engineering, Kyung Hee University", "(visiting TU Delft, Process Intelligence Research group)"])

    # 2 previous meeting summary
    s = D.slide("Previous meeting summary", "지난 미팅 지시 세 가지를 그대로 적었습니다. 이 순서대로 보고드리겠습니다.")
    bullets_box(s, [(0, "Three directives from the last meeting"),
                    (1, "Build a vision model that reads wastewater-treatment process flow diagrams (PFDs)"),
                    (1, "A local, trainable model: not a Claude / API-based pipeline"),
                    (1, "Learn from the Delft group's prior work on PFD digitization (Theisen et al. 2023)"),
                    (0, "Since then: reviewed Theisen 2023, collected 3,273 records (main 993), froze a 33-class taxonomy, set up a 60-image pilot with two annotators, verified the analysis / evaluation pipeline")],
                h=4.6)
    textbox(s, 0.52, 5.9, 12.29, 0.6, [("Today: what Theisen did, how our domain differs, what we are building, status, model plan, decisions", True)], 18, RED, PP_ALIGN.CENTER)

    # 3 framework
    s = D.slide("Proposed framework", "전체 구성입니다. 위가 벤치마크 구축, 가운데가 정답과 채점, 아래가 같은 잣대로 비교할 모델들입니다. 로컬 학습 모델이 산출물이고 VLM은 라벨 없는 하한선만 줍니다.")
    bullets_box(s, [(0, "Two-step frame as in Theisen (detect units → recover connectivity), on a public benchmark with graph ground truth"),
                    (1, "Deliverable = benchmark (images + human labels + metrics) and locally trained detectors; a VLM only sets the no-label floor")], h=1.3)
    _, y, _, h = picture(s, FIG / "fig_pipeline.png", 2.2, 12.2, 3.5)
    caption(s, "Benchmark construction (top), ground truth and scoring (middle), models compared on the same test split (bottom). Steps 1–4 done, 5–6 pending.", y + h + 0.05)

    # 4 Theisen what
    s = D.slide("Literature review: Theisen et al. (2023)", "맥스 논문이 무엇을 했는지입니다. 1,005장, 47클래스, Faster R-CNN, 연결은 픽셀 탐색. 데이터는 비공개이고 연결 복원은 정량 평가가 없습니다.")
    bullets_box(s, [(0, "Digitization of chemical PFDs, Digital Chemical Engineering 6 (2023) 100072 — Delft, Schweidtmann group"),
                    (1, "1,005 PFDs mined from journals/books, 17,411 objects, labelled in LabelImg; data not public"),
                    (1, "47 classes: unit operations split by sub-type and by drawing style (tank1–4, pump1–3, hex …) + IO / arrow / text / stream tags"),
                    (1, "Faster R-CNN for detection: AP50 88 %, AP 68 %; connectivity by pixel search (binarize → skeletonize → trace), shown qualitatively only")], h=2.0)
    _, y, _, h = picture(s, FIG / "max_fig3_detection.png", 2.95, 11.5, 2.6)
    caption(s, "Theisen et al. (2023) Fig. 3 — (a) flowsheet, (b) detected unit operations, (c) skeletonized streams, (d) graph. Reproduced under CC BY.", y + h + 0.05)
    takeaway(s, "Same two-step frame; the gaps are public data, graph ground truth and a quantitative connectivity metric", 6.2)

    # 5 Theisen learned
    s = D.slide("Literature review: what we take from it", "이 논문에서 가져온 원칙 네 가지입니다. 특히 그림 2의 열교환기 23가지가 '양식이 다르면 클래스를 나눈다'는 원칙의 근거입니다.")
    bullets_box(s, [(0, "Principles carried into our design"),
                    (1, "Classes must be visually separable; drawing style matters (Fig. 2: one heat exchanger, 23 drawings)"),
                    (1, "Small symbols (valves, arrowheads) are the hard part; flow-direction errors come from missed arrowheads → arrowhead class + direction accuracy"),
                    (1, "Automatic mining + human labels; AI-assisted screening with a precision check (ours: ≈ 0.90 on 30 samples)"),
                    (1, "Faster R-CNN reproduced as the first baseline, then a modern detector")], h=2.5)
    _, y, _, h = picture(s, FIG / "max_fig2_heat_exchangers.png", 3.45, 9.5, 2.15)
    caption(s, "Theisen et al. (2023) Fig. 2 — 23 representations of a heat exchanger (CC BY).", y + h + 0.05)
    takeaway(s, "Keep the frame and the style-aware class principle; replace the class list and add graph ground truth", 6.2)

    # 6 data collection
    s = D.slide("Materials & Methods: data collection", "6개 출처에서 수집하고 중복 제거 후 3,273건, AI 보조 선별과 사람 확인을 거쳐 본 세트 993장입니다.")
    bullets_box(s, [(0, "Six sources, scripted collection with provenance (SHA-256, pHash, licence tier) → 3,273 records after de-duplication"),
                    (1, "Patents (US/KR/CN), PMC OA papers, other OA papers (OpenAlex), US EPA manuals, Wikimedia Commons, Korean municipal plants"),
                    (1, "AI-assisted screening + human check (precision ≈ 0.90 on 30 random keeps) → main 993 (tier A 776 / B 217), aux 403, crop-pending 223")], h=1.8)
    _, y, _, h = picture(s, FIG / "fig_sources.png", 2.7, 12.0, 2.9)
    caption(s, "Records per source and screening outcome (left); composition of the main set (right).", y + h + 0.05)
    takeaway(s, "Enough whole-plant diagrams (774) for a benchmark; patents and non-English sources make it diverse", 6.2)

    # 7 difference 1
    s = D.slide("Results: domain difference (1) — box-form diagrams", "첫 번째 차이. 절반 가까이가 글자로만 구별되는 박스형입니다. 모양 기준 클래스로는 학습할 게 없으니 의미 클래스와 양식을 분리했습니다.")
    bullets_box(s, [(0, "40–48 % of WWTP diagrams are box-form: identical rectangles, the unit is named only by its text"),
                    (1, "Theisen's premise (the symbol shape tells the class) fails on half of our data"),
                    (1, "Design: semantic_class separated from visual_form; generic class + l1_hint when text names only a stage; a 'semantic mapping on box-form' metric")], h=1.8)
    x1, y, w1, h = picture(s, FIG / "fig_visual_form.png", 2.7, 7.3, 2.9, x=0.5)
    picture(s, MF / "F7_visual_form.png", 2.9, 4.9, 2.5, x=8.1)
    caption(s, "Left: drawing-style shares (random 40 of main, multi-label; pilot 60). Right: box / symbol / pictorial examples from the manual.", y + h + 0.05)
    takeaway(s, "Shape-based classes cannot carry the benchmark: meaning comes from text + context for half the images", 6.2)

    # 8 difference 2
    s = D.slide("Results: domain difference (2) — units and process", "두 번째 차이. 장치 목록이 다르고, 구역과 반송이 공정 구성을 결정합니다. 그래서 전용 클래스 체계와 그래프 정답이 필요합니다.")
    bullets_box(s, [(0, "Caption term counts on 993 images: biological treatment dominates; the chemical-PFD core (heat exchanger, column, compressor) is absent"),
                    (1, "Zones inside one tank (anaerobic / anoxic / aerobic) and recycle streams (RAS, internal) define the configuration (A2O vs MLE vs UCT)"),
                    (1, "Design: 33 WWTP classes, zone boxes with parent_of, edge medium / role, configuration decision table; sources & languages → stratified reporting")], h=1.8)
    _, y, _, h = picture(s, FIG / "fig_term_freq.png", 2.65, 8.5, 3.0)
    caption(s, "Unit-process terms in captions/titles of the main set (regex count; under-counts units absent from captions).", y + h + 0.05)
    takeaway(s, "Theisen's 47 classes cannot be reused; the graph must carry zones and recycles to reach a simulator model", 6.25)

    # 9 taxonomy
    s = D.slide("Materials & Methods: taxonomy v1.1 (frozen)", "분류 체계입니다. L1 7단계, L2 33클래스, 연결 요소 8종. 교과서·시뮬레이터·표준 어휘를 근거로 세 번 검토하고 11월 16일에 동결했습니다.")
    bullets_box(s, [(0, "L1 7 stages → L2 33 unit-process classes (31 + 2 generic) → L3 sub-types where the simulator model differs; 8 connection / annotation classes"),
                    (1, "Evidence: our term counts, prior taxonomies (Theisen, PID2Graph, Kim 2022), ISO 10628 / DEXPI / KDS 61, QSDsan / GPS-X / SUMO units, textbooks (Metcalf & Eddy, Grady, MOP 8, IWA)"),
                    (1, "Three reviews (general → domain → journal-reviewer) → frozen 2026-11-16 as git tag taxonomy-v1.1; later changes logged as v1.1a/b, class count unchanged")], h=1.9)
    _, y, _, h = picture(s, FIG / "fig_taxonomy_tree.png", 2.7, 12.2, 3.4)
    caption(s, "The 33 L2 classes under their L1 stage; biofilm and anaerobic reactors carry required L3 sub-types.", y + h + 0.05)

    # 10 comparison table
    s = D.slide("Materials & Methods: Theisen (2023) vs this work", "한 장으로 비교하면 이렇습니다.")
    bullets_box(s, [(0, "Same frame, different data, classes, ground truth and evaluation")], h=0.5)
    table(s, ["Item", "Theisen et al. 2023 (chemical PFD)", "This work (WWTP PFD)"],
          [["Data", "1,005 PFDs mined from journals, not public", "main 993 + aux, 6 sources incl. patents / EPA / municipal, provenance + licence tiers, public"],
           ["Classes", "47, split by drawing style", "33 L2 + 8 connection; semantic class separated from visual_form; L3 by simulator model"],
           ["Box-form diagrams", "out of scope", "40–48 %: generic + l1_hint + text; box-form mapping accuracy"],
           ["Zones / recycles", "none", "zone boxes (parent_of), recycle roles, configuration table"],
           ["Connectivity GT", "none (qualitative)", "edge GT with direction evidence, medium, role; edge P/R/F1, direction accuracy, graph edit distance"],
           ["Label quality", "single labeller", "pilot: 2 independent annotators + adjudication; κ, IoU, edge F1 with bootstrap CI; human upper bound"],
           ["Models", "Faster R-CNN + pixel search", "Faster R-CNN reproduction, modern detector, pixel vs learned vs VLM zero-shot; taxonomy ablations"],
           ["Downstream", "none", "predicted graph → QSDsan flowsheet code, executability checked"]],
          x=0.65, y=1.45, w=12.0, col_w=[1.9, 3.9, 6.2], size=11, row_h=0.5)

    # 11 GT format
    s = D.slide("Materials & Methods: ground-truth format", "정답 형식입니다. 장치 박스 외에 단자·분기·합류·계측 요소와, 구역 박스와 부모 탱크, 그리고 엣지입니다.")
    bullets_box(s, [(0, "Per image: nodes (box + class + attributes) and directed edges (src → dst, direction evidence, medium / stream role)"),
                    (1, "Connection elements as nodes: IO terminals, junction_split / merge, instrument tags; chemical dosing is an edge, not a unit"),
                    (1, "Medium / role filled by 33 rules from the endpoint classes (checked by the adjudicator on 20 images); only tier-1 fields are scored")], h=1.8)
    picture(s, MF / "F8_connection_elements.png", 2.75, 6.1, 2.85, x=0.5)
    picture(s, MF / "F9_zones.png", 2.75, 6.1, 2.85, x=6.75)
    caption(s, "Left: connection elements (manual Fig. 8). Right: compartments of one tank as zone boxes with a parent box (manual Fig. 9).", 5.65)
    takeaway(s, "The graph, not the boxes, is what maps onto a simulator flowsheet", 6.15)

    # 12 pilot design
    s = D.slide("Materials & Methods: pilot annotation design", "파일럿 설계입니다. 60장을 두 사람이 독립적으로, 제가 판정합니다. 비용 때문에 1~20번만 완전판, 나머지는 쉬운 버전입니다.")
    bullets_box(s, [(0, "60 images, two annotators labelling independently, one adjudicator; target κ ≥ 0.8; disagreements feed guideline v2"),
                    (1, "Stratified draw: sqrt allocation by source, one image per document, ≥ 1 non-English per source; 58 documents, tier A 46 / B 14"),
                    (1, "Lite protocol v1.1b after a cost check (full ≈ 60 clicks / 15 min per image): images 1–20 full (arrowheads, text), 21–60 units / zones / terminals / junctions + edges by direction only")], h=1.9)
    _, y, _, h = picture(s, FIG / "fig_pilot_alloc.png", 2.85, 9.0, 2.75)
    caption(s, "Pilot allocation per source (bars: drawn; of which non-English labels). Numbers under the bars: images in main.", y + h + 0.05)
    takeaway(s, "Agreement statistics on 60 images, full-detail classes on 20: same evidence at about half the annotator time", 6.2)

    # 13 tools
    s = D.slide("Materials & Methods: tools, training, remote setup", "도구와 교육입니다. Label Studio, 매뉴얼 두 종과 요약 카드, 교육 대본. 어노테이터는 한국, 서버는 제 노트북이라 터널로 접속합니다. 교육은 오늘 마쳤습니다.")
    bullets_box(s, [(0, "Label Studio (open source, local) with the taxonomy as labelling config; projects pilot_A, pilot_B, practice (5 images)"),
                    (1, "Manual 17 p (9 figures), lite manual 9 p, one-page cheat sheet, 2-hour training script with 5 practice images and expected questions"),
                    (1, "Remote: server on the adjudicator's laptop (Netherlands) → Cloudflare tunnel → annotators in Korea in a browser, nothing to install; training done 2026-11-19")], h=1.8)
    _, y, _, h = picture(s, MF / "F2_ui_callouts.png", 2.7, 10.5, 2.95)
    caption(s, "Label Studio screen as used in the pilot: class buttons, per-box fields, relation (edge) drawing, image-level fields (manual Fig. 2).", y + h + 0.05)

    # 14 dry run
    s = D.slide("Results: pipeline verified on a synthetic dry run", "실제 결과가 오기 전에 합성 라벨로 파이프라인을 끝까지 돌려 결함 네 개를 고쳤습니다. 자기 비교는 전 지표 1.0입니다.")
    bullets_box(s, [(0, "Synthetic dry run: two throwaway projects, 6 images, B deliberately perturbed (shifted / missing / extra boxes, class swap, dropped and reversed edges)"),
                    (1, "Found and fixed: upload-id prefix made the same image two keys; tiny boxes (junctions, arrowheads) broke IoU 0.5 → centre-distance fallback; duplicate relations; two missing role rules")], h=1.5)
    table(s, ["Step", "Script", "Output", "Check"],
          [["Agreement", "s17", "κ (L2/L1), IoU ≥ 0.7 share, misses, edge P/R/F1, per-class κ, bootstrap CI, adjudication table", "A vs A = 1.000 everywhere; all 7 designed differences listed"],
           ["Medium inference", "s19", "graph.json per image, rule hits, ambiguous edges", "33 rules; 0 ambiguous on 108 synthetic edges"],
           ["GT conversion", "s22", "COCO (L2 + attributes), graph GT, manifest, document-level split", "6 images, 108 boxes"],
           ["Evaluation", "s23", "AP50 / AP L2 & L1, LVIS buckets, strata, box-form mapping acc., edge F1, direction acc., GED", "self = 1.0; A-GT vs B-pred: mAP50 0.72, edge F1 0.58 (synthetic)"]],
          x=0.65, y=2.45, w=12.0, col_w=[1.7, 0.9, 5.6, 3.8], size=11, row_h=0.55)
    takeaway(s, "When the real exports arrive, the same commands run unchanged; the numbers above are plumbing checks, not results", 6.15)

    # 15 model plan
    s = D.slide("Materials & Methods: baselines and the local-model plan", "모델 계획과 지시 2의 관계입니다. 본 모델은 로컬 학습 검출기이고, VLM은 라벨 없이 얻는 하한선과 대조군으로만 씁니다.")
    bullets_box(s, [(0, "Deliverable models are trained locally on our labels; a VLM is used only as the no-label floor and the control for the value of annotation"),
                    (1, "Faster R-CNN R50-FPN (Theisen reproduction) → modern detector (YOLO / DETR family) → graph recovery (pixel search vs learned) + rule-based medium"),
                    (1, "Ablations on the taxonomy itself: L2 33 vs L1 7 classes, with/without visual_form split, with/without zone boxes"),
                    (1, "Table for the paper: VLM zero-shot (0 labels) · learning curve (50 / 100 / 200 / all) · human upper bound (annotator agreement)")], h=2.4)
    table(s, ["Model", "Trained on our labels", "Role in the paper"],
          [["VLM zero-shot (Claude, structured output, 47-class enum)", "no", "floor without labels; script ready (s24), ≈ $3–6 for 60 images"],
           ["Faster R-CNN R50-FPN", "yes", "Theisen reproduction, first local baseline"],
           ["Modern detector + graph recovery", "yes", "main result; same split and metrics (s23)"],
           ["Human upper bound", "—", "pilot agreement: what a model can at most reach"]],
          x=0.65, y=3.45, w=12.0, col_w=[4.6, 2.2, 5.2], size=11, row_h=0.45)
    takeaway(s, "Directive 2 holds: the models we report are local; the API model only measures what labels add", 6.15)

    # 16 schedule
    s = D.slide("Future works: schedule", "일정입니다. 실선은 끝난 것, 빗금은 제안입니다. 본 어노테이션 규모와 인력에 따라 12월 이후가 달라집니다.")
    bullets_box(s, [(0, "Next two weeks: pilot labelling → agreement + adjudication table → guideline v2 → VLM zero-shot scored on the adjudicated 60"),
                    (1, "Then: main annotation on the lab server with individual accounts; Faster R-CNN reproduction; modern detector; QSDsan round-trip; datasheet")], h=1.3)
    _, y, _, h = picture(s, FIG / "fig_timeline.png", 2.2, 12.0, 3.6)
    caption(s, "Solid = done, hatched = proposed. Main annotation scale and staffing decide December onward.", y + h + 0.05)

    # 17 decisions
    s = D.slide("Decisions requested", "교수님께 여쭙고 싶은 다섯 가지입니다.")
    bullets_box(s, [(0, "Five points where I need your decision or approval")], h=0.5)
    table(s, ["Decision", "Options", "My proposal"],
          [["Main annotation scale and staffing", "all 993 (2 annotators × ≈ 2 weeks + adjudication) / first 500", "all 993: per-class instance counts decide whether rare classes can be evaluated"],
           ["Annotation server", "Label Studio on the lab Linux server (always on) / keep the laptop tunnel", "lab server: same place as the annotators, 24 h, individual accounts"],
           ["Data release", "tier A images + labels, tier B URLs + labels / URLs only", "the former, with a Datasheet and a Zenodo DOI"],
           ["Training compute", "lab GPU server / Delft resources", "lab GPU; Faster R-CNN reproduction needs one GPU"],
           ["Collaboration with the Delft group", "ask for the label map and connectivity code (Max sits next door) / independent", "ask for the label map and code; comparison experiments on our data"]],
          x=0.65, y=1.45, w=12.0, col_w=[3.0, 4.6, 4.4], size=11, row_h=0.62)

    # 18 thanks
    s = D.slide("", "")
    textbox(s, 1.0, 3.0, 11.3, 1.0, [("Thank You for Your Kind Attention", True)], 32, RGBColor(0x1F, 0x4E, 0x79), PP_ALIGN.CENTER)
    D.save()


if __name__ == "__main__":
    build()
