# 어노테이터 교육 진행 대본 (2시간 + 연습 5장)

대상: 어노테이터 2명 · 진행: 판정자(연구 책임자) · 절차: 파일럿 v1.1b(쉬운 버전) · 2026-11-18
준비물: 프로젝터(또는 큰 모니터), Label Studio 실행(`label-studio start --port 8080`), 프로젝트 `practice`(5장)·`pilot_A`·`pilot_B`, 인쇄물 = 요약 카드(각 1장) + 쉬운 버전 매뉴얼(각 1부), 완전판 매뉴얼은 진행자용 1부.

원칙: **보여 주고(화면·그림) → 말하고(핵심 한 문장) → 시켜 본다(연습)**. 설명보다 손으로 해 보는 시간이 길어야 한다. 아래 "말하기"는 그대로 읽어도 되는 문장이고, "확인"은 넘어가기 전에 두 사람에게 물어볼 질문이다.

---

## 0. 시작 전 (10분, 교육 시작 전에 끝낼 것)

- Label Studio가 떠 있고 `practice` 프로젝트 1번이 열리는지 확인. 두 사람 각자 노트북에서 로그인(같은 계정이어도 됨; 연습은 `practice`, 본 작업은 A·B로 나뉨).
- 요약 카드를 각자 앞에 둔다. 매뉴얼은 펼쳐 두되 교육 중 읽게 하지 않는다.
- 연습 결과는 버릴 것이므로 "틀려도 된다"를 먼저 말한다.

## 1. 왜 이 일을 하는가 (10분)

**보여 줄 것**: 쉬운 버전 매뉴얼 1쪽 그림 1(다섯 단계), 파일럿 1번 그림(Wet Weather Treatment Train).

**말하기**
- "하수처리장 공정도 그림을 컴퓨터가 읽을 수 있게 만드는 일입니다. 그림 위의 장치마다 네모를 치고 이름을 붙이고, 장치 사이의 흐름을 선으로 잇습니다."
- "이 데이터로 '그림을 보면 공정 그래프를 뽑아 주는' 모델을 학습하고, 그 그래프로 시뮬레이션 모델을 자동으로 만듭니다. 그래서 '어떤 장치인가'와 '어디서 어디로 흐르나'가 핵심입니다."
- "두 분이 같은 60장을 따로 합니다. 목적은 '얼마나 같게 하는가'를 재는 것입니다. 틀린 사람을 찾는 게 아니라 규칙의 빈틈을 찾는 과정입니다. 그래서 작업 중에는 서로 묻지 않고, 애매하면 메모를 남깁니다."
- "기억할 세 가지: 빠짐없이, 규칙대로 일관되게, 그림에 있는 것만."

**확인**: "한 장에서 하는 다섯 단계를 순서대로 말해 보세요." (장치·구역 박스 → 단자·분기·합류·계측 박스 → 속성 → 선 긋기 → 그림 속성·제출)

## 2. 화면 익히기 (15분, 진행자가 시연)

**보여 줄 것**: `practice` 1번(PMC 산업폐수 그림)을 열어 화면을 함께 본다. 매뉴얼 2절 그림 2.

**시연 순서와 말하기**
1. "위쪽 색깔 버튼이 장치 이름입니다. 색은 처리 단계 묶음입니다. 숫자 키 1~0으로 자주 쓰는 것을 바로 고릅니다." → 숫자 3을 눌러 `aerobic_zone`이 선택되는 것을 보여 준다.
2. "버튼을 누른 상태에서 그림 위를 드래그하면 네모가 생깁니다." → 아무 탱크에 하나 그린다.
3. "네모를 클릭하면 오른쪽 아래에 그 네모의 속성 칸이 나옵니다. visual_form, confidence, is_zone, l1_hint, io_role, label_text 여섯 개뿐입니다." → visual_form=pictorial, confidence=inferred_from_text를 고른다.
4. "오른쪽 Regions 목록에 지금까지 그린 네모가 쌓입니다. 거기서 클릭하면 다시 선택됩니다."
5. "잘못 그렸으면 클릭하고 Delete, 되돌리기는 Ctrl+Z." → 방금 네모를 지운다.
6. "선 긋기: 출발 네모 클릭, 키보드 r, 도착 네모 클릭." → 두 네모를 잇고 Relations 탭을 보여 준다. "기본은 라벨 없음. 점선이면 style:dashed처럼 예외만 고릅니다."
7. "맨 아래 그림 속성 세 개를 고르고 Submit. 다음 장으로 넘어갑니다. 저장은 Submit 때 됩니다."
8. 확대: "작은 것은 휠로 확대해서 그립니다. 손바닥 아이콘으로 화면을 옮깁니다."

**확인**: 두 사람이 각자 네모 하나 그리기 → 속성 고르기 → 삭제까지 해 본다.

## 3. 무엇에 네모를 치나 (10분)

**보여 줄 것**: 매뉴얼 1절 표(① ~ ⑤, 쉬운 버전/완전판 열), 요약 카드 ③ "안 치는 것".

**말하기**
- "쉬운 버전(21~60번)에서 치는 것: 장치, 구역, 유입·유출 끝(io_terminal), 갈라짐·합침 지점(junction), 센서 태그(instrument). 안 치는 것: 화살촉, 글자. 1~20번은 화살촉과 글자까지 다 칩니다."
- "치지 않는 것: 흐름선 자체, 캡션 문장, 범례, 표, 제목, 로고."
- "같은 장치가 4개 나란히 있으면 4개 다 칩니다. '×4'라고 글자만 있으면 1개."
- "네모는 장치 윤곽에 꼭 맞게. 여백을 두지 않습니다."

**확인**: 파일럿 1번 그림을 보여 주고 "여기서 쉬운 버전으로 치는 네모는 몇 개?"(장치 8 + 단자 1 + 분기 2 + 합침 2 = 13)

## 4. 이름 고르기 (25분)

**보여 줄 것**: 매뉴얼 3절 표와 그림 3(라벨 버튼), 그림 4(box/symbol/pictorial), 요약 카드 ①.

**말하기 — 가장 자주 쓰는 여섯 개부터**
- "기포·산기관이 있는 생물 탱크 = aerobic_zone(3). 포기조, 폭기조, aeration tank, oxic 전부 이것입니다."
- "교반기만 있고 질산염 반송이나 RAS가 들어오면 anoxic_zone(4). 교반기만 있고 유입수를 가장 먼저 받으면 anaerobic_zone(5)."
- "침전지는 모양이 같습니다. 생물반응조 앞이면 primary_clarifier(2), 뒤이면 secondary_clarifier(6). 반송선이 있으면 무조건 2차."
- "여과(7), 소독(8), 농축조(9), 소화조(0)."

**말하기 — 헷갈리는 쌍**
- "막: 혼합액을 받고 슬러지를 돌려보내면 mbr_unit, 처리수를 받으면 membrane_unit."
- "생물막 반응기와 혐기성 폐수 반응기는 반드시 슬래시 뒤 세부형까지. 살수여상/회전원판/침지여재/담체/유동상/MABR, UASB류/여상/접촉/CSTR/ABR/AnMBR."
- "슬러지 라인: 소화조 앞 원뿔 탱크나 벨트는 농축조, 소화조 뒤 원심·벨트·프레스는 탈수기. 달걀·돔형에 슬러지가 들어가면 소화조."
- "약품은 장치가 아니라 선입니다. 응집 탱크가 그려졌을 때만 chemical_treatment_unit."

**말하기 — 종류 미상**
- "글자가 없거나 번호뿐이거나, 글자가 'Biological Treatment'처럼 단계 이름이면 process_unit_generic. 이때 l1_hint로 어느 단계인지 고르고, 글자를 label_text에 그대로 적습니다."
- "목록에 없는 장치(후포기, 탈취, 열교환기, 소각로 주변 설비)는 unknown_equipment. 역시 l1_hint와 글자."

**말하기 — visual_form**
- "글자로만 종류를 알면 box, 모양 자체가 말해 주면 symbol(원뿔 바닥 침전지, 달걀형 소화조, 막 카세트), 3D·아이콘이면 pictorial. 동그라미에 'Primary Clarifier'라고 쓰였으면 box입니다."
- "confidence: 모양으로 확실하면 certain, 글자를 읽고 알았으면 inferred_from_text, 흐름 위치로 짐작했으면 inferred_from_context."

**확인**: 요약 카드를 보며 "교반기만 있는 탱크가 유입수 바로 다음에 있고 그 뒤에 또 교반 탱크, 그 뒤 포기조. 첫 탱크는?"(anaerobic_zone) "그 그림에서 두 번째 교반 탱크는?"(anoxic_zone)

## 5. 구역과 판별 흐름도 (10분)

**보여 줄 것**: 매뉴얼 4절 그림 5(세 구역), 그림 6(판별 흐름도).

**말하기**
- "한 탱크에 혐기·무산소·호기가 나뉘어 있으면 구역마다 네모를 치고 is_zone을 체크합니다. 탱크 윤곽이 그려져 있으면 탱크에도 네모를 치고, 탱크 네모 → 각 구역으로 parent_of 관계를 긋습니다. 탱크 네모의 이름은 process_unit_generic + l1_hint=secondary."
- "구역 이름이 안 적혀 있으면 흐름도: 호기조 앞에 교반만 하는 구역이 몇 개인지 세고 반송이 어디로 들어오는지 봅니다. 그래도 모르면 generic + is_zone."
- "산화구(길쭉한 트랙 모양)는 한 네모로 aerobic_zone."

**확인**: 그림 6을 가리키며 "교반 구역 2개, 두 번째에 RAS와 내부 반송이 들어오고 두 번째에서 첫 번째로 반송선이 있다. 각각?"(혐기, 무산소 — UCT)

## 6. 선 긋기 (15분, 시연 + 따라 하기)

**보여 줄 것**: 매뉴얼 6절, 그림 8(파일럿 1번 엣지), 요약 카드 ③.

**말하기**
- "출발 클릭 → r → 도착 클릭. 화살표 방향이 흐름 방향이니 출발을 먼저 클릭합니다."
- "라벨은 예외만: 화살촉이 없는 선은 no_arrow, 방향을 모르면 direction_unknown, 점선은 style:dashed, '(Optional)'이면 optional, 탱크→구역은 parent_of."
- "물인지 슬러지인지는 고르지 않습니다. 양쪽 장치를 보면 컴퓨터가 압니다."
- "갈라지거나 합쳐지는 곳은 반드시 junction 네모를 거칩니다. 침전지 바닥에서 반송과 잉여 슬러지가 갈라지면 그 지점에 junction_split, 거기서 반응조로 하나, 농축조로 하나."
- "인접 구역 사이(혐기 → 무산소 → 호기)는 선이 안 그려져 있어도 연결하고 no_arrow."
- "약품 화살표: 시작점에 io_terminal(chemical_source), 들어가는 지점에 junction_merge, 둘을 잇습니다."

**따라 하기**: `practice` 1번에서 진행자가 유입 → 첫 탱크 → 다음 탱크 세 개를 이어 보이고, 두 사람이 같은 것을 각자 해 본다.

## 7. 연습 5장 (40분, 두 사람이 각자 하고 장마다 멈춰서 맞춰 본다)

장마다 "각자 5~7분 → 화면을 나란히 띄우고 다른 점 찾기 → 규칙으로 정리" 순서. 아래는 장별로 **나올 질문과 답**이다.

### 연습 1 — PMC, 산업폐수 처리장 3D 그림 (pictorial)

- 무엇이 보이나: 폐수 집수조(Collection Tank 1), NaOH·HCl 약품 탱크, 중화조(Neutralization), Precoat 탱크, Kelly Filter(여과기), RO, 투과수 집수조(Collection Tank 2), 재이용(Reuse), 펌프 여러 개, Perlite 투입.
- 예상 질문과 답:
  - "약품 탱크(50% NaOH)는 장치인가?" → 그림에 탱크로 그려져 있으니 `storage_tank`(약품 저류). 거기서 나가는 선은 chemical 매체로 자동 채워짐. 탱크가 없고 화살표만 있으면 io_terminal(chemical_source).
  - "Neutralization은?" → 응집·중화 탱크 = `chemical_treatment_unit`. visual_form=pictorial.
  - "Kelly Filter는?" → `filtration_unit`(여과기). 이름이 낯설어도 '필터'면 여과.
  - "RO는?" → 처리수를 받는 막 = `membrane_unit`.
  - "Collection Tank 1·2는?" → `storage_tank`(처리 기능 없는 저류) 또는 유량을 고르는 역할이 명시되면 `equalization_tank`. 글자가 'Collection'이면 저류로.
  - "Perlite(여과 보조제) 투입은?" → 선: io_terminal(chemical_source) → junction_merge.
  - "펌프는 전부 치나?" → 쉬운 버전에서도 `pump`는 장치이므로 친다.
  - "Waste Water Boehmite/Alumina/Boiler Feed 세 줄은?" → 유입 단자 3개 `io_terminal(raw_influent)`, 'Drinking Water'는 external 공급 → io_terminal(continuation 또는 raw_influent 중 '외부 공급수'라 적고 메모).
- 정리 한마디: "산업폐수 그림은 모르는 장치가 많습니다. 모르면 unknown_equipment + 글자, 하지만 필터·막·탱크·펌프처럼 범주가 분명하면 그 클래스."

### 연습 2 — 미국 특허 FIG. 3 (세로로 돌아간 박스 도면, 번호 참조)

- 무엇이 보이나: 0.12" Screen → Inflow → 640 gal Mixed Anoxic Tank → 1105 gal Aerobic Tank → Return flow / Gravity flow → 165 gal Membrane Tank(A-30) → Permeate. Sludge Return, Sewer Lift Station, 펌프 P 3개, 참조 번호(70~132).
- 예상 질문과 답:
  - "글자가 세로로 돌아가 있다" → 그대로 친다. 필요하면 머리를 기울여 읽는다. 회전 기능은 쓰지 않는다.
  - "Mixed Anoxic Tank / Aerobic Tank는?" → `anoxic_zone` / `aerobic_zone`. 별도 탱크로 그려졌으니 parent_of 없이 구역 둘만(is_zone은 체크).
  - "Membrane Tank는?" → 혼합액을 받고 Return flow로 돌려보냄 = `mbr_unit`. Permeate는 effluent 단자.
  - "Sewer Lift Station은?" → `pump_station`.
  - "0.12" Screen은?" → `screen`.
  - "참조 번호 76, 78 …은 글자 박스를 치나?" → 쉬운 버전에서는 글자 박스 없음. 1~20번 완전판이라면 번호는 `text_label`(tag_kind=patent_number).
  - "'PROCESS FLOW DIAGRAM' 세로 글자 박스는?" → 제목이므로 치지 않는다.
  - "Return flow와 Sludge Return 두 선" → 둘 다 엣지로. 매체는 자동(반응조로 돌아가면 반송 슬러지).
  - "번호 104, 132 작은 네모(글자 없음)는?" → `process_unit_generic` + l1_hint=unknown + label_text에 번호.
- 정리 한마디: "특허는 글자 대신 번호를 씁니다. 번호는 label_text에 그대로, 클래스는 generic. 단, 'Aerobic Tank'처럼 이름이 있으면 그 클래스."

### 연습 3 — EPA, 다단 소각로 흐름도 (슬러지 라인·가스 라인)

- 무엇이 보이나: Sludge Feed → Multiple Hearth Furnace → Furnace Exhaust → Heat Recovery Boiler → Precooler and Venturi → Wet Scrubber → Induced Draft Fan → Gas Exhaust; Ash; 팬 3개(Shaft Cooling Air, Combustion Air, Scrubber Water 펌프); Supplemental Fuel, Connected Power 등 외부 입력.
- 예상 질문과 답:
  - "소각로는?" → `drying_incineration_unit`(소각). visual_form=box(글자로 앎).
  - "Heat Recovery Boiler, Precooler/Venturi, Wet Scrubber는?" → 목록에 없는 장치 = `unknown_equipment` + l1_hint=sludge + 글자. (탈취·배기 처리 설비는 예비 클래스라 지금은 unknown.)
  - "팬(Induced Draft Fan, 공기 공급 팬)은?" → `blower`.
  - "Sludge Feed, Gas Exhaust, Ash, Supplemental Fuel, Connected Power, Scrubber Water, Drain은?" → 모두 플랜트 경계의 끝 = `io_terminal`. 역할: Sludge Feed = external_sidestream(다른 그림에서 옴) 또는 continuation, Gas Exhaust = off_gas_out, Ash = solids_disposal, Supplemental Fuel·Power·Scrubber Water = chemical_source에 가장 가까움(메모 남김), Drain = effluent.
  - "'Radiation', 'Recoverable Heat' 화살표는?" → 에너지 흐름. 장치가 아니고 물질 흐름도 아니므로 치지 않고 메모. (규칙에 없는 경우 → annotator_note.)
- 정리 한마디: "우리 목록은 수처리·슬러지 장치 중심이라 소각·배기 설비는 대부분 unknown_equipment입니다. 괜찮습니다. 글자만 정확히 적으면 나중에 분류합니다. 단자 역할이 애매하면 가장 가까운 것 + 메모."

### 연습 4 — 한국 지자체 제2하수처리장 공정도 (그림형, 병렬 2계열, 범례)

- 무엇이 보이나: 원수 → 침사지 및 유입펌프장 → 1단계(최초침전지 → 생물반응조 A2O(개량): 혐기조·무산소조·호기조, 내부반송 → 최종침전지) / 2단계(최초침전지 → 생물반응조 MLE: 탈질조·생물반응조 → 최종침전지) → 응집침전지 → 여과시설 → 소독시설 → 방류. 약품(PAC, NaOH, Alum, 음이온폴리머) 주황 화살표. 반류수처리시설, 연계처리시설, 드럼형농축기, 원심농축기, 소화조, 탈수시설 → 처분. 범례: 수처리계통(실선), 반류수계통(점선), 슬러지계통(일점쇄선).
- 예상 질문과 답:
  - "침사지 및 유입펌프장이 한 그림이다" → 바깥 전체를 `pump_station`, 안의 침사지 부분을 `grit_chamber` 자식으로(parent_of). 스크린이 보이면 `screen`도 자식.
  - "생물반응조 안 혐기조·무산소조·호기조" → 구역 셋(is_zone) + 생물반응조 전체 네모(process_unit_generic, l1_hint=secondary) + parent_of. 2단계 MLE의 탈질조 = anoxic_zone, 생물반응조 = aerobic_zone.
  - "1단계·2단계 두 계열" → 각각 전부 친다. 그림 속성 process_configuration에 "1단계 A2O(개량), 2단계 MLE"라고 원문을 적는다.
  - "응집침전지는?" → `secondary_clarifier`에 clarifier_stage=chemical…인데 쉬운 버전에는 그 칸이 없음 → 클래스 `secondary_clarifier`로 치고 label_text에 '응집침전지'. 앞의 응집 탱크가 그려져 있으면 `chemical_treatment_unit`.
  - "PAC·NaOH·Alum 주황 화살표" → 선: io_terminal(chemical_source) → 들어가는 지점 junction_merge. 탱크가 아니므로 장치 아님.
  - "반류수처리시설" → `sidestream_reactor`(반류수만 받음). "연계처리시설"(분뇨 등 반입) → 들어오는 끝 = io_terminal(external_waste_in)이고 시설 자체가 그려졌으면 unknown_equipment + 메모.
  - "드럼형농축기·원심농축기·소화조·탈수시설" → thickener(2개), digester, dewatering_unit. "처분" → io_terminal(solids_disposal).
  - "점선(반류수)과 일점쇄선(슬러지)" → 엣지에 style:dashed. 매체는 자동.
  - "범례 상자" → 치지 않는다.
  - "여과시설·소독시설" → filtration_unit, disinfection_unit. visual_form=pictorial.
- 정리 한마디: "한국 지자체 그림은 한 장에 다 들어 있어 길지만 규칙은 같습니다. 계열이 둘이면 둘 다, 약품은 선, 반류수는 sidestream_reactor."

### 연습 5 — OpenAlex, 유동상 반응기 파일럿 (단순 기호형)

- 무엇이 보이나: Influent → Oxygenation 박스 → Fluidized bed reactor(탑, 점 무늬 = 담체) → Biomass separation(원뿔 침전지) → Final effluent; Sludge; Recycled effluent가 Oxygenation으로.
- 예상 질문과 답:
  - "Fluidized bed reactor는?" → `biofilm_reactor/fluidized_expanded_bed`. 공기선(Oxygenation)이 있으니 호기(redox는 쉬운 버전 칸에 없음 → 메모 불필요).
  - "Oxygenation 박스는?" → 산소를 녹이는 장치. 목록에 없음 → `unknown_equipment` + l1_hint=secondary + 글자 'Oxygenation'. (aerator_mixer_symbol은 탱크 안 기호일 때만.)
  - "Biomass separation 원뿔은?" → 생물 반응기 뒤 침전지 = `secondary_clarifier`, visual_form=symbol(원뿔 모양), confidence=certain.
  - "Recycled effluent 선" → 침전지 → Oxygenation → 반응기로 이어지는 엣지 두 개. 매체 자동(처리수 순환).
  - "Sludge 화살표 끝" → io_terminal(solids_disposal).
  - "그림 속성" → B_symbol, en, 1.
- 정리 한마디: "파일럿 장치 그림은 단순하지만 세부형(L3)을 꼭 고르고, 목록에 없는 보조 장치는 unknown으로."

## 8. 마무리 (10분)

**말하기**
- "본 작업: A는 pilot_A, B는 pilot_B. 1번부터 순서대로. 1~20번은 화살촉·글자까지, 21~60번은 쉬운 버전. 번호를 꼭 확인하세요."
- "하루 30장 정도가 적당합니다. 피곤하면 멈추고 다음 날 이어서. Submit한 장은 저장돼 있습니다."
- "작업 중 서로 묻지 않습니다. 애매하면 annotator_note에 '몇 번 네모, 무엇이 애매'를 한 줄. 모아서 제가 봅니다."
- "끝나면 알려 주세요. Export는 제가 합니다."

**확인(마지막 퀴즈 5개, 요약 카드 보고 답해도 됨)**
1. 침전지 하부에서 반송과 잉여 슬러지가 갈라진다. 무엇을 치나? → junction_split + 엣지 2개.
2. 'Biological Treatment' 네모 → process_unit_generic, l1_hint=secondary, label_text.
3. 약품 화살표 → io_terminal(chemical_source) → junction_merge, 장치 아님.
4. 살수여상 → biofilm_reactor/trickling_filter(세부형 필수).
5. 점선 반류수 선 → 엣지 + style:dashed, 매체는 안 고름.

## 9. 진행자 메모: 자주 나오는 질문에 대한 답 원칙

- "규칙에 없다" → 가장 가까운 것 + annotator_note. 진행자도 즉석에서 새 규칙을 만들지 않는다(두 사람이 다르게 들을 수 있다). 모아서 v2에 반영.
- "이 장치가 뭔지 모르겠다" → 알 수 있는 범주(필터·막·탱크·펌프)면 그 클래스, 아니면 unknown_equipment + 글자. 추측으로 생물반응조 종류를 정하지 않는다.
- "그림이 너무 작다/흐리다" → 확대해서 보이는 만큼. 전혀 안 보이면 메모하고 넘어간다.
- "한 장에 도면이 둘" → graph_id로 g1, g2 구분.
- 연습 중 두 사람의 차이가 난 항목은 진행자가 표로 적어 둔다(장 번호, 네모, A의 선택, B의 선택, 규칙 번호). 파일럿 뒤 가이드라인 v2의 첫 재료가 된다.
