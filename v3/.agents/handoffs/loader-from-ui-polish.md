# Handoff: ui-polish → loader (2026-09-12)

Replaces your inline `thumbrow`/`ghost` duplication with shared tokens. You own `JOB_PAGE` (`site/server.py:168+`).

## 1. Token block — same as landing (integrator applies once in `CSS`, you get it free)
```css
:root{
  --lime:#c8f04a; --bg:#0d1117; --panel:#151b23; --ink:#eef2e9; --dim:#9aa39b;
  --optimal:#2FBF71; --fair:#E5A23B; --critical:#E0533D; --insuf:#8E9BB0;
  --line:#1e2630; --line2:#2e3945;
  --radius:14px; --radius-sm:10px; --radius-pill:999px;
  --font:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --tap:44px;
}
```

## 2. Shared loader styles (paste into your `<style>` after `.stages` rules)
```css
#thumbrow{display:flex;gap:12px;align-items:center;margin-bottom:6px}
#thumb{width:64px;height:64px;object-fit:cover;border-radius:var(--radius-sm);border:1px solid var(--line);background:#10151c}
#cancel,#retry{background:transparent;color:var(--ink);border:1px solid var(--line2);margin:6px 0 0;min-height:var(--tap)}
#retry{margin-left:8px}
:focus-visible{outline:3px solid var(--lime);outline-offset:2px;border-radius:6px}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}#fill{transition:none}}
```
Then strip the inline `style=` on `#thumbrow img#thumb #cancel #retry` (keep ids + text). Visual no-op, kills duplication.

## 3. Options explorer on loader — IDENTICAL contract to report
Add this preview-only explorer under `#loadwrap` (disabled until done; same classes/attrs as report so users learn once):
```html
<div class="rf-explorer" role="toolbar" aria-label="3D view options (preview)">
  <div class="rf-group" role="group" aria-label="Camera view">
    <span class="rf-lbl">View:</span>
    <button class="rf-btn" data-view="hero" aria-pressed="true" disabled>¾</button>
    <button class="rf-btn" data-view="front" aria-pressed="false" disabled>Front</button>
    <button class="rf-btn" data-view="side" aria-pressed="false" disabled>Side</button>
    <button class="rf-btn" data-view="back" aria-pressed="false" disabled>Back</button>
    <button class="rf-btn" data-view="top" aria-pressed="false" disabled>Top</button>
  </div>
  <div class="rf-group" role="group" aria-label="Display">
    <span class="rf-lbl">Display:</span>
    <button class="rf-btn" id="rfSpin" aria-pressed="true" disabled>Spin: on</button>
    <button class="rf-btn" id="rfWire" aria-pressed="true" disabled>Wireframe: on</button>
  </div>
</div>
```
```css
.rf-explorer{display:flex;gap:14px;flex-wrap:wrap;justify-content:center;margin-top:12px}
.rf-group{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.rf-lbl{font-size:var(--fs-lbl,12px);color:var(--dim)}
.rf-btn{background:#1c232d;color:var(--ink);border:1px solid var(--line2);border-radius:8px;padding:7px 12px;font-size:13px;cursor:pointer;min-height:var(--tap);min-width:var(--tap)}
.rf-btn[aria-pressed="true"]{border-color:var(--lime);color:var(--lime)}
.rf-btn:disabled{opacity:.55;cursor:default}
```
JS: none needed on loader (disabled). On `done`, enable + link to report. Full interactive wiring lives in report; loader mirrors markup only.

## A11y (loader scope)
- `#cancel`/`#retry` already keyboard buttons — keep `<button>`, add `aria-label` if text changes.
- `#pct` gets `role="status" aria-live="polite"` so screen readers hear progress (one attr).
- Timer `#timer` `aria-hidden="true"` (decorative; stage list is the live signal).

## Verify
- `curl -s http://127.0.0.1:8138/job/<id> | grep -o "rf-explorer"` → hit after apply
- Cancel/Retry look identical, thumb 64px rounded kept.

Next: reply `loader-from-ui-polish: applied`; integrator e2es.
