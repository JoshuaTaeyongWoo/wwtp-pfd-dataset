# 파일럿 어노테이션 실행 안내 (60장, 어노테이터 2명 + 판정자 1명)

체계 동결: 태그 `taxonomy-v1.1` (커밋 03f3d10). 표본: `data/pilot/images/` 60장 (`data/pilot/pilot60.csv`).
도구: **Label Studio** (로컬, pip 설치, 관계(엣지) 라벨 지원). CVAT는 엣지를 못 담으므로 보조.
이 PC에는 Docker가 없어 CVAT 로컬 설치는 불가; CVAT를 쓰려면 app.cvat.ai에 `annotation/cvat_labels_expanded.json`을 올린다.

## 1. 설치 (한 번)

```bash
python -m pip install label-studio pyyaml
```

```bash
label-studio start --port 8080
```

브라우저에서 http://localhost:8080 → 계정 생성(로컬 전용).

> **주의 (2026-11-17 교훈)**: 서버는 반드시 **사용자 터미널에서 직접** 켠다. Claude 데스크톱 앱 안에서 켜면 앱 샌드박스(`AppData\Local\Packages\Claude_…\LocalCache\Local\label-studio`)에 별도 데이터베이스가 생겨 계정·프로젝트가 갈라진다. 진짜 데이터는 `AppData\Local\label-studio\label-studio`에 있다. 토큰도 진짜 서버에서 발급한 것만 유효하다.

## 2. 프로젝트 만들기 (어노테이터마다 1개, 총 2개)

같은 설정으로 프로젝트를 **두 개** 만든다(`pilot_A`, `pilot_B`). 한 프로젝트에 두 사람을 넣으면 서로의 라벨을 볼 수 있어 일치도가 오염된다.

**자동 (2026-11-17 완료)**: 계정 → Account & Settings → Access Token을 `data/pilot/.ls_token`에 저장한 뒤
`python data_collection/s18_setup_pilot_projects.py` → 프로젝트 2개 생성 + 라벨 설정 + 60장 업로드(pilot 번호 순, SVG/WebP는 PNG로 변환).
이미 있으면 라벨 설정만 갱신한다. 수동으로 할 때는 아래 순서.

1. Create Project → 이름 `pilot_A`.
2. Data Import → `data/pilot/images/` 의 60장 업로드(드래그). 파일명이 `pilot_NN__…` 이라 순서가 유지된다.
3. Labeling Setup → Custom template → Code → `annotation/label_studio_config.xml` 내용을 붙여넣기 → Save.
4. 같은 과정으로 `pilot_B`.

## 3. 어노테이터 교육 (2시간 + 연습 5장)

- 읽을 것: **`annotation/manual/WWTP_annotation_manual_v1.pdf`** (그림 포함 초보자용 매뉴얼 17쪽; Word 원본 `.docx`, 생성 스크립트 `manual/build_manual.py`·`make_manual_figures.py`). 규칙 원문은 `docs/annotation_guideline_v1.md`.
- 연습: `data/pilot/images/`가 아닌 main의 다른 5장(판정자가 고름)으로 연습하고, 판정자와 함께 맞춰 본다. 연습 결과는 버린다.
- 단축키: 숫자 1~0 = 자주 쓰는 클래스, `r` = 관계, `Ctrl+Enter` = 제출.

## 4. 라벨링

- 60장을 **각자** 전부. 중간에 상의하지 않는다. 막히면 `annotator_note`에 적는다.
- 한 장 완료 기준: 모든 장치·구역·연결 요소 박스, 박스마다 visual_form·confidence·label_text, 구역은 is_zone + parent_of, 흐름 엣지 전부, 이미지 속성(diagram_style, language, n_panels).

## 5. 내보내기와 일치도

각 프로젝트에서 Export → JSON → `data/pilot/exports/pilot_A.json`, `pilot_B.json`.

```bash
python data_collection/s17_pilot_agreement.py --a data/pilot/exports/pilot_A.json --b data/pilot/exports/pilot_B.json --out data/pilot/agreement.md
```

출력: L2/L1 κ, IoU ≥ 0.7 비율, 누락·추가 비율, 엣지 P/R/F1, 클래스별 κ(매칭 ≥ 20), 부트스트랩 95 % CI. 목표 κ ≥ 0.8.

## 6. 판정(adjudication)과 v2

- 판정자는 두 결과를 나란히 보고(Label Studio에서 두 프로젝트를 열거나 `agreement.md`의 불일치 목록) 불일치를 유형별(클래스 경계 / 박스 범위 / 구역 분할 / 누락)로 분류한다.
- 정의·규칙을 고칠 때는 `annotation_taxonomy_plan.md` 변경 이력에 "무엇을·어느 사례 때문에"를 적고 v2 태그를 만든다. 파일럿 전에 동결한 v1.1은 그대로 둔다.
- 클래스 빈도 외삽(인스턴스 × 993/60)으로 50개 미만 클래스의 병합 여부를 정한다.

## 7. 파일

| 파일 | 용도 |
|---|---|
| `annotation/classes.yaml` | 체계 v1.1의 기계용 정의(클래스·속성·매핑·엣지 스키마) |
| `annotation/label_studio_config.xml` | Label Studio 라벨 설정(T1 + 일부 T2 필드, 관계) |
| `annotation/cvat_labels.json` → `s17 --expand-cvat` | CVAT 라벨 정의(엣지 제외) |
| `docs/annotation_guideline_v1.md` | 어노테이터 규칙서 |
| `s17_pilot_agreement.py` | 일치도 계산 |
| `data/pilot/` | 표본 60장, 배분표, 접촉 시트 |
