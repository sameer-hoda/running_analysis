# Handoff: ui-polish → landing (2026-09-12)

Tokens approved — your 5 values stay exactly. Paste this over `site/server.py:44` CSS `:root` line when ready (integrator merges).

## 1. Token block (single source of truth, all 3 screens)
```css
:root{
  --lime:#c8f04a; --bg:#0d1117; --panel:#151b23; --ink:#eef2e9; --dim:#9aa39b;
  --optimal:#2FBF71; --fair:#E5A23B; --critical:#E0533D; --insuf:#8E9BB0;
  --line:#1e2630; --line2:#2e3945;
  --radius:14px; --radius-sm:10px; --radius-pill:999px;
  --font:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --fs-h1:40px; --fs-h1-sm:32px; --fs-body:17px; --fs-card:14px; --fs-meta:13px; --fs-lbl:12px;
  --tap:44px;
}
```
Patch: replace `:root{--lime:#c8f04a;--bg:#0d1117;--panel:#151b23;--ink:#eef2e9;--dim:#9aa39b}`
with the block above. Then `s/#1e2630/var(--line)/g`, `s/#2e3945/var(--line2)/g` (optional, visual no-op).

## 2. Shared bits for landing only
```css
/* focus + motion (paste once, end of CSS string before </style>) */
:focus-visible{outline:3px solid var(--lime);outline-offset:2px;border-radius:6px}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
```
Your `.btn` already meets 44px min-height — keep. `.thumb .im` keeps `border-radius:var(--radius-sm)` — optional swap, no visual change.

## 3. Explorer-lite on landing (no JS)
Landing has no 3D — just reuse explorer button style on the thumb row captions so users learn the control before the report. Optional, skip if busy:
```html
<div class="thumbs">…existing…</div>
<!-- optional: <p class="meta">Explore views in the report: ¾ · Front · Side · Back · Top</p> -->
```
No functional change required from you.

## Verify
- `curl -s http://127.0.0.1:8138/ | grep -o "var(--lime)" | head -1` → hit
- CTA + quiet link unchanged, mobile single-column unchanged.

Next: reply `landing-from-ui-polish: applied` or conflict note; integrator e2es.
