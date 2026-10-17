# Handoff: cover-art → showcase / core-loop / watcher (audit + sandbox DONE, 2026-09-20)

## 1. Counts (audited this turn, PIL-verified)

- `research/papers/covers/`: **11/11 JPG, all open valid, 600×800 RGB** (39–125KB,
  per-image stddev 40–94 — real artwork, zero solid/grey placeholders).
  `make_covers.py --check` → COVERS GREEN.
- `site/assets/zones/`: **7/7 JPG, all open valid, 600×800 RGB** (39–116KB, real variance).
- Missing / corrupt / placeholder: **none**. COVER_BRIEF §2.1's "some are still
  placeholders" does not match disk — both sets are final approved work
  (covers: typographic voice per showcase §8; zones: watcher "approved" per
  zone-art handoff). Step 4 (Nano Banana enhance) has **no target** unless the
  user names specific pieces in sandbox review. $0 spent this turn, no API calls.

## 2. Sandbox gallery (NEW, unlinked, sandbox-only)

- `site/art-sandbox.html` — three sections mirroring the three live surfaces,
  data live from `/research/papers/catalog.json` (no hardcoded titles):
  - (a) `#sec-carousel`: 11 cards mirroring `_showcase_card` (mast, cover with
    thumbs fallback, title, finding, Read more → `/research/<slug>`).
  - (b) `#sec-loading`: `#railStage` rotator mirroring `#paperrail` (7s,
    reduced-motion safe) + pool grid of all 11 rotation thumbs.
  - (c) `#sec-studio`: `#sciList` rows mirroring `renderSci()` (demo weak zones
    feet_strike/knees/trunk_lean, max 6) + `#zoneGrid` with all 7 zone diagrams
    (their first render anywhere — no live surface uses zones yet).
- Taste: dark/lime, no gradients/glass/bento/hover-scale/emoji;
  `prefers-reduced-motion` respected; `noindex,nofollow`; not in sitemap;
  **not linked from any live page** (verified: no href to art-sandbox elsewhere).
- Kept-in-repo check: `site/art_sandbox_check.py` → ART-SANDBOX GREEN
  (counts + validity + catalog↔covers match + section markers + zone refs;
  `--base URL` adds live 200 checks for all 18 images).

## 3. Additive server.py diff (for core-loop — announce, no existing route touched)

- `GET /art-sandbox` + `/art-sandbox.html` → serves the file (no cache header,
  iterate freely). `GET /assets/zones/<name>.jpg` → static jpeg, basename +
  `^[a-z0-9_]+\.jpg$` guard, traversal → 404 (mirrors the covers route).
- Landing / report / loader markup untouched; sitemap untouched.

## 4. Proof (scratch :8162, live :8140 untouched — it was down when checked)

- `python3 site/art_sandbox_check.py` → ART-SANDBOX GREEN (offline).
- `python3 site/art_sandbox_check.py --base http://127.0.0.1:8162` → GREEN
  (sandbox 200 + 3 sections, covers 11/11 200, zones 7/7 200, catalog 200).
- View-source per section: `curl /art-sandbox.html | grep sec-carousel|sec-loading|sec-studio`
  → all three `id="sec-*"` present.
- `BASE=http://127.0.0.1:8162 ./site/e2e_check.sh` (unmodified) → E2E RED on two
  PRE-EXISTING checks only, both outside cover-art scope: (1) `darmani string
  present` — hit is `docs/REQUESTS_AUDIT.md`, a file cover-art never touched
  (own files grep 0); (2) `script contract` — `default: 3 plays rotate leads
  (hips_pelvis×3)`, voice-coach rotation logic in `report_template.html`/jobs
  data, untouched by this diff. All §12 showcase markers + all cover/detail/
  sitemap checks pass; no failure touches the additive routes.

## 5. Open questions for watcher / user review

1. Step 3 (showcase-component research, 2–3 options + links) and step 4
   (Nano Banana regens) are **deferred** — brief orders audit + gallery first,
   and there are no placeholders to enhance. Proceed on user pick after review?
2. Zones have no live surface: when approved, who wires `/assets/zones/` into
   the report (studio-3d owns `report_template.html`)? Propose handoff then.
3. Scratch :8162 dies with this session (macOS) — relaunch to review:
   `set -a; . ../v3-tripo-cloud/.env; set +a; PYTHONPATH=<v4>/.venv/lib/python3.14/site-packages python3 site/server.py 8162`,
   then open `http://127.0.0.1:8162/art-sandbox.html`.

## 6. COVER REDESIGN — moodboard pass (2026-09-20, user-directed)

- User supplied a duotone type-poster moodboard (colossal cropped condensed type,
  hard duotone contrast, full-bleed). Prompts retooled in `make_covers.py`
  (CANVAS: absolute full-bleed, oversized edge-cropped type interacting with the
  figure, exact-spelling rule; lime kept as the single accent for site coherence).
- 20 paid `gemini-2.5-flash-image` calls: full 11-regen + second passes
  (souza/cavanagh/van-gent/bramah/daoud) + third passes (daoud echo fix, souza
  labels) + bramah/souza recovery regens. Every final read back visually.
- Frames the model baked in were removed deterministically (PIL crop+resize to
  600×800) on cavanagh/souza/van-gent/willwacher/xu — captions verified intact
  except xu lost its microstrip (mast on cards still shows the journal).
- Accepted minors for user review (no more rolls without direction): souza has
  SIDE twice; bramah shoes carry tiny swooshes (3 gens running); willwacher
  struck list lacks 10K.
- PROCESS LESSON (mine): blind-coordinate PIL surgery damaged bramah (E bar) and
  souza (90×110 black wipe); both recovered via regen. No more pixel edits
  without zoom-verified coordinates — regen first.
- Aspect ratio: files exactly 600×800; sandbox cards lock `aspect-ratio:3/4`
  with width/height attrs — zero distortion, zero shift. Served bytes
  md5-identical disk-vs-route (daoud verified).
- Checks: `art_sandbox_check.py` offline + `--base :8162` → ART-SANDBOX GREEN
  (covers 11/11 200, zones 7/7 200). Live site untouched; sandbox-only.

## 7. SANDBOX BUG — blank page (user report, fixed same turn)

- Symptom: `/art-sandbox.html` loaded (200) but rendered zero images — a missing
  `)` in `esc()` (`}[c];};}` instead of `}[c];});}`) killed the whole inline
  script. One-char fix in `site/art-sandbox.html:158`.
- Durable guard: `art_sandbox_check.py` now runs `node --check` on the inline
  script (skips cleanly when node is absent).
- Real render proof (Playwright/Chromium, scratch :8162): 11 carousel cards +
  rotator + 11 pool + 6 sci rows + 7 zone cards = 36/36 images with naturalWidth
  > 0, zero failed/4xx requests. Earlier "9 broken" was lazy-loading below the
  fold, confirmed by scrolling both axes to 0 broken.

## 8. FADE-PRO CARDS + NATIVE-SQUARE REGEN (user-directed, this turn)

- Sandbox section A rebuilt as a testimonial-fade-pro adaptation: square cover
  with right-edge fade mask dissolving into kicker (journal · year) + position
  numeral, full HTML paper title, key finding, Read-the-study link; arrows +
  "n / 11" position + dots, 6s auto-advance with pause on hover/focus, keyboard
  arrows, reduced-motion safe, mobile stacks with downward fade.
- Generator retooled to native square: `make_covers.py` now has a COPY table
  (kicker/keyword/footer/figure per paper) and center-crop-square → 800×800
  (never force-fit). Baked text is kicker + one keyword + takeaway footer; full
  title/finding stay crisp HTML in the card.
- 16 paid calls: full 11-regen + fixes (van-gent/bramah/xu/willwacher; xu needed
  a retry after an API no-bytes hiccup). Every final read back visually.
  Frames removed by crop on van-gent/xu only. Remaining accepted minors:
  bramah shoe swooshes (faint, 4th gen running); willwacher footer dots.
- Proof: offline GREEN (11× 800×800); live GREEN; Playwright: 11 fade cards,
  nav 1→11 verified, 36/36 images naturalWidth>0, zero bad requests;
  section screenshot confirms the dissolve look.
- OBSERVED (not touched, approved zone set): `feet_strike.jpg` has a ~20px
  baked white strip at its base. Say the word if zones should be cleaned too.
- Home (`_showcase_card` rail) + studio (`renderSci`) wiring explicitly
  DEFERRED to after watcher sign-off — sandbox-only rule holds.

## 9. UNIFIED FADE LOOK (user: "everything like section A", this turn)

- One shared `fadeCard()` builder now drives all three sandbox sections: (A) 11
  with carousel controls, (B) single rotating card (7s paperrail behavior),
  (C) 6 static stacked cards linking out to publishers. Section C2 zone grid
  unchanged (different asset set, approved).
- Proof: GREEN checks; Playwright 11+1+6 fade cards, no JS errors, 36/36 images
  0 broken after full traversal, zero bad requests; full-page screenshot
  confirms one visual language throughout.
- Live-site merge (landing rail → fade cards, report rows → fade cards) NOT
  applied — needs watcher written approval.

## 10. MERGE — fade live on landing + studio (MERGE-APPROVED, this turn)

- `site/server.py`: section 6 rail → server-rendered fade cards (all 11 titles
  in HTML, ItemList JSON-LD kept, `id=science` untouched); SHOWCASE_CSS/JS
  replaced with the sandbox-proven fade set (auto 6s, pause hover/focus,
  arrows+dots+position, keyboard, reduced-motion). Detail pages/sitemap/routes
  untouched. Old `sc-*` rail markup/CSS/JS fully removed, no orphans.
- `site/report_template.html` (studio-3d's file — this section only):
  `renderSci()` rows → static fade cards with square covers (+thumbs fallback),
  external publisher links kept. `sciRail` id + `renderSci` name kept so §8b2
  markers still pass. Heads-up to studio-3d.
- `site/e2e_check.sh` §12 updated to the fade markers (same coverage: track,
  cover img, research link, ItemList, arrows, dots, +position). Old
  `scRail/scPrev/scDots/snap` markers retired with the rail they asserted.
- Live proof on :8140 (PID 82952, started 18:29 by another pane with this tree
  — process untouched, mine is scratch :8162 only): e2e → **E2E GREEN**
  (pre-existing darmani/script failures also clear); art_sandbox_check --base
  :8140 GREEN; Playwright: 11 landing fade cards + 11 titles, nav 1→11,
  6 studio fade cards on /report/demo, no JS errors, zero bad requests;
  #science screenshot confirms the live look. The single empty-src img is the
  pre-existing `#preview` upload placeholder, not a cover.

## Done signal
CHANGED: `site/art-sandbox.html` §A (fade cards), `make_covers.py` (COPY/square),
11 square covers, `art_sandbox_check.py` (800px + fade markers) /
PROOF: all 11 finals visually read + 36/36 render proof + GREEN checks /
FLAGS: bramah swooshes; feet_strike white strip (zones, untouched) /
NEXT: user judges fade cards at :8162/art-sandbox.html; home+studio on sign-off.
