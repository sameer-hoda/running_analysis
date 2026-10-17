# v6 Canonical Design Tokens — FINAL

Source of truth for v6 color, type, spacing, radii, and motion.
Reconciles topfold / picker / setup / index drift against the
`v5/worker-contracts.md` §2 contract (which wins every conflict unless noted).
Companion file: `v6/tokens.css` (import it; do not redefine tokens per-lane).

Status: final. Verified against the §2 contract in this worktree —
all contract hex values are present in both files, `tokens.css` parses,
focus and reduced-motion rules are included, and neither file contains
secrets, credentials, or network calls.

Theme: **light only.** Page background is always `--paper` (`#ffffff`);
there is no dark-mode inversion of the page. The single dark surface is
the `.preview` panel (`--panel`).

## 1. Color

| Token | Value | Use |
|---|---|---|
| `--paper` | `#ffffff` | Page background |
| `--ink` | `#191412` | Body text, selected chips, mast rule |
| `--muted` | `#6f645c` | Hints, meta, secondary text |
| `--line` | `#e7e0d8` | Hairlines, card borders |
| `--soft` | `#f6f3f0` | Hover wash, light preview background |
| `--accent` | `#fc5200` | Strava orange — CTA + countdown highlight **only** |
| `--accent-pressed` | `#d94800` | CTA hover / active state |
| `--select` | `#fff4ee` | Selected-race row tint (with accent inset bar) |
| `--panel` | `#201a16` | Dark preview panel **only** |
| `--on-panel` | `#f5efe8` | Text on the dark panel |
| `--on-panel-muted` | `#b9a99c` | Secondary text on the dark panel |
| `--ok` | `#22a35c` | Sync-status dot **only** |

### Drift reconciled (all retire in favor of the canonical value)

- `--ink`: topfold used `#111214` (cool near-black). Retired — canonical
  stays the contract's warm `#191412`.
- `--muted`: topfold `#6b6f76`, picker/index `#6b625c`, setup `#6f625c`
  vs contract `#6f645c`. Retired — canonical is `#6f645c` (differences were
  visually negligible per the v5 QA report, but one value wins).
- `--line`: topfold `#e8e8e6`, picker/index `#e8e2dc`, setup `#e9e2dc`
  vs contract `#e7e0d8`. Retired — canonical is `#e7e0d8`.
- `--accent` casing (`#FC5200` vs `#fc5200`) is a non-issue; canonical
  spelling is lowercase `#fc5200`.
- `--soft`: setup `#f7f4f1` vs picker/index `#f6f3f0`. Retired `#f7f4f1`;
  canonical is `#f6f3f0` (majority + pairs with `--line`).
- `--wash` (topfold `#f6f6f4`) merges into `--soft`; one wash token only.
- Selected-row tint: mock `#faf6f1` vs picker/index `#fff4ee`. Retired
  `#faf6f1`; canonical `--select: #fff4ee`, always paired with the
  `inset 3px 0 0 var(--accent)` marker (`--select-bar`).
- `--accent-pressed: #d94800` (observed as the picker/index CTA hover,
  previously undocumented) is now a token so hover is not a magic value.
- `--ok: #22a35c` (observed once, index sync dot) is scoped to that dot;
  success/confirmation copy elsewhere uses `--ink`.

### Mismatch check (final verification)

No token mismatches remain: every color token in the table above is defined
with the same value in `v6/tokens.css`, and all eight §2 contract values
(`#ffffff`, `#191412`, `#6f645c`, `#e7e0d8`, `#fc5200`, `#201a16`,
`#f5efe8`, `#b9a99c`) are present in both files.

### Accent constraints (carried over from the v5 contract, still binding)

- `--accent` is reserved for the Strava CTA, the selected-race inset bar,
  `.num` step numbers, and the dashed `.bibcall` border. Never body text,
  never large surfaces.
- `--panel` is only the `.preview` panel with `--on-panel` / `--on-panel-muted`
  text. The picker's light preview box uses `--soft`, not `--panel`; do not
  restyle other blocks as dark panels.
- Chips: unselected = white bg + `--ink` 1px border; selected = `--ink` bg +
  white text. (The setup `chip.accent` selected-orange variant is retired —
  selection is ink, accent stays reserved per above.)

## 2. Type

Stacks (superset merge — render identically where the extra faces are absent):

- `--font-sans`: `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
  Inter, Helvetica, Arial, sans-serif`
  (contract base + topfold/picker observed `BlinkMacSystemFont` / `Inter`).
- `--font-mono`: `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`
  (contract base + setup observed `Consolas`).

`font-variant-numeric: tabular-nums` is required on anything that counts or
ticks: countdown text, stats, days-left labels, char counts, `.num`, `.hint`
numbers.

Scale (canonical sizes from the mock; hero display scale from topfold):

| Token | Value | Use |
|---|---|---|
| `--text-wordmark` | `22px / 800 / -0.03em` | `mynextpr` wordmark (`span` in accent) |
| `--text-lede` | `19px / -0.01em` | Lede paragraph |
| `--text-sub` | `14px` | Sub / muted supporting copy |
| `--text-h2` | `15px / -0.01em` | Step headings |
| `--text-hint` | `13px` | Hints, race meta |
| `--text-chip` | `14px / 600` | Chips |
| `--text-race-name` | `15px / 700 / -0.01em` | Race names |
| `--text-race-meta` | `13px` | Race meta lines |
| `--text-mono-sm` | mono `12px` | `.when` / `.left` / counts / fine print |
| `--text-status` | mono `16px` | Countdown status line |
| `--text-cta` | `15px / 800` | Strava CTA |
| `--text-display` | `clamp(32px, 4.6vw, 52px), 1.02, -0.03em` | Hero `h1` (topfold only) |

Body `line-height` is `1.45`; hero `.sub` may use `1.55–1.6`.

## 3. Spacing / layout

4pt base scale: `--space-1/2/3/4/5/6/8/10/16` = `4/8/12/16/20/24/32/40/64px`.
Component spacing follows the mock: wrap padding `32px 20px 64px`
(`--wrap-pad-top` / `--wrap-pad-x` / `--wrap-pad-bottom`), mast
`padding-bottom: 12px`, lede margin `22px 0 6px`, step `margin-top: 30px`,
chips gap `8px`, race rows `13px 4px`, preview `margin-top: 34px`,
footer `margin-top: 40px`.

Widths: `--layout-narrow: 680px` (single-column flow, mock canonical);
`--layout-wide: 1080px` (picker/index two-column grid; setup's `1060px`
retires into this — 20px difference, one value wins).

## 4. Radii

| Token | Value | Use |
|---|---|---|
| `--radius-xs` | `4px` | `mocktag`, mono labels |
| `--radius-tag` | `6px` | Distance tags, fine-print `code` |
| `--radius-control` | `10px` | Buttons, inputs, preview boxes |
| `--radius-card` | `16px` | Cards, panels, result lists |
| `--radius-pill` | `999px` | Chips, pills, eyebrows |

Drift reconciled: inputs/buttons observed at `6px` (mock), `9px` (setup),
`10px` (picker/index) → canonical `10px`. Cards/panels observed at `12/14/16px`
→ canonical `16px` (topfold `14px` card retires up; `12px` result-list radius
retires up). Tags observed at `5px` → `6px`. `999px` pills/chips and the `4px`
mocktag were already consistent. Brand-mark `7px` follows `--radius-tag`.

Borders / shadows: `--border-ink` / `--border-line` hairlines;
`--select-bar: inset 3px 0 0 var(--accent)` selected marker;
`--shadow-card: 0 12px 32px rgba(25,20,18,.08)` and
`--shadow-panel: 0 24px 60px -30px rgba(25,20,18,.28)` — both re-tinted from
topfold's drifted `#111214`-based shadow to the warm `--ink` base.

Focus: `:focus-visible` gets a `2px` accent outline (`2px` offset so the ring
clears card borders), observed in picker/setup, now canonical in `tokens.css`.
Inside the dark `.preview` panel the ring flips to a `--on-panel` outline with
a `--accent` halo (`box-shadow: 0 0 0 4px var(--accent)`) so it stays visible
on `--panel`. The mock had no focus style — that gap is closed, not preserved.

## 5. Motion + reduced motion

Canonical motion values (all previously undocumented except topfold's fade):

| Token | Value | Use |
|---|---|---|
| `--motion-fade` | `0.6s ease` | Topfold card-desc crossfade |
| `--motion-loop` | `4s` | Before/after story toggle interval (JS) |
| `--motion-tick` | `1s` | Countdown text refresh (JS interval, not CSS) |
| `--motion-typing` | `5s steps(46, end)` | Index hero typing reveal |
| `--motion-caret` | `0.8s step-end infinite` | Typing caret blink |
| `--motion-refill` | `2.4s ease-in-out infinite` | Index sync-bar slide |

Reduced-motion policy (binding, in `tokens.css`):

1. Content must never depend on animation — the countdown line is always
   present as static text first; animation only enhances it.
2. Under `prefers-reduced-motion: reduce`, all CSS transitions/animations
   collapse (CSS motion tokens go to `0s` plus a blanket duration guard;
   `--motion-loop` / `--motion-tick` are JS intervals and are gated in JS,
   not zeroed in CSS).
3. The 1s countdown **text** tick is a JS text update, not motion — keep it
   live under reduced motion. Gate **only** the 4s before/after fade loop in
   JS via `matchMedia('(prefers-reduced-motion: reduce)')`, leaving the
   countdown line static-visible. (Adopts v5 QA fix #2; topfold's current
   early-`return` that also kills the tick is the behavior being retired.)
4. `scroll-behavior: smooth` reverts to `auto` under reduced motion.

## 6. What v6 does NOT change

Product rules from `v5/worker-contracts.md` §§3–4 still bind every lane and are
not tokens: description-only writes (never the activity title), `read` +
`activity:write` scopes only, CTA gated on race selection, `MOCK · Compatible
with Strava` wording only, fine print adjacent to the CTA, MyNextBib
attribution + `bibUrl()` semantics. No secrets, no network calls, no external
scripts — verified absent in v5 QA and re-asserted here by inspection (this lane
adds no JS, no URLs, no credentials; both v6 files are CSS/prose).

## 7. Token freeze (FROZEN — approved 2026-10-10, Lane 01-design)

Every canonical value in §§1–5 is frozen exactly as written, mirrored in
`v6/tokens.css`. The frozen set, with exact values:

- Color (12 tokens): `--paper #ffffff`, `--ink #191412`, `--muted #6f645c`,
  `--line #e7e0d8`, `--soft #f6f3f0`, `--accent #fc5200`,
  `--accent-pressed #d94800`, `--select #fff4ee`, `--panel #201a16`,
  `--on-panel #f5efe8`, `--on-panel-muted #b9a99c`, `--ok #22a35c`.
- Type: both font stacks (§2, verbatim) + all 12 `--text-*` sizes, from
  `--text-wordmark 22px` through `--text-display clamp(32px, 4.6vw, 52px)`.
- Spacing/layout: `--space-1/2/3/4/5/6/8/10/16` = `4/8/12/16/20/24/32/40/64px`,
  `--layout-narrow 680px`, `--layout-wide 1080px`, wrap pads `32px/20px/64px`.
- Radii: `--radius-xs 4px`, `--radius-tag 6px`, `--radius-control 10px`,
  `--radius-card 16px`, `--radius-pill 999px`.
- Borders/shadows: `--border-ink`, `--border-line`,
  `--select-bar: inset 3px 0 0 var(--accent)`,
  `--shadow-card: 0 12px 32px rgba(25,20,18,.08)`,
  `--shadow-panel: 0 24px 60px -30px rgba(25,20,18,.28)`.
- Motion: `--motion-fade 0.6s ease`, `--motion-loop 4s`, `--motion-tick 1s`,
  `--motion-typing 5s steps(46, end)`, `--motion-caret 0.8s step-end infinite`,
  `--motion-refill 2.4s ease-in-out infinite`, plus the `:focus-visible` and
  `prefers-reduced-motion` rules verbatim.

What stays OPEN (not frozen by this proposal):

- New component-level tokens lanes may need — none proposed yet; add only by
  explicit amendment, never by silent per-lane redefinition.
- Per-page application/composition choices in `watchboard.html` and lane CSS
  (layout, copy, component structure that consumes — but never redefines —
  these tokens).
- Any future dark-mode inversion (out of scope; v6 is light-only).
- Product rules in `v5/worker-contracts.md` §§3–4 (still binding, versioned
  separately from this token freeze).

Post-freeze rule: any change to a frozen value requires an explicit
amendment note here and in the `tokens.css` freeze comment; lanes consume
tokens via `var()` and never hard-code hex. World authority is `v6/DESIGN.md`
(start-line minimalism); product truth is `v6/PRODUCT.md`.
