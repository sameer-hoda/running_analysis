# COVER-ART BRIEF — study artwork gallery + enhancement (user-ordered 2026-09-20)

## 1. Context
v4 has two art sets: `research/papers/covers/` (11 study posters, typographic
voice approved) and `site/assets/zones/` (7 zone diagrams). They surface on the
homepage carousel, the loading paper-rail, and below the studio — but there is
no single place to SEE and judge them all, and some are still placeholders.
User will iterate on design with you before anything merges to the main site.

## 2. Mission (in order)
1. AUDIT: count every artwork file in both sets; verify each opens as a valid
   image; report the counts + any missing/corrupt/placeholder pieces.
2. BUILD a sandbox gallery page (new file, e.g. `site/art-sandbox.html`, NOT
   linked from the main site): three sections mirroring the three surfaces —
   (a) homepage carousel cards, (b) loading-rail previews, (c) below-studio
   research cards — each rendering the real current assets.
3. RESEARCH the internet for best-in-class showcase components (carousels,
   rails, masonry, lightboxes) and propose 2–3 options with links; user picks.
4. ENHANCE placeholders with Nano Banana: Gemini `gemini-2.5-flash-image`.
   Key: `GEMINI_API_KEY` in `../v3-tripo-cloud/.env` (same key/model as
   `site/assets/coach-kabeer.jpg` and the zone set — ask voice-coach/zone-art
   via handoff for the exact call pattern). Keep the approved typographic voice
   (giant condensed type, monochrome + lime accent, citation footer) unless the
   user directs otherwise in review.
5. Iterate ONLY in the sandbox until the user signs off in chat (via watcher).
   NEVER merge into landing/report/loader until watcher gives written approval.

## 3. Success looks like
- `/art-sandbox.html` (or agreed URL) renders all counts correctly with zero
  broken images; user can judge every piece in one scroll.
- Every placeholder replaced with signed-off art; live site untouched meanwhile.

## 4. Keep in mind
- API costs are image-gen calls on the user's Gemini key: batch deliberately,
  no blind regens; reuse approved pieces.
- Taste filter (SHOWCASE_BRIEF.md): no gradients/glass/bento/hover-scale/emoji.
- Kabeer display / Kabir voiceId / zero Darmani anywhere in new copy.
- Server rule: background tasks for servers, never main-turn foreground.
- No paid Tripo builds, ever, for this task (no 3D needed).

## 5. Prove it
- Counts + validity script kept in repo (e.g. extend
  `research/papers/make_covers.py --check` or a small gallery check).
- Screenshot-or-view-source proof per sandbox section; e2e untouched and green.
- Handoff `cover-art-showcase.md` with counts, decisions, open questions.

## 6. Done signal: CHANGED / PROOF / FLAGS / NEXT. Stand down after sign-off.
