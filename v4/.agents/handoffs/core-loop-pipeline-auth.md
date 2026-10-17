# Handoff: pipeline-auth → core-loop + watcher (2026-09-20, update 2)

## Freeze observed — server.py NOT touched this round
No core-loop merge handoff posted yet, so per instruction server.py is frozen.
Verified read-only: my bridge code intact (`owner_hash`/`safe_next`/`loginwait`/
`PARALLEL_PLAN`, 10 refs), alongside core-loop `V4_ROOT` + growth-memory block
(which reuses my `tok` in the upload handler — compatible).

## Shipped safe now (new files only, zero server.py edits)
- `site/tts_prewarm.py` (P1 hook): `build_tts_lines(analysis)` pure (overall +
  per-zone tldr+cue, ≤600 chars, ≤8 lines, insufficient skipped for client
  `coach_unclear`); `prewarm_for_job(job_dir, analysis, synthesize=None,
  voice="Kabir")` caches `tts/<key>.mp3` + `manifest.json`, fail-soft per line.
  Post-merge wiring: call in meshing lane + `GET /jobs/<jid>/tts/<key>.mp3`.
- `site/partials.py` (P2): `new_partial/apply_update/promote` pure score-first
  merge (overall first, zones keyed, findings win ties); `promote` enforces the
  7-zone + `zone_score` contract; `write_partial/read_partial` atomic file IO.
  Post-merge: audit lane streams `write_partial`, loader merges, seal promotes.
- Maintained tests = repo convention (`--selftest`, like `usage.py`): both new
  modules selftest against the live `demo/analysis.json` (69-shape) + temp dirs.

## Verified (observed, not claimed)
- `tts_prewarm` + `partials` + `usage` selftests: ALL GREEN.
- Live :8140: bridge checks 8/8 BRIDGE GREEN + `e2e_check.sh` E2E GREEN.
- My 3 test job dirs removed; others' (`1b886df6`, `67b6d2e`, `68125799`) untouched.
- Nuance: live :8140 process predates my `safe="/"` tweak, so its login form
  shows `next=%2Fjob%2F…`; decode round-trips (303 check proves it). On-disk
  code already emits readable slashes — visible after next :8140 restart.

## Rebase done (merge handoff pipeline-growth-core-loop.md, fresh :8140)
Merged `site/server.py` (1919 lines, `py_compile` clean) keeps pipeline-auth
byte-faithful — verified, zero edits needed: serial docstrings, `PARALLEL_PLAN`
(1363), `session_token`/`owner_hash`/`safe_next`/`login_page` (1036–1071) with
`safe="/"` readable slashes, `?next=` GET+POST wiring (1477/1760), loginwait
link + JS (773/779), `owner` in upload status (1817). Growth cap reuses `tok`;
no conflict.
Observed on merged :8140: bridge 8/8 BRIDGE GREEN, full `e2e_check.sh` E2E
GREEN (incl. Kabeer checks), `tts_prewarm` + `partials` selftests GREEN. Test
jobs removed; `site/jobs/` left as found + demo.
P1/P2 stay shipped-as-hooks (`site/tts_prewarm.py`, `site/partials.py`) —
wiring into `run_pipeline` + loader checklist is the next tracked step, not
this rebase.

## LOADING THEATER shipped (2026-09-20, JOB_PAGE redesign)
Scope kept inside JOB_PAGE only — shared CSS/LANDING/routes untouched, so no
cross-track contract change. Catalog rail reuses research-catalog's serving
contract (`/research/papers/catalog.json` + `/research/papers/thumbs/`, no
hardcode); canon coach name "Kabeer" per report_template majority + asset.
- Globe kept (same canvas/3D/pct). Small-text progress replaced by: Kabeer
  narration line per stage (`KL`, avatar `coach-kabeer.jpg`), 4 check-off
  stage cards (Task-pattern collapsible triggers, active auto-opens, 52px
  targets, `aria-expanded`, reduced-motion safe), live paper rail with catalog
  thumb image previews (7s rotate, fail-silent, links to `/research/<id>`).
- Poll/cancel/retry/done-redirect/fail paths behavior-identical; `failed`
  freezes cards where they were + failed narration. All old ids kept
  (`loginwait`, `paperrail`, `stages`, `detail`, …).
- `site/sandbox_loader.html` centre ported to match (mirror contract holds;
  rail hidden on `file://` where fetch fails — honest, noted in-page).
Verified (observed): rendered-page `node --check` OK; headless stub-DOM proof
(check-off/aria/Kabeer lines/failed-freeze) OK; sandbox script `node --check`
OK; live job page on fresh-code :8143 THEATER GREEN (14/14) + BRIDGE GREEN +
full E2E GREEN. Ledger confirms my 5 proof uploads spent $0 (upload+page
events only); dirs removed, others' untouched.
Live :8140 still serves pre-theater code (process predates this change) —
needs a restart to pick it up; I did not touch it (not my process).
Flags for others (not fixed, out of scope): (1) server processes report
TRIPO_API_KEY missing while `tripo_cloud._key()` resolves one — key lives
where `server.py` doesn't look (`site/.env` or v3 path vs `V3/.env`); (2)
`usage.log` shows real `tripo_build` events from other jobs — live uploads
are spending credits (~30/build) while balance was last seen at 20.0.

## TRIPO 403 diagnosis (2026-09-20, $0 spent — no builds fired)
Symptom: key valid (`POST /v3/files` works) but `POST
/v3/generation/image-to-model` 403s with `model v3.1-20260211`.
Findings (docs + zero-cost `GET /v3/account/balance` via `/tmp/tripo_balance_probe.py`):
- Model ID is CURRENT — docs list `v3.1-20260211` as "latest, best quality".
  Not the cause. Our request shape (Bearer auth, `input: file_token`,
  `model`, fast-lane texture params) matches the H-series doc.
- Per [error-handling docs](https://developers.tripo3d.ai/en/docs/error-handling):
  HTTP 403 = "no permission to access the resource, **or credits
  insufficient**"; code 2010 = Insufficient credits ("top up in console").
- Balance observed: **20.0 available / 0 frozen** (http 200, code 0 — key
  valid, scope fine; `/files` is free so upload works regardless).
- Per [pricing](https://developers.tripo3d.ai/en/pricing): Image-to-3D H =
  20 credits no-texture / **30 standard texture**. Our fast lane sends
  `texture:true` → 30 > 20 → **403 is code-2010 insufficient credits.**
Fix (owner): top up at platform.tripo3d.ai (~$0.30/textured build; $1 = 100
credits ≈ 3 builds). No code change needed. Do NOT "fix" by flipping the
fast lane to `texture:false` unasked (20.0 balance is borderline and it drops
PBR skin the report heat shell expects).
Implemented (2026-09-20): `_http_error_message()` in `site/tripo_cloud.py` —
`_req` now raises `RuntimeError("tripo HTTP 403 [code 2010] Insufficient
credits — …")` instead of a bare HTTPError, so the job error + status show
the cause plainly (flows into `box["tripo_error"]` untouched downstream).
Kept test: `python3 site/tripo_cloud.py --selftest` (mocked HTTPError, zero
spend — 403/JSON, 500/HTML fallback, missing-key, success path). Focused test
GREEN + e2e quick E2E GREEN on :8140, no `tripo_build` fired.

## SPEND-FREEZE RULE (all agents, effective now)
NOBODY runs paid Tripo builds without watcher approval. Balances burn fast
(~30 credits ≈ $0.30 per textured build). Allowed without approval: `GET
/v3/account/balance`, mocked selftests, keyless fail-loud paths, uploads that
provably stop before `create_task`. Verify `tripo_build`-free via
`site/usage.log` after every live test.
Disclosure: e2e quick on keyed :8140 cost one real Gemini audit ($0.0039 —
audit judged images-3.jpeg `is_running=false`); no Tripo build fired.

## SPEND-GUARD shipped (2026-09-20, user order — bots never touch paid Tripo)
- Signal: `POST /api/jobs?test=1` or `X-Test: 1` header (`is_test_upload()`);
  recorded as `test` in job status. Unmarked browser uploads keep the real lane.
- Test lane (`run_test_lane`): copies committed `site/jobs/demo`
  analysis+mesh, best-effort anchors, then done — Gemini/Tripo never imported,
  let alone called. Test jobs skip the 15-cap and history (no cap burn, no
  bot pollution; growth block touched only via `and not test` guards).
- `site/e2e_check.sh` uploads now send `?test=1` (quick + FULL); old servers
  ignore the flag (backward compatible, verified on :8140).
- Kept test: `python3 site/server.py --selftest` (flag parsing + lane with a
  `tripo_cloud` bomb in `sys.modules` + artifact asserts, zero network).
Verified (observed): server selftest GREEN, tripo selftest GREEN, FULL e2e
E2E GREEN on fresh :8144 (test job `test=True`, done, score 69), bridge
GREEN, growth suite GROWTH GREEN, :8140 e2e compat GREEN. Ledger for the
FULL test job: upload+page+job_done = $0.00, zero paid calls. Test dirs
removed (attribution via ledger timestamps; others' untouched).

## RUNNER-ISOLATION shipped (2026-09-20, two-runners-one-mesh bug)
- `extract_pose.py`: lazy ultralytics/PIL imports (server boots without the
  stack); `_weights()` via `YOLO_WEIGHTS` or v3 checkout read-only (53MB
  weights NOT copied); `detect_persons()` (all boxes, area-desc) +
  `isolate_runners()` (crop to largest bbox +15% margin clamped; 0–1 persons
  or detector failure → input unchanged + reason, fail-soft). Old meshes
  untouched (pre-pipeline crop only, no retroactive changes).
- `site/server.py` upload: isolate runs post-sanitize, BEFORE Gemini/Tripo
  can see the photo — both lanes read `input.jpg`, which is the crop;
  original kept as `input_orig.jpg`; `isolation` recorded in status + log.
- Kept test: `python3 extract_pose.py --selftest` (injected detector —
  two/one/zero persons, margin clamp, detector-failure skip; weight-free).
Verified (observed): selftest GREEN; real YOLOv8m-pose on a two-person photo
(v3 `images-10.jpeg`, read-only) finds 2 persons; live stub-lane upload on a
YOLO-capable temp server → status `isolated:true persons:2`, `input.jpg`
163×489 exactly matches the status-box crop of the 554×554 original,
`input_orig.jpg` preserved; ledger upload+job_done = $0.00, zero paid calls;
e2e quick GREEN. Proof job removed.
Activation note: system-python servers lack ultralytics → isolation
fail-soft-skips there. Live :8140 needs either v3-venv python or `pip
install ultralytics` (+ optional `YOLO_WEIGHTS`) for the guarantee to bite.
Flags: (1) v4 lean fixtures `images-3/4.jpeg` score ZERO YOLO persons while
their v3 namesakes score 0.92+ — re-export may have hurt detectability,
worth a look for real-upload quality; (2) a concurrent test-dir cleaner is
active in shared `site/jobs/` (one of my terminal test dirs vanished
mid-turn; I removed only ledger-attributed mine, left the ambiguous rest);
(3) `usage.log` keeps gaining real `tripo_build` events from other jobs —
spend-freeze still stands.

## FINAL-RESTART done (2026-09-20, :8140 on v4 venv + keys)
- Completed the staged stack with `pip install google-genai` into `v4/.venv`
  (now: ultralytics 8.4.156 + PIL/numpy + trimesh + genai). Weights already
  staged at `v4/yolov8m-pose.pt` (used CWD-last in `_weights()` chain).
- Restart: killed old :8140 (PID 41020, system python, zero in-flight jobs),
  carried TRIPO/GEMINI/INWORLD keys + TRIPO_MODEL/FACE_LIMIT/VOICE from its
  env (presence-logged, never printed), exec'd `v4/.venv/bin/python
  site/server.py 8140` with `PYTHONPATH=v4`. No `.env` files exist — keys
  live in process env only; any future restart must repeat the carry.
- Verified live: two-person stub upload → `isolated:true persons:2`, stub
  lane done; `/reel/demo` 200 (composed on demand; $0.0076 TTS voiceover —
  only sanctioned spend this turn); test-mode ledger via sh: both proof jobs
  $0.00, zero `tripo_build`/`gemini_audit`/`tts`; FULL e2e E2E GREEN (pipeline
  done + fresh report + section 12) + BRIDGE GREEN. Proof dirs removed.
- STAND-DOWN WARNING: this :8140 is session-managed (macOS, no setsid) and
  DIES with my session. Watcher must adopt it now — either keep a session
  alive owning it or relaunch via `v4/.venv/bin/python site/server.py 8140`
  (keys must be re-supplied; see carry list above). pipeline-auth standing down.

## FINAL-PROOF evidence record (2026-09-20, run by pipeline-auth on live :8140)
Server: PID 47689 (venv exec from FINAL-RESTART) still serving, landing 200,
TTS Kabir configured. Probed in order, all observed:
1. Two-person stub upload (`/tmp/two_real.jpg`, `?test=1`): job `1ab937ea52da`
   → status `isolated:true persons:2 box:[280,65,443,554]`, stub lane done,
   score 69 — ISOLATION GREEN.
2. `/reel/demo` → 200 (cache composed last turn).
3. Test ledger via sh: isolation job events upload+job_done = $0.00; FULL job
   upload+page+job_done+page = $0.00; 7 recent test jobs swept, ALL $0.00
   with zero `tripo_build`/`gemini_audit`/`tts` — PAID none.
4. FULL e2e E2E GREEN (pipeline done + fresh report 200 + section 12 markers
   all ok) + BRIDGE GREEN.
Cleanup: `1ab937ea52da` + FULL job `f55417e645fd` removed (ledger-attributed);
ambiguous concurrent test dirs left for the active cleaner. :8140 left
serving 200. No real paid builds this turn. pipeline-auth stood down.

Post-stand-down correction: my session-managed :8140 (PID 47689) later
received SIGTERM (runtime notice, exit 143). A new owner has already
relaunched :8140 (PID 51418): landing 200, TTS Kabir configured, merged
landing markers present. Proof results above stand (same merged code); only
process ownership changed. pipeline-auth takes no further action.

## RESTART-VERIFY done (2026-09-20, sample-swap + demo-CTA live)
Stale :8140 (PID 91583, booted 19:05, zero in-flight) restarted via proven
`/tmp/restart_8140.py` (keys carried, venv exec). Mid-verify, my fresh server
was SIGTERMed by another owner (exit 143 → first FULL e2e RED on conn 000s,
not code); port came back under PID 99813 (boot 19:55) — verified against it:
- Sample links x4 → `/report/aeb979a86e8b` live on landing (curl count 4).
- `showcase.mp4` 200, 1.7MB, fresh 18:47 file, audio+video streams.
- FULL e2e E2E GREEN (pipeline done, fresh report, section 12, ratings,
  sample + lab checks all ok).
Ledger: same-second test pair swept, both $0 terminal (one possibly a
concurrent agent's shared-script exhaust — disclosed); keepers intact.
:8140 left serving under its current owner. pipeline-auth stood down.

## JOBS-HYGIENE done (2026-09-20, user order)
Deleted 52 stub test dirs from `site/jobs/` (many carrying 0.7MB demo-mesh
copies from the test lane); kept exactly `demo`, `02652674ecda`,
`419d46c0abbf`, `aeb979a86e8b` (all present, none in-flight at delete time).
Verified `ls` = 4 dirs, then e2e E2E GREEN on :8140; e2e's own test job
(upload+page+job_done = $0.00, zero paid calls) removed after — final `ls`
= 4 dirs. Follow-up idea (not implemented): test lane could hardlink the
demo mesh instead of copying, to stop the 0.7MB-per-test-dir regrowth.
