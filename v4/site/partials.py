#!/usr/bin/env python3
"""Gemini partials (pipeline-auth P2; server.py freeze-safe).

Score-first streaming: the audit persists overall_score immediately, then zone
findings as they arrive, so the loader + report render the score early and
zones stream in. All state lives in jobs/<jid>/analysis.partial.json.

Pure core: new_partial() / apply_update(partial, update) / promote(partial).
An update may carry overall_score/overall_label/one_line_summary, camera/
gait context keys, and/or one finding {zone,...} or insufficient {zone,...}.
Zones accumulate keyed by zone name; findings win over insufficient for the
same zone (contract keeps them disjoint: 7 zones across both lists).

promote() validates the step1_prompt.txt contract (overall_score + exactly 7
unique zones, scored findings carry zone_score) and returns an analysis-shaped
dict (extra context keys pass through). It does NOT write analysis.json —
the server promotes post-merge. File IO is only write_partial()/read_partial()
(atomic tmp+rename writes). Never raises on missing job dirs (returns None).

POST-MERGE integration (core-loop merge handoff first; do NOT wire yet):
  audit lane streams updates -> write_partial(d, update) per arrival;
  loader merges GET analysis.partial.json; run_pipeline promotes at seal.
Run `python3 site/partials.py --selftest` to check merge + promote math.
"""
import json
import os
import time

EXPECTED_ZONES = 7


def new_partial():
    return {"score": {}, "findings": {}, "insufficient": {}, "ts": time.time()}


def apply_update(partial, update):
    """Pure merge of one streamed update. Never raises on gap shapes."""
    partial = partial or new_partial()
    update = update or {}
    for key in ("overall_score", "overall_label", "one_line_summary",
                "camera_angle", "gait_phase", "foot_contact", "is_running"):
        if update.get(key) is not None:
            partial.setdefault("score", {})[key] = update[key]
    finding = update.get("finding")
    if isinstance(finding, dict) and finding.get("zone"):
        partial.setdefault("findings", {})[finding["zone"]] = finding
        (partial.setdefault("insufficient", {}) or {}).pop(finding["zone"], None)
    missing = update.get("insufficient")
    if isinstance(missing, dict) and missing.get("zone"):
        if missing["zone"] not in (partial.get("findings") or {}):
            partial.setdefault("insufficient", {})[missing["zone"]] = missing
    partial["ts"] = time.time()
    return partial


def promote(partial):
    """Validate the 7-zone contract -> analysis dict. Raises ValueError on gaps."""
    partial = partial or {}
    score = partial.get("score") or {}
    if score.get("overall_score") is None:
        raise ValueError("partial lacks overall_score")
    findings = partial.get("findings") or {}
    insufficient = partial.get("insufficient") or {}
    zones = set(findings) | set(insufficient)
    if len(zones) != EXPECTED_ZONES:
        raise ValueError("partial has %d/7 zones" % len(zones))
    for zone, finding in findings.items():
        if not isinstance(finding, dict) or finding.get("zone_score") is None:
            raise ValueError("zone %s lacks zone_score" % zone)
    analysis = dict(score)
    analysis["findings"] = [findings[z] for z in sorted(findings)]
    analysis["insufficient"] = [insufficient[z] for z in sorted(insufficient)]
    return analysis


def _partial_path(job_dir):
    return os.path.join(job_dir, "analysis.partial.json")


def write_partial(job_dir, update):
    """Load-merge-atomically-write one update. Returns merged partial or None."""
    try:
        current = read_partial(job_dir) or new_partial()
        merged = apply_update(current, update)
        tmp = _partial_path(job_dir) + ".tmp"
        with open(tmp, "w") as f:
            json.dump(merged, f)
        os.replace(tmp, _partial_path(job_dir))
        return merged
    except (OSError, ValueError):
        return None


def read_partial(job_dir):
    """Return the stored partial, or None (missing/corrupt/jobless)."""
    try:
        with open(_partial_path(job_dir)) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def selftest():
    # score-first, then zones stream
    p = apply_update(new_partial(), {"overall_score": 69, "overall_label": "Fair",
                                     "camera_angle": "side"})
    try:
        promote(p)
        raise AssertionError("promote must reject 0 zones")
    except ValueError:
        pass
    zones = ["head_neck", "shoulders", "arms_elbows", "trunk_lean",
             "hips_pelvis", "knees", "feet_strike"]
    for i, zone in enumerate(zones):
        upd = {"insufficient": {"zone": zone, "why": "needs view"}} \
            if zone == "hips_pelvis" else \
            {"finding": {"zone": zone, "zone_score": 60 + i, "tldr": "ok"}}
        p = apply_update(p, upd)
    assert p["score"]["overall_score"] == 69 and p["score"]["camera_angle"] == "side"
    a = promote(p)
    assert a["overall_score"] == 69 and len(a["findings"]) == 6
    assert len(a["insufficient"]) == 1 and len(a["findings"] + a["insufficient"]) == 7
    # finding overwrites insufficient for the same zone
    p2 = apply_update(p, {"finding": {"zone": "hips_pelvis", "zone_score": 70}})
    assert "hips_pelvis" not in p2["insufficient"] and promote(p2)["findings"]
    # unscored finding rejected at promote
    p3 = new_partial()
    p3 = apply_update(p3, {"overall_score": 50})
    for zone in zones:
        p3 = apply_update(p3, {"finding": {"zone": zone}})
    try:
        promote(p3)
        raise AssertionError("promote must reject missing zone_score")
    except ValueError:
        pass
    # gaps never raise; missing job dir returns None
    assert apply_update(None, None)["findings"] == {}
    assert read_partial("/nonexistent-job-dir") is None
    assert write_partial("/nonexistent-job-dir", {"overall_score": 1}) is None
    # file round-trip in a temp job dir
    import tempfile
    job = tempfile.mkdtemp(prefix="partials_hook_")
    assert read_partial(job) is None
    write_partial(job, {"overall_score": 69})
    for zone in zones:
        write_partial(job, {"finding": {"zone": zone, "zone_score": 60}})
    stored = read_partial(job)
    assert promote(stored)["overall_score"] == 69
    print("partials selftest: all checks passed")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        selftest()
    else:
        print("usage: python3 site/partials.py --selftest")
