# v5 Worker Contracts

Source of truth for this doc: `v5/mock.html`, `v5/events.snapshot.json`, `v5/sync_events.py`
(snapshot generated `2026-10-03`, 15 events). No other file is in scope.

## 1. File-ownership map (exact, no overlaps)

| Area | Owner | Files / blocks | May edit | Must NOT touch |
|------|-------|----------------|----------|----------------|
| Hero / animation block | **topfold** | `v5/mock.html` only: `.mast`, `.wordmark`, `.mocktag`, `.lede`, `.sub` markup + CSS (lines 19–26), mast/lede divs (lines 75–80) + any hero animation added inside those selectors | Hero copy, hero CSS, hero animation keyframes scoped to hero selectors | Anything under Setup or QA areas; `#buckets`, `#months`, `#races`, `#goal`, `#bibcall`, `.preview`, `.status`, script `EVENTS`/render functions, `events.snapshot.json`, `sync_events.py` |
| Setup block (picker) | **picker** | `v5/mock.html`: sections `#s1`–`#s4`, `#buckets`, `#months`, `#races`, `#goal`, `#bibcall`, `.preview` countdown/status, embedded `EVENTS` array + `renderBuckets/renderMonths/renderRaces/statusText/renderPreview` + footer provenance line; `v5/events.snapshot.json` (generated artifact, refresh via `v5/sync_events.py`); `v5/sync_events.py` (feed glob, bucket map, dedupe) | Picker steps, race list, goal input, bib link (`bibUrl`), preview text, snapshot refresh | Hero selectors listed above; acceptance checklist below |
| Acceptance checklist | **QA** | This section (§5) of `v5/worker-contracts.md` only | Checklist text | No product code: zero edits to `mock.html`, `events.snapshot.json`, `sync_events.py` |

Rules:

- One owner per block. Cross-block changes require handing the edit to the owning lane.
- `v5/worker-contracts.md` itself: lanes may propose text, QA merges checklist edits.
- Do not touch any other file.

## 2. Shared light-theme tokens (read-only for all lanes)

Defined in `v5/mock.html` `:root` (lines 8–11). Use exactly; do not redefine per-lane.

```css
--ink: #191412;
--muted: #6f645c;
--line: #e7e0d8;
--paper: #ffffff;
--accent: #fc5200;   /* Strava orange — CTA + countdown highlight only */
--panel: #201a16;    /* dark preview panel only */
```

Constraints:

- Page background is `--paper` (`#ffffff`), body text `--ink`. Light theme only — no dark-mode inversion of the page.
- Muted/hint text uses `--muted`; hairlines use `--line`.
- `--accent` is reserved for the Strava CTA (`.strava`), selected-race inset bar, `.num` step numbers, and the dashed `.bibcall` border. Do not use it for body text or large surfaces.
- `--panel` (`#201a16`) is used only for the `.preview` panel with light text `#f5efe8` / `#b9a99c`. Do not restyle other blocks as dark panels.
- Chips: unselected white bg + `--ink` 1px border; selected `--ink` bg + white text. Font stack: `system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif`; monospace: `ui-monospace,SFMono-Regular,Menlo,monospace`.
- Max content width 680px (`.wrap`).

## 3. Subtitle-only rule (description, NEVER title)

- Production writes the countdown string (`statusText()` output, e.g. `"<Race> — N days to go — Target <goal>"`) into the Strava activity **description** only.
- NEVER write to, overwrite, prepend, or append to the Strava activity **title**. The user's own title is sacred.
- The `mock.html` `.preview` panel header "YOUR STRAVA TITLE AFTER EVERY RUN" and the lede "written into its Strava title" are **mock placeholders** for preview only. Production copy must say description, and topfold/picker must not extend the title-preview pattern into real Strava API calls.
- Character-count display (`#charcount`) is a mock affordance; description limits, not title limits, govern production.
- Goal suffix (`— Target <goal>`) is free text appended inside the description string only.

## 4. Strava consent / brand constraints

Derived from `mock.html` preview/fine-print block (lines 108–116):

- OAuth via the official Strava flow with scopes `read` + `activity:write` only. No broader scopes.
- Update **only the authenticated user's own activities**, only after explicit connect consent. Mock `Connect with Strava` button does nothing real; production connect must gate on a selected race ("Pick a race first — then connect").
- Brand: the only allowed Strava-adjacent label is the mock tag `MOCK · Compatible with Strava`. Never claim endorsement, partnership, or "powered by Strava". Do not use the Strava logo; CTA button uses `--accent` (`#fc5200`) with label `Connect with Strava`.
- Fine print must stay adjacent to the CTA: consent + own-activities-only + scope note.
- Attribution: `Race data: MyNextBib feed snapshot · generated <date> · …` footer plus `Register for <race> on MyNextBib` bib link (`bibUrl()`: relative paths prefixed with `https://mynextbib.com`; absolute URLs passed through) and `Find more races on MyNextBib` link (`https://mynextbib.com`).

## 5. Acceptance checklist (QA owns)

- [ ] Hero renders light theme (`#ffffff` bg, `#191412` text) within 680px wrap; no dark page, no layout shift in setup block.
- [ ] Picker flow: distance chip → month chips (counts match snapshot buckets) → race list (day label, city, buckets, days-left) → optional goal → preview string `<Race> — N days to go[ — Target <goal>]`.
- [ ] Empty states: "Nothing here in this snapshot." / "No … races in this snapshot." when filters match nothing.
- [ ] Bib link resolves via `bibUrl()` and reads `Register for <race> on MyNextBib`.
- [ ] Contract violation checks: no code path writes activity title; CTA gated on race selection and scopes `read` + `activity:write`; `Compatible with Strava` wording only; fine print + MyNextBib attribution present.
- [ ] Data freshness: footer shows snapshot `generated` date and event count matching `events.snapshot.json` (`count`, `generated`).
