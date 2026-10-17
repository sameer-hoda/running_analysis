# Handoff: landing → integrator (session 2 polish, 2026-09-12)

Landing brief complete + polish merged. Only LANDING + CSS blocks touched (`site/server.py` CSS ~44-77, LANDING ~124-148). Server restarted, verified live.

1. Hero: 1 photo (`/examples/images-3.jpeg`), 1 score badge (63/sample), 1 primary CTA "Analyze my run" → `/login`, sample as quiet link → `/report/demo`. Unchanged, still good.
2. Drop zone is now a real link: `<a class=drop href=/login>` (was static div) + CSS `display:block;text-decoration:none` + lime hover border. Full-width tap target, min-height 44px.
3. Dropped all `onerror=this.remove()` fallbacks (hero + 3 thumbs) per your "route LIVE" note — real `<img>`s with descriptive alts now. Thumbs still images-3/4/5 pattern from `reference/input/`.
4. Mobile: added `.step{min-width:100%}` to the 640px query → true single-column (hero, thumbs wrap, steps stack). `.btn` full-width 44px min-height, `.quiet` centered block. Unchanged.
5. Step strip still capped at 5 bullets with times (Upload ~10s, Audit ~60s, Mesh ~60s, Score ~5s, Drills instant).

Verify proof (just ran):
- `landing:200`, `demo:200`, `images-3/4/5:200`, `grep -c onerror` → 0, `class=drop href=/login` present, `.step{min-width:100%}` present.

Next: nothing needed from you — no route changes. Run e2e whenever ready. Tokens still untouched, awaiting ui-polish sign-off.
