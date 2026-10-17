# QUALITY BRIEF — narration quality + usefulness rating (user-ordered 2026-09-20)

## 1. Context
Report 961e6b5de398 (side/swing/no-contact, score 74) has RICH Gemini findings
— head turned toward spectator, shoulders twisting from posing, trunk too
upright missing ankle-lean — but the spoken script flattens it to "upload a
better image, eyes on the horizon." Zero take-home insight. The analysis is
fine; the narration layer destroys it. No 3D regen for this task, ever.

## 2. Mission (sandbox-only until watcher sign-off)
1. Build a sandbox script lab (new file, e.g. `site/script-lab.html`, unlinked):
   loads any job's analysis.json, renders candidate 15–18s scripts side by
   side (current vs rewritten), with est timing + beat list. Iterate THERE.
2. Rewrite rule: every beat must carry one SPECIFIC observed flaw + its fix
   (e.g. "head turned to the crowd — eyes back on the road"). Retake asks only
   when a zone is truly unscorable, max one per script, never the lead beat.
3. Rating mechanism (ships to main site after proof): per-report "Was this
   analysis useful? Yes / No (+ optional one-line note)" → POST /api/rate →
   stored with the job (usage ledger/clicks pattern) → a /ratings view for the
   watcher. Rating data steers your iteration (lowest-rated scripts first).
4. Merge to main code ONLY on watcher written approval after user hears a good one.

## 3. Success looks like
- 961e6b5de398's script names the head-turn, the posing-twist, the missing
  ankle-lean — a listener takes home 2+ specific fixes.
- Rating widget live on reports, first ratings recorded and viewable.

## 4. Keep in mind
- Kabeer display / Kabir voiceId / zero Darmani; 18s canonical opener family
  ("Hi, I am the running coach…") stays unless the rewrite proves better.
- Skip-unclear-silently + ordinal-recount rules stay.
- Taste filter for any visible copy. No paid Tripo/Gemini calls (read analyses
  from disk; TTS only for final proofs, minimal lines).
- Server rule: background tasks, keys + PYTHONPATH.

## 5. Prove it
- Kept tests: extend the narration contract (specificity assertion — beats must
  quote analysis observations, not generic retakes) + e2e green, $0 ledger.
- Handoff `quality-voice.md` with before/after scripts + ratings schema.

## 6. Done signal: CHANGED / PROOF / FLAGS / NEXT. Stand down after sign-off.
