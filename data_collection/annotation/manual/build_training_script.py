"""
build_training_script.py — docs/annotation_training_script.md -> Word (simple Markdown subset:
#/##/### headings, '-' bullets, '1.' numbered lines, **bold**, `code`, '---' rules, plain paragraphs).
Output: annotation/manual/WWTP_training_script.docx (PDF via Word COM).
"""
from __future__ import annotations

import re
from pathlib import Path

from docx.shared import Pt

from build_manual import Doc, HERE, ACCENT, GREY

SRC = HERE.parents[1] / "docs" / "annotation_training_script.md"
OUT = HERE / "WWTP_training_script.docx"


def build():
    D = Doc()
    lines = SRC.read_text(encoding="utf-8").splitlines()
    first = True
    for ln in lines:
        s = ln.rstrip()
        if not s:
            continue
        if s.startswith("# "):
            D.p(s[2:], 20, True, ACCENT, "center"); first = False
        elif s.startswith("## "):
            D.h(s[3:], 1)
        elif s.startswith("### "):
            D.h(s[4:], 2)
        elif s == "---":
            continue
        elif re.match(r"^\s*- ", s):
            level = 1 if s.startswith("  ") else 0
            D.bullet(re.sub(r"^\s*- ", "", s), level)
        elif re.match(r"^\d+\. ", s):
            D.num(re.sub(r"^\d+\. ", "", s))
        elif s.startswith("**") and s.endswith("**") and s.count("**") == 2:
            D.p(s.strip("*"), 10.5, True)
        elif first:
            D.p(s, 10, color=GREY, align="center")
        else:
            D.p(s)
    D.d.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build()
