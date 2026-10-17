#!/bin/zsh
# INNER script — MUST be run inside Herder (HERDR_ENV=1)
# Creates 7 panes, each starts opencode agent YOLO high with full roster + delegation brief
# Usage inside herdr pane: ./herdr_setup_inner.sh
V3="/Users/sameerhoda/Projects/running_analysis/v3"
SESS="running_gait"
MODEL="opencode/muse-spark-1.3-contributor-free"
VARIANT="high"
HERDR_BIN="${HOME}/.local/bin/herdr"
[[ -x "$HERDR_BIN" ]] || HERDR_BIN="herdr"

if [[ "${HERDR_ENV:-}" != "1" ]]; then
  echo "ERROR: Not in Herder. Run this INSIDE herdr: herdr --session $SESS , then ./herdr_setup_inner.sh"
  exit 1
fi

cd "$V3"
echo "=== Inside Herder, setting up 7 YOLO panes ==="
echo "CWD: $PWD  Model: $MODEL $VARIANT  Session: $SESS"
echo "Current pane: $HERDR_PANE_ID  Workspace: $HERDR_WORKSPACE_ID  Tab: $HERDR_TAB_ID"
echo ""

# Verify herdr commands
$HERDR_BIN pane current --current 2>&1 | head -20

ROSTER="ROSTER delegate: 1 landing CSS 44-84, 2 loader JOB 105-167, 3 backend pipeline 183-275 prompt pose, 4 analysis-page template, 5 integrator routes e2e merges ONLY, 6 ui-polish tokens explorer via handoffs, 7 research gait-science advisory via handoffs to backend and analysis-page"

# List agents to create: file prefix -> opencode agent name -> pane title
typeset -A AGENT_MAP
AGENT_MAP=(
  "01-landing landing"
  "02-loader loader"
  "03-backend backend"
  "04-analysis-page analysis-page"
  "05-integrator integrator"
  "06-ui-polish ui-polish"
  "07-research research"
)

echo "Creating 6 extra panes (we already have 1)..."

# We start with current pane as research? Actually map 1st pane to integrator (primary)
# Strategy: keep current pane as integrator, split 6 more
# Split directions to keep visible: alternate right/down, keep no-focus

# Helper to split and return new pane id
# herdr pane split returns JSON with .result.pane.pane_id

PANE_IDS=()
CURRENT_PANE=$($HERDR_BIN pane current --current 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('result',{}).get('pane',{}).get('pane_id',''))" 2>/dev/null)
if [[ -z "$CURRENT_PANE" ]]; then
  CURRENT_PANE="$HERDR_PANE_ID"
fi
echo "Root pane: $CURRENT_PANE"
PANE_IDS+=("$CURRENT_PANE")

# Create 6 splits
for i in {1..6}; do
  # alternate direction
  if (( i % 2 == 1 )); then
    DIR="right"
  else
    DIR="down"
  fi
  echo "Splitting $DIR -> pane $i..."
  OUT=$($HERDR_BIN pane split --current --direction $DIR --cwd "$V3" --no-focus 2>&1)
  NEW_ID=$(echo "$OUT" | python3 -c "import json,sys; 
try:
 d=json.load(sys.stdin)
 print(d['result']['pane']['pane_id'])
except Exception as e:
 print('', file=sys.stderr)
" 2>/dev/null)
  if [[ -z "$NEW_ID" ]]; then
    echo "Split output: $OUT" | head -20
    # fallback try pane list latest
    NEW_ID=$($HERDR_BIN pane list --workspace "$HERDR_WORKSPACE_ID" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); panes=d['result']['panes']; print(panes[-1]['pane_id'] if panes else '')")
  fi
  if [[ -n "$NEW_ID" ]]; then
    PANE_IDS+=("$NEW_ID")
    echo "  -> new pane $NEW_ID"
  else
    echo "  -> failed to parse new pane id, continuing"
  fi
  sleep 0.5
done

echo ""
echo "Pane IDs: ${PANE_IDS[@]}"
echo "Tiling layout..."

# Try to list tabs to confirm
$HERDR_BIN tab list --workspace "$HERDR_WORKSPACE_ID" 2>&1 | python3 -m json.tool 2>&1 | head -60

# Now start opencode agents in each pane
# Mapping order: 0:integrator (primary), 1:landing, 2:loader, 3:backend, 4:analysis-page, 5:ui-polish, 6:research
AGENT_ORDER=("integrator" "landing" "loader" "backend" "analysis-page" "ui-polish" "research")
FILE_ORDER=("05-integrator" "01-landing" "02-loader" "03-backend" "04-analysis-page" "06-ui-polish" "07-research")

echo ""
echo "Starting opencode agents YOLO high in each pane..."
for idx in {0..6}; do
  PANE_ID="${PANE_IDS[$((idx+1))]:-}" # zsh arrays 1-indexed, so adjust
  # Because zsh indexing weird, handle via iteration over PANE_IDS list
done

# zsh re-iterate correctly
i=0
for PANE_ID in "${PANE_IDS[@]}"; do
  if (( i >= 7 )); then break; fi
  AGENT_NAME="${AGENT_ORDER[$i]}"
  FILE_NAME="${FILE_ORDER[$i]}"
  echo "--- Pane $PANE_ID -> agent $AGENT_NAME (file $FILE_NAME) ---"

  # Build seed prompt - avoid special chars that break shell before opencode prompt
  SEED="Read .agents/00_SHARED_CONTEXT.md then .agents/${FILE_NAME}.md then .opencode/agents/${AGENT_NAME}.md. ${ROSTER}. Model ${MODEL} variant ${VARIANT} auto YOLO Zen high. CWD ${V3}. Own only your files, use handoffs mailbox. Check inbox every 15min. Server 127.0.0.1:8138. Start brief now ADHD action first 5 steps."

  # herdr agent start syntax: herdr agent start <name> --kind opencode --pane <id> -- <opencode args>
  # For TUI, use --auto -m MODEL --agent NAME (no --variant flag, variant high via config zen)

  echo "Starting agent $AGENT_NAME in pane $PANE_ID..."
  $HERDR_BIN agent start "$AGENT_NAME" --kind opencode --pane "$PANE_ID" -- --auto -m "$MODEL" --agent "$AGENT_NAME" 2>&1 | head -20

  sleep 2

  # Now prompt the agent with seed
  echo "Prompting $AGENT_NAME..."
  $HERDR_BIN agent prompt "$AGENT_NAME" "$SEED" --wait --timeout 30000 2>&1 | head -30 || echo "prompt may be working... check agent read"

  i=$((i+1))
  sleep 1
done

echo ""
echo "=== 7 YOLO panes should now be active ==="
$HERDR_BIN agent list 2>&1 | python3 -m json.tool 2>&1 | head -100
$HERDR_BIN pane list --workspace "$HERDR_WORKSPACE_ID" 2>&1 | python3 -m json.tool 2>&1 | head -120

echo ""
echo "You should SEE 7 panes in Herder like interactive teacher pav-bhaji:"
echo "  - landing, loader, backend, analysis-page, integrator, ui-polish, research"
echo "  Each running: opencode --auto -m $MODEL --agent <name>  Zen high via config"
echo "  Each has full context + roster + handoff delegation."
echo ""
echo "Use Herder keys:"
echo "  prefix+h/j/k/l to move between panes"
echo "  prefix+z to zoom"
echo "  Agent panel shows idle/working/blocked"
echo ""
echo "Verify:"
echo "  curl http://127.0.0.1:8138/ and /report/demo"
echo "  ls .agents/handoffs/"
