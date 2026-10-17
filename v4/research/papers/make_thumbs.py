#!/usr/bin/env python3
"""Generate lime-on-dark SVG thumbnails for every paper in catalog.json.

Run: python3 research/papers/make_thumbs.py   (from v4 root)
Output: research/papers/thumbs/<id>.svg (400x300, no network, no fonts needed).

Thumbs are original text cards (title/authors/journal), not scans of
publisher PDFs, so the repo carries no third-party images.
"""
import html
import json
import os
import textwrap

ROOT = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(ROOT, "catalog.json")
THUMBS = os.path.join(ROOT, "thumbs")

W, H = 400, 300


def thumb_svg(paper):
    title = paper["title"]
    lines = textwrap.wrap(title, width=34)[:6]
    author = ", ".join(paper["authors"])
    meta = "%s · %d" % (paper["journal"], paper["year"])
    zones = " ".join(z.replace("_", " ") for z in paper["zones"])

    y = 96
    title_els = []
    for ln in lines:
        title_els.append(
            '<text x="28" y="%d" font-size="19" font-weight="700" fill="#f4f7f2"'
            ' font-family="system-ui,sans-serif">%s</text>' % (y, html.escape(ln)))
        y += 26

    return """<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">
<rect width="%d" height="%d" rx="16" fill="#0a0c11"/>
<rect width="%d" height="%d" rx="16" fill="none" stroke="#1c232d" stroke-width="2"/>
<rect x="0" y="0" width="10" height="%d" rx="5" fill="#c8f04a"/>
<text x="28" y="42" font-size="12" letter-spacing="3" fill="#c8f04a" font-family="system-ui,sans-serif">RUNFORM EVIDENCE</text>
%s
<text x="28" y="%d" font-size="13" fill="#8b938a" font-family="system-ui,sans-serif">%s</text>
<text x="28" y="%d" font-size="12" fill="#5b635c" font-family="system-ui,sans-serif">%s</text>
<text x="28" y="278" font-size="11" fill="#c8f04a" font-family="system-ui,sans-serif">%s</text>
</svg>
""" % (W, H, W, H, W, H, W, H, H,
        "\n".join(title_els),
        y + 8, html.escape(author),
        y + 28, html.escape(meta),
        html.escape(zones))


def main():
    with open(CATALOG) as f:
        catalog = json.load(f)
    os.makedirs(THUMBS, exist_ok=True)
    for paper in catalog["papers"]:
        path = os.path.join(THUMBS, paper["id"] + ".svg")
        with open(path, "w") as f:
            f.write(thumb_svg(paper))
        print("wrote", os.path.relpath(path, os.path.dirname(ROOT)))


if __name__ == "__main__":
    main()
