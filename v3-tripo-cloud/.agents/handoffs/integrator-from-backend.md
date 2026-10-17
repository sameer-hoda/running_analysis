# backend → integrator: wire restore + sanitizer + queue (backend done with owned part)

Backend finished owned edits in `site/server.py` (pipeline slice + helpers). Needs your wiring (your files, I didn't touch them).

## 1. Boot restore (fixes stuck `meshing` jobs `9ec3ee449dea`, `c473b15f0317`)
In `seed_demo()`, after `os.makedirs(JOBS, exist_ok=True)`, add:
```python
restore_status_from_disk()
```
Then keep demo seeding after it (demo overwrite wins). Stuck jobs requeue via `enqueue_pipeline` automatically. Note: their `triposr/` dirs contain only `input.png`/empty output (TripoSR died pre-restart), so re-running `run_pipeline` from `meshing` will redo Gemini + mesh from `input.jpg` — correct behavior, ~2min each, serial via queue.

## 2. Upload hardening (PIL verify / EXIF / downscale / WebP)
In `do_POST` `/api/jobs`, after slicing `img` bytes, add:
```python
try:
    img = sanitize_upload(img)
except Exception:
    return self.send(*page('{"error":"invalid image (JPEG/PNG/WebP only)"}', 400, "application/json"))
```
Keep the existing size checks. `sanitize_upload` returns normalized JPEG ≤1600px. `accept=` attr already lists webp; handling is real now.

## 3. Serial queue
In same handler, replace:
```python
threading.Thread(target=run_pipeline, args=(jid,), daemon=True).start()
```
with:
```python
enqueue_pipeline(jid)
```

## 4. Backward-compat notes (for analysis-page)
`anchors.json` keeps `zone -> [x,y,z]` shape; new optional `_missing` key (`zone -> reason`) appears only on fallback/failure. Template's `if (!a) return` ignores it safely — no template change needed. `run_pipeline` now passes findings+insufficient zones (all 7), so anchors cover every zone.

## Verified by backend
- `compute_anchors` on `site/jobs/d9b1011f7e84/mesh.glb` with all 7 zones → all 7 mapped, no `_missing` (was 5/7 before).
- `sanitize_upload`: 2400px PNG → 1600px JPEG; WebP → JPEG. Magic-byte sniffing in your handler stays as first gate.
- `python -c ast.parse` syntax OK. Server NOT restarted — over to you to wire + restart + e2e.

## UPDATE 2026-09-12 (backend): verified live + backfilled anchors
- Restart proof: `pkill + boot` → landing 200, demo 200. Stuck `meshing` job `799d1f3cc173` requeued to `analyzing` via `restore_status_from_disk`+`enqueue_pipeline`; queued jobs (`7befa157919f`, fresh `d7d9bd7bac04`) preserved. No restart loss.
- Fresh upload e2e: login 303 → POST /api/jobs 200 `{"job_id":"d7d9bd7bac04"}` → queued→analyzing→failed "No runner detected" (correct: test img was a solid square — runner filter works).
- `sanitize_upload`: 2400px PNG→1600×1200 JPEG; WebP→JPEG; corrupt bytes→UnidentifiedImageError→400 handler path.
- `compute_anchors`: 7/7 no `_missing` on demo + sample meshes; unknown zone → explicit `missing`, no crash.
- Backfilled stale anchors to 7/7: demo, 1260dce9ef40 (3→7), d9b1011f7e84 (5→7), 451afcf18b9d, 9dfd9e3cbd95, 2a30d0ec662e, 2f51bfc0adea. Reports 200: demo, 1260dce9ef40, d9b1011f7e84.
- step1_prompt.txt: research patch already applied (judgeability matrix, flight guards, strict 55-75 + caps ≤70/≤60, author-only cites) — no change needed.
- No owned-file edits this round (code was already wired); only runtime data `site/jobs/*/anchors.json` refreshed. Server restarted and live.

## UPDATE 2026-09-12 (backend): research patch applied + re-verified (earlier)
- `step1_prompt.txt` updated per `backend-from-research.md`: judgeability matrix, flight-phase guards, strict mapping optimal 85+/fair 60-84/critical 0-59, caps (any critical ≤70, 2+ ≤60), labels, sand caveat, author-only cites, action=[cue1,cue2,drill], 7-entry shape.
- Re-verified just now: `compute_anchors` 7/7 no `_missing` on demo + 1260dce9ef40; `sanitize_upload` 2400px PNG→1600px JPEG, WebP→JPEG, corrupt rejected (UnidentifiedImageError); `restore_status_from_disk` + `enqueue_pipeline` present.
- Wiring still yours (untouched): boot `restore_status_from_disk()`, `sanitize_upload` gate + `enqueue_pipeline` swap in `do_POST /api/jobs`. Restart + e2e on you.
