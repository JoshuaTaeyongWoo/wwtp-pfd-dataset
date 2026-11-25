# 파일럿 어노테이션 실행 안내 (60장, 어노테이터 2명 + 판정자 1명)

> **현재 절차 = 쉬운 버전 v1.1b (2026-11-18)**: 1~20번 완전판, 21~60번 쉬운 버전(화살촉·글자 박스 생략, 엣지는 방향만). 적용 설정 `annotation/label_studio_config_lite.xml`(v2 그룹 배치, 2026-11-25; pilot_A·pilot_B·practice에 반영됨). 매뉴얼 `manual/WWTP_annotation_manual_v1_lite.pdf`(9쪽) + `manual/WWTP_cheat_sheet.pdf`(1쪽). 매체·역할은 내보낸 뒤 `python data_collection/s19_infer_edge_medium.py --export … --out …` 로 채운다(규칙표 `annotation/edge_medium_rules.md`). 완전판 매뉴얼(17쪽)은 본 작업용.

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
- **터널 끊김 (2026-11-25 교훈)**: 임시 터널은 노트북이 잠들거나 네트워크가 바뀌어 잠시 끊기면 Cloudflare 쪽에서 삭제되고, cloudflared는 `Unauthorized: Tunnel not found`만 반복하며 복구되지 않는다(11-19 터널과 11-25 첫 터널 모두 이렇게 죽음). 그래서 `annotation/run_tunnel.ps1`을 사용자 PowerShell에서 띄워 둔다: 이 오류가 보이거나 프로세스가 죽으면 자동 재시작하고, 현재 주소를 화면과 `data/pilot/tunnel_url.txt`에 쓴다. 주소는 재시작마다 바뀌므로 그때마다 어노테이터에게 알린다. 고정 주소가 필요하면 ngrok 무료 계정의 고정 도메인(계정 가입 필요) 또는 Cloudflare 계정 + 보유 도메인의 named tunnel을 쓴다.
  ```powershell
  powershell -ExecutionPolicy Bypass -File data_collectionnnotation
un_tunnel.ps1
  ```
- **고정 주소 확정 (2026-11-26 00시경)**: `https://decent-reopen-curable.ngrok-free.dev` (ngrok 무료 dev domain, 재시작해도 동일). 어노테이터에게 이 주소를 보낸다. 노트북에서 켜 둘 것 두 가지(둘 다 Claude 앱 밖 PowerShell):
  ```powershell
  $env:CSRF_TRUSTED_ORIGINS='https://*.trycloudflare.com,https://decent-reopen-curable.ngrok-free.dev'; $env:DISABLE_SIGNUP_WITHOUT_LINK='1'; label-studio start --port 8080
  ```
  ```powershell
  ngrok http --url=decent-reopen-curable.ngrok-free.dev 8080
  ```
  위 두 명령을 한 번에 하는 스크립트: `powershell -ExecutionPolicy Bypass -File data_collection\annotation\start_pilot.ps1` (서버·ngrok이 이미 돌고 있으면 건너뛰고, 마지막에 공개 주소 응답을 확인). 노트북이 잠들었다 깨어난 경우에는 아무것도 할 필요 없다(프로세스 유지, ngrok 자동 재접속); 재부팅·창 닫힘 때만 실행.
  설치 교훈: `winget install ngrok.ngrok`은 3.3.1(2023)을 설치하는데 무료 계정은 에이전트 3.30 이상을 요구해 `ERR_NGROK_121`로 거부되고 `--url`도 모른다 → `ngrok update`로 3.39로 올린 뒤 정상. 토큰은 `ngrok config add-authtoken …`(사용자 실행, `%LOCALAPPDATA%\ngrok\ngrok.yml`). 검증(2026-11-26): 로그인 페이지 200, 로그인 POST 200(CSRF 통과), 가입 POST 403, API 무토큰 401. Cloudflare 임시 터널과 `run_tunnel.ps1`은 예비용으로만 남김.
- **고정 주소 (ngrok, 2026-11-25 안내)**: 임시 터널 대신 ngrok 무료 계정의 개발 도메인(계정당 1개, 재시작해도 같은 주소, `https://<이름>.ngrok-free.app`)을 쓰면 어노테이터에게 주소를 한 번만 알리면 된다. 무료 한도: 월 1 GB 송신, 월 2만 요청, 동시 엔드포인트 3개(파일럿 규모면 충분). 브라우저로 처음 열면 'ngrok가 제공하는 사이트' 경고 페이지가 한 번 뜨며 Visit을 누르면 7일간 안 뜬다. 절차(계정·토큰은 사용자가 직접): ① https://dashboard.ngrok.com 가입(무료) → ② Setup & Installation의 Windows 안내대로 설치(`winget install ngrok.ngrok`) → ③ 대시보드 'Your Authtoken'의 명령 `ngrok config add-authtoken …`을 PowerShell에서 실행(토큰은 Claude에 주지 않는다) → ④ 대시보드 Domains에서 할당된 개발 도메인 확인 → ⑤ 서버를 켤 때 `CSRF_TRUSTED_ORIGINS`에 그 도메인을 추가: `$env:CSRF_TRUSTED_ORIGINS='https://*.trycloudflare.com,https://<이름>.ngrok-free.app'` → ⑥ 다른 PowerShell에서 `ngrok http --url=<이름>.ngrok-free.app 8080`. 확인은 Cloudflare 때와 같이 로그인 POST 200, 가입 403.
- 노트북 절전 끄기(한국 낮 = 네덜란드 밤에 켜져 있어야 함): `powercfg /change standby-timeout-ac 0; powercfg /change hibernate-timeout-ac 0`
- 확인(2026-11-19): 공개 주소에서 로그인 페이지 200, 더미 로그인 POST가 CSRF 403 없이 처리됨, `/user/signup/` 차단, API로 pilot_A(60)·pilot_B(60)·practice(5) 조회됨.
- 어노테이터에게 보낼 것: 접속 주소, 판정자 계정 이메일·**임시 비밀번호**(파일럿 전 변경, 끝나면 다시 변경), "A는 pilot_A, B는 pilot_B만 연다", Settings·삭제·Account & Settings(토큰)는 건드리지 않는다.
- 백업: DB는 `C:\Users\<user>\AppData\Local\label-studio\label-studio\label_studio.sqlite3` 한 파일. 시작 전과 매일 한 번 `python data_collection/s27_export_from_db.py --backup`(→ `data/pilot/ls_backup/label_studio_YYYYMMDD_HHMM.sqlite3`, git 제외; 앱 안에서도 진짜 DB를 복사한다, §5 참고). 되돌리려면 서버를 끄고 파일을 덮어쓴다.
- 대안(검토함): Tailscale Funnel은 랩 테일넷에서 관리자가 허용하지 않아 불가(허용되면 고정 주소 `https://taeyong.tail18d6e9.ts.net`). 본 작업(수천 장)은 한국 랩 리눅스 서버(테일넷 `26-pf-10-*`)에 설치하는 쪽이 맞다.

## 3. 어노테이터 교육 (2시간 + 연습 5장)

진행 대본: **`docs/annotation_training_script.md`** (PDF `manual/WWTP_training_script.pdf`, 9쪽: 시간표, 보여 줄 것·말할 것·확인 질문, 연습 5장의 예상 질문과 답). 연습 이미지 5장은 `s20_practice_set.py`가 골라 `data/pilot/practice/`에 두고 Label Studio 프로젝트 `practice`(id 3)에 올려 둠(파일럿 60장과 겹치지 않음).

- **따라하기 설명서 (2026-11-25)**: `annotation/manual/WWTP_annotation_tutorial_v1.pdf` (Word 원본 `.docx`, 생성 `build_tutorial.py` + 그림 `make_tutorial_figures.py` → `figures_tutorial/`). 처음 하는 사람이 혼자 읽고 따라 하도록 접속 → 화면 → 첫 박스 → 이름 고르기(실제 그림 조각 갤러리 9장) → 구역 → 연결 요소 → 선 긋기 → 제출 → 1번 그림 전 과정 → 연습 5장 정답 → 체크리스트 순으로, 단계마다 실제 Label Studio 화면 캡처(`figures_tutorial/U*.png`, 15장)를 넣었다. 캡처 방법: Claude 앱 안에서는 브라우저 패널을 PrintWindow로 창 단위 캡처하고(가려져도 됨, 최소화만 아니면), 박스 드래그는 Chrome_RenderWidgetHostHWND 자식 창에 마우스 메시지를 직접 보내서 했다(스크립트는 세션 scratchpad `win.ps1`/`shot.sh`; 재캡처가 필요하면 같은 방법). 캡처는 설정 v2(압축 배치) 기준으로 11-25 저녁에 전부 다시 찍었고(U01~U15), 쉬운 버전 매뉴얼 그림 2도 같은 캡처로 다시 그렸다(`make_manual_figures.f2_ui_callouts`). **단축키 정정**: 이 Label Studio(1.23) 버전에서 관계 만들기는 `Alt+R`이다(`R` 단독 = 사각형 도구). 설정 XML·매뉴얼·치트시트·대본·규칙서의 'r' 표기를 모두 고치고 세 프로젝트 설정을 s18로 갱신했다(2026-11-25). PDF 변환: `python annotation/manual/make_pdf.py A.docx B.docx …` (Word COM).
- 읽을 것: **`annotation/manual/WWTP_annotation_manual_v1.pdf`** (그림 포함 초보자용 매뉴얼 17쪽; Word 원본 `.docx`, 생성 스크립트 `manual/build_manual.py`·`make_manual_figures.py`). 규칙 원문은 `docs/annotation_guideline_v1.md`.
- 연습: `data/pilot/images/`가 아닌 main의 다른 5장(판정자가 고름)으로 연습하고, 판정자와 함께 맞춰 본다. 연습 결과는 버린다.
- 단축키(설정 v2, 2026-11-25): 숫자 1~0 = 자주 쓰는 장치 10개, `a` = pump, `x`/`z` = generic/unknown, `i`/`j`/`l` = io_terminal/junction_split/junction_merge, `Alt+R` = 관계(연결; `R` 단독은 사각형 도구). 나머지 라벨은 단축키 없음(`hotkey=" "`로 자동 배정을 막음; 빈 문자열은 소용없음), `Ctrl+Enter` = 제출.

## 4. 라벨링

- 60장을 **각자** 전부. 중간에 상의하지 않는다. 막히면 `annotator_note`에 적는다.
- 한 장 완료 기준: 모든 장치·구역·연결 요소 박스, 박스마다 visual_form·confidence·label_text, 구역은 is_zone + parent_of, 흐름 엣지 전부, 이미지 속성(diagram_style, language, n_panels).

## 5. 내보내기와 일치도

각 프로젝트에서 Export → JSON → `data/pilot/exports/pilot_A.json`, `pilot_B.json`. 서버가 꺼져 있어도 DB 파일에서 바로 뽑을 수 있다(2026-11-24, `s27_export_from_db.py`; 진행 상황 확인·백업도 같은 스크립트):

```bash
python data_collection/s27_export_from_db.py --status                                  # 프로젝트별 task·어노테이션 수, 소요 시간, 마지막 제출 시각
python data_collection/s27_export_from_db.py --export pilot_A,pilot_B --out data/pilot/exports
python data_collection/s27_export_from_db.py --backup                                  # data/pilot/ls_backup/label_studio_YYYYMMDD_HHMM.sqlite3
```

> **Claude 앱 안에서 DB를 읽을 때 (2026-11-24 교훈)**: 앱 샌드박스는 `AppData\Local`을 가상화하므로 `C:\Users\<u>\AppData\Local\label-studio\…`는 11-17의 빈 복사본(어노테이션 0, 옛 설정)으로 보인다. 11-19에 만든 백업 두 개도 이 빈 복사본이었다(`ls_backup/_sandbox_copies_invalid/`로 옮김). 루프백 관리 공유 `\\localhost\C$\Users\<u>\AppData\Local\…`는 가상화를 우회해 진짜 파일을 보여 주며, s27의 기본 `--db`가 이 경로다. 검증: dryrun_A·B를 s27로 뽑아 s17을 돌리면 11-19 API 내보내기 결과와 수치가 같다(κ_L2 0.930, 불일치 117행). 2026-11-24 `--status`: pilot_A·pilot_B 어노테이션 0건(서버 마지막 활동 11-19 18:03).

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
