"""Fix 2a: no recurring poller/backup scan in v6/server.py (Strava review fixes).

RED/GREEN: fails while _poller exists, passes after removal.
Run: python3 tests/strava-review/test_no_poller.py
"""
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = (REPO / "v6" / "server.py").read_text()

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


check("no _poller definition", "def _poller" not in SRC)
check("no interval_seconds scheduler", "interval_seconds" not in SRC)
check("no time.sleep scan loop", "time.sleep" not in SRC)
check("HTTP threading retained", "ThreadingHTTPServer" in SRC)
check("threading import retained", "import threading" in SRC)

print(f"\n{len(failures)} failure(s)")
raise SystemExit(1 if failures else 0)
