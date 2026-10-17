# v6 Design Critique — skeptical PM review

READ-ONLY review. No code changed. Grounded in the actual v6 pages
(`index.html`, `hero.html`, `picker.html`, `goal.html`, `connect.html`,
`manage.html`) plus screenshots `/tmp/audit-{index-desktop,index-mobile,
picker,picker-filtered,hero,goal,connect,manage}.png`.

Method: `.agents/skills/gstack/plan-design-review` + `design-review`
7-pass ratings (0-10). A 10 is defined per pass. Mode verdicts use the
design-review classifier: index/hero = PERSUADE, picker/goal/connect/manage
= OPERATE.

## Verdict up front

v6 is a strong, disciplined system with one voice problem: **two heroes,
three funnels, two goal inputs, two race feeds.** A first-time visitor meets
a confident landing page, then a picker that defaults to a "race day today"
edge case, then discovers goal-entry and connect flows exist in two places
each. Nothing here is ugly. The risk is not taste, it is a user who quietly
wonders "wait, which page is the real one?" and never comes back. Fix the
funnel before polishing pixels.

## Scores

| Pass | Score | One-line reason |
|------|-------|-----------------|
| 1. Information Architecture | 5/10 | Two conversion pages, three connect paths, no canonical funnel |
| 2. Interaction State Coverage | 7/10 | Picker/connect/manage states are careful; index/hero have no failure states |
| 3. User Journey & Emotional Arc | 6/10 | Before/after story lands; first-run default (race-day-today) kills momentum |
| 4. AI Slop Risk | 7/10 | No gradients, no card grids, real restraint; system-ui display voice + numbered labels are the tells |
| 5. Design System Alignment | 8/10 | Tokens used consistently; connect.html drifts (stale feed, free-text goal) |
| 6. Responsive & Accessibility | 7/10 | Careful ARIA + reduced-motion; real gaps (aria-disabled buttons, touch/contrast nits) |
| 7. Unresolved decisions | — | 9 questions below the team must answer |

## Pass 1: Information Architecture — 5/10

**What a 10 looks like:** one conversion page, one ordered funnel
(pick → goal → connect → manage), every page knowing its step number, no
two pages answering the same question differently.

**What v6 actually is:**
- `index.html` and `hero.html` are both plausible homepages with different
  headlines, different ledes, different example races (Delhi Half, 8 days vs
  Tata Mumbai, 34 days), and different story treatments (side-by-side drifting
  cards vs crossfading single-card loop with pause control). Screenshots
  confirm they read as two designs, not one design with variants. Which ships?
- `picker.html` has its own "Connect with Strava (mock)" button in the sticky
  panel. `connect.html` is a separate 3-step (Race → Goal → Connect) flow with
  its own race list and its own goal input. `goal.html` is a third place stating
  "Step 04 / 04". So connecting lives in three places; goal-setting in two
  (picker panel free text `1:45:00` vs goal.html structured H/M/S). The picker
  panel goal and goal.html goal even produce different description-line formats
  ("Goal time: 1:45:00." vs "Goal: 2:00:00.").
- `connect.html` hardcodes 3 races (`EVENTS`, GENERATED 2026-10-03) while
  `picker.html` loads 104 from `races.snapshot.json` (generated 2026-10-10).
  Same product, two truths, one of them a week stale.
- Cross-linking is thin: index links to picker and manage ("Review description
  styles"); picker never mentions goal.html or connect.html; manage never links
  back to picker to change races (the "Your race" section is static text).

**User feeling:** "I picked a race, set a goal, and now there is another page
asking me for both again. Did my choices save? Where am I in this flow?"

## Pass 2: Interaction State Coverage — 7/10

**What a 10 looks like:** every surface specifies loading, empty, error,
success, and past/edge states in user-visible words, with no dead ends.

**Working well:**
- Picker: feed-load failure gets a real error panel ("Feed unavailable" +
  recovery note); zero results get warmth + a working Clear action; past races
  are labelled "passed" and gate Connect with an explanatory note; search has
  Escape-to-clear. This is the best-covered page in v6.
- Connect: past-race and no-race gates change button + status text; disconnect
  uses a two-step inline confirm with honest consequence copy ("already written
  stay as they are").
- Manage: connected / paused / disconnected tri-state renders through
  statusline, dot, pills, and switch together; switch goes inert while
  disconnected.

**Gaps:**
- Index/hero have no failure posture at all: the countdown script silently
  keeps static text when the race passes (`if (text === null) return`), so the
  hero claim quietly rots after race day with no "race passed, pick another"
  state. A conversion page whose hero can go stale without anyone noticing.
- Picker's default selection is `firstUpcoming()`, which today resolves to a
  "race day today" race (both picker screenshots show "race day today" in the
  panel). The funnel's opening frame is its rarest edge case.
- Goal.html pre-fills defaults (Half → 2:00:00) while calling the field
  "optional" with a Skip button: three simultaneous answers to "do I need
  this?" Prefilled + optional + skip = the user cannot tell what Continue
  means without experimenting.
- Manage style "Motivational" advances the nudge rotation on re-click of the
  active option — invisible behavior with no affordance. "Auto run
  classification" claims to name runs but the mock only reorders the sentence;
  the preview overpromises what the copy delivers.

## Pass 3: User Journey & Emotional Arc — 6/10

**What a 10 looks like:** 5-second visceral ("I get it"), 5-minute behavioral
("I did it, it worked"), 5-year reflective ("this is my training companion").
Storyboard: land → believe → pick → connect → first stamped run → race day.

**Working well:** the before/after transformation story is the emotional core
and it works. "Your boring update, transformed" / "The same Easy 5k, before
and after" shows the product's value in one glance, and the dark description
preview panel is the single best trust-building element in v6: users see the
exact string before granting write access. Scope fine print adjacent to every
CTA ("titles are never changed") spends the goodwill reservoir wisely.

**What breaks the arc:**
- The 5-second test passes on hero ("34 days to go for Tata Mumbai Marathon"
  with a concrete number) and only half-passes on index (abstract lede, no
  number above the fold). The two pages A/B-test each other unintentionally.
- The 5-minute test fails at the picker default: the user's first touch of the
  core loop shows "race day today," the one day the countdown is least
  exciting. First-run magic should default to a race 2-6 weeks out, not today.
- The reflective horizon is unaddressed: what happens on race day + 1? After
  the race passes, manage shows a frozen "8 days" (hardcoded `N = 8`); nothing
  invites picking the next race. A product named "mynextpr" has no next-race
  moment. That is the missing 5-year loop.
- Trust copy is repeated verbatim on every page (scopes, titles-never-touched).
  Repetition is correct at the connect moment; on manage, post-connection, it
  reads as protesting too much and crowds out what the user needs there
  (what will happen on my next run, exactly?).

## Pass 4: AI Slop Risk — 7/10

**What a 10 looks like:** zero hard-rejection hits, all litmus checks YES,
typography and texture that could only belong to this product.

**Hard-rejection check (all clear):** no generic SaaS card grid as first
impression; no purple/blue gradient; no centered-everything hero; no 3-column
feature grid; no carousel; no stock-photo hero; no glassmorphism. The restraint
is real: hairlines, one accent (Strava orange `#fc5200`, earned), calm
surfaces, utility copy on OPERATE pages. Litmus: brand unmistakable (wordmark +
orange `pr`) YES; one visual anchor (dark preview panel) YES; scannable by
headlines YES; one job per section mostly YES.

**The tells that remain:**
1. `--font-sans: system-ui, -apple-system, ...` (tokens.css) is the PRIMARY
   display voice — blacklist item 11, "I gave up on typography." The headlines
   survive on weight and tracking, but a running product with this much
   character in its copy deserves a display face with character. Cheapest
   premium-feel upgrade available.
2. Numbered-section labels (`01 Distance`, `02 City`, `04 / 04 Goal`) and the
   `MOCK · Compatible with Strava` eyebrow chip on every page trip the
   numbered-label / hero-eyebrow-chip detectors. Fine in a mock; do not let the
   numbering ship as the information hierarchy.
3. The before/after duo is two floating cards — one step from "cards as the
   default component." It earns the cards (the card IS the artifact here), but
   index animates both cards drifting on a loop while hero crossfades text
   inside one card: two motion concepts for one story. Pick hero's (pausable,
   single moment) — index's perpetual drift cheapens the artifact it shows off.
4. Copy smell: "Three taps: distance, month, race" is said on index, picker,
   and hero, but the picker needs 4+ interactions (search + 3 chip groups +
   race select + goal + connect). Users count. Do not promise three and
   deliver seven.

## Pass 5: Design System Alignment — 8/10

**What a 10 looks like:** every page resolves to tokens, one vocabulary for
shared concepts, no page inventing parallel components.

**Working well:** tokens carry the system genuinely — `--paper/--ink/--muted/
--line`, `--select` + `--select-bar` selected states, `--radius-control/
--radius-card/--radius-pill`, mono-for-data discipline, single dark panel as
the one contrast moment, accent reserved for CTA + countdown. Cross-page
consistency (masthead, fine print, footer disclaimers) is high.

**Drift, all in connect.html:** hardcoded 3-race list vs snapshot feed;
free-text goal (`sub-4`) vs structured H/M/S goal; `aria-disabled` + click
guard on the connect button vs picker's real `disabled` attribute; GENERAT
ED 2026-10-03 vs 2026-10-10. Connect reads as an older prototype that the
system outgrew. Either promote it to the canonical funnel step (feed +
structured goal + real disabled states) or delete it and let picker → goal →
manage be the funnel.

## Pass 6: Responsive & Accessibility — 7/10

**What a 10 looks like:** intentional per-viewport layouts, full keyboard
parity, screen-reader announcements that match sighted information, 44px
targets, 4.5:1 body contrast, no hover-dependent discovery.

**Working well:** skip link; roving-tabindex radiogroups with arrow/Home/End
support (picker results, manage styles); `aria-selected`/`aria-checked`
kept in sync; goal errors name fields, pair border with text + `aria-invalid`
(never color-alone); polite live regions gated to day-change, not keystroke;
`prefers-reduced-motion` respected everywhere with content resting in the
correct end state; themed `::selection`; visible focus rings from tokens.

**Gaps:**
1. Connect's CTA uses `aria-disabled="true"` on a still-focusable, still-
   clickable button with a JS guard. Sighted keyboard users can focus a dead
   button; some AT will not announce the disabled state. Use native `disabled`
   like the picker does.
2. Picker city chips live in a 148px scroll well with dozens of pills —
   operable but punishing (fine motor + screen-reader list fatigue). A
   type-to-narrow city input or region grouping would serve 104 races better
   than a scroll box.
3. The 860px breakpoint collapses picker to single column with the sticky
   summary panel dropping below the fold (`position: static`) — on mobile the
   preview/CTA, the highest-converting element, sits under the entire filter
   stack. The mobile screenshot path deserves the panel first or a sticky
   bottom CTA bar.
4. Touch targets: race rows and steps rely on padding (13px vertical) that
   likely lands under 44px; `.fineprint`/`--text-hint` small muted text should
   be contrast-checked against 4.5:1 on `--paper`.
5. Browser surfaces unthemed: caret is set (`caret-color`), but focus-ring,
   scrollbar, and numeral rendering beyond `tabular-nums` are defaults — the
   reflex check the system otherwise passes everywhere else.

## Tough questions the team must answer

1. Which homepage ships — index or hero? What experiment decides, and what
   happens to the loser (redirect, delete, or eternal confusion)?
2. What is the canonical funnel — picker-with-panel-connect, or
   picker → goal.html → connect.html → manage? Who owns each step's state?
3. Why does connect.html carry its own 3-race feed and free-text goal instead
   of the snapshot feed and structured goal? Merge or delete?
4. What does the picker default-select on first load, and why is "race day
   today" acceptable as the product's first impression?
5. Is the goal required or optional? Prefilled default + "optional" label +
   Skip cannot all ship; which one goes?
6. What does the user see the day AFTER their race — on the homepage, the
   picker, and manage? Where is the "pick your next race" loop?
7. What does "Motivational" and "Auto run classification" actually write to
   Strava in production? The manage preview currently demos copy the backend
   may not honor.
8. What is the real tap count from landing to connected, and does "Three taps"
   survive measurement? Rewrite the claim or redesign the flow to earn it.
9. Which display typeface replaces system-ui for headlines, and does it survive
   the tabular-nums countdown rendering the brand depends on?

## Recommendation: how the conversion page should improve

Ship **hero.html as the single conversion page**, with these changes, and
retire index.html to a redirect:

1. **Keep hero's concrete lede** ("34 days to go for Tata Mumbai Marathon" as
   a live number) — it passes the 5-second test where index's abstract lede
   does not. Keep the accent second line; it is the one place expression
   belongs.
2. **Keep hero's story treatment** (pausable crossfade + motion toggle +
   progress bar) and delete index's perpetual drift. One authored motion
   moment, user-controlled, resting on the countdown.
3. **Adopt index's JS discipline** (change-gated live region, past-race guard
   with a "race passed, pick another" state instead of silent stasis) so the
   hero never rots after race day.
4. **Fix the CTA adjacency:** keep the scope fine print, but add the one line
   the funnel needs — "Takes ~1 minute. Preview your exact description before
   anything is written." The current fine print answers fear; it never answers
   effort.
5. **Add the missing proof strip** between story and steps: one line of
   specificity the page currently lacks — feed size ("104 upcoming races"),
   write scope ("descriptions only, titles never touched" as a check-list, not
   a paragraph), and cost ("free"). Three facts, hairline row, no new section
   chrome.
6. **Resolve the headline redundancy:** "Track your goal and go for your next
   PR" + "Three taps..." + steps that repeat the same three nouns. Cut the
   setup sentence from the hero (it lives in step 1) and let the headline,
   concrete lede, and CTA own the fold.
7. **Display typeface.** Before any other polish: replace the system-ui display
   voice with a chosen face, verify tabular numerals for countdowns, and re-
   shoot the audit screenshots. This single change moves Pass 4 from 7 to 9.

Explicitly out of scope for the conversion page: funnel unification (separate
decision), feed/goal consolidation (separate decision), mobile sticky CTA
(Pass 6 fix, same branch OK), manage post-race loop (follow-up).
