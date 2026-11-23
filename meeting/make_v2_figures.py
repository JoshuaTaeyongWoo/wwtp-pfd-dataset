"""
make_v2_figures.py — matplotlib figures for the v2 meeting deck.
Outputs (meeting/figures/v2/): fig_framework.png, fig_framework_status.png, fig_phase_flow.png, fig_ladder.png,
fig_taxonomy_tree.png, fig_pilot_process.png, fig_style_shares.png (appendix), fig_terms_top12.png (appendix).
Korean text uses Malgun Gothic (Windows); English/numbers Arial.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib import font_manager
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "meeting" / "figures" / "v2"
OUT.mkdir(parents=True, exist_ok=True)

for f in ("C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/malgunbd.ttf"):
    font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["Arial", "Malgun Gothic"], "font.size": 10, "axes.unicode_minus": False,
                     "figure.dpi": 200, "savefig.dpi": 200})
KO = {"family": "Malgun Gothic"}

BLUE, GREEN, YELLOW, PURPLE, GREY, RED, TEAL, ORANGE = "#7FB3D5", "#A9DFBF", "#F9E79F", "#D7BDE2", "#D5DBDB", "#C0392B", "#A3E4D7", "#F8C471"
DARK = "#333333"


def box(ax, x, y, w, h, text, fc, fs=9.5, ec="#5D6D7E", ls="-", lw=1.0, bold=False, tc=DARK, ko=False, pad=0.08):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad={pad}", fc=fc, ec=ec, ls=ls, lw=lw)
    ax.add_patch(p)
    kw = dict(ha="center", va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal")
    if ko:
        kw["fontfamily"] = "Malgun Gothic"
    ax.text(x + w / 2, y + h / 2, text, **kw)
    return p


def arrow(ax, p, q, color="#5D6D7E", lw=1.2, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=11, color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0))


# ------------------------------------------------------------------ framework (overview / status)
def fig_framework(status: bool):
    W, H = 13.0, 5.5
    fig, ax = plt.subplots(figsize=(W, H)); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    # state per box: done / doing / todo
    st = {"col": "done", "tax": "done", "pilot": "doing", "adj": "todo", "main": "todo",
          "gt": "done", "eval": "done", "conv": "todo", "vlm": "doing", "frcnn": "todo", "det": "todo", "graph": "todo", "hub": "todo"}

    def style(k, base):
        if not status:
            return dict(fc=base, ls="-", lw=1.0)
        s = st[k]
        return {"done": dict(fc=base, ls="-", lw=1.6), "doing": dict(fc=base, ls="-", lw=1.0, hatch=True),
                "todo": dict(fc="white", ls="--", lw=1.0)}[s]

    def sbox(k, x, y, w, h, text, base, **kw):
        s = style(k, base); hatch = s.pop("hatch", False)
        p = box(ax, x, y, w, h, text, **s, **kw)
        if hatch:
            p.set_hatch("///"); p.set_edgecolor("#5D6D7E")
        if status and st[k] == "done":
            ax.text(x + w - 0.12, y + h - 0.14, "✔", ha="right", va="top", fontsize=11, color="#1E8449", fontfamily="Segoe UI Symbol")
        return p

    # row 1
    y1 = 4.05; h = 0.78; w = 2.25; gap = 0.33; x = 0.3
    ax.text(0.3, y1 + h + 0.12, "1  Benchmark construction", fontsize=11, fontweight="bold", color=DARK)
    r1 = [("col", "Collection + screening\n6 sources → 993 images", BLUE), ("tax", "Taxonomy v1.1\n33 classes + 8 connection", GREEN),
          ("pilot", "Pilot annotation\n60 images × 2 labellers", YELLOW), ("adj", "Adjudication\n→ guideline v2", YELLOW),
          ("main", "Main annotation\n(scale: to decide)", YELLOW)]
    xs = []
    for i, (k, t, c) in enumerate(r1):
        xi = x + i * (w + gap); xs.append(xi); sbox(k, xi, y1, w, h, t, c)
        if i < len(r1) - 1:
            arrow(ax, (xi + w + 0.02, y1 + h / 2), (xi + w + gap - 0.02, y1 + h / 2))
    # row 2
    y2 = 2.5
    ax.text(0.3, y2 + h + 0.12, "2  Ground truth and scoring", fontsize=11, fontweight="bold", color=DARK)
    r2 = [("gt", "Graph ground truth\nboxes + edges (JSON schema)", GREEN), ("eval", "Evaluation\ndetection AP · edge F1 · direction", GREEN),
          ("conv", "Downstream use\ngraph → QSDsan model (runs?)", TEAL)]
    x2 = [2.9, 5.65, 8.4]
    for (k, t, c), xi in zip(r2, x2):
        sbox(k, xi, y2, 2.45, h, t, c)
    arrow(ax, (x2[0] + 2.47, y2 + h / 2), (x2[1] - 0.02, y2 + h / 2)); arrow(ax, (x2[1] + 2.47, y2 + h / 2), (x2[2] - 0.02, y2 + h / 2))
    # labels flow from row 1 (main annotation) down to GT
    ax.plot([xs[4] + w / 2, xs[4] + w / 2, x2[0] + 1.2, x2[0] + 1.2], [y1, y1 - 0.25, y1 - 0.25, y2 + h + 0.02], color="#5D6D7E", lw=1.0)
    arrow(ax, (x2[0] + 1.2, y2 + h + 0.2), (x2[0] + 1.2, y2 + h + 0.02))
    ax.text(x2[0] + 1.3, y1 - 0.36, "labels", fontsize=8.5, color="#5D6D7E", va="top")
    # row 3
    y3 = 0.55
    ax.text(0.3, y3 + h + 0.62, "3  Models compared on the same test split", fontsize=11, fontweight="bold", color=DARK)
    if status:
        sbox("vlm", 0.3, y3, 2.3, h, "VLM zero-shot\n(no training) — no-label floor", GREY)
    else:
        box(ax, 0.3, y3, 2.3, h, "VLM zero-shot\n(no training) — no-label floor", GREY, ls="--")
    # deliverable bracket
    ax.add_patch(Rectangle((2.95, y3 - 0.3), 7.0, h + 0.42, fc="none", ec=PURPLE, lw=2.0, ls="-"))
    ax.text(2.95 + 0.08, y3 - 0.22, "deliverable: trained locally on our labels", fontsize=8.5, color="#6C3483", va="center")
    r3 = [("frcnn", "Faster R-CNN\n(Theisen settings)", PURPLE), ("det", "Modern detector\n(YOLO / DETR family)", PURPLE), ("graph", "Learned graph recovery\n(vs pixel search)", PURPLE)]
    for i, (k, t, c) in enumerate(r3):
        sbox(k, 3.1 + i * 2.3, y3, 2.15, h, t, c)
    sbox("hub", 10.3, y3, 2.4, h, "Human upper bound\n(annotator agreement)", "#F5B7B1")
    # merged arrow to evaluation
    ax.plot([0.3, 12.7], [y3 + h + 0.42, y3 + h + 0.42], color="#95A5A6", lw=1.0)
    for xm in (1.45, 4.2, 6.5, 8.8, 11.5):
        ax.plot([xm, xm], [y3 + h + 0.02, y3 + h + 0.42], color="#95A5A6", lw=1.0)
    arrow(ax, (x2[1] + 1.2, y3 + h + 0.42), (x2[1] + 1.2, y2 - 0.02), color="#95A5A6")
    ax.text(x2[1] + 1.3, y2 - 0.12, "all scored with the same ground truth and metrics", fontsize=8.5, color="#5D6D7E", va="top")
    if status:
        # legend
        lx, ly = 9.3, 5.15
        box(ax, lx, ly, 0.32, 0.22, "", BLUE, lw=1.6); ax.text(lx + 0.4, ly + 0.11, "done", va="center", fontsize=9); ax.text(lx + 0.95, ly + 0.11, "✔", va="center", fontsize=10, color="#1E8449", fontfamily="Segoe UI Symbol")
        p = box(ax, lx + 1.2, ly, 0.32, 0.22, "", YELLOW); p.set_hatch("///"); ax.text(lx + 1.6, ly + 0.11, "in progress", va="center", fontsize=9)
        box(ax, lx + 2.7, ly, 0.32, 0.22, "", "white", ls="--"); ax.text(lx + 3.1, ly + 0.11, "pending", va="center", fontsize=9)
    fig.savefig(OUT / ("fig_framework_status.png" if status else "fig_framework.png"), bbox_inches="tight", pad_inches=0.05); plt.close(fig)


# ------------------------------------------------------------------ phase flow (schedule without dates)
def fig_phase_flow():
    W, H = 13.0, 3.6
    fig, ax = plt.subplots(figsize=(W, H)); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    # completed summary
    box(ax, 0.3, 1.55, 1.85, 0.9, "완료\n수집·선별, 분류 체계,\n파일럿 준비, 평가 코드", GREEN, fs=9, ko=True)
    ax.text(0.45, 2.3, "✔", fontsize=11, color="#1E8449", fontfamily="Segoe UI Symbol", va="center")
    steps = [("파일럿 라벨링\n60장 × 2명", "~2주", YELLOW), ("판정·일치도\n→ 가이드라인 v2", "~1주", YELLOW),
             ("본 어노테이션\n(규모·인력 결정 후)", "~4주", YELLOW), ("Baseline 학습\nFaster R-CNN, 최신\n검출기, 연결 복원", "~4주", PURPLE),
             ("그래프 → QSDsan\n변환·실행 검증", "~3주", TEAL)]
    x = 2.5; w = 1.45; gap = 0.17; y = 1.55; h = 0.9
    arrow(ax, (2.17, y + h / 2), (x - 0.02, y + h / 2))
    xs = []
    for i, (t, dur, c) in enumerate(steps):
        xi = x + i * (w + gap); xs.append(xi)
        box(ax, xi, y, w, h, t, c, fs=9, ko=True)
        ax.text(xi + w / 2, y - 0.22, dur, ha="center", va="top", fontsize=9.5, color="#555", **KO)
        if i < len(steps) - 1:
            arrow(ax, (xi + w + 0.02, y + h / 2), (xi + w + gap - 0.02, y + h / 2))
    # next-meeting marker
    ax.plot([xs[1] - 0.11, xs[1] - 0.11], [y - 0.45, y + h + 0.35], color=RED, lw=1.2, ls="--")
    ax.text(xs[1] - 0.11, y + h + 0.4, "다음 미팅: 파일럿 결과", ha="center", va="bottom", fontsize=9.5, color=RED, **KO)
    # fork
    xe = xs[-1] + w
    box(ax, 11.05, 2.35, 1.75, 0.62, "초안 (2층)\nAEI급", ORANGE, fs=9, ko=True)
    box(ax, 11.05, 0.95, 1.75, 0.8, "+ TEA·LCA 시연\n→ 초안 (3층)\nWater Research 도전", ORANGE, fs=8.6, ko=True, ls="--")
    arrow(ax, (xe + 0.04, y + h / 2), (11.03, 2.76)); arrow(ax, (xe + 0.04, y + h / 2), (11.03, 1.2), ls="--")
    ax.text(11.92, 0.55, "+2~3주", ha="center", va="top", fontsize=9, color="#555", **KO)
    ax.text(0.3, 0.35, "상자 아래 기간은 대략값. 본 어노테이션 규모·인력은 다음 미팅에서 결정.", fontsize=9, color="#555", **KO)
    fig.savefig(OUT / "fig_phase_flow.png", bbox_inches="tight", pad_inches=0.05); plt.close(fig)


# ------------------------------------------------------------------ ladder of baselines
def fig_ladder():
    W, H = 6.2, 4.6
    fig, ax = plt.subplots(figsize=(W, H)); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    rungs = [("Human upper bound", "annotator agreement", "#F5B7B1", "-"),
             ("+ Learned graph recovery", "edges predicted, not traced", PURPLE, "-"),
             ("Modern detector", "YOLO / DETR family, our labels", PURPLE, "-"),
             ("Faster R-CNN", "Theisen settings, our labels", PURPLE, "-"),
             ("VLM zero-shot", "no training, class list given", GREY, "--")]
    y0 = 0.3; h = 0.68; gap = 0.14; x = 0.35; w = 3.6
    ys = []
    for i, (t, sub, c, ls) in enumerate(reversed(rungs)):
        y = y0 + i * (h + gap); ys.append(y)
        box(ax, x, y, w, h, "", c, ls=ls)
        ax.text(x + 0.15, y + h * 0.62, t, fontsize=10.5, fontweight="bold", va="center", color=DARK)
        ax.text(x + 0.15, y + h * 0.25, sub, fontsize=8.5, va="center", color="#555")
    ax.annotate("", xy=(x + w + 0.25, ys[0] + 0.05), xytext=(x + w + 0.25, ys[0] - 0.05), color="none")
    # brackets
    def bracket(y_lo, y_hi, label, xb):
        ax.plot([xb, xb + 0.12, xb + 0.12, xb], [y_lo, y_lo, y_hi, y_hi], color=RED, lw=1.3)
        ax.text(xb + 0.2, (y_lo + y_hi) / 2, label, va="center", fontsize=9.5, color=RED, **KO)
    bracket(ys[0] + 0.1, ys[2] + h - 0.1, "이 간격 = 라벨의 가치\n(VLM vs 학습 모델)", x + w + 0.15)
    bracket(ys[2] + 0.1, ys[3] + h - 0.1, "이 간격 = 방법의 가치\n(픽셀 탐색 vs 학습 연결 복원)", x + w + 0.15)
    ax.plot([x, x + w], [ys[4] - 0.07, ys[4] - 0.07], color="#999", lw=0.8, ls=":")
    ax.text(x + w / 2, ys[4] + h + 0.1, "ceiling: what a model can at most reach", ha="center", fontsize=8.5, color="#777")
    ax.annotate("", xy=(0.18, ys[4] + h), xytext=(0.18, ys[0]), arrowprops=dict(arrowstyle="-|>", color="#999", lw=1))
    ax.text(0.1, (ys[0] + ys[4] + h) / 2, "expected score", rotation=90, va="center", ha="right", fontsize=8.5, color="#777")
    fig.savefig(OUT / "fig_ladder.png", bbox_inches="tight", pad_inches=0.05); plt.close(fig)


# ------------------------------------------------------------------ taxonomy tree with Korean names
def fig_taxonomy_tree():
    tx = yaml.safe_load((ROOT / "data_collection" / "annotation" / "classes.yaml").read_text(encoding="utf-8"))
    l1 = {d["id"]: d["ko"] for d in tx["l1"]}
    cls = tx["classes"]
    conn = tx.get("connection_classes") or tx.get("annotation_classes") or {}
    groups: dict[str, list] = {}
    for cid, c in cls.items():
        groups.setdefault(c["l1"], []).append((cid, c.get("ko", cid), c.get("l3", {})))
    order = ["preliminary", "primary", "separation", "secondary", "sidestream", "tertiary", "sludge", "ancillary", "generic"]
    en = {"preliminary": "Preliminary", "primary": "Primary", "separation": "Separation", "secondary": "Biological", "sidestream": "Sidestream",
          "tertiary": "Tertiary", "sludge": "Sludge", "ancillary": "Ancillary", "generic": "Generic", "annotation": "Connection"}
    cols = [BLUE, "#F5B7B1", GREEN, YELLOW, PURPLE, ORANGE, "#AED6F1", TEAL, BLUE, GREY]
    W, H = 13.0, 4.3
    fig, ax = plt.subplots(figsize=(W, H)); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    ax.text(0.2, 4.1, "L1  공정 단계 7 (+ 부대 설비, 종류 미상, 연결 요소)", fontsize=10, color=DARK, **KO)
    ax.text(5.3, 4.1, "L2  단위공정 클래스 33 (31 + 종류 미상 2)", fontsize=10, color=DARK, **KO)
    ax.text(9.6, 4.1, "L3  시뮬레이터 모델이 다를 때만 하위형", fontsize=10, color=DARK, **KO)
    n = len(order) + 1; w = (W - 0.4) / n - 0.08; x = 0.2
    for i, g in enumerate(order + ["annotation"]):
        xi = x + i * (w + 0.08)
        items = groups.get(g, [])
        if g == "annotation":
            items = [(k, v.get("ko", k) if isinstance(v, dict) else k, {}) for k, v in conn.items()] if conn else \
                [("io_terminal", "유입·방류 단자", {}), ("junction_split", "분기점", {}), ("junction_merge", "합류점", {}), ("instrument", "계기", {}),
                 ("arrowhead", "화살촉", {}), ("text_label", "글자", {}), ("stream_tag", "흐름 태그", {}), ("stream_label", "흐름 라벨", {})]
        cnt = len(items)
        head = f"{l1.get(g, en[g])}\n{en[g]} ({cnt})"
        box(ax, xi, 3.2, w, 0.62, head, cols[i], fs=8.0, ko=True, bold=True)
        ax.plot([xi + w / 2, xi + w / 2], [3.2, 3.05], color="#888", lw=0.8)
        show = items[:3]
        for j, (cid, ko, l3) in enumerate(show):
            yy = 2.8 - j * 0.62
            ax.text(xi + w / 2, yy, ko, ha="center", va="center", fontsize=8.6, color=DARK, **KO)
            sub = cid.replace("_", " ")
            if isinstance(l3, dict) and l3.get("required"):
                sub += f"  (+{len(l3['required'])} L3)"
            ax.text(xi + w / 2, yy - 0.22, sub, ha="center", va="center", fontsize=6.8, color="#777")
        if cnt > 3:
            ax.text(xi + w / 2, 2.8 - 3 * 0.62, f"… 외 {cnt - 3}개", ha="center", va="center", fontsize=8, color="#777", **KO)
    ax.text(0.2, 0.12, "전체 33 클래스 표(한글·영문·L1·L3·예상 빈도)는 부록.", fontsize=8.5, color="#777", **KO)
    fig.savefig(OUT / "fig_taxonomy_tree.png", bbox_inches="tight", pad_inches=0.05); plt.close(fig)


# ------------------------------------------------------------------ pilot process
def fig_pilot_process():
    W, H = 6.6, 4.15
    fig, ax = plt.subplots(figsize=(W, H)); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    box(ax, 0.25, 2.55, 1.9, 0.95, "60장 층화 추출\n출처 6, 문서당 1장,\n비영어 포함", BLUE, fs=9, ko=True)
    box(ax, 2.55, 3.0, 1.6, 0.6, "A 독립 라벨링", YELLOW, fs=9, ko=True)
    box(ax, 2.55, 2.1, 1.6, 0.6, "B 독립 라벨링", YELLOW, fs=9, ko=True)
    ax.text(3.35, 3.78, "서로 결과를 보지 못함", ha="center", va="center", fontsize=8, color="#777", **KO)
    arrow(ax, (2.17, 3.1), (2.53, 3.3)); arrow(ax, (2.17, 2.95), (2.53, 2.4))
    box(ax, 4.55, 2.55, 1.85, 0.95, "일치도\nκ (클래스), 엣지 F1,\n박스 겹침", GREEN, fs=9, ko=True)
    arrow(ax, (4.17, 3.3), (4.53, 3.1)); arrow(ax, (4.17, 2.4), (4.53, 2.95))
    box(ax, 4.55, 1.0, 1.85, 0.95, "판정표\n불일치마다 원인:\n규칙 모호 / 실수 / 도면", GREEN, fs=9, ko=True)
    arrow(ax, (5.47, 2.53), (5.47, 1.97))
    box(ax, 2.55, 1.0, 1.6, 0.95, "가이드라인 v2\n+ 분류 체계 v1.2\n(필요 시)", ORANGE, fs=9, ko=True)
    arrow(ax, (4.53, 1.47), (4.17, 1.47))
    box(ax, 0.25, 1.0, 1.9, 0.95, "본 어노테이션\n(규모·인력 결정 후)", GREY, fs=9, ko=True, ls="--")
    arrow(ax, (2.53, 1.47), (2.17, 1.47))
    ax.text(0.25, 0.45, "목표 κ ≥ 0.8 (거의 완전한 일치). 미달이면 규칙을 고치고 20장을 다시 라벨링.", fontsize=8.5, color="#555", **KO)
    fig.savefig(OUT / "fig_pilot_process.png", bbox_inches="tight", pad_inches=0.05); plt.close(fig)


# ------------------------------------------------------------------ appendix: style shares (A/B/C) and top-12 terms
def fig_style_shares():
    forms = ["A 박스형\n(글자가 장치를 말함)", "B 기호형\n(ISO 10628 유사)", "C 그림형\n(3D·아이콘)"]
    sample40 = [40, 28, 22]; pilot60 = [48, 35, 15]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    x = range(3); w = 0.36
    ax.bar([i - w / 2 for i in x], sample40, w, color=BLUE, label="본 세트 무작위 40장 (다중 라벨)")
    ax.bar([i + w / 2 for i in x], pilot60, w, color=GREEN, label="파일럿 60장")
    for i, (a, b) in enumerate(zip(sample40, pilot60)):
        ax.text(i - w / 2, a + 1, f"{a}%", ha="center", fontsize=9); ax.text(i + w / 2, b + 1, f"{b}%", ha="center", fontsize=9)
    ax.set_xticks(list(x)); ax.set_xticklabels(forms, fontsize=9, **KO); ax.set_ylabel("share of images (%)"); ax.set_ylim(0, 58)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    leg = ax.legend(frameon=False, loc="upper right", prop={"family": "Malgun Gothic", "size": 9})
    ax.set_title("예비 분류(저자). 어노테이션의 diagram_style 항목으로 확정 예정.", fontsize=9, color="#555", loc="left", **KO)
    fig.tight_layout(); fig.savefig(OUT / "fig_style_shares.png"); plt.close(fig)


def fig_terms_top12():
    terms = [("Aeration tank / bioreactor / oxidation ditch", 264, "bio"), ("MBR", 83, "bio"), ("Anoxic / anaerobic zone, nitrif./denitrif.", 75, "bio"),
             ("Tank / storage", 67, "anc"), ("Recycle (RAS / WAS / internal)", 60, "bio"), ("Sand / media filtration", 40, "ter"),
             ("Biofilm (TF, MBBR, RBC)", 38, "bio"), ("Digester", 38, "slu"), ("Disinfection (UV / Cl / O3)", 34, "ter"),
             ("Pump / pump station", 33, "anc"), ("UASB / anaerobic reactor", 32, "bio"), ("Membrane (UF / RO / NF)", 28, "ter"),
             ("Heat exchanger", 1, "chem"), ("Distillation column", 0, "chem"), ("Compressor", 0, "chem")]
    col = {"bio": YELLOW, "ter": ORANGE, "slu": "#AED6F1", "anc": TEAL, "chem": "#F5B7B1"}
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    names = [t for t, _, _ in terms][::-1]; vals = [v for _, v, _ in terms][::-1]; cs = [col[g] for _, _, g in terms][::-1]
    ax.barh(names, vals, color=cs, edgecolor="#999", lw=0.4)
    for i, v in enumerate(vals):
        ax.text(v + 3, i, str(v), va="center", fontsize=8.5)
    ax.set_xlabel("captions mentioning the term (main set, n = 993; regex count — ranking only)")
    ax.tick_params(axis="y", labelsize=8.5)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=YELLOW, label="biological"), Patch(fc=ORANGE, label="tertiary"), Patch(fc="#AED6F1", label="sludge"),
                       Patch(fc=TEAL, label="ancillary"), Patch(fc="#F5B7B1", label="chemical-PFD core: absent")], frameon=False, fontsize=8.5, loc="lower right")
    fig.tight_layout(); fig.savefig(OUT / "fig_terms_top12.png"); plt.close(fig)


if __name__ == "__main__":
    fig_framework(False); fig_framework(True); fig_phase_flow(); fig_ladder(); fig_taxonomy_tree(); fig_pilot_process()
    fig_style_shares(); fig_terms_top12()
    print("figures written to", OUT)
