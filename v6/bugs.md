# v6 Bug List — Lane 07 QA (living document)

Owner: Lane 07 (qa). Scope: all six v6 pages (`index`, `picker`,
`goal`, `connect`, `manage`, `hero`) plus engine self-tests
(`update_engine.py --self-test`). Method: functional pass per the
test-master workflow — happy paths AND edge cases in a real browser
(`agent-browser`, local HTTP, no real Strava calls; every networked
surface is mock by design). Status values: `open` / `fixed` /
`verified`. QA touches only this file — never lane code.

## Pass record

| Date | Pages | Engine | Result |
|------|-------|--------|--------|
| 2026-10-10 | all six over `http://localhost:8907` | 73 passed, 0 failed | 2 seeded + 3 new below; passes at bottom |
| 2026-10-10 (2nd) | all six over `http://localhost:8907` + `file://` spot check | 73 passed, 0 failed (re-run) | QB-01 verified fixed live; QB-03 re-reproduced (open); no new bugs; scores in `qa-score.md` |
| 2026-10-10 (owner-feedback repass) | `picker` + `hero` + `goal` over `http://localhost:8907` (existing server, real browser, no Strava calls) | n/a (pages only) | 2/5 owner items pass (hero minimal, goal HH:MM); 3 fail → QB-06…QB-09 below |

## Open bugs

### QB-01 — Picker preview desync when selection is filtered out (seeded, fix in flight)

- Severity: Medium (screen-reader / sighted mismatch; wrong race could be connected).
- Where: `v6/picker.html` — `selEvent()` falls back to `list[0]`
  (lines ~218-222) and `renderPanel()` silently re-points `state.sel`
  (lines ~313-315), while `renderList()` marks nothing selected.
- Repro: 1. Open `picker.html` over HTTP. 2. Click any Mumbai race.
  3. Type `Bengaluru` in search. 4. Observe: no option carries
  `aria-selected="true"`, but the Strava description preview shows the
  first Bengaluru race.
- Expected: preview tracks the marked selection; when the selection is
  filtered out the panel says "No race selected" (or keeps the marked
  item), never a silent swap.
- Owner lane: catalog/picker. Status: **verified fixed live 2026-10-10 (Lane 07 re-pass)** — repro run (Mumbai pick → `Bengaluru` filter): 0 options `aria-selected="true"`, panel rests at "Pick a race to preview your description line."; post-filter pick syncs selection + preview. Earlier: fixed, coordinator-verified live 2026-10-10.

### QB-02 — Strava-orange body text below AA contrast (seeded)

- Severity: Medium (accessibility; normal text needs 4.5:1).
- Measured: `#fc5200` on `#ffffff` = **3.31:1** (computed, WCAG
  relative-luminance formula); ~3.0-3.1:1 on `--soft`/`--select` tints.
- Failing instances (normal-size text): `index.html` / `hero.html`
  `.sub-after .count`; `connect.html` `.chip .n` + step `.num`;
  `goal.html` `.step-line .num`; `picker.html` `.num`
  (`--text-mono-sm`). Display-size instances (e.g. `manage.html`
  `h1 .n`) pass the 3:1 large-text bar and are excluded.
- Expected: small orange text moves to `--accent-pressed` (`#d94800`)
  or `--ink`, keeping `--accent` for large display type, focus rings,
  and markers.
- Owner lane: design/tokens. Status: **open (re-measured 2026-10-10: 3.31:1 on white, 3.13:1 on soft tint)**. QA note: `--accent-pressed` (`#d94800`) on white computes to **4.31:1** — still under 4.5:1, so small text should move to `--ink`; keep `--accent` for large display type only.

### QB-03 — Manage shows Connect while already connected

- Severity: Low (mock confusion; no data risk).
- Where: `v6/manage.html:197-198` — both `#loginbtn` (Connect) and
  `#logoutbtn` (Disconnect) are always visible; `render()` never hides
  or disables Connect when `state.connected` is true, though the pill
  reads "Connected (mock)".
- Repro: open `manage.html` fresh — pill says connected, yet the
  primary Connect button is offered.
- Expected: when connected, Connect is hidden or disabled until after
  disconnect.
- Owner lane: engine/manage. Status: **open (re-reproduced live 2026-10-10)** — fresh load: pill `Connected (mock)` with `Connect with Strava` visible + enabled. Disconnect confirm → `Disconnected (mock)`; reconnect, pause switch (toggles when connected), and style radios all work.

### QB-04 — Shipped media assets unreferenced by any page

- Severity: Low (dead weight ~640KB; stale acceptance claims).
- Detail: `grep` for `mp4|<video|<img|assets` returns **0 hits** in
  both `index.html` and `hero.html`, yet `v6/assets/` ships
  `hero.mp4` (373KB), `hero-poster.jpg`, `strava-before-5k.jpeg`,
  `strava-before-12k.jpeg`. `acceptance.md` B11.3/B8.4 still claim the
  video/JPEG slots are wired (`src="assets/hero.mp4"`).
- Expected: either wire the video slot with poster fallback or remove
  the binaries and correct the acceptance notes.
- Owner lane: landing/hero. Status: **open (re-confirmed 2026-10-10: 0 media refs in index/hero)**.

### QB-05 — No next-step navigation between picker / goal / connect

- Severity: Low (review-tour friction; mocks document it).
- Detail: picker mock Connect toggles in place, goal Continue/Skip
  "do nothing real" (page's own fine print), connect has no onward
  link; the only cross-links are index/hero CTAs to `picker.html` and
  index to `manage.html`. The watchboard tour order is the sole path.
- Expected: coordinator decision — acceptable for mock wave, or add
  explicit next-step links.
- Owner lane: coordinator. Status: **open (re-confirmed 2026-10-10: no onward hrefs between picker/goal/connect; only index/hero→picker, index→manage)**.

## Owner feedback round — verdicts (verified live 2026-10-10, Lane 07 repass)

1. **Minimal hero per brief — PASS.** `hero.html`: exactly 1× `h1`
   (`Track your goal and go for your next PR.`, the locked primary),
   0 kickers/eyebrows, 0 `<video>`/`<img>`, 1 CTA (`Pick your race`);
   story section keeps Pause-animation toggle.
2. **Tata Mumbai Marathon findable — FAIL → QB-06.** Exact phrase
   yields `No races match`; the event is absent from the feed.
3. **Cities by event count desc + distance/month/city order — SPLIT →
   QB-07.** Filter order live is Distance 01 / Month 02 / City 03
   (PASS — note: file read earlier in this pass showed City 02 /
   Month 03, so another lane reordered mid-pass in this shared
   checkout); city chips remain alphabetical, Agartala first (FAIL).
4. **Single-select distance — FAIL → QB-08.** 5K stays
   `aria-pressed="true"` after 10K is pressed (ANY-match union).
5. **HH:MM goal entry with spinners, no seconds — PASS on `goal.html`,
   caveat → QB-09.** Hours/Minutes inputs + 4 spinner buttons, 0
   seconds fields; Increase-hours 2→3 live, preview shows
   `Goal: 3:00`. `picker.html` goal field is still the old
   single `type="text"` `1:45:00` input.

### QB-06 — "Tata Mumbai Marathon" not findable (missing event + noisy fuzzy)

- Severity: Medium (owner-named race unfindable).
- Detail: feed (`races.snapshot.json`, 104 events) has no Tata Mumbai
  Marathon — only Tata Steel Kolkata 25K ×2 (Kolkata) and Tata Ultra
  Marathon (Lonavala). Exact-phrase search → `No races match`.
  `mumbai` search and the Mumbai city chip work (9 events). `tata`
  alone subsequence-matches ~15+ unrelated races (SEARATHON, DWARKA…).
- Repro: open `picker.html` over HTTP, type `Tata Mumbai Marathon`.
- Expected: coordinator decision — add/alias the event, or scope the
  fuzzy rank so `tata` doesn't flood.
- Owner lane: catalog/picker. Status: **fixed, coordinator-verified live 2026-10-10** — exact search returns Tata Mumbai Marathon 17 Jan 2027 Mumbai 99 days; QA tested the stale 104-event snapshot before the sync refresh (now 113).
- Fixed in: sync normalizer now keeps zero-distance-dict EC2 rows.

### QB-07 — City chips alphabetical, not event-count desc

- Severity: Medium (owner-explicit ordering contract).
- Detail: live chip order starts Agartala, Ahmedabad, Aurangpur…
  (alpha); by count it should lead Mumbai (9), Pune (8),
  Bengaluru (8), New Delhi (6). Source `data.cities` is alpha-ordered.
- Repro: open `picker.html`, read first `#cityChips .chip` labels.
- Expected: cities sorted by event count desc (tie-break alpha).
- Owner lane: catalog/picker. Status: **fixed, coordinator-verified 2026-10-10** — snapshot cities now lead Mumbai, Bengaluru, Pune, New Delhi by count; QA tested the stale alpha build.

### QB-08 — Distance filter is multi-select union, not single-select

- Severity: Medium (owner-explicit single-select contract).
- Detail: clicking 10K after 5K leaves both `aria-pressed="true"`
  (count line `— 8 of 104` with `mumbai` search); code comment
  (`picker.html` ~150-152) cites the v5 ANY-match union contract.
- Repro: press 5K, then 10K; read `aria-pressed` on both chips.
- Expected: pressing one distance releases the others (radio behavior).
- Owner lane: catalog/picker. Status: **fixed, coordinator-verified live 2026-10-10** — clicked Half then Full in a real browser: only Full aria-pressed=true; QA tested the stale multi-toggle build.

### QB-09 — Picker goal field still H:MM:SS text, not HH:MM spinners

- Severity: Low (inconsistent with the `goal.html` contract that passes).
- Detail: `picker.html` `#goal` is `type="text"`
  `placeholder="1:45:00"` with empty value; no spinner buttons, accepts
  seconds — unlike `goal.html`'s Hours/Minutes + spinners.
- Repro: open `picker.html`, inspect `#goal` in the Race countdown panel.
- Expected: coordinator decision — mirror the HH:MM spinner entry in
  the picker panel or confirm the single-field divergence is intended.
- Owner lane: catalog/picker. Status: **open (reported 2026-10-10)**.

## Verified (no bug filed)

- Goal-prefill fix (acceptance B2.5): `picker.html:135` uses
  `placeholder="1:45:00"` with no `value` — blank default confirmed
  live; preview omits the goal line.
- Goal overflow: entering 75 minutes shows `Check minutes (0–59)` and
  the preview excludes the goal line; ranges 0-99/0-59 enforced.
- Connect gate: button disabled until a race radio is chosen, enables
  on select; no real network call.
- Picker empty state (`No races match` + clear), `feedNote` + `Feed
  unavailable` graceful error over `file://`, past-race connect gating
  and `passed` badges (code + partial live).
- Engine: `python3 update_engine.py --self-test` → 73 passed, 0 failed.
- Keyboard/a11y spot checks: skip link receives first Tab on index;
  picker listbox arrow-key selection syncs preview; goal errors
  announced via `#goalStatus`; reduced-motion blocks present on
  index/hero/picker/connect.
- Layout by construction: picker single-column ≤860px, index/hero duo
  single-column below 560px, manage/goal single-column narrow wraps;
  no fixed widths found (viewport-resize CLI unavailable in this
  agent-browser version, so small-screen verified statically).
- Cross-links resolve: `picker.html` vendored, `manage.html` styles
  link OK, watchboard tour order intact (watchboard itself untouched).
- 2026-10-10 re-pass additions: hero Pause→`Play animation` toggle;
  connect mock connect disables Connect + shows `Disconnect (mock)`;
  manage pause switch toggles true→false when connected; picker
  arrow-key moves focus with `aria-selected` sync; goal overflow hint
  `Check minutes (0–59)` with Goal line excluded from preview (160
  chars); picker goal input placeholder `1:45:00` with empty value;
  `file://` feedNote names the exact recovery command; zero console
  errors/warnings on every visited page; no fixed layout-breaking px
  widths; `lang="en"` + unique titles on all six pages; reduced-motion
  blocks confirmed on index/hero/picker/connect only (absent on
  goal/manage).

## 2026-10-10 — picker goal-time digit drums (direct fix, verified live)
- Replaced picker free-text goal input (placeholder `1:45:00`, seconds
  allowed) with the goal.html digit-drum component: Hours/Minutes groups,
  typeable digit boxes, per-digit arrows, ArrowUp/Down + auto-advance +
  Backspace-back + minutes-tens clamp, spinbutton roles.
- Distance-aware defaults re-apply on distance change only (5K 0:30
  hours-hidden, 10K 1:00, Half 2:00, Full 4:00, Ultra 6:00); typing is
  never clobbered by re-renders. Preview + Connect handoff read drums.
- Verified live: 113 feed loads, TMM select → 04:00, arrow → 4:01,
  keystroke 5 → 4:05, ArrowUp → 4:06, screenshot inspected.
- connect.html still uses a plain text goal input — same port pending.

## 2026-10-17 — description format v2 (countdown + target pace, month/year totals)
- Engine: new `goal_to_pace`, `totals_line`, `fmt_km`, `RACE_DIST_KM`;
  `countdown_line` now "<N> days to go for <Race>. Target pace M:SS/km
  (goal H:MM)."; `build_description` returns countdown + totals lines;
  EngineState gains race_dist_km/month_km/year_km. 89/89 self-tests pass.
- Previews (picker/goal/connect/manage) + landing after-card show the new
  2-line shape; preview totals (42/310 km) are labelled samples until
  Strava athlete stats wire in. Unparseable goals fall back to raw text.

## 2026-10-17 — UI simplification pass (picker form flow, minimal manage)
- Picker is now a single top-to-bottom form (panel below results, 720px
  column); goal time hides behind an "Add a target time?" checkbox,
  unchecked by default — preview/connect/OAuth carry no target until
  opted in. Verified live: hidden by default, reveals on check.
- Manage stripped to race card (+ Change race), updates toggle, quiet
  connection section. Style options + run preview removed; format fixed.
  Expired races auto-stop: banner + disabled toggle + pick-new-race CTA.
- Backend (takes effect on next server restart): /api/status reports
  expired/dist; all three stamp paths skip past races. Verified: syntax,
  89/89 engine tests, manage screenshot against live connected state.

## 2026-10-17 — warm copy (#4) + promo line everywhere
- Engine: countdown "92 days to go — Race, target H:MM at M:SS/km.",
  totals "October so far: …", promo footer on every stamp. New
  strip_prior_block removes our own old stamps on re-stamp (notes kept).
  93/93 self-tests pass.
- Picker/goal/connect previews + landing after-card mirror the shape.
- Evening Run (18:31) stamped live, verified by read-back.
