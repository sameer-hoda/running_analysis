#!/usr/bin/env python3
"""Render a 10-15s homepage teaser from a finished job's studio walkthrough.

Same recipe as make_showcase.py (real browser + tour narration muxed with
ffmpeg), but cut to a sneak-peek: first TEASE seconds of picture+voice.

Run: ./venv/bin/python site/make_teaser.py <job_id> [--seconds 15]
Needs: playwright chromium (`python3 -m playwright install chromium`), ffmpeg.
Server must run on 8139 (sandbox default).
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

V3 = "/Users/sameerhoda/Projects/running_analysis/v3-tripo-cloud"
ASSETS = os.path.join(V3, "site", "assets")
WORK = "/tmp/teaser_build"
GAP = 0.85  # must match the tour's inter-step pause


def sh(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job_id")
    ap.add_argument("--seconds", type=float, default=0,
                    help="final length; 0 = auto-fit full voice + 0.6s tail (never cut mid-sentence)")
    ap.add_argument("--rate", type=float, default=1.15,
                    help="narration speed for the teaser mux (site voice untouched)")
    ap.add_argument("--story", default="teaser", help="tour story: teaser (12s) or showcase (full)")
    ap.add_argument("--wait", type=float, default=0,
                    help="record window after tour start; 0 = 45s teaser / 240s showcase")
    ap.add_argument("--size", type=int, default=1000)
    ap.add_argument("--out", default=None, help="output mp4 (default: site/assets/showcase.mp4)")
    args = ap.parse_args()
    url = f"http://127.0.0.1:8139/report/{args.job_id}?showcase=1&auto=1&story={args.story}"

    os.makedirs(ASSETS, exist_ok=True)
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK + "/audio", exist_ok=True)

    from playwright.sync_api import sync_playwright

    audio = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": args.size, "height": args.size},
                                  record_video_dir=WORK + "/video",
                                  record_video_size={"width": args.size, "height": args.size})
        pg = ctx.new_page()
        pg.on("response", lambda r: capture(r, audio))
        pg.goto(url)
        pg.wait_for_function("window.__tourActive===true", timeout=90000)
        t_play = time.time()
        story = pg.evaluate("buildStory().map(function(s){return s.text;})")
        print("story steps:", len(story), flush=True)
        # record window must cover the whole tour, independent of final cut length
        window = args.wait if args.wait > 0 else (45.0 if args.story == "teaser" else 240.0)
        pg.wait_for_timeout(int(window * 1000))
        t_end = time.time()
        ctx.close()
        browser.close()

    videos = sorted(glob.glob(WORK + "/video/*.webm"), key=os.path.getmtime)
    if not videos:
        sys.exit("no video recorded")
    webm = videos[-1]
    dur = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=nw=1:nk=1", webm]).stdout.strip())
    video_start = t_end - dur
    offset = max(0.0, t_play - video_start)
    print("video %.1fs | lead-in %.1fs | steps %d" % (dur, offset, len(story)), flush=True)

    preroll = 0.4
    # 0.7s safety: webm recordings consistently yield ~0.6s less picture than
    # probed (timestamp quirk) — starting the picture slightly early guarantees
    # the voice is never cut; sync is unaffected (voice track untouched).
    trim = max(0.0, offset - preroll - 0.7)
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
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
        "-c:a", "aac", "-b:a", "160k", WORK + "/voice.m4a"])
    # teaser narration runs a touch faster (1.15x); site voice is untouched
    sh(["ffmpeg", "-y", "-i", WORK + "/voice.m4a",
        "-filter:a", "atempo=%.3f" % args.rate, "-c:a", "aac", "-b:a", "160k",
        WORK + "/voice_fast.m4a"])
    vd = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                   "-of", "default=nw=1:nk=1", WORK + "/voice_fast.m4a"]).stdout.strip())
    final_len = args.seconds if args.seconds > 0 else vd + 0.6
    print("voice %.1fs -> %.1fs @%.2fx | final %.1fs" % (
        vd * args.rate, vd, args.rate, final_len), flush=True)

    out = args.out or os.path.join(ASSETS, "showcase.mp4")
    if out == os.path.join(ASSETS, "showcase.mp4") and os.path.exists(out):
        shutil.copy(out, os.path.join(ASSETS, "showcase.prev.mp4"))
        print("backed up previous showcase.mp4", flush=True)
    # tpad holds the last frame so the picture always outlives the voice —
    # webm timestamp quirks can otherwise shave frames off the tail.
    sh(["ffmpeg", "-y", "-ss", "%.3f" % trim, "-i", webm, "-i", WORK + "/voice_fast.m4a",
        "-t", "%.2f" % final_len,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out])
    print("wrote", out, "%.1f MB" % (os.path.getsize(out) / 1e6), flush=True)


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
