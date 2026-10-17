# AGENT BRIEF TEMPLATE (mandatory for every order from watcher)

Copy this skeleton for each task. Fill every section. No bare one-liners.

## 1. Context (why this exists)
- Where we are: v4 on :8140, what already works, what broke to cause this task.
- User's words (quote the actual complaint/request).
- Pointers: exact files, routes, job IDs, handoffs already read by watcher.

## 2. Mission (what to do, step by step)
- Numbered steps in order. Name the files/functions to touch.
- Explicit non-goals: what NOT to touch (other agents' areas, live server
  process ownership, paid APIs without approval).
- Server rule: never run :8140 in the main-turn foreground (it hangs the turn);
  use background tasks; keys via `set -a; . ../v3-tripo-cloud/.env; set +a`,
  PYTHONPATH=/Users/sameerhoda/Projects/running_analysis/v4/.venv/lib/python3.14/site-packages.

## 3. Success looks like (observable, live)
- Concrete live proofs: URLs + expected markers/codes (e.g. "curl X shows Y",
  "job reaches done with isolated:true").
- Numbers where possible (counts, timings, scores).

## 4. Keep in mind (pitfalls already paid for)
- macOS framework python ignores venv symlinks → PYTHONPATH, verify with
  `python3 -c "import trimesh"`, never --break-system-packages.
- Server restarts: confirm listener PID age changed + landing 200 after.
- No paid Tripo builds without watcher approval (test=1 stub lane for proofs).
- Taste filter for anything visual (SHOWCASE_BRIEF.md § Taste filter).
- Kabeer display / Kabir voiceId / zero Darmani. e2e §8d enforces.
- Handoff etiquette: update `.agents/handoffs/<me>-<other>.md`, never rewrite
  another agent's file; mailbox check first.

## 5. Prove it (how to test done)
- Maintained checks first: `bash site/e2e_check.sh` (+ relevant section),
  focused unit/probe scripts kept in repo (no throwaway-only proof).
- Negative + edge paths for the touched area (404s, unknown slugs, %-in-CSS,
  old-schema fallbacks where applicable).
- Test spend: $0 ledger for bot proofs; state any paid spend explicitly.
- Update the handoff with the evidence record, then stand down.

## 6. Done signal
- Reply format: CHANGED files / PROOF (observed outputs) / FLAGS (anything
  odd) / NEXT (suggested follow-up or "stand down").
- Evidence lines must cite inspected bodies (`path:line`), never grep-only
  claims. Carry UNRESOLVED items verbatim into the handoff; never silently
  drop a gap. The watcher synthesizes from these lines, not from summaries.

## 7. Coordination (multi-agent hygiene)
- One owner per file per turn: check `.agents/handoffs/` first, announce
  takes, never edit under another agent's active take.
- server.py is shared ground: additive-only diffs, announce route/handler
  additions in the handoff, core-loop (or watcher-assigned owner) merges.
- Downstream handoffs name the exact consumer + what they must observe.
