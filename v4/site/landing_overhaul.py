"""Landing overhaul (landing-ux, 2026-09-20) — additive-only landing sections.

Covers REQUESTS_AUDIT items 3 (bold-promise H1), 4 (proof/nudge thread),
7 (privacy-first baked into landing), 26 (landing overhaul) while leaving
item 27 (showcase studies beauty) untouched.

Contract with core-loop + showcase-seo:
- This file is NEW and self-contained (pure strings, no imports). server.py
  hooks it in with a ~6-line diff (import + CSS_ADD in <head>, hero copy
  swap, PROOF_HTML + PRIVACY_HTML inserts, upload microcopy). Revert = drop
  those lines; nothing else in server.py depends on this module.
- Anchors preserved: id=science, SCIENCE_HTML/_showcase papers markup,
  ItemList/ScholarlyArticle JSON-LD, all 11 titles server-rendered, the
  word "stride" on landing (e2e §1), carousel ids (scRail/scPrev/scDots).
- Taste: flat lime-on-dark only — no gradients, no glass blur, no bento,
  no hover:scale, no emoji, no scroll-fade; nothing animated so
  prefers-reduced-motion is trivially honored. All radii/class names are
  lu- prefixed so showcase (.sc-) and core (.step/.card) styles never
  collide.
- Honesty: no fake testimonials or invented stats. Proof items point at
  real routes (/report/aeb979a86e8b, /#science, /#faq, /history). Privacy copy
  matches the upload-session contract (Gemini scores, Tripo cloud
  rebuilds, guest cookie, history-deletable).
"""

CSS_ADD = (
    "<style>"
    ".lu-trust{color:var(--dim);font-size:13.5px;line-height:1.7;margin:20px 0 0;max-width:56ch}"
    ".lu-trust a{color:var(--lime)}"
    ".lu-proof{border-top:1px solid var(--line);border-bottom:1px solid var(--line);"
    "padding:56px 22px 0}"
    ".lu-proof h2{font-size:clamp(22px,3vw,32px);letter-spacing:-.02em;margin:0 0 6px}"
    ".lu-proof .lu-sub{color:var(--dim);font-size:15px;margin:0 0 18px;max-width:60ch;line-height:1.55}"
    ".lu-prow{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0;border:1px solid var(--line);"
    "border-radius:14px;background:var(--panel);overflow:hidden}"
    ".lu-prow>div{padding:18px 20px}"
    ".lu-prow>div+div{border-left:1px solid var(--line)}"
    ".lu-prow b{display:block;font-size:15px;margin-bottom:6px}"
    ".lu-prow b .n{color:var(--lime);font-weight:800;margin-right:8px}"
    ".lu-prow p{color:var(--dim);font-size:13.5px;line-height:1.6;margin:0 0 10px}"
    ".lu-prow a{font-size:13.5px}"
    ".lu-privacy{padding:56px 22px 0}"
    ".lu-privacy h2{font-size:clamp(22px,3vw,32px);letter-spacing:-.02em;margin:0 0 6px}"
    ".lu-privacy .lu-sub{color:var(--dim);font-size:15px;margin:0 0 16px;max-width:60ch;line-height:1.55}"
    ".lu-plist{border:1px solid var(--line);border-radius:10px;background:var(--panel);overflow:hidden}"
    ".lu-plist>div{padding:16px 20px}"
    ".lu-plist>div+div{border-top:1px solid var(--line)}"
    ".lu-plist b{display:block;font-size:15px;margin-bottom:4px}"
    ".lu-plist p{color:var(--dim);font-size:13.5px;line-height:1.6;margin:0}"
    ".lu-plist a{color:var(--lime)}"
    ".lu-steps{margin-top:0;padding:56px 22px 0}"
    ".lu-steps-head{width:100%}"
    ".lu-steps-head h2{font-size:clamp(22px,3vw,32px);letter-spacing:-.02em;margin:0 0 6px}"
    ".lu-steps-head .lu-sub{margin:0 0 18px}"
    "#analyse{padding-top:56px;padding-bottom:0}"
    "#faq{padding-top:30px;padding-bottom:64px}"
    "#science{padding-top:30px;padding-bottom:0}"
    ".lu-proof h2,.lu-steps-head h2,.lu-privacy h2{text-align:center}"
    ".lu-proof .lu-sub,.lu-steps-head .lu-sub{margin:0 auto 18px;text-align:center}"
    ".lu-privacy .lu-sub{margin:0 auto 16px;text-align:center}"
    "@media(max-width:820px){.lu-prow{grid-template-columns:1fr}"
    ".lu-prow>div+div{border-left:0;border-top:1px solid var(--line)}"
    ".lu-proof{padding:48px 16px 0}"
    "#analyse{padding-top:48px;padding-bottom:0}"
    ".lu-steps{padding:48px 16px 0}"
    ".lu-privacy{padding:48px 16px 0}"
    "#faq{padding-top:22px;padding-bottom:56px}"
    "#science{padding-top:22px;padding-bottom:0}}"
    "</style>"
)

HERO_H1 = (
    "<h1>Your <span class=lime>running form,</span> exposed &mdash; "
    "every flaw, every fix, in 3D.</h1>"
)

HERO_LEAD = (
    "<p class=lead>One side-profile photo of your stride becomes a 3D "
    "breakdown &mdash; AI form score, zone-by-zone flaws, cues and drills. "
    "Free, about two minutes, no account needed.</p>"
)

HERO_TRUST = (
    "<p class=lu-trust>See a <a href='/report/aeb979a86e8b'>real sample report</a> "
    "&middot; backed by <a href='/#science'>11 peer-reviewed studies</a> "
    "&middot; private by design &mdash; <a href='/#privacy'>delete any run</a>.</p>"
)

STEPS_HEAD = (
    "<div class=lu-steps-head><h2>How it works</h2>"
    "<p class=lu-sub>Three steps, about two minutes, no account needed.</p></div>"
)

PROOF_HTML = (
    "<section class='wrap lu-proof' id=proof>"
    "<h2>Proof, not promises</h2>"
    "<p class=lu-sub>Three things you can check right now, before you upload a photo.</p>"
    "<div class=lu-prow>"
    "<div><b><span class=n>1</span>Watch a real rebuild</b>"
    "<p>The video on this page is a real runner rebuilt in textured 3D and scored 69/100 &mdash; "
    "spin the sample report yourself, zone by zone.</p>"
    "<a href='/report/aeb979a86e8b'>See the full sample report &rarr;</a></div>"
    "<div><b><span class=n>2</span>Every score traces to research</b>"
    "<p>Eleven peer-reviewed gait studies sit at the bottom of this page; each one is linked to "
    "the form zone it backs. No hallucinated advice.</p>"
    "<a href='/#science'>Browse the 11 studies &rarr;</a></div>"
    "<div><b><span class=n>3</span>Honest about limits</b>"
    "<p>What a photo cannot show &mdash; cadence, contact time, forces &mdash; is marked "
    "needs-view and never guessed. The scoring rules say so in public.</p>"
    "<a href='/#faq'>How scoring works &rarr;</a></div>"
    "</div>"
    "</section>"
)

PRIVACY_HTML = (
    "<section class='wrap lu-privacy' id=privacy>"
    "<h2>Private by design</h2>"
    "<p class=lu-sub>Your running photo is personal. Here is exactly what happens to it &mdash; "
    "the same contract shown on the upload screen.</p>"
    "<div class=lu-plist>"
    "<div><b>Your photo works, then rests</b>"
    "<p>It is scored by Gemini and rebuilt in textured 3D in the cloud. Runs stay private to "
    "your session &mdash; there is no public gallery and no feed.</p></div>"
    "<div><b>You hold the keys</b>"
    "<p>No account needed: one guest cookie on your own machine covers 15 free analyses. "
    "After that, a paywall unlock keeps the lights on &mdash; your history never leaks.</p></div>"
    "<div><b>Delete anything, any time</b>"
    "<p>Every run lives in <a href='/history'>your history</a>, where any run can be deleted. "
    "Log in as <a href='/login'>guest</a> while you wait and your spot is kept.</p></div>"
    "</div>"
    "</section>"
)

UPLOAD_META = (
    "<p class=meta>No account needed. Your photo is scored by Gemini and rebuilt in "
    "textured 3D in the cloud &mdash; private to your session, deletable from "
    "<a href='/history'>history</a>.</p>"
)

# Head descriptions — H1 voice ("exposed — every flaw, every fix, in 3D"),
# plain text only (no quotes/entities; the tags use single-quote delimiters).
# Both keep the "running form" head term for SEO.
META_DESC = (
    "See every flaw in your running form \u2014 and exactly how to fix it. "
    "One photo becomes a 3D breakdown with AI score, cues and drills. "
    "Free, about 2 minutes."
)

OG_DESC = (
    "Your running form, exposed \u2014 every flaw, every fix, in 3D. "
    "One photo becomes a scored stride breakdown with cues and drills. "
    "Free, about two minutes."
)
