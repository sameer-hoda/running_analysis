# mynextpr v6 audit report — 2026-10-10

Method: web-quality-audit smoke on all pages, agent-browser live pass
(desktop Chromium, served over localhost), impeccable detect over the six
page targets, plus source checks. Screenshots: /tmp/audit-{index-desktop,
index-mobile, picker, picker-filtered, goal, connect, manage, hero}.png.

## Verdict: PASS WITH NOTES — 1 Medium, 3 Low, 0 Critical, 0 High

## Findings

- Medium · picker preview desync. After filtering (Bengaluru + Half), the
  preview panel keeps showing the previously selected race (Pune) because
  renderPanel resolves state.sel against full EVENTS, not the filtered
  list. Reproduced live. Fix dispatched to 03-catalog (auto-select first
  filtered race or clear selection on filter change).
- Low · orange body text contrast. #fc5200 on light washes measures ~3.1:1
  (body needs 4.5:1); white-on-#d94800 hover measures ~4.3:1. Fine for
  large display type, tighten for body copy.
- Low · mobile viewport unverified in a rendered browser. Responsive rules
  exist in code; the audit CLI has no viewport emulation, so a real-device
  check is still open.
- Low · touch-target sizes unmeasured. Pills look thumb-sized but no
  44px assertion was run.

## Verified clean

- Smoke: 0 issues, 0 warnings on all 7 targets.
- Live: zero page errors, zero console errors on every page; picker pills,
  search, month filters, goal h/m/s inputs with 2:00:00 Half default,
  connect race gate, and manage states all exercised in-browser.
- A11y tree: single h1 per page intent, named regions, labelled searchbox,
  native buttons for actions, aria-selected + aria-live on dynamic zones,
  lang="en" everywhere, unique titles everywhere.
- Goal placeholder "1:45:00" is placeholder text, not a prefilled value.
- No secrets, no tokens, no external calls in any page (only local
  snapshot fetch and links).
- Brand: Compatible with Strava plain text, orange CTA, mock labels,
  consent adjacent to action, no endorsement claims.

## Deferred (needs owner)

- Strava app is Inactive (Application/Status/Inactive): backend blocked
  until reactivated in Strava settings.
- Mobile-device and touch-target assertions pending real-device pass.
