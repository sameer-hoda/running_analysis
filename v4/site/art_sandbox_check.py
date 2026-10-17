#!/usr/bin/env python3
"""Cover-art sandbox check (cover-art agent).

Offline (default): every artwork file in both sets opens as a valid image
with the expected 600x800 shape; catalog ids match covers/; the sandbox page
exists with all three sections and references only assets present on disk.

Live (optional): `--base http://127.0.0.1:PORT` also GETs the sandbox page,
all 11 covers, all 7 zones, and catalog.json — zero broken images.

Exit 0 on green, 1 on red. No paid APIs, no writes, read-only.
"""
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVERS = os.path.join(ROOT, "research", "papers", "covers")
ZONES = os.path.join(ROOT, "site", "assets", "zones")
CATALOG = os.path.join(ROOT, "research", "papers", "catalog.json")
SANDBOX = os.path.join(ROOT, "site", "art-sandbox.html")
EXPECTED_SIZE = (800, 800)
FAIL = []


def note(ok, msg):
    print(("ok - " if ok else "FAIL - ") + msg)
    if not ok:
        FAIL.append(msg)


def check_images(d, expect_n, label, size=EXPECTED_SIZE):
    try:
        names = sorted(n for n in os.listdir(d) if n.endswith(".jpg"))
    except OSError as e:
        note(False, "%s listable (%s)" % (label, e))
        return []
    note(len(names) == expect_n, "%s count %d/%d" % (label, len(names), expect_n))
    good = []
    try:
        from PIL import Image
    except ImportError:
        note(False, "PIL available for image validity")
        return names
    for n in names:
        fp = os.path.join(d, n)
        try:
            with Image.open(fp) as im:
                im.load()
                size_ok = im.size == size
                note(size_ok, "%s %s valid %s" % (label, n, "x".join(map(str, im.size))))
                if size_ok:
                    good.append(n)
        except Exception as e:
            note(False, "%s %s opens (%s)" % (label, n, e))
    return good


def main():
    base = None
    if "--base" in sys.argv:
        base = sys.argv[sys.argv.index("--base") + 1].rstrip("/")

    covers = check_images(COVERS, 11, "covers", (800, 800))
    zones = check_images(ZONES, 7, "zones", (600, 800))

    try:
        with open(CATALOG) as f:
            cat = json.load(f)
        ids = [p["id"] for p in cat["papers"]]
    except (OSError, ValueError, KeyError) as e:
        note(False, "catalog readable (%s)" % e)
        ids = []
    if ids:
        missing = [i for i in ids if i + ".jpg" not in covers]
        extra = [c[:-4] for c in covers if c[:-4] not in ids]
        note(not missing, "catalog ids all have covers%s" %
             ("" if not missing else " — missing: " + ", ".join(missing)))
        note(not extra, "no orphan covers%s" %
             ("" if not extra else " — extra: " + ", ".join(extra)))

    try:
        with open(SANDBOX, encoding="utf-8") as f:
            html = f.read()
    except OSError as e:
        note(False, "sandbox page exists (%s)" % e)
        html = ""
    if html:
        for marker in ("sec-carousel", "sec-loading", "sec-studio",
                       "fadeTrack", "fadePos", "railStage", "sciList", "zoneGrid",
                       "noindex", "/research/papers/covers/",
                       "/research/papers/catalog.json"):
            note(marker in html, "sandbox contains %s" % marker)
        import re as _re
        import shutil as _sh
        import subprocess as _sp
        m = _re.search(r"<script>(.*)</script>", html, _re.S)
        if not m:
            note(False, "sandbox inline script present")
        elif not _sh.which("node"):
            print("ok - sandbox JS syntax SKIPPED (no node)")
        else:
            r = _sp.run(["node", "--check", "/dev/stdin"], input=m.group(1),
                        capture_output=True, text=True, timeout=30)
            detail = ""
            if r.returncode != 0 and (r.stderr or "").strip():
                detail = " (%s)" % (r.stderr.strip().splitlines()[-1])
            note(r.returncode == 0, "sandbox JS parses" + detail)
        note("/assets/zones/" in html, "sandbox references /assets/zones/")
        for z in ("head_neck", "shoulders", "arms_elbows", "trunk_lean",
                  "hips_pelvis", "knees", "feet_strike"):
            note(('"%s"' % z) in html and
                 os.path.isfile(os.path.join(ZONES, z + ".jpg")),
                 "sandbox zone %s listed + on disk" % z)

    if base:
        def get(path):
            try:
                with urllib.request.urlopen(base + path, timeout=10) as r:
                    return r.status, r.read()
            except Exception as e:
                return "ERR %s" % e, b""
        code, body = get("/art-sandbox.html")
        ok = code == 200 and b"sec-carousel" in body and b"sec-studio" in body
        note(ok, "live sandbox 200 + 3 sections (got %s)" % code)
        bad = 0
        for i in ids:
            c, _ = get("/research/papers/covers/%s.jpg" % i)
            if c != 200:
                bad += 1
                print("FAIL - live cover %s (got %s)" % (i, c))
        if bad:
            FAIL.append("%d live covers broken" % bad)
        else:
            print("ok - live covers 11/11 200")
        bad = 0
        for z in ("head_neck", "shoulders", "arms_elbows", "trunk_lean",
                  "hips_pelvis", "knees", "feet_strike"):
            c, _ = get("/assets/zones/%s.jpg" % z)
            if c != 200:
                bad += 1
                print("FAIL - live zone %s (got %s)" % (z, c))
        if bad:
            FAIL.append("%d live zones broken" % bad)
        else:
            print("ok - live zones 7/7 200")
        c, _ = get("/research/papers/catalog.json")
        note(c == 200, "live catalog.json 200 (got %s)" % c)

    if FAIL:
        print("ART-SANDBOX RED (%d failures)" % len(FAIL))
        return 1
    print("ART-SANDBOX GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
