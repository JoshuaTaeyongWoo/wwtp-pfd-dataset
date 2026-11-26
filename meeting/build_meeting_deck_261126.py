"""
build_meeting_deck_261126.py — progress-meeting deck for 2026-11-26 (one week after the 11-20 deck).

v2 of this deck (after the user's review of v1): every slide is built as "last week → what went wrong /
was missing → what was changed → result", with less text and bigger figures; a Label Studio link button and
an embedded step video for the live demo; a slide on why Label Studio and why a public link.
File naming: <name>_<YYMMDD>_v<N> — the date is the meeting, v<N> counts revisions of that deck.

Inputs: meeting/figures/261126/* (make_assets_261126.py: figures, tutorial page renders, demo_steps.mp4),
        meeting/figures/v2/* (framework status figure), data_collection/annotation/manual/figures*.
Output: meeting/WWTP_vision_meeting_261126_v<N>.pptx  (N = DECK_VERSION below or env DECK_VERSION)
Run:    python -X utf8 meeting/build_meeting_deck_261126.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_meeting_deck_v2 as v2  # noqa: E402
from build_meeting_deck_v2 import (DARK, GREY, RED, Deck, bullets_box, caption, no_latin_break, picture, run_style, table, takeaway, textbox)  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MEETING = "261126"
DECK_VERSION = os.environ.get("DECK_VERSION", "2")
FIG = ROOT / "meeting" / "figures" / MEETING
V2 = ROOT / "meeting" / "figures" / "v2"
MF = ROOT / "data_collection" / "annotation" / "manual" / "figures"
TUT = ROOT / "data_collection" / "annotation" / "manual" / "figures_tutorial"
v2.OUT = ROOT / "meeting" / f"WWTP_vision_meeting_{MEETING}_v{DECK_VERSION}.pptx"
v2.MEETING_DATE = os.environ.get("MEETING_DATE", "2026.11.26.(Wed)")
v2.FOOTER = os.environ.get("MEETING_FOOTER", "11.26.(Wed) Progress meeting")
LS_URL = "https://decent-reopen-curable.ngrok-free.dev"

NAVY = RGBColor(0x1F, 0x4E, 0x79)
GREEN = RGBColor(0x1E, 0x84, 0x49)
T_GREY, B_GREY = RGBColor(0xF4, 0xF6, 0xF6), RGBColor(0xAE, 0xB6, 0xBF)      # "last week" panel
T_RED, B_RED = RGBColor(0xFD, 0xED, 0xEC), RGBColor(0xE6, 0xB0, 0xAA)        # "problem" panel
T_GREEN, B_GREEN = RGBColor(0xEA, 0xF7, 0xEE), RGBColor(0x7D, 0xCE, 0xA0)    # "fix / result" panel
T_BLUE, B_BLUE = RGBColor(0xEB, 0xF5, 0xFB), RGBColor(0x7F, 0xB3, 0xD5)


# ------------------------------------------------------------------ helpers
def panel(slide, x, y, w, h, header, lines, tint, border, head_color=DARK, size=12, head_size=13):
    """tinted box with a bold header line and short lines below (each line may start with '• ')."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.fill.solid(); tb.fill.fore_color.rgb = tint; tb.line.color.rgb = border; tb.line.width = Pt(1.25)
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.12); tf.margin_top = Inches(0.08); tf.margin_bottom = Inches(0.06)
    p = tf.paragraphs[0]; no_latin_break(p); r = p.add_run(); r.text = header; run_style(r, head_size, True, head_color)
    p.space_after = Pt(4)
    for ln in lines:
        p = tf.add_paragraph(); no_latin_break(p); p.space_after = Pt(3)
        bold = ln.startswith("**")
        r = p.add_run(); r.text = ln.strip("*"); run_style(r, size, bold, DARK)
    return tb


def message(slide, text, y=0.86, size=16, color=DARK):
    textbox(slide, 0.52, y, 12.29, 0.5, [(text, True)], size, color)


def problem_slide(D, title, notes, msg, before, problem, fix, fig=None, cap=None, fig_box=(5.35, 1.45, 7.5, 4.45), take=None):
    """left: three stacked panels (last week / problem / this week); right: one figure."""
    s = D.slide(title, notes)
    message(s, msg)
    x, w = 0.52, 4.6
    panel(s, x, 1.45, w, 1.25, "지난주 (11/20)", before, T_GREY, B_GREY, GREY)
    panel(s, x, 2.8, w, 1.35, "문제 / 부족했던 것", problem, T_RED, B_RED, RED)
    panel(s, x, 4.25, w, 1.75, "이번 주 조치 → 결과", fix, T_GREEN, B_GREEN, GREEN)
    if fig is not None:
        fx, fy, fw, fh = fig_box
        _, yy, _, hh, _ = picture(s, fig, fy, fw, fh, x=fx)
        if cap:
            caption(s, cap, yy + hh + 0.03, x=fx, w=fw, align=PP_ALIGN.LEFT, size=9)
    if take:
        takeaway(s, take, 6.1, 16)
    return s


def link_button(slide, x, y, w, h, text, url, sub=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = NAVY; shp.line.color.rgb = NAVY; shp.adjustments[0] = 0.18
    tf = shp.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; no_latin_break(p)
    r = p.add_run(); r.text = text; run_style(r, 20, True, RGBColor(0xFF, 0xFF, 0xFF))
    if sub:
        p = tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER; no_latin_break(p)
        r = p.add_run(); r.text = sub; run_style(r, 11, False, RGBColor(0xD6, 0xEA, 0xF8))
    shp.click_action.hyperlink.address = url
    return shp


# ------------------------------------------------------------------ slides
def build():
    D = Deck()

    # 1 title ---------------------------------------------------------------
    s = D.title_slide("Research in progress — week 2",
                      "WWTP Process-Flow-Diagram Benchmark: one week from plan to a running annotation pilot — what went wrong, what was changed, what is next",
                      "TaeYong Woo", v2.MEETING_DATE,
                      ["Dept. of Environmental Science and Engineering, Kyung Hee University", "(visiting TU Delft, Process Intelligence Research group)"])
    s.notes_slide.notes_text_frame.text = (
        "지난주(11/20)는 설계 보고였고, 오늘은 그 설계를 실행에 옮기면서 무엇이 막혔고 무엇을 고쳤는지 보고. 순서: ① 한 장 요약 → ② 왜 Label Studio와 공개 링크인가 → "
        "③~⑤ 이번 주 문제 세 가지와 조치(접속 주소 / 라벨 화면 / 교육 자료) → ⑥ 라이브 시연 → ⑦~⑧ 모델 비교의 잣대(고정 시험 세트)와 데이터 정리 → ⑨ 모델 쪽 현황 → ⑩ 다음 단계 → ⑪ 결정 요청.\n"
        "모델 숫자가 없는 이유를 표지에서 한 문장으로: 11/23 합의대로 모델은 라벨 배치가 오는 대로 올리기로 했고 아직 사람 라벨이 0장. 대신 라벨이 오는 순간 숫자가 나오도록 채점 코드와 라벨 0장 기준선을 준비(⑨).")

    # 2 one week in one slide ------------------------------------------------
    s = D.slide("One week in one slide: what was wrong, what was changed",
                "한 장 요약. 줄마다 '지난주 상태 → 문제 → 이번 주 조치·결과'. 뒤 슬라이드가 줄 하나씩에 해당. "
                "핵심 메시지: 지난주 설계는 그대로이고, 실행에 옮기면서 드러난 문제를 하나씩 고쳐 파일럿이 이번 주 시작됨. 모델 학습은 계획대로 라벨 배치가 오면 시작.")
    message(s, "지난주 설계는 그대로. 실행에 옮기자 드러난 문제 5가지를 고쳤고, 파일럿이 이번 주 시작됩니다")
    table(s, ["", "11/20 state", "what went wrong / was missing", "11/26 action → result"],
          [["Access", "temporary tunnel (address changed on every restart)", "address died after sleep; only alive while the Claude app ran; annotators could not be given one address",
            "fixed public address (ngrok domain) + one-command start script; verified cold start, Wi-Fi move, no sleep"],
           ["Labelling screen", "51 class buttons in one long row", "no stage order, rare classes in the way; relation hotkey documented wrong (r = rectangle tool)",
            "buttons in 9 treatment-stage rows + 2 fold-away panels, hotkeys 1–0; relation = Alt+R fixed in config, manuals, cheat sheet"],
           ["Training", "2-hour video training planned; 1-page cheat sheet", "first-time annotators, two time zones; cheat sheet did not look like the screen (annotator feedback)",
            "37-pp step-by-step tutorial from real screens + 5 practice answers + 20-min Zoom; cheat sheet v2 mirrors the buttons"],
           ["Model yardstick", "train after all labels are in", "no comparable score between label batches; nothing to show until the end",
            "incremental protocol: fixed test set 150 drawn and reviewed first, retrain per batch, one log row per round"],
           ["Data", "main set 993", "test-set review found crop/embedded twins, patent-family twins, broken PNGs",
            "second de-duplication → 910; 19 test images swapped after visual check"]],
          x=0.52, y=1.45, w=12.3, col_w=[1.5, 2.7, 3.9, 4.2], size=10.5, row_h=0.72, first_col_bold=True, header_size=11)
    takeaway(s, "모델은 라벨 0장이라 아직 숫자 없음(계획대로) — 채점 코드와 라벨 0장 기준선은 준비됨 (9번)", 6.05, 15)

    # 3 why Label Studio, why a public link -------------------------------------
    s = D.slide("Why Label Studio, and why a public link to my laptop",
                "도구: Theisen은 LabelImg(박스만). 우리 정답은 박스 + 속성 + 방향 있는 연결(그래프)이라 한 화면에서 셋을 다 할 수 있어야 함. CVAT도 검토(클래스 파일까지 만듦)했으나 관계(엣지) 입력이 약하고 서버가 무거움. "
                "Label Studio: 오픈소스, 로컬 설치, 박스·속성·관계를 한 화면에서, JSON 내보내기 → 우리 채점 코드로 바로 연결. 라벨 화면 자체가 분류 체계(버튼 = 클래스)라 체계가 바뀌면 설정 파일만 고침.\n"
                "링크: 어노테이터는 한국, 저는 네덜란드. 각자 설치하면 결과가 흩어지고 백업·판정이 안 됨. 서버 한 곳에 DB 하나가 있어야 진행 상황·백업·판정이 한 번에 됨. 랩 리눅스 서버는 아직 준비 전이라 파일럿은 제 노트북을 서버로 쓰고 공개 주소로 열어 둠. "
                "브라우저만 있으면 되고 설치·가입 없음. 본 어노테이션은 랩 서버로 옮기는 것이 결정 사항(12번).")
    message(s, "정답이 '박스 + 속성 + 연결'이라 세 가지를 한 화면에서 하는 도구가 필요하고, 결과가 한 곳에 모여야 판정·백업이 됩니다")
    table(s, ["tool", "boxes", "attributes per box", "edges (relations)", "remote, no install", "why / why not"],
          [["LabelImg (Theisen 2023)", "✓", "—", "—", "—", "boxes only; graph ground truth impossible"],
           ["CVAT", "✓", "✓", "weak", "server, heavier", "tried (class file made); edge input clumsy"],
           ["Label Studio 1.23", "✓", "✓", "✓ Alt+R, labelled", "browser only", "all three on one screen; JSON → our scoring code; buttons = taxonomy"]],
          x=0.52, y=1.45, w=12.3, col_w=[2.1, 0.8, 1.4, 1.6, 1.6, 4.8], size=10.5, row_h=0.45, first_col_bold=True)
    panel(s, 0.52, 3.45, 6.0, 2.1, "왜 공개 링크로 접속하나",
          ["• 어노테이터 2명은 한국, 판정자(저)는 네덜란드 → 각자 설치하면 결과가 흩어짐",
           "• DB 하나 = 진행 상황 · 백업 · 판정이 한 곳에서",
           "• 랩 리눅스 서버는 아직 준비 전 → 파일럿은 제 노트북이 서버",
           "• 어노테이터는 브라우저만: 설치 없음, 가입 없음(공용 계정, 프로젝트로 구분)",
           "• 본 어노테이션은 랩 서버로 이전 (12번 결정 사항)"], T_BLUE, B_BLUE, NAVY)
    _, yy, _, hh, _ = picture(s, FIG / "fig_remote.png", 3.45, 6.2, 2.5, x=6.7)
    caption(s, "laptop (NL) → fixed address → annotators (KR), browser only.", yy + hh + 0.02, x=6.7, w=6.2, align=PP_ALIGN.LEFT, size=9)

    # 4 problem 1: the address ------------------------------------------------
    problem_slide(D, "Problem 1 — the access address kept dying",
                  "11/19에 Cloudflare 임시 터널로 열었는데 주소가 재시작마다 바뀌고, 노트북이 잠들거나 Wi-Fi가 바뀌면 Cloudflare 쪽에서 터널이 삭제되어('Tunnel not found') 주소가 죽음. 게다가 Claude 앱 안에서 띄워 앱을 닫으면 끊김. "
                  "어노테이터에게 '이 주소'라고 알려 줄 수가 없었음. 조치: ngrok 고정 도메인(무료 플랜, 제 계정)으로 교체 → 주소 불변. start_pilot.ps1 한 줄이 Label Studio(공개 주소용 CSRF·가입 차단 설정 포함) + ngrok + 공개 주소 점검. "
                  "검증: 전부 끈 뒤 콜드 스타트 → 한국에서 로그인 200 / 연구실 → 집 Wi-Fi 이동 → 터널 자동 재접속 / AC 전원 절전·최대 절전 끔. 진행·내보내기·백업은 DB 파일을 직접 읽는 도구(s27)로 서버 없이.\n"
                  "예상 질문 — '노트북이 꺼지면?': 어노테이터가 페이지를 못 열면 바로 연락 → 한 줄로 재시작. 제출한 작업은 DB에 있어 잃지 않음. '보안은?': HTTPS, 가입 차단, 비밀번호는 파일럿 뒤 변경, 이미지에 개인정보 없음.",
                  "주소를 고정하고, 한 줄로 되살리고, 절전·네트워크 이동을 견디는지 확인했습니다",
                  ["• Cloudflare 임시 터널로 공개 (11/19)", "• 주소가 재시작마다 바뀜", "• Claude 앱 안에서 실행"],
                  ["• 노트북 절전 · Wi-Fi 변경 → Cloudflare가 터널 삭제 (\"Tunnel not found\")", "• 앱을 닫으면 끊김", "• 어노테이터에게 알려 줄 '고정 주소'가 없음"],
                  ["• ngrok 고정 도메인으로 교체 → 주소 불변", "• start_pilot.ps1 한 줄: Label Studio + ngrok + 공개 주소 점검", "• 검증: 콜드 스타트 · 연구실→집 Wi-Fi 이동 · AC 절전 끔", "• 진행·내보내기·백업은 DB 파일 직접 읽기 (서버 무관)"],
                  FIG / "fig_remote.png", "current set-up; green = verified this week.", fig_box=(5.35, 1.6, 7.5, 3.0),
                  take="어노테이터는 한 주소만 기억하면 됩니다. 제가 할 일은 재부팅 뒤 한 줄뿐입니다")

    # 5 problem 2: the labelling screen ----------------------------------------
    s = problem_slide(D, "Problem 2 — the labelling screen",
                      "11/18 설정(v1)은 라벨 버튼 51개가 한 줄로 늘어선 상태라 처리 단계 순서가 없고, 드문 혐기 폐수 반응기 6종과 완전판 전용 4종(화살촉·글자)이 자주 쓰는 버튼 사이에 섞여 있었음. 그리고 설명서·치트시트에 관계 단축키를 'r'로 적었는데 "
                      "실제 Label Studio 1.23에서 r은 사각형 도구이고 관계는 Alt+R — 설명서 캡처를 찍다가 발견. 조치(11/25, v2): 9줄(전처리 / 침전·물리화학 / 생물 반응(구역) / 생물막 / 3차·소독 / 슬러지 / 보조·계측 / 모를 때 / 연결 요소) + 접는 패널 2개, "
                      "자주 쓰는 10개에 숫자 단축키, 버튼과 그림이 한 화면에 들어가게 압축. Alt+R은 설정·설명서·치트시트·교육 대본 전부 수정. 세 프로젝트(pilot_A, pilot_B, practice)에 적용.\n"
                      "예상 질문 — '클래스가 너무 많지 않나?': 보이는 건 41개(33 + 연결 8)지만 그림 한 장에서 실제로 쓰는 건 8~12개. 파일럿 뒤 50 인스턴스 미만 클래스는 병합(지난주 결정).",
                      "버튼을 처리 단계 순서로 9줄에 묶고, 드문 것은 접고, 틀린 단축키를 고쳤습니다",
                      ["• 설정 v1 (11/18): 버튼 51개가 한 줄", "• 설명서에 관계 단축키 = r"],
                      ["• 단계 순서가 없어 버튼 찾기가 느림", "• 드문 클래스 10개가 자주 쓰는 버튼 사이에", "• r은 사각형 도구 — 관계는 Alt+R (캡처 중 발견)"],
                      ["• v2 (11/25): 처리 단계별 9줄 + 접는 패널 2개", "• 자주 쓰는 10개에 숫자 단축키, 한 화면에 버튼 + 그림", "• Alt+R로 설정·설명서·치트시트·대본 전부 수정", "• pilot_A · pilot_B · practice 세 프로젝트에 적용"],
                      MF / "F2_ui_callouts.png", "labelling screen v2 (pilot image 1): ② class buttons in stage rows, ③ image, ⑤ attributes, ⑥ regions / relations, ⑦ Submit.",
                      fig_box=(5.35, 1.45, 7.5, 3.75),
                      take="화면 자체가 분류 체계입니다 — 버튼 순서가 곧 처리 순서")

    # 6 problem 3: training material --------------------------------------------
    s = problem_slide(D, "Problem 3 — training first-time annotators remotely",
                      "지난주 계획은 화상 2시간 교육 + 1쪽 요약 카드. 두 분 다 처음이고 시차가 있어 2시간을 잡기 어려웠고, 오늘 줌으로 설명한 뒤 받은 첫 피드백이 '요약 카드가 화면과 달라서 헷갈린다'(이름·순서·모양이 다름). "
                      "조치: ① 따라하기 설명서 37쪽 — 모든 캡처가 실제 파일럿 서버 화면, 조각 갤러리는 실제 파일럿·연습 그림에서 잘라 냄, 1번 그림을 처음부터 끝까지, 연습 5장 정답과 이유, 제출 전 체크리스트; "
                      "② 치트시트 v2(2쪽): 앞면은 설정 파일에서 버튼을 읽어 화면과 같은 순서·색·단축키로 그리고 옆에 한글 이름과 한 줄 판별, 뒷면은 헷갈리는 짝과 규칙; ③ 줌 20분 + 연습 5장 → 교육 2시간을 대체. 애매하면 메모 칸에 적고 넘어가도록 안내.\n"
                      "예상 질문 — '교육 없이 되나?': 연습 5장을 먼저 하고 정답과 비교. κ가 낮으면 그 자체가 가이드라인을 고칠 근거. '37쪽을 읽겠나?': 그림 위주라 30분. 치트시트는 작업 중 옆에 두는 용도.",
                      "2시간 교육 대신 '실제 화면으로 따라하기' 설명서와 화면을 그대로 옮긴 치트시트로 바꿨습니다",
                      ["• 화상 교육 2시간 계획", "• 1쪽 요약 카드 (글자 위주)"],
                      ["• 두 분 다 처음 + 시차 → 2시간 잡기 어려움", "• 첫 피드백: \"카드가 화면과 달라 헷갈린다\"", "• 이름·순서·모양이 화면과 다름"],
                      ["• 따라하기 설명서 37쪽: 실제 화면 캡처 15 + 실물 조각 9 + 연습 5장 정답", "• 치트시트 v2: 설정 파일에서 버튼을 읽어 화면과 똑같이", "• 줌 20분 + 연습 5장 → 2시간 교육 대체", "• 애매하면 메모 칸에 적고 넘어가기"],
                      None, None)
    xa, ya, wa, ha, _ = picture(s, FIG / "cheat_v1_p1.png", 1.45, 3.6, 2.35, x=5.35)
    textbox(s, 5.35, ya + ha + 0.02, 3.6, 0.3, [("cheat sheet v1 — text only, not like the screen", False, 9, RED)])
    xb, yb, wb, hb, _ = picture(s, FIG / "cheat_p1.png", 1.45, 3.6, 2.35, x=9.2)
    textbox(s, 9.2, yb + hb + 0.02, 3.6, 0.3, [("cheat sheet v2 — the buttons as on screen + Korean hints", False, 9, GREEN)])
    xt = 5.35
    for p, cap in [("tut_p06.png", "screen tour"), ("tut_p13.png", "which class (real crops)"), ("tut_p22.png", "drawing edges"), ("tut_p31.png", "practice answers")]:
        _, _, w, h, _ = picture(s, FIG / p, 4.2, 1.75, 1.55, x=xt)
        textbox(s, xt, 5.77, 1.75, 0.28, [(cap, False, 8.5, GREY)], align=PP_ALIGN.CENTER)
        xt += 1.9
    takeaway(s, "화면 · 종이 · 설명서가 같은 이름, 같은 순서 — 외울 것이 없습니다", 6.1, 16)

    # 7 live demo -------------------------------------------------------------------
    s = D.slide("Live demo: the annotators' screen (link + backup video)",
                "시연 순서(1분): 버튼 클릭 → 브라우저에서 공개 주소 열림(처음 한 번 ngrok 안내 → Visit Site) → 로그인 → practice 프로젝트 → 1번 그림 → aerobic_zone 버튼(3) → 드래그로 박스 → 박스 클릭 → 속성 → 두 번째 박스 → Alt+R → 연결 → Submit은 누르지 않음(연습 결과 보존). "
                "네트워크가 안 되면 오른쪽 영상(실제 서버 화면 캡처 13장, 42초)을 재생. 영상은 화면 녹화가 아니라 설명서용 캡처를 이어 붙인 것.\n"
                "말씀드릴 포인트: ① 설치·가입 없이 브라우저만, ② 버튼 = 분류 체계, ③ 박스 → 속성 → 연결이 한 화면, ④ Submit 전에는 저장되지 않음(어노테이터 규칙).")
    message(s, "클릭 한 번으로 어노테이터가 보는 화면에 들어갑니다 — 박스 하나, 속성, 선 하나를 직접 보여 드리겠습니다")
    link_button(s, 0.52, 1.5, 5.0, 1.0, "Open Label Studio  ▶", LS_URL, "decent-reopen-curable.ngrok-free.dev · 처음 한 번 'Visit Site'")
    panel(s, 0.52, 2.7, 5.0, 2.75, "시연 순서 (약 1분)",
          ["1  로그인 → practice 프로젝트 → 1번 그림", "2  라벨 버튼(예: aerobic_zone, 단축키 3) → 그림 위 드래그 → 박스", "3  박스 클릭 → 속성 2개 (visual_form, confidence)",
           "4  두 번째 박스 → 출발 박스 클릭 → Alt+R → 도착 박스 클릭 → 선", "5  Regions / Relations 목록 확인 (Submit은 누르지 않음)",
           "", "**네트워크가 안 되면 → 오른쪽 영상 (실제 화면 캡처 13장, 42 s)"], T_BLUE, B_BLUE, NAVY, size=11.5)
    s.shapes.add_movie(str(FIG / "demo_steps.mp4"), Inches(5.8), Inches(1.5), Inches(7.0), Inches(3.94), poster_frame_image=str(FIG / "demo_poster.png"), mime_type="video/mp4")
    caption(s, "backup video: 13 real captures of the pilot server (login → box → attributes → edge → submit), 3 s each.", 5.5, x=5.8, w=7.0, align=PP_ALIGN.LEFT, size=9)

    # 8 problem 4: a yardstick for the model --------------------------------------
    problem_slide(D, "Problem 4 — no yardstick for the model until all labels are in",
                  "지난주 계획은 '본 어노테이션이 끝난 뒤 학습'. 그러면 두 달 동안 보여 드릴 숫자가 없고, 배치마다 학습해도 시험 세트가 매번 달라지면 점수를 비교할 수 없음. "
                  "조치(11/23 결정): ① 고정 시험 세트 150장을 먼저 정해 동결(main 910에서 파일럿 60장과 같은 문서의 그림을 뺀 풀 696장/511 문서, 출처 비례 + 출처당 최소 8장 + 문서당 1장, seed 20261123); 접촉 시트로 양식 검토 후 19장 교체; "
                  "첫 본 배치로 두 명이 이중 라벨링. ② 그 뒤 학습 라벨 100~150장(또는 2주)마다 재학습 → 같은 시험 세트에서 채점 → 한 줄 기록. ③ 사전 라벨(모델 예측을 미리 넣어 주기)은 3라운드 이후(학습 300장↑, 시험 AP50 0.70↑), 시험 세트에는 절대 금지.\n"
                  "예상 질문 — '왜 150장?': 클래스별 AP를 낼 최소 규모(장당 10~15 객체 → 약 2,000 박스)이고 출처 6종을 다 넣으려면 바닥 8장이 필요. '시험 세트를 먼저 라벨링하면 학습이 늦어지지 않나?': 150장이면 두 명이 1~2주, 그 뒤 모든 라운드가 비교 가능해지는 비용.",
                  "시험 세트 150장을 먼저 고정해 두면 배치마다 같은 잣대로 점수가 나옵니다 — 그것이 논문의 데이터 효율 곡선",
                  ["• 본 어노테이션 완료 후 학습", "• 분할(train/val/test)은 끝나고 결정"],
                  ["• 두 달간 보여 드릴 숫자가 없음", "• 배치마다 시험 세트가 달라지면 점수 비교 불가", "• 라벨이 몇 장이면 충분한지 알 수 없음"],
                  ["• 고정 시험 세트 150장 추출(11/23) + 양식 검토(11/24, 19장 교체) → 동결", "• 배치 100~150장 또는 2주마다 재학습 → 같은 시험 세트 채점 → 한 줄 기록", "• 파일럿 60 = 검증, 학습은 배치로 누적 (문서 단위 분리)", "• 사전 라벨은 3라운드 이후, 시험 세트에는 금지"],
                  FIG / "fig_incremental.png", "main set split (left) and the per-batch loop (right).", fig_box=(5.35, 1.5, 7.5, 3.0),
                  take="라벨이 다 끝나기 전에도 라운드마다 숫자가 나옵니다")

    # 9 problem 5: duplicates ---------------------------------------------------
    problem_slide(D, "Problem 5 — duplicates found while reviewing the test set",
                  "시험 세트 접촉 시트를 보다가 같은 그림이 두 번 들어온 것을 발견: 페이지 렌더를 잘라 낸 크롭과 같은 페이지의 내장 이미지가 해상도·여백이 달라 1차 pHash(≤6)를 통과. s26으로 main만 다시 훑음: "
                  "① 같은 문서·같은 페이지의 크롭–내장 쌍 69(30쌍은 사람이 나란히 비교), ② main 전체 pHash ≤ 8 근접 쌍 26(특허 패밀리의 같은 도면, Wikimedia SVG/PNG 동일 파일), ③ 배경이 검게 변한 알파 PNG, ④ 비영어 캡션 검출 보강(불·독·스페인어). "
                  "적용 11/24: main 993 → 910. 남는 쪽 규칙: 시험·파일럿 세트 멤버 우선, 그 외 내장 이미지(크롭의 50 % 미만이면 크롭). 시험 세트는 교체 19장 뒤 v8로 동결.\n"
                  "예상 질문 — '910이면 Theisen 1,005보다 적은데?': 박스 수는 비슷(10,000~15,000 추정)하고 그래프 정답이 더해짐. 크롭 대기 223장을 처리하면 다시 늘어남. 중복을 두면 train/test에 같은 그림이 들어가 점수가 부풀려지므로 지금 잡는 것이 맞음.",
                  "같은 그림이 둘로 들어온 쌍을 걸러 main 993 → 910. 지금 잡지 않으면 train과 test에 같은 그림이 들어갑니다",
                  ["• main 993장 (11/16 확정)", "• 1차 중복 제거 pHash ≤ 6 (s07)"],
                  ["• 페이지 크롭 vs 내장 이미지 = 같은 그림인데 해상도·여백이 달라 통과", "• 특허 패밀리 간 같은 도면, SVG/PNG 같은 파일", "• 배경이 검게 변한 PNG(선이 사라짐)"],
                  ["• s26 2차 점검: 크롭–내장 쌍 69, 근접 쌍 26, 깨진 PNG; 사람이 30쌍 비교", "• 적용 11/24: main 993 → 910 (tier A 722 / B 188)", "• 시험 세트 19장 교체 후 동결 (v8)", "• 비영어 캡션 검출 보강 (불·독·스페인어)"],
                  FIG / "dedup_pair.png", "one twin pair from the review sheet: embedded image (left, kept) vs crop of the page render (right, dropped).", fig_box=(5.35, 1.5, 7.5, 4.3),
                  take="시험 세트 검토가 데이터 결함을 잡는 두 번째 그물이 됐습니다")

    # 10 model side -------------------------------------------------------------------
    s = D.slide("Model side: no numbers yet, but ready for the first ones",
                "라벨이 0장이라 학습도 수치 평가도 아직 불가(11/23 합의대로 배치마다 갱신). 그동안 한 것 둘. (1) 채점 코드를 끝까지 검증: Label Studio 내보내기 → 그래프 정답 변환(s22) → 채점(s23) → 일치도(s17). 11/19 모의 데이터 6장으로 돌려 출력 형식 확정 — "
                "검출 mAP, 박스형 의미 매핑 정확도, 노드/엣지 P·R·F1, 방향 정확도, 그래프 편집 거리, κ와 신뢰구간. 표의 숫자는 모의 데이터라 성능이 아니라 '무엇이 나오는가'의 예시. "
                "(2) 라벨 0장 기준선 두 가지를 파일럿 60장에 돌릴 준비: VLM 제로샷(클래스 목록과 규칙을 주고 노드·엣지 JSON, s24 완성, 60장에 몇 달러), 개방형 어휘 검출기(Grounding DINO / OWLv2, 클래스 이름을 텍스트로, CPU 가능). "
                "Theisen의 학습된 가중치는 쓰지 않음(화공 클래스가 겹치지 않아 우리 연구에 필요 없음); Faster R-CNN은 우리 라벨로 재현. 첫 숫자 = 파일럿 판정 직후: 사람 상한(κ·엣지 F1) vs 라벨 0장 기준선.\n"
                "예상 질문 — 'VLM이 잘하면 로컬 모델이 왜 필요한가?': 그 질문에 답하려고 재는 것. 박스 좌표·재순환·구역 경계에서 VLM이 약할 것이 예상이고 숫자로 보이면 논문의 동기. 뜻밖에 잘하면 사전 라벨로 활용.")
    message(s, "라벨이 0장이라 모델 숫자는 아직 없습니다(계획대로). 라벨이 오는 순간 숫자가 나오도록 채점 코드와 0장 기준선을 준비했습니다", size=15)
    # flow: three boxes
    panel(s, 0.52, 1.5, 3.9, 1.75, "① 사람 라벨 (파일럿 60장)", ["• 두 명 독립 라벨링 → 판정", "• 사람 상한 = κ · 엣지 F1", "• 상태: 이번 주 시작, 0 / 60"], T_RED, B_RED, RED)
    panel(s, 4.72, 1.5, 3.9, 1.75, "② 채점 코드 (검증 완료)", ["• 내보내기 → 그래프 정답 → 채점 → 일치도", "• 11/19 모의 데이터 6장으로 끝까지 실행", "• 출력: 검출 AP · 엣지 F1 · 방향 · κ(CI)"], T_GREEN, B_GREEN, GREEN)
    panel(s, 8.92, 1.5, 3.9, 1.75, "③ 라벨 0장 기준선 (준비)", ["• VLM 제로샷 (s24 완성, 60장 몇 달러)", "• 개방형 어휘 검출기 (설정 예정, CPU)", "• 학습 없음 → 데이터 효율 곡선의 0점"], T_BLUE, B_BLUE, NAVY)
    for x0 in (4.42, 8.62):
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x0 - 0.02), Inches(2.3), Inches(0.34), Inches(0.4)); a.fill.solid(); a.fill.fore_color.rgb = B_GREY; a.line.fill.background()
    table(s, ["what the scoring code reports (dry run, synthetic labels — format only)", "example"],
          [["detection mAP50 (33 classes) / folded to 7 stages", "0.72 / 0.80"], ["semantic mapping accuracy on box-form units", "0.82"],
           ["edge F1 (class required / class-agnostic)", "0.42 / 0.58"], ["direction accuracy (arrowhead edges)", "1.00"],
           ["annotator agreement κ with 95 % CI · edge F1", "0.93 [0.92–0.94] · 0.67"]],
          x=0.52, y=3.5, w=7.4, col_w=[5.6, 1.8], size=10, row_h=0.36)
    panel(s, 8.15, 3.5, 4.65, 2.3, "첫 숫자가 나오는 시점",
          ["• 파일럿 판정 직후: 사람 상한 vs 라벨 0장 기준선", "• 라운드 1(시험 세트 150) 뒤: 첫 학습 모델 (Faster R-CNN 재현 + 최신 검출기)", "• 라운드마다 같은 시험 세트 → 곡선이 자라남", "• GPU: 라운드 1부터 랩 GPU 1장"], T_GREY, B_GREY, DARK, size=11)
    takeaway(s, "지금 할 수 있는 모델 작업은 '채점 준비'까지 — 첫 숫자는 파일럿 판정 직후", 6.1, 16)

    # 11 next steps ---------------------------------------------------------------
    s = D.slide("Next steps: pilot → adjudication → test set → batches",
                "날짜 대신 순서와 대략 기간. 파일럿 60장 × 2명 약 1주 → 판정·κ·가이드라인 v2·클래스 병합 약 1주 → 다음 미팅에 파일럿 결과와 라벨 0장 기준선 숫자. 첫 본 배치 = 고정 시험 세트 150장 이중 라벨링 약 2주. 그 뒤 배치 2~5(각 100~150장, 약 2주씩). "
                "모델 라운드는 배치 1 뒤부터 배치마다. 병행: 연결 복원 모듈, 공정 순서 사전지식, QSDsan 매핑, 원고 서론·데이터 절. 총 작업량 약 1,120 장-회, 장당 8~15분 → 두 명이 하루 30장씩이면 순수 약 4주, 학업·판정을 넣으면 두 달 반 안팎.\n"
                "예상 질문 — '언제 끝나나?': 두 달 반 안팎이 기준이되 학생 일정에 따름. 라벨이 끝나기 전에도 라운드마다 숫자가 나옴. '시험 기간은?': 배치 간격이 느슨해 한두 주 밀려도 순서만 유지하면 됨.")
    message(s, "이번 주 파일럿 → 다음 미팅에 판정 결과 → 시험 세트 150장 → 배치 4개.  두 달 반 안팎, 학생 일정에 맞춥니다")
    _, yy, _, hh, _ = picture(s, FIG / "fig_schedule.png", 1.5, 12.3, 4.1)
    caption(s, "order and rough durations (weeks from now); dotted lines = next meeting (pilot results), round-1 numbers, all labels in.", yy + hh + 0.02, size=9)

    # 12 decisions -------------------------------------------------------------------
    s = D.slide("Decisions requested today",
                "지난주에 이번 주로 넘긴 안건(규모·인력·서버) + VLM 대조군. 규모: main 910 전부 — 줄여야 하면 학습 배치를 줄이고 시험 세트 150은 유지. 인력: 랩 학생 2명, 두 달 반 안팎, 하루 30장(1~2시간); 파일럿·시험 세트는 두 명 모두, 학습 배치는 나눠서(10 %는 이중 라벨링으로 품질 감시); 판정은 제가 주 2회. "
                "서버: 파일럿은 제 노트북 + 고정 주소(지금), 본 어노테이션은 랩 리눅스 서버에 Label Studio 상시 가동 + 개인 계정(설치 pip 한 줄, DB 파일 복사; 테일넷 안이면 터널 불필요), 학습은 랩 GPU 1장(라운드마다 수 시간). VLM 대조군: 파일럿 60장에 한해 실행(수 달러).\n"
                "예상 질문 — '학생 2명으로 충분한가?': 2명이면 두 달 반 안팎, 1명이면 두 배. '본인이 한국에 돌아오면?': 서버가 랩에 있으면 위치 무관. 'Max 쪽은?': 데이터·가중치는 받지 않음(필요 없음), 연결 복원 방식과 클래스 정의만 참고; 공동 저자 구조는 양쪽 교수님 합의 필요(지난주와 동일).")
    message(s, "아래 세 가지를 승인받으면 이번 주부터 그대로 진행합니다")
    table(s, ["", "proposal", "why / what it costs"],
          [["① Scale & people", "all 910 main images (pilot 60 ×2, test 150 ×2, train ≈ 700); 2 lab students, ≈ 30 images/day each, about 2.5 months; adjudication by me twice a week",
            "≈ 1,120 image-labellings, 8–15 min each; if the scale must shrink, cut training batches, never the test set"],
           ["② Lab server & GPU", "main annotation on the lab Linux server (Label Studio always on, individual accounts); training on one lab GPU from batch 1",
            "pip install + copy the DB file; inside the tailnet no tunnel; a few GPU-hours per round"],
           ["③ VLM control", "run the zero-shot VLM baseline on the pilot 60 only, reported as the 0-label point",
            "a few dollars; answers 'why not just an API model' with numbers — local models stay the deliverable"]],
          x=0.52, y=1.5, w=12.3, col_w=[2.0, 5.6, 4.7], size=11.5, row_h=0.9, first_col_bold=True)
    textbox(s, 0.52, 5.55, 12.29, 0.6, [("① 규모·인력 승인   ② 랩 서버·GPU 사용   ③ VLM 대조군 실행", True, 18, RED)], align=PP_ALIGN.CENTER)

    # 13 thanks ---------------------------------------------------------------------
    s = D.slide("", "마무리: 결정 세 가지를 다시 짚고 질문. 다음 미팅에는 파일럿 κ·판정표·장당 시간과 라벨 0장 기준선 숫자를 가져옴.")
    textbox(s, 1.0, 3.0, 11.3, 1.0, [("Thank You for Your Kind Attention", True)], 32, NAVY, PP_ALIGN.CENTER)

    # ------------------------------------------------------------------ appendix
    s = D.slide("Appendix A: fixed test set — allocation and visual check", "부록. 고정 시험 세트 배분표(출처별), 양식 분포, 교체 사유.")
    table(s, ["source", "pool", "share", "drawn", "non-en", "main categories"],
          [["Patents (US / KR / CN)", "273", "39 %", "48", "33", "wwtp 45, wtp 1, sludge 1, other 1"], ["PMC OA papers", "303", "44 %", "50", "0", "wwtp 29, pilot 14, other 3, wtp 2, sludge 2"],
           ["Other OA papers (OpenAlex)", "80", "12 %", "24", "1", "wwtp 21, other 1, wtp 1, pilot 1"], ["US EPA manuals", "11", "2 %", "9", "0", "wwtp 8, sludge 1"],
           ["Wikimedia Commons", "19", "3 %", "11", "0", "wwtp 11"], ["Korean municipal", "10", "1 %", "8", "8", "wwtp 8"], ["total", "696", "", "150", "42", "146 documents; tier A 113 / B 37"]],
          x=0.55, y=0.95, w=8.0, col_w=[2.3, 0.7, 0.7, 0.7, 0.8, 2.8], size=10, row_h=0.36)
    table(s, ["visual form (after review)", "n"], [["A box-form", "55"], ["B symbol-form", "49"], ["C pictorial", "38"], ["S simulator / other", "7"], ["D simulator screenshot", "1"]],
          x=8.9, y=0.95, w=3.9, col_w=[2.9, 1.0], size=10, row_h=0.36)
    bullets_box(s, [(0, "Pool = main 910 − pilot 59 − other images of pilot documents 96 − page renders pending crop 33 − excluded list 26 = 696 images / 511 documents"),
                    (1, "proportional allocation with a floor of 8 per source; one image per document; seed 20261123 (re-runnable)"),
                    (1, "visual check on contact sheets: 19 swapped — 10 cross-sections / equipment drawings, 4 number-only patent boxes, 5 other; same source / language / category"),
                    (1, "frozen after review (v8); used as batch 1 of the main annotation, double-annotated, never trained on or pre-annotated")],
                x=0.55, y=4.0, w=12.2, h=2.3, sizes=(12, 10.5, 10))

    s = D.slide("Appendix B: operations detail (pilot)", "부록. 운영 세부: 시작 스크립트, DB 도구, 백업, 보안, 복구 절차.")
    bullets_box(s, [(0, "Start / restart (one command, in a normal PowerShell window)"),
                    (1, "start_pilot.ps1: starts Label Studio with the CSRF / no-signup settings the public address needs, starts ngrok on the fixed domain, checks the public login page; skips what already runs"),
                    (1, "nothing to do after sleep / wake or a network change; only after a reboot or closed windows"),
                    (0, "Progress, export, backup without the server (s27_export_from_db.py)"),
                    (1, "--status: tasks / annotations / hours / last submission per project · --export pilot_A,pilot_B → JSON for s17 (agreement) / s19 (edge medium rules) / s22 (ground truth) · --backup: dated copy of the DB"),
                    (0, "Security"),
                    (1, "HTTPS via ngrok; sign-up disabled (one shared account, one project per annotator, results hidden from each other); password rotated after the pilot; no personal data in the images"),
                    (0, "Failure modes"),
                    (1, "laptop off → annotators see no page → they message me → one command. Submitted work is in the DB (Submit saves)"),
                    (1, "Cloudflare quick tunnel kept as a fallback (run_tunnel.ps1) if the ngrok free plan changes")],
                x=0.55, y=0.95, w=12.2, h=5.3, sizes=(13, 11, 10))

    s = D.slide("Appendix C: overall plan with status (updated from 11/20)",
                "부록. 지난주 안내도에 상태를 갱신: 완료 = 수집·선별, 분류 체계, 정답 양식·평가 코드, 고정 시험 세트, 어노테이션 도구; 진행 = 파일럿, 영점 기준선; 남은 것 = 판정, 본 어노테이션, 모델, 후속 활용.")
    picture(s, V2 / "fig_framework_status.png", 1.0, 12.3, 5.0)
    textbox(s, 0.52, 6.05, 12.29, 0.5, [("since 11/20: + fixed test set, + incremental protocol, + annotation tools v2, + server ops;  pilot now running;  zero-shot baselines queued", False, 12, GREY)], align=PP_ALIGN.CENTER)

    D.save()


# ------------------------------------------------------------------ speaker script → notes
SCRIPT = ROOT / "meeting" / f"WWTP_vision_meeting_{MEETING}_v{DECK_VERSION}_script.md"


def read_script(md_path: Path) -> dict[int, str]:
    """'## <n>. <title>' sections of the script file → {n: spoken text}. Stops at the first '---' after the sections."""
    import re
    sections: dict[int, str] = {}
    cur, buf = None, []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## (\d+)\.\s*(.*)$", line)
        if m:
            if cur is not None:
                sections[cur] = "\n".join(buf).strip()
            cur, buf = int(m.group(1)), []
            continue
        if cur is not None and line.strip() == "---":        # end of the per-slide part
            sections[cur] = "\n".join(buf).strip(); cur = None
            continue
        if cur is not None:
            buf.append(line)
    if cur is not None:
        sections[cur] = "\n".join(buf).strip()
    return sections


def apply_script(pptx_path: Path = None, md_path: Path = None) -> int:
    """prepend the spoken script to each slide's notes; the builder's memo / expected questions stay below a divider."""
    from pptx import Presentation
    pptx_path = pptx_path or v2.OUT
    md_path = md_path or SCRIPT
    if not md_path.exists():
        print(f"[script] no script file: {md_path}"); return 0
    sections = read_script(md_path)
    prs = Presentation(str(pptx_path))
    n = 0
    for i, slide in enumerate(prs.slides, start=1):
        if i not in sections:
            continue
        tf = slide.notes_slide.notes_text_frame
        memo = tf.text.strip()
        memo = memo.split("\n— 메모 · 예상 질문 —\n", 1)[-1] if "— 메모 · 예상 질문 —" in memo else memo
        tf.text = sections[i] + ("\n\n— 메모 · 예상 질문 —\n" + memo if memo else "")
        n += 1
    prs.save(str(pptx_path))
    print(f"[script] notes updated on {n} slides ← {md_path.name}")
    return n


if __name__ == "__main__":
    build()
    apply_script()
