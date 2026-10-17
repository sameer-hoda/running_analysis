#!/bin/zsh
# RUNFORM v3 — Herder launcher: 7 YOLO panes visible like interactive teacher pav-bhaji
# Usage:
#   ./launch_herdr.sh              # starts herdr session running_gait, shows instructions
#   Inside herdr, run: ./herdr_setup_inner.sh   # spawns 7 agents
#
# Or one-shot inside herdr:
#   HERDR_ENV=1 ./herdr_setup_inner.sh
#
# Prereqs: herdr binary in PATH (~/.local/bin/herdr), opencode ~1.18.30+, server on 8138
V3="/Users/sameerhoda/Projects/running_analysis/v3"
SESS="running_gait"
MODEL="opencode/muse-spark-1.3-contributor-free"
VARIANT="high"
HERDR_BIN="${HOME}/.local/bin/herdr"

if [[ ! -x "$HERDR_BIN" && -x "$(which herdr 2>/dev/null)" ]]; then
  HERDR_BIN="herdr"
fi

echo "=== RunForm v3 Herder setup ==="
echo "Project: $V3 (closed to project folder, CWD locked)"
echo "Model: $MODEL --variant $VARIANT --auto (YOLO Zen high)"
echo "Herder bin: $HERDR_BIN"
echo ""

cd "$V3"
mkdir -p .agents/handoffs .opencode/agents

# Ensure opencode integration installed for herdr agent detection
echo "Checking herdr opencode integration..."
$HERDR_BIN integration status 2>&1 | grep -q opencode || {
  echo "Installing herdr opencode integration..."
  $HERDR_BIN integration install opencode
}

# Ensure server
if ! curl -s http://127.0.0.1:8138/ -o /dev/null -w "%{http_code}" 2>/dev/null | grep -q 200; then
  echo "Starting server :8138..."
  pkill -f "site/server.py 8138" 2>/dev/null; sleep 1
  ./.venv/bin/python site/server.py 8138 > /tmp/runform.log 2>&1 &
  sleep 2
  curl -s http://127.0.0.1:8138/ -o /dev/null -w "%{http_code}" | xargs echo "landing code:"
fi

if [[ "${HERDR_ENV:-}" == "1" ]]; then
  echo "Detected HERDR_ENV=1 — you are INSIDE Herder already. Running inner setup directly..."
  exec ./herdr_setup_inner.sh
fi

echo ""
echo "Not inside Herder yet. Two ways to get 7 YOLO panes visible on terminal:"
echo ""
echo "Option A — Herder (recommended for interactive teacher view):"
echo "  1. $HERDR_BIN --session $SESS"
echo "     -> This opens Herder TUI. You'll see 1 pane."
echo "  2. Inside Herder, run:"
echo "     ./herdr_setup_inner.sh"
echo "     -> It will split into 7 panes, each starts opencode --auto -m $MODEL --agent <name> Zen high via config"
echo "  3. You see all 7 live like pav-bhaji teacher."
echo ""
echo "Option B — Tmux (simpler, always visible):"
echo "  ./launch_tmux.sh"
echo "  tmux attach -t $SESS"
echo "  -> 7 panes, each YOLO, visible on terminal."
echo ""
echo "Launching Herder now with session $SESS..."
echo "After it opens, press prefix+b (toggle sidebar) to see agents, then run ./herdr_setup_inner.sh"
sleep 2

# Launch herdr with session name, cwd locked to v3
$HERDR_BIN --session $SESS
