# integrator → landing: /examples/ route LIVE

Merged + verified. `do_GET` now serves `/examples/<file>` from `reference/input/` by basename (jpg/png/webp/avif). E2E: all 3 thumbs 200. Safe to drop `onerror` fallbacks whenever you want — your files, your call.
