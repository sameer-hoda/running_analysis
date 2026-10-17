# Agent 3 — analysis backend

Read `.agents/00_SHARED_CONTEXT.md` first. You own the brain's plumbing.

Scope: `site/server.py:183-275` (gemini_audit, anchors, bake, run_pipeline), `step1_prompt.txt`, `extract_pose.py`. Inbox: `.agents/handoffs/backend-*.md`.

Brief:
1. Persist STATUS to disk on boot (recover stuck `meshing` jobs like `9ec3ee449dea`), add 1-deep job queue (45 min).
2. Harden upload: PIL verify, EXIF rotate, downscale, real WebP accept (30 min).
3. Fix `compute_anchors` fallbacks so all 7 zones map or explicitly report `missing` (30 min).
4. Research agent advises on prompt science — apply their patch via handoff, you edit.

Done = fresh upload→done→report 200 with full anchors, no restart loss.
Next: read shared context, then open `site/server.py:183-275`.
