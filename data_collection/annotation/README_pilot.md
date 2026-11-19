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
