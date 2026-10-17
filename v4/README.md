# V4 — RunForm final draft (working folder)

Core loop: landing → upload → analyse/diagnose/correct. Growth loop: Instagram-ready share.
Moments: intrigue → curiosity → truth (value) → repeat (history, 15-cap).

## Source of truth (best picks, already copied lean — 328K, no jobs bulk)
- `site/server.py` ← v3-tripo-cloud Tripo v3 API + usage ledger (port 8139 pattern; run V4 on 8140)
- `site/report_template.html` ← Triplo (5 cards, tour, TTS, share /s + clicks.jsonl)
- `site/sandbox_loader.html`, `step1_prompt.txt`, `extract_pose.py`, `run_report.py`, `renderer3d.js`
- `site/premium_model.py`, `site/usage.py`, `site/make_showcase.py`, `site/qa_bot.py`, `site/e2e_check.sh`
- `docs/` ← V3 status/README, T3SMALL, SEO, TODO-next
- Do NOT copy: `site/jobs/*` bulk, `.venv`, `*.pt`, `output/*` bulk, `teaser_*_review` bulk

## Rules for all agents
- CWD: `/Users/sameerhoda/Projects/running_analysis/v4`. Work ONLY here. Never edit v3 / v3-tripo-cloud.
- Theme: keep current lime-on-dark (`--lime:#c8f04a`, `--bg:#0a0c11`) + dots.js. Same optimisations continue.
- TDD + taste skills will arrive later — write testable code + `site/e2e_check.sh` green now so skills plug in clean.
- Paid unlock: `mailto:EMAIL_REMOVED`. Cap: 15 analyses/user, then paywall.
- Server (from v4 root, keys + trimesh — venv binary does NOT take on this
  macOS framework python, use PYTHONPATH instead):
  `set -a; . ../v3-tripo-cloud/.env; set +a; PYTHONPATH=/Users/sameerhoda/Projects/running_analysis/v4/.venv/lib/python3.14/site-packages python3 site/server.py 8140`
  binds 127.0.0.1. Pre-flight: `PYTHONPATH=.../site-packages python3 -c "import trimesh"`
  must print 5.1. Keep e2e green.
- Coordinate via `.agents/handoffs/<to>-<from>.md`. This tab-1 watcher relays.
