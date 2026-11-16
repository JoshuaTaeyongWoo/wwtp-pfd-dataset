"""
s03_epa_manuals.py — Source 3: US EPA design manuals and technical reports (US federal works: public domain)

The documents are a curated list (DOCS below) of official EPA-hosted PDFs (epa.gov / nepis.epa.gov /
archive.epa.gov) plus mirrors on university web archives where EPA no longer hosts the file.
Figures are extracted with pdf_figures.extract(): pages whose caption matches the diagram regex are
saved as embedded images + a full-page render (many of these manuals are scanned, so the page
render is the usable artefact; the figure must later be cropped during annotation).

Licence: works of the US federal government are not subject to copyright in the US (17 U.S.C. §105);
figures reproduced *inside* a manual from third parties may carry their own rights — flagged for review.

Usage: python s03_epa_manuals.py
"""
from __future__ import annotations

import re
from pathlib import Path

from common import RAW, PROV, make_session, download, provenance_record, append_jsonl, already_done, get_logger, safe_name
import pdf_figures

SOURCE = "epa_manuals"
OUT = RAW / SOURCE
PDFS = OUT / "_pdf"
FIGS = OUT / "figures"
PROV_FILE = PROV / f"{SOURCE}.jsonl"
log = get_logger(SOURCE)

# (doc_id, title, year, url)
DOCS = [
    ("EPA-600-R-10-100", "Nutrient Control Design Manual", 2010,
     "https://www.epa.gov/sites/default/files/2019-08/documents/nutrient_control_design_manual.pdf"),
    ("EPA-600-R-11-088", "Principles of Design and Operations of Wastewater Treatment Pond Systems for Plant Operators, Engineers, and Managers", 2011,
     "https://www.epa.gov/sites/default/files/2014-09/documents/lagoon-pond-treatment-2011.pdf"),
    ("EPA-625-1-80-012", "Design Manual: Onsite Wastewater Treatment and Disposal Systems", 1980,
     "https://www.epa.gov/sites/default/files/2015-06/documents/septic_1980_osdm_all.pdf"),
    ("EPA-625-R-00-008", "Onsite Wastewater Treatment Systems Manual", 2002,
     "https://www.epa.gov/sites/default/files/2015-06/documents/2004_07_07_septics_septic_2002_osdm_all.pdf"),
    ("EPA-430-9-80-xxx-IA", "Innovative and Alternative Technology Assessment Manual", 1980,
     "https://www.epa.gov/sites/default/files/2019-12/documents/innovative-alternative-tech-manual-1980.pdf"),
    ("EPA-625-R-92-013", "Control of Pathogens and Vector Attraction in Sewage Sludge", 2003,
     "https://www.epa.gov/sites/default/files/2015-04/documents/control_of_pathogens_and_vector_attraction_in_sewage_sludge_july_2003.pdf"),
    ("EPA-600-R-14-241", "Emerging Technologies for Wastewater Treatment and In-Plant Wet Weather Management", 2013,
     "https://www.epa.gov/sites/default/files/2019-02/documents/emerging-tech-wastewater-treatment-management.pdf"),
    # --- verified in this session (official epa.gov / epa.gov snapshot hosts) ---
    ("EPA-832-R-08-006-v1", "Municipal Nutrient Removal Technologies Reference Document, Volume 1 - Technical Report", 2008,
     "https://www.epa.gov/sites/default/files/2019-08/documents/municipal_nutrient_removal_technologies_vol_i.pdf"),
    ("EPA-832-R-08-006-v2", "Municipal Nutrient Removal Technologies Reference Document, Volume 2 - Appendices (case studies)", 2008,
     "https://19january2021snapshot.epa.gov/sites/static/files/2019-02/documents/municipal-nutrient-removal-reference-document.pdf"),
    ("EPA-600-R-09-012", "Nutrient Control Design Manual: State of Technology Review Report", 2009,
     "https://19january2021snapshot.epa.gov/sites/static/files/2019-02/documents/nutrient-control-design-manual-state-tech.pdf"),
    ("EPA-2022-innov-nutrient", "Innovative Nutrient Removal Technologies: Case Studies of Intensified or Enhanced Treatment", 2022,
     "https://www.epa.gov/system/files/documents/2022-08/Innovative%20Nutrient%20Removal%20Technologies%20Report.pdf"),
    ("EPA-625-R-06-016", "Process Design Manual: Land Treatment of Municipal Wastewater Effluents", 2006,
     "https://19january2025snapshot.epa.gov/sites/default/files/2018-12/documents/process-design-manual-land-application.pdf"),
    # --- NEPIS (EPA National Service Center for Environmental Publications). Dockeys taken from the official
    #     NEPIS title lists (nepis.epa.gov/EPA/html/Pubs/pubtitleORD.html, pubtitleOW.html) and verified as PDF.
    #     These are page scans with an OCR text layer -> captions are searchable, figures come out as page renders.
    ("EPA-625-1-79-011", "Process Design Manual for Sludge Treatment and Disposal", 1979, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=P10037H6.PDF"),
    ("EPA-625-1-74-006", "Process Design Manual for Sludge Treatment and Disposal (1974 edition)", 1974, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=20007TN9.PDF"),
    ("EPA-625-1-71-004a", "Process Design Manual for Upgrading Existing Wastewater Treatment Plants", 1974, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=20007T66.PDF"),
    ("EPA-625-1-71-004a-rev", "Process Design Manual for Upgrading Existing Wastewater Treatment Plants (Oct 1974 revision)", 1974, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=9100WEPH.PDF"),
    ("EPA-625-1-75-007", "Process Design Manual for Nitrogen Control", 1975, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=9100PUPQ.PDF"),
    ("EPA-625-R-93-010", "Process Design Manual: Nitrogen Control", 1993, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=30004MI0.PDF"),
    ("EPA-625-1-87-001", "Design Manual: Phosphorus Removal", 1987, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=20008R7B.PDF"),
    ("EPA-625-1-86-021", "Design Manual: Municipal Wastewater Disinfection", 1986, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=300045OY.PDF"),
    ("EPA-625-1-83-015", "Design Manual: Municipal Wastewater Stabilization Ponds", 1983, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=300044QA.PDF"),
    ("EPA-625-1-75-003a", "Process Design Manual for Suspended Solids Removal", 1975, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=9101AVYN.PDF"),
    ("EPA-625-1-77-009-nepis", "Process Design Manual: Wastewater Treatment Facilities for Sewered Small Communities (NEPIS OCR copy)", 1977, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=20007U77.PDF"),
    ("EPA-625-1-89-023", "Design Manual: Fine Pore Aeration Systems", 1989, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=3000464S.PDF"),
    ("EPA-625-1-85-018", "Design Manual: Odor and Corrosion Control in Sanitary Sewerage Systems and Treatment Plants", 1985, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=300045C6.PDF"),
    ("EPA-625-1-87-014", "Design Manual: Dewatering Municipal Wastewater Sludges", 1987, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=300045WA.PDF"),
    ("EPA-625-1-82-014", "Process Design Manual: Dewatering Municipal Wastewater Sludges (1982 edition)", 1982, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=20008QGY.PDF"),
    ("EPA-625-1-81-013", "Process Design Manual: Land Treatment of Municipal Wastewater", 1981, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=30004492.PDF"),
    ("EPA-625-1-81-013a", "Process Design Manual: Land Treatment of Municipal Wastewater - Supplement", 1984, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=300044MM.PDF"),
    ("EPA-625-R-99-010", "Manual: Constructed Wetlands Treatment of Municipal Wastewaters", 2000, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=30004TBD.PDF"),
    ("EPA-625-1-88-022", "Design Manual: Constructed Wetlands and Aquatic Plant Systems for Municipal Wastewater Treatment", 1988, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=30004626.PDF"),
    ("EPA-625-R-92-005", "Wastewater Treatment/Disposal for Small Communities: Manual", 1992, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=30004JRI.PDF"),
    ("EPA-625-1-83-016", "Process Design Manual: Land Application of Municipal Sludge", 1983, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=300044ZS.PDF"),
    ("EPA-sludge-OM-1978", "Sludge Treatment and Disposal, Vol. 1 Sludge Treatment (operations manual)", 1978, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=20008ROG.PDF"),
    ("EPA-832-F-99-065", "Wastewater Technology Fact Sheet: Fine Bubble Aeration", 1999, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=200044EM.PDF"),
    ("EPA-832-F-99-064", "Wastewater Technology Fact Sheet: Ultraviolet Disinfection", 1999, "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=200044EE.PDF"),
    # --- NPDES technology fact sheets, current epa.gov locations
    ("EPA-832-F-00-016", "Wastewater Technology Fact Sheet: Package Plants", 2000, "https://www.epa.gov/sites/default/files/2015-06/documents/package_plant.pdf"),
    ("EPA-932-F-99-073", "Wastewater Technology Fact Sheet: Sequencing Batch Reactors", 1999, "https://www.epa.gov/system/files/documents/2022-10/sequencing-batch-reactors-factsheet.pdf"),
    ("EPA-832-F-00-014", "Wastewater Technology Fact Sheet: Trickling Filters", 2000, "https://www.epa.gov/system/files/documents/2022-10/trickling-filters-factsheet.pdf"),
    ("EPA-832-F-00-013", "Wastewater Technology Fact Sheet: Oxidation Ditches", 2000, "https://www.epa.gov/system/files/documents/2022-10/oxidation-ditch-factsheet.pdf"),
    ("EPA-832-F-07-015", "Wastewater Management Fact Sheet: Membrane Bioreactors", 2007, "https://www.epa.gov/sites/default/files/2019-08/documents/membrane_bioreactor_fact_sheet_p100il7g.pdf"),
    ("EPA-832-F-06-031", "Biosolids Technology Fact Sheet: Multi-Stage Anaerobic Digestion", 2006, "https://www.epa.gov/sites/default/files/2018-11/documents/multistage-anaerobic-digestion-factsheet.pdf"),
    ("EPA-832-R-10-005", "Evaluation of Energy Conservation Measures for Wastewater Treatment Facilities", 2010, "https://www.epa.gov/sites/default/files/2016-01/documents/p1008sbm.pdf"),
]


STOP = {"the", "and", "for", "of", "in", "a", "an", "to", "manual", "design", "process", "vol", "volume", "document", "reference"}


def title_matches(pdf: Path, title: str, pages: int = 6) -> bool:
    import pymupdf
    words = [w.lower() for w in re.findall(r"[A-Za-z]{4,}", title) if w.lower() not in STOP]
    try:
        doc = pymupdf.open(pdf)
        text = " ".join(doc[i].get_text("text").lower() for i in range(min(pages, len(doc))))
        doc.close()
    except Exception:
        return False
    if not text.strip():          # scanned PDF without OCR text: cannot verify, accept with a note
        log.info("no text layer in %s; title check skipped", pdf.name)
        return True
    hit = sum(1 for w in words if w in text)
    return hit >= max(2, len(words) // 2)


def main():
    session = make_session()
    done = already_done(PROV_FILE)
    PDFS.mkdir(parents=True, exist_ok=True)
    tot = 0
    for doc_id, title, year, url in DOCS:
        pdf = PDFS / f"{safe_name(doc_id)}.pdf"
        ok = download(session, url, pdf, timeout=600, min_bytes=50_000)
        if not ok:
            log.warning("download failed: %s %s", doc_id, url)
            continue
        # sanity: must be a PDF
        with open(pdf, "rb") as f:
            head = f.read(5)
        if head != b"%PDF-":
            log.warning("not a PDF (probably an HTML page): %s", doc_id)
            pdf.unlink(missing_ok=True)
            continue
        # sanity: the first pages must mention the expected title words (guards against a wrong Dockey)
        if not title_matches(pdf, title):
            log.warning("title check FAILED (document may not be %s): %s -> skipped, kept pdf for review", doc_id, title)
            continue
        figs = pdf_figures.extract(pdf, FIGS / safe_name(doc_id), safe_name(doc_id))
        n = 0
        for fg in figs:
            rid = f"{SOURCE}:{doc_id}:{fg['path'].name}"
            if rid in done:
                continue
            rec = provenance_record(
                source=SOURCE, tier="A", image_path=fg["path"],
                acquisition_method="HTTP GET of official EPA PDF -> PyMuPDF caption-matched page extraction",
                file_url=url, landing_url=url,
                license="US Government work (public domain, 17 U.S.C. 105)",
                license_url="https://www.usa.gov/government-copyright", rights_holder="US EPA",
                doc_id=doc_id, title=title, venue="US EPA", year=year,
                figure_label=fg["label"], caption=fg["caption"], query="curated list",
                filter_rule=f"caption_tier={fg['tier']};kind={fg['kind']}",
                extra={"page": fg["page"], "kind": fg["kind"], "caption_tier": fg["tier"]},
            )
            rec["record_id"] = rid
            append_jsonl(PROV_FILE, rec)
            n += 1
        tot += n
        log.info("%s: %d figure files (pdf %.1f MB)", doc_id, n, pdf.stat().st_size / 1e6)
    log.info("DONE total figure files %d", tot)


if __name__ == "__main__":
    main()
