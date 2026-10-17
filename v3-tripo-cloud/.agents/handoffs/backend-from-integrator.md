# integrator → backend: wiring MERGED, e2e GREEN

All 3 items merged into `site/server.py` (my owned routes/boot):
1. `seed_demo()` now calls `restore_status_from_disk()` first — demo seed after, wins.
2. `do_POST /api/jobs` sanitizes via `sanitize_upload()` (400 on invalid) + `enqueue_pipeline(jid)`.
3. Boot change you should know: **removed `recover_statuses()` call** — it raced your restore (marked requeued jobs failed on startup). Function kept, just not called. Restore+requeue is now the single recovery path.

Notes:
- `9ec3ee449dea`/`c473b15f0317` were already `failed` (previous boot marked them), so restore skipped them — nothing requeued for those two. They have `input.jpg` + `analysis.json`, re-upload works.
- Live proof: restart requeued an in-flight e2e test job; new upload polled `stage=queued` behind it — serial queue confirmed.
- E2E GREEN (14/14 incl. new `/examples/` asserts).
