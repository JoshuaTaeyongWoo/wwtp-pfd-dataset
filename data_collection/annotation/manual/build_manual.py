"""
build_manual.py — annotator manual (Korean, beginner-friendly) as a Word document.

Source of truth: docs/annotation_guideline_v1.md + annotation/classes.yaml (taxonomy v1.1a).
Figures: make_manual_figures.py -> figures/*.png.
Output: annotation/manual/WWTP_annotation_manual_v1.docx  (PDF via Word COM, see README_pilot)
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
OUT = HERE / "WWTP_annotation_manual_v1.docx"
KO = "Malgun Gothic"
MONO = "Consolas"
ACCENT = RGBColor(0x0F, 0x7B, 0x6C)
GREY = RGBColor(0x5C, 0x6B, 0x75)
RED = RGBColor(0xC0, 0x39, 0x2B)


def set_font(run, size=10.5, bold=False, color=None, mono=False, italic=False):
    run.font.name = MONO if mono else KO
    run._element.rPr.rFonts.set(qn("w:eastAsia"), KO)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def shade(cell, hex_fill):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


class Doc:
    def __init__(self):
        self.d = Document()
        sec = self.d.sections[0]
        sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
        for side in ("left_margin", "right_margin"):
            setattr(sec, side, Cm(2.0))
        sec.top_margin, sec.bottom_margin = Cm(2.0), Cm(1.8)
        st = self.d.styles["Normal"]
        st.font.name = KO; st.element.rPr.rFonts.set(qn("w:eastAsia"), KO); st.font.size = Pt(10.5)
        st.paragraph_format.space_after = Pt(4); st.paragraph_format.line_spacing = 1.25
        for lvl, size in ((1, 16), (2, 13), (3, 11.5)):
            hs = self.d.styles[f"Heading {lvl}"]
            hs.font.name = KO; hs.element.rPr.rFonts.set(qn("w:eastAsia"), KO); hs.font.size = Pt(size)
            hs.font.color.rgb = ACCENT if lvl < 3 else RGBColor(0x1B, 0x2A, 0x33); hs.font.bold = True
            hs.paragraph_format.space_before = Pt(14 if lvl == 1 else 10); hs.paragraph_format.space_after = Pt(4)

    # -- primitives
    def h(self, text, lvl=1):
        return self.d.add_heading(text, lvl)

    def p(self, text="", size=10.5, bold=False, color=None, align=None, italic=False):
        para = self.d.add_paragraph()
        self._runs(para, text, size, bold, color, italic)
        if align == "center":
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return para

    def _runs(self, para, text, size=10.5, bold=False, color=None, italic=False):
        """`code` segments become monospace runs; **bold** segments become bold."""
        import re
        for tok in re.split(r"(`[^`]+`|\*\*[^*]+\*\*)", text):
            if not tok:
                continue
            if tok.startswith("`"):
                set_font(para.add_run(tok[1:-1]), size, bold, RGBColor(0x1B, 0x4F, 0x72), mono=True)
            elif tok.startswith("**"):
                set_font(para.add_run(tok[2:-2]), size, True, color, italic=italic)
            else:
                set_font(para.add_run(tok), size, bold, color, italic=italic)

    def bullet(self, text, level=0):
        para = self.d.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
        self._runs(para, text)
        para.paragraph_format.space_after = Pt(2)
        return para

    def num(self, text):
        para = self.d.add_paragraph(style="List Number")
        self._runs(para, text)
        para.paragraph_format.space_after = Pt(2)
        return para

    def note(self, text, kind="tip"):
        t = self.d.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = t.rows[0].cells[0]; shade(c, "DDF1EC" if kind == "tip" else "FBEEDB")
        para = c.paragraphs[0]
        set_font(para.add_run(("참고  " if kind == "tip" else "주의  ")), 10, True, ACCENT if kind == "tip" else RGBColor(0xB8, 0x70, 0x1E))
        self._runs(para, text, 10)
        self.d.add_paragraph().paragraph_format.space_after = Pt(0)

    def table(self, header, rows, widths=None, size=9.5, header_fill="E1ECF6"):
        t = self.d.add_table(rows=1, cols=len(header)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, h in enumerate(header):
            c = t.rows[0].cells[i]; shade(c, header_fill)
            c.paragraphs[0].text = ""; set_font(c.paragraphs[0].add_run(h), size, True)
        for r in rows:
            cells = t.add_row().cells
            for i, v in enumerate(r):
                cells[i].paragraphs[0].text = ""
                self._runs(cells[i].paragraphs[0], str(v), size)
        if widths:
            t.autofit = False
            for i, w in enumerate(widths):
                t.columns[i].width = Cm(w)
            for row in t.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Cm(w)
        self.d.add_paragraph().paragraph_format.space_after = Pt(0)
        return t

    def fig(self, name, caption, width_cm=17.0):
        self.d.add_picture(str(FIG / name), width=Cm(width_cm))
        self.d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = self.d.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(cap.add_run(caption), 9, color=GREY)
        cap.paragraph_format.space_after = Pt(8)

    def pagebreak(self):
        self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def build():
    D = Doc()
    # ---------------------------------------------------------------- cover
    D.p()
    D.p("하수처리장 공정도 어노테이션 매뉴얼", 24, True, ACCENT, "center")
    D.p("파일럿용 v1 · 클래스 체계 v1.1a (동결 태그 taxonomy-v1.1 + 2026-11-17 보정)", 11, color=GREY, align="center")
    D.p()
    D.p("대상: 파일럿 어노테이터 2명 · 판정자 1명", 11, align="center")
    D.p("도구: Label Studio (http://localhost:8080) · 표본: pilot_A / pilot_B 각 60장", 11, align="center")
    D.p("작성: WWTP_vision 프로젝트 · 2026-11-17", 10, color=GREY, align="center")
    D.p()
    D.note("이 매뉴얼은 '무엇을, 어떤 이름으로, 어떻게' 표시하는지만 다룹니다. 왜 이런 규칙인지는 `docs/annotation_taxonomy_plan.md`와 `docs/evidence_ledger.md`에 있습니다. 애매하면 규칙대로 가장 가까운 것을 고르고 annotator_note에 한 줄 적어 주세요. 옆 사람과 상의하지 않습니다(두 사람이 얼마나 같게 하는지 재는 것이 파일럿의 목적입니다).")
    D.p("차례", 12, True)
    toc = ["이 작업이 무엇인가", "화면 익히기", "한 장 작업 순서(체크리스트)", "무엇에 박스를 치고, 무엇은 안 치나", "박스 그리는 법",
           "클래스(이름) 고르기", "구역(zone) 다루기", "연결 요소", "흐름 연결(엣지) 기록", "속성 채우기", "예제: 한 장 끝까지",
           "자주 틀리는 것 · 애매할 때", "끝낸 뒤", "부록 A 판별 규칙 22개 요약", "부록 B 클래스 전체 목록"]
    t = D.d.add_table(rows=8, cols=2)
    for i, title in enumerate(toc):
        c = t.rows[i % 8].cells[i // 8]
        c.paragraphs[0].text = ""; set_font(c.paragraphs[0].add_run(f"{i + 1}. {title}"), 10); c.paragraphs[0].paragraph_format.space_after = Pt(1)
    D.pagebreak()

    # ---------------------------------------------------------------- 1
    D.h("1. 이 작업이 무엇인가")
    D.p("하수처리장 공정도(논문·특허·설계 매뉴얼의 흐름도 그림)를 컴퓨터가 읽을 수 있게 만드는 작업입니다. 그림 위의 **장치마다 네모 상자(박스)** 를 치고 **이름(클래스)** 을 붙인 뒤, 장치 사이의 **흐름(화살표)** 을 선으로 연결해 줍니다. 이 데이터로 '그림 → 공정 그래프 → 시뮬레이션 모델'을 자동으로 만드는 인공지능을 학습·평가합니다.")
    D.p("한 장에는 보통 박스 10~15개와 화살표 5~15개가 들어갑니다. 처음에는 한 장에 15분쯤 걸리고, 익숙해지면 8분 안팎입니다.")
    D.fig("F1_workflow.png", "그림 1. 한 장을 끝내는 다섯 단계. 이 순서대로 하면 빠뜨리는 것이 줄어든다.", 17)
    D.p("세 가지만 기억하면 됩니다.", bold=True)
    D.bullet("**빠짐없이**: 그림에 있는 장치·화살촉·글자를 전부 표시합니다. 절반만 하면 학습 데이터로 못 씁니다.")
    D.bullet("**규칙대로 일관되게**: '맞는 답'보다 '같은 상황에 같은 선택'이 중요합니다. 규칙에 없는 판단은 메모로 남깁니다.")
    D.bullet("**그림에 있는 것만**: 그림에 없는 지식(이 공장은 분명 MBR일 거야)을 넣지 않습니다. 모르면 '모름'으로 표시하는 선택지가 항상 있습니다.")

    # ---------------------------------------------------------------- 2
    D.h("2. 화면 익히기")
    D.p("브라우저에서 http://localhost:8080 에 로그인 → Projects → pilot_A(또는 pilot_B) → 목록에서 1번 클릭.")
    D.fig("F2_ui_callouts.png", "그림 2. Label Studio 라벨링 화면. ② 그림 영역 위에 라벨 버튼(색깔 이름 목록)이 있고, 박스를 고르면 ④에 속성 칸이 나타난다.", 17)
    D.fig("F3_label_bar.png", "그림 3. 라벨 버튼 전체. 색은 처리 단계별 묶음, 원문자는 숫자 키 단축키.", 15.5)
    D.table(["키", "하는 일"], [["숫자 1~0", "자주 쓰는 클래스 선택(그림 3의 원문자)"], ["마우스 드래그", "선택한 클래스로 박스 그리기"], ["박스 클릭", "선택 → 오른쪽에 속성 칸 표시"],
                                ["Alt+R", "관계(엣지) 만들기: 출발 박스 선택 → Alt+R → 도착 박스 클릭"], ["Delete", "선택한 박스 삭제"], ["Ctrl+Z / Ctrl+Shift+Z", "되돌리기 / 다시 실행"],
                                ["마우스 휠", "확대·축소(작은 요소는 확대해서 그린다)"], ["Ctrl+Enter", "제출(Submit)하고 다음 장으로"]], [4, 12])

    # ---------------------------------------------------------------- 3
    D.h("3. 한 장 작업 순서(체크리스트)")
    D.p("아래 순서대로 하고, 끝에 체크리스트를 다시 확인한 뒤 Submit 합니다.")
    D.table(["단계", "할 일", "완료 기준"], [
        ["① 장치·구역 박스", "장치마다 박스, 한 탱크 안의 혐기/무산소/호기는 구역마다 박스", "그림의 모든 장치에 박스가 있다"],
        ["② 연결 요소 박스", "화살촉, 글자(장치명·설명·흐름 이름·숫자), 유입·유출 끝, 갈라짐·합침 지점, 계측 기호", "화살촉이 하나도 안 빠졌다"],
        ["③ 박스 속성", "박스마다 visual_form · confidence · label_text; 구역은 is_zone; generic은 l1_hint", "오른쪽 Regions 목록에서 속성 없는 박스가 없다"],
        ["④ 흐름 연결", "출발 → Alt+R → 도착, 관계 라벨(매체|방향)", "모든 화살표가 엣지로 들어갔다"],
        ["⑤ 이미지 속성", "diagram_style · language · n_panels, 공정 이름이 있으면 process_configuration", "세 항목이 모두 채워졌다"],
    ], [3.2, 8.5, 5.3])

    # ---------------------------------------------------------------- 4
    D.h("4. 무엇에 박스를 치고, 무엇은 안 치나")
    D.table(["친다", "안 친다"], [
        ["단위공정 장치 하나하나 (탱크·침전지·여과기·소화조·펌프장 …)", "흐름선 자체 (선은 엣지로만 기록)"],
        ["한 탱크 안의 혐기·무산소·호기 **구역** (각각)", "그림 아래 캡션 문장, 그림 번호(Fig. 3)"],
        ["화살촉 (화살표 끝마다)", "범례(legend) 상자, 표, 축척, 로고"],
        ["글자: 장치 이름·설명, 흐름 이름(RAS, WAS), 숫자(유량·농도·①)", "그림 제목 (예: Wet Weather Treatment Train)"],
        ["플랜트 밖으로 나가고 들어오는 끝 (Influent, 방류, 약품 공급, 다른 그림으로 이어짐)", "배경 사진·사람·차량"],
        ["선이 갈라지는 점·합쳐지는 점, 그려진 분배조", ""],
        ["센서·제어 태그 (DO, pH, F, L …)", ""],
        ["그 외 장치 → `unknown_equipment` + 글자", ""],
    ], [8.5, 8.5])

    # ---------------------------------------------------------------- 5
    D.h("5. 박스 그리는 법")
    D.bullet("장치 윤곽에 **꼭 맞게**. 여백을 크게 두지 않습니다.")
    D.bullet("장치 이름이 박스 **안에** 쓰여 있어도 장치 박스는 그대로 두고, 이름 글자에 `text_label` 박스를 **따로** 하나 더 칩니다(겹쳐도 됩니다).")
    D.bullet("구역 박스는 부모 탱크 박스 안에 들어갑니다. 그 밖에는 서로 겹치지 않게 합니다.")
    D.bullet("점처럼 작은 요소: `arrowhead`는 화살촉만 꼭 맞게. `junction_split`·`junction_merge`는 지점 중심의 작은 정사각형(한 변 12 px 이상). 분배조가 상자로 그려졌으면 그 상자를 감쌉니다.")
    D.bullet("`io_terminal`은 화살표 끝과 거기 붙은 글자(\"Influent\", \"방류\")를 함께 감쌉니다.")
    D.bullet("같은 장치가 N개 나란히 그려졌으면 **N개 모두** 칩니다. \"×4\"라고만 쓰였으면 1개 + `n_parallel_lanes=4`.")
    D.bullet("SBR처럼 한 탱크를 단계(phase)별로 여러 번 그렸으면 패널마다 1개 + `panel_phase`.")

    # ---------------------------------------------------------------- 6
    D.h("6. 클래스(이름) 고르기")
    D.p("아래 표에서 '보이는 것'을 찾아 오른쪽 클래스를 고릅니다. 생물막 반응기와 혐기성 폐수 반응기는 반드시 슬래시 뒤 세부형(L3)까지 고릅니다.")
    D.table(["보이는 것", "클래스", "메모"], [
        ["공기방울·산기관·표면포기기가 있는 생물반응 탱크", "`aerobic_zone`", "포기조·폭기조·oxic·aeration tank 전부. 산화구는 한 박스 + is_loop_reactor"],
        ["교반기만 있고 질산염 반송(a)이나 RAS가 들어오는 탱크", "`anoxic_zone`", ""],
        ["교반기만, 유입수를 가장 먼저 받고 그 뒤에 또 교반 구역", "`anaerobic_zone`", "글자 없으면 7절 흐름도"],
        ["생물반응조 뒤 침전지, 하부에서 반송(RAS)", "`secondary_clarifier`", "살수여상 뒤 humus tank 포함"],
        ["생물반응조 앞 침전지, 슬러지가 농축·소화로만 감", "`primary_clarifier`", ""],
        ["막 카세트가 혼합액을 받고 슬러지를 반응조로 돌려보냄", "`mbr_unit`", "처리수를 받는 막은 `membrane_unit`"],
        ["한 탱크에서 채움/반응/침전/배출", "`sbr_tank`", ""],
        ["여재·담체·디스크·탑 + 생물막", "`biofilm_reactor/…`", "살수여상 trickling_filter / 회전원판 rbc / 침지여재+공기 submerged_biofilter / 담체 mbbr_ifas / 유동상 fluidized_expanded_bed / MABR mabr"],
        ["상향류·가스 분리기·바이오가스선이 있는 폐수 반응기", "`anaerobic_wastewater_reactor/…`", "uasb_egsb_ic / anaerobic_filter / anaerobic_contact / anaerobic_cstr / abr / anaerobic_mbr"],
        ["슬러지가 들어가는 달걀·돔형 탱크", "`digester`", "폐수가 들어가면 위 클래스"],
        ["슬러지 라인의 작은 원뿔 탱크(상징수 반류)", "`thickener`", "기포·DAF·'부상'이면 `flotation_unit`"],
        ["슬러지 라인의 원심·벨트·프레스, 산물이 케이크", "`dewatering_unit`", "소화조 **앞** 벨트·드럼은 `thickener`"],
        ["모래·디스크·섬유 여과(3차), 활성탄", "`filtration_unit`", "공기선·탄소원선 있으면 생물막"],
        ["UV·염소 접촉조·오존·탈염소", "`disinfection_unit`", ""],
        ["반류수(탈수여액·상징수)만 받는 생물 반응기", "`sidestream_reactor`", "본류도 받으면 `*_zone`"],
        ["연못·라군·인공습지", "`pond_lagoon_wetland`", ""],
        ["응집·교반 탱크가 그려짐", "`chemical_treatment_unit`", "약품 화살표만 있으면 장치 아님(9절)"],
        ["스크린 / 침사지 / 유량조정조 / 펌프장(수조+펌프 여러 대)", "`screen` / `grit_chamber` / `equalization_tank` / `pump_station`", ""],
        ["단독 펌프 / 송풍기 / 저류탱크 / 밸브 / 산기·교반 기호", "`pump` / `blower` / `storage_tank` / `valve` / `aerator_mixer_symbol`", ""],
        ["글자 없음·번호뿐, 또는 글자가 단계 이름(Biological Treatment)", "`process_unit_generic` + l1_hint", "글자로 장치 종류를 알 수 있으면 그 클래스 + visual_form=box"],
        ["그 외 모든 장치(후포기, 탈취, 열교환기 …)", "`unknown_equipment` + 글자", ""],
    ], [6.2, 5.0, 5.8], size=9)
    D.fig("F7_visual_form.png", "그림 4. visual_form 고르기. 글자로만 종류를 알면 box, 모양이 종류를 말해 주면 symbol, 3D·아이콘이면 pictorial.", 17)
    D.note("'Biological Treatment'처럼 단계 이름만 적힌 박스는 어떤 장치인지(포기조? MBR? 살수여상?) 그림에 없습니다. 아는 척하지 말고 `process_unit_generic`을 고른 뒤 `l1_hint=secondary`로 '생물 처리 단계'라는 것만 남깁니다.", "warn")

    # ---------------------------------------------------------------- 7
    D.h("7. 구역(zone) 다루기")
    D.p("활성슬러지 반응조는 한 탱크를 격벽으로 나눠 혐기·무산소·호기 구역을 둡니다. 시뮬레이터는 구역 단위로 모델을 만들므로 구역마다 박스가 필요합니다.")
    D.fig("F9_zones.png", "그림 5. 한 탱크 안의 세 구역: 구역마다 박스(is_zone) + 탱크 박스 → 구역으로 parent_of 관계.", 17)
    D.p("구역 이름(혐기/무산소/호기)이 적혀 있지 않을 때는 아래 흐름도로 정합니다. 핵심은 '호기조 앞에 교반만 하는 구역이 몇 개인가'와 '어디로 반송이 들어오는가'입니다.")
    D.fig("F6_zone_decision.png", "그림 6. 구역 이름이 없을 때의 판별 흐름도(판별 규칙 1).", 17)

    # ---------------------------------------------------------------- 8
    D.h("8. 연결 요소")
    D.p("장치 말고도 아래 여덟 가지에 박스를 칩니다. 이것들이 있어야 컴퓨터가 흐름을 복원할 수 있습니다.")
    D.fig("F8_connection_elements.png", "그림 7. 간단한 공정도에서 연결 요소가 들어가는 자리.", 17)
    D.table(["클래스", "무엇", "속성"], [
        ["`arrowhead`", "화살표 끝의 화살촉", "없음"],
        ["`text_label`", "장치 이름·설명·설계치 글자 (장치 박스 안의 이름도)", "tag_kind: name / volume / spec …"],
        ["`stream_tag`", "선에 붙은 **숫자·ID** (유량, 농도, ①)", "tag_kind: flow / concentration / stream_no …"],
        ["`stream_label`", "선에 붙은 **글자** (RAS, WAS, a, reject water). 글자+숫자 섞이면 이것 하나로", "stream_role: ras_s / was / influent …"],
        ["`io_terminal`", "플랜트 경계의 끝: 유입, 방류, 약품 공급, 고형물 반출, 다른 그림으로 이어짐", "io_role: raw_influent / effluent / chemical_source / solids_disposal / continuation …"],
        ["`junction_split`", "선이 갈라지는 점, 그려진 분배조", "split_type (글자에 있을 때만)"],
        ["`junction_merge`", "선이 합쳐지는 점, 약품이 들어가는 지점, 반류수가 돌아오는 지점", "merge_role: chemical_dosing_point / sidestream_return …"],
        ["`instrument`", "센서·분석기·제어기 기호나 태그 (DO, NH4, pH, F, L)", "instrument_role, measured_variable"],
    ], [3.4, 8.2, 5.4], size=9)
    D.note("약품은 장치가 아니라 **선**입니다. 약품명이 적힌 화살표는 시작점에 `io_terminal(chemical_source)`, 장치로 들어가는 지점에 `junction_merge(chemical_dosing_point)`를 치고 둘을 엣지로 잇습니다. 응집·교반 **탱크**가 그려졌을 때만 `chemical_treatment_unit`입니다.")

    # ---------------------------------------------------------------- 9
    D.h("9. 흐름 연결(엣지) 기록")
    D.num("출발 장치 박스를 클릭합니다.")
    D.num("키보드 `Alt+R`을 누릅니다 (R 단독은 사각형 도구).")
    D.num("도착 장치 박스를 클릭합니다. 둘 사이에 화살표가 생깁니다.")
    D.num("오른쪽 Relations 탭에서 그 화살표의 라벨을 고릅니다: **매체|방향** 하나는 필수, 점선이면 `style:dashed`, '(Optional)'이나 대안 경로면 `optional`을 추가로.")
    D.table(["라벨", "뜻"], [
        ["`liquid|arrowhead`", "물(유입수·처리수)이 흐르고 화살촉이 그려짐"],
        ["`mixed_liquor|arrowhead`", "반응조 사이의 혼합액"],
        ["`sludge|arrowhead`", "슬러지 (RAS·WAS·1차 슬러지·소화 슬러지)"],
        ["`gas|…` / `air|…`", "바이오가스·배기 / 송풍 공기"],
        ["`chemical|…` / `solid|…`", "약품 / 케이크·협잡물"],
        ["`signal|…`", "점선 신호선 (센서 → 제어기)"],
        ["`…|inferred`", "선은 있는데 방향 표시가 없음 (공정 순서로 추정)"],
        ["`…|ambiguous`", "방향을 알 수 없음"],
        ["`parent_of`", "탱크 박스 → 구역 박스"],
    ], [5.5, 11.5], size=9.5)
    D.bullet("엣지 끝은 항상 **가장 작은 단위**(구역이 있으면 구역, 없으면 탱크)입니다.")
    D.bullet("갈라지거나 합쳐지는 곳은 반드시 `junction_split/merge` 박스를 거칩니다. 장치에서 장치로 바로 두 갈래를 잇지 않습니다.")
    D.bullet("인접 구역 사이(혐기 → 무산소 → 호기)는 선이 없어도 `mixed_liquor|inferred` 엣지를 넣습니다.")
    D.fig("F5_example_edges.png", "그림 8. 파일럿 1번 그림의 엣지. 번호는 그림 9의 장치 번호, J는 분기·합류 박스.", 16.5)

    # ---------------------------------------------------------------- 10
    D.h("10. 속성 채우기")
    D.p("박스를 클릭하면 나오는 칸입니다. **반드시(T1)**, **글자에 있을 때만(T2)**, **하지 않음(T3)** 세 묶음으로 나뉩니다.")
    D.table(["묶음", "항목", "어떻게"], [
        ["반드시", "`visual_form`", "box / symbol / pictorial / simulator_icon / section_view (그림 4)"],
        ["반드시", "`confidence`", "모양으로 확실 certain · 글자 읽고 inferred_from_text · 문맥 추정 inferred_from_context"],
        ["반드시", "`label_text`", "박스 안·옆 글자를 그대로 타이핑 (번호·™ 포함)"],
        ["반드시(구역)", "`is_zone`", "구역 박스에만 체크"],
        ["반드시(generic·unknown)", "`l1_hint`", "preliminary / primary / secondary / tertiary / sludge / sidestream / unknown"],
        ["반드시(이미지)", "`diagram_style`, `language`, `n_panels`", "A_box / B_symbol / C_pictorial / D_simulator / E_page · en / ko / zh / ja / mixed · 독립 도면 수"],
        ["글자에 있을 때만", "`zone_role`, `aeration_mode`, `operation_mode`, `redox_condition`, `clarifier_stage`, `digester_type`, `function`, `treatment_line`", "그림·캡션에 글자로 적혀 있을 때만 고릅니다. 없으면 비워 둡니다(추측 금지)"],
        ["글자에 있을 때만", "`process_configuration`", "캡션·제목의 공정 이름 원문 (A2O + MBR, MLE …)"],
        ["하지 않음", "biomass_form, n_pathway, membrane_type, pond_type, disinfectant 등", "파일럿에서는 건너뜁니다"],
    ], [3.4, 5.2, 8.4], size=9)

    # ---------------------------------------------------------------- 11
    D.h("11. 예제: 한 장 끝까지")
    D.p("파일럿 1번 그림(EPA 우천 시 처리 계열)을 끝까지 해 보면 다음과 같습니다.")
    D.fig("F4_example_boxes.png", "그림 9. 장치 박스 8개와 연결 요소. 색이 클래스 묶음을 나타낸다.", 16.5)
    D.table(["번호", "클래스", "label_text", "visual_form / confidence", "비고"], [
        ["1", "`process_unit_generic`", "Preliminary Treatment", "box / inferred_from_text", "l1_hint=preliminary"],
        ["2", "`primary_clarifier`", "Primary Clarifier", "box / inferred_from_text", "원이지만 글자로 알았으므로 box"],
        ["3", "`process_unit_generic`", "Biological Treatment", "box / inferred_from_text", "l1_hint=secondary"],
        ["4", "`secondary_clarifier`", "Secondary Clarifier", "box / inferred_from_text", ""],
        ["5", "`disinfection_unit`", "Disinfection", "box / inferred_from_text", ""],
        ["6", "`filtration_unit`", "FlexFilter™", "box / inferred_from_text", "1차 여과는 예비 클래스 → 여과로"],
        ["7", "`pump`", "(없음)", "symbol / certain", "펌프 기호"],
        ["8", "`biofilm_reactor/submerged_biofilter`", "Bio-FlexFilter™", "box / inferred_from_text", "redox_condition=aerobic"],
    ], [1.2, 5.0, 3.6, 3.8, 3.4], size=9)
    D.p("연결 요소: 화살촉 10개, 장치 이름 글자 7개 + 설명 글자 3개(`text_label`), 흐름 이름 3개(`stream_label`: WWF → overflow, Backwash → backwash_return), 도면 밖으로 나가는 끝 1개(`io_terminal`: continuation), 갈라짐 2개 + 합침 2개(`junction_*`). 엣지는 그림 8. 이미지 속성: diagram_style=A_box, language=en, n_panels=1, process_configuration 비움.")

    # ---------------------------------------------------------------- 12
    D.h("12. 자주 틀리는 것 · 애매할 때")
    for t in ["\"aeration tank\"라고 쓰여 있다고 `storage_tank`가 아닙니다 → `aerobic_zone`.",
              "약품 화살표에 장치 박스를 만들지 않습니다(8절 참고).",
              "2차 침전지의 RAS 선을 빼먹지 않습니다 → 엣지 `sludge|arrowhead` + `stream_label(ras_s)`.",
              "구역 박스에 `is_zone`을 빠뜨리지 않습니다. 탱크 윤곽이 안 그려졌으면 구역만 치고 parent_of는 생략.",
              "특허 도면의 번호(412, 480)는 `label_text`에 그대로, 클래스는 `process_unit_generic` + l1_hint.",
              "설계치·유량 같은 보조 글자도 전부 박스를 칩니다(OCR 평가에 씁니다).",
              "1차/2차 침전지는 모양이 같습니다 → **위치**로: 생물반응조 앞이면 1차, 뒤면 2차, RAS 선이 있으면 2차.",
              "농축조/탈수기는 **소화조 기준** 앞이면 농축, 뒤(또는 케이크 산출)면 탈수."]:
        D.bullet(t)
    D.note("규칙에 없거나 둘 다 가능해 보이면: 규칙에 가장 가까운 것을 고르고, 맨 아래 annotator_note에 '3번 박스: 혐기조인지 무산소조인지 불명' 처럼 한 줄 적습니다. 판정자가 모아서 가이드라인 v2에 반영합니다.")

    # ---------------------------------------------------------------- 13
    D.h("13. 끝낸 뒤")
    D.bullet("Projects 화면의 'Submitted annotations'가 60이 되면 끝입니다.")
    D.bullet("판정자가 Export → JSON으로 내보내 두 사람의 일치도를 계산합니다(κ ≥ 0.8 목표).")
    D.bullet("불일치가 많은 클래스·규칙은 함께 보고 가이드라인을 고칩니다. 틀린 사람을 찾는 과정이 아니라 규칙의 빈틈을 찾는 과정입니다.")

    # ---------------------------------------------------------------- appendix A
    D.pagebreak()
    D.h("부록 A. 판별 규칙 22개 요약")
    rules = [
        "활성슬러지 열의 탱크: 글자대로 `*_zone`; 글자 없으면 그림 6 흐름도. 밀폐·상향류·가스선 → `anaerobic_wastewater_reactor`; 슬러지 공급 → `digester`.",
        "여재 + 공기선 → `submerged_biofilter(aerobic)`; 여재 + 탄소원선 → `submerged_biofilter(anoxic)`; 둘 다 없음 → `filtration_unit`.",
        "탱크 전체가 담체 → `mbbr_ifas` 한 박스; 담체 케이지·MABR 카세트가 일부에만 → 포기조 박스 + 자식 생물막 박스.",
        "막이 혼합액을 받고 슬러지를 돌려보내면 `mbr_unit`, 처리수를 받으면 `membrane_unit`.",
        "슬러지 라인 장치: 소화조 앞 → `thickener`, 뒤 또는 케이크 산출 → `dewatering_unit`.",
        "약품은 엣지: `io_terminal(chemical_source)` → `junction_merge(chemical_dosing_point)`; 탱크가 그려졌을 때만 `chemical_treatment_unit`.",
        "SBR 패널마다 1단위; 교대 운전 쌍은 둘 다 `aerobic_zone` + operation_mode=alternating.",
        "WAS 화살표는 어디서든 나올 수 있다. 그려진 대로만.",
        "wet well + 펌프 여러 대 = `pump_station` 1개; 단독 펌프 = `pump`.",
        "UASB·IC 한 상자는 한 박스.",
        "예비 클래스 장치(입상슬러지, 열가수분해, 스트루바이트, 1차 여과, 오존·활성탄, 하이드로사이클론, 탈취)는 대응 클래스 + label_text 원문.",
        "캡션·제목의 공정 이름은 이미지 속성 `process_configuration`에.",
        "상자 안 상자: 바깥 = 부모, 안쪽 = 자식(parent_of). 거의 같은 크기면 자식을 만들지 않는다.",
        "1차/2차 침전지·조정조/저류조는 위치로: 생물반응조 앞 = 1차, 뒤 = 2차; RAS 선이 있으면 2차. 유량을 고르면 조정조, 담아만 두면 저류탱크.",
        "박스형 도면도 의미 클래스를 단다(visual_form=box). generic은 글자 없음·번호뿐·단계 이름일 때 + l1_hint 필수.",
        "부상 농축 = `flotation_unit(function=thickening)`; `thickener`는 중력·기계식만.",
        "P-stripper: RAS를 받으면 `anaerobic_zone(stripper)`, 반류수를 받으면 `sidestream_reactor`.",
        "선에 붙은 글자: 문자면 `stream_label`, 숫자·ID면 `stream_tag`, 섞였으면 `stream_label` 하나.",
        "`io_terminal`은 화살표 끝 + 글자; 다른 그림·단계로 이어지면 io_role=continuation.",
        "반류수 반응기: 유일한 공급이 탈수여액·상징수면 `sidestream_reactor`; 본류도 받으면 `*_zone` + 합류점.",
        "발효조: 발효액이 본류 혐기·무산소조로 가면 `fermenter`; 메탄 소화조로 가면 `digester(acid_phase)`.",
        "산화구·Carrousel·Orbal: 수로 전체 한 박스 `aerobic_zone(is_loop_reactor)`; 포기기 위치로 구간이 구분되면 구간마다 자식 구역.",
    ]
    for i, r in enumerate(rules, 1):
        para = D.d.add_paragraph(); D._runs(para, f"**{i}.** {r}", 9.5); para.paragraph_format.space_after = Pt(2)

    # ---------------------------------------------------------------- appendix B
    D.pagebreak()
    D.h("부록 B. 클래스 전체 목록 (L2 33 + 연결 8)")
    D.table(["단계", "클래스", "한글", "한 줄 정의"], [
        ["전처리", "`screen`", "스크린", "조목·세목·드럼·스텝 스크린, 분쇄기"],
        ["전처리", "`grit_chamber`", "침사지", "침사지, 포기식 침사지"],
        ["전처리", "`equalization_tank`", "유량조정조", "유량·수질 조정, 완충·우수 저류"],
        ["전처리", "`pump_station`", "펌프장", "수조 + 펌프 여러 대 (유입·중계·방류)"],
        ["1차", "`primary_clarifier`", "1차 침전지", "생물 처리 앞 침전지"],
        ["분리", "`flotation_unit`", "부상조", "DAF 등 부상 분리 (위치 무관)"],
        ["분리", "`chemical_treatment_unit`", "약품 처리조", "응집·교반 탱크 (주입 화살표는 아님)"],
        ["생물", "`aerobic_zone`", "호기조", "포기 구역, 산화구"],
        ["생물", "`anoxic_zone`", "무산소조", "탈질 구역 (전·후·RAS 전용)"],
        ["생물", "`anaerobic_zone`", "혐기조", "인 방출 구역"],
        ["생물", "`secondary_clarifier`", "2차 침전지", "생물 처리 뒤 침전지, humus tank"],
        ["생물", "`mbr_unit`", "막조", "혼합액을 받는 막 모듈"],
        ["생물", "`sbr_tank`", "연속회분식 반응조", "한 탱크 회분 운전"],
        ["생물", "`biofilm_reactor/…`", "생물막 반응기", "L3 필수: 살수여상·RBC·침지여재·담체·유동상·MABR"],
        ["생물", "`anaerobic_wastewater_reactor/…`", "혐기성 폐수 반응기", "L3 필수: UASB류·여상·접촉·CSTR·ABR·AnMBR"],
        ["생물", "`pond_lagoon_wetland`", "연못·습지", "안정화지, 라군, 인공습지"],
        ["반류수", "`sidestream_reactor`", "반류수 처리 반응기", "탈수여액·상징수만 받는 반응기"],
        ["고도", "`filtration_unit`", "여과", "모래·디스크·섬유·활성탄"],
        ["고도", "`membrane_unit`", "막 여과", "처리수를 받는 MF/UF/NF/RO"],
        ["고도", "`disinfection_unit`", "소독", "UV·염소·오존·탈염소"],
        ["슬러지", "`fermenter`", "발효조", "1차 슬러지 발효(VFA → 본류)"],
        ["슬러지", "`thickener`", "농축조", "소화조 앞 농축"],
        ["슬러지", "`digester`", "소화조", "슬러지 안정화 (혐기·호기)"],
        ["슬러지", "`dewatering_unit`", "탈수기", "원심·벨트·프레스·건조상"],
        ["슬러지", "`drying_incineration_unit`", "건조·소각·퇴비화", "열건조·소각·퇴비화"],
        ["슬러지", "`biogas_unit`", "바이오가스 설비", "가스홀더·플레어·CHP·보일러"],
        ["부대", "`pump` / `blower` / `storage_tank` / `valve` / `aerator_mixer_symbol`", "펌프/송풍기/저류탱크/밸브/산기·교반 기호", ""],
        ["종류 미상", "`process_unit_generic`", "공정 단위(미상)", "글자 없음·번호·단계 이름 → l1_hint"],
        ["종류 미상", "`unknown_equipment`", "기타 장치", "label_text 필수"],
        ["연결", "`arrowhead` `text_label` `stream_tag` `stream_label`", "", "화살촉 / 글자 / 숫자 / 흐름 이름"],
        ["연결", "`io_terminal` `junction_split` `junction_merge` `instrument`", "", "단자 / 분기 / 합류 / 계측"],
    ], [2.3, 5.6, 3.1, 6.0], size=8.8)
    D.p("체계의 근거·정의 전문: docs/annotation_taxonomy_plan.md (v1.1a), 기계용 정의: annotation/classes.yaml", 9, color=GREY)

    D.d.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build()
