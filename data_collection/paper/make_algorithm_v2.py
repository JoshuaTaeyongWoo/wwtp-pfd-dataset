"""
make_algorithm_v2.py — pseudo-code in the most common top-journal layout (LaTeX `algorithm` + `algorithmic` /
`algpseudocode` style): rule above and below, "Algorithm 1  Title" header, Input/Output lines, numbered lines,
bold keywords (for, if, repeat, return), indented blocks, right-aligned grey comments.

Outputs:
  paper/Algorithms_v2.docx   Word version (2-column table: line number | statement; comments in grey italic)
  paper/algorithms_v2.tex    LaTeX version (algorithm + algpseudocode) for journals that typeset from source
Usage: python make_algorithm_v2.py
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
KW = {"for", "do", "end for", "if", "then", "else", "end if", "repeat", "until", "return", "continue", "each", "in", "and", "not", "while", "end while"}

# ----------------------------------------------------------------------------- content
# (indent, statement with **bold** keyword markup, comment)
ALG1 = {
    "title": "Provenance-tracked harvesting and triage of process diagrams",
    "input": "source set S; query sets Q_s; caption rule CaptionTier (Algorithm 2); licence map L → {A, B}; pHash threshold τ; triage criteria C; target precision p*",
    "output": "canonical image set K; provenance table P; decision y(x) ∈ {keep, unsure, reject} and split z(x) for every x ∈ K",
    "lines": [
        (0, "D ← ∅, P ← ∅", "downloaded files and their records"),
        (0, "**for each** source s ∈ S **do**", ""),
        (1, "U_s ← Discover(s, Q_s)", "official index / API; identifying User-Agent, rate-limited"),
        (1, "**for each** document u ∈ U_s **do**", ""),
        (2, "(m_u, F_u) ← Acquire(s, u)", "metadata; JATS XML + figures, PDF, HTML <img>, drawing sheets"),
        (2, "**for each** figure f ∈ F_u **with** caption c_f **do**", ""),
        (3, "**if** c_f ≠ ∅ **and** CaptionTier(c_f) = none **then continue**", "caption-bearing sources only"),
        (3, "x ← Download(f); D ← D ∪ {x}", ""),
        (3, "P ← P ∪ {Record(x, s, u, m_u, c_f, L(m_u), SHA256(x), pHash(x))}", "append-only provenance"),
        (2, "**end for**", ""),
        (1, "**end for**", ""),
        (0, "**end for**", ""),
        (0, "K ← Deduplicate(D, τ)", "SHA-256 identity, then pHash Hamming ≤ τ; keep tier A, then earliest"),
        (0, "**repeat**", ""),
        (1, "y ← VisionTriage(K, C)", "20-image contact sheets; parallel vision-LLM agents"),
        (1, "p ← SpotCheck(y)", "human review of random keep / reject samples"),
        (1, "**if** p < p* **then** C ← Refine(C)", ""),
        (0, "**until** p ≥ p*", ""),
        (0, "z ← AssignSplits(y)", "main; aux_unit; aux_pictorial; aux_other_domain; crop_pending; manual_review; excluded"),
        (0, "K ← K ∪ Crop(K_crop_pending); z(crops) ← main", "manual crop boxes inherit the parent record"),
        (0, "**return** K, P, y, z", ""),
    ],
}
ALG2 = {
    "title": "CaptionTier: keyword rule for literature figure captions",
    "input": "caption c; word sets W_diag ⊇ W_strong (diagram terms; strong = flow diagram, flowsheet, flowchart, process flow, block diagram, treatment train, process scheme, plant layout), W_excl (maps, photographs, spectra, community plots, graphical abstracts, …), W_plant (treatment plant, WWTP, STP, WRRF, treatment line, full-scale plant, …), W_treat (treatment, sludge, clarifier, digester, aeration, MBR, SBR, …)",
    "output": "tier t ∈ {T1, T2, none}",
    "lines": [
        (0, "c ← Normalise(c)", "lower case, collapse whitespace"),
        (0, "**if not** Contains(c, W_diag) **then return** none", "not described as a diagram"),
        (0, "**if** Contains(c, W_excl) **and not** Contains(c, W_strong) **then return** none", "map / photo / chart"),
        (0, "**if** Contains(c, W_plant) **then return** T1", "whole-plant candidate"),
        (0, "**if** Contains(c, W_treat) **then return** T2", "treatment-related schematic"),
        (0, "**return** none", ""),
    ],
    "note": "Measured precision after visual triage: T1 0.55 (n = 429), T2 0.23 (n = 972).",
}


# ----------------------------------------------------------------------------- docx helpers
def border(cell, **sides):
    tcPr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for name in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{name}")
        on = sides.get(name, False)
        el.set(qn("w:val"), "single" if on else "nil"); el.set(qn("w:sz"), "8"); el.set(qn("w:color"), "000000")
        b.append(el)
    tcPr.append(b)


def run(p, text, bold=False, italic=False, color=None, size=9.5):
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.name = FONT; r.font.size = Pt(size)
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    if color is not None:
        r.font.color.rgb = color
    return r


def markup(p, s, size=9.5):
    """**kw** -> bold; identifiers with _ are kept literal (journal copy-editors set them in italics)"""
    parts = s.split("**")
    for i, part in enumerate(parts):
        if part:
            run(p, part, bold=(i % 2 == 1), size=size)


def fmt(p, indent_cm=0.0, after=0):
    pf = p.paragraph_format
    pf.left_indent = Cm(indent_cm); pf.space_after = Pt(after); pf.space_before = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE


def algorithm(doc, number, a):
    t = doc.add_table(rows=0, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    widths = (Cm(0.9), Cm(14.6))

    def row(top=False, bottom=False):
        cells = t.add_row().cells
        for c, w in zip(cells, widths):
            c.width = w
            border(c, top=top, bottom=bottom)
        return cells

    # header
    c = row(top=True, bottom=True)
    c[0].merge(c[1])
    p = c[0].paragraphs[0]; fmt(p, after=1)
    run(p, f"Algorithm {number} ", bold=True); run(p, a["title"])
    # input / output
    for lab, txt in (("Input: ", a["input"]), ("Output: ", a["output"])):
        c = row(); c[0].merge(c[1]); p = c[0].paragraphs[0]; fmt(p)
        run(p, lab, bold=True); run(p, txt)
    # numbered lines
    for n, (ind, stmt, com) in enumerate(a["lines"], 1):
        c = row()
        p = c[0].paragraphs[0]; fmt(p); p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        run(p, f"{n}:", size=8.5)
        p = c[1].paragraphs[0]; fmt(p, indent_cm=0.45 * ind)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(14.2), WD_TAB_ALIGNMENT.RIGHT)
        markup(p, stmt)
        if com:
            run(p, "\t▷ " + com, italic=True, color=GREY, size=8.5)
    # bottom rule (+ optional note)
    c = row(bottom=True); c[0].merge(c[1]); p = c[0].paragraphs[0]; fmt(p)
    run(p, a.get("note", ""), italic=True, size=8.5)
    doc.add_paragraph()


def build_docx():
    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.5)
    st = doc.styles["Normal"]; st.font.name = FONT; st.font.size = Pt(9.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    algorithm(doc, 1, ALG1)
    algorithm(doc, 2, ALG2)
    out = HERE / "Algorithms_v2.docx"; doc.save(out); print("saved", out)


# ----------------------------------------------------------------------------- LaTeX
def tex_line(ind, stmt, com):
    s = stmt
    for k in ("for each", "do", "end for", "if", "then", "else", "end if", "repeat", "until", "return", "continue", "and", "not", "with"):
        pass
    # translate **kw** markup to algpseudocode commands where possible, otherwise \textbf
    s = s.replace("**end for**", "\\EndFor").replace("**end if**", "\\EndIf")
    s = s.replace("**for each** ", "\\ForEach{").replace(" **do**", "}")
    s = s.replace("**repeat**", "\\Repeat").replace("**until** ", "\\Until{") + ("}" if "\\Until{" in s else "")
    s = s.replace("**return** ", "\\State \\Return ")
    s = s.replace("**", "\\textbf{", 1) if "**" in s else s
    while "**" in s:
        s = s.replace("**", "}", 1).replace("**", "\\textbf{", 1) if s.count("**") >= 2 else s.replace("**", "}")
    s = s.replace("←", "$\\leftarrow$").replace("∅", "$\\emptyset$").replace("∈", "$\\in$").replace("∪", "$\\cup$") \
         .replace("≤", "$\\le$").replace("≥", "$\\ge$").replace("≠", "$\\ne$").replace("τ", "$\\tau$").replace("→", "$\\to$") \
         .replace("⊇", "$\\supseteq$").replace("<img>", "\\texttt{<img>}").replace("_", "\\_")
    if not s.startswith("\\") or s.startswith("\\textbf"):
        s = "\\State " + s
    if com:
        s += " \\Comment{" + com.replace("_", "\\_").replace("≤", "$\\le$").replace("τ", "$\\tau$") + "}"
    return s


def build_tex():
    def block(number, a, label):
        lines = ["\\begin{algorithm}[t]", f"\\caption{{{a['title']}}}", f"\\label{{alg:{label}}}", "\\begin{algorithmic}[1]",
                 "\\Require " + a["input"].replace("_", "\\_").replace("→", "$\\to$").replace("τ", "$\\tau$").replace("⊇", "$\\supseteq$"),
                 "\\Ensure " + a["output"].replace("_", "\\_").replace("∈", "$\\in$")]
        lines += [tex_line(*l) for l in a["lines"]]
        lines += ["\\end{algorithmic}", "\\end{algorithm}", ""]
        return lines
    pre = ["% requires: \\usepackage{algorithm} \\usepackage{algpseudocode}",
           "% \\algnewcommand\\algorithmicforeach{\\textbf{for each}}",
           "% \\algdef{S}[FOR]{ForEach}[1]{\\algorithmicforeach\\ #1\\ \\algorithmicdo}", ""]
    out = HERE / "algorithms_v2.tex"
    out.write_text("\n".join(pre + block(1, ALG1, "pipeline") + block(2, ALG2, "captiontier")), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    build_docx()
    build_tex()
