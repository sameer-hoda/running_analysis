# research/papers/deep/ — research-deep store (gait-science library)

Owner: research-deep. research-catalog owns `research/papers/catalog.json`
+ `research/papers/thumbs/` and is the canonical owner of bibliographic fields
(title / authors / year / link / key finding / backing rule / thumbnail).

## Boundary (no duplicate schema)

- Deep entries MUST NOT define catalog fields. They reference the catalog row
  via `catalog_id` (proposed IDs below; catalog agent is canonical — if it
  picks different IDs, update the `catalog_id` values, nothing else).
- `citation` below is a denormalized display copy so the library section
  renders standalone. Canonical bibliographic truth stays in catalog.json.
- Catalog thumbnails (pulled from papers) stay in `thumbs/`; deep figures are
  ORIGINAL redrawn schematics in `deep/figures/` (no paper artwork copied).

## Deep entry schema (deep-only fields)

```json
{
  "deep_id": "deep-001",
  "catalog_id": "<proposed catalog key>",
  "rule_link": {
    "zone": "<one of the 7 step1_prompt.txt zones>",
    "finding_title": "<report_template.html finding>",
    "how_it_backs": "1-2 sentences: what the paper justifies in this rule"
  },
  "summary": "original paraphrase, 3-5 sentences",
  "methods_signal": "design + population + key manipulation, 1-2 sentences",
  "snippet": {
    "text": "original paraphrase of the takeaway (NOT a paper quote)",
    "grounds_in": "where in the paper this comes from, e.g. Abstract + Results"
  },
  "figure": {
    "file": "figures/<name>.svg",
    "caption": "figure caption for the site",
    "what_it_shows": "what the schematic encodes",
    "redrawn": true
  },
  "citation": {
    "authors": "...", "year": 0, "title": "...",
    "journal": "...", "doi_url": "https://doi.org/...",
    "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/..."
  }
}
```

Required per entry: summary + methods_signal + figure + snippet + citation +
rule_link. Figures: original SVG, lime-on-dark (`--lime:#c8f04a`,
`--bg:#0a0c11`).

## Entries

| deep_id | paper | zone |
|---|---|---|
| deep-001 | Lieberman et al. 2010, Nature (`lieberman-2010`) | feet_strike |
| deep-002 | Heiderscheit et al. 2011, MSSE (`heiderscheit-2011`) | knees |
| deep-003 | Teng & Powers 2014, JOSPT (`teng-powers-2014`) | trunk_lean |
| deep-004 | Bramah et al. 2018, AJSM (`bramah-2018`) | trunk_lean |

`catalog_id` values are the catalog agent's canonical IDs verbatim
(enforced by `validate_deep.py`: every `catalog_id` must exist in
`catalog.json`, and the entry zone must be in that row's `zones`).
History: deep-003 was briefly Bramah during a window when Teng was not yet
in the catalog; once catalog v2 added `teng-powers-2014` (claiming deep-003),
Teng was restored to deep-003 and Bramah moved to deep-004 so both
directions of the pointer agree.

Consumers: `deep/library_section.html` is a drop-in gait-science library
section for the site (reads these JSON files' shape; wire-up by core-loop).
