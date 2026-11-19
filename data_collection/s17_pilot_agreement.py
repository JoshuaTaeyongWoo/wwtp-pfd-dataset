"""
s17_pilot_agreement.py — inter-annotator agreement for the 60-image pilot (plan §5.1).

Input: two Label Studio JSON exports (one per annotator) of the same pilot project, or two
directories of per-image graph.json files in the plan §4.6 format. Boxes are matched greedily by
IoU (threshold 0.5); on the matched pairs we compute

  * class agreement  : Cohen's kappa on L2 (and on L1 after collapsing), per-class kappa only for
                       classes with >= 20 matched instances, others folded into L1
  * box agreement    : share of matched pairs with IoU >= 0.7, mean IoU
  * coverage         : unmatched boxes per annotator (missing / extra), overall and per class
  * edges            : precision / recall / F1 of (src, dst) pairs after node matching, plus
                       direction accuracy on arrowhead-backed edges
  * all with bootstrap 95 % CIs (resampling images, 1,000 draws)

Also:
  --expand-cvat annotation/cvat_labels.json   expand the "@group" shorthand into a CVAT labels file

Usage:
  python s17_pilot_agreement.py --a exports/annotatorA.json --b exports/annotatorB.json [--out data/pilot/agreement.md]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

L1_OF = {
    "screen": "preliminary", "grit_chamber": "preliminary", "equalization_tank": "preliminary", "pump_station": "preliminary",
    "primary_clarifier": "primary", "flotation_unit": "separation", "chemical_treatment_unit": "separation",
    "aerobic_zone": "secondary", "anoxic_zone": "secondary", "anaerobic_zone": "secondary", "secondary_clarifier": "secondary",
    "mbr_unit": "secondary", "sbr_tank": "secondary", "biofilm_reactor": "secondary", "anaerobic_wastewater_reactor": "secondary",
    "pond_lagoon_wetland": "secondary", "sidestream_reactor": "sidestream",
    "filtration_unit": "tertiary", "membrane_unit": "tertiary", "disinfection_unit": "tertiary",
    "fermenter": "sludge", "thickener": "sludge", "digester": "sludge", "dewatering_unit": "sludge",
    "drying_incineration_unit": "sludge", "biogas_unit": "sludge",
    "pump": "ancillary", "blower": "ancillary", "storage_tank": "ancillary", "valve": "ancillary", "aerator_mixer_symbol": "ancillary",
    "process_unit_generic": "generic", "unknown_equipment": "generic",
    "arrowhead": "annotation", "text_label": "annotation", "stream_tag": "annotation", "stream_label": "annotation",
    "io_terminal": "annotation", "junction_split": "annotation", "junction_merge": "annotation", "instrument": "annotation",
}


# ----------------------------------------------------------------------------- loading
def image_key(task: dict) -> str:
    """Label Studio prefixes uploaded files with an 8-hex upload id ('/data/upload/4/3e304446-pilot_01__x.png');
    strip it so the same image gets the same key in both annotators' exports."""
    import re
    name = Path(task["data"].get("image", str(task.get("id")))).name
    return re.sub(r"^[0-9a-f]{8}-", "", name)


def load_label_studio(path: Path) -> dict[str, dict]:
    """-> {image_key: {"boxes": [{id, cls, l2, bbox[x0,y0,x1,y1] in px, attrs}], "edges": [(src,dst,label)]}}"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for task in data:
        key = image_key(task)
        ann = (task.get("annotations") or [{}])[0]
        boxes, edges, per_region = [], [], defaultdict(dict)
        for r in ann.get("result", []):
            t = r.get("type")
            if t == "rectanglelabels":
                v = r["value"]
                w, h = r.get("original_width", 100), r.get("original_height", 100)
                x0, y0 = v["x"] / 100 * w, v["y"] / 100 * h
                x1, y1 = x0 + v["width"] / 100 * w, y0 + v["height"] / 100 * h
                cls = v["rectanglelabels"][0]
                boxes.append({"id": r["id"], "cls": cls, "l2": cls.split("/")[0], "bbox": [x0, y0, x1, y1], "attrs": {},
                              "small": (x1 - x0) * (y1 - y0) < SMALL_FRAC * w * h})
            elif t == "relation":
                edges.append((r["from_id"], r["to_id"], (r.get("labels") or [""])[0]))
            elif t in ("choices", "textarea") and r.get("id"):
                val = r["value"].get("choices") or r["value"].get("text")
                per_region[r["id"]][r["from_name"]] = val[0] if isinstance(val, list) and len(val) == 1 else val
        for b in boxes:
            b["attrs"] = per_region.get(b["id"], {})
        image_attrs = {k: v for rid, d in per_region.items() if rid not in {b["id"] for b in boxes} for k, v in d.items()}
        out[key] = {"boxes": boxes, "edges": edges, "image_attrs": image_attrs}
    return out


def load_graph_dir(path: Path) -> dict[str, dict]:
    out = {}
    for f in Path(path).glob("*.json"):
        g = json.loads(f.read_text(encoding="utf-8"))
        boxes = [{"id": n["id"], "cls": n.get("semantic_class", ""), "l2": n.get("semantic_class", "").split("/")[0],
                  "bbox": n["bbox"], "attrs": n} for n in g.get("nodes", [])]
        edges = [(e["src"], e["dst"], f"{e.get('medium', '')}|{e.get('direction_confidence', '')}") for e in g.get("edges", [])]
        out[f.stem] = {"boxes": boxes, "edges": edges}
    return out


# ----------------------------------------------------------------------------- matching & stats
def iou(a, b) -> float:
    ix0, iy0, ix1, iy1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix1 - ix0) * max(0, iy1 - iy0)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


SMALL_FRAC = 0.002  # boxes under 0.2 % of the image area (junctions, arrowheads, valves): a few px of jitter already breaks IoU 0.5


def center_close(a, b) -> bool:
    """small-box fallback: centres closer than the larger box's longest side."""
    ca = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2); cb = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    tol = max(a[2] - a[0], a[3] - a[1], b[2] - b[0], b[3] - b[1])
    return abs(ca[0] - cb[0]) <= tol and abs(ca[1] - cb[1]) <= tol


def match(boxes_a, boxes_b, thr=0.5):
    """greedy IoU >= thr; then, for pairs of SMALL boxes left over, centre proximity (plan §4.6 note).
    Returns (matched [(i, j, iou, by_iou)], unmatched_a, unmatched_b)."""
    pairs = sorted(((iou(a["bbox"], b["bbox"]), i, j) for i, a in enumerate(boxes_a) for j, b in enumerate(boxes_b)), reverse=True)
    used_a, used_b, matched = set(), set(), []
    for v, i, j in pairs:
        if v < thr:
            break
        if i in used_a or j in used_b:
            continue
        used_a.add(i); used_b.add(j); matched.append((i, j, v, True))
    for v, i, j in pairs:
        if i in used_a or j in used_b or v >= thr:
            continue
        if boxes_a[i].get("small") and boxes_b[j].get("small") and center_close(boxes_a[i]["bbox"], boxes_b[j]["bbox"]):
            used_a.add(i); used_b.add(j); matched.append((i, j, v, False))
    return matched, [i for i in range(len(boxes_a)) if i not in used_a], [j for j in range(len(boxes_b)) if j not in used_b]


def cohen_kappa(pairs: list[tuple[str, str]]) -> float:
    n = len(pairs)
    if n == 0:
        return float("nan")
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


FULL_ONLY = {"arrowhead", "text_label", "stream_tag", "stream_label"}


def pilot_no(key: str) -> int:
    import re
    m = re.search(r"pilot_(\d+)", key)
    return int(m.group(1)) if m else 0


ATTRS_T1 = ["visual_form", "confidence", "is_zone", "l1_hint", "io_role", "graph_id"]


def disagreements(A: dict, B: dict, key: str, full_subset: int = 20) -> list[dict]:
    """Rows for the adjudicator: every place A and B differ on this image (class, box, attribute, edge, image field)."""
    a, b = A.get(key, {"boxes": [], "edges": []}), B.get(key, {"boxes": [], "edges": []})
    lite = bool(full_subset) and pilot_no(key) > full_subset
    ba = [x for x in a["boxes"] if not (lite and x["l2"] in FULL_ONLY)]
    bb = [x for x in b["boxes"] if not (lite and x["l2"] in FULL_ONLY)]
    matched, miss_a, miss_b = match(ba, bb)
    rows = []

    def row(kind, item, va, vb, hint=""):
        rows.append({"image": key, "pilot_no": pilot_no(key), "kind": kind, "item": item, "A": va, "B": vb, "hint": hint, "decision": ""})

    for i, j, v, by_iou in matched:
        x, y = ba[i], bb[j]
        if x["cls"] != y["cls"]:
            row("class", f"{x['id']}~{y['id']}", x["cls"], y["cls"], "rule 1-22 / l1_hint")
        elif by_iou and v < 0.7:
            row("box_iou<0.7", f"{x['id']}~{y['id']}", f"{x['cls']} iou={v:.2f}", f"{y['cls']}", "box extent (rule P2)")
        for k in ATTRS_T1:
            va, vb = x["attrs"].get(k), y["attrs"].get(k)
            if (va or vb) and va != vb:
                row(f"attr:{k}", f"{x['id']}~{y['id']} ({x['cls']})", va, vb, "rule 15b" if k == "visual_form" else "")
        if x["l2"] in ("process_unit_generic", "unknown_equipment") and (x["attrs"].get("label_text") or "") != (y["attrs"].get("label_text") or ""):
            row("attr:label_text", f"{x['id']}~{y['id']} ({x['cls']})", x["attrs"].get("label_text"), y["attrs"].get("label_text"))
    def near(x, others):  # same-class unmatched box on the other side that overlaps: same object, different extent
        best = max(((iou(x["bbox"], o["bbox"]), o) for o in others if o["cls"] == x["cls"]), default=(0, None), key=lambda t: t[0])
        return f"same object as {best[1]['id']}? iou={best[0]:.2f}" if best[1] is not None and best[0] > 0 else ""

    for i in miss_a:
        row("box_only_A", ba[i]["id"], ba[i]["cls"], "", near(ba[i], [bb[j] for j in miss_b]) or "missed by B or extra in A")
    for j in miss_b:
        row("box_only_B", bb[j]["id"], "", bb[j]["cls"], near(bb[j], [ba[i] for i in miss_a]) or "missed by A or extra in B")
    b2a = {bb[j]["id"]: ba[i]["id"] for i, j, _, _ in matched}
    def name(_, i):  # A node id, or '?<B id>' for a B node that has no A counterpart
        if i.startswith("?"):
            return "[B-only] " + next((x["cls"] for x in bb if x["id"] == i[1:]), "?")
        return next((x["cls"] for x in ba if x["id"] == i), "?")
    ea = {(s, d): l for s, d, l in a["edges"] if "parent_of" not in (l or "")}
    eb = {(b2a.get(s, f"?{s}"), b2a.get(d, f"?{d}")): l for s, d, l in b["edges"] if "parent_of" not in (l or "")}
    for e in sorted(set(ea) | set(eb)):
        la, lb = ea.get(e), eb.get(e)
        desc = f"{name(ba, e[0])} -> {name(ba, e[1])}"
        if e in ea and e not in eb:
            row("edge_only_A", desc, f"edge {la or 'flow'}", "", "reversed?" if (e[1], e[0]) in eb else "missed by B")
        elif e in eb and e not in ea:
            row("edge_only_B", desc, "", f"edge {lb or 'flow'}", "reversed?" if (e[1], e[0]) in ea else "missed by A")
        elif (la or "") != (lb or ""):
            row("edge_label", desc, la or "flow", lb or "flow", "no_arrow / dashed / optional")
    for k in ("diagram_style", "language", "n_panels", "process_configuration"):
        va, vb = a.get("image_attrs", {}).get(k), b.get("image_attrs", {}).get(k)
        if (va or vb) and va != vb:
            row(f"image:{k}", "", va, vb)
    return rows


def per_image_stats(A: dict, B: dict, key: str, full_subset: int = 20) -> dict:
    a, b = A.get(key, {"boxes": [], "edges": []}), B.get(key, {"boxes": [], "edges": []})
    if full_subset and pilot_no(key) > full_subset:  # pilot-lite images: full-only classes are not expected
        a = {"boxes": [x for x in a["boxes"] if x["l2"] not in FULL_ONLY], "edges": a["edges"]}
        b = {"boxes": [x for x in b["boxes"] if x["l2"] not in FULL_ONLY], "edges": b["edges"]}
    a["edges"] = [e for e in a["edges"] if "parent_of" not in (e[2] or "")]
    b["edges"] = [e for e in b["edges"] if "parent_of" not in (e[2] or "")]
    matched, miss_a, miss_b = match(a["boxes"], b["boxes"])
    cls_pairs = [(a["boxes"][i]["l2"], b["boxes"][j]["l2"]) for i, j, _, _ in matched]
    l1_pairs = [(L1_OF.get(x, x), L1_OF.get(y, y)) for x, y in cls_pairs]
    ious = [v for _, _, v, by_iou in matched if by_iou]  # small boxes matched by centre are not scored on IoU
    # edges: map B node ids onto A node ids through the matching
    b2a = {b["boxes"][j]["id"]: a["boxes"][i]["id"] for i, j, _, _ in matched}
    ea = {(s, d) for s, d, _ in a["edges"]}
    eb = {(b2a.get(s, f"?{s}"), b2a.get(d, f"?{d}")) for s, d, _ in b["edges"]}
    tp = len(ea & eb)
    return {"n_a": len(a["boxes"]), "n_b": len(b["boxes"]), "matched": len(matched), "miss_a": len(miss_a), "miss_b": len(miss_b),
            "cls_pairs": cls_pairs, "l1_pairs": l1_pairs, "ious": ious, "edge_tp": tp, "edge_a": len(ea), "edge_b": len(eb)}


def aggregate(stats: list[dict]) -> dict:
    cls_pairs = [p for s in stats for p in s["cls_pairs"]]
    l1_pairs = [p for s in stats for p in s["l1_pairs"]]
    ious = [v for s in stats for v in s["ious"]]
    n_a, n_b, m = sum(s["n_a"] for s in stats), sum(s["n_b"] for s in stats), sum(s["matched"] for s in stats)
    tp, ea, eb = sum(s["edge_tp"] for s in stats), sum(s["edge_a"] for s in stats), sum(s["edge_b"] for s in stats)
    p = tp / ea if ea else float("nan"); r = tp / eb if eb else float("nan")
    return {"kappa_l2": cohen_kappa(cls_pairs), "kappa_l1": cohen_kappa(l1_pairs),
            "iou07": sum(v >= 0.7 for v in ious) / len(ious) if ious else float("nan"),
            "mean_iou": sum(ious) / len(ious) if ious else float("nan"),
            "unmatched_a": 1 - m / n_a if n_a else float("nan"), "unmatched_b": 1 - m / n_b if n_b else float("nan"),
            "edge_p": p, "edge_r": r, "edge_f1": 2 * p * r / (p + r) if ea and eb and (p + r) else float("nan"),
            "n_matched": m, "n_boxes_a": n_a, "n_boxes_b": n_b, "n_edges_a": ea, "n_edges_b": eb}


def bootstrap(stats: list[dict], n_draw=1000, seed=0) -> dict[str, tuple[float, float]]:
    rng = random.Random(seed)
    draws = defaultdict(list)
    for _ in range(n_draw):
        sample = [stats[rng.randrange(len(stats))] for _ in stats]
        for k, v in aggregate(sample).items():
            if isinstance(v, float) and v == v:
                draws[k].append(v)
    out = {}
    for k, vs in draws.items():
        vs.sort()
        out[k] = (vs[int(0.025 * len(vs))], vs[int(0.975 * len(vs)) - 1])
    return out


def per_class_kappa(stats: list[dict], min_n=20) -> list[tuple[str, int, float]]:
    pairs = [p for s in stats for p in s["cls_pairs"]]
    rows = []
    for c in sorted({x for p in pairs for x in p}):
        sub = [(a == c, b == c) for a, b in pairs if a == c or b == c]
        n = len(sub)
        if n >= min_n:
            rows.append((c, n, cohen_kappa([(str(a), str(b)) for a, b in sub])))
    return rows


# ----------------------------------------------------------------------------- cvat helper
def expand_cvat(path: Path) -> str:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    groups = next((x["_groups"] for x in raw if isinstance(x, dict) and "_groups" in x), {})
    base = raw[0]["attributes"]
    vocab = {
        "zone_role": ["", "main", "selector", "contact", "reaeration", "deoxygenation", "degasifier", "underflow_anoxic", "post_anoxic", "stripper", "swing"],
        "aeration_mode": ["", "diffused", "surface", "brush", "jet", "hpo", "membrane", "mixer_only", "none"],
        "operation_mode": ["", "continuous", "sequencing", "alternating", "intermittent"],
        "clarifier_stage": ["", "primary", "intermediate", "secondary", "chemical"],
        "clarifier_shape": ["", "circular", "rectangular", "vertical_flow", "lamella", "multi_storey"],
        "function": ["", "primary", "secondary_separation", "tertiary", "thickening"],
        "redox_condition": ["", "aerobic", "anoxic", "anaerobic"],
        "digester_type": ["", "anaerobic", "aerobic", "atad", "two_stage", "acid_phase", "thp_fed"],
        "co_digestion": ["", "true", "false"],
        "tag_kind_text": ["", "name", "volume", "depth", "equipment_count", "hrt", "spec", "material", "capacity", "patent_number", "other"],
        "stream_role": ["", "influent", "settled_influent", "effluent", "reclaimed_water", "mixed_liquor", "internal_recycle_a", "ras_s", "r_recycle", "effluent_recirculation_qr", "was", "scum", "primary_sludge", "thickened_sludge", "digested_sludge", "dewatered_cake", "chemical_sludge", "screenings_grit", "fermentate", "co_substrate", "sidestream_return", "backwash_return", "bypass", "overflow", "step_feed", "biogas", "off_gas", "air_supply", "oxygen", "chemical_dose", "carbon_source", "signal"],
        "io_role": ["", "raw_influent", "settled_influent", "external_waste_in", "effluent", "reclaimed_water_out", "solids_disposal", "biogas_use", "off_gas_out", "chemical_source", "overflow_bypass_out", "external_sidestream"],
        "split_type": ["", "ratio", "fraction", "pumped", "bypass", "router_alternating", "pacing"],
        "merge_role": ["", "step_feed_inlet", "sidestream_return", "chemical_dosing_point", "recycle_return", "lane_combiner"],
        "instrument_role": ["", "sensor", "analyser", "controller", "setpoint"],
    }

    def attr(name):
        if name.startswith("l3:"):
            return {"name": "l3", "input_type": "select", "mutable": True, "values": name[3:].split("|"), "default_value": name[3:].split("|")[0]}
        if name in vocab:
            return {"name": name, "input_type": "select", "mutable": True, "values": vocab[name], "default_value": ""}
        if name in ("label_text", "parent_id", "measured_variable", "n_compartments"):
            return {"name": name, "input_type": "text", "mutable": True, "values": [""], "default_value": ""}
        if name == "is_zone":
            return {"name": name, "input_type": "checkbox", "mutable": True, "values": ["false"], "default_value": "false"}
        return next(a for a in base if a["name"] == name)

    labels = []
    for x in raw:
        if not isinstance(x, dict) or "name" not in x:
            continue
        spec = x["attributes"]
        if isinstance(spec, str):
            names = []
            for g in spec.lstrip("@").split("+"):
                names += groups[g]
            spec = [attr(n) for n in dict.fromkeys(names)]
        labels.append({"name": x["name"], "color": x["color"], "type": x["type"], "attributes": spec})
    return json.dumps(labels, indent=1, ensure_ascii=False)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a"); ap.add_argument("--b")
    ap.add_argument("--format", choices=["labelstudio", "graphdir"], default="labelstudio")
    ap.add_argument("--out", default="")
    ap.add_argument("--expand-cvat", default="")
    ap.add_argument("--full-subset", type=int, default=20, help="pilot numbers <= N were annotated in full (arrowheads, text); 0 = all full")
    ap.add_argument("--disagreements", default="", help="CSV of every A/B difference for the adjudicator (decision column left blank)")
    args = ap.parse_args()
    if args.expand_cvat:
        sys.stdout.reconfigure(encoding="utf-8")
        print(expand_cvat(Path(args.expand_cvat)))
        return
    load = load_label_studio if args.format == "labelstudio" else load_graph_dir
    A, B = load(Path(args.a)), load(Path(args.b))
    keys = sorted(set(A) | set(B))
    stats = [per_image_stats(A, B, k, args.full_subset) for k in keys]
    agg, ci = aggregate(stats), bootstrap(stats)
    n_full = sum(1 for k in keys if not args.full_subset or pilot_no(k) <= args.full_subset)
    lines = [f"# Pilot agreement — {len(keys)} images, annotator A vs B (full subset: {n_full} images for arrowhead/text classes; edges compared by src→dst only, medium filled by s19 rules)", "",
             "| metric | value | 95 % CI |", "|---|---|---|"]
    for k in ["kappa_l2", "kappa_l1", "iou07", "mean_iou", "unmatched_a", "unmatched_b", "edge_p", "edge_r", "edge_f1"]:
        lo, hi = ci.get(k, (float("nan"), float("nan")))
        lines.append(f"| {k} | {agg[k]:.3f} | {lo:.3f} – {hi:.3f} |")
    lines += ["", f"boxes A {agg['n_boxes_a']}, B {agg['n_boxes_b']}, matched {agg['n_matched']}; edges A {agg['n_edges_a']}, B {agg['n_edges_b']}", "",
              "| class (>= 20 matched) | n | kappa |", "|---|---|---|"]
    for c, n, k in per_class_kappa(stats):
        lines.append(f"| {c} | {n} | {k:.3f} |")
    if args.disagreements:
        import csv
        rows = [r for k in keys for r in disagreements(A, B, k, args.full_subset)]
        with open(args.disagreements, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["image", "pilot_no", "kind", "item", "A", "B", "hint", "decision"]); w.writeheader(); w.writerows(rows)
        kinds = Counter(r["kind"].split(":")[0] for r in rows)
        lines += ["", f"disagreements for adjudication: {len(rows)} rows -> {args.disagreements} ({dict(kinds)})"]
    text = "\n".join(lines)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
