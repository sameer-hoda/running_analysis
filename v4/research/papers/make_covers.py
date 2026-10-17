#!/usr/bin/env python3
"""Square editorial covers for the fade-pro research carousel (cover-art).

Run: set -a; . ../v3-tripo-cloud/.env; set +a; python3 research/papers/make_covers.py [--check] [--only <slug>]
Output: research/papers/covers/<id>.jpg (800x800, native square for the
fade-card image slot — generated square, never force-fit).

Design system: mono-color editorial print (one-ink + one accent on a dark
ground for the lime-on-dark site). Each cover bakes three text zones: a
small-caps kicker (journal · year) across the top, one colossal condensed
keyword in the middle, and a ruled footer strip (the takeaway). The full paper
title + finding stay as crisp HTML in the card — the baked keyword is the
at-a-glance signal. Referenced by slug convention (covers/<id>.jpg);
catalog.json schema is untouched. Real API (gemini-2.5-flash-image).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
COVERS = os.path.join(ROOT, "covers")
CATALOG = os.path.join(ROOT, "catalog.json")
MODEL = "gemini-2.5-flash-image"
SIZE = (800, 800)

CANVAS = ("Square 1:1 editorial poster, flat front-facing print, absolute "
          "full-bleed: black ink fills the entire image to the extreme edge "
          "pixels, no light margin anywhere, no paper edge visible, no border, "
          "no frame, no mockup, no shadow. Deep black paper ground, off-white "
          "printing ink with exactly one accent ink in lime green; nothing else "
          "colored. Layout in three bands: a small-caps kicker line across the "
          "top eighth, one colossal condensed uppercase keyword dominating the "
          "middle, a ruled footer strip across the bottom eighth, and a "
          "halftone running figure that keeps clear of the letterforms. All "
          "baked text spelled exactly as given, each word appearing once, fully "
          "legible, no repeated words, no invented words, no clipped words. "
          "Crisp halftone screening with visible dots, hard duotone contrast, "
          "mild ink bleed and 1mm plate misregistration. No gradients, no drop "
          "shadows, no 3D letters, no photorealistic full bodies, no brand "
          "marks or logos on shoes or kit, no URLs, no sponsors, no watermarks.")

# Per paper: (kicker, keyword, footer, figure). Kicker/footer are short by
# design — the card's HTML carries the full title + finding crisply.
COPY = {
    "lieberman-2010":
    ("NATURE 2010", "LAND SOFTLY", "FOREFOOT STRIKE · LESS IMPACT",
     "a huge halftone barefoot forefoot-plant on the right half, toes pointing "
     "down, a small lime impact burst under the ball of the foot"),

    "heiderscheit-2011":
    ("MSSE 2011", "QUICKER STEPS", "RAISE CADENCE · UNLOAD THE KNEES",
     "three halftone lower-leg strides crossing the page in a printed cadence "
     "rhythm, the middle leg printed in lime, the rest in off-white"),

    "souza-2016":
    ("PHYS MED REHAB CLIN 2016", "EVERY ANGLE", "SEVEN ZONES · ONE FRAME",
     "a halftone side-profile runner at mid-stride inside thin lime viewfinder "
     "corner brackets; the only words on the figure are exactly two labels, "
     "FRONT at the shoulder and SIDE at the hip, one each"),

    "daoud-2012":
    ("MSSE 2012", "2X", "TWICE THE INJURIES",
     "a small screened heel-plant fragment grounding the base of the numerals"),

    "cavanagh-lafortune-1980":
    ("J BIOMECH 1980", "READ THE FORCE", "STRIKE INDEX · GROUND REACTION",
     "a towering ruled force-curve spike chart with its peak tipped in lime, "
     "one isolated halftone foot specimen numbered 01 at the base"),

    "van-gent-2007":
    ("BR J SPORTS MED 2007", "79 PERCENT", "MOST RUNNERS GET HURT",
     "a large halftone runner sprinting across the full middle band on a ruled "
     "baseline, filling the space between keyword and footer with no large "
     "empty areas"),

    "bramah-2018":
    ("AM J SPORTS MED 2018", "SPOT THE CLUSTER", "PELVIC DROP · TRUNK LEAN",
     "two overlapping halftone runner profiles at midstance in plain unbranded "
     "kit with plain unbranded shoes, a single hand-drawn lime arrow marking "
     "the pelvic drop, no words anywhere on the figures"),

    "schubert-2014":
    ("SPORTS HEALTH 2014", "SHORTER QUICKER", "SHORTEN STRIDE · LESS LOAD",
     "horizontal motion-blur bands of halftone cadence legs streaking edge to "
     "edge across the page"),

    "xu-2021":
    ("SPORTS HEALTH 2021", "SHIFT THE LOAD", "HEEL VS FOREFOOT",
     "a split field: a heel-first landing in off-white with the label HEEL "
     "appearing exactly once on the left, a forefoot landing printed in lime "
     "with the label FOREFOOT appearing exactly once on the right"),

    "willwacher-2022":
    ("SPORTS MED 2022", "NO SINGLE SCORE", "LOAD · MECHANICS · CONTEXT",
     "a ruled list of struck-through numbers reading exactly 100, 180, 10K "
     "with one lime check mark, a small halftone distance runner anchoring "
     "the foot"),

    "teng-powers-2014":
    ("J ORTHOP SPORTS PHYS THER 2014", "LEAN 7 DEGREES",
     "FORWARD LEAN · LESS KNEE STRESS",
     "a halftone runner leaning forward up a hill beside a giant tabular 7 "
     "with a lime degree mark"),
}


def prompt_for(slug):
    kicker, keyword, footer, figure = COPY[slug]
    return ("Editorial cover. " + CANVAS +
            " Kicker across the top eighth reading exactly %s. "
            "Keyword %s in colossal condensed uppercase caps filling the middle. "
            "Ruled footer strip at the base reading exactly %s. "
            "Figure: %s." % (kicker, keyword, footer, figure))


PROMPTS = {slug: prompt_for(slug) for slug in COPY}


def catalog_ids():
    with open(CATALOG) as f:
        cat = json.load(f)
    return [p["id"] for p in cat["papers"]]


def check():
    ids = catalog_ids()
    missing = [i for i in ids if not os.path.isfile(os.path.join(COVERS, i + ".jpg"))]
    extra = [n[:-4] for n in os.listdir(COVERS) if n.endswith(".jpg")] if os.path.isdir(COVERS) else []
    extra = [e for e in extra if e not in ids]
    if missing:
        print("COVERS RED — missing: %s" % ", ".join(missing))
        return 1
    print("COVERS GREEN (%d covers, no schema change)%s" % (
        len(ids), " — extra files: %s" % ", ".join(extra) if extra else ""))
    return 0


def generate(only=None):
    from google import genai
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("GEMINI_API_KEY not set — source ../v3-tripo-cloud/.env first")
        return 1
    client = genai.Client(api_key=key)
    os.makedirs(COVERS, exist_ok=True)
    ids = catalog_ids()
    unknown = [k for k in (PROMPTS) if k not in ids]
    if unknown:
        print("prompt slugs not in catalog: %s" % ", ".join(unknown))
        return 1
    targets = [only] if only else ids
    for slug in targets:
        prompt = PROMPTS.get(slug)
        if not prompt:
            print("no prompt for %s — skipping" % slug)
            continue
        print("generating %s ..." % slug, flush=True)
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
            print("FAIL — no image bytes for %s" % slug)
            return 1
        raw = bytes(data) if isinstance(data, (bytes, bytearray)) else __import__("base64").b64decode(data)
        fp = os.path.join(COVERS, slug + ".jpg")
        with open(fp, "wb") as f:
            f.write(raw)
        try:
            from PIL import Image
            im = Image.open(fp).convert("RGB")
            w, h = im.size
            side = min(w, h)
            im = im.crop(((w - side) // 2, (h - side) // 2,
                          (w + side) // 2, (h + side) // 2))
            im = im.resize(SIZE)
            im.save(fp, "JPEG", quality=82)
        except Exception as e:
            print("note: kept raw bytes for %s (%s)" % (slug, e))
        print("wrote %s (%d bytes)" % (fp, os.path.getsize(fp)))
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    sys.exit(generate(only))
