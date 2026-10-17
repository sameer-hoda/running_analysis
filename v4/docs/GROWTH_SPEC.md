# Growth spec — history, 15-cap + paywall, IG share (growth-memory)

Owner: growth-memory. Scope: ONLY `v4`. Status: spec + flagged implementation.

## 1. Goals
- Repeat loop: per-user history so runners come back and re-test.
- Cap: 15 free analyses per user, then a `mailto:EMAIL_REMOVED` unlock (no payments infra yet).
- Growth loop: Instagram-ready share output + friend sharing, WITHOUT breaking the existing
  tracked share (`/s/<job>` → 302 to `/report/<job>` + `clicks.jsonl`, stats at `/api/links/<job>`).
- Privacy-first: no accounts, no emails stored. Guest cookie only. Retention documented.

## 2. Definitions
- **User** = one `rf_guest` cookie token (random 16 bytes, `HttpOnly`, server-side `SESSIONS` set).
  No login, no email, no cross-device identity. Cookie loss = history loss (documented, accepted).
- **Analysis** = one `POST /api/jobs` upload that passes validation and gets a job id.
  The `demo` job never counts.
- **Cap** = `RF_MAX_ANALYSES` (default **15**). The 16th upload is refused with a paywall.
- **Unlock** = `mailto:EMAIL_REMOVED?subject=RunForm%20unlock` link (override `RF_PAYWALL_MAILTO`).
- **Share (existing, frozen)**: `SHARE_URL = origin + "/s/" + job`. `GET /s/<job>` appends one JSON line
  to `site/jobs/<job>/clicks.jsonl` and 303-redirects to `/report/<job>`. `GET /api/links/<job>`
  returns `{"job","clicks","last","short":"/s/<job>"}`. No changes to either route.

## 3. History
- Store: server-side map token → `[{job, ts, filename}]`, persisted best-effort to
  `site/history.json` (override `RF_HISTORY_PATH`). Never raises; serving never depends on it.
- Write: on each counted upload (after validation, before pipeline enqueue).
- Read: `GET /api/history` (session cookie required) returns
  `{"analyses":[{job,score,stage,ts,filename}],"used":N,"remaining":M,"cap":15,
    "unlock":"mailto:..."}`. Scores/stages resolved live from `status.json` (history file
  stores no scores, so it can't go stale).
- Page: `GET /history` (login-gated like `/upload`) lists own runs, remaining count,
  paywall CTA when capped, privacy note, per-run delete buttons.
- Pruning: entries whose job dirs vanished are hidden (and compacted on write).
- Ledger: `history_view` event on `/api/history` + `/history` hits (free kind).

## 4. Cap + paywall
- Check placement: `POST /api/jobs`, after image validation, before job creation.
  Count = number of history entries for the resolved session token (existing cookie token if
  valid, else the newly minted token — a brand-new user always has count 0).
- Over cap → refuse, create nothing, log `cap_hit`:
  - JSON clients (default): `402 {"error":"analysis cap reached (15 free analyses)",
    "used":15,"cap":15,"unlock":"mailto:EMAIL_REMOVED?subject=..."}`
  - HTML form clients (`Accept: text/html`): `402` paywall page with a big mailto CTA,
    history link, privacy note. Same unlock address.
- Under cap → upload proceeds exactly as before (same cookies, same redirect/JSON).
- Demo, health, report views, `/s/` clicks never count and never check the cap.
- Ledger: `cap_hit` on every refusal (free kind).

## 5. Reel export — ONE button (replaces the old image-plus-caption flow, `/s/` untouched)
- Report page: a single **Export as Instagram post** button. It downloads one
  `1080×1920` MP4 reel (walkthrough video + Kabir voiceover + captions + score
  card) and copies the caption text. The old **IG card** + **Copy IG caption**
  buttons and the `GET /share-card/<job>` PNG route are removed. The existing
  `shareBtn` handler (Web Share API → clipboard → plain text) is unchanged.
- `GET /api/share/<job>` (kept) → `{"job","short":"/s/<job>","caption":"..."}`.
  Caption = score + one-line summary + short link + 3 hashtags (`#runningform #runform #running`).
  Public (no session needed — same visibility as the report itself). Ledger: `share_meta`.
- `GET /reel/<job>` → `video/mp4`, composed on demand by `site/reel.py` (stdlib +
  PIL + ffmpeg, no libass/drawtext) and cached as `site/jobs/<job>/reel.mp4` +
  `reel.json` (freshness = `analysis.json` mtime + voice availability). Timeline is
  deterministic: 3s intro + up to 3 × 5s zone segments + 3s outro. Ken Burns over
  the run photo, PIL score pill + caption cards, per-segment voiceover.
  Public. Ledger: `reel_export` with `{voice, dur}`.
- Voiceover: live TTS via `inworld_tts` (voice Kabir) attempted per segment at
  compose time; any failure — including no `INWORLD_KEY` configured — falls back
  to silence for that segment. Zero paid calls without a key. Voice activates
  automatically when a key appears (cache key includes voice availability).
- `site/make_showcase.py` (browser-recorded landing teaser) repointed to v4 +
  port 8140 + Kabir; unchanged capture/mux logic.
- Friend sharing stays exactly the `/s/` link (redirect + click tracking).

## 6. Privacy + retention
- Stored per user: random token + own job ids/filenames/timestamps. No names, emails, IPs.
  `clicks.jsonl` keeps existing fields (t/ref/ua/lang) — unchanged.
- `DELETE /api/jobs/<job>` (session required): deletes the job dir only if the job is in the
  caller's history (demo can never be deleted). Removes the history entry. Ledger: `job_delete`.
- Retention: `RF_RETENTION_DAYS` default **90**. Documented target: inputs + derived files for
  jobs older than 90 days may be purged (demo exempt). No automatic purge in this cut —
  spec only; the delete route + pruning above are the enforcement primitives.
- Upload/landing copy keeps saying "No account needed" (history page adds the one-line
  cookie explanation).

## 7. Flags (all additive, safe defaults)
- `RF_ENABLE_GROWTH=1` — master switch. `0` disables history/cap/IG/delete routes
  (each returns 404 `{"error":"growth disabled"}`); `/s/` + `/api/links/` keep working.
- `RF_MAX_ANALYSES=15` — cap size. `0` = unlimited (cap check skipped).
- `RF_PAYWALL_MAILTO=EMAIL_REMOVED` — unlock address.
- `RF_RETENTION_DAYS=90` — documented retention window (spec only in this cut).
- `RF_HISTORY_PATH` — history file override (tests use a temp path).

## 8. Edge cases
- No/invalid cookie on `POST /api/jobs` → brand-new token, count 0, proceeds (unchanged behavior).
- Corrupt `history.json` → treated as empty, rewritten on next write. Oversized filenames truncated.
- `demo` excluded from history, cap, delete. Unknown job ids → same 404s as before.
- Growth routes never import optional deps at module load (PIL usage lazily inside the card
  renderer, like `sanitize_upload`).

## 9. Verification
- `python3 - <<EOF` growth selftest (cap counting, paywall 402 + mailto, history round-trip,
  `/s/` redirect + click log intact, `/api/links/` shape intact) — see handoff note.
- `BASE=http://127.0.0.1:8140 ./site/e2e_check.sh` stays GREEN (existing 19 checks untouched).
- Manual once: open `/history`, upload to cap with `RF_MAX_ANALYSES=2`, confirm mailto CTA;
  download one IG card; copy one caption.
