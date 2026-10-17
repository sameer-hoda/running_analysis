#!/usr/bin/env python3
"""Generate a premium homepage model with the Tripo v3 API (H-series, PBR).

Docs: https://developers.tripo3d.ai/en/docs/generation-image-to-model/standard
  1. POST /v3/files                         (multipart image -> file_token)
  2. POST /v3/generation/image-to-model     (file_token -> task_id)
  3. GET  /v3/tasks/{task_id}               (poll -> output.model_url)
  4. download model_url -> .glb

Setup: put TRIPO_API_KEY=... in the project .env (1 credit = $0.01; image-to-3D ~20-30 credits).
Usage: source .venv/bin/activate && python site/premium_model.py reference/input/images-3.jpeg site/assets/hero.glb
"""
import json
import os
import sys
import time
import urllib.request
import uuid

V3 = "/Users/sameerhoda/Projects/running_analysis/v3"
BASE = "https://openapi.tripo3d.ai/v3"
MODEL = "v3.1-20260211"  # latest/best; v2.5-20250123 is cheaper


def env(key):
    if os.environ.get(key):
        return os.environ[key]
    try:
        for line in open(os.path.join(V3, ".env")):
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return ""


KEY = env("TRIPO_API_KEY")


def req(path, data=None, method=None, ctype="application/json", raw=None):
    url = BASE + path
    headers = {"Authorization": "Bearer " + KEY}
    body = raw
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = ctype
    r = urllib.request.Request(url, data=body, headers=headers, method=method or ("POST" if body else "GET"))
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read().decode())


def upload_image(path):
    boundary = "----tripo" + uuid.uuid4().hex
    name = os.path.basename(path)
    with open(path, "rb") as f:
        content = f.read()
    pre = ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
           "Content-Type: image/jpeg\r\n\r\n" % (boundary, name)).encode()
    post = ("\r\n--%s--\r\n" % boundary).encode()
    raw = pre + content + post
    out = req("/files", raw=raw, ctype="multipart/form-data; boundary=" + boundary)
    if out.get("code") != 0:
        raise SystemExit("upload failed: %s" % out)
    return out["data"]["file_token"]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    img = sys.argv[1]
    out_glb = sys.argv[2] if len(sys.argv) > 2 else os.path.join(V3, "site", "assets", "hero.glb")
    if not KEY:
        sys.exit("TRIPO_API_KEY not set (add it to .env) — falling back to the local TripoSR pipeline otherwise.")

    print("1/4 uploading", img)
    token = upload_image(img)
    print("    file_token:", token)

    print("2/4 creating image-to-model task")
    task = req("/generation/image-to-model", {
        "input": token,
        "model": MODEL,
        "texture": True,
        "pbr": True,
        "texture_quality": "detailed",
        "geometry_quality": "detailed",
        "face_limit": 120000,
        "enable_image_autofix": True,
    })
    if task.get("code") != 0:
        raise SystemExit("task failed: %s" % task)
    tid = task["data"]["task_id"]
    print("    task_id:", tid)

    print("3/4 waiting for the model")
    while True:
        info = req("/tasks/" + tid)
        d = info.get("data", {})
        st = d.get("status")
        print("    %s %s%%" % (st, d.get("progress")))
        if st == "success":
            url = d["output"]["model_url"]
            break
        if st in ("failed", "cancelled", "banned"):
            raise SystemExit("generation %s" % st)
        time.sleep(5)

    print("4/4 downloading", url)
    os.makedirs(os.path.dirname(out_glb), exist_ok=True)
    urllib.request.urlretrieve(url, out_glb)
    print("wrote", out_glb, "%.1f MB" % (os.path.getsize(out_glb) / 1e6))


if __name__ == "__main__":
    main()
