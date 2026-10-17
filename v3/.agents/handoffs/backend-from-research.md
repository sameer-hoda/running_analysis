# PATCH PROPOSAL — research → backend (step1_prompt.txt) v2 doctor-grade

Status: RE-VERIFY 2026-09-12. Current prompt already contains v1 patch — good. Gaps below close the science checklist 100%.

## 1. Judgeability matrix — VERIFIED + 3 guards to add
Current matrix correct. ADD verbatim:
- Front-view feet guard: `front photo → feet_strike NEVER overstride/braking; insufficient (needed_view: side-view at initial contact). Pronation note ONLY if clearly visible, else omit.`
- Cadence/VO guard: `Never estimate cadence/spm or vertical oscillation from a single photo; mention relationship only in evidence (higher cadence + lower oscillation → lower loading rate), never as observation.`
- Loading-rate language: change `overstriding increases braking impulse` → `overstriding increases braking impulse and vertical loading rate`.

## 2. Per-zone rubrics (insert into STEP 2, enforces even balance)
- head_neck: optimal = gaze horizon, neutral cervical; fair = slight down/tilt; critical = marked poke/chin-down, gaze at feet.
- shoulders: optimal = level, dropped; fair = slight elevation/tension; critical = shrugged, visibly asymmetric hike.
- arms_elbows: optimal = ~90°, sagittal drive, loose hands; fair = opens slightly / minor cross; critical = stiff straight-arm, wide cross-midline, clenched high carry.
- trunk_lean: optimal = slight ankle-sourced lean, tall crown, ribs down; fair = bolt upright OR soft waist bend; critical = collapsed waist fold / excessive back-lean.
- hips_pelvis: optimal = level, neutral (front view only); fair = minor asymmetry; critical = clear drop/rotation. Side view → always insufficient.
- knees: optimal = soft stance knee / clean swing drive + recovery under butt (phase-appropriate); fair = stiff-ish landing OR low drive; critical = buckled/fully extended stab landing. Valgus/crossover only from front; side view → never claim valgus.
- feet_strike: optimal = lands under hips, quiet midfoot, stiff ankle (stance side view only); fair = mild reach / loud heel; critical = gross overstride, dorsiflexed reach, slap. Flight OR front → always insufficient.

## 3. Scoring — VERIFIED, 1 wording fix
Keep: optimal 85-100 / fair 60-84 / critical 0-59 / insufficient null; optimal<85 invalid; overall=round(mean scored); recreational visible-flaw band 55-75 never 90+; caps any-critical ≤70, 2+ ≤60; labels 85+ Excellent — near textbook / 75-84 Good — minor tweaks / 55-74 Fair — trainable flaws / <55 Needs work.
FIX: canonical label is `Fair — trainable flaws` (fresh JSON says "moderate mechanics" — reject; enforce exact strings).

## 4. Evidence (author-only, no DOIs/years/PMIDs)
- feet_strike evidence MUST cite both: e.g. `Landing ahead of the hips lengthens the braking phase and raises loading rate (Lieberman); rearfoot impact peak absent in forefoot patterns, strike index classifies contact (Cavanagh & Lafortune).`
- knees/cadence evidence: `A small cadence lift with lower vertical oscillation shortens stride and lowers loading rate and braking impulse — consensus, no photo-numbers.`
- All other zones: 1-2 sentences consensus, NO cite required, NO invented authors.

## 5. Imbalance list — fresh JSON bugs (backend: enforce via prompt, do NOT hand-fix JSON)
1. head_neck `optimal/68` — scale violation; optimal must be ≥85. Should be fair ~70. Fix = `optimal zone with score <85 invalid` rule (already in prompt — model disobeyed, strengthen with ALL-CAPS line).
2. `action` has 1 cue — must be exactly [cue1, cue2, drill] from drill library below. Reject otherwise.
3. `evidence` has zero author cites — feet/knee findings MUST carry Lieberman / Cavanagh & Lafortune by name.
4. `overall_label` "Fair — moderate mechanics" — non-canonical; enforce exact 4 label strings.
5. `action` shape in fresh JSON is malformed (`["cue"] , "evidence"` split) — schema example already correct; keep.
6. Sand caveat: old beach stance photo on sand needs `observation` compliance note, no inflated tibia-vertical credit.

## 6. Drill library — canonical verbatim (model picks exactly these triads)
- head_neck: "Gaze on horizon" / "Unclench jaw, tongue off roof" / "Drill: 30s gaze-fix strides"
- shoulders: "Drop shoulders from ears on exhale" / "Thumbs brush hips, no shrug" / "Drill: 4x20s shoulder-drop check-ins"
- arms_elbows: "Elbows ~90°, drive back not across" / "Loose fists, wrists unbent" / "Drill: 6x30m arm-only pumps"
- trunk_lean: "Lean from ankles, not waist" / "Tall through crown, ribs down" / "Drill: 5x20m fall-forward wall leans"
- hips_pelvis: "Hips level, pelvis neutral" / "Glutes push ground behind you" / "Drill: 2x10 single-leg glute bridges + 20m A-march"
- knees: "Soft knee on landing, quick turnover" / "Drive knee forward, heel recovers under butt" / "Drill: 4x20m high-knee march → cadence pickups 180spm"
- feet_strike: "Land under hips, quiet feet" / "Midfoot, ankle stiff not reaching" / "Drill: 6x30s cadence ladder +5spm firm ground"

## 7. Needed_view strings (reuse)
hips "front-on photo at midstance"; feet "side-view photo at initial ground contact"; knees-valgus "front-view midstance"; arms-crossover "front-view waist-up swing"; trunk-sagittal "side-view full-body stance".

## 8. Exact prompt diffs to apply
A) In STEP 2 guard line `Never invent numbers...` append: `Never estimate cadence/spm or vertical oscillation from a still; describe their relationship only in evidence. Overstride raises braking impulse AND vertical loading rate. Lean cues: tall through crown, ribs down.`
B) In STEP 3 add: `overall_label strings exact-match only. optimal with score <85 → INVALID, rescore as fair.`
C) In STEP 3 evidence line append: `feet_strike evidence must name Lieberman and Cavanagh & Lafortune; no DOIs/years/PMIDs ever.`
