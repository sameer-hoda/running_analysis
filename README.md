<p align="center">
  <img src="launch-kit/images/hero.png" alt="A runner tying shoes on an empty road at sunrise" width="100%">
</p>

<h1 align="center">mynextpr — every run, closer to race day</h1>

<p align="center">
  <strong>Pick a race. Connect Strava. Every finished run gets a live countdown written into its activity description. Titles never touched.</strong>
</p>

<p align="center">
  <a href="https://mynextpr.com"><img src="https://img.shields.io/badge/View_Live_Site-mynextpr.com-c8f04a?style=for-the-badge&logo=google-chrome&logoColor=0e1206" alt="View live site — mynextpr.com"></a>
</p>

<p align="center">
  <a href="https://mynextpr.com"><img src="https://img.shields.io/website?url=https%3A%2F%2Fmynextpr.com&style=flat-square&label=live%20site" alt="Live site status"></a>
  <img src="https://img.shields.io/badge/python-3.11-blue?style=flat-square&logo=python" alt="Python 3.11">
  <img src="https://img.shields.io/badge/Compatible_with_Strava-yes-FC5200?style=flat-square&logo=strava&logoColor=white" alt="Compatible with Strava">
  <a href="https://mynextpr.com/privacy.html"><img src="https://img.shields.io/badge/privacy-policy-lightgrey?style=flat-square" alt="Privacy policy"></a>
</p>

---

## The pitch

Training for a race is months of lonely mornings. mynextpr keeps the finish line inside every run: after you cross it, your Strava activity carries a line like *"34 days to go for Tata Mumbai Marathon — Target sub-30"*, next to your month and year totals. Zero habit change, zero manual editing.

<p align="center">
  <img src="launch-kit/images/ig-45.png" alt="Runner's legs at sunrise with '15 days to go' overlay" width="60%">
</p>

## How it works

1. **Pick** an upcoming race (and an optional goal) on the site.
2. **Approve** on strava.com — minimal scopes only: `read`, `activity:read`, `activity:write`.
3. **Forget it.** Webhooks catch each new run and stamp the countdown into the description. Past race day, stamping stops by itself. Disconnect any time.

## Privacy-first by construction

- **Description-only writes.** Activity titles are never read or written (pinned by automated tests).
- **One athlete's data only to that athlete.** Strict login cookies on every API route; no cross-user display, ever.
- **No activity content cached.** Only a stamped-ID dedup log, pruned to 7 days.
- **Instant, complete deletion.** Disconnect revokes Strava access and wipes the record; a timestamped on-screen confirmation proves it.
- Public [privacy policy](https://mynextpr.com/privacy.html), [terms](https://mynextpr.com/terms.html), and [support](https://mynextpr.com/support.html) with a private contact form — no data ever published.

<p align="center">
  <img src="launch-kit/images/x-card.png" alt="Runner approaching India Gate at dawn" width="60%">
</p>

## Under the hood

| Piece | What it is |
|---|---|
| App | Static pages + a dependency-free Python backend (`v6/`) |
| Stamping | Webhook-driven with a poller backup; month/year totals fetched live |
| Auth | Per-athlete token store, short-lived tokens auto-refreshed |
| Hosting | Single EC2 box, nginx + HTTPS, ~zero running cost |

## Repo map

- [`v6/`](v6/) — the live app: pages, backend, countdown engine, self-tests.
- [`strava-application/`](strava-application/README.md) — the whole Strava integration in one folder: OAuth, architecture, compliance, deploy, approval pack.
- [`deploy/`](deploy/) — EC2 context and approval tracker (host details live outside the repo).
- [`launch-kit/`](launch-kit/) — launch art and copy.

## Run it locally

```sh
python3 v6/server.py                 # serves v6/ + API on :8123
python3 v6/server.py --self-test     # backend checks
python3 v6/update_engine.py --self-test  # countdown engine checks
```

Strava OAuth only flows through the live domain (single callback domain per Strava app) — tinker with pages locally, Connect on [mynextpr.com](https://mynextpr.com).

## Status & roadmap

- [x] v6 live on mynextpr.com, end-to-end stamping verified
- [x] Multi-athlete auth, strict login cookies, deletion confirmation
- [ ] Strava production review (10-athlete self-serve → review form)
- [ ] First 9 invited runners, then public launch

## Contact

- Support / privacy / security: the [private form on the site](https://mynextpr.com/support.html) — nothing published.
- Bugs and ideas: [issues](https://github.com/sameer-hoda/running_analysis/issues).

---

<p align="center">
  <sub>mynextpr · Compatible with Strava. Not endorsed by Strava.<br>
  Secrets (<code>.env</code>, keys, tokens) never enter this repo.</sub>
</p>
