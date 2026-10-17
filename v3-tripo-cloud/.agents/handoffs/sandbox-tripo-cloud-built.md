# Sandbox built 2026-09-12 — analysis-page → integrator/backend

## What: `/Users/sameerhoda/Projects/running_analysis/v3-tripo-cloud/` (copy of v3, v3 untouched, still 200 on :8138)
- NEW `site/tripo_cloud.py`: Tripo v3 API (upload→task→poll→download) + `normalize_glb()` (trimesh/numpy only: face +X, feet y=0, height→1.0 for ZONE_BANDS, materials stripped — heat shell is the visible skin).
- `site/server.py`: meshing block → `tripo_cloud.build_mesh()` when TRIPO_API_KEY set, else demo-mesh stand-in (full UX clickable); WORKER_TIMEOUT 600s; port 8139; copy tweaks.
- NEW `requirements-light.txt` (Pillow/trimesh/numpy/google-genai, ~120MB, no torch), `.env.example`, `README-T3SMALL.md`, `deploy/t3-small-systemd.conf` (MemoryMax 1500M), `deploy/t3-small-nginx.conf` (proxy 8139, 600s timeouts, glb/mp4 cache).

## Verified
- `:8139/` landing 200, `/report/demo` 200, cloud copy live.
- Real cloud GLB (`output/tripo_api_beach.glb` 41MB/1.4M faces legacy) normalizes to height 1.000, ymin 0.000, centered; all 5 demo anchors resolve, no missing.
- NOTE: legacy 40MB files predate face_limit; new builds use `face_limit:40000, texture:false` → ~1MB, mobile-safe.

## For backend/integrator
- Needs `TRIPO_API_KEY` in sandbox `.env` for live personal rebuilds; without it, stand-in path is intentional.
- t3.small deploy: AL2023 + Python 3.11 + `requirements-light.txt` + systemd + nginx from `deploy/`.
- Sandbox server currently RUNNING on :8139 (pid via /tmp/tripo-cloud.log).
