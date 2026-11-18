"""
s18_setup_pilot_projects.py — create the two pilot projects in a local Label Studio and upload the 60 images.

One project per annotator (pilot_A, pilot_B) so that the two labelings stay independent (plan §5.1).
Each project gets annotation/label_studio_config.xml as its labeling config and the images of
data/pilot/images/ (sorted by pilot number; SVG/other formats are rasterised to PNG first).

Auth: a Label Studio personal access token (JWT refresh token) read from data/pilot/.ls_token or the
LS_TOKEN environment variable; it is exchanged for a short-lived access token via /api/token/refresh.
The token file lives under data/ (git-ignored) and is never printed.

Usage: python s18_setup_pilot_projects.py [--base http://localhost:8080] [--names pilot_A,pilot_B] [--dry-run]
"""
from __future__ import annotations

import argparse
import io
import os
import re
from pathlib import Path

import requests
from PIL import Image

from common import DATA, ROOT

CONFIG = ROOT / "data_collection" / "annotation" / "label_studio_config.xml"
IMAGES = DATA / "pilot" / "images"


def access_token(base: str) -> str:
    tok = os.environ.get("LS_TOKEN") or (DATA / "pilot" / ".ls_token").read_text(encoding="utf-8").strip()
    r = requests.post(f"{base}/api/token/refresh", json={"refresh": tok}, timeout=30)
    if r.ok and r.json().get("access"):
        return r.json()["access"]
    return tok  # legacy "Token" auth falls back to the raw key


def rasterise(p: Path) -> tuple[str, bytes, str]:
    """-> (filename, bytes, mime). PNG/JPEG pass through; everything else becomes PNG."""
    if p.suffix.lower() in (".png", ".jpg", ".jpeg"):
        return p.name, p.read_bytes(), "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    if p.suffix.lower() == ".svg":
        import pymupdf
        doc = pymupdf.open(p)
        pix = doc[0].get_pixmap(dpi=150)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        doc.close()
    else:
        im = Image.open(p).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return p.stem + ".png", buf.getvalue(), "image/png"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8080")
    ap.add_argument("--names", default="pilot_A,pilot_B")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--config", default=str(CONFIG), help="labeling config XML (default: full config; use label_studio_config_lite.xml for pilot-lite)")
    ap.add_argument("--images", default=str(IMAGES), help="image folder to upload (default: data/pilot/images)")
    a = ap.parse_args()
    images_dir = Path(a.images)
    base = a.base.rstrip("/")
    h = {"Authorization": f"Bearer {access_token(base)}"}
    if "." in h["Authorization"].split()[1] and h["Authorization"].count(".") < 2:
        h = {"Authorization": "Token " + h["Authorization"].split()[1]}
    config = Path(a.config).read_text(encoding="utf-8")
    files = sorted(images_dir.iterdir(), key=lambda p: int(re.match(r"[a-z]+_(\d+)", p.name).group(1)))
    print(f"{len(files)} images, config {len(config)} chars")
    existing = {p["title"]: p["id"] for p in requests.get(f"{base}/api/projects?page_size=100", headers=h, timeout=30).json().get("results", [])}
    for name in a.names.split(","):
        if name in existing:
            pid = existing[name]
            print(f"{name}: exists (id {pid}); updating label config only")
            if not a.dry_run:
                requests.patch(f"{base}/api/projects/{pid}", headers=h, json={"label_config": config}, timeout=60).raise_for_status()
            continue
        body = {"title": name, "label_config": config,
                "description": "WWTP diagram pilot (taxonomy v1.1, 60 stratified images) — one project per annotator",
                "show_instruction": True, "show_skip_button": False,
                "expert_instruction": "규칙서: data_collection/docs/annotation_guideline_v1.md. 다른 어노테이터와 상의하지 말 것."}
        if a.dry_run:
            print(f"{name}: would create and upload {len(files)} images")
            continue
        r = requests.post(f"{base}/api/projects", headers=h, json=body, timeout=60)
        r.raise_for_status()
        pid = r.json()["id"]
        n = 0
        for p in files:  # one request per file keeps task order == pilot order
            fname, data, mime = rasterise(p)
            u = requests.post(f"{base}/api/projects/{pid}/import", headers=h, files={fname: (fname, data, mime)}, timeout=120)
            if not u.ok:
                print("  upload failed", fname, u.status_code, u.text[:120])
                continue
            n += u.json().get("task_count", 0)
        t = requests.get(f"{base}/api/projects/{pid}", headers=h, timeout=30).json()
        print(f"{name}: created id {pid}, uploaded {n}, task_number {t.get('task_number')} -> {base}/projects/{pid}/")


if __name__ == "__main__":
    main()
