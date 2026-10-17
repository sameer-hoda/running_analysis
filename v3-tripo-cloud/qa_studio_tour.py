#!/usr/bin/env python3
"""Studio tour regression QA (Playwright, headless Chrome).

Covers: no colour-key step in the studio story, streamlined voiceover text,
score-only focus badge, removed caption component, single-voice step changes,
4x turntable while the coach speaks. Uses only the demo + a textured job.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE = os.environ.get("QA_BASE", "http://127.0.0.1:8139")
FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail)[:160] if detail else ""), flush=True)
    if not ok:
        FAILS.append(name)


def pxdiff(pg, ms=5000):
    pg.wait_for_timeout(500)
    a = pg.screenshot()
    pg.wait_for_timeout(ms)
    b = pg.screenshot()
    open("/tmp/qa_spin_a.png", "wb").write(a)
    open("/tmp/qa_spin_b.png", "wb").write(b)
    from PIL import Image, ImageChops
    d = ImageChops.difference(Image.open("/tmp/qa_spin_a.png").convert("L"),
                             Image.open("/tmp/qa_spin_b.png").convert("L"))
    return sum(d.histogram()[16:])


with sync_playwright() as pw:
    browser = pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required", "--mute-audio"])
    pg = browser.new_page(viewport={"width": 1280, "height": 800})
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))

    pg.goto(BASE + "/report/demo", wait_until="networkidle")
    pg.wait_for_timeout(4000)

    story = pg.evaluate("""() => buildStory().map(s => ({kind: s.kind, text: s.text}))""")
    kinds = [s["kind"] for s in story]
    check("story has no colour-key step", "colors" not in kinds, ",".join(kinds))
    check("story order overview+3 focus+free",
          kinds == ["overview", "focus", "focus", "focus", "free"], ",".join(kinds))
    check("no repeated card line", all("pulled up" not in s["text"] for s in story))
    check("caption component removed", pg.evaluate("() => !document.getElementById('cap')"))

    pg.click(".zrow")
    pg.wait_for_timeout(1200)
    tip = pg.evaluate("""() => { const t = document.getElementById('tip');
      const b = t.getBoundingClientRect();
      return {visible: b.width > 0, text: t.textContent.trim(),
              words: !!t.querySelector('.tn') || !!t.querySelector('.ts')}; }""")
    check("focus badge is score-only", tip["visible"] and not tip["words"]
          and tip["text"].strip().isdigit(), str(tip))

    # single voice under rapid step changes (whatever engine speaks, >1 is a fail)
    pg.evaluate("() => document.getElementById('tourCtl').style.display='flex'")
    pg.click("#tourPlay")
    pg.wait_for_timeout(4000)
    for _ in range(3):
        pg.click("#tourNext")
        pg.wait_for_timeout(600)
    pg.click("#tourPrev")
    pg.wait_for_timeout(1200)
    voice = pg.evaluate("""() => { const els = [...document.querySelectorAll('audio')];
      return els.filter(a => !a.paused && !a.ended).length; }""")
    step = pg.evaluate("() => document.getElementById('tourStep').textContent")
    check("at most one voice playing after rapid steps", voice <= 1, f"playing={voice} step={step}")

    # 4x spin while touring (muted so steps advance silently) vs idle base speed
    pg.evaluate("() => window.COACH.setMuted(true)")
    pg.wait_for_timeout(2500)
    tour_px = pxdiff(pg)
    pg.evaluate("() => document.getElementById('tourStop').click()")
    pg.wait_for_timeout(3000)
    idle_px = pxdiff(pg)
    ratio = tour_px / max(1, idle_px)
    check("tour spin clearly faster than idle", ratio > 1.5,
          f"tour={tour_px}px idle={idle_px}px ratio={ratio:.1f}x")

    check("zero console errors", len(errs) == 0, "; ".join(errs[:3]))
    browser.close()

print(f"\nQA: {'ALL PASS' if not FAILS else f'{len(FAILS)} FAIL: {FAILS}'}", flush=True)
sys.exit(1 if FAILS else 0)
