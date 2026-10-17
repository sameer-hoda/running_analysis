#!/usr/bin/env python3
"""Tripo v3 cloud image-to-3D for the t3.small sandbox (NO torch, NO TripoSR local).

Pipeline per job:
  input.jpg -> POST /v3/files -> POST /v3/generation/image-to-model
  -> poll GET /v3/tasks/{id} -> download .glb -> normalize -> mesh.glb

Normalize (trimesh + numpy only, ~50MB deps) so the report heat shell looks good:
  - combine scene bounds, center x/z, feet y=0
  - scale height to 1.0 (matches ZONE_BANDS 0.00-1.00 fractions in server.py)
  - rotate to face +X like the local upright_bake (Tripo cloud faces +Z)
  - KEEP full PBR textures (base_color/metallic/roughness/normal)

Docs: https://developers.tripo3d.ai/en/docs/generation-image-to-model/standard
Cost: ~20-30 credits/build (~$0.20-0.30). Demo/sample reuses jobs/demo/mesh.glb ($0).
"""
import json
import os
import time
import urllib.request
import uuid

BASE = "https://openapi.tripo3d.ai/v3"
MODEL = os.environ.get("TRIPO_MODEL", "v3.1-20260211")
# Two lanes (env TRIPO_QUALITY=fast|best, default fast):
# - fast: standard texture+geometry, 50k faces, no autofix/align overhead.
#   Targets ~40-70s cloud builds, smaller files, fewer credits. Default,
#   because the heat shell carries the visuals anyway.
# - best: the documented max lane (PBR + detailed + Ultra + align_image,
#   100k faces). ~2min builds. Set TRIPO_QUALITY=best in .env for hero-grade.
QUALITY = os.environ.get("TRIPO_QUALITY", "fast").strip().lower()
FACE_LIMIT = int(os.environ.get("TRIPO_FACE_LIMIT",
                                "100000" if QUALITY == "best" else "50000"))


def _key():
    if os.environ.get("TRIPO_API_KEY"):
        return os.environ["TRIPO_API_KEY"]
    for base in (os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "/Users/sameerhoda/Projects/running_analysis/v3-tripo-cloud"):
        for name in (".env", "site/.env"):
            try:
                for line in open(os.path.join(base, name)):
                    if line.startswith("TRIPO_API_KEY="):
                        return line.split("=", 1)[1].strip().strip("\"'")
            except OSError:
                pass
    return ""


def _req(path, data=None, method=None, ctype="application/json", raw=None, timeout=120):
    key = _key()
    if not key:
        raise RuntimeError("TRIPO_API_KEY not set (add it to .env)")
    url = BASE + path
    headers = {"Authorization": "Bearer " + key}
    body = raw
    if data is not None:
        body = json.dumps(data).encode()
    if body is not None and ctype:
        headers["Content-Type"] = ctype
    req = urllib.request.Request(url, data=body, headers=headers,
                                 method=method or ("POST" if body else "GET"))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def upload_image(path):
    boundary = "----tripo" + uuid.uuid4().hex
    with open(path, "rb") as f:
        content = f.read()
    pre = ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"upload.jpg\"\r\n"
           "Content-Type: image/jpeg\r\n\r\n" % boundary).encode()
    post = ("\r\n--%s--\r\n" % boundary).encode()
    out = _req("/files", raw=pre + content + post,
               ctype="multipart/form-data; boundary=" + boundary)
    if out.get("code") != 0:
        raise RuntimeError("tripo upload failed: %s" % out)
    return out["data"]["file_token"]


def create_task(file_token):
    if QUALITY == "best":
        params = {
            "texture": True,               # full PBR skin (base_color/metallic/roughness/normal)
            "pbr": True,
            "texture_quality": "detailed",  # 'extreme' (8K) costs extra credits; detailed is the sweet spot
            "geometry_quality": "detailed",  # Ultra mode: finest geometry (v3.0+ only)
            "orientation": "align_image",    # align mesh to the photo viewpoint (needs texture:true)
            "texture_alignment": "original_image",
            "face_limit": FACE_LIMIT,
            "enable_image_autofix": True,    # enhance low-res inputs before generation
        }
    else:
        params = {
            "texture": True,               # base color only (pbr:false skips metal/rough/normal maps)
            "pbr": False,
            "texture_quality": "standard",  # fastest texture tier
            "geometry_quality": "standard",  # balanced geometry (heat shell hides the difference)
            "texture_alignment": "original_image",
            "face_limit": FACE_LIMIT,
            "enable_image_autofix": False,   # skip the enhance pass for speed
        }
    params.update({"input": file_token, "model": MODEL})
    task = _req("/generation/image-to-model", params)
    if task.get("code") != 0:
        raise RuntimeError("tripo task failed: %s" % task)
    return task["data"]["task_id"]


def wait_task(task_id, poll=5, timeout=540, cb=None):
    t0 = time.time()
    while True:
        info = _req("/tasks/" + task_id, timeout=60)
        d = info.get("data", {})
        st = d.get("status")
        if cb:
            try:
                cb(d.get("progress") or 0, st)
            except Exception:
                pass
        if st == "success":
            return d["output"]["model_url"]
        if st in ("failed", "cancelled", "banned"):
            raise RuntimeError("tripo generation %s: %s" % (st, d))
        if time.time() - t0 > timeout:
            raise RuntimeError("tripo poll timed out after %ss" % timeout)
        time.sleep(poll)


def download(url, dst, timeout=60):
    import shutil
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with urllib.request.urlopen(url, timeout=timeout) as r, open(dst, "wb") as f:
        shutil.copyfileobj(r, f, length=256 * 1024)
    return dst


def normalize_glb(src_glb, dst_glb):
    """Center + scale + face +X, KEEPING PBR textures. trimesh/numpy only.

    Works at scene level so texture/material bindings survive: bake the
    combined-bounds transform into every geometry, then export the scene.
    Height is scaled to 1.0 to match ZONE_BANDS fractions in server.py.
    """
    import numpy as np
    import trimesh
    scene = trimesh.load(src_glb, force="scene")
    if not isinstance(scene, trimesh.Scene):
        scene = trimesh.Scene(scene)
    # combined bounds across all geometries (in world frame)
    try:
        bounds = scene.bounding_box.bounds
    except Exception:
        geoms = [g for g in scene.dump(concatenate=False)]
        m0 = trimesh.util.concatenate(geoms)
        bounds = np.array([m0.vertices.min(0), m0.vertices.max(0)])
    (lo, hi) = bounds
    size, center = hi - lo, (hi + lo) / 2.0
    h = float(size[1]) or 1.0
    s = 1.0 / h
    # rotate cloud +Z-facing model to +X like local upright_bake
    R = np.array([[0., 0., 1.], [0., 1., 0.], [-1., 0., 0.]])
    c = R @ center
    # world v -> R@(v-c)*s + t, with t chosen so feet sit on y=0, x/z centered
    t = np.array([0.0, -s * (R @ lo)[1], 0.0]) - np.array([s * c[0], 0.0, s * c[2]])
    M = np.vstack([np.hstack([s * R, t.reshape(3, 1)]), [0, 0, 0, 1]])
    try:
        scene.apply_transform(M)
    except Exception:
        for name in list(scene.geometry.keys()):
            scene.geometry[name].apply_transform(M)
    scene.export(dst_glb)
    return dst_glb


def build_mesh(input_jpg, dst_glb, status_cb=None):
    def say(s):
        if status_cb:
            status_cb(s)

    say("uploading photo to Tripo cloud")
    token = upload_image(input_jpg)
    say("starting cloud 3D build")
    tid = create_task(token)
    say("building mesh in cloud (~1-3 min)")
    url = wait_task(tid)
    say("downloading + normalizing mesh")
    tmp = dst_glb + ".raw.glb"
    download(url, tmp)
    try:
        normalize_glb(tmp, dst_glb)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    return dst_glb
