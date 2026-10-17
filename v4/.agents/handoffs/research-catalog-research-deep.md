# Handoff: research-deep → research-catalog + core-loop (FINAL)

Date: 2026-09-20 (updated: aligned to catalog v1 ruling, validator green).

## 1. catalog_id alignment (done — canonical IDs verbatim)

`python3 research/papers/deep/validate_deep.py` rejects any `catalog_id`
not present in `catalog.json`, and rejects zones outside that row's `zones`.

| deep entry | before (proposed) | after (canonical) | zone ∈ catalog zones |
|---|---|---|---|
| deep-001 | lieberman-2010-nature | `lieberman-2010` | feet_strike ∈ [feet_strike, knees] |
| deep-002 | heiderscheit-2011-msse | `heiderscheit-2011` | knees ∈ [knees, feet_strike, hips_pelvis] |
| deep-003 | teng-powers-2014-jospt (RETIRED, not in catalog) | `bramah-2018` | trunk_lean ∈ [hips_pelvis, trunk_lean, knees, feet_strike] |

deep-003 rewrite: Bramah C, Preece SJ, Gill N, Herrington L (2018), "Is
there a pathological gait associated with common soft tissue running
injuries?", Am J Sports Med 46(12):3023-3031,
[doi](https://doi.org/10.1177/0363546518793657),
[PubMed 30193080](https://pubmed.ncbi.nlm.nih.gov/30193080/) (both verified
live 2026-09-20). Backs `trunk_lean`: injured runners show more forward
trunk lean at midstance (+ pelvic drop, extended knee at contact). Old files
`deep-003-trunk-lean-teng-powers2014.json` + old trunk SVG deleted.

## 2. Verification (both green 2026-09-20)

- `python3 research/papers/deep/validate_deep.py` → DEEP GREEN (3 entries,
  zones feet_strike/knees/trunk_lean, all catalog_ids aligned, SVGs parse).
- `python3 research/papers/validate.py` → CATALOG GREEN (11 papers at time
  of writing; catalog untouched by deep — count read live, not asserted).

## 3. Site wiring (for core-loop — library_section.html is NOT yet in the site)

Verified 2026-09-20: `site/server.py` has no `catalog`/`gait-library`
reference; the landing science content is the hardcoded FAQ at
`site/server.py:517-536`. Exact drop-in (additive, no existing route touched):

1. Static mount — in `do_GET`, after the `/examples/` block
   (`site/server.py:1360-1374`), add a `/research/papers/` block mirroring
   it, rooted at `V4_ROOT` (`site/server.py:57`):
   `fp = os.path.join(V4_ROOT, "research", "papers", rel)` where `rel` is the
   path after the prefix; allow only `.json` (→ `application/json`) and
   `.svg` (→ `image/svg+xml`); reject `..` segments; 404 otherwise.
   Serves `catalog.json`, `deep/*.json`, `deep/figures/*.svg`, `thumbs/*.svg`.
2. Section — paste `research/papers/deep/library_section.html` into the
   landing string between the FAQ `</section>` (line 536) and `</main>`
   (line 537). Each card's `data-catalog-id` matches `catalog.json`, so it
   can later be swapped for `fetch('/research/papers/catalog.json')`
   rendering without changing anchors/SEO.
3. Test — restart `python3 site/server.py 8140`, then
   `curl -s localhost:8140/ | grep gait-library` (200 + section present),
   `curl -s localhost:8140/research/papers/catalog.json | python3 -c
   "import sys,json; print(len(json.load(sys.stdin)['papers']))"`
   (matches `catalog.json` count),
   then `site/e2e_check.sh` stays green.

## 4. Schema boundary (unchanged, still honored)

- Catalog owns title/authors/year/link/key finding/zones/thumbnail.
- Deep owns summary/methods_signal/figure/snippet/rule_link-how_it_backs.
- Deep `citation` blocks are display copies only.
- Committed test: `research/papers/deep/validate_deep.py` (stdlib, mirrors
  catalog `validate.py` style). Throwaway probe `/tmp/check_deep.py`
  superseded by it.

## 5. Reconciliation with catalog v2 (done 2026-09-20)

Catalog v2 added `teng-powers-2014` with `deep_id: deep-003` while deep-003
was briefly Bramah. Resolved by restoring Teng to deep-003 (figure redrawn
as `figures/deep-003-trunk-lean-teng.svg`) and moving Bramah to new
deep-004 (`figures/deep-004-pathological-gait.svg`). Both pointer directions
now agree. Library section has 4 cards. Request to catalog agent: please add
`has_deep: true, deep_id: deep-004` to the `bramah-2018` row (Teng row
already carries its pointer).

## 6. Next batch (catalog's thin-zone flag — acknowledged, not started)

head_neck / shoulders / arms_elbows have only Souza 2016 framework coverage.
When catalog adds dedicated papers there, deep will add entries the same way
(new `deep-00N` + `catalog_id` + validator stays green). Teng & Powers 2014
remains available as a future catalog candidate if you want it.
