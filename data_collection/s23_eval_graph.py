"""
s23_eval_graph.py — benchmark evaluation (plan §6): detection + semantic mapping + connectivity.

GT   : a folder written by s22 (coco.json, graphs/*.graph.json, manifest.csv).
Pred : a folder of graphs/*.graph.json with the same keys (nodes: bbox [x0,y0,x1,y1] px, semantic_class or l2,
       optional score; edges: src, dst, optional direction_confidence), e.g. a model's output or another
       annotator's s22/s19 folder. Optionally --pred-coco results.json (COCO results format) for detection AP
       with real confidence scores; otherwise detections are taken from the pred graphs with score 1.

Metrics
  detection : AP50, AP[.5:.95] (101-point), per-class AP50, at L2 and L1 (labels collapsed, Open-Images style);
              LVIS buckets by number of GT images per class (rare 1-10, common 11-100, frequent >100);
              strata from manifest (diagram_style, source, lang) and by GT visual_form
  semantic  : for GT boxes with visual_form=box, L2 accuracy of the class-agnostic IoU>=0.5 match
  graph     : node matching IoU>=0.5 (class required / agnostic), edge P/R/F1, direction accuracy
              (arrowhead-backed GT edges / all), inferred-edge P/R separately, normalised graph edit distance
              = (node del + node ins + class subst + edge del + edge ins) / |GT nodes|

Usage:
  python s23_eval_graph.py --gt data/pilot/gt_A --pred data/pilot/gt_B [--pred-coco results.json] [--out report.md]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from s17_pilot_agreement import L1_OF, iou


# ----------------------------------------------------------------------------- loading
def norm(key: str) -> str:
    """image key without extension ('pilot_02__x.png', 'pilot_02__x.graph.json' -> 'pilot_02__x')."""
    import re
    return re.sub(r"(\.graph)?\.[A-Za-z0-9]+$", "", Path(key).name)


def load_gt(d: Path):
    coco = json.loads((d / "coco.json").read_text(encoding="utf-8"))
    cats = {c["id"]: c["name"] for c in coco["categories"]}
    gt = defaultdict(list)
    for a in coco["annotations"]:
        x, y, w, h = a["bbox"]
        gt[a["image_id"]].append({"cls": cats[a["category_id"]], "bbox": [x, y, x + w, y + h], "attrs": a.get("attributes", {}), "id": a.get("region_id")})
    keys = {im["id"]: norm(im["key"]) for im in coco["images"]}
    manifest = {}
    if (d / "manifest.csv").exists():
        with open(d / "manifest.csv", encoding="utf-8-sig") as f:
            manifest = {norm(r["key"]): r for r in csv.DictReader(f)}
    graphs = {norm(p.name): json.loads(p.read_text(encoding="utf-8")) for p in (d / "graphs").glob("*.graph.json")}
    return coco, {keys[i]: v for i, v in gt.items()}, manifest, graphs, keys


def load_pred_graphs(d: Path):
    g = d / "graphs" if (d / "graphs").exists() else d
    return {norm(p.name): json.loads(p.read_text(encoding="utf-8")) for p in g.glob("*.graph.json")}


def node_cls(n: dict) -> str:
    return (n.get("l2") or n.get("semantic_class", "")).split("/")[0]


def pred_dets(pred_graphs: dict, pred_coco: Path | None, keys: dict, cats_by_name: dict):
    """-> {key: [{cls, bbox, score}]}"""
    out = defaultdict(list)
    if pred_coco:
        id2name = {v: k for k, v in cats_by_name.items()}
        for r in json.loads(pred_coco.read_text(encoding="utf-8")):
            x, y, w, h = r["bbox"]
            out[keys[r["image_id"]]].append({"cls": id2name[r["category_id"]], "bbox": [x, y, x + w, y + h], "score": r.get("score", 1.0)})
    else:
        for k, g in pred_graphs.items():
            for n in g["nodes"]:
                out[k].append({"cls": node_cls(n), "bbox": n["bbox"], "score": n.get("score", 1.0)})
    return out


# ----------------------------------------------------------------------------- detection AP
def ap_for_class(gt: dict, dets: dict, cls: str, thr: float, collapse=None) -> float | None:
    c = (lambda x: collapse.get(x, x)) if collapse else (lambda x: x)
    g = {k: [b for b in v if c(b["cls"]) == cls] for k, v in gt.items()}
    n_gt = sum(len(v) for v in g.values())
    if n_gt == 0:
        return None
    d = sorted(((x["score"], k, x) for k, v in dets.items() for x in v if c(x["cls"]) == cls), key=lambda t: -t[0])
    used = {k: [False] * len(v) for k, v in g.items()}
    tp = []
    for _, k, x in d:
        best, bi = 0.0, -1
        for i, b in enumerate(g.get(k, [])):
            v = iou(x["bbox"], b["bbox"])
            if v > best:
                best, bi = v, i
        if best >= thr and not used[k][bi]:
            used[k][bi] = True; tp.append(1)
        else:
            tp.append(0)
    if not tp:
        return 0.0
    tp = np.array(tp); fp = 1 - tp
    rec = np.cumsum(tp) / n_gt; prec = np.cumsum(tp) / (np.cumsum(tp) + np.cumsum(fp))
    for i in range(len(prec) - 2, -1, -1):
        prec[i] = max(prec[i], prec[i + 1])
    return float(np.mean([prec[rec >= r].max() if (rec >= r).any() else 0.0 for r in np.linspace(0, 1, 101)]))


def detection_block(gt, dets, classes, collapse=None) -> dict:
    thrs = np.arange(0.5, 0.96, 0.05)
    per = {}
    for cls in classes:
        aps = [ap_for_class(gt, dets, cls, t, collapse) for t in thrs]
        if aps[0] is None:
            continue
        per[cls] = {"AP50": aps[0], "AP": float(np.mean(aps)), "n_gt": sum(1 for v in gt.values() for b in v if (collapse or {}).get(b["cls"], b["cls"]) == cls)}
    return {"mAP50": float(np.mean([v["AP50"] for v in per.values()])) if per else float("nan"),
            "mAP": float(np.mean([v["AP"] for v in per.values()])) if per else float("nan"), "per_class": per}


# ----------------------------------------------------------------------------- graph metrics
def match_nodes(gn, pn, thr=0.5, need_class=True):
    pairs = sorted(((iou(a["bbox"], b["bbox"]), i, j) for i, a in enumerate(gn) for j, b in enumerate(pn)
                    if not need_class or node_cls(a) == node_cls(b)), reverse=True)
    ua, ub, m = set(), set(), {}
    for v, i, j in pairs:
        if v < thr:
            break
        if i in ua or j in ub:
            continue
        ua.add(i); ub.add(j); m[i] = j
    return m


def graph_block(gt_graphs: dict, pred_graphs: dict, need_class: bool) -> dict:
    tot = Counter()
    for k, G in gt_graphs.items():
        P = pred_graphs.get(k, {"nodes": [], "edges": []})
        gn, pn = G["nodes"], P["nodes"]
        m = match_nodes(gn, pn, need_class=need_class)
        g2p = {gn[i]["id"]: pn[j]["id"] for i, j in m.items()}
        subst = sum(node_cls(gn[i]) != node_cls(pn[j]) for i, j in m.items())
        ge = {(e["src"], e["dst"]): e for e in G["edges"]}
        pe = {(e["src"], e["dst"]) for e in P["edges"]}
        ge_m = {(g2p[s], g2p[d]): e for (s, d), e in ge.items() if s in g2p and d in g2p}  # GT edges whose endpoints are both matched
        tp = sum(1 for e in ge_m if e in pe)
        tot.update({"n_gt_nodes": len(gn), "n_pred_nodes": len(pn), "matched": len(m), "subst": subst,
                    "n_gt_edges": len(ge), "n_pred_edges": len(pe), "edge_tp": tp})
        for (s, d), e in ge_m.items():
            kind = "arrow" if e.get("direction_confidence") == "arrowhead" else ("inferred" if e.get("direction_confidence") == "inferred" else "amb")
            present = (s, d) in pe or (d, s) in pe
            tot[f"{kind}_total"] += 1
            if present:
                tot[f"{kind}_present"] += 1
                tot[f"{kind}_dir_ok"] += (s, d) in pe
            if kind == "inferred":
                tot["inf_tp"] += (s, d) in pe
        tot["inf_pred"] += 0  # placeholder for symmetry
        ged = (len(gn) - len(m)) + (len(pn) - len(m)) + subst + (len(ge) - tp) + (len(pe) - tp)
        tot["ged_sum"] += ged; tot["ged_norm_sum"] += ged / max(len(gn), 1); tot["images"] += 1
    p = tot["edge_tp"] / tot["n_pred_edges"] if tot["n_pred_edges"] else float("nan")
    r = tot["edge_tp"] / tot["n_gt_edges"] if tot["n_gt_edges"] else float("nan")
    return {"node_recall": tot["matched"] / tot["n_gt_nodes"] if tot["n_gt_nodes"] else float("nan"),
            "node_precision": tot["matched"] / tot["n_pred_nodes"] if tot["n_pred_nodes"] else float("nan"),
            "class_subst_rate": tot["subst"] / tot["matched"] if tot["matched"] else float("nan"),
            "edge_precision": p, "edge_recall": r, "edge_f1": 2 * p * r / (p + r) if p == p and r == r and (p + r) else float("nan"),
            "direction_acc_arrowhead": tot["arrow_dir_ok"] / tot["arrow_present"] if tot["arrow_present"] else float("nan"),
            "direction_acc_all": (tot["arrow_dir_ok"] + tot["inferred_dir_ok"] + tot["amb_dir_ok"]) / (tot["arrow_present"] + tot["inferred_present"] + tot["amb_present"]) if (tot["arrow_present"] + tot["inferred_present"] + tot["amb_present"]) else float("nan"),
            "inferred_edge_recall": tot["inf_tp"] / tot["inferred_total"] if tot["inferred_total"] else float("nan"),
            "ged_norm_mean": tot["ged_norm_sum"] / tot["images"] if tot["images"] else float("nan"),
            "counts": dict(tot)}


def semantic_block(gt: dict, pred_graphs: dict) -> dict:
    """box-form GT: does the class-agnostic matched prediction carry the right L2?"""
    n, ok = 0, 0
    for k, boxes in gt.items():
        pn = pred_graphs.get(k, {"nodes": []})["nodes"]
        gb = [b for b in boxes if b["attrs"].get("visual_form") == "box"]
        m = match_nodes([{"bbox": b["bbox"], "l2": b["cls"]} for b in gb], pn, need_class=False)
        n += len(gb); ok += sum(node_cls(pn[j]) == gb[i]["cls"] for i, j in m.items())
    return {"n_box_form_gt": n, "l2_acc_on_box_form": ok / n if n else float("nan")}


# ----------------------------------------------------------------------------- main
def fmt(v):
    return f"{v:.3f}" if isinstance(v, float) and v == v else ("—" if isinstance(v, float) else str(v))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", required=True); ap.add_argument("--pred", required=True)
    ap.add_argument("--pred-coco", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    coco, gt, manifest, gt_graphs, keys = load_gt(Path(a.gt))
    pred_graphs = load_pred_graphs(Path(a.pred))
    cats_by_name = {c["name"]: c["id"] for c in coco["categories"]}
    dets = pred_dets(pred_graphs, Path(a.pred_coco) if a.pred_coco else None, keys, cats_by_name)
    classes = [c["name"] for c in coco["categories"]]
    l1_classes = sorted(set(L1_OF.values()))
    det_l2 = detection_block(gt, dets, classes)
    det_l1 = detection_block(gt, dets, l1_classes, collapse=L1_OF)
    # LVIS buckets by number of GT images containing the class
    img_per_cls = Counter(c for v in gt.values() for c in {b["cls"] for b in v})
    bucket = lambda c: "rare" if img_per_cls[c] <= 10 else ("common" if img_per_cls[c] <= 100 else "frequent")
    lvis = {b: float(np.mean([v["AP50"] for c, v in det_l2["per_class"].items() if bucket(c) == b])) for b in ("rare", "common", "frequent") if any(bucket(c) == b for c in det_l2["per_class"])}
    strata = {}
    for field in ("diagram_style", "source", "lang"):
        for val in sorted({m.get(field, "") for m in manifest.values()} - {""}):
            ks = {k for k, m in manifest.items() if m.get(field) == val}
            sub_gt = {k: v for k, v in gt.items() if k in ks}
            if sub_gt:
                strata[f"{field}={val}"] = {"images": len(sub_gt), "mAP50": detection_block(sub_gt, {k: v for k, v in dets.items() if k in ks}, classes)["mAP50"]}
    vf_strata = {}
    for vf in ("symbol", "box", "pictorial", "simulator_icon", "section_view"):
        sub = {k: [b for b in v if b["attrs"].get("visual_form") == vf] for k, v in gt.items()}
        if any(sub.values()):
            vf_strata[vf] = detection_block(sub, dets, classes)["mAP50"]
    sem = semantic_block(gt, pred_graphs)
    g_cls = graph_block(gt_graphs, pred_graphs, need_class=True)
    g_agn = graph_block(gt_graphs, pred_graphs, need_class=False)
    rep = {"detection_L2": det_l2, "detection_L1": det_l1, "lvis_AP50": lvis, "strata_mAP50": strata, "visual_form_mAP50": vf_strata,
           "semantic": sem, "graph_class_required": g_cls, "graph_class_agnostic": g_agn}
    L = [f"# Evaluation — GT {a.gt} vs pred {a.pred} ({len(gt)} images)", "",
         "| detection | L2 | L1 |", "|---|---|---|",
         f"| mAP50 | {fmt(det_l2['mAP50'])} | {fmt(det_l1['mAP50'])} |", f"| mAP[.5:.95] | {fmt(det_l2['mAP'])} | {fmt(det_l1['mAP'])} |", "",
         "LVIS buckets AP50 (L2): " + ", ".join(f"{k} {fmt(v)}" for k, v in lvis.items()),
         "visual_form AP50 (L2): " + ", ".join(f"{k} {fmt(v)}" for k, v in vf_strata.items()),
         "strata mAP50 (L2): " + ", ".join(f"{k} {fmt(v['mAP50'])} (n={v['images']})" for k, v in strata.items()), "",
         f"semantic mapping on box-form GT: L2 acc {fmt(sem['l2_acc_on_box_form'])} (n={sem['n_box_form_gt']})", "",
         "| graph | class required | class agnostic |", "|---|---|---|"]
    for k in ("node_recall", "node_precision", "class_subst_rate", "edge_precision", "edge_recall", "edge_f1", "direction_acc_arrowhead", "direction_acc_all", "inferred_edge_recall", "ged_norm_mean"):
        L.append(f"| {k} | {fmt(g_cls[k])} | {fmt(g_agn[k])} |")
    L += ["", "| class | n_gt | AP50 | AP |", "|---|---|---|---|"] + [f"| {c} | {v['n_gt']} | {fmt(v['AP50'])} | {fmt(v['AP'])} |" for c, v in sorted(det_l2["per_class"].items())]
    text = "\n".join(L)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8"); Path(a.out).with_suffix(".json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8"); print(text)


if __name__ == "__main__":
    main()
