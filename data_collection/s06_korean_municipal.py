"""
s06_korean_municipal.py — Source 6: Korean public WWTP operators' web pages (지자체·공단·K-water 공정도)

Pipeline
  1. A curated page list (PAGES below; add more lines freely — each is "operator | plant | url").
     The pages are public information pages ("하수처리과정", "처리공정", "공정도") of municipal
     wastewater treatment plants.
  2. Each page is fetched once (honest User-Agent, 2 s between requests). All <img> tags are scanned;
     an image is kept when (a) its src/alt/title contains a process keyword (공정, 계통, 처리, flow, process,
     diagram, …) or (b) it is a large content image (>= 500 px wide after download) that is not a banner/
     logo/icon by path name. Linked PDFs whose link text contains 공정/계통 are also fetched and passed to
     pdf_figures.extract().
  3. Licence: Korean public bodies mark reusable content with 공공누리 (KOGL) type 1-4. The page HTML is
     searched for "공공누리"/"KOGL" + 유형; type 1 (출처표시) -> tier A, types 2-4 or none -> tier B
     (= internal research use only until confirmed with the operator).

Usage: python s06_korean_municipal.py
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from common import (RAW, PROV, make_session, download, provenance_record, append_jsonl, already_done,
                    get_logger, safe_name, image_size, RateLimiter)
import pdf_figures

SOURCE = "korean_municipal"
OUT = RAW / SOURCE
OUT.mkdir(parents=True, exist_ok=True)
PROV_FILE = PROV / f"{SOURCE}.jsonl"
log = get_logger(SOURCE)

# operator | plant/page | url
PAGES = """
구리시 | 구리하수처리장 하수처리과정 | https://www.guri.go.kr/environment/contents.do?key=1488
구리시 | 구리하수처리장 시설현황 | https://www.guri.go.kr/environment/contents.do?key=1486
파주시 | 파주 공공하수처리시설 처리공정 | https://www.paju.go.kr/www/www_02/environment/environment_04/environment_04_08/environment_04_08_02.jsp
목포시 | 목포 하수처리공정 (PDF) | https://www.mokpo.go.kr/www/life_welfare/water_quality/waterquality_condition/process/screen_print.pdf
서울특별시 | 중랑물재생센터 소개 (하수처리공정·오니처리과정 그림) | https://news.seoul.go.kr/env/water-recycling-facility/jungnang-water-center/jungnang-water-center-introduction
서울특별시 | 난지물재생센터 소개 | https://news.seoul.go.kr/env/water-recycling-facility/nanji-water-center/nanji-water-center-introduction
인천광역시 | 하수처리시설 현황 | https://www.incheon.go.kr/env/ENV030301
대전광역시시설관리공단 | 대전하수처리장 하수처리계통도 | https://www.djsiseol.or.kr/portal/sub010102.asp
대전광역시시설관리공단 | 대전하수처리장 고도처리·슬러지처리 | https://www.djsiseol.or.kr/portal/sub010102_03.asp
광주시(경기) | 공공하수처리시설 흐름도 | https://www.gjcity.go.kr/depart/contents.do?mId=0903060000
천안시 맑은물사업본부 | 천안수질정화센터 처리계통도 | https://www.cheonan.go.kr/water/sub03_02_03.do
제주특별자치도 상하수도본부 | 하수도처리공정도 | https://www.jeju.go.kr/jejuwater/sewer/process.htm
청주시 환경관리본부 | 하수슬러지 소각처리공정도 | https://www.cheongju.go.kr/environment/contents.do?key=24193
안산시 상하수도사업소 | 하수도 처리과정 계통도 | https://www.ansan.go.kr/water/common/cntnts/selectContents.do?cntnts_id=C0001864
남양주시 | 정하수처리과정 | https://www.nyj.go.kr/www/contents.do?key=3132
원주시 상하수도사업소 | 하수처리과정 | https://www.wonju.go.kr/sudo/sub.do?key=1937
포항시 맑은물사업본부 | 하수처리과정 | https://www.pohang.go.kr/water/contents.do?mid=0502000000
하남시 | 공공하수처리시설 처리공정 (A2O+MBR) | https://www.hanam.go.kr/www/contents.do?key=8724
과천시 | 하수처리과정 | https://www.gccity.go.kr/dept/contents.do?mId=0606080300
이천시 | 하수도 처리과정 | https://www.icheon.go.kr/depart/contents.do?mid=0403020000
광주광역시 | 제1·제2·효천하수처리장 공정도 | https://www.gwangju.go.kr/envi/contentsView.do?pageId=envi62
제천시 환경사업소 | 하수 처리 과정 | https://www.jecheon.go.kr/jcstp/contents.do?key=1072
용인시 상하수도사업소 | 하수처리과정 (재시도) | https://www.yongin.go.kr/home/water/swAd/swAdSw.jsp
평택시 | 하수도처리과정 (재시도) | https://www.pyeongtaek.go.kr/sanghasudo/contents.do?mId=0703000000
의정부시 | 시설개요 및 공정소개 (재시도) | https://ui4u.go.kr/eco/contents.do?mId=0104000000
양주시 | 하수처리장 (재시도) | https://www.yangju.go.kr/www/contents.do?key=2293
수원시 | 하수처리 (재시도) | https://www.suwon.go.kr/sw-www/deptHome/dep_env/env_01/env_01_10.jsp
창원시 | 하수처리공법 (재시도) | https://www.changwon.go.kr/depart/contents.do?mId=1002040400
서울특별시 | 서울시 하수도 정책 홍보 브로슈어 (PDF) | https://seoulsolution.kr/sites/default/files/%EC%84%9C%EC%9A%B8%EC%8B%9C%ED%95%98%EC%88%98%EB%8F%84%EC%A0%95%EC%B1%85%ED%99%8D%EB%B3%B4%EB%B8%8C%EB%A1%9C%EC%8A%88%EC%96%B4_%EA%B5%AD%EB%AC%B8%28%EC%B5%9C%EC%A2%85%29.pdf
"""
KEY_RX = re.compile(r"(공정|계통|처리과정|처리공정|흐름|flow|process|diagram|scheme|treat|sewage|wwtp|하수)", re.I)
SKIP_RX = re.compile(r"(logo|banner|icon|btn|button|bullet|arrow|bg_|background|visual|top_|menu|nav|sns|footer|quick|spacer|blank|dot|line\.)", re.I)
KOGL_RX = re.compile(r"(공공누리|KOGL)[^<]{0,80}?(제?\s*([1-4])\s*유형|type\s*([1-4]))", re.I)


def parse_pages() -> list[tuple[str, str, str]]:
    rows = []
    for line in PAGES.strip().splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 3 and parts[2].startswith("http"):
            rows.append(tuple(parts))
    return rows


def kogl_type(html: str) -> str | None:
    m = KOGL_RX.search(html)
    if not m:
        return None
    return m.group(3) or m.group(4)


def main():
    session = make_session()
    done = already_done(PROV_FILE)
    rl = RateLimiter(2.0)
    n = 0
    for operator, plant, url in parse_pages():
        try:
            n += process_page(session, rl, done, operator, plant, url)
        except Exception as e:  # one bad page must not stop the run
            log.warning("page failed %s: %r", url, e)
    log.info("DONE %d files", n)


def process_page(session, rl, done, operator, plant, url) -> int:
    n = 0
    if True:
        rl.wait()
        try:
            r = session.get(url, timeout=60)
        except Exception as e:
            log.warning("fetch failed %s: %s", url, e)
            return 0
        if r.status_code != 200:
            log.warning("HTTP %s %s", r.status_code, url)
            return n
        # safe_name() strips Hangul, so add a short hash of the URL to keep directories unique
        import hashlib
        tag = (safe_name(f"{operator}_{plant}") or "page") + "_" + hashlib.sha1(url.encode()).hexdigest()[:6]
        ddir = OUT / tag
        ctype = r.headers.get("Content-Type", "")
        # ---- PDF page
        if "pdf" in ctype or ".pdf" in url.lower():
            if not r.content.startswith(b"%PDF-"):
                log.warning("not a PDF / empty response: %s", url)
                return n
            pdf = ddir / "_source.pdf"
            pdf.parent.mkdir(parents=True, exist_ok=True)
            pdf.write_bytes(r.content)
            figs = pdf_figures.extract(pdf, ddir, tag, max_pages=80)
            # brochures rarely have "Figure n" captions -> also render every page as candidate (tier T2, manual triage)
            if not figs:
                import pymupdf
                doc = pymupdf.open(pdf)
                for pno in range(min(len(doc), 80)):
                    p = ddir / f"{tag}_p{pno + 1:04d}_page.png"
                    doc[pno].get_pixmap(dpi=150).save(p)
                    figs.append({"path": p, "page": pno + 1, "caption": None, "label": None, "tier": "T2", "kind": "page_render_all"})
                doc.close()
            for fg in figs:
                rid = f"{SOURCE}:{url}:{fg['path'].name}"
                if rid in done:
                    continue
                rec = provenance_record(
                    source=SOURCE, tier="B", image_path=fg["path"],
                    acquisition_method="HTTP GET of public PDF -> PyMuPDF page extraction",
                    file_url=url, landing_url=url, license="unknown (check 공공누리/KOGL with operator)",
                    license_url="https://www.kogl.or.kr/", rights_holder=operator,
                    doc_id=url, title=plant, venue=operator, year=None,
                    figure_label=fg["label"], caption=fg["caption"], query="curated page list",
                    filter_rule=f"kind={fg['kind']};caption_tier={fg['tier']}",
                    extra={"page": fg["page"], "kind": fg["kind"]})
                rec["record_id"] = rid
                append_jsonl(PROV_FILE, rec)
                n += 1
            log.info("%s | %s: %d page/figure files from PDF", operator, plant, len(figs))
            return n
        # ---- HTML page
        html = r.text
        kogl = kogl_type(html)
        lic = f"공공누리(KOGL) 제{kogl}유형" if kogl else "unknown (no KOGL mark found on page)"
        tier = "A" if kogl == "1" else "B"
        soup = BeautifulSoup(html, "lxml")
        cands = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or ""
            if not src or src.startswith("data:"):
                continue
            alt = (img.get("alt") or "") + " " + (img.get("title") or "")
            full = urljoin(url, src)
            if SKIP_RX.search(full) and not KEY_RX.search(alt + src):
                continue
            cands.append((full, alt.strip(), bool(KEY_RX.search(alt + src))))
        # linked PDFs with process keywords in link text
        pdf_links = [(urljoin(url, a["href"]), a.get_text(" ", strip=True)) for a in soup.find_all("a", href=True)
                     if a["href"].lower().endswith(".pdf") and KEY_RX.search(a.get_text(" ", strip=True))]
        got = 0
        for full, alt, kw in cands:
            fname = safe_name(Path(urlparse(full).path).name) or "img"
            dest = ddir / fname
            rid = f"{SOURCE}:{url}:{dest.name}"
            if rid in done:
                continue
            rl.wait()
            if not download(session, full, dest, min_bytes=3000):
                continue
            sz = image_size(dest)
            if not sz or (sz[0] < 500 and not kw):
                dest.unlink(missing_ok=True)
                continue
            rec = provenance_record(
                source=SOURCE, tier=tier, image_path=dest,
                acquisition_method="HTTP GET of public operator web page -> <img> keyword/size filter",
                file_url=full, landing_url=url, license=lic, license_url="https://www.kogl.or.kr/",
                rights_holder=operator, doc_id=url, title=plant, venue=operator, year=None,
                figure_label=None, caption=alt or None, query="curated page list",
                filter_rule="img keyword match" if kw else "large content image (manual triage)",
                extra={"kogl_type": kogl})
            rec["record_id"] = rid
            append_jsonl(PROV_FILE, rec)
            got += 1
        for plink, ptext in pdf_links[:5]:
            rl.wait()
            pdf = ddir / (safe_name(Path(urlparse(plink).path).name) or "linked.pdf")
            if download(session, plink, pdf, min_bytes=20_000):
                for fg in pdf_figures.extract(pdf, ddir, pdf.stem, max_pages=60):
                    rid = f"{SOURCE}:{plink}:{fg['path'].name}"
                    if rid in done:
                        continue
                    rec = provenance_record(
                        source=SOURCE, tier=tier, image_path=fg["path"],
                        acquisition_method="HTTP GET of PDF linked from operator page -> PyMuPDF caption-matched extraction",
                        file_url=plink, landing_url=url, license=lic, license_url="https://www.kogl.or.kr/",
                        rights_holder=operator, doc_id=plink, title=f"{plant} / {ptext}", venue=operator, year=None,
                        figure_label=fg["label"], caption=fg["caption"], query="curated page list",
                        filter_rule=f"kind={fg['kind']};caption_tier={fg['tier']}", extra={"page": fg["page"]})
                    rec["record_id"] = rid
                    append_jsonl(PROV_FILE, rec)
                    got += 1
        n += got
        log.info("%s | %s: %d images (KOGL type=%s)", operator, plant, got, kogl)
    return n


if __name__ == "__main__":
    main()
