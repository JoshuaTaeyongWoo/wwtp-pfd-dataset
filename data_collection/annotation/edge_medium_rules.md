# 엣지 매체·역할 자동 채움 규칙 (pilot protocol v1.1b, 2026-11-18)

쉬운 버전 파일럿에서 어노테이터는 **방향만** 긋는다(출발 → 도착, 예외 라벨 `no_arrow`·`direction_unknown`·`style:dashed`·`optional`·`parent_of`).
`medium`과 `stream_role`은 `s19_infer_edge_medium.py`가 아래 규칙으로 채우고, 못 정하면 `ambiguous`로 남겨 판정자가 본다.
완전판 20장(1~20번)에서 판정자가 직접 단 값과 비교해 규칙 정확도를 보고한다(논문: 사람 상한 지표에서 매체는 제외, 규칙 정확도는 별도 보고).

규칙은 위에서 아래로 처음 맞는 것을 쓴다. `src`/`dst`는 엣지 양 끝 박스의 L2 클래스(L3는 L2로 접음). `junction_*`·`pump`·`valve`·`storage_tank`는 **통과 노드**: 매체는 상류 엣지에서 이어받고, 상류가 없으면 하류에서 거꾸로 받는다.

| # | src | dst | medium | stream_role | 근거·메모 |
|---|---|---|---|---|---|
| 1 | `io_terminal(chemical_source)` | 아무것 | chemical | chemical_dose | 약품 주입은 엣지 [B-08]; 탄소원(메탄올·아세트산 글자) → carbon_source |
| 2 | `blower` | 아무것 | air | air_supply | 순산소 글자면 oxygen |
| 3 | 아무것 | `blower` | air | air_supply | 공기 흡입선 |
| 4 | `digester` / `anaerobic_wastewater_reactor` | `biogas_unit` / `io_terminal(biogas_use)` | gas | biogas | |
| 5 | `digester` | `io_terminal(off_gas_out)` / `unknown_equipment`(탈취) | gas | off_gas | |
| 6 | `secondary_clarifier` | `biofilm_reactor/trickling_filter` | liquid | effluent_recirculation_qr | **살수여상 순환은 처리수**이지 슬러지가 아님 [B-20] |
| 7 | `secondary_clarifier` / `mbr_unit` | `aerobic_zone` / `anoxic_zone` / `anaerobic_zone` / `sbr_tank` / `biofilm_reactor` / `process_unit_generic(l1_hint=secondary)` | sludge | ras_s | 반송 슬러지 [B-20, B-21] |
| 8 | `secondary_clarifier` / `mbr_unit` / `aerobic_zone` / `anoxic_zone` / `anaerobic_zone` / `sbr_tank` | `thickener` / `digester` / `dewatering_unit` / `flotation_unit` / `fermenter` / `io_terminal(solids_disposal)` / `process_unit_generic(l1_hint=sludge)` | sludge | was | 잉여 슬러지; 출처 가정 금지(규칙 8) |
| 9 | `primary_clarifier` | `thickener` / `digester` / `fermenter` / `dewatering_unit` / `process_unit_generic(l1_hint=sludge)` | sludge | primary_sludge | |
| 10 | `primary_clarifier` | `secondary_clarifier` / 생물 단계 / `process_unit_generic(l1_hint=secondary)` | liquid | settled_influent | |
| 11 | `aerobic_zone` | `anoxic_zone` / `anaerobic_zone` | mixed_liquor | internal_recycle_a | 질산염 내부 반송 |
| 12 | `anoxic_zone` | `anaerobic_zone` | mixed_liquor | r_recycle | UCT r 반송 |
| 13 | 생물 구역(`*_zone`, `sbr_tank`) | 생물 구역 / `secondary_clarifier` / `mbr_unit` / `biofilm_reactor` | mixed_liquor | mixed_liquor | 순방향 혼합액 |
| 14 | `fermenter` | `anaerobic_zone` / `anoxic_zone` / 생물 구역 | liquid | fermentate | **발효액은 액체** [B-14] |
| 15 | `fermenter` | `digester` | sludge | primary_sludge | 발효 후 슬러지 |
| 16 | `thickener` / `flotation_unit(function=thickening)` | `digester` / `dewatering_unit` / `fermenter` / `storage_tank` | sludge | thickened_sludge | |
| 17 | `digester` | `dewatering_unit` / `thickener` / `storage_tank` / `drying_incineration_unit` | sludge | digested_sludge | |
| 18 | `dewatering_unit` | `io_terminal(solids_disposal)` / `drying_incineration_unit` / `storage_tank(sludge)` | solid | dewatered_cake | **탈수기 두 갈래 중 고형물** |
| 19 | `dewatering_unit` / `thickener` / `digester` / `sidestream_reactor` | 본류 단위(전처리·1차·생물 구역·`equalization_tank`) / `sidestream_reactor` / `junction_merge` | liquid | sidestream_return | **탈수여액·상징수 반류** (탈수기 두 갈래 중 액체) |
| 20 | `drying_incineration_unit` | `io_terminal(solids_disposal)` | solid | dewatered_cake | 재·퇴비 |
| 21 | `screen` / `grit_chamber` | `io_terminal(solids_disposal)` / `unknown_equipment` | solid | screenings_grit | |
| 22 | `filtration_unit` / `membrane_unit` / `biofilm_reactor` | 상류 단위 / `equalization_tank` / `junction_merge` | liquid | backwash_return | 역세척 (점선·"backwash" 글자) |
| 23 | `io_terminal(external_waste_in)` | `digester` / `anaerobic_wastewater_reactor` | sludge | co_substrate | 분뇨·음식물 연계 |
| 24 | `io_terminal(raw_influent)` | 아무것 | liquid | influent | |
| 25 | 아무것 | `io_terminal(effluent)` / `io_terminal(reclaimed_water_out)` | liquid | effluent / reclaimed_water | |
| 26 | 아무것 | `io_terminal(overflow_bypass_out)` | liquid | overflow | |
| 27 | `instrument` ↔ 아무것 | — | signal | signal | 점선 신호선 |
| 28 | 그 밖에 src·dst 둘 다 본류 단위 | — | liquid | mixed_liquor(생물 구역 사이) 또는 liquid·unknown_role | 기본값 |
| 29 | 그 밖에 src 또는 dst가 슬러지 라인(`thickener`·`digester`·`dewatering_unit`·`fermenter`·`l1_hint=sludge`) | — | sludge | unknown_role | |
| 30 | 그 밖에 | — | **ambiguous** | — | 판정자 확인 (generic↔generic, unknown_equipment 관련, 스컴 등) |

관계 라벨 반영: `no_arrow` → `direction_confidence=inferred`; `direction_unknown` → `ambiguous`; 라벨 없음 → `arrowhead`; `style:dashed` → `line_style=dashed`; `optional` → `optional=true`; `parent_of`는 엣지가 아니라 `parent_id`로 기록.
통과 노드 체인(junction → pump → junction …)은 상류 매체를 그대로 잇되, `junction_split` 뒤 가지는 가지마다 도착 노드로 규칙을 다시 적용한다(예: 침전지 하부 분기 → 반응조 = ras_s, → 농축조 = was).

| 31 | 분기 앞 / 합류 뒤 줄기 엣지 | — | 가지들이 공유하는 매체 | split_or_merge_trunk | 2차 패스: 모든 가지의 매체가 같을 때만; 다르면 ambiguous |

2026-11-19 예행연습(s21 dry run)에서 추가 — 규칙 28보다 먼저 검사:

| 32 | `screen`·`grit_chamber`·`equalization_tank`·`pump_station` | 본류 단위 | liquid | influent | 전처리 뒤 유입수 (예: 스크린 → 1차 침전지) |
| 33 | `secondary_clarifier`·`mbr_unit` | `filtration_unit`·`membrane_unit`·`disinfection_unit`·`chemical_treatment_unit` | liquid | effluent | 2차 처리수 → 3차 처리 |
