"""
build_tutorial.py — step-by-step illustrated tutorial for annotators (self-study, remote).

Output: WWTP_annotation_tutorial_v1.docx (PDF via Word COM: build_tutorial.py --pdf).
Figures: figures_tutorial/ (make_tutorial_figures.py: galleries G*, states S*, practice keys PR*)
         figures_tutorial/U*.png = Label Studio screen captures taken on the adjudicator's PC
         (missing captures are replaced by a grey placeholder so the document always builds).
Reuses the Doc helper and some figures of build_manual.py (F1 workflow, F5 edges).
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

from build_manual import Doc, HERE, ACCENT, GREY, set_font, shade

OUT = HERE / "WWTP_annotation_tutorial_v1.docx"
FT = HERE / "figures_tutorial"
F = HERE / "figures"

# ---- screen captures: name -> (caption, what the reader should look at)
SHOTS = {
    "U01_login": "로그인 화면. 받은 주소를 열면 이 화면이 나온다. 이메일·비밀번호는 판정자가 보낸 것.",
    "U02_projects": "프로젝트 목록. 본인 것(pilot_A 또는 pilot_B)만 연다. practice는 연습용.",
    "U03_tasks": "작업 목록. 번호 순서(1~60)로 되어 있다. 1번을 클릭하면 라벨링 화면이 열린다.",
    "U04_labeling": "라벨링 화면. ① 라벨 버튼 ② 그림 ③ 확대·이동 ④ 속성 칸 ⑤ Regions/Relations ⑥ Submit",
    "U05_label_pressed": "라벨 버튼을 누르면 버튼이 진해진다. 이 상태에서 그림 위를 드래그한다.",
    "U06_box_drawn": "드래그를 놓으면 박스가 생기고 Regions 목록에 한 줄 추가된다.",
    "U07_box_selected": "박스를 클릭하면 속성 칸이 나온다. visual_form과 confidence를 고른다.",
    "U08_regions": "Regions 목록. 지금까지 친 박스가 쌓인다. 여기서 클릭해도 선택된다.",
    "U09_zone_attr": "구역 박스는 is_zone의 zone을 체크한다.",
    "U10_parent_of": "부모 박스 → Alt+R → 자식 박스 클릭 → 관계 라벨에서 parent_of를 고른다.",
    "U11_relation_r": "출발 박스를 클릭한 뒤 키보드 Alt+R을 누르면 연결 모드가 된다.",
    "U12_relations_tab": "도착 박스를 클릭하면 Relations 탭에 관계가 한 줄 생긴다.",
    "U13_relation_label": "관계 줄의 라벨 칸. 점선·방향 없음 같은 예외일 때만 고른다.",
    "U14_image_attrs": "그림 전체 속성. 맨 아래로 내리면 diagram_style·language·n_panels·공정 이름·메모 칸이 있다.",
    "U15_submit": "Submit을 누르면 저장되고 다음 장으로 넘어간다. 누르기 전에는 저장되지 않는다.",
}


class TDoc(Doc):
    def tfig(self, name, caption, width_cm=16.5):
        p = FT / name if (FT / name).exists() else F / name
        if not p.exists():
            self.placeholder(name, caption)
            return
        self.fig(str(p), caption, width_cm)

    def placeholder(self, name, caption):
        t = self.d.add_table(rows=1, cols=1)
        c = t.rows[0].cells[0]; shade(c, "EEEEEE")
        para = c.paragraphs[0]; para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(para.add_run(f"[화면 캡처 예정: {name}]"), 11, True, GREY)
        for _ in range(5):
            c.add_paragraph()
        cap = self.d.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(cap.add_run(caption), 9, color=GREY); cap.paragraph_format.space_after = Pt(8)

    def step(self, no, title, todo, fig=None, caption="", check="", width_cm=16.5, notes=()):
        """One step = heading + '할 일' + figure + '확인'."""
        self.h(f"단계 {no}. {title}", 2)
        para = self.d.add_paragraph()
        set_font(para.add_run("할 일  "), 10.5, True, ACCENT)
        self._runs(para, todo)
        for n in notes:
            self.bullet(n)
        if fig:
            if fig.startswith("U"):
                self.tfig(fig + ".png", caption or SHOTS.get(fig, ""), width_cm)
            else:
                self.tfig(fig, caption, width_cm)
        if check:
            para = self.d.add_paragraph()
            set_font(para.add_run("확인  "), 10.5, True, RGBColor(0xB8, 0x70, 0x1E))
            self._runs(para, check)

    def kv(self, rows, widths=(4.5, 12.5), size=9.5):
        self.table(["항목", "내용"], rows, list(widths), size=size)


def build():
    D = TDoc()
    D.p()
    D.p("하수처리장 공정도 어노테이션", 24, True, ACCENT, "center")
    D.p("따라하기 설명서 — 처음 하는 사람을 위한 단계별 그림 안내", 15, True, None, "center")
    D.p("파일럿 v1.1b (쉬운 버전) · Label Studio · 2026-11-25", 11, color=GREY, align="center")
    D.p()
    D.note("이 문서는 한 번도 해 본 적이 없는 사람이 혼자 읽고 따라 할 수 있게 썼습니다. 한 쪽에 한 단계씩, 실제 화면과 실제 그림 조각을 넣었습니다. "
           "규칙을 전부 외울 필요는 없습니다. 1~3부를 따라 해 보고, 4부(이름 고르기)는 작업하면서 필요할 때 펼쳐 보면 됩니다. "
           "짧은 요약은 치트시트(1쪽), 규칙 전체는 쉬운 버전 매뉴얼(9쪽)에 있습니다.")

    D.h("0. 시작하기 전에")
    D.p("**우리가 하는 일.** 하수처리장 공정도(논문·보고서·특허에 나오는 흐름도) 위에서 ① 장치마다 네모(박스)를 치고 ② 무슨 장치인지 이름을 고르고 ③ 어디서 어디로 흐르는지 선으로 잇습니다. "
        "이렇게 모은 자료로, 그림만 보고 공정 흐름을 읽어 내는 컴퓨터 모델을 만듭니다.")
    D.p("**세 가지만 기억하세요.** 빠짐없이(그림에 있는 건 다 표시), 규칙대로 똑같이(같은 상황이면 같은 선택), 그림에 있는 것만(짐작으로 넣지 않기).")
    D.tfig("F1_workflow.png", "그림 0-1. 한 장에서 하는 다섯 단계. 쉬운 버전(21~60번)에서는 ②가 많이 줄고 ④는 선만 긋는다.", 16.5)
    D.kv([
        ["받아야 할 것", "접속 주소 https://decent-reopen-curable.ngrok-free.dev (고정, 바뀌지 않음), 로그인 이메일·임시 비밀번호, 내 프로젝트 이름(pilot_A 또는 pilot_B)"],
        ["읽을 것", "이 문서 → 치트시트 1쪽(옆에 두고 작업) → 쉬운 버전 매뉴얼 9쪽(규칙 전체)"],
        ["장비", "노트북 + 마우스 권장(터치패드로도 되지만 드래그가 불편). 모니터가 크면 좋다. 설치할 것은 없다."],
        ["시간", "교육 2시간 + 연습 5장. 본 작업 60장은 하루 30장 정도, 장당 10~15분."],
        ["하지 말 것", "작업 중 다른 어노테이터와 상의하지 않기. 애매하면 메모 칸에 한 줄. 프로젝트 Settings·휴지통·Account & Settings는 열지 않기(공용 계정이라 클릭 한 번에 프로젝트가 지워질 수 있다)."],
    ])

    # ------------------------------------------------------------ 1. access
    D.pagebreak()
    D.h("1부. 접속하기")
    D.step("1-1", "주소 열고 로그인", "브라우저(Chrome 권장)에 `https://decent-reopen-curable.ngrok-free.dev` 를 붙여 넣는다. 처음 한 번은 'You are about to visit … served by ngrok' 이라는 안내 화면이 나오는데, **Visit Site** 버튼을 누르면 된다(일주일에 한 번 정도 다시 나온다). 로그인 화면이 나오면 받은 이메일과 비밀번호를 넣는다.",
           "U01_login", check="로그인 뒤 프로젝트 목록이 보이면 성공. 주소가 안 열리면 판정자 노트북이 꺼져 있거나 잠든 것이니 판정자에게 알린다.",
           notes=["주소는 고정이다. 즐겨찾기에 넣어 두면 편하다.", "가입(Sign up)은 하지 않는다. 받은 계정으로만 들어간다."])
    D.step("1-2", "내 프로젝트 열기", "프로젝트 목록에서 **내 것만** 연다. A는 pilot_A, B는 pilot_B. 연습은 practice.",
           "U02_projects", check="프로젝트 안에 그림 60장(연습은 5장)이 번호 순으로 보인다.")
    D.step("1-3", "1번 그림 열기", "작업 목록에서 맨 위 1번을 클릭한다. 라벨링 화면이 열린다.",
           "U03_tasks", check="화면 위에 색깔 라벨 버튼, 가운데에 그림, 오른쪽에 빈 Regions 목록이 보인다.",
           notes=["번호 순서대로 한다. 1~20번은 완전판(화살촉·글자까지), 21~60번은 쉬운 버전(장치·구역·단자·분기·합류·계측만). 7부 참고."])

    # ------------------------------------------------------------ 2. screen
    D.pagebreak()
    D.h("2부. 화면 익히기")
    D.step("2-1", "화면의 여섯 부분", "아무것도 누르지 말고 화면을 한 번 훑어본다. 쓰는 곳은 여섯 군데뿐이다.",
           "U04_labeling", check="여섯 군데를 손으로 짚어 가며 이름을 말해 본다.")
    D.table(["번호", "이름", "하는 일"], [
        ["①", "라벨 버튼", "장치 이름. 처리 단계별로 줄을 나눠 놓았다(전처리 / 침전·물리화학 / 생물 반응 / 생물막 / 3차·소독 / 슬러지 / 보조 / 모를 때 / 연결 요소). 드물게 쓰는 혐기 폐수 반응기와 완전판 전용(화살촉·글자)은 접힌 줄을 눌러 연다. 자주 쓰는 것은 버튼에 적힌 숫자·글자 키로 바로 켠다."],
        ["②", "그림", "라벨 버튼을 켠 상태에서 드래그하면 박스가 생긴다."],
        ["③", "확대·이동", "마우스 휠 = 확대/축소, 손바닥 아이콘(또는 Space 누른 채 드래그) = 화면 옮기기. 작은 요소는 확대해서 그린다."],
        ["④", "속성 칸", "박스를 클릭하면 그 박스에 대한 질문(visual_form, confidence, is_zone, l1_hint, io_role, label_text)이 나온다."],
        ["⑤", "Regions / Relations", "친 박스 목록 / 그은 선 목록. 클릭하면 선택된다."],
        ["⑥", "Submit", "저장하고 다음 장으로. Ctrl+Enter와 같다. 누르기 전에는 저장되지 않는다."],
    ], [1.2, 3.3, 12.5])
    D.table(["키", "하는 일"], [["숫자 1~0", "자주 쓰는 장치 10개 (버튼에 적힌 숫자)"], ["a", "pump"], ["x / z", "process_unit_generic / unknown_equipment"], ["i / j / l", "io_terminal / junction_split / junction_merge"], ["드래그", "박스 그리기"], ["클릭", "박스 선택 (u = 선택 해제)"], ["Alt+R", "연결 모드 (출발 박스 선택 → Alt+R → 도착 박스 클릭)"], ["Backspace", "선택한 박스·관계 삭제"], ["Ctrl+Z", "되돌리기"], ["마우스 휠", "확대·축소"], ["Ctrl+Enter", "제출하고 다음 장"]], [4, 12])

    # ------------------------------------------------------------ 3. first box
    D.pagebreak()
    D.h("3부. 첫 박스 치기 (연습 1번 그림으로)")
    D.step("3-1", "라벨 버튼 누르기", "치려는 장치의 이름 버튼을 누른다. 예: 포기조면 `aerobic_zone`. 버튼이 진해지면 켜진 것이다.",
           "U05_label_pressed", check="버튼 하나만 진하다. 두 개가 켜져 있으면 한 번 더 눌러 끈다.")
    D.step("3-2", "드래그해서 박스 만들기", "장치의 왼쪽 위에서 오른쪽 아래로 드래그한다. 장치에 **딱 맞게**, 여유 없이. 글자(이름)는 박스에 넣지 않는다(장치 모양만).",
           "U06_box_drawn", check="박스가 장치를 꼭 감싼다. 오른쪽 Regions에 한 줄이 생겼다.",
           notes=["너무 작아 드래그가 어려우면 휠로 확대한 뒤 그린다.", "잘못 그렸으면 박스를 클릭하고 Delete. 바로 전 동작은 Ctrl+Z."])
    D.step("3-3", "박스 클릭하고 속성 고르기", "방금 그린 박스를 클릭한다. 아래에 질문이 나온다. 필수는 두 개: **visual_form**(어떻게 그려졌나)과 **confidence**(이름을 어떻게 알았나).",
           "U07_box_selected", check="두 항목에 각각 하나씩 체크되어 있다.")
    D.table(["visual_form", "뜻"], [["symbol", "장치 모양 기호(침전지 사다리꼴, 펌프 원, 스크린 빗살…)"], ["box", "글자가 적힌 네모·동그라미. 모양으로는 알 수 없고 글자로 안다"],
                                    ["pictorial", "3D 그림·사진 같은 실물 묘사"], ["simulator_icon", "GPS-X·SUMO 같은 시뮬레이터 화면의 아이콘"], ["section_view", "단면도·평면도(건물 도면처럼 그린 것)"]], [4, 12])
    D.table(["confidence", "뜻"], [["certain", "모양만 보고도 안다(기호·그림)"], ["inferred_from_text", "옆의 글자를 읽고 알았다"], ["inferred_from_context", "모양도 글자도 없고, 앞뒤 장치를 보고 추정했다"]], [4, 12])
    D.step("3-4", "다음 박스로", "다른 장치의 라벨 버튼을 누르고 3-2, 3-3을 반복한다. Regions 목록이 쌓인다.",
           "U08_regions", check="장치 수만큼 줄이 있다. 같은 장치가 네 개 나란히 있으면 네 개 다 친다. '×4'처럼 글자로만 적혀 있으면 하나만.")

    # ------------------------------------------------------------ 4. names
    D.pagebreak()
    D.h("4부. 이름 고르기 — 이렇게 생겼으면 이 이름")
    D.p("아래 그림들은 실제 파일럿·연습 그림에서 잘라 낸 것입니다. 초록 박스가 '여기에 이렇게 친다'입니다. 이름 고르는 순서는 네 단계입니다.")
    D.num("**글자가 있나?** 옆에 이름이 적혀 있으면 그 이름의 클래스. (침전지·포기조·소화조·여과…) confidence = inferred_from_text.")
    D.num("**모양으로 알 수 있나?** 사다리꼴·V자 = 침전지, 원 + 꼬리 = 펌프, 빗살 = 스크린, 달걀형 = 소화조, 점 무늬 기둥 = 생물막 반응기. confidence = certain.")
    D.num("**앞뒤를 보면 아나?** 생물반응조 **앞** 침전지 = primary, **뒤** = secondary. 소화조 **앞** 벨트·드럼 = thickener, **뒤** = dewatering. confidence = inferred_from_context.")
    D.num("**그래도 모르면** 목록에 없는 장치 = `unknown_equipment` + 글자 그대로 `label_text`. 글자도 없는 네모(번호만) = `process_unit_generic` + `l1_hint`(어느 단계인지) + 번호.")
    D.note("슬래시(/)가 있는 이름은 뒤까지 고른다: `biofilm_reactor/trickling_filter`(살수여상), `/mbbr_ifas`(담체), `/submerged_biofilter`(여재+공기), `/fluidized_expanded_bed`(유동상), `/rbc`(회전원판). `anaerobic_wastewater_reactor/uasb_egsb_ic` 등도 같다.")
    D.tfig("G1_preliminary.png", "그림 4-1. 전처리. 스크린은 기호·그림·글자 상자 어느 형태든 screen. '침사지 및 유입펌프장'처럼 한 덩어리면 바깥 pump_station + 안쪽 grit_chamber.", 16.5)
    D.pagebreak()
    D.tfig("G2_primary_secondary.png", "그림 4-2. 1차·2차 처리. 침전지는 생물반응조 앞이면 primary, 뒤면 secondary. 생물 반응 탱크는 포기(공기)면 aerobic, 교반만이면 anoxic/anaerobic(유입을 가장 먼저 받으면 anaerobic).", 16.5)
    D.pagebreak()
    D.tfig("G3_tertiary.png", "그림 4-3. 3차 처리·소독·물리화학. 처리수를 받는 막은 membrane_unit, 혼합액을 받고 슬러지를 돌려보내는 막은 mbr_unit. 약품 탱크가 그려졌으면 chemical_treatment_unit, 화살표만이면 장치가 아니다(6부).", 16.5)
    D.tfig("G4_sludge.png", "그림 4-4. 슬러지 처리. 소화조 앞의 농축(드럼·원심·중력)은 thickener, 뒤의 원심·벨트프레스는 dewatering_unit. 소각로·건조기는 drying_incineration_unit. 보일러·스크러버 같은 배가스 장치는 unknown + 글자.", 16.5)
    D.pagebreak()
    D.tfig("G5_ancillary.png", "그림 4-5. 보조 장치·generic·unknown·계측. 펌프·송풍기는 아무리 작아도 친다. 번호만 있는 상자 = generic + 번호, 단계 이름만 있는 상자('Biological Treatment') = generic + l1_hint. 목록에 없는 장치 = unknown + 글자.", 16.5)
    D.table(["l1_hint (generic·unknown일 때)", "뜻"], [["preliminary", "전처리(스크린·침사·조정)"], ["primary", "1차 침전"], ["secondary", "생물 처리"], ["tertiary", "3차·소독"],
                                                     ["sludge", "슬러지 처리"], ["sidestream", "반류수"], ["unknown", "모름"]], [6, 10])

    # ------------------------------------------------------------ 5. zones
    D.pagebreak()
    D.h("5부. 구역(zone) — 한 탱크 안의 칸")
    D.p("생물반응조 하나가 혐기·무산소·호기 **칸**으로 나뉘어 있으면, 칸마다 박스를 치고 **탱크 전체**에도 박스를 하나 더 친다. 전체 박스가 부모, 칸이 자식이다.")
    D.tfig("G7_zones.png", "그림 5-1. 구역 예. 칸이 한 탱크 안에 있으면 부모 + 자식. 탱크가 따로따로 그려져 있으면(CSTR 6개) 부모 없이 각각.", 16.5)
    D.step("5-1", "칸마다 박스 + is_zone", "칸 하나를 `anaerobic_zone`/`anoxic_zone`/`aerobic_zone`으로 치고, 속성에서 **is_zone의 zone**을 체크한다.",
           "U09_zone_attr", check="칸 박스마다 zone이 체크되어 있다.")
    D.step("5-2", "탱크 전체 박스", "탱크 전체를 감싸는 박스를 친다. 이름은 탱크에 적힌 대로(예: '생물반응조' → `process_unit_generic` + l1_hint=secondary). 산화구처럼 한 수로면 `aerobic_zone` 하나 + 메모.",
           check="전체 박스가 칸 박스들을 모두 감싼다.")
    D.step("5-3", "parent_of 연결", "전체 박스 클릭 → Alt+R → 칸 박스 클릭 → Relations에서 라벨 **parent_of**. 칸마다 반복.",
           "U10_parent_of", check="Relations 탭에 parent_of 줄이 칸 수만큼 있다.")

    # ------------------------------------------------------------ 6. connection elements
    D.pagebreak()
    D.h("6부. 연결 요소 — 단자·분기·합류·계측")
    D.p("장치가 아니지만 흐름을 잇는 데 필요한 것들입니다. 쉬운 버전(21~60번)에서도 칩니다.")
    D.table(["클래스", "어디에", "속성"], [
        ["`io_terminal`", "그림 밖에서 들어오거나 밖으로 나가는 **끝**(유입·방류·처분·약품·바이오가스·다른 그림으로 이어짐). 글자·화살표 끝을 감싸는 작은 박스", "io_role 필수"],
        ["`junction_split`", "선 하나가 **둘로 갈라지는** 점(반송/폐기, 우회)", "—"],
        ["`junction_merge`", "선 둘이 **하나로 합쳐지는** 점(반송이 들어오는 곳, 약품이 들어가는 곳)", "—"],
        ["`instrument`", "센서·계측 태그(DO, pH, 유량계)", "—"],
    ], [3.5, 10, 3.5])
    D.table(["io_role", "뜻"], [["raw_influent", "원수 유입"], ["settled_influent", "1차 처리된 물이 들어옴"], ["external_waste_in", "분뇨·음폐수 등 외부 유입"], ["effluent", "방류"],
                               ["reclaimed_water_out", "재이용수"], ["solids_disposal", "슬러지·케이크·재 반출"], ["biogas_use", "바이오가스 이용"], ["off_gas_out", "배가스"],
                               ["chemical_source", "약품·연료·공기 투입(장치 없이 화살표만)"], ["overflow_bypass_out", "월류·우회 방류"], ["external_sidestream", "외부 반류수"], ["continuation", "다른 그림에서 오거나 다른 그림으로 감"]], [5, 11])
    D.tfig("G6_connection.png", "그림 6-1. 연결 요소 예. 약품 화살표(PAC·Alum·Perlite)는 장치가 아니다: 시작점 io_terminal(chemical_source) → 들어가는 점 junction_merge → 장치. 분기·합류 박스는 작으니 확대해서 그린다.", 16.5)
    D.pagebreak()
    D.h("안 치는 것", 2)
    D.p("범례, 제목·캡션, 로고, 번호 원, 표시 점, 선 자체, 흐름 이름 글자. 쉬운 버전에서는 화살촉과 글자도 치지 않는다(완전판 1~20번만 친다, 7부).")
    D.tfig("G8_not_annotated.png", "그림 6-2. 안 치는 것들.", 16.5)

    # ------------------------------------------------------------ 7. edges
    D.pagebreak()
    D.h("7부. 선 긋기 — 어디서 어디로")
    D.p("박스를 다 친 뒤, 흐름을 **출발 박스 → 도착 박스**로 잇습니다. 장치→장치를 바로 잇지 말고, 사이에 분기·합류 박스가 있으면 반드시 거칩니다. 물인지 슬러지인지는 고르지 않습니다(나중에 컴퓨터가 양쪽 장치를 보고 채웁니다).")
    D.step("7-1", "출발 박스 클릭 → Alt+R", "출발 박스를 클릭해서 선택한 뒤 키보드 **Alt+R**을 누른다(R만 누르면 사각형 도구가 켜진다). 연결 모드가 된다.",
           "U11_relation_r", check="마우스를 움직이면 출발 박스에서 선이 따라온다.")
    D.step("7-2", "도착 박스 클릭", "도착 박스를 클릭한다. Relations 탭에 '출발 → 도착' 한 줄이 생긴다.",
           "U12_relations_tab", check="방향이 맞다(출발 → 도착). 거꾸로 됐으면 그 줄을 지우고 다시.", notes=["선 하나에 관계 하나. 한 박스에서 두 군데로 가면 관계 두 개(갈라지는 점이 그려져 있으면 junction_split을 거친다)."])
    D.step("7-3", "라벨은 예외만", "보통은 라벨을 고르지 않는다. 점선이면 **style:dashed**, 화살촉이 없으면 **no_arrow**, 방향을 알 수 없으면 **direction_unknown**, '(Optional)'처럼 써 있으면 **optional**.",
           "U13_relation_label", check="실선 + 화살촉인 보통 선에는 라벨이 없다.")
    D.tfig("G9_lines.png", "그림 7-1. 선 종류. 종류(물·슬러지·공기)는 고르지 않는다. 점선·화살촉 없음·선택 사항만 라벨.", 16.5)
    D.note("흐름선 위에 펌프·밸브가 있으면 장치 → 펌프 → 장치로 두 번 잇는다. 반송(RAS·내부반송)도 똑같이 선이다. 열(Radiation, Heat)처럼 물질이 아닌 화살표는 긋지 않는다.", "warn")

    # ------------------------------------------------------------ 8. image attrs + submit
    D.pagebreak()
    D.h("8부. 그림 속성 적고 제출하기")
    D.step("8-1", "그림 전체 속성", "화면을 맨 아래로 내린다. 그림 한 장에 한 번만 고르는 항목이 있다.",
           "U14_image_attrs", check="diagram_style·language·n_panels 세 개가 채워져 있다(필수).")
    D.table(["항목", "고르는 법"], [
        ["diagram_style", "A_box 글자 상자형 / B_symbol 기호형 / C_pictorial 그림형 / D_simulator 시뮬레이터 화면 / E_page 페이지 전체 / hydraulic_profile 수리 종단면"],
        ["language", "en / ko / zh / ja / other / mixed"],
        ["n_panels", "독립된 도면 수. 보통 1. (a)(b)(c)처럼 나뉘어 있으면 그 수, 박스마다 graph_id로 g1·g2 구분"],
        ["process_configuration", "캡션·제목에 적힌 공정 이름 **원문 그대로**(예: A2O + MBR, 1단계 A2O(개량)·2단계 MLE). 없으면 비움"],
        ["annotator_note", "애매했던 점을 한 줄(예: '7번 박스가 농축인지 탈수인지 불확실'). 판정자가 모아서 본다"],
    ], [4, 12.5])
    D.step("8-2", "Submit", "오른쪽 아래 **Submit**(또는 Ctrl+Enter)을 누른다. 저장되고 다음 장이 열린다.",
           "U15_submit", check="작업 목록에서 방금 장에 완료 표시가 붙었다. Submit 전에 창을 닫으면 날아간다.",
           notes=["중간에 쉬려면 Submit까지 하고 쉰다. 다음 날 이어서 하면 된다.", "제출한 장을 고치려면 목록에서 다시 열어 수정하고 Update."])
    D.h("1~20번 완전판과 21~60번 쉬운 버전", 2)
    D.table(["", "21~60번 (쉬운 버전)", "1~20번 (완전판)"], [
        ["장치·구역 박스", "친다", "친다"], ["단자·분기·합류·계측", "친다", "친다"], ["화살촉(arrowhead)", "**안 친다**", "화살촉마다 작은 박스"],
        ["글자(text_label·stream_tag·stream_label)", "**안 친다**", "장치 이름·흐름 이름 글자마다 박스"], ["선 긋기", "방향만 (라벨은 예외만)", "같음"], ["그림 속성", "같음", "같음"],
    ], [5, 5.5, 5.5])
    D.tfig("S2_full.png", "그림 8-1. 완전판(1~20번)에서 추가로 치는 것: 글자 박스(파랑·보라)와 화살촉 박스(빨강 작은 네모). 쉬운 버전에서는 이것들이 없다.", 15)

    # ------------------------------------------------------------ 9. full example
    D.pagebreak()
    D.h("9부. 1번 그림을 처음부터 끝까지")
    D.p("파일럿 1번(EPA 우천 처리 계열)을 순서대로 해 보면 이렇게 됩니다.")
    D.tfig("S1_units.png", "그림 9-1. ① 장치 박스 8개. 'Preliminary Treatment'·'Biological Treatment'는 단계 이름뿐이라 generic + l1_hint. 펌프 기호도 친다.", 15)
    D.pagebreak()
    D.tfig("S2_lite.png", "그림 9-2. ② 연결 요소(쉬운 버전): 단자 1개(Backwash To Solids Processing → continuation), 분기 2개, 합류 2개.", 15)
    D.pagebreak()
    D.tfig("F5_example_edges.png", "그림 9-3. ④ 선 긋기: 본류 1→2→3→4→5, 우천 우회 1→분기→6→7→8→5, 역세척 점선 6→분기→2와 분기→단자(style:dashed + optional).", 15)
    D.p("③ 속성: 상자 글자형이니 visual_form=box, confidence=inferred_from_text (펌프 기호만 symbol·certain). ⑤ 그림 속성: A_box · en · 1.")

    # ------------------------------------------------------------ 10. practice answers
    D.pagebreak()
    D.h("10부. 연습 5장 — 정답 그림과 이유")
    D.p("연습 프로젝트(practice)의 5장입니다. 먼저 혼자 해 보고, 끝난 뒤에 이 쪽과 비교하세요. 박스 번호는 아래 표와 같고, 선은 글로 적었습니다. 정답이 하나뿐인 건 아닙니다. 다르게 했다면 '왜'를 메모해 두면 교육 때 같이 봅니다.")
    for i, cap in enumerate([
        "그림 10-1. 연습 1. 산업폐수라 모르는 장치가 많다. 필터·막·탱크·펌프처럼 범주가 분명하면 그 클래스, 정말 모르면 unknown + 글자.",
        "그림 10-2. 연습 2. 특허는 이름 대신 번호를 쓴다. 번호만 있는 상자는 generic + 번호. 흐름 이름 상자(GRAVITY FLOW 등)는 장치가 아니다.",
        "그림 10-3. 연습 3. 소각 계통은 목록에 거의 없다. unknown + 글자로 적어 두면 나중에 분류한다. 그림 밖으로 드나드는 끝은 전부 단자.",
        "그림 10-4. 연습 4. 한 장에 두 계열 + 슬러지 + 반류수가 다 있다. 규칙은 같다: 계열 둘 다, 약품은 선, 구역은 부모+자식, 범례는 안 침.",
        "그림 10-5. 연습 5. 단순하지만 슬래시 뒤 세부형과 분기·합류 박스를 빠뜨리기 쉽다.",
    ], 1):
        D.tfig(f"PR{i}.png", cap, 16.0 if i != 2 else 11.5)
        if i < 5:
            D.pagebreak()

    # ------------------------------------------------------------ 11. checklist
    D.pagebreak()
    D.h("11부. 제출 전 체크리스트 · 자주 틀리는 것 · 막혔을 때")
    D.h("제출 전 10초 점검", 2)
    for t in ["장치마다 박스가 있다 (나란한 것도 각각)", "박스마다 visual_form·confidence가 있다", "구역은 is_zone + 부모 박스 + parent_of",
              "들어오고 나가는 끝마다 io_terminal + io_role", "갈라지는 점·합쳐지는 점에 junction", "선이 다 그어졌다 (반송·우회·슬러지 라인 포함)",
              "generic·unknown에는 label_text가 있다", "그림 속성 3개가 채워졌다", "애매했던 것은 메모에 적었다", "1~20번이면 화살촉·글자까지"]:
        D.bullet("☐ " + t)
    D.h("자주 틀리는 것", 2)
    D.table(["이렇게 하기 쉽다", "이렇게 한다"], [
        ["약품 화살표에 장치 박스를 친다", "장치 아님. 시작점 io_terminal(chemical_source) + 들어가는 점 junction_merge"],
        ["장치 이름 글자까지 박스에 넣는다", "장치 모양만. 글자는 완전판에서 따로 text_label"],
        ["침전지를 전부 secondary로", "생물반응조 앞이면 primary"],
        ["소화조 앞 드럼을 dewatering으로", "소화조 앞 = thickener, 뒤 = dewatering"],
        ["살수여상을 biofilm_reactor까지만", "슬래시 뒤 /trickling_filter까지"],
        ["장치→장치를 바로 잇는다 (사이에 갈라짐이 있는데)", "junction을 거쳐 두 번 잇는다"],
        ["점선에 '슬러지'를 고르려 한다", "종류는 안 고른다. style:dashed만"],
        ["'×4'를 보고 박스 4개", "그려진 것만. 글자로만 적혀 있으면 1개"],
        ["모르는 장치를 짐작으로 aerobic_zone", "unknown_equipment + 글자. 짐작 금지"],
        ["Submit 안 하고 창을 닫는다", "장마다 Submit. 안 누르면 저장 안 됨"],
    ], [7.5, 9])
    D.h("막혔을 때", 2)
    D.bullet("**규칙에 없는 상황**: 가장 가까운 것으로 하고 annotator_note에 한 줄. 새 규칙을 혼자 만들지 않는다.")
    D.bullet("**장치가 뭔지 모르겠다**: 범주(필터·막·탱크·펌프)를 알면 그 클래스, 모르면 unknown + 글자. 생물반응조 종류를 짐작으로 정하지 않는다.")
    D.bullet("**그림이 너무 작다**: 확대해서 보이는 만큼. 전혀 안 보이면 메모하고 넘어간다.")
    D.bullet("**한 장에 그림이 둘**: n_panels=2, 박스마다 graph_id로 g1·g2.")
    D.bullet("**접속이 안 된다**: 판정자 노트북(서버)이 꺼져 있거나 잠든 것이다. 판정자에게 알린다. 주소는 바뀌지 않는다.")
    D.bullet("**실수로 뭔가 지웠다**: Ctrl+Z. 프로젝트 자체가 안 보이면 바로 판정자에게.")
    D.p()
    D.p("문의: 판정자(우태용). 작업 중 다른 어노테이터와는 상의하지 않습니다. 두 사람이 다르게 한 곳이 규칙을 고치는 재료가 됩니다.", 10, color=GREY)

    D.d.save(OUT)
    print("saved", OUT)


def to_pdf():
    """Word COM export; copies to an ASCII temp path first (COM dislikes the Korean folder name)."""
    import shutil, subprocess, tempfile
    tmp = Path(tempfile.mkdtemp(prefix="tut_"))
    src = tmp / OUT.name; shutil.copy2(OUT, src)
    pdf = src.with_suffix(".pdf")
    ps = f"""
$w = New-Object -ComObject Word.Application; $w.Visible = $false
$d = $w.Documents.Open('{src}', $false, $true)
$d.ExportAsFixedFormat('{pdf}', 17)
$d.Close($false); $w.Quit()
"""
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    shutil.copy2(pdf, OUT.with_suffix(".pdf"))
    print("saved", OUT.with_suffix(".pdf"))


if __name__ == "__main__":
    build()
    if "--pdf" in sys.argv:
        to_pdf()
