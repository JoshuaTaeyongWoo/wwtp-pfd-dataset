"""
s21_dryrun_synthetic.py — dry run of the post-pilot pipeline with synthetic labelings.

Posts a plausible synthetic annotation (one small treatment-train graph per image) to every task of
project A, and a deliberately perturbed copy (shifted / missing / extra boxes, one class swap, one
dropped edge, one reversed edge, one relation-label change) to project B, in the exact Label Studio
result format the lite config produces. Then exports both projects as JSON so s17 / s19 can be run
end to end before the real pilot results exist. The two projects are throwaway (dryrun_A, dryrun_B).

Usage:
  python s21_dryrun_synthetic.py [--base http://localhost:8080] [--names dryrun_A,dryrun_B]
                                 [--exports data/pilot/exports] [--seed 1]
"""
from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

import requests
from PIL import Image

from common import DATA
from s18_setup_pilot_projects import access_token

IMAGES = DATA / "pilot" / "images"

# a generic train: (id, class, x, y, w, h in % of image, per-region attrs)
TRAIN = [
    ("inf", "io_terminal", 2, 40, 6, 8, {"visual_form": "box", "confidence": "certain", "io_role": "raw_influent", "label_text": "Influent"}),
    ("scr", "screen", 10, 38, 7, 12, {"visual_form": "box", "confidence": "inferred_from_text", "label_text": "Screen"}),
    ("pc", "primary_clarifier", 20, 36, 9, 16, {"visual_form": "symbol", "confidence": "certain"}),
    ("anx", "anoxic_zone", 32, 36, 9, 16, {"visual_form": "box", "confidence": "inferred_from_text", "is_zone": "zone", "label_text": "Anoxic"}),
    ("aer", "aerobic_zone", 42, 36, 12, 16, {"visual_form": "box", "confidence": "inferred_from_text", "is_zone": "zone", "label_text": "Aerobic"}),
    ("bio", "process_unit_generic", 31, 34, 24, 20, {"visual_form": "box", "confidence": "inferred_from_text", "l1_hint": "secondary", "label_text": "Bioreactor"}),
    ("sc", "secondary_clarifier", 58, 36, 9, 16, {"visual_form": "symbol", "confidence": "certain"}),
    ("dis", "disinfection_unit", 70, 38, 8, 12, {"visual_form": "box", "confidence": "inferred_from_text", "label_text": "UV"}),
    ("eff", "io_terminal", 82, 40, 6, 8, {"visual_form": "box", "confidence": "certain", "io_role": "effluent", "label_text": "Effluent"}),
    ("spl", "junction_split", 62, 56, 2, 3, {"visual_form": "symbol", "confidence": "certain"}),
    ("thk", "thickener", 30, 66, 8, 12, {"visual_form": "symbol", "confidence": "certain"}),
    ("dig", "digester", 44, 64, 10, 16, {"visual_form": "symbol", "confidence": "certain"}),
    ("dew", "dewatering_unit", 60, 66, 8, 12, {"visual_form": "box", "confidence": "inferred_from_text", "label_text": "Centrifuge"}),
    ("cake", "io_terminal", 74, 68, 6, 8, {"visual_form": "box", "confidence": "certain", "io_role": "solids_disposal", "label_text": "Cake"}),
    ("chem", "io_terminal", 70, 24, 6, 6, {"visual_form": "box", "confidence": "certain", "io_role": "chemical_source", "label_text": "NaOCl"}),
    ("mrg", "junction_merge", 73, 34, 2, 3, {"visual_form": "symbol", "confidence": "certain"}),
]
# (src, dst, labels)
EDGES = [
    ("inf", "scr", []), ("scr", "pc", []), ("pc", "anx", []), ("anx", "aer", ["no_arrow"]), ("aer", "sc", []),
    ("sc", "dis", []), ("dis", "eff", []), ("aer", "anx", []), ("sc", "spl", []), ("spl", "anx", []), ("spl", "thk", []),
    ("pc", "thk", ["style:dashed"]), ("thk", "dig", []), ("dig", "dew", []), ("dew", "cake", []), ("dew", "scr", ["style:dashed"]),
    ("chem", "mrg", []), ("mrg", "dis", []), ("bio", "anx", ["parent_of"]), ("bio", "aer", ["parent_of"]),
]
FULL_EXTRA = [  # tasks <= 20 only: arrowheads and text boxes
    ("ah1", "arrowhead", 19, 43, 1.2, 2, {"visual_form": "symbol", "confidence": "certain"}),
    ("ah2", "arrowhead", 57, 43, 1.2, 2, {"visual_form": "symbol", "confidence": "certain"}),
    ("tx1", "text_label", 20, 53, 9, 3, {"visual_form": "box", "confidence": "certain", "label_text": "Primary clarifier"}),
    ("tx2", "stream_label", 48, 30, 8, 3, {"visual_form": "box", "confidence": "certain", "label_text": "Internal recycle"}),
]


def rect(rid, cls, x, y, w, h, W, H):
    return {"id": rid, "type": "rectanglelabels", "from_name": "unit", "to_name": "img", "original_width": W, "original_height": H,
            "image_rotation": 0, "value": {"x": x, "y": y, "width": w, "height": h, "rotation": 0, "rectanglelabels": [cls]}}


def per_region(rid, name, val):
    if name == "label_text":
        return {"id": rid, "type": "textarea", "from_name": name, "to_name": "img", "value": {"text": [val]}}
    return {"id": rid, "type": "choices", "from_name": name, "to_name": "img", "value": {"choices": [val]}}


def relation(a, b, labels):
    r = {"type": "relation", "from_id": a, "to_id": b, "direction": "right"}
    if labels:
        r["labels"] = labels
    return r


def build(pilot_no: int, W: int, H: int, variant: str, rng: random.Random) -> list[dict]:
    boxes = list(TRAIN) + (list(FULL_EXTRA) if pilot_no <= 20 else [])
    edges = list(EDGES)
    res = []
    if variant == "B":  # perturbations
        boxes = [list(b) for b in boxes]
        for b in boxes:  # small jitter: IoU stays > 0.7 for most
            b[2] += rng.uniform(-0.6, 0.6); b[3] += rng.uniform(-0.6, 0.6)
        boxes[1][2] += 5.0  # screen shifted hard -> unmatched on both sides
        boxes[3][1] = "anaerobic_zone"  # class swap on anoxic
        boxes[11][6] = dict(boxes[11][6], visual_form="box")  # attr disagreement on digester
        boxes = [b for b in boxes if b[0] != "mrg"]  # missing merge box
        boxes.append(["extra", "pump", 36, 60, 3, 4, {"visual_form": "symbol", "confidence": "certain"}])
        edges = [e for e in edges if e[:2] not in {("chem", "mrg"), ("mrg", "dis"), ("pc", "thk")}]  # dropped edges
        edges.append(("chem", "dis", []))
        edges = [("anx", "aer", []) if e[:2] == ("aer", "anx") else e for e in edges]  # reversed internal recycle
        edges = [(e[0], e[1], []) if e[:2] == ("anx", "aer") and e[2] == ["no_arrow"] else e for e in edges]
    ids = {b[0] for b in boxes}
    for rid, cls, x, y, w, h, attrs in boxes:
        res.append(rect(rid, cls, round(x, 3), round(y, 3), w, h, W, H))
        for k, v in attrs.items():
            res.append(per_region(rid, k, v))
    for a, b, labels in edges:
        if a in ids and b in ids:
            res.append(relation(a, b, labels))
    res.append({"id": "style", "type": "choices", "from_name": "diagram_style", "to_name": "img", "value": {"choices": ["A_box" if variant == "A" else "B_symbol"]}})
    res.append({"id": "lang", "type": "choices", "from_name": "language", "to_name": "img", "value": {"choices": ["en"]}})
    res.append({"id": "np", "type": "number", "from_name": "n_panels", "to_name": "img", "value": {"number": 1}})
    res.append({"id": "pcfg", "type": "textarea", "from_name": "process_configuration", "to_name": "img", "value": {"text": ["MLE (synthetic)"]}})
    if variant == "B":
        res.append({"id": "note", "type": "textarea", "from_name": "annotator_note", "to_name": "img", "value": {"text": ["dry run: anoxic vs anaerobic unclear"]}})
    return res


def image_size(pilot_no: int) -> tuple[int, int]:
    p = next(IMAGES.glob(f"pilot_{pilot_no:02d}__*"))
    if p.suffix.lower() == ".svg":
        return 1000, 700
    with Image.open(p) as im:
        return im.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8080")
    ap.add_argument("--names", default="dryrun_A,dryrun_B")
    ap.add_argument("--exports", default=str(DATA / "pilot" / "exports"))
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    base = a.base.rstrip("/")
    h = {"Authorization": f"Bearer {access_token(base)}"}
    rng = random.Random(a.seed)
    projects = {p["title"]: p["id"] for p in requests.get(f"{base}/api/projects?page_size=100", headers=h, timeout=30).json()["results"]}
    out = Path(a.exports); out.mkdir(parents=True, exist_ok=True)
    for name, variant in zip(a.names.split(","), "AB"):
        pid = projects[name]
        tasks = requests.get(f"{base}/api/tasks?project={pid}&page_size=1000", headers=h, timeout=60).json()["tasks"]
        n = 0
        for t in tasks:
            if t.get("annotations"):
                continue  # already labelled: keep idempotent
            m = re.search(r"pilot_(\d+)", t["data"]["image"])
            pno = int(m.group(1))
            W, H = image_size(pno)
            r = requests.post(f"{base}/api/tasks/{t['id']}/annotations/", headers=h, json={"result": build(pno, W, H, variant, rng), "was_cancelled": False}, timeout=60)
            r.raise_for_status(); n += 1
        e = requests.get(f"{base}/api/projects/{pid}/export?exportType=JSON&download_all_tasks=true", headers=h, timeout=120)
        e.raise_for_status()
        (out / f"{name}.json").write_bytes(e.content)
        print(f"{name}: posted {n} annotations, exported {len(e.json())} tasks -> {out / (name + '.json')}")


if __name__ == "__main__":
    main()
