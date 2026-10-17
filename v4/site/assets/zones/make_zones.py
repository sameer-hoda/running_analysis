#!/usr/bin/env python3
"""Instructional zone diagrams for the studio report (zone-art).

Run: set -a; . ../v3-tripo-cloud/.env; set +a; python3 site/assets/zones/make_zones.py [--check] [--only <zone>]
Output: site/assets/zones/<zone>.jpg (retro anatomical poster diagrams).

Style (per user refs, distinct from showcase-seo's monochrome PAPER covers):
retro anatomical instruction poster — off-white runner figure on dark
near-black background, lime-green (#c8f04a) callout arrows + short labels,
vintage-plate linework. Lime-on-dark compatible with the report theme.

Boundary: showcase-seo owns monochrome PAPER covers in
research/papers/covers/; these instructional ZONE diagrams are a different
style, no duplication.

Zones (7, match ZONE_BANDS/ZONE_GUIDES in site/server.py):
feet_strike, knees, trunk_lean, hips_pelvis, head_neck, shoulders, arms_elbows.
"""
import os
import sys

ZONES_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "gemini-2.5-flash-image"

STYLE = ("Retro anatomical instruction-poster illustration, vintage "
         "engraving linework with clean modern diagram overlays. A single "
         "athletic runner figure wearing a singlet and shorts (clothed, "
         "brand-fit — never nude), drawn in off-white on a dark near-black "
         "background (#0a0c11). Bright lime-green (#c8f04a) callout arrows "
         "and short "
         "uppercase labels pointing at the relevant body part. Only the labels named in the prompt may appear — no other words, codes, numbers, or symbols anywhere. No logos, brand marks, or trademarks on clothing. High contrast, "
         "print-poster composition, portrait 3:4. Keep any text to a few "
         "short uppercase words only, spelled exactly as given.")

PROMPTS = {
    "feet_strike": "Side view of a runner's lower leg and foot landing directly "
                   "under the hip with a MIDFOOT strike, small impact lines at "
                   "contact, a faded heel-first silhouette crossed out beside it "
                   "labelled OVERSTRIDE. Labels: LAND UNDER HIP, MIDFOOT. " + STYLE,
    "knees": "Side view of a runner at mid-swing with the swing knee driving "
             "forward and high, motion arc tracing the knee path, a low "
             "shuffling silhouette faded behind for contrast. Labels: DRIVE "
             "THE KNEE, QUICK TURNOVER. " + STYLE,
    "trunk_lean": "Side view of a full runner with a straight line from ankle "
                  "through hip to crown showing a slight forward lean from the "
                  "ankles, plumb-line overlay, a hunched-over silhouette faded "
                  "behind crossed out. Labels: TALL CROWN, LEAN FROM ANKLES. " + STYLE,
    "hips_pelvis": "Front view of a runner at midstance with level hips, a "
                   "horizontal lime line across the pelvis, glute activation "
                   "callout, a dropped-hip silhouette faded beside it crossed "
                   "out. Labels: LEVEL HIPS, STRONG GLUTES. " + STYLE,
    "head_neck": "Side-profile close-up of a runner's head and neck with a "
                 "steady forward gaze line to the horizon, relaxed long neck, "
                 "a chin-poking-forward silhouette faded behind crossed out. "
                 "Labels: STEADY GAZE, LONG NECK. " + STYLE,
    "shoulders": "Front view of a runner's relaxed low shoulders, tension "
                 "lines melting off the traps, a shrugged-tense silhouette "
                 "faded behind crossed out. Labels: LOW AND LOOSE, DROP THE "
                 "TENSION. " + STYLE,
    "arms_elbows": "Side view of a runner's bent arm swinging front-to-back "
                   "with a pendulum arc overlay near 90 degrees at the elbow, "
                   "hands relaxed, a cross-body arm silhouette faded behind "
                   "crossed out. Labels: 90 DEGREES, SWING BACK. " + STYLE,
}

ALL_ZONES = list(PROMPTS)


def check():
    missing = [z for z in ALL_ZONES
               if not os.path.isfile(os.path.join(ZONES_DIR, z + ".jpg"))]
    if missing:
        print("ZONES RED — missing: %s" % ", ".join(missing))
        return 1
    print("ZONES GREEN (%d zone diagrams)" % len(ALL_ZONES))
    return 0


def generate(only=None):
    from google import genai
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("GEMINI_API_KEY not set — source ../v3-tripo-cloud/.env first")
        return 1
    client = genai.Client(api_key=key)
    targets = [only] if only else ALL_ZONES
    for zone in targets:
        prompt = PROMPTS.get(zone)
        if not prompt:
            print("no prompt for %s — skipping" % zone)
            continue
        print("generating %s ..." % zone, flush=True)
        r = client.models.generate_content(model=MODEL, contents=[prompt])
        data = None
        for cand in getattr(r, "candidates", []) or []:
            for part in getattr(getattr(cand, "content", None), "parts", []) or []:
                inline = getattr(part, "inline_data", None)
                if inline and getattr(inline, "data", None):
                    data = inline.data
                    break
            if data:
                break
        if not data:
            print("FAIL — no image bytes for %s" % zone)
            return 1
        import base64
        raw = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
        fp = os.path.join(ZONES_DIR, zone + ".jpg")
        with open(fp, "wb") as f:
            f.write(raw)
        try:
            from PIL import Image
            im = Image.open(fp)
            im = im.convert("RGB").resize((600, 800))
            im.save(fp, "JPEG", quality=84)
        except Exception as e:
            print("note: kept raw bytes for %s (%s)" % (zone, e))
        print("wrote %s (%d bytes)" % (fp, os.path.getsize(fp)))
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    sys.exit(generate(only))
