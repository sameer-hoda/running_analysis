# Strava approval — gap tracker (code side, verified 2026-10-17)

All gaps from the Strava review audit are closed in `v6/`. Verified locally:
`python3 v6/server.py --self-test` (12/12), `python3 v6/update_engine.py
--self-test` (93 passed), HTTP smoke probe `/tmp/mnp-smoke.py` (16/16).
Live EC2 redeploy is the one remaining step (see bottom).

## Closed gaps

- [x] Per-athlete token store — `server.py`: `.athletes/{id}.json`, cookie
  `mnp_athlete`, legacy `.tokens.json` auto-migrates on first read.
- [x] Per-athlete isolation — status/pause/resume/stamp/export/delete resolve
  the caller from the cookie; webhook routes by `owner_id`; poller iterates
  all athletes; a foreign cookie sees `connected: false` (probed).
- [x] Revocation handling — Strava athlete webhooks delete that athlete's file;
  Disconnect and `/api/delete-account` revoke remotely then wipe locally.
- [x] Minimal scopes locked — `read, activity:read, activity:write` in
  `server.py` (`MINIMAL_SCOPES`), `update_engine.py` (`SCOPES` + self-test),
  `strava.js` default, `strava-config.example.js`, and every consent line
  (`index`, `connect`, `picker`, `hero`).
- [x] Consent text — `connect.html`/`picker.html` state data types, Strava-side
  approval, description-only writes, and links to Privacy/Terms/Support.
- [x] Privacy page — `v6/privacy.html`: data list, collection method,
  purpose limit, withdrawal, deletion (`#delete`), export, security, Strava
  policy reference.
- [x] Terms page — `v6/terms.html`: description, user duties, Strava
  relationship + no-endorsement, free use, stop/delete, as-is.
- [x] Support page — `v6/support.html`: `support@mynextpr.com`, self-help
  checklist, export/delete instructions, privacy/security reporting.
  **Action for owner: create the `support@mynextpr.com` mailbox.**
- [x] User data export — `GET /api/export` (tokens never included) + a
  Download button on `manage.html`.
- [x] Delete account — `POST /api/delete-account` + a Delete button with
  confirm on `manage.html`.
- [x] Branding — text “Connect with Strava” buttons link to the official
  OAuth authorize endpoint; “Compatible with Strava / not endorsed” labels
  kept; “View on Strava — connected apps” link on `manage.html`; no Strava
  logo, name, or icon use anywhere.
- [x] API hygiene — JSON responses marked `no-store`; tokens never logged,
  served, or exported; `.athletes/` added to `.gitignore`.
- [x] Maintained tests — `server.py --self-test` (isolation, cookies,
  revocation, scope lock) alongside the existing engine self-test.

## Still yours (not code)

1. Create the `support@mynextpr.com` mailbox (referenced by support page).
2. Redeploy to EC2 (standard steps in `deploy/mynextpr-ec2.md`).
3. Take screenshots of every screen showing Strava data + the Connect button,
   plus a short OAuth video.
4. Fill the review form + send the approval email (draft already with you).
