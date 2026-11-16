# one-off: manual triage decisions for the re-rendered transparent/SVG images (alpha_000..006 sheets), 2026-11-16
import csv
import json

from common import DATA

m = json.load(open(DATA / "review/sheets/alpha_sheets.json", encoding="utf-8"))
U, K, R = "unsure", "keep", "reject"
D = {
    "alpha_000.jpg": {0: (U, "wwtp", "dark render; boxes of treatment units"), 1: (U, "", "render issue"), 2: (U, "other", "pond section single unit"), 3: (U, "", "no render"), 4: (K, "wwtp", ""), 5: (U, "", "render issue"), 6: (K, "wwtp", ""), 7: (U, "other", "ZLD block overview"), 8: (K, "wwtp", "A/B stage"), 9: (K, "wwtp", "two trains"), 10: (K, "wwtp", "tank+clarifier"), 11: (U, "wwtp", "cross-section two units"), 12: (U, "", "no render"), 13: (K, "wwtp", "tank+clarifier"), 14: (R, "", ""), 15: (U, "other", "CW section"), 16: (U, "", "no render"), 17: (R, "", "map"), 18: (U, "wwtp", "trickling filter single unit"), 19: (U, "", "no render")},
    "alpha_001.jpg": {0: (U, "sludge", "drying bed single unit"), 1: (U, "", "no render"), 2: (R, "", ""), 3: (U, "", "no render"), 4: (K, "wwtp", ""), 5: (R, "", "photo"), 6: (R, "", "photo"), 7: (K, "wwtp", "ozone train"), 8: (R, "", "aerial photo"), 9: (R, "", "SFD sankey"), 10: (R, "", "photo"), 11: (R, "", "photo"), 12: (R, "", "photo"), 13: (R, "", "photo"), 14: (K, "wwtp", "tank+clarifier"), 15: (K, "wwtp", "tank+clarifier"), 16: (U, "other", "pond section"), 17: (U, "", "no render"), 18: (U, "other", "CW section"), 19: (U, "", "no render")},
    "alpha_002.jpg": {0: (U, "other", "CW section"), 1: (U, "", "no render"), 2: (U, "", "no render"), 3: (R, "", "silhouette"), 4: (U, "other", "biodiesel"), 5: (U, "other", "BtL"), 6: (U, "other", "distillation"), 7: (U, "other", "distillation"), 8: (U, "other", "ethylene oxide"), 9: (U, "other", "lead alkyl"), 10: (U, "other", "biodiesel"), 11: (U, "other", "gas processing"), 12: (U, "other", "GTL blocks"), 13: (R, "", "boiler drawing"), 14: (U, "other", "ammonia loop"), 15: (U, "other", "power plant"), 16: (U, "other", "power plant"), 17: (U, "other", "iron ore"), 18: (U, "other", "sorting"), 19: (U, "other", "gas flowchart")},
    "alpha_003.jpg": {0: (R, "", "manufacturing pictorial"), 1: (U, "other", "blast furnace gas"), 2: (U, "other", "flowchart"), 3: (U, "other", "CW section"), 4: (U, "wwtp", "pond sections in series, no lines"), 5: (U, "", "no render"), 6: (U, "other", ""), 7: (U, "other", "generic boxes"), 8: (U, "other", "gas processing"), 9: (U, "other", "gas processing"), 10: (U, "other", "oil field"), 11: (U, "other", "nitric acid"), 12: (R, "", "manufacturing"), 13: (U, "other", "metallurgy flowchart"), 14: (U, "other", "refinery"), 15: (U, "other", "refinery"), 16: (U, "other", "KCl"), 17: (U, "other", "coffee"), 18: (U, "other", "refinery"), 19: (U, "other", "refinery")},
    "alpha_004.jpg": {0: (U, "other", "distillation"), 1: (U, "other", "powder coating"), 2: (U, "other", "distillation"), 3: (U, "other", "salt"), 4: (U, "other", "salt"), 5: (R, "", "infographic"), 6: (R, "", "photo"), 7: (U, "wtp", "3D pictorial"), 8: (U, "wtp", "3D pictorial"), 9: (R, "", "photo"), 10: (R, "", "photo"), 11: (R, "", "ad photo"), 12: (R, "", "ad photo"), 13: (U, "", "render issue"), 14: (R, "", ""), 15: (R, "", "manufacturing flowchart"), 16: (R, "", "membrane cartoon"), 17: (U, "other", "desalination MED"), 18: (R, "", "single filter"), 19: (R, "", "photo")},
    "alpha_005.jpg": {0: (U, "other", "ABR pictorial"), 1: (U, "other", "wetland pictorial"), 2: (U, "other", "reedbed 3D"), 3: (U, "other", "reedbed 3D"), 4: (U, "other", "reedbed 3D"), 5: (U, "other", "ABR pictorial"), 6: (R, "", "map"), 7: (R, "", "mechanism"), 8: (K, "wwtp", "unit train A to H"), 9: (R, "", "screenshot"), 10: (R, "", "map"), 11: (K, "wwtp", "Korean process flow"), 12: (R, "", "photo sequence"), 13: (U, "other", "HTL blocks"), 14: (U, "other", "dark render"), 15: (U, "other", "dark render"), 16: (U, "", "render issue"), 17: (K, "wwtp", "block"), 18: (K, "wwtp", "block"), 19: (K, "wwtp", "block")},
    "alpha_006.jpg": {0: (K, "wwtp", "block"), 1: (K, "wwtp", "block"), 2: (U, "", "no render"), 3: (R, "", "logo"), 4: (R, "", "logo"), 5: (R, "", "control icons"), 6: (K, "wwtp", "pictorial section train"), 7: (K, "wwtp", "pictorial section train"), 8: (R, "", "icons"), 9: (K, "wwtp", ""), 10: (R, "", "shapes"), 11: (K, "wwtp", "SBR dark render"), 12: (R, "", "taxonomy")},
}
out = DATA / "review/decisions/zz_alpha_manual.csv"
n = 0
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["sheet", "idx", "record_id", "decision", "category", "note"])
    for sheet, dec in D.items():
        ids = m[sheet]["record_ids"]
        for i, (d, c, note) in dec.items():
            if i < len(ids):
                w.writerow([sheet, i, ids[i], d, c, note])
                n += 1
print("rows", n)
