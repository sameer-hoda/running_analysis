#!/usr/bin/env python3
"""TTS pre-warm hook (pipeline-auth P1; server.py freeze-safe).

Builds Coach Kabeer's walkthrough lines from an analysis dict and caches them
as per-line MP3s under jobs/<jid>/tts/ DURING the meshing lane, so the
report's first voice tap is a cache hit instead of a cold synthesis.

Shape: build_tts_lines(analysis) -> [{"key": "overall"|"zone:<zone>",
"text": "<=600 chars"}]. Overall first (score + label + one-line summary),
then one line per scored finding (tldr + first cue). Insufficient zones are
skipped server-side (the client narrates its coach_unclear lines).

prewarm_for_job(job_dir, analysis, synthesize=None, voice="Kabir") writes
tts/<key>.mp3 + tts/manifest.json. synthesize(text, voice) -> bytes is
injected (server wires Inworld post-merge); None = dry-run manifest with
status "skipped". Fail-soft per line: errors are recorded, never raised.

POST-MERGE integration (core-loop merge handoff first; do NOT wire yet):
  run_pipeline meshing lane -> prewarm_for_job(d, analysis)
  GET /jobs/<jid>/tts/<key>.mp3 (cacheable) serves the files.
Run `python3 site/tts_prewarm.py --selftest` to check line + manifest math.
"""
import json
import os
import time

MAX_LINE_CHARS = 600
VOICE_DEFAULT = "Kabir"


def _clip(text, limit=MAX_LINE_CHARS):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def build_tts_lines(analysis):
    """Pure: analysis dict -> ordered [{key, text}]. Never raises on gaps."""
    analysis = analysis or {}
    lines = []
    overall = " ".join(str(analysis.get(k) or "") for k in
                       ("overall_label", "one_line_summary")).strip()
    score = analysis.get("overall_score")
    if overall or score is not None:
        lines.append({"key": "overall",
                      "text": _clip("Your form scores %s out of 100. %s"
                                    % (score, overall))})
    for z in analysis.get("findings") or []:
        if not isinstance(z, dict) or not z.get("zone") or z.get("zone_score") is None:
            continue
        cues = z.get("action") or []
        cue = cues[0] if cues else ""
        text = _clip("%s. %s%s" % (z.get("title") or z["zone"],
                                   z.get("tldr") or z.get("observation") or "",
                                   " Cue: %s." % cue if cue else ""))
        if text.strip(" ."):
            lines.append({"key": "zone:" + str(z["zone"]), "text": text})
    return lines


def prewarm_for_job(job_dir, analysis, synthesize=None, voice=VOICE_DEFAULT):
    """Cache walkthrough lines as tts/<key>.mp3 + manifest.json. Fail-soft."""
    tts_dir = os.path.join(job_dir, "tts")
    try:
        os.makedirs(tts_dir, exist_ok=True)
    except OSError:
        return {"status": "error", "lines": []}
    manifest = {"voice": voice, "ts": time.time(), "lines": []}
    for line in build_tts_lines(analysis):
        entry = {"key": line["key"], "chars": len(line["text"])}
        if synthesize is None:
            entry["status"] = "skipped"
        else:
            try:
                audio = synthesize(line["text"], voice)
                if not audio:
                    raise ValueError("empty audio")
                with open(os.path.join(tts_dir, line["key"].replace(":", "_")
                                       + ".mp3"), "wb") as f:
                    f.write(audio)
                entry.update(status="cached", bytes=len(audio))
            except Exception as e:
                entry.update(status="error", detail=str(e)[-120:])
        manifest["lines"].append(entry)
    try:
        with open(os.path.join(tts_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)
    except OSError:
        pass
    return manifest


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    demo = os.path.join(here, "jobs", "demo", "analysis.json")
    try:
        analysis = json.load(open(demo))
    except (OSError, ValueError):
        analysis = {"overall_score": 69, "overall_label": "Fair",
                    "one_line_summary": "test",
                    "findings": [{"zone": "feet_strike", "title": "Foot Strike",
                                  "zone_score": 62, "tldr": "Overstride.",
                                  "action": ["Land under hips", "x", "drill"]}]}
    lines = build_tts_lines(analysis)
    assert lines and lines[0]["key"] == "overall", lines
    assert all(len(l["text"]) <= MAX_LINE_CHARS for l in lines)
    assert len(lines) <= 8, lines  # overall + <=7 zones
    assert all(l["key"].startswith(("overall", "zone:")) for l in lines)
    # gaps never raise, insufficient-only yields overall-or-empty
    assert isinstance(build_tts_lines(None), list)
    assert build_tts_lines({"findings": [{"zone": "x"}]}) == []
    no_score = build_tts_lines({"findings": [{"zone": "hips_pelvis"}]})
    assert all(l["key"] != "zone:hips_pelvis" for l in no_score)
    # dry-run manifest round-trips to a temp job dir
    import tempfile
    job = tempfile.mkdtemp(prefix="tts_hook_")
    man = prewarm_for_job(job, analysis)
    assert all(e["status"] == "skipped" for e in man["lines"]), man
    assert json.load(open(os.path.join(job, "tts", "manifest.json")))["voice"] == "Kabir"
    # injected synthesizer caches bytes; failures record, never raise
    def fake(text, voice):
        return b"ID3" + text.encode()[:10]
    man2 = prewarm_for_job(job, analysis, synthesize=fake)
    assert all(e["status"] == "cached" and e["bytes"] > 3 for e in man2["lines"]), man2
    def boom(text, voice):
        raise RuntimeError("tts down")
    man3 = prewarm_for_job(job, analysis, synthesize=boom)
    assert all(e["status"] == "error" for e in man3["lines"]), man3
    print("tts_prewarm selftest: all checks passed")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        selftest()
    else:
        print("usage: python3 site/tts_prewarm.py --selftest")
