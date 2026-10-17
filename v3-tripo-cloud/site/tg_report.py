#!/usr/bin/env python3
"""Telegram activity + cost reports for RunForm (stdlib only).

  python3 site/tg_report.py --mode hourly [--dry-run]
  python3 site/tg_report.py --mode daily  [--dry-run]

Hourly sends only when the last hour contains API usage (gemini/tripo/tts);
otherwise it prints SKIP and exits 0 (systemd stays green, no noise).
Daily always sends: last 24h + all-time totals + costliest jobs.

Secrets: TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID from env or the sandbox .env.
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import usage  # noqa: E402


def _read_env_file(path):
    out = {}
    try:
        for line in open(path):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip("\"'")
    except OSError:
        pass
    return out


_ENV = _read_env_file(os.path.join(V3, ".env"))
BOT = os.environ.get("TELEGRAM_BOT_TOKEN") or _ENV.get("TELEGRAM_BOT_TOKEN", "")
CHAT = os.environ.get("TELEGRAM_CHAT_ID") or _ENV.get("TELEGRAM_CHAT_ID", "")


def send(text, dry_run=False):
    if dry_run or not BOT or not CHAT:
        return False
    body = urllib.parse.urlencode(
        {"chat_id": CHAT, "text": text}).encode()
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/sendMessage" % BOT, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode()).get("ok", False)


def fmt_ts(ts):
    return datetime.datetime.fromtimestamp(
        ts, datetime.timezone.utc).astimezone().strftime("%H:%M")


def pct(a, b):
    return "%.1f%%" % (100.0 * a / b) if b else "-"


def funnel_block(s):
    p = s["pages"]
    reps = p["report"] + p["demo"]
    lines = ["Funnel:",
             "Landing %d -> uploads %d (%s)" %
             (p["landing"], s["uploads"], pct(s["uploads"], p["landing"])),
             "Uploads %d -> done %d (%s) - failed %d" %
             (s["uploads"], s["done"], pct(s["done"], s["uploads"]),
              s["failed"]),
             "Reports viewed %d (%d demo) - loader %d - shared opened %d" %
             (reps, p["demo"], p["loader"], p["shared"])]
    return "\n".join(lines)


def block(title, s):
    lines = [title,
             "Jobs: %d submitted - %d done - %d failed" %
             (s["uploads"], s["done"], s["failed"]),
             "Gemini audits: %d (%dk in / %dk out)" %
             (s["gemini"], s["gemini_in"] // 1000, s["gemini_out"] // 1000),
             "Tripo builds: %d - TTS: %d calls (%d chars)" %
             (s["tripo"], s["tts"], s["tts_chars"]),
             "Cost: %s" % usage.fmt_usd(s["usd"])]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("hourly", "daily"), required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    now = time.time()

    if args.mode == "hourly":
        s = usage.summarize(usage.read_events(since=now - 3600))
        api_n = s["gemini"] + s["tripo"] + s["tts"]
        if api_n == 0:
            print("SKIP: no API usage in the last hour")
            return 0
        day = usage.summarize(usage.read_events(since=now - 86400))
        tot = usage.summarize(usage.read_events())
        msg = (block("RunForm hourly %s-%s: %d API calls" %
                     (fmt_ts(now - 3600), fmt_ts(now), api_n), s)
               + "\n" + funnel_block(s)
               + "\nToday so far: %s - All-time: %s" %
               (usage.fmt_usd(day["usd"]), usage.fmt_usd(tot["usd"])))
    else:
        s = usage.summarize(usage.read_events(since=now - 86400))
        tot = usage.summarize(usage.read_events())
        top = [jt for jt in
               sorted(s["jobs"].items(), key=lambda kv: -kv[1]["usd"])
               if jt[1]["usd"] > 0][:5]
        msg = (block("RunForm daily report (last 24h)", s)
               + "\n" + funnel_block(s))
        if top:
            msg += "\nCostliest jobs:\n" + "\n".join(
                "  %s: %s (%d events)" % (jid, usage.fmt_usd(j["usd"]),
                                          j["events"]) for jid, j in top)
        msg += "\nAll-time: %s across %d events" % (
            usage.fmt_usd(tot["usd"]), tot["n"])

    if args.dry_run or not BOT or not CHAT:
        print("---- message ----")
        print(msg)
        print("-----------------")
        if not args.dry_run:
            print("NOT SENT: set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID")
            return 2
        return 0
    ok = send(msg)
    print("sent" if ok else "SEND FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
