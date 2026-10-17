# 1. Overview

mynextpr writes a race countdown into the **description** of a runner's own new Strava runs. Activity titles are never changed. Stamping stops by itself after race day, and disconnecting stops it immediately.

## Live endpoints

- Site: [mynextpr.com](https://mynextpr.com)
- Health: [mynextpr.com](https://mynextpr.com) homepage (200), `/api/status` (connection + race).

## Strava app facts (public, no secrets)

- Client ID: `140606`.
- Authorization Callback Domain: `mynextpr.com`.
- Redirect URI sent by the code: `https://mynextpr.com/exchange_token`.
- Scopes: `read`, `activity:read`, `activity:write`.
- Webhook subscription: ID `377414` on `https://mynextpr.com/webhook`, Strava-verified.
- Writes: activity `description` only. Reads: identity, new-run lookup, month/year totals for the countdown line.

## What it is not

No leaderboards, no cross-athlete display, no analytics, no AI use, no resale of data, no scraping. One athlete's data is shown only to that athlete.
