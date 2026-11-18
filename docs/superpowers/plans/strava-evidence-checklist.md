# Strava review evidence checklist (refresh after fixes)

Owner-only steps. Do not reconnect OAuth, write an activity, or submit
anything to obtain evidence. Missing captures are listed with the approval
each needs. The five existing captures in the private review folder stay
preserved and labelled `captured-before-fixes` — do not overwrite them.

## Synthetic (local, no approval needed)

| # | Place | What to capture | How |
|---|---|---|---|
| S1 | Homepage hero demo (`v6/index.html`) | Fictional "You" run card with countdown + "Example run" hint | Serve `python3 v6/server.py`, screenshot mobile + desktop |
| S2 | Hero mock cards (`v6/hero.html`) | Before/After cards, fictional "Alex Demo", MOCK tag | Same local serve, motion on + reduced-motion |
| S3 | Race picker (`v6/picker.html`) | Distance → month → race flow, Connect disabled until race picked | Click through locally |
| S4 | Connect page (`v6/connect.html`) | Connect button + scope explanation + consent lines | Screenshot incl. consent section |
| S5 | Manage demo (`v6/manage.html`, signed out, no server) | "Example Harbor Half Marathon" + visible "Demo preview" badge | Serve static only (no backend) or clear site data |
| S6 | Manage demo (JS disabled) | Same page with JS off: fictional example + badge, no countdown errors | Browser JS-off mode |
| S7 | Privacy analytics controls (`v6/privacy.html`) | "Analytics consent" section: not-set → accept → accepted; then reject → rejected | Click through; confirm login/session unaffected |
| S8 | Consent banner (any page, fresh profile) | Banner text, Accept/Reject, no gtag request before choice (devtools network) | Fresh profile, network tab filtered `googletagmanager` |

## Real integration (needs owner action — see approvals below)

| # | Place | What to capture | Approval needed |
|---|---|---|---|
| R1 | OAuth consent screen (strava.com) | Official Strava authorize page showing `read, activity:read, activity:write` | Owner reconnects OAuth (explicit approval) |
| R2 | Manage connected view | Real race, real countdown, real totals for the owner's athlete | Same session as R1 |
| R3 | Stamped activity description | One real run description after a real stamp (shows countdown block + totals, title unchanged) | Owner logs a real run or re-stamps own activity (explicit approval — writes own activity only) |
| R4 | Webhook health (server-side) | Subscription still active + recent delivery log from Strava settings / server log | Owner opens Strava API settings (read-only) |
| R5 | Live EC2 revision | Deployed commit == branch HEAD after owner deploys + health check | Owner deploys (explicit approval, separate step) |

## Notes

- R3 must use only the owner's own authorised data. Never other athletes' data or credentials.
- The short OAuth walkthrough video is optional (older pack item, not a stated form requirement).
- Do not claim screenshots/tests completed until captured. S1–S8 can be done
  locally today; R1–R5 each wait on the approval in their row.
- Webhook health and the live EC2 revision are currently unverified; a
  successful homepage health check does not verify them.
