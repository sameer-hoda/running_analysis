# model-3d → core-loop: Tripo tier verdict + env-gated upgrade (2026-09-20)

Owner of default-quality decision: core-loop (landing/demo). Default is UNCHANGED
(fast/standard). Nothing to wire unless you approve the hero upgrade below.

## 1. Model comparison (developers.tripo3d.ai, image-to-3D H series, verified today)

| Tier | Geometry model | texture_quality / geometry_quality | Faces cap | Price (1cr=$0.01) |
|---|---|---|---|---|
| v3.1-20260211 (current default) | latest, best quality; Ultra OK | standard / standard = base | adapts; game-ready guide 50–100k | 30cr ≈ $0.30 |
| v3.1 + best lane (this eval) | same | detailed (+10 HD tex) / detailed Ultra (+20 HD geo) | 100k (our cap; API allows 1.5M/2M) | **60cr ≈ $0.60 measured** |
| v3.0-20250812 | stable, Ultra OK | same options as v3.1 | 1M / 2M Ultra | same ladder |
| v2.5-20250123 | balanced; NO Ultra, NO texture/geometry_quality params | n/a | 500k | cheaper, worse |
| extreme texture (NOT used) | — | 8K Ultra texture | — | +20 on top (≈70cr with Ultra geo) |

Notes: `orientation=align_image` needs texture:true (free). `enable_image_autofix`
(default false, free, no add-on listed) enhances low-res inputs. `face_limit` and
`pbr:true` show NO add-on charge — see evidence below. Failed/cancelled tasks are
refunded (freeze returned). Docs: `/en/docs/generation-image-to-model/standard`,
`/en/pricing`, `/en/docs/billing`.

## 2. Env-gated upgrade — implemented, default frozen

- `site/tripo_cloud.py`: `lane_settings()` / `describe_lane()` read
  TRIPO_MODEL / TRIPO_QUALITY / TRIPO_FACE_LIMIT **live per build** (was:
  import-time only, so .env changes needed a restart). `create_task(tok,
  model=None, quality=None, face_limit=None)` — explicit args beat env.
  Unknown TRIPO_QUALITY falls back to `fast` (typos never burn credits).
  Fast params and best params byte-identical to before; default still fast.
- `site/server.py` (`tripo_job`): logs `{task_id, model, quality, face_limit}`
  into the `tripo_build` usage event (guarded; serving never depends on it).
- Provenance: throwaway probe `/tmp/model3d_lane_probe.py` — 12/12 green
  (defaults, live env, typo fallback, arg precedence, fast+best param shapes,
  old single-arg call compat). Syntax-checked both files.

To serve hero-grade: `TRIPO_QUALITY=best` in env / `.env`, restart server.
To switch back: unset (default fast). No code change needed either way.

## 3. ONE best-tier build — record + side-by-side

- Task `9b36ec77-70dd-45d6-9089-a7a040924ccc` (v3.1, best, 100k cap),
  input `site/jobs/demo/input.jpg`, plain env-path `create_task(tok)`.
  155s cloud build, **60.0cr consumed** ($0.60). Output (NOT in site/jobs,
  live server untouched): `/tmp/model3d_best/mesh.glb` + `preview.webp`
  (Tripo's own render). Ledger: `tripo_build/model3d-best-eval` in usage.log.

| | current demo mesh | best-tier build (same photo) |
|---|---|---|
| faces / verts | 26,764 / 13,382 | **95,630 / 51,515 (3.57x)** |
| file | 0.70 MB | 3.88 MB (5.5x) |
| material | vertex colors, no texture | **PBR, 4096x4096 base color** |
| normalize check | — | bounds x-centered, feet y=0, height 1.0 OK; not watertight (normal for Tripo humans) |
| visual (Tripo preview render) | — | faithful: capsule runner preserves input pose (stride stance, bent arms); flat-color input so texture detail unresolvable |
| cost | ~30cr (all 3 prior builds: 30.0cr each — `39b3fa9c`, `c2f3ba12`, `ad7e0ebe`) | **60.0cr** |

Calibrating data point (zero extra spend): job `02652674ecda` (real runner
photo, standard-era 30.0cr build) = 99,062 faces, PBR 2048 texture, 3.1 MB.
So the marginal +30cr bought **4K-vs-2K texture + Ultra geometry — not more
faces, not PBR itself** (both lanes hit ~100k faces with PBR).

Update 13:25 UTC (user-approved 2nd build): real-photo A/B DONE. Best-tier
rebuild of `site/jobs/02652674ecda/input.jpg` — task
`4539a598-628c-4745-84ab-8d8b75c3f2a1`, 187s, **60.0cr**, output
`/tmp/model3d_0265best/mesh.glb` (+ Tripo preview alongside). Ledger:
`tripo_build/model3d-0265best-eval` ($0.60).

| same 0265 photo | standard (30cr, existing mesh) | best (60cr, this build) |
|---|---|---|
| faces / verts | 99,062 / 54,151 | 95,182 / 52,491 (~same) |
| file | 3.14 MB | 4.50 MB |
| texture | PBR 2048 | **PBR 4096** |
| Tripo render | softer; shoe ghosting, bib readable | crisper: bib 36536 legible, singlet logos, shoe tread, muscle definition |

Faces confirm the verdict: the +30cr buys texture resolution + Ultra geometry,
NOT polycount. Visible on a real photo, but incremental — standard already
nails identity/kit/pose. Default stays fast; best for hero/demo only.

DECISION (user, 2026-09-20): main site stays on the 30cr fast lane. Verified
live :8140 (pid 34241) env carries NO TRIPO_QUALITY (= fast default) with
TRIPO_MODEL=v3.1 + TRIPO_FACE_LIMIT=100000 (cap only, still 30cr/build) — no
code or restart needed, nothing to flip. `site/jobs/0265best/` remains as a
static side-by-side reference page only; it never enters the upload pipeline.

## 4. Verdict (quality-per-credit)

- Best lane = exactly 2x credits (60 vs 30) for 4K PBR texture + Ultra geometry
  + autofix + align_image. Worth it for hero/demo imagery, NOT for every user
  build while the heat shell carries diagnosis visuals.
- **Recommendation: keep `fast` default; approve `best` only for curated
  hero/demo photos (or per-job opt-in later).** `extreme` 8K never worth it.
- Cheap follow-up worth one 30cr test (proposal only, NOT implemented):
  fast lane with `pbr:true` + higher `face_limit` may cost the same 30cr
  (0265 evidence) — would enrich default meshes for free if confirmed.
- Watch: shared balance fell 870 → 630 with 180 frozen during this session
  (other agents building). Coordinate spend; my total burn = 60cr, logged.

## 5. Regression

Live :8140 untouched (outputs went to /tmp). Read-only checks after my edit:
landing 200, `/report/demo` 200. Full e2e deliberately NOT run (it POSTs a real
job = burns ~30cr + minutes). server.py + tripo_cloud.py syntax + lane probe green.
