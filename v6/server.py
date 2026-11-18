#!/usr/bin/env python3
"""mynextpr backend (v6): Strava OAuth + auto-stamp webhooks, multi-athlete.

One process serves the static v6 pages AND the API the manage page talks to:

  GET  /exchange_token?code=..&state=..  Strava OAuth return: swaps the code
      for tokens (client secret stays server-side), stores them in
      .athletes/{athlete_id}.json (git-ignored), sets an mnp_athlete
      cookie, then redirects to /manage.html.
  GET  /api/status                       {connected, paused, race, goal, athlete}
  GET  /api/export                       everything stored about this athlete
  POST /api/pause | /api/resume | /api/disconnect | /api/delete-account
  POST /api/stamp-latest[?dry=1]         stamp the athlete's latest run now
      (dry=1 returns the would-be description without writing anything).
  GET  /webhook                          Strava subscription verification.
  POST /webhook                          activity create/update events: stamps
      new runs automatically unless paused/disconnected; athlete
      revocations drop that athlete's data.
  POST /api/subscribe                    one-time webhook subscription setup.

Run:  python3 v6/server.py  (serves http://localhost:8123)
Env (.env, never committed): STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET,
  STRAVA_VERIFY_TOKEN (any random string you invent for webhooks).

Stdlib only. No tokens or secrets are ever logged or served to pages.
"""

import calendar
import datetime
import http.server
import json
import os
import threading
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8123"))
STATE_PATH = os.path.join(ROOT, ".tokens.json")  # legacy single-athlete file
ATHLETES_DIR = os.path.join(ROOT, ".athletes")  # per-athlete files: {id}.json
ATHLETE_COOKIE = "mnp_athlete"
MINIMAL_SCOPES = ("read", "activity:read", "activity:write")

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".mp4": "video/mp4",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".txt": "text/plain; charset=utf-8",
    ".xml": "application/xml; charset=utf-8",
    ".ico": "image/x-icon",
}

import sys
sys.path.insert(0, ROOT)
import update_engine as engine


# --------------------------------------------------------------------------
# local state + .env (quote-tolerant: values may be wrapped in '...')


def load_env(path=None):
    env = {}
    path = path or os.path.join(os.path.dirname(ROOT), ".env")
    try:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                    value = value[1:-1]
                env[key.strip()] = value
    except OSError:
        pass
    return env


ENV = load_env()
CLIENT_ID = ENV.get("STRAVA_CLIENT_ID", "")
CLIENT_SECRET = ENV.get("STRAVA_CLIENT_SECRET", "")
VERIFY_TOKEN = ENV.get("STRAVA_VERIFY_TOKEN", "")

_state_lock = threading.Lock()


def load_state():
    """Legacy single-athlete state (kept for migration only)."""
    try:
        with open(STATE_PATH) as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(patch):
    with _state_lock:
        data = load_state()
        data.update(patch)
        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(data, fh)
        os.replace(tmp, STATE_PATH)
        return data


def clear_state():
    with _state_lock:
        try:
            os.remove(STATE_PATH)
        except OSError:
            pass


# -- per-athlete store (multi-user) -------------------------------------------
# One JSON file per athlete: .athletes/{athlete_id}.json. Each file holds only
# that athlete's tokens + race + flags. Strava activity content is never
# retained beyond the transient stamped-id list (no activity cache).


def _athlete_path(athlete_id):
    safe = "".join(ch for ch in str(athlete_id or "") if ch.isdigit())
    return os.path.join(ATHLETES_DIR, safe + ".json") if safe else ""


def _migrate_legacy():
    """One-time move of the old single-athlete .tokens.json, if present."""
    try:
        if not os.path.isfile(STATE_PATH):
            return
        with open(STATE_PATH) as fh:
            data = json.load(fh)
        if not isinstance(data, dict) or not data.get("athlete_id"):
            return
        dest = _athlete_path(data["athlete_id"])
        if dest and not os.path.isfile(dest):
            os.makedirs(ATHLETES_DIR, exist_ok=True)
            tmp = dest + ".tmp"
            with open(tmp, "w") as fh:
                json.dump(data, fh)
            os.replace(tmp, dest)
    except (OSError, ValueError):
        pass


def load_athlete(athlete_id):
    _migrate_legacy()
    path = _athlete_path(athlete_id)
    if not path:
        return {}
    try:
        with open(path) as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_athlete(athlete_id, patch):
    path = _athlete_path(athlete_id)
    if not path:
        return {}
    with _state_lock:
        try:
            os.makedirs(ATHLETES_DIR, exist_ok=True)
            data = load_athlete(athlete_id)
            data.update(patch)
            tmp = path + ".tmp"
            with open(tmp, "w") as fh:
                json.dump(data, fh)
            os.replace(tmp, path)
            return data
        except OSError:
            return {}


def clear_athlete(athlete_id):
    path = _athlete_path(athlete_id)
    if not path:
        return
    with _state_lock:
        for candidate in (path, STATE_PATH):
            try:
                if candidate == STATE_PATH:
                    # Only remove the legacy file when it belongs to athlete.
                    existing = load_state()
                    if str(existing.get("athlete_id", "")) != str(athlete_id):
                        continue
                os.remove(candidate)
            except OSError:
                pass


def list_athlete_ids():
    _migrate_legacy()
    try:
        return sorted(
            name[:-5] for name in os.listdir(ATHLETES_DIR)
            if name.endswith(".json") and name[:-5].isdigit())
    except OSError:
        return []


# -- stamped-ID dedup log (7-day retention) -----------------------------------
# Only activity IDs + first-stamp timestamps are kept (no activity content),
# solely to avoid double-stamping retries. Entries older than 7 days are
# pruned on every write, per the cache limit in the privacy policy.
STAMP_TTL_S = 7 * 24 * 3600
STAMP_CAP = 200


def _stamped_ids(state):
    raw = state.get("stamped", [])
    if isinstance(raw, dict):
        return {str(k): v for k, v in raw.items()}
    if isinstance(raw, list):  # legacy format: IDs without timestamps
        return {str(i): 0 for i in raw}
    return {}


def _remember_stamped(athlete_id, state, activity_id):
    now = time.time()
    kept = {k: v for k, v in _stamped_ids(state).items()
            if now - float(v or 0) < STAMP_TTL_S}
    kept[str(activity_id)] = now
    trimmed = dict(sorted(kept.items(), key=lambda kv: kv[1])[-STAMP_CAP:])
    save_athlete(athlete_id, {"stamped": trimmed})
    return trimmed


# --------------------------------------------------------------------------
# Telegram activity alerts (best-effort, owner-only, never blocks requests)


def _race_line(race):
    """One-line human summary of a chosen race: name (date), goal + dist."""
    if not isinstance(race, dict):
        return "-"
    name = str(race.get("race") or "-")
    date = str(race.get("date") or "")
    goal = str(race.get("goal") or "")
    dist = str(race.get("dist") or "")
    line = name + (" (" + date + ")" if date else "")
    extra = " ".join(p for p in (goal, dist) if p)
    return line + (" — goal " + extra if extra else "")


def _esc(text):
    """Escape dynamic text for Telegram HTML messages."""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _who(athlete_id, state=None):
    """Friendly runner label: stored first name, else the bare ID."""
    name = ""
    if isinstance(state, dict):
        name = str(state.get("firstname") or "")
    return name or ("runner " + str(athlete_id))


def _dayword(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return ""
    if n > 1:
        return "%d days to go" % n
    if n == 1:
        return "1 day to go"
    return "race day today"


def _km(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "—"
    return "%.1f" % value


def _notify(text):
    """Send one owner alert via Telegram as formatted HTML. Silent no-op
    unless the server .env sets both TELEGRAM_BOT_TOKEN and
    TELEGRAM_CHAT_ID. Sends in a daemon thread so slow networks never
    delay a response. Compose with _esc() around every dynamic value."""
    token = ENV.get("TELEGRAM_BOT_TOKEN", "")
    chat = ENV.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat or not text:
        return None
    def _send():
        try:
            req = urllib.request.Request(
                "https://api.telegram.org/bot" + token + "/sendMessage",
                data=json.dumps(
                    {"chat_id": chat, "text": text[:3500],
                     "parse_mode": "HTML",
                     "disable_web_page_preview": True}).encode(),
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10).read(64)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()
    return True


def _cookie_athlete(cookie_header):
    for part in str(cookie_header or "").split(";"):
        name, _, value = part.partition("=")
        if name.strip() == ATHLETE_COOKIE and value.strip().isdigit():
            return value.strip()
    return ""


def _resolve_athlete(handler):
    """Which athlete is calling? Strictly the `mnp_athlete` login cookie.

    There is deliberately NO fallback: with a single athlete connected, a
    visitor without (or with a wrong) cookie must never resolve to that
    athlete — otherwise /api/status, /api/export, pause/resume/stamp and
    even disconnect/delete would be open to anyone. Webhooks don't use
    this function (they resolve server-side by owner_id).
    """
    return _cookie_athlete(handler.headers.get("Cookie", ""))


def _known_athlete(handler):
    """aid only when a real athlete record exists — never create one.

    A well-formed cookie for an unknown athlete (or none at all) yields "",
    so no route can read, mutate, or claim success on someone else's (or
    nobody's) data.
    """
    aid = _resolve_athlete(handler)
    if aid and load_athlete(aid).get("refresh_token"):
        return aid
    return ""


# --------------------------------------------------------------------------
# Strava API helpers (server-side only: the secret never leaves this file)

# Rate-limit handling (see https://developers.strava.com/docs/rate-limits/):
# read endpoints share 100 req/15min + 1000/day per app; 429s reset at the
# next natural quarter hour (:00/:15/:30/:45). Every api/v3 call below goes
# through the guard so a burst of webhooks backs off instead of burning
# the daily quota. The token endpoint is exempt (auth, uncounted).
_RATE_LOCK = threading.Lock()
_RATE_LIMITED_UNTIL = 0.0
_LAST_429_NOTICE = {}  # activity key -> timestamp of last 429 Telegram alert
NOTICE_TTL_S = 900


def _seconds_to_reset(now=None):
    """Seconds until the next natural quarter hour (+5s safety buffer)."""
    now = time.time() if now is None else now
    secs = 900 - (now % 900)
    return secs + 5


def _rate_limited():
    with _RATE_LOCK:
        return time.time() < _RATE_LIMITED_UNTIL


def _note_429(headers=None):
    """Record a 429: back off until Retry-After or the next reset window."""
    delay = 0
    try:
        if headers:
            retry = headers.get("Retry-After", "")
            delay = int(str(retry).strip())
    except (TypeError, ValueError):
        delay = 0
    if delay <= 0:
        delay = _seconds_to_reset()
    delay = min(max(delay, 1), 3600)
    with _RATE_LOCK:
        global _RATE_LIMITED_UNTIL
        _RATE_LIMITED_UNTIL = max(_RATE_LIMITED_UNTIL, time.time() + delay)
    return delay


def _should_notify_429(key):
    """True once per activity per window — stops Telegram retry storms."""
    now = time.time()
    with _RATE_LOCK:
        last = _LAST_429_NOTICE.get(str(key), 0)
        if now - last < NOTICE_TTL_S:
            return False
        _LAST_429_NOTICE[str(key)] = now
        return True


def _strava(method, path, token=None, params=None, timeout=15):
    if path.startswith("/api/v3") and _rate_limited():
        return 429, {"_error": "rate limited, retry later"}
    data = None
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if params is not None:
        encoded = urllib.parse.urlencode(params)
        if method == "GET":  # GET params ride in the URL; a body is ignored
            path = path + ("&" if "?" in path else "?") + encoded
        else:
            data = encoded.encode()
    req = urllib.request.Request(
        "https://www.strava.com" + path, data=data, headers=headers,
        method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            return resp.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            detail = ""
        if exc.code == 429 and path.startswith("/api/v3"):
            try:
                _note_429(exc.headers)
            except Exception:
                _note_429(None)
        return exc.code, {"_error": detail}


def _token_request(payload):
    return _strava("POST", "/oauth/token", params=payload)


def _fresh_token(state, athlete_id=""):
    """Return a usable access token, refreshing once when expired."""
    access = state.get("access_token", "")
    if state.get("expires_at", 0) > time.time() + 60 and access:
        return access
    status, body = _token_request({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": state.get("refresh_token", ""),
    })
    if status != 200 or not body.get("access_token"):
        return ""
    refreshed = {
        "access_token": body.get("access_token", ""),
        "refresh_token": body.get("refresh_token", state.get("refresh_token", "")),
        "expires_at": body.get("expires_at", 0),
    }
    if athlete_id:
        save_athlete(athlete_id, refreshed)
    else:  # legacy path (migration only)
        save_state(refreshed)
    return body.get("access_token", "")


SUPPORT_TOPICS = ("general", "privacy", "security", "bug")
INBOX_DIR = os.path.join(ROOT, ".support-inbox")
INBOX_FILE = os.path.join(INBOX_DIR, "inbox.jsonl")
INBOX_MAX_BYTES = 5 * 1024 * 1024


def _valid_support(payload):
    """Validate a support-form submission. Returns (entry, error)."""
    if not isinstance(payload, dict):
        return None, "bad request"
    topic = str(payload.get("topic", "")).strip().lower()
    message = str(payload.get("message", "")).strip()
    athlete_id = "".join(
        ch for ch in str(payload.get("athlete_id", "")) if ch.isdigit())[:20]
    contact = str(payload.get("contact", "")).strip()[:120]
    if topic not in SUPPORT_TOPICS:
        return None, "unknown topic"
    if not (10 <= len(message) <= 2000):
        return None, "message must be 10-2000 characters"
    try:
        size = os.path.getsize(INBOX_FILE)
    except OSError:
        size = 0
    if size > INBOX_MAX_BYTES:
        return None, "inbox full — try again later"
    entry = {
        "id": "%d-%d" % (int(time.time()), os.getpid() % 100000),
        "ts": int(time.time()),
        "topic": topic,
        "athlete_id": athlete_id,
        "contact": contact,
        "message": message,
    }
    return entry, ""


def _revoke_and_clear(athlete_id):
    """Best-effort remote revoke, then always drop local data."""
    state = load_athlete(athlete_id)
    token = state.get("access_token", "")
    if token:
        try:
            _strava("POST", "/oauth/deauthorize", token=token)
        except Exception:
            pass
    clear_athlete(athlete_id)


def _athlete_name(token):
    """(athlete_id, name); ("", "") on failure. No caching, one read."""
    status, me = _strava("GET", "/api/v3/athlete", token=token)
    if status != 200 or not isinstance(me, dict) or not me.get("id"):
        return "", ""
    name = f"{me.get('firstname', '')} {me.get('lastname', '')}".strip()
    return me["id"], name


# Activity types counted toward run totals (same filter as the stamp path).
_RUN_TYPES = ("run", "trailrun", "")


def _period_epochs(ref_iso=None):
    """(month_after, year_after, ref_iso): epoch bounds for calendar sums.

    ref_iso is a YYYY-MM-DD day — the stamped run's local date when known,
    else today. Windows start at UTC midnight of the 1st / Jan 1st, so a
    run within hours of a boundary in a far timezone can land on either
    side; the label always follows the run's own date.
    """
    try:
        day = (engine.parse_iso_day(ref_iso) if ref_iso
               else datetime.date.today())
    except (TypeError, ValueError):
        day = datetime.date.today()
    month_start = datetime.date(day.year, day.month, 1)
    year_start = datetime.date(day.year, 1, 1)
    return (calendar.timegm(month_start.timetuple()),
            calendar.timegm(year_start.timetuple()), day.isoformat())


def _sum_run_km(token, after_epoch, max_pages=5):
    """(total_km, seen_ids, ok): sum run distances over listed activities.

    Only run/trailrun types count. ok is False when the listing failed —
    callers then omit that total instead of printing a stale number.
    """
    total_m = 0.0
    seen = set()
    page = 1
    while page <= max_pages:
        status, acts = _strava(
            "GET", "/api/v3/athlete/activities", token=token,
            params={"after": int(after_epoch), "per_page": 200, "page": page})
        if status != 200 or not isinstance(acts, list):
            return total_m / 1000.0, seen, False
        if not acts:
            break
        for act in acts:
            if not isinstance(act, dict):
                continue
            aid = act.get("id")
            if aid is not None:
                seen.add(str(aid))
            if str(act.get("type", "")).lower() not in _RUN_TYPES:
                continue
            try:
                total_m += float(act.get("distance") or 0)
            except (TypeError, ValueError):
                continue
        if len(acts) < 200:
            break
        page += 1
    return total_m / 1000.0, seen, True


def _run_month_year_totals(token, run_date_iso=None, run_id=None, run_m=None):
    """(month_km, year_km, ref_iso): calendar-month + YTD run totals.

    Summed live from the activity list so the numbers are always current:
    Strava's aggregate stats lag behind the webhook that fires seconds
    after upload, and `recent_*` is a rolling 28 days, not a calendar
    month. The run being stamped is added when the listing does not
    contain it yet (never double-counted when it does). Each side is
    None when its listing failed — never a stale cached number.
    """
    month_after, year_after, ref = _period_epochs(run_date_iso)
    try:
        extra = float(run_m or 0) / 1000.0
    except (TypeError, ValueError):
        extra = 0.0
    extra = extra if extra > 0 else 0.0
    month_km = year_km = None
    m_total, m_seen, m_ok = _sum_run_km(token, month_after)
    if m_ok:
        month_km = m_total
        if run_id is not None and str(run_id) not in m_seen:
            month_km += extra
    y_total, y_seen, y_ok = _sum_run_km(token, year_after)
    if y_ok:
        year_km = y_total
        if run_id is not None and str(run_id) not in y_seen:
            year_km += extra
    return month_km, year_km, ref


def _race_dist_km(dist_label, race_name=""):
    """Nominal race distance (km) from a distance label, falling back to
    the race name ("Tata Mumbai Marathon" → marathon → 42.195)."""
    if "ultra" in f"{dist_label or ''} {race_name or ''}".lower():
        return None
    for text in (dist_label, race_name):
        d = str(text or "").lower().strip()
        if not d:
            continue
        if d.startswith("5k") or d == "5":
            return 5.0
        if d.startswith("10k") or d == "10":
            return 10.0
        if "half" in d or "21" in d:
            return 21.0975
        if "full" in d or "marathon" in d or "42" in d:
            return 42.195
    return None


def _stamp_activity(token, activity_id, race, goal, dist_km, month_km,
                    year_km, today_iso=None, dry=False, act=None):
    """Compute the block and PUT it on the activity. Returns (ok, detail).

    Pass the already-fetched activity dict (from the webhook pre-read) via
    `act` to skip the duplicate GET — that alone cuts one read per run.
    """
    if not isinstance(act, dict):
        status, act = _strava("GET", f"/api/v3/activities/{activity_id}",
                              token=token)
        if status == 429:
            return False, "fetch failed: HTTP 429 (rate limited, will retry)"
        if status != 200:
            return False, f"fetch failed: HTTP {status}"
    block = engine.build_description(
        race.get("race", ""), race.get("date", ""), goal or "",
        dist_km, month_km, year_km, today_iso)
    cleaned = engine.strip_prior_block(str(act.get("description") or ""))
    merged = engine.apply_style(cleaned, block, engine.APPEND)
    if dry:
        return True, merged
    status, _ = _strava("PUT", f"/api/v3/activities/{activity_id}",
                        token=token, params={"description": merged})
    if status == 429:
        return False, "write failed: HTTP 429 (rate limited, will retry)"
    if status != 200:
        return False, f"write failed: HTTP {status}"
    return True, merged


# --------------------------------------------------------------------------
# HTTP handler


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "mynextpr/6"

    def log_message(self, fmt, *args):  # quieter; never log bodies/tokens
        sys.stderr.write("mynextpr: " + fmt % args + "\n")

    def _send(self, code, body, ctype="application/json"):
        raw = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _json(self, code, obj):
        raw = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _redirect(self, location, cookie=""):
        self.send_response(302)
        self.send_header("Location", location)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    @staticmethod
    def _athlete_cookie_value(athlete_id):
        return (f"{ATHLETE_COOKIE}={athlete_id}; Path=/; Max-Age=31536000; "
                "SameSite=Lax")

    @staticmethod
    def _expired_athlete_cookie():
        return f"{ATHLETE_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax"

    # -- static ------------------------------------------------------------
    def _serve_static(self, path):
        rel = urllib.parse.unquote(path.split("?", 1)[0]).lstrip("/")
        if not rel:
            rel = "index.html"
        if rel.startswith(".") or rel.endswith(".py") or ".." in rel:
            self._send(403, "forbidden")
            return
        # Sandbox preview: /v7/* maps to the sibling v7/ dir so the picker
        # gets same-origin data, strava.js, and /api/* in one server.
        if rel == "v7" or rel.startswith("v7/"):
            full = os.path.join(os.path.dirname(ROOT), rel)
        else:
            full = os.path.join(ROOT, rel)
        if not os.path.isfile(full):
            self._send(404, "not found")
            return
        ext = os.path.splitext(full)[1].lower()
        ctype = CONTENT_TYPES.get(ext, "application/octet-stream")
        try:
            with open(full, "rb") as fh:
                raw = fh.read()
        except OSError:
            self._send(404, "not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        if ext == ".mp4":
            self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self.wfile.write(raw)

    # -- routes -------------------------------------------------------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/exchange_token":
            self._handle_exchange(query)
        elif parsed.path == "/api/status":
            self._handle_status()
        elif parsed.path == "/api/export":
            self._handle_export()
        elif parsed.path == "/webhook":
            self._handle_webhook_verify(query)
        else:
            self._serve_static(parsed.path)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except ValueError:
            payload = {}
        if parsed.path == "/api/pause":
            aid = _known_athlete(self)
            if not aid:
                self._json(401, {"ok": False, "detail": "not connected"})
                return
            save_athlete(aid, {"paused": True})
            self._json(200, {"paused": True})
        elif parsed.path == "/api/resume":
            aid = _known_athlete(self)
            if not aid:
                self._json(401, {"ok": False, "detail": "not connected"})
                return
            save_athlete(aid, {"paused": False})
            self._json(200, {"paused": False})
        elif parsed.path == "/api/disconnect":
            aid = _known_athlete(self)
            if not aid:
                self._json(401, {"ok": False, "detail": "not connected"})
                return
            label = _who(aid, load_athlete(aid))
            _revoke_and_clear(aid)
            _notify("⏸️ <b>%s paused out</b>\nDisconnected — tokens revoked, data cleared." %
                    _esc(label))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Set-Cookie", self._expired_athlete_cookie())
            raw = b'{"connected": false}'
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        elif parsed.path == "/api/delete-account":
            aid = _known_athlete(self)
            if not aid:
                self._json(401, {"ok": False, "detail": "not connected"})
                return
            label = _who(aid, load_athlete(aid))
            _revoke_and_clear(aid)
            _notify("🗑️ <b>%s deleted everything</b>\nTokens revoked, all data wiped." %
                    _esc(label))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Set-Cookie", self._expired_athlete_cookie())
            raw = b'{"deleted": true}'
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        elif parsed.path == "/api/support":
            self._handle_support(payload)
        elif parsed.path == "/api/stamp-latest":
            dry = urllib.parse.parse_qs(parsed.query).get("dry", ["0"])[0] == "1"
            self._handle_stamp_latest(dry)
        elif parsed.path == "/api/subscribe":
            self._handle_subscribe()
        elif parsed.path == "/webhook":
            self._handle_webhook_event(payload)
        else:
            self._send(404, "not found")

    # -- OAuth return --------------------------------------------------------
    def _handle_exchange(self, query):
        code = (query.get("code") or [""])[0]
        if (query.get("error") or [""])[0]:
            _notify("🚫 <b>Sign-in declined</b>\nA visitor said no at Strava — no runner added.")
            self._send(400, "Strava sign-in was declined. Go back and try again.",
                        "text/plain; charset=utf-8")
            return
        if not code or not CLIENT_ID or not CLIENT_SECRET:
            self._send(400, "Missing code or server is not configured (.env).",
                        "text/plain; charset=utf-8")
            return
        status, body = _token_request({
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        })
        if status != 200 or not body.get("access_token"):
            _notify("⚠️ <b>Connect failed</b>\nToken swap with Strava returned HTTP %s — "
                    "the code may have expired. Runner asked to try again." % status)
            self._send(502, "Token exchange failed. The code may have expired — connect again.",
                        "text/plain; charset=utf-8")
            return
        race = {}
        raw_state = (query.get("state") or [""])[0]
        try:
            parsed_state = json.loads(raw_state) if raw_state else {}
            if isinstance(parsed_state, dict) and parsed_state.get("race"):
                race = parsed_state
        except ValueError:
            pass
        athlete_id = (body.get("athlete") or {}).get("id", "")
        if not athlete_id:
            me_status, me = _strava(
                "GET", "/api/v3/athlete", token=body.get("access_token", ""))
            if me_status == 200 and me.get("id"):
                athlete_id = me["id"]
        if not athlete_id:
            _notify("⚠️ <b>Connect failed</b>\nStrava returned no athlete id — nothing was set up.")
            self._send(502, "Connected, but Strava did not return an athlete.",
                        "text/plain; charset=utf-8")
            return
        profile = body.get("athlete")
        if not isinstance(profile, dict):
            profile = {}
        firstname = str(profile.get("firstname") or "")
        save_athlete(str(athlete_id), {
            "access_token": body.get("access_token", ""),
            "refresh_token": body.get("refresh_token", ""),
            "expires_at": body.get("expires_at", 0),
            "athlete_id": athlete_id,
            "race": race,
            "paused": False,
        })
        if firstname:
            save_athlete(str(athlete_id), {"firstname": firstname})
        goal = str(race.get("goal") or "")
        _notify("🎉 <b>New runner: %s!</b>\n"
                "🏁 %s (%s)\n"
                "%s\n"
                "🆔 %s" % (
                    _esc(firstname or ("runner " + str(athlete_id))),
                    _esc(str(race.get("race") or "-")),
                    _esc(str(race.get("date") or "?")),
                    ("🎯 Goal %s · %s" % (_esc(goal), _esc(str(race.get("dist") or ""))))
                    if goal else "🎯 No goal time — countdown only",
                    _esc(athlete_id)))
        self._redirect("/manage.html?connected=1",
                       self._athlete_cookie_value(athlete_id))

    # -- status / stamp / subscribe -------------------------------------------
    def _handle_status(self):
        aid = _known_athlete(self)
        state = load_athlete(aid) if aid else {}
        token = _fresh_token(state, aid) if state.get("refresh_token") else ""
        if not token:
            self._json(200, {"connected": False})
            return
        athlete_id, name = _athlete_name(token)
        if not athlete_id:
            self._json(200, {"connected": False})
            return
        month_km, year_km, _ = _run_month_year_totals(token)
        race = state.get("race", {}) if isinstance(state.get("race"), dict) else {}
        days = None
        expired = False
        try:
            if race.get("date"):
                days = engine.days_to_go(race["date"])
                expired = days < 0
        except ValueError:
            pass
        self._json(200, {
            "connected": True,
            "paused": bool(state.get("paused")),
            "athlete": name or str(athlete_id),
            "athlete_id": athlete_id,
            "race": race.get("race", ""),
            "date": race.get("date", ""),
            "city": race.get("city", ""),
            "dist": race.get("dist", ""),
            "days": days,
            "expired": expired,
            "goal": race.get("goal", ""),
            "month_km": month_km,
            "year_km": year_km,
        })

    def _handle_support(self, payload):
        """Private contact form. Messages land in a server-side inbox file
        (git-ignored, read by the operator over SSH) — never published."""
        entry, error = _valid_support(payload)
        if error:
            self._json(400, {"ok": False, "detail": error})
            return
        try:
            os.makedirs(INBOX_DIR, exist_ok=True)
            with open(INBOX_FILE, "a") as fh:
                fh.write(json.dumps(entry) + "\n")
        except OSError:
            self._json(500, {"ok": False, "detail": "could not store message"})
            return
        self._json(200, {"ok": True, "ref": entry["id"]})

    def _handle_export(self):
        """Each user can download everything stored about them."""
        aid = _known_athlete(self)
        if not aid:
            self._json(401, {"ok": False, "detail": "not connected"})
            return
        state = load_athlete(aid)
        self._json(200, {
            "ok": True,
            "athlete_id": state.get("athlete_id", aid),
            "race": state.get("race", {}),
            "paused": bool(state.get("paused")),
            "stamped_activity_ids": sorted(_stamped_ids(state)),
            "note": "Tokens are never included in exports.",
        })

    def _handle_stamp_latest(self, dry):
        aid = _known_athlete(self)
        state = load_athlete(aid) if aid else {}
        token = _fresh_token(state, aid) if state.get("refresh_token") else ""
        if not token:
            self._json(401, {"ok": False, "detail": "not connected"})
            return
        if state.get("paused"):
            self._json(200, {"ok": False, "detail": "paused"})
            return
        race = state.get("race", {}) if isinstance(state.get("race"), dict) else {}
        if not race.get("race") or not race.get("date"):
            self._json(400, {"ok": False, "detail": "no race selected"})
            return
        try:
            if engine.days_to_go(race["date"]) < 0:
                self._json(200, {"ok": False, "detail": "race finished — updates stopped"})
                return
        except ValueError:
            pass
        status, acts = _strava("GET", "/api/v3/athlete/activities",
                               token=token, params={"per_page": 1, "page": 1})
        if status != 200 or not acts:
            self._json(502, {"ok": False, "detail": "no activities found"})
            return
        latest = acts[0] if isinstance(acts, list) else {}
        if str(latest.get("type", "")).lower() not in ("run", "trailrun", ""):
            self._json(200, {"ok": False, "detail": "latest activity is not a run"})
            return
        run_date = str(latest.get("start_date_local") or "")[:10] or None
        month_km, year_km, ref = _run_month_year_totals(
            token, run_date, latest.get("id"), latest.get("distance"))
        ok, detail = _stamp_activity(
            token, latest.get("id"), race, race.get("goal", ""),
            _race_dist_km(race.get("dist"), race.get("race")),
            month_km, year_km, today_iso=ref, dry=dry)
        if ok and not dry and aid:
            _remember_stamped(aid, state, latest.get("id"))
        self._json(200 if ok else 502, {
            "ok": ok, "detail": detail, "activity": latest.get("id"),
            "dry": dry,
        })

    def _handle_subscribe(self):
        if not CLIENT_ID or not CLIENT_SECRET or not VERIFY_TOKEN:
            self._json(400, {"ok": False,
                             "detail": "need CLIENT_ID/SECRET + VERIFY_TOKEN in .env"})
            return
        state = load_state()
        callback = (ENV.get("STRAVA_REDIRECT_URI") or "").rsplit("/", 1)[0] + "/webhook"
        status, body = _strava("POST", "/api/v3/push_subscriptions", params={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "callback_url": callback,
            "verify_token": VERIFY_TOKEN,
        })
        if status not in (200, 201) or not body.get("id"):
            self._json(502, {"ok": False, "detail": f"HTTP {status}: {body}"})
            return
        save_state({"subscription_id": body["id"]})
        self._json(200, {"ok": True, "subscription_id": body["id"]})

    # -- webhooks ---------------------------------------------------------------
    def _handle_webhook_verify(self, query):
        mode = (query.get("hub.mode") or [""])[0]
        token = (query.get("hub.verify_token") or [""])[0]
        challenge = (query.get("hub.challenge") or [""])[0]
        if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
            self._json(200, {"hub.challenge": challenge})
        else:
            self._send(403, "forbidden")

    def _handle_webhook_event(self, payload):
        if not isinstance(payload, dict):
            self._json(400, {"ok": False})
            return
        if payload.get("object_type") == "athlete":
            # Strava sends athlete events when access is revoked
            # (updates: {"authorized": "false"}). Athlete events have no
            # other cause, so any of them drops that athlete's data.
            updates = payload.get("updates", {})
            authorized = updates.get("authorized", "false")
            owner = payload.get("owner_id")
            if owner and str(authorized).lower() != "true":
                label = _who(owner, load_athlete(str(owner)))
                clear_athlete(str(owner))
                _notify("🚪 <b>%s left</b>\nRevoked Strava access — all data purged." %
                        _esc(label))
            self._json(200, {"ok": True, "detail": "athlete removed"})
            return
        if payload.get("object_type") != "activity" or payload.get(
                "aspect_type") not in ("create", "update"):
            self._json(200, {"ok": True, "detail": "ignored"})
            return
        owner = payload.get("owner_id")
        state = load_athlete(str(owner)) if owner else {}
        if not state:
            self._json(200, {"ok": True, "detail": "unknown athlete"})
            return
        token = _fresh_token(state, str(owner)) if state.get("refresh_token") else ""
        if not token or state.get("paused"):
            self._json(200, {"ok": True, "detail": "paused or disconnected"})
            return
        activity_id = payload.get("object_id")
        aspect = payload.get("aspect_type")
        who = _who(owner, state)
        if str(activity_id) in _stamped_ids(state):
            _notify("⏭️ <b>Already stamped</b> — %s\nActivity %s needed nothing." %
                    (_esc(who), _esc(activity_id)))
            self._json(200, {"ok": True, "detail": "already stamped"})
            return
        race = state.get("race", {}) if isinstance(state.get("race"), dict) else {}
        if not race.get("race") or not race.get("date"):
            _notify("⏭️ <b>Skipped</b> — %s\nActivity %s: no race selected yet." %
                    (_esc(who), _esc(activity_id)))
            self._json(200, {"ok": True, "detail": "no race selected"})
            return
        try:
            if engine.days_to_go(race["date"]) < 0:
                _notify("⏭️ <b>Skipped</b> — %s\nActivity %s: race day passed." %
                        (_esc(who), _esc(activity_id)))
                self._json(200, {"ok": True, "detail": "race finished — updates stopped"})
                return
        except ValueError:
            pass
        status, act = _strava("GET", f"/api/v3/activities/{activity_id}", token=token)
        if status == 429:
            detail = "rate limited, will retry on next delivery"
            sys.stderr.write(
                f"mynextpr: webhook 429 for activity {activity_id}\n")
            if _should_notify_429(f"webhook-{activity_id}"):
                _notify("⏳ <b>Rate limited</b> — %s\nActivity %s: %s." %
                        (_esc(who), _esc(activity_id), _esc(detail)))
            self._json(200, {"ok": False, "detail": detail})
            return
        if not isinstance(act, dict):
            act = {}
        if status == 200 and str(act.get("type", "")).lower() not in ("run", "trailrun", ""):
            _notify("⏭️ <b>Skipped</b> — %s\nActivity %s is a %s, not a run." %
                    (_esc(who), _esc(activity_id),
                     _esc(str(act.get("type") or "?"))))
            self._json(200, {"ok": True, "detail": "not a run"})
            return
        run_name = str(act.get("name") or "A run")
        try:
            run_km = float(act.get("distance") or 0) / 1000.0
        except (TypeError, ValueError):
            run_km = 0.0
        run_date = str(act.get("start_date_local") or "")[:10]
        _notify("🔔 <b>Webhook: new activity</b> — %s\n"
                "🏃 “%s” · %.1f km · %s" %
                (_esc(who), _esc(run_name), run_km, _esc(run_date)))
        run_date = str(act.get("start_date_local") or "")[:10] or None
        month_km, year_km, ref = _run_month_year_totals(
            token, run_date, activity_id, act.get("distance"))
        ok, detail = _stamp_activity(
            token, activity_id, race, race.get("goal", ""),
            _race_dist_km(race.get("dist"), race.get("race")),
            month_km, year_km, today_iso=ref,
            act=act if status == 200 else None)
        if ok:
            _remember_stamped(str(owner), state, activity_id)
            days = None
            try:
                days = engine.days_to_go(race["date"])
            except ValueError:
                pass
            goal = str(race.get("goal") or "")
            pace = ""
            try:
                pace = engine.goal_to_pace(
                    goal, _race_dist_km(race.get("dist"), race.get("race"))) if goal else ""
            except Exception:
                pace = ""
            try:
                ref_day = engine.parse_iso_day(ref)
            except ValueError:
                ref_day = datetime.date.today()
            today = ref_day.strftime("%B")
            year = str(ref_day.year)
            _notify("✅ <b>Stamped “%s”</b> — %s\n"
                    "⏳ %s — %s%s\n"
                    "📊 %s so far: %s km · %s so far: %s km" % (
                        _esc(run_name), _esc(who),
                        _esc(_dayword(days)), _esc(str(race.get("race") or "")),
                        (" — target %s%s" % (_esc(goal), (" at %s/km" % _esc(pace)) if pace else ""))
                        if goal else "",
                        _esc(today), _esc(_km(month_km)),
                        _esc(year), _esc(_km(year_km))))
        else:
            sys.stderr.write(
                f"mynextpr: stamp failed for activity {activity_id}: {detail}\n")
            if "429" in str(detail):
                if _should_notify_429(f"stamp-{activity_id}"):
                    _notify("❌ <b>Stamp failed</b> — %s\nActivity %s: %s" %
                            (_esc(who), _esc(activity_id), _esc(detail)))
            else:
                _notify("❌ <b>Stamp failed</b> — %s\nActivity %s: %s" %
                        (_esc(who), _esc(activity_id), _esc(detail)))
        self._json(200, {"ok": ok, "detail": detail})


def main():
    missing = [k for k in ("STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET")
               if not ENV.get(k)]
    if missing:
        sys.stderr.write(f"mynextpr: .env missing {', '.join(missing)}\n")
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"mynextpr backend on http://localhost:{PORT} (serves v6/ + API)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def _self_test():
    """Offline checks: per-athlete isolation, cookies, revocation. No network."""
    import tempfile
    failures = []

    def check(name, cond):
        print(("PASS " if cond else "FAIL ") + name)
        if not cond:
            failures.append(name)

    global ATHLETES_DIR
    real_dir = ATHLETES_DIR
    tmp = tempfile.mkdtemp(prefix="mnp-test-")
    ATHLETES_DIR = tmp
    try:
        check("athlete path digits-only",
              _athlete_path("123") == os.path.join(tmp, "123.json"))
        check("athlete path rejects injection", _athlete_path("../../etc") == "" or
              _athlete_path("../..") == "")
        check("cookie parse", _cookie_athlete("a=1; mnp_athlete=42; b=2") == "42")
        check("cookie empty", _cookie_athlete("") == "")
        check("cookie non-numeric rejected",
              _cookie_athlete("mnp_athlete=abc") == "")

        class _Headers(dict):
            def get(self, key, default=None):
                return super().get(key, default)

        class _Req:
            def __init__(self, cookie):
                self.headers = _Headers(
                    {"Cookie": cookie} if cookie is not None else {})

        check("strict: no cookie resolves to nobody",
              _resolve_athlete(_Req(None)) == "")
        check("strict: wrong cookie never becomes the lone athlete",
              _resolve_athlete(_Req("mnp_athlete=999")) == "999")
        check("strict: own cookie resolves",
              _resolve_athlete(_Req("mnp_athlete=111")) == "111")
        save_athlete("111", {"access_token": "tok111", "race": {"race": "TMM"}})
        save_athlete("222", {"access_token": "tok222", "race": {"race": "DHM"}})
        check("isolated reads",
              load_athlete("111").get("access_token") == "tok111"
              and load_athlete("222").get("access_token") == "tok222")
        save_athlete("111", {"paused": True})
        check("patch preserves token",
              load_athlete("111").get("access_token") == "tok111"
              and load_athlete("111").get("paused") is True)
        check("unknown athlete empty", load_athlete("999") == {})
        check("two athletes listed",
              "111" in list_athlete_ids() and "222" in list_athlete_ids())
        check("escapes html", _esc("<b>&") == "&lt;b&gt;&amp;")
        check("who prefers name",
              _who("42", {"firstname": "Sam"}) == "Sam")
        check("who falls back to id", _who("42", {}) == "runner 42")
        check("dayword plural", _dayword(91) == "91 days to go")
        check("dayword one", _dayword(1) == "1 day to go")
        check("dayword zero", _dayword(0) == "race day today")
        check("km formats", _km(99.8) == "99.8" and _km(None) == "—")
        check("race line full",
              _race_line({"race": "TMM", "date": "2027-01-17",
                          "goal": "4:00", "dist": "Full"})
              == "TMM (2027-01-17) — goal 4:00 Full")
        check("race line sparse", _race_line({"race": "DHM"}) == "DHM")
        check("race line bad input", _race_line(None) == "-")
        real_tele = (ENV.pop("TELEGRAM_BOT_TOKEN", None),
                     ENV.pop("TELEGRAM_CHAT_ID", None))
        try:
            check("notify no-op unconfigured", _notify("test") is None)
            check("notify no-op empty", _notify("") is None)
        finally:
            if real_tele[0] is not None:
                ENV["TELEGRAM_BOT_TOKEN"] = real_tele[0]
            if real_tele[1] is not None:
                ENV["TELEGRAM_CHAT_ID"] = real_tele[1]
        check("minimal scopes locked",
              tuple(MINIMAL_SCOPES) == ("read", "activity:read", "activity:write"))
        check("engine scopes match", tuple(engine.SCOPES) == tuple(MINIMAL_SCOPES))
        clear_athlete("111")
        check("clear drops one athlete",
              load_athlete("111") == {}
              and load_athlete("222").get("access_token") == "tok222")
        import time as _t
        save_athlete("333", {"stamped": {"old": _t.time() - 8 * 86400,
                                         "fresh": _t.time()}})
        _remember_stamped("333", load_athlete("333"), "new")
        ids = _stamped_ids(load_athlete("333"))
        check("7-day prune drops old ids",
              "old" not in ids and "fresh" in ids and "new" in ids)
        save_athlete("444", {"stamped": [111, 222]})
        check("legacy list migrates",
              set(_stamped_ids(load_athlete("444"))) == {"111", "222"})
        clear_athlete("333")
        clear_athlete("444")
        global INBOX_FILE
        real_inbox, INBOX_FILE = INBOX_FILE, os.path.join(tmp, "inbox.jsonl")
        try:
            ok_entry, err = _valid_support({
                "topic": "privacy", "message": "please delete my data please",
                "athlete_id": "12ab34", "contact": "x" * 200})
            check("support accepts valid",
                  err == "" and ok_entry["topic"] == "privacy"
                  and ok_entry["athlete_id"] == "1234"
                  and len(ok_entry["contact"]) == 120)
            _, err = _valid_support({"topic": "spam", "message": "x" * 20})
            check("support rejects bad topic", err != "")
            _, err = _valid_support({"topic": "bug", "message": "short"})
            check("support rejects short message", err != "")
            _, err = _valid_support({"topic": "bug", "message": "x" * 2001})
            check("support rejects long message", err != "")
        finally:
            INBOX_FILE = real_inbox
        global _RATE_LIMITED_UNTIL
        _RATE_LIMITED_UNTIL = 0.0
        with _RATE_LOCK:
            _LAST_429_NOTICE.clear()
        check("reset window sane",
              1 <= _seconds_to_reset(0) <= 905
              and _seconds_to_reset(899) < _seconds_to_reset(0))
        _note_429(None)
        check("429 sets backoff", _rate_limited())
        real_strava = globals()["_strava"]
        check("guard short-circuits api/v3 during backoff",
              real_strava("GET", "/api/v3/athlete", token="x")[0] == 429)
        check("sums degrade to unknown during backoff, never stale",
              _run_month_year_totals("tok-x", "2026-11-15", 10, 3000)[:2]
              == (None, None))
        _RATE_LIMITED_UNTIL = 0.0
        check("period bounds split calendar month and year",
              _period_epochs("2026-11-15")[2] == "2026-11-15"
              and _period_epochs("2026-11-15")[1]
              <= _period_epochs("2026-11-15")[0])
        check("period bounds fall back to today on garbage",
              _period_epochs("not-a-date")[2]
              == datetime.date.today().isoformat())

        def _fake_list(method, path, token=None, params=None, timeout=15):
            if path == "/api/v3/athlete":
                return 200, {"id": 42, "firstname": "Sam", "lastname": "H"}
            page = int((params or {}).get("page", 1))
            if page > 1:
                return 200, []
            return 200, [
                {"id": 7, "type": "Run", "distance": 5000,
                 "start_date_local": "2026-11-01T07:00:00Z"},
                {"id": 8, "type": "Ride", "distance": 20000,
                 "start_date_local": "2026-11-01T08:00:00Z"},
                {"id": 9, "type": "TrailRun", "distance": 12000,
                 "start_date_local": "2026-11-02T07:00:00Z"},
            ]
        try:
            globals()["_strava"] = _fake_list
            m, y, ref = _run_month_year_totals("tok", "2026-11-15", 10, 3000)
            check("sums include the stamped run, skip non-runs",
                  m == 20.0 and y == 20.0 and ref == "2026-11-15")
            m2, _, _ = _run_month_year_totals("tok", "2026-11-15", 7, 5000)
            check("sums never double-count an already listed run",
                  m2 == 17.0)
            check("athlete name resolves",
                  _athlete_name("tok") == (42, "Sam H"))
        finally:
            globals()["_strava"] = real_strava

        def _fake_fail(method, path, token=None, params=None, timeout=15):
            return 500, {}
        try:
            globals()["_strava"] = _fake_fail
            m3, y3, ref3 = _run_month_year_totals(
                "tok", "2026-11-15", 10, 3000)
            check("failed listings degrade to unknown, never stale",
                  (m3, y3) == (None, None) and ref3 == "2026-11-15")
            check("athlete lookup fails closed",
                  _athlete_name("tok") == ("", ""))
        finally:
            globals()["_strava"] = real_strava
        calls = []
        def _fake_strava(method, path, token=None, params=None, timeout=15):
            calls.append((method, path))
            if method == "PUT":
                return 200, {}
            return 200, {"description": "prior"}
        try:
            globals()["_strava"] = _fake_strava
            ok, _ = _stamp_activity(
                "tok-z", "1",
                {"race": "TMM", "date": "2027-01-17"},
                "4:00", 42.195, 42.0, 310.0,
                act={"description": "prior", "type": "Run"})
            check("stamp reuses pre-fetched activity (one PUT, no GET)",
                  ok and calls == [("PUT", "/api/v3/activities/1")])
        finally:
            globals()["_strava"] = real_strava
        check("429 notice dedupes",
              _should_notify_429("selftest-429") is True
              and _should_notify_429("selftest-429") is False)
        with _RATE_LOCK:
            _LAST_429_NOTICE.clear()
        _RATE_LIMITED_UNTIL = 0.0
    finally:
        ATHLETES_DIR = real_dir
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{'ALL PASS' if not failures else 'FAILURES: ' + str(len(failures))}")
    return 1 if failures else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    main()
