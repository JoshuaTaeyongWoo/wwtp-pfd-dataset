# Triage criteria for WWTP process-diagram candidates (v1, 2026-11-16)

Each candidate image gets one `decision` and, for keep/unsure, one `category`.

## decision
- **keep** — a process-level diagram of a treatment plant or treatment train: two or more unit processes
  (screens, grit chamber, primary/secondary clarifier, aeration tank/bioreactor, MBR, SBR, filters, UV/chlorination,
  thickener, digester, dewatering, ...) drawn as boxes, equipment symbols or icons, connected by flow lines or
  arrows. Block flow diagrams, PFDs, simplified P&IDs and simulator layouts (GPS-X, BioWin, SUMO screenshots) all
  count. Drinking-water plants, industrial wastewater plants, sludge/biosolids lines and pilot-scale trains count
  (see category).
- **unsure** — could be usable after cropping or with a relaxed inclusion rule: 3D/pictorial illustrations of a plant
  (cartoon tanks), one unit with its ancillaries only, equipment drawings without a flow path, plant layouts
  (top view) without flow lines, mass-balance box diagrams, infographics that embed a treatment train,
  multi-panel figures where only one panel is a diagram, low resolution / unreadable.
- **reject** — charts, graphs, tables, maps, satellite images, photographs, microscopy, molecular/biological
  schematics, chemical reaction pathways, study-design workflows, conceptual frameworks, sampling-point schemes
  without process units, text pages, blank cells, non-treatment processes (e.g. chemical synthesis, energy systems
  without a treatment train).

## category (keep / unsure only)
- **wwtp** — municipal or industrial wastewater treatment (water line, with or without sludge line)
- **sludge** — sludge / biosolids / digestion line only
- **wtp** — drinking-water or water-reuse treatment plant
- **pilot** — lab- or pilot-scale treatment train
- **other** — any other process diagram (e.g. membrane pilot for seawater, bio-refinery)

## note
Free text, optional (e.g. "panel (a) only", "3D cartoon", "pump station").

## Splits (decided 2026-11-16, applied by s11_apply_rules.py)

| decision / unsure group | split | use |
|---|---|---|
| keep | **main** | benchmark dataset (plant-level process diagrams) |
| unsure: single unit + ancillaries (233) | aux_unit | unit-level auxiliary set; not in the benchmark |
| unsure: 3D / pictorial (87) | aux_pictorial | domain-shift / robustness test set |
| unsure: crop needed (99) | crop_pending | becomes main after cropping (s12 crop tool -> s13) |
| unsure: layout, mass balance, control diagrams (41) | excluded | — |
| unsure: other-domain process diagrams (83) | aux_other_domain | chemical/refinery/power PFDs; optional pre-training data |
| unsure: unspecified or render failed (89) | manual_review | human decides in data/review/manual_review.html |
| reject | excluded | — |
