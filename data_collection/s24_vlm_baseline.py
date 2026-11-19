"""
s24_vlm_baseline.py — zero-shot VLM baseline (plan §6 "baselines": graph recovery by a vision-language model
with no training on our labels). One request per image; the model returns units/zones/terminals/junctions
with pixel boxes and the flow edges between them, constrained to taxonomy v1.1 classes by a strict JSON
schema (structured outputs). Output is the s23 prediction format, so:

  python s24_vlm_baseline.py --images data/pilot/images --out data/pilot/vlm_opus55 [--limit 3] [--overlay]
  python s23_eval_graph.py --gt data/pilot/gt --pred data/pilot/vlm_opus55

Credentials: ANTHROPIC_API_KEY in the environment (or an `ant auth login` profile). Model and effort are
recorded in _summary.csv / _run.json for the paper. Cost is estimated from usage at list prices.
"""
from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import re
import time
from datetime import date
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

from common import ROOT

HERE = Path(__file__).resolve().parent
CLASSES = HERE / "annotation" / "classes.yaml"
MAX_SIDE = 1568  # the API downsizes larger images anyway; sending the resized copy keeps our coordinates exact
PRICE = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-5-5": (0.10, 0.50), "claude-fable-5-2": (8.0, 40.0)}  # $/M input, output

VISUAL_FORM = ["symbol", "box", "pictorial", "simulator_icon", "section_view"]
IO_ROLE = ["raw_influent", "settled_influent", "external_waste_in", "effluent", "reclaimed_water_out", "solids_disposal", "biogas_use", "off_gas_out", "chemical_source", "overflow_bypass_out", "external_sidestream", "continuation"]
L1_HINT = ["preliminary", "primary", "secondary", "tertiary", "sludge", "sidestream", "unknown"]
CONNECTION = {"io_terminal": "a point where a stream enters or leaves the drawn system (influent, effluent, sludge to disposal, chemical dosing source, biogas use, continuation to another figure)",
              "junction_split": "a point where one line divides into two or more lines (e.g. clarifier underflow splitting into return and waste sludge)",
              "junction_merge": "a point where two or more lines join into one (e.g. chemical dosing entering a pipe, sidestream returning)",
              "instrument": "a sensor / analyser / controller tag (DO, NH4, pH, FIC ...), usually a circle with letters"}


def load_taxonomy() -> tuple[list[str], str]:
    """-> (allowed class strings incl. L3 forms, class reference text for the prompt)."""
    tx = yaml.safe_load(CLASSES.read_text(encoding="utf-8"))
    allowed, lines = [], []
    for name, c in tx["classes"].items():
        l3 = (c.get("l3") or {})
        req = l3.get("required") or []
        if req:
            allowed += [f"{name}/{x}" for x in req]
            lines.append(f"- {name}/<{'|'.join(req)}> [{c['l1']}]: {c.get('definition', '')} Aliases: {', '.join(map(str, c.get('aliases', [])[:6]))}")
        else:
            allowed.append(name)
            lines.append(f"- {name} [{c['l1']}]: {c.get('definition', '')} Aliases: {', '.join(map(str, c.get('aliases', [])[:6]))}")
    for name, d in CONNECTION.items():
        allowed.append(name); lines.append(f"- {name} [connection]: {d}")
    return allowed, "\n".join(lines)


def system_prompt(class_ref: str) -> str:
    return f"""You extract the process graph of a wastewater treatment plant (WWTP) process flow diagram.

Task: for the given diagram image, list every drawn unit process, tank zone, stream terminal and line junction as a node with a tight pixel bounding box, and list the flow connections between nodes as directed edges. Coordinates are pixels of the image exactly as given to you ([x0, y0, x1, y1], origin top-left, x0 < x1, y0 < y1).

Node classes (choose exactly one per node; use the slash form for classes that require a sub-type):
{class_ref}

Rules (annotation taxonomy v1.1):
1. One node per drawn unit. If the same unit is drawn four times, make four nodes. If only "x4" is written, one node.
2. Do not create nodes for lines, arrowheads, free text, captions, legends, tables, titles or logos. Text is read, not boxed.
3. A tank divided into compartments (anaerobic / anoxic / aerobic): one node per compartment with is_zone=true; if the outer tank is also drawn, add a node for it with class process_unit_generic, l1_hint=secondary, and list it as parent_of its compartments in the "parents" field.
4. A box or shape whose text names only a stage ("Biological Treatment", "Pretreatment", "412") and does not identify the unit: class process_unit_generic with l1_hint and label_text; a drawn unit that is not in the list (heat exchanger, scrubber, post-aeration): unknown_equipment with l1_hint and label_text.
5. Clarifiers: before the biological reactor = primary_clarifier, after it = secondary_clarifier; an underflow return line always means secondary. Membrane receiving mixed liquor with sludge return = mbr_unit; membrane receiving treated water = membrane_unit. Thickener is upstream of the digester, dewatering downstream.
6. Chemical dosing is an edge, not a unit: an io_terminal (io_role=chemical_source) at the arrow start, a junction_merge where it enters, and an edge between them. A drawn chemical tank is storage_tank.
7. Where a line divides or joins, route through a junction node: never draw two edges leaving one unit for one physical split.
8. Edge direction follows the arrowhead (src -> dst). Compartments of one tank are connected in flow order even if no arrow is drawn. Give every edge a medium guess: liquid, mixed_liquor, sludge, solid, gas, air, chemical or signal.
9. visual_form: box = named only by text, symbol = recognisable by shape alone, pictorial = 3-D / icon drawing. confidence: certain (shape), inferred_from_text, inferred_from_context.
10. Only what is drawn. Do not add units you expect but cannot see. If unsure between two classes, pick process_unit_generic with l1_hint.

Return only the JSON object required by the output schema."""


def output_schema(allowed: list[str]) -> dict:
    node = {"type": "object", "additionalProperties": False,
            "properties": {"id": {"type": "string"}, "class": {"type": "string", "enum": allowed},
                           "bbox": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4},
                           "label_text": {"type": ["string", "null"]}, "visual_form": {"type": "string", "enum": VISUAL_FORM},
                           "confidence": {"type": "string", "enum": ["certain", "inferred_from_text", "inferred_from_context"]},
                           "is_zone": {"type": "boolean"}, "l1_hint": {"type": ["string", "null"], "enum": L1_HINT + [None]},
                           "io_role": {"type": ["string", "null"], "enum": IO_ROLE + [None]}},
            "required": ["id", "class", "bbox", "label_text", "visual_form", "confidence", "is_zone", "l1_hint", "io_role"]}
    edge = {"type": "object", "additionalProperties": False,
            "properties": {"src": {"type": "string"}, "dst": {"type": "string"},
                           "medium": {"type": "string", "enum": ["liquid", "mixed_liquor", "sludge", "solid", "gas", "air", "chemical", "signal", "unknown"]},
                           "arrowhead_seen": {"type": "boolean"}},
            "required": ["src", "dst", "medium", "arrowhead_seen"]}
    parent = {"type": "object", "additionalProperties": False, "properties": {"parent": {"type": "string"}, "child": {"type": "string"}}, "required": ["parent", "child"]}
    return {"type": "object", "additionalProperties": False,
            "properties": {"nodes": {"type": "array", "items": node}, "edges": {"type": "array", "items": edge}, "parents": {"type": "array", "items": parent},
                           "diagram_style": {"type": "string", "enum": ["A_box", "B_symbol", "C_pictorial", "D_simulator", "E_page", "hydraulic_profile"]},
                           "language": {"type": "string", "enum": ["en", "ko", "zh", "ja", "other", "mixed"]},
                           "process_configuration": {"type": ["string", "null"]}},
            "required": ["nodes", "edges", "parents", "diagram_style", "language", "process_configuration"]}


def prep_image(p: Path) -> tuple[bytes, int, int, float]:
    """-> (png bytes sent to the model, original W, original H, scale sent/original)."""
    if p.suffix.lower() == ".svg":
        import pymupdf
        doc = pymupdf.open(p); pix = doc[0].get_pixmap(dpi=150)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples); doc.close()
    else:
        im = Image.open(p).convert("RGB")
    W, H = im.size
    s = min(1.0, MAX_SIDE / max(W, H))
    if s < 1.0:
        im = im.resize((round(W * s), round(H * s)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "PNG")
    return buf.getvalue(), W, H, s


def to_graph(key: str, data: dict, W: int, H: int, s: float, allowed: set[str]) -> dict:
    ids, nodes = set(), []
    for n in data["nodes"]:
        nid = n["id"] if n["id"] not in ids else f"{n['id']}_{len(ids)}"
        ids.add(nid)
        x0, y0, x1, y1 = [v / s for v in n["bbox"]]
        x0, x1 = sorted((max(0, x0), min(W, x1))); y0, y1 = sorted((max(0, y0), min(H, y1)))
        cls = n["class"] if n["class"] in allowed else "unknown_equipment"
        nodes.append({"id": nid, "semantic_class": cls, "l2": cls.split("/")[0], "bbox": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)], "score": 1.0,
                      "label_text": n.get("label_text") or "", "visual_form": n["visual_form"], "confidence": n["confidence"],
                      "is_zone": "zone" if n.get("is_zone") else None, "l1_hint": n.get("l1_hint"), "io_role": n.get("io_role"), "parent_id": None})
    by_id = {n["id"]: n for n in nodes}
    for pr in data.get("parents", []):
        if pr["child"] in by_id and pr["parent"] in by_id:
            by_id[pr["child"]]["parent_id"] = pr["parent"]
    edges, seen = [], set()
    for e in data["edges"]:
        if e["src"] in by_id and e["dst"] in by_id and (e["src"], e["dst"]) not in seen and e["src"] != e["dst"]:
            seen.add((e["src"], e["dst"]))
            edges.append({"id": f"e{len(edges) + 1}", "src": e["src"], "dst": e["dst"], "medium": e["medium"], "stream_role": "",
                          "direction_confidence": "arrowhead" if e.get("arrowhead_seen") else "inferred", "line_style": "solid", "optional": False})
    return {"image": key, "nodes": nodes, "edges": edges, "image_attrs": {k: data.get(k) for k in ("diagram_style", "language", "process_configuration")}}


def overlay(p: Path, g: dict, out: Path):
    im = Image.open(p).convert("RGB") if p.suffix.lower() != ".svg" else Image.new("RGB", (1000, 700), "white")
    d = ImageDraw.Draw(im)
    c = {n["id"]: ((n["bbox"][0] + n["bbox"][2]) / 2, (n["bbox"][1] + n["bbox"][3]) / 2) for n in g["nodes"]}
    for e in g["edges"]:
        d.line([c[e["src"]], c[e["dst"]]], fill="#d62728", width=2)
        x, y = c[e["dst"]]; d.ellipse([x - 4, y - 4, x + 4, y + 4], fill="#d62728")
    for n in g["nodes"]:
        x0, y0, x1, y1 = n["bbox"]
        d.rectangle([x0, y0, x1, y1], outline="#1f77b4", width=2)
        d.text((x0 + 2, max(0, y0 - 11)), n["semantic_class"], fill="#1f77b4")
    im.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", default=str(ROOT / "data" / "pilot" / "images"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--keys", default="", help="comma-separated substrings to select images (e.g. pilot_01,pilot_21)")
    ap.add_argument("--overlay", action="store_true", help="also write <out>/overlays/<key>.png for eyeballing")
    ap.add_argument("--dry-run", action="store_true", help="build prompts and prepared images only, no API call")
    ap.add_argument("--max-tokens", type=int, default=16000)
    a = ap.parse_args()
    out = Path(a.out); (out / "graphs").mkdir(parents=True, exist_ok=True); (out / "_raw").mkdir(exist_ok=True)
    if a.overlay:
        (out / "overlays").mkdir(exist_ok=True)
    allowed, class_ref = load_taxonomy()
    system = system_prompt(class_ref); schema = output_schema(allowed)
    files = sorted(p for p in Path(a.images).iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".tif", ".tiff", ".bmp"))
    if a.keys:
        files = [p for p in files if any(k in p.name for k in a.keys.split(","))]
    if a.limit:
        files = files[:a.limit]
    (out / "_run.json").write_text(json.dumps({"date": str(date.today()), "model": a.model, "effort": a.effort, "n_images": len(files), "system_prompt": system, "schema": schema}, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        png, W, H, s = prep_image(files[0])
        print(f"dry run: {len(files)} images, system prompt {len(system)} chars, {len(allowed)} classes; first image {W}x{H} sent at scale {s:.3f} ({len(png) // 1024} KB)")
        return
    import anthropic
    client = anthropic.Anthropic()
    rows, done = [], {p.stem for p in (out / "graphs").glob("*.graph.json")}
    for p in files:
        key = p.name
        if Path(key).stem in done:
            continue  # resume
        png, W, H, s = prep_image(p)
        t0 = time.time()
        try:
            r = client.beta.messages.create(
                model=a.model, max_tokens=a.max_tokens,
                betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                output_config={"effort": a.effort, "format": {"type": "json_schema", "schema": schema}},
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.standard_b64encode(png).decode()}},
                    {"type": "text", "text": f"Image size: {round(W * s)} x {round(H * s)} pixels (width x height). Extract the process graph."}]}])
        except anthropic.APIStatusError as e:
            print(f"{key}: API error {e.status_code} {e.message[:120]}"); rows.append({"image": key, "status": f"error {e.status_code}"}); continue
        except anthropic.APIConnectionError as e:
            print(f"{key}: connection error {e}"); rows.append({"image": key, "status": "connection error"}); continue
        dt = time.time() - t0
        u = r.usage
        (out / "_raw" / f"{Path(key).stem}.json").write_text(r.to_json(), encoding="utf-8")
        if r.stop_reason == "refusal":
            cat = getattr(getattr(r, "stop_details", None), "category", None)
            print(f"{key}: refused ({cat})"); rows.append({"image": key, "status": f"refusal:{cat}", "model_served": r.model}); continue
        text = next((b.text for b in r.content if b.type == "text"), "")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print(f"{key}: invalid JSON (stop_reason {r.stop_reason})"); rows.append({"image": key, "status": f"bad json ({r.stop_reason})"}); continue
        g = to_graph(key, data, W, H, s, set(allowed))
        (out / "graphs" / f"{Path(key).stem}.graph.json").write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
        if a.overlay:
            overlay(p, g, out / "overlays" / f"{Path(key).stem}.png")
        pi, po = PRICE.get(a.model, (0, 0))
        cost = (u.input_tokens * pi + (u.cache_creation_input_tokens or 0) * pi * 1.25 + (u.cache_read_input_tokens or 0) * pi * 0.1 + u.output_tokens * po) / 1e6
        rows.append({"image": key, "status": "ok", "model_served": r.model, "nodes": len(g["nodes"]), "edges": len(g["edges"]), "seconds": round(dt, 1),
                     "input_tokens": u.input_tokens, "cache_read": u.cache_read_input_tokens or 0, "output_tokens": u.output_tokens, "usd": round(cost, 4)})
        print(f"{key}: {len(g['nodes'])} nodes, {len(g['edges'])} edges, {dt:.0f}s, ${cost:.3f}")
    if rows:
        fields = sorted({k for r in rows for k in r}, key=lambda k: ["image", "status", "model_served", "nodes", "edges", "seconds", "input_tokens", "cache_read", "output_tokens", "usd"].index(k) if k in ["image", "status", "model_served", "nodes", "edges", "seconds", "input_tokens", "cache_read", "output_tokens", "usd"] else 99)
        new = not (out / "_summary.csv").exists()
        with open(out / "_summary.csv", "a", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields); (w.writeheader() if new else None); w.writerows(rows)
        ok = [r for r in rows if r["status"] == "ok"]
        print(f"done: {len(ok)}/{len(rows)} ok, total ${sum(r['usd'] for r in ok):.2f}")


if __name__ == "__main__":
    main()
