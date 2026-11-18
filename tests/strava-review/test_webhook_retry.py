"""Fix pass: webhook answers retryable codes on transient failure (review issue 1).

Deliberate skips stay HTTP 200 (no pointless Strava retry); transient
failures (429, 5xx fetch/write) answer non-2xx so Strava redelivers.
Run: python3 tests/strava-review/test_webhook_retry.py
"""
import json
import pathlib
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "v6"))

import server  # noqa: E402

failures = []
RUN = {"id": 999, "type": "Run", "name": "Morning Run", "distance": 5000.0,
       "start_date_local": "2027-01-10T06:03:00Z", "description": "My notes."}
RACE = {"race": "Example Harbor 10K", "date": "2027-04-18", "goal": ""}

tmp = tempfile.mkdtemp(prefix="mnp-retry-")
server.ATHLETES_DIR = tmp
pathlib.Path(tmp, "42.json").write_text(json.dumps({
    "access_token": "tok", "refresh_token": "r", "expires_at": 9999999999,
    "race": RACE, "paused": False}))

mode = {"get": "ok", "put": "ok"}


def reset_state(paused=False):
    pathlib.Path(tmp, "42.json").write_text(json.dumps({
        "access_token": "tok", "refresh_token": "r", "expires_at": 9999999999,
        "race": RACE, "paused": paused}))


def fake_strava(method, path, token=None, params=None, timeout=15):
    if method == "GET" and path.startswith("/api/v3/activities/"):
        if mode["get"] == "429":
            return 429, {}
        if mode["get"] == "500":
            return 500, {"_error": "boom"}
        return 200, dict(RUN)
    if method == "GET":
        return 200, [dict(RUN, id=999)]
    if method == "PUT":
        if mode["put"] == "500":
            return 500, {"_error": "boom"}
        if mode["put"] == "404":
            return 404, {"_error": "gone"}
        return 200, {}
    if path == "/oauth/token":
        return 200, {"access_token": "tok", "refresh_token": "r",
                     "expires_at": 9999999999}
    return 404, {}


server._strava = fake_strava


def call(payload):
    captured = {}
    h = server.Handler.__new__(server.Handler)
    h._json = lambda code, obj: captured.update(code=code, obj=obj)
    h._handle_webhook_event(payload)
    return captured.get("code"), captured.get("obj", {})


def base(**kw):
    p = {"object_type": "activity", "aspect_type": "create",
         "owner_id": 42, "object_id": 999}
    p.update(kw)
    return p


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not failures or True:
        pass
    if not cond:
        failures.append(name)


reset_state()
mode.update(get="ok", put="ok")
code, obj = call(base())
check("success stamps with 200", code == 200 and obj.get("ok") is True, f"{code} {obj}")

reset_state()
mode.update(get="429", put="ok")
code, obj = call(base())
check("429 pre-read asks Strava to retry", code == 429, f"{code} {obj}")

reset_state()
mode.update(get="500", put="ok")
code, obj = call(base())
check("5xx fetch asks Strava to retry", code == 502, f"{code} {obj}")

reset_state()
mode.update(get="ok", put="500")
code, obj = call(base())
check("5xx write asks Strava to retry", code == 502, f"{code} {obj}")

reset_state()
mode.update(get="ok", put="404")
code, obj = call(base())
check("permanent write failure stays 200", code == 200 and obj.get("ok") is False, f"{code} {obj}")

mode.update(get="ok", put="ok")
reset_state(paused=True)
code, obj = call(base())
check("paused athlete stays 200", code == 200, f"{code} {obj}")

print(f"\n{len(failures)} failure(s)")
raise SystemExit(1 if failures else 0)
