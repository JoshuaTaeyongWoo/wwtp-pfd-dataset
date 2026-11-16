"""
s12_crop_tool.py — build a local HTML tool to draw crop boxes on the `crop_pending` images (and any other split).

Open data/review/crop_tool.html in a browser. For each image: drag on the picture to draw one or more boxes
(a box = one diagram to extract). Keys: Backspace removes the last box, "n"/"p" next/previous image.
Boxes are stored in localStorage and exported with the button as data/review/crops.json
(record_id -> [[x0,y0,x1,y1], ...] in ORIGINAL pixel coordinates). Then run s13_apply_crops.py.

Usage: python s12_crop_tool.py [--split crop_pending]
"""
from __future__ import annotations

import argparse
import json

import pandas as pd

from common import DATA, ROOT, image_size

PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><title>Crop tool</title>
<style>
body{font-family:sans-serif;margin:0;background:#222;color:#eee}
#bar{padding:8px;background:#333;position:sticky;top:0;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
#wrap{position:relative;display:inline-block;margin:10px}
#img{max-width:95vw;max-height:85vh;display:block}
#cv{position:absolute;left:0;top:0;cursor:crosshair}
button{font-size:13px} .small{font-size:11px;color:#bbb}
</style></head><body>
<div id="bar"><button onclick="prev()">◀ prev (p)</button><button onclick="next()">next (n) ▶</button>
<span id="pos"></span><span id="cap" class="small"></span>
<button onclick="undo()">undo box (Backspace)</button><button onclick="exportJson()">Export crops.json</button>
<span id="cnt" class="small"></span></div>
<div id="wrap"><img id="img"><canvas id="cv"></canvas></div>
<script>
const ITEMS=__ITEMS__; let i=0; const key='crops_v1';
let boxes=JSON.parse(localStorage.getItem(key)||'{}');
const img=document.getElementById('img'),cv=document.getElementById('cv'),ctx=cv.getContext('2d');
function load(){const it=ITEMS[i];img.src=it.uri;img.onload=()=>{cv.width=img.clientWidth;cv.height=img.clientHeight;draw();};
 document.getElementById('pos').textContent=`${i+1}/${ITEMS.length}  ${it.rid}`;document.getElementById('cap').textContent=it.cap;count();}
function scale(){return img.naturalWidth/img.clientWidth;}
function draw(){ctx.clearRect(0,0,cv.width,cv.height);const s=scale();for(const b of (boxes[ITEMS[i].rid]||[])){ctx.strokeStyle='#ff3';ctx.lineWidth=2;ctx.strokeRect(b[0]/s,b[1]/s,(b[2]-b[0])/s,(b[3]-b[1])/s);}
 if(cur){ctx.strokeStyle='#0f0';ctx.strokeRect(cur[0],cur[1],cur[2]-cur[0],cur[3]-cur[1]);}}
let cur=null,start=null;
cv.onmousedown=e=>{start=[e.offsetX,e.offsetY];cur=[...start,...start];};
cv.onmousemove=e=>{if(!start)return;cur=[Math.min(start[0],e.offsetX),Math.min(start[1],e.offsetY),Math.max(start[0],e.offsetX),Math.max(start[1],e.offsetY)];draw();};
cv.onmouseup=e=>{if(!start)return;const s=scale();const b=cur.map(v=>Math.round(v*s));if(b[2]-b[0]>20&&b[3]-b[1]>20){(boxes[ITEMS[i].rid]=boxes[ITEMS[i].rid]||[]).push(b);save();}start=null;cur=null;draw();count();};
function save(){localStorage.setItem(key,JSON.stringify(boxes));}
function undo(){const a=boxes[ITEMS[i].rid]||[];a.pop();save();draw();count();}
function next(){i=Math.min(i+1,ITEMS.length-1);load();} function prev(){i=Math.max(i-1,0);load();}
function count(){const n=Object.values(boxes).reduce((a,b)=>a+b.length,0);document.getElementById('cnt').textContent=` boxes: ${n} on ${Object.keys(boxes).filter(k=>boxes[k].length).length} images`;}
function exportJson(){const a=document.createElement('a');a.href='data:application/json;charset=utf-8,'+encodeURIComponent(JSON.stringify(boxes,null,1));a.download='crops.json';a.click();}
document.onkeydown=e=>{if(e.key==='n')next();else if(e.key==='p')prev();else if(e.key==='Backspace'){e.preventDefault();undo();}};
load();
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="crop_pending")
    ap.add_argument("--ids", default="", help="CSV with a record_id column: build the tool for exactly these rows instead of a split")
    ap.add_argument("--out", default="crop_tool.html", help="output file name under data/review/")
    args = ap.parse_args()
    df = pd.read_csv(DATA / "triage_final.csv", dtype=str, encoding="utf-8-sig").fillna("")
    if args.ids:
        ids = pd.read_csv(args.ids, dtype=str, encoding="utf-8-sig")["record_id"].tolist()
        sub = df[df["record_id"].isin(ids)]
    else:
        sub = df[df["split"] == args.split]
    items = []
    for _, r in sub.iterrows():
        p = ROOT / r["image_path"]
        if p.suffix.lower() == ".svg" or not image_size(p):
            continue
        items.append({"rid": r["record_id"], "uri": p.resolve().as_uri(), "cap": (r["note"] + " | " + (r["caption"] or r["title"]))[:200]})
    out = DATA / "review" / args.out
    out.write_text(PAGE.replace("__ITEMS__", json.dumps(items, ensure_ascii=False)), encoding="utf-8")
    print(len(items), "images ->", out)


if __name__ == "__main__":
    main()
