"""Fix 3: legacy mynextpr repo no longer claims to be live at mynextpr.com.

RED/GREEN: fails until the banner patch file exists with the required
removals/additions. The patch is applied in the legacy checkout by the
owner (no commit/push here). Never touches repo settings.
Run: python3 tests/strava-review/test_legacy_runform.py
"""
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
PATCH = REPO / "docs" / "superpowers" / "plans" / "mynextpr-legacy-banner.patch"

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


check("patch file exists", PATCH.exists())
text = PATCH.read_text() if PATCH.exists() else ""
check("patch removes Live-at-mynextpr claim",
      "-  <strong>Live at <a href=\"https://mynextpr.com\">mynextpr.com</a></strong>" in text)
check("patch removes live-site badge", "-  <a href=\"https://mynextpr.com\"><img" in text)
check("patch adds legacy identifier", "+  <strong>RunForm (legacy)</strong>" in text)
check("patch states not the live site", "not the site live at mynextpr.com" in text)
check("patch touches README only, no settings",
      ("README.md" in text) and ("settings" not in text.lower()),
      "scope must stay README-only")

print(f"\n{len(failures)} failure(s)")
raise SystemExit(1 if failures else 0)
