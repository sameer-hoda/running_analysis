#!/usr/bin/env python3
"""RunForm cloud sandbox: landing -> guest login -> upload -> Tripo cloud 3D + Gemini report.

Run: ./venv/bin/python site/server.py [port]   (binds 127.0.0.1, default 8139)
Target: t3.small (2 vCPU / 2GB). No torch, no local TripoSR — mesh via Tripo v3 API.
TRIPO_API_KEY must be in .env (else jobs fall back to the demo mesh so the site stays clickable).

SERIAL PIPELINE (pipeline-auth documented; see run_pipeline/enqueue_pipeline).
Upload (POST /api/jobs, multipart photo, <=8MB) -> sanitize_upload (PIL verify +
EXIF rotate + downscale + JPEG normalize) -> isolate_runners (multi-person
crop to largest bbox, fail-soft; orig kept as input_orig.jpg) ->
jobs/<jid>/{input.jpg,status.json} ->
enqueue_pipeline (CROSS-JOB SERIAL QUEUE: one ACTIVE_JOB at a time, extras park at
stage=queued; WORKER_TIMEOUT=600s; restart requeues stuck jobs via
restore_status_from_disk) -> run_pipeline per job:
  IN-JOB LANES (concurrent threads sharing only input.jpg):
    audit_job: gemini_audit(input.jpg, step1_prompt.txt) -> analysis.json.
      is_running=false fails fast ("No runner detected in photo").
    tripo_job: tripo_cloud.upload_image -> create_task -> wait_task (80-110s cloud
      gen overlaps the 10-25s audit) -> model_url. Started WITHOUT waiting for the
      audit; download is gated on is_running so joke uploads fail before download.
  SERIAL TAIL (after both lanes join): download model (3x retry) -> normalize_glb ->
  compute_anchors(mesh.glb, zones) -> anchors.json -> stage=done (+score).
Loader contract (JOB_PAGE polls GET /api/jobs/<jid> every 2s):
  stages queued(4%) -> analyzing(30%) -> meshing(30+progress*0.65) -> done(100%) /
  failed(100%). progress = Tripo cloud percent. Sandbox mirror: sandbox_loader.html.
  Watch screen (loading theater): 3D globe + Kabeer narration line per stage +
  check-off stage cards (collapsible, active auto-opens) + live paper rail
  (catalog thumbs as image previews, 7s rotate, reduced-motion safe).
PARALLEL PLAN + GUEST-AUTH BRIDGE: see PARALLEL_PLAN below and the auth helpers
(session_token/owner_hash, POST /login ?next=, claim endpoint notes).
"""
import http.cookies
import http.server
import html as _html
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
import uuid

try:
    import usage
except ImportError:  # ledger is optional; serving never depends on it
    usage = None

try:
    from landing_overhaul import (CSS_ADD as LANDING_CSS_ADD, HERO_H1,
                                  HERO_LEAD, HERO_TRUST, PROOF_HTML,
                                  PRIVACY_HTML, UPLOAD_META, META_DESC,
                                  OG_DESC, STEPS_HEAD)
except ImportError:  # overhaul is optional; landing renders the old copy
    LANDING_CSS_ADD = ""
    HERO_H1 = ("<h1>Analyze your <span class=lime>running form</span>.</h1>")
    HERO_LEAD = ("<p class=lead>One photo becomes a 3D breakdown of your stride "
                 "&mdash; the flaws, the fixes, the drills. About two minutes.</p>")
    HERO_TRUST = ""
    PROOF_HTML = ""
    PRIVACY_HTML = ""
    UPLOAD_META = ("<p class=meta>No account needed. Your photo is scored by Gemini "
                   "and rebuilt in textured 3D in the cloud.</p>")
    META_DESC = ("Analyze your running form from one photo: AI form score, "
                 "zone-by-zone flaws, fixes and drills, plus a 3D model of "
                 "your stride. Free, about 2 minutes.")
    OG_DESC = ("One running photo becomes a 3D breakdown of your stride — "
               "flaws, fixes, drills. Free, about two minutes.")
    STEPS_HEAD = ""


def _ulog(kind, job=None, **kw):
    try:
        if usage is not None:
            usage.log_event(kind, job=job, **kw)
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
V4_ROOT = os.path.dirname(HERE)  # v4 checkout root (work ONLY here; never v3)
V3 = os.environ.get("RUNFORM_ROOT", V4_ROOT)
JOBS = os.path.join(V3, "site", "jobs")
TEMPLATE = os.path.join(V3, "site", "report_template.html")
TRIPOSR_SRC = os.path.join(V3, "tripoSR_src")  # legacy local path; unused in cloud sandbox
STEP1_PROMPT = open(os.path.join(V3, "step1_prompt.txt")).read()


def _read_env_file(path):
    out = {}
    try:
        for line in open(path):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip("\"'")
    except OSError:
        pass
    return out


_ENV = _read_env_file(os.path.join(V3, ".env"))
# GEMINI key: env > sandbox .env > legacy v2 path (local dev only)
GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or _ENV.get("GEMINI_API_KEY", "")
if not GEMINI_KEY:
    try:
        GEMINI_KEY = [l.split("=", 1)[1].strip().strip("\"'") for l in
                      open("/Users/sameerhoda/Projects/running_analysis/v2/.env")
                      if l.startswith("GEMINI_API_KEY=")][0]
    except (OSError, IndexError):
        GEMINI_KEY = ""
if not GEMINI_KEY:
    print("WARNING: GEMINI_API_KEY not set — audits will fail", flush=True)
INWORLD_KEY = os.environ.get("INWORLD_API_KEY") or _ENV.get("INWORLD_API_KEY", "")
# NOTE: "Kabir" is the Inworld provider voiceId on the wire (changing it breaks
# synthesis). The coach's display name everywhere the user reads is "Kabeer".
INWORLD_VOICE = os.environ.get("INWORLD_TTS_VOICE") or _ENV.get("INWORLD_TTS_VOICE", "Kabir")
INWORLD_MODEL = "inworld-tts-2"
INWORLD_VOICES = ["Kabir", "Nate", "Brian", "Liam", "Elliot", "Cooper", "Arthur"]
# Premium homepage model path (optional): Tripo v3 image-to-3D, generated by site/premium_model.py
TRIPO_KEY = os.environ.get("TRIPO_API_KEY") or _ENV.get("TRIPO_API_KEY", "")
TRIPO_MODEL = os.environ.get("TRIPO_MODEL") or _ENV.get("TRIPO_MODEL", "v3.1-20260211")
# Google Analytics 4: set GA_MEASUREMENT_ID=G-XXXXXXXXXX (env or sandbox .env).
# Empty/invalid -> no tag emitted, pages render unchanged.
GA_MEASUREMENT_ID = os.environ.get("GA_MEASUREMENT_ID") or _ENV.get("GA_MEASUREMENT_ID", "")
if not re.match(r"^G-[A-Z0-9]{4,}$", GA_MEASUREMENT_ID or ""):
    if GA_MEASUREMENT_ID:
        print("WARNING: GA_MEASUREMENT_ID looks wrong (want G-XXXXXXXXXX) — tag disabled", flush=True)
    GA_MEASUREMENT_ID = ""
GA_SNIPPET = ("<script async src='https://www.googletagmanager.com/gtag/js?id=" + GA_MEASUREMENT_ID + "'></script>"
              "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}"
              "gtag('js',new Date());gtag('config','" + GA_MEASUREMENT_ID + "');</script>") if GA_MEASUREMENT_ID else ""
MAX_UPLOAD = 8 * 1024 * 1024
JOB_RE = re.compile(r"^[a-zA-Z0-9_-]{1,40}$")

# --- growth-memory: history + 15-cap + IG share (additive; see docs/GROWTH_SPEC.md) ---
# All growth routes are gated on RF_ENABLE_GROWTH (default on). /s/ + /api/links/ are
# frozen and never consult these flags.
def _growth_enabled():
    return os.environ.get("RF_ENABLE_GROWTH", "1") != "0"


def _growth_cap():
    try:
        return max(0, int(os.environ.get("RF_MAX_ANALYSES", "15")))
    except (TypeError, ValueError):
        return 15


def _growth_mailto():
    addr = os.environ.get("RF_PAYWALL_MAILTO", "EMAIL_REMOVED").strip() or \
        "EMAIL_REMOVED"
    return "mailto:%s?subject=RunForm%%20unlock" % addr


def _growth_history_path():
    return os.environ.get("RF_HISTORY_PATH",
                          os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "history.json"))


def _token_of(handler):
    try:
        jar = http.cookies.SimpleCookie(handler.headers.get("Cookie") or "")
        tok = jar.get("rf_guest")
        return tok.value if tok else None
    except Exception:
        return None


def _history_load():
    try:
        with open(_growth_history_path()) as f:
            h = json.load(f)
        return h if isinstance(h, dict) else {}
    except (OSError, ValueError):
        return {}


def _history_save(h):
    try:
        with open(_growth_history_path(), "w") as f:
            json.dump(h, f)
    except OSError:
        pass


def _history_prune(entries):
    """Drop entries whose job dirs vanished (demo never stored, so never pruned)."""
    kept = []
    for e in entries or []:
        jid = (e or {}).get("job")
        if not jid or not JOB_RE.match(jid):
            continue
        if os.path.isdir(os.path.join(JOBS, jid)):
            kept.append(e)
    return kept


def _history_for(token):
    if not token:
        return []
    h = _history_load()
    entries = _history_prune(h.get(token))
    if entries != h.get(token):
        h[token] = entries
        _history_save(h)
    return entries


def _history_add(token, jid, filename=""):
    if not token or jid == "demo":
        return 0
    h = _history_load()
    entries = _history_prune(h.get(token))
    entries.append({"job": jid, "ts": time.time(),
                    "filename": (filename or "")[:80]})
    h[token] = entries
    _history_save(h)
    return len(entries)


def _history_remove(token, jid):
    h = _history_load()
    entries = [e for e in (h.get(token) or []) if (e or {}).get("job") != jid]
    h[token] = entries
    _history_save(h)
    return entries


# --- quality-voice: usefulness ratings (additive; see .agents/handoffs/quality-voice.md) ---
# Per-report "Was this analysis useful? Yes/No (+ one-line note)" votes live with
# the job as site/jobs/<jid>/ratings.jsonl (the /s/ clicks.jsonl pattern); every
# vote also appends a zero-cost "rating" line to the usage ledger. /ratings
# (login-gated, like /history) aggregates every job for the watcher; the lowest
# rated scripts get rewritten first in the script lab.
def _ratings_path(jid):
    return os.path.join(JOBS, jid, "ratings.jsonl")


def _ratings_read(jid):
    votes = []
    try:
        with open(_ratings_path(jid)) as f:
            for line in f:
                try:
                    v = json.loads(line)
                except ValueError:
                    continue
                if isinstance(v, dict) and isinstance(v.get("useful"), bool):
                    votes.append({"ts": v.get("ts", 0),
                                  "useful": v["useful"],
                                  "note": str(v.get("note", ""))[:140]})
    except OSError:
        pass
    return votes


def _ratings_add(jid, useful, note=""):
    v = {"ts": time.time(), "useful": bool(useful),
         "note": str(note or "")[:140]}
    try:
        with open(_ratings_path(jid), "a") as f:
            f.write(json.dumps(v) + "\n")
    except OSError:
        return None
    return v


def _ratings_summary(jid):
    votes = _ratings_read(jid)
    notes = [v for v in sorted(votes, key=lambda x: x.get("ts", 0),
                               reverse=True) if v.get("note")][:5]
    return {"job": jid, "yes": sum(1 for v in votes if v["useful"]),
            "no": sum(1 for v in votes if not v["useful"]), "notes": notes}


def _ratings_page():
    try:
        jids = sorted(os.listdir(JOBS))
    except OSError:
        jids = []
    cards = []
    for jid in jids:
        if not JOB_RE.match(jid):
            continue
        s = _ratings_summary(jid)
        if not (s["yes"] or s["no"]):
            continue
        try:
            a = json.load(open(os.path.join(JOBS, jid, "analysis.json")))
            score = a.get("overall_score", "")
        except (OSError, ValueError):
            score = ""
        notes = "".join("<p class=meta>%s — %s</p>" % (
            _html.escape("useful" if n["useful"] else "not useful"),
            _html.escape(n["note"])) for n in s["notes"])
        cards.append(("<div class=card><p><b><a href='/report/%s'>%s</a></b> "
                      "score %s · <span class=lime>%d yes</span> · %d no</p>%s</div>") % (
            _html.escape(jid), _html.escape(jid), _html.escape(str(score)),
            s["yes"], s["no"], notes))
    body = ("<h1>Analysis <span class=lime>ratings.</span></h1>"
            "<p class=sub>Lowest-rated scripts get rewritten first in the "
            "script lab (<a href='/script-lab.html'>sandbox</a>).</p>"
            + ("".join(cards) or "<div class=card><p>No votes yet.</p></div>"))
    return ("<!doctype html><html><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>RunForm — analysis ratings</title>" + CSS +
            "</head><body><div class=wrap>" + body + "</div></body></html>")


def _paywall_body(used, cap):
    # Token replacement (NOT %-formatting): CSS contains literal % characters.
    return (("<!doctype html><html><head><meta charset=utf-8>"
             "<meta name=viewport content='width=device-width,initial-scale=1'>"
             "<title>RunForm — unlock unlimited analyses</title>"
             "<meta name=robots content='noindex,nofollow'>" + CSS +
             "<script src=/assets/dots.js defer></script></head>"
             "<body><canvas id=dots-bg></canvas><div class=wrap>"
             "<h1>You've used your <span class=lime>__USED__ free analyses.</span></h1>"
             "<p class=sub>RunForm is free for the first __CAP__ runs per runner. "
             "Email to unlock unlimited analyses — a human replies, no checkout, no account.</p>"
             "<div class=card style='text-align:center'>"
             "<a class=btn href='__MAILTO__'>Unlock via email &rarr;</a><br>"
             "<a class=quiet href='/history'>See your history</a></div>"
             "<p class=meta>Privacy-first: we store only a random guest cookie plus your own "
             "run ids. Delete any run anytime from history.</p>"
             "</div></body></html>")
            .replace("__USED__", str(used)).replace("__CAP__", str(cap))
            .replace("__MAILTO__", _html.escape(_growth_mailto(), quote=True)))


def _history_page(token):
    entries = _history_for(token)
    cap = _growth_cap()
    remaining = max(0, cap - len(entries)) if cap else None
    cards = []
    for e in sorted(entries, key=lambda x: x.get("ts", 0), reverse=True):
        jid = e["job"]
        st = load_status(jid) or {}
        score = st.get("score", "")
        stage = st.get("stage", "")
        ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(e.get("ts", 0)))
        cards.append(
            "<div class=step><b><a href='/report/%s'>%s</a> — %s</b>"
            "<p>score %s · %s · %s</p>"
            "<p><a href='/s/%s'>share link</a> · "
            "<a href='#' data-del='%s'>delete</a></p></div>"
            % (_html.escape(jid),
               _html.escape(e.get("filename") or jid),
               _html.escape(ts), _html.escape(str(score)),
               _html.escape(str(stage)), "%d of %d used" % (len(entries), cap) if cap else "unlimited",
               _html.escape(jid), _html.escape(jid)))
    if cap and len(entries) >= cap:
        cta = ("<div class=card style='text-align:center'><p class=sub>"
               "You've used all %d free analyses.</p>"
               "<a class=btn href='%s'>Unlock via email &rarr;</a></div>"
               % (cap, _html.escape(_growth_mailto(), quote=True)))
    else:
        cta = ("<div class=card style='text-align:center'>"
               "<a class=btn href='/#analyse'>Analyze another run &rarr;</a></div>")
    remain = ("<p class=sub>%d of %d free analyses left.</p>" % (remaining, cap) if cap
              else "<p class=sub>Unlimited analyses (cap disabled).</p>")
    return ("<!doctype html><html><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>RunForm — your history</title>"
            "<meta name=robots content='noindex,nofollow'>" + CSS + GA_SNIPPET +
            "<script src=/assets/dots.js defer></script></head>"
            "<body><canvas id=dots-bg></canvas><div class=wrap>"
            "<h1>Your <span class=lime>run history.</span></h1>" + remain +
            "<p class=sub>No account — this list lives in your guest cookie on this device. "
            "Retention: runs may be purged after 90 days; delete any run anytime.</p>"
            "<section class='wrap steps' style='margin-top:12px;max-width:none;padding:0'>"
            + ("".join(cards) if cards else
               "<div class=step><b>No runs yet</b><p>Upload a side-profile photo to start.</p></div>") +
            "</section>" + cta +
            "<script>document.querySelectorAll('[data-del]').forEach(function(a){"
            "a.addEventListener('click',function(e){e.preventDefault();"
            "if(!confirm('Delete this run?'))return;"
            "fetch('/api/jobs/'+encodeURIComponent(a.getAttribute('data-del')),{method:'DELETE'})"
            ".then(function(){location.reload();});});});</script>"
            "</div></body></html>")


def _ig_caption(jid, analysis):
    try:
        score = analysis.get("overall_score", "")
        label = analysis.get("overall_label") or analysis.get("one_line_summary") or ""
    except AttributeError:
        score, label = "", ""
    text = ("My running form scored %s/100 on RunForm. %s "
            "See the 3D breakdown: /s/%s #runningform #runform #running"
            % (score, label, jid)).strip()
    return re.sub(r"\s+", " ", text)[:280]

SESSIONS = set()
STATUS = {}  # job_id -> dict (mirrored to jobs/<id>/status.json)

ZONE_BANDS = {
    "head_neck":   ((0.86, 1.00), (0, 1, 0.15)),
    "shoulders":   ((0.74, 0.84), (-0.8, 0.15, 0.55)),
    "arms_elbows": ((0.58, 0.70), (-0.25, 0, 1)),
    "trunk_lean":  ((0.55, 0.72), (-1, 0.15, 0.1)),
    "knees":       ((0.22, 0.38), (-0.9, -0.1, 0.45)),
    "feet_strike": ((0.00, 0.14), (-1, -0.2, 0.3)),
    "hips_pelvis": ((0.42, 0.55), (0.2, 0, 1)),
}

CSS = ("<style>*{box-sizing:border-box}:root{--lime:#c8f04a;--bg:#0a0c11;--panel:#12161d;--panel2:#171d26;--ink:#f4f7f2;--dim:#8b938a;--faint:#5b635c;--line:#1c232d;--line2:#2a3441}"
       "html{background:radial-gradient(120% 80% at 70% -10%,#141b26 0,transparent 55%),var(--bg)}#dots-bg{position:fixed;inset:0;z-index:-1;pointer-events:none}body{background:transparent;font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;color:var(--ink);margin:0;-webkit-font-smoothing:antialiased}"
       ".wrap{max-width:1080px;margin:0 auto;padding:26px 22px 64px}"
       "h1{font-size:clamp(30px,5vw,48px);margin:0 0 12px;letter-spacing:-.03em;line-height:1.05}h1 .lime{color:var(--lime)}"
       ".sub{color:var(--dim);font-size:17px;line-height:1.55;max-width:52ch}"
       ".btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;background:linear-gradient(135deg,#dcff72,#a9e33c);color:#0e1206;font-weight:800;border:0;border-radius:12px;padding:15px 26px;font-size:16px;cursor:pointer;text-decoration:none;min-height:52px;box-shadow:0 14px 34px -12px rgba(200,240,74,.6);transition:transform .18s}"
       ".btn:hover{transform:translateY(-1px)}"
       ".btn.ghost{background:transparent;color:var(--ink);border:1px solid var(--line2);box-shadow:none;margin-left:10px}"
       ".quiet{display:inline-block;margin:16px 0 0;color:var(--dim);font-size:14px;min-height:44px;line-height:44px}"
       ".nav{display:flex;align-items:center;gap:14px;padding:18px 26px;position:sticky;top:0;z-index:20;background:linear-gradient(rgba(10,12,17,.9),rgba(10,12,17,.35));backdrop-filter:blur(16px);border-bottom:1px solid rgba(255,255,255,.05)}"
       ".brand{display:inline-flex;align-items:center;gap:10px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;font-size:12px;color:var(--lime)}"
       ".brand .blogo{width:30px;height:30px;border-radius:8px;display:block}"
       ".navlink{margin-left:auto;color:var(--dim);font-size:13px;text-decoration:none}.navlink:hover{color:var(--ink)}"
       ".hero{display:grid;grid-template-columns:1fr 1fr;gap:36px;align-items:center;padding-top:26px}"
       ".upload{margin-top:22px}"
       ".drop{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px;border:1.5px dashed var(--line2);border-radius:16px;padding:26px 20px;text-align:center;color:var(--dim);font-size:14px;background:#0f141b;cursor:pointer;transition:.2s;min-height:152px}"
       ".drop:hover,.drop.over{border-color:var(--lime);background:#11170f}"
       ".drop.has{border-style:solid;border-color:var(--lime)}"
       ".drop-ic{font-size:22px;color:var(--lime);line-height:1}"
       ".drop b{color:var(--ink);font-size:16px}"
       ".stage3d{position:relative;border-radius:20px;border:1px solid rgba(255,255,255,.06);background:radial-gradient(90% 70% at 50% 10%,#18202b,#0c1016 65%);overflow:hidden;aspect-ratio:1/1;box-shadow:0 24px 60px -24px rgba(0,0,0,.8)}"
       ".stage3d canvas{width:100%;height:100%;display:block;cursor:grab;touch-action:none}"
       ".stage3d canvas:active{cursor:grabbing}"
       ".badge{position:absolute;top:14px;right:14px;background:var(--lime);color:#0e1206;font-weight:800;border-radius:999px;padding:7px 13px;font-size:15px}"
       ".badge small{font-weight:400;font-size:11px;opacity:.7}"
       ".hint{position:absolute;bottom:12px;left:50%;transform:translateX(-50%);font-size:11px;color:var(--dim);background:rgba(9,12,17,.6);border:1px solid var(--line);border-radius:999px;padding:4px 12px;white-space:nowrap}"
       ".load3d{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:13px;color:var(--dim)}"
       ".legend{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:14px;font-size:12px;color:var(--dim)}"
       ".legend span{display:inline-flex;align-items:center;gap:6px}.legend i{width:8px;height:8px;border-radius:50%;box-shadow:0 0 8px 1px currentColor}"
       ".steps{display:flex;gap:14px;margin-top:46px;flex-wrap:wrap}"
       ".step{flex:1;min-width:200px;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}"
       ".step b{color:var(--lime);font-size:13px}.step p{color:var(--dim);font-size:14px;margin:6px 0 0;line-height:1.5}"
       ".card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:26px;margin-top:24px}"
       "input[type=file]{margin:14px 0;font-size:15px}"
       ".meta{color:var(--dim);font-size:12.5px;margin-top:14px;line-height:1.6}"
       "a{color:var(--lime)}"
       "#bar{height:8px;background:#1e2630;border-radius:6px;overflow:hidden;margin-top:14px}"
       "#fill{height:100%;width:5%;background:var(--lime);transition:width .5s}"
       ".drop{position:relative}"
       ".preview{display:none;width:100%;max-height:170px;object-fit:cover;border-radius:10px;margin-bottom:8px;border:1px solid var(--line)}"
       ".drop.has .preview{display:block}"
       ".drop.has .drop-ic{display:none}"
       ".btn.ready{animation:btnGlow 1.8s ease-in-out infinite}"
       "@keyframes btnGlow{0%,100%{box-shadow:0 0 0 0 rgba(200,240,74,.5),0 14px 34px -12px rgba(200,240,74,.6)}50%{box-shadow:0 0 0 16px rgba(200,240,74,0),0 18px 44px -12px rgba(200,240,74,.95)}}"
       ".playfab{position:absolute;left:50%;bottom:16px;transform:translateX(-50%);display:inline-flex;align-items:center;gap:10px;background:var(--lime);color:#0e1206;font-weight:800;border:0;border-radius:999px;padding:13px 22px;font-size:14px;cursor:pointer;box-shadow:0 14px 40px -12px rgba(200,240,74,.7);z-index:3}"
       ".playfab svg{width:12px;height:13px;fill:currentColor}"
       ".stage3d video{width:100%;height:100%;display:block;object-fit:cover;background:#0c1016}"
       ":focus-visible{outline:3px solid var(--lime);outline-offset:2px;border-radius:8px}"
       "@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}"
       "@media(max-width:820px){.hero{grid-template-columns:1fr;gap:22px}.stage3d{aspect-ratio:4/3}.wrap{padding:16px 16px 56px}.step{min-width:100%}.btn{width:100%}.quiet{display:block;text-align:center}}"
       ".fold{position:relative;min-height:100svh;display:flex;align-items:center;overflow:hidden}.fold .glow{position:absolute;inset:0;z-index:1;pointer-events:none;background:radial-gradient(55% 45% at 76% 18%,rgba(200,240,74,.10),transparent 60%),radial-gradient(60% 60% at 8% 92%,rgba(79,124,255,.10),transparent 60%)}.hero-bg{position:absolute;inset:0;z-index:0;will-change:transform,opacity}.hero-bg video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:72% 40%;opacity:.6}.hero-shade{position:absolute;inset:0;background:linear-gradient(100deg,var(--bg) 20%,rgba(10,12,17,.55) 42%,transparent 68%),linear-gradient(transparent 55%,var(--bg) 97%)}.fold-grid{position:relative;z-index:2;width:100%}.fold-copy{max-width:660px}.fold h1{font-size:clamp(42px,7.5vw,92px);line-height:1.0;letter-spacing:-.04em;margin:0 0 16px}.fold .lead{color:var(--dim);font-size:18px;line-height:1.55;max-width:44ch}.cta-row{display:flex;gap:16px;align-items:center;margin-top:28px;flex-wrap:wrap}.ghostlink{color:var(--dim);font-size:14px;text-decoration:none}.ghostlink:hover{color:var(--lime)}.hero-vid{position:relative;justify-self:center;width:min(340px,70vw)}.hero-vid:before{content:'';position:absolute;inset:-16%;z-index:-1;filter:blur(8px);background:radial-gradient(closest-side,rgba(200,240,74,.18),transparent 70%)}.hero-vid video{width:100%;display:block;border-radius:28px;border:1px solid rgba(255,255,255,.09);background:#0c1016;box-shadow:0 40px 90px -30px rgba(0,0,0,.95)}.scrollcue{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);font-size:10px;letter-spacing:.28em;text-transform:uppercase;color:var(--faint);transition:opacity .2s;z-index:2}.section2{display:grid;grid-template-columns:1fr 1fr;gap:38px;align-items:center;padding-top:72px}.showvid{position:relative;border-radius:22px;overflow:hidden;border:1px solid rgba(255,255,255,.06);background:#0c1016;aspect-ratio:1/1;box-shadow:0 30px 70px -30px rgba(0,0,0,.9)}.showvid video{width:100%;height:100%;object-fit:cover;display:block}.vidtag{position:absolute;top:14px;left:14px;background:rgba(9,12,17,.6);border:1px solid var(--line);color:var(--dim);font-size:11px;border-radius:999px;padding:5px 12px}.soundbtn{position:absolute;bottom:14px;left:50%;transform:translateX(-50%);background:var(--lime);color:#0e1206;font-weight:700;border:0;border-radius:999px;padding:10px 18px;font-size:13px;cursor:pointer;min-height:42px;box-shadow:0 12px 30px -10px rgba(200,240,74,.6)}.uploadcol h2{font-size:clamp(24px,3.4vw,38px);letter-spacing:-.03em;margin:0 0 8px}.lead2{color:var(--dim);font-size:15px;line-height:1.5;margin:0 0 18px;max-width:44ch}@media(max-width:820px){.fold{min-height:92svh;padding:34px 0 54px}.hero-bg video{object-position:60% 35%;opacity:.45}.fold-grid{grid-template-columns:1fr;gap:26px}.section2{grid-template-columns:1fr;gap:26px;padding-top:48px}}</style>")


def set_status(jid, **kw):
    st = STATUS.get(jid, {"job": jid})
    prev = st.get("stage")
    st.update(kw)
    STATUS[jid] = st
    if kw.get("stage") in ("done", "failed") and prev != kw.get("stage"):
        _ulog("job_" + kw["stage"], job=jid,
              detail={"score": st.get("score"),
                      "error": (st.get("error") or "")[-120:]})
    try:
        with open(os.path.join(JOBS, jid, "status.json"), "w") as f:
            json.dump(st, f)
    except OSError:
        pass
    return st


def load_status(jid):
    """Lazy-load status from disk if missing in memory (restart recovery)."""
    if jid in STATUS:
        return STATUS[jid]
    if not JOB_RE.match(jid or ""):
        return None
    try:
        with open(os.path.join(JOBS, jid, "status.json")) as f:
            st = json.load(f)
        STATUS[jid] = st
        return st
    except (OSError, ValueError):
        return None


def recover_statuses():
    """On startup: reload persisted statuses; fail jobs stuck mid-run."""
    try:
        names = os.listdir(JOBS)
    except OSError:
        return
    for jid in names:
        if jid == "demo" or not JOB_RE.match(jid):
            continue
        st = load_status(jid)
        if not st:
            continue
        if st.get("stage") in ("queued", "analyzing", "meshing"):
            set_status(jid, stage="failed",
                       error="server restarted mid-run, please re-upload")


# --- core-loop: landing science section (research-catalog + research-deep) ---
# Server-rendered from research/papers/ at boot — no hardcoded papers in the
# page. Catalog owns bibliography (title/authors/year/link/key_finding/zones/
# thumb); deep owns summaries/snippets/figures/rule links (deep/deep-*.json).
# Static: /research/papers/catalog.json, /research/papers/thumbs/*.svg,
# /research/papers/deep/figures/*.svg. Missing/corrupt store -> SCIENCE_HTML
# is "" and the landing renders unchanged (fail-closed, never 500).
PAPERS_DIR = os.path.join(V3, "research", "papers")
# NOTE: route regex below must stay in sync with the thumbs/figures routes
# (research-catalog block in do_GET): validated names always serve.
_SVG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}\.svg$")


def _papers_link(url):
    u = (url or "").strip()
    return u if u.startswith("https://") else ""


def _papers_thumb_url(thumb):
    base = os.path.basename(thumb or "")
    if not _SVG_RE.match(base):
        return ""
    if not os.path.isfile(os.path.join(PAPERS_DIR, "thumbs", base)):
        return ""
    return "/research/papers/thumbs/" + base


def _papers_catalog():
    try:
        with open(os.path.join(PAPERS_DIR, "catalog.json")) as f:
            cat = json.load(f)
    except (OSError, ValueError):
        return [], {}
    if not isinstance(cat, dict) or not isinstance(cat.get("papers"), list):
        return [], {}
    return cat["papers"], cat


def _papers_card(p):
    if not isinstance(p, dict):
        return ""
    title = str(p.get("title") or "Untitled")
    link = _papers_link(p.get("link"))
    img = _papers_thumb_url(p.get("thumb"))
    zones = [str(z).replace("_", " ") for z in (p.get("zones") or [])
             if isinstance(z, str)]
    byline = ", ".join(str(a) for a in (p.get("authors") or [])
                       if isinstance(a, str))
    journal = str(p.get("journal") or "")
    year = str(p.get("year") or "")
    head = _html.escape(title)
    if link:
        head = "<a href='%s'>%s</a>" % (_html.escape(link, quote=True), head)
    bits = [b for b in (byline, journal, year) if b]
    meta = " · ".join(_html.escape(b) for b in bits)
    if zones:
        meta += (" · backs: " if meta else "backs: ") + _html.escape(
            ", ".join(zones))
    if link:
        meta += " · <a href='%s'>%s</a>" % (
            _html.escape(link, quote=True),
            "PubMed" if "pubmed" in link else "DOI")
    return ("<div class=step>" +
            ("<img src='%s' alt='%s' loading=lazy style='width:100%%;border-radius:10px;border:1px solid var(--line);margin-bottom:10px'>"
             % (_html.escape(img, quote=True),
                _html.escape(title, quote=True)) if img else "") +
            "<b>%s</b><p>%s</p>" % (head, _html.escape(
                str(p.get("key_finding") or ""))) +
            ("<p class=meta>%s</p>" % meta if meta else "") +
            "</div>")


def _deep_entries():
    out = []
    ddir = os.path.join(PAPERS_DIR, "deep")
    try:
        names = sorted(n for n in os.listdir(ddir)
                       if n.startswith("deep-") and n.endswith(".json"))
    except OSError:
        return out
    for n in names:
        try:
            with open(os.path.join(ddir, n)) as f:
                e = json.load(f)
            if not isinstance(e, dict):
                continue
            fig = (e.get("figure") or {}).get("file") or ""
            base = os.path.basename(fig) if isinstance(fig, str) else ""
            if (not _SVG_RE.match(base) or not os.path.isfile(
                    os.path.join(ddir, "figures", base))):
                continue
            rl = e.get("rule_link") or {}
            cit = e.get("citation") or {}
            snip = e.get("snippet") or {}
            if not isinstance(rl, dict) or not isinstance(cit, dict) \
                    or not isinstance(snip, dict):
                continue
            zone = str(rl.get("zone") or "")
            text = str(snip.get("text") or "")
            if not zone or not text:
                continue
            out.append({
                "fig": "/research/papers/deep/figures/" + base,
                "alt": str((e.get("figure") or {}).get("caption") or zone),
                "zone": zone.replace("_", " "),
                "finding": str(rl.get("finding_title") or zone),
                "how": str(rl.get("how_it_backs") or ""),
                "text": text,
                "methods": str(e.get("methods_signal") or ""),
                "cite": "%s (%s). %s. %s." % (
                    cit.get("authors") or "", cit.get("year") or "",
                    cit.get("title") or "", cit.get("journal") or ""),
                "doi": _papers_link(cit.get("doi_url")),
                "pubmed": _papers_link(cit.get("pubmed_url")),
            })
        except (OSError, ValueError, AttributeError):
            continue
    return out


def _deep_card(e):
    links = []
    if e["doi"]:
        links.append("<a href='%s'>DOI</a>"
                     % _html.escape(e["doi"], quote=True))
    if e["pubmed"]:
        links.append("<a href='%s'>PubMed</a>"
                     % _html.escape(e["pubmed"], quote=True))
    links = " · ".join(links)
    meta = _html.escape(e["cite"])
    if e["methods"]:
        meta += " " + _html.escape(e["methods"])
    if e["how"]:
        meta += " Backs " + _html.escape(e["zone"]) + ": " + _html.escape(
            e["how"])
    if links:
        meta += " " + links
    return ("<div class=step>"
            "<img src='%s' alt='%s' loading=lazy style='width:100%%;border-radius:10px;border:1px solid var(--line);margin-bottom:10px'>"
            "<b>%s</b><p>%s</p><p class=meta>%s</p></div>"
            % (_html.escape(e["fig"], quote=True),
               _html.escape(e["alt"], quote=True),
               _html.escape(e["finding"]), _html.escape(e["text"]), meta))


# --- showcase-seo: poster carousel + study detail pages (additive) ---
# Covers: research/papers/covers/<slug>.jpg via gemini-2.5-flash-image
# (convention-based, no catalog.json schema change). Detail pages read
# catalog (bibliography) + deep/*.json (summaries/figures/snippets).
# Landing keeps id=science + all 11 titles server-rendered for SEO.
SHOWCASE_CSS = ("<style>"
       ".sc-railwrap{width:100%;margin-top:16px}"
       ".fade-viewport{overflow:hidden;border:1px solid var(--line);border-radius:8px;background:var(--panel)}"
       ".fade-track{display:flex;transition:transform .45s ease}"
       ".fade-card{flex:0 0 100%;display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);min-height:340px}"
       ".fade-fig{position:relative;margin:0;min-height:340px}"
       ".fade-fig img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block;background:#000;-webkit-mask-image:linear-gradient(to right,#000 62%,transparent 98%);mask-image:linear-gradient(to right,#000 62%,transparent 98%)}"
       ".fade-tx{padding:30px 34px 26px 6px;display:flex;flex-direction:column;justify-content:center}"
       ".fade-eyebrow{display:flex;justify-content:space-between;align-items:baseline;gap:10px;font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim);border-bottom:1px solid var(--line2);padding-bottom:10px;margin:0 0 14px}"
       ".fade-eyebrow .n{color:var(--lime);font-weight:800;font-size:15px;letter-spacing:0}"
       ".fade-title{font-size:24px;line-height:1.25;letter-spacing:-.015em;margin:0}"
       ".fade-title a{color:var(--ink);text-decoration:none}"
       ".fade-title a:hover{color:var(--lime);text-decoration:underline}"
       ".fade-find{color:var(--dim);font-size:14.5px;line-height:1.6;margin:10px 0 0}"
       ".fade-more{margin:16px 0 0;font-size:13.5px}"
       ".fade-more a{color:var(--lime);text-decoration:none}"
       ".fade-controls{display:flex;align-items:center;gap:14px;margin:12px 0 0}"
       ".fade-arrows{display:flex;gap:8px}"
       ".fade-arrows button{width:44px;height:44px;border-radius:50%;border:1px solid var(--line2);background:var(--panel);color:var(--ink);font-size:18px;line-height:1;cursor:pointer}"
       ".fade-arrows button:hover{border-color:var(--lime);color:var(--lime)}"
       ".fade-pos{font-size:13px;color:var(--dim);font-variant-numeric:tabular-nums;margin:0}"
       ".fade-pos b{color:var(--ink)}"
       ".fade-dots{display:flex;gap:8px;flex:1}"
       ".fade-dots button{width:22px;height:4px;border-radius:2px;border:0;background:var(--line2);cursor:pointer;padding:0}"
       ".fade-dots button.on{background:var(--lime)}"
       "@media(max-width:700px){.fade-card{grid-template-columns:1fr;min-height:0}.fade-fig{min-height:220px}.fade-fig img{-webkit-mask-image:linear-gradient(to bottom,#000 62%,transparent 98%);mask-image:linear-gradient(to bottom,#000 62%,transparent 98%)}.fade-tx{padding:6px 20px 22px}.fade-title{font-size:20px}}"
       "@media(prefers-reduced-motion:reduce){.fade-track{transition:none}}"
       ".sc-hero{display:grid;grid-template-columns:300px 1fr;gap:32px;align-items:start;margin-top:26px}"
       ".sc-heroimg{width:100%;aspect-ratio:3/4;object-fit:cover;border-radius:4px 22px 4px 22px;border:1px solid var(--line2);background:#000}"
       ""       ".sc-backing{background:var(--panel);border:1px solid var(--line);border-top:2px solid var(--lime);border-radius:4px 14px 14px 14px;padding:18px 20px;margin-top:22px}"
       ".sc-fig{margin:26px 0 0;background:var(--panel);border:1px solid var(--line);border-radius:6px 18px 6px 18px;padding:20px}"
       ".sc-fig img{width:100%;border-radius:4px;border:1px solid var(--line)}"
       ".sc-fig figcaption{color:var(--dim);font-size:13px;margin-top:10px;line-height:1.55}"
       ".sc-quote{border-left:3px solid var(--lime);margin:26px 0 0;padding:4px 0 4px 18px;font-size:17px;line-height:1.6}"
       ".sc-quote footer{color:var(--dim);font-size:13px;margin-top:8px}"
       ".sc-zones{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 0;padding:0;list-style:none}"
       ".sc-zones a{display:inline-block;border:1px solid var(--line2);border-radius:999px;padding:6px 14px;font-size:12.5px;text-decoration:none}"
       ".sc-rel{display:flex;gap:14px;margin-top:14px;flex-wrap:wrap}"
       ".sc-relcard{flex:1;min-width:180px;background:var(--panel);border:1px solid var(--line);border-radius:6px 16px 6px 16px;padding:12px;text-decoration:none;display:block}"
       ".sc-relcard img{width:100%;aspect-ratio:16/10;object-fit:cover;object-position:top;border-radius:3px 10px 3px 10px;border:1px solid var(--line2)}"
       ".sc-relcard b{display:block;color:var(--ink);font-size:13.5px;line-height:1.4;margin-top:8px}"
       ".sc-prevnext{display:flex;justify-content:space-between;gap:12px;margin-top:30px;flex-wrap:wrap}"
       "@media(max-width:820px){.sc-hero{grid-template-columns:1fr;gap:18px}.sc-heroimg{max-width:340px}.fade-arrows button{width:40px;height:40px;font-size:16px}}"
       "</style>")

SHOWCASE_JS = ("(function(){var r=document.getElementById('fadeTrack');if(!r)return;try{"
       "var cards=r.children,n=cards.length;"
       "var dw=document.getElementById('fadeDots'),pos=document.getElementById('fadePos');"
       "var rm=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;"
       "var idx=0,timer=null;"
       "function paint(){for(var j=0;j<n;j++){"
       "cards[j].setAttribute('aria-hidden',j===idx?'false':'true');"
       "if(dw&&dw.children[j])dw.children[j].className=j===idx?'on':'';}"
       "if(pos)pos.innerHTML='<b>'+(idx+1)+'</b> / '+n;}"
       "function restart(){if(timer){clearInterval(timer);timer=null;}"
       "if(!rm&&n>1)timer=setInterval(function(){go(idx+1);},6000);}"
       "function go(k){idx=((k%n)+n)%n;"
       "r.style.transform='translateX(-'+(idx*100)+'%)';paint();restart();}"
       "if(dw){for(var k=0;k<n;k++){(function(q){var b=document.createElement('button');"
       "b.setAttribute('aria-label','Go to study '+(q+1));"
       "b.addEventListener('click',function(){go(q);});dw.appendChild(b);})(k);}"
       "var pv=document.getElementById('fadePrev'),nx=document.getElementById('fadeNext');"
       "if(pv)pv.addEventListener('click',function(){go(idx-1);});"
       "if(nx)nx.addEventListener('click',function(){go(idx+1);});"
       "r.addEventListener('keydown',function(e){"
       "if(e.key==='ArrowLeft')go(idx-1);else if(e.key==='ArrowRight')go(idx+1);});"
       "var view=r.parentElement;"
       "view.addEventListener('mouseenter',function(){if(timer)clearInterval(timer);});"
       "view.addEventListener('mouseleave',restart);"
       "view.addEventListener('focusin',function(){if(timer)clearInterval(timer);});"
       "view.addEventListener('focusout',restart);"
       "go(0);}"
       "}catch(e){}})();")

# Zone -> fix guide (internal linking for detail pages).
ZONE_GUIDES = {
    "feet_strike": "stop-overstriding",
    "knees": "increase-running-cadence",
    "trunk_lean": "running-forward-lean",
    "hips_pelvis": "hip-drop-running",
    "head_neck": "head-position-running",
    "shoulders": "relaxed-shoulders-running",
    "arms_elbows": "arm-swing-running-form",
}


def _papers_cover_url(pid):
    base = str(pid or "") + ".jpg"
    if not re.match(r"^[a-z0-9-]+\.jpg$", base):
        return ""
    if not os.path.isfile(os.path.join(PAPERS_DIR, "covers", base)):
        return ""
    return "/research/papers/covers/" + base


def _papers_by_id():
    papers, _ = _papers_catalog()
    return {p["id"]: p for p in papers if isinstance(p, dict) and p.get("id")}


def _deep_by_catalog():
    """Map catalog_id -> deep entry (summary/methods/figure/snippet/rule/cite)."""
    out = {}
    ddir = os.path.join(PAPERS_DIR, "deep")
    try:
        names = sorted(n for n in os.listdir(ddir)
                       if n.startswith("deep-") and n.endswith(".json"))
    except OSError:
        return out
    for n in names:
        try:
            with open(os.path.join(ddir, n)) as f:
                e = json.load(f)
            if not isinstance(e, dict):
                continue
            cid = e.get("catalog_id")
            if not cid or not isinstance(cid, str):
                continue
            fig = (e.get("figure") or {}).get("file") or ""
            base = os.path.basename(fig) if isinstance(fig, str) else ""
            figurl = ""
            if _SVG_RE.match(base) and os.path.isfile(
                    os.path.join(ddir, "figures", base)):
                figurl = "/research/papers/deep/figures/" + base
            rl = e.get("rule_link") or {}
            cit = e.get("citation") or {}
            snip = e.get("snippet") or {}
            if not isinstance(rl, dict) or not isinstance(cit, dict) \
                    or not isinstance(snip, dict):
                continue
            out[cid] = {
                "summary": str(e.get("summary") or ""),
                "methods": str(e.get("methods_signal") or ""),
                "fig": figurl,
                "caption": str((e.get("figure") or {}).get("caption") or ""),
                "snippet": str(snip.get("text") or ""),
                "grounds": str(snip.get("grounds_in") or ""),
                "zone": str(rl.get("zone") or ""),
                "finding": str(rl.get("finding_title") or ""),
                "how": str(rl.get("how_it_backs") or ""),
                "cite": "%s (%s). %s. %s." % (
                    cit.get("authors") or "", cit.get("year") or "",
                    cit.get("title") or "", cit.get("journal") or ""),
                "doi": _papers_link(cit.get("doi_url")),
                "pubmed": _papers_link(cit.get("pubmed_url")),
            }
        except (OSError, ValueError, AttributeError):
            continue
    return out


def _showcase_card(i, p):
    slug = str(p.get("id") or "")
    title = str(p.get("title") or "Untitled")
    link = _papers_link(p.get("link"))
    img = _papers_cover_url(slug) or _papers_thumb_url(p.get("thumb"))
    journal = str(p.get("journal") or "")
    year = str(p.get("year") or "")
    mast = " · ".join(b for b in (journal, year) if b)
    ext = (" · <a href='%s' rel=noopener>%s</a>"
           % (_html.escape(link, quote=True),
              "PubMed" if "pubmed" in link else "DOI") if link else "")
    return ("<article class=fade-card aria-hidden=%s>"
            "<figure class=fade-fig>"
            "<img src='%s' alt='' width=800 height=800%s></figure>"
            "<div class=fade-tx>"
            "<p class=fade-eyebrow><span>%s</span>"
            "<span class=n>%02d</span></p>"
            "<h3 class=fade-title><a href='/research/%s'>%s</a></h3>"
            "<p class=fade-find>%s</p>"
            "<p class=fade-more><a href='/research/%s'>Read the study &rarr;</a>%s</p>"
            "</div></article>"
            % ("false" if i == 0 else "true",
               _html.escape(img, quote=True),
               "" if i < 2 else " loading=lazy",
               _html.escape(mast), i + 1, _html.escape(slug),
               _html.escape(title), _html.escape(str(p.get("key_finding") or "")),
               _html.escape(slug), ext))


def _showcase_papers(papers):
    """Poster carousel rail + ItemList JSON-LD (all titles stay in HTML)."""
    cards = "".join(_showcase_card(i, p) for i, p in enumerate(papers))
    items = [{"@type": "ListItem", "position": i + 1,
              "url": "https://mynextpr.com/research/" + str(p.get("id")),
              "name": str(p.get("title"))}
             for i, p in enumerate(papers) if p.get("id") and p.get("title")]
    ld = {"@context": "https://schema.org", "@type": "ItemList",
          "name": "Running gait research behind RunForm",
          "itemListElement": items}
    return ("<h3 style='width:100%;color:var(--lime);font-size:13px;letter-spacing:.14em;margin:18px 0 2px'>"
            "02 &middot; THE PAPERS</h3>"
            "<div class=sc-railwrap>"
            "<div class=fade-viewport>"
            "<div class=fade-track id=fadeTrack role=region "
            "aria-label='Research studies' tabindex=0>" + cards + "</div>"
            "</div>"
            "<div class=fade-controls>"
            "<div class=fade-arrows>"
            "<button id=fadePrev aria-label='Previous studies'>&larr;</button>"
            "<button id=fadeNext aria-label='Next studies'>&rarr;</button></div>"
            "<p class=fade-pos id=fadePos><b>1</b> / " + str(len(papers)) + "</p>"
            "<div class=fade-dots id=fadeDots aria-label='Choose study'></div>"
            "</div></div>"
            "<script type='application/ld+json'>" + json.dumps(ld) + "</script>"
            "<script>" + SHOWCASE_JS + "</script>")


def research_page(slug):
    """Server-rendered study detail page. Returns HTML or None (unknown slug)."""
    by_id = _papers_by_id()
    p = by_id.get(slug)
    if not p:
        return None
    deep = _deep_by_catalog()
    d = deep.get(slug)
    title = str(p.get("title") or "Untitled")
    authors = ", ".join(str(a) for a in (p.get("authors") or []) if isinstance(a, str))
    journal = str(p.get("journal") or "")
    year = str(p.get("year") or "")
    link = _papers_link(p.get("link"))
    finding = str(p.get("key_finding") or "")
    zones = [z for z in (p.get("zones") or []) if isinstance(z, str)]
    cover = _papers_cover_url(slug)
    byline = " · ".join(b for b in (authors, journal, year) if b)
    desc = finding[:155]
    ld = {"@context": "https://schema.org", "@type": "ScholarlyArticle",
          "headline": title,
          "author": [{"@type": "Person", "name": a} for a in
                     (p.get("authors") or []) if isinstance(a, str)],
          "datePublished": str(year),
          "publisher": {"@type": "Organization", "name": "RunForm",
                        "url": "https://mynextpr.com/"},
          "about": [z.replace("_", " ") for z in zones],
          "description": finding,
          "sameAs": link,
          "mainEntityOfPage": "https://mynextpr.com/research/" + slug}
    if cover:
        ld["image"] = "https://mynextpr.com" + cover
    if d and d["doi"]:
        ld["sameAs"] = d["doi"]
    body = ["<main><div class=wrap>",
            "<nav aria-label='Breadcrumb'><p class=meta style='margin-top:0'>"
            "<a href='/'>RunForm</a> / <a href='/#science'>Research</a> / %s</p></nav>"
            % _html.escape(title),
            "<article>",
            "<h1>%s</h1>" % _html.escape(title),
            "<p class=sub>%s</p>" % _html.escape(byline),
            "<div class=sc-hero>"]
    if cover:
        body.append("<img class=sc-heroimg src='%s' alt='Monochrome cover art for: %s' width=600 height=800>"
                    % (_html.escape(cover, quote=True),
                       _html.escape(title, quote=True)))
    else:
        body.append("<div></div>")
    body.append("<div><h2 style='font-size:clamp(20px,2.6vw,26px);letter-spacing:-.02em;margin:0 0 8px'>"
                "The one-line finding</h2>"
                "<p class=sub style='margin:0'>%s</p>" % _html.escape(finding))
    if link:
        body.append("<p class=meta>Source: <a href='%s' rel=noopener>%s</a></p>"
                    % (_html.escape(link, quote=True), _html.escape(link)))
    zonechips = "".join(
        "<li><a href='/guide/%s'>%s &rarr;</a></li>"
        % (ZONE_GUIDES[z], _html.escape(z.replace("_", " ")))
        for z in zones if z in ZONE_GUIDES)
    for z in zones:
        if z not in ZONE_GUIDES:
            zonechips += "<li>%s</li>" % _html.escape(z.replace("_", " "))
    body.append("<h2 style='font-size:clamp(18px,2.4vw,24px);letter-spacing:-.02em;margin:22px 0 4px'>"
                "Which analysis rule it backs</h2>"
                "<ul class=sc-zones>" + zonechips + "</ul></div></div>")
    if d and d["summary"]:
        body.append("<section aria-label='Summary'><h2 style='font-size:clamp(20px,2.6vw,26px);"
                    "letter-spacing:-.02em;margin:30px 0 4px'>What the researchers did</h2>"
                    "<p class=sub style='margin:0'>%s</p>" % _html.escape(d["summary"]))
        if d["methods"]:
            body.append("<p class=meta>Methods signal: %s</p>" % _html.escape(d["methods"]))
        body.append("</section>")
        if d["how"]:
            zone = d["zone"].replace("_", " ")
            body.append("<section class=sc-backing aria-label='How it backs the analysis'>"
                        "<b>How it backs your %s score</b><p>%s</p></section>"
                        % (_html.escape(zone), _html.escape(d["how"])))
        if d["fig"]:
            body.append("<figure class=sc-fig><img src='%s' alt='%s' loading=lazy>"
                        "<figcaption>%s</figcaption></figure>"
                        % (_html.escape(d["fig"], quote=True),
                           _html.escape(d["caption"], quote=True),
                           _html.escape(d["caption"])))
        if d["snippet"]:
            body.append("<blockquote class=sc-quote><p>%s</p>"
                        "<footer>%s</footer></blockquote>"
                        % (_html.escape(d["snippet"]),
                           _html.escape(d["grounds"]) if d["grounds"] else ""))
    cite = (d["cite"] if d and d["cite"] else byline + ". " + title + ".")
    doilink = (d["doi"] if d and d["doi"] else (link if link and "doi.org" in link else ""))
    publink = (d["pubmed"] if d and d["pubmed"] else (link if link and "pubmed" in link else ""))
    citebtns = ""
    if doilink:
        citebtns += " <a class=btn ghost href='%s' rel=noopener>Read the DOI &rarr;</a>" \
            % _html.escape(doilink, quote=True)
    if publink:
        citebtns += " <a class=btn ghost href='%s' rel=noopener>PubMed &rarr;</a>" \
            % _html.escape(publink, quote=True)
    body.append("<section aria-label='Citation'><h2 style='font-size:clamp(20px,2.6vw,26px);"
                "letter-spacing:-.02em;margin:30px 0 4px'>Cite it</h2>"
                "<p class=sub style='margin:0'>%s</p><p>%s</p></section>"
                % (_html.escape(cite), citebtns))
    ids = [k for k in by_id]
    me = set(zones)
    rel = sorted(((len(me & set((by_id[k].get("zones") or []))), k) for k in ids
                  if k != slug and isinstance(by_id[k], dict)),
                 key=lambda t: (-t[0], ids.index(t[1])))[:3]
    relcards = ""
    for _, k in rel:
        rp = by_id[k]
        rc = _papers_cover_url(k)
        t = _html.escape(str(rp.get("title") or ""))
        if rc:
            relcards += ("<a class=sc-relcard href='/research/%s'>"
                         "<img src='%s' alt='' loading=lazy><b>%s</b></a>"
                         % (_html.escape(k), _html.escape(rc, quote=True), t))
        else:
            relcards += ("<a class=sc-relcard href='/research/%s'><b>%s</b></a>"
                         % (_html.escape(k), t))
    body.append("<section aria-label='Related studies'><h2 style='font-size:clamp(20px,2.6vw,26px);"
                "letter-spacing:-.02em;margin:30px 0 4px'>Related studies</h2>"
                "<div class=sc-rel>" + relcards + "</div></section>")
    pos = ids.index(slug)
    prevlink = ("<a href='/research/%s'>&larr; %s</a>"
                % (_html.escape(ids[pos - 1]),
                   _html.escape(str(by_id[ids[pos - 1]].get("title") or "")))) if pos > 0 else ""
    nextlink = ("<a href='/research/%s'>%s &rarr;</a>"
                % (_html.escape(ids[pos + 1]),
                   _html.escape(str(by_id[ids[pos + 1]].get("title") or "")))) \
        if pos < len(ids) - 1 else ""
    body.append("<nav class=sc-prevnext aria-label='More studies'>"
                "<span>%s</span><span>%s</span></nav>" % (prevlink, nextlink))
    body.append("<div class=card style='text-align:center'><p class=sub>"
                "See your own zones scored from one photo.</p>"
                "<a class=btn href='/#analyse'>Analyze my run &rarr;</a> "
                "<a class=quiet href='/report/aeb979a86e8b'>or see a sample report</a></div>")
    body.append("</article></div></main>")
    return ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>" + _html.escape(title) + " (" + _html.escape(year) + ") | RunForm Research</title>"
            "<meta name=description content='" + _html.escape(desc, quote=True) + "'>"
            "<link rel=canonical href='https://mynextpr.com/research/" + _html.escape(slug) + "'>"
            "<meta property='og:type' content='article'>"
            "<meta property='og:site_name' content='RunForm'>"
            "<meta property='og:title' content='" + _html.escape(title, quote=True) + " | RunForm Research'>"
            "<meta property='og:description' content='" + _html.escape(desc, quote=True) + "'>"
            "<meta property='og:url' content='https://mynextpr.com/research/" + _html.escape(slug) + "'>"
            + ("<meta property='og:image' content='https://mynextpr.com" + _html.escape(cover, quote=True) + "'>"
               if cover else
               "<meta property='og:image' content='https://mynextpr.com/assets/og-image.jpg'>")
            + "<meta name=twitter:card content='summary_large_image'>"
            "<script type='application/ld+json'>" + json.dumps(ld) + "</script>"
            + CSS + SHOWCASE_CSS + GA_SNIPPET +
            "<script src=/assets/dots.js defer></script></head><body><canvas id=dots-bg></canvas>"
            "<div class=nav><span class=brand><img class=blogo src='/assets/logo.png' alt='RunForm logo' width=30 height=30>RunForm</span>"
            "<a class=navlink href='/#science'>All 11 studies &rarr;</a></div>"
            + "".join(body) + "</body></html>")


def _science_html():
    papers, cat = _papers_catalog()
    deep = _deep_entries()
    if not papers and not deep:
        return ""
    parts = ["<section class='wrap steps' id=science>",
             "<h2 style='width:100%;font-size:clamp(22px,3vw,32px);letter-spacing:-.02em;margin:26px 0 4px'>"
             "Every score is backed by published research</h2>"]
    n = len(papers)
    ver = _html.escape(str(cat.get("version") or ""))
    upd = _html.escape(str(cat.get("updated") or ""))
    stamp = " · ".join(s for s in (
        "%d papers" % n if n else "",
        "catalog v%s" % ver if ver else "",
        "updated %s" % upd if upd else "") if s)
    parts.append(
        "<p class=sub style='width:100%'>Not vibes, not hallucinated advice — "
        "every zone we score traces to at least one of these studies."
        + (" (%s.)" % stamp if stamp else "") + "</p>")
    if deep:
        parts.append(
            "<h3 style='width:100%;color:var(--lime);font-size:13px;letter-spacing:.14em;margin:18px 0 2px'>"
            "01 &middot; DEEP DIVES</h3>")
        parts.extend(_deep_card(e) for e in deep)
    if papers:
        if any(_papers_cover_url(str(p.get("id") or "")) for p in papers
               if isinstance(p, dict)):
            parts.append(SHOWCASE_CSS)
            parts.append(_showcase_papers(papers))
        else:
            parts.append(
                "<h3 style='width:100%;color:var(--lime);font-size:13px;letter-spacing:.14em;margin:18px 0 2px'>"
                "02 &middot; THE PAPERS</h3>")
            parts.extend(c for c in (_papers_card(p) for p in papers) if c)
    parts.append("</section>")
    return "".join(parts)


try:
    SCIENCE_HTML = _science_html()
except Exception:
    SCIENCE_HTML = ""
if not SCIENCE_HTML:
    print("WARNING: research papers store missing — landing science section off",
          flush=True)


LANDING_JS = (
  "(function(){"
  "var form=document.getElementById('upForm'),file=document.getElementById('file'),drop=document.getElementById('drop'),go=document.getElementById('go'),title=document.getElementById('dropTitle'),sub=document.getElementById('dropSub'),prev=document.getElementById('preview');"
  "function show(f){ if(!f) return; title.textContent=f.name; sub.textContent=(Math.round(f.size/1024))+' KB · ready to analyse'; drop.classList.add('has'); go.classList.add('ready'); try{ prev.src=URL.createObjectURL(f); }catch(x){} }"
  "file.addEventListener('change',function(){ show(file.files[0]); });"
  "['dragenter','dragover'].forEach(function(ev){ drop.addEventListener(ev,function(e){ e.preventDefault(); drop.classList.add('over'); }); });"
  "['dragleave','drop'].forEach(function(ev){ drop.addEventListener(ev,function(e){ e.preventDefault(); drop.classList.remove('over'); }); });"
  "drop.addEventListener('drop',function(e){ if(e.dataTransfer&&e.dataTransfer.files.length){ try{ file.files=e.dataTransfer.files; }catch(x){} show(e.dataTransfer.files[0]); } });"
  "form.addEventListener('submit',function(e){ if(!file.files.length){ e.preventDefault(); drop.classList.add('over'); title.textContent='Choose a photo first'; return; } go.textContent='Building your runner…'; go.style.pointerEvents='none'; go.style.opacity='.75'; });"
  "var ct=document.getElementById('ctaBtn'); if(ct) ct.addEventListener('click',function(e){ e.preventDefault(); var a=document.getElementById('analyse'); if(a) a.scrollIntoView({behavior:'smooth'}); });"
  "var sv=document.getElementById('showcaseVid'),sb=document.getElementById('soundToggle'); if(sv){ var kick=function(){ try{ var p=sv.play(); if(p&&p.catch)p.catch(function(){}); }catch(x){} }; if(document.readyState==='complete')kick(); else window.addEventListener('load',kick); if('IntersectionObserver' in window){ var io=new IntersectionObserver(function(es){ es.forEach(function(e){ if(e.isIntersecting&&sv.paused&&sv.muted)kick(); }); },{threshold:0.3}); io.observe(sv); } }"
  "if(sb&&sv) sb.addEventListener('click',function(){ if(sv.muted){ sv.muted=false; sv.currentTime=0; sv.play(); sb.textContent='Mute'; } else { sv.muted=true; sb.textContent='Watch with sound'; } });"
  "var rt=document.getElementById('rateToggle'); if(rt&&sv) rt.addEventListener('click',function(){ var r=sv.playbackRate||1; r=(r>=2)?1:(r>=1.5?2:1.5); sv.playbackRate=r; rt.innerHTML=(r+'&times;').replace('.5','.5'); });"
  "var hb=document.getElementById('heroBg'),sc=document.querySelector('.scrollcue');function heroScroll(){var y=window.scrollY||window.pageYOffset||0,h=window.innerHeight||800,k=Math.min(1,y/(h*0.85));if(hb){hb.style.opacity=(1-k*0.95).toFixed(3);hb.style.transform='translate3d(0,'+Math.round(y*0.22)+'px,0)';}if(sc)sc.style.opacity=Math.max(0,1-k*2.5).toFixed(3);}window.addEventListener('scroll',heroScroll,{passive:true});heroScroll();"
  "})();"
)

LANDING = ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
           "<title>Running Form Analysis in 3D | RunForm</title>"
           "<meta name=description content='" + META_DESC + "'>"
           "<link rel=canonical href='https://mynextpr.com/'>"
           "<meta name=theme-color content='#0a0c11'>"
           "<link rel=icon href='/assets/favicon.ico' sizes='any'>"
           "<link rel=icon type='image/png' href='/assets/logo.png'>"
           "<link rel=apple-touch-icon href='/assets/apple-touch-icon.png'>"
           "<meta property='og:type' content='website'>"
           "<meta property='og:site_name' content='RunForm'>"
           "<meta property='og:title' content='Running Form Analysis in 3D | RunForm'>"
           "<meta property='og:description' content='" + OG_DESC + "'>"
           "<meta property='og:url' content='https://mynextpr.com/'>"
           "<meta property='og:image' content='https://mynextpr.com/assets/og-image.jpg'>"
           "<meta property='og:image:width' content='1200'>"
           "<meta property='og:image:height' content='630'>"
           "<meta property='og:image:alt' content='RunForm logo — a runner in motion'>"
           "<meta name=twitter:card content='summary_large_image'>"
           "<meta name=twitter:title content='Running Form Analysis in 3D | RunForm'>"
           "<meta name=twitter:description content='" + OG_DESC + "'>"
           "<meta name=twitter:image content='https://mynextpr.com/assets/og-image.jpg'>"
           "<script type='application/ld+json'>{\"@context\":\"https://schema.org\",\"@graph\":[{\"@type\":\"Organization\",\"name\":\"RunForm\",\"url\":\"https://mynextpr.com/\",\"logo\":\"https://mynextpr.com/assets/logo.png\"},{\"@type\":\"WebApplication\",\"name\":\"RunForm\",\"url\":\"https://mynextpr.com/\",\"applicationCategory\":\"HealthApplication\",\"operatingSystem\":\"Any\",\"offers\":{\"@type\":\"Offer\",\"price\":\"0\"},\"description\":\"Analyze your running form from one photo: AI form score, zone-by-zone flaws, fixes and drills, plus a 3D model of your stride.\"},{\"@type\":\"FAQPage\",\"mainEntity\":[{\"@type\":\"Question\",\"name\":\"What is running form?\",\"acceptedAnswer\":{\"@type\":\"Answer\",\"text\":\"Running form is how your body moves when you run — posture, foot strike, knee drive, arm swing and lean. Small flaws raise injury risk and waste energy.\"}},{\"@type\":\"Question\",\"name\":\"Can running form really be analyzed from a single photo?\",\"acceptedAnswer\":{\"@type\":\"Answer\",\"text\":\"Yes for visible mechanics — foot strike, overstride, lean, knee drive, arm swing, head and hip alignment, each judged view- and phase-dependently. What a photo cannot show — cadence, contact time, bounce, forces — needs video or sensors, so it is never guessed.\"}},{\"@type\":\"Question\",\"name\":\"How can I analyze my running form from a photo?\",\"acceptedAnswer\":{\"@type\":\"Answer\",\"text\":\"Upload one side-profile running photo. RunForm scores each form zone with AI and rebuilds you in 3D so you can see every flaw and fix.\"}},{\"@type\":\"Question\",\"name\":\"How do I stop overstriding?\",\"acceptedAnswer\":{\"@type\":\"Answer\",\"text\":\"Land with the foot under the hips instead of reaching ahead: lift cadence slightly, run quieter, stop reaching. Cue: land under hips, quiet feet.\"}},{\"@type\":\"Question\",\"name\":\"Is heel striking bad?\",\"acceptedAnswer\":{\"@type\":\"Answer\",\"text\":\"Not by itself — most runners, even elites, land rearfoot. The red flag is heel strike plus overstride, a locked knee and low cadence, which together create braking force. Isolated rearfoot contact under the body is acceptable.\"}},{\"@type\":\"Question\",\"name\":\"What running cadence should I aim for?\",\"acceptedAnswer\":{\"@type\":\"Answer\",\"text\":\"Forget 180 as a magic number — ideal cadence is individual. The evidence-backed move is raising cadence 5–10% above your own preferred rate, which cuts hip and knee loading.\"}},{\"@type\":\"Question\",\"name\":\"How do I improve my running form?\",\"acceptedAnswer\":{\"@type\":\"Answer\",\"text\":\"Work one zone at a time with a cue and a drill — e.g. land with your foot under your hip, then practice with short strides. Re-test with a new photo.\"}},{\"@type\":\"Question\",\"name\":\"What is a good running form score?\",\"acceptedAnswer\":{\"@type\":\"Answer\",\"text\":\"Most recreational runners score 55-75 out of 100. Anything under 60 usually means two or more zones need drills.\"}},{\"@type\":\"Question\",\"name\":\"How is my score calculated?\",\"acceptedAnswer\":{\"@type\":\"Answer\",\"text\":\"Each visible zone scores 0–100 (optimal 85+, fair 60–84, critical below 60) and the overall is the rounded average. Guardrails keep it honest: any critical zone caps the total at 70, two or more cap it at 60.\"}},{\"@type\":\"Question\",\"name\":\"What research is this based on?\",\"acceptedAnswer\":{\"@type\":\"Answer\",\"text\":\"Systematic reviews on running-injury biomechanics (Willwacher 2022; Ceyssens 2019), the evidence-based video-analysis framework (Souza 2016), cadence-loading studies (Heiderscheit 2011), and foot-strike work (Lieberman; Cavanagh and Lafortune; Xu 2021).\"}},{\"@type\":\"Question\",\"name\":\"What can't a photo measure?\",\"acceptedAnswer\":{\"@type\":\"Answer\",\"text\":\"Cadence, ground-contact time, vertical bounce, loading rate, leg stiffness and pronation speed all need time-series, video or force data — so they are never guessed from your photo, only prescribed as drills where the evidence supports them.\"}},{\"@type\":\"Question\",\"name\":\"Does overstriding cause injuries?\",\"acceptedAnswer\":{\"@type\":\"Answer\",\"text\":\"Overstride mechanics feed hamstring strain and raise tibial loading, and high loading rates are tied to stress fractures — which is why braking force, not foot strike alone, is what gets flagged.\"}}]}]}</script>" + GA_SNIPPET + CSS + LANDING_CSS_ADD +
           "<script src=/assets/dots.js defer></script></head><body><canvas id=dots-bg></canvas>"
           "<div class=nav><span class=brand><img class=blogo src='/assets/logo.png' alt='RunForm logo' width=30 height=30>RunForm</span><a class=navlink href='/report/aeb979a86e8b'>See the sample report &rarr;</a></div>"
           "<main>"
           "<section class=fold id=top>"
           "<div class=hero-bg id=heroBg><video src='/assets/hero-run.mp4' poster='/assets/hero-run.jpg' autoplay muted loop playsinline preload=metadata></video><div class=hero-shade></div></div>"
           "<div class=glow></div>"
           "<div class='wrap fold-grid'>"
           "<div class=fold-copy>" +
           HERO_H1 +
           HERO_LEAD +
           "<div class=cta-row><a href='#analyse' id=ctaBtn class=btn>Analyze my run &rarr;</a>"
           "<a class=ghostlink href='/report/aeb979a86e8b'>or see a sample report</a></div>" +
           HERO_TRUST +
           "</div>"
           "<div class=scrollcue>scroll</div>"
           "</section>" +
           PROOF_HTML +
           "<section class='wrap section2' id=analyse>"
           "<div class=showvid>"
           "<video id=showcaseVid src='/assets/showcase.mp4' poster='/assets/showcase-poster.jpg' autoplay muted playsinline preload=metadata></video>"
           "<span class=vidtag>Real runner &middot; score 69</span>"
           "<button id=soundToggle class=soundbtn type=button>Watch with sound</button>"
           "<button id=rateToggle class=soundbtn type=button style='left:auto;right:14px;transform:none' aria-label='Playback speed'>1&times;</button>"
           "</div>"
           "<div class=uploadcol>"
           "<h2>Try it on your run</h2>"
           "<p class=lead2>Drop a side-profile running photo and we&rsquo;ll rebuild you in 3D and score every zone.</p>"
           "<form id=upForm method=post action=/api/jobs enctype='multipart/form-data'>"
           "<label id=drop class=drop for=file><input id=file type=file name=photo accept='image/jpeg,image/png,image/webp' hidden>"
           "<img id=preview class=preview alt='your run photo'>"
           "<span class=drop-ic>&#11014;</span><b id=dropTitle>Drop your run photo</b>"
           "<span id=dropSub>or tap to browse &middot; side-profile, mid-stride &middot; JPEG/PNG/WebP &le; 8 MB</span></label>"
           "<button id=go class=btn type=submit style='margin-top:16px;width:100%'>Analyse my run &rarr;</button>"
           "</form>" +
           UPLOAD_META +
           "</div>"
           "</section>" +
           SCIENCE_HTML +
           "<section class='wrap steps lu-steps'>" +
           STEPS_HEAD +
           "<div class=step><b>1 &middot; Upload</b><p>One side-profile running photo. Nothing to install.</p></div>"
           "<div class=step><b>2 &middot; Analyse + build</b><p>Gemini scores your form; the cloud rebuilds you in textured 3D with every zone marked.</p></div>"
           "<div class=step><b>3 &middot; Explore</b><p>A coach walkthrough with captions, then spin the model and tap any zone.</p></div>"
           "</section>" +
           PRIVACY_HTML +
           "<section class='wrap steps' id=faq>"
           "<h2 style='width:100%;font-size:clamp(22px,3vw,32px);letter-spacing:-.02em;margin:26px 0 4px'>Running form questions, answered</h2>"
           "<p class=sub style='width:100%'>Twelve answers from our biomechanics evidence audit — the same research our scoring is built on.</p>"
           "<h3 style='width:100%;color:var(--lime);font-size:13px;letter-spacing:.14em;margin:18px 0 2px'>03 &middot; THE BASICS</h3>"
           "<div class=step><b>What is running form?</b><p>Running form is how your body moves when you run &mdash; posture, foot strike, knee drive, arm swing and lean. Small flaws raise injury risk and waste energy.</p></div>"
           "<div class=step><b>Can running form really be analyzed from a single photo?</b><p>Yes for visible mechanics &mdash; foot strike, overstride, lean, knee drive, arm swing, head and hip alignment, each judged view- and phase-dependently. What a photo cannot show &mdash; cadence, contact time, bounce, forces &mdash; needs video or sensors, so it is never guessed.</p></div>"
           "<div class=step><b>How can I analyze my running form from a photo?</b><p>Upload one side-profile running photo. RunForm scores each form zone with AI and rebuilds you in 3D so you can see every flaw and fix.</p></div>"
           "<h3 style='width:100%;color:var(--lime);font-size:13px;letter-spacing:.14em;margin:18px 0 2px'>04 &middot; FIX YOUR ZONES</h3>"
           "<div class=step><b>How do I stop overstriding?</b><p>Land with the foot under the hips instead of reaching ahead: lift cadence slightly, run quieter, stop reaching. Cue: land under hips, quiet feet. <a href='/guide/stop-overstriding'>Full overstriding guide &rarr;</a></p></div>"
           "<div class=step><b>Is heel striking bad?</b><p>Not by itself &mdash; most runners, even elites, land rearfoot. The red flag is heel strike <i>plus</i> overstride, a locked knee and low cadence, which together create braking force. Isolated rearfoot contact under the body is acceptable. <a href='/guide/stop-overstriding'>Foot-strike guide &rarr;</a></p></div>"
           "<div class=step><b>What running cadence should I aim for?</b><p>Forget 180 as a magic number &mdash; ideal cadence is individual. The evidence-backed move is raising cadence 5&ndash;10% above your own preferred rate, which cuts hip and knee loading. <a href='/guide/increase-running-cadence'>Cadence guide &rarr;</a></p></div>"
           "<div class=step><b>How do I improve my running form?</b><p>Work one zone at a time with a cue and a drill &mdash; e.g. land with your foot under your hip, then practice with short strides. Re-test with a new photo. <a href='/guides/'>All 7 zone guides &rarr;</a></p></div>"
           "<h3 style='width:100%;color:var(--lime);font-size:13px;letter-spacing:.14em;margin:18px 0 2px'>05 &middot; SCORES</h3>"
           "<div class=step><b>What is a good running form score?</b><p>Most recreational runners score 55-75 out of 100. Anything under 60 usually means two or more zones need drills.</p></div>"
           "<div class=step><b>How is my score calculated?</b><p>Each visible zone scores 0&ndash;100 (optimal 85+, fair 60&ndash;84, critical below 60) and the overall is the rounded average. Guardrails keep it honest: any critical zone caps the total at 70, two or more cap it at 60.</p></div>"
           "<h3 style='width:100%;color:var(--lime);font-size:13px;letter-spacing:.14em;margin:18px 0 2px'>06 &middot; THE SCIENCE</h3>"
           "<div class=step><b>What research is this based on?</b><p>Systematic reviews on running-injury biomechanics (Willwacher 2022; Ceyssens 2019), the evidence-based video-analysis framework (Souza 2016), cadence-loading studies (Heiderscheit 2011), and foot-strike work (Lieberman; Cavanagh &amp; Lafortune; Xu 2021). Key papers: <a href='https://pubmed.ncbi.nlm.nih.gov/20581720/'>cadence &amp; joint loading</a> &middot; <a href='https://pubmed.ncbi.nlm.nih.gov/26616185/'>video analysis framework</a> &middot; <a href='https://pubmed.ncbi.nlm.nih.gov/32813597/'>foot-strike meta-analysis</a> &middot; <a href='https://pubmed.ncbi.nlm.nih.gov/35247202/'>biomechanical risk factors</a>.</p></div>"
           "<div class=step><b>What can't a photo measure?</b><p>Cadence, ground-contact time, vertical bounce, loading rate, leg stiffness and pronation speed all need time-series, video or force data &mdash; so they are never guessed from your photo, only prescribed as drills where the evidence supports them.</p></div>"
           "<div class=step><b>Does overstriding cause injuries?</b><p>Overstride mechanics feed hamstring strain and raise tibial loading, and high loading rates are tied to stress fractures &mdash; which is why braking force, not foot strike alone, is what gets flagged. <a href='/guide/stop-overstriding'>Fix overstriding &rarr;</a></p></div>"
           "</section>" +
           "</main>"
           "<script>" + LANDING_JS + "</script>"
           "</body></html>")

LOGIN = ("<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
         "<title>RunForm — guest login</title><meta name=robots content='noindex,nofollow'>" + CSS + GA_SNIPPET + "<script src=/assets/dots.js defer></script></head><body><canvas id=dots-bg></canvas><div class=wrap>"
         "<h1>Log in <span class=lime>as guest.</span></h1>"
         "<p class=sub>No password, no email. One click gives you a demo session on this machine.</p>"
         "<div class=card><form method=post action=/login>"
         "<button class=btn type=submit name=guest value=1>Continue as guest →</button>"
         "</form><p class=meta>Demo only: the session lives in server memory and vanishes on restart.</p></div>"
         "</div></body></html>")

UPLOAD = ("<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
          "<title>RunForm — upload</title><meta name=robots content='noindex,nofollow'>" + CSS + GA_SNIPPET + "<script src=/assets/dots.js defer></script></head><body><canvas id=dots-bg></canvas><div class=wrap>"
          "<h1>Upload <span class=lime>your run.</span></h1>"
          "<p class=sub>A side-profile shot, mid-stride if you have one. Processing takes about 2 minutes.</p>"
          "<div class=card><form method=post action=/api/jobs enctype=multipart/form-data>"
          "<input type=file name=photo accept='image/jpeg,image/png,image/webp' required><br>"
          "<button class=btn type=submit>Analyze my form →</button>"
          "</form><p class=meta>JPEG/PNG/WebP up to 8 MB. Sent to Gemini for scoring and Tripo for the 3D rebuild; runs stay private to your session and deletable from history.</p></div>"
          "</div></body></html>")

JOB_PAGE = ("<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>RunForm — building your runner</title><meta name=robots content='noindex,nofollow'>" + CSS + GA_SNIPPET +
            "<script src='https://unpkg.com/three@0.147.0/build/three.min.js'></script>"
            "<style>#loadwrap{position:relative;width:280px;height:280px;margin:10px auto}"
            "#loadwrap canvas{position:absolute;inset:0}"
            "#pct{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:44px;font-weight:800;color:var(--ink)}"
            "#pct small{font-size:15px;color:var(--dim);font-weight:400;margin-left:3px}"
            ".stages{list-style:none;margin:18px 0 0;padding:0;font-size:14px}"
            ".stages li{padding:7px 0;color:var(--dim);display:flex;gap:10px;align-items:center}"
            ".stages li.on{color:var(--ink)}.stages li.done{color:var(--lime)}"
            ".stages li .mk{width:18px;text-align:center}"
            ".kabir{display:flex;gap:12px;align-items:flex-start;background:var(--panel2);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:14px 0 0;text-align:left}"
            ".kabir img{width:44px;height:44px;border-radius:50%;object-fit:cover;border:1px solid var(--line2);flex:0 0 44px}"
            ".kabir .who{font-size:12px;color:var(--lime);font-weight:700;letter-spacing:.06em}"
            ".kabir .line{font-size:14.5px;line-height:1.5;margin:2px 0 0}"
            ".tcards{list-style:none;margin:14px 0 0;padding:0;display:flex;flex-direction:column;gap:8px}"
            ".tcard{background:#0f141b;border:1px solid var(--line);border-radius:12px;overflow:hidden}"
            ".tcard>button{all:unset;display:flex;gap:12px;align-items:center;width:100%;padding:6px 12px;min-height:52px;cursor:pointer;color:var(--dim);font-size:14px}"
            ".tcard>button:focus-visible{outline:3px solid var(--lime);outline-offset:-3px}"
            ".tcard .mk{width:26px;height:26px;flex:0 0 26px;border-radius:50%;border:1.5px solid var(--line2);display:inline-flex;align-items:center;justify-content:center;font-size:13px}"
            ".tcard .tx{flex:1;min-width:0}.tcard .tx b{display:block;font-size:14px;color:var(--ink)}"
            ".tcard .tx span{font-size:12px;color:var(--dim)}"
            ".tcard .chev{color:var(--faint);font-size:12px}"
            ".tcard .tbody{display:none;padding:0 14px 12px 50px;font-size:13px;color:var(--dim);line-height:1.55}"
            ".tcard.open .tbody{display:block}.tcard.open .chev{transform:rotate(180deg);display:inline-block}"
            ".tcard.on{border-color:#3a4a2e;background:#121a0e}.tcard.on>button{color:var(--ink)}.tcard.on .mk{border-color:var(--lime);color:var(--lime)}"
            ".tcard.done .mk{border-color:var(--lime);background:var(--lime);color:#0e1206}"
            ".tcard.done .tx span{color:var(--lime)}"
            ".rail{margin:14px 0 0;background:#0f141b;border:1px solid var(--line);border-radius:12px;padding:12px 14px;text-align:left}"
            ".rail .rhead{font-size:12px;color:var(--faint);margin-bottom:8px}"
            ".rail a{display:flex;gap:12px;align-items:center;text-decoration:none;color:var(--ink)}"
            ".rail img{width:64px;height:64px;border-radius:10px;object-fit:cover;border:1px solid var(--line2);background:#10151c;flex:0 0 64px}"
            ".rail b{display:block;font-size:13.5px;line-height:1.4}.rail span{display:block;font-size:12px;color:var(--dim);margin-top:3px}"
            "@media(prefers-reduced-motion:reduce){.tcard .tbody{transition:none}}</style>"
            "<script src=/assets/dots.js defer></script></head><body><canvas id=dots-bg></canvas><div class=wrap style='text-align:center'>"
            "<h1>Building <span class=lime>your runner…</span></h1>"
            "<p class=sub>Gemini audits your form while the cloud rebuilds your body in 3D.</p>"
            "<div class=card style='text-align:left'>"
            "<div id=thumbrow style='display:flex;gap:12px;align-items:center;margin-bottom:6px'>"
            "<img id=thumb alt='your upload' style='width:64px;height:64px;object-fit:cover;border-radius:10px;border:1px solid #1e2630;background:#10151c'>"
            "<div><div id=fname style='font-size:14px;font-weight:700;word-break:break-all'>preparing…</div>"
            "<div id=timer class=meta style='margin-top:2px'>elapsed 0:00</div></div></div>"
            "<div id=loadwrap><canvas id=lc width=560 height=560 style='width:280px;height:280px'></canvas>"
            "<div id=pct>0<small>%</small></div></div>"
            "<div class=kabir id=kabir><img src=/assets/coach-kabeer.jpg alt='Coach Kabeer' onerror='this.style.display=\"none\"'>"
            "<div><div class=who>Kabeer · your running coach</div><p class=line id=kabirline>Getting your run ready…</p></div></div>"
            "<ul class=tcards id=stages>"
            "<li class=tcard data-s=queued><button aria-expanded=false><span class=mk>·</span><span class=tx><b>Queued</b><span class=st>Waiting for a worker</span></span><span class=chev>▾</span></button>"
            "<div class=tbody>Your photo is uploaded and sanitized. One job runs at a time — yours starts the moment the worker is free.</div></li>"
            "<li class=tcard data-s=analyzing><button aria-expanded=false><span class=mk>·</span><span class=tx><b>Form audit</b><span class=st>Scoring zones</span></span><span class=chev>▾</span></button>"
            "<div class=tbody>Each visible zone is scored against published gait research. Anything the photo cannot show is marked needs-view — never guessed.</div></li>"
            "<li class=tcard data-s=meshing><button aria-expanded=false><span class=mk>·</span><span class=tx><b>3D rebuild</b><span class=st>Growing the mesh</span></span><span class=chev>▾</span></button>"
            "<div class=tbody>The cloud grows your textured mesh while the audit seals. The percent in the globe is the live cloud build.</div></li>"
            "<li class=tcard data-s=done><button aria-expanded=false><span class=mk>·</span><span class=tx><b>Bake</b><span class=st>Score + report ready</span></span><span class=chev>▾</span></button>"
            "<div class=tbody>Score sealed — baking your studio with markers, tour and voice walkthrough.</div></li></ul>"
            "<div class=rail id=rail style='display:none'><div class=rhead>Research cross-check — the papers scoring you</div><div id=paperrail></div></div>"
            "<p class=meta id=detail></p><p class=meta>job <span id=jid style='font-family:monospace'></span> &middot; <a id=loginwait href=/login>log in while you wait — we'll keep your spot</a></p>"
            "<p class=meta id=ncdn style='display:none'>3D preview offline (CDN blocked) — progress continues below.</p>"
            "<p><button class=btn ghost id=cancel style='background:transparent;color:var(--ink);border:1px solid #2e3945;margin:6px 0 0'>Cancel watch</button> "
            "<button class=btn ghost id=retry style='display:none;background:transparent;color:var(--ink);border:1px solid #2e3945;margin:6px 0 0 8px'>Retry</button></p></div>"
            "<script>var JID=__JID__;"
            "document.getElementById('jid').textContent=JID;"
            "document.getElementById('loginwait').href='/login?next='+encodeURIComponent('/job/'+JID);"
            "var T={queued:4,analyzing:30,meshing:93,done:100,failed:100};"
            "var shown=0,target=4,term=false;"
            "var t0=Date.now();"
            "document.getElementById('thumb').src='/jobs/'+JID+'/input.jpg';"
            "document.getElementById('thumb').onerror=function(){this.style.display='none';};"
            "var rail=document.getElementById('rail'),pr=document.getElementById('paperrail');"
            "try{if(rail&&pr&&window.fetch){fetch('/research/papers/catalog.json').then(function(r){return r.ok?r.json():null;}).then(function(c){"
            "if(!c||!c.papers)return;var ps=c.papers.filter(function(p){return p&&p.id&&p.title&&p.thumb;});if(!ps.length)return;"
            "var i=0;function show(){var p=ps[i%ps.length];pr.innerHTML='';"
            "var a=document.createElement('a');a.href='/research/'+encodeURIComponent(p.id);"
            "var img=document.createElement('img');img.alt='';img.src='/research/papers/thumbs/'+String(p.thumb).split('/').pop();"
            "img.onerror=function(){this.style.display='none';};"
            "var d=document.createElement('div');var b=document.createElement('b');b.textContent=p.title;"
            "var s=document.createElement('span');s.textContent=((p.authors||[]).join(', ')||p.journal||'')+(p.year?' · '+p.year:'');"
            "d.appendChild(b);d.appendChild(s);a.appendChild(img);a.appendChild(d);pr.appendChild(a);"
            "rail.style.display='block';i++;}"
            "show();var rm=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;"
            "if(!rm&&ps.length>1)setInterval(show,7000);}).catch(function(){});}}catch(e){}"
            "setInterval(function(){var s=Math.floor((Date.now()-t0)/1000);"
            "document.getElementById('timer').textContent='elapsed '+Math.floor(s/60)+':'+('0'+(s%60)).slice(-2);},1000);"
            "var cv=document.getElementById('lc');var has3d=(typeof THREE!=='undefined');"
            "if(!has3d){cv.style.display='none';document.getElementById('ncdn').style.display='block';}"
            "var rn=null,sc=null,ca=null,mesh=null,core=null;"
            "if(has3d){try{"
            "rn=new THREE.WebGLRenderer({canvas:cv,alpha:true,antialias:true});"
            "rn.setSize(560,560,false);"
            "sc=new THREE.Scene();"
            "ca=new THREE.PerspectiveCamera(40,1,0.1,50);ca.position.set(0,0,4.2);"
            "sc.add(new THREE.HemisphereLight(0xffffff,0x3a4350,1.2));"
            "var kl=new THREE.DirectionalLight(0xffffff,1.4);kl.position.set(2,3,2.5);sc.add(kl);"
            "mesh=new THREE.Mesh(new THREE.IcosahedronGeometry(1.25,2),"
            "new THREE.MeshStandardMaterial({color:0x4F7CFF,wireframe:true,transparent:true,opacity:0.9}));"
            "sc.add(mesh);"
            "core=new THREE.Mesh(new THREE.IcosahedronGeometry(0.5,1),"
            "new THREE.MeshBasicMaterial({color:0xc8f04a,wireframe:true,transparent:true,opacity:0.55}));"
            "sc.add(core);}catch(e){has3d=false;cv.style.display='none';document.getElementById('ncdn').style.display='block';}}"
            "function tick(){requestAnimationFrame(tick);"
            "if(Math.abs(target-shown)>0.05){shown+=(target-shown)*0.045;}"
            "else if(shown!==target){shown=target;}"
            "document.getElementById('pct').innerHTML=Math.floor(shown)+'<small>%</small>';"
            "if(!has3d||!rn)return;"
            "mesh.rotation.y+=0.008;mesh.rotation.x+=0.003;core.rotation.y-=0.012;"
            "var s=1+Math.sin(Date.now()/600)*0.03;mesh.scale.set(s,s,s);"
            "rn.render(sc,ca);}"
            "tick();"
            "var KL={queued:'You are in the queue — I will get your run file ready.',"
            "analyzing:'I am reviewing your stride, zone by zone, against published gait research.',"
            "meshing:'Rebuilding you in 3D while I double-check the tricky zones.',"
            "done:'Your studio is ready — let us walk through it together.',"
            "failed:'This run hit a snag. The note below says what — retry when ready.'};"
            "var lastStage='';"
            "function setKabir(stage){var l=document.getElementById('kabirline');if(l&&KL[stage])l.textContent=KL[stage];}"
            "function mark(stage){if(stage==='failed'){if(stage!==lastStage){lastStage=stage;setKabir(stage);}return;}"
            "var L=document.querySelectorAll('#stages li');"
            "var order=['queued','analyzing','meshing','done'];"
            "for(var i=0;i<L.length;i++){var s=L[i].getAttribute('data-s');"
            "var mk=L[i].querySelector('.mk');var btn=L[i].querySelector('button');"
            "if(s===stage){L[i].className='tcard on';mk.textContent='◌';}"
            "else if(order.indexOf(s)<order.indexOf(stage)||stage==='done'){L[i].className='tcard done';mk.textContent='✓';}"
            "else{L[i].className='tcard';mk.textContent='·';}"
            "if(stage!==lastStage){var open=s===stage;L[i].classList.toggle('open',open);if(btn)btn.setAttribute('aria-expanded',open?'true':'false');}}"
            "if(stage!==lastStage){lastStage=stage;setKabir(stage);}}"
            "document.querySelectorAll('#stages .tcard>button').forEach(function(b){b.addEventListener('click',function(){"
            "var li=b.parentNode;var open=li.classList.toggle('open');b.setAttribute('aria-expanded',open?'true':'false');});});"
            "var fails=0,cancelled=false;"
            "document.getElementById('cancel').onclick=function(){cancelled=true;"
            "document.getElementById('detail').textContent='Watch cancelled — your run continues in background. Re-open this page to keep watching.';"
            "document.getElementById('retry').style.display='inline-block';this.style.display='none';};"
            "document.getElementById('retry').onclick=function(){cancelled=false;fails=0;term=false;"
            "this.style.display='none';document.getElementById('cancel').style.display='inline-block';"
            "document.getElementById('detail').textContent='Reconnecting…';poll();};"
            "function poll(){if(term||cancelled)return;fetch('/api/jobs/'+JID).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(j){"
            "fails=0;"
            "target=(j.stage==='meshing'&&j.progress)?(30+j.progress*0.65):(T[j.stage]||4);mark(j.stage);"
            "if(j.stage==='meshing'){var mm=document.querySelector('#stages li[data-s=meshing] .st');if(mm)mm.textContent=j.progress?('Cloud build '+j.progress+'%'):'Growing the mesh';}"
            "if(j.filename)document.getElementById('fname').textContent=j.filename;else document.getElementById('fname').textContent='run '+JID;"
            "if(j.detail)document.getElementById('detail').textContent=j.detail;"
            "if(j.stage==='done'){term=true;shown=100;"
            "document.getElementById('pct').innerHTML=\"100<small>%</small>\";"
            "document.getElementById('detail').textContent='Score '+j.score+' — opening your finished studio…';"
            "setTimeout(function(){location.href='/report/'+JID;},1200);}"
            "if(j.stage==='failed'){term=true;"
            "document.getElementById('detail').textContent='Failed: '+(j.error||'unknown');"
            "document.getElementById('retry').style.display='inline-block';}"
            "else setTimeout(poll,2000);"
            "}).catch(function(){fails++;var wait=Math.min(15000,2000*Math.pow(2,fails-1));"
            "document.getElementById('detail').textContent='Reconnecting… (try '+fails+', retry in '+Math.round(wait/1000)+'s)';"
            "setTimeout(poll,wait);});}poll();</script></div></body></html>")


ROBOTS = "User-agent: *\nAllow: /\nSitemap: https://mynextpr.com/sitemap.xml\n"

def sitemap_xml():
    return ("<?xml version='1.0' encoding='UTF-8'?>"
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
            "<url><loc>https://mynextpr.com/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>"
            "<url><loc>https://mynextpr.com/report/aeb979a86e8b</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>"
            "<url><loc>https://mynextpr.com/guides/</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>"
            + "".join("<url><loc>https://mynextpr.com/guide/%s</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>" % s
                      for s in GUIDES) +
            "".join("<url><loc>https://mynextpr.com/research/%s</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>" % k
                    for k in sorted(_papers_by_id())) +
            "</urlset>")





def seo_summary_html(a):
    """Static crawlable summary for report pages (the interactive body is JS-rendered)."""
    try:
        score = a.get("overall_score", "")
    except AttributeError:
        return ""
    parts = ["<section style='max-width:920px;margin:36px auto 64px;padding:0 22px'>",
             "<h2 style='font-size:clamp(20px,2.6vw,28px);letter-spacing:-.02em;margin:0 0 8px'>"
             "Running form report: %s/100 — %s</h2>"
             % (_html.escape(str(score)), _html.escape(str(a.get("overall_label") or ""))),
             "<p style='color:#8b938a;font-size:15px;line-height:1.6'>%s</p>"
             % _html.escape(str(a.get("one_line_summary") or ""))]
    findings = a.get("findings") or []
    if findings:
        parts.append("<ul style='list-style:none;margin:16px 0 0;padding:0'>")
        for z in findings:
            parts.append("<li style='margin:10px 0;font-size:14px;line-height:1.6'><b>%s — %s/100.</b> %s</li>" % (
                _html.escape(str(z.get("title") or z.get("zone") or "")),
                _html.escape(str(z.get("zone_score") or "")),
                _html.escape(str(z.get("tldr") or z.get("observation") or ""))))
        parts.append("</ul>")
    parts.append("</section>")
    return "".join(parts)


GUIDES = {
 "stop-overstriding": {
  "kw": "Stop Overstriding: Land Under Your Hips",
  "h1": "Stop <span class=lime>overstriding</span>.",
  "intro": "Overstriding is when your foot lands well ahead of your hips, usually with the toes pulled up and the heel reaching. Every such step starts with a braking phase that slows you down and spikes the vertical loading rate through your shins and knees (Lieberman). The tell-tale signs: loud slapping steps, sore shins, and a foot you can see way out in front in photos.",
  "good": "The foot lands under the hips with a quiet midfoot contact and a stiff ankle — judged at stance phase from a side view.",
  "cues": ["Land under hips, quiet feet", "Midfoot, ankle stiff not reaching"],
  "drill": "6x30s cadence ladder +5spm on firm ground",
  "evidence": "Landing ahead of the hips lengthens the braking phase and raises loading rate (Lieberman); rearfoot impact peak is absent in forefoot patterns, and strike index classifies contact (Cavanagh & Lafortune).",
 },
 "running-forward-lean": {
  "kw": "Forward Lean for Runners: Lean From the Ankles",
  "h1": "Lean from the <span class=lime>ankles</span>, not the waist.",
  "intro": "Many runners either run bolt upright or fold at the waist. A waist fold collapses the hips, kills hip extension behind you, and forces your quads to do all the work. Leaning back is worse — it puts the brakes on every step. The fix is a slight whole-body lean sourced at the ankles, with a tall crown and ribs down.",
  "good": "Slight ankle-sourced lean, tall through the crown, ribs down — never a waist fold or back-lean.",
  "cues": ["Lean from ankles, not waist", "Tall through crown, ribs down"],
  "drill": "5x20m fall-forward wall leans",
  "evidence": "Coaching consensus: postural lean should come from the ankles with a neutral spine; waist flexion shortens stride behind the body.",
 },
 "increase-running-cadence": {
  "kw": "Increase Running Cadence: Shorter, Quicker Strides",
  "h1": "Quicker <span class=lime>cadence</span>, softer landing.",
  "intro": "A stiff, fully extended knee stabbing into the ground is the classic low-cadence landing — it maximizes impact and minimizes turnover. On the swing side, a low knee drive with the heel dragging behind means short, choppy power. A small cadence lift with lower vertical oscillation shortens the stride and lowers both loading rate and braking impulse.",
  "good": "Soft stance knee at landing with quick turnover; clean swing-knee drive with the heel recovering under the butt.",
  "cues": ["Soft knee on landing, quick turnover", "Drive knee forward, heel recovers under butt"],
  "drill": "4x20m high-knee march, then cadence pickups at 180spm",
  "evidence": "A small cadence lift with lower vertical oscillation shortens stride and lowers loading rate and braking impulse — consensus, no photo-numbers.",
 },
 "arm-swing-running-form": {
  "kw": "Arm Swing: Drive Back, Not Across",
  "h1": "Drive the elbows <span class=lime>back</span>, not across.",
  "intro": "Hands crossing the midline, stiff straight arms, or fists carried high by the chest all waste energy and twist the torso with every step. The arms should mirror the legs: drive straight back from a roughly 90-degree elbow, hands loose, wrists unbent.",
  "good": "Elbows near 90 degrees with a sagittal (straight back-and-forth) drive and loose hands.",
  "cues": ["Elbows ~90°, drive back not across", "Loose fists, wrists unbent"],
  "drill": "6x30m arm-only pumps",
  "evidence": "Coaching consensus: cross-midline arm swing couples into torso rotation and costs economy; a sagittal drive stabilizes the trunk.",
 },
 "head-position-running": {
  "kw": "Head Position for Runners: Eyes on the Horizon",
  "h1": "Eyes up, <span class=lime>neck</span> long.",
  "intro": "Staring at your feet or poking the chin forward drags the whole posture down with it — shoulders round, chest drops, breathing narrows. A level gaze with a neutral cervical spine keeps the chain tall from the crown down.",
  "good": "Gaze on the horizon with a neutral cervical spine through the flight phase.",
  "cues": ["Gaze on horizon", "Unclench jaw, tongue off roof"],
  "drill": "30s gaze-fix strides",
  "evidence": "Coaching consensus: head carriage sets trunk posture; a level gaze preserves a tall, open chest.",
 },
 "relaxed-shoulders-running": {
  "kw": "Relaxed Shoulders While Running",
  "h1": "Drop the <span class=lime>shoulders</span> from your ears.",
  "intro": "Shrugged, tense shoulders creep up as fatigue sets in — sometimes hiking one side higher than the other. That tension burns energy, restricts breathing, and usually drags bad arm swing along with it.",
  "good": "Shoulders level and dropped, no shrug, symmetric left to right.",
  "cues": ["Drop shoulders from ears on exhale", "Thumbs brush hips, no shrug"],
  "drill": "4x20s shoulder-drop check-ins",
  "evidence": "Coaching consensus: upper-body tension is a fatigue response; scheduled check-ins keep the shoulders down and breathing open.",
 },
 "hip-drop-running": {
  "kw": "Hip Drop When Running: Keep Hips Level",
  "h1": "Keep the <span class=lime>hips</span> level.",
  "intro": "If one hip visibly drops or the pelvis rotates every step, the stance leg is collapsing instead of supporting you — a common source of knee and IT-band complaints. Note this one needs a front view to judge; from the side it is always marked insufficient. Level hips with a neutral pelvis and active glutes is the target.",
  "good": "Hips level with a neutral pelvis, judged from a front view; glutes pushing the ground behind you.",
  "cues": ["Hips level, pelvis neutral", "Glutes push ground behind you"],
  "drill": "2x10 single-leg glute bridges + 20m A-march",
  "evidence": "Coaching consensus: stance-side pelvic drop signals weak lateral support; glute strengthening plus marching drills rebuild level hips.",
 },
}


def guide_page(slug):
    g = GUIDES[slug]
    Steps = "".join(
        "<div class=step><b>%d &middot; %s</b><p>%s</p></div>" % (i + 1, _html.escape(s),
         _html.escape(d)) for i, (s, d) in
        enumerate([("Cue", g["cues"][0]), ("Cue", g["cues"][1]), ("Drill", g["drill"])]))
    others = "".join(
        "<div class=step><b>%s</b><p><a href='/guide/%s'>Read the fix &rarr;</a></p></div>" % (
            _html.escape(GUIDES[s]["kw"].split(":")[0]), s)
        for s in GUIDES if s != slug)
    howto = {"@context": "https://schema.org", "@type": "HowTo", "name": g["kw"],
             "description": g["intro"],
             "step": [{"@type": "HowToStep", "name": n, "text": t}
                      for n, t in [("Cue 1", g["cues"][0]), ("Cue 2", g["cues"][1]),
                                   ("Drill", g["drill"])]]}
    return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>" + _html.escape(g["kw"]) + " | RunForm</title>"
            "<meta name=description content='" + _html.escape(g["intro"][:155]) + "'>"
            "<link rel=canonical href='https://mynextpr.com/guide/" + slug + "'>"
            "<meta property='og:type' content='article'>"
            "<meta property='og:title' content='" + _html.escape(g["kw"]) + " | RunForm'>"
            "<meta property='og:description' content='" + _html.escape(g["intro"][:155]) + "'>"
            "<meta property='og:url' content='https://mynextpr.com/guide/" + slug + "'>"
            "<meta property='og:image' content='https://mynextpr.com/assets/og-image.jpg'>"
            "<script type='application/ld+json'>" + json.dumps(howto) + "</script>"
            + CSS + GA_SNIPPET +
            "<script src=/assets/dots.js defer></script></head><body><canvas id=dots-bg></canvas>"
            "<div class=nav><span class=brand>RunForm</span><a class=navlink href='/'>Analyze your run &rarr;</a></div>"
            "<main><div class=wrap>"
            "<h1>" + g["h1"] + "</h1>"
            "<p class=sub>" + _html.escape(g["intro"]) + "</p>"
            "<section class='card'><h2 style='margin:0 0 8px;font-size:20px'>What good looks like</h2>"
            "<p class=sub style='margin:0'>" + _html.escape(g["good"]) + "</p>"
            "<p class=meta>Evidence: " + _html.escape(g["evidence"]) + "</p></section>"
            "<h2 style='font-size:clamp(22px,3vw,30px);letter-spacing:-.02em;margin:26px 0 4px'>Fix it: 2 cues + 1 drill</h2>"
            "<section class='wrap steps' style='margin-top:12px;max-width:none;padding:0'>" + Steps + "</section>"
            "<div class=card style='text-align:center'><p class=sub>See your own zones scored from one photo.</p>"
            "<a class=btn href='/#analyse'>Analyze my run &rarr;</a> "
            "<a class=quiet href='/report/aeb979a86e8b'>or see a sample report</a></div>"
            "<h2 style='font-size:clamp(22px,3vw,30px);letter-spacing:-.02em;margin:26px 0 4px'>Fix the next zone</h2>"
            "<section class='wrap steps' style='margin-top:12px;max-width:none;padding:0'>" + others + "</section>"
            "</div></main>"
            "</body></html>")


def guides_index():
    cards = "".join(
        "<div class=step><b>%s</b><p>%s</p><p><a href='/guide/%s'>Read the fix &rarr;</a></p></div>" % (
            _html.escape(g["kw"].split(":")[0]), _html.escape(g["intro"][:140] + "…"), s)
        for s, g in GUIDES.items())
    return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>Running Form Guides: Fix Every Zone | RunForm</title>"
            "<meta name=description content='Zone-by-zone running form guides: overstriding, forward lean, cadence, arm swing, head, shoulders and hips — each with cues and a drill.'>"
            "<link rel=canonical href='https://mynextpr.com/guides/'>"
            "<meta property='og:type' content='website'>"
            "<meta property='og:title' content='Running Form Guides | RunForm'>"
            "<meta property='og:url' content='https://mynextpr.com/guides/'>"
            "<meta property='og:image' content='https://mynextpr.com/assets/og-image.jpg'>"
            + CSS + GA_SNIPPET +
            "<script src=/assets/dots.js defer></script></head><body><canvas id=dots-bg></canvas>"
            "<div class=nav><span class=brand>RunForm</span><a class=navlink href='/'>Analyze your run &rarr;</a></div>"
            "<main><div class=wrap>"
            "<h1>Fix your <span class=lime>running form</span>, zone by zone.</h1>"
            "<p class=sub>Seven evidence-backed guides — one per form zone. Each gives you what good looks like, two cues, and one drill.</p>"
            "<section class='wrap steps' style='margin-top:18px;max-width:none;padding:0'>" + cards + "</section>"
            "</div></main>"
            "</body></html>")


def page(body, code=200, ctype="text/html; charset=utf-8"):
    return code, ctype, body.encode()


def need_session(handler):
    jar = http.cookies.SimpleCookie(handler.headers.get("Cookie") or "")
    tok = jar.get("rf_guest")
    if tok and tok.value in SESSIONS:
        return True
    handler.redirect("/login")
    return False


def session_token(handler):
    """Return the caller's guest session token, or None. Pure read helper."""
    jar = http.cookies.SimpleCookie(handler.headers.get("Cookie") or "")
    tok = jar.get("rf_guest")
    if tok and tok.value in SESSIONS:
        return tok.value
    return None


def owner_hash(tok):
    """Opaque per-session owner id for jobs. SHA256 truncated: stable for the
    future Google/OAuth attach (growth-memory maps owner->sub on login) but
    never the session secret, so it is safe to expose in /api/jobs status."""
    import hashlib
    return hashlib.sha256(("rf-owner:" + (tok or "")).encode()).hexdigest()[:16]


def safe_next(path):
    """Guest-auth bridge: validate a post-login redirect. Relative job/upload
    paths only; anything else falls back to /upload (no open redirects)."""
    if path and re.match(r"^/(job/[a-zA-Z0-9_-]{1,40}|upload|report/[a-zA-Z0-9_-]{1,40})$", path):
        return path
    return "/upload"


def login_page(next_path="/upload"):
    """Guest login with login-while-waiting: preserves ?next= so a user who
    logs in from a job page returns to the same watch (poll state is URL-based,
    so nothing is lost). Future Google/OAuth attaches here: mint/merge session
    then 303 to next_path, and claim owner-hash jobs to the login identity."""
    nxt = safe_next(next_path)
    action = "/login" if nxt == "/upload" else "/login?next=" + urllib.parse.quote(nxt, safe="/")
    return LOGIN.replace('action=/login', 'action=' + action)


def inworld_tts(text, voice, instruction=None):
    """Proxy a single Inworld TTS-2 request (key stays server-side). Returns dict."""
    import urllib.request
    payload = {
        "text": text,
        "voiceId": voice,
        "modelId": INWORLD_MODEL,
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1},
        "deliveryMode": "CREATIVE",
        "language": "AUTO",
    }
    if instruction:
        payload["instruction"] = instruction[:400]
    req = urllib.request.Request(
        "https://api.inworld.ai/tts/v1/voice",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Basic " + INWORLD_KEY, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def gemini_audit(img_path, job=None):
    from PIL import Image
    from google import genai
    client = genai.Client(api_key=GEMINI_KEY)
    r = client.models.generate_content(
        model="gemini-3.8-flash", contents=[STEP1_PROMPT, Image.open(img_path)])
    text = r.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        um = getattr(r, "usage_metadata", None)
        inp = (um.prompt_token_count or 0) if um else 0
        outp = ((um.candidates_token_count or 0) +
                (getattr(um, "thoughts_token_count", 0) or 0)) if um else 0
        if not inp and not outp:
            raise ValueError("empty usage")
        _ulog("gemini_audit", job=job, in_tokens=inp, out_tokens=outp,
              detail={"model": "gemini-3.8-flash"})
    except Exception:
        _ulog("gemini_audit", job=job,
              in_tokens=len(STEP1_PROMPT) // 4 + 1500,
              out_tokens=max(500, len(text) // 4),
              detail={"model": "gemini-3.8-flash", "tokens": "estimated"})
    return json.loads(text)


def ray_hit_all(T, o, d):
    import numpy as np
    e1 = T[:, 1] - T[:, 0]
    e2 = T[:, 2] - T[:, 0]
    p = np.cross(d, e2)
    det = (e1 * p).sum(1)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    tv = o - T[:, 0]
    u = (tv * p).sum(1) * inv
    q = np.cross(tv, e1)
    vv = (q * d).sum(1) * inv
    t = (q * e2).sum(1) * inv
    good = ok & (u >= 0) & (vv >= 0) & (u + vv <= 1) & (t > 1e-9)
    return (t[good].min(), o + d * t[good].min()) if good.any() else (None, None)


def compute_anchors(mesh_path, zones):
    import trimesh
    import numpy as np
    m = trimesh.load(mesh_path, force="mesh")
    v = m.vertices
    tris = m.triangles
    out = {}
    missing = {}
    for z in zones:
        band_cfg = ZONE_BANDS.get(z)
        if not band_cfg:
            missing[z] = "no band config"
            continue
        (lo, hi), d = band_cfg
        band = None
        for pad in (0.0, 0.05, 0.10, 0.20):
            b = v[(v[:, 1] >= lo - pad) & (v[:, 1] <= hi + pad)]
            if len(b) >= 10:
                band = b
                break
        if band is None:
            missing[z] = "empty height band even after widening"
            continue
        c = band.mean(0)
        r = float(np.linalg.norm(band[:, [0, 2]] - c[[0, 2]], axis=1).max())
        dn = np.array(d, dtype=float) / np.linalg.norm(d)
        z_axis = np.array([0.0, 0.0, 1.0])
        y_axis = np.array([0.0, 1.0, 0.0])
        hit = None
        for origin, direction in (
            (c + dn * (r + 0.6), -dn),
            (c - dn * (r + 0.6), dn),
            (c + z_axis * (r + 0.6), -z_axis),
            (c + y_axis * 0.6, -y_axis),
        ):
            t, h = ray_hit_all(tris, origin, direction)
            if t is not None:
                hit = h
                break
        if hit is None:
            # Surface fallback: outermost band vertex along approach dir.
            i = int((band @ dn).argmax())
            surf = band[i] + dn * 0.010
            out[z] = [round(float(x), 4) for x in surf]
            missing[z] = "ray miss; surface fallback"
            continue
        out[z] = [round(float(x), 4) for x in hit + dn * 0.010]
    if missing:
        out["_missing"] = missing
    return out


def upright_bake(src_obj, dst_glb):
    import trimesh
    import numpy as np
    m = trimesh.load(src_obj, force="mesh")
    R = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    m.apply_transform(np.vstack([np.hstack([R, [[0], [0], [0]]]), [0, 0, 0, 1]]))
    m.apply_translation([-m.vertices[:, 0].mean(), -m.vertices[:, 1].min(), -m.vertices[:, 2].mean()])
    _ = m.vertex_normals
    m.export(dst_glb)


def is_test_upload(handler):
    """Spend-guard signal: bot/test uploads take the stub-mesh lane (zero
    Tripo calls). Sent as ?test=1 query (what e2e sends) or X-Test: 1 header.
    Real browser uploads omit both and keep the real lane."""
    try:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(handler.path).query)
        if (q.get("test") or [""])[0] == "1":
            return True
    except Exception:
        pass
    try:
        if (handler.headers.get("X-Test") or "").strip() == "1":
            return True
    except Exception:
        pass
    return False


def run_test_lane(job_dir, demo_dir=None):
    """Spend-guard lane: copy the committed demo fixture (analysis + mesh)
    into the job dir; best-effort anchors. NEVER calls Gemini/Tripo —
    tripo_cloud is not even imported here. Raises RuntimeError if the
    fixture is missing. Returns the analysis dict."""
    import shutil
    demo = demo_dir or os.path.join(JOBS, "demo")
    analysis_src = os.path.join(demo, "analysis.json")
    mesh_src = os.path.join(demo, "mesh.glb")
    if not os.path.isfile(analysis_src) or not os.path.isfile(mesh_src):
        raise RuntimeError("test lane needs demo fixture: %s" % demo)
    with open(analysis_src) as f:
        analysis = json.load(f)
    shutil.copy(analysis_src, os.path.join(job_dir, "analysis.json"))
    shutil.copy(mesh_src, os.path.join(job_dir, "mesh.glb"))
    try:
        zones = [z["zone"] for z in analysis.get("findings", [])]
        zones += [z["zone"] for z in analysis.get("insufficient", [])
                  if z.get("zone") not in zones]
        with open(os.path.join(job_dir, "anchors.json"), "w") as f:
            json.dump(compute_anchors(os.path.join(job_dir, "mesh.glb"),
                                      zones or list(ZONE_BANDS)), f)
    except Exception:
        try:
            with open(os.path.join(job_dir, "anchors.json"), "w") as f:
                json.dump({}, f)
        except OSError:
            pass
    return analysis


def run_pipeline(jid):
    """One job's pipeline. In-job lanes (audit+tripo threads) run CONCURRENTLY —
    they only share input.jpg. Tripo's 80-110s cloud gen overlaps the 10-25s
    audit, cutting ~20s off wall time. The download is gated on is_running so
    joke uploads fail fast — though an abandoned Tripo task may still consume
    credits, runners are the norm here. Cross-job order is NOT here: see
    enqueue_pipeline (serial queue, one ACTIVE_JOB). Serial tail after join:
    download (3x retry) -> normalize_glb -> compute_anchors -> done."""
    d = os.path.join(JOBS, jid)
    try:
        if (STATUS.get(jid) or {}).get("test"):
            # Spend-guard: bot lane — stub mesh, zero paid calls.
            set_status(jid, stage="analyzing",
                       detail="Test lane: stub mesh, zero paid calls")
            analysis = run_test_lane(d)
            set_status(jid, stage="done", detail="test report ready",
                       score=analysis.get("overall_score"))
            return
        set_status(jid, stage="analyzing", detail="Scoring form + starting 3D build in parallel")
        mesh_path = os.path.join(d, "mesh.glb")
        if not TRIPO_KEY:
            try:
                analysis = gemini_audit(os.path.join(d, "input.jpg"), job=jid)
                with open(os.path.join(d, "analysis.json"), "w") as f:
                    json.dump(analysis, f)
            except Exception:
                pass
            set_status(jid, stage="failed",
                       error="3D build not configured: TRIPO_API_KEY is missing in .env — "
                             "add it and re-upload. Your photo was scored but no model was built, "
                             "so no stand-in is shown.")
            return
        sys.path.insert(0, os.path.join(V3, "site"))
        import tripo_cloud
        audit_done = threading.Event()
        box = {}

        def audit_job():
            try:
                a = gemini_audit(os.path.join(d, "input.jpg"), job=jid)
                with open(os.path.join(d, "analysis.json"), "w") as f:
                    json.dump(a, f)
                box["analysis"] = a
                if a.get("is_running"):
                    set_status(jid, stage="meshing",
                               detail="Cloud 3D rebuild (~1-3 min)", analysis_ready=True)
            except Exception as e:
                box["audit_error"] = str(e)[-200:]
            finally:
                audit_done.set()

        def tripo_job():
            try:
                set_status(jid, stage="meshing", detail="Uploading photo to Tripo cloud", progress=2)
                tok = tripo_cloud.upload_image(os.path.join(d, "input.jpg"))
                tid = tripo_cloud.create_task(tok)
                box["task_id"] = tid
                try:
                    lane = tripo_cloud.describe_lane()
                except Exception:
                    lane = {}
                _ulog("tripo_build", job=jid,
                      detail={"task_id": tid, **lane})

                def on_prog(p, _st):
                    try:
                        p = max(2, min(99, int(p or 0)))
                    except (TypeError, ValueError):
                        p = 5
                    set_status(jid, stage="meshing",
                               detail="Cloud 3D build %d%%" % p, progress=p)

                box["model_url"] = tripo_cloud.wait_task(tid, cb=on_prog)
            except Exception as e:
                box["tripo_error"] = str(e)[-260:]

        ta = threading.Thread(target=audit_job, daemon=True)
        tm = threading.Thread(target=tripo_job, daemon=True)
        ta.start()
        tm.start()
        ta.join(180)
        if box.get("audit_error"):
            set_status(jid, stage="failed",
                       error="Form audit failed: %s" % box["audit_error"])
            return
        analysis = box.get("analysis")
        if not analysis:
            set_status(jid, stage="failed", error="Form audit timed out — please re-upload.")
            return
        if not analysis.get("is_running"):
            set_status(jid, stage="failed", error="No runner detected in photo")
            return
        set_status(jid, stage="meshing", detail="3D model ready — downloading + fitting",
                   analysis_ready=True)
        tm.join(600)
        if box.get("tripo_error"):
            # Never show another runner's model: surface the real error instead.
            set_status(jid, stage="failed",
                       error="Cloud 3D build failed: %s" % box["tripo_error"])
            return
        if not box.get("model_url"):
            set_status(jid, stage="failed", error="Cloud 3D build timed out — please re-upload.")
            return
        try:
            tmp = mesh_path + ".raw.glb"
            ok_dl = False
            for attempt in (1, 2, 3):
                try:
                    tripo_cloud.download(box["model_url"], tmp, timeout=60)
                    ok_dl = True
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    set_status(jid, stage="meshing",
                               detail="Slow download from 3D CDN — retry %d/3" % (attempt + 1),
                               analysis_ready=True)
            if not ok_dl:
                raise RuntimeError("model download failed after 3 tries")
            try:
                tripo_cloud.normalize_glb(tmp, mesh_path)
            finally:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
        except Exception as e:
            set_status(jid, stage="failed",
                       error="Cloud 3D build failed: %s" % str(e)[-260:])
            return
        if not os.path.exists(mesh_path):
            set_status(jid, stage="failed", error="Cloud 3D build returned no file — please re-upload.")
            return
        zones = [z["zone"] for z in analysis.get("findings", [])]
        zones += [z["zone"] for z in analysis.get("insufficient", [])
                  if z.get("zone") not in zones]
        if not zones:
            zones = list(ZONE_BANDS)
        with open(os.path.join(d, "anchors.json"), "w") as f:
            json.dump(compute_anchors(os.path.join(d, "mesh.glb"), zones), f)
        set_status(jid, stage="done", detail="report ready",
                   score=analysis.get("overall_score"))
    except Exception as e:
        set_status(jid, stage="failed", error=str(e)[-300:])


# --- backend-owned helpers (integrator wires into boot/routes; see handoff) ---

def sanitize_upload(img_bytes, max_dim=1600, quality=88):
    """PIL verify + EXIF rotate + downscale + normalize to JPEG. Returns JPEG bytes."""
    import io
    from PIL import Image, ImageOps
    Image.open(io.BytesIO(img_bytes)).verify()
    im = Image.open(io.BytesIO(img_bytes))
    im = ImageOps.exif_transpose(im).convert("RGB")
    im.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality)
    return buf.getvalue()


def restore_status_from_disk():
    """Reload STATUS from site/jobs/*/status.json; requeue stuck jobs."""
    import glob as _glob
    for sf in _glob.glob(os.path.join(JOBS, "*", "status.json")):
        jid = os.path.basename(os.path.dirname(sf))
        if not JOB_RE.match(jid):
            continue
        try:
            st = json.load(open(sf))
        except (OSError, ValueError):
            continue
        STATUS[jid] = st
        if st.get("stage") in ("queued", "analyzing", "meshing"):
            enqueue_pipeline(jid)


PARALLEL_PLAN = """pipeline-auth parallel plan (post-serial doc; implements in order):
P1 TTS pre-warm during meshing (voice-coach): synthesize coach lines server-side
  into jobs/<jid>/tts/*.mp3 while Tripo builds; loader streams partial voice
  checklist (voice 2/5 cached). Kills first-tap voice latency. No audit/mesh change.
P2 Gemini partials (studio-3d): persist overall_score first, then zone findings as
  they arrive (analysis.partial.json); loader + report render score early, zones
  stream. Requires prompt tweak (score-first) + poller partial merge.
P3 Per-zone anchor fan-out (studio-3d): compute_anchors already loops zones
  independently -> ThreadPoolExecutor over zones (CPU-bound ray hits; 2 vCPU ->
  cap workers=2). Pure speedup, same anchors.json shape.
P4 Cross-job concurrency cap (growth-memory): today ONE ACTIVE_JOB serializes all
  uploads (t3.small safety). Raise to N=2 with a semaphore ONLY after measuring
  P1-P3 wall-time table (same photo, fast lane) + memory headroom; Tripo cloud
  work is off-box so the cap mostly guards Gemini/download bursts.
Accept: wall-time table before/after; zero regressions in fail-loud paths (no
TRIPO key / cloud 503 / no-runner / timeout). Loader stays honest: checklist
states audit/mesh/voice/fit, never fake progress."""

JOB_LOCK = threading.Lock()
ACTIVE_JOB = {"jid": None}
WORKER_TIMEOUT = 600  # seconds: cloud builds take 1-5 min; never stall the serial queue


def enqueue_pipeline(jid):
    """Serial queue: run now if idle, else park as queued; worker drains.
    Cross-job order lives ONLY here (run_pipeline handles in-job lanes)."""
    with JOB_LOCK:
        if ACTIVE_JOB["jid"] is None:
            ACTIVE_JOB["jid"] = jid
            threading.Thread(target=_pipeline_worker, args=(jid,), daemon=True).start()
        else:
            set_status(jid, stage="queued", detail="waiting for worker")


def _pipeline_worker(jid):
    try:
        t = threading.Thread(target=run_pipeline, args=(jid,), daemon=True)
        t.start()
        t.join(WORKER_TIMEOUT)
        if t.is_alive():
            set_status(jid, stage="failed", error="pipeline timed out — please re-upload")
    finally:
        with JOB_LOCK:
            ACTIVE_JOB["jid"] = None
            nxt = next((c for c, st in STATUS.items()
                        if st.get("stage") == "queued" and c != jid), None)
            if nxt:
                ACTIVE_JOB["jid"] = nxt
                threading.Thread(target=_pipeline_worker, args=(nxt,), daemon=True).start()


class H(http.server.BaseHTTPRequestHandler):
    server_version = "RunForm/0.1"

    def redirect(self, path, cookie=None):
        self.send_response(303)
        self.send_header("Location", path)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def send(self, code, ctype, body, cookie=None, cache=None):
        if isinstance(body, str):
            body = body.encode()
        import gzip as _gzip
        if (len(body) > 1024 and isinstance(ctype, str)
                and ctype.split(";")[0].strip() in ("text/html", "application/json", "text/plain")
                and "gzip" in (self.headers.get("Accept-Encoding") or "")):
            body = _gzip.compress(body, 6)
            gzipped = True
        else:
            gzipped = False
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        if gzipped:
            self.send_header("Content-Encoding", "gzip")
        if cache:
            self.send_header("Cache-Control", cache)
        self.send_header("Content-Length", str(len(body)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def session_ok(self):
        jar = http.cookies.SimpleCookie(self.headers.get("Cookie") or "")
        tok = jar.get("rf_guest")
        return bool(tok and tok.value in SESSIONS)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/favicon.ico":
            fp = os.path.join(V3, "site", "assets", "favicon.ico")
            if os.path.exists(fp) and os.path.isfile(fp):
                return self.send(200, "image/x-icon", open(fp, "rb").read(), cache="public, max-age=86400")
            return self.send(204, "text/plain", b"")
        if path == "/":
            _ulog("page", detail={"page": "landing"})
            return self.send(*page(LANDING))
        if path == "/robots.txt":
            return self.send(*page(ROBOTS, 200, "text/plain; charset=utf-8"))
        if path == "/sitemap.xml":
            return self.send(*page(sitemap_xml(), 200, "application/xml; charset=utf-8"))
        if path == "/guides/" or path == "/guides":
            return self.send(*page(guides_index()))
        if path.startswith("/guide/"):
            slug = path[len("/guide/"):]
            if slug in GUIDES:
                return self.send(*page(guide_page(slug)))
            return self.send(*page("unknown guide", 404, "text/plain"))
        if path == "/login":
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            return self.send(*page(login_page((q.get("next") or [""])[0])))
        if path == "/upload":
            if not self.session_ok():
                return self.redirect("/login")
            return self.send(*page(UPLOAD))
        if path.startswith("/job/"):
            if not self.session_ok():
                return self.redirect("/login")
            jid = path[len("/job/"):]
            if not JOB_RE.match(jid) or not load_status(jid):
                return self.send(*page("unknown job", 404, "text/plain"))
            _ulog("page", job=jid, detail={"page": "loader"})
            return self.send(*page(JOB_PAGE.replace("__JID__", json.dumps(jid))))
        if path.startswith("/api/jobs/"):
            rest = path[len("/api/jobs/"):]
            parts = rest.split("/")
            if len(parts) == 2 and parts[1] in ("analysis", "anchors") and JOB_RE.match(parts[0]):
                fp = os.path.join(JOBS, parts[0], parts[1] + ".json")
                try:
                    return self.send(*page(open(fp).read(), 200, "application/json"))
                except OSError:
                    return self.send(*page('{"error":"not found"}', 404, "application/json"))
            jid = parts[0]
            st = load_status(jid) if JOB_RE.match(jid) else None
            if not st:
                return self.send(*page('{"error":"unknown job"}', 404, "application/json"))
            return self.send(*page(json.dumps(st), 200, "application/json"))
        if path.startswith("/report/"):
            jid = path[len("/report/"):]
            if not JOB_RE.match(jid):
                return self.send(*page("unknown report", 404, "text/plain"))
            d = os.path.join(JOBS, jid)
            try:
                a = json.load(open(os.path.join(d, "analysis.json")))
            except OSError:
                return self.send(*page("report not ready", 404, "text/plain"))
            try:
                anchors = json.load(open(os.path.join(d, "anchors.json")))
            except OSError:
                anchors = {}  # progressive: scores render now, mesh+markers stream in when built
            _ulog("page", job=jid,
                  detail={"page": "demo" if jid == "demo" else "report"})
            try:
                t = open(TEMPLATE).read()
            except OSError:
                return self.send(*page("report template missing", 500, "text/plain"))
            t = t.replace("var ANALYSIS = __ANALYSIS_JSON__;", "var ANALYSIS = " + json.dumps(a) + ";")
            t = t.replace("var ANCHORS = __ANCHORS_JSON__;", "var ANCHORS = " + json.dumps(anchors) + ";")
            t = t.replace("var MESH = __MESH_URL__;", "var MESH = " + json.dumps("/jobs/%s/mesh.glb" % jid) + ";")
            proto = (self.headers.get("X-Forwarded-Proto") or "http").split(",")[0].strip()
            base = proto + "://" + (self.headers.get("Host") or "127.0.0.1:8138")
            score = a.get("overall_score", "")
            title = "Running Form Score %s/100 in 3D | RunForm" % score
            desc = a.get("one_line_summary") or a.get("overall_label") or "See your running form rebuilt in 3D, zone by zone."
            img_rel = "/jobs/%s/input.jpg" % jid
            if not os.path.exists(os.path.join(d, "input.jpg")):
                img_rel = "/examples/images-3.jpeg"
            t = (t.replace("__OG_TITLE__", _html.escape(title, quote=True))
                  .replace("__OG_DESC__", _html.escape(desc, quote=True))
                  .replace("__OG_IMAGE__", _html.escape(base + img_rel, quote=True))
                  .replace("__OG_URL__", _html.escape(base + "/report/" + jid, quote=True))
                  .replace("__GA_SNIPPET__", GA_SNIPPET)
                  .replace("__SEO_SUMMARY__", seo_summary_html(a)))
            return self.send(*page(t))
        if path.startswith("/jobs/"):
            parts = path[len("/jobs/"):].split("/")
            if len(parts) == 2 and JOB_RE.match(parts[0]) and parts[1] in ("mesh.glb", "input.jpg"):
                fp = os.path.join(JOBS, parts[0], parts[1])
                if os.path.exists(fp):
                    ct = "model/gltf-binary" if fp.endswith(".glb") else "image/jpeg"
                    return self.send(200, ct, open(fp, "rb").read())
            return self.send(*page("not found", 404, "text/plain"))
        if path.startswith("/examples/"):
            fp = os.path.join(V3, "reference", "input", os.path.basename(path))
            if os.path.exists(fp) and os.path.isfile(fp):
                if fp.endswith((".jpg", ".jpeg")):
                    ct = "image/jpeg"
                elif fp.endswith(".png"):
                    ct = "image/png"
                elif fp.endswith(".webp"):
                    ct = "image/webp"
                elif fp.endswith(".avif"):
                    ct = "image/avif"
                else:
                    ct = "application/octet-stream"
                return self.send(200, ct, open(fp, "rb").read())
            return self.send(*page("not found", 404, "text/plain"))
        # --- research-catalog routes (additive; catalog.json is the source of truth) ---
        if path == "/research/papers/catalog.json":
            fp = os.path.join(PAPERS_DIR, "catalog.json")
            if os.path.exists(fp) and os.path.isfile(fp):
                return self.send(200, "application/json",
                                 open(fp, "rb").read(),
                                 cache="public, max-age=3600")
            return self.send(*page("not found", 404, "text/plain"))
        if path.startswith("/research/papers/thumbs/"):
            name = os.path.basename(path)
            if re.match(r"^[a-z0-9-]+\.svg$", name):
                fp = os.path.join(PAPERS_DIR, "thumbs", name)
                if os.path.exists(fp) and os.path.isfile(fp):
                    return self.send(200, "image/svg+xml",
                                     open(fp, "rb").read(),
                                     cache="public, max-age=86400")
            return self.send(*page("not found", 404, "text/plain"))
        if path.startswith("/research/papers/deep/figures/"):
            name = os.path.basename(path)
            if re.match(r"^[a-z0-9-]+\.svg$", name):
                fp = os.path.join(PAPERS_DIR, "deep", "figures", name)
                if os.path.exists(fp) and os.path.isfile(fp):
                    return self.send(200, "image/svg+xml",
                                     open(fp, "rb").read(),
                                     cache="public, max-age=86400")
            return self.send(*page("not found", 404, "text/plain"))
        # --- showcase-seo routes (additive; covers + detail pages) ---
        if path.startswith("/research/papers/covers/"):
            name = os.path.basename(path)
            if re.match(r"^[a-z0-9-]+\.jpg$", name):
                fp = os.path.join(PAPERS_DIR, "covers", name)
                if os.path.exists(fp) and os.path.isfile(fp):
                    return self.send(200, "image/jpeg",
                                     open(fp, "rb").read(),
                                     cache="public, max-age=86400")
            return self.send(*page("not found", 404, "text/plain"))
        # --- cover-art routes (additive; sandbox gallery only, unlinked) ---
        if path == "/art-sandbox.html" or path == "/art-sandbox":
            fp = os.path.join(V3, "site", "art-sandbox.html")
            if os.path.exists(fp) and os.path.isfile(fp):
                return self.send(200, "text/html", open(fp, "rb").read())
            return self.send(*page("not found", 404, "text/plain"))
        # --- landing-ux routes (additive; home sandbox only, unlinked) ---
        if path == "/home-sandbox.html" or path == "/home-sandbox":
            fp = os.path.join(V3, "site", "home-sandbox.html")
            if os.path.exists(fp) and os.path.isfile(fp):
                return self.send(200, "text/html", open(fp, "rb").read())
            return self.send(*page("not found", 404, "text/plain"))
        # --- quality-voice: script lab (sandbox, unlinked) + raw analysis ---
        if path == "/script-lab.html" or path == "/script-lab":
            fp = os.path.join(V3, "site", "script-lab.html")
            if os.path.exists(fp) and os.path.isfile(fp):
                return self.send(200, "text/html", open(fp, "rb").read())
            return self.send(*page("not found", 404, "text/plain"))
        if path.startswith("/api/analysis/"):
            jid = path[len("/api/analysis/"):]
            if not JOB_RE.match(jid):
                return self.send(*page('{"error":"bad job"}', 400,
                                       "application/json"))
            fp = os.path.join(JOBS, jid, "analysis.json")
            if os.path.exists(fp) and os.path.isfile(fp):
                return self.send(200, "application/json",
                                 open(fp, "rb").read())
            return self.send(*page('{"error":"not found"}', 404,
                                   "application/json"))
        # --- quality-voice: watcher ratings view (login-gated, like /history) ---
        if path == "/ratings":
            if not self.session_ok():
                return self.redirect("/login")
            _ulog("ratings_view", detail={"page": "ratings"})
            return self.send(*page(_ratings_page()))
        if path.startswith("/assets/zones/"):
            name = os.path.basename(path)
            if re.match(r"^[a-z0-9_]+\.jpg$", name):
                fp = os.path.join(V3, "site", "assets", "zones", name)
                if os.path.exists(fp) and os.path.isfile(fp):
                    return self.send(200, "image/jpeg",
                                     open(fp, "rb").read(),
                                     cache="public, max-age=86400")
            return self.send(*page("not found", 404, "text/plain"))
        if path.startswith("/research/") and not path.startswith("/research/papers/"):
            rest = path[len("/research/"):]
            if rest.endswith("/") and len(rest) > 1:
                rest = rest[:-1]
            if rest and "/" not in rest and re.match(r"^[a-z0-9-]+$", rest):
                body = research_page(rest)
                if body is not None:
                    _ulog("page", detail={"page": "research/" + rest})
                    return self.send(*page(body))
            return self.send(*page("unknown study", 404, "text/plain"))
        if path.startswith("/s/"):
            jid = path[len("/s/"):]
            if not JOB_RE.match(jid) or not load_status(jid):
                return self.send(*page("unknown link", 404, "text/plain"))
            click = {
                "t": time.time(),
                "ref": self.headers.get("Referer") or "",
                "ua": (self.headers.get("User-Agent") or "")[:200],
                "lang": self.headers.get("Accept-Language") or "",
            }
            try:
                with open(os.path.join(JOBS, jid, "clicks.jsonl"), "a") as f:
                    f.write(json.dumps(click) + "\n")
            except OSError:
                pass
            _ulog("page", job=jid, detail={"page": "shared"})
            return self.redirect("/report/" + jid)
        if path.startswith("/api/links/"):
            jid = path[len("/api/links/"):]
            if not JOB_RE.match(jid):
                return self.send(*page('{"error":"bad link"}', 400, "application/json"))
            clicks = []
            try:
                with open(os.path.join(JOBS, jid, "clicks.jsonl")) as f:
                    clicks = [json.loads(l) for l in f if l.strip()]
            except (OSError, ValueError):
                pass
            return self.send(*page(json.dumps({
                "job": jid, "clicks": len(clicks),
                "last": clicks[-1] if clicks else None,
                "short": "/s/" + jid}), 200, "application/json"))
        # --- growth-memory routes (additive; /s/ + /api/links/ above are frozen) ---
        if path == "/api/history":
            if not _growth_enabled():
                return self.send(*page('{"error":"growth disabled"}', 404,
                                       "application/json"))
            tok = _token_of(self)
            if not tok or tok not in SESSIONS:
                return self.send(*page('{"error":"login required"}', 401,
                                       "application/json"))
            entries = _history_for(tok)
            cap = _growth_cap()
            out = []
            for e in sorted(entries, key=lambda x: x.get("ts", 0), reverse=True):
                st = load_status(e["job"]) or {}
                out.append({"job": e["job"], "ts": e.get("ts", 0),
                            "filename": e.get("filename", ""),
                            "stage": st.get("stage", ""),
                            "score": st.get("score", "")})
            _ulog("history_view", detail={"used": len(out)})
            return self.send(*page(json.dumps(
                {"analyses": out, "used": len(out),
                 "remaining": max(0, cap - len(out)) if cap else None,
                 "cap": cap, "unlock": _growth_mailto()}), 200,
                "application/json"))
        if path == "/history":
            if not _growth_enabled():
                return self.send(*page("growth disabled", 404, "text/plain"))
            if not self.session_ok():
                return self.redirect("/login")
            _ulog("history_view", detail={"page": "history"})
            return self.send(*page(_history_page(_token_of(self))))
        if path.startswith("/api/share/"):
            if not _growth_enabled():
                return self.send(*page('{"error":"growth disabled"}', 404,
                                       "application/json"))
            jid = path[len("/api/share/"):]
            if not JOB_RE.match(jid):
                return self.send(*page('{"error":"bad link"}', 400,
                                       "application/json"))
            try:
                a = json.load(open(os.path.join(JOBS, jid, "analysis.json")))
            except (OSError, ValueError):
                return self.send(*page('{"error":"not found"}', 404,
                                       "application/json"))
            _ulog("share_meta", job=jid)
            return self.send(*page(json.dumps(
                {"job": jid, "short": "/s/" + jid,
                 "caption": _ig_caption(jid, a)}), 200, "application/json"))
        if path.startswith("/reel/"):
            # One-button Instagram post: single 1080x1920 MP4 (Ken Burns photo
            # + score pill + caption cards + voiceover/silence), composed on
            # demand and cached per job. Caption text via /api/share/<job>.
            if not _growth_enabled():
                return self.send(*page("growth disabled", 404, "text/plain"))
            jid = path[len("/reel/"):]
            if not JOB_RE.match(jid):
                return self.send(*page("bad link", 400, "text/plain"))
            d = os.path.join(JOBS, jid)
            try:
                a = json.load(open(os.path.join(d, "analysis.json")))
                amt = os.path.getmtime(os.path.join(d, "analysis.json"))
            except (OSError, ValueError):
                return self.send(*page("not found", 404, "text/plain"))
            try:
                import reel as _reel
            except ImportError as e:
                return self.send(*page(json.dumps(
                    {"error": "reel unavailable",
                     "detail": str(e)[:120]}), 503, "application/json"))
            voice = bool(INWORLD_KEY)
            if not _reel.is_fresh(d, amt, voice):
                tts_fn = None
                if voice:
                    def tts_fn(text, _v=INWORLD_VOICE):
                        import base64 as _b64
                        out = inworld_tts(text[:400], _v)
                        b64 = out.get("audioContent")
                        if not b64:
                            raise RuntimeError("no audio")
                        return _b64.b64decode(b64)
                try:
                    _, manifest = _reel.compose(d, jid, a, tts_fn=tts_fn)
                except Exception as e:
                    return self.send(*page(json.dumps(
                        {"error": "reel compose failed",
                         "detail": str(e)[:160]}), 503, "application/json"))
            else:
                try:
                    manifest = json.load(open(os.path.join(d, "reel.json")))
                except (OSError, ValueError):
                    manifest = {}
            try:
                mp4 = open(os.path.join(d, "reel.mp4"), "rb").read()
            except OSError:
                return self.send(*page("not found", 404, "text/plain"))
            _ulog("reel_export", job=jid,
                  detail={"voice": manifest.get("voice", voice),
                          "dur": manifest.get("dur", 0)})
            return self.send(200, "video/mp4", mp4,
                             cache="public, max-age=86400")
        if path == "/qa":
            fp = os.path.join(V3, "site", "qa", "latest", "index.html")
            if os.path.exists(fp):
                return self.send(*page(open(fp).read()))
            return self.send(*page("no QA runs yet", 404, "text/plain"))
        if path.startswith("/qa/"):
            fp = os.path.join(V3, "site", "qa", "latest", os.path.basename(path))
            if os.path.exists(fp) and os.path.isfile(fp):
                ct = "image/png" if fp.endswith(".png") else "application/json" if fp.endswith(".json") else "text/plain"
                return self.send(200, ct, open(fp, "rb").read(), cache="no-store")
            return self.send(*page("not found", 404, "text/plain"))
        if path == "/healthz":
            return self.send(*page(json.dumps(
                {"ok": True, "jobs": len(STATUS),
                 "inworld": bool(INWORLD_KEY),
                 "python": sys.executable}), 200, "application/json"))
        if path == "/api/showcase":
            vp = os.path.join(V3, "site", "assets", "showcase.mp4")
            return self.send(*page(json.dumps({"video": os.path.exists(vp)}), 200, "application/json"))
        if path.startswith("/assets/"):
            fp = os.path.join(V3, "site", "assets", os.path.basename(path))
            if os.path.exists(fp) and os.path.isfile(fp):
                if fp.endswith(".mp4"):
                    ct = "video/mp4"
                    return self.send(200, ct, open(fp, "rb").read(), cache="public, max-age=604800")
                elif fp.endswith(".png"):
                    ct = "image/png"
                elif fp.endswith((".jpg", ".jpeg")):
                    ct = "image/jpeg"
                elif fp.endswith(".webm"):
                    ct = "video/webm"
                elif fp.endswith(".js"):
                    ct = "application/javascript"
                elif fp.endswith(".css"):
                    ct = "text/css"
                elif fp.endswith(".ico"):
                    ct = "image/x-icon"
                else:
                    ct = "application/octet-stream"
                return self.send(200, ct, open(fp, "rb").read(), cache="public, max-age=86400")
            return self.send(*page("not found", 404, "text/plain"))
        if path == "/api/demo":
            d = os.path.join(JOBS, "demo")
            try:
                a = json.load(open(os.path.join(d, "analysis.json")))
                an = json.load(open(os.path.join(d, "anchors.json")))
            except (OSError, ValueError):
                return self.send(*page('{"error":"no demo"}', 404, "application/json"))
            return self.send(*page(json.dumps({"analysis": a, "anchors": an}), 200, "application/json"))
        if path == "/api/tts/status":
            return self.send(*page(json.dumps({
                "configured": bool(INWORLD_KEY), "engine": "inworld",
                "model": INWORLD_MODEL, "voice": INWORLD_VOICE,
                "voices": INWORLD_VOICES}), 200, "application/json"))
        return self.send(*page("not found", 404, "text/plain"))

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/login":
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            nxt = (q.get("next") or [""])[0]
            try:
                length = int(self.headers.get("Content-Length", 0))
            except ValueError:
                length = 0
            if not nxt and 0 < length <= 2048:
                try:
                    form = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"))
                    nxt = (form.get("next") or [""])[0]
                except (ValueError, UnicodeDecodeError):
                    nxt = ""
            tok = secrets.token_hex(16)
            SESSIONS.add(tok)
            self.send_response(303)
            self.send_header("Location", safe_next(nxt))
            self.send_header("Set-Cookie", "rf_guest=%s; Path=/; HttpOnly" % tok)
            self.end_headers()
            return
        if path == "/api/jobs":
            newtok = None
            tok = session_token(self)
            if not tok:
                newtok = secrets.token_hex(16)
                SESSIONS.add(newtok)
                tok = newtok
            cookie = ("rf_guest=%s; Path=/; HttpOnly" % newtok) if newtok else None
            owner = owner_hash(tok)
            test = is_test_upload(self)  # spend-guard: bots take stub lane
            try:
                length = int(self.headers.get("Content-Length", 0))
            except ValueError:
                length = 0
            if length <= 0 or length > MAX_UPLOAD + 65536:
                return self.send(*page('{"error":"empty or too large (8MB max)"}', 400, "application/json"))
            body = self.rfile.read(length)
            sep = body.find(b"\xff\xd8\xff")
            png = body.find(b"\x89PNG")
            webp = body.find(b"RIFF")
            starts = [s for s in (sep, png, webp) if s >= 0]
            if not starts:
                return self.send(*page('{"error":"no JPEG/PNG/WebP image found"}', 400, "application/json"))
            start = min(starts)
            endmark = body.rfind(b"\r\n--")
            img = body[start:endmark] if endmark > start else body[start:]
            m = re.search(rb'filename="([^"]{1,120})"', body[:max(0, start)])
            fname = os.path.basename(m.group(1).decode("utf-8", "replace")) if m else "upload"
            if len(img) > MAX_UPLOAD or len(img) < 1024:
                return self.send(*page('{"error":"bad image size"}', 400, "application/json"))
            try:
                img = sanitize_upload(img)
            except Exception:
                return self.send(*page('{"error":"invalid image (JPEG/PNG/WebP only)"}', 400, "application/json"))
            # --- pipeline-auth: runner isolation (single-runner guarantee) ---
            # Crop to the most prominent runner BEFORE Gemini/Tripo ever see
            # the photo. Fail-soft: original proceeds with a reason recorded.
            orig = img
            iso = {"isolated": False}
            try:
                if V3 not in sys.path:
                    sys.path.insert(0, V3)
                from extract_pose import isolate_runners
                img, iso = isolate_runners(img)
            except Exception as e:
                iso = {"isolated": False, "persons": 0, "box": None,
                       "reason": str(e)[-120:]}
            # --- growth-memory: 15-cap (frozen /s/ share unaffected) ---
            # Spend-guard: test jobs skip cap (bots must never burn the cap).
            if _growth_enabled() and not test:
                cap = _growth_cap()
                used = len(_history_for(tok))
                if cap and used >= cap:
                    _ulog("cap_hit", detail={"used": used, "cap": cap})
                    if "text/html" in (self.headers.get("Accept") or ""):
                        return self.send(*page(_paywall_body(used, cap), 402),
                                         cookie=cookie)
                    return self.send(*page(json.dumps(
                        {"error": "analysis cap reached (%d free analyses)" % cap,
                         "used": used, "cap": cap,
                         "unlock": _growth_mailto()}), 402,
                        "application/json"), cookie=cookie)
            jid = uuid.uuid4().hex[:12]
            d = os.path.join(JOBS, jid)
            os.makedirs(d)
            with open(os.path.join(d, "input.jpg"), "wb") as f:
                f.write(img)
            if iso.get("isolated"):
                with open(os.path.join(d, "input_orig.jpg"), "wb") as f:
                    f.write(orig)
            set_status(jid, stage="queued", detail="waiting for worker",
                       filename=fname, started_at=time.time(), owner=owner,
                       test=test, isolation=iso)
            _ulog("upload", job=jid,
                  detail={"filename": fname, "test": test,
                          "isolated": iso.get("isolated"),
                          "persons": iso.get("persons", 0)})
            # Spend-guard: test jobs skip history (no bot pollution).
            if _growth_enabled() and not test:
                _history_add(tok, jid, fname)
            enqueue_pipeline(jid)
            if "text/html" in (self.headers.get("Accept") or ""):
                return self.redirect("/job/" + jid, cookie)
            return self.send(*page(json.dumps({"job_id": jid}), 200, "application/json"), cookie=cookie)
        if path == "/api/tts":
            if not INWORLD_KEY:
                return self.send(*page('{"error":"tts not configured"}', 503, "application/json"))
            try:
                length = int(self.headers.get("Content-Length", 0))
            except ValueError:
                length = 0
            if length <= 0 or length > 20000:
                return self.send(*page('{"error":"bad request"}', 400, "application/json"))
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return self.send(*page('{"error":"bad json"}', 400, "application/json"))
            text = (body.get("text") or "").strip()
            if not text or len(text) > 2000:
                return self.send(*page('{"error":"text required (<=2000 chars)"}', 400, "application/json"))
            voice = body.get("voice") or INWORLD_VOICE
            if not re.match(r"^[A-Za-z][A-Za-z0-9 _-]{0,39}$", voice):
                return self.send(*page('{"error":"bad voice"}', 400, "application/json"))
            try:
                out = inworld_tts(text, voice, body.get("instruction"))
            except Exception as e:
                return self.send(*page(json.dumps({"error": "tts failed", "detail": str(e)[:160]}), 502, "application/json"))
            audio = out.get("audioContent")
            if not audio:
                return self.send(*page('{"error":"no audio"}', 502, "application/json"))
            _ulog("tts", detail={"voice": voice}, chars=len(text))
            return self.send(*page(json.dumps({"audioContent": audio}), 200, "application/json"))
        # --- quality-voice: usefulness vote (public; reports are public) ---
        if path == "/api/rate":
            try:
                length = int(self.headers.get("Content-Length", 0))
            except ValueError:
                length = 0
            if length <= 0 or length > 4096:
                return self.send(*page('{"error":"bad request"}', 400,
                                       "application/json"))
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return self.send(*page('{"error":"bad json"}', 400,
                                       "application/json"))
            jid = body.get("job", "")
            useful = body.get("useful")
            note = body.get("note", "")
            if (not isinstance(jid, str) or not JOB_RE.match(jid)
                    or not os.path.isdir(os.path.join(JOBS, jid))):
                return self.send(*page('{"error":"unknown job"}', 404,
                                       "application/json"))
            if not isinstance(useful, bool):
                return self.send(*page('{"error":"useful must be true/false"}',
                                       400, "application/json"))
            if not isinstance(note, str) or len(note) > 140:
                return self.send(*page('{"error":"note must be <=140 chars"}',
                                       400, "application/json"))
            if _ratings_add(jid, useful, note.strip()) is None:
                return self.send(*page('{"error":"store failed"}', 500,
                                       "application/json"))
            _ulog("rating", job=jid,
                  detail={"useful": useful, "note": bool(note.strip())})
            s = _ratings_summary(jid)
            return self.send(*page(json.dumps(
                {"ok": True, "job": jid, "yes": s["yes"], "no": s["no"]}),
                200, "application/json"))
        return self.send(*page("not found", 404, "text/plain"))

    def do_DELETE(self):
        # --- growth-memory: privacy-first job delete (own history only) ---
        path = urllib.parse.urlparse(self.path).path
        if path.startswith("/api/jobs/"):
            if not _growth_enabled():
                return self.send(*page('{"error":"growth disabled"}', 404,
                                       "application/json"))
            jid = path[len("/api/jobs/"):]
            tok = _token_of(self)
            if not tok or tok not in SESSIONS:
                return self.send(*page('{"error":"login required"}', 401,
                                       "application/json"))
            if not JOB_RE.match(jid) or jid == "demo":
                return self.send(*page('{"error":"not found"}', 404,
                                       "application/json"))
            if jid not in [e.get("job") for e in _history_for(tok)]:
                return self.send(*page('{"error":"not found"}', 404,
                                       "application/json"))
            try:
                shutil.rmtree(os.path.join(JOBS, jid))
            except OSError:
                return self.send(*page('{"error":"delete failed"}', 500,
                                       "application/json"))
            try:
                STATUS.pop(jid, None)
            except Exception:
                pass
            _history_remove(tok, jid)
            _ulog("job_delete", job=jid)
            return self.send(*page(json.dumps({"deleted": jid}), 200,
                                   "application/json"))
        return self.send(*page("not found", 404, "text/plain"))

    def log_message(self, *a):
        pass


def seed_demo():
    # v4-local: demo fixture is committed under site/jobs/demo/ (no copies,
    # no output/ bulk). Just load its status; never fabricate a mesh here.
    os.makedirs(JOBS, exist_ok=True)
    restore_status_from_disk()
    d = os.path.join(JOBS, "demo")
    try:
        if os.path.exists(os.path.join(d, "analysis.json")) and os.path.exists(
                os.path.join(d, "mesh.glb")):
            try:
                STATUS["demo"] = json.load(open(os.path.join(d, "status.json")))
            except (OSError, ValueError):
                set_status("demo", stage="done", detail="sample report", score=63)
            return
        print("seed_demo skipped: site/jobs/demo fixture missing", flush=True)
    except Exception as e:
        print("seed_demo skipped:", e, flush=True)


def selftest():
    """Spend-guard proof: ?test=1/X-Test:1 detected; test lane completes with
    tripo_cloud unimportable and writes analysis+mesh+anchors. Zero network."""
    import shutil
    import tempfile

    class FakeH:
        def __init__(self, path, xtest=None):
            self.path = path
            self.headers = {"X-Test": xtest} if xtest else {}

    assert is_test_upload(FakeH("/api/jobs?test=1"))
    assert is_test_upload(FakeH("/api/jobs", xtest="1"))
    assert not is_test_upload(FakeH("/api/jobs"))
    assert not is_test_upload(FakeH("/api/jobs?test=0"))
    assert "tripo_cloud" not in sys.modules, "tripo imported at server boot"

    class Bomb:
        def __getattr__(self, name):
            raise AssertionError("test lane touched tripo_cloud." + name)

    sys.modules["tripo_cloud"] = Bomb()
    job = tempfile.mkdtemp(prefix="spendguard_")
    try:
        analysis = run_test_lane(job)
        assert analysis.get("overall_score") is not None
        for name in ("analysis.json", "mesh.glb", "anchors.json"):
            assert os.path.isfile(os.path.join(job, name)), name
    finally:
        del sys.modules["tripo_cloud"]
        shutil.rmtree(job, ignore_errors=True)
    print("server selftest: spend-guard OK (test lane, zero Tripo calls)")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        seed_demo()  # includes restore_status_from_disk(): requeue stuck jobs
        if not os.path.exists(TEMPLATE):
            print("WARNING: report template missing: %s" % TEMPLATE, flush=True)
        port = int(sys.argv[1]) if len(sys.argv) > 1 else 8139
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), H)
        print("RunForm demo at http://127.0.0.1:%d/" % port, flush=True)
        srv.serve_forever()

