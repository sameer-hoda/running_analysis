# v6 — daily race-data refresh runbook

Refreshes `v6/races.snapshot.json` (picker feed) and incrementally learns
`v6/aliases.json` (canonical race-name catalogue). Idempotent: re-run
nightly with `python3 v6/sync_races.py`.

## 1. Live EC2 pull (read-only, always first)

The script `scp`-GETs one file and never writes to EC2:

```sh
scp -i "$MYNEXTBIB_FEED_KEY" -o BatchMode=yes -o ConnectTimeout=15 \
  "$MYNEXTBIB_FEED_HOST:$MYNEXTBIB_FEED_PATH" <tmpfile>
```

- Key is referenced by path only; its contents are never read into the
  repo. No passwords, tokens, or key material in any v6 file.
- `BatchMode=yes` means no interactive password prompt: a missing key or
  unreachable host fails fast to local fallback instead of hanging.
- Pull timeout 90 s. Any failure (no key, ssh/scp error, bad JSON,
  unexpected shape) prints to stderr and falls through — never raises.

## 2. Local fallback (gap-fill + full fallback)

Source: `~/Projects/mynextbib/v1/scraper_v2/*_events.json` (lists or
`{"events": [...]}`; unreadable files skipped).

- Live rows are ingested first and win `(name, date)` ties, so local rows
  only add what the live feed lacks or leaves bucket-less.
- When the live pull fails entirely, local feeds become the whole dataset.
- Last verified run (2026-10-10): live 223 rows → 98 events; local
  12 files / 451 rows → 6 new events; snapshot 104 events.

## 3. Filtering and normalisation

- Keeps events dated ≥ today; drops non-running names (tape / triathlon /
  cycling / duathlon), bucket-less rows, and `(name, date)` dupes; sorts
  by date; emits `{generated, count, cities, months, events[]}`.
- Dates: ISO plus `"Feb. 22, 2026"`-style feeds; unparseable/missing dates
  are skipped, never guessed.
- Record shapes: live `prd.json` is a URL-keyed dict, local files are
  lists; live `location` dicts (city → venue → state) become city strings;
  live `distances` bool-maps become label lists. Each snapshot event
  carries its canonical `alias` key for stable identity across renames.

## 4. Alias learning (incremental, never rebuilt)

`aliases.json` maps normalized key → `{name, aliases[], last_seen}`. Each
run loads the file, attaches seen names on exact key or identical token
set only (deliberately strict: "Delhi Half Marathon" vs "Winter Delhi
Half Marathon 2026" stay distinct; pure token reorders merge), and appends
only genuinely new names. Display names and alias history are preserved;
a no-change re-run learns 0 new names (verified: 102 keys before/after).

## 5. Verify it is still green

```sh
python3 v6/sync_races.py            # expect exit 0
python3 -c "import json;d=json.load(open('v6/races.snapshot.json'));print(d['generated'],d['count'],len(d['events']))"
grep -c 'value="1:45:00"' v6/picker.html   # expect 0 (goal blank by default)
```

Green means: exit 0, `count` equals the events array length, `generated`
is today, re-run learns 0 new names, and no `value=` prefill in the
picker goal field.

## 6. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `live feed: key not found` | `MYNEXTBIB_FEED_KEY` unset; local-only run, still valid |
| `live feed: scp failed` | Network/host down; local fallback covers it |
| `0 events` | Feeds moved or all dates past; check `FEED_GLOB` path and system date |
| Picker shows stale data | Re-run sync, then hard-refresh; picker reads the snapshot over HTTP |

## 7. No-secrets check (before every commit)

```sh
grep -rniE 'BEGIN.*PRIVATE|client_secret|password|api[_-]?key' v6/ | grep -v 'no-secrets\|never read\|by path only' ; echo "clean:$?"
```

Only public race-feed fields (name/date/city/url/buckets) belong in the
snapshot and alias files. The EC2 host + key path are infra references,
not key material.
