# Agent 6 — UI polish + options explorer

Read `.agents/00_SHARED_CONTEXT.md` first. You own shared tokens.

Scope: design tokens + options-explorer component injected into landing/loader/analysis (no direct edits — ship via handoffs to 1, 2, 4). Inbox: `.agents/handoffs/ui-polish-*.md`.

Brief:
1. Define tokens (lime/dark, radius, type scale) as one CSS block for all 3 screens (25 min).
2. Build options explorer: view/wireframe/spin/colour control used identically on loader + report (35 min).
3. Accessibility pass spec: focus rings, contrast, 44px targets, reduced-motion (20 min).
4. Ship as copy-paste patches; owners apply, integrator verifies.

Done = token patch + explorer patch accepted by 1, 2, 4.
Next: read shared context, then draft tokens from `site/server.py:44-59`.
