# mynextpr — every run, closer to race day

Pick a race, connect Strava, and every finished run gets a live countdown written into its activity **description**. Titles are never touched.

- Live: [mynextpr.com](https://mynextpr.com)
- Status: v6 live on EC2, preparing the Strava review submission for all-user access.

## How it works

1. Runner picks a race and an optional goal.
2. They approve on strava.com (scopes: `read`, `activity:read`, `activity:write`).
3. Each new run gets a countdown block appended to its description. Past race date? Stamping stops on its own. Disconnect any time.

## Repo map

- `v6/` — the live app: static pages plus a stdlib Python backend ([server backend](v6/server.py), [update engine](v6/update_engine.py)).
- `strava-application/` — the whole Strava application in one folder: overview, OAuth and scopes, architecture, compliance, deploy, and the approval pack.
- `deploy/` — Strava approval tracker (no host details or secrets).

## Docs

- [Strava application](strava-application/README.md) — start here for anything Strava.
- [Deploy and operations](strava-application/05-deploy-and-operations.md) — host details live in a private ops file outside the repo.
- [Approval tracker](deploy/strava-approval-tracker.md) — gap closure status.
- [v6 Strava plan](v6/strava-plan.md) — original OAuth and consent plan (historical; scopes have since widened to include `activity:read`).

## Local dev

```sh
python3 v6/server.py   # serves v6/ + API on :8123
python3 v6/server.py --self-test
python3 v6/update_engine.py --self-test
```

Strava OAuth only works through the live domain (single callback domain). Tinker with pages locally, but Connect on [mynextpr.com](https://mynextpr.com).

## Secrets policy

`.env`, `*.pem`, `.tokens.json`, and `v6/.athletes/` are git-ignored. They never enter the repo, chat, or tooling output.
