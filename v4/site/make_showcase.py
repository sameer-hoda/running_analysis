#!/usr/bin/env python3
"""Render site/assets/showcase.mp4: record the /report/demo canonical 18s tour in a
real browser, capture the Kabeer narration audio (Inworld TTS-2, voiceId "Kabir")
from the page's own /api/tts responses, then mux with ffmpeg.

Run: python3 site/make_showcase.py [--url URL] [--seconds 240]
V4-only: paths resolve from this file (never v2/v3); voice is Kabir to match
INWORLD_VOICE in site/server.py. "Kabeer" is the display name; "Kabir" is the
provider voiceId on the wire. The build FAILS CLOSED: every captured line must
request voiceId "Kabir" and /api/tts/status must report "Kabir", otherwise the
old showcase.mp4 is left untouched. A provenance sidecar
site/assets/showcase.json records the voice proof + script.
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

V4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(V4, "site", "assets")
WORK = "/tmp/showcase_build"


def sh(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8140/report/demo?showcase=1&story=demo&auto=1")
    ap.add_argument("--min-mesh-bytes", type=int, default=2000000,
                    help="fail closed below this mesh size (stub demo mesh is ~0.7MB; real Tripo ~3MB)")
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
        story = pg.evaluate("buildStory().map(function(s){return {text:s.text, gap:(s.gap==null?850:s.gap), rate:(s.rate||1)};})")
        print("story steps:", len(story))
        for st in story:
            print("  beat: gap=%dms rate=%s %s" % (st["gap"], st["rate"], st["text"][:70]))
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

    # --- mesh gate (fail closed): homepage slot ships the real Tripo mesh only ---
    base = args.url.split("/report/")[0]
    try:
        jid = args.url.split("/report/")[1].split("?")[0].split("/")[0]
    except IndexError:
        jid = ""
    mesh_bytes = 0
    try:  # GET to null: this server answers HEAD with 501, so measure the real body
        out = sh(["curl", "-s", "-o", "/dev/null", "-w", "%{size_download}",
                  "%s/jobs/%s/mesh.glb" % (base, jid)]).stdout
        mesh_bytes = int(out.strip())
    except Exception:
        pass
    print("mesh job=%s bytes=%d" % (jid, mesh_bytes))
    if mesh_bytes < args.min_mesh_bytes:
        sys.exit("ABORT: mesh for job %r is %d bytes (< %d) — stub mesh, leaving showcase.mp4 untouched"
                 % (jid, mesh_bytes, args.min_mesh_bytes))
    # --- voice gate (fail closed): every captured line must be voiceId Kabir ---
    try:
        st = json.loads(sh(["curl", "-s", base + "/api/tts/status"]).stdout)
    except Exception:
        st = {}
    status_voice = st.get("voice") if isinstance(st, dict) else None
    print("tts status voice:", status_voice)
    if status_voice != "Kabir":
        sys.exit("ABORT: tts status voice is %r, not Kabir — leaving showcase.mp4 untouched" % (status_voice,))
    missing = [s["text"] for s in story if s["text"] not in audio]
    if missing:
        print("WARNING: missing audio for %d line(s)" % len(missing))
    bad_voice = [(s["text"][:50], audio[s["text"]]["voice"])
                 for s in story if s["text"] in audio and audio[s["text"]]["voice"] != "Kabir"]
    if bad_voice:
        sys.exit("ABORT: non-Kabir voice captured %r — leaving showcase.mp4 untouched" % (bad_voice,))

    # --- cut the loading/intro out of the video, then build the narration track ---
    # Sync model: the page plays each line at its step rate (1.15x) and waits the
    # step's own gap before the next camera move, so the mux applies the same
    # atempo + per-step gap — each beat lands its move.
    preroll = 0.4
    trim = max(0.0, offset - preroll)   # start the picture where the voice begins (model already spinning)
    wavs = [silence(preroll)]
    line_durs = []
    for i, s in enumerate(story):
        t = s["text"]
        if t not in audio:
            continue
        raw = WORK + "/audio/%02d.mp3" % i
        with open(raw, "wb") as f:
            f.write(base64.b64decode(audio[t]["b64"]))
        wav = WORK + "/audio/%02d.wav" % i
        rate = float(s.get("rate") or 1)
        if abs(rate - 1.0) > 1e-6:
            sh(["ffmpeg", "-y", "-i", raw, "-filter:a", "atempo=%.4f" % rate,
                "-ar", "44100", "-ac", "1", wav])
        else:
            sh(["ffmpeg", "-y", "-i", raw, "-ar", "44100", "-ac", "1", wav])
        line_durs.append(float(sh(["ffprobe", "-v", "error", "-show_entries",
                                   "format=duration", "-of", "default=nw=1:nk=1", wav]).stdout.strip()))
        wavs.append(wav)
        if i < len(story) - 1:
            wavs.append(silence(float(s.get("gap", 850)) / 1000.0))
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
    sidecar = {
        "mesh": {"job": jid, "bytes": mesh_bytes},
        "voice": "Kabir",            # display name Kabeer; provider voiceId Kabir
        "display": "Kabeer",
        "engine": (st.get("engine") if isinstance(st, dict) else None),
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source_url": args.url,
        "missing_lines": len(missing),
        "lines": [{"text": s["text"], "gap_ms": s.get("gap"), "rate": s.get("rate"),
                   "voice": (audio.get(s["text"], {}) or {}).get("voice"),
                   "dur_s": round(d, 2)}
                  for s, d in zip([x for x in story if x["text"] in audio], line_durs)],
    }
    with open(os.path.join(ASSETS, "showcase.json"), "w") as f:
        json.dump(sidecar, f, indent=1)
    print("wrote", os.path.join(ASSETS, "showcase.json"),
          "| voice=Kabir on %d/%d lines" % (len(line_durs), len(story)))


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
        post = json.loads(resp.request.post_data or "{}")
    except Exception:
        post = {}
    # Voice proof: the page posts the requested voiceId alongside each line;
    # the server forwards it verbatim as Inworld voiceId (see inworld_tts).
    if post.get("text") is not None:
        audio[post["text"]] = {"b64": b64, "voice": post.get("voice")}


if __name__ == "__main__":
    main()
