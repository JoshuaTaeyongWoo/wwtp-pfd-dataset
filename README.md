# wwtp-pfd-dataset

Provenance-tracked collection of wastewater treatment plant (WWTP) process flow diagrams (PFDs) from open-access
literature, public agencies, plant operators, Wikimedia Commons and patents, for diagram-digitization research.
Non-commercial academic use.

This repository holds the **collection and screening code and its documentation**. The image files, provenance
records and catalog are not included yet; a curated release (redistributable "tier A" images with licence and
attribution metadata) will follow once the dataset is finalised.

## What is here

| Path | Content |
|---|---|
| `data_collection/README.md` | Methodology and results write-up (Korean, with an English methods draft and pseudo-code): sources, acquisition routes, caption-tier filter, provenance schema, de-duplication, AI-assisted visual triage, inclusion rules, final counts |
| `data_collection/TRIAGE_CRITERIA.md` | Decision rules for visual screening (keep / unsure / reject, categories, dataset splits) |
| `data_collection/s01…s14_*.py` | The pipeline, one script per stage: six source collectors (s01–s06), catalog and de-duplication (s07), review gallery (s08), contact sheets and AI triage merge (s09–s10), split rules (s11), crop tool and crop/review application (s12–s14) |
| `data_collection/common.py`, `pdf_figures.py` | Shared utilities: polite HTTP session, provenance records, hashing, caption filter, PDF figure extraction |
| `data_collection/paper/` | Generators for the manuscript figures and algorithm tables (matplotlib, python-docx, python-pptx) |

## Running

```bash
pip install -r data_collection/requirements.txt
cd data_collection
python s01_europepmc_pmc.py          # and s02 … s06; each is independent and resumable
python s07_dedup_catalog.py
python s08_review_gallery.py
```

Every collector identifies itself with a descriptive User-Agent, keeps a fixed request rate and uses only official
indexes and APIs (Europe PMC, the PMC Open Access bucket on AWS, OpenAlex, MediaWiki, Google Patents, EPA/NEPIS,
operator web pages). No access controls are circumvented. The Wikimedia collector requires a contact URL
(`--contact`), as the Wikimedia User-Agent policy asks; this repository URL is used for that purpose.

## Contact

Questions about the collector or the dataset, including requests from site operators about the crawler, can be
raised through the Issues tab of this repository.
