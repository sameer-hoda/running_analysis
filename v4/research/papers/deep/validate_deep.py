#!/usr/bin/env python3
"""Validate research/papers/deep/ entries + alignment to catalog.json (stdlib only).

Run: python3 research/papers/deep/validate_deep.py   (from v4 root)
Exit 0 when green, 1 with reasons on stdout otherwise.

Checks per deep entry: required fields (summary, methods_signal, figure,
snippet, citation, rule_link), figure file exists + is well-formed XML,
citation URLs https, zone in the 7 step1_prompt.txt zones — AND alignment to
the catalog agent's canonical ruling: catalog_id must exist in
research/papers/catalog.json and the entry zone must be one of that catalog
row's zones.
"""
import glob
import json
import os
import sys
import xml.dom.minidom

ROOT = os.path.dirname(os.path.abspath(__file__))
PAPERS = os.path.dirname(ROOT)
ZONES = {"head_neck", "shoulders", "arms_elbows", "trunk_lean",
         "hips_pelvis", "knees", "feet_strike"}

errors = []


def err(msg):
    errors.append(msg)


try:
    catalog = json.load(open(os.path.join(PAPERS, "catalog.json")))
except (OSError, ValueError) as e:
    print("FAIL - catalog.json unreadable: %s" % e)
    sys.exit(1)
cat_zones = {p.get("id"): set(p.get("zones", [])) for p in catalog.get("papers", [])}

files = sorted(glob.glob(os.path.join(ROOT, "deep-*.json")))
if len(files) < 3:
    err("expected >=3 deep entries, found %d" % len(files))

seen_ids, seen_cat, seen_zones = set(), set(), set()
for f in files:
    try:
        d = json.load(open(f))
    except ValueError as e:
        err("%s: invalid JSON (%s)" % (os.path.basename(f), e))
        continue
    tag = d.get("deep_id", os.path.basename(f))
    for field in ("deep_id", "catalog_id", "rule_link", "summary",
                  "methods_signal", "snippet", "figure", "citation"):
        if field not in d:
            err("%s: missing field %s" % (tag, field))
    if tag in seen_ids:
        err("%s: duplicate deep_id" % tag)
    seen_ids.add(tag)

    rl = d.get("rule_link", {})
    zone = rl.get("zone")
    for field in ("zone", "finding_title", "how_it_backs"):
        if field not in rl:
            err("%s: rule_link missing %s" % (tag, field))
    if zone not in ZONES:
        err("%s: bad zone %r" % (tag, zone))
    seen_zones.add(zone)

    cid = d.get("catalog_id")
    if cid in seen_cat:
        err("%s: duplicate catalog_id %s" % (tag, cid))
    seen_cat.add(cid)
    if cid not in cat_zones:
        err("%s: catalog_id %r not in catalog.json ruling" % (tag, cid))
    elif zone is not None and zone not in cat_zones[cid]:
        err("%s: zone %r not in catalog zones %r for %s"
            % (tag, zone, sorted(cat_zones[cid]), cid))

    sn = d.get("snippet", {})
    if "text" not in sn or "grounds_in" not in sn:
        err("%s: snippet needs text + grounds_in" % tag)
    fig = d.get("figure", {})
    for field in ("file", "caption", "what_it_shows", "redrawn"):
        if field not in fig:
            err("%s: figure missing %s" % (tag, field))
    if fig.get("redrawn") is not True:
        err("%s: figure must be original redrawn schematic" % tag)
    fpath = os.path.join(ROOT, str(fig.get("file", "")))
    if not os.path.isfile(fpath):
        err("%s: figure file missing %s" % (tag, fig.get("file")))
    else:
        try:
            xml.dom.minidom.parse(fpath)
        except Exception as e:
            err("%s: figure not well-formed XML (%s)" % (tag, e))
    cit = d.get("citation", {})
    for field in ("authors", "year", "title", "journal",
                  "doi_url", "pubmed_url"):
        if field not in cit:
            err("%s: citation missing %s" % (tag, field))
    for field in ("doi_url", "pubmed_url"):
        if not str(cit.get(field, "")).startswith("https://"):
            err("%s: citation %s must be https" % (tag, field))

if errors:
    for e in errors:
        print("FAIL -", e)
    sys.exit(1)
print("DEEP GREEN - %d entries, zones %s, all catalog_ids aligned"
      % (len(files), sorted(z for z in seen_zones if z)))
