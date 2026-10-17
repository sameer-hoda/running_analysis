# PROJECT STATUS — Running Gait Analysis — Herder + Tmux YOLO Zen High Live

**Date:** 2026-09-12
**CWD Locked:** `/Users/sameerhoda/Projects/running_analysis/v3` (repo closed to project folder)
**Model:** `opencode/muse-spark-1.3-contributor-free` — Zen high via `opencode.json` reasoningEffort high
**Mode:** `--auto` YOLO — every pane auto-approves non-denied permissions
**Server:** http://127.0.0.1:8138/ — `site/server.py 8138` — E2E GREEN

## Live Panes — You SHOULD SEE on Terminal

### Tmux (active now)
```bash
cd /Users/sameerhoda/Projects/running_analysis/v3
tmux attach -t running_gait
# 7 panes tiled:
# 0 landing - Landing auto · Muse Spark 1.3 Free OpenCode Zen · high
# 1 loader - Loader auto · ...
# 2 backend - Backend auto · ...
# 3 analysis-page - Analysis-page auto · ...
# 4 integrator - Integrator auto · ... (primary orchestrator, merging)
# 5 ui-polish - Ui-polish auto · ...
# 6 research - Research auto · ... (doctor-grade brain)

tmux ls
tmux list-panes -t running_gait
```

Current tmux running_gait (verified 2026-09-12 12:31):
- All 7 panes `opencode --auto -m opencode/muse-spark-1.3-contributor-free --agent <name>`
- Each pane title shows agent + YOLO zen-high
- Each agent auto-read `00_SHARED_CONTEXT.md` + own brief + `.opencode/agents/<name>.md`
- Roster known: landing, loader, backend, analysis-page, integrator, ui-polish, research
- Delegation via `.agents/handoffs/<to>-<from>.md` — mailbox checked on start + every 15min

### Herder (Herdr) — interactive teacher pav-bhaji view

Herder binary: `~/.local/bin/herdr` — integration `opencode` current v10

**To see Herder 7 panes visible on terminal:**

```bash
cd /Users/sameerhoda/Projects/running_analysis/v3
./launch_herdr.sh
# Opens herdr TUI session running_gait with 1 pane

# Inside herdr (HERDR_ENV=1), you are in a pane:
./herdr_setup_inner.sh
# -> splits into 7 panes (herdr pane split --current --direction right/down --cwd $PWD --no-focus)
# -> starts: herdr agent start <name> --kind opencode --pane <id> -- --auto -m opencode/muse-spark-1.3-contributor-free --agent <name>
# -> prompts each: herdr agent prompt <name> "Read .agents/00_SHARED_CONTEXT.md then ..."
# -> You SEE 7 panes live, sidebar shows idle/working/blocked

herdr agent list
herdr pane list --workspace <id>
```

Herder workspace already in `~/.config/herdr/session.json`:
- w6 identity_cwd = /Users/sameerhoda/Projects/running_analysis/v3
- So `herdr --session running_gait` restores CWD-locked project

## Agent Context — Full Project + Roster + Delegation

Each agent gets:

1. **Project context:** `opencode.json` with model, permissions, instructions CWD, server URL, e2e flow, handoff protocol, restart command
2. **Shared context:** `.agents/00_SHARED_CONTEXT.md` — server live, stack, roster, handoff protocol, verify curl
3. **Own brief:** `.agents/01-07-*.md` + `.opencode/agents/<name>.md` — scope owned files, inbox, done criteria
4. **Roster knowledge:** Every agent brief includes same roster string:
   `ROSTER delegate: 1 landing CSS 44-84, 2 loader JOB 105-167, 3 backend pipeline 183-275, 4 analysis-page template, 5 integrator routes e2e, 6 ui-polish tokens explorer, 7 research gait-science`
   So they can smartly delegate and assign — e.g., landing → ui-polish for tokens, research → backend for prompt patch, all → integrator for merges

5. **YOLO mode:** `--auto` flag — permission allow all except doom_loop/external_directory ask — see opencode.json

6. **Zen high mode:** Model `opencode/muse-spark-1.3-contributor-free` — UI shows `· high` — reasoningEffort high via provider config (built-in for free Zen) — validated in pane capture: `Landing auto · Muse Spark 1.3 Free OpenCode Zen · high`

## Files Created for Herder + Tmux Project

- `opencode.json` — model locked to project, YOLO perms, instructions
- `.opencode/agents/{landing,loader,backend,analysis-page,integrator,ui-polish,research}.md` — 7 agents mode all, model zen high, delegation roster
- `.agents/00_SHARED_CONTEXT.md` — existing, already has roster + handoff
- `.agents/01..07-*.md` — existing briefs
- `.agents/handoffs/` — 5 files already: backend-from-research, analysis-page-from-research, integrator-from-backend, integrator-from-landing, ui-polish-from-landing
- `launch_tmux.sh` — 7 panes tiled, YOLO, visible on terminal, sends seed briefing, now live as `running_gait`
- `.agents/launch_tmux.sh` — copy
- `launch_herdr.sh` — outer launcher, checks opencode integration, starts server, then `herdr --session running_gait`
- `herdr_setup_inner.sh` — inner, MUST be run inside herdr (HERDR_ENV=1), splits 6 panes, starts 7 opencode agents YOLO, prompts roster
- `README.md` — full usage
- `PROJECT_STATUS.md` — this file

## Verification — Curl + E2E GREEN

```
landing 200
demo 200
Analyze my run present
e2e: landing 200, login 200, upload guard 303, rf_guest cookie, upload 200, job id valid, job page 200, poll stage analyzing|meshing, demo report 200, demo mesh 200, unknown 404 → E2E GREEN
```

Server log: `/tmp/runform.log`
Jobs: `site/jobs/` 11 jobs including demo + stuck meshing (recoverable via backend queue)

## Deep Research — Doctor-Grade Brain Exhaustive

Research agent (07) already shipped:

- `backend-from-research.md` — judgeability matrix side vs front, flight-phase guards hard, scoring strict 55-75 recreational, caps critical ≤70, 2+ ≤60, evidence with Lieberman/Cavanagh&Lafortune author-only, sand caveat, 7 entries, action 2 cues + drill
- `analysis-page-from-research.md` — status vocab fix critical vs poor, zone titles, insufficient copy, evidence collapsible, meta dynamic, retake tip

Both patches ready for backend + analysis-page to apply, integrator to merge.

## Next Steps for User — Sudha ki nahi, pav bhaji live?

1. **See tmux now:**
   ```bash
   tmux attach -t running_gait
   ```
   You SEE 7 YOLO panes. Move with `ctrl+b` + arrow or `h/j/k/l`, zoom `ctrl+b z`, detach `ctrl+b d`

2. **Open Herder teacher view:**
   ```bash
   cd /Users/sameerhoda/Projects/running_analysis/v3
   ./launch_herdr.sh
   # Inside herdr pane:
   ./herdr_setup_inner.sh
   ```

3. **Watch agents delegate:**
   - Landing writes `integrator-from-landing.md` + `ui-polish-from-landing.md`
   - Research already wrote `backend-from-research.md`
   - Integrator reads all inboxes, merges patches in order 6→1→2→4→3, restarts server, runs `site/e2e_check.sh`

4. **Full pipeline test:**
   ```bash
   FULL=1 ./site/e2e_check.sh reference/input/images-3.jpeg
   # ~2min: Gemini audit + TripoSR mesh + report
   ```

All agents YOLO zen-high, CWD locked, roster aware, handoff delegation working — interactive teacher pav-bhaji is LIVE.
