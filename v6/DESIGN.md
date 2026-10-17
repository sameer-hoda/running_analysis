# Design — mynextpr v6 visual world

World: **start-line minimalism.** A race bib pinned to a white wall: warm
paper ground, sharp warm-ink type, hairline rules, one orange accent spent
only where the runner acts or counts down. Mode: **Operate** — the visitor
completes a task (pick race, connect, manage styles), so scanability and
task clarity outrank expression; brand lives in precise details.

## Direction contract

- **THESIS:** The page is a start line, not a celebration. Everything serves
  the countdown number and the next action; nothing performs running. The
  category default this refuses: the heroic orange-drenched athlete banner
  with metric tiles and motivational noise.
- **OWN-WORLD:** Light paper (`--paper`), warm ink (`--ink`), hairline
  dividers (`--line`), tabular mono numerals, pill chips with ink-selected
  states, a single dark preview panel as the one contrast moment. Recognizable
  with all copy removed by its restraint: hairlines, mono counts, one orange.
- **STORY:** The visitor understands within seconds that picking a race puts
  a live countdown into their Strava descriptions, believes it touches
  nothing else, and connects — or manages styles — in three taps.
- **FIRST VIEWPORT:** Wordmark, lede, then the task itself: step chips and
  race rows in a single narrow column (`--layout-narrow`), CTA in Strava
  orange gated on race selection with scope fine print beside it, countdown
  status in mono. Mobile-first single column; two-column grid only on wide
  picker surfaces (`--layout-wide`).
- **FORM:** Brief-pinned direction (minimal, sharp, mobile-first, Strava
  orange accent) — beats the roll; no concept-seed round was dealt.
- **FINISH:** unreviewed and undocumented is unfinished; this build ends with
  the finish review, the verdict, DESIGN.md, and every shipping raster carrying
  its provenance

## Color strategy

**Restrained:** neutrals tinted warm from the world plus one accent. Orange
(`--accent`) is reserved for the Strava CTA, the selected-race inset bar,
step numerals, and the dashed bib-call border — never body text, never large
surfaces. The single dark surface is the `.preview` panel (`--panel` with
`--on-panel` text); nothing else goes dark. Light-only: no dark-mode
inversion exists and none is planned (owner veto).

## Type

System sans stack for UI, system mono stack for anything that counts or
ticks (countdowns, stats, days-left, char counts) with `tabular-nums`.
Wordmark `22px/800/-0.03em` with the accent span; hero display
`clamp(32px, 4.6vw, 52px)` topfold scale; body `1.45` line-height, 65–75ch
measure. No eyebrow kickers above headings; headings carry their own weight.
No gradient text; emphasis comes from weight and size.

## Components

- Chips: unselected white with ink hairline border; selected ink fill with
  white text. No orange-selected variant — selection is ink, accent stays
  reserved.
- Race rows: name (`15px/700`) over meta (`13px` muted); selected row gets
  the `--select` tint plus the `inset 3px 0 0` accent bar (inset shadow, not
  a `border-left` — the floor bans colored side borders above 1px).
- CTA: orange fill, `--accent-pressed` hover/active, `10px` control radius,
  gated on race selection with adjacent scope fine print.
- Cards/panels at `--radius-card 16px` with either border or shadow, never
  both (no ghost cards). Pills only for small controls.
- Countdown status line in mono `16px`; sync dot in `--ok` green only.

## Motion grammar

One authored moment per surface, exponential ease-out from an already-visible
default: the hero typing reveal or the before/after story fade — never both
competing, never identical entrances per section. Countdown ticks are text
updates, not motion. Reduced-motion policy per tokens: CSS motion collapses,
countdown text stays live, only the story loop gates in JS.

## Browser surfaces

Selection, caret, focus rings, and tabular numerals are themed from the
palette: 2px accent `:focus-visible` ring (2px offset); inside the dark
preview panel the ring flips to `--on-panel` with an accent halo so it stays
visible. `scroll-behavior: smooth` reverts to `auto` under reduced motion.

## Bans carried into every lane

No dark mode. No glass, blur decoration, or gradients. No gamification. No
endorsement claims, no Strava logo, no title writes. No secrets, network
calls, or external scripts. Token values are frozen — lanes consume via
`var()`, never hard-code hex; any change needs an explicit amendment note
in `v6/design-tokens.md` §7 and the `tokens.css` freeze comment.
