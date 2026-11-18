# 6. Approval pack

Path to all-user access: self-upgrade to 10 athletes in [API settings](https://www.strava.com/settings/api), then submit [the review form](https://share.hsforms.com/1VXSwPUYqSH6IxK0y51FjHwcnkd8). Admission is discretionary with no fixed SLA. Owner-side status lives in the [approval tracker](../deploy/strava-approval-tracker.md).

## Review checklist (all done in code)

- Minimal scopes with per-scope justification ([oauth and scopes](02-oauth-and-scopes.md)).
- Description-only writes; title never read or written (engine self-test).
- Per-athlete storage, isolation, revocation purge, export and delete endpoints.
- Public privacy, terms, and support pages linked from every footer.
- Official OAuth endpoint for sign-in; Compatible-with-Strava wording only.
- Webhook-driven updates; no polling storms; `no-store` API responses.

## Strava API settings — Application description (paste exactly)

> Manual step for the owner (a repo edit does not update Strava settings):
> open [API settings](https://www.strava.com/settings/api), replace the
> Application description with the two sentences below, and save.

```text
mynextpr adds a countdown to your chosen race to the description of your Strava runs. Activity titles are never changed.
```

Checked against the final code: stamping writes the countdown block into the
activity description only (`v6/server.py` + `v6/update_engine.py`); titles
are never read or written (pinned by automated tests).

## Still needed from the owner

1. Create the `support@mynextpr.com` mailbox.
2. Paste the Application description above into Strava API settings and save.
3. Redeploy to EC2.
3. Screenshots of every screen showing Strava data plus the Connect button, and a short OAuth video.
4. Submit the form, then send the email below to `developers@strava.com`.

## Submission email (plain text, copy as-is)

```
Subject: Production access request — mynextpr.com — Client ID 140606

Strava developer team,

App mynextpr.com, Client ID 140606, requests Standard tier production access.

What it does: user picks a race, connects Strava, and we write a countdown line into that user's own new run description. Reads are limited to finding the new activity. Writes touch description only. Titles are never changed.

Scopes requested: read, activity:read, activity:write. Webhook-driven, no polling.

Callback domain: mynextpr.com. Redirect: https://mynextpr.com/exchange_token.

Compliance: per-user display only, no activity content cached (stamped-ID dedup log pruned to 7 days), deletion completes promptly and always within 30 days, public privacy policy and support contact on site, official Connect buttons, no AI use, no aggregation or resale.

Screenshots and OAuth video attached. Please advise next steps.

Thanks.
```
