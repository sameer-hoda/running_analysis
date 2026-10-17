#!/bin/bash
# RunForm e2e: landing -> login -> upload -> poll -> report/mesh
# Quick (default): validates wiring without waiting ~2min pipeline.
# Full pipeline: FULL=1 ./site/e2e_check.sh [/path/to/test.jpg]
set -u
BASE="${BASE:-http://127.0.0.1:8138}"
IMG="${1:-reference/input/images-3.jpeg}"
FULL="${FULL:-0}"
POLL_MAX="${POLL_MAX:-60}"   # quick: 60x2s; full: override e.g. POLL_MAX=450 FULL=1
FAIL=0
pass(){ echo "ok - $1"; }
fail(){ echo "FAIL - $1"; FAIL=1; }

[ -f "$IMG" ] || { echo "FAIL - test image missing: $IMG"; exit 1; }
[ -f "site/report_template.html" ] || { echo "FAIL - template missing: site/report_template.html"; exit 1; }

JAR=$(mktemp /tmp/runform_cookies.XXXX)
trap 'rm -f "$JAR"' EXIT

# 1. landing 200
code=$(curl -s -o /tmp/e2e_land.html -w "%{http_code}" "$BASE/")
[ "$code" = "200" ] && grep -q "stride" /tmp/e2e_land.html && pass "landing 200" || { fail "landing 200 (got $code)"; }

# 2. login page 200
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/login")
[ "$code" = "200" ] && pass "login 200" || { fail "login 200 (got $code)"; }

# 3. upload guard: no cookie -> 303 to /login
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/upload")
[ "$code" = "303" ] && pass "upload guard 303" || { fail "upload guard 303 (got $code)"; }

# 4. guest login sets cookie + upload 200 with cookie
code=$(curl -s -c "$JAR" -o /dev/null -w "%{http_code}" -X POST "$BASE/login" -d "guest=1")
grep -q "rf_guest" "$JAR" && pass "login sets rf_guest" || { fail "login sets rf_guest"; }
code=$(curl -s -b "$JAR" -o /tmp/e2e_up.html -w "%{http_code}" "$BASE/upload")
[ "$code" = "200" ] && pass "upload 200 (authed)" || { fail "upload 200 (got $code)"; }

# 5. POST upload -> job_id
RESP=$(curl -s -b "$JAR" -X POST "$BASE/api/jobs" -F "photo=@$IMG" -H "Accept: application/json")
JID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('job_id',''))" 2>/dev/null)
if [[ "$JID" =~ ^[a-zA-Z0-9_-]{1,40}$ ]]; then pass "upload -> job $JID"; else fail "upload -> job_id (got: $RESP)"; fi

# 6. job page 200
if [ -n "${JID:-}" ]; then
  code=$(curl -s -b "$JAR" -o /dev/null -w "%{http_code}" "$BASE/job/$JID")
  [ "$code" = "200" ] && pass "job page 200" || { fail "job page 200 (got $code)"; }
  # 7. poll api once: stage valid
  STAGE=$(curl -s -b "$JAR" "$BASE/api/jobs/$JID" | python3 -c "import sys,json; print(json.load(sys.stdin).get('stage',''))" 2>/dev/null)
  case "$STAGE" in queued|analyzing|meshing|done|failed) pass "poll stage=$STAGE";; *) fail "poll stage (got $STAGE)";; esac
fi

# 8. demo report 200 + score
code=$(curl -s -o /tmp/e2e_demo.html -w "%{http_code}" "$BASE/report/demo")
[ "$code" = "200" ] && grep -q "var ANALYSIS" /tmp/e2e_demo.html && pass "demo report 200" || { fail "demo report 200 (got $code)"; }
# 8b. studio features (Whoop ring, heat shell, insight sheet, zone rail)
for feat in "ringArc" "id=\"detailView\"" "buildHeat" "zonelist" "pickZone"; do
  grep -q "$feat" /tmp/e2e_demo.html && pass "studio feature: $feat" || fail "studio feature: $feat"
done

# 9. demo mesh 200
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/jobs/demo/mesh.glb")
[ "$code" = "200" ] && pass "demo mesh 200" || { fail "demo mesh 200 (got $code)"; }

# 10. unknown job 404
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/jobs/nope-not-real")
[ "$code" = "404" ] && pass "unknown job 404" || { fail "unknown job 404 (got $code)"; }

# 10b. landing thumbs resolve (examples route)
for ex in images-3.jpeg images-4.jpeg images-5.jpeg; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/examples/$ex")
  [ "$code" = "200" ] && pass "example $ex 200" || { fail "example $ex (got $code)"; }
done

# 11. full pipeline wait (FULL=1 only)
if [ "$FULL" = "1" ] && [ -n "${JID:-}" ]; then
  echo "waiting for job $JID (max ${POLL_MAX}x2s)..."
  for ((i=0;i<POLL_MAX;i++)); do
    STAGE=$(curl -s -b "$JAR" "$BASE/api/jobs/$JID" | python3 -c "import sys,json; print(json.load(sys.stdin).get('stage',''))" 2>/dev/null)
    [ "$STAGE" = "done" ] || [ "$STAGE" = "failed" ] && break
    sleep 2
  done
  [ "$STAGE" = "done" ] && pass "pipeline done" || { fail "pipeline done (stage=$STAGE)"; exit $FAIL; }
  code=$(curl -s -b "$JAR" -o /tmp/e2e_rep.html -w "%{http_code}" "$BASE/report/$JID")
  [ "$code" = "200" ] && grep -q "var ANALYSIS" /tmp/e2e_rep.html && pass "fresh report 200" || { fail "fresh report 200 (got $code)"; }
fi

[ "$FAIL" = "0" ] && echo "E2E GREEN" || echo "E2E RED"
exit $FAIL
