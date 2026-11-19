# WWTP 공정도 어노테이션 클래스 체계 설계안 (v1.1, 2026-11-16, 교과서 검토 + 최신 교과서·KDS 보강 반영)

> v0 → v1 변경 근거는 `taxonomy_textbook_review.md`에, v1 → v1.1(최신 교과서·KDS 61·한국 설계 자료) 변경은 §8에, 각 결정의 출처는 `evidence_ledger.md`의 ID로 추적한다.
> ID 체계: [D-nn] 우리 데이터, [T-nn] 선행연구·데이터셋, [S-nn] 표준·시뮬레이터, [B-nn] 교과서(IWA08·Olsson·GMP·ASM), [K-nn] 한국 자료, [B2-nn] 최신·주요 교과서, [M-nn] 방법론.

목적: main 벤치마크 993장(및 보조 세트)에 바운딩박스 어노테이션을 시작하기 전에, **무엇을 클래스로 둘 것인가**를
근거를 갖고 결정한다. 이 문서는 (1) 체계가 만족해야 할 요구조건, (2) 우리 데이터·선행연구·표준·하류 활용·교과서에서 얻은 근거,
(3) 그 근거에서 도출한 설계 원칙, (4) 제안 클래스 체계 v1, (5) 검증·확정 절차를 담는다.

---

## 1. 클래스 체계가 만족해야 할 요구조건

| # | 요구조건 | 이유 |
|---|---|---|
| R1 | 검출 모델이 **이미지만 보고** 구별할 수 있어야 한다 | 바운딩박스 클래스는 시각적 범주다. 눈으로 구별 안 되는 클래스는 학습이 안 되고 AP만 떨어진다 (Theisen 2023의 tank·IO·X 클래스가 그 예) [T-02] |
| R2 | 클래스가 **하수처리 공정의 단위공정(unit process)** 의미와 대응해야 한다 | 최종 목적은 도면 → 공정 그래프 → 시뮬레이션 모델 구조(ASM/BSM 계열) 자동 생성이다. 그래프 노드의 의미가 시뮬레이터 단위모델로 매핑되지 않으면 하류 활용이 막힌다 [S-03, S-04, B-02] |
| R3 | 각 클래스에 **학습 가능한 수의 인스턴스**가 있어야 한다 | 데이터셋 ~1,000장 규모에서 클래스당 수십 개 미만이면 학습·평가 모두 불안정하다 [T-02, M-02] |
| R4 | 도면 양식이 달라도(기호형·박스형·그림형·시뮬레이터 화면) **일관되게** 라벨링할 수 있어야 한다 | WWTP 도면은 화공 PFD보다 양식 편차가 크다 [D-01, S-01] |
| R5 | 연결 관계 복원에 필요한 **비장치 요소**(흐름선 방향, 텍스트, 유입·유출 표시, 분기·합류)를 포함해야 한다 | 선행 연구에서 흐름 방향 오류의 원인이 작은 화살표 미검출이었다. 연결 인식의 정량 평가가 우리의 차별점이다 [T-03] |
| R6 | 명칭이 **표준 어휘**를 따라야 한다 | 공개 벤치마크로 재사용되려면 EN 16323 / DEXPI / ISO 10628 / KDS 61 어휘와 호환되어야 한다 [S-01, S-02, S-05] |

---

## 2. 근거

### 2.1 우리 데이터: main 993장의 내용과 양식 [D-01 ~ D-05]

**출처 구성**: 특허 342, PMC 논문 325, OpenAlex 논문 178, EPA 매뉴얼 90, Wikimedia 36, 한국 지자체 22.
**카테고리**: wwtp 774, pilot 105, sludge 45, other 42, wtp 27.

**단위공정 용어 빈도** (캡션·제목에서 정규식으로 집계, 993장 기준; 캡션에 없는 장치는 과소집계됨) [D-03]:

| 용어군 | 건 | 용어군 | 건 |
|---|---|---|---|
| 포기조·생물반응조·활성슬러지·산화구 | 264 | 스크린 | 24 |
| MBR | 83 | 1차 침전지 | 19 |
| 무산소·혐기 구역, 질산화·탈질 | 75 | 탈수(원심·벨트·필터프레스) | 19 |
| 탱크·저류조 | 67 | SBR | 18 |
| 반송(RAS/WAS, recycle) | 60 | 인공습지·연못 | 17 |
| 모래·여재 여과 | 40 | 응집·침전 약품 | 16 |
| 살수여상·생물막(MBBR, RBC) | 38 | 바이오가스·CHP | 16 |
| 소화조 | 38 | 2차 침전지 | 14 |
| 소독(UV·염소·오존) | 34 | 침사지 | 12 |
| 펌프·펌프장 | 33 | 송풍기 | 12 |
| UASB·혐기성 반응기 | 32 | 유량조정조 | 10 |
| 막(UF/RO/NF) | 28 | 농축조 | 9 |
| DAF·부상 | 27 | 건조·소각 | 9 |
| 계측·제어 | 26 | 열교환기 | 1 |

후보 1,325장(main + aux_unit + crop_pending)에서 교과서 검토가 지적한 항목의 빈도 [D-04]: 반류수 처리 42, 계측·제어 52, 교대·간헐·상(phase) 운전 31, MBBR/IFAS 25, BAF 14, 살수여상 9, RBC 2, DAF 22, 응집·침전 26, 연못 19, 발효조 11, 밸브 14, 교반기 17, 산기 11, 산화구 11, 우회·월류 15, selector 3, 재포기 2, humus tank 0, step feed 1.

→ 생물학적 처리(포기조·무산소조·MBR·SBR·UASB·생물막)가 압도적이고, 침전지·여과·소독·슬러지 계통이 그다음이다.
화공 PFD의 핵심이던 열교환기·증류탑·압축기는 거의 없다. **Theisen의 47개 클래스는 그대로 쓸 수 없고, WWTP 전용 체계가 필요하다.**

**그림 양식 분포** (무작위 40장 수작업 분류, 중복 허용) [D-01, D-02]:

| 양식 | 장 | 특징 | 어노테이션에 주는 함의 |
|---|---|---|---|
| A. 텍스트 박스형(사각형 + 공정명) | 16 | 특허·중국어/한국어 논문·EPA 블록도. 장치 모양 정보가 **없고 텍스트만** 의미를 담음 | 검출기는 "공정 박스"만 찾을 수 있고 의미는 OCR이 결정 → **시각 클래스와 의미 클래스를 분리**해야 함 |
| B. 기호형(ISO 10628류: 침전지 원뿔·탱크 액면·막 모듈·펌프 원형) | 11 | 영문 논문·EPA 설계매뉴얼·일부 특허 | 기호 모양으로 클래스 구별 가능, 화공 PFD와 유사 |
| C. 그림형(3D 탱크·아이콘·색 일러스트) | 9 | 지자체 홍보, 교과서, 일부 논문 | 모양이 제각각, 텍스트 동반 → 의미는 텍스트·문맥 |
| D. 시뮬레이터 화면(BioWin, GPS-X, SUMO) | 2 | 아이콘이 소프트웨어마다 고정 | 소프트웨어별 아이콘 세트가 사실상 별도 "폰트" |
| E. 페이지 렌더·다중 패널(crop 필요) | 5 | 스캔 매뉴얼, 논문 페이지 | crop 후 A~D 중 하나 |

또한 40장 중 6장(15%)이 중국어·한국어·일본어 라벨이다. 텍스트 클래스와 다국어 OCR이 필수다.

### 2.2 선행 연구의 클래스 체계 [T-01 ~ T-07]

- **Theisen et al. 2023 (화공 PFD, 47 클래스, 1,005장, 17,411 객체)**. Zhang et al. 2019의 12개 단위조작을 세 규칙으로 분해했다. ① 장비 세부 유형별 분할(valve → 8종), ② 같은 장비의 **그림 양식별 분할**(tank1~4, pump1~3, hex 계열, col/col_aspen), ③ 도면 고유 기호 추가(IO 태그, 화살표, 텍스트, 스트림 태그 strm1~4, 제어기, mixer/splitter, unknown X) [T-01]. 결과: 자주 나오거나 양식이 일정한 클래스(col_aspen 90%, tank_gas 89%, blwr 88%)는 높고, 작은 기호(밸브류 45~65%, mix2 34%, strm3/4 36~41%)와 희귀·다양 클래스(tank 37%, IO 44%, X 46%)는 낮았다 [T-02]. **교훈**: 양식별 분할은 효과가 있지만 인스턴스가 충분할 때만이며, 작은 객체·희귀 클래스는 체계 설계로는 못 구하고 데이터·모델로 풀어야 한다.
- **P&ID 데이터셋들** [T-04 ~ T-07]: *Dataset-P&ID*(Paliwal 2021)는 합성 500장, 기호 32 클래스(이름 없이 Symbol_1~32); *Kim et al. 2022*는 76 라벨(장비 25 + 배관 33 + 계기 18), ISO 10628-2·PIP PIC001 참조; *PID2Graph*(Stürmer 2025)는 기호 **7 클래스만**(General, Pump/Compressor, Tank/Vessel, Instrumentation, Inlet/Outlet, Valve, Arrow) + 선 2종으로 GraphML 그래프 복원을 평가; *Elyan 2018 / Jamieson 2024*는 클래스 분해가 샘플링 기반 불균형 대응보다 우수함을 보임; *FC_A*(Awal 2011) 흐름도 7 클래스는 박스형 도면 검출의 선례.
- **2026년 신규 선행(학술 검토에서 추가, 원문 확인)** [T-08, T-09]: Yu & Zheng 2026 (*Chem. Eng. Res. Des.* 234:330) = 화공 PFD → Aspen Plus. 비공개 데이터 300여 장(Google·Baidu 이미지, 7,701 인스턴스), YOLOv11 mAP50 0.916, 선 복원 + 계층 잠금 방향 추론(화살표 → 장치 기하 규칙 → 수지 전파)으로 5장 206 연결 중 77.6 % 방향 결정, 수작업 그래프 정답 173 연결에서 **F1 0.771, 방향 정확도 0.968**; 재순환이 많은 도면은 미해결로 남겨 Aspen 생성은 3건만 성공. Sketch2Simulation(멀티모달 LLM 에이전트 → Aspen HYSYS, 연결 일관성 ≥ 0.93)도 같은 방향. 따라서 "도면 → 시뮬레이션 구조"는 더 이상 새롭지 않다. 우리 논문의 신규성은 (i) WWTP 도메인 최초의 **공개** 벤치마크(그들은 비공개·5장 평가), (ii) 박스 + 그래프 정답으로 재현 가능한 연결 복원 평가, (iii) 장치 기하 규칙이 아닌 **공정 순서·반송 사전지식**(유입 → 1차 → 2차 → 3차, RAS·내부반송·슬러지선 방향)에 의한 방향 추론과 ASM/BSM 단위모델 매핑, (iv) 반송(RAS·MLR·반류수)이 본질인 WWTP가 그들이 실패한 "재순환이 많은 도면"의 체계적 시험대라는 점으로 쓴다. 비교 기준값으로 F1 0.771 / 방향 결정률 77.6 % / 방향 정확도 0.968을 인용하고, VLM/LLM 에이전트를 기준 모델에 반드시 포함한다.
- **공통점**: 모두 "장치 클래스 + 연결 요소 클래스(선·화살표·텍스트·태그)"의 2계층 구조이고, 연결은 별도 알고리즘(픽셀 탐색 또는 그래프 모델)이 담당한다. P&ID는 ISA-5.1 표준 기호가 있어 기호 = 클래스가 성립하지만 WWTP PFD는 그렇지 않다(2.3).

### 2.3 기호·어휘 표준 [S-01, S-02, S-05]

- **ISO 10628-2:2012**: 29개 주제군 중 WWTP에 해당하는 것은 1 Vessels and tanks, 6 Filters, 7 Screening devices, 8 Separators, 9 Centrifuges, 12/28 Mixers·Agitators, 15 Liquid pumps, 17 Blowers/fans, 3 Heat exchangers. **침전지·포기조·소화조 전용 기호는 없다.** 기호형 도면에서도 저자마다 변형이 크다는 뜻이며, L3 양식 분할의 필요성을 뒷받침한다.
- **DEXPI (ISO 15926 기반, OPC 30250, 164 클래스)**: Equipment 계층에 **Separator·Clarifier·Blower·Centrifuge·Digester 클래스가 없다.** DEXPI로 내보내려면 WWTP 확장 클래스를 정의하고 Vessel/Tank 등 상위 클래스로 매핑해야 한다(4.3의 `dexpi_parent`).
- **어휘**: EN 1085:2007은 철회되었고 후속은 **EN 16323:2014**; 미국은 WEF MOP 8과 EPA Nutrient Control Design Manual; 한국은 **KDS 61 하수도 설계기준**(61 45 00 펌프장시설, 61 50 00 수처리시설, 61 55 00 찌꺼기(슬러지)처리시설). 클래스 영문명은 EN 16323/EPA 용어, 한글명은 KDS 61 용어를 따른다.
- WWTP 전용 공식 기호 표준(DWA/ATV 등)은 **없다.** 표준 기호 부재가 WWTP 도면 양식 편차(2.1)의 근본 원인이다.

### 2.4 하류 활용: 시뮬레이터 단위모델 [S-03, S-04]

- **BSM1/BSM2**: BSM1 = 활성슬러지 5칸(무산소 2 + 호기 3) + 2차 침전지 + 반송·내부순환. BSM2 = 1차 침전지 + 무산소 CSTR 2 + 호기 CSTR 3 + 2차 침전지 + 분기 + 농축조 + 혐기성 소화조(ADM1) + 탈수기 + 반류수 저류조.
- **GPS-X 단위 라이브러리**: Influent/Effluent · Flow(Splitter/Combiner/Pump) · Preliminary(Pumping Station, Equalization, Grit) · Primary(원형/사각 1차 침전지, 고속처리, 약품주입, 마이크로스크린) · Suspended growth(CSTR, Anoxic CSTR, Plug-flow, MBR, SBR, Oxidation Ditch) · Attached growth(TF, BAF, RBC, IFAS/MBBR, UASB, MABR, 입상슬러지) · Secondary clarifier(원형/사각) · Tertiary(여과, 막, 소독, AOP, RO) · Biosolids(DAF, Thickener, Dewatering, 소화, 건조, 소각) · Control. **SUMO** 도 같은 구성.
- **설계 결론**: 4.1의 L2 클래스는 GPS-X 분류와 **거의 동형**으로 설계했다. 분기·합류·유입·유출은 장치가 아니어도 노드 클래스로 둔다.

### 2.5 교과서 검토 (IWA08 · Olsson · GMP · ASM) [B-01 ~ B-31]

전체는 `taxonomy_textbook_review.md`. 핵심 결론: (a) 교과서 자체가 박스형으로 그린다(Olsson Fig 2.5) → 원칙 1 확정 [B-01]; (b) 모델링의 첫 행위는 격벽·산기관 구역을 따라 탱크를 CSTR 연쇄로 자르는 것(GMP Fig A.9) → 구역 박스 필수 [B-03]; 단 IWA08은 구역을 별도 상자로 그리고 산화구는 상자 없는 수로 → parent 없는 구역 허용 [B-04]; (c) "anaerobic reactor"가 EBPR 구역과 UASB 둘 다를 뜻해 v0 이름이 충돌 → 개명 [B-06]; (d) 약품 주입은 대부분 화살표이지 장치가 아님 [B-08]; (e) DAF는 슬러지 농축용 [B-09]; (f) 생물막·혐기성 반응기 세부형은 그림이 서로 다름 [B-10, B-11]; (g) 반류수 반응기·발효조·계측기·밸브·산기/교반 기호와 구역 역할·운전 방식 속성이 빠져 있었음 [B-13 ~ B-19]; (h) 스트림 유형이 교과서 어휘보다 거칠었음 [B-20, B-21]; (i) AOP는 독립 단위가 아님 [B-30].

### 2.6 최신·주요 교과서와 설계기준 (Metcalf & Eddy 5판 · IWA 2020 · WEF MOP 8 6/7판 · Grady 3판 · van Haandel · KDS 61 · EPA 2013) [B2-01 ~ B2-21], 한국 설계 자료 [K-01 ~ K-09]

로컬 교과서 4권(2008~2012)이 놓쳤을 수 있는 **최신 단위공정**과 **세계적으로 통용되는 명명**을 확인했다(상세 §8). 핵심 결론: (a) 다섯 참고서 모두 L1 골격(전처리 → 1차 → 생물 → 고도 → 소독 → 슬러지, 반류수 별도)을 같은 순서로 장 단위로 다룬다 [B2-01, B2-07, B2-13]; (b) 2014년 이후 새로 장 단위로 승격된 단위는 호기성 입상슬러지(AGS), MBR, 생물막 반응기, 반류수 처리·영양염 회수, 슬러지 개량(열가수분해), 1차 여과, 자연정화시설이며 [B2-04, B2-07, B2-08], 이 가운데 MBR·생물막·반류수 처리는 이미 L2이고, AGS·영양염 회수·개량(열가수분해)·1차 여과·오존/AOP는 우리 데이터에서 50장 미만이다 [D-03, D-06] → **예비 클래스**로 두고 속성·L3로 기록한다(§4.1b); (c) MLE·A2O·UCT 같은 "이름 붙은 공정"은 구역과 반송의 배치이지 장치가 아니다 [B2-10, B2-16] → 이미지 수준 속성 `process_configuration`; (d) KDS 61은 스크린·침사지를 펌프장시설에 두고, 슬러지 라인에 저류·개량·퇴비화 단계를 둔다 [B2-14, B2-15]; (e) 한국 설계 자료는 박스형 도면의 또 다른 관행(선 종류로 매체 구별, "#1~#4" 구역 번호, 기존/증설 병기)을 보여 주었다 [K-01, K-06, K-07].

---

## 3. 설계 원칙 (근거 → 원칙)

**P1. 의미 클래스와 시각 형태를 분리한다.** [D-01, B-01, B-02]
2.1의 양식 A(텍스트 박스형)가 40%로 가장 많고, 교과서의 전형적 공정흐름도도 기능 코드만 적은 동일 사각형 연쇄다. 박스 모양만으로는 "포기조"와 "소독조"를 구별할 수 없다. 따라서 어노테이션은 `semantic_class`(단위공정)와 `visual_form`(symbol / box / pictorial / simulator_icon / section_view)을 **별도 필드**로 기록한다. 어노테이터는 **항상 `semantic_class`를 적고**(박스형이면 `visual_form=box`, `confidence=inferred_from_text`), `process_unit_generic`은 텍스트가 없거나 번호뿐인 박스에만 쓴다. 검출 모델은 (a) semantic_class를 직접 학습하거나 (b) 공정 박스를 generic으로 검출한 뒤 OCR + 문맥으로 의미를 부여할 수 있고, 벤치마크는 둘 다 평가한다. (b) 트랙의 정답은 라벨을 다시 달지 않고 평가 시 `visual_form=box`인 박스를 generic으로 접어 자동 생성한다. 교과서 검토는 여기에 **모양만으로는 못 읽는 속성**(`aeration_mode`, `zone_role`, `operation_mode`)이 추가로 필요함을 보여주었다 [B-15, B-16, B-19].

**P2. 3단 계층으로 정의하되, 어노테이션은 가장 구체적인 단계(L2 또는 L3)에서 한다.** [M-01, M-02]
L1 = 기능 단계(preliminary / primary / separation / secondary / sidestream / tertiary / sludge / ancillary / generic / annotation), L2 = 단위공정(31개 + generic 2개), L3 = 세부형·양식 변형(Theisen 규칙 ①·②; 생물막·혐기성 반응기는 필수, 그 외는 인스턴스 ≥ 150일 때). 평가는 L2에서 하고, L1으로 접어 올리면 희귀 클래스도 포함한 안정적 지표를 얻는다. 근거: Open Images는 객체를 가장 하위(leaf) 라벨로만 라벨링하고 평가 시 정답을 모든 상위 클래스로 확장해 mAP를 계산한다. LVIS는 학습 이미지 수로 rare(1~10장) / common(11~100장) / frequent(>100장)를 나눠 따로 보고한다.

**P3. 독립 클래스가 되려면 세 조건을 모두 만족해야 한다.** [T-02, M-02, S-03]
① 시각적 구별 가능성(기호형에서 모양 차이가 있거나, 박스형에서는 텍스트로만 구별되므로 L2 의미 클래스로만 존재), ② 예상 인스턴스 ≥ 50(학습) + ≥ 20(평가) — Theisen에서 35개뿐인 blower는 모양이 독특해 AP 88%였지만 양식이 다양한 tank·IO·mix2는 수백 개여도 34~44%였다; Ultralytics 권고(클래스당 이미지 ≥ 1,500)는 우리 규모에서 불가능하므로 LVIS의 common 구간(11~100장) 이상을 목표로 하고 rare 구간은 repeat factor sampling(t = 0.001)으로 보정한다, ③ 하류 매핑 필요성(시뮬레이터 단위가 다르면 분리, 같으면 병합). 조건 ②를 못 채우는 클래스는 상위 L2/L1로 병합하고 `attribute`로만 남긴다.

**P4. generic 클래스와 unknown 클래스를 둔다.** [T-02, B-01]
`process_unit_generic`(단위공정이지만 종류 미상·박스형)과 `unknown_equipment`(X)를 두어 롱테일을 흡수한다. 없으면 어노테이터가 억지로 다른 클래스를 고르게 되어 일관성이 깨진다.

**P5. 연결 요소는 장치와 같은 수준의 클래스로 둔다.** [T-03, T-04, B-17, B-20, B-22]
`arrowhead`, `text_label`, `stream_tag`, `stream_label`, `io_terminal`, `junction_split`, `junction_merge`, `instrument`. 흐름선 자체는 바운딩박스 대상이 아니라 픽셀 탐색 또는 그래프 모델의 대상이며, 연결 정답은 별도 그래프 라벨(노드 id 쌍 + 방향 + 스트림 속성)로 기록한다.

**P6. 구역(zone)은 반응조의 자식 노드다.** [B-03, B-04, B-05]
한 탱크의 혐기·무산소·호기 구역은 각각 박스(`is_zone=true`)로 치고, 탱크 윤곽이 그려졌으면 parent 박스를 두며(`parent_id`), 구역이 별도 상자로 그려졌거나 산화구처럼 수로 구간만 있으면 parent 없이(`parent_id=null`) 인접성으로 묶는다. 시뮬레이터는 구역 단위(CSTR)로 모델을 만들기 때문이다.

**P7. 명칭과 정의는 표준·교과서 어휘를 따르고, 한 클래스에 한 문장 정의 + 포함·제외 예 + 별칭을 둔다.** [S-05, B-06, B-07, B-27]
클래스마다 영문명(EN 16323/EPA/IWA08 선호어), 한글명(KDS 61), 정의, 포함 예, 제외 예, 양식별 대표 그림 3종을 둔다.

---

## 4. 제안 클래스 체계 v1

### 4.1 L1 → L2 단위공정 클래스 (33개 = 단위공정 31 + generic 2) 및 근거

| L1 | L2 class (영문 / 한글) | 정의·포함 (별칭) | 판별 단서 | 하류 단위 (GPS-X / BSM2) | 근거 | 예상 빈도* |
|---|---|---|---|---|---|---|
| preliminary | `screen` / 스크린 | 조목·세목·드럼·스텝 스크린 | 빗살·격자 | Screen / – | S-01, S-03 | 중 |
| preliminary | `grit_chamber` / 침사지 | 침사지, 포기식 침사지 | 긴 수로형 상자 | Grit Chamber / – | S-03 | 중 |
| preliminary (위치 무관) | `equalization_tank` / 유량조정조 | 유량·수질 조정조, 완충조, 우수(storm)·체류(detention) 조; 한국 교재는 2차 침전 뒤에도 둠 | 액면 있는 큰 탱크 | Equalization Tank / storage | B-28, K-03 | 중 |
| preliminary (위치 무관) | `pump_station` / 펌프장(유입·중계·방류 펌프장) | wet well + 펌프 여러 대(+ 월류); 단독 펌프 기호는 `pump`; 한국 도면의 "유입펌프장" 상자가 스크린·침사지를 품으면 parent로 둔다; 중계·방류·반송 펌프장도 같은 클래스 | 펌프 원형 + 수조 | Pumping Station / – | B-28, B2-14 | 중 |
| primary | `primary_clarifier` / 1차 침전지 | 1차·최초 침전지(primary sedimentation tank, primary settler); Imhoff·septic tank은 하위 태그 `imhoff_septic` + `multi_unit=[primary_clarifier, digester]`; CEPT·ballasted·다층식·1차 여과는 `primary_enhancement`, 형상은 `clarifier_shape` | 원뿔 바닥, 사다리꼴 단면; 슬러지가 농축조로 가고 반송선 없음 | Primary Clarifier / primary clarifier | S-04, B-25, B2-03, B2-13 | 중 |
| separation (위치 무관) | `flotation_unit` / 부상조 | DAF, 부상 분리; `function ∈ {primary, secondary_separation, tertiary, thickening}` (총인처리시설의 부상조 = tertiary) | 거품·기포 표기 | DAF / – | B-09, K-05 | 중 |
| separation (위치 무관) | `chemical_treatment_unit` / 약품 처리조 | 응집·응결·침전 **탱크**만. 약품 공급원은 `io_terminal(role=chemical_source)`, 단위로 들어가는 지점은 `junction_merge(chemical_dosing_point)`; 후침전지는 `secondary_clarifier(clarifier_stage=chemical)` | 교반기 + 약품 탱크 | Chemical Dosage / input model | B-08 | 중 |
| secondary | `aerobic_zone` / 호기조(포기조) | 호기성 활성슬러지 구역; 별칭 aeration tank/basin, aerator, aerobic reactor, Deep Shaft, 순산소(HPO) 밀폐 반응조(`aeration_mode=hpo`), swing zone(`zone_role=swing`); **산화구·Carrousel·Orbal**은 한 박스 + `is_loop_reactor=true`이며 산기기 위치로 호기/무산소 구간이 표시되면 자식 구역을 친다; 입상·밀집 슬러지는 `biomass_form`; 안에 든 MABR 카세트·담체 케이지는 자식 `biofilm_reactor`(규칙 13) | 기포·산기관·표면 포기기 | CSTR aerobic, Oxidation Ditch / aerobic CSTR | B-05, B-06, B-07, B-27, B2-03, B2-20 | **상** |
| secondary | `anoxic_zone` / 무산소조 | 탈질 구역(질산염 있음, O2 없음): 전무산소(MLE·A2O·UCT의 a 반송 수용), RAS 전용 전무산소(JHB `zone_role=underflow_anoxic`), 후무산소(Bardenpho `zone_role=post_anoxic`, 외부 탄소원 주입이 단서) | 교반기만; 질산염 반송(a) 또는 RAS가 들어옴 | Anoxic CSTR / anoxic CSTR | B-04, B-05, B-06 | 상 |
| secondary | `anaerobic_zone` / 혐기조 | EBPR 인 방출 구역(O2·질산염 없음), RAS를 받는 P-stripper(`zone_role=stripper`) | 교반기만(무산소조와 같은 모양); 유입수를 **가장 먼저** 받는 교반 구역이고 그 뒤에 또 다른 교반 구역(무산소)이 있음. A2O는 +RAS, UCT는 +r 반송(무산소→혐기), JHB는 앞에 RAS 전용 무산소조가 있음; 규칙 1의 판별표 | CSTR (anaerobic) / – | B-04, B-06, B-15 | 중 |
| secondary | `secondary_clarifier` / 2차 침전지 | 2차·최종 침전지(SST, final settling tank, final settler), humus tank, 2단 생물처리 사이의 중간 침전지(`clarifier_stage=intermediate`), 후침전지(`clarifier_stage=chemical`) | 원뿔 바닥 + 하부에서 상류 반응조로 되돌아가는 RAS 선 | Secondary Clarifier / secondary clarifier | B-25, B-26, B2-06 | 상 |
| secondary | `mbr_unit` / 막분리 생물반응조 | 침지식(iMBR)·외부식(sMBR) 막 모듈(막조); 혼합액을 받고 슬러지를 반응조로 되돌림. 생물반응조 구역은 따로 `*_zone`으로 친다; 박스형에서 "MBR" 한 상자만 있으면 `mbr_unit` + `multi_unit=[aerobic_zone, mbr_unit]` | 막 카세트 빗살 | MBR / – | B-32, B2-04 | 상 |
| secondary | `sbr_tank` / 연속회분식 반응조 | fill/react/settle/decant; 다중 패널은 패널마다 1단위 + `panel_phase`; AGS(Nereda형)는 `biomass_form=granular` | 수위 표기, 디캔터 | SBR / – | B-16, B2-04 | 중 |
| secondary (3차 위치 허용) | `biofilm_reactor` / 생물막 반응기 | **L3 필수**: trickling_filter, rbc, submerged_biofilter(BAF/SAF, 접촉산화, **탈질 여과(denitrification filter)** 포함), mbbr_ifas("MBBR / IFAS (hybrid)"), fluidized_expanded_bed(← airlift_fluidized_granular), mabr; 생물막도 redox가 다르므로 `redox_condition ∈ {aerobic, anoxic, anaerobic, unknown}`(후탈질 MBBR·탈질 여과 = anoxic, 질산화 살수여상 = aerobic); 탱크 전체가 담체로 차 있으면 한 박스, 포기조 안의 카세트·케이지만 그려졌으면 `aerobic_zone`의 자식 | 여재·캐리어·디스크·3상 분리기 | TF / BAF / RBC / IFAS-MBBR / – | B-10, D-04, B2-07, B2-10, B2-13, B2-20 | 중 |
| secondary (전처리 위치 허용) | `anaerobic_wastewater_reactor` / 혐기성 폐수 반응기 | **L3**: uasb_egsb_ic, anaerobic_filter, anaerobic_contact, anaerobic_cstr, abr, anaerobic_mbr; `multi_unit` 매핑; 활성슬러지 앞의 UASB(anaerobic pretreatment)도 같은 클래스 | 상향류, GLSS·가스돔, 바이오가스선 | UASB / – | B-06, B-11, B-12, B2-11, B2-17 | 중 |
| secondary | `pond_lagoon_wetland` / 연못·라군·인공습지(자연정화시설) | 안정화지, 라군, 인공습지; 하위 태그 `pond_type ∈ {anaerobic, facultative, aerated, maturation, wetland_surface, wetland_subsurface, unknown}` | 식물 그림, 흙 단면 | lagoon / – | B-27, B2-07, B2-10 | 하 |
| sidestream | `sidestream_reactor` / 반류수 처리 반응기 | 별칭 plant recycle flow treatment. 물리적으로는 CSTR·SBR·입상 반응기와 같으므로 **공급 스트림만이 판별 기준**: 유일한 공급이 탈수여액·소화 상징수(reject water, centrate)이면 이 클래스, 본류도 받으면 `*_zone`(규칙 20). **L3(선택)**: nitritation_denitritation(SHARON), deammonification_anammox(Anammox·CANON·DEMON·ANITA-Mox), bioaugmentation(BABE·BAR·InNitri), nutrient_recovery(스트루바이트·암모니아 스트리핑) | 공급선이 탈수·소화 반류수 | – / – | B-13, D-04, B2-01, B2-08, B2-17 | 하~중 |
| tertiary | `filtration_unit` / 여과 | 모래·여재·디스크·섬유·마이크로스크린 여과(3차 위치); **L3(선택)** activated_carbon(GAC/BAC 흡착); 공기 공급선 또는 탄소원 주입선이 있으면 생물여과(`biofilm_reactor/submerged_biofilter`) | 여재층 패턴 | Sand/Disc Filter / – | B-10, B2-07, D-06 | 중 |
| tertiary | `membrane_unit` / 막 여과 | MF/UF/NF/RO(`membrane_type`); 처리수를 받음(혼합액을 받으면 `mbr_unit`) | 원통 막 모듈 | Membrane Filter / RO / – | B-32 | 중 |
| tertiary | `disinfection_unit` / 소독 | UV, 염소 접촉조, 탈염소, 오존·AOP·PAA; `disinfectant`, `purpose ∈ {pathogen, micropollutant}` 속성 | 램프·접촉 수로 | UV / Chemical Disinfection / – | B-30, B2-08, B2-13, D-06 | 중 |
| sludge | `fermenter` / 1차 슬러지 발효조 | prefermenter(VFA 생산); 발효액(`stream_role=fermentate`)이 **본류 혐기조·무산소조로** 감. 산발효조 유출이 메탄 소화조로 가면 `digester(digester_type=acid_phase)`(규칙 21); 50개 미만이면 거기에 병합 | 소화조와 유사, 1차 슬러지 공급 | – / – | B-14, D-04, B2-10 | 하 |
| sludge | `thickener` / 농축조 | 중력·기계(원심·벨트(GBT)·드럼·디스크) 농축; 부상 농축은 `flotation_unit` | 슬러지 라인의 작은 원뿔 탱크(상징수가 반류); 벨트·드럼 장치는 소화조 **상류** | Thickener / thickener | B-28, B2-15 | 중 |
| sludge | `digester` / 소화조 | 슬러지가 공급됨; `digester_type ∈ {anaerobic, aerobic, atad, two_stage, acid_phase, thp_fed}`, `co_digestion` 속성(분뇨·음식물폐수·FOG 연계, `stream_role=co_substrate`); 석회 안정화는 `chemical_treatment_unit(treatment_line=sludge)` | 달걀형·돔형 | Anaerobic/Aerobic Digestion / ADM1 digester | B-12, B-29, B2-10, B2-15 | 중 |
| sludge | `dewatering_unit` / 탈수기 | 원심·벨트·스크류·필터프레스·**건조상(drying bed)·갈대상·슬러지 라군**; 슬러지 라인의 "Filter"; 산물이 케이크(`stream_role=dewatered_cake`); 약품 개량 주입은 화살표(`chemical_dosing_point`) | 드럼·롤러; 소화조 **하류** | Dewatering / dewatering | B-28, B2-15 | 중 |
| sludge | `drying_incineration_unit` / 건조·소각·퇴비화 | 열건조기·소각로·퇴비화·열분해/가스화(`final_process` 속성); 자연 건조상은 `dewatering_unit` | 불꽃·굴뚝 | Sludge Drying / Incinerator / – | B-29, B2-07, B2-15 | 하 |
| sludge | `biogas_unit` / 바이오가스 설비 | 가스홀더, 플레어, 엔진/CHP, 보일러, H2S 제거 | 구형 홀더·엔진 | – / gas storage | B-29 | 하 |
| ancillary | `pump` / 펌프 | 단독 펌프 기호; 약품 펌프 = `pump` + `stream_role=chemical_dose` | 원 + 삼각 | Pump / – | B-28 | 중 |
| ancillary | `blower` / 송풍기·압축기·팬 | 공기 공급 기계 | 사다리꼴·팬 | – / – | B-18, B-19 | 하 |
| ancillary | `storage_tank` / 저류 탱크 | 처리수·방류·슬러지(저류조)·반송슬러지·약품 저류(공정 기능 없음); `treatment_line`으로 구분 | 액면 탱크 | Storage / – | B-28, B2-07, B2-15 | 중 |
| ancillary | `valve` / 밸브 | 모든 밸브 기호(세부형 없음) | ISO 밸브 기호 | – / – | B-18, T-02 | 하 |
| ancillary | `aerator_mixer_symbol` / 산기·교반 기호 | 표면 포기기, 브러시, 산기관 열, "M" 교반기(탱크 안 기호) | 기호 자체 | – / aeration sub-model | B-19 | 중 |
| generic | `process_unit_generic` / 공정 단위(종류 미상) | **텍스트가 없거나 번호뿐**(특허 "412", 한국 "#1~#4")이어서 어노테이터도 L2를 못 정하는 공정 박스. 텍스트로 L2를 읽을 수 있는 박스형 도면은 해당 L2 + `visual_form=box` + `confidence=inferred_from_text`로 적는다(규칙 15) | 사각형 + 번호/무표기 | (문맥 추론 후 매핑) | B-01, D-01, K-06 | 중 |
| generic | `unknown_equipment` / 기타 장치 | 그 외 장치. 가이드라인에 명시할 예: 방류 전 후포기(post-aeration cascade), 탈취·스크러버(예비 클래스 `odor_control_unit`), 열교환기·보일러, 협잡물 세척기·침사 분급기, 하이드로사이클론, 약품 제조조; 모두 `label_text` 필수 | — | — | T-02, D-07 | 하 |

\* 등급: 상 ≥ 200, 중 50~200, 하 < 50 인스턴스 추정 [D-03, D-04]. **v0 대비**: 개명 4(`aeration_tank`→`aerobic_zone`, `anoxic_tank`→`anoxic_zone`, `anaerobic_tank`→`anaerobic_zone`, `anaerobic_reactor`→`anaerobic_wastewater_reactor`), 추가 4(`sidestream_reactor`, `fermenter`, `valve`, `aerator_mixer_symbol`), 병합 1(`advanced_oxidation_unit`→`disinfection_unit`), 위치 무관화 2(`flotation_unit`, `chemical_dosing`→`chemical_treatment_unit`), L3 필수화 2(`biofilm_reactor`, `anaerobic_wastewater_reactor`), 개명 1(`constructed_wetland_pond`→`pond_lagoon_wetland`). 하 등급 7개(`pond_lagoon_wetland`, `fermenter`, `drying_incineration_unit`, `biogas_unit`, `blower`, `valve`, `unknown_equipment`)는 파일럿 후 병합 후보.
**v1 → v1.1** [§8.2]: L2 수는 33개(단위공정 31 + generic 2)로 유지. (v0·v1 문서의 "28개"·"30개"는 generic을 빼고 센 값과 집계 오류가 섞인 것이라 v1.1에서 표의 실제 행 수로 정정.) 개명 1(L3 `airlift_fluidized_granular` → `fluidized_expanded_bed`), L3 추가 6(`anaerobic_mbr`; `sidestream_reactor` 선택 L3 4종; `filtration_unit/activated_carbon`), 별칭 보강(primary/final settler, SST, swing zone, plant recycle flow treatment, 접촉산화, 자연정화시설), 위치 허용 1(`anaerobic_wastewater_reactor` 전처리 위치), 속성 추가 8(§4.4), 예비 클래스 6(§4.1b), 판별 규칙 9개 추가(§4.5 11~19), 그래프 정답 스키마 신설(§4.6). **v1.1b — 파일럿 절차 변경(2026-11-18, 라벨링 시작 전 기록; 체계 불변)**: 어노테이터 부담(장당 약 60클릭, 15분)을 줄이기 위해 파일럿을 **쉬운 버전 60장 + 완전판 부분집합 20장(1~20번)** 으로 바꿈. ① 21~60번은 `arrowhead`·`text_label`·`stream_tag`·`stream_label` 박스 생략(1~20번은 전부) → 화살촉·글자 클래스의 사람 일치도·사람 상한은 20장 기준으로 보고. ② 엣지는 방향만 긋고 예외 라벨(`no_arrow`, `direction_unknown`, `style:dashed`, `optional`, `parent_of`)만 선택; `medium`·`stream_role`은 `s19_infer_edge_medium.py`가 규칙표(`annotation/edge_medium_rules.md`, 31개 규칙; 살수여상 순환·발효액·탈수기 두 갈래 예외 포함)로 채우고 판정자가 1~20번에서 직접 단 값과 비교해 규칙 정확도를 보고(사람 상한 지표에서 매체 제외). ③ T2 속성 칸은 파일럿 화면에서 숨김(본 작업 첫 100장에서 검증). ④ `label_text`는 generic·unknown 박스만 필수. ⑤ OCR 사전 라벨링은 설치 시 글자 클래스에만 적용하고 수정 비율 보고. 설정 `annotation/label_studio_config_lite.xml`, 매뉴얼 `manual/WWTP_annotation_manual_v1_lite.pdf` + 요약 카드. ⑥ (2026-11-19, 합성 라벨 예행연습 `s21`에서 확정) 일치도 계산의 노드 매칭은 IoU ≥ 0.5 탐욕 매칭에 더해, **둘 다 이미지 면적 0.2 % 미만인 작은 박스**(분기·합류·화살촉·밸브)는 중심 거리(큰 쪽 박스의 긴 변 이내)로 보조 매칭한다 — 작은 박스는 몇 px 차이로 IoU 0.5가 깨져 "누락+추가"로 이중 계상되기 때문. 보조 매칭 쌍은 IoU ≥ 0.7 비율에서 제외. 모델 평가(§6)의 매칭 규칙은 그대로 IoU ≥ 0.5. 중복으로 그린 관계는 하나로 합침; 매체 규칙 32·33(전처리→본류 influent, 2차 침전지→3차 effluent) 추가. **v1.1a — 파일럿 중 보정(2026-11-17, 동결 후 변경 이력; 클래스 수 불변)**: ① 파일럿 1번 그림(EPA Wet Weather Treatment Train)의 "Biological Treatment"·"Preliminary Treatment" 박스는 단계 이름이라 L2를 못 정하는데 generic으로 적으면 L1 정보까지 사라짐 → generic·unknown 박스에 `l1_hint` 속성(T1) 추가, 규칙 15 확장. ② 같은 그림의 "To Solids Processing"처럼 다른 그림·단계로 이어지는 끝 → `io_role=continuation` 추가(규칙 19). ③ "(Optional)"·점선 대안 경로를 엣지에 못 적던 것 → 엣지 `optional` 플래그와 Label Studio 관계 추가 라벨 `style:dashed/dotted`, `optional`(§4.6 `line_style` 보완). ④ `visual_form` box/symbol 판정 기준을 명문화(규칙 15b). ⑤ `graph_id`를 박스 선택지로 제공. **학술·저널 검토(2026-11-16)** 에서 더한 것: §4.5b 필수·조건부·선택 필드 3층(평가는 T1만), §5.0 동결·사전 등록, §5.1 어노테이터 구성·판정자·일치도 통계(부트스트랩 CI, 클래스별 ≥ 20 조건)·사람 상한, §6 계층 평가 규칙·LVIS 구간·층화 보고·체계 ablation 4종·기준 모델·round-trip 하류 검증·datasheet·AI 선별 recall 추정·"최초" 주장 근거, 선행 T-08·T-09 추가. **v1.1 최종 검토(2026-11-16, 독립 검토 포함)** 에서 고친 것: 박스형 도면도 의미 클래스를 단다는 원칙 확정(P1·규칙 15, generic은 무표기·번호 박스로 한정), 침전지·조정조 위치 규칙(14), 부상 농축 vs 농축조(16), P-stripper(17), 선 텍스트 3종(18), io_terminal 범위(19), 혐기조 시각 단서 정정, 선택 L3 = 하위 태그로 지위 정의, 패널·계열 속성을 박스 수준으로 이동, D-01·D-06 수치 정정. **도메인 전문가 검토(2026-11-16)** 에서 고친 것 [D-07]: 규칙 1을 A2O 중심 휴리스틱에서 **공정 구성 판별표**(CAS·MLE·A/O·A2O·UCT·JHB·Bardenpho)로 교체; `anoxic_zone`에 전/후/RAS 전용 무산소 구분(`post_anoxic` 추가); 생물막 반응기에 `redox_condition`(후탈질 MBBR·탈질 여과)과 규칙 2 보강; 규칙 3·13의 담체 라벨 충돌 해소; 농축/탈수 장치는 소화조 기준 상·하류로(GBT 오분류 방지); 건조상은 탈수로; 발효조 vs 산발효 소화조(규칙 21); 반류수 반응기는 공급 스트림만으로 판별(규칙 20); 산화구 규칙(22); 중간 침전지·MF·HPO·jet 값; 스트림 역할 8종(scum, screenings_grit, reclaimed_water, dewatered_cake, off_gas, oxygen, carbon_source, 상징수 명시)과 `io_terminal` 반입·고형물 반출 역할; Imhoff·"MBR 한 상자"의 `multi_unit`; 펌프장 위치 무관; 예비 클래스 `odor_control_unit`(7개째); `unknown_equipment` 명시 예 목록.

### 4.1b 예비 L2 클래스 (reserve; `classes.yaml`에 `active: false`로 등재) [B2, D-06]

최신 교과서·기준에서 **장 또는 기술 단위**로 승격됐지만 우리 데이터에서 조건 ②(≥ 50 학습 인스턴스)를 못 채우는 단위. 지금은 아래 "현재 라벨" 규칙으로 기록하고, 파일럿·본 어노테이션 집계에서 50개를 넘기면 L2로 활성화한다(속성에 이미 정보가 있으므로 재라벨링 없이 변환 가능).

| 예비 클래스 | 근거(최신 자료) | 데이터 [D-06] | 현재 라벨 방법 |
|---|---|---|---|
| `granular_sludge_reactor` 호기성 입상슬러지 반응조 | IWA20 11장 전용 [B2-04]; EPA13 AGSP [B2-17]; 국내 AGS-SBR [B2-16]; 밀집 활성슬러지 [B2-19]; GPS-X 단위 있음 [S-03] | 16장 | `sbr_tank` 또는 `aerobic_zone` + `biomass_form=granular/densified` |
| `sludge_conditioning_unit` 슬러지 개량(약품·세정) + 열 전처리(열가수분해) | MOP8-6 20장 Chemical Conditioning(약품만)과 24.2 "Thermal Conditioning and Pretreatment"·23.2.4 Pretreatment [B2-07, B2-22]; KDS 61 55 00 6절(세정·약품·열처리) [B2-15]; ME5 13장 [B2-02, 미확인] | 7장(열가수분해 0) | 약품 개량은 `junction_merge(chemical_dosing_point)`; 열가수분해 반응기는 `process_unit_generic` + `label_text` + `treatment_line=sludge` |
| `nutrient_recovery_unit` 영양염 회수(스트루바이트·암모니아 스트리핑) | ME5 15장 제목 [B2-01]; MOP8-7 [B2-08]; EPA13 [B2-17] | 4장 | `sidestream_reactor/nutrient_recovery` |
| `primary_filter` 1차 여과(회전 벨트·압축 여재) | MOP8-7 "Emerging primary filtration" [B2-08]; EPA13 Salsnes·CMF [B2-17] | 0장 | 침전지 모양이면 `primary_clarifier` + `primary_enhancement=primary_filter`; 여과기 모양이면 `filtration_unit` + `label_text`(1차 위치는 그래프 위치에서 복원) |
| `adsorption_oxidation_unit` 오존·AOP·활성탄 고도처리(재이용) | MOP8-6 14장 [B2-07]; KDS 7.7 [B2-13]; 국내 "+ 오존" [B2-16]; GPS-X에 AOP 단위 있음 [S-03] | 오존 13·AOP 17·활성탄 31(중복 있음) | 흡착은 `filtration_unit/activated_carbon`; 오존·AOP는 `disinfection_unit(disinfectant=ozone/aop, purpose=micropollutant)` [B-30 유지] |
| `hydrocyclone` 물리 선별기 | *Water Research* 2024, WRF 5130 [B2-19] | 1장 | `unknown_equipment` + `label_text` |
| `odor_control_unit` 탈취·악취방지 설비(스크러버·바이오필터·활성탄 탑) | KDS 61 50 00 12절 "악취방지 및 탈취설비" [B2-13]; MOP8-6 6장 Odor and Air Emissions [B2-07]; 한국 지자체 도면에 흔함 | 12장 | `unknown_equipment` + `label_text`; 연결 엣지는 `medium=gas`, `stream_role=off_gas` |

### 4.2 연결·주석 클래스 (8개)

| class | 정의 | 속성 | 근거 |
|---|---|---|---|
| `arrowhead` | 흐름선 끝 화살촉 | — | T-03 |
| `text_label` | 장치명·구역명·설계치 텍스트 블록 | `tag_kind ∈ {name, volume, depth, equipment_count, hrt, spec, material, capacity, patent_number, other}` | B-24, K-08 |
| `stream_tag` | 스트림 번호·유량·농도·분기 비율·부하·수질·수리 값 | `tag_kind ∈ {stream_no, flow, fraction, concentration, loading, performance, quality, hydraulic, other}` | B-24, K-08 |
| `stream_label` (← recycle_marker) | 선 위·옆의 스트림 이름(RAS, a, s, r, WAS, reject water …) | `stream_role` (4.4) | B-20 |
| `io_terminal` | 플랜트 경계의 유입·유출·외부 반출·반입·약품 공급 | `role ∈ {raw_influent, settled_influent, external_waste_in(분뇨·음식물폐수·정화조 반입), effluent, reclaimed_water_out, solids_disposal(케이크·협잡물·침사·재), biogas_use, off_gas_out, chemical_source, overflow_bypass_out, external_sidestream}` | B-24, B2-15, D-07 |
| `junction_split` | 분기점(선만 갈라지는 지점 + 그려진 분배조·Divider; 분배조가 구조물로 그려졌으면 박스는 그 구조물을 감싼다) | `split_type ∈ {ratio, fraction, pumped, bypass, router_alternating, pacing, unknown}` | B-22, K-03 |
| `junction_merge` | 합류점 | `merge_role ∈ {step_feed_inlet, sidestream_return, chemical_dosing_point, recycle_return, lane_combiner}` | B-22, B-24 |
| `instrument` | 센서·분석기·제어기 기호 또는 태그(DO, NH4, pH, F, L …) | `measured_variable`(자유 텍스트), `instrument_role ∈ {sensor, analyser, controller, setpoint}` | B-17, T-04, T-05, D-04 |

### 4.3 표준 매핑 필드

`classes.yaml`에 L2(및 L3)마다 **`qsdsan_unit`**(S-06, 오픈소스 1순위: CSTR / ActivatedSludgeProcess / FlatBottomCircularClarifier·IdealClarifier·PrimaryClarifier / AnaerobicCSTR·AnaerobicDigestion·AnaerobicBaffledReactor·AnMBR / MembraneBioreactor / Thickener·Centrifuge 등), `gpsx_unit`(S-03), `sumo_unit`(SUMO 단위명; 연구실 보유), `bsm_unit`(GMP Table 5.3.2 어휘로 제한: CSTR / point·ideal·layered clarifier / splitter type / input model / primaries / digester / sludge handling [B-02, S-04]), `dexpi_parent`(S-02: 없는 클래스는 확장명 + 상위 Vessel/Tank), `iso10628_group`(S-01), `kds61_term`(S-05), `multi_unit`(B-11: UASB = primary_clarifier + reactor + secondary_clarifier + digester)을 둔다. QSDsan에 없는 단위(살수여상·RBC·MBBR·연못·UV 등)는 `qsdsan_unit=null`로 두고 round-trip 검증에서 "매핑 불가" 건수로 보고한다. 그래프를 SFILES2·DEXPI·GPS-X 입력으로 바꾸는 단계에서 추가 매핑 표가 필요 없게 된다.

### 4.4 어노테이션 속성(필드)

- **L3의 지위**: 필수 L3(`biofilm_reactor`, `anaerobic_wastewater_reactor`)만 평가 클래스다. "선택 L3"(`sidestream_reactor` 4종, `filtration_unit/activated_carbon`, 침전지 형상 등)는 평가 클래스가 아니라 라벨에 기록만 하는 **하위 태그**이며, 인스턴스 ≥ 150이 되면 평가 L3로 승격한다. v1 검토안의 침전지 L3(circular/rectangular/vertical/lamella)와 MBR L3(immersed/sidestream)는 v1.1에서 `clarifier_shape`·`mbr_config ∈ {immersed, sidestream, unknown}` 속성으로 통일했다 [B-25, B-32, M-02].
- **박스**: `semantic_class`, `visual_form ∈ {symbol, box, pictorial, simulator_icon, section_view}`(symbol = 모양이 종류를 말해 줄 때만; 글자 달린 원·네모는 box), `label_text`, `confidence ∈ {certain, inferred_from_text, inferred_from_context}`, **`l1_hint ∈ {preliminary, primary, secondary, tertiary, sludge, sidestream, unknown}`**(generic·unknown 박스 필수; v1.1a), `is_zone` + `parent_id`(null 허용 [B-04]), `is_loop_reactor`(산화구 [B-04]), `treatment_line ∈ {mainstream, sidestream, sludge}` [B-13], `zone_role ∈ {main, selector, contact(접촉안정화의 접촉조·한국 혼화조), reaeration(RAS 재포기·안정화조), deoxygenation, degasifier, underflow_anoxic(JHB), post_anoxic(Bardenpho 후무산소), stripper, swing}` [B-04, B-15, K-05; `swing`은 미확인 근거 B2-03뿐이라 잠정 값], `redox_condition ∈ {aerobic, anoxic, anaerobic, unknown}`(biofilm_reactor 전용 [B-10]), `pond_type`(pond_lagoon_wetland [B-27]), `membrane_type ∈ {mf, uf, nf, ro, unknown}` [B-32], `mixing_stage ∈ {rapid_mix, flocculation, combined, unknown}`(chemical_treatment_unit [K-05]), `aerated`(pond_lagoon_wetland [B-27]), `graph_id`, `panel_phase`, `n_parallel_lanes`, `lane_group_id`(박스 수준 [B-16, B-23, K-07]), `aeration_mode ∈ {diffused, surface, brush, jet, hpo, membrane, mixer_only, none, unknown}` [B-19, B2-20], `operation_mode ∈ {continuous, sequencing, alternating, intermittent}` [B-16], `n_compartments` [B-03], `function`(flotation [B-09]), `clarifier_stage ∈ {primary, intermediate, secondary, chemical}` [B-26], `clarifier_shape ∈ {circular, rectangular, vertical_flow, lamella, multi_storey, unknown}` [B-25, B2-13], `primary_enhancement ∈ {none, cept, ballasted, primary_filter, unknown}`(lamella는 `clarifier_shape`) [B2-22(확인), B2-08, B2-17], `digester_type ∈ {anaerobic, aerobic, atad, two_stage, acid_phase, thp_fed, unknown}` + `co_digestion ∈ {true, false, unknown}` [B-29, B2-10, B2-15], `biomass_form ∈ {floc, granular, densified, unknown}` [B2-04, B2-19], `n_pathway ∈ {conventional, nitrite_shunt, pdna, anammox, unknown}`(그림에서 못 읽으므로 캡션·라벨 텍스트에 명시된 경우만, 기본 `unknown`) [B2-17, B2-18], `disinfectant ∈ {chlorine, chlorine_dioxide, ozone, uv, paa, aop, other, unknown}` + `purpose ∈ {pathogen, micropollutant}` + `dechlorination ∈ {true, false, unknown}` [B-30, B2-08, B2-13], `final_process ∈ {drying, incineration, composting, pyrolysis_gasification}` [B2-15], `existing_or_new`, `standby_count` [K-07].
- **스트림(그래프 엣지)**: `medium ∈ {liquid, mixed_liquor, sludge, gas, air, chemical, solid, signal}`, `stream_role ∈ {influent, settled_influent, effluent, reclaimed_water, mixed_liquor, internal_recycle_a, ras_s, r_recycle, effluent_recirculation_qr, was, scum, primary_sludge, thickened_sludge, digested_sludge, dewatered_cake, chemical_sludge, screenings_grit, fermentate, co_substrate, sidestream_return(상징수·탈수여액·centrate), backwash_return, bypass, overflow, step_feed, biogas, off_gas, air_supply, oxygen, chemical_dose, carbon_source(메탄올·아세트산 등 외부 탄소원), signal}`, `split_fraction`, `direction_confidence` [B-20, B-21, B-23, B2-10, B2-15, D-07].
- **이미지**: `diagram_style(A~E, hydraulic_profile)`, `language`, `n_panels`, `panel_crop` [B-16, D-02, K-09], **`process_configuration`**(플랜트 수준 공정 명칭; 통제 어휘 {cas, step_feed, contact_stabilization, extended_aeration, oxidation_ditch, hpo, deep_shaft, mle, ao, a2o, uct, muct, vip, bardenpho_4, bardenpho_5, jhb, sbr, mbr, ifas, mbbr, ags, uasb_as, tf, rbc, baf, contact_oxidation, unknown} + 자유 텍스트 원문; 한국 계열 {A2O 계열, SBR 계열, 담체 계열, MBR 계열, 기타}) [B2-10, B2-13, B2-16].

### 4.5 판별 규칙 (가이드라인 핵심 22개)

1. **활성슬러지 열**(1차 침전지 또는 스크린·침사지 하류, 2차 침전지·막조 상류)의 개방 탱크 → redox 라벨(혐기/무산소/호기, anaerobic/anoxic/aerobic/oxic)로 `*_zone`. 라벨이 없으면 **공정 구성 판별표**로 정한다 [B-04, B-06, B2-10]:
   | 호기조 앞 교반(무포기) 구역 수 | 반송 패턴 | 판정 |
   |---|---|---|
   | 0 | — | 전부 `aerobic_zone`(CAS·장기포기·산화구) |
   | 1 | 질산염 반송(a) 또는 RAS가 들어옴 | `anoxic_zone`(MLE) |
   | 1 | 반송 없이 유입수만 | `anaerobic_zone`(A/O, 인 제거) |
   | 2 | 1번째에 유입수(+RAS), 2번째에 a | 1번째 `anaerobic_zone`, 2번째 `anoxic_zone`(A2O) |
   | 2 | 2번째에 RAS·a, 2번째→1번째 r 반송 | 1번째 `anaerobic_zone`, 2번째 `anoxic_zone`(UCT·MUCT·VIP) |
   | 3 | 1번째에 RAS만 | 1번째 `anoxic_zone(underflow_anoxic)`, 2번째 `anaerobic_zone`, 3번째 `anoxic_zone`(JHB) |
   | 호기조 **뒤**에 교반 구역 | 탄소원 주입 또는 재포기 구역이 뒤따름 | `anoxic_zone(post_anoxic)`, 마지막 작은 호기조는 `aerobic_zone(reaeration)`(Bardenpho 4/5단) |
   판별표로도 못 정하면 generic + `inferred_from_context`. 밀폐·상향류·바이오가스선 → `anaerobic_wastewater_reactor`; 슬러지 공급 → `digester`; 공기선이 있는 상향류 탑 → `biofilm_reactor/fluidized_expanded_bed`. 포기식 침사지·포기식 유량조정조·포기 라군은 활성슬러지 열 밖이므로 기포가 있어도 각자 클래스 [B-06, B-10, B-11, B-12].
2. 여재층 + 공기 공급선 → `biofilm_reactor/submerged_biofilter(redox_condition=aerobic)`; 여재층 + 탄소원 주입선(공기 없음) → 같은 L3에 `redox_condition=anoxic`(탈질 여과); 둘 다 없음 → `filtration_unit` [B-10, D-07].
3. 탱크 전체에 캐리어·충전재가 표시된 포기 탱크 → 한 박스 `biofilm_reactor/mbbr_ifas`; 표시 없으면 `aerobic_zone`; 담체 케이지·MABR 카세트처럼 탱크 일부에만 그려졌으면 규칙 13(부모–자식) [B-10, B2-20].
4. 막 모듈이 혼합액을 받고 슬러지를 반응조로 되돌리면 `mbr_unit`, 처리수를 받으면 `membrane_unit` [B-32].
5. 슬러지 라인의 벨트·드럼·원심 장치: 소화조 **상류**(산물이 농축 슬러지) → `thickener`; 소화조 **하류** 또는 산물이 케이크·탈수여액 → `dewatering_unit`; 소화조가 없으면 산물 라벨로, 그것도 없으면 `dewatering_unit` + `inferred_from_context`. 물 라인의 "Filter" → `filtration_unit` [B-28, B2-15].
6. 약품은 장치가 아니라 **엣지**다: 화살표가 시작하는 약품 공급원(약품명 텍스트·탱크 기호 없는 끝)은 `io_terminal(chemical_source)`, 기존 단위로 들어가는 지점은 `junction_merge(chemical_dosing_point)`, 엣지는 `medium=chemical`·`stream_role=chemical_dose`. 응집·교반 탱크가 그려진 경우만 `chemical_treatment_unit`; 그 뒤 침전지는 `secondary_clarifier(clarifier_stage=chemical)`; 약품 저장 탱크가 그려졌으면 `storage_tank` [B-08].
7. SBR 다중 패널은 패널마다 1단위 + `panel_phase`; 교대 운전 쌍은 둘 다 `aerobic_zone` + `operation_mode=alternating` [B-16].
8. WAS는 반응조·침전지·반송선 어디서든 나올 수 있다; 출처를 가정하지 말고 `stream_role=was`만 붙인다 [B-21].
9. 한 wet well 안의 펌프 여러 대 = `pump_station` 1개; 단독 펌프 = `pump`; 약품 펌프 = `pump` + `stream_role=chemical_dose` [B-28].
10. UASB·IC 한 상자는 `multi_unit=[primary_clarifier, reactor, secondary_clarifier, digester]` [B-11].
11. 예비 클래스(§4.1b)에 해당하는 장치는 L2로 새 이름을 만들지 말고 표의 "현재 라벨 방법"대로 기존 클래스 + 속성으로 적는다; `label_text`에 원문(예: "Nereda", "Cambi THP", "struvite reactor")을 남겨 나중에 활성화할 수 있게 한다 [B2-04, B2-07, D-06].
12. 캡션·도면 제목의 공정 명칭(예: "A2O + MBR", "MLE응집 4-stage BNR", "AGS-SBR+고속응집침전")은 장치가 아니라 이미지 속성 `process_configuration`에 적는다. 한국 표기는 "+"로 단계를 잇고 "계열"로 묶으므로 "+"로 나눠 통제 어휘에 대응시키고 원문을 보존한다 [B2-10, B2-16].
13. 한 상자 안에 다른 단위가 **일부 영역으로** 그려진 하이브리드: 유입펌프장 안의 스크린·침사지, 포기조 안의 담체 케이지·MABR 카세트, 생물반응조 안의 침지막 모듈은 **바깥 상자를 parent**, 안쪽을 `parent_id`가 있는 자식으로 각각 라벨한다(구역 박스와 같은 방식). 자식 박스가 부모와 거의 같은 영역이 되면 자식을 만들지 않고 부모의 클래스·속성으로만 적는다(규칙 3) [B2-14, B2-20, P6].
14. **침전지 1차/2차, 조정조/저류조는 위치로 가른다**(교과서도 둘 다 "S"로 그림 [B-01]): 생물반응조 상류의 침전지 = `primary_clarifier`(슬러지가 농축조·소화조로만 감), 하류(살수여상·RBC 후단 humus tank, 2단 처리 사이의 중간 침전지 포함) = `secondary_clarifier`; 침전지 하부에서 상류 반응조로 되돌아가는 RAS 선이 있으면 그것만으로 secondary. 드럼·디스크 스크린은 유입부면 `screen`, 2차 침전 뒤면 `filtration_unit`. 유입 쪽에서 유량을 고르는 탱크 = `equalization_tank`(위치 무관이지만 처리 단위 사이), 처리수·슬러지·약품을 담기만 하면 `storage_tank` [B-25, B-26, B-28, K-03].
15. **박스형 도면도 의미 클래스를 단다**: 박스 안·옆 텍스트로 L2를 읽을 수 있으면 그 L2 + `visual_form=box` + `confidence=inferred_from_text`; 텍스트가 없거나 번호뿐이면 `process_unit_generic` + `label_text`=번호 + `inferred_from_context`. 장치 박스 안의 이름 텍스트는 별도 `text_label` 박스로도 친다 [B-01, D-01, K-06].
16. **부상 농축 vs 농축조**: 기포·DAF 표기·"부상" 명칭이 있으면 `flotation_unit(function=thickening)`; `thickener`는 중력·원심·벨트·디스크 농축만 [B-09, B2-15].
17. **P-stripper**: RAS(또는 혼합액)를 받으면 `anaerobic_zone(zone_role=stripper)`; reject water·탈수여액을 받으면 `sidestream_reactor/nutrient_recovery` [B-13, B-15].
18. **선에 붙은 텍스트 3종**: 문자(RAS, WAS, a, reject water)면 `stream_label`; 숫자·ID(유량, 농도, ①)면 `stream_tag`; 혼합("RAS 100 %")이면 `stream_label` 하나에 `tag_kind`를 함께 적는다. 장치 이름·설계치는 `text_label` [B-20, B-24, K-08].
19. **`io_terminal` 박스 범위**: 플랜트 경계의 화살표 꼬리(또는 머리)와 그에 붙은 텍스트("Influent", "방류", 약품명)를 함께 감싼다; 텍스트가 없으면 화살표 끝 주변 정사각형(규칙 §4.6의 점 박스 크기) [T-04].
20. **반류수 반응기 vs 본류 구역**: 생물 반응조의 유일한 공급이 탈수여액·소화 상징수·centrate(슬러지 라인에서 오는 선)이면 `sidestream_reactor`(+`treatment_line=sidestream`); 본류(유입수·1차 처리수·혼합액)도 받으면 `*_zone` + `treatment_line=mainstream`이고 반류수는 `merge_role=sidestream_return`으로 합류점만 친다. 모양(CSTR·SBR·입상 탑)은 판별에 쓰지 않는다 [B-13, B-15].
21. **발효조 vs 산발효 소화조**: 1차 슬러지를 받아 발효액이 **본류 혐기조·무산소조**로 가면 `fermenter`(`stream_role=fermentate`); 유출이 메탄 소화조로 가면 2단 소화의 1단 = `digester(digester_type=acid_phase)` [B-14, B-29, B2-10].
22. **산화구·Carrousel·Orbal**: 수로 전체를 한 박스 `aerobic_zone(is_loop_reactor=true)`로; 표면 포기기·산기기 위치로 호기/무산소 구간이 구분돼 그려졌으면 구간마다 자식 구역(`anoxic_zone`은 포기기 없는 구간); 다중 수로(Orbal)는 수로마다 자식, `n_compartments`에 수로 수. 간헐·교대 운전 표기는 `operation_mode` [B-04, B-27, B2-13].

### 4.5b 필수·선택 필드 계층 (어노테이션 부담 통제) [M-01, M-03]

33 클래스 + 속성 30여 개 + 규칙 22개를 어노테이터가 한 번에 다 적게 하면 일치도가 떨어지고 작업량이 비현실적이 된다. 필드를 세 층으로 나누고 **층마다 일치도를 따로 보고**한다.

| 층 | 필드 | 누가·언제 | 일치도 보고 |
|---|---|---|---|
| **T1 필수(검출 정답)** | 박스, `semantic_class`(L2/필수 L3), `visual_form`, `is_zone`+`parent_id`, `label_text`, `confidence`, 연결 클래스 8종, 그래프 엣지(src/dst/`medium`/`direction_confidence`) | 모든 이미지, 어노테이터 2명 | κ, IoU ≥ 0.7 비율, 엣지 F1 |
| **T2 조건부(텍스트에 명시된 경우만)** | `stream_role`, `treatment_line`, `zone_role`, `operation_mode`, `aeration_mode`, `redox_condition`, `clarifier_stage/shape`, `digester_type`, `function`, `n_compartments`, `n_parallel_lanes`, `existing_or_new`, `process_configuration` | 텍스트·캡션에 근거가 있을 때만; 없으면 `unknown`(추측 금지) | 값이 있는 인스턴스에 한해 일치율 |
| **T3 선택(하위 태그·메타)** | 선택 L3, `biomass_form`, `n_pathway`, `primary_enhancement`, `membrane_type`, `pond_type`, `mixing_stage`, `disinfectant`, `final_process`, `co_digestion`, `standby_count`, `polyline` | 전문가 1명이 2차 패스에서 | 보고하지 않음(설명 통계만) |

벤치마크 공개본의 평가는 T1만으로 정의하고, T2·T3는 분석·하류 매핑용 보조 라벨로 배포한다. 이렇게 해야 "속성 때문에 κ가 낮다"는 비판과 "속성이 없어 시뮬레이터 매핑이 안 된다"는 비판을 동시에 피한다.

### 4.6 그래프 정답 라벨 스키마 (연결 복원 벤치마크용) [T-03, T-04, B-02, B-20]

박스 어노테이션(COCO JSON)과 별도로 이미지마다 `graph.json`을 둔다. 흐름선 자체는 박스로 치지 않고(P5) 아래 엣지로만 기록한다.

- **노드** = 박스 id 중 그래프에 참여하는 것: L2 단위공정(구역 박스 포함; parent 탱크 박스는 구역이 있으면 노드가 아니고 `n_compartments`로만 남김), `io_terminal`, `junction_split`, `junction_merge`, `process_unit_generic`, `unknown_equipment`. 주석 클래스(`arrowhead`, `text_label`, `stream_tag`, `stream_label`, `instrument`)와 `aerator_mixer_symbol`, `valve`는 노드가 아니라 엣지·노드의 **증거 박스**로 연결한다.
- **엣지** = `{id, src, dst, medium, stream_role, split_fraction, direction_confidence ∈ {arrowhead, inferred, ambiguous}, line_style ∈ {solid, dashed, dotted, unknown}, evidence ∈ [arrowhead·stream_label·stream_tag·valve 박스 id], polyline(선택)}`. 위상(src→dst)이 필수이고 선의 기하(polyline)는 선택이다(픽셀 탐색 평가용). 엣지 끝점은 항상 **leaf 노드**(구역이 있으면 구역, 없으면 탱크).
- **점 클래스의 박스 크기**: `arrowhead`는 화살촉을 꼭 맞게, `junction_split/merge`는 교차점 중심 정사각형으로 변 = max(12 px, 이미지 짧은 변의 2 %); 분배조·혼합조가 구조물(탱크·상자)로 그려졌으면 그 구조물을 감싼다. 한 이미지에 독립 도면이 둘 이상이면 박스 속성 `graph_id`로 나눈다. 방향이 그려지지 않은 선은 공정 순서 사전지식(P-prior)으로 추론하되 `direction_confidence=inferred`로 표시해 평가에서 분리한다 [T-03].
- **규칙**: 분기·합류는 반드시 junction 노드를 거친다(한 노드에서 두 노드로 바로 가는 엣지 금지) [B-22]; 인접 구역 사이의 내부 흐름(혐기 → 무산소 → 호기)은 선이 없어도 엣지로 기록하고 `direction_confidence=inferred` [B-03]; 신호선은 `medium=signal`로 `instrument` 박스를 src/dst에 허용한다 [B-17]; 병렬 계열은 `lane_group_id`가 같은 노드를 평가 시 하나로 접을 수 있다 [B-23].
- **평가 프로토콜**: 예측 박스를 IoU ≥ 0.5로 정답 노드에 매칭한 뒤 엣지 precision/recall/F1, 방향 정확도(`arrowhead` 엣지만 / 전체), 그래프 편집 거리; L1로 접은 그래프에서도 같은 지표를 낸다(PID2Graph 방식) [T-04]. `inferred` 엣지는 별도 집계한다.
- **내보내기**: `graph.json` → NetworkX → GraphML / SFILES2 / GPS-X 레이아웃 초안; 4.3의 매핑 필드가 노드 속성으로 따라간다 [B-02].

---

## 5. 확정 절차

**확정된 결정 (2026-11-16, 연구 책임자 승인)**: ① `semantic_class`와 `visual_form`을 별도 필드로 분리(P1), ② 하 등급 7개 클래스는 파일럿 후 병합 여부 결정, ③ 구역 박스 + `parent_id`(null 허용)(P6). 인력: 어노테이터 2명(환경공학 대학원생) + 판정자 1명(체계 설계자, 어노테이션에는 참여하지 않음). 하류 검증 시뮬레이터: **QSDsan(오픈소스, 1순위)**, GPS-X·SUMO(보조) — §4.3·§6 참조.

0. **동결과 사전 등록(pre-registration)** — **완료 2026-11-16: 커밋 `03f3d10`, 태그 `taxonomy-v1.1`** (github.com/JoshuaTaeyongWoo/wwtp-pfd-dataset). 파일럿 전에 v1.1 체계(클래스·속성·규칙·예비 클래스 활성 기준 50/20·L3 승격 기준 150·병합 규칙)를 git 커밋 해시로 고정하고, 파일럿 이후의 모든 변경은 v2 변경 이력에 "무엇을·왜(어느 불일치 사례 때문에)" 적는다. 리뷰어가 "결과를 보고 클래스를 맞췄다"고 의심하지 못하게 하는 장치다 [M-01].
1. **파일럿 어노테이션 (main에서 층화 표본 60장)** — **표본 추출 완료 2026-11-16**: `data_collection/s15_pilot_sample.py`(seed 20261116; 출처별 제곱근 배분 16/16/11/8/5/4, 문서당 1장, 출처마다 비영문 1장 이상, 카테고리 분산; 페이지 렌더(E) 10장은 같은 출처·카테고리·언어의 그림 크기 이미지로 교체, `data/pilot/replacements.json`). 결과 `data/pilot/pilot60.csv`, 이미지 `data/pilot/images/`, 점검용 `data/pilot/sheets/`, 배분표 `data/pilot/allocation.md`. 잠정 양식 분포 A 29 / B 21 / C 9 / D 1(시뮬레이터 화면은 main에 드묾), 비영문 17, 문서 58종(EPA는 문서 수가 적어 교체 시 같은 문서 허용), tier A 46 / B 14. 출처 6종 × 양식 A~D × 언어(영문/비영문)를 고루 포함. **어노테이터 2명(환경공학 대학원생, 가이드라인 교육 2시간 + 연습 5장)** 이 서로 보지 않고 독립 라벨링하고, **제3자(공정 전문가)** 가 불일치를 판정(adjudication)한다. 체계 설계자는 어노테이터가 아니라 판정자만 맡아 순환성을 피한다. 일치도는 (i) 박스 greedy 매칭(IoU 최대, 임계 0.5) 후 **매칭된 쌍의 클래스 Cohen's κ**(목표 ≥ 0.8), (ii) 매칭 안 된 박스 비율(누락·추가 불일치, 양쪽 각각), (iii) 매칭 쌍 중 IoU ≥ 0.7 비율, (iv) 엣지 F1(노드 매칭 후)을 **부트스트랩 1,000회 95 % CI**와 함께 보고한다. 클래스별 κ는 매칭 인스턴스 ≥ 20인 클래스만 보고하고 나머지는 L1로 접어 보고한다. 참고치: Open Images의 전문가 일치도 0.88, 박스 검증 수용 기준 IoU ≥ 0.7, PASCAL 계열의 사실상 상한 ≈ 0.7 평균 IoU; COCO는 검증에 5명 중 4명 동의를 요구했다 [M-01, M-03]. 불일치 사례를 유형별(클래스 경계 / 박스 범위 / 구역 분할 / 누락)로 분류해 정의·포함·제외 예를 수정한다. 어노테이터 일치도는 이후 모델 성능의 **사람 상한(human ceiling)** 으로 논문에 함께 보고한다.
2. **클래스 빈도 추정**: 파일럿 60장의 인스턴스 수 × (993/60)로 전체 빈도를 외삽. P3 ②를 못 채우는 클래스는 병합하고 v2 체계를 확정한다. 예상: 33 → 26~29개 L2 (하 등급 7개가 병합 후보; 예비 클래스 7개는 켜지지 않을 것으로 예상).
3. **가이드라인 v1 작성**: 클래스별 한 문장 정의, 포함·제외 예, 별칭, 대표 그림 3종(기호·박스·그림형), 박스 규칙(텍스트 포함 여부, 겹침, 구역 박스), 판별 규칙 22개, 그래프 라벨 규칙(§4.6).
3b. **페이지 렌더 크롭(본 어노테이션 전 필수, 2026-11-16 착수)**: main의 페이지 전체 렌더(EPA·OpenAlex 162장)를 `s16_crop_pages.py`로 PDF 레이아웃에서 자동 크롭(106장 적용, 사람이 미리보기 전부 검토·8장 기각) → 나머지 56장은 크롭 도구로 수작업 → 부모 페이지는 `crop_pending`으로 이동. 특허 전면 도면(68장)은 페이지 자체가 그림이라 자르지 않는다. 파일럿 60장에는 페이지 렌더가 없다.
4. **본 어노테이션(active learning)**: Theisen 방식대로 100장 수동 → 모델 학습 → 다음 200장 예측 후 수정 → 반복 [T-01]. 도구는 CVAT 또는 Label Studio(바운딩박스 + 속성 + 관계 라벨을 지원하고, 모델 예측을 불러올 수 있음). 연결 그래프 라벨은 CVAT의 skeleton/relation 또는 별도 JSON(노드 id 쌍)로 기록한다.
5. **모니터링**: 200장마다 클래스 분포·κ·클래스별 AP를 확인하고, 분할(인스턴스 ≥ 150이고 양식 변형이 뚜렷한 클래스 → L3 분리)이나 병합을 결정한다. 변경 이력은 버전으로 기록한다(v0 → v1 → …).
6. **라벨링 완전성 규칙**: 한 이미지의 모든 클래스 인스턴스를 빠짐없이 라벨링한다(부분 라벨링은 검출 학습을 망친다 [M-04]). 박스는 객체를 꼭 맞게 감싸고, 배경 전용 이미지(공정도가 아닌 것) 0~10%를 negative로 포함한다.
7. **동결(freeze)과 분할(split)**: 어노테이션 완료 후 체계를 동결하고 train/val/test를 **문서 단위**로 분할한다(같은 논문의 그림이 양쪽에 들어가지 않도록). 분할은 출처(6종) × `visual_form` 주 양식 × 언어(영문/비영문)로 층화해 test에 모든 조합이 들어가게 한다 [D-01, D-02, D-05]. 보조 세트(unit-level, pictorial, other-domain)는 test-only 또는 도메인 일반화 평가용으로 둔다.

**수량 목표**: main 993장, 장당 평균 10~15 객체로 추정 → 10,000~15,000 박스. Theisen(17,411)과 같은 규모. 작업량은 active learning 적용 시 장당 3~5분 → 50~80시간 + 그래프 라벨 50~80시간.

---

## 6. 평가 지표와 리스크

- **검출**: COCO AP / AP50 / AP75, 크기별(APs/APm/APl), 클래스별 AP, L1로 접은 AP(희귀 클래스 포함 지표). 계층 평가는 Open Images 방식으로 명시한다: 정답은 leaf 라벨을 모든 상위 클래스로 확장하고, 예측도 같은 규칙으로 확장한 뒤 각 수준에서 AP를 계산한다 [M-01]. LVIS 방식으로 rare(1~10장)/common(11~100장)/frequent(>100장) 구간별 AP를 따로 보고한다 [M-02]. 모든 지표는 `visual_form`(기호/박스/그림), 출처, 언어(영문/비영문)로 층화해 보고한다 [D-01, D-02].
- **의미 부여(박스형 포함)**: `visual_form=box` 박스에 대해, 검출(generic) + OCR + 문맥 → 정답 `semantic_class`(L2) 매핑 정확도. 이것이 WWTP 특유의 지표이며 Theisen에는 없다. 정답 L2는 어노테이터가 텍스트로 읽어 적은 값이다(P1).
- **연결**: 노드 매칭(IoU ≥ 0.5, 클래스 일치 요구/비요구 두 버전) 후 엣지 precision/recall/F1, 방향 정확도(`arrowhead` 근거 엣지만 / 전체), 정규화 그래프 편집 거리(노드 수로 나눔; PID2Graph 방식) [T-04]. `direction_confidence=inferred` 엣지는 별도 집계한다.
- **체계 자체의 타당성 실험(논문의 ablation)**: ① 같은 검출기로 L2 33 vs 파일럿 후 병합본 vs L1 7 클래스를 학습해 AP·엣지 F1 비교(클래스 수가 성능을 해치지 않음을 보임); ② `semantic_class`만 학습 vs `visual_form`별 분리 학습(Theisen 규칙 ② 재검증 [T-01, T-06]); ③ 구역 박스 포함/제외가 그래프 F1과 시뮬레이터 매핑 성공률에 주는 영향; ④ 사람 상한(어노테이터 κ·IoU)과 모델 성능의 간격.
- **기준 모델(baselines)**: Faster R-CNN R50-FPN(Theisen 재현 [T-01]), 최신 검출기 1종(DETR 계열 또는 YOLO 계열), 그래프 복원은 픽셀 탐색(Theisen) vs 학습 기반(FR-DETR형 선 검출 [T-07]) vs VLM 제로샷; 모두 같은 분할·같은 지표.
- **하류 검증(round-trip)**: 시험 세트에서 10장을 골라 예측 그래프 → `classes.yaml` 매핑 → **QSDsan 플로우시트 코드 자동 생성(1순위, 오픈소스라 재현 가능)** → 실행 가능 여부·단위 수·연결 수를 자동 집계하고, 공정 전문가가 단위·연결 오류 수를 세어 보고. GPS-X·SUMO 레이아웃 초안 생성은 보조 검증(연구실 보유). "시뮬레이션 구조 자동 생성"을 정량 주장으로 만들려면 이 수치가 필요하다 [S-03, S-04, S-06].
- **데이터 공개 문서**: Datasheets for Datasets 형식(동기, 구성, 수집 과정, 전처리, 용도, 배포, 유지보수)으로 작성하고, tier A(CC BY·공공저작물·특허)는 이미지+라벨, tier B(비상업·저작권)는 URL+라벨만 배포한다. 수집·선별 스크립트와 provenance 기록(SHA-256·pHash)은 저장소에 두고 Zenodo DOI로 고정한다 [D-05].
- **선별 편향**: AI 선별(s09/s10)의 precision은 표본 점검으로 ~0.90이지만 **recall은 미추정**이다. 논문 전에 reject 집합에서 무작위 200장을 사람이 재검토해 recall과 95 % CI를 보고하고, 누락 유형(그림형·비영문)을 기록한다.
- **리스크**: ① 박스형 도면에서 시각 클래스가 무의미 → P1로 대응. ② 특허 도면의 번호 참조(텍스트 없음, "412", "480") → `process_unit_generic` + `label_text`=번호, `confidence=inferred_from_context`. ③ 구역 박스 처리 일관성 → P6 + 판별 규칙 7. ④ 다국어 라벨 → OCR 모델 선택과 `language` 필드. ⑤ 그림형(C) 도면이 train에 섞이면 기호형 AP를 떨어뜨릴 수 있음 → `visual_form`으로 층화 평가. ⑥ 혐기 CSTR·소화조·발효조처럼 기호가 같은 장치 → 공급 스트림 규칙과 `confidence`로 대응 [B-12]. ⑦ 출처 편향: 특허(342장)는 번호 참조 박스형, 한국 지자체(22장)는 그림형에 치우침 → 출처별 층화 보고와 한계 명시. ⑧ 근거 원장의 "미확인" 행은 논문에 인용하지 않는다(확인된 행과 공개 PDF만 인용).

**논문에서 "최초"를 주장할 때의 근거**: 2026-11-16 웹 검색(영문 "wastewater process flow diagram dataset object detection", 한글 "하수처리장 공정도 딥러닝 데이터셋")에서 WWTP 도면을 대상으로 한 공개 검출·그래프 데이터셋은 찾지 못했다. 가장 가까운 선행은 화공 PFD(Theisen 2023, 비공개 [T-01]; Yu & Zheng 2026 CERD, 비공개 300여 장, 그래프 정답 173 연결 F1 0.771 [T-08]), P&ID(PID2Graph 공개 [T-04]), 흐름도(hdFlowmind 1,776장, 화살표 머리·꼬리 좌표 포함 [T-07])이다. 공개 PFD 벤치마크로 그래프 수준 정답을 배포하는 것은 도메인을 불문하고 우리가 처음이 될 수 있으므로, 논문에서는 "WWTP 최초"와 "그래프 정답을 공개한 PFD 벤치마크로서 최초"를 구분해 두 주장 모두 체계적 검색 결과로 뒷받침한다. 논문 제출 전 Scopus/WoS 체계적 검색으로 다시 확인하고 검색식·날짜·건수를 보충자료에 적는다.

---

## 7. 참고 자료 (2026-11-16 조사·검증)

**선행 데이터셋·클래스 체계**
- Theisen et al. 2023, Digital Chem. Eng. 6:100072. https://doi.org/10.1016/j.dche.2022.100072 (47 클래스 전체는 Table 4의 약어로 확인. 약어 → 의미·양식 대응표는 그림이라 추출 불가 → Max에게 LabelImg 라벨 파일 요청)
- Paliwal et al. 2021, Digitize-PID / Dataset-P&ID. https://arxiv.org/abs/2109.03794
- Kim et al. 2022, J. Comput. Des. Eng. 9(4):1298. https://academic.oup.com/jcde/article/9/4/1298/6650284 ; Moon et al. 2021, Expert Syst. Appl. https://doi.org/10.1016/j.eswa.2021.115337
- Stürmer et al. 2025, PID2Graph. https://arxiv.org/abs/2411.13929 ; 데이터 https://zenodo.org/records/14803338
- Elyan et al. 2018 (IJCNN), 2020 (Neural Networks 129:91); Jamieson et al. 2024 (IJDAR). https://rgu-repository.worktribe.com/output/2457618
- Awal et al. 2011, FC_A 흐름도 데이터셋. https://arxiv.org/pdf/1712.04833 ; Liu et al. 2024, Flowmind2Digital / hdFlowmind. https://arxiv.org/abs/2401.03742 ; FR-DETR (2022) https://www.researchgate.net/publication/363021700
- Yu, Y., Zheng, S., 2026. Automated process flow diagram parsing and simulation model generation via visual perception and topology reasoning. *Chem. Eng. Res. Des.* 234, 330–340. https://doi.org/10.1016/j.cherd.2026.09.022 (로컬 PDF `Ref/[CERD]…pdf`, 2026-11-17 원문 정독)
- Bahamdan, Pajak, Hedengren, del Rio Chanona 2026, Sketch2Simulation. https://arxiv.org/abs/2603.24629

**표준·어휘**
- ISO 10628-2:2012 (주제군 29개). https://standards.iteh.ai/catalog/standards/iso/8bc45867-650c-4d1c-b32f-726b336223ba/iso-10628-2-2012
- DEXPI 정보모델 / OPC 30250. https://reference.opcfoundation.org/specs/OPC-30250/7 ; 클래스 개요 https://dexpi-information-model.aixcape.org/queries/classes_overview.html
- EN 16323:2014 Glossary of wastewater engineering terms (EN 1085 후속). https://knowledge.bsigroup.com/products/glossary-of-wastewater-engineering-terms
- WEF MOP 8 (7판) https://www.wef.org/?p=2184 ; EPA Nutrient Control Design Manual https://19january2025snapshot.epa.gov/sites/default/files/2019-08/documents/nutrient_control_design_manual.pdf
- KDS 61 하수도 설계기준 (국가건설기준센터) https://www.kcsc.re.kr

**시뮬레이터 단위모델**
- BSM1 보고서 (Alex et al. 2008) https://www2.iea.lth.se/publications/Reports/LTH-IEA-7229.pdf ; BSM2 구현(WaterTAP) https://watertap.readthedocs.io/en/stable/technical_reference/flowsheets/BSM2.html ; bsm2-python https://bsm2-python.readthedocs.io/user_guide/
- GPS-X 단위 공정 목록 https://www.hydromantis.com/GPSX-unit-processes.html
- SUMO24 https://dynamita.com/sumo24/Why_choose_SUMO24.pdf ; BioWin https://envirosim.com/support ; WEST https://www.dhigroup.com/technologies/mikepoweredbydhi/west
- QSDsan (Li et al. 2022, *Environ. Sci.: Water Res. Technol.*, https://doi.org/10.1039/D2EW00455K ; 단위 목록 https://qsdsan.readthedocs.io/en/latest/api/sanunits/_index.html ; GitHub QSD-Group/QSDsan)

**교과서 (로컬 PDF, `WWTP_RL/Ref/textbook`)**
- Henze, van Loosdrecht, Ekama, Brdjanovic (eds.) 2008, *Biological Wastewater Treatment: Principles, Modelling and Design*, IWA.
- Olsson & Newell 1999, *Wastewater Treatment Systems: Modelling, Diagnosis and Control*, IWA.
- Rieger et al. 2012, *Guidelines for Using Activated Sludge Models*, IWA STR 22.
- Henze et al., *Activated Sludge Models ASM1, ASM2, ASM2d and ASM3*, IWA STR 9.

**최신·주요 교과서·기준 (웹 목차·공개 PDF 확인, 2026-11-16; 상세 `evidence_ledger.md` G절)**
- Tchobanoglous, Stensel, Tsuchihashi, Burton (Metcalf & Eddy | AECOM) 2014, *Wastewater Engineering: Treatment and Resource Recovery*, 5th ed., McGraw-Hill. 장 목차: https://www.mheducation.com/highered/product/wastewater-engineering-treatment-resource-recovery-metcalf-eddy-inc/M9780073401188.html
- Chen, van Loosdrecht, Ekama, Brdjanovic (eds.) 2020, *Biological Wastewater Treatment: Principles, Modelling and Design*, 2nd ed., IWA. 목차: https://bdd.pseau.org/outils/biblio/resume.php?d=8875&l=en ; 연습서(OA) Lopez-Vazquez et al. 2023 https://iwaponline.com/ebooks/book/871/
- WEF/ASCE 2017, *Design of Water Resource Recovery Facilities*, MOP 8, 6th ed. 목차: https://find.library.upenn.edu/catalog/9979431069503681 ; 7th ed. (2025) https://www.wef.org/?p=2184
- Grady, Daigger, Love, Filipe 2011, *Biological Wastewater Treatment*, 3rd ed., CRC/IWA. 목차: https://www.perlego.com/book/4364773/biological-wastewater-treatment-pdf ; https://www.routledge.com/product/isbn/9781040061763 ; 1장 미리보기(Table 1.1·1.2 원문) 로컬 `Ref/Grady2011_BWT3e_preview_ch1.pdf`
- van Haandel & van der Lubbe 2012, *Handbook of Biological Wastewater Treatment*, 2nd ed., IWA. 목차: https://www.perlego.com/book/572008/handbook-of-biological-wastewater-treatment-pdf
- 환경부 2022, 『하수도설계기준 KDS 61 00 00』(61 45 00 펌프장시설, 61 50 00 수처리시설, 61 55 00 찌꺼기(슬러지)처리시설). 원본 https://www.kcsc.re.kr ; 열람 사본 https://files-scs.pstatic.net/2024/08/30/FEFOlqHQAr/하수도설계기준(2023).pdf
- 하수도정보시스템 처리공법 분류(A2O·SBR·담체 계열) https://www.hasudoinfo.or.kr/cms/lay1/WS10000231/program.do ; 인천시 하수처리시설 현황(실제 처리공법 표기) https://www.incheon.go.kr/env/ENV030301
- US EPA 2013, *Emerging Technologies for Wastewater Treatment and In-Plant Wet Weather Management*, EPA 832-R-12-011. https://www.epa.gov/sites/production/files/2019-02/documents/emerging-tech-wastewater-treatment-management.pdf
- Spérandio, Comeau, Rieger (eds.) 2021, *Water Resource Recovery Modelling*, IWA; Derlon, Villez, Rahman, Stewart (eds.) 2024, *Modelling for Water Resource Recovery*, IWA.
- 밀집 활성슬러지·AGS: "Making waves: Riding the densification wave…", *Water Research* 2024; WRF Project 5130 https://waterrf.org/node/252221 ; MABR 검토 (WST 2021) https://doaj.org/article/717e47559f804cb09f53e651d732db5b

**체계 설계·어노테이션 방법론**
- LVIS (Gupta et al. 2019; rare/common/frequent, repeat factor sampling) https://arxiv.org/pdf/1908.03195
- Open Images V4 (Kuznetsova et al.; leaf 라벨링, 계층 평가, 박스 검증 IoU ≥ 0.7, 전문가 일치도 0.88) https://arxiv.org/pdf/1811.00982 ; 평가 스크립트 https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/challenge_evaluation.md
- COCO (Lin et al. 2014; 다단계 어노테이션, 5명 중 4명 검증) https://arxiv.org/abs/1405.0312
- Ultralytics 학습 데이터 권고 https://docs.ultralytics.com/yolov5/tutorials/tips_for_best_training_results/
- 바운딩박스 일치도 지표(Krippendorff α, iaa-od) https://arxiv.org/pdf/1912.10107 ; https://pypi.org/project/iaa-od/

**확인하지 못한 것 (후속)**
- Theisen Table 1의 약어 → 의미·양식 대응 → Max에게 요청.
- Kim et al. 2022의 76 라벨 이름 → OUP PDF의 표에서 확인.
- ~~KDS 61 50 00 / 55 00의 단위공정 소절 제목~~ → 확인 완료 [B2-13, B2-15]; 61 45 00(펌프장: 스크린·침사지) 절 제목은 미추출.
- ASM 보고서의 ASM1·ASM2 부분(스캔 이미지) [B-31].
- ~~MOP 8 6판 절 제목~~ → AccessEngineering 공개 목차로 확인 완료 [B2-22]. ~~Grady 3판 표 1.1·1.2~~ → CRC 미리보기 PDF(1장 전문, `Ref/Grady2011_BWT3e_preview_ch1.pdf`)로 확인 완료 [B2-23]. Metcalf & Eddy 5판은 Google Books 차단으로 절 단위 미확인 [B2-21] → 실물 또는 다른 네트워크에서 확인.
- ~~Yu & Zheng 2026 CERD 원문~~ → 2026-11-17 `Ref/[CERD]…pdf`로 정독 완료 [T-08]; 데이터 비공개, 그래프 정답 173 연결 F1 0.771, 방향 결정률 77.6 %.
- 환경부 하수도통계 "처리방법별" 공식 분류, 「공공하수처리시설 운영관리 실무지침」 목차 [B2-16, B2-21].

## 8. 한국 설계 자료 [K] 및 최신·주요 교과서 보강 [B2]

### 8.1 한국 설계 자료 (환경종합설계·수리설계 과목 자료) [K-01 ~ K-09]

- **양식**: 교재의 처리공정도는 텍스트 화살표 나열, 물질수지도는 "박스 + Q/S/D 라벨 + 슬러지는 아래 점선, 가스는 위, 약품은 위에서 유입, 반송은 하단 실선 루프에 R·C_R" 관행 [K-01]. 한국 교재식 도면도 양식 A(박스형)다 → 원칙 1 추가 확인.
- **스트림 3분류**: 물질수지 범례가 "수처리계통 / 슬러지처리계통 / 반송수" [K-02] → `medium` 상위 묶음(liquid·mixed_liquor / sludge / 반송·반류)과 일치. 한국 도면에서는 선 종류(실선·점선)가 매체를 구별하므로 `line_style` 단서를 가이드라인에 기록.
- **클래스 반영**: 총인처리시설(급속교반 → 완속교반 → 부상조)은 `chemical_treatment_unit` + `flotation_unit(function=tertiary)`; 슬러지발효조는 `fermenter`의 실재 사례; 혼화조(반송슬러지 + 원수 접촉)는 `zone_role=contact`(기능상 selector와 같으나 한국 명칭을 보존); 분배조·분배탱크·유입분배조는 **그려진 분기점**으로 `junction_split`; 방류맨홀은 `io_terminal(effluent)`; 여과기 이송조는 `storage_tank` [K-03, K-05].
- **구역 표기 관행**: 생물반응조를 혐기/무산소/호기 명칭 없이 "#1~#4(간벽 3)"로만 표기하는 보고서가 있음 [K-06] → redox가 적히지 않은 구역은 `aerobic/anoxic/anaerobic_zone` 대신 `process_unit_generic(is_zone=true)` + `n_compartments` + `confidence=inferred_from_context`로 라벨.
- **속성 추가**: `existing_or_new ∈ {existing, new, unknown}`(기존/증설 병기), `standby_count`(S.B 예비 대수), `n_parallel_lanes`는 지·조·열·기·대 표기와 "×N개"에서 읽음 [K-07].
- **태그 항목 확장** [K-08]: `text_label.tag_kind`에 {spec(W×L×H, ø D×H), material, capacity}, `stream_tag.tag_kind`에 {loading(수면적부하·고형물부하), performance(HRT·SRT·MLSS·F/M·SVI), quality(BOD/COD/SS/T-N/T-P), hydraulic(EL, WSE, HWL/DWL/LWL)}를 추가. 수리종단도는 PFD가 아니므로 수집 시 별도 `diagram_style=hydraulic_profile`로 분리 [K-09].
- **한글 별칭표** [K-04]: 1차침전지=일차=최초침전지=초침; 2차침전지=이차=최종침전지=종침; 포기조=폭기조=활성오니조=공기공급조=생물반응조; 소독조=염소접촉조=UV소독조; 찌꺼기=오니=슬러지; 반송슬러지=반송활성오니=반송수; 잉여슬러지=잉여오니; 생슬러지=생오니; 세정조=제2소화조; 가스탱크=dome tank. OCR 후 정규화 사전에 그대로 사용.

### 8.2 최신·주요 교과서·설계기준 보강 [B2-01 ~ B2-23]

**조사 범위와 한계.** Metcalf & Eddy 5판(2014), IWA *Biological Wastewater Treatment* 2판(2020)과 연습서(2023, OA), WEF MOP 8 6판(2017)·7판(2025), Grady 3판(2011), van Haandel & van der Lubbe 2판(2012), Davis 2판(2019), KDS 61(2022) 전문, EPA 2013 신기술 보고서, IWA In Focus(2021·2024), 밀집 활성슬러지·MABR 검토 논문. 로컬 PDF가 없는 책은 **장 목차(출판사·도서관 페이지)** 까지만 원문으로 확인했고, 절 단위 내용은 미확인으로 표시했다(근거 원장 "검증" 열, [B2-21]). 미확인 항목은 KDS 전문·EPA 보고서·우리 데이터 빈도 [D-06]와 함께 썼을 때만 결정에 반영했다.

**확인된 것(v1 유지).**
- L1 골격과 순서가 다섯 참고서에서 동일(전처리 → 1차 → 생물 → 고도·분리 → 소독 → 슬러지; 반류수 별도) [B2-01, B2-07, B2-13]. 소독은 ME5·MOP8·KDS 모두 별도 장이지만, 우리 L1은 평가용 상위 묶음이므로 `tertiary` 아래 유지(별칭·`kds61_term=소독시설`로 식별 가능).
- 구역(`*_zone`) 명명과 selector의 "구역 역할" 지위 [B2-03, B2-04]; MBR·생물막·혐기성 폐수 반응기·자연정화시설이 각각 장 단위 [B2-04, B2-07, B2-10, B2-11]; 발효조와 호기성 소화가 "named operation" [B2-10]; 반류수 처리가 장 단위 [B2-01, B2-07, B2-15].
- Grady의 분류 3축(생화학적 환경 / 반응기 구성 / 운전)은 우리 속성(`aerobic/anoxic/anaerobic_zone`, 부유 vs `biofilm_reactor`, `operation_mode`)과 일치 [B2-10].

**바뀐 것(v1 → v1.1).**
1. **이름 붙은 공정은 장치가 아니다** → 이미지 속성 `process_configuration` 신설 [B2-10, B2-16]; 한국 표기 "A2O + MBR" 파싱 규칙(판별 규칙 12).
2. **예비 L2 클래스 7개**(§4.1b): AGS·슬러지 개량(열가수분해)·영양염 회수·1차 여과·오존/AOP/활성탄·하이드로사이클론·탈취 설비. 모두 최신 자료에서 장·기술 단위로 승격됐으나 우리 데이터에서 ≤ 31장 [D-06] → 지금은 속성·L3로 기록, 50개 넘으면 활성화.
3. L3 추가: `anaerobic_wastewater_reactor/anaerobic_mbr` [B2-11, B2-17]; `sidestream_reactor` 선택 L3 4종 [B2-01, B2-17]; `filtration_unit/activated_carbon` [B2-07]; `biofilm_reactor` L3 개명 `fluidized_expanded_bed` [B2-10], 접촉산화는 `submerged_biofilter` 별칭 [B2-13].
4. 속성 추가: `zone_role=swing`, `aeration_mode=membrane`, `clarifier_shape=multi_storey`, `primary_enhancement`, `digester_type` 값 확장 + `co_digestion`, `biomass_form`, `n_pathway`, `disinfectant`·`purpose`·`dechlorination`, `final_process`; `stream_role`에 `fermentate`, `co_substrate` [B2-03, B2-08, B2-10, B2-13, B2-15, B2-17 ~ B2-20].
5. 위치 규칙: `anaerobic_wastewater_reactor`는 활성슬러지 앞 전처리 위치에서도 같은 클래스 [B2-11]; 유입펌프장 안의 스크린·침사지, 포기조 안의 담체·MABR은 parent–자식으로(판별 규칙 13) [B2-14, B2-20].
6. 별칭: primary/final settler, final settling tank, SST, plant recycle flow treatment, 자연정화시설, WRRF [B2-03, B2-06, B2-09].

**수집에 되돌아가는 것.** IWA 연습서(2023, OA, CC BY-NC-ND)와 EPA 2013 보고서는 각각 tier B·tier A 도식 출처 후보 [B2-05, B2-17]; 검색어에 "WRRF", "water resource recovery facility" 추가 [B2-09].

**아직 확인하지 못한 것.** [B2-21] 참조. 2차 조사(2026-11-16)로 MOP 8 6판 절 제목은 전부 확인했고 [B2-22], Grady 3판은 1장 전문(표 1.1·1.2 포함)을 CRC 미리보기 PDF로 확인했다 [B2-23]. 남은 것은 ME5 절 제목(B2-02·B2-03: Google Books 차단)이며, 여기에만 기대는 결정은 `zone_role=swing`(잠정)뿐이다.
