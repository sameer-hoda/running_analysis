# Demo Direction — Studio Report 02652674ecda (score 72)

Status: PROPOSAL ONLY. No code edited. voice-coach + studio-3d implement after watcher approval.
Source studied live: `http://127.0.0.1:8140/report/02652674ecda` + `/api/jobs/02652674ecda/analysis` + `site/report_template.html`.

## Ground truth (verified, not assumed)

- Score 72, "Fair — trainable flaws", front view, stance, 6 zones scored: arms 65, hips 70, knees 72, shoulders 74, head 75, trunk 78.
- "Foot Strike & Overstride" card EXISTS as an `insufficient` entry ("Sagittal strike pattern … cannot be reliably measured from a frontal angle", needed_view: side-view at ground contact) but has **no visual callout**: grey "can't assess yet" pill, no `Contact:` strike/overstride line (that renders only for scored findings), quiet hollow marker, and it never gets a tour beat.
- 7 coach zone markers on the model (6 scored sprites + 1 hollow insufficient marker).
- Current non-showcase tour is 5 steps (overview + 3 worst zones + outro), each gated on full TTS + 850 ms gap — roughly 45–60 s, not demo-dense. Opener is "Alright, coach here! You scored 72…" — no hook in the first 2 s.
- `storyFocus()` always sorts findings ascending and takes 3 → identical order (arms → hips → knees) on every replay. Ordinals are fixed ("First up / Second / And third").
- Stale line: `ZONE_KB.hips_pelvis.coach` says "can't call this one from a side view" but fires for THIS front-view job too (hips scored 70). It reads as a miss on the demo page.

## 1. 10–15 s walkthrough script (≈35 words at ~150 wpm)

Hook lands inside the first 2 s (first 5 words). "Kabeer" is the USER spelling — see §4.

| Beat | Time | Line |
|---|---|---|
| HOOK | 0–2 s | "Your stride is braking — here's where." |
| Beat 1 (arms, 65) | 2–6 s | "I'm Kabeer. Worst first: that right arm saws across your chest — drive the elbows back." |
| Beat 2 (foot strike, visual callout) | 6–10 s | "And your foot? I can't score it from the front — send a side shot at ground contact." |
| CTA | 10–14 s | "Seventy-two, all trainable. Tap any glowing spot — spin it yourself." |

Why this order: worst-scored zone first (65 earns the hook's promise), the unscored foot-strike card second (turns the page's biggest hole into a retake CTA), CTA last while the model is back at hero.

## 2. Model turn/twist choreography (synced to beats, reuses existing machinery)

- HOOK (overview): `goView("hero")`, `SPIN_TOUR` fast spin already engaged during tour; no selection, no detail card.
- Beat 1 (arms): `selectZone("arms_elbows")` + `flyToZone("arms_elbows", 1.42)` + `showDetail` pop, exactly as `gotoStep` "focus" does today; camera settles front-three-quarter so crossover reads against the torso.
- Beat 2 (foot strike): NEW "glide" beat — `flyToZone("feet_strike", 1.55)` WITHOUT `selectZone` (turntable keeps spinning, same as teaser `kind:"glide"`), halo pulse on the hollow marker (see diff D3), caption carries the retake ask. No detail card — card stays one tap away.
- CTA (free): `hideDetail()`, clear selection, `goView("hero")`, `lastInteract=0` so auto-spin resumes immediately under the CTA line.

Total camera moves: hero → arm zone → foot glide-by → hero. Never parks mid-beat.

## 3. Anti-repetition rotation scheme

Problem: same 3 zones, same order, same ordinals, same CTA on every play.

- Rotate the lead slot per play: `lead = playCount % focus.length`, order beats `[lead, lead+1, lead+2]`; persist `playCount` + last-shown zones in `localStorage` (same pattern as `rf_coach_voice` / `rf_coach_vol`).
- Rotate ordinals and CTA from small arrays ("Worst first" / "First up" / "Opening with"; two CTA variants), indexed by `playCount`.
- Never lead twice in a row with the same zone; if a zone led last play, advance the lead index.
- Exact diff in D2 below (`storyFocus` + `coachFocusLine` + `coachOutroFree` variants). No new dependencies.

## 4. Kabeer spelling (USER spelling — product says "Kabir" in all these places)

Display name becomes "Kabeer" everywhere; the Inworld `voiceId: "Kabir"` is a real TTS voice — voice-coach must confirm whether "Kabeer" is a valid Inworld voiceId or whether we keep `voiceId "Kabir"` and only re-label the display. Default: display-only rename, voiceId untouched until voice-coach confirms.

Occurrences of "Kabir" to change (display): `site/report_template.html:252` ("Play Kabir's walkthrough"), `:259` coach chip `<b>Kabir</b>` + `alt="Coach Kabir"`, `:266` loading "Kabir is reviewing your run…", `:288` "Kabir · your running coach", `:679` `tag(label()==="Kabir"?"voice ready":…)` comparison; `site/tts_prewarm.py` docstring + user-facing strings (keep `VOICE_DEFAULT="Kabir"` if it is the voiceId); `site/assets/coach-kabir.jpg` filename/alt text (rename file or alt only — studio-3d call); `site/server.py:92,94` only if "Kabeer" proves to be a valid voiceId, else add a `VOICE_DISPLAY = {"Kabir": "Kabeer"}` map and use it in `/api/tts/status` (`:2105-2107`).

## 5. Exact diffs to implement (proposal — do not apply before watcher approval)

D1 — `coachIntro()` (`report_template.html:521`): replace opener with the hook + Kabeer intro:
`hook="Your stride is braking — here's where. I'm Kabeer — you scored "+score+" out of a hundred. ";` keep the "nail just three things" sentence, drop "Alright, coach here!".

D2 — rotation (`report_template.html:537-553`): `storyFocus()` takes `leadIdx` (from `localStorage rf_tour_count`) and returns rotated worst-3; `coachFocusLine(f,i,lead)` picks ordinals from `["Worst first","Next","And third"]` rotated by `playCount % 3`; `coachOutroFree()` alternates two CTA strings by parity.

D3 — foot-strike visual callout, two parts: (a) `detailHTML()` (`:805-812`): for `e.kind==="insufficient" && zone==="feet_strike"`, render an amber (not grey) callout strip — "No landing visible from the front — send a side shot at ground contact" + `needed_view` retake line, reusing `.sh-test` styling; (b) markers (`:1386-1392`): insufficient `feet_strike` marker gets the scored-marker pulse treatment (`base:0.05`, halo) in amber instead of the quiet hollow sprite, so the tour glide beat has something glowing to fly to.

D4 — demo cut in `buildStory()` (`:589-601`): new `?story=demo` branch returning the 4-step §1 script with kinds `[overview, focus(arms_elbows), glide(feet_strike), free]` and the §2 camera mapping; showcase/teaser/default paths untouched.

D5 — tour chrome labels: `tourPlay` span → "Play Kabeer's walkthrough (14 s)"; coach chip/loading/strip per §4.

Taste filter (SHOWCASE_BRIEF.md): lime-on-dark stays; no purple/blue gradients, no gradient headline text, no AI-slop tells — callout strip uses existing amber `#e6a63a` + panel styles only.

Suggested verify after implement: reload report, `?story=demo` runs ≤15 s by wall clock, hook audible first, foot marker pulses amber, three consecutive plays lead with three different zones, `grep -ri kabir site/` shows only voiceId + compat map.
