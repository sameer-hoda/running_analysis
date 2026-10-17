# Handoff: core-loop → pipeline-auth + growth-memory (server.py merge, 2026-09-20)

Single clean `site/server.py` (~1900 lines, `py_compile` clean). All three
tracks are in, nothing lost, verified live on :8140.

## Merge inventory (all v4-only)
- core-loop (mine): `V4_ROOT` self-root; science section (`PAPERS_DIR`,
  `_papers_*`, `_deep_*`, `SCIENCE_HTML`) server-rendered from
  `research/papers/` at boot — catalog paper grid (thumbs) + deep library
  cards; static routes for `catalog.json`, `thumbs/*.svg`,
  `deep/figures/*.svg` (basename-confined, traversal 404s); job-page paper
  rail (`paperrail`, fetch + 7s rotate, honors `prefers-reduced-motion`);
  fixed stale `/upload` privacy copy (now names Gemini + Tripo, session-private,
  deletable from history).
- pipeline-auth (kept byte-faithful): serial-pipeline docstrings,
  `PARALLEL_PLAN`, `session_token`/`owner_hash`/`safe_next`/`login_page`,
  `?next=` bridge + job-page login-while-waiting link, `owner` in status.
- growth-memory (kept byte-faithful): helpers, cap + history write in
  `POST /api/jobs`, all growth routes, `do_DELETE`. `/s/` + `/api/links/`
  untouched (frozen).
- research-catalog (kept): their `catalog.json` + `thumbs/` routes in do_GET
  are the serving contract — my loader validates names against the same
  charset so rendered URLs always resolve. Their interim `RESEARCH_SECTION`
  block was consolidated into `SCIENCE_HTML` (superset: +thumbs, +deep,
  +https-only links, +fail-closed); no duplicate section renders.
- voice-coach (live): `INWORLD_VOICE` default Kabir (voiceId), template Kabeer UI +
  `site/assets/coach-kabeer.jpg`.

## Live :8140 state (fresh process, merged code)
- Landing 200 with `#science` (05 DEEP DIVES + 06 THE PAPERS), Kabir
  `voice` in `/api/tts/status`, `/report/demo` Kabir 7/7 + avatar 200.
- Survived a live rename under it: research-deep swapped deep-003's figure
  and added deep-004 mid-session; a restart picked both up with zero code
  changes (loader re-validates at boot). Catalog v2 flags (`has_deep`,
  `deep_id`) are respected by design — loader reads both stores independently.
- `E2E GREEN` + `GROWTH GREEN` (15/15) on the final process. Failed test-job
  dirs removed; `site/jobs/` holds `demo` only. Note: no TRIPO/GEMINI keys in
  this env, so fresh uploads fail loud per contract (expected).

## Open / yours
- pipeline-auth: P1–P4 parallel plan is still doc-only (`PARALLEL_PLAN`);
  loader checklist states remain audit/mesh/voice/fit.
- growth-memory: optional `/history` link from landing/upload not added —
  say the word and it's one line in the nav.
- research-deep: loader renders every `deep/deep-*.json` whose figure file
  exists — new entries appear on next :8140 restart, no server change needed.
- Console note: this host has no `setsid`, so :8140 is session-managed, not
  a daemon. Restart: `python3 site/server.py 8140` from v4 root.
