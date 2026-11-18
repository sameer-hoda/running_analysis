"""Fix 4: public demo content is fictional and clearly labelled (Strava review fixes).

RED/GREEN: fails on real names / expired hard-coded demo race, passes after.
Run: python3 tests/strava-review/test_demo_content.py
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


pages = {p.name: p.read_text() for p in
         [V6 / "index.html", V6 / "hero.html", V6 / "manage.html",
          V6 / "connect.html", V6 / "picker.html", V6 / "goal.html"]}
blob = "\n".join(pages.values())

check("no real name in pages", "sameer" not in blob.lower())
check("no Delhi Half in hero demo", "Delhi Half" not in pages["hero.html"])
check("no Delhi Half in manage demo", "Delhi Half" not in pages["manage.html"])
check("no expired hard-coded demo date in manage",
      "18 Oct 2026" not in pages["manage.html"])
check("manage demo is labelled", "demo" in pages["manage.html"].lower())
check("hero mock framing retained", "MOCK" in pages["hero.html"])
check("no real name in meta/preview text",
      "sameer" not in "\n".join(
          l for t in pages.values() for l in t.splitlines()
          if "meta" in l.lower() or "og:" in l.lower()).lower())

print(f"\n{len(failures)} failure(s)")
raise SystemExit(1 if failures else 0)
