"""
make_assets_261126.py — figures and page renders for the 2026-11-26 progress deck (build_meeting_deck_261126.py).

Outputs (meeting/figures/261126/):
  fig_incremental.png   data split + incremental-training loop (plan §5 4b, decided 2026-11-23)
  fig_remote.png        remote set-up: laptop (NL) → fixed public address → annotators (KR)
  fig_schedule.png      phase flow with rough durations (pilot → adjudication → test set → batches), no calendar dates
  tut_pNN.png           selected tutorial pages rendered from WWTP_annotation_tutorial_v1.pdf
  cheat_p1.png / cheat_p2.png   cheat sheet v2 pages (copied from the manual _render folder)
Run: python -X utf8 meeting/make_assets_261126.py
"""
from __future__ import annotations

import io
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pymupdf
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "meeting" / "figures" / "261126"
OUT.mkdir(parents=True, exist_ok=True)
MAN = ROOT / "data_collection" / "annotation" / "manual"

for f in ("C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/malgunbd.ttf"):
    font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["Arial", "Malgun Gothic"], "font.size": 10, "axes.unicode_minus": False,
                     "figure.dpi": 200, "savefig.dpi": 200})
KO = {"fontfamily": "Malgun Gothic"}
BLUE, GREEN, YELLOW, PURPLE, GREY, RED, TEAL, ORANGE = "#7FB3D5", "#A9DFBF", "#F9E79F", "#D7BDE2", "#D5DBDB", "#C0392B", "#A3E4D7", "#F8C471"
DARK = "#333333"


def box(ax, x, y, w, h, text, fc, fs=9.5, ec="#5D6D7E", ls="-", lw=1.0, bold=False, tc=DARK, ko=False, pad=0.08):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad={pad}", fc=fc, ec=ec, ls=ls, lw=lw))
    kw = dict(ha="center", va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal")
    if ko:
        kw.update(KO)
    ax.text(x + w / 2, y + h / 2, text, **kw)


def arrow(ax, p, q, color="#5D6D7E", lw=1.2, style="-|>", ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=11, color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0,
                                 connectionstyle=f"arc3,rad={rad}"))


# ------------------------------------------------------------------ 1. split + incremental loop
def fig_incremental():
    W, H = 13.0, 4.3
    fig, ax = plt.subplots(figsize=(W, H)); ax.set_xlim(0, W); ax.set_ylim(-0.3, H); ax.axis("off")
    # left: the three fixed parts of the main set
    ax.text(0.3, 3.95, "Main set 910 images (after 2nd de-dup, 11-24)", fontsize=11, fontweight="bold", va="top")
    y0 = 1.25; h = 2.1; x = 0.3
    parts = [("Pilot 60", "= validation\n2 annotators\nκ · adjudication\nguideline v2", YELLOW, 1.35),
             ("Test 150", "FROZEN\ndrawn 11-23\ndouble-annotated\nas batch 1\nnever trained on", BLUE, 1.55),
             ("Train ≈ 700", "accumulated in batches\n100–150 images or 2 weeks\nbatch 2, 3, 4, 5 …", GREEN, 3.15)]
    for name, desc, c, w in parts:
        ax.add_patch(FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.03", fc=c, ec="#5D6D7E", lw=1.2))
        ax.text(x + w / 2, y0 + h - 0.22, name, ha="center", va="top", fontsize=11, fontweight="bold")
        ax.text(x + w / 2, y0 + h / 2 - 0.22, desc, ha="center", va="center", fontsize=8.6, linespacing=1.35)
        x += w + 0.08
    # dashed batch separators inside train
    xt = 0.3 + 1.35 + 0.08 + 1.55 + 0.08
    for i in range(1, 5):
        xx = xt + 3.15 * i / 5
        ax.plot([xx, xx], [y0 + 0.05, y0 + h - 0.05], color="#5D6D7E", ls=":", lw=0.9)
    ax.text(0.3, 0.95, "document-disjoint: pilot / test / train never share a source document.\n"
            "pre-annotation (model output shown to annotators) only from round 3 (≥ 300 train images,\ntest AP50 ≥ 0.70) and never on the test set.",
            fontsize=8.6, color="#555", va="top", linespacing=1.3)
    # right: loop
    cx = 9.7; cy = 2.05; r = 1.25
    steps = [("Label batch\n(Label Studio)", YELLOW), ("Export → GT\n(s27, s22)", GREY), ("Retrain\ndetector + graph", PURPLE),
             ("Score on\nfixed test 150", BLUE), ("Log round\ndata-vX.Y, metrics", GREEN)]
    import math
    pts = []
    for i, (t, c) in enumerate(steps):
        a = math.pi / 2 - 2 * math.pi * i / len(steps)
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        pts.append((px, py))
        box(ax, px - 0.62, py - 0.3, 1.24, 0.6, t, c, fs=8.6)
    for i in range(len(pts)):
        p, q = pts[i], pts[(i + 1) % len(pts)]
        # shorten to box edges roughly
        dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy)
        s = 0.5 / L
        arrow(ax, (p[0] + dx * s, p[1] + dy * s), (q[0] - dx * s, q[1] - dy * s), rad=-0.25)
    ax.text(cx, cy, "every 100–150\nlabels or 2 weeks", ha="center", va="center", fontsize=9, color=RED, fontweight="bold")
    ax.text(cx, 3.95, "Incremental training (decided 11-23)", fontsize=11, fontweight="bold", va="top", ha="center")
    ax.text(cx, 0.38, "one row per round in docs/training_log.md = the paper's data-efficiency curve\n(x: labelled images, y: AP50 · AP · edge F1; point 0 = zero-shot baselines)",
            fontsize=8.6, color="#555", va="top", ha="center", linespacing=1.3)
    fig.savefig(OUT / "fig_incremental.png", bbox_inches="tight", pad_inches=0.05); plt.close(fig)


# ------------------------------------------------------------------ 2. remote set-up
def fig_remote():
    W, H = 13.0, 3.2
    fig, ax = plt.subplots(figsize=(W, H)); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    # laptop NL
    box(ax, 0.3, 0.9, 3.3, 1.7, "", GREY, lw=1.2)
    ax.text(1.95, 2.38, "Adjudicator's laptop (Delft)", ha="center", va="center", fontsize=10.5, fontweight="bold")
    box(ax, 0.5, 1.05, 1.4, 1.0, "Label Studio\n1.23 (local)\nSQLite DB", YELLOW, fs=8.8)
    box(ax, 2.05, 1.05, 1.4, 1.0, "ngrok agent\n(fixed domain)", TEAL, fs=8.8)
    arrow(ax, (1.9, 1.55), (2.05, 1.55))
    # cloud
    box(ax, 4.6, 1.15, 3.3, 0.9, "https://decent-reopen-curable.ngrok-free.dev\n(fixed address, HTTPS, free plan)", BLUE, fs=8.8)
    arrow(ax, (3.6, 1.6), (4.6, 1.6)); arrow(ax, (4.6, 1.5), (3.6, 1.5))
    ax.text(4.1, 1.78, "tunnel", ha="center", fontsize=8.5, color="#555")
    # annotators KR
    box(ax, 9.0, 0.9, 3.7, 1.7, "", GREY, lw=1.2)
    ax.text(10.85, 2.38, "Annotators (Korea) — browser only", ha="center", va="center", fontsize=10.5, fontweight="bold")
    box(ax, 9.2, 1.05, 1.6, 1.0, "annotator A\nproject pilot_A", GREEN, fs=8.8)
    box(ax, 10.9, 1.05, 1.6, 1.0, "annotator B\nproject pilot_B", GREEN, fs=8.8)
    arrow(ax, (7.9, 1.6), (9.0, 1.6)); arrow(ax, (9.0, 1.5), (7.9, 1.5))
    ax.text(8.45, 1.78, "https", ha="center", fontsize=8.5, color="#555")
    # bottom notes
    notes = ["one command restarts everything (start_pilot.ps1): Label Studio + ngrok + public check",
             "verified: cold start · lab → home Wi-Fi move (tunnel reconnects by itself) · laptop never sleeps on AC",
             "progress / export / backup read straight from the DB file (s27), no server round-trip; daily backup"]
    for i, n in enumerate(notes):
        ax.text(0.3, 0.6 - 0.26 * i, "✔", fontsize=8.6, color="#1E8449" if i < 2 else "#555", va="center", fontfamily="Segoe UI Symbol")
        ax.text(0.55, 0.6 - 0.26 * i, n, fontsize=8.6, color="#1E8449" if i < 2 else "#555", va="center")
    fig.savefig(OUT / "fig_remote.png", bbox_inches="tight", pad_inches=0.05); plt.close(fig)


# ------------------------------------------------------------------ 3. schedule (targets)
def fig_schedule():
    W, H = 13.0, 4.3
    fig, ax = plt.subplots(figsize=(W, H)); ax.set_xlim(-3.6, 11.3); ax.set_ylim(0, 7.4); ax.axis("off")

    # phases with rough durations only (no calendar dates): the x axis is weeks from now
    rows = [  # (label, start week, end week, colour, duration text)
        ("Pilot labelling (60 × 2)", 0, 1.2, YELLOW, "~1 week"),
        ("Adjudication · κ · guideline v2 · merges", 1.2, 2.2, YELLOW, "~1 week"),
        ("Zero-shot baselines (VLM · open-vocabulary)", 0.5, 2.3, PURPLE, "code now · numbers right after adjudication"),
        ("Batch 1 = fixed test set 150 (×2)", 2.2, 4.2, BLUE, "~2 weeks"),
        ("Batches 2–5 (≈ 700 train images)", 5.2, 11.0, GREEN, "~2 weeks each"),
        ("Model rounds (retrain per batch)", 4.5, 11.0, PURPLE, "from round 1 on"),
        ("Parallel: connectivity · priors · QSDsan · manuscript", 1.0, 11.0, TEAL, ""),
    ]
    for i, (lab, s, e, c, txt) in enumerate(rows):
        y = 6.4 - i * 0.85
        ax.add_patch(FancyBboxPatch((s, y - 0.28), e - s, 0.56, boxstyle="round,pad=0.01", fc=c, ec="#5D6D7E", lw=0.8))
        ax.text(-0.1, y, lab, va="center", ha="right", fontsize=8.6, fontweight="bold")
        if txt:
            ax.text(s + 0.1, y, txt, va="center", fontsize=8.2, color="#333")
    for wk in range(0, 12):
        ax.plot([wk, wk], [0.45, 7.0], color="#DDDDDD", lw=0.6, zorder=0)
        if wk % 2 == 0:
            ax.text(wk, 0.25, "now" if wk == 0 else f"+{wk} wk", ha="center", va="top", fontsize=8, color="#555")
    ax.axvspan(4.2, 5.2, color="#F2F3F4", zorder=0)
    ax.text(4.7, 0.6, "year-end\nbreak", ha="center", fontsize=8, color="#888", va="bottom")
    for xx, lab in [(2.2, "next meeting:\npilot results"), (5.5, "round-1 numbers"), (11.0, "all labels in\n→ full curve")]:
        ax.plot([xx, xx], [0.45, 7.0], color="#1F4E79", lw=0.9, ls=":")
        ax.text(xx, 7.15, lab, ha="center", fontsize=8, color="#1F4E79", va="bottom")
    fig.savefig(OUT / "fig_schedule.png", bbox_inches="tight", pad_inches=0.05); plt.close(fig)


# ------------------------------------------------------------------ 4. page renders
def renders():
    doc = pymupdf.open(MAN / "WWTP_annotation_tutorial_v1.pdf")
    for n in (1, 6, 13, 17, 22, 28, 31):
        pix = doc[n - 1].get_pixmap(dpi=90)
        pix.save(OUT / f"tut_p{n:02d}.png")
    for p in ("cheat_p1.png", "cheat_p2.png"):
        shutil.copy(MAN / "_render" / p, OUT / p)




# ------------------------------------------------------------------ 5. extra assets for the v2 deck
SHOTS = [  # tutorial captures in order -> demo video frames (caption shown under each frame)
    ("U01_login", "1  받은 주소를 열고 로그인"),
    ("U02_projects", "2  내 프로젝트만 연다 (pilot_A / pilot_B, practice = 연습)"),
    ("U03_tasks", "3  작업 목록: 1번부터 순서대로"),
    ("U04_labeling", "4  라벨링 화면: 버튼(위) · 그림(가운데) · Regions/Relations(오른쪽)"),
    ("U05_label_pressed", "5  라벨 버튼을 누르면 진해진다 → 그림 위를 드래그"),
    ("U06_box_drawn", "6  박스가 생기고 Regions에 한 줄 추가"),
    ("U07_box_selected", "7  박스를 클릭 → 속성(visual_form, confidence) 선택"),
    ("U09_zone_attr", "8  구역 박스는 is_zone = zone"),
    ("U11_relation_r", "9  출발 박스 클릭 → Alt+R → 연결 모드"),
    ("U12_relations_tab", "10  도착 박스 클릭 → Relations에 관계 한 줄"),
    ("U13_relation_label", "11  예외(점선 · 방향 없음)일 때만 관계 라벨"),
    ("U14_image_attrs", "12  맨 아래: 그림 전체 속성 (양식 · 언어 · 메모)"),
    ("U15_submit", "13  Submit → 저장 + 다음 장"),
]


def demo_video(sec_per_frame: float = 3.0):
    """demo_steps.mp4 from the real tutorial captures (no screen recording tool needed): 1600x900, caption bar."""
    import subprocess
    from PIL import Image, ImageDraw, ImageFont
    TUT = ROOT / "data_collection" / "annotation" / "manual" / "figures_tutorial"
    frames_dir = OUT / "_frames"; frames_dir.mkdir(exist_ok=True)
    W, H, BAR = 1600, 900, 110
    font = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 34)
    small = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 22)
    lst = []
    for i, (name, cap) in enumerate(SHOTS):
        im = Image.open(TUT / f"{name}.png").convert("RGB")
        s = min(W / im.width, (H - BAR) / im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        fr = Image.new("RGB", (W, H), "white")
        fr.paste(im, ((W - im.width) // 2, 0))
        d = ImageDraw.Draw(fr)
        d.rectangle([0, H - BAR, W, H], fill="#1F4E79")
        d.text((40, H - BAR + 22), cap, font=font, fill="white")
        d.text((W - 40, H - BAR + 70), f"{i + 1} / {len(SHOTS)}   실제 파일럿 서버 화면 캡처", font=small, fill="#D6EAF8", anchor="ra")
        p = frames_dir / f"f{i:02d}.png"; fr.save(p); lst.append(p)
    concat = frames_dir / "list.txt"
    with io.open(concat, "w", encoding="utf-8") as f:
        for p in lst:
            f.write(f"file '{p.name}'\nduration {sec_per_frame}\n")
        f.write(f"file '{lst[-1].name}'\n")
    out = OUT / "demo_steps.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat), "-vf", "fps=10,format=yuv420p",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-movflags", "+faststart", str(out)], check=True, cwd=frames_dir)
    Image.open(lst[0]).save(OUT / "demo_poster.png")
    print("video", out, out.stat().st_size // 1024, "KB")


def extra_renders():
    """cheat sheet v1 (from git, converted to PDF by Word beforehand) and one dedup twin pair."""
    import os
    from PIL import Image
    v1 = Path(os.environ["TEMP"]) / "cheat_v1.pdf"
    if v1.exists():
        doc = pymupdf.open(v1)
        doc[0].get_pixmap(dpi=90).save(OUT / "cheat_v1_p1.png")
    sheet = ROOT / "data" / "dedup" / "check_000.jpg"
    if sheet.exists():
        im = Image.open(sheet)
        im.crop((0, 0, im.width, int(im.height * 0.163))).save(OUT / "dedup_pair.png")


if __name__ == "__main__":
    fig_incremental(); fig_remote(); fig_schedule(); renders(); demo_video(); extra_renders()
    print("assets ->", OUT)
