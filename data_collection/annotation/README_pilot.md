# 파일럿 어노테이션 실행 안내 (60장, 어노테이터 2명 + 판정자 1명)

> **현재 절차 = 쉬운 버전 v1.1b (2026-11-18)**: 1~20번 완전판, 21~60번 쉬운 버전(화살촉·글자 박스 생략, 엣지는 방향만). 적용 설정 `annotation/label_studio_config_lite.xml`(두 프로젝트에 반영됨). 매뉴얼 `manual/WWTP_annotation_manual_v1_lite.pdf`(9쪽) + `manual/WWTP_cheat_sheet.pdf`(1쪽). 매체·역할은 내보낸 뒤 `python data_collection/s19_infer_edge_medium.py --export … --out …` 로 채운다(규칙표 `annotation/edge_medium_rules.md`). 완전판 매뉴얼(17쪽)은 본 작업용.

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

## 2b. 원격 접속 (판정자 네덜란드, 어노테이터 한국; 2026-11-19 설정)

서버는 판정자 노트북에서 돌고, **Cloudflare 임시 터널**로 공개 주소를 받아 한국에서 접속한다. 어노테이터는 아무것도 설치하지 않고 브라우저로 접속해 **판정자 계정으로 로그인**한다(파일럿 한정; 본 작업은 개인 계정). 작업 구분은 계정이 아니라 프로젝트(pilot_A / pilot_B)로 한다.

- 서버 켜기 (판정자, **윈도우에서 직접 연 PowerShell**; Claude 앱 안 터미널은 AppData가 가상화되어 빈 DB를 봄):
  ```powershell
  $env:CSRF_TRUSTED_ORIGINS='https://*.trycloudflare.com'; $env:DISABLE_SIGNUP_WITHOUT_LINK='1'; label-studio start --port 8080
  ```
  `CSRF_TRUSTED_ORIGINS`가 없으면 공개 주소에서 로그인 POST가 403으로 막힌다. `DISABLE_SIGNUP_WITHOUT_LINK=1`은 초대 링크 없는 가입 차단.
- 터널 켜기 (다른 PowerShell 창; `winget install Cloudflare.cloudflared`로 설치됨, `C:\Program Files (x86)\cloudflared\`):
  ```powershell
  cloudflared tunnel --url http://localhost:8080
  ```
  출력의 `https://<임의단어>.trycloudflare.com`이 접속 주소. **터널을 다시 켤 때마다 주소가 바뀌므로** 그때마다 어노테이터에게 다시 알린다. 계정 없이 쓰는 임시 터널이라 SLA가 없다; 끊기면 재실행.
- 노트북 절전 끄기(한국 낮 = 네덜란드 밤에 켜져 있어야 함): `powercfg /change standby-timeout-ac 0; powercfg /change hibernate-timeout-ac 0`
- 확인(2026-11-19): 공개 주소에서 로그인 페이지 200, 더미 로그인 POST가 CSRF 403 없이 처리됨, `/user/signup/` 차단, API로 pilot_A(60)·pilot_B(60)·practice(5) 조회됨.
- 어노테이터에게 보낼 것: 접속 주소, 판정자 계정 이메일·**임시 비밀번호**(파일럿 전 변경, 끝나면 다시 변경), "A는 pilot_A, B는 pilot_B만 연다", Settings·삭제·Account & Settings(토큰)는 건드리지 않는다.
- 백업: DB는 `C:\Users\<user>\AppData\Local\label-studio\label-studio\label_studio.sqlite3` 한 파일. 시작 전과 매일 한 번 `data/pilot/ls_backup/label_studio_YYYYMMDD_HHMM.sqlite3`로 복사(git 제외). 되돌리려면 서버를 끄고 파일을 덮어쓴다.
- 대안(검토함): Tailscale Funnel은 랩 테일넷에서 관리자가 허용하지 않아 불가(허용되면 고정 주소 `https://taeyong.tail18d6e9.ts.net`). 본 작업(수천 장)은 한국 랩 리눅스 서버(테일넷 `26-pf-10-*`)에 설치하는 쪽이 맞다.

## 3. 어노테이터 교육 (2시간 + 연습 5장)

진행 대본: **`docs/annotation_training_script.md`** (PDF `manual/WWTP_training_script.pdf`, 9쪽: 시간표, 보여 줄 것·말할 것·확인 질문, 연습 5장의 예상 질문과 답). 연습 이미지 5장은 `s20_practice_set.py`가 골라 `data/pilot/practice/`에 두고 Label Studio 프로젝트 `practice`(id 3)에 올려 둠(파일럿 60장과 겹치지 않음).

- 읽을 것: **`annotation/manual/WWTP_annotation_manual_v1.pdf`** (그림 포함 초보자용 매뉴얼 17쪽; Word 원본 `.docx`, 생성 스크립트 `manual/build_manual.py`·`make_manual_figures.py`). 규칙 원문은 `docs/annotation_guideline_v1.md`.
- 연습: `data/pilot/images/`가 아닌 main의 다른 5장(판정자가 고름)으로 연습하고, 판정자와 함께 맞춰 본다. 연습 결과는 버린다.
- 단축키: 숫자 1~0 = 자주 쓰는 클래스, `r` = 관계, `Ctrl+Enter` = 제출.

## 4. 라벨링

- 60장을 **각자** 전부. 중간에 상의하지 않는다. 막히면 `annotator_note`에 적는다.
- 한 장 완료 기준: 모든 장치·구역·연결 요소 박스, 박스마다 visual_form·confidence·label_text, 구역은 is_zone + parent_of, 흐름 엣지 전부, 이미지 속성(diagram_style, language, n_panels).

## 5. 내보내기와 일치도

각 프로젝트에서 Export → JSON → `data/pilot/exports/pilot_A.json`, `pilot_B.json`.

```bash
python data_collection/s17_pilot_agreement.py --a data/pilot/exports/pilot_A.json --b data/pilot/exports/pilot_B.json --full-subset 20 --out data/pilot/agreement.md --disagreements data/pilot/disagreements.csv
python data_collection/s19_infer_edge_medium.py --export data/pilot/exports/pilot_A.json --out data/pilot/graphs_A
python data_collection/s19_infer_edge_medium.py --export data/pilot/exports/pilot_B.json --out data/pilot/graphs_B
```

출력: L2/L1 κ, IoU ≥ 0.7 비율, 누락·추가 비율, 엣지 P/R/F1, 클래스별 κ(매칭 ≥ 20), 부트스트랩 95 % CI. 목표 κ ≥ 0.8. `--disagreements`는 판정자용 표(§6): 그림·종류(class / attr / box_only / edge_only / edge_label / image)·A값·B값·힌트·빈 decision 열.
매칭: IoU ≥ 0.5 탐욕 매칭 뒤, 둘 다 작은 박스(이미지 면적 0.2 % 미만: 분기·합류·화살촉·밸브)는 중심 거리로 보조 매칭(작은 박스는 몇 px 흔들림에도 IoU 0.5가 깨짐; 보조 매칭된 쌍은 IoU 통계에서 제외).

**예행연습(2026-11-19, 실제 결과 전에 파이프라인 검증)**: `s21_dryrun_synthetic.py`가 버리는 프로젝트 `dryrun_A`·`dryrun_B`(파일럿 1·2·3·21·22·23번 6장)에 합성 라벨(B는 일부러 다르게: 박스 이동·누락·추가, 클래스 바꿈, 엣지 누락·역방향, 관계 라벨 차이)을 넣고 내보내 위 명령을 끝까지 돌림. 이때 고친 것: ① Label Studio가 업로드 파일명 앞에 붙이는 8자리 해시(`3e304446-pilot_01__…`) 때문에 두 내보내기의 같은 그림이 다른 키가 되고 번호 인식이 실패하던 문제(s17·s19 키 정규화), ② 작은 박스 보조 매칭, ③ 중복 관계 제거(s19), ④ 규칙 32·33 추가(전처리→본류 = influent, 2차 침전지→3차 = effluent; 전에는 unknown_role). 출력 예: `data/pilot/exports/dryrun_agreement.md`, `dryrun_disagreements.csv`, `graphs_dryrun_*`. 실제 결과가 오면 파일 경로만 바꿔 같은 명령을 돌린다.

## 5b. 정답 변환과 모델 평가 (파일럿 뒤·본 작업 공통)

판정이 끝난 내보내기(또는 한 어노테이터의 내보내기)를 벤치마크 정답으로 바꾸고, 어떤 모델이든 같은 형식으로 출력하면 같은 지표로 평가한다.

```bash
python data_collection/s22_export_to_gt.py --export data/pilot/exports/pilot_adjudicated.json --out data/pilot/gt --split 0.7,0.15,0.15
python data_collection/s23_eval_graph.py --gt data/pilot/gt --pred <모델 출력 폴더> [--pred-coco results.json] --out data/pilot/eval_model.md
```

- s22 출력: `coco.json`(L2 41 범주, supercategory = L1, 박스마다 속성), `graphs/*.graph.json`(§4.6, s19 규칙으로 매체 채움), `manifest.csv`(그림별 출처·언어·diagram_style), `splits.json`(문서 단위, 출처별 층화, 시드 고정).
- 모델 출력 형식: `graphs/<key>.graph.json`(노드 bbox px + `semantic_class`/`l2` + `score`, 엣지 src/dst). 검출만 하는 모델은 COCO results JSON을 `--pred-coco`로.
- s23 지표(계획서 §6): AP50·AP[.5:.95]를 L2와 L1(접기)에서, LVIS 구간(rare ≤ 10장 / common ≤ 100 / frequent), `visual_form`·diagram_style·출처·언어 층화; 박스형 정답의 L2 매핑 정확도; 노드 매칭(IoU ≥ 0.5, 클래스 요구/비요구) 뒤 엣지 P/R/F1, 방향 정확도(화살촉 근거 / 전체), 추론 엣지 재현율, 정규화 그래프 편집 거리.
- 자기 검사: 같은 폴더를 `--gt`와 `--pred`로 주면 모든 지표가 1.0(편집 거리 0)이어야 한다. 예행연습 출력 `data/pilot/exports/eval_dryrun_A_vs_B.md`.

## 5c. VLM 제로샷 기준선 (사람 라벨 0장)

```bash
pip install anthropic            # 한 번
$env:ANTHROPIC_API_KEY = '...'   # 사용자 터미널에서; 저장소에 적지 않는다
python data_collection/s24_vlm_baseline.py --images data/pilot/images --out data/pilot/vlm_opus55 --overlay [--limit 3]
python data_collection/s23_eval_graph.py --gt data/pilot/gt --pred data/pilot/vlm_opus55 --out data/pilot/eval_vlm_opus55.md
```

- 그림 한 장당 요청 한 번. 시스템 프롬프트에 분류 체계(`classes.yaml`의 33 L2 + 필수 L3 + 연결 4종 = 47개 선택지, 정의·별칭)와 규칙 10개를 넣고, 구조화 출력(JSON 스키마, 클래스는 enum)으로 노드·엣지·부모 관계·그림 속성을 받는다. 좌표는 모델에 보낸 이미지 픽셀(긴 변 1568 이하로 축소)이며 원본 크기로 되돌려 저장한다.
- 출력은 s23 예측 형식 `graphs/*.graph.json` + `_raw/`(응답 원문·usage) + `_summary.csv`(장당 노드·엣지·시간·토큰·추정 비용) + `_run.json`(날짜·모델·effort·프롬프트·스키마, 논문 재현용) + `--overlay`면 `overlays/*.png`.
- 기본 모델 `claude-opus-5-5`, effort high, 거부 시 서버측 대체 모델(`fallbacks="default"`); `_summary.csv`의 `model_served`로 실제 응답 모델을 확인한다. 다시 실행하면 이미 있는 그림은 건너뛴다(재개).
- 이 수치는 "사람 라벨 없이 얻을 수 있는 성능"이다. 사람 라벨로 학습한 모델과 같은 시험 세트·같은 s23 지표로 비교하는 것이 §6 기준선 비교의 한 축이다. 사람 라벨을 프롬프트에 예시로 넣는 few-shot 변형은 `--examples`로 추후 추가.

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
