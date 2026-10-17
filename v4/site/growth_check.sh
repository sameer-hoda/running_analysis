#!/bin/bash
# growth-memory checks: history, 15-cap + mailto paywall, IG share, share intact.
# Additive to e2e_check.sh (which stays the deploy gate). Starts its own server
# on an isolated port with RF_HISTORY_PATH in /tmp so the repo stays clean.
# Usage: ./site/growth_check.sh [port]   (default 8142)
set -u
PORT="${1:-8142}"
BASE="http://127.0.0.1:$PORT"
FAIL=0
pass(){ echo "ok - $1"; }
fail(){ echo "FAIL - $1"; FAIL=1; }

export RF_HISTORY_PATH="/tmp/growth_hist_$$.json"
export RF_MAX_ANALYSES=1
rm -f "$RF_HISTORY_PATH"

python3 site/server.py "$PORT" >/tmp/growth_srv_$$.log 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null; rm -f "$RF_HISTORY_PATH" /tmp/growth_srv_$$.log /tmp/growth_img_$$.jpg "$JAR"' EXIT
for _ in $(seq 1 50); do curl -s -o /dev/null "$BASE/healthz" && break; sleep 0.2; done

JAR=$(mktemp /tmp/growth_cookies.XXXX)
python3 -c "from PIL import Image; Image.new('RGB',(320,240),(90,140,60)).save('/tmp/growth_img_$$.jpg',quality=92)"
IMG="/tmp/growth_img_$$.jpg"

# 1. login + empty history
curl -s -c "$JAR" -o /dev/null -X POST "$BASE/login" -d "guest=1"
H=$(curl -s -b "$JAR" "$BASE/api/history")
echo "$H" | python3 -c "import sys,json; h=json.load(sys.stdin); assert h['used']==0 and h['cap']==1, h" \
  && pass "history empty used=0 cap=1" || fail "history empty ($H)"
echo "$H" | grep -q "mailto:EMAIL_REMOVED" && pass "history unlock mailto" || fail "history unlock mailto"

# 2. /history page 200, no-login 401 on API
code=$(curl -s -b "$JAR" -o /dev/null -w "%{http_code}" "$BASE/history")
[ "$code" = "200" ] && pass "history page 200" || fail "history page (got $code)"
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/history")
[ "$code" = "401" ] && pass "history API 401 anon" || fail "history API anon (got $code)"

# 3. first upload counts (cap=1), second is refused with mailto paywall
R1=$(curl -s -b "$JAR" -X POST "$BASE/api/jobs" -F "photo=@$IMG" -H "Accept: application/json")
JID=$(echo "$R1" | python3 -c "import sys,json; print(json.load(sys.stdin).get('job_id',''))" 2>/dev/null)
[[ "$JID" =~ ^[a-zA-Z0-9_-]{1,12}$ ]] && pass "upload #1 -> $JID" || { fail "upload #1 ($R1)"; JID=""; }
code=$(curl -s -b "$JAR" -o /tmp/growth_pay.json -w "%{http_code}" -X POST "$BASE/api/jobs" -F "photo=@$IMG" -H "Accept: application/json")
[ "$code" = "402" ] && grep -q "mailto:EMAIL_REMOVED" /tmp/growth_pay.json \
  && pass "cap 402 JSON + mailto" || fail "cap JSON (got $code)"
code=$(curl -s -b "$JAR" -o /tmp/growth_pay.html -w "%{http_code}" -X POST "$BASE/api/jobs" -F "photo=@$IMG" -H "Accept: text/html" --max-time 10)
[ "$code" = "402" ] && grep -q "mailto:EMAIL_REMOVED" /tmp/growth_pay.html \
  && pass "cap 402 HTML paywall + mailto" || fail "cap HTML (got $code)"

# 4. /s/ share intact: 302 to /report/<jid>, click logged, links shape intact
if [ -n "$JID" ]; then
  code=$(curl -s -b "$JAR" -o /dev/null -w "%{http_code}" "$BASE/s/$JID")
  [ "$code" = "303" ] && pass "share /s/ 303" || fail "share /s/ (got $code)"
  loc=$(curl -s -b "$JAR" -o /dev/null -w "%{redirect_url}" "$BASE/s/$JID")
  [[ "$loc" == *"/report/$JID" ]] && pass "share redirects to report" || fail "share target ($loc)"
  L=$(curl -s "$BASE/api/links/$JID")
  echo "$L" | python3 -c "import sys,json; l=json.load(sys.stdin); assert l['short']=='/s/$JID' and l['clicks']>=1 and 'last' in l, l" \
    && pass "links shape + clicks>=1" || fail "links shape ($L)"
fi

# 5. Reel export on demo: caption JSON + single 1080x1920 MP4 (cached 2nd hit)
S=$(curl -s "$BASE/api/share/demo")
echo "$S" | python3 -c "import sys,json; s=json.load(sys.stdin); assert s['short']=='/s/demo' and '/s/demo' in s['caption'] and '#runningform' in s['caption'], s" \
  && pass "IG caption JSON" || fail "IG caption ($S)"
code=$(curl -s -o /tmp/growth_reel.mp4 -w "%{http_code}" --max-time 180 "$BASE/reel/demo")
if [ "$code" = "200" ]; then
  INFO=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of default=nw=1 /tmp/growth_reel.mp4)
  echo "$INFO" | grep -q "width=1080" && echo "$INFO" | grep -q "height=1920" \
    && pass "reel MP4 1080x1920" || fail "reel size ($INFO)"
  AC=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=nw=1:nk=1 /tmp/growth_reel.mp4)
  [ "$AC" = "aac" ] && pass "reel audio aac" || fail "reel audio ($AC)"
else fail "reel compose (got $code)"; fi
t0=$(date +%s)
code=$(curl -s -o /tmp/growth_reel2.mp4 -w "%{http_code}" --max-time 60 "$BASE/reel/demo")
t1=$(date +%s)
[ "$code" = "200" ] && [ $((t1-t0)) -lt 20 ] && cmp -s /tmp/growth_reel.mp4 /tmp/growth_reel2.mp4 \
  && pass "reel cached 2nd hit ($((t1-t0))s, identical)" || fail "reel cache (got $code, $((t1-t0))s)"
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/reel/nope-not-real")
[ "$code" = "404" ] && pass "reel unknown 404" || fail "reel unknown (got $code)"
rm -f /tmp/growth_reel.mp4 /tmp/growth_reel2.mp4 /tmp/growth_pay.json /tmp/growth_pay.html

# 6. privacy delete: remove own job, history back to 0, demo undeletable
if [ -n "$JID" ]; then
  sleep 1  # let the failed-fast worker release the job dir
  code=$(curl -s -b "$JAR" -o /dev/null -w "%{http_code}" -X DELETE "$BASE/api/jobs/$JID")
  [ "$code" = "200" ] && pass "delete own job" || fail "delete own job (got $code)"
  U=$(curl -s -b "$JAR" "$BASE/api/history" | python3 -c "import sys,json; print(json.load(sys.stdin)['used'])")
  [ "$U" = "0" ] && pass "history used=0 after delete" || fail "history after delete (used=$U)"
fi
code=$(curl -s -b "$JAR" -o /dev/null -w "%{http_code}" -X DELETE "$BASE/api/jobs/demo")
[ "$code" = "404" ] && pass "demo undeletable" || fail "demo delete (got $code)"

# demo reel artifacts are composed by this gate — remove them so the
# committed fixture stays lean (live servers recompose on demand + cache).
rm -rf site/jobs/demo/reel.mp4 site/jobs/demo/reel.json site/jobs/demo/reel_work

[ "$FAIL" = "0" ] && echo "GROWTH GREEN" || echo "GROWTH RED"
exit $FAIL
