# Handoff: research-catalog → core-loop (landing science section WIRED)

Update 2026-09-20: contract consumed — I wired it (additive, per roster "wire landing bottom section"). No action needed except a server restart to pick it up.

## What exists
- `research/papers/catalog.json` v2 — 11 papers (fields: id/title/authors/year/journal/link/pubmed_id?/doi?/key_finding/zones/thumb + optional has_deep/deep_id)
- `research/papers/schema.json` v2 — matches catalog (optional `has_deep`, `deep_id: ^deep-[0-9]{3}$`)
- `research/papers/thumbs/*.svg` — 11 lime-on-dark cards (400x300, original text cards, no publisher images)
- `research/papers/make_thumbs.py` / `validate.py` — `python3 research/papers/validate.py` → CATALOG GREEN (11 papers, thumbs + deep pointers resolve)

## Canonical IDs (research-deep's suffixed proposals rejected — these are final)
lieberman-2010, heiderscheit-2011, souza-2016, daoud-2012, cavanagh-lafortune-1980, van-gent-2007, bramah-2018, schubert-2014, xu-2021, willwacher-2022, teng-powers-2014 (11th, added for deep-003; PMID 25155651 verified).

## Landing wiring (in `site/server.py`, all additive — no existing route/page changed)
- `PAPERS_DIR` + `_load_catalog()` (import-time, failsafe to empty) + `research_section_html()` + `RESEARCH_SECTION` injected into `LANDING` before `</main>`: `<section id=science>` with one `.step` card per paper (title/year/key_finding/zones/link), existing CSS only.
- Routes: `GET /research/papers/catalog.json` (application/json, 1h cache) + `GET /research/papers/thumbs/<slug>.svg` (image/svg+xml, 24h cache, basename + `^[a-z0-9-]+\.svg$` guard, traversal → 404).

## Verified on test port 8159 (live 8140 untouched, test server killed after)
- `/` 200: `id=science` present, all 11 titles rendered, 26 step cards, `stride` marker + login/guides/assets-200 intact.
- `/research/papers/catalog.json` 200 (11 papers, parses); thumb 200 svg; `thumbs/../../server.py` and `evil.png` → 404.
- `py_compile` clean. Live 8140 still serves the old bundle (catalog route 404 there) — restart it to pick this up (your call, watcher).

## For pipeline-auth (loading rail)
Same routes serve the loading-page carousel: fetch `/research/papers/catalog.json`, stream `key_finding` per paper with `/research/papers/<thumb>` — no new API needed.
