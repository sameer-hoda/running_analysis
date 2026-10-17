# 3. Architecture

## Backend (`v6/server.py`, stdlib only)

| Route | Purpose |
|---|---|
| `GET /exchange_token` | OAuth code swap, per-athlete store, cookie, redirect |
| `GET /api/status` | Connection, race, goal, live month/year totals |
| `GET /api/export` | Everything stored about this athlete (tokens excluded) |
| `POST /api/pause`, `/api/resume` | Per-athlete stamping toggle |
| `POST /api/disconnect`, `/api/delete-account` | Revoke remotely, wipe locally |
| `POST /api/stamp-latest[?dry=1]` | Stamp newest run now (dry previews) |
| `GET /webhook` | Strava subscription verification |
| `POST /webhook` | Activity create/update → stamp; athlete events → purge |
| `POST /api/subscribe` | One-time webhook subscription setup |

JSON API responses are `no-store`. Tokens are never logged, served, or exported.

## Per-athlete store

One file per athlete: `v6/.athletes/{athlete_id}.json` (tokens, race, pause flag, stamped IDs). Callers resolve via the `mnp_athlete` cookie; a lone athlete is the fallback. The old single `.tokens.json` migrates itself on first read. Webhooks route by `owner_id`; the poller iterates all athletes every few minutes as backup. Activity content is never retained beyond the stamped-ID list.

## Frontend pages

- `index.html` — landing. `picker.html` — race search. `connect.html` — consent + connect.
- `manage.html` — pause toggle, connection, Download/Delete my data, View-on-Strava link.
- `privacy.html`, `terms.html`, `support.html` — public policy pages, linked from every footer.
- `strava.js` + `strava-config.js` — authorize-URL builder (client ID and redirect only; secret stays server-side).

## Engine (`v6/update_engine.py`)

Pure-stdlib countdown composer: description-only, title never read or written (pinned by self-test), minimal scopes pinned by self-test. Tests: `python3 v6/server.py --self-test`, `python3 v6/update_engine.py --self-test`.
