# voice-coach → core-loop + pipeline-auth (2026-09-20, FULL e2e results)

## What changed (v4 only)
- `site/server.py:92`: Inworld TTS fallback voice `Sarah` → `Kabir`
  (matches `INWORLD_TTS_VOICE=Kabir` voiceId already in sandbox .env + client default).
- `site/report_template.html`: Coach Kabeer identity, no credentials/numbers anywhere:
  tour-HUD avatar chip + name + voice status, "Kabeer is reviewing your run…"
  loading state, "Play Kabeer's walkthrough" button, scorecard coach strip
  ("Every call cross-checked against published gait research").
  `tag()` statuses normalized (bare "Coach:" prefix gone).
- `site/assets/coach-kabeer.jpg`: new (renamed from coach-kabir.jpg), Gemini `gemini-2.5-flash-image`, 24KB.
- `site/e2e_check.sh` §8c (durable collateral): coach avatar 200, demo contains
  `coach-kabeer.jpg` + `Kabeer is reviewing` + `Play Kabeer`, voice id `Kabir`,
  voices list contains Kabir.

## FULL e2e on :8140 — 25/26 green (FULL=1 POLL_MAX=240, job bb192440b28c, fresh PID 19105)
Green: everything including tts voice id Kabir / coach Kabeer (restart picked up the fix).
node --check clean. Only `pipeline done` still red — same two stacked causes
(see below); re-verified on the new job, unchanged.

## Two failures — both need OWNER action, neither is fixable in repo code
1. `tts voice (got Sarah)`: :8140 process (PID 16018, started 11:48) predates the
   voice-coach fix, so its in-memory default is still Sarah. File is correct
   (witness-proven). Fix = restart the server. I did not restart it: it is
   another session's long-lived process, and a restart from my session would
   not survive session end on macOS (no setsid) — it must be relaunched by its
   owner. After restart, `voice` reads Kabir (provider id; display is Kabeer).
2. `pipeline done (stage=failed)`: TWO stacked causes, both outside voice-coach:
   a. `TRIPO_API_KEY is missing in .env` — the v4 cutover stranded Inworld +
      Tripo keys in `v3-tripo-cloud/.env` (v4 has no .env by design, and secrets
      must stay out of the repo). Serves as env: `set -a;
      . /Users/sameerhoda/Projects/running_analysis/v3-tripo-cloud/.env; set +a`
      (6 vars: INWORLD_API_KEY, INWORLD_TTS_VOICE=Kabir, TRIPO_API_KEY,
      TRIPO_MODEL, TRIPO_FACE_LIMIT, GEMINI_API_KEY) before launching.
      Same file restores `configured:true`.
   b. Default e2e image `reference/input/images-3.jpeg` is a stick-figure
      illustration — audit correctly rejects (`is_running:false`), and the
      pipeline fails fast before any 3D download. FULL with the default IMG
      can NEVER reach done, even with keys. Suggests pipeline-auth pick a real
      runner photo as the FULL fixture (try images-4/5).
   Note: current code hard-fails without Tripo ("no stand-in is shown") while
   README/docstring still promise demo-mesh fallback — pipeline-auth to reconcile.

## Suggested owner one-liner (from v4, restores pre-cutover parity + picks up fixes)
`set -a; . ../v3-tripo-cloud/.env; set +a; python3 site/server.py 8140`
then re-run `FULL=1 POLL_MAX=240 ./site/e2e_check.sh` with a real-runner IMG.
Expected: 26/26 green.

## Update post-restart (PID 19105, 12:09)
Restart done WITHOUT sourcing keys: `voice` now Kabir ✓ but
`configured:false` persists. Consequences: (a) walkthrough narration renders
in system/Kokoro voice, NOT Kabeer's Inworld voice — hearing Kabeer himself
needs INWORLD_API_KEY in the server env; (b) Tripo leg still hard-fails, so
`pipeline done` stays red. Both clear once the server is relaunched with the
one-liner above. No code change needed from any agent for either.

## DEMO D1-D5 implemented (2026-09-20, watcher-approved DEMO_DIRECTION.md)
Voice-coach owned D1/D2/D4/D5 + Kabeer rename; D3b handed to studio-3d
(`studio-3d-from-voice-coach.md`).

- D1: default overview opener is now the hook — "Your stride is braking —
  here's where. I'm Kabeer — you scored …" (dropped "Alright, coach here!").
- D2: rotation via `rf_tour_count`/`rf_tour_lead` — lead cycles worst-3, never
  repeats; ordinals rotate Worst first/First up/Opening with; CTA alternates
  2 variants by parity. Verified: 3 plays → arms, hips, knees.
- D4: `?story=demo` branch → 4 beats [overview hook, focus worst, glide foot,
  free CTA] with per-step `gap` (150 ms) + `rate` (1.15x) now threaded through
  speakStep→COACH.speak→playSrc→playBlob/playUrl. Showcase/teaser/default
  paths untouched. Demo beat copy is dynamic (worst zone, foot-unclear check,
  score) so non-demo jobs degrade sanely.
- D5: button reads "Play Kabeer's walkthrough (14 s)" only on ?story=demo.
- Infra: `prefetchAll` is now concurrent (was sequential+120 ms stagger) and
  `init()` prefetches the current story's lines — demo cache is warm before
  the hook finishes. Kabeer display / Kabir voiceId split held everywhere;
  `grep Kabir` outside `<script>` = 0.
- node --check clean. FULL e2e 25/26 (only pre-existing pipeline fixture/key
  fail). D3a amber callout verified rendering on 02652674ecda.

## OPEN: ?story=demo ≤15 s gate — missed at 16–17.5 s, with measured proof
Harness-measured wall: 16.1–17.7 s across 4 runs (in-page marks, no polling
slack). Root cause, measured not assumed: Inworld CREATIVE synthesis bakes
~40–49% dead air per beat (silencedetect per-line: 1.3–1.9 s of pauses) and
is NONDETERMINISTIC across identical calls (same text → different bytes,
±8% size swing), so no fixed copy length can guarantee the gate. mp3 Σ alone
is 14.2 s for 123 chars; +gaps/start ≈ 16+. Already applied: copy trimmed
228→123 chars, DEMO_PACE delivery instruction (~0.4 s/line saved), 150 ms
gaps, concurrent+early prefetch, 1.15x playbackRate (helps real browsers;
headless null-sink clock ignores it — verified in-page).
Deliberately NOT done: gutting beats to slogans, 3-beat cut, or Web-Audio
silence surgery (~50 lines in shared audio path). Watcher options: (a) waive
gate to ≤18 s (passes every run as-is); (b) approve 3-beat demo (drop foot
glide → ~12.5 s); (c) authorize silence-surgery (~11 s, biggest change).

## CLOSED: 18 s waiver accepted (2026-09-20, user call)
Bound set to ≤18 s, all four beats kept. Button now reads "Play Kabeer's
walkthrough (18 s)" on ?story=demo only. Final verify GREEN: 4 demo steps,
rotation arms→hips→knees, foot amber callout, Kabeer-only user-visible copy,
node clean, demo wall 17.4 s ≤ 18 s, e2e E2E GREEN. Voice-coach standing down —
no further changes. D3b marker pulse remains with studio-3d.

## SCRIPT-REBUILD closed (2026-09-20, user-ordered + Kabeer spelling)
- Intro is name+title up front ("I am Kabeer, your running coach — …") in both
  demo hooks and default coachIntro; no counts anywhere ("three things" gone).
- HARD 15 s cap enforced in generator: estSecs model + greedy worst-first
  beats + per-beat char budget so even the mandatory insight fits; unclear
  zones skipped silently (no glide-to-unclear, no hedge lines).
- Dynamic per image: seedFromAnalysis drives hook/lead/CTA variants; beats use
  finding tldr/action data, fixed arms/foot templates deleted. 3 photos →
  3 different scripts (node + live proof), deterministic per photo.
- Repetition audit: ninety-degree echo removed from showcase arms clue
  (ZONE_KB keeps the factual reference); tour no longer repeats fixed lines.
- Spelling: coach is exactly Kabeer (display) + Kabir (voiceId); zero Darmani
  anywhere (§8d0 guard excludes its own test text).
- Proof: site/demo_script_test.js 25/25 GREEN; live 3-photo distinct + est≤15
  GREEN; e2e E2E GREEN. Standing down.

## DEFAULT-TOUR-FIX closed (2026-09-20, proven on fresh 419d46c0abbf front/swing)
- Default tour now runs the shared capped generator (buildCappedStory):
  est ≤15 s hard, worst-first greedy beats, footstrike pin, silent skip.
- Suitability guard (zoneSuitable, from step1 matrix): hips needs contact +
  non-swing + non-side/oblique (no pelvic language without contact); scored
  feet needs contact; legacy missing fields stay permissive.
- Footstrike always spoken: scored callout when suitable, else fixed short
  retake ask ("The foot needs a side view — send one.").
- coachIntro is name+title ("I am Kabeer, coach — [lead] first."); removed
  superseded storyFocus/coachFocusLine/coachOutroFree (mine, D2 era).
- Proof: node contract 56/56; live 419d+demo+0265 default+demo all distinct,
  capped, foot present; 419d has zero pelvic/braking language; live default
  wall 12.8 s; e2e E2E GREEN. Standing down.

## SCRIPT-TUNE closed (2026-09-20, brief: aeb979a86e8b side/stance/79)
- Prosody intro: em-dash → period ("I am Kabeer, coach. …") in coachIntro +
  all DEMO_HOOKS; Kabeer display / Kabir voiceId / zero Darmani held.
- Whole-thought beats: clause() takes full sentences (commas do NOT split —
  caught live: "Land with a soft, receptive knee" was cut to "Land with a
  soft"); shortest whole clause wins; nothing sliced mid-word. Greedy capped
  at hook+≤2+close; CTA iff it fits.
- Stale "20-30s hook" comment removed.
- aeb979a86e8b before → after (demo branch):
  BEFORE: "Your stride is braking — here's where." / fixed arms copy or
    generic filler / mislabeled second-zone glide / "All trainable, tap…"
  AFTER: "I am Kabeer, coach. 79 today, here's the work." /
    "Foot strike: Aim to place the foot down beneath your center of mass." /
    "Fix one thing, then re-test." (foot scored 74 → spoken callout ✓)
- Proof: contract 82→78 checks GREEN (count varies with beats picked);
  default rotation live (knees, trunk_lean, arms_elbows); e2e E2E GREEN.
  No paid TTS calls used (structure-only page evals + est model). Standing down.

## REBUILD-18 closed (2026-09-20, canonical: intro verbatim, foot→hip→third→CTA, 18 s)
- Spoken intro is exactly "Hi, I am the running coach. Let us deep dive into
  the model. Here is what your running form is hiding." (no name spoken;
  Kabeer on display chip/labels only, Kabir voiceId, zero Darmani).
- Fixed order foot→hip→third→CTA: foot overstride-aware ("way ahead of your
  body" / "a touch ahead" variants, retake ask when unclear), hip only when
  suitable (skipped silently), third = next suitable, CTA pinned when it fits.
  Cap 15→18 (DEMO_BUDGET_S). Rotation/startTour-bookkeeping/tourCount/
  coachIntro/capLead/seed/HOOKS/LEADS/CTAS removed as superseded orphans.
- Sync: every focus beat carries zone+view; gotoStep runs select+fly+detail
  pop before speak. Live: selection+rail track beats (SYNC GREEN), full play
  wall 17.9 s ≤ 18 s. aeb9 full beat text (default branch):
  1. "Hi, I am the running coach. Let us deep dive into the model. Here is
     what your running form is hiding."
  2. "First, your foot lands a touch ahead of your body, place it under you."
  3. "Third: Trunk is slightly too upright." (hips skipped: side view)
  (CTA dropped by cap math on this photo; trunk narrated, nothing hedged.)
- Proof: contract GREEN (intro/order/cap/verbatim/skip/determinism/distinct),
  3-photo distinct, e2e E2E GREEN. Standing down.
