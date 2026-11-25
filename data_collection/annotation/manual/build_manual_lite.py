"""
build_manual_lite.py — short annotator manual for the PILOT-LITE protocol (v1.1b) + one-page cheat sheet.

Outputs: WWTP_annotation_manual_v1_lite.docx and WWTP_cheat_sheet.docx (PDFs via Word COM).
Reuses the Doc helper and figures of build_manual.py.
"""
from __future__ import annotations

from docx.enum.section import WD_ORIENT
from docx.shared import Cm, Pt, RGBColor

from build_manual import Doc, HERE, ACCENT, GREY, set_font

OUT = HERE / "WWTP_annotation_manual_v1_lite.docx"
OUT_CARD = HERE / "WWTP_cheat_sheet.docx"


def build_lite():
    D = Doc()
    D.p()
    D.p("하수처리장 공정도 어노테이션 매뉴얼 — 쉬운 버전", 22, True, ACCENT, "center")
    D.p("파일럿 절차 v1.1b (2026-11-18) · 클래스 체계 v1.1a · Label Studio pilot_A / pilot_B 60장", 11, color=GREY, align="center")
    D.p()
    D.note("이 버전은 60장 파일럿용입니다. 1~20번 그림은 **완전판**(화살촉·글자 박스까지), 21~60번은 **쉬운 버전**(장치·구역·단자·분기·합류·계측만)입니다. 흐름선의 '물/슬러지' 종류는 사람이 고르지 않고 나중에 컴퓨터가 양쪽 장치를 보고 채웁니다. 애매하면 규칙에 가장 가까운 것을 고르고 annotator_note에 한 줄 적습니다. 옆 사람과 상의하지 않습니다.")

    D.h("1. 한 장에서 하는 일 (4단계)")
    D.fig("F1_workflow.png", "그림 1. 쉬운 버전에서는 ②가 많이 줄고 ④는 선만 긋는다.", 17)
    D.table(["단계", "할 일", "21~60번(쉬운 버전)", "1~20번(완전판)"], [
        ["① 장치·구역 박스", "장치마다 박스 + 이름. 한 탱크 안의 혐기/무산소/호기는 구역마다 박스", "함", "함"],
        ["② 연결 요소 박스", "유입·유출 끝(`io_terminal`), 갈라짐·합침 지점(`junction_*`), 센서 태그(`instrument`)", "함", "함"],
        ["② 연결 요소 박스", "화살촉(`arrowhead`), 글자(`text_label`·`stream_tag`·`stream_label`)", "**안 함**", "함"],
        ["③ 박스 속성", "visual_form · confidence · (구역) is_zone · (generic·unknown) l1_hint + 글자", "함", "함"],
        ["④ 흐름 연결", "출발 박스 → Alt+R → 도착 박스. 라벨은 예외만", "함", "함"],
        ["⑤ 그림 속성", "diagram_style · language · n_panels (+ 공정 이름)", "함", "함"],
    ], [3.0, 7.0, 3.5, 3.5], size=9.5)

    D.h("2. 화면과 단축키")
    D.fig("F2_ui_callouts.png", "그림 2. 라벨 버튼(②)은 처리 단계별로 줄을 나눠 그림 위에 있다. 박스를 고르면 그 박스의 속성 칸이 그림 아래에 펼쳐지고 ⑤에 요약이 보인다.", 16)
    D.table(["키", "하는 일"], [["숫자 1~0", "자주 쓰는 장치 10개"], ["a · x z · i j l", "pump · generic/unknown · 단자/분기/합류"], ["드래그", "박스 그리기"], ["Alt+R", "연결 만들기 (출발 선택 → Alt+R → 도착 클릭)"],
                                ["Backspace / Ctrl+Z", "삭제 / 되돌리기"], ["마우스 휠", "확대 (작은 요소는 확대해서)"], ["Ctrl+Enter", "제출하고 다음 장"]], [4, 12])

    D.h("3. 이름(클래스) 고르기")
    D.fig("F3_label_bar.png", "그림 3. 라벨 버튼 전체. 생물막·혐기성 반응기는 슬래시 뒤 세부형까지.", 15)
    D.table(["보이는 것", "클래스"], [
        ["공기방울·산기관이 있는 생물 탱크 (포기조·폭기조·산화구)", "`aerobic_zone`"],
        ["교반기만, 질산염 반송(a)이나 RAS가 들어옴", "`anoxic_zone`"],
        ["교반기만, 유입수를 가장 먼저 받고 뒤에 또 교반 구역", "`anaerobic_zone`"],
        ["생물반응조 **뒤** 침전지(반송선 있음) / **앞** 침전지", "`secondary_clarifier` / `primary_clarifier`"],
        ["혼합액을 받는 막 / 처리수를 받는 막", "`mbr_unit` / `membrane_unit`"],
        ["여재·담체·디스크·탑 생물막", "`biofilm_reactor/…` (세부형 필수)"],
        ["상향류·가스 돔 폐수 반응기 (UASB 등)", "`anaerobic_wastewater_reactor/…` (세부형 필수)"],
        ["슬러지가 들어가는 달걀·돔형 탱크 / 슬러지 라인 원뿔 탱크 / 원심·벨트·프레스", "`digester` / `thickener` / `dewatering_unit`"],
        ["여과·활성탄 / UV·염소·오존 / 반류수만 받는 반응기 / 연못·습지", "`filtration_unit` / `disinfection_unit` / `sidestream_reactor` / `pond_lagoon_wetland`"],
        ["스크린 / 침사지 / 유량조정조 / 펌프장(수조+펌프들) / 응집 탱크 / 부상조(DAF)", "`screen` / `grit_chamber` / `equalization_tank` / `pump_station` / `chemical_treatment_unit` / `flotation_unit`"],
        ["단독 펌프 / 송풍기 / 저류탱크 / 밸브 / 산기·교반 기호 / 가스홀더·CHP / 발효조 / 건조·소각", "`pump` / `blower` / `storage_tank` / `valve` / `aerator_mixer_symbol` / `biogas_unit` / `fermenter` / `drying_incineration_unit`"],
        ["글자 없음·번호뿐, 또는 글자가 단계 이름(Biological Treatment)", "`process_unit_generic` + l1_hint + 글자"],
        ["그 외 장치 (후포기, 탈취, 열교환기 …)", "`unknown_equipment` + l1_hint + 글자"],
    ], [9.5, 7.5], size=9.3)
    D.fig("F7_visual_form.png", "그림 4. visual_form: 글자로만 알면 box, 모양이 말해 주면 symbol, 3D·아이콘이면 pictorial.", 16)
    D.note("**원·네모에 글자**로 이름이 쓰였으면 모양이 원이라도 box입니다. 1차/2차 침전지는 모양이 같으니 **위치**로(생물반응조 앞 = 1차, 뒤 = 2차, RAS 선 있으면 2차). 농축조/탈수기는 **소화조 기준** 앞/뒤로.")

    D.h("4. 구역(zone)")
    D.fig("F9_zones.png", "그림 5. 구역마다 박스 + is_zone, 탱크 박스 → 구역으로 parent_of.", 16.5)
    D.fig("F6_zone_decision.png", "그림 6. 구역 이름이 없을 때: 호기조 앞 교반 구역 수와 반송 위치로 정한다. 모르면 generic + is_zone + l1_hint=secondary.", 16.5)

    D.h("5. 연결 요소 (쉬운 버전에서 하는 것)")
    D.table(["클래스", "무엇", "속성"], [
        ["`io_terminal`", "플랜트 밖에서 들어오고 나가는 끝(화살표 끝 + 글자). 다른 그림으로 이어지면 continuation", "io_role 필수"],
        ["`junction_split` / `junction_merge`", "선이 갈라지는 점 / 합쳐지는 점(약품이 들어가는 지점, 반류수가 돌아오는 지점). 분배조가 상자로 그려졌으면 상자 전체", "없음"],
        ["`instrument`", "센서·제어 태그 (DO, pH, F, L)", "없음(파일럿)"],
    ], [4.2, 9.3, 3.5], size=9.3)
    D.p("완전판(1~20번)에서만 추가: `arrowhead`(화살촉마다 꼭 맞게), `text_label`(장치명·설명 글자), `stream_tag`(숫자·ID), `stream_label`(선 옆 글자 RAS·WAS 등). 글자 박스의 label_text는 원문 그대로.", 10)
    D.fig("F8_connection_elements.png", "그림 7. 연결 요소가 들어가는 자리(완전판 기준).", 16)
    D.note("약품은 장치가 아니라 선입니다: 시작점 `io_terminal(chemical_source)` → 들어가는 지점 `junction_merge` → 연결. 응집 **탱크**가 그려졌을 때만 `chemical_treatment_unit`.")

    D.h("6. 흐름 연결(엣지): 선만 긋는다")
    D.num("출발 장치 박스 클릭 → `Alt+R` → 도착 장치 박스 클릭. 화살표 방향이 흐름 방향.")
    D.num("기본은 라벨 없음(= 보통의 흐름). **예외일 때만** Relations 탭에서 라벨: `no_arrow`(선은 있는데 화살촉이 없음), `direction_unknown`(방향을 모름), `style:dashed`(점선), `optional`('(Optional)'·대안 경로), `parent_of`(탱크 → 구역).")
    D.num("갈라지거나 합쳐지는 곳은 반드시 `junction_*` 박스를 거칩니다(장치 → 장치로 두 갈래 직결 금지).")
    D.num("인접 구역 사이(혐기 → 무산소 → 호기)는 선이 없어도 연결하고 `no_arrow`.")
    D.p("물인지 슬러지인지는 고르지 않습니다. 컴퓨터가 양쪽 장치로 채웁니다(침전지 → 반응조 = 반송 슬러지, 반응조 → 침전지 = 혼합액 …). 판정자가 1~20번에서 확인합니다.", 10, color=GREY)
    D.fig("F5_example_edges.png", "그림 8. 파일럿 1번 그림의 연결. 쉬운 버전에서는 선만 긋고 주황 점선에만 style:dashed + optional.", 16)

    D.h("7. 속성 (필수 5개 + 그림 속성)")
    D.table(["항목", "어떻게"], [
        ["`visual_form`", "box / symbol / pictorial / simulator_icon / section_view"],
        ["`confidence`", "certain(모양으로 확실) / inferred_from_text(글자 읽고) / inferred_from_context(문맥 추정)"],
        ["`is_zone`", "구역 박스만 체크"],
        ["`l1_hint`", "generic·unknown 박스만: preliminary / primary / secondary / tertiary / sludge / sidestream / unknown"],
        ["`label_text`", "generic·unknown 박스는 **필수**(원문 그대로). 다른 박스는 선택"],
        ["`io_role`", "io_terminal만: raw_influent / effluent / chemical_source / solids_disposal / continuation …"],
        ["그림 속성", "diagram_style(A_box…E_page) · language · n_panels · process_configuration(캡션의 공정 이름, 있을 때만)"],
    ], [4, 13], size=9.5)
    D.p("그 밖의 선택 칸(산기 방식, 운전 방식 등)은 이 버전 화면에 없습니다. 본 작업에서 다시 켭니다.", 10, color=GREY)

    D.h("8. 예제: 1번 그림")
    D.fig("F4_example_boxes.png", "그림 9. 1번 그림(완전판)의 박스. 쉬운 버전이라면 파란 글자 박스·빨간 화살촉 박스는 생략하고 장치 8개 + 주황 단자 + 빨간 분기·합류만.", 16)
    D.p("장치 8개: ① Preliminary Treatment → `process_unit_generic`(l1_hint=preliminary) ② Primary Clarifier → `primary_clarifier` ③ Biological Treatment → `process_unit_generic`(l1_hint=secondary) ④ Secondary Clarifier → `secondary_clarifier` ⑤ Disinfection → `disinfection_unit` ⑥ FlexFilter → `filtration_unit` ⑦ 펌프 기호 → `pump` ⑧ Bio-FlexFilter → `biofilm_reactor/submerged_biofilter`. 전부 visual_form=box(⑦만 symbol), confidence=inferred_from_text(⑦ certain). 단자 1개(To Solids Processing → continuation), 분기 2 + 합침 2. 연결은 그림 8. 그림 속성 A_box / en / 1.", 10)

    D.h("9. 자주 틀리는 것")
    for t in ["\"aeration tank\" 글자를 보고 `storage_tank`로 치지 않는다 → `aerobic_zone`.",
              "약품 화살표에 장치 박스를 만들지 않는다.",
              "2차 침전지 → 반응조로 돌아가는 반송선을 빼먹지 않는다.",
              "구역 박스에 `is_zone`, generic·unknown 박스에 `l1_hint`를 빠뜨리지 않는다.",
              "갈라짐·합침에 `junction_*` 박스를 빠뜨리고 장치끼리 직결하지 않는다.",
              "1~20번은 화살촉·글자 박스까지, 21~60번은 생략. 번호를 확인한다."]:
        D.bullet(t)
    D.note("끝나면 Projects 화면의 Submitted annotations가 60. 판정자가 Export → JSON으로 내보내 일치도를 계산하고, 매체 자동 채움 정확도를 1~20번으로 확인합니다.")
    D.d.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build_lite()
