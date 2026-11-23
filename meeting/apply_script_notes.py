"""
apply_script_notes.py — copy the v2 deck to v3 and replace each slide's speaker notes with the
spoken script + expected Q&A from meeting/script_v2.md (sections "## Sxx." / "### Sxx.").
Slides themselves are not touched.

usage: python -I -X utf8 meeting/apply_script_notes.py [src.pptx] [script.md] [dst.pptx]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "meeting" / "WWTP_vision_meeting_v2.pptx"
MD = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "meeting" / "script_v2.md"
DST = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "meeting" / "WWTP_vision_meeting_v3.pptx"

HEAD = re.compile(r"^#{2,3} S(\d{2})\.\s*(.*)$")


def parse(md: str) -> dict[int, str]:
    """slide number -> notes text (markdown markers stripped)"""
    sections: dict[int, list[str]] = {}
    cur = None
    for line in md.splitlines():
        m = HEAD.match(line)
        if m:
            cur = int(m.group(1))
            sections[cur] = [m.group(2).strip()]
            continue
        if line.startswith("## ") or line.startswith("# "):   # 부록 / 시간 배분 headings end a section
            cur = None
            continue
        if cur is not None:
            sections[cur].append(line)
    out = {}
    for n, lines in sections.items():
        title, body = lines[0], lines[1:]
        text = "\n".join(body).strip()
        text = text.replace("**", "")
        text = re.sub(r"^> ?", "", text, flags=re.M)          # block quotes
        text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", text)  # *(동작)* -> (동작)
        text = re.sub(r"^---\s*$", "", text, flags=re.M)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        out[n] = f"{title}\n\n{text}"
    return out


def main():
    notes = parse(MD.read_text(encoding="utf-8"))
    prs = Presentation(str(SRC))
    missing = []
    for i, slide in enumerate(prs.slides, 1):
        if i not in notes:
            missing.append(i)
            continue
        tf = slide.notes_slide.notes_text_frame
        tf.text = notes[i]
    prs.save(str(DST))
    print(f"saved {DST.name}: {len(prs.slides)} slides, notes set for {len(prs.slides) - len(missing)}, missing {missing}")


if __name__ == "__main__":
    main()
