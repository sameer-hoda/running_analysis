#!/usr/bin/env python3
"""QA battle-test bot: push every image in reference/input through the full pipeline,
render each report headlessly, score it, and publish a gallery + results.

Run (needs the server + Playwright):
  /opt/homebrew/opt/python@3.14/bin/python3.14 site/qa_bot.py            # one sweep
  /opt/homebrew/opt/python@3.14/bin/python3.14 site/qa_bot.py --loop      # keep publishing
"""
import argparse
import http.cookiejar
import json
import mimetypes
import os
import shutil
import time
import urllib.request
import uuid

V3 = "/Users/sameerhoda/Projects/running_analysis/v3"
EXTS = (".jpg", ".jpeg", ".png", ".webp", ".avif")


def opener():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def post_job(op, base, path):
    boundary = "----qa" + uuid.uuid4().hex
    name = os.path.basename(path)
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        content = f.read()
    body = (("--%s\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"%s\"\r\n"
             "Content-Type: %s\r\n\r\n" % (boundary, name, ctype)).encode() + content +
            ("\r\n--%s--\r\n" % boundary).encode())
    req = urllib.request.Request(base + "/api/jobs", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary,
                                          "Accept": "application/json"})
    try:
        r = op.open(req, timeout=90)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {"error": "http %d" % e.code}


def get_json(op, url):
    try:
        with op.open(url, timeout=30) as r:
            return r.status, json.loads(r.read())
    except Exception as e:
        return 0, {"error": str(e)}


def score_one(op, base, pw, img, outdir, timeout):
    rec = {"image": os.path.basename(img), "job": None, "stage": None, "is_running": None,
           "overall_score": None, "findings": None, "insufficient": None, "anchors": None,
           "markers": None, "markers_expected": None, "errors": [], "score": 0, "notes": []}
    ok, j = post_job(op, base, img)
    if ok != 200 or "job_id" not in j:
        rec["stage"] = "rejected"
        rec["notes"].append(j.get("error", "rejected by upload guard"))
        rec["score"] = 80 if rec["notes"][-1] else 0  # graceful rejection is acceptable
        return rec
    jid = j["job_id"]; rec["job"] = jid
    t0 = time.time()
    while time.time() - t0 < timeout:
        _, st = get_json(op, base + "/api/jobs/" + jid)
        rec["stage"] = st.get("stage")
        if rec["stage"] in ("done", "failed"):
            break
        time.sleep(4)
    if rec["stage"] != "done":
        rec["errors"].append((st.get("error") or "did not finish")[:160])
        rec["score"] = 40  # backend handled it but no report
        return rec
    # analysis
    _, a = get_json(op, base + "/api/jobs/%s/analysis" % jid)
    rec["is_running"] = a.get("is_running")
    rec["overall_score"] = a.get("overall_score")
    rec["findings"] = len(a.get("findings") or [])
    rec["insufficient"] = len(a.get("insufficient") or [])
    rec["markers_expected"] = rec["findings"]
    # render report
    page = pw.new_page(viewport={"width": 1280, "height": 860})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    try:
        page.goto(base + "/report/" + jid, timeout=45000)
        try:
            page.wait_for_selector("#tourPlay", state="visible", timeout=40000)
            rec["notes"].append("3D loaded")
        except Exception:
            rec["notes"].append("3D did not load in time")
        page.wait_for_timeout(1500)
        png = os.path.join(outdir, rec["image"] + ".png")
        page.screenshot(path=png)
        rec["screenshot"] = os.path.basename(png)
        rec["markers"] = page.evaluate("document.querySelectorAll('.zrow').length")
    except Exception as e:
        rec["errors"].append(str(e)[:160])
    finally:
        page.close()
    rec["errors"] += errs[:3]
    # score
    s = 0
    s += 20 if rec["stage"] == "done" else 0
    s += 20 if not rec["errors"] else 0
    s += 20 if "3D loaded" in rec["notes"] else 0
    s += 15 if rec["markers"] and rec["markers"] >= max(1, rec["markers_expected"] or 1) else 0
    s += 15 if (rec["findings"] is not None and rec["findings"] + (rec["insufficient"] or 0) == 7) else 0
    s += 10 if (rec["overall_score"] is not None and 0 <= rec["overall_score"] <= 100) else 0
    rec["score"] = s
    return rec


def publish(outroot, stamp, results):
    run = os.path.join(outroot, stamp)
    os.makedirs(run, exist_ok=True)
    with open(os.path.join(run, "results.json"), "w") as f:
        json.dump(results, f, indent=1)
    avg = round(sum(r["score"] for r in results) / max(1, len(results)))
    rows = []
    for r in results:
        shot = ("<img src='%s' loading=lazy>" % r["screenshot"]) if r.get("screenshot") else ""
        rows.append("<tr><td>%s</td><td>%s</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            r["image"], r.get("stage"), r["score"], r.get("overall_score"),
            " · ".join(r.get("notes", [])) + (" · " + "; ".join(r.get("errors", [])) if r.get("errors") else ""), shot))
    html = ("<!doctype html><meta charset=utf-8><title>RunForm QA</title>"
            "<style>body{font-family:system-ui;background:#0a0c11;color:#eef;padding:24px}"
            "table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #222;padding:8px;font-size:13px;text-align:left}"
            "img{height:110px;border-radius:8px;border:1px solid #222}.big{font-size:34px;color:#c8f04a}</style>"
            "<h1>RunForm QA — __STAMP__</h1><p class=big>avg __AVG__</p><table><tr><th>image</th><th>stage</th><th>qa</th>"
            "<th>score</th><th>notes</th><th>render</th></tr>__ROWS__</table>")
    html = html.replace("__STAMP__", stamp).replace("__AVG__", str(avg)).replace("__ROWS__", "".join(rows))
    with open(os.path.join(run, "index.html"), "w") as f:
        f.write(html)
    latest = os.path.join(outroot, "latest")
    try:
        if os.path.islink(latest) or os.path.exists(latest):
            os.remove(latest) if os.path.islink(latest) else shutil.rmtree(latest)
        os.symlink(run, latest)
    except OSError:
        pass
    with open(os.path.join(run, "summary.md"), "w") as f:
        f.write("# RunForm QA %s — avg %d\n\n" % (stamp, avg))
        for r in results:
            f.write("- **%s** — %s, qa %d, score %s%s\n" % (
                r["image"], r.get("stage"), r["score"], r.get("overall_score"),
                (" — " + "; ".join(r.get("errors", []))) if r.get("errors") else ""))
    print("avg QA score:", avg, "| published:", run)


def sweep(args):
    from playwright.sync_api import sync_playwright
    imgs = [os.path.join(args.dir, f) for f in sorted(os.listdir(args.dir))
            if f.lower().endswith(EXTS) and not f.startswith(".")]
    if not imgs:
        raise SystemExit("no images in " + args.dir)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    outroot = os.path.join(V3, "site", "qa")
    run = os.path.join(outroot, stamp)
    os.makedirs(run, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        op = opener()
        for i, img in enumerate(imgs, 1):
            print("[%d/%d] %s" % (i, len(imgs), os.path.basename(img)), flush=True)
            try:
                rec = score_one(op, args.base, browser, img, run, args.timeout)
            except Exception as e:
                rec = {"image": os.path.basename(img), "score": 0, "errors": [str(e)[:160]]}
            results.append(rec)
            print("     ->", rec.get("stage"), "qa", rec.get("score"), rec.get("errors") or "", flush=True)
        browser.close()
    publish(outroot, stamp, results)
    avg = round(sum(r["score"] for r in results) / max(1, len(results)))
    return avg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8138")
    ap.add_argument("--dir", default=os.path.join(V3, "reference", "input"))
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=600)
    args = ap.parse_args()
    while True:
        avg = sweep(args)
        if not args.loop or avg >= 95:
            break
        print("below 95 — re-running in %ds" % args.interval)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
