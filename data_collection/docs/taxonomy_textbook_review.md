# 어노테이션 클래스 체계 v0 — 교과서 기반 도메인 검토 (2026-11-16)

검토 대상: `annotation_taxonomy_plan.md` v0 (L1 7단계, L2 28 클래스, 연결 7 클래스, 속성 visual_form / is_zone / stream_type).
검토 자료 (`WWTP_RL/Ref/textbook`):
- **[IWA]** Henze, van Loosdrecht, Ekama, Brdjanovic (eds.) 2008, *Biological Wastewater Treatment: Principles, Modelling and Design*, IWA. 517쪽. (페이지 = 인쇄 쪽수)
- **[Olsson]** Olsson & Newell 1999, *Wastewater Treatment Systems: Modelling, Diagnosis and Control*, IWA. 741쪽. (페이지 = PDF 쪽수)
- **[GMP]** Rieger et al. 2012, *Guidelines for Using Activated Sludge Models*, IWA STR 22. 303쪽. (페이지 = PDF 쪽수)
- **[ASM]** Henze et al., *Activated Sludge Models ASM1, ASM2, ASM2d, ASM3*, IWA STR 9. ASM1·ASM2 부분은 스캔 이미지라 텍스트 추출 불가(ASM2d·ASM3만 확인).
- `Textbook_ref_matching.docx`는 온도계수 참고용 한 줄 메모라 본 검토와 무관.

방법: 각 책을 전담 검토(단위공정 목록, 공정 구성 그림, 용어, 모델 요소, 글로서리)하고, 4권 전체에서 용어 빈도를 세어 교차 검증했으며, 지적된 누락 항목이 우리 후보 이미지 1,325장(main + aux_unit + crop_pending)의 캡션에 얼마나 나오는지 확인했다.

---

## 1. 요약: 교과서가 확인해 준 것과 틀렸다고 한 것

### 1.1 옳았던 것 (근거 포함)

| v0의 결정 | 교과서 근거 |
|---|---|
| **의미 클래스와 그림 양식 분리 (원칙 1)** | [Olsson] Fig 2.5 (p.32)의 "typical WWT process flowsheets"는 똑같은 사각형에 기능 코드(C, N, DN, CP, PR, PU, S)만 적은 박스 연쇄다. 1차·2차 침전지는 둘 다 "S"이고 위치로만 구별된다. 교과서 자체가 우리 양식 A(박스형)로 그리며, 모양에는 정보가 없다. [GMP] p.80: 시뮬레이터 레이아웃은 "아이콘 + 연결"이며 실제 공정도를 모델 개념으로 "번역"하는 일이다. |
| **L1 7단계 골격** | [Olsson] p.29-30 (1차 = 스크린·침전·스컴, 2차 = 생물반응 + 침전, 3차 = 여과·막·소독), [IWA] Fig 9.1 (p.245), Fig 16.24 (p.448) 전체 플랜트 흐름도가 같은 골격. 양쪽 모두 슬러지 라인을 별도로 그린다. |
| **구역 박스 + parent (is_zone / parent_id)** | [GMP] Fig A.9 (p.196): 실제 탱크는 격벽(partition walls)으로 나뉜 한 상자이고, 모델은 그 격벽·산기관 구역을 따라 자른 CSTR 연쇄다. "모델링의 첫 행위가 탱크를 구역으로 자르는 것"이므로 구역 박스는 선택이 아니라 필수. [Olsson] p.361: BNR 공정은 "prefermenter, anaerobic zone, anoxic zone, aerobic zone"으로 나뉜다. |
| **digester(슬러지)와 anaerobic_reactor(폐수) 분리** | [Olsson] p.89: 활성슬러지 소화에는 단순 완전혼합 반응기, 고농도 폐수에는 2단 반응기. [IWA] ch.16은 폐수용 혐기성 반응기(UASB 등)를 소화조와 구별. |
| **junction_split / junction_merge** | [Olsson] p.241: 시뮬레이터의 "flow splitters, mixer boxes"; [GMP] Table 5.3.2 (p.82-83): 분기기(ratio/fraction/pumped/bypass/router/pacing)가 독립 모델 요소. |
| **process_unit_generic** | [Olsson] Fig 2.5, Fig 15.1 (p.395)처럼 교과서의 플랜트 그림 대부분이 라벨 박스. |
| **1차·2차 침전지 분리, L3 원형/사각 분할** | [IWA] Fig 12.3·12.5·12.6 (p.312-313): 원형 방사류, 사각 수평류, 수직류(Dortmund)는 그림이 다름. [Olsson] Fig 2.10 (p.37). |

### 1.2 틀렸거나 모호한 것 (심각도 순)

| # | 문제 | 근거 | 수정 방향 |
|---|---|---|---|
| E1 | **`anaerobic_tank` vs `anaerobic_reactor` 이름 충돌.** [IWA]는 EBPR 혐기 구역도 "anaerobic reactor"(ch.7), UASB도 "anaerobic reactor"(ch.16 제목)라 부른다. 우리 이름은 두 개념을 tank/reactor로 가르는데, 교과서 어휘와 반대다. | [IWA] p.165 Fig 7.12, p.433; 각주 p.167: anoxic = 질산염 있음·산소 없음, anaerobic = 둘 다 없음. [Olsson] 글로서리 p.678 동일 정의. | 활성슬러지 구역 셋을 `aerobic_zone` / `anoxic_zone` / `anaerobic_zone`으로, 폐수용 혐기성 반응기를 `anaerobic_wastewater_reactor`로 개명. 판별 규칙: 활성슬러지 열 안의 개방 탱크(교반, 가스 후드 없음) → zone; 밀폐·상향류·바이오가스 배관·GLSS → wastewater reactor. |
| E2 | **`chemical_dosing`이 세 가지를 뭉침**(주입점 / 응집·응결조 / 후침전지), 그리고 L1 "primary"에 둔 것이 틀림. | [IWA] Fig 7.11 (p.164): Al/Fe/Ca·탄소원 주입은 대부분 기존 단위(PST, 혐기조, 포기조, SST)로 들어가는 **화살표**이지 장치가 아님. 전·동시·후침전 (p.164, 356, 403). [Olsson] p.30, 417: 약품 침전은 1차·동시·3차 어디든 가능하고, 후침전은 별도 침전지와 "return chemical sludge"를 가짐 (Fig 15.1 p.395). [GMP] p.83: "Iron or aluminium salt dosage"는 입력 모델. | (a) 주입점은 `io_terminal(role=chemical_source)` + `stream_role=chemical_dose`로, (b) 응집·응결·침전 탱크만 `chemical_treatment_unit`(L1 무관, 위치 속성), (c) 후침전지는 `clarifier(stage=chemical)`로. |
| E3 | **`flotation_unit`을 "primary"에 둔 것이 틀림.** | [IWA] p.80, 83: DAF는 WAS 농축; p.309: 활성슬러지 분리의 대안. [Olsson] 언급 없음. [GMP] Beenyup 사례 p.144: "WAS is thickened using DAF". 우리 캡션에도 DAF 22건은 대부분 슬러지·산업폐수. | L1 무관 클래스로 두고 `function ∈ {primary, secondary_separation, thickening}` 속성. |
| E4 | **`biofilm_reactor` 한 클래스가 R1(시각 구별)·R2(하류 매핑)을 모두 위반.** 살수여상(탑 + 회전 살수기 + 별도 침전지 + QR 순환), RBC(축에 디스크), BAF/SAF(여재층 + 역세 + 공기, **여과지와 똑같이 보임**), MBBR/IFAS(캐리어 든 탱크, **포기조와 똑같이 보임**), airlift/유동상/입상(3상 분리기 달린 탑, **UASB와 똑같이 보임**), MABR. | [IWA] Fig 18.1 (p.494) A~H 유형, Fig 18.3·18.5·18.7·18.9·18.10. GPS-X·SUMO도 모두 별도 단위. 우리 캡션: MBBR/IFAS 25, BAF 14, 살수여상 9, RBC 2. | L3 분할을 **필수**로: `trickling_filter`, `rbc`, `submerged_biofilter`(BAF/SAF), `mbbr_ifas`, `airlift_fluidized_granular`, `mabr`. 판별 규칙: 공기 공급선 있음 + 여재 → 생물여과, 없음 → `filtration_unit`; 바이오가스선 → 혐기성, 공기선 → airlift. |
| E5 | **`anaerobic_reactor` 세부형과 소화조 판별.** UASB/EGSB/IC(상향류·GLSS·가스돔), 혐기성 여상(충전층), ACP(CSTR + 침전지 + 반송 = 활성슬러지처럼 보임), CSTR(소화조와 **동일 기호**), ABR, AnMBR, 혐기성 연못. 한 UASB 박스는 "1차 침전지 + 반응기 + 2차 침전지 + 슬러지 소화조" 네 기능을 겸한다. | [IWA] Fig 16.14·16.15·16.20·16.25 (p.434-449), p.447. [Olsson] p.89, 536 (2단 소화). | L3: `uasb_egsb_ic`, `anaerobic_filter`, `anaerobic_contact`, `anaerobic_cstr`, `abr`. 소화조 vs CSTR은 **공급 스트림으로 판별**(슬러지 → `digester`, 폐수 → wastewater reactor, 불명 → generic + `confidence=inferred_from_context`). 매핑 필드에 `multi_unit`(한 노드 → 여러 시뮬레이터 단위) 추가. |
| E6 | **누락 클래스·역할.** ① 반류수(sidestream) 처리 반응기: SHARON, Anammox, CANON/DEMON, BABE/BAR, P-stripper, 스트루바이트 — 호기 CSTR이나 UASB처럼 보이지만 공급이 reject water. ② 1차 슬러지 발효조(prefermenter). ③ 구역 역할: selector(IWA 115회), 재포기(reaeration), 탈산소(oxygen depletion), 반송선 위 무산소조(JHB underflow anoxic), 탈기(degasifier). ④ 교대·간헐 운전(MIA, Bio-Denitro, IDEA, SBR 상) — 한 탱크의 기능이 시간에 따라 바뀜. ⑤ 계측·제어 요소, ⑥ 밸브, ⑦ 교반기·산기장치 기호. | ① [IWA] ch.6 p.144-150, Fig 6.11; [GMP] p.56, 180 ("sidestream" 정의). 우리 캡션 42건. ② [IWA] p.163-164 Fig 7.11; [Olsson] p.35, 361-363, 395, 246. 캡션 11건. ③ [IWA] p.299-302 Table 11.2, p.111-112, p.356, p.170; [GMP]는 selector를 아예 이름 짓지 않고 "산기 상태가 다른 CSTR"로 취급(p.195). ④ [IWA] p.80, 171, 356-357; [Olsson] p.522-524, 550-551; [GMP] Table 5.3.3 "Alternating" (p.83). 캡션 31건. ⑤ [Olsson] p.507, 536, 456 (태그·버블로만 등장), p.573 ("센서 위치는 P&ID에"); [IWA] Fig 13.24, 14.4, 15.11. 캡션 52건. ⑥ [Olsson] p.608 "predominant actuator"; 캡션 14건. ⑦ [IWA] ch.9 Fig 9.2-9.10; 캡션 교반기 17, 산기 11. | ① `sidestream_reactor`(L2, 의미) + 박스 속성 `treatment_line ∈ {mainstream, sidestream, sludge}`. ② `fermenter`(슬러지 L1; 50개 미만이면 `digester/acid_phase` L3). ③ 클래스가 아니라 **속성** `zone_role ∈ {main, selector, reaeration, deoxygenation, underflow_anoxic, stripper}` (세 책 모두 독립 장치로 보지 않음; Olsson에서 "selector"는 제어 선택기 의미라 클래스명으로 쓰면 안 됨). ④ 속성 `operation_mode ∈ {continuous, sequencing, alternating, intermittent}` + SBR 다중 패널은 패널마다 1 단위 + `panel_phase`. ⑤ `instrument`(주석 클래스; `measured_variable` 자유 텍스트, `instrument_role ∈ {sensor, analyser, controller, setpoint}`; Kim 2022의 18종 분할은 인스턴스 부족으로 채택 안 함). ⑥ `valve`(ancillary; 세부형 없음 — Theisen의 밸브 8종은 AP 45~65%). ⑦ `aerator_mixer_symbol`(ancillary, 병합 후보) 또는 탱크 속성 `aeration_mode ∈ {diffused, surface, brush, mixer_only, none}` — 이 기호가 호기/무산소를 가르는 시각 단서이므로 반드시 라벨. |
| E7 | **`stream_type` {water, sludge, gas, chemical, air}가 너무 거침.** 교과서 스트림 이름: influent/settled/screened, mixed liquor, a-recycle(MLR), s(RAS), r(anoxic→anaerobic), QR(TF 순환), WAS, primary/thickened/digested/chemical sludge, supernatant/reject water/centrate/filtrate/backwash, bypass/overflow, step-feed, biogas/off-gas/N2, process air/air scour/pure O2, chemicals, signal(점선). WAS는 침전지가 아니라 **반응조에서** 뽑는 그림이 IWA ch.4-7 전부. | [IWA] p.56, 84-85, 169, 402-403, 495; [Olsson] Fig 15.1 p.395, Table 16.4 p.422, p.362 ("liquid or gas flows as solid lines, logical connections as dashed"); [GMP] p.82, 185, 196. | 2단 필드: `medium ∈ {liquid, mixed_liquor, sludge, gas, air, chemical, solid, signal}` + `stream_role ∈ {influent, settled_influent, effluent, mixed_liquor, internal_recycle_a, ras_s, r_recycle, effluent_recirculation_QR, was, primary_sludge, thickened_sludge, digested_sludge, chemical_sludge, sidestream_return, backwash_return, bypass, overflow, step_feed, biogas, air_supply, chemical_dose, signal}`. `recycle_marker` → `stream_label`(선 위 텍스트)로 개명하고 `stream_role`을 속성으로. WAS 출처를 침전지로 가정하지 말 것. |
| E8 | **`junction_split`에 유형이 없고, 그려진 분배조를 빠뜨림.** | [GMP] p.186 분기기 6유형(ratio, fraction, pumped, bypass, router/alternating, pacing); [IWA] Fig 14.4 "Divider", Fig 16.25 "distribution box", p.315 "splitting boxes"; [Olsson] p.413 (고정 수로 분배, bypass, step feed). | `split_type` 속성; 박스·기호로 그려진 분배조도 junction으로 라벨; `junction_merge`에 `merge_role ∈ {step_feed_inlet, sidestream_return, chemical_dosing_point, recycle_return, lane_combiner}`. |
| E9 | **병렬 계열(lanes) 정보가 없음.** 모델러는 병렬 계열을 "총 부피 한 계열"로 합치거나 하나만 모델링한다. 분기 비율(40/60%)도 필요. | [GMP] Table 5.3.1 p.80, p.172, p.146. | 이미지·단위 속성 `n_parallel_lanes`, `lane_group_id`; 스트림 속성 `split_fraction`. |
| E10 | **정의 보강이 필요한 클래스.** `aeration_tank`에 "aerator", "aeration basin", "oxidation ditch", "Deep Shaft", "aerated lagoon(연못 윤곽이면 pond)" 별칭; `secondary_clarifier`에 humus tank(살수여상 후단), 후침전지, Dortmund·lamella 형상; `equalization_tank`에 storm/detention/buffer tank; `pump_station` = wet well + 펌프 여러 대 = 1 단위; `storage_tank`에 슬러지 저류·반송슬러지 저류; `digester`에 호기·ATAD·2단(산발효/메탄) 소화; `biogas_unit`에 가스홀더·플레어·엔진/CHP·보일러·H2S 제거; "Filter" 박스는 라인으로 판별(슬러지 라인 → dewatering, 물 라인 → filtration); `sbr_tank` 정의에 fill/react/settle/decant; SBR는 "sequencing"(Olsson은 sequential). | [Olsson] p.31, 379, 483, 245, 689, 62, 414, 508, 485, 363, 89, 388-389, 395, 522; [IWA] p.77-80, 309-314, 355-356, 433, 441, 447-450. | 가이드라인 v1의 정의·별칭·판별 규칙에 반영. |
| E11 | **`advanced_oxidation_unit` 독립 근거 없음.** | [IWA]에 AOP 단위 없음; 오존은 소독(p.237)과 벌킹 제어(p.299)로만 등장. 캡션 빈도 낮음. | `disinfection_unit`으로 병합(오존·UV·염소), 목적은 `label_text`로. |

### 1.3 교과서끼리 다른 점 (가이드라인에 별칭으로 흡수)

| 용어 | IWA | Olsson | GMP | 우리 선택 |
|---|---|---|---|---|
| 호기 구역 | aerobic reactor(273) ≫ aeration tank(41) | "aerator" = 포기조(p.379, 483), aeration tank | aerated CSTR, "aerobic condition" | `aerobic_zone`; 별칭 aeration tank/basin, aerator, aerobic reactor |
| 2차 침전 | secondary settling tank(SST) ≈ settler ≈ clarifier | settler/clarifier 혼용 | clarifier (point/ideal/layered 모델) | `secondary_clarifier`; 별칭 SST, final settler, settler, humus tank |
| RAS | sludge recycle s, return sludge | "recycle activated sludge" | RAS, RS, return sludge | `ras_s`; 별칭 모두 |
| selector | 생물학적 셀렉터 구역(115회) | 제어 MAX/MIN 선택기 | 언급 없음 | 클래스명 금지, `zone_role=selector` |
| anaerobic reactor | EBPR 구역과 UASB 둘 다 | — | "anaerobic condition" | E1의 개명 |
| 산기 장치 | diffused aeration 140, surface aerator 28 | 거의 없음 | 별도 aeration sub-model | 속성 `aeration_mode` + 기호 클래스 |

---

## 2. 세 가지 결정 사항의 재평가

| 결정 | v0 권고 | 교과서 검토 후 |
|---|---|---|
| ① 의미/양식 두 필드 분리 | 채택 | **더 강하게 채택.** Olsson Fig 2.5는 교과서도 박스형으로 그린다는 증거이고, GMP는 모델 레이아웃이 "아이콘+연결"이라고 명시. 여기에 `aeration_mode`·`zone_role`·`operation_mode`처럼 **모양만으로는 못 읽는 속성**이 추가로 필요하다는 것이 세 책의 공통 결론. |
| ② 병합 후보 5개 | 파일럿 후 결정 | AOP → 소독에 **지금 병합**(E11). 바이오가스·건조소각은 유지(두 책이 플레어·CHP·홀더·소각을 명시). 송풍기 유지 + `valve`·`mixer/aerator` 추가. 인공습지 유지하되 `pond_lagoon_wetland`로 개명, `aerated` 속성. |
| ③ 구역 박스 | 구역 박스 + parent | **필수.** 단, parent가 그려지지 않은 경우(IWA는 구역을 각각 별도 상자로 그림)와 산화구처럼 상자 없이 수로 구간만 텍스트로 표시된 경우를 허용해야 함: `parent_id` null 허용 + 인접성으로 추론, `is_loop_reactor` 플래그. |

---

## 3. 개정안 v1 (교과서 반영)

### 3.1 L2 의미 클래스 (28 → 30; 개명 4, 추가 4, 병합 2, 이동 2)

> 정정(v1.1 검토, 2026-11-16): 위 "28 → 30"은 generic 2개를 뺀 값에 집계 오류가 섞인 것이다. 아래 표의 실제 행 수는 **33개(단위공정 31 + generic 2)** 이며 `annotation_taxonomy_plan.md` §4.1이 기준이다.

| L1 | L2 (v1) | v0 대비 | L3 (데이터 충분 시) |
|---|---|---|---|
| preliminary | `screen`, `grit_chamber`, `equalization_tank`(+storm/buffer), `pump_station`(wet well 포함) | 정의 보강 | — |
| primary | `primary_clarifier`(+Imhoff/septic) | 정의 보강 | circular / rectangular |
| separation(위치 무관) | `flotation_unit` | **이동**: primary → 위치 무관, `function` 속성 | — |
| separation(위치 무관) | `chemical_treatment_unit` | **개명·축소**: 응집·응결·침전 탱크만. 주입점은 `io_terminal(chemical_source)` | — |
| secondary | `aerobic_zone`, `anoxic_zone`, `anaerobic_zone` | **개명** (E1); 속성 zone_role, aeration_mode, operation_mode | — |
| secondary | `secondary_clarifier`(+humus, 후침전) | 정의 보강 | circular / rectangular / vertical / lamella |
| secondary | `mbr_unit` | 위상 판별 규칙(iMBR/sMBR) 추가 | immersed / sidestream |
| secondary | `sbr_tank` | 정의 보강, panel_phase | — |
| secondary | `biofilm_reactor` | **L3 필수** (E4) | trickling_filter / rbc / submerged_biofilter / mbbr_ifas / airlift_fluidized_granular / mabr |
| secondary | `anaerobic_wastewater_reactor` | **개명** (E1), L3 (E5), multi_unit | uasb_egsb_ic / anaerobic_filter / anaerobic_contact / anaerobic_cstr / abr |
| secondary | `pond_lagoon_wetland` | **개명**, `aerated` 속성 | — |
| sidestream | `sidestream_reactor` | **추가** (E6-①) | — |
| tertiary | `filtration_unit`, `membrane_unit`, `disinfection_unit`(+AOP) | **병합** AOP→소독 (E11) | — |
| sludge | `fermenter` | **추가** (E6-②) | — |
| sludge | `thickener`, `digester`(+aerobic/ATAD/2단), `dewatering_unit`, `drying_incineration_unit`, `biogas_unit`(+flare/CHP/holder) | 정의 보강 | — |
| ancillary | `pump`, `blower`(+compressor/fan), `storage_tank`, `valve`, `aerator_mixer_symbol` | **추가** valve, aerator_mixer_symbol (E6-⑥⑦) | — |
| generic | `process_unit_generic`, `unknown_equipment` | 유지 | — |

### 3.2 연결·주석 클래스 (7 → 8)

`arrowhead`, `text_label`, `stream_tag`(+tag_kind), `stream_label`(← recycle_marker, +stream_role), `io_terminal`(+role), `junction_split`(+split_type), `junction_merge`(+merge_role), **`instrument`**(추가; +measured_variable, instrument_role).

### 3.3 속성 (박스·스트림·이미지)

- 박스: `visual_form`, `treatment_line`, `zone_role`, `aeration_mode`, `operation_mode`, `is_zone`/`parent_id`(null 허용), `is_loop_reactor`, `function`(flotation), `clarifier_stage`, `confidence`, `label_text`, `n_compartments`.
- 스트림(그래프 엣지): `medium`, `stream_role`, `split_fraction`, `direction_confidence`.
- 이미지: `diagram_style`, `language`, `n_parallel_lanes`, `lane_group_id`, `panel_phase`.
- 매핑(classes.yaml): `gpsx_unit`, `bsm_unit`(GMP Table 5.3.2 어휘로 제한: CSTR / point·ideal·layered clarifier / splitter type / input model / primaries / digester / sludge handling), `dexpi_parent`, `iso10628_group`, `kds61_term`, `multi_unit`.

### 3.4 판별 규칙 (가이드라인에 넣을 핵심 문장)

1. 활성슬러지 열 안의 개방 탱크는 redox 라벨로 `aerobic/anoxic/anaerobic_zone`; 밀폐·상향류·가스선이 있으면 `anaerobic_wastewater_reactor`; 슬러지가 공급되면 `digester`; 모르면 generic + `inferred_from_context`.
2. 여재층 + 공기 공급선 → `biofilm_reactor/submerged_biofilter`; 공기선 없음 → `filtration_unit`.
3. 캐리어·충전재가 든 포기 탱크 → `biofilm_reactor/mbbr_ifas`; 캐리어 표시가 없으면 `aerobic_zone`.
4. 막 모듈이 혼합액을 받고 슬러지/농축액을 반응조로 되돌리면 `mbr_unit`, 처리수를 받으면 `membrane_unit`.
5. "Filter" 박스: 농축조·소화조 하류 → `dewatering_unit`, 물 라인 → `filtration_unit`.
6. 약품은 화살표(주입점)로 라벨; 탱크가 그려진 경우만 `chemical_treatment_unit`; 그 뒤의 침전지는 `secondary_clarifier(stage=chemical)`.
7. 한 탱크를 여러 번 그린 SBR 패널은 패널마다 1 단위 + `panel_phase`; 교대 운전 쌍은 둘 다 `aerobic_zone` + `operation_mode=alternating`.
8. WAS 화살표는 반응조·침전지·반송선 어디서든 나올 수 있다; 출처를 가정하지 말고 `stream_role=was`만 붙인다.
9. 한 wet well 안의 펌프 여러 대 = `pump_station` 1개; 단독 펌프 기호 = `pump`; 약품 펌프 = `pump` + `stream_role=chemical_dose`.
10. UASB·IC 한 상자는 `multi_unit=[primary_clarifier, reactor, secondary_clarifier, digester]`로 매핑.

---

## 4. 데이터로 본 추가 클래스의 실현 가능성 (후보 1,325장 캡션)

| 항목 | 캡션 건수 | 판단 |
|---|---|---|
| 반류수 처리(SHARON·Anammox·reject water 등) | 42 | `sidestream_reactor` 독립 가능성 있음(파일럿 확인) |
| 계측·제어 | 52 | `instrument` 주석 클래스 타당 |
| 교대·간헐·상(phase) 운전 | 31 | `operation_mode` 속성 필요 |
| MBBR/IFAS 25, BAF 14, 살수여상 9, RBC 2 | — | `biofilm_reactor` L3 중 mbbr_ifas·submerged_biofilter는 독립 가능, rbc는 병합 |
| DAF 22, 응집·침전 26 | — | 위치 무관 클래스로 충분 |
| 발효조 11, 밸브 14, 교반기 17, 산기 11 | — | 50개 미만 예상 → 병합 후보로 두고 파일럿에서 결정 |
| selector 3, 재포기 2, humus 0, step feed 1 | — | 클래스 불가, 속성으로만 |

---

## 5. 한계

- ASM 보고서의 ASM1 "Modelling of complex flow schemes"와 ASM2 전체가 스캔 이미지라 확인하지 못했다(ASM2d·ASM3만 텍스트). GMP가 같은 내용을 더 자세히 다루므로 결론에는 영향이 작다.
- GMP의 Table 5.3.3(실제 플랜트 ↔ 모델 흐름도)과 Fig 7.24(Beenyup 전체 모델)는 그림이라 텍스트가 단편적이다.
- 교과서는 활성슬러지 중심이라 MBR·SBR·생물막·혐기성 세부형의 모델링 관행은 GPS-X·SUMO 매핑에 의존한다.
- 캡션 빈도는 하한선이다(캡션에 없는 장치가 많다). 최종 클래스 수는 파일럿 60장의 실제 인스턴스 수로 정한다.
