"""
s13_apply_crops.py — apply the boxes exported by the crop tool (crops.json) and promote the crops to the main split.

  * reads data/review/crops.json  {record_id: [[x0,y0,x1,y1], ...]}  (original pixel coordinates)
  * writes data/raw/crops/<record>_cropN.png
  * appends provenance records to data/provenance/crops.jsonl (source "<orig source>", acquisition_method
    "manual crop of <parent record_id>", all other fields inherited from the parent)
  * appends the new rows to data/triage_final.csv with decision=keep, split=main, note="crop of <parent>"

Usage: python s13_apply_crops.py [--json data/review/crops.json]
"""
from __future__ import annotations

import argparse
import json

import pandas as pd
from PIL import Image

from common import DATA, ROOT, RAW, PROV, provenance_record, append_jsonl, read_jsonl, safe_name

OUT = RAW / "crops"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=str(DATA / "review" / "crops.json"))
    args = ap.parse_args()
    boxes = json.load(open(args.json, encoding="utf-8"))
    df = pd.read_csv(DATA / "triage_final.csv", dtype=str).fillna("")
    by_id = df.set_index("record_id")
    prov_by_id = {}
    for f in PROV.glob("*.jsonl"):
        for r in read_jsonl(f):
            prov_by_id[r["record_id"]] = r
    OUT.mkdir(parents=True, exist_ok=True)
    new_rows, n = [], 0
    for rid, bl in boxes.items():
        if rid not in by_id.index or not bl:
            continue
        r = by_id.loc[rid]
        parent = prov_by_id.get(rid, {})
        src = ROOT / r["image_path"]
        try:
            im = Image.open(src).convert("RGB")
        except Exception:
            continue
        for k, (x0, y0, x1, y1) in enumerate(bl):
            # short readable stem + hash of the full record_id: long URLs would otherwise be truncated to the
            # same 120-char stem and crops from different pages would overwrite each other
            import hashlib
            stem = safe_name(rid.replace(':', '_'))[:60] + "_" + hashlib.sha1(rid.encode()).hexdigest()[:8]
            dest = OUT / f"{stem}_crop{k}.png"
            im.crop((x0, y0, x1, y1)).save(dest)
            rec = provenance_record(
                source=r["source"], tier=r["tier"], image_path=dest,
                acquisition_method=f"manual crop of {rid} (box {x0},{y0},{x1},{y1}); parent: {parent.get('acquisition_method', '')}",
                file_url=r["file_url"], landing_url=r["landing_url"], license=r["license"],
                license_url=parent.get("license_url"), rights_holder=r["rights_holder"], doc_id=r["doc_id"],
                title=r["title"], venue=r["venue"], year=r["year"] or None, figure_label=r["figure_label"],
                caption=r["caption"], query=r["query"], filter_rule="manual crop", extra={"parent": rid, "box": [x0, y0, x1, y1]})
            rec["record_id"] = f"{rid}#crop{k}"
            append_jsonl(PROV / "crops.jsonl", rec)
            row = r.to_dict(); row.update({"record_id": rec["record_id"], "image_path": rec["image_path"], "sha256": rec["sha256"],
                                           "phash": rec["phash"] or "", "decision": "keep", "split": "main",
                                           "note": f"crop of {rid}", "duplicate_of": "", "canonical": "True"})
            new_rows.append(row); n += 1
    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        df.to_csv(DATA / "triage_final.csv", index=False, encoding="utf-8-sig")
    print(f"{n} crops written to {OUT}; triage_final.csv now has {len(df)} rows")


if __name__ == "__main__":
    main()
