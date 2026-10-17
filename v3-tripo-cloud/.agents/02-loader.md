# Agent 2 — loader / processing design

Read `.agents/00_SHARED_CONTEXT.md` first. You own the processing screen.

Scope: JOB_PAGE only (`site/server.py:105-167`). Inbox: `.agents/handoffs/loader-*.md`.

Brief:
1. Show uploaded thumbnail + filename + elapsed timer (replaces fake icosahedron %) (30 min).
2. 3 honest stages (audit → mesh → bake) driven by `/api/jobs/<id>` stage, retry/backoff, cancel button (30 min).
3. No-CDN fallback text if three.js offline; keep polling every 2s (15 min).
4. Handoff stage-shape changes to integrator; styling tokens to ui-polish.

Done = upload→job page polls to done→redirects, curl-verified.
Next: read shared context, then open `site/server.py:105-167`.
