"""Build v5/events.snapshot.json from mynextbib scraper feeds.

Source of truth (live refresh lives on EC2; this reads the local checkout):
  ~/Projects/mynextbib/v1/scraper_v2/*_events.json

Keeps entries with an ISO event_date >= today, normalises distance labels
into buckets (5K / 10K / Half / Full / Ultra) and writes a lean snapshot
the mock frontend embeds. Re-run nightly (or from EC2) to refresh.
"""
import json
import glob
import os
import re
from datetime import date

FEED_GLOB = os.path.expanduser(
    '~/Projects/mynextbib/v1/scraper_v2/*_events.json')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'events.snapshot.json')

DIST_RE = re.compile(r'(\d+(?:\.\d+)?)\s*[kK][mM]?')


def bucket(label):
    """Map a free-text distance label to 5K/10K/Half/Full/Ultra/None."""
    if not label or not isinstance(label, str):
        return None
    low = label.lower().replace('\xa0', ' ').strip()
    if low in ('hm', 'half marathon') or 'half' in low:
        return 'Half'
    if low in ('m', 'fm', 'marathon') or re.search(r'\bmarathon\b', low):
        # 'Marathon' word alone means full unless 'half' matched above
        return 'Full'
    m = DIST_RE.search(low)
    if not m:
        return None
    km = float(m.group(1))
    if km >= 60:
        return 'Ultra'
    if km >= 40:
        return 'Full'
    if km >= 18:
        return 'Half'
    if km >= 8:
        return '10K'
    return '5K'


SKIP = ('tape', 'triathlon', 'cycling', 'duathlon')

def main():
    today = date.today().isoformat()
    seen = {}
    for path in glob.glob(FEED_GLOB):
        try:
            data = json.load(open(path))
        except Exception:
            continue
        items = data if isinstance(data, list) else data.get('events', [])
        for e in items:
            if not isinstance(e, dict):
                continue
            day = (e.get('event_date') or '').strip()
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day) or day < today:
                continue
            key = ((e.get('event_name') or '').strip(), day)
            if key in seen:
                continue
            if any(s in key[0].lower() for s in SKIP):
                continue
            buckets = sorted(
                {b for d in (e.get('distances') or [])
                 for b in [bucket(d)] if b},
                key=['5K', '10K', 'Half', 'Full', 'Ultra'].index)
            if not buckets:
                continue
            seen[key] = {
                'name': key[0],
                'date': day,
                'city': (e.get('location') or '').strip(),
                'url': e.get('event_url') or '',
                'buckets': buckets,
            }
    events = sorted(seen.values(), key=lambda e: e['date'])
    json.dump({'generated': today, 'count': len(events),
               'events': events}, open(OUT, 'w'), indent=1)
    print(f'{len(events)} events -> {OUT}')


if __name__ == '__main__':
    main()
