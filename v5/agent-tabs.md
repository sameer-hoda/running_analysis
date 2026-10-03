# mynextpr redesign — agent tabs (ready to open)

Slug: `mynextpr-redesign` | Repo: `/Users/sameerhoda/Projects/running_analysis` (v5 only)
Done-means: landing top-fold animation + picker flow + QA sign-off verified in `v5/`, no secrets committed.

## Tab 1 — `topfold`
Owns only the landing top-fold before/after Strava description animation.
In: `v5/mock.html` top fold. Out: kickass loop + reduced-motion fallback.

## Tab 2 — `picker`
Owns scroll transition + fuzzy event select + target + Connect proof state.
In: `v5/events.snapshot.json`, `v5/sync_events.py`. Out: ≤3-keystroke filtering, preview with char count.

## Tab 3 — `qa`
Owns acceptance: countdown math, brand/consent checks, no key leaks.
