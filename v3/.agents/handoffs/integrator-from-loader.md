# loader → integrator (2026-09-12, update)

JOB_PAGE (`site/server.py:168-261`) verified live on :8138. One-label tweak today:
`done` row now reads "Bake — score + report ready" (matches brief audit→mesh→bake;
stage logic/keys unchanged: queued 4 / analyzing 30 / meshing 93 / done 100).

## curl proof (fresh server, fresh guest session)
- `POST /login guest=1` → 303 + cookie; anon `/job/<id>` → 303→/login (correct)
- `POST /api/jobs` (images-3.jpeg) → `{"job_id":"7befa157919f"}`
- `/job/7befa157919f` → 200, contains thumb/fname/timer/poll/`#ncdn`/Bake/`setTimeout(poll,2000)`
- `/api/jobs/7befa157919f` → `queued/waiting for worker` (honest 4% shown)
- Done-job path: `/api/jobs/1260dce9ef40` → `done/report ready/score 62`;
  `/job/1260dce9ef40` → 200 with `location.href='/report/'`; `/report/1260dce9ef40` → 200.
  = poll-to-done → redirect-to-report contract holds against real API shapes.

## Queue jam — YOURS/backend (loader cannot fix, JOB_PAGE handles it honestly)
- `site/jobs/799d1f3cc173` stuck `meshing` with a live worker → `ACTIVE_JOB` never
  frees → serial queue stalls. New uploads sit `queued` (~6 min observed).
  Loader page degrades correctly (4%, "waiting for worker", 2s poll, backoff copy).
- Suggest: worker heartbeat/timeout + surface position-in-queue in status `detail`
  (loader already renders `j.detail` verbatim — no loader change needed).
- Still open from last handoff: store `filename` + `started_at` in status on
  POST /api/jobs (loader renders both, falls back to `run <jid>` / page-load timer).
- Note: server restarted itself mid-session (fresh PID, SESSIONS wiped, old guest
  cookie 303'd). If you added auto-reload, guest sessions die with it — consider
  cookie-signed or disk-backed sessions.

No merge risk: only one JOB_PAGE line touched (done-row label).
