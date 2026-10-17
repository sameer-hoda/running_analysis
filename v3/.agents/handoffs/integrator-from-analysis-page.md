# DONE — analysis-page → integrator (report_template.html)

Template rewritten, server restarted, verified live.

## What changed (`site/report_template.html` only)
1. **Status vocab**: `poor→critical` (#E0533D kept, `poor` aliased so old JSON still renders). Legend now optimal/fair/critical/needs-view. New `statusColor()` helper with grey fallback — critical zones no longer render unstyled.
2. **Cards**: `tldr` + `observation` + action as 2 cues + 1 drill (`Drill (30s):` when 3+ items, graceful when fewer) + `<details>Why this matters (science)</details>` from `evidence`. Numbered `<span class=kbd>1..n</span>` per card.
3. **Insufficient cards**: `why` + `Needs: needed_view` + `Retake tip: {needed_view} in daylight, full body, 3m away.`
4. **Meta line dynamic**: `{camera_angle} view · {gait_phase} · {n} zones scored + {m} need view` (was hardcoded "Side view").
5. **Markers**: radius 0.01→**0.025**, numbered sprites (canvas-texture 1..n above each dot), keyboard **1-9** jumps to zone.
6. **Compare slider**: `Original-vs-3D` range input overlays `/jobs/<id>/input.jpg` (auto-hides if missing). **Share** (navigator.share → clipboard fallback) + **Print** buttons.
7. **View persistence**: active view saved to `localStorage rf_view`, restored on load.
8. **Canvas 2D fallback**: triggers on (a) THREE/CDN missing, (b) no WebGL, (c) GLTFLoader missing, (d) mesh load fail. Draws stick-figure + numbered zone list; cards/keyboard keep working via `selectLite`.

## Verified
- `curl /` → 200, `/report/demo` → 200 (all 12 feature strings present, no `poor` legend, placeholders replaced)
- `/report/1260dce9ef40` (fresh job) → 200, same checks OK
- `node --check` on extracted script → OK

## Notes for integrator
- No changes outside `site/report_template.html`. No route/template-path changes — regression guard should still pass.
- Zone titles come from JSON verbatim (research titles flow through; template doesn't hardcode them).
- `select()` in 3D path unchanged except marker scale; fallback path uses `selectLite` (no camera refs — safe).

## Update 2026-09-12 (badge copy, brief alignment)
- One-line change: viewport badge `keys 1-9` → `keys 1-5` to match brief (handler already covers 1..n, so 1-5 subset guaranteed).
- Research deck re-audited against template — all items already implemented, no other changes:
  critical #E0533D + poor alias, evidence `<details>`, 2 cues + 1 drill, insufficient why/needed_view/retake tip,
  dynamic `{camera_angle}` meta, markers r=0.025 numbered, slider + persistent views + share/print, Canvas 2D fallback (4 triggers).
- Verified after server restart: `/report/demo` → 200 (badge `keys 1-5` live), fresh cloned job `/report/verify-*` → 200
  (blend/fallback/critical/needs-view/evidence strings present), then removed the verify job dir. No other files touched.
