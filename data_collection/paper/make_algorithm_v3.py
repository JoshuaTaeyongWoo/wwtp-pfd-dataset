"""
make_algorithm_v3.py — pseudo-code revised for a water / environmental-engineering readership.

Changes from v2
  * domain wording: "process flow diagram (PFD) of a treatment plant", "treatment train", "unit process",
    "full-scale plant", "licence tier", "benchmark subset" — no CS jargon (no "canonical", "hash cluster", "LLM agent")
  * plain-English procedure names (QueryIndex, FetchFigures, TierCaption, RemoveDuplicates, ScreenVisually,
    AuditSample, AssignSubset, CropAndPromote) with one-line meaning in the right-hand comment
  * flat structure: one loop over documents, one over figures; the triage loop reads as a quality-control cycle
  * every symbol is defined once in the Input block; measured values are quoted in comments
  * Algorithm 2 is written as a decision list (rule 1-4), which is how screening rules are reported in this field
Outputs: paper/Algorithms_v3.docx, paper/algorithms_v3.tex
Usage  : python make_algorithm_v3.py
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
FONT = "Times New Roman"
GREY = RGBColor(0x59, 0x59, 0x59)

ALG1 = {
    "title": "Collection and screening of treatment-plant process diagrams with full provenance",
    "input": [
        "S — document sources: open-access journal articles, public-agency design manuals, plant-operator web pages, Wikimedia Commons, patents",
        "Q — search terms per source (e.g. “wastewater treatment plant”, “sewage treatment plant”, “water resource recovery facility”)",
        "TierCaption — caption screening rule (Algorithm 2)",
        "τ — near-duplicate threshold (perceptual-hash Hamming distance; τ = 6 bits)",
        "C — visual screening criteria (keep / unsure / reject; category wwtp, sludge, wtp, pilot, other)",
        "p* — minimum acceptable precision of “keep” decisions on an audited sample (p* = 0.90)",
    ],
    "output": [
        "I — set of unique candidate images with one provenance record each (source, URLs, licence tier, caption, rule, hashes)",
        "Subsets of I: main benchmark; auxiliary sets (unit-level, pictorial, other-domain); crop-pending; manual-review; excluded",
    ],
    "lines": [
        (0, "I ← ∅", "image set and provenance records start empty"),
        (0, "**for each** source s **in** S **do**", ""),
        (1, "U ← QueryIndex(s, Q)", "candidate documents from the official index or API of s"),
        (1, "**for each** document u **in** U **do**", ""),
        (2, "F ← FetchFigures(s, u)", "figures with captions (XML or PDF), web images, or patent drawing sheets"),
        (2, "**for each** figure f **in** F **do**", ""),
        (3, "**if** f has a caption **and** TierCaption(f) = none **then skip** f", "keeps only T1 / T2 captions"),
        (3, "download f; add f to I **with** record(source, identifiers, URLs, rights holder, caption, licence tier, SHA-256, pHash)", "tier A = redistributable, tier B = research use only"),
        (2, "**end for**", ""),
        (1, "**end for**", ""),
        (0, "**end for**", "3,300 files from 1,877 documents"),
        (0, "I ← RemoveDuplicates(I, τ)", "identical files (SHA-256) and near-identical copies (pHash ≤ τ); 3,114 unique images"),
        (0, "**repeat**", "quality-control cycle"),
        (1, "ScreenVisually(I, C)", "every image judged on 20-image contact sheets: keep / unsure / reject + category"),
        (1, "p ← AuditSample(I)", "expert review of random “keep” and “reject” samples (30 + 30)"),
        (1, "**if** p < p* **then** revise C", ""),
        (0, "**until** p ≥ p*", "achieved p ≈ 0.90; no process diagram found in the reject sample"),
        (0, "AssignSubset(I)", "keep → main; unsure → auxiliary / crop-pending / manual-review by reason; reject → excluded"),
        (0, "CropAndPromote(I)", "multi-panel figures and page scans cropped by hand; crops inherit the parent record and join main"),
        (0, "**return** I **with** subsets", "main 952 (747 tier A), auxiliary 403, crop-pending 99, manual-review 89, excluded 1,571"),
    ],
    "note": "Values in the comments are from the run of 16 November 2026 (Section 6).",
}
ALG2 = {
    "title": "TierCaption — caption-based screening of literature figures",
    "input": [
        "c — figure caption (lower-cased)",
        "Diagram words — flow diagram, flowsheet, flowchart, process flow, schematic, layout, configuration, treatment train, block diagram, process scheme",
        "Strong diagram words — subset of the above that almost always denote a process diagram: flow diagram, flowsheet, flowchart, process flow, block diagram, treatment train, process scheme, plant layout",
        "Exclusion words — sampling site, map of, photograph, aerial, microscopy, chromatogram, spectrum, heat map, Venn, microbial community, graphical abstract, study workflow",
        "Plant words — wastewater / sewage treatment plant, WWTP, STP, WRRF, treatment works, treatment line, full-scale plant",
        "Treatment words — treatment, sludge, clarifier, digester, aeration, activated sludge, MBR, SBR",
    ],
    "output": ["tier — T1 (whole-plant diagram), T2 (treatment-related schematic) or none (not downloaded)"],
    "lines": [
        (0, "**Rule 1** — **if** c contains no diagram word **then return** none", "caption does not describe a diagram"),
        (0, "**Rule 2** — **if** c contains an exclusion word **and** no strong diagram word **then return** none", "maps, photographs, charts, biology figures"),
        (0, "**Rule 3** — **if** c contains a plant word **then return** T1", "candidate whole-plant diagram"),
        (0, "**Rule 4** — **if** c contains a treatment word **then return** T2", "single unit process, pilot or sludge-line schematic"),
        (0, "**return** none", ""),
    ],
    "note": "Precision measured after visual screening: T1 0.55 (n = 429), T2 0.23 (n = 972). Rule 2 was added after a first pass let “map of the study area … wastewater treatment plant” through as T1.",
}


# ----------------------------------------------------------------------------- Word
def border(cell, **sides):
    tcPr = cell._tc.get_or_add_tcPr(); b = OxmlElement("w:tcBorders")
    for name in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{name}"); on = sides.get(name, False)
        el.set(qn("w:val"), "single" if on else "nil"); el.set(qn("w:sz"), "8"); el.set(qn("w:color"), "000000"); b.append(el)
    tcPr.append(b)


def run(p, text, bold=False, italic=False, color=None, size=9.5):
    r = p.add_run(text); r.bold, r.italic = bold, italic
    r.font.name = FONT; r.font.size = Pt(size); r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    if color is not None:
        r.font.color.rgb = color
    return r


def markup(p, s, size=9.5):
    for i, part in enumerate(s.split("**")):
        if part:
            run(p, part, bold=(i % 2 == 1), size=size)


def fmt(p, indent_cm=0.0, after=0, before=0):
    pf = p.paragraph_format; pf.left_indent = Cm(indent_cm); pf.space_after = Pt(after); pf.space_before = Pt(before)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE


def algorithm(doc, number, a):
    t = doc.add_table(rows=0, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    widths = (Cm(0.9), Cm(14.6))

    def row(top=False, bottom=False):
        cells = t.add_row().cells
        for c_, w in zip(cells, widths):
            c_.width = w; border(c_, top=top, bottom=bottom)
        return cells

    c = row(top=True, bottom=True); c[0].merge(c[1]); p = c[0].paragraphs[0]; fmt(p, after=1, before=1)
    run(p, f"Algorithm {number}  ", bold=True); run(p, a["title"], bold=True)
    for lab, items in (("Input", a["input"]), ("Output", a["output"])):
        c = row(); c[0].merge(c[1]); p = c[0].paragraphs[0]; fmt(p, before=1)
        run(p, lab + ":", bold=True)
        for it in items:
            p = c[0].add_paragraph(); fmt(p, indent_cm=0.6)
            sym, _, rest = it.partition(" — ")
            run(p, sym, italic=True); run(p, " — " + rest if rest else "")
    c = row(top=True); c[0].merge(c[1]); fmt(c[0].paragraphs[0])   # thin rule before the numbered lines
    for n, (ind, stmt, com) in enumerate(a["lines"], 1):
        c = row(); p = c[0].paragraphs[0]; fmt(p); p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT; run(p, f"{n}", size=8.5, color=GREY)
        p = c[1].paragraphs[0]; fmt(p, indent_cm=0.5 * ind)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(14.2), WD_TAB_ALIGNMENT.RIGHT)
        markup(p, stmt)
        if com:
            run(p, "\t▷ " + com, italic=True, color=GREY, size=8.5)
    c = row(bottom=True); c[0].merge(c[1]); p = c[0].paragraphs[0]; fmt(p, before=1)
    run(p, a.get("note", ""), italic=True, size=8.5)
    doc.add_paragraph()


def build_docx():
    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.5)
    st = doc.styles["Normal"]; st.font.name = FONT; st.font.size = Pt(9.5); st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    algorithm(doc, 1, ALG1); algorithm(doc, 2, ALG2)
    out = HERE / "Algorithms_v3.docx"; doc.save(out); print("saved", out)


# ----------------------------------------------------------------------------- LaTeX
def tex_esc(s):
    return (s.replace("←", "$\\leftarrow$").replace("∅", "$\\emptyset$").replace("≤", "$\\le$").replace("≥", "$\\ge$")
             .replace("τ", "$\\tau$").replace("→", "$\\to$").replace("≈", "$\\approx$").replace("—", "---").replace("_", "\\_")
             .replace("“", "``").replace("”", "''").replace("%", "\\%"))


def tex_line(ind, stmt, com):
    s = stmt
    s = s.replace("**end for**", "\\EndFor").replace("**repeat**", "\\Repeat")
    if s.startswith("**until** "):
        s = "\\Until{" + s[len("**until** "):] + "}"
    elif s.startswith("**for each** "):
        s = "\\ForEach{" + s[len("**for each** "):].replace(" **do**", "") + "}"
    elif s.startswith("**return**"):
        s = "\\State \\Return" + s[len("**return**"):]
    elif not s.startswith("\\"):
        s = "\\State " + s
    s = s.replace("**", "\\textbf{", 1)
    while "**" in s:
        s = s.replace("**", "}", 1)
        if "**" in s:
            s = s.replace("**", "\\textbf{", 1)
    s = tex_esc(s)
    if com:
        s += " \\Comment{" + tex_esc(com) + "}"
    return s


def build_tex():
    def block(number, a, label):
        L = ["\\begin{algorithm}[t]", f"\\caption{{{tex_esc(a['title'])}}}", f"\\label{{alg:{label}}}", "\\begin{algorithmic}[1]",
             "\\Require"] + ["  \\Statex \\hspace{1em}" + tex_esc(i) for i in a["input"]] + ["\\Ensure"] + \
            ["  \\Statex \\hspace{1em}" + tex_esc(i) for i in a["output"]]
        L += [tex_line(*l) for l in a["lines"]]
        L += ["\\end{algorithmic}", f"\\begin{{flushleft}}\\footnotesize\\emph{{{tex_esc(a['note'])}}}\\end{{flushleft}}", "\\end{algorithm}", ""]
        return L
    pre = ["% requires: \\usepackage{algorithm} \\usepackage{algpseudocode}",
           "% \\algnewcommand\\algorithmicforeach{\\textbf{for each}}",
           "% \\algdef{S}[FOR]{ForEach}[1]{\\algorithmicforeach\\ #1\\ \\algorithmicdo}", ""]
    out = HERE / "algorithms_v3.tex"
    out.write_text("\n".join(pre + block(1, ALG1, "pipeline") + block(2, ALG2, "tiercaption")), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    build_docx(); build_tex()
