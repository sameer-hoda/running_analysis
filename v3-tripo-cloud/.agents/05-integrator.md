# Agent 5 — end-to-end integrator

Read `.agents/00_SHARED_CONTEXT.md` first. You own wiring + merges.

Scope: routes `H.do_GET/do_POST`, `seed_demo`, e2e script. Merge conflicts in `site/server.py`. Inbox: `.agents/handoffs/integrator-*.md`.

Brief:
1. Write `site/e2e_check.sh`: landing/login/upload/poll/report/mesh curl asserts (20 min).
2. Merge agents' patches in order 6→1→2→4→3, restart server, run e2e after each (40 min).
3. Fix stuck-job recovery + template-path regression guard (20 min).
4. Broadcast API/stage changes to all via handoffs; you are the only merger.

Done = e2e script green on fresh upload, demo 200, no regressions.
Next: read shared context, then write `site/e2e_check.sh`.
