# Next work — 3 items (scoped, not started)

Date: 2026-09-12. Site live at https://mynextpr.com (sandbox `v3-tripo-cloud`, :8139).

## 1. Homepage teaser video quality
- Current: `site/assets/showcase.mp4` (Kabir voice, 12.7s, 1000px, crf 20, 1.6MB).
- Levers: record at 1440px, crf 16-18, `preset slow`; sharper mux (no atempo change); check Tripo texture detail upstream.
- Accept: side-by-side frames old-vs-new, no audio drift, file stays streamable (<4MB).
- Note: each re-record costs 3 Inworld TTS calls (teaser story).

## 2. Loader deep-dive (parallelism + rich progress UI)
- Current: `run_pipeline()` already overlaps Gemini audit + Tripo cloud gen (threads);
  loader shows `Cloud 3D build NN%` → bar `30 + p*0.65`. Serial tail: download →
  normalize (0.7s) → anchors → done. Worker timeout 600s, single-job queue.
- Candidate parallel wins: pre-warm TTS voice lines during meshing (server-side mp3s
  into job dir, cacheable GET — kills first-tap voice latency); stream Gemini
  partials (score first, zones as they arrive); parallelize anchors per-zone.
- UI ask: more than a percent — a task checklist component (audit ✓ / mesh % /
  voice / fit), animated, honest states. **Waiting on user's UI component link**
  before designing.
- Accept: measured wall-time table before/after (same photo, fast lane), zero
  regressions in fail-loud paths (no key / cloud error / no-runner).

## 3. Studio mobile layout (captions + tray)
- Current: `#cap` bottom line + `#tourCtl` stack; last verified desktop-only.
- Task: load `/report/demo` (and a textured job, e.g. `9e1557b6bf38`) at 390×844
  (+ landscape), screenshot caption/tray/view-buttons/legend overlap; fix
  collisions, tap-target sizes (≥44px), caption max-width vs tray.
- Accept: screenshot set portrait + landscape, zero console errors, tour fully
  operable by thumb (play/next/stop/views).
