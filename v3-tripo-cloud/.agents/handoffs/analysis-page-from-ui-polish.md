# Handoff: ui-polish → analysis-page (2026-09-12)

You own `site/report_template.html`. Token block + full explorer wiring here; loader mirrors your markup (disabled).

## 1. Token block (replace `:root` line 8)
```css
:root {
  --lime: #c8f04a; --bg: #0d1117; --panel: #151b23; --ink: #eef2e9; --dim: #9aa39b;
  --optimal: #2FBF71; --fair: #E5A23B; --critical: #E0533D; --insuf: #8E9BB0;
  --line: #1e2630; --line2: #2e3945;
  --radius: 14px; --radius-sm: 10px; --radius-pill: 999px;
  --font: system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --tap: 44px;
}
```

## 2. Explorer CSS (append to `<style>`, replaces ad-hoc `button` rules for explorer rows)
```css
.rf-explorer{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:12px;align-items:center}
.rf-group{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.rf-lbl{font-size:12px;color:var(--dim);margin-right:2px}
.rf-btn{background:#1c232d;color:var(--ink);border:1px solid var(--line2);border-radius:8px;padding:7px 12px;font-size:13px;cursor:pointer;min-height:var(--tap);min-width:var(--tap)}
.rf-btn[aria-pressed="true"],button.active{border-color:var(--lime);color:var(--lime)}
:focus-visible{outline:3px solid var(--lime);outline-offset:2px;border-radius:6px}
#blend{width:160px;accent-color:var(--lime);min-height:var(--tap)}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
```
Then: every explorer `button` gets `class="rf-btn"` + `aria-pressed` (views: radiogroup pattern below). Keep ids (`spinBtn wireBtn wallBtn origBtn shareBtn printBtn blend`) — JS untouched.

## 3. Explorer markup (replace the two `.row` divs, lines 67-88 — same ids, same data-view)
```html
<div class="rf-explorer" role="toolbar" aria-label="3D view options">
  <div class="rf-group" role="radiogroup" aria-label="Camera view">
    <span class="rf-lbl" id="rfViewLbl">View:</span>
    <button class="rf-btn" data-view="hero" aria-pressed="true" aria-labelledby="rfViewLbl">¾</button>
    <button class="rf-btn" data-view="front" aria-pressed="false">Front</button>
    <button class="rf-btn" data-view="side" aria-pressed="false">Side</button>
    <button class="rf-btn" data-view="back" aria-pressed="false">Back</button>
    <button class="rf-btn" data-view="top" aria-pressed="false">Top</button>
  </div>
  <div class="rf-group" role="group" aria-label="Display">
    <span class="rf-lbl">Display:</span>
    <button class="rf-btn" id="spinBtn" aria-pressed="true">Spin: on</button>
    <button class="rf-btn" id="wireBtn" aria-pressed="true">Wireframe: on</button>
    <button class="rf-btn" id="wallBtn" aria-pressed="false">Measure wall: off</button>
    <button class="rf-btn" id="origBtn" aria-pressed="false">Original colours</button>
  </div>
  <div class="rf-group" role="group" aria-label="Compare">
    <span class="rf-lbl"><label for="blend">Compare:</label></span>
    <input id="blend" type="range" min="0" max="100" value="0" aria-label="Reveal original photo over 3D">
    <span class="rf-lbl">photo ↔ 3D</span>
    <button class="rf-btn" id="shareBtn">Share</button>
    <button class="rf-btn" id="printBtn">Print</button>
  </div>
</div>
```
JS contract (add ~6 lines to your existing handlers, or keep as spec): every `data-view` click sets `aria-pressed` on siblings; toggles flip `aria-pressed` + text (`Spin: on/off` etc.); keys `1-5` views, `s` spin, `w` wire. Loader uses same markup disabled — no fork.

## 4. Status colors → tokens (kills hardcoded hex drift)
- Legend line 91: `style="background:#2FBF71"` → `style="background:var(--optimal)"` (same for fair/critical/insuf).
- JS line 108: `STATUS = { optimal:"#2FBF71",…}` → read from CSS: `getComputedStyle(document.documentElement).getPropertyValue('--optimal').trim()||"#2FBF71"` (fallback kept so offline still works). Same for others.
- Marker/card styles: keep, add `.card{border-radius:var(--radius-sm)}` + `.card .pill{min-height:var(--tap)?}` no — pills stay small text, only interactive cards need 44px: cards already full-width click targets, fine.

## 5. A11y pass (report scope)
- All `.rf-btn` ≥44px (new) — fixes current 7px-padding buttons failing tap target.
- `aria-pressed` on all toggles; `radiogroup` on views; `label for="blend"` (new).
- Reduced-motion: default `spinBtn` to OFF when `matchMedia('(prefers-reduced-motion: reduce)').matches` (one `if` in init).
- Contrast: `--dim` on `--bg` ≈ 7:1 pass; lime-on-dark pass; keep pill text dark-on-status (`#10130a` on fair) — check your `.pill` bg rules use status bg + dark text.
- `#badge` kbd hint already documents keys — keep.

## Verify
- `curl -s http://127.0.0.1:8138/report/demo | grep -o "rf-explorer"` → hit after apply
- Click each view → camera moves + `aria-pressed` flips; spin/wire toggle; slider crossfades; keyboard 1-5 works.

Next: reply `analysis-page-from-ui-polish: applied`; integrator e2es all 3.
