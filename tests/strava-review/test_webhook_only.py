"""Fix 2b: webhook stamping works with zero periodic reads (Strava review fixes).

Mocked proof: _stamp_activity reuses the webhook pre-read (no GET),
PUTs description-only params, preserves the athlete's own text, and
re-stamping never stacks blocks (self-triggered update loop guard).
Run: python3 tests/strava-review/test_webhook_only.py
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "v6"))

import update_engine as engine  # noqa: E402
import server  # noqa: E402

failures = []
calls = {"get": 0, "put": []}

RACE = {"race": "Example Harbor 10K", "date": "2027-04-18", "goal": "sub-50"}
OWN_TEXT = "Easy morning run, felt great."
PRIOR_BLOCK = engine.build_description(
    "Example Harbor 10K", "2027-04-18", "sub-50", 10.0, 42.0, 610.0,
    today_iso="2027-01-10")


def fake_strava(method, path, token=None, params=None, timeout=15):
    if method == "GET":
        calls["get"] += 1
        return 200, {"id": 999, "type": "Run", "name": "Morning Run",
                     "distance": 5000.0, "start_date_local": "2027-01-10T06:03:00Z",
                     "description": OWN_TEXT}
    if method == "PUT":
        calls["put"].append(params or {})
        return 200, {}
    return 404, {}


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


server._strava = fake_strava

# 1. Webhook pre-read path: act passed in -> zero GET reads, one PUT.
act = {"id": 999, "type": "Run", "name": "Morning Run", "distance": 5000.0,
       "start_date_local": "2027-01-10T06:03:00Z", "description": OWN_TEXT}
ok, merged = server._stamp_activity("tok", 999, RACE, RACE["goal"], 10.0,
                                    42.0, 610.0, today_iso="2027-01-10", act=act)
check("stamp ok via webhook pre-read", ok is True, merged)
check("zero GET reads on webhook path", calls["get"] == 0, str(calls))
check("exactly one PUT write", len(calls["put"]) == 1, str(calls))
params = calls["put"][0] if calls["put"] else {}
check("PUT is description-only", set(params) == {"description"}, str(set(params)))
check("athlete's own text preserved", OWN_TEXT in merged, merged)
check("countdown block present", "days to go" in merged, merged)

# 2. Duplicate/concurrent delivery: re-stamping the stamped text stacks nothing.
restamped = engine.apply_style(
    engine.strip_prior_block(merged),
    engine.build_description("Example Harbor 10K", "2027-04-18", "sub-50",
                             10.0, 42.0, 610.0, today_iso="2027-01-10"),
    engine.APPEND)
check("re-stamp keeps one countdown block",
      restamped.count("days to go") == 1, restamped)
check("re-stamp keeps own text once", restamped.count(OWN_TEXT) == 1, restamped)

# 3. Failed fetch degrades to an error, never a corrupt write.
server._strava = lambda *a, **k: (500, {})
ok2, detail2 = server._stamp_activity("tok", 999, RACE, RACE["goal"], 10.0,
                                      42.0, 610.0, today_iso="2027-01-10")
check("failed fetch returns not-ok", ok2 is False, detail2)
check("failed fetch reports status", "500" in detail2, detail2)

print(f"\n{len(failures)} failure(s)")
raise SystemExit(1 if failures else 0)
