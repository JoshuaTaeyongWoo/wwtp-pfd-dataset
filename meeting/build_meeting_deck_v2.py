"""
build_meeting_deck_v2.py — advisor-meeting deck v2 in the EMSEL lab style (template: meeting/Ref/EMSEL/agentic_easm_261015.pptx).
v2 follows the slide-by-slide review of v1 (see the discussion log): 14 main slides + 3 appendix slides, mixed language
(titles / table headers / captions / technical terms in English, bullet sentences in Korean), Korean speaker notes with
expected Q&A, no script numbers on slides, real images instead of manual schematics.
Inputs: meeting/figures/v2/* (make_v2_assets.py, make_v2_figures.py), meeting/figures/* (v1 figures still used: fig_sources,
max_fig2/3/7), data_collection/annotation/manual/figures/F2_ui_callouts.png (placeholder until a live screenshot is taken),
Label Studio API for the pilot progress line (optional).
Output: meeting/WWTP_vision_meeting_v2.pptx
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

import yaml
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.lang import MSO_LANGUAGE_ID
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "meeting" / "Ref" / "EMSEL" / "agentic_easm_261015.pptx"
FIG = ROOT / "meeting" / "figures"
V2 = FIG / "v2"
MF = ROOT / "data_collection" / "annotation" / "manual" / "figures"
OUT = ROOT / "meeting" / "WWTP_vision_meeting_v2.pptx"
MEETING_DATE = os.environ.get("MEETING_DATE", "2026.11.20.(Fri)")   # change here or via env
FOOTER = os.environ.get("MEETING_FOOTER", "11.20.(Fri) Progress meeting")
DARK = RGBColor(0x22, 0x22, 0x22); RED = RGBColor(0xC0, 0x00, 0x00); WHITE = RGBColor(0xFF, 0xFF, 0xFF); GREY = RGBColor(0x66, 0x66, 0x66)
KO_FONT = "맑은 고딕"


# ------------------------------------------------------------------ text helpers
def no_latin_break(para):
    para._p.get_or_add_pPr().set("latinLnBrk", "0")


def run_style(run, size, bold=False, color=DARK, font="Arial", italic=False):
    run.font.name = font; run.font.size = Pt(size); run.font.bold = bold; run.font.italic = italic; run.font.color.rgb = color
    run.font.language_id = MSO_LANGUAGE_ID.ENGLISH_US
    rPr = run._r.get_or_add_rPr()
    latin = rPr.find(qn("a:latin"))
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        if latin is not None:
            latin.addnext(ea)
        else:
            rPr.append(ea)
    ea.set("typeface", KO_FONT)


def textbox(slide, x, y, w, h, paras, size=18, color=DARK, align=None, anchor=None, name=None, border=None, fill=None):
    """paras: list of (text, bold) or (text, bold, size) or (text, bold, size, color)."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    if border:
        tb.line.color.rgb = border; tb.line.width = Pt(1.0)
    if fill:
        tb.fill.solid(); tb.fill.fore_color.rgb = fill
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.06); tf.margin_top = tf.margin_bottom = Inches(0.04)
    if anchor:
        tf.vertical_anchor = anchor
    for i, p in enumerate(paras):
        text, bold = p[0], p[1]; sz = p[2] if len(p) > 2 else size; col = p[3] if len(p) > 3 else color
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if align:
            para.alignment = align
        no_latin_break(para); r = para.add_run(); r.text = text; run_style(r, sz, bold, col)
    return tb


def bullets_box(slide, items, x=0.65, y=0.86, w=12.03, h=1.9, sizes=(18, 15, 13)):
    """items: list of (level, text). level 0 -> '• ' bold, 1 -> '▪ ', 2 -> '- '."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05); tf.margin_top = tf.margin_bottom = Inches(0.03)
    for i, (lvl, text) in enumerate(items):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        mark = {0: "• ", 1: "▪ ", 2: "- "}[lvl]
        ind = {0: 0.0, 1: 0.35, 2: 0.7}[lvl]
        pPr = para._p.get_or_add_pPr(); pPr.set("marL", str(int(Inches(ind + 0.3)))); pPr.set("indent", str(int(-Inches(0.3))))
        para.space_after = Pt(3); no_latin_break(para)
        r = para.add_run(); r.text = mark + text; run_style(r, sizes[lvl], lvl == 0, DARK)
    return tb


def picture(slide, path, y, max_w=12.2, max_h=2.9, x=None):
    with Image.open(path) as im:
        W, H = im.size
    s = min(max_w / W, max_h / H); w, h = W * s, H * s
    if x is None:
        x = (13.333 - w) / 2
    pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
    return x, y, w, h, s


def caption(slide, text, y, x=0.52, w=12.29, align=PP_ALIGN.CENTER, size=10):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(0.34))
    tf = tb.text_frame; tf.word_wrap = True; tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]; p.alignment = align; no_latin_break(p)
    r = p.add_run(); r.text = "Figure. "; run_style(r, size, True)
    r = p.add_run(); r.text = text; run_style(r, size, False)
    return tb


def takeaway(slide, text, y=6.11, size=18):
    textbox(slide, 0.52, y, 12.29, 0.6, [("➔ " + text, True)], size, RED, PP_ALIGN.CENTER)


def footer(slide, n):
    textbox(slide, 0.40, 7.15, 8.0, 0.30, [(FOOTER, True)], 8, WHITE, name="footer-text")
    textbox(slide, 12.0, 7.15, 1.07, 0.30, [(str(n), True)], 10, WHITE, PP_ALIGN.RIGHT, name="page-number")


def table(slide, header, rows, x, y, w, col_w=None, size=11, row_h=0.34, first_col_bold=True, header_size=None):
    nrows, ncols = len(rows) + 1, len(header)
    shp = slide.shapes.add_table(nrows, ncols, Inches(x), Inches(y), Inches(w), Inches(row_h * nrows))
    t = shp.table
    tblPr = t._tbl.tblPr; tblPr.set("bandRow", "0"); tblPr.set("firstRow", "0")
    style = tblPr.find(qn("a:tableStyleId"))
    if style is not None:
        style.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"
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
            p = tf.paragraphs[0]; no_latin_break(p); r = p.add_run(); r.text = str(val)
            run_style(r, header_size or size if ri == 0 else size, ri == 0 or (ci == 0 and first_col_bold))
            if ri == 0:
                p.alignment = PP_ALIGN.CENTER
    for yy in (y, y + row_h, y + row_h * nrows):
        ln = slide.shapes.add_connector(1, Inches(x), Inches(yy), Inches(x + w), Inches(yy))
        ln.line.color.rgb = DARK; ln.line.width = Pt(1.0 if yy != y + row_h else 0.75)
    return t


def mark(slide, x, y, w, h, color=RED, width=2.0, dash=False):
    """red outline rectangle used to point at a region of a picture (inches)."""
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.background(); shp.line.color.rgb = color; shp.line.width = Pt(width)
    shp.adjustments[0] = 0.08
    if dash:
        shp.line.dash_style = 4  # dash
    shp.text_frame.text = ""
    return shp


def img_px_to_in(px_box, x0, y0, scale, dpi_scale=1.0):
    """convert an image-pixel box (x0,y0,x1,y1) to slide inches given the picture origin and inch-per-pixel scale."""
    a, b, c, d = px_box
    return (x0 + a * scale, y0 + b * scale, (c - a) * scale, (d - b) * scale)


def pilot_progress():
    """returns (annotated tasks pilot_A, pilot_B) from the local Label Studio server, or None."""
    try:
        tok = (ROOT / "data" / "pilot" / ".ls_token").read_text(encoding="utf-8").strip()
        base = "http://localhost:8080"
        req = urllib.request.Request(base + "/api/token/refresh", data=json.dumps({"refresh": tok}).encode(), headers={"Content-Type": "application/json"})
        acc = json.load(urllib.request.urlopen(req, timeout=10))["access"]
        r = urllib.request.Request(base + "/api/projects?page_size=50", headers={"Authorization": "Bearer " + acc})
        ps = json.load(urllib.request.urlopen(r, timeout=10))
        d = {p["title"]: p.get("num_tasks_with_annotations", 0) for p in ps.get("results", ps)}
        return d.get("pilot_A", 0), d.get("pilot_B", 0)
    except Exception as e:  # server down → leave the line generic
        print("progress: n/a", type(e).__name__)
        return None


class Deck:
    def __init__(self):
        self.prs = Presentation(TEMPLATE)
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
                        for r in p.runs[1:]:
                            r.text = ""
                    else:
                        p.add_run().text = t
            for p in tf.paragraphs[len(texts):]:
                for r in p.runs:
                    r.text = ""
        set_text(by["TextBox 3"], [kicker]); set_text(by["TextBox 4"], [title]); set_text(by["TextBox 5"], [authors])
        set_text(by["TextBox 6"], [date]); set_text(by["TextBox 7"], lines); set_text(by["footer-text"], [FOOTER]); set_text(by["page-number"], ["1"])
        return s

    def slide(self, title, notes=""):
        s = self.prs.slides.add_slide(self.layout)
        for ph in list(s.placeholders):
            if ph.placeholder_format.idx == 0 and title:
                ph.left, ph.top, ph.width, ph.height = Inches(0.52), Inches(0.24), Inches(12.29), Inches(0.52)
                ph.text_frame.text = title
                p = ph.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.LEFT; no_latin_break(p)
                r = p.runs[0]; run_style(r, 30, True, RGBColor(0, 0, 0))
                ph.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            else:
                ph._element.getparent().remove(ph._element)
        self.n += 1; footer(s, self.n)
        if notes:
            s.notes_slide.notes_text_frame.text = notes
        return s

    def save(self):
        self.prs.save(OUT); print("saved", OUT, "slides", len(self.prs.slides))


# ------------------------------------------------------------------ slides
def build():
    D = Deck()
    prog = pilot_progress()
    # 1 title
    s = D.title_slide("Research in progress",
                      "A Public Benchmark for Wastewater-Treatment Process Flow Diagrams: Unit Detection, Connectivity Graphs and Local Vision Models",
                      "TaeYong Woo", MEETING_DATE,
                      ["Dept. of Environmental Science and Engineering, Kyung Hee University", "(visiting TU Delft, Process Intelligence Research group)"])
    s.notes_slide.notes_text_frame.text = ("표지에서 구두로: 지난 미팅 지시 세 가지 — ① 하수처리장 공정도를 읽는 비전 모델, ② Claude 같은 API가 아니라 로컬에서 학습하는 모델, "
                                          "③ Delft 그룹의 선행 연구(Theisen 2023)에서 배울 것. 오늘 순서: 그 논문이 한 것 → 우리 도메인이 다른 점 → 우리가 만드는 것(전체 그림) → "
                                          "데이터·분류 체계·정답 형식·품질 설계 → 모델 계획 → 현황과 다음 단계.")

    # 2 Theisen 2023: the paper and its method
    s = D.slide("Literature review: Theisen et al. (2023)",
                "Delft Schweidtmann 그룹의 논문. 이 그룹에서 '공정도 이미지 → 그래프'를 다룬 저널 논문은 이것 하나이고, 전신은 2022년 ESCAPE 학회 논문(Schulze Balhorn et al.). "
                "그룹의 나머지 연구(SFILES 2.0, 플로우시트 자동완성, LLM 제어구조 생성, pyDEXPI, P&ID 자동 교정)는 이미 그래프가 된 뒤의 일이라 이미지 단계는 이 논문에만 있음. "
                "후속 디지털화는 DigiCo라는 상용 프로토타입(P&ID)으로 갔고 논문은 없음(모델 구조 비공개; Max에게 물어볼 수 있음).\n"
                "예상 질문 — '최근 논문 없나?': 2026 Digital Discovery 'Text-to-flowsheet'(ETH Zürich, Bardow 그룹)는 텍스트 설명 → 그래프 → Aspen 시뮬레이션. 이미지 단계가 아니고 다른 그룹.\n"
                "'Faster R-CNN은 옛날 모델 아니냐': 2022년 투고라 가능했던 선택. 우리는 재현용 baseline으로만 쓰고 본 모델은 최신 검출기(뒤 슬라이드).\n"
                "'Max 데이터 요청했나': 데이터는 필요 없음(화공 클래스가 안 겹치고 이미지 재배포 불가). 연결 복원 코드와 클래스 정의 문서만 요청할 생각.\n"
                "'왜 P&ID가 아니라 PFD': P&ID는 시공 문서(배관·밸브·계기), PFD는 공정 구성 — 우리 목적(시뮬레이터 모델)에 맞는 수준이 PFD. 문헌 속 지식은 전부 PFD 형태. "
                "P&ID 쪽은 표준 기호라 방법이 성숙(PID2Graph 공개 벤치마크)하고 새 P&ID는 DEXPI로 바로 나옴. 하수처리장 P&ID 디지털화 논문도 없음.")
    bullets_box(s, [(0, "Digitization of chemical PFDs — Digital Chemical Engineering 6 (2023), TU Delft, Schweidtmann group"),
                    (1, "1,005장의 화공 PFD를 저널·책·백과사전·웹에서 모아 라벨링 (비공개)"),
                    (1, "47개 클래스: 장치를 종류와 그리는 양식별로 나눔 (tank1–4, pump1–3 …)"),
                    (1, "① Faster R-CNN으로 장치 검출 (AP50 88 %, AP 68 %) → ② 픽셀 탐색으로 연결 복원 → 그래프")], h=1.55, sizes=(17, 15, 13))
    x1, y1, w1, h1, _ = picture(s, V2 / "max_page1_header.png", 2.45, 6.1, 3.4, x=0.45)
    caption(s, "the paper's first page (CC BY 4.0).", y1 + h1 + 0.05, x=0.52, w=w1, size=9)
    x2, y2, w2, h2, _ = picture(s, FIG / "max_fig3_detection.png", 2.45, 6.3, 3.8, x=6.75)
    caption(s, "Theisen et al. Fig. 3 — (a) flowsheet, (b) detected units, (c) skeletonized streams, (d) graph.", y2 + h2 + 0.05, x=6.55, w=6.4, size=9)

    # 3 what we take, their result, the gaps
    s = D.slide("Literature review: what we take, what is missing",
                "가져온 원칙 둘: ① 그리는 양식이 다르면 같은 장치도 다르게 보인다(Fig. 2: 열교환기 하나를 23가지로) → 우리는 양식을 별도 속성으로 기록. "
                "② 작은 기호(밸브, 화살촉, 스트림 태그)의 AP가 낮고(Table 4), 화살촉을 놓치면 흐름 방향이 틀린다 → 화살촉 클래스 + 방향 정확도 지표.\n"
                "결과: 검출은 AP로 보고(AP50 88.4, AP 68.3). 연결 복원은 Fig. 7 같은 예시 그림뿐이고 '몇 개 중 몇 개를 맞혔다'는 숫자가 없음 — 연결 정답을 만들지 않았기 때문.\n"
                "빈자리 셋: 공개 데이터 없음(라이선스 구분 없이 수집), 그래프(연결) 정답 없음, 연결 정량 지표 없음. 이 셋이 우리 기여의 뼈대.")
    bullets_box(s, [(0, "가져온 원칙 → 우리 설계"),
                    (1, "그리는 양식이 다르면 같은 장치도 다르게 보인다 (Fig. 2)  →  양식(drawing style)을 별도 속성으로 기록"),
                    (1, "작은 기호와 화살촉이 어렵고, 화살촉을 놓치면 방향이 틀린다 (Table 4)  →  화살촉 클래스 + 방향 정확도 지표"),
                    (0, "결과 보고: 검출은 AP50 88 % / AP 68 %로 정량.  연결 복원은 예시 그림만, 정량 평가 없음")], h=1.75, sizes=(17, 14, 13))
    xa, ya, wa, ha, _ = picture(s, FIG / "max_fig2_heat_exchangers.png", 2.65, 5.4, 3.0, x=0.6)
    caption(s, "Fig. 2 — one heat exchanger, 23 drawings.", ya + ha + 0.03, x=0.5, w=wa + 0.2, size=9)
    xb, yb, wb, hb, _ = picture(s, FIG / "max_fig7_graph.png", 2.65, 6.9, 3.0, x=6.1)
    caption(s, "Fig. 7 — the paper's connectivity result: a graph overlaid on one flowsheet (qualitative only).", yb + hb + 0.03, x=6.0, w=7.0, size=9)
    takeaway(s, "빈자리 셋: 공개 데이터 · 그래프(연결) 정답 · 연결의 정량 지표 — 우리 벤치마크가 채우는 자리", 6.05, 17)

    # 4 framework overview
    s = D.slide("What we are building: overview",
                "안내도. 윗줄 벤치마크 구축(수집 → 분류 체계 → 파일럿 → 판정 → 본 어노테이션), 가운데 정답과 채점(그래프 정답, 평가, 후속 활용), "
                "아랫줄 같은 시험 세트로 비교할 모델들. 보라 테두리가 산출물(로컬 학습). VLM은 점선 — 라벨 없이 얻는 하한선일 뿐 결과물이 아님. "
                "이후 슬라이드가 상자 하나씩에 해당. 끝에 같은 그림을 진행 상태와 함께 다시 보여 드림.")
    bullets_box(s, [(0, "틀은 Theisen과 같은 두 단계(장치 검출 → 연결 복원). 다른 것은 공개 벤치마크, 그래프 정답, 같은 잣대로 비교할 모델들"),
                    (1, "산출물 = 벤치마크(이미지 + 사람 라벨 + 채점 코드) + 우리 라벨로 학습한 로컬 모델.  VLM은 라벨 없는 하한선(대조군)")], h=1.2, sizes=(17, 14, 13))
    xf, yf, wf, hf, _ = picture(s, V2 / "fig_framework.png", 2.0, 12.3, 4.55)
    caption(s, "Three layers: benchmark construction → ground truth and scoring → models compared on the same test split.", yf + hf + 0.03, size=9)

    # 5 data collection
    s = D.slide("Materials & Methods: data collection",
                "6개 출처: 특허(US·KR·CN), 오픈액세스 논문 두 경로(PMC, OpenAlex), 미국 EPA 설계 매뉴얼, Wikimedia Commons, 한국 지자체·공단 자료. "
                "모든 파일에 출처·해시·라이선스 기록 → 재배포 가능(tier A) 776 / 내부용(tier B) 217. 한국 지자체 자료는 전부 내부용. "
                "선별: AI(비전 LLM)가 3,114장을 채택/보류/제외로 1차 분류, 사람이 무작위 30장씩 검사(채택 정밀도 ≈ 0.90, 제외에서 놓친 공정도 0), 보류 632장은 사람이 재검토. "
                "본 세트 993장 = 처리장 전체 공정도 774 + 파일럿·실험 105 + 슬러지 공정만 45 + 기타 42 + 정수 27. 보조·대기 626장(단일 장치, 그림풍, 타 도메인, 잘라내기 대기 223 중 38장 수작업 남음).\n"
                "'774장이면 충분한가': Theisen이 1,005장(박스만). 우리는 993장에 그래프 정답까지 — 규모는 비슷하고 정답은 더 많음. 드문 클래스의 인스턴스 수가 관건(본 어노테이션 규모 결정과 연결).")
    bullets_box(s, [(0, "출처 6곳에서 자동 수집 + 사람 라벨 (Theisen 방식), 모든 이미지에 출처·라이선스 기록, 중복 제거 → 3,273장"),
                    (1, "AI 1차 선별 → 사람 표본 검사(정확도 약 90 %)와 최종 확정 → 본 세트 993장 (재배포 가능 776 / 내부용 217)")], h=1.15, sizes=(17, 14, 13))
    xs_, ys_, ws_, hs_, _ = picture(s, FIG / "fig_sources.png", 1.95, 8.6, 2.45)
    caption(s, "Records per source and screening outcome (left); composition of the main set (right).", ys_ + hs_ + 0.0, size=9)
    # four real examples
    ex = [(V2 / "ex_kr_patent_box.png", "KR patent · Korean · box-form"), (V2 / "ex_en_paper_symbol.png", "OA paper · English · symbol-form"),
          (V2 / "ex_epa_manual.png", "US EPA manual · English · box + symbol"), (V2 / "ex_pictorial.png", "OA paper · English · pictorial")]
    xe = 0.55; wcell = 3.0; ytop = 4.78; hmax = 1.25
    for p, cap in ex:
        _, _, w, h, _ = picture(s, p, ytop, wcell, hmax, x=xe + (wcell - min(wcell, hmax * Image.open(p).width / Image.open(p).height)) / 2)
        textbox(s, xe, ytop + hmax + 0.02, wcell, 0.3, [(cap, False, 9, GREY)], align=PP_ALIGN.CENTER)
        xe += wcell + 0.1
    textbox(s, 0.52, 6.4, 12.29, 0.35, [("수집한 그림 실물 4장: 같은 '하수처리장 공정도'라도 출처·언어·그리는 방식이 이렇게 다르다", True, 13, RED)], align=PP_ALIGN.CENTER)

    # 6 why WWTP diagrams differ (merged 7 + 8)
    s = D.slide("Results: why WWTP diagrams differ from chemical PFDs",
                "왼쪽(어떻게 그려지나): 박스형이 40~48 %(예비 수치: 본 세트 무작위 40장은 저자 분류, 파일럿 60장은 추출 시 분류; 어노테이션의 diagram_style로 확정). "
                "같은 포기조가 위 그림에서는 글자뿐인 네모, 아래 그림에서는 구역이 있는 탱크 기호. 모양이 클래스를 말해 주지 않으므로 Theisen의 전제가 절반에서 무너짐 → 클래스는 의미로, 양식은 속성으로.\n"
                "오른쪽(무엇이 그려지나): 캡션 용어 집계(993장)에서 생물학적 처리가 지배, 열교환기 1건·증류탑 0·압축기 0 → 47 클래스 재사용 불가. "
                "그리고 반송 흐름(내부 반송, 외부 반송)과 구역(혐기·무산소·호기)이 공정 구성(A2O vs MLE vs UCT)을 정함 → 그래프에 구역과 반송이 들어가야 시뮬레이터 모델로 감. "
                "부록에 양식 분포와 용어 빈도 막대 그림.")
    # left column
    textbox(s, 0.52, 0.86, 6.1, 0.4, [("어떻게 그려지나 — 박스형 40~48 %: 모양에 클래스 정보가 없다", True, 14)])
    xl, yl, wl, hl, sl = picture(s, V2 / "ex_kr_patent_box.png", 1.3, 6.0, 2.6, x=0.6)
    mx, my, mw, mh = img_px_to_in((414, 437, 657, 489), xl, yl, sl); mark(s, mx, my, mw, mh)
    textbox(s, mx - 1.35, my - 0.05, 1.3, 0.35, [("호기조 (글자만) →", True, 10, RED)], align=PP_ALIGN.RIGHT)
    xl2, yl2, wl2, hl2, sl2 = picture(s, V2 / "ex_en_paper_symbol.png", 4.0, 6.0, 1.65, x=0.6)
    mx, my, mw, mh = img_px_to_in((418, 148, 738, 262), xl2, yl2, sl2); mark(s, mx, my, mw, mh)
    textbox(s, mx, my + mh + 0.0, 1.3, 0.35, [("호기조 (기호)", True, 10, RED)])
    caption(s, "same unit (aeration / aerobic zone): a labelled rectangle in a Korean patent (top) vs a tank symbol with zones in a paper (bottom).", 5.72, x=0.52, w=6.2, align=PP_ALIGN.LEFT, size=9)
    textbox(s, 0.52, 6.12, 6.2, 0.5, [("→ 클래스는 의미(33개)로, 그리는 양식은 별도 속성으로. 글자와 문맥이 의미를 정한다", True, 12, RED)])
    # right column
    textbox(s, 6.9, 0.86, 6.0, 0.4, [("무엇이 그려지나 — 생물 처리 중심, 구역과 반송이 공정을 정한다", True, 14)])
    xr, yr, wr, hr, sr = picture(s, V2 / "ex_aao_recycles.png", 1.3, 6.0, 2.2, x=6.95)
    mark(s, *img_px_to_in((770, 85, 862, 340), xr, yr, sr))           # AAO box
    mark(s, *img_px_to_in((780, 340, 930, 470), xr, yr, sr), dash=True)   # internal recycle
    mark(s, *img_px_to_in((85, 440, 1000, 505), xr, yr, sr), dash=True)   # external recycle
    caption(s, "box-form plant with 'AAO' (three zones collapsed into one box), internal recycle and external (sludge) recycle drawn as lines.", yr + hr + 0.02, x=6.85, w=6.1, align=PP_ALIGN.LEFT, size=9)
    table(s, ["caption term (993 images)", "count"], [["aeration tank / bioreactor", "264"], ["MBR", "83"], ["anoxic / anaerobic zone", "75"], ["recycle (RAS / internal)", "60"],
                                                       ["heat exchanger", "1"], ["distillation column / compressor", "0"]],
          x=6.95, y=4.05, w=5.9, col_w=[4.4, 1.5], size=10, row_h=0.27)
    textbox(s, 6.9, 6.12, 6.1, 0.5, [("→ Theisen 47 클래스는 재사용 불가. 그래프에 구역·반송이 있어야 시뮬레이터 모델에 닿는다", True, 12, RED)])

    # 7 taxonomy
    s = D.slide("Materials & Methods: taxonomy v1.1",
                "L1 7단계(+ 부대 설비, 종류 미상, 연결 요소) → L2 33 클래스(31 + 종류 미상 2) → L3 하위형은 시뮬레이터 모델이 다를 때만(생물막 반응기 6종, 혐기성 반응기 6종). "
                "연결·주석 요소 8종은 장치가 아닌 상자(단자, 분기, 합류, 계기, 화살촉, 글자, 흐름 태그·라벨) → 검출기가 찾는 상자 종류는 33 + 8 = 41.\n"
                "'왜 33개인가': ① 모양 또는 글자로 구별 가능할 것, ② 학습 50 + 평가 20 인스턴스 이상 예상(Theisen에서 송풍기 35개는 학습이 안 됨), ③ 시뮬레이터에서 다른 모델일 것. "
                "Theisen 47개는 모양별 분할, 우리 33개는 의미별이고 모양은 속성.\n"
                "'MBR·SBR처럼 한 상자가 여러 구역을 겸하면': 막 분리는 mbr_unit, 구역은 *_zone으로 따로; 박스형에 'MBR' 한 상자면 mbr_unit 하나.\n"
                "검토 세 번(일반 → 도메인 → 심사자 관점) 뒤 11/16 확정(git tag). 이후 변경은 기록만, 클래스 수 불변. 전체 33 클래스 표는 부록.")
    bullets_box(s, [(0, "L1 공정 단계 7 → L2 단위공정 33 (의미 기준, 양식은 속성) → L3 하위형은 시뮬레이터 모델이 다를 때만;  연결·주석 요소 8"),
                    (1, "Theisen 47개는 모양별로 쪼갠 것. 우리 33개는 의미별이라 박스형과 기호형의 포기조가 같은 클래스.  2026-11-16 버전 확정")], h=1.15, sizes=(17, 14, 13))
    xt, yt, wt, ht, _ = picture(s, V2 / "fig_taxonomy_tree.png", 1.95, 12.3, 3.0)
    # evidence box + criteria line
    textbox(s, 0.6, 5.05, 6.0, 1.25, [("클래스 선정 근거", True, 12), ("우리 데이터: 캡션 용어 빈도 (993장)", False, 11), ("선행 분류 체계: Theisen 2023, PID2Graph", False, 11),
                                       ("표준: ISO 10628, DEXPI   ·   시뮬레이터 단위: QSDsan, GPS-X, SUMO", False, 11), ("교과서: Metcalf & Eddy, MOP 8", False, 11)],
            border=GREY)
    textbox(s, 6.8, 5.05, 6.0, 1.25, [("선정 기준", True, 12), ("① 모양 또는 글자로 구별 가능", False, 11), ("② 학습 50 + 평가 20 인스턴스 이상 예상", False, 11),
                                       ("③ 시뮬레이터 모델이 다르면 하위형(L3)으로", False, 11), ("세 번 검토(일반 → 도메인 → 심사자) 후 확정", False, 11, GREY)], border=GREY)

    # 8 ground-truth format
    s = D.slide("Materials & Methods: ground-truth format",
                "이미지 한 장의 정답은 박스 목록이 아니라 그래프: 노드(박스 + 클래스 + 속성) + 방향 있는 엣지(출발 → 도착, 방향 근거, 흐름 종류, 역할). "
                "그림은 파일럿 60장 중 한 장(KAUST MBR)을 제가 판정자로서 직접 라벨링한 예. 구역(무산소·호기)은 소속 탱크(종류 미상 + 단계 힌트) 안의 점선 박스; 구역 사이는 선이 없어도 혼합액이 흐르는 것으로 봄. "
                "단자(유입·방류·슬러지 배출), 분기·합류점, 계기도 노드. 약품 주입은 장치가 아니라 엣지 — 시뮬레이터에서 약품은 유입 스트림이지 단위공정이 아니고, 주입점을 장치로 세면 박스 수가 늘고 일치도가 떨어짐.\n"
                "흐름 종류(물·슬러지·가스)와 역할(유입·반송 등)은 어노테이터가 고르지 않고 양 끝 클래스로부터 규칙 33개가 채움(어떤 모델의 예측 그래프에도 사후 적용). 판정자가 20장에서 규칙 결과 검토. "
                "채점은 필수 항목(클래스, 박스, 엣지 방향)만; 확신도·읽은 글자 같은 보조 항목은 기록만.")
    bullets_box(s, [(0, "이미지 한 장 = 노드(박스 + 클래스 + 속성) + 방향 있는 엣지(출발 → 도착, 방향 근거, 흐름 종류, 역할)"),
                    (1, "유입·방류 단자, 분기·합류점, 계기도 노드.  약품 주입은 장치가 아니라 엣지.  흐름 종류·역할은 양 끝 클래스에서 규칙으로 채움")], h=1.1, sizes=(17, 14, 13))
    xg, yg, wg, hg, _ = picture(s, V2 / "gt_overlay_pilot44.png", 1.95, 8.2, 3.6, x=0.45)
    caption(s, "one pilot image hand-labelled by the adjudicator: units (blue), zones inside a parent tank (green, dashed), terminals (orange), edges (magenta).", yg + hg + 0.02, x=0.52, w=8.0, align=PP_ALIGN.LEFT, size=9)
    table(s, ["what one edge carries", "example"], [["from → to", "mbr_unit → anoxic_zone"], ["direction evidence", "arrowhead seen"], ["medium (rule)", "mixed liquor"],
                                                   ["role (rule)", "internal recycle"], ["scored?", "direction: yes · medium/role: checked on 20 images"]],
          x=8.75, y=2.0, w=4.1, col_w=[1.6, 2.5], size=10, row_h=0.42)
    takeaway(s, "시뮬레이터 플로우시트에 대응되는 것은 박스가 아니라 그래프", 6.05, 17)

    # 9 quality-assurance design (pilot)
    n_line = "진행 중"
    if prog is not None:
        n_line = f"진행 중 (A {prog[0]}/60, B {prog[1]}/60)"
    s = D.slide("Materials & Methods: annotation quality design (pilot)",
                "파일럿의 목적은 데이터가 아니라 '가이드라인과 분류 체계가 사람 사이에서 재현되는지' 검증. 두 명이 서로 못 보게 같은 60장을 라벨링, 제가 판정자로 불일치를 하나씩 가려 규칙이 모호했던 곳을 고침(가이드라인 v2).\n"
                "κ ≥ 0.8은 Landis & Koch 기준 '거의 완전한 일치'. 60장: 장당 박스 약 15개 → 약 900개 비교라 κ 신뢰구간이 충분히 좁고, 두 명 × 60장 × 8~15분이면 각각 하루 반 — 연구실 구성원 두 명이 그 정도 시간을 도와주고 있음(감사의 글 또는 기여도에 따라 공저, 교수님 의견 여쭘).\n"
                "층화 추출: 출처별 제곱근 배분(작은 출처도 들어감), 문서당 1장, 출처마다 비영어 1장 이상. 쉬운 버전: 완전판은 장당 클릭 60회·15분이라 1~20번만 완전판(화살촉·글자 포함), 21~60번은 장치·구역·단자·분기 + 엣지 방향만. "
                "통계(κ, 엣지 F1)는 60장 전부에서, 화살촉·글자 일치도는 20장에서.\n"
                "도구 Label Studio(오픈소스, 로컬 → 데이터 비공개, 박스·속성·엣지를 한 화면에서; Theisen의 LabelImg는 박스만). 원격은 임시 터널 — 본 어노테이션은 랩 서버·개인 계정(다음 주 결정). "
                "분석·평가 코드는 합성 데이터로 끝까지 검증 완료. 결과는 다음 미팅.")
    bullets_box(s, [(0, "같은 60장을 두 명이 독립 라벨링, 판정자 1명 → 일치도(κ ≥ 0.8 목표, 거의 완전한 일치) → 판정표 → 가이드라인 v2"),
                    (1, "60장 층화 추출(출처별 제곱근 배분, 문서당 1장, 비영어 포함).  1~20번 완전판, 21~60번 쉬운 버전(장치·구역·단자 + 엣지 방향) — 같은 통계를 절반의 시간에"),
                    (1, f"도구 Label Studio(로컬·무료), 매뉴얼 2종 + 요약 카드 + 2시간 교육, 원격 접속(임시 터널).  분석·평가 코드 준비 완료.  11/19 교육 완료 → {n_line}")], h=1.75, sizes=(16, 13, 12))
    xp, yp, wp, hp, _ = picture(s, V2 / "fig_pilot_process.png", 2.7, 6.0, 3.3, x=0.52)
    caption(s, "pilot procedure.", yp + hp + 0.02, x=0.52, w=6.0, align=PP_ALIGN.LEFT, size=9)
    shot = V2 / "ls_screen.png" if (V2 / "ls_screen.png").exists() else MF / "F2_ui_callouts.png"
    xq, yq, wq, hq, _ = picture(s, shot, 2.7, 6.2, 3.3, x=6.75)
    caption(s, "annotator's screen: class buttons = taxonomy, per-box attributes, edge drawing.", yq + hq + 0.02, x=6.75, w=6.2, align=PP_ALIGN.LEFT, size=9)

    # 10 comparison table (moved to the end of M&M)
    s = D.slide("Materials & Methods: Theisen (2023) vs this work",
                "지금까지 설명한 것을 한 표로. 틀은 같고(두 단계), 데이터·클래스·정답·평가·후속 활용이 다름. "
                "표 문구는 논문 원문 기준: Theisen은 라벨러 수나 일치도를 보고하지 않음(능동 학습 보조 + 수동 교정, LabelImg); 이미지는 저널·책·Ullmann 백과사전·구글에서 수집.")
    bullets_box(s, [(0, "틀은 같다 (장치 검출 → 연결 복원). 다른 것은 데이터, 클래스, 정답, 평가, 후속 활용")], h=0.5, sizes=(17, 14, 13))
    table(s, ["Item", "Theisen et al. 2023 (chemical PFD)", "This work (WWTP PFD)"],
          [["Data", "1,005 PFDs from journals, books, an encyclopedia and web search; not public", "993 main images, 6 sources incl. patents / EPA / municipal; licence recorded; public release"],
           ["Classes", "47, split by drawing style", "33 semantic classes + 8 connection elements; drawing style as an attribute; sub-types by simulator model"],
           ["Box-form diagrams", "out of scope", "40–48 %: generic class + stage hint + text; box-form mapping accuracy"],
           ["Zones / recycles", "none", "zone boxes with parent tank; recycle roles; configuration table (A2O / MLE / UCT)"],
           ["Connectivity ground truth", "none (examples only)", "edge ground truth (direction, medium, role); edge P/R/F1, direction accuracy, graph edit distance"],
           ["Label quality", "no agreement measurement reported", "two independent annotators + adjudication; κ, edge F1 with CI; human upper bound"],
           ["Models", "Faster R-CNN + pixel search", "Faster R-CNN reproduction, modern detector, pixel search vs learned vs VLM; taxonomy ablations"],
           ["Downstream use & format", "none", "ground-truth format published as a JSON schema; graph → QSDsan converter; executability check"]],
          x=0.65, y=1.45, w=12.0, col_w=[2.0, 4.1, 5.9], size=10.5, row_h=0.56)

    # 11 baselines and the local-model plan
    s = D.slide("Materials & Methods: baselines and the local-model plan",
                "지시 2(로컬 모델)에 대한 답. 산출물은 우리 라벨로 학습한 로컬 모델. VLM(Claude 등)은 대조군: 라벨 없이 기성 AI가 얼마나 하는지를 재야 '라벨의 가치'를 숫자로 보임. "
                "심사자가 2026년에 반드시 묻는 질문이기도 함. 비용은 60장에 3~6달러. 원치 않으시면 빼도 논문은 성립(학습 곡선의 0점만 사라짐).\n"
                "연결 복원 3방식 비교: 픽셀 탐색(Theisen) vs 학습 기반(본 방법: 검출된 노드 쌍 사이의 연결·방향을 예측) vs VLM. PID2Graph(P&ID)에서는 학습 기반이 모듈식보다 엣지 정확도 25 %p 이상 높았음.\n"
                "용어: ablation = 설계 요소를 하나씩 빼고 재학습해 가치를 재는 실험(33 vs 7 클래스, 양식 속성 유무, 구역 박스 유무). human upper bound = 두 어노테이터 일치도 = 모델이 도달 가능한 최대치. "
                "learning curve = 라벨 50/100/200/전부로 학습했을 때 성능(라벨이 몇 장이면 충분한가).\n"
                "시기·자원: 본 어노테이션 후 12~1월, 랩 GPU 1장(Faster R-CNN 재현은 RTX 3090 한 장에 약 3시간).")
    bullets_box(s, [(0, "산출물은 우리 라벨로 학습한 로컬 모델.  VLM은 라벨 없는 하한선(대조군)으로만 사용"),
                    (1, "연결 복원은 3방식 비교: 픽셀 탐색(Theisen) vs 학습 기반(본 방법) vs VLM.  분류 체계 설계 요소 제거 실험, 라벨 수에 따른 성능")], h=1.15, sizes=(17, 14, 13))
    xl_, yl_, wl_, hl_, _ = picture(s, V2 / "fig_ladder.png", 1.95, 5.6, 4.0, x=0.6)
    table(s, ["Model", "Trained on our labels", "Role"],
          [["VLM zero-shot (class list given, no training)", "no", "no-label floor; control for the value of labels"],
           ["Faster R-CNN (Theisen settings)", "yes", "reproduction baseline"],
           ["Modern detector (YOLO / DETR family)", "yes", "main detector"],
           ["Learned graph recovery (vs pixel search)", "yes", "main connectivity method"],
           ["Human upper bound", "—", "annotator agreement: the ceiling"]],
          x=6.5, y=2.0, w=6.3, col_w=[3.0, 1.2, 2.1], size=10, row_h=0.46)
    textbox(s, 6.5, 4.95, 6.3, 0.9, [("시기·자원: 본 어노테이션 뒤 12~1월, 랩 GPU 1장(Faster R-CNN 재현 ≈ 3 h / RTX 3090)", False, 12),
                                      ("논문 표: VLM(라벨 0) · 라벨 50/100/200/전부 학습 곡선 · 사람 상한", False, 12)])
    takeaway(s, "지시 2 유지: 보고하는 모델은 로컬.  API 모델은 라벨이 더하는 것을 재는 대조군일 뿐", 6.05, 17)

    # 12 framework with status
    s = D.slide("Status: where we are on the overall plan",
                "같은 그림에 진행 상태. 완료(체크): 수집·선별, 분류 체계, 그래프 정답 양식과 평가 코드(합성 데이터로 검증). 진행 중(빗금): 파일럿 어노테이션, VLM 기준선 코드(실행 대기). "
                "남은 것(점선): 판정·가이드라인 v2, 본 어노테이션, 후속 활용 변환기, 학습 모델들, 사람 상한(파일럿 결과에서 나옴).")
    bullets_box(s, [(0, "완료: 수집·선별, 분류 체계, 정답 양식·평가 코드.  진행 중: 파일럿 어노테이션.  남은 것: 판정, 본 어노테이션, 모델 학습, 후속 활용")], h=0.6, sizes=(17, 14, 13))
    xs2, ys2, ws2, hs2, _ = picture(s, V2 / "fig_framework_status.png", 1.5, 12.3, 5.2)

    # 13 phase flow
    s = D.slide("Future works: next steps",
                "날짜 대신 순서와 대략 기간. 다음 미팅에 파일럿 결과(κ, 판정표, 장당 시간)와 함께 본 어노테이션 규모·인력·서버를 결정 요청. "
                "끝의 갈림길: 2층(벤치마크 + 분석 + 방법 비교 → AEI / Automation in Construction급, 2월 초안) vs 3층(+ QSDsan 자동 변환·실행 검증 + 표준 유입 조건(BSM1)에서 구성별 TEA·LCA 비교 시연 → Water Research 도전, 3월 중순 초안). "
                "후속 활용(QSDsan)이 저널을 가르므로 본 어노테이션 다음 우선순위로 두려 함 — 교수님 의견 여쭘. 'TEA가 그림에서 자동으로 나온다'고는 말하지 않음(유량·농도·단가는 그림에 없음).")
    bullets_box(s, [(0, "다음 2주: 파일럿 라벨링 → 판정·일치도 → 가이드라인 v2.  다음 미팅: 결과와 함께 본 어노테이션 규모·인력·서버 결정"),
                    (1, "그 뒤: 본 어노테이션 → baseline 학습 → 그래프 → QSDsan 변환.  갈림길: 2층 초안(AEI급) / 3층(+ 실행 검증·TEA 시연, Water Research 도전)")], h=1.15, sizes=(17, 14, 13))
    xp2, yp2, wp2, hp2, _ = picture(s, V2 / "fig_phase_flow.png", 2.2, 12.3, 3.6)
    textbox(s, 0.52, 6.0, 12.29, 0.6, [("여쭙고 싶은 것: 후속 활용 범위(QSDsan 실행 검증 · TEA 시연)를 어디까지 넣을지 → 목표 저널", True, 15, RED)], align=PP_ALIGN.CENTER)

    # 14 thanks
    s = D.slide("", "")
    textbox(s, 1.0, 3.0, 11.3, 1.0, [("Thank You for Your Kind Attention", True)], 32, RGBColor(0x1F, 0x4E, 0x79), PP_ALIGN.CENTER)

    # ---------------------------------------------------------------- appendix
    s = D.slide("Appendix A: drawing styles and unit-process terms", "부록. 양식 분포(예비 분류)와 캡션 용어 빈도 상위 12개 + 화공 핵심 장치 부재.")
    xa1, ya1, wa1, ha1, _ = picture(s, V2 / "fig_style_shares.png", 1.1, 6.1, 4.3, x=0.52)
    caption(s, "drawing-style shares (preliminary, author's classification).", ya1 + ha1 + 0.02, x=0.52, w=6.1, align=PP_ALIGN.LEFT, size=9)
    xa2, ya2, wa2, ha2, _ = picture(s, V2 / "fig_terms_top12.png", 1.1, 6.3, 4.6, x=6.75)
    caption(s, "unit-process terms in captions / titles of the main set (regex count; ranking only).", ya2 + ha2 + 0.02, x=6.75, w=6.2, align=PP_ALIGN.LEFT, size=9)

    s = D.slide("Appendix B: the 33 unit-process classes (taxonomy v1.1)", "부록. 전체 클래스 표: 영문 id, 한글, L1, 필수 L3 하위형, 예상 빈도.")
    tx = yaml.safe_load((ROOT / "data_collection" / "annotation" / "classes.yaml").read_text(encoding="utf-8"))
    l1ko = {d["id"]: d["ko"] for d in tx["l1"]}
    rows = []
    for name, c in tx["classes"].items():
        l3list = (c.get("l3") or {}).get("required") or []
        l3 = ", ".join(x.replace("_", " ") for x in l3list)
        rows.append([name.replace("_", " "), c.get("ko", ""), l1ko.get(c["l1"], c["l1"]), (f"{len(l3list)}: " + l3) if l3list else "—", c.get("expected_freq", "")])
    half = (len(rows) + 1) // 2
    table(s, ["class", "한글", "L1", "required L3", "freq"], rows[:half], x=0.4, y=0.9, w=6.2, col_w=[1.7, 1.45, 1.0, 1.6, 0.45], size=7.5, row_h=0.29, header_size=8)
    table(s, ["class", "한글", "L1", "required L3", "freq"], rows[half:], x=6.75, y=0.9, w=6.2, col_w=[1.7, 1.45, 1.0, 1.6, 0.45], size=7.5, row_h=0.29, header_size=8)

    s = D.slide("Appendix C: pilot sample, tools, training, remote setup",
                "부록. 출처별 배분(제곱근 배분, 비영어 포함), 도구와 교육 자료, 원격 구성(임시).")
    table(s, ["source", "main images", "drawn", "non-English"],
          [["Patents (US / KR / CN)", "342", "16", "11"], ["PMC OA papers", "325", "16", "0"], ["Other OA papers", "178", "11", "1"], ["US EPA manuals", "90", "8", "0"],
           ["Wikimedia Commons", "36", "5", "1"], ["Korean municipal", "22", "4", "4"], ["total", "993", "60", "17"]],
          x=0.6, y=1.0, w=5.6, col_w=[2.6, 1.0, 1.0, 1.0], size=10, row_h=0.36)
    bullets_box(s, [(0, "Tools"), (1, "Label Studio (open source, local): taxonomy as the labelling screen; one project per annotator (results hidden from each other); practice project (5 images)"),
                    (1, "Manual 17 p (9 figures), lite manual 9 p, one-page cheat sheet, 2-hour training guide with 5 practice images and expected questions"),
                    (0, "Remote setup (pilot, temporary)"),
                    (1, "Server on the adjudicator's laptop (NL) → temporary public URL (tunnel) → annotators in Korea in a browser, nothing to install; daily DB backup"),
                    (1, "Main annotation: Label Studio on the lab Linux server, always on, individual accounts (to decide)")],
                x=6.5, y=1.0, w=6.4, h=4.5, sizes=(13, 11, 10))
    xa3, ya3, wa3, ha3, _ = picture(s, MF / "F2_ui_callouts.png", 4.1, 5.6, 2.6, x=0.6)
    caption(s, "annotator screen with callouts (manual Fig. 2).", ya3 + ha3 + 0.02, x=0.6, w=5.6, align=PP_ALIGN.LEFT, size=9)
    D.save()


if __name__ == "__main__":
    build()
