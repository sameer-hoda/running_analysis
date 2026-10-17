#!/usr/bin/env python3
"""Validate research/papers/catalog.json against schema.json (stdlib only).

Run: python3 research/papers/validate.py   (from v4 root)
Exit 0 when green, 1 with reasons on stdout otherwise.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ZONES = {"head_neck", "shoulders", "arms_elbows", "trunk_lean",
         "hips_pelvis", "knees", "feet_strike"}

errors = []


def err(msg):
    errors.append(msg)


try:
    catalog = json.load(open(os.path.join(ROOT, "catalog.json")))
except (OSError, ValueError) as e:
    print("FAIL - catalog.json unreadable: %s" % e)
    sys.exit(1)

if not isinstance(catalog.get("version"), int):
    err("version must be int")
if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(catalog.get("updated", ""))):
    err("updated must be YYYY-MM-DD")

papers = catalog.get("papers")
if not isinstance(papers, list) or not papers:
    err("papers must be a non-empty array")
    papers = []

seen = set()
for i, p in enumerate(papers):
    tag = p.get("id", "#%d" % i)
    for field in ("id", "title", "authors", "year", "journal",
                  "link", "key_finding", "zones", "thumb"):
        if field not in p:
            err("%s: missing field %s" % (tag, field))
    if p.get("id") in seen:
        err("%s: duplicate id" % tag)
    seen.add(p.get("id"))
    if not re.match(r"^[a-z0-9-]+$", str(p.get("id", ""))):
        err("%s: bad id slug" % tag)
    if not isinstance(p.get("authors"), list) or not p.get("authors"):
        err("%s: authors must be a non-empty array" % tag)
    if not isinstance(p.get("year"), int) or not 1970 <= p["year"] <= 2030:
        err("%s: bad year" % tag)
    if not str(p.get("link", "")).startswith("https://"):
        err("%s: link must be https" % tag)
    zones = p.get("zones", [])
    if not zones or set(zones) - ZONES:
        err("%s: bad zones %r" % (tag, zones))
    thumb = os.path.join(ROOT, str(p.get("thumb", "")))
    if not os.path.isfile(thumb):
        err("%s: thumb missing %s" % (tag, p.get("thumb")))
    elif os.path.getsize(thumb) == 0:
        err("%s: thumb empty" % tag)
    hd = p.get("has_deep", False)
    did = p.get("deep_id")
    if hd:
        if not isinstance(did, str) or not re.match(r"^deep-[0-9]{3}$", did):
            err("%s: has_deep true needs deep_id like deep-001" % tag)
        elif not glob.glob(os.path.join(ROOT, "deep", did + "*.json")):
            err("%s: deep entry missing for %s" % (tag, did))
    elif did is not None:
        err("%s: deep_id without has_deep" % tag)
    if len(str(p.get("key_finding", ""))) < 20:
        err("%s: key_finding too short" % tag)

if errors:
    for e in errors:
        print("FAIL -", e)
    sys.exit(1)
print("CATALOG GREEN - %d papers, all thumbs resolve" % len(papers))
