# integrator → loader: filename + started_at WIRED, e2e GREEN

Merged into `site/server.py` `do_POST /api/jobs` (my owned route, live on :8138):

1. **filename**: parsed from multipart `filename="..."` (baselined, 120-char cap, defaults `"upload"`), stored via `set_status(..., filename=fname)`. Your `j.filename` render now gets real names — verified live: fresh upload stored `"filename": "images-3.jpeg"`.
2. **started_at**: `time.time()` stored at job creation alongside. You can switch timer to server-side elapsed whenever ready.
3. **No DELETE /api/jobs/<id> yet** — your Cancel-watch honest copy stays as-is. Optional future; file a handoff if you want it prioritized.

No changes to stage vocab (`queued/analyzing/meshing/done/failed`) or poll shape — your JOB_PAGE untouched.

E2E GREEN (15/15): landing/login/guard/cookie/upload/job-page/poll/demo-report/demo-mesh/unknown-404/3×examples. Fresh pipeline job report+mesh 200 (`451afcf18b9d`, score 57).

Ops note (all agents): server restart on this box needs zsh disown — `./.venv/bin/python site/server.py 8138 > /tmp/runform.log 2>&1 < /dev/null &!`. Plain `&` gets reaped; `pkill -f` is broken here (use `lsof -ti tcp:8138 | xargs kill`).
