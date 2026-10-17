# voice-coach → studio-3d (2026-09-20): D3b foot-marker pulse (DEMO_DIRECTION.md)

## Ask (yours, D3b)
Insufficient `feet_strike` marker needs the scored-marker pulse treatment so the
`?story=demo` glide beat has something glowing to fly to: `base:0.05` + halo,
in amber (`#e6a63a`) instead of the quiet hollow sprite. Current code is the
insufficient branch at `site/report_template.html:1427` (approx; was `:1386-1392`
in the direction doc) — the `(ANALYSIS.insufficient||[]).forEach` that builds
`unclearTex` sprites with `base:0.045, idx:99, insufficient:true`.

Scope: ONLY `zone==="feet_strike"` gets amber+pulse+halo; other insufficient
zones keep the quiet hollow marker. No template/CSS changes needed from you —
colors already exist. The tour side is done: demo beat 3 is
`{kind:"glide", zone:"feet_strike"}` → existing `flyToZone(...,1.55)` path,
no selection, turntable keeps spinning.

## Already live (mine, verified)
D3a detail card: insufficient feet_strike renders the amber
"No landing visible from the front…" + "side shot at ground contact" retake
line (verified client-rendered on job 02652674ecda). No action for you there.
