# studio-3d → voice-coach + pipeline-auth (2026-09-20, demo-fixed + real-image tested)

## What changed (v4 only, E2E GREEN)
- `site/report_template.html`: status-colored markers/rail/tip/diagrams +
  `zoneStatus` fallback; `ZONE_KB.feet_strike` split into `coach` (scored,
  heel-vs-proper) + `coach_unclear` (mid-flight); detail contact badge +
  diagram strike labels + braking arrow. Backward compatible.
- `step1_prompt.txt`: scored feet_strike requests `strike_type` +
  `overstride`; rearfoot alone ≠ critical.
- `renderer3d.js` foot zone carries the new fields. `node --check` clean.
- `site/jobs/demo/`:Statuses added to all findings; feet = rearfoot +
  overstride (fair 62). Stub files kept at `/tmp/stub_triangle.glb`,
  `/tmp/stub_anchors.json`.

## Demo triangle fixed (user-visible)
- Root cause: `site/jobs/demo/mesh.glb` was a 604-byte single-triangle stub.
- Fix (copy only, v3 untouched): real 697KB runner mesh + full 7-zone
  anchors from v3-tripo-cloud demo seed it. Live proof: `/jobs/demo/mesh.glb`
  → 200, 697144 bytes; `/report/demo` serves all 7 anchors. Open it and drag
  to spin a real runner with amber markers.

## Real running-image tests (actual photos, Gemini audit)
- Beach side-runner → side/swing/no-contact: feet_strike→insufficient with
  `needed_view`, NO fabricated strike fields. Guards hold.
  Report: `/report/67fdf9cc0297` (scores 73, public link).
- Second photo → front/stance: feet insufficient per matrix (front can't judge
  overstride). Guards hold again. Report: `/report/1c5b0c5b9ba6`.
- Shipped-function harness (`/tmp/make_harness.py` + `/tmp/run_harness.js`,
  scratch): extracted the merged template's real `diagram()`/`coachLine()` and
  ran them on live demo data — HEEL label present, braking arrow present,
  YOURS figure amber, unclear path + unclear coach line correct.
- Full `site/e2e_check.sh`: GREEN (incl. merged voice-coach checks).

## Known limit (not mine — pipeline-auth/core-loop)
- Both real jobs end `failed` on 3D: `TRIPO_API_KEY is missing in .env`, so no
  per-photo mesh. Scores/cards/diagrams all render; mesh streams in once the
  key lands. TTS voice is Kabir (merged, untouched by me).

## For voice-coach / pipeline-auth
- No action. Tour focus step for scored feet uses the new `coach` line;
  your Kabeer blocks verified intact in the merged file.

## FOOT-STRIKE CALLOUT (live on /report/02652674ecda, score 72)
- Diagnosis: feet is INSUFFICIENT there (front angle; contact undetermined),
  anchor present, 3.1MB mesh done — but the only marker was a halo-less grey
  dash that reads as nothing, and no hero presence. Fixed in template only
  (no restart needed, served per-request):
- `strikeCallout` hero strip in the scorecard (new `.strike` style, existing
  palette): scored → status dot + contact label; insufficient → honest
  "Not visible from this angle · retake: <needed_view>" + tap opens the
  Strike detail card. Rendered from `renderRail()` via `renderStrike()`.
- Insufficient markers now get the same additive halo treatment as scored
  ones (grey), so the foot orb glows on hover/select instead of vanishing.
- Proof: shipped `diagram()`/`coachLine()`/`renderStrike()` executed in node
  against the report's LIVE data — insufficient callout with retake text ✓,
  scored variant (rearfoot+overstride) red "Heel · ahead of hips" ✓; live page
  contains strikeCallout/renderStrike/strikeContact; demo mesh still 200.
- e2e scope note: all 25 studio/auth/demo/coach lines GREEN (incl. Tripo
  `meshing` — key is wired). The 24 RED lines are all research-catalog's new
  checks (carousel/covers//research//sitemap, server.py + research/papers) —
  files I never touch; leaving them to that lane, not masking with edits.

## D3 (DEMO_DIRECTION.md, watcher-assigned — implemented, no VC dependency)
- D3 is independent of voice-coach branch scaffolding (D1/D2/D4/D5 tour work):
  detail strip + marker only. Kabeer spelling untouched (theirs).
- (a) `detailHTML()` insufficient-feet: amber `.sh-test` strip "No landing
  visible from the front. Send a side shot at ground contact." (front-aware;
  "in this photo" otherwise) + existing needed_view retake line; grey
  "can't assess yet" pill kept for honesty.
- (b) Insufficient `feet_strike` marker: solid amber `markerTex` orb, base
  0.05 + amber additive halo (scored pulse treatment); other insufficient
  zones keep the quiet hollow grey. Hero `strikeCallout` dot amber for
  insufficient feet to match.
- Proof: shipped fns executed in node on live 02652674ecda data — strip,
  amber, retake, honest pill, amber hero callout all present; live page
  serves the strings; syntax clean; e2e studio lines all green (4 "detail
  marker" FAILs are research JSON-LD, not 3D markers — verified by name).
- Screenshot check BLOCKED by environment: no chromium, no Chrome app, no
  Playwright browser cache, installs forbidden — so the amber pulse was
  proven at function/DOM level (exact hero + card HTML printed from shipped
  code on live data) but never eyeballed in a real browser frame. Ask a
  machine with Chrome to open /report/02652674ecda, tap the Foot strike
  strip, and watch the foot orb across 2–3 pulse frames before calling D3
  visually closed.

## ANALYSIS-TRUTH (user orders — done, full e2e 58ok/0 FAIL)
- AUDIT (traced live on 02652674ecda): Gemini honest (front→feet
  insufficient, no fabricated strike fields); rail renders feet dim/buried;
  THE DROP was 3D+hero absence for insufficient feet (silent anchor skip +
  halo-less dash + no tour beat — tour beat is voice-coach D4, flagged not
  taken). strikeCallout+D3 closed hero+marker; tour gap remains theirs.
- Board rethink: every zone card now opens with the runner's own photo
  (`input.jpg` derived from MESH, self-hiding on 404) captioned "every call
  on this card is read from it, not the model"; insufficient copy changed to
  "the model only illustrates; your photo decides."
- Research rail below the model (`#sciWrap`, CSS scroll-snap pattern per
  W3C carousel explainer): fetches live catalog, picks feet-first + 3 worst
  zones, max 6 papers with thumbs/bylines/findings + PubMed "Read study ›";
  lead block carries the read line. Fail-closed hidden. Monochrome+lime,
  hairline rows (not cards), no lifts/emoji/animation.
- Durable: e2e §8b2 asserts strikeCallout/sh-fig photo/sciRail/renderSci.
  Harness (/tmp/make_harness4.py) runs shipped fns on live data: weak zones,
  photo figs, rail content + escaping all proven. Style filter honored.

## TRIPO_KEY wiring finding (for core-loop — needs YOUR restart, not mine)
- Key exists: `TRIPO_API_KEY` (+MODEL/FACE_LIMIT) live in
  `v3-tripo-cloud/.env`. `v3/.env` has none. No `v4/.env` exists.
- Server reads it once at import: env `TRIPO_API_KEY` first, else
  `<RUNFORM_ROOT>/.env` ([server.py](/Users/sameerhoda/Projects/running_analysis/v4/site/server.py:96)).
  Live :8140 (PID 19105, core-loop owned) started without it → every 3D
  build fails `TRIPO_API_KEY is missing in .env`; my two real-image audits
  scored fine (Gemini path works) but produced no mesh, and both job dirs
  have since been cleaned — that is why the beach report link now 404s.
- Fix: create `v4/.env` with the Tripo line (copy from v3-tripo-cloud, never
  commit secrets) and restart :8140. Per guard I did NOT restart or upload;
  standing down. Verified read-only this turn: landing 200, demo 200 with
  real 697KB mesh live, beach report 404 (job cleaned).
