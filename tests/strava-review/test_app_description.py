"""Fix 1: Strava app description alignment (Strava review fixes).

RED/GREEN: fails before the approval-pack edit, passes after.
Run: python3 tests/strava-review/test_app_description.py
"""
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
PACK = REPO / "strava-application" / "06-approval-pack.md"

SENTENCE_1 = "mynextpr adds a countdown to your chosen race to the description of your Strava runs."
SENTENCE_2 = "Activity titles are never changed."

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


text = PACK.read_text()

check("pack file exists", PACK.exists())
check("exact sentence 1 present", SENTENCE_1 in text)
check("exact sentence 2 present", SENTENCE_2 in text)
check(
    "no unsupported 48-hour deletion promise",
    "48-hour" not in text,
    "email draft must match privacy.html (promptly, always within 30 days)",
)

print(f"\n{len(failures)} failure(s)")
raise SystemExit(1 if failures else 0)
