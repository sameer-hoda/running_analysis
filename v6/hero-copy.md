# mynextpr — Hero & Countdown Copy (v6)

Scope: homepage hero, Strava description templates, manage-page update styles, CTA + consent microcopy.
Lane: hero-copy. Source constraints: `v5/worker-contracts.md` §§3–4.

Standing rules for every string below:

- Production writes the countdown into the Strava activity **description only**. Never the title — the user's own title is sacred.
- Brand label is `Compatible with Strava` only. Never claim endorsement, partnership, or "powered by Strava". No Strava logo.
- OAuth scopes: `read` + `activity:write` only. Updates touch only the authenticated user's own activities, only after explicit connect consent.

---

## 1. Homepage headline lockup

**Primary (locked):**

> Track your goal and go for your next PR

Supporting lede (pairs with primary):

> Pick your race. Every run you log gets its countdown added to the run's Strava description — automatically.

Supporting sub:

> Three taps: distance, month, race. Then connect Strava and forget about it.

**Alternate A (countdown-forward):**

> Every run counts down to race day

- Lede: `Pick your race. Every run you log carries the countdown in its Strava description.`
- Use when: hero needs the mechanism up front (returning runners, referral landing).

**Alternate B (goal-forward):**

> Set the target. Chase it every run.

- Lede: `Pick your race, add an optional target finish, and every run you log carries both in its Strava description.`
- Use when: goal input is the featured action (campaigns around target times).

Usage notes:

- Headline is page copy only; it never appears inside a Strava activity.
- Wordmark stays `mynextpr`; mock tag stays `MOCK · Compatible with Strava`.
- Keep the 680px wrap, light theme (`#ffffff` bg, `#191412` text); no dark-page inversion.
- Only one headline shows at a time; Alternates never combine with the primary on the same view.

---

## 2. Canonical Strava description template

Base template (description only):

```text
{N} days to go for {Race}. {RunKind} run.
```

Goal-time variant (appended inside the same description when the user sets a target):

```text
{N} days to go for {Race}. {RunKind} run. Target {Goal}.
```

Slot definitions:

| Slot | Required? | Meaning | Format | Example values |
|------|-----------|---------|--------|----------------|
| `{N}` | Always | Whole days from run date to race date (race date minus run date, calendar days) | Non-negative integer only; `1` renders as `1 day to go`, `0` renders per race-day edge below, all other values as `{N} days to go`; never write negative values | `70`, `15`, `1` |
| `{Race}` | Always | Race name exactly as listed in `v6/races.snapshot.json` — copy verbatim, never shorten or rephrase | Plain text | `Delhi Half Marathon`, `Mysuru Marathon 26` |
| `{RunKind}` | Always | Auto-classified run kind | Exactly one of `Easy`, `Tempo`, `Long`, `Recovery`, `Intervals`; default to `Easy` when classification is unsure | `Easy`, `Tempo`, `Long` |
| `{Goal}` | Only when set | User's free-text target finish, copied verbatim | Plain text, no validation or reformatting | `sub-2`, `sub-4`, `1:44:00` |

Template rules:

- One line for the base template, plain text, sentence case. Ends with a period.
- `{RunKind}` always present; default to `Easy` when classification is unsure rather than omitting it.
- `{Goal}` appears only when the user set one; never invent, normalize, or reformat a goal. When present it is always the last sentence (`Target {Goal}.`).
- Singular: when `{N}` is `1`, write `1 day to go for {Race}.` — never `1 days to go`.
- Race-day edge: when `{N}` is `0`, write `Race day for {Race}. {RunKind} run.` (and `Target {Goal}.` when set) instead of `0 days to go`.
- Past-race edge: stop writing countdown lines once race date has passed; never write negative days.
- Never write to the activity title. The template output goes in the description field only.
- Verdict ban (Strava API Policy §5.11): never write performance judgments (`on track`, `ahead`, `behind`, `faded`), coaching advice, or finish predictions. Allowed content is arithmetic on user inputs (days-left, goal pace) plus echoes of Strava's own activity data (distance, pace). Show both numbers and let the runner judge, e.g. `Goal pace 5:55/km · Today 6:50/km` — never the verdict.
- Attribution: every written description ends with its own `— countdown by mynextpr` line, so followers can tell the text is auto-written. Never drop it, never promotionalize beyond it.
- Today line: when writing to a specific activity, include one `Today: {RunKind} {distance} @ {pace}` echo line drawn from that activity's own data.

---

## 3. Concrete countdown examples

All examples use exact race names from `v6/races.snapshot.json` (generated 2026-10-10, 104 events).
`{N}` is whole days from the stated run date to the race date.

Run logged 2026-10-03:

1. Race `Mysuru Marathon 26` (2026-12-12) → N = 70:
   `70 days to go for Mysuru Marathon 26. Long run.`
2. Race `Delhi Half Marathon` (2026-10-18) → N = 15:
   `15 days to go for Delhi Half Marathon. Easy run.`

Run logged 2026-10-17:

3. Race `Vedanta Delhi Half Marathon` (2026-10-18) → N = 1:
   `1 day to go for Vedanta Delhi Half Marathon. Tempo run.`

With goal-time variant (same three runs, user set `sub-2`):

1. `70 days to go for Mysuru Marathon 26. Long run. Target sub-2.`
2. `15 days to go for Delhi Half Marathon. Easy run. Target sub-2.`
3. `1 day to go for Vedanta Delhi Half Marathon. Tempo run. Target sub-2.`

Race-day edge (run logged 2026-10-18, race `Delhi Half Marathon` 2026-10-18 → N = 0):

- `Race day for Delhi Half Marathon. Easy run.`

Past-race edge (run logged 2026-10-12, race `Chase 10K Noida 2nd Edition` 2026-10-11 → race date passed):

- No countdown line is written; the description is left untouched.

---

## 4. Manage-page update-style options

Three styles, user-pickable on the manage page. Default: **Days to go**. Each style writes to the description only.

### Style 1 — Days to go (default)

- Label: `Days to go`
- Hint: `Simple countdown on every run.`
- Output: base template exactly — `{N} days to go for {Race}. {RunKind} run.` (+ `Target {Goal}.` when set)
- Example: `15 days to go for Delhi Half Marathon. Easy run.`

### Style 2 — Motivational

- Label: `Motivational`
- Hint: `Countdown plus a short nudge. Rotates, never shouts.`
- Output: base template + one short second sentence, rotated from a fixed list:
  - `One run closer.`
  - `Stack the miles.`
  - `Trust the buildup.`
  - `Keep showing up.`
- Example: `15 days to go for Delhi Half Marathon. Easy run. One run closer.`
- Goal variant (nudge sits between base and goal): `15 days to go for Delhi Half Marathon. Easy run. One run closer. Target sub-2.`
- Rules: second sentence only, no emojis, no all-caps, never mentions the title. The countdown number always leads; the nudge never replaces or precedes it. Goal variant appends `Target {Goal}.` last, after the nudge. Singular/race-day edges follow §2.

### Style 3 — Auto run classification

- Label: `Auto run classification`
- Hint: `We detect Easy, Tempo, Long, Recovery, or Intervals from each run and name it in the description.`
- Output: base template with the detected `{RunKind}` emphasized first:
  - `Tempo run. 1 day to go for Vedanta Delhi Half Marathon.`
  - Goal variant: `Tempo run. 1 day to go for Vedanta Delhi Half Marathon. Target sub-2.`
- Rules: kind vocabulary fixed to `Easy / Tempo / Long / Recovery / Intervals`; fall back to `Easy` when unsure; classification never alters the title. Singular/race-day edges follow §2, with kind still first on race day (e.g. `Tempo run. Race day for Vedanta Delhi Half Marathon.`).

Manage-page helper copy (shared):

- Section heading: `How your runs update`
- Note under styles: `Applies to future runs only. Your Strava titles are never touched — only descriptions.`

---

## 5. CTA and consent microcopy

Connect button:

- Ready state: `Connect with Strava`
- Gated state (no race picked yet): `Pick a race first — then connect`
- Button flips to ready only after a race is selected. Mock button does nothing real; production uses the official Strava OAuth flow.

Hero big-button CTA (locked 2026-10-10, Lane 09-copy):

- Primary: `Pick your race` — scrolls to the race picker. Kept verbatim with the §1 lede and the gated connect state so the page repeats one action phrase.
- Fallback: `Start chasing your PR` — motivational alternate for campaign/goal-forward views (pairs with Alternate B). Same target as primary (race picker), never a direct Strava write.
- Candidate scoring (clarity / punch, 1–5):
  - `Pick your race`: clarity 5 (names the exact action) / punch 4 (short, active, warm) — best combined total. Locked primary.
  - `Select your race`: clarity 5 (same action) / punch 2 (formal, dropdown-flavoured) — rejected: says the same thing with less energy.
  - `Get started`: clarity 2 (started on what?) / punch 3 (familiar but bland) — rejected: too generic for a one-action hero.
  - `Start chasing your PR`: clarity 3 (outcome, not the action) / punch 5 (most emotional, echoes headline `go for your next PR`) — locked fallback.
- Rules: hero CTA is page copy only — it never appears inside a Strava activity, and clicking it never writes anything (description-only rule holds; titles never touched). Brand label stays `Compatible with Strava` wherever the CTA view carries attribution.

Fine print (stays adjacent to the CTA):

> Connect uses the official Strava flow (scopes: read + activity:write). Only your own activities are updated, and only with your consent. Your activity titles are never changed — countdowns go in descriptions only. You can disconnect anytime — future updates stop and past runs stay as they are. [Find more races on MyNextBib](https://mynextbib.com).

Post-connect confirmation:

- `Connected. Future runs for {Race} will carry the countdown in their descriptions.`

Disconnect / revoke:

- Link label: `Disconnect Strava`
- Confirm line: `Disconnecting stops future description updates. Past runs stay as they are.`

Attribution footer (unchanged contract):

- `Race data: MyNextBib feed snapshot · generated {date} · {count} events`
- Per-race link reads: `Register for {race} on MyNextBib`
- Also: `Find more races on MyNextBib` → `https://mynextbib.com`
- Also: `mynextpr · writes descriptions, never titles. Not endorsed by Strava.`

Veto list (never ship):

- Never "powered by Strava", "in partnership with Strava", "endorsed by Strava", or the Strava logo.
- Never "written into its Strava title" in production copy — that phrasing is a mock-preview placeholder only.
- Never request scopes beyond `read` + `activity:write`.

---

## 6. Copy-freeze proposal (Lane 09-copy increment — approval gate, description-only)

Status: proposed freeze. No string in §§1–5 changes after approval except through a new lane increment. All strings below are description-only (Strava activity description field); titles are never touched. Brand label stays `Compatible with Strava` only.

### 6a. Locked strings (frozen on approval)

- Homepage headline (primary): `Track your goal and go for your next PR` + lede `Pick your race. Every run you log gets its countdown added to the run's Strava description — automatically.` + sub `Three taps: distance, month, race. Then connect Strava and forget about it.`
- Alternates A/B verbatim per §1 (countdown-forward `Every run counts down to race day`; goal-forward `Set the target. Chase it every run.`), one headline per view only.
- Base description template: `{N} days to go for {Race}. {RunKind} run.` + goal append `Target {Goal}.` last; singular (`1 day to go`), race-day (`Race day for {Race}. {RunKind} run.`), and past-race (no line written) edges per §2.
- Run-kind vocabulary: exactly `Easy / Tempo / Long / Recovery / Intervals`, default `Easy` when unsure.
- Motivational nudge rotation (fixed order, second sentence only, no emojis, no all-caps): `One run closer.` / `Stack the miles.` / `Trust the buildup.` / `Keep showing up.` — goal variant appends `Target {Goal}.` after the nudge.
- Style 3 kind-first order: `{RunKind} run. {N} days to go for {Race}.` (+ `Target {Goal}.` when set).
- CTA states: ready `Connect with Strava`; gated `Pick a race first — then connect`. Hero big-button: primary `Pick your race`, fallback `Start chasing your PR` (both scroll to race picker; page copy only). Fine print, post-connect (`Connected. Future runs for {Race} will carry the countdown in their descriptions.`), disconnect (`Disconnect Strava` / `Disconnecting stops future description updates. Past runs stay as they are.`), manage heading (`How your runs update`), style labels/hints, futures-only note, attribution footer, and veto list — all verbatim per §§4–5.
- Mock tag stays `MOCK · Compatible with Strava`; wordmark stays `mynextpr`.

### 6b. Open items (need decision before freeze)

1. Nudge rotation order and reset rule: keep listed order cycling per run, or randomize without repeat — which one?
2. Style 3 race-day kind-first sentence: keep `Tempo run. Race day for Vedanta Delhi Half Marathon.` or fall back to base order on race day?
3. Gated CTA wording: keep em-dash form `Pick a race first — then connect` or switch to colon form for small buttons?

### 6c. Per-style examples (same run for comparison; run logged 2026-10-03, race `Delhi Half Marathon` 2026-10-18, N = 15, kind Easy, no goal)

- Style 1 — Days to go: `15 days to go for Delhi Half Marathon. Easy run.`
- Style 2 — Motivational: `15 days to go for Delhi Half Marathon. Easy run. One run closer.`
- Style 3 — Auto run classification: `Easy run. 15 days to go for Delhi Half Marathon.`

With goal `sub-2` (same run):

- Style 1: `15 days to go for Delhi Half Marathon. Easy run. Target sub-2.`
- Style 2: `15 days to go for Delhi Half Marathon. Easy run. One run closer. Target sub-2.`
- Style 3: `Easy run. 15 days to go for Delhi Half Marathon. Target sub-2.`
