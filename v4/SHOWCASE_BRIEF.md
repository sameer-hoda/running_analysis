# V4 SHOWCASE-SEO agent — landing bottom half (below steps 1-2-3) + SEO

You own ONLY the bottom of the landing page. Do not touch the hero/upload,
pipeline, studio, auth, or growth code — coordinate through handoffs.

## Problem (see user screenshot 2026-09-20)
Below steps 1-2-3, the studies section is verbose walls of text — not cool,
not clickable, weak SEO. Redesign it completely.

## What to build
1. **Monochrome cover per study** via Nano Banana (Gemini gemini-2.5-flash-image —
   voice-coach already used it for `site/assets/coach-kabir.jpg`; same key in server
   env). One striking B/W cover per paper in `research/papers/covers/` (hero-run
   energy: track at dawn, mid-stride silhouette, grain). Keep palette lime-on-dark.
2. **Floating carousel UI** — smooth, auto-drift + drag, `prefers-reduced-motion`
   respected. Each card: cover, paper title, one-line finding, "Read more".
3. **Detail page per study** — route like `/research/<slug>`: summary, methods
   signal, key finding, which analysis rule it backs, figure/snippet from deep
   entries, and the real DOI/PubMed link out. Real links, no placeholders.
4. **SEO** — semantic HTML, per-page meta/OG, JSON-LD (ScholarlyArticle), sitemap
   entries, internal links from landing. Measure: view-source check + e2e additions.

## Data (do not hardcode)
- `research/papers/catalog.json` (11 papers, thumbs) + `research/papers/deep/`
  (summaries, figures, citations, rule links). Extend schema only via handoff with
  research-catalog. Covers referenced by slug.
- Landing owner is core-loop: propose the integration contract in
  `.agents/handoffs/showcase-core-loop.md` and let core-loop wire it (or wire it
  yourself only with their written OK in a handoff).

## Bar
- Covers generated with the real API (no grey boxes), carousel runs at 60fps
  feel, detail pages for all 11 papers, e2e additions green, `site/e2e_check.sh`
  still GREEN, no server.py conflicts (talk to core-loop first).
- Out of scope: hero 3D demo video (separate agent later, needs Tripo credits).

CWD: `/Users/sameerhoda/Projects/running_analysis/v4`. Server :8140. Theme stays.

## Taste filter (applies to your carousel/cards/pages)
Avoid the AI-slop tells: no purple/blue gradients, no gradient headline text, no
aurora glows, no identical 3-card grids, no bento, no glassmorphism everywhere,
no single radius on everything, no hover:scale lifts, no emoji icons, no
scroll-fade on everything — and always honor `prefers-reduced-motion`.
Monochrome covers + lime-on-dark already steer clear; keep it that way.
