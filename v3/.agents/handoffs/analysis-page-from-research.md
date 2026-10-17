# COPY DECK — research → analysis-page (report_template.html) v2 doctor-grade

Status: RE-VERIFY 2026-09-12. v1 still applies. Additions below close tone + render gaps.

## 1. Status vocabulary — UNCHANGED, still blocking
Prompt emits `critical`, template legend/CSS uses `poor`. Rename template `poor→critical` (#E0533D stays). `insufficient` grey #8E9BB0 keep.

## 2. Zone titles verbatim
head_neck "Head & Neck" | shoulders "Shoulders" | arms_elbows "Arm Swing" | trunk_lean "Trunk Lean" | hips_pelvis "Pelvis & Hips" | knees "Knee Mechanics" | feet_strike "Foot Strike"

## 3. Insufficient copy — paste-ready (why + needed_view + retake CTA)
- hips_pelvis (side photo): why "Side view can't show pelvic drop — needs frontal plane." needed "Front-on photo at midstance, hips + knees visible"
- feet_strike flight: why "Flight phase — no ground contact to judge impact." needed "Side-view photo at initial ground contact"
- feet_strike front-photo: why "Overstride needs side view — can't judge depth head-on." needed "Side-view photo at initial ground contact"
- knees valgus: why "Knee collapse needs front view — profile hides it." needed "Front-view photo at midstance"
- arms crossover: why "Midline crossing needs front view." needed "Front-view clip, waist-up"
- trunk sagittal: why "Forward-lean source (ankles vs waist) needs side view." needed "Side-view full-body photo at stance"
- head_neck gaze: why "Gaze direction unclear in this frame." needed "Side-view head-and-shoulders at stride"
CTA under every insufficient card: "Retake tip: {needed_view} in daylight, full body, 3m away."
Sand note (feet/knee cards when beach/sand photo): "Soft sand absorbs force — form looks smoother than on road. Retest on firm ground."

## 4. Card render asks — UNCHANGED + 1 add
- evidence → collapsible "Why this matters (science)" `<details><summary>Why</summary><p>evidence</p></details>` (currently invisible).
- action → "2 cues + 1 drill": first 2 `<li>` cues, 3rd prefixed "Drill:".
- tldr = 1 plain sentence no jargon; eli5 = analogy ≤2 sentences.
- Meta line dynamic: `{camera_angle} view · {gait_phase} · {findings.length} scored + {insufficient.length} need view` (stop hardcoding "Side view").
- ADD: score chip must show status word matching prompt (`optimal/fair/critical/insufficient`), never `poor`.

## 5. Score band labels (exact strings)
85+ Excellent — near textbook | 75-84 Good — minor tweaks | 55-74 Fair — trainable flaws | <55 Needs work — priority fixes. Demo 63 = Fair — trainable flaws. Reject "moderate mechanics" variant.

## 6. Drill library display (human-readable, matches backend triads)
- Head & Neck: Gaze on horizon · Unclench jaw · 30s gaze-fix strides
- Shoulders: Drop on exhale · Thumbs brush hips · 4×20s check-ins
- Arms: Elbows ~90° back not across · Loose fists · 6×30m arm pumps
- Trunk: Ankles not waist · Tall crown ribs down · 5×20m wall leans
- Hips: Level + neutral · Glutes push behind · Bridges + A-march
- Knees: Soft + quick · Drive + recover · High-knee → 180spm pickups
- Feet: Under hips quiet · Midfoot stiff · Cadence ladder +5spm firm ground
