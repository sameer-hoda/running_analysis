# V4 AGENTS ROSTER — 7 YOLO agents (`muse --yolo --model muse-spark-1.3-contributor`, reasoning high)

## 1. core-loop → pane w6:p2 (tab V4-core)
Landing intrigue: big bold promise up front; scroll → proof (3D video already there + voiceover) → nudge to try. Subtle reassurances: Privacy-first baked everywhere + science-backed backbone (never hearsay/LLM hallucination). Upload screen next. Files: `site/server.py` landing routes, `site/assets/*`, `docs/SEO.md`. First: get `python3 site/server.py 8140` landing green, then enhance promise/proof/nudge. Handoff to pipeline-auth on upload contract.

## 2. pipeline-auth → pane w6:p5 (tab V4-core)
Upload→loading page: show user image + AI workload centre right (validating runner image, isolating main donor, task list of backend workflow at high level). Research-paper rail: papers stream in, get evaluated — reinforce research-backed. Parallelise AI calls / optimised sequence + EDA. Login-while-waiting: Google login or own auth to save time. Files: `site/server.py` jobs API, `site/sandbox_loader.html`, `step1_prompt.txt`, `extract_pose.py`. First: document current serial pipeline, then parallel plan + guest→auth bridge. No real auth secrets in repo.

## 3. studio-3d → pane w6:p3 (tab V4-studio)
Studio: high-quality 3D model with clear problem markers (glowing orb/overlay per issue). ADD missing foot-strike (heel vs proper landing) scored + shown properly. Historical photos in analysis when present; else first-time mode; history navigation. Files: `site/report_template.html`, `renderer3d.js`, `site/premium_model.py`, `run_report.py`. First: audit markers + foot-strike gap, then overlay + foot-strike scoring.

## 4. voice-coach → pane w6:p6 (tab V4-studio)
Humanised clinic feel: 3D + voice-coach analysis with coach profile + credentials shown while review runs ("Dr X is reviewing…"), then land at studio. Voiceover + rendered video very high quality. Files: `site/report_template.html` TTS/tour, `site/make_showcase.py`, `site/assets/*`. First: audit TTS/coach gap (today only "Coach:" tag), then coach identity + voice/video quality pass.

## 5. growth-memory → pane w6:p4 (tab V4-growth-research)
Repeat + growth: per-user history, 15-analysis cap then `mailto:EMAIL_REMOVED` unlock, Instagram-ready share output + friend sharing, privacy-first + retention. Files: `site/server.py` share (`/s`, clicks.jsonl), `site/usage.py`, `docs/SEO.md`, `deploy/`. First: spec history/cap/paywall + IG export without breaking share, then implement behind flags.

## 6. research-catalog → pane w6:p7 (tab V4-growth-research)
Catalogue EVERY running-gait paper backing the product: title/authors/year/link/key finding/which analysis rule it backs + thumbnail image pulled from paper. Powers landing-page bottom section (SEO) + loading-page carousel ("papers being referred to right now"). Store in `research/papers/catalog.json` + `research/papers/thumbs/`. Site reads catalog (no hardcode). First: schema + first 10 papers with real thumbnails, wire landing bottom section.

## 7. research-deep → pane w6:p8 (tab V4-growth-research)
Deep extraction: for top papers, extract figures + nice content snippets → valuable website section (gait-science library). Each entry: summary, methods signal, figure image, citation, linked analysis rule. Same `research/papers/` store, separate `deep/` docs. Coordinates with research-catalog (no duplicate schema) + studio-3d/core-loop (which rule cites which paper). First: 3 deep entries end-to-end (figure + snippet + citation + rule link).
