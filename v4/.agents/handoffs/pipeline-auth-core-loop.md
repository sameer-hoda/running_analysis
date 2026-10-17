# Handoff: core-loop → pipeline-auth (upload contract, 2026-09-20)

Landing + upload audit done. `python3 site/server.py 8140` serves landing 200,
`./site/e2e_check.sh` E2E GREEN (19/19) against 127.0.0.1:8140, fully v4-local.

## What core-loop changed (v4 only, no v3 touched)
- `site/server.py`: root now resolves to v4 checkout (`V4_ROOT`, `RUNFORM_ROOT`
  override kept); was hardcoded to `/Users/.../v3-tripo-cloud`. `seed_demo()`
  loads committed `site/jobs/demo/` fixture instead of copying `output/*` bulk.
- New lean fixtures (authored, ~50K): `reference/input/images-{3,4,5}.jpeg`,
  `site/jobs/demo/{analysis.json(69),anchors.json,mesh.glb(stub triangle),status.json,input.jpg}`.
- `site/e2e_check.sh`: `BASE` default 8138 → 8140.

## Upload contract (yours from here)
- `POST /api/jobs` multipart `photo` → JSON `{"job_id": <12hex>}`, or 303
  `/job/<id>` when `Accept: text/html`. Auto-issues `rf_guest` cookie if none.
- Limits: 8MB max, JPEG/PNG/WebP magic-byte sniff, PIL verify + EXIF + downscale
  → `site/jobs/<id>/input.jpg`. Errors: 400 empty/too-large/no-image/bad-size/invalid.
- Lifecycle: `set_status queued → enqueue_pipeline` (serial worker, 600s timeout).
  Poll `GET /api/jobs/<id>` stages: queued/analyzing/meshing/done/failed.
  Loader page `GET /job/<id>` (authed, 303→/login without cookie).
- Guest sessions live in server memory only (vanish on restart) — your guest→auth bridge.

## Gaps core-loop did NOT fix (your call / studio / growth)
- Proof media 404 in v4: `logo.png`, `hero-run.mp4`, `showcase.mp4`+poster,
  `og-image.jpg`, favicons. Tags render, files absent → proof section is a black
  box. Decide: copy from v3 (~2.6MB) or regenerate lean.
- Stale privacy copy on `/upload`: "never leaves this machine except Gemini audit"
  — Tripo cloud upload also exfiltrates. Needs rewrite (privacy-first everywhere).
- Science-backed rail on landing = FAQ + guide links only; loading-page paper
  carousel is yours per roster (research-catalog schema first).
- Realtime check used session-managed server (macOS, no setsid): green in-session,
  not a post-session daemon. Restart with `python3 site/server.py 8140`.
