#!/usr/bin/env python3
"""Render site/assets/showcase.mp4: record the /report/demo walkthrough in a real browser,
capture the Inworld narration audio from the page's own /api/tts responses, then mux with ffmpeg.

Run: ./.venv/bin/python site/make_showcase.py [--url http://127.0.0.1:8138/report/demo] [--seconds 220]
"""
import argparse
import base64
import glob
import json
import os
import shutil
import subprocess
import sys
import time

V3 = "/Users/sameerhoda/Projects/running_analysis/v3"
ASSETS = os.path.join(V3, "site", "assets")
WORK = "/tmp/showcase_build"
GAP = 0.85  # must match the tour's inter-step pause


def sh(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8138/report/demo?showcase=1&auto=1")
    ap.add_argument("--seconds", type=float, default=240)
    ap.add_argument("--size", type=int, default=1000)
    args = ap.parse_args()
    autoplay = "auto=1" in args.url

    os.makedirs(ASSETS, exist_ok=True)
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK + "/audio", exist_ok=True)

    from playwright.sync_api import sync_playwright

    audio = {}  # text -> base64 mp3
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": args.size, "height": args.size},
                                  record_video_dir=WORK + "/video", record_video_size={"width": args.size, "height": args.size})
        pg = ctx.new_page()
        pg.on("response", lambda r: capture(r, audio))
        pg.goto(args.url)
        if autoplay:
            pg.wait_for_function("window.__tourActive===true", timeout=90000)
            t_play = time.time()
        else:
            pg.wait_for_selector("#tourPlay", state="visible", timeout=60000)
            pg.wait_for_timeout(1200)
            t_play = time.time()
            pg.click("#tourPlay")
        story = pg.evaluate("buildStory().map(function(s){return s.text;})")
        print("story steps:", len(story))
        try:
            pg.wait_for_function("window.__tourActive===false", timeout=int(args.seconds * 1000))
        except Exception:
            print("tour did not finish in time; closing anyway")
        pg.wait_for_timeout(1500)  # let the closing spin breathe
        t_end = time.time()
        ctx.close()  # finalizes video
        browser.close()

    videos = sorted(glob.glob(WORK + "/video/*.webm"), key=os.path.getmtime)
    if not videos:
        sys.exit("no video recorded")
    webm = videos[-1]
    dur = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=nw=1:nk=1", webm]).stdout.strip())
    video_start = t_end - dur
    offset = max(0.0, t_play - video_start)
    print("video %.1fs | lead-in %.1fs | steps %d" % (dur, offset, len(story)))

    missing = [t for t in story if t not in audio]
    if missing:
        print("WARNING: missing audio for %d line(s)" % len(missing))

    # --- cut the loading/intro out of the video, then build the narration track ---
    preroll = 0.4
    trim = max(0.0, offset - preroll)   # start the picture where the voice begins (model already spinning)
    wavs = [silence(preroll)]
    for i, t in enumerate(story):
        b64 = audio.get(t)
        if not b64:
            continue
        raw = WORK + "/audio/%02d.mp3" % i
        with open(raw, "wb") as f:
            f.write(base64.b64decode(b64))
        wav = WORK + "/audio/%02d.wav" % i
        sh(["ffmpeg", "-y", "-i", raw, "-ar", "44100", "-ac", "1", wav])
        wavs.append(wav)
        if i < len(story) - 1:
            wavs.append(silence(GAP))
    lst = WORK + "/list.txt"
    with open(lst, "w") as f:
        for w in wavs:
            f.write("file '%s'\n" % w)
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:a", "aac", "-b:a", "160k", WORK + "/voice.m4a"])

    out = os.path.join(ASSETS, "showcase.mp4")
    sh(["ffmpeg", "-y", "-ss", "%.3f" % trim, "-i", webm, "-i", WORK + "/voice.m4a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out])
    print("wrote", out, "%.1f MB | trimmed %.1fs of loading" % (os.path.getsize(out) / 1e6, trim))


def silence(sec):
    p = WORK + "/audio/sil_%d.wav" % int(sec * 1000)
    if not os.path.exists(p):
        sh(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", "%.3f" % sec, p])
    return p


def capture(resp, audio):
    if not resp.url.endswith("/api/tts") or not resp.ok:
        return
    try:
        j = resp.json()
    except Exception:
        return
    b64 = j.get("audioContent")
    if not b64:
        return
    try:
        text = json.loads(resp.request.post_data or "{}").get("text")
    except Exception:
        text = None
    if text is not None:
        audio[text] = b64


if __name__ == "__main__":
    main()
