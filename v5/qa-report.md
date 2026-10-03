# v5 QA Report — topfold + picker lanes

Scope: `v5/topfold.html`, `v5/picker.html`, `v5/worker-contracts.md` (read-only review; no lane files edited).
Date: 2026-10-03. Verdict: **PASS on all 5 checks**, with 3 minor non-blocking fixes recommended.

## 1. Picker filters fast — PASS

- `picker.html` embeds a curated 8-race `EVENTS` array; filtering is synchronous, in-memory, no network, no build step.
- `matchRank()`: direct substring = rank 0, subsequence fuzzy = rank 1, else no match; `filtered()` sorts direct hits first, then by date. `renderList()` re-renders on each `input` event plus month-chip clicks.
- Month chips (All/Oct/Nov/Dec) apply even with an empty query and the empty state names the rescue path ("Clear the search or pick a month chip").
- 8 items = trivially fast; no debounce needed. No defect found.

## 2. Countdown math sane — PASS

- Topfold (`topfold.html` lines 207–217): `target = now + ((84*24+6)*3600 + 12*60 + 33)*1000`, tick does `s = max(0, floor((target-now)/1000))`, `d/h/m/sec` decomposition with zero-pad. Initial static text `84d 06:12:33` matches the seed offset. `setInterval(tick, 1000)` + 4 s before/after loop toggle. `Math.max(0, …)` clamps post-race to zero — sane.
- Picker (`picker.html` lines 138–147): `daysTo()` = `round((raceMidnight − todayMidnight)/86400000)`; `whenText()` covers `>1` ("N days to go"), `1` (tomorrow), `0` (today), `<0` (passed). Goal-time field is free text, blank skips the goal line — no fake arithmetic on the goal.
- Minor note (non-blocking): under `prefers-reduced-motion` the countdown renders once and stays static (interval skipped). Acceptable as a motion fallback; if a live-but-non-animated countdown is preferred, keep the 1 s `tick` interval and only disable the 4 s fade loop.

## 3. Description-only, never title — PASS

- Topfold: `.card-title` ("Morning Run", line 183) is static markup; JS only toggles `#line-before` / `#line-after` inside `.card-desc` and updates `#countdown` text. No code path touches the title node.
- Picker: preview is labeled "Strava description preview" with an `N / 500` char count; fine print states "The bot writes to the activity `description`; your titles stay yours." `descText()` builds only the description string. Mock Connect button only toggles a proof panel, gated on a selected race.
- Consistent with `worker-contracts.md` §3 (subtitle/description-only rule). No violation.

## 4. No secrets — PASS

- Searched all three files for `api_key / client_secret / client_id / token / bearer / sk-… / password / -----BEGIN` — zero hits.
- No network calls, no external scripts, no analytics, no OAuth URLs, no embedded credentials. Picker fine print confirms "no data leaves this page." `title` string matches are only the HTML `<title>` tags, the static card title, and the "your titles stay yours" copy — no title-write API.

## 5. Light minimal theme — PASS (with token-drift note)

- Both pages are light: white page background, dark ink text, gray muted/line, single Strava-orange `#FC5200` accent. Topfold uses the accent in exactly one rule (`.card-desc .accent`); tabular-nums applied to countdown/stats/pill/hint. Zero dependencies, inline CSS/JS.
- Minor drift vs `worker-contracts.md` §2 tokens (non-blocking, visual difference negligible):
  - topfold `--ink #111214` vs contract `#191412`; `--muted #6b6f76` vs `#6f645c`; `--line #e8e8e6` vs `#e7e0d8`.
  - picker `--muted #6b625c` vs `#6f645c`; `--line #e8e2dc` vs `#e7e0d8`.
  - Fix: align both files to the contract tokens (`#191412 / #6f645c / #e7e0d8 / #ffffff / #fc5200`) in a follow-up lane. Not a QA failure.

## Fixes needed

1. (Optional) Align theme tokens to `worker-contracts.md` §2 exact values — cosmetic only.
2. (Optional) Reduced-motion: keep the 1 s countdown `tick` live and gate only the 4 s fade loop, if a live static-text countdown is desired.
3. (Optional) Picker search `input` handler calls `renderList()` only; panel re-render isn't needed until selection changes — current behavior correct, no change required. Listed only to record it was checked.

No blocking defects. No files other than this report were created or modified by QA.
