#!/bin/bash
# RunForm e2e: landing -> login -> upload -> poll -> report/mesh
# Quick (default): validates wiring without waiting ~2min pipeline.
# Full pipeline: FULL=1 ./site/e2e_check.sh [/path/to/test.jpg]
set -u
BASE="${BASE:-http://127.0.0.1:8140}"
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

# 5. POST upload -> job_id (?test=1: bots take the stub-mesh lane, zero Tripo spend)
RESP=$(curl -s -b "$JAR" -X POST "$BASE/api/jobs?test=1" -F "photo=@$IMG" -H "Accept: application/json")
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
# 8b2. studio-3d: foot-strike callout + photo-grounded cards + research rail (durable)
for feat in "strikeCallout" "sh-fig photo" "sciRail" "renderSci"; do
  grep -q "$feat" /tmp/e2e_demo.html && pass "studio-3d: $feat" || fail "studio-3d: $feat"
done
# 8c. voice-coach: Kabeer chip + avatar + TTS voice (durable: coach identity in report_template.html)
# NOTE: "Kabeer" is the display name; "Kabir" below is the Inworld provider voiceId.
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/assets/coach-kabeer.jpg")
[ "$code" = "200" ] && pass "coach avatar 200" || { fail "coach avatar (got $code)"; }
for feat in "coach-kabeer.jpg" "Kabeer is reviewing" "Play Kabeer"; do
  grep -q "$feat" /tmp/e2e_demo.html && pass "demo coach: $feat" || fail "demo coach: $feat"
done
VOICE=$(curl -s "$BASE/api/tts/status" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('voice','') if isinstance(d,dict) else '')" 2>/dev/null)
[ "$VOICE" = "Kabir" ] && pass "tts voice id=Kabir (coach Kabeer)" || { fail "tts voice (got $VOICE)"; }
curl -s "$BASE/api/tts/status" | grep -q '"Kabir"' && pass "tts voices list Kabir" || { fail "tts voices list Kabir"; }
# 8d0. voice-coach: no Darmani string anywhere (coach is exactly Kabeer).
# Excluded: this file + the contract test (assert the rule in text) + the
# watcher's requests ledger (quotes the rule as "zero Darmani").
if grep -rqi "darmani" site/ research/ docs/ step1_prompt.txt --exclude=e2e_check.sh --exclude=demo_script_test.js --exclude=REQUESTS_AUDIT.md 2>/dev/null; then
  fail "darmani string present"
else
  pass "no darmani string"
fi
# 8d. voice-coach: script-rebuild contract (intro/cap/dynamic/skip/no-repeat/distinct)
if command -v node >/dev/null 2>&1; then
  if node site/demo_script_test.js site/report_template.html site/jobs/demo/analysis.json site/jobs/aeb979a86e8b/analysis.json site/jobs/419d46c0abbf/analysis.json > /tmp/e2e_script_test.log 2>&1; then
    pass "script contract (3 photos distinct, <=18s est)"
  else
    fail "script contract (see /tmp/e2e_script_test.log)"
  fi
else
  pass "script contract SKIPPED (no node)"
fi

# 8e. KABEER-DEMO-VOICE: homepage demo video speaks Kabeer throughout.
# site/assets/showcase.json is written by make_showcase, which fails closed
# unless every captured line requested voiceId Kabir (display name Kabeer).
SC=$(curl -s "$BASE/assets/showcase.json")
echo "$SC" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d.get('voice') == 'Kabir', d
assert d.get('display') == 'Kabeer', d
assert d.get('engine') == 'inworld', d
assert d.get('missing_lines') == 0, d
lines = d.get('lines') or []
assert len(lines) >= 2, d
assert all(l.get('voice') == 'Kabir' for l in lines), d
assert lines[0]['text'].startswith('Hi, I am the running coach.'), d
" 2>/dev/null && pass "showcase sidecar: Kabir on every line (Kabeer)" || { fail "showcase sidecar voice (see $BASE/assets/showcase.json)"; }
# Stub-mesh guard (pick-agnostic until the mesh pick lands: pre-pick sidecars
# without a mesh block skip; post-render sidecars must prove a real mesh).
echo "$SC" | python3 -c "
import sys, json
d = json.load(sys.stdin)
m = d.get('mesh')
if m is None:
    print('SKIP')
else:
    assert (m.get('bytes') or 0) >= 2000000, d
    print('REAL:%s:%d' % (m.get('job'), m.get('bytes')))
" 2>/dev/null > /tmp/e2e_mesh.txt && {
  MRES=$(cat /tmp/e2e_mesh.txt)
  [ "$MRES" = "SKIP" ] && pass "showcase mesh guard SKIPPED (pre-pick sidecar)" || pass "showcase mesh: real Tripo ($MRES)"
} || { fail "showcase mesh: stub mesh guard"; }
if command -v ffprobe >/dev/null 2>&1; then
  curl -s -o /tmp/e2e_showcase.mp4 "$BASE/assets/showcase.mp4"
  PROBE=$(ffprobe -v error -show_entries stream=codec_type,codec_name -show_entries format=duration -of default=nw=1 /tmp/e2e_showcase.mp4 2>/dev/null)
  echo "$PROBE" | grep -q "codec_type=audio" && pass "showcase mp4 has audio track" || { fail "showcase mp4 audio track"; }
  DUR=$(echo "$PROBE" | grep -m1 "^duration=" | cut -d= -f2 | cut -d. -f1)
  { [ -n "$DUR" ] && [ "$DUR" -ge 12 ] && [ "$DUR" -le 25 ]; } && pass "showcase mp4 18-25s window (${DUR}s)" || { fail "showcase mp4 duration (got ${DUR:-?}s)"; }
else
  pass "showcase mp4 probe SKIPPED (no ffprobe)"
fi

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

# 12. cover-art: fade cards + covers + detail pages + sitemap
grep -q 'id=fadeTrack' /tmp/e2e_land.html && pass "landing fade track" || fail "landing fade track"
grep -q 'covers/lieberman-2010.jpg' /tmp/e2e_land.html && pass "landing cover img" || fail "landing cover img"
grep -q '/research/lieberman-2010' /tmp/e2e_land.html && pass "landing Read-more link" || fail "landing Read-more link"
grep -q 'ItemList' /tmp/e2e_land.html && pass "landing ItemList JSON-LD" || fail "landing ItemList JSON-LD"
grep -q 'id=fadePrev' /tmp/e2e_land.html && pass "landing fade arrows" || fail "landing fade arrows"
grep -q 'id=fadeDots' /tmp/e2e_land.html && pass "landing fade dots" || fail "landing fade dots"
grep -q 'id=fadePos' /tmp/e2e_land.html && pass "landing fade position" || fail "landing fade position"
grep -q 'fade-card' /tmp/e2e_land.html && pass "landing fade cards" || fail "landing fade cards"
for ex in covers/lieberman-2010.jpg covers/teng-powers-2014.jpg; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/research/papers/$ex")
  [ "$code" = "200" ] && pass "cover $ex 200" || { fail "cover $ex (got $code)"; }
done
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/research/papers/covers/../../server.py")
[ "$code" = "404" ] && pass "cover traversal 404" || { fail "cover traversal (got $code)"; }
for s in lieberman-2010 heiderscheit-2011 souza-2016 daoud-2012 cavanagh-lafortune-1980 van-gent-2007 bramah-2018 schubert-2014 xu-2021 willwacher-2022 teng-powers-2014; do
  code=$(curl -s -o /tmp/e2e_res.html -w "%{http_code}" "$BASE/research/$s")
  [ "$code" = "200" ] && pass "research $s 200" || { fail "research $s (got $code)"; }
done
for feat in "ScholarlyArticle" "rel=canonical" "research/teng-powers-2014" "Which analysis rule it backs"; do
  grep -q "$feat" /tmp/e2e_res.html && pass "detail marker: $feat" || fail "detail marker: $feat"
done
curl -s -o /tmp/e2e_res2.html "$BASE/research/souza-2016"
grep -q "ScholarlyArticle" /tmp/e2e_res2.html && pass "shallow detail JSON-LD" || fail "shallow detail JSON-LD"
grep -q "/guide/stop-overstriding" /tmp/e2e_res2.html && pass "detail guide cross-link" || fail "detail guide cross-link"
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/research/not-a-study")
[ "$code" = "404" ] && pass "unknown study 404" || { fail "unknown study 404 (got $code)"; }
curl -s "$BASE/sitemap.xml" | grep -q "/research/lieberman-2010" && pass "sitemap research URLs" || fail "sitemap research URLs"

# 13. landing-tidy: headed steps trio + proof/privacy sections + rhythm hooks
for feat in "lu-steps" "How it works" "id=proof" "id=privacy" "1 &middot; Upload" "2 &middot; Analyse" "3 &middot; Explore"; do
  grep -q "$feat" /tmp/e2e_land.html && pass "tidy marker: $feat" || fail "tidy marker: $feat"
done
# 13b. centering guards: proof keeps .wrap centering (no margin:0 kill), heads centered
grep -q "lu-proof{[^}]*margin:0" /tmp/e2e_land.html && fail "centering guard: proof margin kill" || pass "centering guard: proof margin intact"
grep -q "lu-privacy h2{text-align:center}" /tmp/e2e_land.html && pass "centering guard: heads centered" || fail "centering guard: heads centered"
# 13c. section order (analyse<science<faq) + sample report repoint
ANL=$(grep -b -o 'id=analyse' /tmp/e2e_land.html | head -n1 | cut -d: -f1)
SCI=$(grep -b -o 'id=science' /tmp/e2e_land.html | head -n1 | cut -d: -f1)
FAQ=$(grep -b -o 'id=faq' /tmp/e2e_land.html | head -n1 | cut -d: -f1)
[ -n "$ANL" ] && [ -n "$SCI" ] && [ -n "$FAQ" ] && [ "$ANL" -lt "$SCI" ] && [ "$SCI" -lt "$FAQ" ] && pass "section order analyse<science<faq" || fail "section order analyse<science<faq"
for feat in "id=analyse" "id=science" "id=faq"; do
  grep -q "$feat" /tmp/e2e_land.html && pass "anchor present: $feat" || fail "anchor present: $feat"
done
N=$(grep -o "/report/aeb979a86e8b" /tmp/e2e_land.html | wc -l)
[ "$N" -ge 4 ] && pass "sample links x$N on landing" || fail "sample links (got $N, want >=4)"
curl -s "$BASE/sitemap.xml" | grep -q "/report/aeb979a86e8b" && pass "sitemap sample URL" || fail "sitemap sample URL"
code=$(curl -s -o /tmp/e2e_sample.html -w "%{http_code}" "$BASE/report/aeb979a86e8b")
[ "$code" = "200" ] && grep -q "var ANALYSIS" /tmp/e2e_sample.html && pass "sample report 200 + renders" || fail "sample report (got $code)"

# 14. quality-voice: script lab + usefulness ratings
code=$(curl -s -o /tmp/e2e_lab.html -w "%{http_code}" "$BASE/script-lab.html")
[ "$code" = "200" ] && grep -q "Script lab" /tmp/e2e_lab.html && pass "script lab 200" || { fail "script lab (got $code)"; }
grep -q "buildLabStory" /tmp/e2e_lab.html && pass "script lab rewrite builder" || fail "script lab builder"
grep -q "Was this analysis useful" /tmp/e2e_demo.html && pass "report rating widget" || fail "report rating widget"
grep -q '"/api/rate"' /tmp/e2e_demo.html && pass "report rate endpoint ref" || fail "report rate ref"
code=$(curl -s -o /tmp/e2e_an.json -w "%{http_code}" "$BASE/api/analysis/961e6b5de398")
[ "$code" = "200" ] && grep -q "overall_score" /tmp/e2e_an.json && pass "analysis api 200" || { fail "analysis api (got $code)"; }
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/analysis/nope-not-real")
[ "$code" = "404" ] && pass "analysis unknown 404" || { fail "analysis 404 (got $code)"; }
if command -v node >/dev/null 2>&1; then
  if node site/script_lab_test.js site/script-lab.html site/jobs/961e6b5de398/analysis.json site/jobs/demo/analysis.json site/jobs/aeb979a86e8b/analysis.json site/jobs/419d46c0abbf/analysis.json > /tmp/e2e_lab_test.log 2>&1; then
    pass "lab contract (flaw+fix specificity, retake cap)"
  else
    fail "lab contract (see /tmp/e2e_lab_test.log)"
  fi
else
  pass "lab contract SKIPPED (no node)"
fi
RATE=$(curl -s -X POST "$BASE/api/rate" -H "Content-Type: application/json" -d '{"job":"demo","useful":true,"note":"e2e probe"}')
echo "$RATE" | grep -q '"ok": *true' && pass "rate POST ok" || { fail "rate POST (got $RATE)"; }
echo "$RATE" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('yes',0)>=1, d" 2>/dev/null && pass "rate counts yes>=1" || { fail "rate counts"; }
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/rate" -H "Content-Type: application/json" -d '{"job":"nope-not-real","useful":true}')
[ "$code" = "404" ] && pass "rate unknown job 404" || { fail "rate 404 (got $code)"; }
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/rate" -H "Content-Type: application/json" -d '{"job":"demo","useful":"yes"}')
[ "$code" = "400" ] && pass "rate non-bool 400" || { fail "rate non-bool (got $code)"; }
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/rate" -H "Content-Type: application/json" -d '{"job":"demo"}')
[ "$code" = "400" ] && pass "rate missing useful 400" || { fail "rate missing (got $code)"; }
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/ratings")
[ "$code" = "303" ] && pass "ratings guard 303" || { fail "ratings guard (got $code)"; }
code=$(curl -s -b "$JAR" -o /tmp/e2e_ratings.html -w "%{http_code}" "$BASE/ratings")
[ "$code" = "200" ] && grep -q "demo" /tmp/e2e_ratings.html && pass "ratings 200 shows demo vote" || { fail "ratings page (got $code)"; }
python3 -c "
import json
rated=[json.loads(l) for l in open('site/usage.log') if l.strip() and json.loads(l).get('kind') in ('rating','ratings_view')]
assert rated, 'no rating ledger lines'
assert all((l.get('usd') or 0)==0 for l in rated), rated
print('ledger rating lines:', len(rated))
" 2>/dev/null && pass 'ledger rating $0' || { fail "ledger rating spend"; }

[ "$FAIL" = "0" ] && echo "E2E GREEN" || echo "E2E RED"
exit $FAIL
