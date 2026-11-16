# WWTP 공정흐름도(PFD) 수집 파이프라인 — 방법론 및 결과

작성일: 2026-11-16. 목적: 하수처리장(WWTP) 공정흐름도 디지털화 연구용 이미지 데이터셋 구축.
선행 연구(Theisen et al., 2023, *Digital Chem. Eng.* 6:100072)가 화공 PFD 1,005장을 저널·백과사전·검색엔진에서
수집한 방식을 WWTP 도메인에 맞게 재구성하되, **모든 이미지의 출처·취득 경로·라이선스를 기계가 읽을 수 있는
provenance 레코드로 남기고**, 재배포 가능한 라이선스(tier A)와 연구 내부용(tier B)을 처음부터 구분한다.

## 1. 디렉터리 구조

```
WWTP_vision/
├─ Ref/                                  참고 논문
├─ data_collection/                      이 문서와 모든 코드
│   ├─ common.py                         공통: HTTP 세션, 다운로드, 해시, provenance 레코드, 캡션 필터, 라이선스 tier
│   ├─ pdf_figures.py                    PDF에서 캡션 매칭 페이지의 그림 추출 (PyMuPDF)
│   ├─ s01_europepmc_pmc.py              소스 1  Europe PMC 검색 → PMC OA S3 버킷에서 그림 취득
│   ├─ s02_wikimedia_commons.py          소스 2  Wikimedia Commons API
│   ├─ s03_epa_manuals.py                소스 3  US EPA 설계 매뉴얼(공공저작물) PDF
│   ├─ s04_patents.py                    소스 4  Google Patents 특허 도면
│   ├─ s05_openalex_nonpmc.py            소스 5  OpenAlex → PMC 밖의 OA 논문 PDF
│   ├─ s06_korean_municipal.py           소스 6  한국 지자체·공단 하수처리장 홈페이지
│   ├─ s07_dedup_catalog.py              통합 카탈로그, 중복 제거, 통계
│   ├─ s08_review_gallery.py             수작업 선별용 HTML 갤러리
│   ├─ s09_make_sheets.py                20장 단위 대조표(contact sheet) 생성 (AI 1차 선별 입력)
│   ├─ s10_merge_triage.py               AI 1차 선별 결과 병합 → triage_ai.csv, 갤러리에 미리 채움
│   ├─ TRIAGE_CRITERIA.md                선별 기준 (keep / unsure / reject, 카테고리)
│   └─ requirements.txt
└─ data/
    ├─ raw/<source>/...                  원본 파일 (수정하지 않음)
    ├─ provenance/<source>.jsonl         파일 1개당 레코드 1줄 (append-only)
    ├─ logs/                             실행 로그
    ├─ catalog.csv / catalog_canonical.csv   통합 카탈로그 (전체 / 중복 제거)
    ├─ stats.md                          통계표 (s07이 생성)
    ├─ triage_ai.csv / triage_stats.md   AI 1차 선별 결과 (s10이 생성)
    ├─ review/sheets/                    대조표 159장 + sheets.json
    ├─ review/decisions/*.csv            선별 결정 (에이전트 7개 + 수작업 1개)
    └─ review/*.html                     선별 갤러리 (s08이 생성)
```

실행 순서: `pip install -r requirements.txt` → `s01`~`s06` (서로 독립, 병렬 가능, 모두 재실행 시 이어받기) → `s07` → `s08` → `s09` → (AI/사람 선별) → `s10`.

## 2. Provenance 레코드 (모든 소스 공통)

| 필드 | 내용 |
|---|---|
| `record_id` | `<source>:<doc_id>:<filename>` 고유키 |
| `source` / `tier` | 소스명 / A = 재배포 가능(CC0, CC BY, CC BY-SA, 공공저작물), B = 연구 내부용(CC BY-NC·ND, 라이선스 불명) |
| `image_path`, `sha256`, `phash`, `image_size` | 로컬 경로, 정확 중복용 해시, 근사 중복용 perceptual hash, 픽셀 크기 |
| `acquired_at`, `acquisition_method` | 취득 시각(UTC), 취득 경로 설명(API → 파일 URL 등) |
| `file_url`, `landing_url` | 파일 직접 URL, 사람이 보는 문서 페이지 |
| `license`, `license_url`, `rights_holder` | 라이선스 문자열, 라이선스 URL, 저작권자·저자 |
| `doc_id`, `title`, `venue`, `year`, `doi` | 문서 식별자(PMCID/DOI/특허번호/파일명), 제목, 저널·기관, 연도 |
| `figure_label`, `caption` | 그림 번호, 캡션 원문 |
| `query`, `filter_rule` | 이 파일을 찾아낸 검색식, 통과한 필터 규칙(캡션 tier 등) |
| `extra` | 소스별 부가 정보(페이지 번호, CPC 코드, S3 버전 등) |

## 3. 소스별 취득 방법

### 소스 1. 오픈액세스 저널 논문 (PMC Open Access Subset) — `s01_europepmc_pmc.py`
1. **후보 검색**: Europe PMC REST API (`/search`, cursorMark 페이징, `resultType=core`)에 전문(BODY) 검색식
   `("wastewater treatment plant" OR "sewage treatment plant" OR "water resource recovery facility" OR "wastewater treatment works" OR "sewage treatment works" OR "wastewater treatment facility") AND OPEN_ACCESS:y AND HAS_FT:y`
   → PMCID, DOI, 제목, 저널, 연도, 라이선스.
2. **그림 취득**: PMC OA 웹서비스와 FTP가 2026년에 폐지되어, 공식 후속 경로인 AWS Open Data 버킷
   `s3://pmc-oa-opendata`(익명 읽기, HTTPS `https://pmc-oa-opendata.s3.amazonaws.com/`)를 사용. 논문별 prefix
   `PMC<id>.<version>/`에 JATS XML, PDF, 그림 파일(jpg/png/webp), 라이선스 JSON이 있다. XML의 `<fig>`에서
   `<label>`, `<caption>`, `<graphic xlink:href>`를 읽고, 캡션이 필터를 통과한 그림만 내려받는다.
3. **캡션 필터** (`common.caption_tier`): 다이어그램 단어(flow diagram, flowsheet, schematic, layout, configuration,
   treatment train, block diagram …)가 있고, 제외어(sampling site, map of, photograph, SEM, chromatogram, Venn,
   pie chart, microbial community, graphical abstract …)가 없을 때, **T1** = 캡션에 플랜트 단위 단어(treatment plant,
   WWTP, STP, WRRF, full-scale plant, treatment line …)가 있음, **T2** = 처리 관련 단어(treatment, sludge, clarifier,
   digester, MBR …)만 있음(단일 반응기·파일럿 등). T1이 PFD 후보의 핵심이며 T2는 수작업 선별 대상.
4. 라이선스는 S3 JSON(없으면 Europe PMC)에서 읽어 tier를 정한다. 저자 정보는 attribution용으로 보존.
5. 동일 논문의 여러 버전이 있으면 최신 버전 prefix를 사용. 재실행 시 `_processed_pmcids.txt`로 이어받기.

### 소스 2. Wikimedia Commons — `s02_wikimedia_commons.py`
MediaWiki API: 파일 네임스페이스(ns=6) 전문검색 19개 질의(영·독·불·서·한·일·중) + 관련 카테고리 8개와 1단계 하위
카테고리의 파일 목록 → `prop=imageinfo`(원본 URL, MIME, 크기, `extmetadata`의 LicenseShortName/LicenseUrl/Artist).
제목 정규식 필터 후 래스터·SVG만 다운로드(PDF·DjVu 스캔은 제외). 폭 300 px 미만 제외.

### 소스 3. US EPA 설계 매뉴얼·보고서 — `s03_epa_manuals.py`
epa.gov(및 epa.gov 공식 스냅샷 호스트)에 있는 PDF를 큐레이션 목록으로 다운로드. 첫 6쪽 텍스트가 제목 단어와
맞는지 검사(잘못된 문서 방지). `pdf_figures.extract`: 각 페이지에서 "Figure n-m. …" 형태 캡션 줄을 찾아 캡션 필터 적용,
통과한 페이지의 **내장 래스터 이미지 + 200 dpi 전체 페이지 렌더**를 모두 저장(설계 매뉴얼의 흐름도는 대부분 벡터
드로잉이거나 스캔이라 페이지 렌더가 실제 사용 가능한 산출물이며, 어노테이션 때 crop이 필요). 미국 연방정부 저작물은
저작권 대상이 아님(17 U.S.C. §105) → tier A. 단 매뉴얼 안에 재수록된 제3자 그림은 선별 시 확인.
텍스트 레이어가 없는 스캔본(1977, 1980 매뉴얼)은 OCR이 없어 캡션 매칭이 불가하여 0건으로 기록됨(향후 OCR 적용 대상).

### 소스 4. 특허 도면 — `s04_patents.py`
Google Patents 공개 검색이 사용하는 JSON 엔드포인트(`/xhr/query`)로 CPC `C02F3`(생물학적 수처리), `C02F11`(슬러지),
`C02F9`(다단 처리) × 검색식("wastewater treatment plant" "flow diagram" 등)의 결과를 모으고, 각 특허 공개 페이지의
`<meta itemprop="full">`에 나열된 원본 도면 이미지를 내려받는다(요청 간격 2 s, 특허당 최대 6면). 특허 도면은 공개
문서이며 미국에서는 복제에 저작권 제한이 없음 → tier A(비미국 특허는 국가별 확인 필요). 도면에는 캡션이 없으므로
전수 수작업 선별 대상. 스타일이 블록 흐름도(숫자 참조부호)라 논문 PFD와 다름 → 보조 학습용.

### 소스 5. PMC 밖의 OA 논문 — `s05_openalex_nonpmc.py`
OpenAlex `/works` 검색(`is_oa:true`, PMCID 없음)으로 `best_oa_location.pdf_url`과 라이선스를 받아 PDF를 내려받고
`pdf_figures.extract` 적용. **정직한 User-Agent로 PDF를 돌려주는 서버만 사용**하고, 자동 접근을 차단하는 출판사
(HTML challenge 페이지 반환)는 건너뛰며 로그에 호스트별 차단 수를 남긴다. 브라우저 위장 헤더는 사용하지 않았다.

### 소스 6. 한국 지자체·공단 하수처리장 홈페이지 — `s06_korean_municipal.py`
큐레이션한 공개 페이지 목록(운영기관 | 시설 | URL)을 2 s 간격으로 받아 `<img>` 중 공정 키워드(공정, 계통, 처리과정,
flow, process …)가 src/alt에 있거나 폭 500 px 이상인 콘텐츠 이미지를 저장. 페이지에 링크된 공정 PDF와 홍보
브로슈어 PDF는 `pdf_figures.extract`(캡션 없으면 전 페이지 렌더) 적용. 페이지 HTML에서 공공누리(KOGL) 유형을
정규식으로 찾아 제1유형이면 tier A, 그 외·표시 없음은 tier B(운영기관 확인 전까지 내부용).

### 채택하지 않은 소스와 이유
- **Google/Bing 이미지 검색**: 선행 연구는 사용했으나 출처·라이선스 추적이 불가능해 공개 벤치마크에 넣을 수 없고,
  검색엔진 약관상 자동 수집이 제한됨. 내부 보조용으로도 제외.
- **교과서(Metcalf & Eddy, WEF MOP 8 등)**: 저작권 자료. 연구기관의 TDM 예외(EU DSM 지침 3조) 또는 공정이용으로
  내부 학습은 가능할 수 있으나 재배포 불가 → 본 파이프라인에서 제외, 필요 시 별도 tier B로 관리.
- **비OA 저널(Elsevier 등) 기관 구독 전문**: 동일 이유로 제외. 필요 시 `s05`와 같은 PDF 추출기를 기관 접속 환경에서
  돌려 tier B로 관리 가능.

## 4. 중복 제거와 카탈로그 — `s07_dedup_catalog.py`
sha256 동일 → 정확 중복, pHash(64 bit) 해밍거리 ≤ 6 → 근사 중복(같은 그림의 재인코딩, 페이지 렌더 vs 내장 이미지,
논문 간 재사용). 클러스터마다 tier A 우선, 그다음 취득 시각 순으로 대표(canonical)를 정하고 나머지는
`duplicate_of`로 표시(파일은 삭제하지 않음). 결과: `catalog.csv`, `catalog_canonical.csv`, `stats.md`.

## 5. 선별 — `s08_review_gallery.py`, `s09_make_sheets.py`, `s10_merge_triage.py`
소스별 HTML 갤러리(썸네일, 캡션, tier, 캡션 tier)에서 keep / reject / unsure를 눌러 CSV로 내보낸다. 선별 기준(안):
keep = 둘 이상의 단위공정이 기호 또는 박스로 그려지고 흐름선이 있는 플랜트·공정 수준 다이어그램; reject = 단일
장치 단면도, 실험장치도, 지도, 사진, 그래프; unsure = 사진형 일러스트(3D 탱크 그림) 등 포함 기준 결정 필요.

## 6. 결과

(실행 완료 후 `data/stats.md`의 표를 아래에 복사. 각 실행의 날짜·후보 수·수집 수·실패 원인은 `data/logs/`에 있음.)

### 6.1 실행 요약 (2026-11-16, 단일 PC, 순차·병렬 실행 약 2시간)

| 소스 | 스크립트 | 후보 규모 | 결과 |
|---|---|---|---|
| 1 PMC OA 논문 | s01 | Europe PMC 후보 10,323편 → S3 패키지 10,323건, 그림 56,617장 검사 | 캡션 통과 1,204장 (931편), 실패 0 |
| 2 Wikimedia Commons | s02 | 검색·카테고리로 4,705개 파일, 제목 필터 후 1,173개 | 1차 실행은 9장 후 중단(upload.wikimedia.org가 연락처 없는 UA에 HTTP 429, Retry-After 600 s). Wikimedia UA 정책에 따라 프로젝트 URL(github.com/JoshuaTaeyongWoo/wwtp-pfd-dataset)을 연락처로 넣어 재실행 → 635장(제목 필터가 넓어 무관한 그림 다수 포함, 수작업 선별 필요) |
| 3 US EPA | s03 | 큐레이션 33문서 (epa.gov 9, NEPIS 24) | 33건 모두 PDF 확보(약 500 MB), 캡션 매칭 238장(23문서). 스캔 OCR 품질이 낮은 10개 매뉴얼은 0장 |
| 4 특허 도면 | s04 | Google Patents 4개 질의, 상위 300건 | 도면 페이지 접근 189건, 796장 (특허당 ≤6면) |
| 5 OpenAlex 비PMC OA | s05 | 6개 질의 → OA PDF URL 보유 453편 | PDF 정상 수신 187편, 차단·비PDF 응답 266편(mdpi.com 76, sciencedirect.com 35, iwaponline.com 25, els-cdn 14, wiley 10 …), 332장 |
| 6 한국 지자체·공단 | s06 | 큐레이션 27페이지(검증 15 + 재시도 6 + 초기 6) | 접속 성공 20페이지, 97장 (브로슈어 전체 페이지 렌더 48장 포함); 6개 시 서버 TLS/접속 실패, 1개 403 |

### 6.2 통합 카탈로그 (`s07`, pHash ≤ 6 bit)

## Per source

| source            |   files_downloaded |   exact_or_near_duplicates |   canonical_files |   tier_A_canonical |   tier_B_canonical |   unique_documents |
|:------------------|-------------------:|---------------------------:|------------------:|-------------------:|-------------------:|-------------------:|
| epa_manuals       |                238 |                         70 |               168 |                168 |                  0 |                 23 |
| europepmc_pmc     |               1204 |                         19 |              1185 |                880 |                305 |                931 |
| korean_municipal  |                 95 |                          9 |                86 |                  0 |                 86 |                 15 |
| openalex_nonpmc   |                332 |                         25 |               307 |                100 |                207 |                106 |
| patents_google    |                796 |                         46 |               750 |                750 |                  0 |                184 |
| wikimedia_commons |                635 |                         17 |               618 |                596 |                 22 |                618 |
| TOTAL             |               3300 |                        186 |              3114 |               2494 |                620 |               1877 |

## Canonical files by licence

|                                                                                                   |   n |
|:--------------------------------------------------------------------------------------------------|----:|
| ('A', 'cc by')                                                                                    | 876 |
| ('A', 'Patent drawing (published patent document; US: no copyright restriction on reproduction)') | 750 |
| ('B', 'cc by-nc-nd')                                                                              | 181 |
| ('A', 'US Government work (public domain, 17 U.S.C. 105)')                                        | 168 |
| ('A', 'CC BY 2.0')                                                                                | 151 |
| ('A', 'Public domain')                                                                            | 134 |
| ('A', 'CC BY-SA 4.0')                                                                             | 109 |
| ('A', 'CC BY-SA 3.0')                                                                             | 101 |
| ('A', 'cc-by')                                                                                    |  98 |
| ('B', 'unknown (check 공공누리/KOGL with operator)')                                                  |  44 |
| ('B', 'cc by-nc')                                                                                 |  43 |
| ('B', 'cc-by-nc-nd')                                                                              |  34 |
| ('A', 'CC BY 3.0')                                                                                |  29 |
| ('A', 'CC BY-SA 2.0')                                                                             |  28 |
| ('B', 'cc-by-nc')                                                                                 |  26 |
| ('B', 'unknown (no KOGL mark found on page)')                                                     |  24 |
| ('A', 'CC BY 4.0')                                                                                |  18 |
| ('A', 'CC0')                                                                                      |  17 |
| ('B', 'public-domain')                                                                            |  14 |
| ('B', 'No restrictions')                                                                          |  13 |
| ('B', '공공누리(KOGL) 제4유형')                                                                          |  13 |
| ('B', 'other-oa')                                                                                 |   8 |
| ('A', 'CC BY-SA 3.0 de')                                                                          |   8 |
| ('B', '공공누리(KOGL) 제3유형')                                                                          |   5 |
| ('A', 'cc0')                                                                                      |   4 |

## Literature figures by caption tier (T1 = whole-plant diagram, T2 = treatment-related schematic, T0 = demoted by the v2 rule after download)

|                           |   n |
|:--------------------------|----:|
| ('europepmc_pmc', 'T0')   |  87 |
| ('europepmc_pmc', 'T1')   | 271 |
| ('europepmc_pmc', 'T2')   | 827 |
| ('openalex_nonpmc', 'T0') |   4 |
| ('openalex_nonpmc', 'T1') | 158 |
| ('openalex_nonpmc', 'T2') | 145 |

## Literature figures: tier x licence tier (canonical)

| caption_tier   |   A |   B |
|:---------------|----:|----:|
| T0             |  62 |  29 |
| T1             | 231 | 198 |
| T2             | 687 | 285 |

## Literature figures: top journals

| venue                                                                               |   n |
|:------------------------------------------------------------------------------------|----:|
| Membranes                                                                           | 130 |
| Scientific reports                                                                  | 100 |
| International journal of environmental research and public health                   |  61 |
| Heliyon                                                                             |  48 |
| RSC advances                                                                        |  39 |
| Environmental science and pollution research international                          |  37 |
| Nature communications                                                               |  36 |
| PloS one                                                                            |  36 |
| DUT Open Scholar (Durban University of Technology)                                  |  31 |
| Molecules (Basel, Switzerland)                                                      |  31 |
| InTech eBooks                                                                       |  27 |
| OSTI OAI (U.S. Department of Energy Office of Scientific and Technical Information) |  26 |
| Environmental science & technology                                                  |  24 |
| The Science of the total environment                                                |  23 |
| Environmental science and ecotechnology                                             |  22 |
| Materials (Basel, Switzerland)                                                      |  22 |
| Frontiers in microbiology                                                           |  20 |
| Sensors (Basel, Switzerland)                                                        |  19 |
| ACS ES&T engineering                                                                |  18 |
| ACS omega                                                                           |  17 |
| Environmental monitoring and assessment                                             |  14 |
| UPCommons institutional repository (Universitat Politècnica de Catalunya)           |  14 |
| Microorganisms                                                                      |  13 |
| Polymers                                                                            |  13 |
| Water research X                                                                    |  12 |

## Literature figures by year

|    |   1979 |   1994 |   2002 |   2003 |   2006 |   2007 |   2008 |   2009 |   2011 |   2012 |   2013 |   2014 |   2015 |   2016 |   2017 |   2018 |   2019 |   2020 |   2021 |   2022 |   2023 |   2024 |   2025 |   2026 |
|:---|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| n  |      9 |      1 |      1 |      2 |      5 |      1 |      6 |      3 |      9 |     18 |     26 |     27 |     52 |     69 |     33 |     50 |     67 |    109 |    160 |    191 |    129 |    164 |    171 |    189 |

### 6.3 1차 선별 (AI 보조, 2026-11-16)

`s09`가 canonical 3,114장을 20장짜리 대조표 159장으로 만들고, `TRIAGE_CRITERIA.md`의 기준(keep = 단위공정 2개 이상이
흐름선으로 연결된 플랜트·공정 수준 다이어그램, unsure = 3D 일러스트·단일 장치·다중 패널 중 일부·레이아웃, reject = 그래프·
지도·사진·생물학 모식도·연구 절차도)에 따라 비전 LLM 에이전트 7개가 병렬로 분류했다(대조표당 약 1~2분). 투명 배경
PNG/SVG 133장은 흰 배경으로 다시 렌더링해 사람이 직접 분류했다. 결과는 `data/triage_ai.csv`에 있고, 갤러리(`data/review/`)에
"AI: keep/unsure/reject" 배지와 함께 미리 채워져 있어 사람이 확인·수정만 하면 된다.

| 소스 | keep | unsure | reject | 합계 | keep 중 tier A |
|---|---|---|---|---|---|
| PMC OA 논문 | 307 | 206 | 672 | 1,185 | 228 |
| OpenAlex 비PMC | 170 | 40 | 97 | 307 | 67 |
| EPA 매뉴얼 | 87 | 40 | 41 | 168 | 87 |
| 특허 도면 | 334 | 200 | 216 | 750 | 334 |
| Wikimedia Commons | 36 | 132 | 450 | 618 | 31 |
| 한국 지자체 | 18 | 14 | 54 | 86 | 0 |
| **합계** | **952** | **632** | **1,530** | **3,114** | **747** |

keep+unsure의 카테고리: wwtp 1,060, pilot 241, other 156, sludge 72, wtp 39 (Wikimedia의 other는 대부분 화학·정유·발전
공정도로, 도메인 외 보조 데이터).

**AI 선별 정확도 (사람 표본 검사)**: keep 무작위 30장 중 27~28장이 기준에 맞는 공정도(정밀도 ≈ 0.90; 나머지는 단일 장치
단면도 2장), reject 무작위 30장 중 공정도 누락 0장. 따라서 keep 952장은 거의 그대로 쓸 수 있고, unsure 632장(3D 일러스트,
단일 반응기 파일럿, 다중 패널 그림 등)은 포함 기준을 정한 뒤 사람이 다시 봐야 한다.

**캡션 필터의 실제 정밀도 (문헌 소스, AI 선별 기준)**: T1 429장 중 keep 235(55%) / unsure 37 / reject 157; T2 972장 중
keep 223(23%) / unsure 196 / reject 553; v2 규칙으로 강등된 T0 91장 중 keep 19(21%). T1 정밀도 0.55는 6.3의 수작업 표본
추정(0.50~0.67)과 일치한다. T2에서도 223장이 나왔으므로 T2를 버리지 않은 것이 옳았다.

### 6.4 데이터셋 규모 (선별 후)

| 구분 | 수량 |
|---|---|
| keep (바로 사용 가능) | 952 |
| 그중 재배포 가능(tier A: CC BY/CC0/공공저작물/특허) | 747 |
| 그중 wwtp·sludge·wtp 카테고리 (도메인 핵심) | 약 820 |
| unsure (기준 완화 또는 crop 후 추가 가능) | 632 |
| EPA·브로슈어 페이지 렌더 중 crop 필요 | 약 110 |

선행 연구(Theisen et al., 1,005장)와 같은 규모의 WWTP 공정도 데이터셋이 확보되었고, 그중 약 78%가 공개 벤치마크로 재배포
가능하다. unsure에서 "단일 반응기 + 부대설비" 파일럿 도면을 포함하기로 하면 약 200장이 더 들어온다.

### 6.5 unsure 처리 규칙과 최종 분할 (2026-11-16 결정, `s11_apply_rules.py`)

unsure 632장을 AI 메모 기반으로 7개 부류로 나누고 다음과 같이 처리했다: 단일 장치+부대설비(233) → `aux_unit` 보조 세트,
3D·그림형(87) → `aux_pictorial` 보조 세트, crop 필요(99) → `crop_pending`(crop 후 main 승격), 레이아웃·질량수지·제어도(41) → 제외,
타 도메인 공정도(83) → `aux_other_domain`, 미분류·렌더 실패(89) → `manual_review`(사람 확인). 보조 세트는 벤치마크에서 빼되
단위공정 검출 학습이나 도메인 일반화 평가에 쓸 수 있도록 보존한다.

#### split by source

| source            |   aux_other_domain |   aux_pictorial |   aux_unit |   crop_pending |   excluded |   main |   manual_review |   total |
|:------------------|-------------------:|----------------:|-----------:|---------------:|-----------:|-------:|----------------:|--------:|
| epa_manuals       |                  0 |               3 |          8 |             23 |         46 |     87 |               1 |     168 |
| europepmc_pmc     |                 13 |              43 |         85 |             27 |        682 |    307 |              28 |    1185 |
| korean_municipal  |                  0 |               2 |          4 |              4 |         54 |     18 |               4 |      86 |
| openalex_nonpmc   |                  3 |               1 |          8 |             22 |         99 |    170 |               4 |     307 |
| patents_google    |                  3 |              18 |        109 |             21 |        234 |    334 |              31 |     750 |
| wikimedia_commons |                 64 |              20 |         19 |              2 |        456 |     36 |              21 |     618 |
| TOTAL             |                 83 |              87 |        233 |             99 |       1571 |    952 |              89 |    3114 |

## main split: licence tier x category

| tier   |   other |   pilot |   sludge |   wtp |   wwtp |
|:-------|--------:|--------:|---------:|------:|-------:|
| A      |      29 |      68 |       36 |    19 |    595 |
| B      |      12 |      27 |        6 |     8 |    152 |


main 952장 중 tier A(재배포 가능) 747장, 카테고리는 wwtp 747 / pilot 95 / sludge 42 / other 41 / wtp 27.
도구: `data/review/crop_tool.html`(상자를 그려 `crops.json` 내보내기 → `s13_apply_crops.py`), `data/review/manual_review.html`.

### 6.6 실행 중 발견한 문제와 조치 (재현성 기록)

- PMC OA Web Service(`oa.fcgi`)와 FTP `oa_package`는 2026년 2·8월에 폐지됨 → S3 버킷 `pmc-oa-opendata`로 전환.
  europepmc.org의 `/articles/PMC…/bin/` 그림 URL은 자동 클라이언트에 403을 반환(우회하지 않음).
- MDPI, Elsevier 등 일부 출판사는 PDF 요청에 HTML challenge 페이지를 반환 → `s05`에서 건너뜀(로그에 호스트 기록).
- OpenAlex API가 간헐적으로 503 → 후보 목록 캐시 파일 도입.
- Wikimedia `upload.wikimedia.org` 429 → UA에 연락처(프로젝트 URL) 추가 후 1 s 간격으로 재실행하여 해결(실패 1건).
- 한국 지자체 일부(용인·평택·의정부·양주·수원·대전시설공단)는 TLS/연결 오류, 천안은 403 → 수작업 저장 대상.
- Windows 콘솔 인코딩(cp1252) 문제 → 모든 실행에 `PYTHONIOENCODING=utf-8` 사용.
- EPA 문서번호로 추측한 NEPIS Dockey는 전부 틀렸음 → 공식 NEPIS 제목 목록(pubtitleORD/OW.html)에서 Dockey를 확인해 교체.


### 6.7 최종 수량 (crop·수작업 확인 반영, 2026-11-16)

crop 도구로 35개 crop을 만들어 main에 승격했고(`s13`), manual_review 75장을 사람이 판정해(`s14`) keep 6 → main, reject 50 → excluded,
unsure 19는 유지했다(렌더 실패 14장 포함 33장이 manual_review에 남음).

| 분할 | 수량 | 비고 |
|---|---|---|
| main | **993** | 952 keep + 35 crops + 6 reviewed; tier A 776 / tier B 217; wwtp 774 · pilot 105 · sludge 45 · other 42 · wtp 27 |
| aux_unit / aux_pictorial / aux_other_domain | 233 / 87 / 83 | 보조 세트 403 |
| crop_pending | 99 | 원본 행 유지(35장은 crop본이 main에 있음) |
| manual_review | 33 | unsure 19 + 렌더 실패 14 |
| excluded | 1,621 | reject 1,530 + 레이아웃 41 + 수작업 reject 50 |
| 합계 | 3,149 | canonical 3,114 + crop 35 |

그림·표의 수치는 이 표를 기준으로 갱신했다(`Fig_pipeline_styles.pptx`, `Fig1_pipeline_v2.*`, `Algorithms_v4.docx`).

## 7. 한계와 후속 작업
- 캡션 기반 필터는 캡션 없이 본문에만 설명된 그림, 캡션이 모호한 그림("Schematic of the system")을 놓친다. 재현율
  보완을 위해 선행 연구처럼 **flowsheet 분류 CNN**(Balhorn et al., 2022)을 후보 전체 그림에 적용하는 2차 필터를 둘 수 있다
  (현재는 캡션 통과 그림만 내려받으므로, 전수 적용하려면 `s01`에서 모든 그림을 받도록 옵션 추가).
- PDF 추출은 텍스트 레이어가 있는 문서에서만 동작한다. 스캔본(EPA 1970~80년대 매뉴얼, 일부 홍보물)은 OCR 전처리 필요.
- 특허 도면과 지자체 홍보 이미지는 캡션이 없어 전수 수작업 선별이 필요하다.
- 한국 공공기관 자료의 공공누리 유형은 페이지마다 달라 기관별 확인이 필요하다.
- 공개 벤치마크로 배포할 때는 tier A만 포함하고, CC BY/CC BY-SA의 출처 표시 의무를 `rights_holder`, `landing_url`,
  `license_url` 필드로 충족한다. CC BY-SA 이미지가 섞이면 데이터셋 라이선스도 SA 조건을 따라야 하므로 분리 배포를 검토.

## 8. Methods (English draft for the manuscript)

**Data sources and acquisition.** Candidate process diagrams were harvested from six source types with a fully
scripted, provenance-tracked pipeline (Python 3.12; code in `data_collection/`). (i) *Open-access literature*:
Europe PMC was queried for open-access full-text articles mentioning wastewater/sewage treatment plants or water
resource recovery facilities; for every PMCID the JATS XML, figure files and licence metadata were retrieved from
the official PMC Open Access AWS bucket (`pmc-oa-opendata`). Figures were retained when the caption matched a
rule set for process diagrams (flow diagram, flowsheet, schematic, layout, treatment train, …) and did not match
an exclusion set (maps, photographs, spectra, community-composition plots, graphical abstracts, …); captions
naming a whole plant (WWTP, STP, WRRF, treatment line, full-scale plant) were labelled T1 and other
treatment-related schematics T2. (ii) *Open-access articles outside PMC* were located through OpenAlex
(`is_oa`, no PMCID) and their publisher/repository PDFs processed with a caption-anchored page extractor
(PyMuPDF); servers that do not serve PDFs to automated clients were skipped. (iii) *Wikimedia Commons* was
searched through the MediaWiki API with multilingual queries and category traversal; licence and author
metadata were taken from `extmetadata`. (iv) *US EPA design manuals and technical reports* (public domain,
17 U.S.C. §105) were downloaded from epa.gov and processed with the same extractor, keeping both embedded
raster images and 200-dpi page renders. (v) *Patent drawings* were collected from Google Patents for CPC classes
C02F3/C02F9/C02F11. (vi) *Korean municipal operators' public web pages* were harvested from a curated URL list.
Every file carries a provenance record (source, acquisition route, file and landing URLs, licence, rights holder,
document identifiers, figure label and caption, matching rule, SHA-256 and perceptual hash). Exact (SHA-256) and
near duplicates (pHash Hamming distance ≤ 6) were collapsed. Licences were mapped to tier A (CC0, CC BY,
CC BY-SA, public domain; redistributable) or tier B (NC/ND or unknown; research use only). All automated
requests used an identifying User-Agent and fixed rate limits; no access controls were circumvented.

## 9. 논문용 산출물 — `paper/`

- `paper/algorithm.tex` / `paper/algorithm.md` — 수집·필터·선별 절차의 의사코드 3개 (S1 수집, S2 CaptionTier, S3 중복 제거·선별). LaTeX는 `algorithm` + `algpseudocode` 패키지용.
- `paper/make_figures.py` — Fig S1(파이프라인 개요, 16:9)과 Fig S2(소스별 선별 결과, 4:3)를 `paper/figures/`에 PDF·SVG·PNG로 생성. 연구실 figure 규칙(`figure_style.py`: Arial, 영문, 제목 없음, 300 dpi)을 따름. 수치는 `data/triage_ai.csv`에서 읽고, 없으면 2026-11-16 실행값을 사용.

## 9. Algorithm 표 초안 (논문 Table용, 예시 형식에 맞춤)

**Table X. Pseudo-code of the provenance-tracked collection and triage pipeline.**

```
Algorithm 1: Provenance-tracked harvesting of WWTP process diagrams
Input:  source set S = {literature (Europe PMC / PMC-OA S3, OpenAlex), Wikimedia Commons, EPA documents,
        patents, operator web pages}; query sets Q_s; caption rule set R = (D_strong, D_weak, P, T, E);
        licence map L -> {A, B}; pHash threshold tau = 6; triage criteria C
Output: catalog K with provenance records; splits {main, aux_unit, aux_pictorial, aux_other_domain,
        crop_pending, manual_review, excluded}
Initialization: K <- {}; D <- {}  (D = set of downloaded files)
For each source s in S do
  1. Discovery:   U_s <- candidate documents from Q_s via the source's official API / index
  2. Acquisition: for each document u in U_s: fetch metadata (id, title, venue, year, licence, authors)
                  and the figure container (JATS XML + figure files | PDF | HTML <img> | drawing sheets)
  3. Figure extraction:
        if captions available (JATS, PDF text layer):
            for each figure f with caption c:
                t <- CaptionTier(c; R)          // T1 if plant words, T2 if treatment words, None otherwise
                if t in {T1, T2}: download f; D <- D + {f}
        else (patents, web images, scanned pages):
            download all drawing sheets / keyword-matched images / caption-matched page renders
  4. Provenance:  for each f in D: write record r_f = (source, tier = L(licence), file URL, landing URL,
                  rights holder, doc id, figure label, caption, query, filter rule, SHA-256, pHash)
End for
5. De-duplication: cluster D by SHA-256 (exact) and by pHash Hamming distance <= tau (near);
                   keep one canonical file per cluster (tier A preferred, then earliest); K <- canonical set
6. First-pass triage: render K as 20-image contact sheets; vision-LLM agents assign
                   decision in {keep, unsure, reject} and category in {wwtp, sludge, wtp, pilot, other} under C;
                   transparent images re-rendered on white and judged manually
7. Validation:   human spot check of random keep / reject samples (precision, miss rate)
8. Split assignment: keep -> main; unsure -> group by reason -> {aux_unit, aux_pictorial, crop_pending,
                   aux_other_domain, manual_review, excluded}; reject -> excluded
9. Crop and promote: human draws boxes on crop_pending images; crops inherit the parent record and join main
Return: K, provenance records, splits
```


### 9.5 트리형 슬라이드 2종과 알고리즘 v4 (2026-11-16)

- `paper/Fig_pipeline_styles.pptx` 슬라이드 4 = Style D "Hierarchical tree"(루트 → 3단계 → 단계별 리프, 선별 결정 → 서브셋;
  단색 슬레이트), 슬라이드 5 = Style E "Decision tree"(후보 그림 1장이 캡션 검사 다이아몬드 → provenance → 중복 검사 → 시각
  선별 → 불확실 사유 → 서브셋에 이르는 경로; 청록/주황). 생성 스크립트 `paper/make_figure_deck_trees.py`(슬라이드 1–3은
  `make_figure_deck.py`에서 가져와 5장짜리 파일로 저장).
- `paper/Algorithms_v4.docx`, `paper/algorithms_v4.md` (`paper/make_algorithm_v4.py`): 오른쪽 회색 ▷ 주석(LaTeX algorithmic
  관례) 제거. 예시 표 구조(Input / Output / Initialization / For each … do / 굵은 단계명 + 평서문 / End for / Return)로 다시 쓰고,
  실행 수치는 표 아래 "Result" 한 줄로 분리. 기호는 τ와 p* 둘만 사용.

### 9.4 편집 가능한 PPT 3종 스타일과 알고리즘 v3 (2026-11-16)

- **`paper/Fig_pipeline_styles.pptx`** (`paper/make_figure_deck.py`, python-pptx, 모든 요소가 네이티브 도형·텍스트·커넥터):
  슬라이드 1 = Style A "Stage bands"(v2 디자인을 도형으로 재구성), 슬라이드 2 = Style B "Vertical stepper"(남색 스파인 +
  번호 노드 + 단계 카드 + 데이터 칩 + KPI 타일), 슬라이드 3 = Style C "Data funnel"(이미지 수에 비례한 깔때기 + 단계 설명 +
  분할 타일). 슬라이드 크기 7.5 × 10 in 세로. PowerPoint에서 열어 내보내기(PNG/PDF)로 그림 파일 생성.
- **`paper/Algorithms_v3.docx`, `paper/algorithms_v3.tex`** (`paper/make_algorithm_v3.py`): 수처리·환경공학 독자용 용어
  (treatment-plant process diagram, unit process, full-scale plant, licence tier, benchmark subset)와 평이한 절차명
  (QueryIndex, FetchFigures, TierCaption, RemoveDuplicates, ScreenVisually, AuditSample, AssignSubset, CropAndPromote).
  Input/Output을 기호별 정의 목록으로, 선별 루프를 품질관리 사이클(repeat … until p ≥ p*)로, Algorithm 2를 Rule 1–4 결정 목록으로
  작성. 실측값은 회색 주석에만 둠.

### 9.3 논문용 파일 (v2, 저널 관행 기준, 2026-11-16)

- **그림** `paper/figures/Fig1_pipeline_v2.{png,svg,pdf}` (`paper/make_flowchart_v2.py`): 180 mm 2단 폭, top-down 3단계
  밴드(① Harvesting with provenance ② Curation ③ Visual triage and split assignment). 색은 역할만 부호화(파랑 = 자동 단계,
  주황 = 사람 개입 단계, 청록 = 데이터 산출물, 소스 카드 5색). 왼쪽 여백에 데이터 깔때기 수치, 하단에 결과 분할 비례 막대.
- **알고리즘** `paper/Algorithms_v2.docx`, `paper/algorithms_v2.tex` (`paper/make_algorithm_v2.py`): LaTeX algorithm +
  algpseudocode 관행(상·하 괘선, "Algorithm n Title", Input/Output, 줄 번호, 굵은 키워드, 회색 ▷ 주석). Word 버전은 줄 번호 열 +
  문장 열의 2열 표, LaTeX 버전은 ForEach, Repeat–Until, Comment 매크로 사용.

### 9.2 예시 형식으로 만든 논문용 파일 (v1, 참고용)

- `paper/Table_Algorithms.docx` (`paper/make_algorithm_docx.py`): 예시 "Table 4 / Algorithm 1" 형식의 Word 단일 칸 표.
  Algorithm 1 = 수집·선별 파이프라인(Input/Output/Initialization/For each source … do/9단계/Return), Algorithm 2 = CaptionTier 규칙.
- `paper/figures/Fig_pipeline_vertical.{png,svg,pdf}` (`paper/make_flowchart.py`): 예시 흐름도 형식(세로 흐름, 데이터 원통,
  색 박스, 오른쪽 확대 루프 패널)의 방법론 그림. 수치는 6절 실행값.
- 포크 세션이 만든 `paper/algorithm.{md,tex}`, `paper/figures/FigS1_pipeline.*`, `FigS2_triage.*`는 다른 형식의 참고용.

### 9.1 Methods figure (초안 계획, 9.2로 구현됨)

예시 흐름도와 같은 형식(세로 흐름, 데이터 원통 → 처리 박스 → 산출물, 반복 루프는 회색 박스로 확대)으로 그릴 구성:
왼쪽 열에 소스 6종의 원통(저널 OA 전문, OpenAlex OA PDF, Wikimedia, EPA 문서, 특허, 운영기관 웹), 가운데 열에
"Discovery → Acquisition → Caption filter (T1/T2) → Provenance record → Dedup (SHA-256, pHash) → AI triage → Human
validation → Split", 오른쪽 확대 박스에 캡션 규칙(강한 다이어그램어 / 플랜트어 / 제외어)과 triage 결정 트리.
수치(후보 10,323편, 그림 56,617장, 3,300 → 3,114 → main 952)를 화살표 옆에 표기.

## 10. 어노테이션 클래스 체계 — `docs/`

- `docs/annotation_taxonomy_plan.md`: 클래스 체계 설계안 v1.1 (요구조건 → 근거 → 원칙 → L2 33 클래스 + 연결 8 클래스 + 예비 7 클래스, 속성, 판별 규칙 22개, 그래프 정답 스키마, 확정 절차, 평가 지표).
- `docs/evidence_ledger.md`: 설계안의 모든 결정을 출처(데이터·선행연구·표준·교과서·KDS·방법론)와 분석 방법으로 추적하는 근거 원장. "미확인" 행은 논문에 인용하지 않는다.
- `docs/taxonomy_textbook_review.md`: v0를 교과서 4권으로 검토한 보고서(오류 E1–E11, v1 제안).
- 설명 페이지(비전문가용 시각 설명): https://claude.ai/artifact/RHaxhG7DwhQaEy8HA47FzY

## 11. 페이지 렌더 자동 크롭 — `s16_crop_pages.py`

main의 약 1/4(EPA 64, OpenAlex 109; 크기 h > 1400 px, 종횡비 1.25~1.5)은 `pdf_figures.py`가 저장한 **페이지 전체 렌더**였다(벡터 도면은 이미지 객체가 아니라서 페이지를 통째로 저장). 어노테이터가 텍스트 페이지를 받지 않도록 그림 영역만 잘라낸다.

- 방법: 원본 PDF를 PyMuPDF로 열어 캡션 블록("Fig./Figure n")을 찾고, 캡션 위(또는 아래)에서 본문 텍스트 블록(3줄 이상·페이지 폭 30 % 이상)을 만나기 전까지의 띠 안에 있는 벡터 드로잉·이미지·짧은 라벨 텍스트의 합집합을 그림 영역으로 잡는다. 영역이 본문 텍스트 35 % 이상이면, 또는 120×60 pt·페이지의 5 % 미만이면 수작업 큐로; 페이지의 65 % 이상이면 자르지 않는다.
- 검토: `data/review/sheets_crops/`에 "페이지 + 빨간 박스 | 잘린 그림" 미리보기 시트를 만들고 사람이 전부 훑는다. 2026-11-16: 162장 중 자동 114 → 눈으로 8장 기각(`crops_auto_reject.txt`: 회전된 전면 도면 3, 사진·그래프·피라미드 그림 4, 검은 가림 블록 1) → **자동 106장 적용**, 수작업 큐 56장(`crops_auto_manual.csv`; 대부분 EPA 스캔본 "캡션 옆에 그래픽 객체 없음").
- 적용: `s13_apply_crops.py --json data/review/crops_auto.json --method "auto crop (s16 PDF layout)" --parent-split crop_pending` → 잘린 그림이 `record_id#crop0`으로 main에 들어가고 부모 페이지는 `crop_pending`으로 빠진다. provenance에는 `auto crop (s16 PDF layout) of <parent> (box …)`가 남는다.
- 수작업 큐는 `s12_crop_tool.py --ids data/review/crops_auto_manual.csv`로 크롭 도구를 만들어 처리한 뒤 같은 s13으로 적용한다.

## 12. 파일럿 표본 — `s15_pilot_sample.py`

설계안 §5.1의 60장 파일럿 표본. `python s15_pilot_sample.py` 로 1차 추출(seed 20261116, 출처별 제곱근 배분, 문서당 1장, 출처마다 비영문 ≥ 1, 카테고리 분산) → 접촉 시트(`data/pilot/sheets/`)에서 양식 A~E를 눈으로 판정해 `visual_form_prelim_draw1.csv`에 적음 → `--prelim` 옵션으로 재실행하면 페이지 렌더(E) 항목을 같은 출처·카테고리·언어의 그림 크기 이미지로 교체하고 `replacements.json`에 기록. 산출물: `data/pilot/pilot60.csv`(record_id ↔ pilot_no ↔ 잠정 양식), `images/pilot_NN__*.ext`(CVAT 업로드용), `allocation.md`(배분·양식 분포·페이지 렌더 비율 메모). 데이터 폴더는 git에 올리지 않으므로 같은 seed로 재실행하면 동일 표본이 나온다.

## 13. 파일럿 어노테이션 패키지 — `annotation/`, `s17_pilot_agreement.py`

- `annotation/classes.yaml`: 체계 v1.1의 기계용 정의(L2 33 + 예비 7 + 연결 8, 속성 어휘와 T1/T2/T3 층, QSDsan·GPS-X·SUMO·BSM·DEXPI·ISO·KDS 매핑, 엣지 스키마).
- `annotation/label_studio_config.xml`: Label Studio 라벨 설정(박스 41종, perRegion 속성, 관계 라벨 `medium|direction_confidence`·`parent_of`). `annotation/cvat_labels.json` → `python s17_pilot_agreement.py --expand-cvat …` 로 CVAT용 전개본(`cvat_labels_expanded.json`).
- `docs/annotation_guideline_v1.md`: 어노테이터 규칙서(클래스 표, 판별 규칙 22개, 엣지 기록법, 자주 틀리는 것).
- `annotation/README_pilot.md`: 설치·프로젝트 생성·교육·내보내기·일치도 계산 절차.
- `s17_pilot_agreement.py`: 두 어노테이터의 Label Studio 내보내기에서 κ(L2/L1)·IoU·누락·엣지 F1·클래스별 κ·부트스트랩 CI를 계산.
