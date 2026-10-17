#!/usr/bin/env python3
"""RunForm API usage + cost ledger (stdlib only).

Every billable or lifecycle event appends one JSON line to site/usage.log:
  {"ts": 1726..., "kind": "gemini_audit|tripo_build|tts|upload|job_done|job_failed",
   "job": "abc123"|null, "detail": {...}, "usd": 0.0012}

Rates are provider list prices (Sep 2026, see SOURCES) and overridable via env:
  RF_USD_PER_1M_GEMINI_IN / _OUT, RF_USD_PER_1M_TTS_CHARS, RF_USD_PER_TRIPO_BUILD,
  RF_USAGE_LOG (path override, used by tests).

Run `python3 site/usage.py --selftest` to check the cost math.
"""
import json
import os
import time

SOURCES = {
    "gemini_flash": "Gemini 3 Flash $0.50/1M in + $3.00/1M out "
                    "(Google + corroborating trackers, Sep 2026)",
    "inworld_tts2": "Inworld TTS-2 $25/1M chars on-demand (inworld.ai/pricing)",
    "tripo_build": "Tripo image-to-3D ~20-30 credits ~= $0.20-0.30 "
                   "(site/tripo_cloud.py header + fal proxy $0.20-0.40)",
}

HERE = os.path.dirname(os.path.abspath(__file__))


def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def rates():
    return {
        "gemini_in": _env_float("RF_USD_PER_1M_GEMINI_IN", 0.50),
        "gemini_out": _env_float("RF_USD_PER_1M_GEMINI_OUT", 3.00),
        "tts_chars": _env_float("RF_USD_PER_1M_TTS_CHARS", 25.0),
        "tripo_build": _env_float("RF_USD_PER_TRIPO_BUILD", 0.25),
    }


def log_path():
    return os.environ.get("RF_USAGE_LOG",
                          os.path.join(HERE, "usage.log"))


def cost_usd(kind, r=None, in_tokens=0, out_tokens=0, chars=0):
    """Pure cost math. Unknown kinds cost 0 (lifecycle events are free)."""
    r = r or rates()
    if kind == "gemini_audit":
        return in_tokens / 1e6 * r["gemini_in"] + out_tokens / 1e6 * r["gemini_out"]
    if kind == "tts":
        return chars / 1e6 * r["tts_chars"]
    if kind == "tripo_build":
        return r["tripo_build"]
    return 0.0


def log_event(kind, job=None, detail=None, in_tokens=0, out_tokens=0,
              chars=0, usd=None, ts=None):
    """Append one ledger line. Never raises (logging must not break serving)."""
    try:
        if usd is None:
            usd = cost_usd(kind, in_tokens=in_tokens, out_tokens=out_tokens,
                           chars=chars)
        line = {"ts": ts if ts is not None else time.time(), "kind": kind,
                "job": job, "detail": detail or {},
                "in_tokens": in_tokens, "out_tokens": out_tokens,
                "chars": chars, "usd": round(usd, 6)}
        with open(log_path(), "a") as f:
            f.write(json.dumps(line) + "\n")
        return line
    except OSError:
        return None


def read_events(since=None, path=None):
    out = []
    try:
        with open(path or log_path()) as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    ev = json.loads(raw)
                except ValueError:
                    continue
                if since is not None and ev.get("ts", 0) < since:
                    continue
                out.append(ev)
    except OSError:
        pass
    return out


def summarize(events):
    """Aggregate counts + costs. Pure function over event dicts."""
    s = {"n": 0, "usd": 0.0, "uploads": 0, "done": 0, "failed": 0,
         "gemini": 0, "gemini_in": 0, "gemini_out": 0, "tripo": 0,
         "tts": 0, "tts_chars": 0, "jobs": {},
         "pages": {"landing": 0, "loader": 0, "report": 0, "demo": 0,
                   "shared": 0, "upload_page": 0, "other": 0}}
    for ev in events:
        k = ev.get("kind")
        s["n"] += 1
        s["usd"] += ev.get("usd", 0) or 0
        if k == "upload":
            s["uploads"] += 1
        elif k == "job_done":
            s["done"] += 1
        elif k == "job_failed":
            s["failed"] += 1
        elif k == "gemini_audit":
            s["gemini"] += 1
            s["gemini_in"] += ev.get("in_tokens", 0)
            s["gemini_out"] += ev.get("out_tokens", 0)
        elif k == "tripo_build":
            s["tripo"] += 1
        elif k == "tts":
            s["tts"] += 1
            s["tts_chars"] += ev.get("chars", 0)
        elif k == "page":
            p = (ev.get("detail") or {}).get("page", "other")
            s["pages"][p if p in s["pages"] else "other"] += 1
        j = ev.get("job")
        if j:
            jst = s["jobs"].setdefault(j, {"usd": 0.0, "events": 0})
            jst["usd"] += ev.get("usd", 0) or 0
            jst["events"] += 1
    s["usd"] = round(s["usd"], 4)
    return s


def fmt_usd(x):
    return "$%.2f" % x if x >= 0.01 else "$%.4f" % x


def selftest():
    r = {"gemini_in": 0.50, "gemini_out": 3.00, "tts_chars": 25.0,
         "tripo_build": 0.25}
    # 1 audit: 12k image+prompt tokens in, 4k JSON out
    assert abs(cost_usd("gemini_audit", r, 12000, 4000) - 0.018) < 1e-9
    # teaser voice line: 45 chars
    assert abs(cost_usd("tts", r, chars=45) - 0.001125) < 1e-9
    # one cloud build flat
    assert cost_usd("tripo_build", r) == 0.25
    # lifecycle events are free
    assert cost_usd("upload", r) == 0.0
    assert cost_usd("job_done", r) == 0.0
    # end-to-end job: audit + build + 6 TTS lines ≈ $0.27
    e2e = (cost_usd("gemini_audit", r, 12000, 4000)
           + cost_usd("tripo_build", r) + cost_usd("tts", r, chars=600))
    assert abs(e2e - 0.283) < 1e-9, e2e
    # funnel: landing -> upload -> done, plus report/demo/shared views
    fevs = [{"kind": "page", "detail": {"page": "landing"}, "job": None,
             "usd": 0}] * 100
    fevs += [{"kind": "upload", "job": "j%d" % i, "usd": 0}
             for i in range(10)]
    fevs += [{"kind": "job_done", "job": "j%d" % i, "usd": 0}
             for i in range(8)]
    fevs += [{"kind": "page", "detail": {"page": "demo"}, "job": None,
              "usd": 0}] * 30
    fevs += [{"kind": "page", "detail": {"page": "shared"}, "job": "j1",
              "usd": 0}] * 5
    fs = summarize(fevs)
    assert fs["pages"]["landing"] == 100, fs["pages"]
    assert fs["pages"]["demo"] == 30 and fs["pages"]["shared"] == 5
    assert fs["uploads"] == 10 and fs["done"] == 8
    # ledger round-trip on a temp path
    import tempfile
    os.environ["RF_USAGE_LOG"] = tempfile.mktemp(prefix="usage_test_")
    try:
        log_event("gemini_audit", job="t1", in_tokens=12000, out_tokens=4000)
        log_event("tripo_build", job="t1")
        log_event("tts", job="t1", chars=600)
        log_event("job_done", job="t1")
        s = summarize(read_events())
        assert s["gemini"] == 1 and s["tripo"] == 1 and s["tts"] == 1
        assert s["done"] == 1 and abs(s["usd"] - 0.283) < 1e-3, s
    finally:
        try:
            os.remove(os.environ.pop("RF_USAGE_LOG"))
        except OSError:
            pass
    print("usage selftest: all checks passed")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        selftest()
    else:
        print("usage: python3 site/usage.py --selftest")
