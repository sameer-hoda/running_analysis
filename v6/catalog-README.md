# v6 — race-data refresh (live EC2 pull + local fallback) + picker scaffold

## Files

| File | Role |
|------|------|
| `v6/sync_races.py` | Refresh: scp-gets live prd.json (read-only), falls back to local mynextbib scraper feeds, writes `races.snapshot.json`, learns `aliases.json` |
| `v6/match.py` | Shared matcher: distance buckets, substring/fuzzy rank, alias catalogue learning |
| `v6/races.snapshot.json` | Generated: upcoming events + `cities`/`months` facets |
| `v6/aliases.json` | Generated, incremental: canonical race-name catalogue |
| `v6/picker.html` | Scaffold: search + distance/city/month filters over the snapshot |
| `v6/catalog-README.md` | This file |

## Refresh

```sh
python3 v6/sync_races.py   # idempotent; re-run nightly (cron-safe)
```

Cron-safe: every run appends timestamped lines to `v6/sync_races.log`
(stdout is mirrored there). Exit 0 on success; exit 1 when there is no
usable feed source, zero indexable events, or an unwritten output — a
failed run never overwrites the last good snapshot. Example crontab
(daily 03:10 local):

```sh
10 3 * * * /usr/bin/python3 /path/to/worktree/v6/sync_races.py
```

Live pull first (read-only `scp` GET of
`ec2-user@HOST_REMOVED:~/mynextbib_v3/dist/prd.json` via `~/.ssh/SSH_KEY_REMOVED`;
nothing is ever written to EC2), then local feeds
(`~/Projects/mynextbib/v1/scraper_v2/*_events.json`) fill gaps: rows the
live feed lacks or leaves bucket-less, plus full fallback when the live
pull fails. Live rows win on (name, date) ties. Keeps events with a
usable date ≥ today, drops non-running entries (tape/triathlon/cycling/
duathlon) and bucket-less rows, dedupes on (name, date). Parses ISO dates
plus the `"Feb. 22, 2026"` feed format; unparseable/missing dates are
skipped, never guessed. Live `location` dicts (city/venue/state) and
`distances` bool-maps are normalised to the local string/list shapes.

## Alias catalogue (incremental learning, no full rebuild)

`aliases.json` maps a normalized canonical key → `{name, aliases[], last_seen}`.
Each run loads the existing file, attaches seen names (exact key or identical
token set — deliberately strict so distinct races sharing words, e.g. Delhi
Half vs Winter Delhi Half, never fuse), and appends only genuinely new names.
Existing keys, display names, and alias history are preserved across runs;
a second run without feed changes learns 0 new names (verified).

Fuzzy/substring matching is the *picker search* behaviour (`match_rank`, rank
0 substring / rank 1 subsequence, mirrored in `picker.html` JS) — it does not
drive catalogue identity.

## Picker

Open over HTTP (fetch needs it, e.g. `python3 -m http.server` in the worktree
root, then `/v6/picker.html`): text search, multi-toggle distance pills
(5K/10K/Half/Full/Ultra, ANY-match union), city selector pills (built from
the snapshot `cities` facet, multi-toggle union; empty = all cities),
dynamic month pills, and a filtered event list showing the matching events
for the selection with a `Clear filters` reset. All filters compose and
re-render list + panel. Description-only preview with char count
(`n / 500 chars`), mock Connect gated on selection, MyNextBib signup link
(relative feed paths prefixed with `https://mynextbib.com`). The bot writes
to the activity `description`; titles stay untouched. Copy states
`Compatible with Strava` only (mock tag + fine print; no endorsement
claim). Tokens follow the canonical set (`--muted #6f645c`,
`--line #e7e0d8`, `--accent #fc5200`). The page's only network call is
`fetch("races.snapshot.json")`.

## No secrets

No credentials, tokens, keys, or key material in any v6 file. The live pull
references the SSH key by path only; the key itself is never read into the
repo. Verification: snapshot and alias files contain only public race feed
fields (name/date/city/url/buckets).
