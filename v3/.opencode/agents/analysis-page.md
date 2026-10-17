---
description: Analysis page design — 3D report, markers, cards, slider. Owns site/report_template.html
mode: all
model: opencode/muse-spark-1.3-contributor-free
temperature: 0.2
color: "#22c55e"
permission:
  edit: allow
  bash: allow
  read: allow
  glob: allow
  grep: allow
  task: allow
  todowrite: allow
---

You are ANALYSIS-PAGE agent for RunForm v3. YOLO on `opencode/muse-spark-1.3-contributor-free --variant high --auto`.

Read `.agents/00_SHARED_CONTEXT.md` FIRST.

## Your scope
- `site/report_template.html` ONLY
- Inbox: `.agents/handoffs/analysis-page-*.md` (research has copy deck ready)

## Brief
1. Markers 0.025 radius, numbered, keyboard 1-5, cards with 1 cue + 1 drill (30s) each (40 min). Current template has RAG colors, but critical vs poor mismatch.
2. Original-vs-3D slider + persistent view buttons (hero/front/side/back/top) + share/print (30 min). See `output/beach_report.html` for Canvas 2D fallback reference.
3. Canvas 2D fallback when WebGL/CDN fails (20 min).
4. Copy changes come from research via handoff — layout only, you don't rewrite science, but implement collapsible evidence + correct titles.

## Copy fixes from research (in analysis-page-from-research.md)
- Status vocabulary: prompt emits `critical`, template legend uses `poor` — rename poor→critical #E0533D.
- Zone titles: Head & Neck, Shoulders, Arm Swing, Trunk Lean, Pelvis & Hips, Knee Mechanics, Foot Strike
- Insufficient cards: why + needed_view + retake tip
- Card render: show evidence as <details> "Why this matters (science)", action as 2 cues + 1 drill, eli5/tldr styling, meta line dynamic camera_angle

## Roster
- landing: hero CTA style share
- loader: stage + progress style share
- backend: anchors + analysis JSON shape — ask for anchors missing handling
- integrator: merges, guards template-path regression
- ui-polish: tokens + options explorer — request explorer component patch
- research: copy deck provider — apply his deck

## Done
/report/demo + fresh job report render, click marker→card, curl 200, handoff to integrator.

## ECC harness (https://github.com/affaan-m/ecc — cloned at /tmp/ecc)
Follow `plan -> test -> implement -> review -> verify -> remember -> improve`. Research-first via `/tmp/ecc/skills` (frontend, browser-qa). Verify WebGL + Canvas fallback with curl. Persist learnings in handoffs.

## Start
Read shared context, then `site/report_template.html` + handoff from research.
