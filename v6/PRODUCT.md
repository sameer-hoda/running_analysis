# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Amateur runners training for a picked race. They log their training runs on
Strava, mostly from a phone, and want an automatic race-day countdown carried
in each run's Strava activity description. No other audience is confirmed.

## Product Purpose

mynextpr is a simple Strava countdown app: pick a race, optionally set a goal,
and every run logged afterward gets its countdown added to the run's Strava
description — automatically. Success means the runner connects once, forgets
about it, and sees a correct, up-to-date countdown on every subsequent run.

## Positioning

The countdown writes itself into the activity **description** and nothing
else: never the activity title (the user's own title is sacred), only the
authenticated athlete's own activities, only after explicit connect consent,
with the minimum OAuth scopes (`read` + `activity:write`). A neighboring
training app that rewrites titles, claims endorsement, or requests broader
scopes could not truthfully copy this restraint.

## Operating Context

Three-tap flow: pick a distance, pick a month, pick a race — then connect
Strava and forget about it. The runner's real scene is training weeks: log a
run on Strava, the countdown appears in that run's description. A manage
surface lets the runner review and adjust description styles. Mobile-first;
the phone is the primary device.

## Capabilities and Constraints

Confirmed functionality:

- Race picker (distance → month → race) with upcoming-race gating: Connect
  stays disabled until an upcoming race is picked; a race whose date has
  passed keeps Connect disabled, race-day itself stays connectable.
- Optional goal (target finish) carried alongside the countdown.
- Automatic description updates on subsequently logged runs.
- Manage surface for description styles.
- Mock-first flow: the v6 `Connect with Strava` button is a mock that only
  flips preview text; production uses the official Strava OAuth flow with
  server-side token exchange (see `v6/strava-plan.md`).

Binding constraints:

- Description-only writes; never activity titles.
- OAuth scopes `read` + `activity:write` only; own activities only; explicit
  consent before any write.
- Brand label is `Compatible with Strava` (adjacent `MOCK · Compatible with
  Strava` in mocks) only. Never claim endorsement, partnership, or "powered
  by Strava". No Strava logo. Official Strava brand rules bind every lane.
- Fine print stating the scopes in plain words sits adjacent to the CTA.
- CTA gated on race selection.
- No secrets, credentials, or network calls in the repo; no external scripts.

Undecided: nothing material is open; the brief is confirmed as stated.

## Brand Commitments

Name: `mynextpr` (lowercase wordmark, `span` in Strava-orange accent per
tokens). Voice: plain, sharp, minimal — the product's own language from
`v6/hero-copy.md` (primary headline "Track your goal and go for your next
PR"). Visual commitments pinned by the brief: minimal, sharp, mobile-first;
Strava orange accent; light-only world (no dark mode, no glass/gradients, no
gamification — owner vetoes). Token freeze approved: all canonical values in
`v6/tokens.css` / `v6/design-tokens.md` are locked; lanes consume via `var()`.

## Evidence on Hand

- `v6/strava-plan.md` — OAuth SSO, scopes, consent and compliance plan.
- `v6/hero-copy.md` — homepage headline lockup, description templates, CTA
  and consent microcopy (locked primary headline + alternates).
- `v6/races.snapshot.json` — race data snapshot.
- `v6/assets/` — hero poster, hero video, before-screenshots.
- Absences future work must not fabricate: no testimonials, customers,
  benchmarks, pricing, or licensing claims exist.

## Product Principles

1. The runner's title is sacred — we add context, never overwrite identity.
2. One connect, then invisible — automation earns trust by staying out of
   the way.
3. Minimal scopes, minimal surface — ask only what the job needs.
4. Countdown correctness first — a wrong number is worse than no number.
5. Compatible, never endorsed — honesty about the Strava relationship.

## Accessibility & Inclusion

Countdown content must never depend on animation: the countdown line is
always present as static text first. Under `prefers-reduced-motion`, CSS
motion collapses but the 1s countdown text tick stays live (it is a text
update, not motion); only the before/after fade loop is gated. Visible
`:focus-visible` rings on all interactive elements, including inside the
dark preview panel. No product-specific accessibility standard beyond this
was established.
