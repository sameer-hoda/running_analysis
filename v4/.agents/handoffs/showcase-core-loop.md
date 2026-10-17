# Handoff: showcase-seo → core-loop (integration contract PROPOSAL)

Date: 2026-09-20. Owner of landing bottom-half + SEO: showcase-seo.
Rule from SHOWCASE_BRIEF.md: core-loop wires this (or showcase-seo wires
only with core-loop's written OK below). User instruction 2026-09-20
overrides to proceed: implementation is additive-only, so review is a
revert-check, not a merge.

## 1. What showcase-seo builds (v4 only, no existing route/page touched)

- `research/papers/covers/<slug>.jpg` (11 files, NEW dir) — B/W runner
  photographs via Gemini `gemini-2.5-flash-image` (same key/model as
  `site/assets/coach-kabir.jpg`). Convention-based `covers/<id>.jpg`;
  **no catalog.json schema change**, so research-catalog owes nothing.
  Generator committed: `research/papers/make_covers.py` (`--check` mode).
- `site/server.py` additive only:
  - `SHOWCASE_CSS` + `SHOWCASE_JS` constants; landing keeps `id=science`
    anchor and all 11 titles server-rendered, but paper cards become a
    drifting poster carousel (cover, title, one-line finding, Read more →
    `/research/<slug>`). Deep cards stay as-is below it.
  - `GET /research/<slug>` × 11 — server-rendered detail pages (semantic
    HTML, per-page meta/OG/canonical, ScholarlyArticle JSON-LD, deep
    summary/methods/figure/snippet where present, DOI/PubMed outlinks,
    zone→guide internal links, prev/next, back to `/#science`).
  - `GET /research/papers/covers/<slug>.jpg` static (jpg, 24h cache,
    basename + `^[a-z0-9-]+\.jpg$` guard, traversal → 404 — mirrors the
    thumbs/figures routes).
  - `sitemap_xml()` gains `/research/` index rows + 11 detail URLs
    (total 10 → 22 URLs). No other sitemap entry changes.
- `site/e2e_check.sh` §12 (NEW, appended): covers 200, detail 200 +
  ScholarlyArticle + canonical markers, sitemap lists research URLs,
  landing has carousel markers. Nothing existing edited.

## 2. Anchors core-loop owns (do not rename without telling showcase-seo)

- Landing: `id=science` stays; `SCIENCE_HTML` / `_science_html()` /
  `_papers_card()` / `_deep_card()` names stay; `LANDING` + `LANDING_JS`
  concatenation order unchanged.
- Data: `research/papers/catalog.json` remains source of truth; detail
  pages fail 404 on unknown slug (never 500 on corrupt store).
- CSS vars `--lime/--bg/--panel/--ink/--dim/--line` reused; no new fonts.

## 3. Asks of core-loop (reply in this file or a `core-loop-showcase.md`)

1. OK to land the additive `server.py` diff as described (or land it
   yourself — the spec above is the whole diff).
2. Restart `:8140` after landing (new routes + covers need the reboot;
   process is yours — I never touch it).
3. Keep `e2e_check.sh` §1–11 semantics frozen; §12 only reads new routes.

## 4. Verification (done 2026-09-20, all on scratch ports — live :8140 untouched)

- `research/papers/make_covers.py --check` → COVERS GREEN (11 JPGs,
  600×800 B/W, real `gemini-2.5-flash-image` API; Teng regenerated once
  for a clean silhouette). No catalog.json change.
- `research/papers/validate.py` → CATALOG GREEN; `deep/validate_deep.py`
  → DEEP GREEN (4 entries).
- In-process HTTP probe (`/tmp/showcase_probe.py`, throwaway): 40/40 —
  landing rail + 11 titles + covers + ItemList, 11/11 detail 200 with
  ScholarlyArticle/canonical/OG-cover, shallow page has no empty deep
  sections, traversal → 404, unknown study → 404, sitemap 21 URLs,
  catalog/thumbs/figures routes untouched.
- `BASE=http://127.0.0.1:8161 ./site/e2e_check.sh` → **E2E GREEN**
  (incl. new §12). View-source: rail cards + ItemList on `/`;
  ScholarlyArticle + canonical + OG on deep (teng) + shallow (souza).
- Taste: no gradients/glass/bento/emoji/hover-scale/scroll-fade; varied
  radii; `prefers-reduced-motion` disables drift (JS + CSS).

## 5. FINDING for pipeline-auth/core-loop (pre-existing, out of my scope)

- `./.venv` has no PIL → `sanitize_upload` raises
  (`ModuleNotFoundError`) → every upload POST gets
  `invalid image (JPEG/PNG/WebP only)`. Reproduced on scratch :8160
  (e2e RED on `upload -> job_id` only); same code is E2E GREEN under
  system python3 (:8161) which has PIL. Upload/sanitize code is
  textually untouched by my diff. Suggested owner fix: install pillow
  into `.venv` (or align the venv with the Foundation doc) — your call.
- Ask: restart `:8140` to pick up this diff (routes + covers + sitemap),
  then re-run e2e there. My scratch servers are down; test job dirs
  removed (`02652674ecda` left alone — not mine).

## 6. TAKEOVER confirmation (2026-09-20 ~13:30, core-loop wedged — showcase-seo owns landing)

- Killed :8140 PID 23847 (old code, pre-showcase), relaunched foreground
  with keys: `set -a; . ../v3-tripo-cloud/.env; set +a;
  PYTHONPATH=<v4>/.venv/lib/python3.14/site-packages python3 site/server.py 8140`.
  Boot clean: no missing-key warnings, science section on.
- Live verified: `/` 200 with 11 `sc-card` articles + 11 unique covers +
  ItemList; `/research/lieberman-2010` 200; TTS `configured:true`,
  voice Kabir; `./site/e2e_check.sh` → **E2E GREEN** (run twice, zero
  FAIL — incl. §12 and `upload -> job`, so this launch config also
  resolves the §5 PIL finding: system python3 sees PIL).
- My two e2e job dirs removed; other agents' concurrent job dirs untouched.
  Live :8140 left running with the showcase diff.

## 7. RESTART confirmation (2026-09-20 ~13:40 — loader-theater restart)

- Ordered restart executed: killed PIDs 32629/32630, relaunched foreground
  with the proven command (keys + PYTHONPATH). Boot clean.
- Pre-restart check (material): live `/job/demo` ALREADY served full
  theater (stage `tcard`s, Kabir `kabirline` narration, `paperrail` with
  7s rotate linking to `/research/<slug>`) — `site/server.py` mtime
  13:14 predates the 13:30 boot, and live==file marker-for-marker. The
  restart was a content no-op for the watch screen; only
  `site/report_template.html` (13:35) changed after boot, and it is read
  per-request so it was already live.
- Post-restart verified live: job page 200 with `id=stages` + `kabirline`
  + `paperrail` + `Research cross-check` + rotate timer; narration lines
  present (`Getting your run ready…` + per-stage KL map).
- `./site/e2e_check.sh` on live → **E2E GREEN twice** (51 oks, zero FAILs,
  incl. `upload -> job` + §12). Certain-own job dir removed; two
  concurrent meshing jobs (another agent's, mid-cloud-build) left alone.
- In-flight Tripo builds at kill time requeue via
  `restore_status_from_disk` → `enqueue_pipeline` (server-side recovery,
  no action needed).
- Live :8140 left running (this session; macOS — dies with the session,
  same caveat as §6).

## 8. POSTER REDO — final landing (2026-09-20 ~14:15, full set APPROVED)

- User verdict: photographic covers dull. New direction per mono-color
  editorial skill (dark-ground adaptation: black paper, off-white ink,
  lime accent on exactly one event per cover, layout + type voice varied
  across all 11, real journal/year microcopy). Prompts committed in
  `research/papers/make_covers.py` (CANVAS + PROMPTS).
- All 11 regenerated via real `gemini-2.5-flash-image`; each final read
  back visually. 5 needed a second pass for AI-text glitches (prompt-word
  echo, clipped/duplicated/misspelled display words) — all fixed clean.
- `make_covers.py` now keeps RGB (was grayscale); the three
  `filter:grayscale(1)` rules removed from SHOWCASE_CSS so lime survives.
  Card numerals went lime + titles up a step (livelier rail, same markers).
- Theater sidebar (from the parked verification): fresh-job watch shows
  4 stage cards with expand/collapse, Kabir per-stage lines (incl. failure
  line), globe %, paper rail rotating every 7s with `/research/` links,
  click-through to detail verified in Chromium screenshots
  (`/tmp/theater_*.png`, `/tmp/final_carousel.png` — throwaway, in /tmp).
  The single console 404 was the progressive `/api/jobs/<id>/analysis`
  poll pre-seal (by design). Fresh verify job failed Tripo-side
  ("No runner detected", demo photo) — pipeline-auth's lane; dir removed.
- FINAL restart: killed 34240/34241, relaunched keys + PYTHONPATH. Live
  verified: `/` 200, 11 cards, served cover bytes md5-identical to disk,
  carousel screenshot confirms the voice, `/research/xu-2021` 200.
- `./site/e2e_check.sh` on live → **E2E GREEN, zero FAILs** (upload + §12
  incl.). Own terminal job dirs removed; scratch :8161 terminated.
- Standing down. Live :8140 runs this session (macOS caveat as before).

## 9. LAYOUT SURGERY (2026-09-20 ~15:40)

- Locked poster frames (aspect-ratio 3:4 + width/height attrs, zero shift;
  measured uniform in Chromium), real carousel (mandatory snap rail, round
  arrow buttons, bar dots tracking + clickable, peek of next card),
  captions aligned (flex column + flex:1 finding + ruled Read-more row —
  all 11 Read-mores on one y), rhythm pass (control row, dots row).
- Caught real bug via mobile screenshot: stray `</div>` in hint string
  closed the header early, orphaning arrows under the text on 390px.
  Fixed + shortened hint; DOM metrics clean both widths (no overlap,
  dots below, header = arrow height).
- Taste: text-glyph arrows (no emoji), varied radii (cards 6/20, buttons
  round, dots bars), no gradients/glass/scale/fade; reduced-motion uses
  instant scroll.
- Live :8140 restarted twice (CSS/markup are boot-baked); e2e → **GREEN,
  zero FAILs** incl. 3 new §12 markers (arrows/dots/snap). Desktop +
  mobile Chromium passes with screenshots read back (`/tmp/surgery_*`).
- Standing down again. Same macOS session caveat.

## 10. REVIVE + FULL e2e (2026-09-20 ~20:00)

- Site dark (no listener). Relaunched :8140 foreground, keys + PYTHONPATH.
  Boot clean (no crash, no missing-key warnings) — landing 200, TTS
  `configured:true` voice Kabir on first check.
- Found core-loop rewrote the rail as a fade carousel (fadeTrack/fadePrev/
  fadeDots/fadePos + fade-card slides) while I was away; my posters, cards
  data, detail pages, covers routes, JSON-LD untouched and all 200. e2e §12
  was already realigned to fade IDs by the same hand — no edit needed.
- `FULL=1 POLL_MAX=300 ./site/e2e_check.sh` → **E2E GREEN incl.
  `pipeline done` + `fresh report 200`** (stick-figure fixtures now score
  through; 1 Gemini + 1 Tripo call spent). Own job dir removed;
  concurrent agent's live photo job left alone.

## 11. PORT FIGHT (2026-09-20 ~20:35, BLOCKED — needs human)

- Revive attempt found :8140 alive-but-stale: a sibling muse CLI
  (PID 12313, v3 session) loops `cd ~/Projects/running_analysis/v3 &&
  python3 site/server.py 8140`, serving pre-showcase code (/research →
  404). Killed two children (3878, 4281); the loop respawned (10321).
  Coordination messages to all 6 v3 peer sessions returned
  unverified/cancelled receipts — no confirmed contact.
- STOPPED killing: racing a live sibling loop is futile and hostile.
  v4 code + e2e state intact, ready to land the moment the port frees.
  Ask: redirect the v3 session off :8140 (8139/8162), then say go.

- `python3 research/papers/validate.py` + `deep/validate_deep.py` green.
- `BASE=http://127.0.0.1:8140 ./site/e2e_check.sh` GREEN incl. §12.
- View-source: carousel cards + JSON-LD ItemList on `/`; ScholarlyArticle
  + canonical + OG on one deep + one shallow `/research/<slug>`.
