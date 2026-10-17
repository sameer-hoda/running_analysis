# v6 QA Score — Lane 07 full functional pass (2026-10-10)

Method: test-master happy-path + edge-case pass in a real browser
(`agent-browser` 0.39.0, desktop Chromium, named session) over local HTTP
(`python3 -m http.server 8907` in `v6/`), no real Strava calls — every
networked surface is mock by design. All six pages (`index`, `picker`,
`goal`, `connect`, `manage`, `hero`) exercised live plus
`python3 update_engine.py --self-test` (73 passed, 0 failed, re-run this
pass). Screenshots: `/tmp/qa-{index,goal,connect,manage,hero,picker-filtered}.png`.
Live evidence per claim is noted inline; anything not rendered is marked
static-only. Bug details live in [bugs.md](/Users/sameerhoda/Projects/running_analysis/v6/bugs.md).

## Scores (0–10)

| Area | Score | Basis |
|------|-------|-------|
| Functionality | 9 | Every happy path passes live: index CTA → picker nav; picker filter/select/empty-state (`No races match` + clear); goal 2:00:00 default + overflow; connect radio gate → mock connect/disconnect; manage disconnect/reconnect, style radios, pause switch; hero pause/play toggle; skip-link focus. QB-01 fix verified live (filter-out → no `aria-selected`, panel rests). Engine 73/73. −1 for three open Lows. |
| Accessibility | 7 | Skip link first-focusable; arrow-key moves focus Pune→Bengaluru with `aria-selected` sync; labelled searchbox; native buttons/radios/switch; goal overflow announced in hint text; `lang="en"` + unique titles everywhere. −3: QB-02 open (orange body text 3.31:1, needs 4.5:1), reduced-motion blocks absent on goal/manage, touch-target sizes unmeasured. Caveat: `--accent-pressed` (#d94800) on white computes to 4.31:1 — still under 4.5:1, so `--ink` is the safe small-text fix. |
| Responsive | 7 | Picker single-column ≤860px, index/hero duo single-column below 560px, goal/connect/manage fluid (`65ch`/`layout-narrow` caps); no layout-breaking fixed px widths (remaining px values are dots, avatars, switch knobs, sr-only helpers, capped inputs). −3: narrow viewport never rendered — this agent-browser version has no viewport emulation, so small-screen is static-only. |
| Content/copy | 9 | Mock labelling consistent (`(mock)` titles, `Disconnect (mock)`); consent-adjacent copy on connect; feedNote file:// guidance tells the user exactly what to run; no typos or endorsement claims seen. −1 for QB-05 (no onward links between picker/goal/connect; watchboard tour is the only path). |
| Brand compliance | 9 | Strava-orange CTA, plain-text compatible copy, no endorsement claims, register links point at MyNextBib. −1: QB-04 still open (~640KB unreferenced media) and small-text orange use overlaps QB-02. |
| Robustness | 9 | Graceful `file://` degradation (`Could not load races.snapshot.json … Serve this folder over HTTP …`); empty-filter state with recovery action; connect button disabled until a race is picked and past-race gating present in code; zero console errors/warnings on every visited page; zero external network calls. −1: past-race gating only partially exercised live. |

Overall: **50 / 60 (avg 8.3) — PASS WITH NOTES.**

## Verdict

Ship-blockers: none (0 Critical, 0 High). The one Medium (QB-02 contrast)
is real and re-measured at 3.31:1, with the refinement that the suggested
`--accent-pressed` remedy only reaches 4.31:1 — route small orange text to
`--ink`. QB-01 is closed and verified live. QB-03 (Connect offered while
connected) re-reproduced live and stays open as a Low. QB-04/QB-05
re-confirmed statically and stay open as Lows. Deferred, unchanged:
real-device narrow-viewport + touch-target assertions, and the Strava-side
app reactivation (backend blocked, not a page defect).

## Coverage checklist

- [x] index: CTA navigation, skip link, screenshot, console clean
- [x] picker: search filter, distance/city chips, select, filter-out desync (QB-01), empty state + clear, goal placeholder blank default, feedNote over `file://`, arrow-key sync, console clean
- [x] goal: 2:00:00 default preview with Goal line, minutes=75 → `Check minutes (0–59)` + Goal line excluded, screenshot
- [x] connect: disabled-until-pick gate, enable on radio select, mock connect → Disconnect appears + Connect disables, screenshot
- [x] manage: connected pill, QB-03 repro, disconnect confirm → `Disconnected (mock)`, reconnect, pause switch toggles when connected, style radios, screenshot
- [x] hero: pause → `Play animation` toggle, screenshot
- [x] engine: `--self-test` → 73 passed, 0 failed
- [x] cross-links: all local hrefs resolve (200s); external links are MyNextBib register links only
- [ ] narrow-viewport render (tooling limitation, static rules verified instead)
