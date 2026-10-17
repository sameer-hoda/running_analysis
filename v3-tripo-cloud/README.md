# RunForm v3 — Running Gait Analysis — 7-Agent Zen High Project

> Project root **closed to folder**: `/Users/sameerhoda/Projects/running_analysis/v3`
> All agents CWD-locked here, YOLO `--auto`, model `opencode/muse-spark-1.3-contributor-free --variant high`

Live stack: `site/server.py` stdlib http (port 8138) + `site/report_template.html` Three.js GLB + `step1_prompt.txt` Gemini audit + TripoSR CPU mesh.

**E2E:** `/` landing → `/login` guest → `/upload` → `POST /api/jobs` → `/job/<id>` polls `/api/jobs/<id>` → `/report/<id>` — Demo `/report/demo` (score 63)

---

## Agents — 7 Panes Visible Like Teacher Pav-Bhaji

| # | Agent | Owns | File |
|---|---|---|---|
| 01 | **landing** | Hero + CSS `site/server.py:44-84` | `.agents/01-landing.md` + `.opencode/agents/landing.md` |
| 02 | **loader** | Job processing screen `105-167` | `.agents/02-loader.md` + `.opencode/agents/loader.md` |
| 03 | **backend** | Pipeline `183-275`, prompt, pose | `.agents/03-backend.md` + `.opencode/agents/backend.md` |
| 04 | **analysis-page** | Report 3D `report_template.html` | `.agents/04-analysis-page.md` + `.opencode/agents/analysis-page.md` |
| 05 | **integrator** | Routes, merges, e2e `e2e_check.sh` | `.agents/05-integrator.md` + `.opencode/agents/integrator.md` (primary) |
| 06 | **ui-polish** | Tokens + options explorer (via handoffs) | `.agents/06-ui-polish.md` + `.opencode/agents/ui-polish.md` |
| 07 | **research** | Doctor-grade gait science (advisory) | `.agents/07-research.md` + `.opencode/agents/research.md` |

All know each other via `00_SHARED_CONTEXT.md`:

```
# RUNFORM v3 — shared context (read first, all agents)

Server live: http://127.0.0.1:8138/ (`./.venv/bin/python site/server.py 8138`)
Roster (delegate, don't duplicate)
1. landing — owns LANDING+CSS in site/server.py:44-84
2. loader — owns JOB_PAGE in site/server.py:105-167
3. backend — owns pipeline site/server.py:183-275, step1_prompt.txt, extract_pose.py
4. analysis-page — owns site/report_template.html
5. integrator — owns routes/wiring/e2e tests, merges conflicts
6. ui-polish — owns design tokens/shared CSS, options explorer
7. research — owns gait-science content, advises 3+4, edits prompt only via backend

Handoff: .agents/handoffs/<to>-<from>.md — check inbox on start + every ~15min
Never edit another agent's owned files. Propose patch in handoff, integrator merges.
Restart: pkill -f "site/server.py 8138"; ./.venv/bin/python site/server.py 8138 > /tmp/runform.log 2>&1 &
Verify curl: landing 200, demo 200, upload→done→report 200
```

Model for every agent: `opencode/muse-spark-1.3-contributor-free`, `--variant high`, `--auto` (YOLO Zen high).

---

## How to see YOLO panes on terminal (interactive teacher)

### Option A — Herder (Herdr) — you asked for 1 pane per agent visible ERHERE

Prereqs: `herdr` installed at `~/.local/bin/herdr`, opencode 1.18.30+, `herdr integration install opencode` done.

```bash
cd /Users/sameerhoda/Projects/running_analysis/v3

# 1. Launch herder session locked to project folder
./launch_herdr.sh
# -> opens herdr TUI with session running_gait, 1 pane initially

# Inside herdr (you are now HERDR_ENV=1), spawn 7 YOLO panes:
./herdr_setup_inner.sh
# -> Creates 6 more panes, runs:
#    herdr agent start landing --kind opencode --pane <id> -- --auto -m opencode/muse-spark-1.3-contributor-free --variant high --agent landing
#    ... for loader, backend, analysis-page, integrator, ui-polish, research
# -> Each pane auto-prompted with:
#    "Read .agents/00_SHARED_CONTEXT.md then .agents/<file>.md and .opencode/agents/<name>.md. Roster: ... Use handoffs..."
# -> You SEE all 7 live like pav-bhaji teacher.

# Herder keys:
#  prefix is ctrl+b (default)
#  prefix+h/j/k/l move between panes, prefix+z zoom, prefix+b toggle sidebar
#  Bottom/agent panel shows idle/working/blocked/done

# Check:
herdr agent list
herdr pane list
curl http://127.0.0.1:8138/ -o /dev/null -w "%{http_code}"
```

Herder already has workspace w6 identity_cwd = v3, so session restore keeps CWD.

### Option B — Tmux — simplest visible YOLO

```bash
cd /Users/sameerhoda/Projects/running_analysis/v3
./launch_tmux.sh
# -> kills old running_gait, creates 7 panes tiled, each:
#   opencode --auto -m opencode/muse-spark-1.3-contributor-free --variant high --agent <name>
#   + seed briefing

tmux attach -t running_gait
# -> you SEE all 7 agents typing live, ADHD-style steps ≤5
# detach: ctrl+b d
# kill: tmux kill-session -t running_gait
```

Pane border titles show `agent | model YOLO zen-high`.

### Manual single agent YOLO

```bash
cd /Users/sameerhoda/Projects/running_analysis/v3
opencode --auto -m opencode/muse-spark-1.3-contributor-free --variant high --agent landing
# then inside opencode prompt:
# Read .agents/00_SHARED_CONTEXT.md then .agents/01-landing.md and start brief
```

---

## Project wiring check

```bash
cd /Users/sameerhoda/Projects/running_analysis/v3
./.venv/bin/python site/server.py 8138 > /tmp/runform.log 2>&1 &
sleep 2
curl -s http://127.0.0.1:8138/ -o /dev/null -w "%{http_code}" # 200
curl -s http://127.0.0.1:8138/report/demo -o /dev/null -w "%{http_code}" # 200
./site/e2e_check.sh
FULL=1 ./site/e2e_check.sh reference/input/images-3.jpeg # ~2min full pipeline

opencode agent list
ls .opencode/agents/ # 7 agents
ls .agents/handoffs/ # mailbox
```

---

## Deep research — brain perfect like doctor

Research agent (07) owns science, ships patches:

- Judgeability matrix enforced: side CAN head_neck, arms sagittal, trunk lean source, knee drive, feet ONLY if contact yes; CANNOT hips_pelvis drop, knee valgus, crossover → insufficient
- Front view mirror opposite, flight-phase guards: foot_contact=no → feet_strike insufficient, never claim overstride/braking in flight
- Scoring strict: optimal 85-100, fair 60-84, critical 0-59, recreational visible flaws MUST 55-75 never 90+, caps any critical ≤70, 2+ critical ≤60
- Evidence lines: 1-2 sentences consensus + author-only cites Lieberman, Cavanagh & Lafortune, no invented DOIs
- Exactly 7 entries across findings+insufficient, action = [cue1, cue2, drill] — drill library per zone documented in research agent file
- Sand/soft-surface caveat, dynamic meta line, evidence collapsible, status vocab fix critical vs poor

See `.agents/handoffs/backend-from-research.md` and `analysis-page-from-research.md` for applied patches.

---

## Closing repo to project folder

Project is **locked to**: `/Users/sameerhoda/Projects/running_analysis/v3`

- `opencode.json` sets CWD model + instructions
- `launch_tmux.sh` and `launch_herdr.sh` both `cd $V3` and `--cwd $V3` for every pane
- Herder workspace w6 identity_cwd = v3 (session.json)
- Agent briefs all start with "Read .agents/00_SHARED_CONTEXT.md then ..." so each agent has full project context + knows other agents to smartly delegate
- No external repo cloning needed — v3 *is* the repo. If you need git, `git init` inside v3 is safe, .env never committed (see e2e guard)

Sudha ki nahi, interactive teacher jaisa keep ho raha hai pav bhaji — you now SEE 7 YOLO panes live.
