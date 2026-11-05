#!/bin/bash
# mynextpr runner report — read-only status of the live site.
# No secrets in this file: pass them as env vars (host/key live in the
# private ops doc, never in the repo).
#
#   MY_NEXTPR_SSH_KEY=~/.ssh/mynextpr.pem MY_NEXTPR_SSH_HOST=ec2-user@1.2.3.4 \
#     bash deploy/runner-report.sh
#
# Prints: athlete count + per-runner setup (no tokens), recent stamp /
# webhook / connect activity from the server log, support inbox volume.
set -u
: "${MY_NEXTPR_SSH_KEY:?set MY_NEXTPR_SSH_KEY (path to EC2 key)}"
: "${MY_NEXTPR_SSH_HOST:?set MY_NEXTPR_SSH_HOST (e.g. ec2-user@HOST)}"
SSH="ssh -i $MY_NEXTPR_SSH_KEY -o ConnectTimeout=10 -o BatchMode=yes $MY_NEXTPR_SSH_HOST"

echo "=== mynextpr runner report: $(date '+%Y-%m-%d %H:%M %Z') ==="
$SSH "python3.11 -c \"
import json, glob, os, datetime
fs = sorted(glob.glob(os.path.expanduser('~/mynextpr-v6/v6/.athletes/*.json')))
print('registered runners:', len(fs))
today = datetime.date.today()
for f in fs:
    try:
        a = json.load(open(f))
    except Exception:
        print(' ', os.path.basename(f), 'UNREADABLE'); continue
    r = a.get('race', {}) or {}
    try:
        days = (datetime.date.fromisoformat(r.get('date')) - today).days if r.get('date') else '?'
    except ValueError:
        days = '?'
    stamped = a.get('stamped', {})
    print('  athlete', os.path.basename(f).replace('.json', ''),
          '| race:', (r.get('race') or '-'),
          '| in', str(days) + 'd',
          '| goal:', r.get('goal') or '-', '| dist:', r.get('dist') or '-',
          '| paused:', bool(a.get('paused')),
          '| token:', 'yes' if a.get('access_token') else 'NO',
          '| stamped:', len(stamped))
\""
echo "--- recent activity (server log) ---"
$SSH "grep -E 'STAMPED|stamp|webhook|exchange|connected|deleted|purge|revok' /tmp/mynextpr-v6.log 2>/dev/null | sed -E 's/code=[^& ]*/code=REDACTED/g' | tail -n 15; echo '(log lines above; empty = no recent activity)'"
echo "--- support inbox volume ---"
$SSH "wc -l ~/mynextpr-v6/v6/.support-inbox/inbox.jsonl 2>/dev/null || echo 'no inbox file'"
echo "--- site reachability ---"
curl -s -o /dev/null -w "home: %{http_code}\n" https://mynextpr.com/
curl -s -o /dev/null -w "api: %{http_code}\n" https://mynextpr.com/api/status
