"""
make_algorithm_v4.py — pseudo-code tables written for readability (v4).

What changed and why
  * No right-aligned grey "▷ comment" column. That convention comes from the LaTeX `algorithmic` package; in a Word
    table it reads as clutter. Every explanation is now part of the step sentence itself.
  * Layout follows the familiar "Algorithm 1" table used in process-engineering papers: Input / Output /
    Initialization, then numbered steps with a bold step name and one plain sentence, For/End for, Return.
  * One idea per line, no nested loops deeper than one level, no function names in code font, no symbols that need
    a legend (τ and p* are the only symbols, both defined in Input).
  * Run results are shown once, in a short "Result" row under the table, not inside the steps.
Outputs: paper/Algorithms_v4.docx, paper/algorithms_v4.md
Usage  : python make_algorithm_v4.py
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

HERE = Path(__file__).resolve().parent
FONT = "Times New Roman"
B, N, I = "b", "n", "i"   # run styles

# (indent level, [(style, text), ...])
ALG1 = {
    "caption": "Table X. Pseudo-code of the collection and screening procedure for treatment-plant process diagrams.",
    "rows": [
        (0, [(B, "Algorithm 1: Collection and screening of treatment-plant process diagrams")]),
        (0, [(B, "Input: "), (N, "document sources (open-access journals, agency design manuals, plant-operator web pages, Wikimedia Commons, patents); search terms; caption screening rule (Algorithm 2); duplicate threshold "), (I, "τ"), (N, " = 6 bits; visual screening criteria; target precision "), (I, "p"), (N, "* = 0.90")]),
        (0, [(B, "Output: "), (N, "main benchmark of process-diagram images, each with a provenance record; auxiliary, crop-pending, manual-review and excluded subsets")]),
        (0, [(B, "Initialization: "), (N, "empty image set and empty provenance table; identifying User-Agent and fixed request rate for every source")]),
        (0, [(B, "For each "), (N, "document source "), (B, "do")]),
        (1, [(B, "1.  Search: "), (N, "query the source's official index or API with the search terms to obtain candidate documents.")]),
        (1, [(B, "2.  Retrieval: "), (N, "for each candidate document, download its metadata and figures (article XML with image files, PDF pages, web images or patent drawing sheets).")]),
        (1, [(B, "3.  Caption screening: "), (N, "keep a figure only if its caption passes Algorithm 2 (tier T1 or T2). Figures without captions (patents, web images, scanned pages) are kept for visual screening.")]),
        (1, [(B, "4.  Provenance record: "), (N, "store source, document identifiers, file and landing URLs, rights holder, caption, screening rule, licence tier (A = redistributable, B = research use only), SHA-256 and perceptual hash.")]),
        (0, [(B, "End for")]),
        (1, [(B, "5.  Duplicate removal: "), (N, "merge files with the same SHA-256 and near-identical copies whose perceptual-hash distance is ≤ "), (I, "τ"), (N, "; keep the redistributable copy.")]),
        (1, [(B, "6.  Visual screening: "), (N, "present the unique images on 20-image contact sheets and assign a decision (keep, unsure, reject) and a category (wwtp, sludge, wtp, pilot, other).")]),
        (1, [(B, "7.  Quality check: "), (N, "audit random samples of keep and reject decisions. "), (B, "If "), (N, "precision < "), (I, "p"), (N, "*, "), (B, "then "), (N, "revise the criteria and repeat step 6 "), (B, "End if")]),
        (1, [(B, "8.  Subset assignment: "), (N, "keep → main benchmark; unsure → auxiliary (unit-level, pictorial, other-domain), crop-pending or manual-review by reason; reject → excluded.")]),
        (1, [(B, "9.  Cropping: "), (N, "crop multi-panel figures and page scans by hand; each crop inherits its parent record and joins the main benchmark.")]),
        (0, [(B, "Return: "), (N, "main benchmark and subsets with provenance records")]),
    ],
    "result": "Result of the run on 16 November 2026: 56,617 figures inspected → 3,300 files with provenance → 3,114 unique images → keep 952 (747 redistributable), unsure 632, reject 1,530; after manual cropping (35 crops) and human review of the undecided images: main 993 (776 redistributable), auxiliary 403, manual review 33, excluded 1,621.",
}
ALG2 = {
    "caption": "Table Y. Pseudo-code of the caption screening rule.",
    "rows": [
        (0, [(B, "Algorithm 2: Caption screening rule")]),
        (0, [(B, "Input: "), (N, "figure caption; four word lists — diagram words (flow diagram, flowsheet, flowchart, process flow, schematic, layout, configuration, treatment train, block diagram), of which the strong diagram words are flow diagram, flowsheet, flowchart, process flow, block diagram, treatment train, process scheme and plant layout; exclusion words (sampling site, map, photograph, aerial, microscopy, chromatogram, spectrum, heat map, Venn, microbial community, graphical abstract); plant words (wastewater or sewage treatment plant, WWTP, STP, WRRF, treatment works, treatment line, full-scale plant); treatment words (treatment, sludge, clarifier, digester, aeration, activated sludge, MBR, SBR)")]),
        (0, [(B, "Output: "), (N, "tier T1 (whole-plant diagram), T2 (treatment-related schematic) or none (not downloaded)")]),
        (0, [(B, "Initialization: "), (N, "convert the caption to lower case and collapse repeated spaces")]),
        (1, [(B, "1.  Diagram test: "), (B, "If "), (N, "the caption contains no diagram word, "), (B, "then "), (N, "return none "), (B, "End if")]),
        (1, [(B, "2.  Exclusion test: "), (B, "If "), (N, "the caption contains an exclusion word and no strong diagram word, "), (B, "then "), (N, "return none "), (B, "End if")]),
        (1, [(B, "3.  Plant test: "), (B, "If "), (N, "the caption contains a plant word, "), (B, "then "), (N, "return T1 "), (B, "End if")]),
        (1, [(B, "4.  Treatment test: "), (B, "If "), (N, "the caption contains a treatment word, "), (B, "then "), (N, "return T2 "), (B, "End if")]),
        (0, [(B, "Return: "), (N, "none")]),
    ],
    "result": "Precision measured after visual screening: T1 0.55 (429 figures), T2 0.23 (972 figures). The exclusion test was added after a first pass let captions such as “map of the study area … wastewater treatment plant” through as T1.",
}


def set_borders(cell, top, bottom):
    tcPr = cell._tc.get_or_add_tcPr(); b = OxmlElement("w:tcBorders")
    for name, on in (("top", top), ("left", False), ("bottom", bottom), ("right", False)):
        el = OxmlElement(f"w:{name}"); el.set(qn("w:val"), "single" if on else "nil"); el.set(qn("w:sz"), "8"); el.set(qn("w:color"), "000000"); b.append(el)
    tcPr.append(b)


def add_runs(p, runs, size=10):
    for style, text in runs:
        r = p.add_run(text); r.font.name = FONT; r.font.size = Pt(size)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        r.bold = style == B; r.italic = style == I


def table(doc, a):
    cap = doc.add_paragraph(); add_runs(cap, [(B, a["caption"])], size=10); cap.paragraph_format.space_after = Pt(3)
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.cell(0, 0); cell.width = Cm(16); set_borders(cell, True, True)
    for i, (lvl, runs) in enumerate(a["rows"]):
        p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        pf = p.paragraph_format; pf.left_indent = Cm(0.6 * lvl); pf.space_after = Pt(1.5); pf.space_before = Pt(0)
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
        if lvl == 1:
            pf.first_line_indent = Cm(-0.0)
        add_runs(p, runs)
    res = doc.add_paragraph(); res.paragraph_format.space_before = Pt(2)
    add_runs(res, [(I, a["result"])], size=9)
    doc.add_paragraph()


def to_md(a):
    out = [f"**{a['caption']}**", "", "```"]
    for lvl, runs in a["rows"]:
        out.append("    " * lvl + "".join(t for _, t in runs))
    out += ["```", "", f"*{a['result']}*", ""]
    return "\n".join(out)


def main():
    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.5)
    st = doc.styles["Normal"]; st.font.name = FONT; st.font.size = Pt(10); st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    table(doc, ALG1); table(doc, ALG2)
    doc.save(HERE / "Algorithms_v4.docx")
    (HERE / "algorithms_v4.md").write_text(to_md(ALG1) + "\n" + to_md(ALG2), encoding="utf-8")
    print("saved", HERE / "Algorithms_v4.docx")


if __name__ == "__main__":
    main()
