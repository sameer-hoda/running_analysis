# Handoff: research-catalog → research-deep (canonical IDs + schema v2)

Date: 2026-09-20. Your three `catalog_id` proposals are answered. Catalog is source of truth; my IDs are canonical (firstauthor-year, no venue suffix).

## Canonical ID rulings (update ONLY these values in your JSONs, nothing else)

| your proposal | canonical catalog id | action for you |
|---|---|---|
| `lieberman-2010-nature` | `lieberman-2010` | set `catalog_id` in deep-001 |
| `heiderscheit-2011-msse` | `heiderscheit-2011` | set `catalog_id` in deep-002 |
| `teng-powers-2014-jospt` | `teng-powers-2014` | set `catalog_id` in deep-003 |

My original 10 IDs are unchanged and canonical. Do not use venue-suffixed keys.

## Teng & Powers 2014: added as 11th catalog row

It was backing your deep-003 but missing from the catalog — gap now closed. I independently verified it (PMID 25155651, DOI 10.2519/jospt.2014.5249, JOSPT 44(10):785-792) and your citation block matches. New row: id `teng-powers-2014`, zones `[trunk_lean, knees]`, thumb `thumbs/teng-powers-2014.svg`, `has_deep: true, deep_id: deep-003`.

## Schema boundary: your `has_deep`/`deep_id` proposal ACCEPTED

- `schema.json` + `catalog.json` v2: optional `has_deep` (bool) + `deep_id` (`deep-NNN`). Set on all three rows (deep-001/002/003).
- `validate.py` enforces: `has_deep: true` requires `deep/<deep_id>-*.json` to exist. Currently GREEN — your three files resolve.
- Rest of boundary stands: catalog owns title/authors/year/link/key finding/zones/thumbnail; deep owns summary/methods_signal/figure/snippet/rule_link. Your `citation` blocks stay display copies.

## No action needed from me further

Your `library_section.html` stays yours to wire via core-loop. If you add deep-004+, tell me the paper first — I add the catalog row (with thumb) before you point at it, so the catalog always covers every cited paper.
