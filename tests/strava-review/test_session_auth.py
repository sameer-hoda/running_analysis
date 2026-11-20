"""Problem 1: unforgeable server sessions replace the public-ID cookie.

Design: opaque session (hashed at rest, 0600 files), HttpOnly+Secure+
SameSite session cookie, one CSRF token per session, HMAC nonce binding
the OAuth round-trip to the initiating browser. Legacy ID cookies are
never trusted; fresh login required.
Isolated: temp copy of v6/, fresh dummy athletes, ALL outbound Strava
calls mocked (any unexpected call raises). Loopback only.
Run: python3 tests/strava-review/test_session_auth.py
"""
import http.client
import http.server
import json
import pathlib
import shutil
import sys
import tempfile
import threading
import urllib.parse

REPO = pathlib.Path(__file__).resolve().parents[2]
TMP = pathlib.Path(tempfile.mkdtemp(prefix="mnp-auth-"))
shutil.copytree(REPO / "v6", TMP / "v6",
                ignore=shutil.ignore_patterns(".athletes", "__pycache__",
                                             ".tokens.json", "*.log"))
sys.path.insert(0, str(TMP / "v6"))
import server  # noqa: E402  (isolated temp copy)

failures = []
DUMMY_A = {"access_token": "tok-a", "refresh_token": "ref-a",
           "expires_at": 9999999999, "athlete_id": 42,
           "race": {"race": "Example Harbor 10K", "date": "2027-04-18",
                    "goal": ""}, "paused": False}
DUMMY_B = {"access_token": "tok-b", "refresh_token": "ref-b",
           "expires_at": 9999999999, "athlete_id": 7,
           "race": {"race": "Example Bay 5K", "date": "2027-05-01",
                    "goal": ""}, "paused": False}
OUTBOUND = []


def fake_strava(method, path, token=None, params=None, timeout=15):
    OUTBOUND.append((method, path))
    if path == "/oauth/token":
        return (200, {"access_token": "tok-a", "refresh_token": "ref-a",
                       "expires_at": 9999999999,
                       "athlete": {"id": 42, "firstname": "Demo"}})
    if path == "/api/v3/athlete":
        return 200, {"id": 42, "firstname": "Demo", "lastname": "Runner"}
    if path == "/oauth/deauthorize":
        return 200, {}
    if method == "GET":
        return 200, []
    if method == "PUT":
        return 200, {}
    raise AssertionError("unexpected outbound call: %s %s" % (method, path))


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


server._strava = fake_strava
server.CLIENT_ID = "test-id"
server.CLIENT_SECRET = "test-secret"
(TMP / "v6" / ".athletes").mkdir(exist_ok=True)
(TMP / "v6" / ".athletes" / "42.json").write_text(json.dumps(DUMMY_A))
(TMP / "v6" / ".athletes" / "7.json").write_text(json.dumps(DUMMY_B))

httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
httpd.daemon_threads = True
threading.Thread(target=httpd.serve_forever, daemon=True).start()
PORT = httpd.server_address[1]


def req(method, path, cookie=None, origin=None, body=None, headers=None):
    c = http.client.HTTPConnection("127.0.0.1", PORT, timeout=10)
    h = dict(headers or {})
    if cookie:
        h["Cookie"] = cookie
    if origin is not None:
        h["Origin"] = origin
    raw = json.dumps(body).encode() if body is not None else None
    if raw is not None:
        h["Content-Type"] = "application/json"
        h["Content-Length"] = str(len(raw))
    c.request(method, path, body=raw, headers=h)
    r = c.getresponse()
    data = r.read()
    try:
        payload = json.loads(data or b"{}")
    except ValueError:
        payload = {}
    cookies = [v for k, v in r.getheaders() if k.lower() == "set-cookie"]
    return r.status, payload, cookies, r


def cookie_val(cookies, name):
    for c in cookies:
        for part in c.split(";"):
            k, _, v = part.partition("=")
            if k.strip() == name:
                return v.strip(), c
    return "", ""


def login(state_obj, nonce_cookie):
    state = urllib.parse.quote(json.dumps(state_obj), safe="")
    return req("GET", "/exchange_token?code=dummy&state=" + state,
               cookie=("mnp_oauth=" + nonce_cookie) if nonce_cookie else None)


ID_COOKIE = "mnp_athlete=42"

# A. Legacy public-ID cookie must no longer authenticate.
# Status stays 200 + connected:false for logged-out browsers (page contract);
# it must never report connected with the forged ID.
code, payload, _, _ = req("GET", "/api/status", cookie=ID_COOKIE)
check("legacy ID cookie rejected: GET /api/status",
      code == 200 and payload.get("connected") is not True
      and "athlete_id" not in payload, "%s %s" % (code, payload))
for method, path, body in (("GET", "/api/export", None),
                            ("POST", "/api/pause", {})):
    code, _, _, _ = req(method, path, cookie=ID_COOKIE, body=body)
    check("legacy ID cookie rejected: %s %s" % (method, path),
          code in (401, 403), "got %s" % code)

# B. Forged session rejected.
code, _, _, _ = req("GET", "/api/export",
                    cookie="mnp_session=" + "x" * 43)
check("forged session rejected", code in (401, 403), "got %s" % code)

# C0. Login without a bound nonce is refused.
code, _, _, _ = req("GET", "/exchange_token?code=dummy&state=" +
                    urllib.parse.quote(json.dumps({"race": "X"}), safe=""))
check("nonce-less login refused", code == 400, "got %s" % code)

# C. Verified OAuth login issues hardened cookies.
_, _, page_cookies, _ = req("GET", "/index.html")
nonce, _ = cookie_val(page_cookies, "mnp_oauth")
check("page sets oauth nonce cookie", bool(nonce), str(page_cookies))
st = {"race": "Example Harbor 10K", "date": "2027-04-18", "goal": "",
      "nonce": nonce}
code, _, login_cookies, _ = login(st, nonce)
check("login redirects", code == 302, "got %s" % code)
sess_tok, sess_full = cookie_val(login_cookies, "mnp_session")
check("session cookie HttpOnly", "httponly" in sess_full.lower(), sess_full)
check("session cookie Secure", "secure" in sess_full.lower(), sess_full)
check("session cookie SameSite", "samesite" in sess_full.lower(), sess_full)
csrf_tok, csrf_full = cookie_val(login_cookies, "mnp_csrf")
check("csrf cookie issued (readable)", bool(csrf_tok) and "httponly" not in csrf_full.lower(), str(login_cookies))
legacy, legacy_full = cookie_val(login_cookies, "mnp_athlete")
check("legacy ID cookie killed", "max-age=0" in legacy_full.lower(), str(login_cookies))
sess_cookie = "mnp_session=" + sess_tok
CSRF_H = {"X-CSRF-Token": csrf_tok}

# C3. Replay of the same callback URL fails (single-use nonce).
code, _, _, _ = login(st, nonce)
check("replayed callback refused", code == 400, "got %s" % code)

# C2. Secrets hashed at rest with owner-only permissions.
sfiles = list((TMP / "v6" / ".sessions").glob("*.json"))
check("exactly one session stored", len(sfiles) == 1, str(sfiles))
blob = sfiles[0].read_text() if sfiles else ""
check("raw session token not on disk", sess_tok not in blob, blob[:120])
check("raw csrf token not on disk", csrf_tok not in blob, blob[:120])
import stat  # noqa: E402
mode = oct(sfiles[0].stat().st_mode & 0o777) if sfiles else ""
check("session file is 0600", mode == "0o600", mode)

# D. Session authenticates its own athlete only.
code, status, _, _ = req("GET", "/api/status", cookie=sess_cookie)
check("session sees own status",
      code == 200 and status.get("connected") is True
      and status.get("race") == "Example Harbor 10K",
      "%s %s" % (code, status))
code, export, _, _ = req("GET", "/api/export", cookie=sess_cookie)
check("session sees own export",
      code == 200 and export.get("race", {}).get("race") == "Example Harbor 10K",
      "%s %s" % (code, export))
check("export carries no tokens",
      "tok-a" not in json.dumps(export) and "ref-a" not in json.dumps(export),
      str(export))

# D2. Writes need the per-session CSRF token.
code, _, _, _ = req("POST", "/api/pause", cookie=sess_cookie, body={})
check("write without csrf token rejected", code == 403, "got %s" % code)
code, _, _, _ = req("POST", "/api/pause", cookie=sess_cookie, body={},
                    headers={"X-CSRF-Token": "wrong"})
check("write with wrong csrf token rejected", code == 403, "got %s" % code)
code, paused, _, _ = req("POST", "/api/pause", cookie=sess_cookie, body={},
                         headers=CSRF_H)
check("write with csrf token pauses",
      code == 200 and paused.get("paused") is True, "%s %s" % (code, paused))
code, resumed, _, _ = req("POST", "/api/resume", cookie=sess_cookie, body={},
                          headers=CSRF_H)
check("write with csrf token resumes",
      code == 200 and resumed.get("paused") is False, "%s %s" % (code, resumed))

# F. Logout invalidates the session.
code, _, _, _ = req("POST", "/api/disconnect", cookie=sess_cookie, body={},
                    headers=CSRF_H)
check("disconnect clears", code == 200, "got %s" % code)
code, _, _, _ = req("GET", "/api/export", cookie=sess_cookie)
check("session dead after disconnect", code in (401, 403), "got %s" % code)
(TMP / "v6" / ".athletes" / "42.json").write_text(json.dumps(DUMMY_A))
_, _, page_cookies, _ = req("GET", "/index.html")
nonce2, _ = cookie_val(page_cookies, "mnp_oauth")
st2 = dict(st, nonce=nonce2)
code, _, login_cookies, _ = login(st2, nonce2)
sess2, _ = cookie_val(login_cookies, "mnp_session")
csrf2, _ = cookie_val(login_cookies, "mnp_csrf")
sess_cookie2 = "mnp_session=" + sess2

# G. Expired sessions rejected.
import time  # noqa: E402
for f in (TMP / "v6" / ".sessions").glob("*.json"):
    rec = json.loads(f.read_text())
    if rec.get("athlete_id") == "42":
        rec["expires"] = time.time() - 1
        f.write_text(json.dumps(rec))
code, _, _, _ = req("GET", "/api/export", cookie=sess_cookie2)
check("expired session rejected", code in (401, 403), "got %s" % code)

# H. Restart-safe: reimport keeps honoring the live session file.
(TMP / "v6" / ".athletes" / "42.json").write_text(json.dumps(DUMMY_A))
_, _, page_cookies, _ = req("GET", "/index.html")
nonce3, _ = cookie_val(page_cookies, "mnp_oauth")
st3 = dict(st, nonce=nonce3)
code, _, login_cookies, _ = login(st3, nonce3)
sess3, _ = cookie_val(login_cookies, "mnp_session")
import importlib  # noqa: E402
importlib.reload(server)
server._strava = fake_strava
server.CLIENT_ID = "test-id"
server.CLIENT_SECRET = "test-secret"
code, status3, _, _ = req("GET", "/api/status",
                          cookie="mnp_session=" + sess3)
check("session survives restart",
      code == 200 and status3.get("connected") is True, "got %s" % code)

# P. Reconnect preserves race, goal, paused and stamping history.
RICH = {"access_token": "old-a", "refresh_token": "old-r",
        "expires_at": 9999999999, "athlete_id": 42,
        "race": {"race": "Example Harbor 10K", "date": "2027-04-18",
                 "goal": "sub-50"},
        "paused": True, "stamped": {"999": 1234567890, "998": 1234567800}}
(TMP / "v6" / ".athletes" / "42.json").write_text(json.dumps(RICH))
_, _, page_cookies, _ = req("GET", "/index.html")
nonce_p, _ = cookie_val(page_cookies, "mnp_oauth")
code, _, _, _ = login({"nonce": nonce_p}, nonce_p)
check("raceless reconnect still logs in", code == 302, "got %s" % code)
after = json.loads((TMP / "v6" / ".athletes" / "42.json").read_text())
check("race preserved on reconnect",
      after.get("race") == RICH["race"], str(after.get("race")))
check("goal preserved on reconnect",
      after.get("race", {}).get("goal") == "sub-50", str(after.get("race")))
check("paused preserved on reconnect",
      after.get("paused") is True, str(after.get("paused")))
check("stamping history preserved on reconnect",
      after.get("stamped") == RICH["stamped"], str(after.get("stamped")))
check("tokens refreshed on reconnect",
      after.get("access_token") == "tok-a", str(after.get("access_token")))
# Fresh race choice still adopts + unpauses.
_, _, page_cookies, _ = req("GET", "/index.html")
nonce_q, _ = cookie_val(page_cookies, "mnp_oauth")
new_race = {"race": "Example Bay 5K", "date": "2027-05-01", "goal": "sub-30",
            "nonce": nonce_q}
code, _, _, _ = login(new_race, nonce_q)
after2 = json.loads((TMP / "v6" / ".athletes" / "42.json").read_text())
check("new race choice adopted",
      after2.get("race", {}).get("race") == "Example Bay 5K",
      str(after2.get("race")))
check("new race choice unpauses",
      after2.get("paused") is False, str(after2.get("paused")))
check("stamping history survives race change",
      after2.get("stamped") == RICH["stamped"], str(after2.get("stamped")))

# I. Strava deauthorization wipes sessions too.
h = server.Handler.__new__(server.Handler)
captured = {}
h._json = lambda code_, obj: captured.update(code=code_, obj=obj)
h._handle_webhook_event({"object_type": "activity", "owner_id": 42,
                         "aspect_type": "create", "object_id": 1})
h._handle_webhook_event({"object_type": "athlete", "owner_id": 42,
                         "updates": {"authorized": "false"}})
code, _, _, _ = req("GET", "/api/export", cookie="mnp_session=" + sess3)
check("deauth kills sessions", code in (401, 403), "got %s" % code)

print("outbound Strava calls (all mocked): %d" % len(OUTBOUND))
print("\n%s failure(s)" % len(failures))
shutil.rmtree(TMP, ignore_errors=True)
raise SystemExit(1 if failures else 0)
