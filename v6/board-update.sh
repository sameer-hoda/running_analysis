#!/bin/bash
# mynextpr watchboard auto-updater. Runs from cron every 2 minutes.
# Polls Orca lane state and rewrites the dynamic board sections.
# Read-only w.r.t. lanes: never sends, acks, releases, or edits lane files.
ORCA=/usr/local/bin/orca
BOARD=/Users/sameerhoda/Projects/running_analysis/v6/watchboard.html
RUNS="run_54cf6cc1038c run_2b03790e9a7d run_e76233812978 run_d7d3006702e4 run_5ead2520b3ef run_b907a75d764c run_f60793710887 run_f06f811cef18 run_52011c5f699a run_a52a66911321 run_d0e51905ac77"
"$ORCA" orchestration worker-list --run run_a52a66911321 --json 2>/dev/null | python3 -c "import sys; sys.exit(0)" || exit 0
python3 - "$BOARD" "$RUNS" <<'EOF'
import json, subprocess, sys, datetime
board_path, runs = sys.argv[1], sys.argv[2].split()
ORCA = '/usr/local/bin/orca'

def q(*args):
    try:
        out = subprocess.run([ORCA] + list(args), capture_output=True, text=True, timeout=60).stdout
        return json.loads(out).get('result', {})
    except Exception:
        return {}

cards = {'doing': [], 'gate': [], 'done': []}
seen_lanes = set()
import re as _re
def lane_key(name):
    m = _re.match(r'(\d\d)-([a-z]+)', name or '')
    return m.group(1) + '-' + m.group(2) if m else (name or '?')[:24]
for run in runs:
    r = q('orchestration', 'worker-list', '--run', run, '--json')
    workers = r.get('workers', [])
    titles = {}
    t = q('orchestration', 'task-list', '--run', run, '--json')
    for task in t.get('tasks', []) or []:
        titles[task.get('id')] = task.get('display_name') or task.get('task_title') or task.get('id')
    for w in workers:
        p = w.get('projection', {}) or {}
        outcome = p.get('outcome', 'in_progress')
        live = (p.get('liveness') or {}).get('verdict', '?')
        name = titles.get(w.get('taskId'), w.get('dispatchId', '?')[:13])
        key = lane_key(name)
        if key in seen_lanes:
            continue
        seen_lanes.add(key)
        stage = (p.get('stage') or {}).get('detail', '')
        if outcome == 'succeeded' and live == 'exited':
            cards['done'].append((name, 'verified · terminal closed'))
        elif outcome == 'succeeded':
            cards['gate'].append((name, 'reported · live' + (' · ' + stage if stage else '')))
        elif outcome == 'failed':
            cards['gate'].append((name, 'FAILED needs attention'))
        elif live == 'live':
            cards['doing'].append((name, stage or 'working'))
        else:
            cards['doing'].append((name, 'state unknown'))

def card_html(name, sub, cls, st, stcls):
    safe = name.replace('&', '&amp;').replace('<', '&lt;')
    return '<div class="card %s"><h3>%s</h3><p>%s</p><p class="st %s">%s</p></div>' % (cls, safe, sub, stcls, st)

doing = ''.join(card_html(n, s, '', 'DOING', 'work') for n, s in cards['doing'][:12])
gate = ''.join(card_html(n, s, 'gate', 'GATE', 'gate') for n, s in cards['gate'][:12])
done = cards['done']
done_txt = ' · '.join(n for n, _ in done[-12:])
done_html = '<div class="card done"><h3>Settled lanes (%d)</h3><p>%s</p><p class="st ok">DONE</p></div>' % (len(done), done_txt or 'none yet')
gates_txt = '; '.join(n for n, _ in cards['gate']) or 'none open'

import re
html = open(board_path).read()
html = re.sub(r'<!-- COL-DOING -->.*?<!-- /COL-DOING -->',
              '<!-- COL-DOING -->\n      ' + doing + '\n      <!-- /COL-DOING -->', html, flags=re.S)
html = re.sub(r'<!-- COL-GATE -->.*?<!-- /COL-GATE -->',
              '<!-- COL-GATE -->\n      ' + gate + '\n      <!-- /COL-GATE -->', html, flags=re.S)
html = re.sub(r'<!-- COL-DONE -->.*?<!-- /COL-DONE -->',
              '<!-- COL-DONE -->\n      ' + done_html + '\n      <!-- /COL-DONE -->', html, flags=re.S)
html = re.sub(r'<!-- GATES -->.*?</div>',
              '<!-- GATES -->' + gates_txt + '.</div>', html, flags=re.S)
stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
html = re.sub(r'<!-- UPDATED -->.*?( · coordinator)?</div>',
              '<!-- UPDATED -->' + stamp + ' · auto</div>', html, flags=re.S)
open(board_path, 'w').write(html)
print('board updated', stamp, '| doing:', len(cards['doing']), '| gate:', len(cards['gate']), '| done:', len(cards['done']))
EOF
