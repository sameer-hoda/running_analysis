#!/usr/bin/env python3
"""Full browser E2E QA for the tripo-cloud sandbox (Selenium, headless Chrome).
Free checks reuse done jobs; ONE paid upload proves the live pipeline.
Writes screenshots + qa_result.json into /tmp/qa/.
"""
import json, os, sys, time, urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = "http://127.0.0.1:8139"
OUT = "/tmp/qa"
os.makedirs(OUT, exist_ok=True)
RES = {"checks": []}

def check(name, ok, detail=""):
    RES["checks"].append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail)[:160] if detail else ""), flush=True)

def make_driver():
    o = Options()
    o.add_argument("--headless=new")
    o.add_argument("--no-sandbox"); o.add_argument("--disable-dev-shm-usage")
    o.add_argument("--enable-unsafe-swiftshader")
    o.add_argument("--window-size=1280,900")
    o.add_argument("--mute-audio")
    o.add_argument("--autoplay-policy=no-user-gesture-required")
    o.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return webdriver.Chrome(options=o)

def console_errors(d):
    try:
        return [e for e in d.get_log("browser") if e.get("level") in ("SEVERE",)]
    except Exception as e:
        return [{"level": "LOGREAD_FAIL", "message": str(e)}]

def canvas_alive(d):
    # Screenshot the composited viewport element (drawImage on a raw WebGL
    # canvas lies without preserveDrawingBuffer) and measure variance.
    from PIL import Image, ImageStat
    el = d.find_element(By.ID, "viewport")
    png = el.screenshot_as_png
    import io
    im = Image.open(io.BytesIO(png)).convert("L")
    st = ImageStat.Stat(im)
    return {"ok": True, "mean": round(st.mean[0]), "std": round(st.stddev[0])}

def score_shown(d, jid, timeout=15):
    try:
        exp = str(json.load(urllib.request.urlopen(f"{BASE}/api/jobs/{jid}")) .get("score", ""))
    except Exception:
        exp = ""
    t0 = time.time()
    while time.time() - t0 < timeout:
        t = d.execute_script("return document.getElementById('score').textContent") or ""
        if exp and exp in t:
            return True, t.strip()[:20]
        time.sleep(1)
    return False, (t or "").strip()[:20]

def wait_mesh(d, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = d.execute_script("""
          var l = document.getElementById('loading');
          var hidden = !l || l.style.display==='none' || l.style.opacity==='0';
          return {hidden:hidden, status:(document.getElementById('status')||{}).textContent||''};""")
        if st["hidden"]:
            return True
        time.sleep(3)
    return False

d = make_driver()
try:
  try:
    # ---- 1. landing ----
    d.get(BASE + "/")
    WebDriverWait(d, 15).until(EC.presence_of_element_located((By.ID, "upForm")))
    check("landing loads + upload form", True, d.title)
    d.save_screenshot(f"{OUT}/1_landing.png")

    # ---- 2. done job, fast lane ----
    J1 = "91cff3d7f601"
    d.get(f"{BASE}/report/{J1}")
    WebDriverWait(d, 15).until(EC.presence_of_element_located((By.ID, "score")))
    ok_s, score = score_shown(d, J1)
    check("report scores render", ok_s, f"score={score}")
    got_mesh = wait_mesh(d, 90)
    check("fast-lane mesh appears (spinner gone)", got_mesh)
    time.sleep(4)
    px = canvas_alive(d)
    check("canvas pixels vary (3D rendered)", px.get("ok") and px.get("std", 0) > 3, str(px))
    d.save_screenshot(f"{OUT}/2_report_fast.png")
    errs = [e["message"][:200] for e in console_errors(d)]
    check("no severe console errors (fast)", len(errs) == 0, "; ".join(errs[:3]))

    # markers -> click the 3D body, detail card must open (tests raycast picking)
    from selenium.webdriver.common.action_chains import ActionChains
    stage = d.find_element(By.ID, "stage")
    ActionChains(d).move_to_element_with_offset(stage, 10, -40).click().perform()
    time.sleep(2)
    dv = d.execute_script("var e=document.getElementById('detailView');return e ? e.hidden===false : 'NO_EL'")
    check("click body -> detail card opens (3D picking)", dv is True, f"detailView open={dv}")
    d.save_screenshot(f"{OUT}/3_markers.png")

    # ---- 3. tour + voice (click the real Play button like a user) ----
    tts_before = d.execute_script("return performance.getEntriesByType('resource').filter(r=>r.name.includes('/api/tts')).length")
    WebDriverWait(d, 20).until(EC.visibility_of_element_located((By.ID, "tourCtl")))
    d.find_element(By.ID, "tourPlay").click()
    time.sleep(10)
    cap = d.execute_script("var c=document.getElementById('cap');return c?c.textContent.slice(0,120):'NO_CAP_EL'")
    tts_after = d.execute_script("return performance.getEntriesByType('resource').filter(r=>r.name.includes('/api/tts')).length")
    step = d.execute_script("var s=document.getElementById('tourStep');return s?s.textContent:'?'")
    story = d.execute_script("try{return buildStory().map(function(s){return s.kind;}).join(',');}catch(e){return 'ERR:'+e;}")
    check("caption component removed", cap == "NO_CAP_EL", cap[:100])
    check("tour story has no colour-key step", "colors" not in story, story[:160])
    check("tour requests voice (TTS calls firing)", tts_after > tts_before, f"tts reqs {tts_before}->{tts_after}, step={step}")
    d.save_screenshot(f"{OUT}/4_tour.png")
    time.sleep(12)
    step2 = d.execute_script("var s=document.getElementById('tourStep');return s?s.textContent:'?'")
    check("tour auto-advances", step2 != step, f"{step} -> {step2}")
    try:
        d.find_element(By.ID, "tourStop").click()
    except Exception:
        pass
    errs = [e["message"][:200] for e in console_errors(d)]
    check("no severe console errors (tour)", len(errs) == 0, "; ".join(errs[:3]))

    # ---- 4. best-lane heavy mesh ----
    d.get(f"{BASE}/report/125d94c6dd3d")
    WebDriverWait(d, 15).until(EC.presence_of_element_located((By.ID, "score")))
    check("best-lane mesh appears", wait_mesh(d, 120))
    time.sleep(4)
    px = canvas_alive(d)
    check("best-lane canvas rendered", px.get("ok") and px.get("std", 0) > 3, str(px))
    d.save_screenshot(f"{OUT}/5_report_best.png")

    # ---- 5. LIVE paid upload (images-7.jpeg) ----
    d.get(BASE + "/")
    WebDriverWait(d, 15).until(EC.presence_of_element_located((By.ID, "file")))
    d.find_element(By.ID, "file").send_keys("/Users/sameerhoda/Projects/running_analysis/v3-tripo-cloud/reference/input/images-7.jpeg")
    time.sleep(1)
    d.save_screenshot(f"{OUT}/6_upload_preview.png")
    d.find_element(By.ID, "go").click()
    WebDriverWait(d, 30).until(lambda x: "/job/" in x.current_url)
    jid = d.current_url.rstrip("/").split("/")[-1]
    check("upload -> job page", True, f"jid={jid}")
    # wait for studio to open only when the job is DONE (loader means loaded)
    try:
        WebDriverWait(d, 420).until(lambda x: "/report/" in x.current_url)
        t_redir = True
    except Exception:
        t_redir = False
    check("job opens finished studio at 100%", t_redir, d.current_url)
    d.save_screenshot(f"{OUT}/7_studio_open.png")
    ok_s2, early_score = score_shown(d, jid)
    check("scores visible at studio open", ok_s2, early_score)
    check("live mesh completes", wait_mesh(d, 420))
    time.sleep(4)
    px = canvas_alive(d)
    check("live canvas rendered", px.get("ok") and px.get("std", 0) > 3, str(px))
    d.save_screenshot(f"{OUT}/8_live_done.png")
    errs = [e["message"][:200] for e in console_errors(d)]
    check("no severe console errors (live)", len(errs) == 0, "; ".join(errs[:3]))
  except Exception as e:
    check("QA run completed without harness crash", False, f"{type(e).__name__}: {str(e)[:200]}")
finally:
    try:
        d.quit()
    except Exception:
        pass

RES["summary"] = {"pass": sum(1 for c in RES["checks"] if c["ok"]), "fail": sum(1 for c in RES["checks"] if not c["ok"])}
json.dump(RES, open(f"{OUT}/qa_result.json", "w"), indent=1)
print(f"\nQA: {RES['summary']['pass']} pass / {RES['summary']['fail']} fail", flush=True)
