"""
s22_export_to_gt.py — Label Studio export (adjudicated, or one annotator) -> benchmark ground truth.

Writes, under --out:
  manifest.csv        one row per image: key, file, width, height, pilot_no, record_id, source, doc_id, lang,
                      diagram_style, language, n_panels, process_configuration (image-level fields)
  coco.json           COCO detection GT at L2 (categories = the RectangleLabels of the labeling config, L3
                      collapsed to L2, supercategory = L1); every annotation carries the box attributes
                      (semantic_class incl. L3, visual_form, confidence, is_zone, l1_hint, io_role, graph_id,
                      label_text, parent_id)
  graphs/<key>.graph.json   plan §4.6 graph per image (nodes + edges with medium / stream_role from s19 rules)
  splits.json         (with --split) document-level train/val/test split, stratified by source, seeded

Usage:
  python s22_export_to_gt.py --export data/pilot/exports/pilot_adjudicated.json --out data/pilot/gt
                             [--catalog data/pilot/pilot60.csv] [--config annotation/label_studio_config_lite.xml]
                             [--split 0.7,0.15,0.15 --seed 20261116]
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from common import ROOT
from s17_pilot_agreement import L1_OF
from s19_infer_edge_medium import build_graph, l2

HERE = Path(__file__).resolve().parent


def categories(config: Path) -> list[dict]:
    labels = [el.get("value") for el in ET.parse(config).getroot().iter("Label")]
    seen = []
    for v in labels:
        c = l2(v)
        if c not in seen:
            seen.append(c)
    return [{"id": i + 1, "name": c, "supercategory": L1_OF.get(c, "other")} for i, c in enumerate(seen)]


def parse_tasks(path: Path):
    """-> (key, W, H, nodes, rels, image_attrs) per task, same conventions as s19.load_tasks."""
    for task in json.loads(path.read_text(encoding="utf-8")):
        ann = (task.get("annotations") or [{}])[0]
        nodes, per_region, rels, W, H = {}, defaultdict(dict), [], None, None
        for r in ann.get("result", []):
            t = r.get("type")
            if t == "rectanglelabels":
                v = r["value"]; W, H = r.get("original_width", W), r.get("original_height", H)
                x0, y0 = v["x"] / 100 * W, v["y"] / 100 * H
                nodes[r["id"]] = {"id": r["id"], "cls": v["rectanglelabels"][0], "bbox": [x0, y0, x0 + v["width"] / 100 * W, y0 + v["height"] / 100 * H], "attrs": {}, "parent_id": None}
            elif t == "relation":
                rels.append(r)
            elif t in ("choices", "textarea", "number") and r.get("id"):
                val = r["value"].get("choices") or r["value"].get("text") or r["value"].get("number")
                per_region[r["id"]][r["from_name"]] = val[0] if isinstance(val, list) and len(val) == 1 else val
        for nid, n in nodes.items():
            n["attrs"] = per_region.pop(nid, {})
        image_attrs = {k: v for d in per_region.values() for k, v in d.items()}
        name = Path(task["data"].get("image", str(task["id"]))).name
        yield re.sub(r"^[0-9a-f]{8}-", "", name), W, H, nodes, rels, image_attrs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--catalog", default=str(ROOT / "data" / "pilot" / "pilot60.csv"), help="pilot60.csv-style table joined on pilot_no ('' to skip)")
    ap.add_argument("--config", default=str(HERE / "annotation" / "label_studio_config_lite.xml"))
    ap.add_argument("--split", default="", help="train,val,test fractions by document, e.g. 0.7,0.15,0.15")
    ap.add_argument("--seed", type=int, default=20261116)
    a = ap.parse_args()
    out = Path(a.out); (out / "graphs").mkdir(parents=True, exist_ok=True)
    cats = categories(Path(a.config)); cat_id = {c["name"]: c["id"] for c in cats}
    catalog = {}
    if a.catalog and Path(a.catalog).exists():
        with open(a.catalog, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                catalog[int(row["pilot_no"])] = row
    images, annots, manifest = [], [], []
    for key, W, H, nodes, rels, iattrs in parse_tasks(Path(a.export)):
        if not nodes:
            continue
        g = build_graph(key, nodes, rels)
        (out / "graphs" / f"{Path(key).stem}.graph.json").write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
        m = re.search(r"pilot_(\d+)", key); pno = int(m.group(1)) if m else 0
        cat = catalog.get(pno, {})
        img_id = len(images) + 1
        images.append({"id": img_id, "file_name": cat.get("pilot_image", key), "width": W, "height": H, "key": key})
        manifest.append({"key": key, "file": cat.get("pilot_image", key), "width": W, "height": H, "pilot_no": pno,
                         "record_id": cat.get("record_id", ""), "source": cat.get("source", ""), "doc_id": cat.get("doc_id", ""),
                         "lang": cat.get("lang_proxy", ""), "diagram_style": iattrs.get("diagram_style", ""), "language": iattrs.get("language", ""),
                         "n_panels": iattrs.get("n_panels", ""), "process_configuration": iattrs.get("process_configuration", "")})
        for n in g["nodes"]:
            x0, y0, x1, y1 = n["bbox"]
            annots.append({"id": len(annots) + 1, "image_id": img_id, "category_id": cat_id[n["l2"]], "bbox": [round(x0, 2), round(y0, 2), round(x1 - x0, 2), round(y1 - y0, 2)],
                           "area": round((x1 - x0) * (y1 - y0), 1), "iscrowd": 0, "region_id": n["id"],
                           "attributes": {k: n.get(k) for k in ("semantic_class", "visual_form", "confidence", "is_zone", "l1_hint", "io_role", "graph_id", "label_text", "parent_id") if n.get(k) not in (None, "")}})
    (out / "coco.json").write_text(json.dumps({"info": {"description": "WWTP_vision GT (taxonomy v1.1, L2)", "source_export": Path(a.export).name},
                                               "images": images, "categories": cats, "annotations": annots}, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(out / "manifest.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0].keys())); w.writeheader(); w.writerows(manifest)
    if a.split:
        fr = [float(x) for x in a.split.split(",")]
        rng = random.Random(a.seed)
        by_src = defaultdict(set)
        for r in manifest:
            by_src[r["source"]].add(r["doc_id"] or r["key"])
        split = {}
        for src, docs in sorted(by_src.items()):
            docs = sorted(docs); rng.shuffle(docs)
            n = len(docs); n_tr, n_va = round(fr[0] * n), round(fr[1] * n)
            for i, d in enumerate(docs):
                split[d] = "train" if i < n_tr else ("val" if i < n_tr + n_va else "test")
        per_image = {r["key"]: split[r["doc_id"] or r["key"]] for r in manifest}
        (out / "splits.json").write_text(json.dumps({"by_document": split, "by_image": per_image, "seed": a.seed, "fractions": fr}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(images)} images, {len(annots)} boxes, {sum(len(json.loads((out / 'graphs' / f).read_text(encoding='utf-8'))['edges']) for f in [p.name for p in (out / 'graphs').glob('*.graph.json')])} edges, {len(cats)} categories -> {out}")


if __name__ == "__main__":
    main()
