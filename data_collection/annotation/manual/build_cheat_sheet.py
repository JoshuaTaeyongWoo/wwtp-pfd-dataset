"""
build_cheat_sheet.py — two-page A4-landscape cheat sheet that mirrors the Label Studio button bar.

Page 1: every label button drawn exactly as Label Studio shows it (same group order, group colour,
        label text and hotkey badge), with the Korean name and a one-line "what it looks like" hint.
Page 2: the decisions that are not on the buttons: confusable pairs, per-box fields, drawing lines,
        the per-image questions, what not to annotate, full-protocol extras, hotkeys.

The label list is READ FROM label_studio_config_lite.xml so the sheet cannot drift from the screen;
only the Korean names / hints live here (KO dict). Output: WWTP_cheat_sheet.pdf (vector, Malgun Gothic).

    python -X utf8 build_cheat_sheet.py
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent / "label_studio_config_lite.xml"
OUT = HERE / "WWTP_cheat_sheet.pdf"
FONT = "C:/Windows/Fonts/malgun.ttf"
FONTB = "C:/Windows/Fonts/malgunbd.ttf"
VERSION = "v2 · 2026-11-26"

W, H = 841.89, 595.28          # A4 landscape, points
M = 26                          # margin
INK = (0.11, 0.16, 0.20)
GREY = (0.38, 0.44, 0.48)
ACCENT = (0.06, 0.48, 0.42)
LINE = (0.85, 0.87, 0.89)

_font = {False: pymupdf.Font(fontfile=FONT), True: pymupdf.Font(fontfile=FONTB)}


def tl(text, size, bold=False):
    return _font[bold].text_length(text, fontsize=size)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def tint(rgb, a=0.15):
    return tuple(1 - a * (1 - c) for c in rgb)


# ----------------------------------------------------------------------------- Korean names + hints
# value -> (korean name, hint).  Hints are deliberately short (one glance).
KO = {
    "screen": ("스크린", "세로 막대·빗살 기호, Screen·Bar"),
    "grit_chamber": ("침사지", "모래·유지 제거 수로 (Grit, Sand)"),
    "equalization_tank": ("유량조정조", "EQ, Equalization"),
    "pump_station": ("펌프장", "Pump/Lift station (펌프 기호 하나면 pump)"),
    "primary_clarifier": ("1차 침전지", "생물반응조 앞의 침전지"),
    "secondary_clarifier": ("2차 침전지", "생물반응조 뒤, RAS 반송선 있음"),
    "chemical_treatment_unit": ("약품 처리조", "응집·중화 탱크가 그려졌을 때만"),
    "flotation_unit": ("부상 분리", "DAF, 기포로 띄움"),
    "aerobic_zone": ("호기조", "기포·산기관, Aeration·Oxic"),
    "anoxic_zone": ("무산소조", "교반만 + 반송(내부반송·RAS)이 들어옴"),
    "anaerobic_zone": ("혐기조", "교반만 + 유입수를 가장 먼저 받음"),
    "mbr_unit": ("MBR 탱크", "혼합액(슬러지)을 받는 막 탱크"),
    "sbr_tank": ("SBR", "연속회분식, 단계 패널마다 1개"),
    "pond_lagoon_wetland": ("연못·라군·습지", "자연형 처리"),
    "sidestream_reactor": ("반류수 반응기", "반류수만 받는 생물 반응기 (Anammox 등)"),
    "biofilm_reactor/trickling_filter": ("살수여상", "Trickling filter, 둥근 탑"),
    "biofilm_reactor/rbc": ("회전원판", "RBC, 디스크 여러 장"),
    "biofilm_reactor/submerged_biofilter": ("침지 생물여과", "BAF, 여재 + 공기선"),
    "biofilm_reactor/mbbr_ifas": ("MBBR·IFAS", "담체 알갱이가 떠다님"),
    "biofilm_reactor/fluidized_expanded_bed": ("유동상", "점 무늬 기둥"),
    "biofilm_reactor/mabr": ("MABR", "막 포기 생물막"),
    "filtration_unit": ("여과", "모래·디스크·섬유, Filter"),
    "membrane_unit": ("막 여과", "처리수를 받는 막 (MF·UF·RO)"),
    "disinfection_unit": ("소독", "UV·염소·오존, 접촉조"),
    "thickener": ("농축", "소화조 앞, 원뿔·드럼·원심"),
    "digester": ("소화조", "달걀·돔형, 슬러지 유입, 가스 발생"),
    "dewatering_unit": ("탈수", "벨트·원심, 케이크가 나옴"),
    "fermenter": ("발효조", "발효액이 본류로 돌아감"),
    "drying_incineration_unit": ("건조·소각", "소각로, 건조기"),
    "biogas_unit": ("바이오가스 설비", "가스홀더·발전기·보일러"),
    "pump": ("펌프", "원 + 꼬리, P 원. 작아도 친다"),
    "blower": ("송풍기", "팬, Blower, Air"),
    "storage_tank": ("저류 탱크", "약품·슬러지 저장 탱크"),
    "valve": ("밸브", "나비넥타이 기호"),
    "aerator_mixer_symbol": ("산기·교반 기호", "탱크 안에 따로 그려진 기호만"),
    "instrument": ("계측", "유량계·센서 태그 (FM, DO, pH)"),
    "process_unit_generic": ("이름뿐인 장치", "'Biological treatment', 번호 상자 → l1_hint + 글자"),
    "unknown_equipment": ("목록에 없는 장치", "Chiller, 탈취, 열교환기 → l1_hint + 글자"),
    "io_terminal": ("단자 (입출력 끝)", "그림 밖에서 오거나 나가는 끝 → io_role"),
    "junction_split": ("분기점", "선이 갈라지는 곳"),
    "junction_merge": ("합류점", "선이 합쳐지는 곳 (약품 들어오는 점 포함)"),
    "anaerobic_wastewater_reactor/uasb_egsb_ic": ("UASB·EGSB·IC", "상향류 슬러지 블랭킷"),
    "anaerobic_wastewater_reactor/anaerobic_filter": ("혐기 여상", "여재 채운 혐기조"),
    "anaerobic_wastewater_reactor/anaerobic_contact": ("혐기 접촉", "혐기조 + 침전·반송"),
    "anaerobic_wastewater_reactor/anaerobic_cstr": ("혐기 CSTR", "교반 혐기 탱크 (폐수)"),
    "anaerobic_wastewater_reactor/abr": ("혐기 배플", "ABR, 칸막이 여러 개"),
    "anaerobic_wastewater_reactor/anaerobic_mbr": ("혐기 MBR", "AnMBR"),
    "arrowhead": ("화살촉", "화살촉마다 작은 박스"),
    "text_label": ("장치 글자", "장치명·설명 글자"),
    "stream_tag": ("선 번호", "선 위 숫자 태그"),
    "stream_label": ("선 글자", "선 옆 글자 (RAS, WAS…)"),
}

GROUP_NOTE = {  # extra words after a group title (page 1)
    "g10_anaerobic": "접힌 줄 '드물게 쓰는 것' — 폐수가 들어가는 혐기 반응기만. 슬러지면 digester",
    "g11_full": "접힌 줄 — 1~20번(완전판)에서만 사용",
}
GROUP_TITLE = {"g10_anaerobic": "혐기 폐수 반응기", "g11_full": "화살촉·글자 박스"}


def read_groups():
    """[(name, title, [(value, hotkey, colour)])] in config order; panels get their own titles."""
    root = ET.parse(CONFIG).getroot()
    out = []
    for rl in root.iter("RectangleLabels"):
        name = rl.get("name")
        title = GROUP_TITLE.get(name)
        if title is None:                      # inline group: the Header right before it
            parent = next(p for p in root.iter() if rl in list(p))
            title = parent.find("Header").get("value")
        labels = [(l.get("value"), l.get("hotkey", " ").strip(), hexrgb(l.get("background"))) for l in rl.findall("Label")]
        out.append((name, title, labels))
    return out


# ----------------------------------------------------------------------------- drawing helpers
class Page:
    """Shapes are collected in one Shape, text in one TextWriter per (bold, colour); commit() draws the
    shapes first and the text on top, and embeds each font once (page.insert_text per call would
    re-embed the font and bury the text under later rectangles)."""

    def __init__(self, doc):
        self.p = doc.new_page(width=W, height=H)
        self.s = self.p.new_shape()
        self.tw: dict[tuple, pymupdf.TextWriter] = {}

    def text(self, x, y, s, size=8, bold=False, color=INK, maxw=None):
        """y = baseline. Shrinks the font when maxw is given and the text would overflow."""
        if maxw:
            while size > 5.5 and tl(s, size, bold) > maxw:
                size -= 0.25
        key = (bold, color)
        if key not in self.tw:
            self.tw[key] = pymupdf.TextWriter(self.p.rect)
        self.tw[key].append((x, y), s, font=_font[bold], fontsize=size)
        return tl(s, size, bold)

    def rect(self, x0, y0, x1, y1, fill=None, stroke=None, width=0.5):
        self.s.draw_rect(pymupdf.Rect(x0, y0, x1, y1))
        self.s.finish(color=stroke, fill=fill, width=width)

    def hline(self, x0, x1, y, color=LINE, width=0.5):
        self.s.draw_line((x0, y), (x1, y)); self.s.finish(color=color, width=width)

    def chip(self, x, y, value, hotkey, rgb, size=7.6, h=12.5):
        """A Label Studio label button: tinted box, 3-pt colour bar on the left, grey hotkey badge."""
        tw = tl(value, size)
        bw = (tl(hotkey, 6, True) + 6) if hotkey else 0
        w = 3 + 6 + tw + (6 + bw if hotkey else 0) + 6
        self.rect(x, y, x + w, y + h, fill=tint(rgb))
        self.rect(x, y, x + 3, y + h, fill=rgb)
        self.text(x + 8, y + h - 3.3, value, size)
        if hotkey:
            bx = x + 8 + tw + 6
            self.rect(bx, y + 2, bx + bw, y + h - 2, fill=(0.93, 0.93, 0.93))
            self.text(bx + 3, y + h - 4, hotkey, 6, True, GREY)
        return w

    def commit(self):
        self.s.commit()
        for (bold, color), tw in self.tw.items():
            tw.write_text(self.p, color=color)


def group_block(pg, x, y, colw, title, labels, note=None, chipw=176):
    """One group: title line, then one row per label. Returns the y after the block."""
    pg.text(x, y + 9, title, 8.6, True, INK)
    if note:
        pg.text(x + tl(title, 8.6, True) + 8, y + 9, note, 6.8, False, GREY, maxw=colw - tl(title, 8.6, True) - 10)
    pg.hline(x, x + colw, y + 12.5, LINE, 0.6)
    y += 15.5
    widths = [3 + 6 + tl(v, 7.6) + ((6 + tl(h, 6, True) + 6) if h else 0) + 6 for v, h, _ in labels]
    chipw = max(chipw, max(widths) + 10)        # long names (anaerobic_wastewater_reactor/...) push the text right
    for value, hk, rgb in labels:
        ko, hint = KO.get(value, (value, ""))
        pg.chip(x, y, value, hk, rgb)
        nx = x + chipw
        nw = pg.text(nx, y + 9.3, ko, 8.3, True, INK)
        pg.text(nx + nw + 5, y + 9.3, hint, 7.2, False, GREY, maxw=colw - chipw - nw - 6)
        y += 14.2
    return y + 5


def page1(doc, groups):
    pg = Page(doc)
    pg.text(M, M + 10, "라벨 버튼 한눈에 보기", 14, True, ACCENT)
    pg.text(M + tl("라벨 버튼 한눈에 보기", 14, True) + 10, M + 10, "— Label Studio 화면과 같은 순서·색·단축키", 9, False, GREY)
    r = f"1~20번 완전판 · 21~60번 쉬운 버전 · {VERSION}"
    pg.text(W - M - tl(r, 7.5), M + 10, r, 7.5, False, GREY)

    # workflow strip
    steps = ["① 장치·구역 박스", "② 단자·분기·합류·계측 박스", "③ 박스마다 속성", "④ 선 긋기: 출발 클릭 → Alt+R → 도착 클릭", "⑤ 그림 질문", "Submit (Ctrl+Enter)"]
    y0 = M + 20
    x = M
    for i, s in enumerate(steps):
        w = tl(s, 7.8, True) + 14
        last = i == len(steps) - 1
        pg.rect(x, y0, x + w, y0 + 15, fill=ACCENT if last else (0.93, 0.96, 0.95))
        pg.text(x + 7, y0 + 11, s, 7.8, True, (1, 1, 1) if last else ACCENT)
        x += w
        if not last:
            pg.text(x + 4, y0 + 11, "›", 9, True, GREY); x += 14

    colw = (W - 2 * M - 16) / 2
    left_names = ["g1_pre", "g2_settle", "g3_bio", "g4_biofilm", "g8_generic", "g9_conn"]
    by = {g[0]: g for g in groups}
    y = y0 + 26
    for n in left_names:
        _, title, labels = by[n]
        y = group_block(pg, M, y, colw, title, labels)
    # legend: how to read a button
    pg.text(M, y + 9, "버튼 읽는 법:", 7.4, True, GREY)
    xx = M + tl("버튼 읽는 법:", 7.4, True) + 6
    xx += pg.chip(xx, y, "label_name", "1", (0.12, 0.47, 0.71)) + 5
    pg.text(xx, y + 9, "색 띠 = 그룹색 · 회색 칸 = 단축키 (없으면 클릭) · 영문 이름은 화면과 동일", 7.2, False, GREY, maxw=colw - (xx - M))
    xr = M + colw + 16
    y = y0 + 26
    for n in ["g5_tertiary", "g6_sludge", "g7_aux", "g10_anaerobic", "g11_full"]:
        _, title, labels = by[n]
        y = group_block(pg, xr, y, colw, title, labels, GROUP_NOTE.get(n))

    # bottom-right: hotkeys
    pg.text(xr, y + 9, "단축키", 8.6, True, INK); pg.hline(xr, xr + colw, y + 12.5, LINE, 0.6)
    keys = [("1~0", "자주 쓰는 장치"), ("a", "펌프"), ("x / z", "모를 때"), ("i / j / l", "단자·분기·합류"), ("Alt+R", "선 긋기"),
            ("Backspace", "박스 삭제"), ("Ctrl+Z", "되돌리기"), ("u", "선택 해제"), ("휠", "확대"), ("Ctrl+Enter", "제출")]
    kx, ky = xr, y + 18
    for k, v in keys:
        kw = tl(k, 7.2, True) + 8
        pg.rect(kx, ky, kx + kw, ky + 12, fill=(0.93, 0.93, 0.93))
        pg.text(kx + 4, ky + 9, k, 7.2, True, INK)
        pg.text(kx + kw + 3, ky + 9, v, 7.2, False, GREY)
        kx += kw + 3 + tl(v, 7.2) + 10
        if kx > xr + colw - 60:
            kx, ky = xr, ky + 15
    pg.commit()
    return pg


# ----------------------------------------------------------------------------- page 2
def rich(pg, x, y, parts, size=7.4, maxw=380, lh=None):
    """parts: list of (text, style) with style in {'', 'b', 'chip:<value>'}; wraps at part boundaries."""
    lh = lh or size * 1.45
    cx = x
    for text, st in parts:
        if st.startswith("chip:"):
            w = 3 + 6 + tl(text, size - 0.6) + 6
            if cx + w > x + maxw:
                cx, y = x, y + lh
            rgb = CHIP_RGB.get(text, (0.3, 0.3, 0.3))
            pg.rect(cx, y - size - 1.2, cx + w, y + 2.8, fill=tint(rgb)); pg.rect(cx, y - size - 1.2, cx + 3, y + 2.8, fill=rgb)
            pg.text(cx + 8, y, text, size - 0.6)
            cx += w + 3
        else:
            bold = st == "b"
            words = [w for w in text.split(" ") if w]
            for i, word in enumerate(words):
                last = i == len(words) - 1
                ww = tl(word, size, bold)
                if cx + ww > x + maxw and cx > x:
                    cx, y = x, y + lh
                pg.text(cx, y, word, size, bold, INK)
                cx += ww + (0 if last and not text.endswith(" ") else tl(" ", size, bold))
    return y + lh


CHIP_RGB: dict[str, tuple] = {}
P2 = 8.4                      # body size on page 2


def section(pg, x, y, w, title):
    pg.text(x, y + 9, title, 8.8, True, ACCENT); pg.hline(x, x + w, y + 12.5, LINE, 0.6)
    return y + 22


def page2(doc, groups):
    for _, _, labels in groups:
        for v, _, rgb in labels:
            CHIP_RGB[v] = rgb
    pg = Page(doc)
    pg.text(M, M + 10, "판별·속성·선·제출", 14, True, ACCENT)
    pg.text(M + tl("판별·속성·선·제출", 14, True) + 10, M + 10, "— 버튼에 없는 결정들", 9, False, GREY)
    r = f"애매하면: 규칙에 가장 가까운 것 + annotator_note 한 줄. 다른 사람과 상의 금지 · {VERSION}"
    pg.text(W - M - tl(r, 7.5), M + 10, r, 7.5, False, GREY)

    cw = (W - 2 * M - 2 * 14) / 3
    x1, x2, x3 = M, M + cw + 14, M + 2 * (cw + 14)
    top = M + 24

    # ---- column 1: confusable pairs
    y = section(pg, x1, top, cw, "헷갈리는 짝 — 이럴 때 이 버튼")
    pairs = [
        [("침전지:", "b"), (" 생물반응조 ", ""), ("앞", "b"), (" ", ""), ("primary_clarifier", "chip:"), (" 뒤(RAS 있음) ", ""), ("secondary_clarifier", "chip:")],
        [("슬러지:", "b"), (" 소화조 ", ""), ("앞", "b"), (" ", ""), ("thickener", "chip:"), (" 뒤, 케이크 ", ""), ("dewatering_unit", "chip:")],
        [("막:", "b"), (" 혼합액(슬러지) 받음 ", ""), ("mbr_unit", "chip:"), (" 처리수 받음 ", ""), ("membrane_unit", "chip:")],
        [("여재·담체 있음:", "b"), (" + 공기선 → ", ""), ("biofilm_reactor/submerged_biofilter", "chip:"), (" 담체 떠다님 → ", ""), ("biofilm_reactor/mbbr_ifas", "chip:"), (" 둘 다 없음 → ", ""), ("filtration_unit", "chip:")],
        [("혐기 반응기:", "b"), (" 폐수 들어감 → ", ""), ("anaerobic_wastewater_reactor/uasb_egsb_ic", "chip:"), (" 등 세부형 · 슬러지 들어감 → ", ""), ("digester", "chip:")],
        [("발효:", "b"), (" 발효액이 본류로 → ", ""), ("fermenter", "chip:"), (" 메탄 소화조로 → ", ""), ("digester", "chip:")],
        [("약품:", "b"), (" 화살표만 → ", ""), ("io_terminal", "chip:"), ("(chemical_source) → ", ""), ("junction_merge", "chip:"), (" 탱크가 그려짐 → ", ""), ("chemical_treatment_unit", "chip:")],
        [("반류수:", "b"), (" 반류수만 받는 반응기 → ", ""), ("sidestream_reactor", "chip:"), (" 본류도 받으면 구역 버튼", "")],
        [("구역 이름 없을 때:", "b"), (" 호기조 앞 교반 칸 0개 → 전부 호기 · 1개 + 반송 → 무산소(MLE) · 1개 유입만 → 혐기(A/O) · 2개 → 혐기, 무산소(A2O) · 3개 → 무산소, 혐기, 무산소(JHB) · 호기 뒤 교반 → 무산소 · 모르면 ", ""), ("process_unit_generic", "chip:"), (" + is_zone + l1_hint", "")],
        [("산화구:", "b"), (" 한 박스 ", ""), ("aerobic_zone", "chip:"), (" (+ 포기기 구간은 자식 구역)", "")],
        [("상자 안 상자:", "b"), (" 바깥 부모, 안쪽 자식 (선 parent_of). 거의 같은 크기면 자식 없음", "")],
        [("같은 장치 N개:", "b"), (" N개 모두 박스. '×4' 글자뿐이면 1개", "")],
        [("SBR 단계 패널:", "b"), (" 패널마다 ", ""), ("sbr_tank", "chip:"), (" 1개", "")],
        [("펌프 기호 하나:", "b"), (" ", ""), ("pump", "chip:"), (" · 펌프들이 모인 건물·웰 → ", ""), ("pump_station", "chip:")],
    ]
    for p in pairs:
        y = rich(pg, x1, y, p, P2, cw) + 3

    # ---- column 2: per-box fields + lines
    y = section(pg, x2, top, cw, "박스마다 고르는 것 (박스 선택 → 아래 칸)")
    fields = [
        [("visual_form", "b"), ("  글자로만 알았다 → ", ""), ("box", "b"), (" · 모양이 말해 준다 → ", ""), ("symbol", "b"), (" · 3D·사진·아이콘 → ", ""), ("pictorial", "b"), (" · 시뮬레이터 아이콘 → simulator_icon · 단면도 → section_view", "")],
        [("confidence", "b"), ("  확실 → ", ""), ("certain", "b"), (" · 글자 보고 추론 → inferred_from_text · 앞뒤 공정 보고 추론 → inferred_from_context", "")],
        [("is_zone", "b"), ("  한 탱크 안의 칸(구역)이면 체크", "")],
        [("l1_hint", "b"), ("  generic·unknown 박스만: 어느 단계인지 → preliminary 전처리 · primary 1차 · secondary 2차(생물) · tertiary 3차 · sludge 슬러지 · sidestream 반류수 · unknown", "")],
        [("label_text", "b"), ("  generic·unknown은 필수 (그림 글자 원문 그대로), 나머지는 선택", "")],
        [("io_role", "b"), ("  io_terminal만: raw_influent 원수 유입 · settled_influent 1차 처리수 유입 · external_waste_in 외부 반입 · effluent 방류 · reclaimed_water_out 재이용수 · solids_disposal 슬러지 반출 · biogas_use 가스 이용 · off_gas_out 배가스 · chemical_source 약품 · overflow_bypass_out 월류·우회 · external_sidestream 외부 반류수 · continuation 다른 그림으로 이어짐", "")],
        [("graph_id", "b"), ("  독립 도면이 둘 이상일 때만 g1, g2…", "")],
    ]
    for p in fields:
        y = rich(pg, x2, y, p, P2, cw) + 3

    y = section(pg, x2, y + 4, cw, "선 긋기 (흐름 연결)")
    lines = [
        [("출발 박스 클릭 → ", ""), ("Alt+R", "b"), (" → 도착 박스 클릭. ", ""), ("보통 선은 라벨 없음.", "b")],
        [("예외일 때만 선 라벨: ", ""), ("no_arrow", "b"), (" 화살촉 없음 · ", ""), ("direction_unknown", "b"), (" 방향 모름 · ", ""), ("style:dashed", "b"), (" 점선 · ", ""), ("optional", "b"), (" (optional) 표시 · ", ""), ("parent_of", "b"), (" 탱크 → 안의 구역", "")],
        [("갈라짐·합침은 ", ""), ("junction_split", "chip:"), (" ", ""), ("junction_merge", "chip:"), (" 박스를 거쳐서 잇는다", "")],
        [("붙어 있는 구역끼리는 선이 없어도 연결 + no_arrow", "")],
        [("물·슬러지·공기 종류는 고르지 않는다 (자동)", "")],
    ]
    for p in lines:
        y = rich(pg, x2, y, p, P2, cw) + 3

    # ---- column 3: per-image, not annotated, full extras
    y = section(pg, x3, top, cw, "그림 한 장에 한 번 (맨 아래 ▼ 질문)")
    img = [
        [("diagram_style", "b"), ("  A_box 글자 상자 · B_symbol 기호 · C_pictorial 그림·3D · D_simulator 시뮬레이터 화면 · E_page 문서 페이지 · hydraulic_profile 수리 종단면", "")],
        [("language", "b"), ("  en · ko · zh · ja · other · mixed", "")],
        [("n_panels", "b"), ("  독립 도면 수 (보통 1)", "")],
        [("process_configuration", "b"), ("  캡션·제목의 공정 이름 원문 (예: A2O + MBR), 없으면 비움", "")],
        [("annotator_note", "b"), ("  판단이 어려웠던 점 한 줄 (판정자에게)", "")],
    ]
    for p in img:
        y = rich(pg, x3, y, p, P2, cw) + 3

    y = section(pg, x3, y + 4, cw, "안 치는 것")
    y = rich(pg, x3, y, [("흐름선 자체 · 캡션 문장 · 범례 · 표 · 축척 · 로고 · 그림 제목 · 샘플링 점 · 수식·변수 글자(Q, SS) · 쉬운 버전(21~60번)에서는 모든 글자", "")], P2, cw) + 3

    y = section(pg, x3, y + 4, cw, "1~20번 완전판에서만 더 치는 것")
    y = rich(pg, x3, y, [("접힌 줄을 펴서 ", ""), ("arrowhead", "chip:"), (" 화살촉마다 · ", ""), ("text_label", "chip:"), (" 장치명·설명 글자 · ", ""), ("stream_tag", "chip:"), (" 선 위 숫자 · ", ""), ("stream_label", "chip:"), (" 선 옆 글자(RAS, WAS…)", "")], P2, cw) + 3

    y = section(pg, x3, y + 4, cw, "제출·주의")
    for p in [
        [("한 장 끝 → ", ""), ("Submit", "b"), (" (Ctrl+Enter). Submit 전에는 집계되지 않음", "")],
        [("1번부터 순서대로. 하루 30장 정도", "")],
        [("Settings · 휴지통 · Account & Settings 열지 않기 (공용 계정)", "")],
        [("박스를 잘못 그렸으면 선택 → Backspace. 라벨을 바꾸려면 박스 선택 후 다른 버튼 클릭", "")],
    ]:
        y = rich(pg, x3, y, p, P2, cw) + 3

    y = section(pg, x3, y + 4, cw, "박스 그리기 요령")
    for p in [
        [("장치 기호(또는 글자 상자)에 ", ""), ("딱 맞게", "b"), (". 옆 글자는 넣지 않는다 (단자는 글자까지)", "")],
        [("상자 안 상자는 ", ""), ("안쪽 먼저", "b"), (" 그린다. 기존 박스 안에서 드래그하면 그 박스가 움직인다", "")],
        [("작은 기호(펌프·합류점)는 ", ""), ("휠로 확대", "b"), ("한 뒤 그린다", "")],
        [("칸이 나란한 탱크는 칸마다 하나씩. 따로 떨어진 탱크는 부모 없이 각각", "")],
    ]:
        y = rich(pg, x3, y, p, P2, cw) + 3
    pg.commit()
    return pg


def build():
    groups = read_groups()
    doc = pymupdf.open()
    page1(doc, groups)
    page2(doc, groups)
    doc.set_metadata({"title": "WWTP annotation cheat sheet v2", "author": "WWTP_vision"})
    doc.subset_fonts()                       # Malgun Gothic is ~5 MB per embedding; subset -> ~0.2 MB total
    doc.save(OUT, garbage=4, deflate=True)
    print("saved", OUT, f"{OUT.stat().st_size / 1024:.0f} KB")
    for i, pg in enumerate(doc, 1):
        pg.get_pixmap(dpi=130).save(HERE / "_render" / f"cheat_p{i}.png")


if __name__ == "__main__":
    (HERE / "_render").mkdir(exist_ok=True)
    build()
