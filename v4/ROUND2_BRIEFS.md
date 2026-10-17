# V4 ROUND-2 BRIEFS — model-3d, demo-critic, zone-art (user-ordered, 2026-09-20)

CWD for all: `/Users/sameerhoda/Projects/running_analysis/v4`. Server :8140 (keys live).
Theme lime-on-dark. Taste filter from SHOWCASE_BRIEF.md applies to all visual work.
Coordinate via `.agents/handoffs/`. Watcher (tab-1) audits every finish — nothing is
done until watcher confirms live.

## model-3d → tab V4-model
Goal: best-in-class Tripo 3D mesh. Research developers.tripo3d.ai model types
(v3.1 vs v2.5 vs others, `detailed` vs `standard` geometry/texture, face limits,
orientation flags) + cost per tier. Current lane: fast/standard (~30 credits).
Deliver: (1) model comparison table with quality-per-credit verdict; (2) implement
the upgrade env-gated (TRIPO_MODEL / TRIPO_QUALITY honored, default unchanged
until approved); (3) run max ONE best-tier build to compare mesh side-by-side
with the current demo mesh, report verdict with numbers (faces, texture size,
visual check). Do NOT burn builds sweeping tiers. Handoff: model-3d-core-loop.md.

## demo-critic → tab V4-critic
Goal: direction doc that makes the studio report unmissable. Study ONLY this page
live: http://127.0.0.1:8140/report/02652674ecda (curl + real browser via repo QA
tooling — check site/qa_bot.py, ../v3-tripo-cloud/qa_*.py, playwright if present).
Ground truth I verified: score 72, foot-strike card EXISTS ("Strike & Overstride")
but has no visual callout; coach markers present 7x ("Kabir" spelling — see below).
Deliver `docs/DEMO_DIRECTION.md`: (1) 10–15s dense walkthrough script with a real
hook in the first 2s; (2) model turn/twist choreography synced to script beats;
(3) anti-repetition rotation scheme; (4) coach intro line as "Kabeer" (USER
SPELLING — note everywhere the product says "Kabir" must become "Kabeer");
(5) exact template/script diffs to implement (proposal only — voice-coach and
studio-3d implement after watcher approval). No code edits yet.

## zone-art → tab V4-art
Goal: instructional zone images in the style of the 3 user references (retro
anatomical poster, callout arrows, mid-foot strike / posture / cadence). Tool:
Nano Banana = Gemini gemini-2.5-flash-image (key live in server env; voice-coach
used it for coach-kabir.jpg — ask them for the exact call pattern via handoff).
Scope: 7 zones (feet_strike first). Boundary: showcase-seo owns monochrome PAPER
covers; you own instructional ZONE diagrams — different styles, no duplication.
Deliver: `site/assets/zones/<zone>.jpg` + a style sample FIRST (feet_strike + one
more) posted for watcher review before generating the rest. Photorealistic or
poster style per user refs, lime-on-dark compatible. Handoff: zone-art-showcase.md.
