# mynextpr V5 — project context

Date: 2026-10-10
Workspace: `/Users/sameerhoda/Projects/running_analysis`
Scope for the next task: `v5/` only. `v1/`, `v2/`, `v3/`, `v3-tripo-cloud/`, and `v4/` are legacy and untracked.

## Current state

`v5/` is a static prototype/mock stage, not a final product:

- No backend.
- No Strava OAuth implementation.
- No webhook receiver.
- No token storage.
- No live Strava activity updates.
- All “Connect with Strava” buttons are mocks.
- Pages can be opened directly in a browser; there is no build or server requirement.

It is also not a single final landing page. There are overlapping prototypes that need consolidation.

## Product intent

Build a simple mynextpr experience:

1. Show the value proposition on a landing page.
2. Let the user quickly select a target race.
3. Optionally set a target finish time.
4. Connect Strava.
5. After each run, update the Strava activity **description/subtitle only**.
6. Never modify the Strava activity title.
7. Use MyNextBib race data and include a MyNextBib registration callout.

Current working Strava constraints carried forward:

- Minimum scopes: `read` plus `activity:write`.
- Only update the authenticated user’s own activities.
- Require explicit consent.
- Production copy must say **description**, not title.
- Do not claim Strava endorsement or partnership.
- Privacy, support, deletion, webhook, rate-limit, and app-review requirements still need to be implemented before production.

## Important inconsistency to resolve

`v5/mock.html` still says the countdown is written into the Strava **title**:

- Lede: “written into its Strava title.”
- Preview header: “YOUR STRAVA TITLE AFTER EVERY RUN.”
- Fine print: “Titles update only on your own activities.”

That conflicts with the current subtitle/description-only decision and `v5/worker-contracts.md`. The next task should either remove, replace, or explicitly supersede `mock.html`.

## Current `v5/` files

- `[index.html](/Users/sameerhoda/Projects/running_analysis/v5/index.html)`
  - Closest current landing-page prototype.
  - Hero plus Strava description animation.
  - Small race teaser.
  - Links to `setup.html`.

- `[topfold.html](/Users/sameerhoda/Projects/running_analysis/v5/topfold.html)`
  - Isolated top-fold/hero prototype.
  - Strava-style activity card with a countdown/race-story loop.
  - Reduced-motion fallback.
  - Uses slightly different theme tokens from the worker contract.

- `[picker.html](/Users/sameerhoda/Projects/running_analysis/v5/picker.html)`
  - Curated race-search prototype.
  - Embeds 8 races.
  - Fuzzy/substring matching.
  - Month chips.
  - Optional goal.
  - Live description preview and character count.
  - Mock Connect button and proof state.

- `[setup.html](/Users/sameerhoda/Projects/running_analysis/v5/setup.html)`
  - Fuller setup prototype.
  - Embeds all 15 snapshot races.
  - Combines text search, distance chips, and month chips.
  - Goal field, description preview, mock Connect/Save buttons.
  - MyNextBib sign-up callout.

- `[mock.html](/Users/sameerhoda/Projects/running_analysis/v5/mock.html)`
  - Earlier combined distance/month/race/goal/preview prototype.
  - Contains the outdated title-based wording described above.

- `[events.snapshot.json](/Users/sameerhoda/Projects/running_analysis/v5/events.snapshot.json)`
  - Generated: `2026-10-03`.
  - Count: `15`.
  - This snapshot is now stale relative to 2026-10-10 and should be refreshed before further date-sensitive work.

- `[sync_events.py](/Users/sameerhoda/Projects/running_analysis/v5/sync_events.py)`
  - Reads local MyNextBib scraper files matching:
    - `~/Projects/mynextbib/v1/scraper_v2/*_events.json`
  - Filters for ISO dates on or after the run date.
  - Normalizes distances into `5K`, `10K`, `Half`, `Full`, and `Ultra`.
  - Skips cycling/duathlon/triathlon-style names.
  - Writes `events.snapshot.json`.
  - Live EC2 refresh is not wired into this repository.

- `[worker-contracts.md](/Users/sameerhoda/Projects/running_analysis/v5/worker-contracts.md)`
  - Original lane-ownership and theme/consent rules.
  - Useful constraints, but written around `mock.html`; update it if the page structure changes.

- `[agent-tabs.md](/Users/sameerhoda/Projects/running_analysis/v5/agent-tabs.md)`
  - Earlier proposed `topfold`, `picker`, and `qa` lane split.

- `[qa-report.md](/Users/sameerhoda/Projects/running_analysis/v5/qa-report.md)`
  - Date: `2026-10-03`.
  - Verdict: PASS on five checks.
  - Remaining items are minor/cosmetic, including theme-token drift.
  - Previous automated page checks used throwaway harnesses outside the repository; there is no durable committed test suite in `v5/`.

- `[.env.example](/Users/sameerhoda/Projects/running_analysis/v5/.env.example)`
  - Template only.
  - Contains no real credentials.
  - Uses placeholder Strava client ID/secret fields and local redirect URI.

- `[.gitignore](/Users/sameerhoda/Projects/running_analysis/v5/.gitignore)`
  - Ignores `.env` and Python cache/artifacts.

## Repository state

- Current branch: `main`.
- Latest commit: `04eb0a3 v5 mynextpr Strava countdown mock + worker outputs`.
- Local worker branches exist:
  - `mynextpr-picker`
  - `mynextpr-qa`
  - `mynextpr-topfold`
- No git remote is configured.
- Untracked items include:
  - `.DS_Store`
  - Root `.env`
  - `v1/`
  - `v2/`
  - `v3/`
  - `v3-tripo-cloud/`
  - `v4/`
- The root `.env` is untracked and must remain local-only. Do not commit it or paste its contents into chat, screenshots, or issues.

## Missing inputs

The next task does not yet have:

- User’s actual Strava screenshots.
- Stock activity image for landing-page animation work.
- Exact production description template.
- Timezone and days-left calculation rules.
- Race-date maintenance owner/process.
- Confirmation of which prototype becomes canonical.
- Nano Banana/Gemini image-generation requirements.
- Any Gemini API key; if used, it must remain server-side and must not enter the frontend repository.

## Suggested next-task boundaries

A clean next task should first decide:

1. Whether `index.html` becomes the canonical landing page.
2. Whether `setup.html` or `picker.html` becomes the canonical setup flow.
3. What happens to `mock.html` and `topfold.html`.
4. Exact Strava description wording and character handling.
5. Event-refresh cadence and canonical race-data source.
6. Whether the next task is design-only or may begin backend/OAuth/webhook work.
7. Strava compliance copy, privacy/deletion flows, and brand treatment.
8. Whether worker branches should be merged, rebased, or discarded.
