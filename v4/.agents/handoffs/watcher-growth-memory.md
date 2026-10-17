# Handoff: growth-memory → watcher (relay to all)

## Done (v4 only)
Spec + flagged implementation of history / 15-cap + mailto paywall / IG share.
`docs/GROWTH_SPEC.md` is the contract; all behavior behind `RF_ENABLE_GROWTH` (default 1).

## Files touched (all additive except where noted)
- `site/server.py` — growth block (~top: helpers; GET routes after `/api/links/`;
  cap check + history write inside `POST /api/jobs`; new `do_DELETE`).
  NOTE: pipeline-auth is editing this file concurrently (their `session_token`/
  `owner_hash` refactor is now in). My code reuses their `tok` variable in the
  upload handler and does not touch their helpers. Merge carefully if you rebase.
- `site/report_template.html` — two buttons (`igCardBtn`, `igCapBtn`) + handlers.
  `shareBtn` handler byte-identical; `SHARE_URL` (`/s/<job>`) unchanged.
- `site/growth_check.sh` (new, committed) — 15 checks on an isolated port with
  `RF_HISTORY_PATH` in /tmp; cleans up its own jobs.
- `docs/GROWTH_SPEC.md` (new) — full contract.

## New routes (all 404 `growth disabled` when `RF_ENABLE_GROWTH=0`)
- `GET /api/history`, `GET /history` (session-gated)
- `GET /api/share/<job>`, `GET /share-card/<job>.png` (public, like reports)
- `DELETE /api/jobs/<job>` (own history only; demo never deletable)
- Cap: `POST /api/jobs` → 402 + `mailto:EMAIL_REMOVED?subject=RunForm%20unlock`
  (JSON by default, HTML paywall page for form clients) once history length ≥
  `RF_MAX_ANALYSES` (default 15, 0 = unlimited).

## Frozen (verified, do not change)
- `GET /s/<job>` → 303 to `/report/<job>` + `clicks.jsonl` append (unchanged code path).
- `GET /api/links/<job>` → `{job,clicks,last,short}` (unchanged code path).

## Verification observed
- `GROWTH GREEN` (15/15) on isolated :8142; unit probe for capped history page
  (incl. `%`-in-filename), paywall tokens, caption, PNG magic.
- `E2E GREEN` (19/19) vs live :8140 — pre-existing surface unbroken.
- Two real bugs caught by probes, both fixed: HTML paywall crashed on `%20` inside
  `%`-formatting (CSS has literal `%`, so paywall uses token replacement); a
  misapplied `%`-escape helper corrupted values (removed — values are safe).

## For other agents
- core-loop: you may link `/history` from landing/upload when ready; route exists.
- studio-3d / voice-coach: IG buttons live in the report header; style via `.ibtn`.
- No action needed; just don't alter `/s/` or `/api/links/` semantics.

## Post-cutover verification (merge handoff `pipeline-growth-core-loop.md`, 2026-09-20)
- Freeze honored: no `server.py` edits while blocked; post-merge inspection shows
  the rebase was unnecessary — growth block (helpers, cap + history write in
  `POST /api/jobs`, all growth routes, `do_DELETE`) is present and intact in the
  merged 1919-line file (`py_compile` clean, 23 growth-marker refs). Zero edits made.
- `report_template.html` retains both IG buttons + handlers; `shareBtn` unchanged.
- Live :8140 probed directly: landing 200, `/api/history` anon 401, `/api/share/demo`
  caption JSON correct, `/share-card/demo` 200.
- `GROWTH GREEN` 15/15 (isolated :8142, merged on-disk code). `E2E GREEN` on live
  :8140 (all checks incl. voice-coach additions). No failures — nothing to fix.
- Tree left clean: growth-check temp jobs deleted; `site/jobs/` holds only demo
  plus other agents' live test jobs (untouched).

## REEL-EXPORT (user order, 2026-09-20) — separate-image-plus-caption flow killed
- ONE button **Export as Instagram post** on the report → single `1080×1920` MP4
  reel (Ken Burns walkthrough + Kabir voiceover + caption cards + score pill) +
  caption text. Old `igCardBtn`/`igCapBtn` buttons, `/share-card/` route, and
  `_ig_card_png` helper removed (no references remain); `/api/share/` caption
  kept; `shareBtn` + `/s/` + `/api/links/` untouched.
- New `site/reel.py`: deterministic timeline (3s + ≤3×5s + 3s), PIL overlays
  (no libass/drawtext), TTS attempted live per segment with per-segment silence
  fallback — zero paid calls without a key (none configured in this env).
  `reel.py --selftest` = stub compose proof (1080×1920, aac, cache-fresh).
- `site/make_showcase.py` repointed to v4 (paths from `__file__`,
  default URL :8140) + Kabir; capture/mux logic unchanged.
- Server `GET /reel/<job>`: on-demand compose, cached (`reel.mp4` + `reel.json`,
  freshness = analysis mtime + voice flag), `reel_export` ledger event.
- Verified: stub selftest GREEN → one real compose over HTTP (`/reel/demo`,
  1080×1920/aac/0s cached 2nd hit, unknown-job 404) → `GROWTH GREEN` 18/18 →
  `E2E GREEN` on isolated new-code instance. `node --check` on the new handler OK.
  Demo fixture left clean (gate removes composed reel artifacts); own e2e job
  removed; others' job dirs untouched.
- Note: live :8140 still runs pre-reel code (session-managed, no setsid daemon)
  — needs a restart (`python3 site/server.py 8140` from v4 root) to serve `/reel/`.
  Voiceover is silent until an `INWORLD_KEY` is configured; activates automatically.
