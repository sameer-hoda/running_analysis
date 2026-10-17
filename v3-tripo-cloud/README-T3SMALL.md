# v3-tripo-cloud — t3.small sandbox (copy of v3, local TripoSR removed)

Goal: full RunForm experience on a `t3.small` (2 vCPU / 2GB / 30GB gp3,
AL2023, Python 3.11) for ~$22/mo instead of ~$95-155/mo.

## What changed vs v3
- `site/tripo_cloud.py` (NEW): Tripo v3 image-to-model via API —
  upload → task → poll → download → `normalize_glb()` (trimesh/numpy only:
  face +X, feet y=0, height scaled to 1.0 to match `ZONE_BANDS`, materials
  stripped because the heat shell is the visible skin).
- `site/server.py`: `run_pipeline()` meshing block calls `tripo_cloud.build_mesh()`
  when `TRIPO_API_KEY` is set, else copies `site/jobs/demo/mesh.glb` as a
  studio stand-in (report, anchors, tour all stay clickable). `WORKER_TIMEOUT`
  360→600s. Default port 8138→8139. V3 path → sandbox. Copy updated.
- Deleted from sandbox: `.venv` (1.7GB torch), `tripoSR_src/`, `motionbert_src/`,
  `yolov8m-pose.pt`, all `site/jobs/*` except `demo/`.
- New: `requirements-light.txt` (~120MB install, no torch), `.env.example`,
  `deploy/t3-small-systemd.conf`, `deploy/t3-small-nginx.conf`.

## Model look (why it still looks good)
- Report shows the **heat shell** (`group.clone()` + per-vertex IDW colors),
  base mesh hidden — so geometry quality matters most. Cloud call uses the
  documented best lane: `v3.1-20260211`, `texture:true, pbr:true`,
  `texture_quality:detailed`, `geometry_quality:detailed` (Ultra),
  `orientation:align_image`, `face_limit:100000`. No `compress` (meshopt GLBs
  need a decoder the r147 page doesn't ship). PBR textures are KEPT in
  `mesh.glb` for future textured-base views.
- `normalize_glb` works at scene level (textures survive): feet grounded,
  centered, +X facing so hero/front/side/back/top views and height-band
  anchors land correctly.
- Fail-loud: missing key or cloud error → job `failed` with the real error on
  the loader page (`Failed: …` + retry). NEVER a stand-in mesh — a wrong model
  is worse than an error.

## Speed (measured 2026-09-12, live paid builds)
- `fast` lane: report scores @ ~24s, mesh @ ~120s, 1.6MB GLB.
- `best` lane: report scores @ ~10s, mesh @ ~130s, 4.4MB GLB.
- Progressive UX (default): loader jumps to `/report/<jid>` the moment
  `analysis_ready` lands — scores/cards/drills in ~15-25s, spinner viewport
  polls `/api/jobs/<jid>` every 5s and hot-loads mesh+anchors at `done`.
  Perceived wait dropped ~5x with zero quality loss.

## Run locally
```
cd /Users/sameerhoda/Projects/running_analysis/v3-tripo-cloud
python3.11 -m venv venv && ./venv/bin/pip install -r requirements-light.txt
cp .env.example .env   # fill GEMINI_API_KEY + TRIPO_API_KEY
RUNFORM_ROOT=$PWD ./venv/bin/python site/server.py 8139
# open http://127.0.0.1:8139/  demo: /report/demo
```

## EC2 t3.small setup
1. Launch AL2023, t3.small, 30GB gp3, SG 22/80/443.
2. `sudo dnf install -y python3.11 git nginx && python3.11 -m venv ~/venv`
3. Copy sandbox (no `.venv`, no `reference/`, no `output/`), `pip install -r requirements-light.txt`.
4. Install `deploy/t3-small-systemd.conf` → `/etc/systemd/system/runform.service`, `systemctl enable --now runform`.
5. Install `deploy/t3-small-nginx.conf` (proxy 8139, `client_max_body_size 10M`), certbot.
