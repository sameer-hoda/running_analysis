# quality → voice-coach/watcher (2026-09-20, QUALITY_BRIEF, sandbox until sign-off)

## 1. Before / after — 961e6b5de398 (side/swing/no-contact, score 74)

BEFORE (live `buildCappedStory`, est 14.86s):
1. "Hi, I am the running coach. Let us deep dive into the model. Here is what your running form is hiding."
2. "First, the foot needs a side view, send one." (retake as LEAD beat)
3. "Second, eyes on the horizon." (generic — names no flaw)

AFTER (lab rewrite `buildLabStory`, est 17.90s ≤ 18s):
1. same canonical intro (verbatim, kept)
2. "First, head is turned sideways toward the spectator — eyes on the horizon."
3. "Second, trunk posture is too upright — lean from the ankles not the waist."

Take-home: eyes on the horizon + ankle-lean (2 specific fixes). No retake
(didn't fit; correctly dropped, never lead). No 3D regen touched. No paid
calls ($0 ledger — rating/ratings_view lines all usd 0.0).

## 2. What shipped (sandbox + rating mechanism only; narration NOT merged)

- `site/script-lab.html` (new, unlinked): job loader via `GET /api/analysis/<jid>`,
  current snapshot vs rewritten `buildLabStory` side by side, est + budget bar +
  flaw/fix chips per beat, editable rewritten beats with live est/budget/quote
  badges, tunable budget/flaw/fix budgets, take-home list. Rewrite rule enforced
  in code: flaw (tldr → longest short sign → observation) + first non-drill fix,
  whole thoughts only (never sliced), worst-score first, praise zones (≥85 +
  good/optimal) skipped, retake ≤1 and only after a flaw beat.
- `site/server.py`: `POST /api/rate` (server.py:~2545), `GET /ratings`
  (login-gated, watcher view), `GET /api/analysis/<jid>` (lab data),
  `/script-lab.html` route; helpers `_ratings_*` (server.py:~235). All additive.
- `site/report_template.html`: rating widget after coach-strip
  ("Was this analysis useful? Yes/No + optional one-line note", one vote per
  browser per job via localStorage). Narration generator untouched.
- Ratings schema — `site/jobs/<jid>/ratings.jsonl`, one JSON line per vote:
  `{"ts": 1789911256.81, "useful": true, "note": "e2e probe"}` (note ≤140 chars,
  votes fail-soft). `POST /api/rate` returns `{"ok": true, "job", "yes", "no"}`.
  Seed: 2 probe votes on `demo` (note "e2e probe") so /ratings is viewable now.
- Tests: `site/script_lab_test.js` (61 checks: specificity quote per beat,
  retake ≤1 + never-lead incl. synthetic fits/orphan cases, ordinals, budget,
  determinism, 961e spectator+ankle+2-fix asserts) + `site/e2e_check.sh` §14
  (lab 200, widget markers, analysis api ±404, lab contract, rate ±404/400s,
  ratings 303→200, ledger $0). Existing `demo_script_test.js` still green.

## 3. Proof (own :8147 instance; live :8140 untouched, owner restarts to deploy)

- `node site/script_lab_test.js site/script-lab.html` 4 fixtures: 61/61 ok.
- `BASE=http://127.0.0.1:8147 bash site/e2e_check.sh`: E2E GREEN, zero FAIL
  (incl. pre-existing script contract + §14 rating block; ledger $0 line).

## 4. Iteration findings (take-home insight obsessions, honestly)

- Budget math is the whole game: canonical intro costs 6.28s of 18s, so at most
  TWO flaw+fix beats fit. The posing-twist (shoulders, score 78) is the budget
  casualty on 961e — visible in the lab as the dropped third candidate. Naming
  all three needs a shorter opener ("stays unless the rewrite proves better"):
  watcher call, editable beats in the lab prove any candidate instantly.
- Real bug found by the new contract: retake push never advanced the budget
  total, so CTA over-admitted (synth script hit 21.17s). Fixed in lab
  (script-lab.html `buildLabStory` retake branch); live builder never had it
  (its push path always accounts).
- aeb9 yields intro + 1 long beat (13.35s, CTA misses by 0.2s): worst-first
  greedy takes the long trunk beat and blocks two shorter ones. Tightening the
  fix in the lab ("lean from the ankles") recovers a 2-beat 17.66s script —
  this is the intended lab workflow, not a generator defect worth complicating.
- 419d trunk ("stability is well controlled — brace core gently") is a
  praise-textured fair zone: quotable but weak. If these top /ratings "not
  useful", teach the builder a flaw-lexicon next round.

## 5. FLAGS / UNRESOLVED

- Live :8140 (PID 86532, another owner) was NOT restarted: widget + routes go
  live on the owner's next restart. Verified identical code on :8147.
- TTS proof deferred: no voice lines synthesized (brief allows minimal final
  proofs; none needed — text+est is the deliverable until the user listens).
- `site/jobs/demo/ratings.jsonl` holds 2 labeled probe votes — keep as seed,
  real watcher/user votes accumulate alongside.

## 6. NEXT (stand down after this)

Watcher: open `/script-lab.html` on :8140 (after restart), load 961e, hear the
AFTER script (minimal TTS), cast the first real votes. On written approval,
merge `buildLabStory` → `report_template.html` `buildCappedStory`, extend
`demo_script_test.js` with the specificity asserts, and work /ratings bottom-up.
