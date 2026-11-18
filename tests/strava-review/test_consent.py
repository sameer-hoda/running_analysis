"""GA consent hygiene: opt-in only, no pre-consent loading (Strava review fixes).

RED/GREEN: fails while pages auto-load gtag, passes after consent.js gating.
Run: python3 tests/strava-review/test_consent.py
"""
import glob
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
V6 = REPO / "v6"

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


pages = {pathlib.Path(p).name: pathlib.Path(p).read_text()
         for p in glob.glob(str(V6 / "*.html"))}
consent = (V6 / "consent.js").read_text() if (V6 / "consent.js").exists() else ""

check("consent.js exists", bool(consent))
check("measurement ID retained", "G-B63L6BJZLY" in consent)
check("no page hard-loads googletagmanager",
      not any("googletagmanager.com/gtag/js" in t for t in pages.values()))
check("no page auto-configs analytics",
      not any("gtag('config'" in t or 'gtag("config"' in t
              for t in pages.values()))
check("no analytics events with data anywhere",
      "gtag('event'" not in consent and
      not any("gtag('event'" in t for t in pages.values()))
check("page URL query stripped before send",
      "page_location" in consent and "pathname" in consent)
check("opt-in API present",
      all(s in consent for s in ("mnpConsent", "grant", "deny")))
check("choice persisted",
      "mnp.analytics" in consent and "localStorage" in consent)
check("privacy page offers change of choice",
      "mnpConsent" in pages.get("privacy.html", ""))
check("essential login independent of consent",
      "mnp_athlete" in (REPO / "v6" / "server.py").read_text() and
      "mynextpr.connected" in pages.get("callback.html", "") and
      "mynextpr.connected" in pages.get("manage.html", "") and
      "mnpConsent" not in (REPO / "v6" / "strava.js").read_text() and
      "mnp.analytics" not in (REPO / "v6" / "strava.js").read_text())

print(f"\n{len(failures)} failure(s)")
raise SystemExit(1 if failures else 0)
