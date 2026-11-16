"""
make_algorithm_docx.py — pseudo-code tables for the manuscript in the "Table 4 / Algorithm 1" style
(single-column Word table, bold step names, indented sub-lines, Input / Output / Initialization / For … do /
End for / Return), Times New Roman 10 pt.

Output: paper/Table_Algorithms.docx  (Algorithm 1: harvesting + triage pipeline; Algorithm 2: CaptionTier rule)
Usage : python make_algorithm_docx.py
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
OUT = HERE / "Table_Algorithms.docx"
FONT = "Times New Roman"


def set_cell_borders(cell, top=True, bottom=True, left=False, right=False, sz=8):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for name, on in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{name}")
        el.set(qn("w:val"), "single" if on else "nil")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tcPr.append(borders)


def para(cell, runs, indent_cm=0.0, space_after=0, first=False):
    """runs: list of (text, bold, italic)"""
    p = cell.paragraphs[0] if first else cell.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(indent_cm)
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    for text, bold, italic in runs:
        r = p.add_run(text)
        r.bold, r.italic = bold, italic
        r.font.name = FONT
        r.font.size = Pt(10)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    return p


def B(t): return (t, True, False)
def I(t): return (t, False, True)
def N(t): return (t, False, False)


def algorithm_table(doc, caption, rows):
    """rows: list of (indent_level, [runs])"""
    cap = doc.add_paragraph()
    r = cap.add_run(caption)
    r.font.name = FONT; r.font.size = Pt(10); r.bold = True
    cap.paragraph_format.space_after = Pt(2)
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.cell(0, 0)
    cell.width = Cm(15.5)
    set_cell_borders(cell, top=True, bottom=True)
    first = True
    for lvl, runs in rows:
        para(cell, runs, indent_cm=0.5 * lvl, first=first)
        first = False
    doc.add_paragraph()


def main():
    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.5)
    st = doc.styles["Normal"]
    st.font.name = FONT; st.font.size = Pt(10)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    # ------------------------------------------------------------------ Algorithm 1
    rows1 = [
        (0, [B("Algorithm 1: Provenance-tracked harvesting and triage of process diagrams")]),
        (0, [B("Input: "), N("source set "), I("S"), N(" = {open-access literature, public agency documents, operator web pages, Wikimedia Commons, patents}; query sets "), I("Q"), I("s"), N("; caption rule "), N("CaptionTier"), N(" (Algorithm 2); licence map "), I("L"), N(" → {A, B}; pHash threshold "), I("τ"), N(" = 6; triage criteria "), I("C")]),
        (0, [B("Output: "), N("canonical image set "), I("K"), N(", provenance table "), I("P"), N(", decision "), I("y"), N("("), I("x"), N(") and split "), I("z"), N("("), I("x"), N(") for every image")]),
        (0, [B("Initialization: "), I("D"), N(" ← ∅ (downloaded files), "), I("P"), N(" ← ∅; rate limits and an identifying User-Agent for every source")]),
        (0, [B("For each "), N("source "), I("s"), N(" ∈ "), I("S"), B(" do")]),
        (1, [B("1.  Discovery:")]),
        (2, [N("Query the source's official index with "), I("Q"), I("s"), N(" → candidate documents "), I("U"), I("s"), N(" (PMCIDs, DOIs, file titles, patent numbers, page URLs)")]),
        (1, [B("2.  Acquisition:")]),
        (2, [N("For each "), I("u"), N(" ∈ "), I("U"), I("s"), N(": fetch metadata (identifier, title, venue, year, licence, authors) and the figure container "), N("(JATS XML + figure files from the PMC-OA bucket; PDF; HTML <img>; drawing sheets)")]),
        (1, [B("3.  Figure extraction:")]),
        (2, [B("If "), N("captions are available (JATS XML, PDF text layer), "), B("then")]),
        (3, [N("For each figure "), I("f"), N(" with caption "), I("c"), N(": "), I("t"), N(" ← CaptionTier("), I("c"), N("); download "), I("f"), N(" only if "), I("t"), N(" ∈ {T1, T2}")]),
        (2, [B("Else")]),
        (3, [N("Download every drawing sheet (patents), keyword-matched image (web pages) or caption-matched page render (scanned documents)")]),
        (2, [B("End if")]),
        (1, [B("4.  Provenance record:")]),
        (2, [N("For each downloaded "), I("x"), N(": "), I("P"), N(" ← "), I("P"), N(" ∪ {(source, tier = "), I("L"), N("(licence), file URL, landing URL, rights holder, document id, figure label, caption, query, filter rule, SHA-256("), I("x"), N("), pHash("), I("x"), N("), time)}")]),
        (0, [B("End for")]),
        (1, [B("5.  De-duplication:")]),
        (2, [N("Cluster "), I("D"), N(" by identical SHA-256 (exact) and by pHash Hamming distance ≤ "), I("τ"), N(" (near); keep one canonical file per cluster (tier A preferred, then earliest) → "), I("K")]),
        (1, [B("6.  AI first-pass visual triage:")]),
        (2, [N("Render "), I("K"), N(" as 20-image contact sheets; vision-LLM agents assign "), I("y"), N("("), I("x"), N(") ∈ {keep, unsure, reject} and category ∈ {wwtp, sludge, wtp, pilot, other} under "), I("C"), N("; images with transparent background are re-rendered on white and judged manually")]),
        (1, [B("7.  Human validation:")]),
        (2, [N("Estimate precision on random keep / reject samples; "), B("If "), N("precision < target, "), B("then"), N(" refine "), I("C"), N(" and repeat step 6 "), B("End if")]),
        (1, [B("8.  Split assignment:")]),
        (2, [N("keep → main; unsure → {aux_unit, aux_pictorial, crop_pending, aux_other_domain, manual_review, excluded} by reason; reject → excluded")]),
        (1, [B("9.  Crop and promote:")]),
        (2, [N("Human draws boxes on crop_pending images; each crop inherits the parent provenance record and joins main")]),
        (0, [B("Return: "), I("K"), N(", "), I("P"), N(", "), I("y"), N(", "), I("z")]),
    ]
    algorithm_table(doc, "Table X. Pseudo-code of the provenance-tracked collection and triage pipeline.", rows1)

    # ------------------------------------------------------------------ Algorithm 2
    rows2 = [
        (0, [B("Algorithm 2: CaptionTier — keyword rule for literature figure captions")]),
        (0, [B("Input: "), N("caption "), I("c"), N("; word sets "), I("W"), N("diag (flow diagram, flowsheet, flowchart, process flow, schematic, layout, configuration, treatment train, block diagram, …), "), I("W"), N("strong ⊂ "), I("W"), N("diag (flow diagram, flowsheet, flowchart, process flow, block diagram, treatment train, process scheme, plant layout), "), I("W"), N("excl (sampling site, map of, photograph, SEM image, chromatogram, heat map, Venn, microbial community, graphical abstract, …), "), I("W"), N("plant (wastewater treatment plant, sewage treatment plant, WWTP, STP, WRRF, treatment line, full-scale plant, …), "), I("W"), N("treat (treatment, sludge, clarifier, digester, aeration, MBR, SBR, …)")]),
        (0, [B("Output: "), N("tier "), I("t"), N(" ∈ {T1, T2, none}")]),
        (0, [B("Initialization: "), I("c"), N(" ← lower-cased, whitespace-normalised caption")]),
        (1, [B("1.  Diagram test: "), B("If "), N("Contains("), I("c"), N(", "), I("W"), N("diag) = false, "), B("then"), N(" return none "), B("End if")]),
        (1, [B("2.  Exclusion test: "), B("If "), N("Contains("), I("c"), N(", "), I("W"), N("excl) and not Contains("), I("c"), N(", "), I("W"), N("strong), "), B("then"), N(" return none "), B("End if")]),
        (1, [B("3.  Plant test: "), B("If "), N("Contains("), I("c"), N(", "), I("W"), N("plant), "), B("then"), N(" return T1 "), B("End if")]),
        (1, [B("4.  Treatment test: "), B("If "), N("Contains("), I("c"), N(", "), I("W"), N("treat), "), B("then"), N(" return T2 "), B("End if")]),
        (0, [B("Return: "), N("none")]),
    ]
    algorithm_table(doc, "Table Y. Pseudo-code of the caption-tier rule (measured precision after visual triage: T1 0.55, n = 429; T2 0.23, n = 972).", rows2)

    doc.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
