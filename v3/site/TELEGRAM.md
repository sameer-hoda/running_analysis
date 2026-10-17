# Telegram — RunForm notifications + digest

Secrets live ONLY in the server `.env` (never committed):
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Empty/missing → all Telegram
paths silently skip; the pipeline never depends on them.

## 1. Completed-report notification (this server)

`run_pipeline()` calls `notify_report_done(jid, score)` when a job reaches
`done`. It sends one fire-and-forget message in a daemon thread:

```
RunForm report ready — score 73/100
https://mynextpr.com/report/<job_id>
```

- `telegram_notify()` is best-effort: returns True/False, never raises.
- Report base URL defaults to `https://mynextpr.com`; override with
  `PUBLIC_BASE_URL` in env/`.env` (e.g. local dev).
- Failed jobs do NOT notify (only completed reports with a score).

## 2. Daily/hourly digest (EC2 systemd, already scheduled)

On EC2 (`~/v3-tripo-cloud`) two timers are active — verified 2026-09-20:

| Timer | Service | What it runs |
|---|---|---|
| `runform-tg-daily.timer` (daily 08:00 + jitter) | `runform-tg-daily.service` | `site/tg_report.py --mode daily` — always sends: last 24h + all-time totals + costliest jobs |
| `runform-tg-hourly.timer` (hourly + jitter) | `runform-tg-hourly.service` | `site/tg_report.py --mode hourly` — sends only when the last hour has API usage, else prints `SKIP` |

Both read `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` from
`~/v3-tripo-cloud/.env` via `EnvironmentFile=`. Check health with:

```
sudo journalctl -u runform-tg-daily --no-pager | tail
sudo journalctl -u runform-tg-hourly --no-pager | tail
```

## 3. Dormant: legacy `~/telegram_daily.py`

`~/telegram_daily.py` + `~/set_telegram_chat.sh` target the OLD v2 backend
(`~/backend/users.db`, nginx log parsing) and are superseded by
`site/tg_report.py` + the timers above — nothing schedules them (no cron on
the box; `crontab` is not installed). They also embed a bot token in source.
Leave dormant; delete only after confirming no other host references them.
