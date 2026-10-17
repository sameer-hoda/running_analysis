# 4. Privacy and compliance

Summary of the [API Agreement](https://www.strava.com/legal/api) (2026) and [API Policy](https://www.strava.com/legal/api_policy) (2026) as applied to this app.

## Data rules we follow

- One athlete's data only to that athlete. No cross-user display, even of public data.
- Purpose-limited: countdown descriptions, nothing else.
- No AI training, grounding, embeddings, or RAG on Strava data.
- No aggregation, analytics, advertising, resale, or third-party transfer.
- No scraping or bulk export. Webhooks instead of polling.
- Cache: no activity content cached at all. A stamped-ID dedup log (IDs plus timestamps) is pruned to the last 7 days on every write. User deletions reflected promptly; full delete immediate, always within 30 days.

## User rights (all live in-app)

- Pause, Disconnect, Download my data (`GET /api/export`), Delete my data (`POST /api/delete-account`) on the Manage page.
- Revoking in Strava settings purges the athlete here automatically.
- Public [privacy](../v6/privacy.html), [terms](../v6/terms.html), [support](../v6/support.html) pages state data types, collection method, withdrawal, and deletion.

## Brand rules

- Text “Connect with Strava” buttons link to the official OAuth authorize endpoint.
- Interoperability wording is only “Compatible with Strava”, with explicit no-endorsement notes.
- “View on Strava” link format for Strava data links. No Strava logo, name, or icon in the app name or artwork.

## Security

Tokens live server-side only, never in pages, logs, exports, or the repo. Breach notification to Strava legal within 24 hours if ever needed. Support contact: a private on-site form (`support.html` → `POST /api/support`)
stored in a server-side inbox read only by the operator — never published,
never a public tracker, no mailbox claimed.
