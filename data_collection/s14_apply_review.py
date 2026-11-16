"""
s14_apply_review.py — apply human decisions exported from a review gallery (data/review/*.html) to triage_final.csv.

The gallery's "Export decisions CSV" button writes decisions_<gallery>.csv with columns record_id,decision
(decision in keep / reject / unsure). This script:
  keep   -> decision=keep,   split=main
  reject -> decision=reject, split=excluded
  unsure -> left as is (still manual_review)
and records who decided (reviewer=human) and when. Rows not in the CSV are untouched.

Usage: python s14_apply_review.py <path to decisions_manual_review.csv>
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd

from common import DATA


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: python s14_apply_review.py <decisions_*.csv>")
    src = Path(sys.argv[1])
    dec = pd.read_csv(src, dtype=str).fillna("")
    dec["decision"] = dec["decision"].str.strip().str.lower()
    dec = dec[dec["decision"].isin(["keep", "reject", "unsure"])].drop_duplicates("record_id", keep="last")

    tf = DATA / "triage_final.csv"
    df = pd.read_csv(tf, dtype=str).fillna("")
    for col in ("reviewer", "reviewed_at"):
        if col not in df.columns:
            df[col] = ""
    m = df["record_id"].isin(dec["record_id"])
    lut = dec.set_index("record_id")["decision"]
    now = dt.datetime.now().isoformat(timespec="minutes")
    n_keep = n_rej = n_uns = 0
    for i in df.index[m]:
        d = lut[df.at[i, "record_id"]]
        if d == "keep":
            df.at[i, "decision"], df.at[i, "split"] = "keep", "main"; n_keep += 1
        elif d == "reject":
            df.at[i, "decision"], df.at[i, "split"] = "reject", "excluded"; n_rej += 1
        else:
            n_uns += 1
        df.at[i, "reviewer"], df.at[i, "reviewed_at"] = "human", now
    df.to_csv(tf, index=False, encoding="utf-8-sig")
    print(f"applied {len(dec)} decisions: keep {n_keep} -> main, reject {n_rej} -> excluded, unsure {n_uns} unchanged")
    print("split counts now:"); print(df["split"].value_counts().to_string())


if __name__ == "__main__":
    main()
