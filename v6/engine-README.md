# v6 — post-connect update engine (hardened)

Lane: engine build. Source contracts: `v5/worker-contracts.md` (§3 description-only
rule, §4 consent/brand). Reference scaffold (read-only):
`<engine-worktree>/v6/` — this worktree owns only its own `v6/`.

## Files

- `v6/update_engine.py` — pure-stdlib post-connect logic plus runnable
  self-tests. No network, no tokens, no title reads/writes (the activity
  `title` key is never even accessed).
- `v6/manage.html` — static outline mock of the manage page (login status,
  race, update-style options, pause/stop, latest-run preview). Same light-theme
  tokens as the v5 contract. All buttons toggle local proof states only.
- `v6/engine-README.md` — this file.

## Engine contract

Description block for a finished run:

```text
<Race> — N days to go[ — Target <goal>]
<one-line run classification>
```

- `countdown_line()` mirrors the v5 `statusText()` string (`race day is here`
  at ≤0 days); goal is free text, blank omits it. Strict YYYY-MM-DD parsing
  (rejects wrong shapes and impossible dates like Feb 30).
- `classify_run(distance_km)` distance heuristic: Shakeout / Easy miles /
  Steady run / Long run / Big long run; `None`/garbage/boolean/NaN/Inf →
  `Training run`; negative raises.
- Update styles: `append` (keep the runner's notes, countdown block after a
  blank line) or `replace` (countdown block only). Over-long results truncate
  the runner's text first; the countdown block always survives whole
  (`MAX_DESCRIPTION_CHARS = 500`).
- `EngineState`: race + goal + style + `connected`/`paused` booleans (consent
  stub, never a token) + `stamped` id set against double-writes.
- `connect()` requires a selected race (`Pick a race first — then connect`);
  `disconnect()` clears consent + history; `pause()`/`resume()` gate stamping.
- `preview_update(state, activity)` returns `(new_description, reason)`:
  `None` with `skipped: not connected | paused | already stamped`. It never
  mutates the input dict, rejects non-dict activities, and reads only
  `id` / `distance_km` / `description`.

## Self-tests

```sh
python3 v6/update_engine.py --self-test
```

73 checks, stdlib only. They pin the countdown template (plural/singular/
race-day/past, optional goal, numeric goal, non-string name rejected),
strict date parsing (whitespace-padded ok; month 13 / day 00 rejected),
classification boundaries (numeric strings, `False`), append/replace
merging plus truncation survival (`None` existing, empty block rejected),
connect gating (bad style rejected), **no-double-stamp**
(retry with the same id skips, int/str ids dedupe),
**pause skip** (nothing stamped, resume re-stamps),
**disconnect skip** (consent + history + pause cleared, reconnect
re-stamps), missing/`None` payload fields, bad CLI flags (`exit 2`),
input immutability, title-tripwire + AST proof that no code
path touches `title`, and no network imports / no token fields.

## What's stubbed for later lanes

Real OAuth redirect + token vault, webhook/poll trigger on finished runs,
the live activity fetch/update HTTP calls, race-day follow-up copy, and any
persistence of `EngineState`.
