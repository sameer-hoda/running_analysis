# Handoff: zone-art → showcase/core-loop (all 7 zone diagrams DONE, 2026-09-20)

## Deliverable
`site/assets/zones/<zone>.jpg` — all 7, 600×800 JPEG, retro anatomical
poster style (off-white clothed figure, singlet+shorts, lime callouts on
near-black). Generator committed: `site/assets/zones/make_zones.py`
(`--check` / `--only <zone>`), same `gemini-2.5-flash-image` call pattern
as voice-coach's coach-kabir.jpg and showcase-seo's `make_covers.py`.

| zone | bytes | notes |
|---|---|---|
| feet_strike | 39879 | watcher: "superb" |
| trunk_lean | 75545 | hex leak regenned clean; faint corner speck painted out (PIL, bg-median fill, verified invisible) |
| knees | 58757 | clothed, clean |
| hips_pelvis | 82450 | C3FQ4 leak regenned clean ("LEVEL HIPS" appears twice — minor) |
| head_neck | 75166 | clean |
| shoulders | 116510 | typo+logo regen clean; #02CC11 corner speck painted out, verified invisible |
| arms_elbows | 80324 | "90 DEGRES" typo regenned clean; has thin light poster frame baked in |

## Boundary kept
showcase-seo owns monochrome PAPER covers in `research/papers/covers/`;
these are instructional ZONE diagrams, different style, no duplication.

## For the integrator (core-loop / studio-3d)
- No route serves `/assets/zones/` yet — wire it like the existing
  `/assets/coach-kabir.jpg` static route when the report needs them, or
  say the word and I'll add it.
- Watcher verdict: set APPROVED. Standing down; no further generation
  planned.
