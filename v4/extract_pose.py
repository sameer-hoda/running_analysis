"""Step 1b: true pose extraction for the RUNFORM v3 avatar.

Runs YOLOv8m-pose (ungated weights, CPU) on the analyzed photo, then
IK-retargets the detected joint DIRECTIONS onto anatomical segment lengths.
Result: skeleton JSON whose angles come from the photo, not hand placement.

Usage (from v3 root, venv active):
    source .venv/bin/activate
    python extract_pose.py reference/input/<photo>.jpg output/skeleton_<name>.json

Output joints are meters, y-up, root at hips, facing +X, camera-side limbs +z.
Only L/R root split + depth stagger are presentation priors (flagged in HTML).
"""
import json, math, os, sys

YOLO_WEIGHTS_DEFAULT = "/Users/sameerhoda/Projects/running_analysis/v3/yolov8m-pose.pt"


def _weights():
    for cand in (os.environ.get("YOLO_WEIGHTS"), YOLO_WEIGHTS_DEFAULT,
                 "yolov8m-pose.pt"):
        if cand and os.path.isfile(cand):
            return cand
    raise RuntimeError("YOLO pose weights not found (set YOLO_WEIGHTS)")

NAMES = ["NOSE","L_EYE","R_EYE","L_EAR","R_EAR","L_SH","R_SH","L_ELB","R_ELB",
         "L_WR","R_WR","L_HIP","R_HIP","L_KNEE","R_KNEE","L_ANK","R_ANK"]

def detect(img_path):
    from ultralytics import YOLO
    model = YOLO(_weights())
    res = model.predict(img_path, verbose=False)[0]
    assert res.keypoints is not None and len(res.keypoints) > 0, "NO PERSON DETECTED"
    best = int(res.keypoints.conf.mean(1).argmax()) if len(res.keypoints) > 1 else 0
    xy, cf = res.keypoints.xy[best].tolist(), res.keypoints.conf[best].tolist()
    W, H = res.orig_shape[1], res.orig_shape[0]
    return {n: {"x": xy[i][0]/W, "y": xy[i][1]/H, "conf": cf[i]} for i, n in enumerate(NAMES)}

def retarget(d, height=1.78):
    P = lambda n: (d[n]["x"], d[n]["y"])
    mid = lambda a, b: ((a[0]+b[0])/2, (a[1]+b[1])/2)
    shM, hipM = mid(P("L_SH"), P("R_SH")), mid(P("L_HIP"), P("R_HIP"))
    facing = 1 if d["NOSE"]["x"] > shM[0] else -1
    cam_side = "R" if d["R_EAR"]["conf"] >= d["L_EAR"]["conf"] else "L"
    raw = {n: (facing*(x-hipM[0]), hipM[1]-y)
           for n, (x, y) in ((n, P(n)) for n in NAMES)}
    def v(a, b):
        dx, dy = b[0]-a[0], b[1]-a[1]
        L = math.hypot(dx, dy) or 1e-6
        return (dx/L, dy/L)
    SEG = {"thigh": 0.245*height, "shin": 0.246*height, "trunk": 0.288*height,
           "uarm": 0.170*height, "farm": 0.160*height, "hand": 0.108*height,
           "neck": 0.07}
    S = {"HIPM": (0.0, 1.00, 0.0)}
    dL, dR = v(raw["L_HIP"], raw["L_SH"]), v(raw["R_HIP"], raw["R_SH"])
    td = ((dL[0]+dR[0])/2, (dL[1]+dR[1])/2)
    L = math.hypot(*td); td = (td[0]/L, td[1]/L)
    S["SHM"] = (td[0]*SEG["trunk"], 1.00+td[1]*SEG["trunk"], 0.0)
    S["R_SH"] = (S["SHM"][0]-0.03, S["SHM"][1]-0.01, +0.21)
    S["L_SH"] = (S["SHM"][0]+0.03, S["SHM"][1]-0.01, -0.21)
    S["R_HIP"] = (-0.02, 1.00, +0.10)
    S["L_HIP"] = (+0.02, 1.00, -0.10)
    def chain(js, lens, side):
        z = {"ELB": 0.21, "WR": 0.21, "KNEE": 0.10, "ANK": 0.10}
        pts = [S[js[0]]]
        for j, Ls in zip(js[1:], lens):
            prev = js[js.index(j)-1]
            dd = v(raw[prev], raw[j])
            p0 = pts[-1]
            key = "".join(k for k in ("ELB", "WR", "KNEE", "ANK") if k in j)
            zz = (1 if side == "R" else -1) * z[key]
            pts.append((p0[0]+dd[0]*Ls, p0[1]+dd[1]*Ls, zz))
            S[j] = pts[-1]
    chain(["R_SH", "R_ELB", "R_WR"], [SEG["uarm"], SEG["farm"]], "R")
    chain(["L_SH", "L_ELB", "L_WR"], [SEG["uarm"], SEG["farm"]], "L")
    chain(["R_HIP", "R_KNEE", "R_ANK"], [SEG["thigh"], SEG["shin"]], "R")
    chain(["L_HIP", "L_KNEE", "L_ANK"], [SEG["thigh"], SEG["shin"]], "L")
    for s in ("R", "L"):
        dd = v(raw[s+"_ELB"], raw[s+"_WR"])
        w = S[s+"_WR"]
        S[s+"_HAND"] = (w[0]+dd[0]*SEG["hand"], w[1]+dd[1]*SEG["hand"], w[2])
    S["NECK"] = (S["SHM"][0]+td[0]*SEG["neck"], S["SHM"][1]+td[1]*SEG["neck"], 0.0)
    nd = v(mid(raw["L_SH"], raw["R_SH"]), raw["NOSE"])
    S["HEAD"] = (S["NECK"][0]+nd[0]*0.13, S["NECK"][1]+nd[1]*0.13, 0.0)
    stance = "R_ANK" if S["R_ANK"][1] < S["L_ANK"][1] else "L_ANK"
    for s in ("R", "L"):
        a = S[s+"_ANK"]
        if s+"_ANK" == stance:
            S[s+"_TOE"] = (a[0]+0.17, a[1], a[2])
        else:
            dd = v(raw[s+"_KNEE"], raw[s+"_ANK"])
            S[s+"_TOE"] = (a[0]+dd[0]*0.17, a[1]+dd[1]*0.17, a[2])
    dy = 0.07 - S[stance][1]
    S = {k: (x, y+dy, z) for k, (x, y, z) in S.items()}
    return {"facing": facing, "cam_side": cam_side, "stance": stance,
            "joints": {k: [round(a, 3) for a in p] for k, p in S.items()}}

def detect_persons(img_path, conf=0.35):
    """All person boxes as [((x1, y1, x2, y2) pixels, conf)], area-desc.
    Lazy ultralytics import; raises RuntimeError when stack/weights missing."""
    from ultralytics import YOLO
    model = YOLO(_weights())
    res = model.predict(img_path, verbose=False)[0]
    boxes = res.boxes
    if boxes is None or len(boxes) == 0:
        return []
    out = [((float(x1), float(y1), float(x2), float(y2)), float(c))
           for (x1, y1, x2, y2), c in
           zip(boxes.xyxy.tolist(), boxes.conf.tolist()) if c >= conf]
    out.sort(key=lambda b: (b[0][2] - b[0][0]) * (b[0][3] - b[0][1]),
             reverse=True)
    return out


def isolate_runners(jpeg_bytes, detect_fn=None, margin=0.15, min_persons=2):
    """Single-runner guarantee. Returns (jpeg_bytes, info) where info is
    {"isolated": bool, "persons": N, "box": [x1,y1,x2,y2]|None, reason}.
    With >= min_persons detected, crops to the largest bbox (+margin,
    clamped); otherwise returns the input unchanged. detect_fn(jpeg_bytes)
    is injectable (unit tests run weight-free); default runs YOLO via a temp
    file. Detector failure -> unchanged + reason (fail-soft); corrupt image
    input still raises (callers sanitize first)."""
    from PIL import Image
    import io
    import tempfile
    im = Image.open(io.BytesIO(jpeg_bytes)).convert("RGB")
    W, H = im.size
    try:
        if detect_fn is None:
            with tempfile.NamedTemporaryFile(suffix=".jpg",
                                             delete=True) as tmp:
                tmp.write(jpeg_bytes)
                tmp.flush()
                persons = detect_persons(tmp.name)
        else:
            persons = detect_fn(jpeg_bytes)
    except Exception as e:
        return jpeg_bytes, {"isolated": False, "persons": 0, "box": None,
                            "reason": "detector: %s" % str(e)[-120:]}
    persons = persons or []
    if len(persons) < min_persons:
        return jpeg_bytes, {"isolated": False, "persons": len(persons),
                            "box": None, "reason": None}
    (x1, y1, x2, y2), _ = persons[0]
    bw, bh = max(1.0, x2 - x1), max(1.0, y2 - y1)
    x1 = max(0.0, x1 - margin * bw)
    y1 = max(0.0, y1 - margin * bh)
    x2 = min(float(W), x2 + margin * bw)
    y2 = min(float(H), y2 + margin * bh)
    crop = im.crop((int(round(x1)), int(round(y1)),
                    int(round(x2)), int(round(y2))))
    buf = io.BytesIO()
    crop.save(buf, "JPEG", quality=88)
    box = [int(round(v)) for v in (x1, y1, x2, y2)]
    return buf.getvalue(), {"isolated": True, "persons": len(persons),
                            "box": box, "reason": None}


def selftest():
    """Weight-free: injected detector (no ultralytics/network)."""
    from PIL import Image
    import io
    base = Image.new("RGB", (400, 300), (10, 20, 30))
    buf = io.BytesIO()
    base.save(buf, "JPEG", quality=88)
    raw = buf.getvalue()

    def two(_jpg):
        return [((200, 40, 360, 280), 0.9), ((10, 60, 120, 260), 0.8)]

    out, info = isolate_runners(raw, detect_fn=two)
    assert info["isolated"] and info["persons"] == 2, info
    got = Image.open(io.BytesIO(out)).size
    # largest box (160x240) + 15% margin each side, clamped: (176,4)-(384,300)
    assert got == (208, 296), (got, info)
    assert out != raw
    one = isolate_runners(raw, detect_fn=lambda _j: [((10, 10, 100, 100), 0.9)])
    assert one[0] == raw and one[1]["isolated"] is False
    zero = isolate_runners(raw, detect_fn=lambda _j: [])
    assert zero[0] == raw and zero[1]["persons"] == 0
    # margin expands then clamps at image edges: (343,243)-(400,300)
    edge, einfo = isolate_runners(
        raw, detect_fn=lambda _j: [((350, 250, 399, 299), 0.9),
                                   ((0, 0, 20, 20), 0.8)])
    assert einfo["isolated"] and Image.open(io.BytesIO(edge)).size == (57, 57)
    # detector failure -> unchanged + reason (covers missing stack/weights)
    skip, sinfo = isolate_runners(raw, detect_fn=_boom)
    assert skip == raw and sinfo["isolated"] is False and sinfo["reason"]
    print("extract_pose selftest: all checks passed")


def _boom(_jpg):
    raise RuntimeError("no detector")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else "output/skeleton.json"
    skel = retarget(detect(src))
    with open(dst, "w") as f:
        json.dump(skel, f, indent=1)
    print(f"pose: facing={skel['facing']:+d} cam_side={skel['cam_side']} stance={skel['stance']} -> {dst}")
