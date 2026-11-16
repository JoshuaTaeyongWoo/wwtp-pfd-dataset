# WWTP 공정도 어노테이션 가이드라인 v1 (파일럿용)

체계: `annotation_taxonomy_plan.md` v1.1 (동결 태그 `taxonomy-v1.1`, 커밋 03f3d10). 기계용 정의: `annotation/classes.yaml`.
이 문서는 어노테이터가 작업 중 옆에 두고 보는 **실무 규칙서**다. 왜 그런 규칙인지는 설계안과 근거 원장을 본다.

---

## 0. 작업 개요 (60장 파일럿)

- 이미지: `data/pilot/images/pilot_01 … pilot_60`. 하수처리장 공정도(논문·특허·설계 매뉴얼·위키·지자체 자료).
- 두 사람이 **서로 보지 않고** 같은 60장을 라벨링한다. 끝나면 판정자가 불일치를 정리한다. 틀리는 것보다 **규칙대로 일관되게** 하는 것이 중요하다. 애매하면 "annotator_note"에 적고 규칙대로 선택한다.
- 한 장당 할 일: ① 장치·구역 박스 ② 연결 요소 박스 ③ 박스마다 T1 속성 ④ 흐름 엣지(관계) ⑤ 이미지 속성. T2 속성은 **그림·캡션에 글자로 적혀 있을 때만**, T3는 하지 않는다.
- 예상 시간: 장당 8~15분(파일럿은 익숙해지는 단계라 더 걸려도 된다). 교육 2시간 + 연습 5장 후 시작.

## 1. 무엇에 박스를 치는가

**친다** — 아래 전부, 빠짐없이(부분 라벨링 금지):
1. 단위공정 장치 하나하나(탱크·침전지·여과기·소화조·펌프장 …) → L2 클래스.
2. 한 탱크 안의 혐기·무산소·호기 **구역** → 각각 `*_zone` 박스 + `is_zone` 체크 + 부모 탱크와 `parent_of` 관계(§5).
3. 연결 요소: 화살촉, 텍스트 라벨, 스트림 태그, 스트림 이름, 유입·유출 단자, 분기점, 합류점, 계측 기호.
4. 그 외 장치 → `unknown_equipment` + `label_text`.

**치지 않는다**: 흐름선 자체(엣지로만 기록), 캡션 문장, 범례(legend) 상자, 표, 그림 번호, 저자 로고, 축척.

## 2. 박스 치는 법

- 장치 윤곽을 **꼭 맞게**. 장치 이름이 박스 안에 쓰여 있으면 장치 박스는 그대로 두고 이름에 `text_label` 박스를 **따로** 친다.
- 겹침: 구역 박스는 부모 탱크 박스 안에 들어간다. 그 밖에는 겹치지 않게.
- 점(point) 요소: `arrowhead`는 화살촉만 꼭 맞게. `junction_split/merge`는 선이 갈라지는/만나는 지점에 **한 변 12 px 이상(이미지 짧은 변의 2 %)** 정사각형. 분배조·혼합조가 구조물로 그려졌으면 그 구조물을 감싼다.
- `io_terminal`: 플랜트 경계의 화살표 끝 + 붙은 글자("Influent", "방류", 약품명)를 함께. 글자가 없으면 화살표 끝 정사각형.
- 같은 장치가 병렬로 N개 그려졌으면 **N개 모두** 친다("×4"라고만 쓰였으면 1개 + `n_parallel_lanes=4`).
- SBR을 상(phase)마다 여러 패널로 그렸으면 패널마다 1개 + `panel_phase`.

## 3. 클래스 고르기 — 자주 쓰는 것부터

| 보이는 것 | 클래스 | 메모 |
|---|---|---|
| 공기방울·산기관·표면포기기가 있는 생물반응 탱크 | `aerobic_zone` | 포기조·폭기조·oxic·aeration tank 전부. 산화구는 한 박스 + `is_loop_reactor` |
| 교반기만 있고 질산염 반송(a) 또는 RAS가 들어오는 탱크 | `anoxic_zone` | |
| 교반기만, 유입수를 **가장 먼저** 받고 그 뒤에 또 교반 구역 | `anaerobic_zone` | 글자 없으면 §4 판별표 |
| 생물반응조 뒤 원뿔 바닥 침전지, 하부에서 반송(RAS) | `secondary_clarifier` | 살수여상 뒤 humus tank 포함 |
| 생물반응조 앞 침전지, 슬러지가 농축·소화로만 감 | `primary_clarifier` | |
| 막 카세트가 혼합액을 받고 슬러지를 반응조로 돌려보냄 | `mbr_unit` | 처리수를 받는 막은 `membrane_unit` |
| 한 탱크에서 채움/반응/침전/배출 | `sbr_tank` | |
| 여재·담체·디스크·탑 + 생물막 | `biofilm_reactor/…` | **L3 필수**: 살수여상 trickling_filter / 회전원판 rbc / 침지여재+공기(BAF, 접촉산화, 탈질여과) submerged_biofilter / 담체 MBBR·IFAS mbbr_ifas / 유동상 fluidized_expanded_bed / MABR mabr |
| 상향류·GLSS·바이오가스선 있는 폐수 반응기 | `anaerobic_wastewater_reactor/…` | **L3 필수**: uasb_egsb_ic / anaerobic_filter / anaerobic_contact / anaerobic_cstr / abr / anaerobic_mbr |
| 슬러지가 들어가는 달걀·돔형 탱크 | `digester` | 폐수가 들어가면 위 클래스 |
| 슬러지 라인의 작은 원뿔 탱크(상징수 반류) | `thickener` | 기포·DAF·"부상"이면 `flotation_unit` |
| 슬러지 라인의 원심·벨트·프레스, 산물이 케이크 | `dewatering_unit` | 소화조 **앞** 벨트·드럼은 `thickener` |
| 모래·디스크·섬유 여과(3차), 활성탄 | `filtration_unit` | 공기선·탄소원선 있으면 생물막 |
| UV·염소 접촉조·오존·탈염소 | `disinfection_unit` | |
| 반류수(탈수여액·상징수)만 받는 생물 반응기 | `sidestream_reactor` | 본류도 받으면 `*_zone` |
| 연못·라군·인공습지 | `pond_lagoon_wetland` | |
| 응집·교반 **탱크**가 그려짐 | `chemical_treatment_unit` | 약품 화살표만 있으면 장치 아님(§5) |
| 스크린 / 침사지 / 유량조정조 / 펌프장(수조+펌프 여러 대) | `screen` / `grit_chamber` / `equalization_tank` / `pump_station` | |
| 단독 펌프 / 송풍기 / 저류탱크 / 밸브 / 산기·교반 기호 | `pump` / `blower` / `storage_tank` / `valve` / `aerator_mixer_symbol` | |
| 글자 없음·번호뿐인 공정 박스 | `process_unit_generic` | 글자로 종류를 알 수 있으면 **그 클래스** + `visual_form=box` |
| 그 외 모든 장치(후포기, 탈취, 열교환기, 협잡물 세척기 …) | `unknown_equipment` | `label_text` 필수 |

**연결 요소**: `arrowhead`(화살촉) · `text_label`(장치명·설계치) · `stream_tag`(숫자·ID: 유량·농도·①) · `stream_label`(선 옆 글자: RAS, WAS, a, reject water) · `io_terminal` · `junction_split` · `junction_merge` · `instrument`(DO, pH, F, L 등 센서·제어 태그).

## 4. 판별 규칙 (설계안 §4.5 요약; 번호 동일)

1. **활성슬러지 열의 구역**: 글자(혐기/무산소/호기, anaerobic/anoxic/aerobic)가 있으면 그대로. 없으면 **호기조 앞 교반 구역 수 × 반송**으로:
   - 교반 구역 0 → 전부 `aerobic_zone`
   - 1개, a 반송 또는 RAS가 들어옴 → `anoxic_zone` (MLE)
   - 1개, 유입수만 → `anaerobic_zone` (A/O)
   - 2개, 1번째 유입수(+RAS)·2번째 a → 혐기, 무산소 (A2O)
   - 2개, 2번째에 RAS·a, 2→1 반송 → 혐기, 무산소 (UCT)
   - 3개, 1번째 RAS만 → 무산소(underflow_anoxic), 혐기, 무산소 (JHB)
   - 호기조 **뒤** 교반 구역 → `anoxic_zone(post_anoxic)`; 마지막 작은 포기 구역 → `aerobic_zone(reaeration)`
   - 그래도 모르면 `process_unit_generic` + `is_zone` + `confidence=inferred_from_context`
2. 여재 + 공기선 → `submerged_biofilter(aerobic)`; 여재 + 탄소원선 → `submerged_biofilter(anoxic)`; 둘 다 없음 → `filtration_unit`.
3. 탱크 전체가 담체 → `mbbr_ifas` 한 박스; 담체 케이지·MABR 카세트가 일부에만 → 포기조 박스 + 자식 생물막 박스.
4. 막이 혼합액을 받고 슬러지를 돌려보내면 `mbr_unit`, 처리수를 받으면 `membrane_unit`.
5. 슬러지 라인 장치: 소화조 **앞** → `thickener`, **뒤** 또는 케이크 산출 → `dewatering_unit`.
6. **약품은 엣지**: 공급원 끝 `io_terminal(chemical_source)` → 단위로 들어가는 지점 `junction_merge(chemical_dosing_point)`; 엣지는 medium=chemical. 응집·교반 탱크가 그려졌을 때만 `chemical_treatment_unit`.
7. SBR 패널마다 1단위; 교대 운전 쌍은 둘 다 `aerobic_zone` + `operation_mode=alternating`.
8. WAS 화살표는 어디서든 나올 수 있다. 출처를 짐작하지 말고 그려진 대로.
9. wet well + 펌프 여러 대 = `pump_station` 1개; 단독 펌프 = `pump`.
10. UASB·IC 한 상자는 한 박스(`multi_unit`은 나중에 자동).
11. 예비 클래스 장치(입상슬러지, 열가수분해, 스트루바이트, 1차 여과, 오존·활성탄, 하이드로사이클론, 탈취)는 새 이름을 만들지 말고 §3의 대응 클래스 + `label_text` 원문.
12. 캡션·제목의 공정 이름("A2O + MBR", "MLE")은 이미지 속성 `process_configuration`에.
13. 상자 안 상자(유입펌프장 안 스크린·침사지, 포기조 안 카세트, 반응조 안 침지막): 바깥 = 부모, 안쪽 = 자식(`parent_of`). 자식이 부모와 거의 같은 크기면 자식을 만들지 않는다.
14. 1차/2차 침전지·조정조/저류조는 **위치**로: 생물반응조 앞 = 1차, 뒤 = 2차; RAS 선이 있으면 2차. 유입 쪽에서 유량을 고르면 조정조, 담아만 두면 저류탱크.
15. 박스형 도면도 의미 클래스를 단다(`visual_form=box`, `confidence=inferred_from_text`). generic은 글자 없음·번호뿐일 때만.
16. 부상 농축 = `flotation_unit(function=thickening)`; `thickener`는 중력·기계식만.
17. P-stripper: RAS를 받으면 `anaerobic_zone(stripper)`, 반류수를 받으면 `sidestream_reactor`.
18. 선에 붙은 글자: 문자면 `stream_label`, 숫자·ID면 `stream_tag`, 섞였으면 `stream_label` 하나 + tag_kind.
19. `io_terminal` 범위: 화살표 끝 + 글자.
20. 반류수 반응기: 유일한 공급이 탈수여액·상징수면 `sidestream_reactor`; 본류도 받으면 `*_zone` + 합류점 `sidestream_return`.
21. 발효조: 발효액이 본류 혐기·무산소조로 가면 `fermenter`; 메탄 소화조로 가면 `digester(acid_phase)`.
22. 산화구·Carrousel·Orbal: 수로 전체 한 박스 `aerobic_zone(is_loop_reactor)`; 포기기 위치로 구간이 구분돼 있으면 구간마다 자식 구역.

## 5. 엣지(흐름) 기록 — Label Studio 관계

- 출발 박스 선택 → `r` → 도착 박스 클릭 → 관계 라벨 `medium|direction_confidence` 선택.
  - medium: liquid(처리수·유입수) / mixed_liquor(반응조 사이) / sludge / gas(바이오가스·배기) / air(송풍) / chemical / solid(케이크·협잡물) / signal(점선 신호선)
  - direction_confidence: `arrowhead` = 화살촉이 그려짐, `inferred` = 선은 있지만 방향 표시 없음(공정 순서로 추정), `ambiguous` = 방향을 알 수 없음
- 엣지 끝점은 **가장 작은 단위**(구역이 있으면 구역, 없으면 탱크).
- 갈라지거나 합쳐지는 곳은 반드시 `junction_split/merge` 박스를 거친다(장치→장치 직결 금지).
- 인접 구역 사이(혐기→무산소→호기)는 선이 없어도 `mixed_liquor|inferred` 엣지를 넣는다.
- 부모–자식: 탱크 박스 → 구역 박스로 `parent_of`.
- 스트림 이름·태그·화살촉을 어느 엣지의 근거로 쓸지는 선택(`evidence_for`: 라벨 박스 → 도착 장치). 파일럿에서는 생략 가능.

## 6. 이미지 속성 (장당 1회)

- `diagram_style`: A_box(사각형+글자) / B_symbol(기호형) / C_pictorial(3D·아이콘) / D_simulator(소프트웨어 화면) / E_page(페이지 통째) / hydraulic_profile
- `language`: 라벨 글자 언어. `n_panels`: 독립 도면 수(둘 이상이면 박스마다 graph_id를 `label_text` 앞에 "[g2]"로 표시).
- `process_configuration`: 캡션·제목에 공정 이름이 있으면 원문 그대로.

## 7. 자주 틀리는 것

- 포기조를 "aeration tank"라고 써 있다고 `storage_tank`로 치지 않는다 → `aerobic_zone`.
- 약품 화살표에 장치 박스를 만들지 않는다(규칙 6).
- 2차 침전지의 RAS 선을 빼먹지 않는다(엣지 sludge|arrowhead, 스트림 이름 `ras_s`).
- 구역 박스에 `is_zone`을 빠뜨리지 않는다; 부모가 그려지지 않았으면 `parent_of` 없이 구역만 친다.
- 특허 도면의 번호(412, 480)는 `label_text`에 그대로 적고 클래스는 `process_unit_generic`.
- 보조 텍스트(설계치, 유량)는 전부 박스를 친다 — OCR 평가에 쓴다.

## 8. 모르겠을 때

규칙대로 가장 가까운 것을 고르고 `annotator_note`에 한 줄 적는다. 판정자가 모아서 가이드라인 v2에 반영한다. 서로 상의하지 않는다(일치도를 재야 하므로).
