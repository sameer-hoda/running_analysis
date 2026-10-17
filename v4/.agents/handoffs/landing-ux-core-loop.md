# Handoff: landing-ux → core-loop (+ showcase-seo CC)

Date: 2026-09-20. Scope: REQUESTS_AUDIT items 3, 4, 7, 26, 27.
Rule honored: additive files preferred (core-loop session fragile).

## What landed

NEW file (no existing file depends on it):
- `site/landing_overhaul.py` — pure-string module: `CSS_ADD` (lu- prefixed,
  flat lime-on-dark, no gradients/glass/bento/hover-scale/emoji, no
  animation so reduced-motion is trivially honored), `HERO_H1` /
  `HERO_LEAD` / `HERO_TRUST`, `PROOF_HTML` (id=proof, honest 3-item strip
  linking /report/demo, /#science, /#faq), `PRIVACY_HTML` (id=privacy,
  matches the upload-screen contract), `UPLOAD_META`.

`site/server.py` — 6-line hook only (import with old-copy fallback +
CSS_ADD in LANDING head + hero swap + PROOF/UPLOAD_META/PRIVACY inserts).
Revert = delete those lines; page renders the old copy without the module.

Missing-asset fix (item 4, live-verified BEFORE restart, no reboot needed):
copied byte-identical from `../v3-tripo-cloud/site/assets/` into
`site/assets/`: `hero-run.mp4`, `showcase.mp4`, `showcase-poster.jpg`,
plus `logo.png`, `og-image.jpg`, `favicon.ico`, `apple-touch-icon.png`
(all four were also 404 — SEO head references them). All 200 live with
matching byte counts.

## Item-by-item

- 3 (bold-promise H1): "Your running form, exposed — every flaw, every
  fix, in 3D." Keeps the "running form" SEO phrase; lead keeps "stride"
  (e2e §1 greps it).
- 4 (proof/nudge): videos now 200; proof strip points at verifiable
  routes only (no fake testimonials/stats, per 2026 landing research).
- 7 (privacy-first): landing privacy mentions 0 → 10 (hero trust line,
  upload microcopy + history link, dedicated #privacy section).
- 26 (overhaul): hero → proof → try/upload → steps → privacy → FAQ →
  science order follows problem/solution/proof + trust-first research.
- 27 (studies beauty): showcase untouched — id=science, scRail/scPrev/
  scDots, ItemList JSON-LD, all 11 titles/covers/Read-mores preserved
  (verified in rendered output). Showcase CSS/JS not edited.

## Restart + verify (landing-ux owns this round)

- Pre-restart: no ACTIVE jobs (queued/analyzing/meshing = none), so the
  reboot fails nothing mid-flight.
- Relaunch with the proven command (keys + PYTHONPATH), then:
  `BASE=http://127.0.0.1:8140 ./site/e2e_check.sh` must be GREEN,
  plus live curl checks for the H1, #proof/#privacy, and both mp4s.
- macOS caveat (same as showcase §§6-9): the relaunched :8140 lives in
  this session and dies with it.

## Asks of core-loop / showcase-seo

1. If the H1 voice is wrong, edit copy inside `site/landing_overhaul.py`
   only — no server.py rework needed (restart picks it up).
2. Showcase: confirm the rail still drifts/measures clean on your next
   pass; my diff adds no styles outside `.lu-*` and no landing JS.
3. Watcher: items 3/4/7 flip to YES once e2e is GREEN on live :8140.

## E2E result (2026-09-20 ~16:10, live :8140, relaunched with this diff)

- Landing scope ALL GREEN: landing 200 + "stride", upload guard/login/
  job/stage, demo report + studio-3d + Kabeer markers, demo mesh,
  examples, full §12 showcase block (rail/covers/arrows/dots/snap,
  11/11 research 200, ScholarlyArticle + canonical + guide links,
  traversal/unknown 404, sitemap). Proof videos + brand assets 200.
- One RED, out of landing scope: `script contract`
  (`node site/demo_script_test.js` on report_template.html + fixture
  analyses — pure file test, no HTTP, untouched by this diff):
  `demo:default est 16.26s > 15s cap`, `02652674ecda:default est
  17.62s > 15s cap` (= audit item 18, default-tour-too-long bug), and
  `02652674ecda:demo beats only from suitable zones` (= audit item 19,
  silence rule). Owned by voice-coach + studio-3d; left for them, test
  not narrowed or skipped.
- Own test job dirs (`c5cd7203935e`, `7cacbcd32899`, test lane, $0)
  removed; all other job dirs untouched (36 remain).

## ADD-ON: meta + OG descriptions in H1 voice (2026-09-20 ~16:15)

- Watcher verified the old tags missed a standard `name="description"`
  check (unquoted attrs) and the copy predated the H1 overhaul.
- `site/landing_overhaul.py`: new `META_DESC` (152 chars) + `OG_DESC`
  (149 chars), plain text, "running form" head term kept, JSON-LD
  untouched. `site/server.py`: import + fallback (old copy) + 3 hook
  lines (meta, og:description, twitter:description reuses OG_DESC).
- Live view-source: both new descriptions present; H1/stride/carousel/
  ItemList/FAQ/proof/privacy markers all still present.
- `./site/e2e_check.sh` on live → **E2E GREEN, zero FAILs** (the prior
  script-contract RED from items 18/19 no longer reproduces — owning
  tracks evidently fixed it since; nothing narrowed or skipped).
- Own test job `ea9e5e42ac01` (test lane, $0) removed;
  `dc1c536c3961` (16:09, another agent's concurrent lane) left alone.

## SITE-TIDY audit + fix (2026-09-20 ~18:05, user: steps 1-2-3 renders off)

Audit method: live :8140 + headless Chromium at 1280/768/390 (element
screenshots eyeballed: fold/steps/analyse/proof/privacy; full-page
downscaled for rhythm) + DOM metrics (overflow, boxes, order). Before
shots: /tmp/tidy_before_*.png. No horizontal overflow anywhere
(docSW==docCW at 1280 + 390; only .sc-rail scrolls by design).

Defects (file:line refs from inspected bodies):
- A1 (the complaint) — steps trio heading-less + adrift between two
  CTAs: `site/server.py:1073-1077` (bare 3×`.step`, no heading).
  FIXED: trio is now `section.wrap.steps.lu-steps` + `STEPS_HEAD`
  ("How it works" + sub) from `site/landing_overhaul.py`; cards
  untouched. Verified: 3-across equal-height desktop (y=1970 ×3,
  h=104), stacked full-width 390/768, tops aligned.
- A2 — content gaps ~100-120px from `.wrap` bottom pad
  (`site/server.py:333`: 64px/56px) stacking with section margins
  (`.steps` margin-top:46, `site/server.py:360`; `.section2`
  padding-top:72). FIXED via landing-scoped overrides only (new rules
  in `landing_overhaul.py` CSS_ADD; shared `.wrap`/`.steps`/`.step`
  untouched so login/upload/job/guides + FAQ/science cards unaffected):
  proof 56/0, analyse 56/0, steps 56/0 (margin 0), privacy 56/0,
  faq 30/0 (+26 inline h2 = 56), science 30/64 page-end (mobile:
  48/48/48/48/22/22-56). Measured after: uniform ~56px rhythm,
  zero overflow.
- A3 — `.showvid` aspect: VERIFIED CORRECT, no change. ffprobe:
  showcase.mp4 1080×1080 square == `aspect-ratio:1/1`
  (`site/server.py:381`). The "ONE PHOTO IN" overlay is baked into
  the video's own opening title card, not a layout defect.
  hero-run.mp4 is 540×960 portrait; hero-bg `object-fit:cover` handles
  all widths (verified 390 + 1280).
- A4 — OBSERVATION (not touched; owner showcase/cover-art): `.sc-cover`
  frames 3/4 (`site/server.py:596` region) while covers regen'd to
  native 800×800 squares (cover-art §8) → landing crops baked edge
  type. Their home-wiring sign-off is pending; left alone.
- A5 — OBSERVATION (not touched; owner research-deep/core-loop):
  `_deep_card`/`_papers_card` imgs (`site/server.py:~471-481,~550-554`)
  have no width/height attrs → layout shift as figures load. Below
  fold; needs owner dims fix.
- A6 — OBSERVATION (no owner): landing ends abruptly after the rail
  (no footer). Propose follow-up, not this turn.
- A7 — grandfathered taste debt, untouched: pre-existing gradients
  (`.btn`, `.fold .glow`, `site/server.py:336,381`), dead `.hero-vid`
  CSS. My additions add none (flat only, no kicker, no animation).
- UNRESOLVED: user-device (Safari) confirmation of the original
  complaint still needed — Chromium shows no structural breakage, so
  the fix targets the supported reading (hierarchy + rhythm). If the
  user saw an actual overlap/tear, need their viewport + screenshot.

Collateral: `site/e2e_check.sh` §13 appended (tidy markers: lu-steps,
How it works, proof/privacy ids, trio labels) — additive, nothing
existing edited. `./site/e2e_check.sh` on live → **E2E GREEN, zero
FAILs** incl §12 + §13. Own test job `2f9259f557fc` (18:03, $0)
removed; 16:53/16:54 lanes left alone. After shots:
/tmp/tidy_after_{desktop,mobile,tablet}_steps.png + full pages.

## CENTERING-FIX (2026-09-20 ~18:30, user verdict: steps render off-center)

Root cause (measured, then eyeballed): `.lu-proof` carried `margin:0`
(`site/landing_overhaul.py:30-31`), which killed `.wrap`'s
`margin:0 auto` (`site/server.py:333`) — proof section pinned left at
x=0, w=1080 on 1280 viewports (offset -100px vs center; invisible on
390px full-width, which is why mobile looked fine). My bug from the
overhaul turn. Authentic failure observed on live HTML before the fix
(negative guard tripped); all other sections already measured off:0.

Fix (all in `site/landing_overhaul.py` CSS_ADD, no markup changes):
- `.lu-proof`: dropped `margin:0`, restored `padding:56px 22px 0`
  (mobile `48px 16px 0`) → uniform max-width container everywhere.
- Centered heads per brief: proof/steps/privacy h2 + subs
  `text-align:center` with auto side margins (sub bottom margins
  preserved: 18/18/16). Analyse column head left (grid context);
  FAQ/science heads left (core-loop/showcase owned — one-line
  follow-up if they want the centered system); full-bleed sticky nav
  intentional, not a defect.
- Taste: centering only (no kickers/pills/grids added, no animation).

Proof: section offsets all 0.0 at 1280 + 390 (proof/analyse/steps/
privacy/faq/science); computed head align `center` ×3 both widths;
after-shots eyeballed (`/tmp/centerfix_{desktop,mobile}_{steps,proof}.png`).
`site/e2e_check.sh` §13b appended (durable guards: negative grep for
the margin-kill rule + positive grep for the centered-heads rule).
`./site/e2e_check.sh` on live → **E2E GREEN, zero FAILs** incl
§12/§13/§13b. SEO/schema untouched (head + JSON-LD identical).
Own test job `052937e62b86` (18:30, $0) removed.

## SECTION-REORDER + SAMPLE-REPORT (2026-09-20 ~18:45, user-ordered, landed together)

Reading adopted (stated so watcher can correct): "hero/upload block" =
the conversion top (fold → proof → analyse); science goes immediately
after #analyse, above steps/privacy/FAQ-basics. Alternative (science
above the fold, splitting hero from upload) rejected: it would bury
the core-loop conversion spine under ~2600-3900px of papers.

Reorder (`site/server.py`): SCIENCE_HTML moved from tail
(`"</section>" + SCIENCE_HTML + "</main>"`) to after the analyse
close (before the lu-steps trio); all ids travel with the block.
Kickers renumbered to stay sequential (necessary consequence, flagged
for core-loop/showcase veto): science 05→01 DEEP DIVES
(`site/server.py:971`), rail header 06→02 THE PAPERS
(`site/server.py:775`, live branch — the 981 fallback already read
02), FAQ 01→03, 02→04, 03→05, 04→06 (`site/server.py:1083-1095`).
Rhythm swapped to match (science bottom 0, FAQ bottom 64/56 page-end;
`sitemap_xml()` verified page-URLs-only, no order refs — untouched).
Anchors all fragment-based (nav /#science, proof /#science+/#faq,
detail `/#science`, guides `/#analyse`, LANDING_JS #analyse scroll) —
order-free, all resolve live.

Sample repoint (THE sample = 02652674ecda, score 72, done): all 6
user-facing links, not just the 4 named (superset, same intent):
nav (`:1036`), hero ghostlink (`:1046`), trust (`landing_overhaul.py:84`),
proof (`:102`), research-detail CTA (`:925`), guide CTA (`:1424`),
plus sitemap loc (`:1282`, demo entry replaced). `/report/demo`
route + fixtures untouched (e2e §8 + tooling still use it).
FLAGGED follow-up (not changed, out of named scope): proof copy +
showcase vidtag still cite "score 69" (demo's score); new sample
scores 72 — one-line copy update whenever watcher wants it.

Collision note: at ~18:40 a concurrent fade-rail merge landed in
`site/server.py` (scRail/scPrev/scDots → fadeTrack/fadePrev/fadeDots,
`§12` updated to match — coordinated, header now cover-art's). My
in-flight edits survived intact; my kicker fix targeted the merged
text. No action needed; showcase owns the rail.

Proof (all observed live :8140 after restart, zero in-flight jobs):
- Byte offsets: analyse(18929) < science(20300) < faq(45506);
  proof < analyse < privacy < faq. Science = first section after upload.
- 4/4 landing sample links → /report/02652674ecda, 0 × /report/demo
  left on landing; sitemap lists report/02652674ecda only.
- `/report/02652674ecda` 200 + renders (var ANALYSIS);
  `/report/demo` 200 (kept); `/research/lieberman-2010` 200.
- `./site/e2e_check.sh` → **E2E GREEN, zero FAILs** incl updated §12
  (fade), §13/13b, and new §13c (order analyse<science<faq, anchors
  present, sample ×4, sitemap sample URL, sample renders).
- Kickers render sequential 01–06; SEO/schema (head + JSON-LD) byte-identical.
Own test job `47f21d9d255b` (18:44, $0) removed.

## SAMPLE-SWAP (2026-09-20 ~20:05, user: 0265's footstrike photo is a bad sample)

Target verified first: `aeb979a86e8b` side/stance, feet_strike 74
midfoot, overall 79, stage done, `/report/aeb979a86e8b` 200 + renders.
Swap: all 6 sample links + sitemap loc 02652674ecda → aeb979a86e8b
(`site/server.py` nav/hero/research-CTA/guide-CTA/sitemap +
`site/landing_overhaul.py` trust/proof/docstring) via scoped sed
(scope pre-verified: those 8 hits were the only refs in both files).
`/report/demo` route + fixtures untouched; e2e fixture migration
(aeb9/419d in script + lab tests) was another track's prior work,
preserved — only §13c sample assertions updated to the new id.

Restart note (deviation with reason): my relaunch failed EADDRINUSE —
PID 99813 (started 19:55:17, another owner's fresh server) already
serves the current tree (mtime 19:40/19:51, both pre-start), so per
protected-process rules I did NOT kill it. Verified instead that live
== tree: landing carries 4 × aeb9 / 0 × 0265, sitemap lists aeb9 only.

Proof (all observed live): `/report/aeb979a86e8b` 200,
`/report/demo` 200 (kept), `/report/02652674ecda` 200 (kept, unlinked);
`./site/e2e_check.sh` → **E2E GREEN, zero FAILs** incl §13c (order,
anchors, sample ×4, sitemap, renders). Own test job `38c4783b934c`
(20:05, $0) removed. Standing down.

## HOME-SANDBOX (2026-09-20 ~19:10, user: fancy components, sandbox-only)

URL: `http://127.0.0.1:8140/home-sandbox` (also `.html`; judge in browser).
Files: NEW `site/home-sandbox.html` (self-contained, inline CSS/JS) +
6-line additive route in `site/server.py:2182-2187` (mirrors the
art-sandbox/script-lab pattern, file-exists guard). Zero live changes:
no live page links to it (grep-verified), noindex/nofollow, not in
sitemap (verified 0 refs), no JSON-LD, no forms — CTAs are outbound
anchors to live routes only, nothing posts or creates jobs.

Research basis: GitHub `topics/ui-components?l=vue` index (fetched live;
names the vocabulary — vuetify/nuxt/vuestic/element-plus/naive-ui/primevue)
+ component-pattern search. Adapted to SSR, no framework: (1) hero proof
ticker (live paper count via catalog.json fetch + honest static markers);
(2) steps as vertical timeline with connected nodes (vs numbered cards);
(3) Q&A as grouped native `<details>` accordions (4 groups × 2, trimmed
with links to live /#faq); (4) studies as snap-rail cards rendered live
from catalog.json + covers (same data as home rail, distinct treatment);
(5) privacy as checklist rows; (6) minimal footer with route links.
Taste strict: flat colors only (zero gradients/glass/blur), varied radii,
no hover:scale, no emoji (text glyphs +/−/→ only), no scroll-fade,
left-aligned hero (not the banned centered-hero combo), no kickers,
`prefers-reduced-motion` disables all motion (rail is native snap,
nothing auto-advances).

Proof (all observed): `/home-sandbox` 200 (11,851 bytes) with all six
section ids + noindex; studies rail 11/11 cards from live catalog,
ticker reads 11, 8/8 accordions, zero failed/4xx requests at 1280 +
390; screenshots eyeballed (`/tmp/sb_{desktop,mobile}_{top,studies,qa}.png`)
incl. a mobile CTA-stacking fix verified live without restart (static
file served from disk per request). `./site/e2e_check.sh` → **E2E GREEN**
untouched (no e2e edits this turn). Own test job `d755d214ccd6`
(19:07, $0) removed. NEXT: user judges treatments in browser; promote
winners to live only on explicit pick.

## SANDBOX-WIRING (2026-09-20 ~19:20, user verdict: sandbox proves nothing without upload + model + dots)

All in `site/home-sandbox.html` only (no server.py change — route
already served from disk, no restart; no e2e change). Skill basis:
`plugin:threejs:threejs` hub + `threejs-loaders` (GLTFLoader load /
Box3 center-scale / error callback) + `threejs-interaction`
(OrbitControls damping/update/limits), mapped onto the live UMD globals
(`three@0.147.0` build + examples/js controls + loaders — the exact
scripts `report_template.html:256-258` uses).
- (1) Upload wired to the REAL contract: multipart `photo` field →
  `POST /api/jobs?test=1`, same JSON `{job_id}` + guest-cookie flow as
  live (`server.py:2521`, `is_test_upload` covers `?test=1`), status
  poll on `/api/jobs/<id>`, links to live `/job/<id>` + `/report/<id>`.
  Pinned + labeled test lane ($0 stub mesh); form never touches the
  paid lane. Sandbox-tag copy updated (it claimed "nothing posts").
- (2) REAL 3D stage: renderer/camera/controls/lights mirrored from
  live `init3D` (`report_template.html:1191-1212`: WebGLRenderer
  antialias+alpha, sRGB+ACES, fov 38, OrbitControls damping .07 /
  rotate .85 / zoom 1.1 / no pan / polar .18–.52π, hemi+ambient+key+
  fill+rim) + `GLTFLoader().load('/jobs/demo/mesh.glb', ok, undefined,
  err)` (`:1614` shape) + Box3 ground+center framing (`:1628-1630`
  pattern). Plain mesh only — zone overlays stay on the live report
  (labeled as such). Reduced-motion: render-on-change instead of rAF.
  Probe hook `window.__stage`.
- (3) Dots restored: `<canvas id=dots-bg>` + `/assets/dots.js`
  (1657 bytes, motion-safe, zero deps) + the fixed-position rule.
- Taste: flat stage frame, no new gradients/glass/scale/emoji; mobile
  CTA stacking kept from last turn.

Proof (all observed): node --check clean on all 3 inline scripts;
`/home-sandbox` 200 with try/model/stage/upload/dots/three/GLTF/
Orbit/test-lane/demo-mesh markers; sh upload `c7d185afc6a3` →
analyzing → done 69 → mesh 200; in-page: dots canvas 1280×900,
`__stage` ready with 1 mesh, drag-orbit diff 132,851 bytes, form
submit → live watch link, zero failed/4xx at 1280; stage screenshot
eyeballed (textured runner, `/tmp/sb_stage_after.png`).
`./site/e2e_check.sh` → **E2E GREEN unmodified**. Own proof jobs
`c7d185afc6a3` (sh) + `3d332e2409a5` (browser) + e2e `293ee7520dc2`
($0 lanes) removed; 19:04 lane left alone.
