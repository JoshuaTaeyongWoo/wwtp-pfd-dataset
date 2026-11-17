"""
make_manual_figures.py — figures for the annotator manual (annotation/manual/figures/*.png).

F1 workflow, F2 Label Studio screen call-outs (user screenshot), F3 label-button bar, F4 worked example:
boxes on pilot image 1, F5 worked example: edges, F6 zone decision flow, F7 box vs symbol vs pictorial,
F8 connection elements, F9 parent/zone boxes.
"""
from __future__ import annotations

import glob
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Polygon, Circle, Ellipse
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = ["Malgun Gothic", "Arial"]
plt.rcParams["axes.unicode_minus"] = False
FONT = "C:/Windows/Fonts/malgun.ttf"
FONTB = "C:/Windows/Fonts/malgunbd.ttf"

C = {"unit": "#0F7B6C", "generic": "#444444", "text": "#2C5F8A", "stream": "#7A3E9D", "io": "#B8701E",
     "junction": "#C0392B", "arrow": "#C0392B", "zone": "#2C5F8A", "edge": "#1B4F72"}


def font(size, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, size)


# ------------------------------------------------------------------ F1 workflow
def f1_workflow():
    fig, ax = plt.subplots(figsize=(11, 2.6))
    ax.set_xlim(0, 11); ax.set_ylim(0, 2.6); ax.axis("off")
    steps = [("①", "장치·구역 박스", "탱크·침전지·소화조…\n구역은 따로"), ("②", "연결 요소 박스", "화살촉·글자·단자\n분기·합류·계측"),
             ("③", "박스 속성", "visual_form\nconfidence · label_text"), ("④", "흐름 연결(엣지)", "출발 클릭 → r →\n도착 클릭 → 라벨"),
             ("⑤", "이미지 속성 · 제출", "diagram_style · language\nn_panels → Submit")]
    for i, (n, t, d) in enumerate(steps):
        x = 0.2 + i * 2.2
        ax.add_patch(FancyBboxPatch((x, 0.5), 1.9, 1.7, boxstyle="round,pad=0.02,rounding_size=0.12", fc="#DDF1EC" if i % 2 == 0 else "#E1ECF6", ec="#0F7B6C", lw=1.5))
        ax.text(x + 0.95, 1.85, f"{n} {t}", ha="center", va="center", fontsize=12, fontweight="bold")
        ax.text(x + 0.95, 1.1, d, ha="center", va="center", fontsize=9.5, color="#333")
        if i < 4:
            ax.add_patch(FancyArrowPatch((x + 1.92, 1.35), (x + 2.18, 1.35), arrowstyle="-|>", mutation_scale=18, color="#5C6B75", lw=1.5))
    ax.text(5.5, 0.18, "한 장당 이 다섯 단계를 반복한다. 한 장에 10~15분.", ha="center", fontsize=10, color="#5C6B75")
    fig.savefig(OUT / "F1_workflow.png", dpi=200, bbox_inches="tight"); plt.close(fig)


# ------------------------------------------------------------------ F2 UI call-outs
def f2_ui_callouts():
    src = sorted(glob.glob(str(Path.home() / "AppData/Local/Temp/claude/*/*/images/2.png")))
    if not src:
        print("F2: screenshot not found, skipped"); return
    im = Image.open(src[-1]).convert("RGB")
    d = ImageDraw.Draw(im)
    callouts = [  # (x0,y0,x1,y1, number, label)
        (0, 100, 232, 905, "1", "작업 목록 (1~60)"),
        (248, 160, 1205, 870, "2", "그림 — 라벨 버튼을 누른 뒤 여기서 드래그"),
        (1530, 210, 1575, 440, "3", "확대·이동 도구"),
        (1600, 120, 1910, 500, "4", "Info: 선택한 박스의 속성"),
        (1600, 530, 1910, 800, "5", "Regions / Relations 목록"),
        (1438, 872, 1590, 915, "6", "Submit (저장, Ctrl+Enter)"),
        (280, 878, 400, 910, "7", "되돌리기"),
    ]
    for x0, y0, x1, y1, n, lab in callouts:
        d.rectangle([x0, y0, x1, y1], outline="#C0392B", width=4)
        d.ellipse([x0 - 4, y0 - 4, x0 + 44, y0 + 44], fill="#C0392B")
        d.text((x0 + 20, y0 + 20), n, fill="white", font=font(26, True), anchor="mm")
    # legend strip
    strip = Image.new("RGB", (im.width, 150), "white")
    sd = ImageDraw.Draw(strip)
    for i, (_, _, _, _, n, lab) in enumerate(callouts):
        x = 20 + (i % 4) * 470; y = 15 + (i // 4) * 60
        sd.ellipse([x, y, x + 40, y + 40], fill="#C0392B"); sd.text((x + 20, y + 20), n, fill="white", font=font(24, True), anchor="mm")
        sd.text((x + 52, y + 20), lab, fill="black", font=font(24), anchor="lm")
    sd.text((20, 125), "※ 새 설정에서는 라벨 버튼(색깔 이름 목록)이 그림 위에 나타난다. 이 화면은 설정 변경 전 모습.", fill="#5C6B75", font=font(20), anchor="lm")
    canvas = Image.new("RGB", (im.width, im.height + strip.height), "white")
    canvas.paste(im, (0, 0)); canvas.paste(strip, (0, im.height))
    canvas.save(OUT / "F2_ui_callouts.png")


# ------------------------------------------------------------------ F3 label bar
def f3_label_bar():
    groups = [("전처리", "#1f77b4", ["screen ①", "grit_chamber", "equalization_tank", "pump_station"]),
              ("1차·분리", "#8c564b", ["primary_clarifier ②", "flotation_unit", "chemical_treatment_unit"]),
              ("생물", "#2ca02c", ["aerobic_zone ③", "anoxic_zone ④", "anaerobic_zone ⑤", "secondary_clarifier ⑥", "mbr_unit", "sbr_tank", "pond_lagoon_wetland"]),
              ("생물막 L3", "#17becf", ["biofilm_reactor/ trickling_filter", "…/rbc", "…/submerged_biofilter", "…/mbbr_ifas", "…/fluidized_expanded_bed", "…/mabr"]),
              ("혐기성 L3", "#9467bd", ["anaerobic_wastewater_reactor/ uasb_egsb_ic", "…/anaerobic_filter", "…/anaerobic_contact", "…/anaerobic_cstr", "…/abr", "…/anaerobic_mbr"]),
              ("반류수·고도", "#ff7f0e", ["sidestream_reactor", "filtration_unit ⑦", "membrane_unit", "disinfection_unit ⑧"]),
              ("슬러지", "#7f7f7f", ["fermenter", "thickener ⑨", "digester ⓪", "dewatering_unit", "drying_incineration_unit", "biogas_unit"]),
              ("부대", "#d62728", ["pump", "blower", "storage_tank", "valve", "aerator_mixer_symbol"]),
              ("종류 미상", "#000000", ["process_unit_generic", "unknown_equipment"]),
              ("연결·주석", "#aec7e8", ["arrowhead", "text_label", "stream_tag", "stream_label", "io_terminal", "junction_split", "junction_merge", "instrument"])]
    fig, ax = plt.subplots(figsize=(11, 8.8)); ax.axis("off"); ax.set_xlim(0, 11); ax.set_ylim(0, 8.8)
    y = 8.5
    for name, col, labs in groups:
        ax.text(0.1, y, name, fontsize=11, fontweight="bold", va="center")
        x = 1.6
        for lab in labs:
            w = 0.085 * len(lab) + 0.3
            if x + w > 10.9:
                x = 1.6; y -= 0.42
            ax.add_patch(FancyBboxPatch((x, y - 0.17), w, 0.34, boxstyle="round,pad=0.01,rounding_size=0.08", fc=col, ec="none", alpha=0.85))
            ax.text(x + w / 2, y, lab, ha="center", va="center", fontsize=8.6, color="white" if col not in ("#aec7e8",) else "black", family="Consolas")
            x += w + 0.12
        y -= 0.62
    ax.text(5.5, 0.15, "원문자(①~⓪)는 숫자 키 단축키. 색은 단계별 묶음. 생물막·혐기성 반응기는 반드시 L3(슬래시 뒤)까지 고른다.", ha="center", fontsize=9.5, color="#5C6B75")
    fig.savefig(OUT / "F3_label_bar.png", dpi=200, bbox_inches="tight"); plt.close(fig)


# ------------------------------------------------------------------ F4/F5 worked example on pilot image 1
def pilot1():
    p = glob.glob(str(ROOT / "data/pilot/images/pilot_01__*"))[0]
    im = Image.open(p).convert("RGB")
    S = 3
    return im.resize((im.width * S, im.height * S), Image.LANCZOS), S


UNITS = [  # (x0,y0,x1,y1 in original 480x360 px, class, label_text)
    (84, 35, 106, 63, "process_unit_generic", "Preliminary Treatment  (l1_hint=preliminary)"),
    (77, 83, 115, 123, "primary_clarifier", "Primary Clarifier"),
    (65, 139, 128, 186, "process_unit_generic", "Biological Treatment  (l1_hint=secondary)"),
    (76, 205, 116, 243, "secondary_clarifier", "Secondary Clarifier"),
    (78, 277, 116, 313, "disinfection_unit", "Disinfection"),
    (161, 145, 277, 183, "filtration_unit", "FlexFilter"),
    (277, 145, 312, 183, "pump", "(pump symbol)"),
    (312, 145, 439, 183, "biofilm_reactor/submerged_biofilter", "Bio-FlexFilter"),
]
TEXTS = [(13, 33, 77, 64, "Preliminary Treatment"), (25, 88, 71, 118, "Primary Clarifier"), (4, 146, 64, 176, "Biological Treatment"),
         (12, 210, 71, 239, "Secondary Clarifier"), (6, 285, 70, 301, "Disinfection"), (147, 192, 251, 224, "High Performance Solids Separation"),
         (271, 207, 321, 237, "Low Head Pumping"), (368, 194, 463, 239, "Bio-Filtration for Soluble Organic Removal")]
STREAMS = [(113, 33, 228, 64, "Excess Wet Weather Flow (WWF)  → overflow"), (154, 88, 218, 103, "(Optional)"), (264, 88, 322, 103, "Backwash → backwash_return")]
IO = [(389, 74, 460, 120, "Backwash To Solids Processing → continuation")]
JUNCTIONS = [(107, 48, "split"), (294, 104, "split"), (112, 103, "merge"), (116, 295, "merge")]
ARROWS = [(94, 78), (94, 135), (94, 200), (94, 273), (238, 143), (322, 140), (118, 103), (389, 103), (118, 296), (263, 182)]


def f4_boxes():
    im, S = pilot1()
    d = ImageDraw.Draw(im)
    f = font(22, True); fs = font(18)
    for x0, y0, x1, y1, cls, lab in UNITS:
        col = C["generic"] if cls.startswith("process_unit") else C["unit"]
        d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], outline=col, width=5)
    for x0, y0, x1, y1, _ in TEXTS:
        d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], outline=C["text"], width=2)
    for x0, y0, x1, y1, _ in STREAMS:
        d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], outline=C["stream"], width=3)
    for x0, y0, x1, y1, _ in IO:
        d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], outline=C["io"], width=4)
    for x, y, kind in JUNCTIONS:
        r = 6 * S
        d.rectangle([x * S - r, y * S - r, x * S + r, y * S + r], outline=C["junction"], width=3)
    for x, y in ARROWS:
        r = 5 * S
        d.rectangle([x * S - r, y * S - r, x * S + r, y * S + r], outline=C["arrow"], width=2)
    # numbered tags for unit boxes
    for i, (x0, y0, x1, y1, cls, lab) in enumerate(UNITS, 1):
        tx, ty = x0 * S, y0 * S - 26
        d.rectangle([tx, ty, tx + 30, ty + 24], fill=C["generic"] if cls.startswith("process_unit") else C["unit"])
        d.text((tx + 15, ty + 12), str(i), fill="white", font=f, anchor="mm")
    # legend below
    legend = Image.new("RGB", (im.width, 420), "white")
    ld = ImageDraw.Draw(legend)
    ld.text((20, 14), "장치 박스 (번호 = 아래 표)", fill="black", font=font(24, True))
    for i, (_, _, _, _, cls, lab) in enumerate(UNITS, 1):
        x = 20 + (i - 1) % 2 * 700; y = 52 + (i - 1) // 2 * 34
        col = C["generic"] if cls.startswith("process_unit") else C["unit"]
        ld.rectangle([x, y, x + 26, y + 24], fill=col); ld.text((x + 13, y + 12), str(i), fill="white", font=font(18, True), anchor="mm")
        ld.text((x + 36, y + 12), f"{cls}   — \"{lab}\"", fill="black", font=font(19), anchor="lm")
    y = 200
    items = [(C["unit"], 5, "장치 박스 (L2 클래스; 녹색)"), (C["generic"], 5, "process_unit_generic (단계 이름만 있는 박스; 회색) + l1_hint"),
             (C["text"], 2, "text_label (장치 이름·설명 글자; 파란 얇은 선)"), (C["stream"], 3, "stream_label (선 옆 흐름 이름; 보라)"),
             (C["io"], 4, "io_terminal (도면 밖으로 나가는 끝; 주황)"), (C["junction"], 3, "junction_split / merge (갈라짐·합침 지점; 빨간 작은 네모)"),
             (C["arrow"], 2, "arrowhead (화살촉마다; 빨간 더 작은 네모)")]
    for col, w, txt in items:
        ld.rectangle([20, y, 60, y + 22], outline=col, width=w); ld.text((72, y + 11), txt, fill="black", font=font(19), anchor="lm"); y += 30
    canvas = Image.new("RGB", (im.width, im.height + legend.height), "white")
    canvas.paste(im, (0, 0)); canvas.paste(legend, (0, im.height))
    canvas.save(OUT / "F4_example_boxes.png")


def f5_edges():
    im, S = pilot1()
    im = Image.blend(im, Image.new("RGB", im.size, "white"), 0.45)  # fade the drawing
    d = ImageDraw.Draw(im)
    ctr = {i: ((u[0] + u[2]) / 2 * S, (u[1] + u[3]) / 2 * S) for i, u in enumerate(UNITS, 1)}
    J = {k: (x * S, y * S) for k, (x, y, _) in zip(["s1", "s2", "m1", "m2"], JUNCTIONS)}
    io = (424 * S, 97 * S)
    P = lambda x, y: (x * S, y * S)  # original-pixel helper
    edges = [  # (polyline points, color, dashed) — routed along the drawn lines
        ([ctr[1], ctr[2]], C["edge"], False), ([ctr[2], ctr[3]], C["edge"], False),
        ([ctr[3], ctr[4]], C["edge"], False), ([ctr[4], ctr[5]], C["edge"], False),
        ([ctr[1], J["s1"]], "#2e8b57", False), ([J["s1"], P(238, 48), P(238, 143), ctr[6]], "#2e8b57", False),
        ([ctr[6], ctr[7]], "#2e8b57", False), ([ctr[7], ctr[8]], "#2e8b57", False),
        ([ctr[8], P(350, 183), P(350, 295), ctr[5]], "#2e8b57", False),
        ([ctr[6], P(294, 146), J["s2"]], "#d35400", True), ([J["s2"], P(130, 104), ctr[2]], "#d35400", True),
        ([J["s2"], io], "#d35400", True),
    ]
    import math
    for pts, col, dashed in edges:
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            if dashed:
                n = max(4, int(math.hypot(x1 - x0, y1 - y0) / 24))
                for k in range(n):
                    if k % 2 == 0:
                        d.line([(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n), (x0 + (x1 - x0) * (k + 1) / n, y0 + (y1 - y0) * (k + 1) / n)], fill=col, width=5)
            else:
                d.line([(x0, y0), (x1, y1)], fill=col, width=5)
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        ang = math.atan2(y1 - y0, x1 - x0); L = 18
        d.polygon([(x1, y1), (x1 - L * math.cos(ang - 0.4), y1 - L * math.sin(ang - 0.4)), (x1 - L * math.cos(ang + 0.4), y1 - L * math.sin(ang + 0.4))], fill=col)
    for i, (x, y) in ctr.items():
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill="white", outline=C["unit"], width=4)
        d.text((x, y), str(i), fill=C["unit"], font=font(22, True), anchor="mm")
    for k, (x, y) in J.items():
        d.rectangle([x - 14, y - 14, x + 14, y + 14], fill="white", outline=C["junction"], width=3)
        d.text((x, y), "J", fill=C["junction"], font=font(16, True), anchor="mm")
    d.rectangle([io[0] - 40, io[1] - 18, io[0] + 40, io[1] + 18], fill="white", outline=C["io"], width=3)
    d.text(io, "io", fill=C["io"], font=font(18, True), anchor="mm")
    legend = Image.new("RGB", (im.width, 330), "white")
    ld = ImageDraw.Draw(legend)
    ld.text((20, 14), "엣지 (출발 박스 클릭 → r → 도착 박스 클릭 → 관계 라벨)", fill="black", font=font(24, True))
    rows = ["파란 실선: 본류 1→2→3→4→5, 관계 라벨 liquid|arrowhead",
            "초록 실선: 우천 시 우회 1→J→6(FlexFilter)→7(펌프)→8(Bio-FlexFilter)→5, 전부 liquid|arrowhead",
            "주황 점선: 역세척 6→J→2 와 J→io(To Solids Processing), liquid|arrowhead + style:dashed + optional",
            "J = junction_split / junction_merge 박스를 반드시 거친다 (장치→장치 직결 금지)",
            "점선인데 방향 표시가 없으면 …|inferred, 방향을 알 수 없으면 …|ambiguous",
            "구역이 있는 탱크: 탱크 → 구역으로 parent_of 관계 (이 그림에는 없음)"]
    for i, r in enumerate(rows):
        ld.text((20, 56 + i * 40), "• " + r, fill="black", font=font(19), anchor="lm")
    canvas = Image.new("RGB", (im.width, im.height + legend.height), "white")
    canvas.paste(im, (0, 0)); canvas.paste(legend, (0, im.height))
    canvas.save(OUT / "F5_example_edges.png")


# ------------------------------------------------------------------ F6 zone decision
def f6_zone_decision():
    fig, ax = plt.subplots(figsize=(11, 6.4)); ax.axis("off"); ax.set_xlim(0, 11); ax.set_ylim(0, 6.4)

    def box(x, y, w, h, text, fc="#E1ECF6", ec="#2C5F8A", fs=10, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.1", fc=fc, ec=ec, lw=1.4))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")

    def arrow(x0, y0, x1, y1, label=""):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=14, color="#5C6B75", lw=1.3))
        if label:
            ax.text((x0 + x1) / 2 + 0.08, (y0 + y1) / 2, label, fontsize=8.5, color="#C0392B", ha="left", va="center")

    box(3.5, 5.6, 4, 0.6, "활성슬러지 열의 탱크 (1차 침전지 뒤, 2차 침전지 앞)", "#DDF1EC", "#0F7B6C", 10.5, True)
    box(3.5, 4.6, 4, 0.6, "혐기/무산소/호기 글자가 있는가?", "#FBEEDB", "#B8701E", 10.5, True)
    arrow(5.5, 5.6, 5.5, 5.2)
    box(0.3, 4.6, 2.6, 0.6, "글자대로 *_zone", "#DDF1EC"); arrow(3.5, 4.9, 2.9, 4.9, "예")
    box(3.5, 3.6, 4, 0.6, "호기조 앞에 교반만 하는 구역이 몇 개?", "#FBEEDB", "#B8701E", 10.5, True)
    arrow(5.5, 4.6, 5.5, 4.2, "아니오")
    # branches
    branches = [(0.2, "0개", "전부 aerobic_zone\n(CAS · 장기포기 · 산화구)"),
                (2.95, "1개", "a 반송·RAS가 들어옴\n→ anoxic (MLE)\n유입수만\n→ anaerobic (A/O)"),
                (5.7, "2개", "1번째 유입수(+RAS), 2번째 a\n→ 혐기, 무산소 (A2O)\n2번째에 RAS·a, 2→1 반송\n→ 혐기, 무산소 (UCT)"),
                (8.45, "3개", "1번째 RAS만\n→ anoxic(underflow_anoxic)\n2번째 anaerobic\n3번째 anoxic (JHB)")]
    for x, n, t in branches:
        box(x, 1.6, 2.55, 1.5, t, "#E1ECF6", fs=8.4)
        ax.text(x + 0.1, 3.25, n, fontsize=10, fontweight="bold", color="#C0392B")
        arrow(5.5, 3.6, x + 1.275, 3.1)
    box(0.3, 0.3, 4.6, 0.8, "호기조 뒤에 교반 구역 → anoxic_zone(post_anoxic)\n마지막 작은 포기 구역 → aerobic_zone(reaeration)", "#F6E3E6", "#8E3B46", 9)
    box(5.4, 0.3, 5.3, 0.8, "그래도 모르겠으면 → process_unit_generic + is_zone\n+ l1_hint=secondary + confidence=inferred_from_context", "#EEEEEE", "#444444", 9)
    fig.savefig(OUT / "F6_zone_decision.png", dpi=200, bbox_inches="tight"); plt.close(fig)


# ------------------------------------------------------------------ F7 box vs symbol vs pictorial
def f7_visual_form():
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    titles = [("visual_form = box", "글자로만 종류를 앎 → confidence=inferred_from_text"),
              ("visual_form = symbol", "모양이 종류를 말해 줌 → confidence=certain"),
              ("visual_form = pictorial", "3D·아이콘 그림 → 글자·문맥으로 판단")]
    ax = axes[0]; ax.add_patch(Rectangle((1, 1), 4, 2.2, fc="none", ec="black", lw=1.5)); ax.text(3, 2.1, "Primary\nClarifier", ha="center", va="center", fontsize=11)
    ax.add_patch(Circle((7.5, 2.1), 1.1, fc="none", ec="black", lw=1.5)); ax.text(7.5, 2.1, "2차\n침전지", ha="center", va="center", fontsize=10)
    ax = axes[1]; ax.add_patch(Polygon([(1, 3.2), (5, 3.2), (5, 1.8), (3, 0.8), (1, 1.8)], closed=True, fc="none", ec="black", lw=1.5))
    ax.add_patch(FancyArrowPatch((3, 0.8), (3, 0.2), arrowstyle="-|>", mutation_scale=12, color="black"))
    ax.text(3, 3.5, "원뿔 바닥 = 침전지", ha="center", fontsize=9)
    ax.add_patch(Ellipse((7.5, 2.0), 2.2, 2.8, fc="none", ec="black", lw=1.5)); ax.text(7.5, 3.7, "달걀형 = 소화조", ha="center", fontsize=9)
    ax = axes[2]; ax.add_patch(Polygon([(1, 1), (5, 1), (5.6, 1.6), (1.6, 1.6)], closed=True, fc="#9ecae1", ec="black"))
    ax.add_patch(Polygon([(1, 1), (1, 2.6), (5, 2.6), (5, 1)], closed=True, fc="#deebf7", ec="black")); ax.add_patch(Polygon([(5, 1), (5, 2.6), (5.6, 3.2), (5.6, 1.6)], closed=True, fc="#c6dbef", ec="black"))
    ax.text(3, 1.8, "~ ~ ~", ha="center", fontsize=12, color="#2C5F8A"); ax.text(3.3, 3.6, "3D 탱크 아이콘", ha="center", fontsize=9)
    for ax, (t, s) in zip(axes, titles):
        ax.set_xlim(0, 9); ax.set_ylim(-0.3, 4.3); ax.axis("off"); ax.set_title(t, fontsize=11, fontweight="bold"); ax.text(4.5, -0.25, s, ha="center", fontsize=8.5, color="#5C6B75")
    fig.savefig(OUT / "F7_visual_form.png", dpi=200, bbox_inches="tight"); plt.close(fig)


# ------------------------------------------------------------------ F8 connection elements
def f8_connection_elements():
    fig, ax = plt.subplots(figsize=(11, 4.2)); ax.axis("off"); ax.set_xlim(0, 11); ax.set_ylim(0, 4.2)
    ax.text(0.3, 2.3, "Influent", fontsize=10, style="italic"); ax.add_patch(Rectangle((0.2, 2.05), 1.1, 0.5, fc="none", ec=C["io"], lw=2, ls="--"))
    ax.text(0.75, 1.85, "io_terminal\nraw_influent", ha="center", va="top", fontsize=8, color=C["io"])
    ax.add_patch(FancyArrowPatch((1.4, 2.3), (2.9, 2.3), arrowstyle="-|>", mutation_scale=16, color="black", lw=1.5))
    ax.add_patch(Rectangle((2.65, 2.15), 0.3, 0.3, fc="none", ec=C["arrow"], lw=2)); ax.text(2.8, 2.6, "arrowhead", ha="center", fontsize=8, color=C["arrow"])
    ax.add_patch(Rectangle((3, 1.6), 2.2, 1.4, fc="none", ec="black", lw=1.5)); ax.text(4.1, 2.3, "Aeration tank", ha="center", va="center", fontsize=11)
    ax.add_patch(Rectangle((2.95, 1.55), 2.3, 1.5, fc="none", ec=C["unit"], lw=2.5)); ax.text(4.1, 3.2, "aerobic_zone (장치 박스)", ha="center", fontsize=8.5, color=C["unit"])
    ax.add_patch(Rectangle((3.35, 2.1), 1.5, 0.45, fc="none", ec=C["text"], lw=1.5)); ax.text(4.1, 1.3, "text_label (이름 글자도 따로)", ha="center", fontsize=8, color=C["text"])
    ax.add_patch(FancyArrowPatch((5.2, 2.3), (6.9, 2.3), arrowstyle="-|>", mutation_scale=16, color="black", lw=1.5))
    ax.text(6.0, 2.45, "Q = 10,000 m³/d", ha="center", fontsize=8.5); ax.add_patch(Rectangle((5.35, 2.35), 1.3, 0.3, fc="none", ec=C["stream"], lw=1.5, ls=":"))
    ax.text(6.0, 2.85, "stream_tag (숫자)", ha="center", fontsize=8, color=C["stream"])
    ax.add_patch(Polygon([(7, 3.0), (9.2, 3.0), (9.2, 2.0), (8.1, 1.4), (7, 2.0)], closed=True, fc="none", ec="black", lw=1.5))
    ax.add_patch(Rectangle((6.95, 1.35), 2.3, 1.7, fc="none", ec=C["unit"], lw=2.5)); ax.text(8.1, 3.2, "secondary_clarifier", ha="center", fontsize=8.5, color=C["unit"])
    ax.add_patch(FancyArrowPatch((9.2, 2.6), (10.6, 2.6), arrowstyle="-|>", mutation_scale=16, color="black", lw=1.5)); ax.text(10.3, 2.75, "Effluent", fontsize=9, style="italic")
    # RAS loop
    ax.plot([8.1, 8.1, 4.1, 4.1], [1.4, 0.6, 0.6, 1.55], color="black", lw=1.5); ax.add_patch(FancyArrowPatch((4.1, 0.9), (4.1, 1.55), arrowstyle="-|>", mutation_scale=16, color="black", lw=1.5))
    ax.text(6.1, 0.7, "RAS", ha="center", fontsize=9, style="italic"); ax.add_patch(Rectangle((5.75, 0.55), 0.7, 0.32, fc="none", ec=C["stream"], lw=1.5))
    ax.text(6.1, 0.3, "stream_label (글자, stream_role=ras_s)", ha="center", fontsize=8, color=C["stream"])
    ax.add_patch(Rectangle((7.9, 0.4), 0.4, 0.4, fc="none", ec=C["junction"], lw=2)); ax.text(8.9, 0.6, "junction_split\n(WAS가 갈라지면)", fontsize=8, color=C["junction"], va="center")
    ax.add_patch(FancyArrowPatch((8.1, 0.6), (8.1, -0.1), arrowstyle="-|>", mutation_scale=12, color="black", lw=1.2)); ax.text(8.25, 0.05, "WAS", fontsize=8, style="italic")
    ax.set_ylim(-0.3, 3.5)
    fig.savefig(OUT / "F8_connection_elements.png", dpi=200, bbox_inches="tight"); plt.close(fig)


# ------------------------------------------------------------------ F9 parent / zones
def f9_zones():
    fig, ax = plt.subplots(figsize=(11, 3.2)); ax.axis("off"); ax.set_xlim(0, 11); ax.set_ylim(0, 3.2)
    ax.add_patch(Rectangle((0.5, 0.8), 6.0, 1.8, fc="none", ec="black", lw=1.5))
    for i, (name, col) in enumerate([("혐기", "#DDF1EC"), ("무산소", "#E1ECF6"), ("호기", "#FBEEDB")]):
        x = 0.5 + i * 2.0
        ax.add_patch(Rectangle((x, 0.8), 2.0, 1.8, fc=col, ec="black", lw=0.8, ls="--" if i else "-"))
        ax.text(x + 1.0, 1.9, name, ha="center", fontsize=11)
    ax.text(5.5, 1.25, "~ ~ ~", ha="center", fontsize=12, color="#2C5F8A")
    ax.add_patch(Rectangle((0.42, 0.72), 6.16, 1.96, fc="none", ec=C["unit"], lw=2.5)); ax.text(3.5, 2.85, "parent: 탱크 박스 = process_unit_generic + l1_hint=secondary", ha="center", fontsize=9, color=C["unit"])
    for i, cls in enumerate(["anaerobic_zone", "anoxic_zone", "aerobic_zone"]):
        x = 0.58 + i * 2.0
        ax.add_patch(Rectangle((x, 0.9), 1.84, 1.6, fc="none", ec=C["zone"], lw=2)); ax.text(x + 0.92, 0.55, cls + "\n(is_zone 체크)", ha="center", va="top", fontsize=8.5, color=C["zone"])
    ax.text(7.0, 2.4, "규칙", fontsize=11, fontweight="bold")
    ax.text(7.0, 2.05, "1. 구역마다 박스 + is_zone 체크", fontsize=9.5)
    ax.text(7.0, 1.7, "2. 탱크 윤곽이 그려졌으면 탱크 박스도 치고", fontsize=9.5)
    ax.text(7.0, 1.4, "   탱크 → 각 구역으로 parent_of 관계", fontsize=9.5)
    ax.text(7.0, 1.05, "3. 탱크 박스 클래스 = process_unit_generic", fontsize=9.5)
    ax.text(7.0, 0.75, "   + l1_hint=secondary (구역이 의미를 가짐)", fontsize=9.5)
    ax.text(7.0, 0.4, "4. 구역끼리는 선이 없어도 mixed_liquor|inferred 엣지", fontsize=9.5)
    fig.savefig(OUT / "F9_zones.png", dpi=200, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    for fn in (f1_workflow, f2_ui_callouts, f3_label_bar, f4_boxes, f5_edges, f6_zone_decision, f7_visual_form, f8_connection_elements, f9_zones):
        fn(); print("ok", fn.__name__)
