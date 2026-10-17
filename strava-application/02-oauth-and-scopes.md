# 2. OAuth and scopes

## Flow

1. Runner picks an upcoming race (Connect stays disabled until then).
2. App redirects to `https://www.strava.com/oauth/authorize` with client ID, redirect URI, `response_type=code`, scopes, and race details in `state`.
3. Runner approves or declines on strava.com. The app never sees the password.
4. `GET /exchange_token?code=..` swaps the code server-side (secret never leaves the server), stores per-athlete tokens, sets an `mnp_athlete` cookie, redirects to `manage.html`.
5. Short-lived access tokens refresh automatically. Disconnect revokes remotely and deletes locally.

## Scopes (minimal set)

- `read` — identify the athlete (ID, name for the Manage page).
- `activity:read` — fetch the new run and read its current description so the countdown merges without wiping the runner's own text.
- `activity:write` — write the countdown block into the description. Nothing else is written, and `name`/`title` is never sent.

No `read_all`, `profile:read_all`, or broader scopes.

## Consent

The connect screens state the scopes, description-only writes, own-activities-only, and how to disconnect or delete — next to the button, before approval. See [privacy and compliance](04-privacy-compliance.md).
