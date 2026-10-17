#!/usr/bin/env python3
"""One-button Instagram reel export: a single 1080x1920 MP4 per job.

Content: Ken Burns walkthrough over the run photo + persistent score pill +
per-segment caption cards + voiceover (live TTS when a key is configured,
deterministic silence otherwise) + caption text via /api/share/<jid>.

Composed on demand by the server and cached per job as
  site/jobs/<jid>/reel.mp4 + reel.json (freshness = analysis.json mtime +
  voice availability). No paid calls ever fire without INWORLD_KEY: the TTS
  hook is only invoked when the server passes a tts_fn, and every TTS failure
  falls back to silence for that segment.

Timeline is fully deterministic: INTRO 3s + up to 3 x 5s zone segments +
3s outro, so stub and real composes share durations and only differ in
content/audio bytes. stdlib + PIL + ffmpeg only (no libass/drawtext: all
text is PIL-rendered PNG overlays).

Linux deploy note: fonts resolve Helvetica.ttc (macOS) -> DejaVuSans
(Linux) -> PIL default. Install DejaVu on the EC2 target.
"""
import json
import os
import subprocess
import time

W, H, FPS = 1080, 1920, 30
INTRO_DUR, SEG_DUR, OUTRO_DUR = 3.0, 5.0, 3.0
MAX_ZONES = 3
REEL_JSON = "reel.json"
REEL_MP4 = "reel.mp4"

_FONT_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",  # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _font(size):
    from PIL import ImageFont
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def segments_for(analysis, jid):
    """Split an analysis into deterministic timeline segments."""
    try:
        score = analysis.get("overall_score", "")
        label = analysis.get("overall_label") or ""
        summary = analysis.get("one_line_summary") or ""
    except AttributeError:
        score, label, summary = "", "", ""
    segs = [{
        "kind": "intro", "dur": INTRO_DUR,
        "title": "My running form",
        "head": "%s/100" % score,
        "body": (label + (". " + summary if summary else ""))[:140],
        "voice": ("My running form scored %s out of 100. %s %s"
                  % (score, label, summary))[:400],
    }]
    for z in (analysis.get("findings") or [])[:MAX_ZONES]:
        title = z.get("title") or z.get("zone") or ""
        tldr = z.get("tldr") or z.get("observation") or ""
        cue = z.get("cue") or ""
        segs.append({
            "kind": "zone", "dur": SEG_DUR,
            "title": title, "head": "%s/100" % (z.get("zone_score") or ""),
            "body": tldr[:140],
            "cue": ("Cue: " + cue)[:90] if cue else "",
            "voice": ("%s. %s %s" % (title, tldr,
                                     ("Cue: " + cue) if cue else ""))[:400],
        })
    segs.append({
        "kind": "outro", "dur": OUTRO_DUR,
        "title": "See the 3D breakdown",
        "head": "/s/%s" % jid,
        "body": "Full zone-by-zone fixes and drills in the interactive report.",
        "voice": "See the full 3D breakdown. Link is in the post.",
    })
    t = 0.0
    for s in segs:
        s["start"], s["end"] = t, t + s["dur"]
        t += s["dur"]
    return segs


def total_dur(segs):
    return sum(s["dur"] for s in segs)


def _textcard(title, head, body, cue=""):
    """Render a 960x620 lime-on-dark caption card. Pure PIL."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (960, 620), (14, 17, 23, 235))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 960, 10], fill=(200, 240, 74, 255))
    d.text((48, 44), title[:42], font=_font(44), fill=(244, 247, 242, 255))
    d.text((48, 112), head[:42], font=_font(64), fill=(200, 240, 74, 255))
    y = 210
    for line in _wrap(body, 38)[:4]:
        d.text((48, y), line, font=_font(36), fill=(200, 205, 195, 255))
        y += 52
    if cue:
        d.text((48, y + 18), cue, font=_font(34), fill=(200, 240, 74, 255))
    return img


def _pill(score, label):
    """Persistent 960x150 top score pill. Pure PIL."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (960, 150), (9, 12, 17, 220))
    d = ImageDraw.Draw(img)
    d.text((36, 28), "RUNFORM  %s/100" % score, font=_font(52),
           fill=(200, 240, 74, 255))
    d.text((36, 92), str(label)[:44], font=_font(32),
           fill=(160, 168, 158, 255))
    return img


def _wrap(text, width):
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        if len((cur + " " + w).strip()) > width:
            lines.append(cur.strip())
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur.strip():
        lines.append(cur.strip())
    return lines or [""]


def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if p.returncode != 0:
        raise RuntimeError("ffmpeg failed: %s" % (p.stderr or "")[-300:])
    return p


def _silence_wav(path, dur, ffmpeg="ffmpeg"):
    _run([ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
          "-t", "%.2f" % dur, "-ar", "44100", "-ac", "1", path])


def _audio_for(segs, workdir, tts_fn=None, ffmpeg="ffmpeg"):
    """One wav per segment: live TTS when tts_fn yields mp3 bytes, else silence."""
    wavs = []
    for i, s in enumerate(segs):
        wav = os.path.join(workdir, "seg%02d.wav" % i)
        mp3 = None
        if tts_fn is not None:
            try:
                mp3 = tts_fn(s["voice"])
            except Exception:
                mp3 = None
        if mp3:
            raw = os.path.join(workdir, "seg%02d.mp3" % i)
            with open(raw, "wb") as f:
                f.write(mp3)
            _run([ffmpeg, "-y", "-i", raw, "-ar", "44100", "-ac", "1", wav])
        else:
            _silence_wav(wav, s["dur"], ffmpeg)
        wavs.append(wav)
    lst = os.path.join(workdir, "audio.txt")
    with open(lst, "w") as f:
        for w in wavs:
            f.write("file '%s'\n" % w)
    out = os.path.join(workdir, "voice.m4a")
    _run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", lst,
          "-c:a", "aac", "-b:a", "128k", out])
    return out


def is_fresh(job_dir, analysis_mtime, voice):
    try:
        m = json.load(open(os.path.join(job_dir, REEL_JSON)))
        return (m.get("analysis_mtime") == analysis_mtime
                and m.get("voice") == bool(voice)
                and os.path.exists(os.path.join(job_dir, REEL_MP4)))
    except (OSError, ValueError):
        return False


def compose(job_dir, jid, analysis, tts_fn=None, ffmpeg="ffmpeg"):
    """Build reel.mp4 + reel.json in job_dir. Returns (mp4_path, manifest)."""
    try:
        score = analysis.get("overall_score", "")
        label = analysis.get("overall_label") or ""
    except AttributeError:
        score, label = "", ""
    segs = segments_for(analysis, jid)
    dur = total_dur(segs)
    workdir = os.path.join(job_dir, "reel_work")
    os.makedirs(workdir, exist_ok=True)

    pill = os.path.join(workdir, "pill.png")
    _pill(score, label).save(pill)
    cards = []
    for i, s in enumerate(segs):
        cp = os.path.join(workdir, "card%02d.png" % i)
        _textcard(s["title"], s["head"], s["body"],
                  s.get("cue", "")).save(cp)
        cards.append((cp, s["start"], s["end"]))

    photo = os.path.join(job_dir, "input.jpg")
    frames = int(round(dur * FPS))
    fc = ["[0:v]scale=2160:3840:force_original_aspect_ratio=increase,"
          "crop=2160:3840,zoompan=z='min(1+0.00045*on,1.12)':d=1:"
          "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=%dx%d:fps=%d[base]"
          % (W, H, FPS)]
    last = "base"
    nxt_in = 1
    fc.append("[%s][%d:v]overlay=(W-w)/2:110[pv%d]" % (last, nxt_in, nxt_in))
    last = "pv%d" % nxt_in
    nxt_in += 1
    for cp, a, b in cards:
        fc.append("[%s][%d:v]overlay=(W-w)/2:H-h-170:"
                  "enable='between(t,%.2f,%.2f)'[pv%d]"
                  % (last, nxt_in, a, b, nxt_in))
        last = "pv%d" % nxt_in
        nxt_in += 1
    filt = ";".join(fc)

    vmp4 = os.path.join(workdir, "video.mp4")
    # Overlay PNGs are single frames: loop each for the full duration so the
    # overlay filter never hits EOF mid-timeline.
    inputs = (["-loop", "1", "-framerate", str(FPS), "-i", photo]
              + ["-loop", "1", "-framerate", str(FPS), "-t", "%.2f" % dur,
                 "-i", pill])
    for c, _, _ in cards:
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", "%.2f" % dur,
                   "-i", c]
    cmd = ["ffmpeg", "-y"] + inputs + [
           "-filter_complex", filt, "-map", "[%s]" % last,
           "-frames:v", str(frames), "-c:v", "libx264", "-preset", "medium",
           "-crf", "21", "-pix_fmt", "yuv420p", vmp4]
    _run([ffmpeg if c == "ffmpeg" else c for c in cmd])

    ama = _audio_for(segs, workdir, tts_fn, ffmpeg)
    out = os.path.join(job_dir, REEL_MP4)
    _run([ffmpeg, "-y", "-i", vmp4, "-i", ama,
          "-filter:a", "apad=whole_dur=%.2f" % dur,
          "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
          "-t", "%.2f" % dur, "-movflags", "+faststart", out])

    manifest = {"analysis_mtime": os.path.getmtime(
                    os.path.join(job_dir, "analysis.json")),
                "voice": tts_fn is not None, "dur": dur,
                "segs": len(segs), "built_at": time.time()}
    with open(os.path.join(job_dir, REEL_JSON), "w") as f:
        json.dump(manifest, f)
    return out, manifest


def selftest():
    import tempfile
    from PIL import Image
    d = tempfile.mkdtemp(prefix="reel_stub_")
    Image.new("RGB", (640, 480), (90, 140, 60)).save(
        os.path.join(d, "input.jpg"), quality=90)
    stub = {"overall_score": 71, "overall_label": "Test label",
            "one_line_summary": "Stub summary for timing.",
            "findings": [
                {"title": "Zone A", "zone": "za", "zone_score": 60,
                 "tldr": "Stub tldr one.", "cue": "Stub cue one."},
                {"title": "Zone B", "zone": "zb", "zone_score": 80,
                 "tldr": "Stub tldr two.", "cue": "Stub cue two."}]}
    with open(os.path.join(d, "analysis.json"), "w") as f:
        json.dump(stub, f)
    # zero paid builds: tts_fn=None -> deterministic silence
    out, m = compose(d, "stubjob", stub, tts_fn=None)
    assert os.path.exists(out), "no mp4"
    assert m["voice"] is False and m["segs"] == 4, m  # intro+2+outro
    assert abs(m["dur"] - (INTRO_DUR + 2 * SEG_DUR + OUTRO_DUR)) < 1e-6, m
    assert is_fresh(d, os.path.getmtime(os.path.join(d, "analysis.json")),
                    False), "cache should be fresh"
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,duration",
         "-of", "default=nw=1", out], capture_output=True, text=True)
    info = probe.stdout
    assert "width=1080" in info and "height=1920" in info, info
    acheck = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=codec_name", "-of", "default=nw=1:nk=1",
         out], capture_output=True, text=True)
    assert acheck.stdout.strip() == "aac", acheck.stdout
    print("reel selftest: all checks passed (stub, silence, %dx%d)" % (W, H))


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        selftest()
    else:
        print("usage: python3 site/reel.py --selftest")
