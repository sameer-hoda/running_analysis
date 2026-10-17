#!/bin/zsh
# RUNFORM v3 — 7 agents, 1 tmux session, 2 tabs, 1 pane each. YOLO + Zen high.
# Tab 0 frontend (4 panes 2x2): landing, loader, analysis-page, ui-polish
# Tab 1 backend+brain (3 panes even): backend, integrator, research
# Model: opencode/muse-spark-1.3-contributor-free, --auto YOLO, --variant high via opencode.json
# ECC baked: https://github.com/affaan-m/ecc cloned at /tmp/ecc, injected in every agent brief
V3="/Users/sameerhoda/Projects/running_analysis/v3"
SESS="running_gait"
MODEL="opencode/muse-spark-1.3-contributor-free"
VARIANT="high"

mkdir -p "$V3/.agents/handoffs" "$V3/.opencode/agents"
echo "=== RunForm v3 — closing repo to project folder: $V3 ==="
cd "$V3"
pwd

if [[ ! -d /tmp/ecc/skills ]]; then
  echo "Cloning ECC skill..."
  git clone --depth 1 https://github.com/affaan-m/ecc.git /tmp/ecc 2>&1 | tail -n 2
else
  echo "ECC present: /tmp/ecc/skills ($(ls /tmp/ecc/skills | wc -l | tr -d ' ') skills)"
fi

if ! curl -s http://127.0.0.1:8138/ -o /dev/null -w "%{http_code}" 2>/dev/null | grep -q 200; then
  echo "Starting server :8138..."
  pkill -f "site/server.py 8138" 2>/dev/null; sleep 1
  ./.venv/bin/python site/server.py 8138 > /tmp/runform.log 2>&1 &
  sleep 2
  curl -s http://127.0.0.1:8138/ -o /dev/null -w "%{http_code}" | xargs echo "landing:"
fi

tmux kill-session -t $SESS 2>/dev/null; sleep 0.5
# Tab 0 — frontend
tmux new-session -d -s $SESS -n frontend -c "$V3" -x 300 -y 90
tmux set-option -t $SESS pane-border-status top
tmux set-option -t $SESS pane-border-format "#{pane_index}: #{pane_title} - #{pane_current_command}"
tmux set-option -t $SESS status on

# 4 panes 2x2: split h, then v each side
tmux split-window -h -t $SESS:frontend.0 -c "$V3"
tmux split-window -v -t $SESS:frontend.0 -c "$V3"
tmux split-window -v -t $SESS:frontend.1 -c "$V3"
tmux select-layout -t $SESS:frontend tiled

# Tab 1 — backend (3 panes wide, easy to read)
tmux new-window -t $SESS -n backend -c "$V3"
tmux split-window -h -t $SESS:backend.0 -c "$V3"
tmux split-window -h -t $SESS:backend.1 -c "$V3"
tmux select-layout -t $SESS:backend even-horizontal

sleep 0.3

ROSTER="ROSTER delegate: 1 landing CSS 44-84, 2 loader JOB 105-167, 3 backend pipeline 183-275, 4 analysis-page template, 5 integrator routes e2e, 6 ui-polish tokens explorer, 7 research gait-science"
ECC="ECC plan-test-implement-review-verify-remember-improve research-first skills at /tmp/ecc/skills"

launch_one() {
  local target="$1" file="$2" agent="$3"
  local title="$agent - $MODEL YOLO zen-high ECC"
  local seed="Read .agents/00_SHARED_CONTEXT.md then .agents/${file}.md then .opencode/agents/${agent}.md. ${ROSTER}. ${ECC}. Model ${MODEL} variant ${VARIANT} auto YOLO. CWD ${V3}. Own only your files, use handoffs mailbox. Check inbox every 15min. Start brief now ADHD action first 5 steps max one next step."
  tmux select-pane -t "$target" -T "$title"
  tmux send-keys -t "$target" "clear; echo '$title'; cat .agents/${file}.md | head -n 12; echo '---'; echo '$ROSTER'; echo '$ECC'; echo 'Starting opencode YOLO high'; sleep 1; opencode --auto -m $MODEL --agent $agent" C-m
  sleep 6
  tmux send-keys -t "$target" -l "$seed"
  tmux send-keys -t "$target" C-m
}

# Frontend tab panes 0..3
launch_one "$SESS:frontend.0" "01-landing" "landing"
launch_one "$SESS:frontend.1" "02-loader" "loader"
launch_one "$SESS:frontend.2" "04-analysis-page" "analysis-page"
launch_one "$SESS:frontend.3" "06-ui-polish" "ui-polish"
# Backend tab panes 0..2
launch_one "$SESS:backend.0" "03-backend" "backend"
launch_one "$SESS:backend.1" "05-integrator" "integrator"
launch_one "$SESS:backend.2" "07-research" "research"

echo ""
echo "session $SESS ready — 2 tabs, 7 YOLO panes (1 pane per agent)"
echo "  tmux attach -t $SESS"
echo "  Tab frontend: landing | loader | analysis-page | ui-polish (2x2)"
echo "  Tab backend:  backend | integrator | research (3-across)"
echo "  Switch tabs: ctrl+b w  or  ctrl+b n/p  | move panes: ctrl+b arrows | zoom: ctrl+b z"
echo "  tmux select-window -t $SESS:frontend / backend"
echo "  Server: http://127.0.0.1:8138/  Demo: /report/demo  Log: /tmp/runform.log"
echo "  Handoffs: ls .agents/handoffs/   ECC: /tmp/ecc/skills"
echo "  Herder alt: ./launch_herdr.sh"
