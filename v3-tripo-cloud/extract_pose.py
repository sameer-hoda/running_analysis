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
import json, math, sys
from ultralytics import YOLO

NAMES = ["NOSE","L_EYE","R_EYE","L_EAR","R_EAR","L_SH","R_SH","L_ELB","R_ELB",
         "L_WR","R_WR","L_HIP","R_HIP","L_KNEE","R_KNEE","L_ANK","R_ANK"]

def detect(img_path):
    model = YOLO("yolov8m-pose.pt")
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

if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else "output/skeleton.json"
    skel = retarget(detect(src))
    with open(dst, "w") as f:
        json.dump(skel, f, indent=1)
    print(f"pose: facing={skel['facing']:+d} cam_side={skel['cam_side']} stance={skel['stance']} -> {dst}")
