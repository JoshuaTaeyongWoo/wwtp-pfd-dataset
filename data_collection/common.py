"""
common.py — shared utilities for the WWTP process-flow-diagram (PFD) collection pipeline.

Every collector script writes:
  data/raw/<source>/...            the downloaded files (never modified)
  data/provenance/<source>.jsonl   one JSON record per downloaded file (append-only)
  data/logs/<source>.log           run log

A provenance record always carries the same core fields so that the per-source
files can be concatenated into one master catalog (see s07_dedup_catalog.py).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --------------------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent.parent          # WWTP_vision/
DATA = ROOT / "data"
RAW = DATA / "raw"
PROV = DATA / "provenance"
LOGS = DATA / "logs"
for _d in (RAW, PROV, LOGS):
    _d.mkdir(parents=True, exist_ok=True)

# Identify ourselves honestly to every server. No browser spoofing.
USER_AGENT = "WWTP-PFD-collector/0.1 (academic research; non-commercial; contact via project README)"

# --------------------------------------------------------------------------- http
def make_session(total_retries: int = 4, backoff: float = 1.5) -> requests.Session:
    s = requests.Session()
    retry = Retry(total=total_retries, backoff_factor=backoff,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset(["GET", "HEAD"]))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": USER_AGENT})
    return s


class RateLimiter:
    """Simple fixed-interval limiter (seconds between calls)."""
    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self._last = 0.0

    def wait(self):
        now = time.monotonic()
        delta = now - self._last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last = time.monotonic()


def download(session: requests.Session, url: str, dest: Path, timeout: int = 120,
             min_bytes: int = 200) -> bool:
    """Stream a URL to dest. Returns True if a file with >= min_bytes was written.
    Existing non-empty files are kept (idempotent / resumable)."""
    if dest.exists() and dest.stat().st_size >= min_bytes:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with session.get(url, stream=True, timeout=timeout) as r:
            if r.status_code != 200:
                return False
            tmp = dest.with_suffix(dest.suffix + ".part")
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(1 << 16):
                    f.write(chunk)
            if tmp.stat().st_size < min_bytes:
                tmp.unlink(missing_ok=True)
                return False
            tmp.replace(dest)
            return True
    except Exception:  # network errors, malformed (non-UTF-8) URLs, disk errors: treat as "not downloaded"
        return False


# --------------------------------------------------------------------------- hashing
def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def phash_of(path: Path) -> str | None:
    """Perceptual hash (64-bit, hex). None for non-raster files (svg, pdf) or failures."""
    try:
        from PIL import Image
        import imagehash
        with Image.open(path) as im:
            return str(imagehash.phash(im.convert("L")))
    except Exception:
        return None


def image_size(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


# --------------------------------------------------------------------------- provenance
def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def provenance_record(*, source: str, tier: str, image_path: Path, acquisition_method: str,
                      file_url: str, landing_url: str, license: str | None, license_url: str | None,
                      rights_holder: str | None, doc_id: str, title: str | None,
                      venue: str | None, year: str | int | None, figure_label: str | None,
                      caption: str | None, query: str | None, filter_rule: str | None,
                      extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build one provenance record. `tier`:
         A = licence allows redistribution in a public dataset (CC0/CC BY/CC BY-SA/public domain)
         B = licence allows research use but not redistribution (CC BY-NC*, CC BY-ND, publisher OA w/o CC, unknown)
    """
    rec = {
        "source": source,
        "tier": tier,
        "record_id": f"{source}:{doc_id}:{image_path.name}",
        "image_path": str(image_path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": sha256_of(image_path),
        "phash": phash_of(image_path),
        "image_size": image_size(image_path),
        "acquired_at": now_iso(),
        "acquisition_method": acquisition_method,
        "file_url": file_url,
        "landing_url": landing_url,
        "license": license,
        "license_url": license_url,
        "rights_holder": rights_holder,
        "doc_id": doc_id,
        "title": title,
        "venue": venue,
        "year": str(year) if year is not None else None,
        "figure_label": figure_label,
        "caption": caption,
        "query": query,
        "filter_rule": filter_rule,
    }
    if extra:
        rec["extra"] = extra
    return rec


def append_jsonl(path: Path, rec: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def already_done(path: Path) -> set[str]:
    """record_ids already present in a provenance file (for resume)."""
    return {r["record_id"] for r in read_jsonl(path)}


# --------------------------------------------------------------------------- licence mapping
_TIER_A = ("cc0", "cc by", "cc-by", "public domain", "pd", "cc by-sa", "cc-by-sa")
_TIER_B_MARKERS = ("nc", "nd")


def licence_tier(lic: str | None) -> str:
    """Map a licence string to tier A (redistributable) or B (research-only)."""
    if not lic:
        return "B"
    l = lic.lower().replace("_", "-").strip()
    if any(m in l.split("-") or m in l.split() for m in _TIER_B_MARKERS) or "nc" in l or "nd" in l:
        return "B"
    if any(l.startswith(a) or a in l for a in _TIER_A):
        return "A"
    return "B"


# --------------------------------------------------------------------------- caption filter
# Tier-1: caption describes a whole-plant / treatment-train diagram.
# Tier-2: any schematic/flow diagram that mentions treatment (may be single reactor, pilot, lab).
DIAGRAM_WORDS = r"(flow\s*-?\s*diagram|flow\s*-?\s*sheet|flowsheet|flow\s*-?\s*chart|flowchart|process\s*diagram|process\s*flow|schematic|layout|configuration|process\s*scheme|treatment\s*scheme|treatment\s*train|treatment\s*process|block\s*diagram|diagram\s*of|scheme\s*of|overview\s*of\s*the)"
PLANT_WORDS = r"(wastewater\s*treatment\s*plant|sewage\s*treatment\s*plant|treatment\s*plant|wwtp|stp|wrrf|water\s*resource\s*recovery|sewage\s*works|treatment\s*works|treatment\s*facility|treatment\s*line|treatment\s*train|full\s*-?\s*scale\s*plant|municipal\s*plant|plant\s*process|the\s*plant)"
TREAT_WORDS = r"(treatment|wastewater|sewage|sludge|effluent|activated\s*sludge|clarifier|digester|aeration|mbr|membrane\s*bioreactor|sbr)"
EXCLUDE_WORDS = r"(sampling\s*(site|point|location)|study\s*area|map\s*of|geographic|satellite|photograph|photo\s*of|aerial|microscop|sem\s*image|gel\s*electrophoresis|chromatogram|spectr|phylogenetic|heat\s*map|box\s*plot|bar\s*chart|time\s*series|correlation|regression|removal\s*efficienc|concentration\s*of|kinetic|venn|pie\s*chart|sankey|network\s*analysis|co-?occurrence|metabolic\s*pathway|gene\s*expression|microbial\s*communit|relative\s*abundance|taxonom|pcoa|nmds|rda\s|workflow\s*of\s*the\s*(study|analysis|research|methodology)|methodolog|graphical\s*abstract|conceptual\s*framework|research\s*framework)"

# "strong" diagram words almost always denote a process diagram; "weak" ones (schematic, configuration,
# diagram of, overview of) also occur in maps / sampling schemes and therefore do not override the exclusion list.
STRONG_DIAGRAM_WORDS = r"(flow\s*-?\s*diagram|flow\s*-?\s*sheet|flowsheet|flow\s*-?\s*chart|flowchart|process\s*diagram|process\s*flow|block\s*diagram|treatment\s*train|process\s*scheme|treatment\s*scheme|plant\s*layout|process\s*layout)"

_RX_DIAG = re.compile(DIAGRAM_WORDS, re.I)
_RX_STRONG = re.compile(STRONG_DIAGRAM_WORDS, re.I)
_RX_PLANT = re.compile(PLANT_WORDS, re.I)
_RX_TREAT = re.compile(TREAT_WORDS, re.I)
_RX_EXCL = re.compile(EXCLUDE_WORDS, re.I)


def caption_tier(caption: str) -> str | None:
    """Return 'T1', 'T2' or None for a figure caption.
    v2 (2026-11-16): an exclusion hit now rejects the caption unless a *strong* diagram word is present;
    v1 let 'Map of the study area ... wastewater treatment plant' through as T1."""
    c = " ".join(caption.split())
    if not _RX_DIAG.search(c):
        return None
    if _RX_EXCL.search(c) and not _RX_STRONG.search(c):
        return None
    if _RX_PLANT.search(c):
        return "T1"
    if _RX_TREAT.search(c):
        return "T2"
    return None


# --------------------------------------------------------------------------- logging
def get_logger(name: str) -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(LOGS / f"{name}.log", encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    log.addHandler(fh)
    log.addHandler(sh)
    return log


def safe_name(s: str, maxlen: int = 120) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    return s[:maxlen].strip("_") or "file"
