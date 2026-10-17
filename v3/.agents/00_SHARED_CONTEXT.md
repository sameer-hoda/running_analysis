# RUNFORM v3 — shared context (read first, all agents)

Server live: http://127.0.0.1:8138/ (`./.venv/bin/python site/server.py 8138` from v3 root).
E2E: `/` landing → `/login` guest → `/upload` → POST `/api/jobs` → `/job/<id>` polls `/api/jobs/<id>` → `/report/<id>`. Demo: `/report/demo` (score 63).

Stack: `site/server.py` (stdlib http, all pages inline) + `site/report_template.html` (Three.js GLB report) + `step1_prompt.txt` (Gemini audit) + TripoSR CPU mesh + `output/beach_report.html` (Canvas 2D prototype, reference only).

Model for every agent: `opencode/muse-spark-1.3-contributor-free`, `--variant high`, `--auto` (YOLO). Cwd: `/Users/sameerhoda/Projects/running_analysis/v3`. Reply ADHD-style: action first, numbered steps ≤5, one next step, no fluff.

## ECC harness — baked into ALL agents (https://github.com/affaan-m/ecc)
Source cloned at `/tmp/ecc`. Every agent MUST follow this loop:
`plan -> test -> implement -> review -> verify -> remember -> improve`
- Plan before building, research-first (websearch/webfetch + `/tmp/ecc/skills` e.g. tdd-workflow, security-review, frontend, search-first).
- Verify with tests + curl, never assume. Review own work from fresh context.
- Security: sanitize inputs, PIL-verify uploads, no secrets, no invented DOIs/years.
- Memory: persist wins/learnings in `.agents/handoffs/` so other panes reuse them.
- Rules: consult `/tmp/ecc/rules/common` + language packs as needed.

## Roster (delegate, don't duplicate)
1. landing — owns LANDING+CSS in `site/server.py:44-84`
2. loader — owns JOB_PAGE in `site/server.py:105-167`
3. backend — owns pipeline `site/server.py:183-275`, `step1_prompt.txt`, `extract_pose.py`
4. analysis-page — owns `site/report_template.html`
5. integrator — owns routes/wiring/e2e tests, merges conflicts in `site/server.py`
6. ui-polish — owns design tokens/shared CSS, options explorer used by 1+2+4
7. research — owns gait-science content/copy, advises 3+4, edits `step1_prompt.txt` only via backend

## Handoff protocol
- Mailbox: `.agents/handoffs/<to>-<from>.md` (e.g. `analysis-page-from-research.md`). Check your inbox on start and every ~15 min.
- Never edit another agent's owned files directly. Propose patch in handoff, integrator merges.
- Server is running — restart it after edits: `pkill -f "site/server.py 8138"; ./.venv/bin/python site/server.py 8138 > /tmp/runform.log 2>&1 &`.
- Verify with curl, never assume: landing 200, demo 200, upload→done→report 200.
