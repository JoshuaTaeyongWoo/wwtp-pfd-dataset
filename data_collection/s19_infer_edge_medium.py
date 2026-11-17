"""
s19_infer_edge_medium.py — fill `medium` / `stream_role` for pilot-lite edges from the endpoint classes
(rule table: annotation/edge_medium_rules.md, pilot protocol v1.1b).

Input : a Label Studio JSON export (one annotator). Boxes = rectanglelabels; relations = edges
        (direction "right" = from -> to; "left" swapped; "bi" -> ambiguous). Relation labels:
        no_arrow -> direction_confidence=inferred, direction_unknown -> ambiguous, style:dashed,
        optional, parent_of (-> parent_id, not an edge).
Output: <out_dir>/<image>.graph.json per task (plan §4.6 schema) and <out_dir>/_summary.csv
        (rule hits, ambiguous edges to be resolved by the adjudicator).

Usage: python s19_infer_edge_medium.py --export data/pilot/exports/pilot_A.json --out data/pilot/graphs_A
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

PASS = {"junction_split", "junction_merge", "pump", "valve", "storage_tank"}
BIO = {"aerobic_zone", "anoxic_zone", "anaerobic_zone", "sbr_tank", "biofilm_reactor", "mbr_unit", "anaerobic_wastewater_reactor", "pond_lagoon_wetland"}
ZONES = {"aerobic_zone", "anoxic_zone", "anaerobic_zone", "sbr_tank"}
SLUDGE = {"thickener", "digester", "dewatering_unit", "fermenter", "drying_incineration_unit", "biogas_unit"}
MAIN = {"screen", "grit_chamber", "equalization_tank", "pump_station", "primary_clarifier", "flotation_unit", "chemical_treatment_unit",
        "secondary_clarifier", "filtration_unit", "membrane_unit", "disinfection_unit"} | BIO


def l2(cls: str) -> str:
    return cls.split("/")[0]


def l3(cls: str) -> str:
    return cls.split("/")[1] if "/" in cls else ""


def node_kind(n: dict) -> str:
    """class plus the attributes the rules look at, e.g. io_terminal(chemical_source), generic(sludge)."""
    c = l2(n["cls"])
    if c == "io_terminal":
        return f"io:{n['attrs'].get('io_role', '')}"
    if c in ("process_unit_generic", "unknown_equipment"):
        return f"{c}:{n['attrs'].get('l1_hint', 'unknown')}"
    return c


def infer(src: dict, dst: dict, src_text: str = "") -> tuple[str, str, int]:
    """-> (medium, stream_role, rule_no). Follows annotation/edge_medium_rules.md."""
    s, d = node_kind(src), node_kind(dst)
    sc, dc = l2(src["cls"]), l2(dst["cls"])
    s_hint = s.split(":")[1] if ":" in s else ""
    d_hint = d.split(":")[1] if ":" in d else ""
    txt = (src_text or "").lower()
    if s == "io:chemical_source":
        return ("chemical", "carbon_source" if any(k in txt for k in ("methanol", "acetate", "carbon", "탄소원", "메탄올")) else "chemical_dose", 1)
    if sc == "blower":
        return ("air", "oxygen" if "oxygen" in txt or "순산소" in txt else "air_supply", 2)
    if dc == "blower":
        return ("air", "air_supply", 3)
    if sc in ("digester", "anaerobic_wastewater_reactor") and (dc == "biogas_unit" or d == "io:biogas_use"):
        return ("gas", "biogas", 4)
    if sc == "digester" and (d == "io:off_gas_out" or dc == "unknown_equipment"):
        return ("gas", "off_gas", 5)
    if sc == "secondary_clarifier" and dc == "biofilm_reactor" and l3(dst["cls"]) == "trickling_filter":
        return ("liquid", "effluent_recirculation_qr", 6)
    if sc in ("secondary_clarifier", "mbr_unit") and (dc in ZONES or dc == "biofilm_reactor" or (dc == "process_unit_generic" and d_hint == "secondary")):
        return ("sludge", "ras_s", 7)
    if sc in ({"secondary_clarifier", "mbr_unit"} | ZONES) and (dc in {"thickener", "digester", "dewatering_unit", "flotation_unit", "fermenter"} or d == "io:solids_disposal" or (dc == "process_unit_generic" and d_hint == "sludge")):
        return ("sludge", "was", 8)
    if sc == "primary_clarifier" and (dc in {"thickener", "digester", "fermenter", "dewatering_unit"} or (dc == "process_unit_generic" and d_hint == "sludge")):
        return ("sludge", "primary_sludge", 9)
    if sc == "primary_clarifier" and (dc in BIO or dc == "secondary_clarifier" or (dc == "process_unit_generic" and d_hint == "secondary")):
        return ("liquid", "settled_influent", 10)
    if sc == "aerobic_zone" and dc in ("anoxic_zone", "anaerobic_zone"):
        return ("mixed_liquor", "internal_recycle_a", 11)
    if sc == "anoxic_zone" and dc == "anaerobic_zone":
        return ("mixed_liquor", "r_recycle", 12)
    s_bio = sc in ZONES or (sc == "process_unit_generic" and s_hint == "secondary")
    d_bio = dc in ZONES or (dc == "process_unit_generic" and d_hint == "secondary")
    if s_bio and (d_bio or dc in ("secondary_clarifier", "mbr_unit", "biofilm_reactor")):
        return ("mixed_liquor", "mixed_liquor", 13)
    if sc == "fermenter" and dc in BIO:
        return ("liquid", "fermentate", 14)
    if sc == "fermenter" and dc == "digester":
        return ("sludge", "primary_sludge", 15)
    if (sc == "thickener" or (sc == "flotation_unit" and src["attrs"].get("function") == "thickening")) and dc in {"digester", "dewatering_unit", "fermenter", "storage_tank"}:
        return ("sludge", "thickened_sludge", 16)
    if sc == "digester" and dc in {"dewatering_unit", "thickener", "storage_tank", "drying_incineration_unit"}:
        return ("sludge", "digested_sludge", 17)
    if sc == "dewatering_unit" and (d == "io:solids_disposal" or dc == "drying_incineration_unit" or (dc == "storage_tank" and src["attrs"].get("treatment_line") == "sludge")):
        return ("solid", "dewatered_cake", 18)
    if sc in {"dewatering_unit", "thickener", "digester", "sidestream_reactor"} and (dc in MAIN or dc == "sidestream_reactor" or dc == "junction_merge" or dc == "equalization_tank"):
        return ("liquid", "sidestream_return", 19)
    if sc == "drying_incineration_unit" and d == "io:solids_disposal":
        return ("solid", "dewatered_cake", 20)
    if sc in ("screen", "grit_chamber") and (d == "io:solids_disposal" or dc == "unknown_equipment"):
        return ("solid", "screenings_grit", 21)
    if sc in ("filtration_unit", "membrane_unit", "biofilm_reactor") and dc in ("equalization_tank", "junction_merge", "primary_clarifier", "screen", "grit_chamber", "pump_station"):
        return ("liquid", "backwash_return", 22)
    if s == "io:external_waste_in" and dc in ("digester", "anaerobic_wastewater_reactor"):
        return ("sludge", "co_substrate", 23)
    if s == "io:raw_influent":
        return ("liquid", "influent", 24)
    if d in ("io:effluent", "io:reclaimed_water_out"):
        return ("liquid", "effluent" if d == "io:effluent" else "reclaimed_water", 25)
    if d == "io:overflow_bypass_out":
        return ("liquid", "overflow", 26)
    if sc == "instrument" or dc == "instrument":
        return ("signal", "signal", 27)
    if sc in MAIN and dc in MAIN:
        return ("liquid", "liquid_unknown_role", 28)
    if sc in SLUDGE or dc in SLUDGE or s_hint == "sludge" or d_hint == "sludge":
        return ("sludge", "sludge_unknown_role", 29)
    return ("ambiguous", "", 30)


# ----------------------------------------------------------------------------- Label Studio export
def load_tasks(path: Path):
    for task in json.loads(path.read_text(encoding="utf-8")):
        ann = (task.get("annotations") or [{}])[0]
        res = ann.get("result", [])
        nodes, per_region, rels = {}, defaultdict(dict), []
        for r in res:
            if r.get("type") == "rectanglelabels":
                v = r["value"]; w, h = r.get("original_width", 100), r.get("original_height", 100)
                x0, y0 = v["x"] / 100 * w, v["y"] / 100 * h
                nodes[r["id"]] = {"id": r["id"], "cls": v["rectanglelabels"][0], "bbox": [x0, y0, x0 + v["width"] / 100 * w, y0 + v["height"] / 100 * h], "attrs": {}, "parent_id": None}
            elif r.get("type") == "relation":
                rels.append(r)
            elif r.get("type") in ("choices", "textarea") and r.get("id"):
                val = r["value"].get("choices") or r["value"].get("text")
                per_region[r["id"]][r["from_name"]] = val[0] if isinstance(val, list) and len(val) == 1 else val
        for nid, n in nodes.items():
            n["attrs"] = per_region.get(nid, {})
        yield Path(task["data"].get("image", str(task.get("id")))).name, nodes, rels


def build_graph(image: str, nodes: dict, rels: list) -> dict:
    edges = []
    for r in rels:
        labels = set(r.get("labels") or [])
        a, b = r["from_id"], r["to_id"]
        if a not in nodes or b not in nodes:
            continue
        if "parent_of" in labels:
            nodes[b]["parent_id"] = a
            continue
        direction = r.get("direction", "right")
        if direction == "left":
            a, b = b, a
        edges.append({"id": f"e{len(edges) + 1}", "src": a, "dst": b,
                      "direction_confidence": "ambiguous" if (direction == "bi" or "direction_unknown" in labels) else ("inferred" if "no_arrow" in labels else "arrowhead"),
                      "line_style": "dashed" if "style:dashed" in labels else "solid", "optional": "optional" in labels})
    out_e, in_e = defaultdict(list), defaultdict(list)
    for e in edges:
        out_e[e["src"]].append(e); in_e[e["dst"]].append(e)

    def eff_src(e, depth=0):
        n = nodes[e["src"]]
        if l2(n["cls"]) not in PASS or depth > 6:
            return n
        ups = [x for x in in_e[n["id"]] if x is not e]
        return eff_src(ups[0], depth + 1) if len(ups) == 1 else None

    def eff_dst(e, depth=0):
        n = nodes[e["dst"]]
        if l2(n["cls"]) not in PASS or depth > 6:
            return n
        downs = [x for x in out_e[n["id"]] if x is not e]
        return eff_dst(downs[0], depth + 1) if len(downs) == 1 else None

    pending = []
    for e in edges:
        s, d = eff_src(e), eff_dst(e)
        if s is None or d is None:
            pending.append(e)
            continue
        m, role, rule = infer(s, d, str(s["attrs"].get("label_text", "")) + " " + str(d["attrs"].get("label_text", "")))
        e.update({"medium": m, "stream_role": role, "rule": rule, "eff_src": s["id"], "eff_dst": d["id"]})
    # second pass: an edge INTO a split (or out of a merge) takes the medium shared by its branches
    for e in pending:
        branches = [x for x in out_e[e["dst"]] if x is not e and "medium" in x] or [x for x in in_e[e["src"]] if x is not e and "medium" in x]
        media = {x["medium"] for x in branches if x.get("medium") not in (None, "ambiguous")}
        if len(media) == 1:
            e.update({"medium": media.pop(), "stream_role": "split_or_merge_trunk", "rule": 31, "note": "inherited from branches"})
        else:
            e.update({"medium": "ambiguous", "stream_role": "", "rule": 30, "note": "pass-through chain not unique"})
    return {"image": image, "nodes": [{"id": n["id"], "semantic_class": n["cls"], "l2": l2(n["cls"]), "bbox": n["bbox"], "parent_id": n["parent_id"], **{k: v for k, v in n["attrs"].items()}} for n in nodes.values()],
            "edges": edges}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rule_hits, rows = Counter(), []
    for image, nodes, rels in load_tasks(Path(a.export)):
        g = build_graph(image, nodes, rels)
        (out / f"{Path(image).stem}.graph.json").write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
        for e in g["edges"]:
            rule_hits[e["rule"]] += 1
            if e["medium"] == "ambiguous":
                rows.append({"image": image, "edge": e["id"], "src": nodes[e["src"]]["cls"], "dst": nodes[e["dst"]]["cls"], "note": e.get("note", "")})
    with open(out / "_ambiguous.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["image", "edge", "src", "dst", "note"]); w.writeheader(); w.writerows(rows)
    total = sum(rule_hits.values())
    print(f"edges {total}, ambiguous {rule_hits[30]} ({rule_hits[30] / total:.0%} )" if total else "no edges")
    print("rule hits:", dict(sorted(rule_hits.items())))


if __name__ == "__main__":
    main()
