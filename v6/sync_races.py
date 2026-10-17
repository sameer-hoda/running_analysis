"""Build v6/races.snapshot.json from the live mynextbib feed, local fallback.

Live source (read-only scp GET; this script NEVER writes to EC2): configured
via MYNEXTBIB_FEED_KEY / MYNEXTBIB_FEED_HOST / MYNEXTBIB_FEED_PATH in the
environment; unset means local feeds only.

Fallback (local checkout only, used when the live pull fails AND to fill
gaps the live feed leaves, e.g. live rows with no usable distances):
  ~/Projects/mynextbib/v1/scraper_v2/*_events.json

v6 behaviour (kept from the local-only revision):
  - Parses non-ISO feed dates too (e.g. "Feb. 22, 2026"); unparseable or
    missing dates are skipped, never guessed.
  - Maintains v6/aliases.json incrementally: new race names are learned
    daily (attached to a canonical key or appended as new entries) without
    rebuilding the catalogue (see v6/match.py).
  - Each snapshot event carries its canonical "alias" key for stable
    identity across renames ("Delhi Half Marathon" vs
    "Winter Delhi Half Marathon 2026" stay distinct; "KHARGHAR HALF
    MARATHON" vs "Kharghar Half Marathon 2026" merge).
  - Emits "cities" (event-count descending, name tiebreak) and sorted
    "months" facets for picker filters.

Record-shape normalisation (the two sources disagree):
  - Live prd.json is a dict keyed by event URL; local files are lists (or
    {"events": [...]}) of rows. Both are accepted.
  - Live "location" is a {"city","venue","state"} dict; local is a plain
    string. city_of() prefers city, then venue, then state.
  - Live "distances" is a {"5K": bool, "21.1K": bool, ...} map; local is a
    list of labels (or null). distance_labels() takes truthy keys / the
    list as-is; rows with no bucketable distance are dropped, except
    live rows whose only truthy flag is "other" (uncategorised distances
    asserted): those fall back to text_buckets() over descriptive copy
    (name/description/seo text), and are dropped only when the copy
    carries no bucket signal either.

Refresh:  python3 v6/sync_races.py   (re-run nightly; idempotent)

Cron-safe: every run appends timestamped lines to v6/sync_races.log
(stdout is mirrored there); exit 0 on success, nonzero on failure
(no usable feed source, zero indexable events, or an unwritten
snapshot/alias file — a failed run never overwrites the last good
snapshot). Example crontab (daily 03:10 local):
  10 3 * * * /usr/bin/python3 /path/to/worktree/v6/sync_races.py

No secrets: the SSH key is referenced by path only (never read into the
repo, never pasted); only the snapshot and alias catalogue are written
(no tokens, no credentials, no key material).
"""

import glob
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from match import BUCKET_ORDER, bucket_for, learn_alias  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FEED_GLOB = os.path.expanduser(
    '~/Projects/mynextbib/v1/scraper_v2/*_events.json')
SNAPSHOT = os.path.join(HERE, 'races.snapshot.json')
ALIASES = os.path.join(HERE, 'aliases.json')
LOG_FILE = os.path.join(HERE, 'sync_races.log')

# Live feed access (read-only GET via scp; no remote writes, no credentials
# in code — set MYNEXTBIB_FEED_KEY/HOST in the environment of whoever runs
# the live pull; when unset, the script uses local feeds only).
LIVE_KEY = os.path.expanduser(os.environ.get('MYNEXTBIB_FEED_KEY', ''))
LIVE_USER_HOST = os.environ.get('MYNEXTBIB_FEED_HOST', '')
LIVE_REMOTE = os.environ.get('MYNEXTBIB_FEED_PATH', '~/mynextbib_v3/dist/prd.json')
LIVE_TIMEOUT_S = 90

def log(msg):
    """Mirror a status line to stdout and the run log (cron-safe file log)."""
    line = '%s %s' % (datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), msg)
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a') as fh:
            fh.write(line + '\n')
    except OSError as exc:
        print('log: cannot append to %s (%s)' % (LOG_FILE, exc),
              file=sys.stderr, flush=True)


SKIP = ('tape', 'triathlon', 'cycling', 'duathlon')

# Non-ISO feed date seen in the wild: "Feb. 22, 2026".
_EXTRA_DATE_FMTS = ('%b. %d, %Y', '%b %d, %Y', '%B %d, %Y')


def parse_date(raw):
    """Return YYYY-MM-DD or None. Never guesses: unknown formats -> None."""
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        return s
    for fmt in _EXTRA_DATE_FMTS:
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def city_of(event):
    """Normalise the location field (dict in live feed, str locally)."""
    loc = event.get('location')
    if isinstance(loc, dict):
        for field in ('city', 'venue', 'state'):
            val = loc.get(field)
            if isinstance(val, str) and val.strip():
                return val.strip()
        return ''
    if isinstance(loc, str):
        return loc.strip()
    return ''


def distance_labels(event):
    """Normalise the distances field (bool-map live, label list local)."""
    dist = event.get('distances')
    if isinstance(dist, dict):
        return [k for k, v in dist.items() if v]
    if isinstance(dist, (list, tuple)):
        return [d for d in dist if isinstance(d, str) and d]
    return []


def text_buckets(event):
    """Infer buckets from descriptive copy (name/description/seo text).

    Used ONLY when the feed asserts uncategorised distances exist
    (live "other" flag truthy) but no bucketable label survived. Never
    invents distances: returns [] when the copy carries no signal, and
    the row is still dropped.
    """
    out = set()
    for field in ('event_name', 'event_description', 'seo_description'):
        val = event.get(field)
        if isinstance(val, str) and val.strip():
            b = bucket_for(val)
            if b:
                out.add(b)
    return sorted(out, key=BUCKET_ORDER.index)


def fetch_live_feed():
    """scp-get the live prd.json (read-only). Return records or None.

    Returns a list of event dicts on success, or None when the live pull
    is unavailable (no key, ssh/scp failure, bad payload) so the caller
    can fall back to local feeds. Never raises; never writes remotely.
    """
    if not os.path.exists(LIVE_KEY):
        log('live feed: key not found, using local feeds only')
        return None
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(prefix='prd_live_', suffix='.json')
        os.close(fd)
        proc = subprocess.run(
            ['scp', '-i', LIVE_KEY, '-o', 'BatchMode=yes',
             '-o', 'ConnectTimeout=15',
             '%s:%s' % (LIVE_USER_HOST, LIVE_REMOTE), tmp],
            capture_output=True, text=True, timeout=LIVE_TIMEOUT_S)
        if proc.returncode != 0:
            log('live feed: scp failed (%s), using local feeds only'
                % (proc.stderr.strip().splitlines()[:1] or ['']))
            return None
        with open(tmp) as fh:
            payload = json.load(fh)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        log('live feed: pull failed (%s), using local feeds only' % exc)
        return None
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
    if isinstance(payload, dict):
        return list(payload.values())
    if isinstance(payload, list):
        return payload
    log('live feed: unexpected payload shape, using local feeds only')
    return None


def load_local_feed():
    """Read local scraper feeds. Returns (records, files_read)."""
    records = []
    files_read = 0
    for path in sorted(glob.glob(FEED_GLOB)):
        try:
            with open(path) as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue
        files_read += 1
        items = data if isinstance(data, list) else data.get('events', [])
        records.extend(e for e in items if isinstance(e, dict))
    return records, files_read


def load_aliases():
    try:
        with open(ALIASES) as fh:
            data = json.load(fh)
        if isinstance(data, dict) and 'canonical' in data:
            return data
    except (OSError, ValueError):
        pass
    return {'updated': None, 'canonical': {}}


def ingest(records, today, catalogue, seen):
    """Filter/normalise records into seen[(name, date)]. Returns counts."""
    kept = 0
    skipped_no_date = 0
    for e in records:
        if not isinstance(e, dict):
            continue
        day = parse_date(e.get('event_date'))
        if day is None:
            skipped_no_date += 1
            continue
        if day < today:
            continue
        name = (e.get('event_name') or '').strip()
        if not name or any(s in name.lower() for s in SKIP):
            continue
        buckets = sorted(
            {b for d in distance_labels(e)
             for b in [bucket_for(d)] if b},
            key=BUCKET_ORDER.index)
        if not buckets:
            # Live rows whose only truthy flag is "other" assert
            # uncategorised distances (e.g. Tata Mumbai Marathon
            # 2027-01-17: every known key false, "other" true). Rescue
            # via descriptive copy; rows with no "other" flag and rows
            # whose copy carries no signal are still dropped.
            dist = e.get('distances')
            if isinstance(dist, dict) and dist.get('other'):
                buckets = text_buckets(e)
        if not buckets:
            continue
        key = (name, day)
        if key in seen:
            continue
        alias = learn_alias(catalogue, name, today)
        seen[key] = {
            'name': name,
            'alias': alias,
            'date': day,
            'city': city_of(e),
            'url': e.get('event_url') or '',
            'buckets': buckets,
        }
        kept += 1
    return kept, skipped_no_date


def main():
    """Run one sync. Returns process exit code (0 ok, 1 failure)."""
    log('sync start')
    try:
        today = date.today().isoformat()
        catalogue = load_aliases()
        before = len(catalogue.get('canonical', {}))
        seen = {}

        live = fetch_live_feed()
        live_kept = live_nodate = 0
        if live is not None:
            live_kept, live_nodate = ingest(live, today, catalogue, seen)
            log('live feed: %d rows -> %d events' % (len(live), live_kept))

        local, files_read = load_local_feed()
        local_kept, local_nodate = ingest(local, today, catalogue, seen)
        log('local feed: %d files, %d rows -> %d new events (fallback/fill)'
            % (files_read, len(local), local_kept))

        if live is None and files_read == 0:
            log('sync FAILED: no usable feed source (live pull failed, '
                'no local feed files); snapshot left untouched')
            return 1

        events = sorted(seen.values(), key=lambda e: e['date'])
        if not events:
            log('sync FAILED: 0 indexable events; snapshot left untouched')
            return 1

        catalogue['updated'] = today
        with open(ALIASES, 'w') as fh:
            json.dump(catalogue, fh, indent=1, sort_keys=True)
            fh.write('\n')
        counts = {}
        for e in events:
            if e['city']:
                counts[e['city']] = counts.get(e['city'], 0) + 1
        cities = sorted(counts, key=lambda c: (-counts[c], c))
        months = sorted({e['date'][:7] for e in events})
        with open(SNAPSHOT, 'w') as fh:
            json.dump({'generated': today, 'count': len(events),
                       'cities': cities, 'months': months,
                       'events': events}, fh, indent=1)
            fh.write('\n')
        learned = len(catalogue.get('canonical', {})) - before
        log('%d events -> %s' % (len(events), SNAPSHOT))
        log('%d canonical names (%d new), %d+%d rows skipped '
            '(no usable date)'
            % (len(catalogue.get('canonical', {})), learned,
               live_nodate, local_nodate))
    except Exception as exc:  # cron must see a nonzero exit, never silence
        log('sync FAILED: %s: %s' % (type(exc).__name__, exc))
        return 1
    log('sync ok')
    return 0


if __name__ == '__main__':
    sys.exit(main())
