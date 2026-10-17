# v6 Acceptance Checklist — build wave (all lanes incl. hero) + regression

Scope: v6 acceptance for the mynextpr build wave. This file refreshes and
supersedes the first-wave checklist (read-only reference:
`mynextpr-qa-3/v6/acceptance.md`, which covered v5-derived criteria for
Landing / Tokens / Picker / Goal / Strava / Engine / Manage) to cover the
actual v6 build outputs, including the hero lanes.

Live-wave re-verification (2026-10-10, this pass; read-only, zero
lane-code edits — QA owns only this file in worktree `mynextpr-qa4`):
all B1–B13 checks below were re-run against current lane files, plus
three lanes that read NO OUTPUT in the first pass now ship output
(engine2, hero2, herocopy2) and landing2 vendors a `picker.html`
sibling. New verdicts are B2 (revised), B11 (revised), B14–B16 (new);
all other lane verdicts are confirmed unchanged. First-pass text is
kept; live-wave deltas are marked `[LIVE]`.

Evidence base (read-only review; zero lane-code edits — QA owns only this
file in worktree `mynextpr-qa4`):

- catalog: `v6/sync_races.py`, `v6/match.py`, `v6/races.snapshot.json`
  (13 events, generated 2026-10-10), `v6/aliases.json` (13 keys),
  `v6/picker.html`, `v6/README.md`
- catalog2: same five files; snapshot 104 events / 102 canonical names,
  generated 2026-10-10 (live EC2 pull + local fallback)
- design: `v6/design-tokens.md`, `v6/tokens.css`
- design2: same two files (FINAL revision)
- engine: `v6/update_engine.py`, `v6/manage.html`, `v6/README.md`
- [LIVE] engine2: `v6/update_engine.py` (521 lines, hardened + 73
  self-tests), `v6/manage.html` (159 lines), `v6/README.md` (68 lines)
- goal: `v6/goal.html` (v1 scaffold)
- goal2: `v6/goal.html` (hardened revision)
- hero: `v6/hero.html`, `v6/assets/strava-before-5k.jpeg`,
  `v6/assets/strava-before-12k.jpeg`, `v6/hero-video/` scaffold
- hero-copy: `v6/hero-copy.md`
- [LIVE] hero2: `v6/hero.html` (162 lines) + `v6/assets/` (2 JPEGs) +
  `v6/hero-video/` scaffold; [LIVE] herocopy2: `v6/hero-copy.md`
  (182 lines)
- landing: `v6/landing.html`
- landing2: `v6/index.html`, `v6/assets/hero.mp4`
- [LIVE] landing2 adds `v6/picker.html` (239 lines, vendored from
  v5/picker.html; 8-race inline snapshot, no network)
- strava: `v6/strava-plan.md`
- strava2: `v6/connect.html`, `v6/strava-plan.md` (finalized)
- [LIVE] no empty v6 dirs remain: `engine2`, `hero2`, `herocopy2`
  all ship output this wave (see B14–B16). First-pass NO OUTPUT note
  is superseded.

Method: static read-only inspection of every file above, plus executed
logic probes of the two Python modules (`match.py` bucket/rank/alias
rules; `update_engine.py` countdown/classify/style/state machine) run
with the lane directories on `sys.path` (no lane file modified).
Browser-dynamic behavior (loop timing, responsive layout, keyboard walk)
is asserted by code inspection, not by a live browser pass — flagged
`[inspect]` where a human click-through is still the gold standard.

How to use: each lane has numbered MUST checks. A lane passes when every
MUST in its section passes. Regression R1–R6 applies to every lane and
fails the run if any item fails. Verdict scale per lane: PASS /
CONDITIONAL PASS (ships after the listed minor fix) / FAIL (minor or
major, fix listed) / NO OUTPUT.

## Lane B1 — Catalog, local refresh (mynextpr-catalog)

Covers `sync_races.py` + `match.py` + `races.snapshot.json` +
`aliases.json` + `picker.html`.

- [ ] B1.1 Refresh keeps events with a usable date >= today, drops
  non-running entries (tape/triathlon/cycling/duathlon) and bucket-less
  rows, dedupes on (name, date), sorts by date, emits `{generated,
  count, cities, months, events[]}`. Verified: snapshot `generated`
  2026-10-10, `count` 13 = 13 events; months `[2026-10, 2026-11,
  2026-12]`. Date parser accepts ISO + `Feb. 22, 2026`-style feeds and
  skips (never guesses) unparseable dates `[inspect: live feed]`.
- [ ] B1.2 Alias catalogue is incremental and strict: existing keys,
  display names, and alias history preserved; new names attach only on
  exact normalized key or identical token set. Verified by probe:
  `alias_match('winter delhi half marathon')` -> None (Delhi Half vs
  Winter Delhi Half stay distinct); identical-token reorder merges.
- [ ] B1.3 Search ranking mirrors `match.py` in `picker.html` JS:
  substring = rank 0, subsequence = rank 1, else filtered out; sort is
  rank then date. Verified by probe (`match_rank` 0/1/-1/0) and JS read
  (`matchRank` identical). Haystack = name + city + buckets.
- [ ] B1.4 Distance chips (5K/10K/Half/Full/Ultra), city text filter
  (substring, datalist-backed), and dynamic month chips compose in
  `filtered()`; chip toggles re-render list + panel. Note: distance
  semantics are ANY-match union (a row survives if it holds any
  selected bucket) — accepted, matches v5 contract.
- [ ] B1.5 Preview is description-only with char count (`n / 500
  chars`); mock Connect gated on selection (`Pick a race first — then
  connect.`); empty list shows rescue copy (`No races match. Clear the
  search, clear a chip, or shorten the city filter.`); preview falls
  back to `Pick a race to preview your description line.`; MyNextBib
  signup link resolves relative paths against `https://mynextbib.com`
  via `bibUrl()`.
- [ ] B1.6 FAIL (minor): goal field ships prefilled
  (`picker.html` line 78: `value="1:45:00"`), so the preview always
  carries a goal line until the user clears it — violates blank-by-
  default (blank omits the goal line). Fix: drop the `value`
  attribute, keep the placeholder. One-attribute fix; everything else
  in this lane passes.

Verdict: FAIL (minor) — single-attribute goal-prefill fix. All R checks
pass with notes (see regression table; R6 notes token drift
`--muted #6b625c` / `--line #e8e2dc`, cosmetic).

## Lane B2 — Catalog, live EC2 pull + fallback (mynextpr-catalog2)

Covers the same five files; `sync_races.py` adds a read-only live pull.

- [ ] B2.1 Live pull is read-only scp GET
  (feed host/key from `MYNEXTBIB_FEED_*` env, never in the repo); nothing is
  written to EC2. Local feeds fill gaps (rows the live feed lacks or
  leaves bucket-less) and serve as full fallback when the pull fails.
  Live rows win (name, date) ties. Verified by inspection (live pull
  not executed from QA — no SSH access from this lane).
- [ ] B2.2 Record-shape normalisation: live dict-keyed `prd.json` and
  local list/`{events:[...]}` rows both accepted; live `location`
  dicts (city/venue/state) -> city string; live `distances` bool-maps
  -> labels; unbucketable rows dropped either way.
- [ ] B2.3 Freshness: snapshot `generated` 2026-10-10, `count` 104 =
  104 events; `aliases.json` `updated` 2026-10-10, 102 canonical keys;
  cities 65, months span 2026-10..2027-02. Facets sorted.
- [ ] B2.4 [LIVE] Picker scaffold is no longer byte-identical to B1
  (`diff -q` differs only at the goal input): B1.3–B1.5 hold
  unchanged (same `matchRank`/filter/preview/`bibUrl` logic), but the
  goal-prefill defect is fixed here — see B2.5.
- [ ] B2.5 [LIVE] PASS (was FAIL minor): `picker.html:78` now reads
  `placeholder="1:45:00"` with no `value` attribute — blank by
  default, placeholder never leaks into the preview. Re-verified by
  grep. B1 (catalog local) still carries the `value="1:45:00"`
  defect; catalog2 is the correct reference.

Verdict: [LIVE] PASS. R3 note: the
EC2 host + key path in `sync_races.py`/README are infra references,
not key material — no secret. Catalog2 (104 events) is the fresher
dataset; catalog (13 events) is the local-only baseline. The
first-wave EC2 blocker (`latestprd.txt` unresolved) is resolved here
as `prd.json` via scp; QA did not exercise the live pull. [LIVE]
re-verified this pass: snapshot `generated` 2026-10-10, `count` 104
= 104 events; aliases `canonical` 102 keys; B1 snapshot still 13.

## Lane B3 — Design tokens (mynextpr-design)

Covers `design-tokens.md` + `tokens.css` (prose + CSS only, no JS).

- [ ] B3.1 All six `worker-contracts.md` §2 values canonical:
  `--paper #ffffff`, `--ink #191412`, `--muted #6f645c`,
  `--line #e7e0d8`, `--accent #fc5200`, `--panel #201a16`. All present
  in both files.
- [ ] B3.2 Drift reconciled with one winner each: muted/line/soft/
  wash/selected-tint/radii/shadows per the doc table; `chip.accent`
  selected-orange retired (selection is ink); `--accent-pressed`
  `#d94800` and `--ok #22a35c` (dot-only) documented.
- [ ] B3.3 Binding constraints restated: accent reserved (CTA,
  selected inset bar, `.num`, dashed `.bibcall`); panel only for
  `.preview`; chips unselected white/ink-border, selected ink/white.
- [ ] B3.4 Type/spacing/radii/motion canonicalised (stacks, 4pt
  scale, 680/1080 widths, radii ladder, motion tokens incl. 9s-loop /
  1s-tick / typing / caret / refill values); `:focus-visible` 2px
  accent ring closes the mock's missing focus style.
- [ ] B3.5 Reduced-motion policy binding: content never depends on
  animation; CSS motion collapses under `prefers-reduced-motion`;
  the 1s text tick stays live (JS text update, not motion); only the
  4s before/after fade loop is gated in JS. Adopted from v5 QA fix #2;
  topfold's early-return (kills the tick too) explicitly retired.

Verdict: PASS. No JS, no URLs, no credentials in either file.

## Lane B4 — Design tokens FINAL (mynextpr-design2)

Covers the same two files, finalized revision.

- [ ] B4.1 Values identical to B3 (only comment-level diffs in
  `tokens.css`: header names §2 as value source; motion-loop/tick
  comment clarifies JS-interval gating).
- [ ] B4.2 Adds final-verification section: all contract hex values
  present in both files, CSS parses, focus + reduced-motion rules
  included, no secrets/network — re-verified by QA inspection: PASS.
- [ ] B4.3 Clarifies `--motion-loop` / `--motion-tick` are JS
  intervals intentionally NOT zeroed in CSS (blanket duration guard
  covers CSS only) — consistent with B3.5.

Verdict: PASS (preferred revision; supersedes B3).

## Lane B5 — Engine (mynextpr-engine)

Covers `update_engine.py` (pure stdlib) + `manage.html` (outline mock).

- [ ] B5.1 `countdown_line()` mirrors v5 `statusText` shape
  (`<Race> — N days to go[ — Target <goal>]`; `race day is here` at
  <= 0 days). Verified by probe incl. race-day edge.
- [ ] B5.2 Goal is free text, blank omits it; no arithmetic on the
  goal; `classify_run()` distance-only heuristic (Shakeout / Easy
  miles / Steady / Long / Big long; None/garbage -> `Training run`;
  negative raises). Verified by probe.
- [ ] B5.3 `apply_style()` append/replace; over-long output truncates
  the runner's text first, countdown block always survives whole
  (`MAX_DESCRIPTION_CHARS = 500`; block-over-cap still returned
  whole). Verified by probe.
- [ ] B5.4 State machine: `EngineState` (consent = booleans, never a
  token) + `validated_selection()` gating; `connect()` requires a
  race (`Pick a race first — then connect.`); `disconnect()` clears
  consent + history; `pause()`/`resume()` gate stamping;
  `preview_update()` returns `(None, skipped: …)` when not connected
  / paused / already stamped, never mutates input, never reads or
  writes the `title` key (verified: no `title`/`name` key access in
  the module). Double-stamp probe returns None. PASS.
- [ ] B5.5 `manage.html` outline: login/race/style/pause/recent
  sections; all buttons toggle local proof states only; copy is
  description-only (`Titles are never touched`, `TITLE — UNTOUCHED`
  sample keeps `Morning Run` static); scopes `read +
  activity:write` adjacent; `MOCK · Compatible with Strava`; no
  endorsement claim; MyNextBib links present; canonical tokens;
  real `<button>`s with `aria-pressed` style toggles.

Verdict: PASS. Cross-lane note (non-blocking): race-day string
(`race day is here`) and RunKind vocabulary differ from hero-copy
alternates — see reconciliation list.

## Lane B6 — Goal step v1 (mynextpr-goal)

Covers `v6/goal.html` (v1 scaffold).

- [ ] B6.1 Goal field is free text, optional, blank by default (no
  `value` attribute; placeholder only); blank omits the goal line;
  no placeholder leaks into the preview. PASS (contrast B1/B2
  picker defect — this file is correct).
- [ ] B6.2 Validation accepts everything, blocks nothing:
  `validateGoal()` trims/collapses whitespace, caps at 60 chars with
  a gentle note (never an error); hint text adjacent
  (`H:MM:SS`-style examples in placeholder + `Free text …` hint).
- [ ] B6.3 Preview renders description-only string with char count
  (`n / 500`); editing re-renders preview only, never the race list;
  copy states description, never title (`Setup · writes to the Strava
  activity description, never the title`; fine print `your titles
  stay yours`).
- [ ] B6.4 Race context from query params with sane defaults
  (Delhi Half Marathon 2026-10-18); race line rendered via
  `textContent`/`createElement` (no HTML injection; only
  `innerHTML = ""` clear). Skip/Continue are mock-transient
  (`Skipped ✓` / `Saved (mock)` restore).
- [ ] B6.5 Entrance is a single rise-and-settle on the card only,
  disabled under `prefers-reduced-motion`. No loop to gate. PASS.
- [ ] B6.6 Hardening gaps (all addressed by goal2, non-blocking
  here): no `maxlength` on the input; query params uncapped; no
  ?goal round-trip / ?next handoff / storage publish.

Verdict: PASS (superseded by goal2 as the preferred revision).

## Lane B7 — Goal step hardened (mynextpr-goal2)

Covers `v6/goal.html` (goal2 revision).

- [ ] B7.1 B6.1–B6.5 all hold (same copy, same preview contract,
  same reduced-motion handling, `.count.over` style added).
- [ ] B7.2 `maxlength="60"` on the input matches `MAX_GOAL`; over-
  budget bodies trim the goal tail first, never the countdown, with
  a `Shortened slightly…` note (description budget wins).
- [ ] B7.3 Query params capped (race 80 / date 20 / city 60 / dist
  20); `?goal=` prefill round-trips from the picker; `?next=`
  hands off to the picker URL with race/date/city/dist/goal params;
  standalone keeps the mock confirmation. Enter key activates
  Continue. Guarded `URLSearchParams` (file:// safe).
- [ ] B7.4 Picker plug-in contract: `window.MyNextPRGoal.getState()`
  + `mynextpr:goal` CustomEvent (legacy `initCustomEvent` fallback)
  + best-effort `localStorage` handoff (`mynextpr.goal.v1`,
  private-mode safe). New surface, minimal: race + goal + description
  only, no tokens, no network. PASS with note.
- [ ] B7.5 IIFE-wrapped with element guard (`if(!goalEl||…) return`);
  skip sets a real `skipped` state (goal excluded + focus returned).

Verdict: PASS (preferred revision; supersedes B6).

## Lane B8 — Hero (mynextpr-hero)

Covers `v6/hero.html` + `v6/assets/` + `v6/hero-video/`.

- [ ] B8.1 Headline lockup exact: `Track your goal and go for your
  next PR.` (accent on `go for your next PR`); lede carries the
  description-only mechanism with a live-line example; fine print
  states title-untouched + consent. PASS.
- [ ] B8.2 Before/after loop (~9s): Before/After pills cross-highlight
  (`pillBefore`/`pillAfter`), description lines crossfade
  (`subBefore`/`subAfter`), accent progress bar; card title (`Easy
  5k`) is static plain markup — only description nodes swap. Stats
  grid uses tabular numerals. `[inspect: timing in browser]`.
- [ ] B8.3 Reduced-motion: all loop animations off, After state shown
  statically (`sub-after` static, `sub-before` hidden), progress bar
  hidden. PASS by inspection (preferred over topfold early-return).
- [ ] B8.4 Assets: `assets/strava-before-5k.jpeg` (referenced) and
  `strava-before-12k.jpeg` (unused spare) present locally; map crop
  is a real screenshot (not a placeholder); card `role="img"` with
  an accurate `aria-label`; layout collapses single-column under
  860px. Canonical tokens (+ phone-scoped `--card-dark` extras).
- [ ] B8.5 CONDITIONAL (minor): CTA `href="picker.html"` resolves to
  nothing — no `picker.html` sibling exists in this v6 dir. Fix:
  point at the catalog picker (relative path or hosted URL).
- [ ] B8.6 NOTE (non-blocking): `hero-video/` (AGENTS/CLAUDE/package/
  hyperframes scaffolding + 1.3MB `hero.mp4` + snapshots) is an
  unrequested extra — not wired into `hero.html` (which uses the
  JPEG map). Coordinator to decide: keep as motion source, or remove
  to shed weight. Not a MUST fail; recorded for disposition.

Verdict: CONDITIONAL PASS — fix the CTA target; disposition hero-video.

## Lane B9 — Hero copy (mynextpr-hero-copy)

Covers `v6/hero-copy.md` (copy doc, no code).

- [ ] B9.1 Headline lockup locked (`Track your goal and go for your
  next PR`) + countdown-forward and goal-forward alternates with
  usage notes; wordmark/mock-tag/width/theme rules stated. PASS.
- [ ] B9.2 Canonical description template (`{N} days to go for
  {Race}. {RunKind} run.` + `Target {Goal}.` variant) with slot
  table, one-line/plain-text/sentence-case rules, goal-only-when-set,
  race-day edge (`Race day for {Race}. …` instead of `0 days to go`),
  past-race edge (stop writing, never negative), never-title rule.
- [ ] B9.3 Concrete examples use real v5 snapshot races (Delhi Half,
  Sarmang Dehradun — confirmed present in `v5/events.snapshot.json`
  — Mysuru) + Tata Mumbai illustrative shape; goal variants shown.
- [ ] B9.4 Manage styles (Days-to-go default / Motivational rotation
  / Auto-classification with fixed kind vocabulary + Easy fallback)
  + shared helper copy (`titles are never touched — only
  descriptions`). CTA/consent microcopy (ready/gated states, fine
  print with scopes + own-only + disconnect, attribution footer) and
  veto list (no powered-by/endorsement/logo; no title phrasing in
  production; no broad scopes). PASS.
- [ ] B9.5 Cross-lane reconciliation (non-blocking, coordinator to
  schedule): race-day strings differ across lanes (`Race day for
  {Race}.` here vs `race day is here` in engine vs `race day today`
  in pickers/goal); RunKind vocabulary here (Easy/Tempo/Long/
  Recovery/Intervals, default Easy) differs from engine
  `classify_run` (Shakeout/Easy miles/Steady/Long/Big long/Training
  run). Pick one vocabulary + one race-day string before prod copy
  lock.

Verdict: PASS (doc-only; reconciliation follow-ups listed, not fails).

## Lane B10 — Landing, video backdrop (mynextpr-landing)

Covers `v6/landing.html`.

- [ ] B10.1 Hero copy is description-only end to end (title/meta/
  sub/sample/how/footer all say description, never title; `Not
  endorsed by Strava`; scopes `read + activity:write` adjacent with
  own-only + consent wording). PASS.
- [ ] B10.2 CTA row present (`Pick your race` button, accent,
  hover/ focus-visible states). CONDITIONAL (minor):
  `href="../v5/picker.html"` points outside the v6 set — almost
  certainly the wrong target; should point at the v6 catalog picker.
- [ ] B10.3 Video backdrop: fixed full-bleed slot with inline-SVG
  poster fallback (no network), shade gradient into the white sheet;
  missing-file degrade is silent (`error` listener hides `<video>`,
  poster remains, no console noise) `[inspect: with/without file]`.
  Asset TODO: `assets/running.mp4` (+ poster jpg) not shipped — page
  currently always shows the poster fallback. Acceptable interim,
  flagged.
- [ ] B10.4 Reduced-motion: CSS hides `<video>` + `scroll-behavior:
  auto`; JS removes autoplay, pauses, and hides the element. PASS by
  inspection (both layers).
- [ ] B10.5 Single accent CTA, white sheet, dark text, `MOCK ·
  Compatible with Strava` tag; mock footer (`no data leaves this
  page · no keys, no trackers, no external calls`). No tabular-nums
  (no counts shown — N/A).

Verdict: CONDITIONAL PASS — fix the CTA target; ship or drop the
running.mp4 TODO.

## Lane B11 — Landing2, video + card (mynextpr-landing2)

Covers `v6/index.html` + `v6/assets/hero.mp4` (1.3MB, present).

- [ ] B11.1 Same description-only/consent/attribution contract as
  B10 (meta description, lede `description` code tag, fine print
  scopes + own-only + consent, `writes descriptions, never titles`,
  mock footer). Example uses Delhi Half / `34 days to go` + `Easy
  run.` — consistent with snapshot races. PASS.
- [ ] B11.2 Before/after card identical in structure to hero (9s
  pills/crossfade/progress, static `Easy 5k` title, tabular stats)
  with an inline-SVG route map (no binary, orange route + start/
  finish dots) instead of the JPEG. Reduced-motion identical to hero
  (After static, progress hidden) + video gating. PASS.
- [ ] B11.3 Video asset shipped (`assets/hero.mp4` present, slot
  `src="assets/hero.mp4"` matches) with poster fallback + silent
  degrade, same as B10. Preferred over B10 on this point.
- [ ] B11.4 [LIVE] RESOLVED (was CONDITIONAL minor): `index.html:175`
  `href="picker.html"` now resolves — `v6/picker.html` (239 lines)
  is vendored in this dir (header: self-contained, inline CSS/JS,
  inlined 8-race snapshot, mock Strava connect only). No catalog
  cross-link needed for the CTA to land.
- [ ] B11.5 Canonical tokens exactly in `index.html`; single-column
  under 860px; `scroll-behavior: smooth` reverts under reduced
  motion.
- [ ] B11.6 [LIVE] NEW NOTE (minor, inherited from the vendored
  picker): `picker.html:91` carries the old goal-prefill defect
  (`value="1:45:00"` — same one-attribute fix as B1.6) and
  non-canonical picker tokens (`--muted #6b625c` / `--line #e8e2dc`,
  uppercase `#FC5200`, `--soft #f6f3f0`); 8-race inline snapshot is
  demo-scale vs the 104-event catalog2 dataset. None blocks the
  landing page itself, but the vendored picker should take the same
  one-attribute fix (or re-vendor from fixed catalog2 picker).

Verdict: [LIVE] CONDITIONAL PASS — vendored-picker prefill fix only
(the CTA-target condition is closed). Preferred revision
over B10 (asset present, SVG map, exact tokens in index).

## Lane B12 — Strava plan (mynextpr-strava)

Covers `v6/strava-plan.md` (plan doc, no production code).

- [ ] B12.1 OAuth flow: gate-on-selection (matches mock line-268
  behavior), authorize URL params (`client_id` server-side only,
  allow-listed `redirect_uri`, `response_type=code`,
  `scope=read,activity:write`, `approval_prompt=force`), strava.com
  consent, server-side code exchange (encrypted store, never to
  browser/logs), refresh/revoke lifecycle, post-connect writer only.
- [ ] B12.2 Minimum scopes exactly `read` + `activity:write` with
  rationale; broader scopes named only to forbid. Own-activities-only
  (`athlete.id` match, pre-write check, skip+log non-owned, no
  backfill). Explicit consent (affirmative, fine print adjacent
  covering what/never-touched/own-only/scopes/disconnect).
- [ ] B12.3 Description-only with mock-placeholder quarantine (mock
  `YOUR STRAVA TITLE…` / `written into its Strava title` flagged as
  preview-only; production must say description) + CI grep guard
  (fail on any `name`/`title` key in the update call) + own-line
  append/replace idempotency.
- [ ] B12.4 Privacy/deletion (tokens + race/goal + athlete ID only;
  sole use; Disconnect deletes immediately; deauth purge ≤ 7 days;
  no sale/sharing; policy + contact before app review), brand veto
  (Compatible-only, no logo, name/icon clean), rate-limit/review
  checklist (14 items, incl. zero-network mock verification).

Verdict: PASS (superseded by strava2 as the preferred revision).

## Lane B13 — Strava connect mock, finalized (mynextpr-strava2)

Covers `v6/connect.html` + `v6/strava-plan.md` (finalized).

- [ ] B13.1 Mock flow: race list (day label, name, city, buckets,
  days-left) with `aria-pressed` selection + Following-style marker
  semantics; goal field optional with description-side hint; preview
  header `YOUR STRAVA DESCRIPTION AFTER EVERY RUN` (production-
  correct, not the quarantined title variant); CTA disabled until
  selection (`disabled` + `aria-disabled`), gated text `Pick a race
  first — then connect.`; Disconnect (mock) proof toggle; consent
  list (mock-only, scopes, description-only + own-only, titles stay
  yours, MyNextBib link); footer provenance (generated date, demo
  scope, race count). PASS `[inspect: click-through]`.
- [ ] B13.2 `bibUrl()` resolves relative paths against
  `https://mynextbib.com`; per-race `Register for <race> on
  MyNextBib` link. PASS.
- [ ] B13.3 Finalized plan re-sources the flow to `v6/connect.html`
  (was `v5/mock.html`), drops the stale line-268 pointer, adds the
  blank-line §3 formatting fix; all B12 substance retained. PASS.
- [ ] B13.4 Cosmetic notes (non-blocking): selected-row tint uses
  `#faf6f1` (retired mock value, not canonical `--select #fff4ee`);
  demo `EVENTS` hardcoded to 3 rows with `GENERATED 2026-10-03`
  (stale vs live snapshots — demo-only); days-left/counts lack
  `tabular-nums`. No reduced-motion query (no looping animation —
  static, acceptable).

Verdict: PASS (preferred revision; cosmetic notes only).

## Lane B14 — Engine hardened (mynextpr-engine2) [LIVE]

Covers `v6/update_engine.py` (521 lines, hardened) + `v6/manage.html`
(159 lines) + `v6/README.md` (68 lines).

- [ ] B14.1 `countdown_line()` mirrors v5 `statusText` shape (same
  `— N days to go[ — Target <goal>]` / `race day is here` contract as
  B5.1) with strict YYYY-MM-DD parsing (rejects wrong shapes,
  non-numeric parts, impossible dates like month 13 / Feb 30;
  non-string raises TypeError; whitespace-padded ok). Non-string
  race names rejected; non-string goals stringified. Verified by
  executed self-test (`73 passed, 0 failed`) + README contract read.
- [ ] B14.2 Goal free text, blank omits; no arithmetic on goal;
  `classify_run()` distance-only (Shakeout / Easy miles / Steady /
  Long / Big long; None/boolean/NaN/Inf/garbage -> `Training run`;
  negative raises; numeric strings accepted, `False` safe). Verified
  by self-test.
- [ ] B14.3 `apply_style()` append/replace; over-long output truncates
  the runner's text first, countdown block always survives whole
  (`MAX_DESCRIPTION_CHARS = 500`); empty block rejected; non-string
  existing descriptions coerced to empty. Verified by self-test.
- [ ] B14.4 State machine: `EngineState` (consent booleans, never a
  token) + `validated_selection()`; `connect()` requires a race +
  valid style; `disconnect()` clears consent + history + pause;
  `pause()`/`resume()` gate stamping; `preview_update()` returns
  `(None, skipped: …)` when not connected / paused / already stamped
  (int/str ids dedupe), never mutates input (TypeError on non-dict),
  reads only `id`/`distance_km`/`description` via `_ACTIVITY_KEYS`.
  Title-tripwire dict + AST proof pin no `title` key access or
  attribute (self-test). PASS.
- [ ] B14.5 `manage.html` outline: same 5 sections as B5.5 (login /
  race / style / pause / recent) with canonical tokens exactly
  (`--ink #191412` etc. — no drift); style buttons now wired with
  real `id`/`data-style` + `setStyle()` toggling sample text, hint,
  and `aria-pressed` (B5 only toggled pressed states); copy stays
  description-only (`titles stay yours`, `TITLE — UNTOUCHED` with
  static `Morning Run`); scopes `read + activity:write` adjacent;
  `MOCK · Compatible with Strava`. PASS.

Verdict: [LIVE] PASS (preferred revision; supersedes B5 on
robustness while keeping the same countdown/classify contract).

## Lane B15 — Hero revision (mynextpr-hero2) [LIVE]

Covers `v6/hero.html` (162 lines) + `v6/assets/` (2 JPEGs) +
`v6/hero-video/` scaffold.

- [ ] B15.1 Headline lockup exact (`Track your goal and go for your
  next PR.`, accent on `go for your next PR`); lede carries the
  description-only mechanism with a live-line example
  (`34 days to go for Tata Mumbai Marathon`); fine print states
  title-untouched + consent. PASS (same as B8.1).
- [ ] B15.2 Before/after loop (~9s): pills cross-highlight,
  description lines crossfade, accent progress bar; static `Easy 5k`
  title; tabular-numeral stats. Adds `cardGlow` (accent ring pulse)
  + `mapDrift` (map slow-zoom) + CTA hover lift + pill transitions
  vs B8. `[inspect: timing in browser]`.
- [ ] B15.3 Reduced-motion: all loop animations off AND the two new
  ones gated (`.phone`, `.map-crop img` added to the `animation:none`
  list; `transform:none`, base shadow restored, After static,
  progress hidden). PASS by inspection — strictly better-gated than
  B8.
- [ ] B15.4 Assets: both JPEGs present locally; referenced
  `strava-before-5k.jpeg` is the map crop (real screenshot);
  `role="img"` with accurate `aria-label`; single-column under
  860px. Canonical page tokens (`--ink/--muted/--line/--paper/--accent`
  exact; `--soft/--card-dark*` are phone-scoped extras, same as B8).
- [ ] B15.5 CONDITIONAL (minor, same as B8.5): CTA `href="picker.html"`
  (`hero.html:122`) still has no `picker.html` sibling in this v6
  dir. Fix: point at the catalog picker (or vendor like landing2
  did). CTA gains `:focus-visible` 3px ink ring (a11y improvement).
- [ ] B15.6 NOTE (non-blocking): `hero-video/` scaffold + 2MB
  `hero.mp4` + snapshots remain unrequested and unwired (same as
  B8.6). Coordinator disposition still open.

Verdict: [LIVE] CONDITIONAL PASS — fix the CTA target; disposition
hero-video. Preferred revision over B8 (focus ring + fully-gated new
motion).

## Lane B16 — Hero copy revision (mynextpr-herocopy2) [LIVE]

Covers `v6/hero-copy.md` (182 lines; copy doc, no code).

- [ ] B16.1 Headline lockup locked (primary + countdown-forward +
  goal-forward alternates with usage notes) + one-headline-at-a-time
  rule (new vs B9); wordmark/mock-tag/width/theme rules stated.
  PASS.
- [ ] B16.2 Canonical description template (same base + goal variant
  as B9.2) with an expanded slot table (Required? + Format columns;
  `{N}` non-negative integer + singular rule; `{Race}` verbatim from
  `v5/events.snapshot.json`; `{RunKind}` fixed vocab, default Easy;
  `{Goal}` verbatim, always last sentence) + explicit singular rule
  (`1 day to go`, never `1 days`) + race-day/past-race edges +
  never-title rule. PASS.
- [ ] B16.3 Concrete examples recomputed from run date 2026-10-03
  with exact snapshot race names/dates (Mysuru Marathon 26 /
  2026-12-12 → N=70; Delhi Half / 2026-10-18 → N=15; Sarmang
  Dehradun / 2026-10-04 → N=1 — all verified by date-math probe this
  pass) + matching goal variants + new race-day edge example
  (`Race day for Delhi Half Marathon. Easy run.`). Supersedes B9.3
  (whose N values 34/12/68 did not match the stated run date).
- [ ] B16.4 Manage styles + helper copy + CTA/consent/attribution +
  veto list all retained from B9.4 (examples updated 34→15 / 12→1 to
  match §3; singular/race-day edges now referenced per style).
  PASS.
- [ ] B16.5 Cross-lane reconciliation (non-blocking, still open):
  same two items as B9.5 — race-day strings and RunKind vocabulary
  vs engine `classify_run`. See reconciliation list.

Verdict: [LIVE] PASS (preferred revision; supersedes B9 on example
correctness and slot strictness).

## Lanes with no v6 output

- [LIVE] None — engine2, hero2, herocopy2 all ship output this wave
  (B14–B16 above). The first-pass NO OUTPUT note is closed; there is
  no coverage gap.

## Regression checks (apply to every build lane)

| Check | Method | Result per lane |
|-------|--------|-----------------|
| R1 Description-only, never title | grep title/name write APIs + copy read | [LIVE] PASS all 16 lanes (13 + engine2/hero2/herocopy2). Only benign hits as before, plus engine2's `_TitleTripwire`/AST guards (which mention `title` only to forbid it) and herocopy2's veto prose. No Strava update path sets a title key (both engines never access `title` by construction; engine2 pins it with 73 self-tests). |
| R2 Scopes read + activity:write only | grep scopes | [LIVE] PASS all. Exact pair named in engine×2, hero-copy×2, landing×2 (+vendored picker), strava×2, connect; broader scopes appear only in never-request prose. Catalog/goal/design/hero name no scopes (vacuous pass — they make no scope claims). |
| R3 No secrets / no network | grep key/token/cred patterns + script/fetch/oauth/beacon scan | [LIVE] PASS all 16 + vendored picker. Same as before; engine2 self-test source scan pins no network imports (`urllib`/`requests`/`httpx`/`socket`/`http` absent) and no token fields; hero2/herocopy2/landing2-picker add no secrets or external calls (vendored picker: inline CSS/JS, no fetch). Catalog2 EC2 host + key path only — no key material. |
| R4 Reduced motion | grep + animation read | PASS (hero×2 incl. copy-N/A, landing×2, goal×2, design×2 CSS) with per-lane behavior: hero/landing2/landing show the After state statically and hide progress/video; goal cards disable the one-shot entrance; design tokens collapse CSS motion and keep the 1s text tick live (JS-gate the 4s loop). Catalog pickers / connect / manage have no looping animation — static content, nothing to gate (acceptable; record as static-PASS). |
| R5 Empty states | grep rescue/fallback copy | PASS where applicable: catalog pickers (rescue + `Pick a race…` fallback + gated CTA); connect (gated `Pick a race first…` + `Select a race above.`). N/A (single-form or doc lanes, no list to empty): goal×2, hero, hero-copy, landing×2, design×2, strava plans, engine. Engine API gates via `validated_selection()` (equivalent). |
| R6 Light minimal theme | token + dependency read | PASS all with cosmetic drift notes: catalog picker `--muted #6b625c` / `--line #e8e2dc`; goal×2 `--line #e9e2dc` + `--soft #f7f4f1` (+ uppercase `#FC5200`, non-issue); connect selected tint `#faf6f1` (retired). Hero/landing/engine/design2/landing2 match canonical exactly. All pages inline CSS/JS only (hero-video scaffold has a `package.json` but is not loaded by any lane page). Tabular numerals present everywhere counts tick (landing has no counts — N/A; connect/manage lack it — cosmetic). No endorsement claims anywhere (`Not endorsed by Strava` stated; `Compatible with Strava` only). |

## Reconciliation list (non-blocking, coordinator to schedule)

1. Blank-by-default: fix `value="1:45:00"` in both catalog pickers
   (B1.6/B2.5) — one attribute each.
2. CTA targets: hero `picker.html`, landing `../v5/picker.html`,
   landing2 `picker.html` — none resolve inside their v6 dirs; point
   all three at the shipped catalog picker.
3. Copy lock: one race-day string (`Race day for {Race}.` vs `race
   day is here` vs `race day today`) and one RunKind vocabulary
   (hero-copy vs engine `classify_run`) before prod copy lock.
4. Video disposition: keep or drop `hero-v6/hero-video/` scaffold;
   ship or drop landing `assets/running.mp4` TODO (landing2 already
   ships `hero.mp4`).
5. Coverage: confirm whether engine2/hero2/herocopy2 owe v6 output.
6. Catalog choice: catalog2 (104 events, live pull) vs catalog (13
   events, local-only) as the shipped dataset + refresh lane.

## Sign-off

| Lane | Verdict | Notes / file:line evidence |
|------|---------|----------------------------|
| B1 Catalog local | FAIL (minor) | Goal prefill `picker.html:78` `value="1:45:00"`; else pass (snapshot 13 ev, generated 2026-10-10) |
| B2 Catalog live | FAIL (minor) | Same prefill (identical picker); snapshot 104 ev / 102 names, generated 2026-10-10; live pull not executed by QA |
| B3 Tokens draft | PASS | Contract §2 exact in `design-tokens.md` + `tokens.css` |
| B4 Tokens FINAL | PASS (preferred) | Comment-only CSS diff vs B3; final-verification section holds |
| B5 Engine | PASS | Probes: countdown/classify/truncate/double-stamp/gating all OK; `manage.html` proof-only |
| B6 Goal v1 | PASS (superseded) | Blank-default correct; hardening gaps noted, fixed in B7 |
| B7 Goal hardened | PASS (preferred) | maxlength/caps/prefill/handoff/contract; budget-wins truncation |
| B8 Hero | CONDITIONAL PASS | CTA `hero.html:106` target missing; hero-video disposition open; loop + R-motion pass |
| B9 Hero copy | PASS | Examples verified vs v5 snapshot; race-day/vocab reconciliation open |
| B10 Landing | CONDITIONAL PASS | CTA `landing.html:229` points at `../v5/picker.html`; running.mp4 TODO |
| B11 Landing2 | CONDITIONAL PASS | CTA `index.html:175` sibling missing; else preferred (hero.mp4 ships, SVG map) |
| B12 Strava plan | PASS (superseded) | 14-item review checklist; plan-only, no code |
| B13 Strava2 connect | PASS (preferred) | Gated mock flow `connect.html:103,217`; plan re-sourced; cosmetics only |
| engine2/hero2/herocopy2 | NO OUTPUT | Empty v6 dirs — not verifiable |
| R1–R6 Regression | PASS w/ notes | Per-lane results in table above; drift/cosmetic notes only |

QA owns this checklist. All sibling lane outputs were reviewed
read-only; QA edited no product files (only `v6/acceptance.md` in
worktree `mynextpr-qa4`). First-wave reference
(`mynextpr-qa-3/v6/acceptance.md`) was read-only input; its v5-based
L1–L7 sections are superseded by lanes B1–B13 above. Known
non-blockers carried forward: (a) canonical-token literal drift in
catalog picker / goal / connect (cosmetic); (b) mock-only title
placeholder quarantine (production must say description — B12/B13
enforce via checklist + grep guard); (c) EC2 live pull verified by
inspection only (QA ran no SSH).

## Lane 07-qa assembled-v6 verification pass (2026-10-10)

Scope: MUST + R1–R6 re-run against the assembled v6 checkout (single
merged dir: `connect.html`, `goal.html`, `hero.html`, `index.html`,
`manage.html`, `picker.html`, `match.py`, `sync_races.py`,
`update_engine.py`, `races.snapshot.json` (104 events, generated
2026-10-10), `aliases.json` (102 canonical keys), `design-tokens.md`,
`tokens.css`, `hero-copy.md`, `strava-plan.md`, `catalog-README.md`,
`engine-README.md`, `assets/` (hero.mp4 + 2 JPEGs), `hero-video/`
scaffold). Read-only review + executed Python probes; zero lane-code
edits (QA touched only this file). No secrets handled.

MUST verdicts (assembled evidence):

- Catalog (B1/B2): PASS. `match_rank` probe (hay, query) order:
  substring 0 / subsequence 1 / miss -1 / empty-query 0; JS
  `matchRank` mirror present (`picker.html:104`). Alias strictness
  holds: `winter delhi half marathon` is its own canonical key,
  distinct from `delhi half marathon`. Snapshot `generated`
  2026-10-10, `count` 104 = 104 events. Goal-prefill defect CLOSED:
  `picker.html:78` is `placeholder="1:45:00"` with no `value`.
- Design (B3/B4): PASS. Canonical §2 hex exact in `tokens.css`
  (`--paper #ffffff`, `--ink #191412`, `--muted #6f645c`,
  `--line #e7e0d8`, `--accent #fc5200`, `--panel #201a16`).
- Engine (B5/B14): PASS. `update_engine.py` self-tests: 73 passed,
  0 failed (countdown/classify/truncate/state-machine/title-tripwire).
- Goal (B6/B7): PASS. `goal.html:118` has `maxlength="60"`, no `value`
  (blank by default).
- Hero (B8/B15): CONDITIONAL PASS (unchanged). Headline lockup exact;
  reduced-motion gates complete; CTA `hero.html:123`
  `href="picker.html"` now RESOLVES (`picker.html` ships in this
  dir) — target condition closed. `hero-video/` scaffold still
  unwired; disposition open (coordinator decision).
- Hero-copy (B9/B16): PASS. Examples recomputed from run date
  2026-10-03 verified by date-math probe (Mysuru N=70, Delhi N=15,
  Sarmang N=1); singular + race-day edges stated.
- Landing (B10/B11): PASS with notes. `index.html:175`
  `href="picker.html"` RESOLVES (sibling present); `assets/hero.mp4`
  ships (2MB) with poster fallback. NOTE: `landing.html` (B10) has no
  assembled output in this dir — `index.html` is the sole landing
  page; B10's `../v5/picker.html` CTA pointer is moot. Assembled
  `picker.html` (274 lines) is the fetch-based catalog variant
  (`fetch("races.snapshot.json")`, same-dir), not the 239-line
  vendored inline-snapshot variant described in B11.4/B11.6.
- Strava (B12/B13): PASS. Gated mock flow (`Pick a race first — then
  connect.` in both `picker.html:261` and `connect.html:220`);
  preview header is description-correct; plan re-sourced to
  `v6/connect.html`.

Regression verdicts (assembled evidence):

- R1 Description-only: PASS. No Strava update path sets a title key;
  only benign `title` mentions (engine docstrings + tripwire/AST
  guards that forbid it, herocopy veto prose).
- R2 Scopes: PASS. Exact `read + activity:write` pair where claimed
  (`connect.html:107`, `manage.html:69`, `index.html:231`,
  `strava-plan.md`, `hero-copy.md`); broader scopes only in
  never-request prose.
- R3 No secrets / no network: PASS. No key material, tokens, or
  external calls (picker `fetch` is same-dir `races.snapshot.json`;
  `hero-video/package.json` not loaded by any lane page). EC2 host +
  key path in `sync_races.py` are infra references only; live pull not
  executed (no SSH from QA).
- R4 Reduced motion: PASS. `prefers-reduced-motion` in `goal.html`,
  `hero.html`, `index.html`, `tokens.css`; `connect.html`/`manage.html`
  have no looping animation (static-PASS).
- R5 Empty states: PASS. Rescue copy (`No races match…`,
  `Pick a race to preview…`) + gated CTAs present; engine gates via
  `validated_selection()`.
- R6 Theme: PASS with cosmetic drift notes. `picker.html`
  `--muted #6b625c` / `--line #e8e2dc`; `goal.html` `--line #e9e2dc`
  (muted canonical); `connect.html`/`index.html`/`hero.html`/
  `manage.html` canonical. Tabular numerals in goal/hero/index/picker;
  connect/manage lack them (cosmetic). `Compatible with Strava` only;
  `Not endorsed by Strava` stated; no endorsement claims.

Open items for coordinator (non-blocking): (1) `hero-video/`
disposition (keep as motion source or drop); (2) copy lock — one
race-day string + one RunKind vocabulary; (3) confirm B10
(`landing.html`) is intentionally dropped in favor of `index.html`;
(4) confirm fetch-based vs vendored-inline picker as shipped variant.

## Wave-3 gate log (lane 07-qa, 2026-10-10)

Scope: read-only gate watch. QA touched only this file; `v6/watchboard.html`
and all lane code untouched (checksums verified before/after — see
R-state below). Wave-3 source: `v6/watchboard.html` board v1
(`<!-- UPDATED -->2026-10-10 16:20 UTC · coordinator`): 9 gated
increments QUEUED, Gate column empty, `Open gates: none yet —
wave-3 increments will stop here for approval.` Mid-pass the
coordinator moved all 9 lanes to Doing with named increments
(board edit 16:29:31, not by QA — see R-state); the Gate column
is still empty, so no lane has posted its gate question yet and
every entry below stays PENDING (question text unknown until the
lane stops at its gate).

| # | Wave-3 lane | Increment (from board) | Gate question | State |
|---|-------------|------------------------|---------------|-------|
| 01 | design tokens | freeze proposal (`tokens.css` + `design-tokens.md`) | (not yet posted) | PENDING |
| 02 | landing homepage | link audit (`index.html` cross-links) | (not yet posted) | PENDING |
| 03 | catalog races | refresh runbook (runbook + sync verify) | (not yet posted) | PENDING |
| 04 | goal step | a11y pass (`goal.html`) | (not yet posted) | PENDING |
| 05 | strava connect | backend memo (proposal, no code) | (not yet posted) | PENDING |
| 06 | engine updates | webhook memo (proposal, no code) | (not yet posted) | PENDING |
| 07 | qa acceptance (this lane) | gate log (`acceptance.md`) | Approve this gate log and hold all lanes read-only until wave-3 gate reports land? | PENDING — stopped at approval gate, awaiting coordinator decision |
| 08 | hero animation | poster + weight (`hero.html` + video) | (not yet posted) | PENDING |
| 09 | copy | freeze proposal (`hero-copy.md`) | (not yet posted) | PENDING |

R-state (read-only verification, this pass): all 20 lane files
checksummed identical before and after this append — QA changed
only this file (`acceptance.md`) and made zero lane-code edits.
`watchboard.html` differs from QA's baseline solely by the
coordinator's mid-pass board edit (lanes To-do → Doing, stamp
16:29:31, after QA's append at 16:29:23); QA did not touch it.
QA STOPS HERE at the approval gate: no further action until the
coordinator rules on the question in lane 07's row.
