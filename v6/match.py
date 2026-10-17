"""Fuzzy/substring race-name matching + incremental alias catalogue.

Shared by v6/sync_races.py (Python). The v6 picker scaffold (picker.html)
mirrors match_rank() in JS; keep the two in sync (both documented here).

Alias catalogue (v6/aliases.json) shape:
  {"updated": "YYYY-MM-DD",
   "canonical": {<key>: {"name": <display>, "aliases": [...], "last_seen": ...}}}

Incremental learning rule: a sync run NEVER rebuilds this file from
scratch. It loads existing entries, attaches newly seen names to the
best-matching canonical key (exact/substring/token-overlap), and appends
only genuinely new names as fresh canonical entries. Existing keys,
display names and alias history are preserved across runs.
"""

import re

DIST_RE = re.compile(r'(\d+(?:\.\d+)?)\s*[kK][mM]?')
BUCKET_ORDER = ['5K', '10K', 'Half', 'Full', 'Ultra']


def bucket_for(label):
    """Map a free-text distance label to 5K/10K/Half/Full/Ultra/None.

    Same contract as v5/sync_events.py bucket(): 'half' variants -> Half,
    bare 'marathon' -> Full, numeric km thresholds otherwise.
    """
    if not label or not isinstance(label, str):
        return None
    low = label.lower().replace('\xa0', ' ').strip()
    if low in ('hm', 'half marathon') or 'half' in low:
        return 'Half'
    if low in ('m', 'fm', 'marathon') or re.search(r'\bmarathon\b', low):
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


# Tokens stripped when deriving a canonical key: years, edition markers,
# ordinals (17th), and generic filler. Display names are never modified.
_STRIP_RE = re.compile(
    r'\b(19|20)\d{2}\b|\bedition\b|\b\d+(st|nd|rd|th)\b|\brun\b$', re.I)
_WS_RE = re.compile(r'[^a-z0-9]+')


def normalize(name):
    """Lowercase, strip edition/year filler, collapse to space-separated key."""
    if not name or not isinstance(name, str):
        return ''
    low = name.lower().replace('\u00a0', ' ')
    low = _STRIP_RE.sub(' ', low)
    return _WS_RE.sub(' ', low).strip()


def tokens(key):
    return set(key.split()) if key else set()


def match_rank(hay, query):
    """0 = substring hit, 1 = subsequence (fuzzy) hit, -1 = no match.

    Mirrors the v5 picker readable-first ranking.
    """
    q = (query or '').strip().lower()
    if not q:
        return 0
    h = (hay or '').lower()
    if q in h:
        return 0
    hi = 0
    for ch in q:
        hi = h.find(ch, hi)
        if hi == -1:
            return -1
        hi += 1
    return 1


def alias_match(norm, catalogue):
    """Return the canonical key in catalogue matching norm, or None.

    Deliberately strict: exact normalized key or identical token set
    (order-insensitive). Distinct races often share words ("Delhi Half
    Marathon" vs "Winter Delhi Half Marathon 2026" are different events
    on different dates), so substring/overlap merging would fuse races
    that must stay distinct. Fuzzy/substring matching lives in the
    picker search (match_rank), not in catalogue identity.
    """
    if not norm:
        return None
    entries = catalogue.get('canonical', {})
    if norm in entries:
        return norm
    ntok = tokens(norm)
    if not ntok:
        return None
    for key in entries:
        if tokens(key) == ntok:
            return key
    return None


def learn_alias(catalogue, raw_name, today):
    """Attach raw_name to its canonical entry, creating one if new.

    Mutates catalogue in place; returns the canonical key. Existing
    entries are only appended to, never rebuilt or deleted.
    """
    norm = normalize(raw_name)
    if not norm:
        return ''
    entries = catalogue.setdefault('canonical', {})
    key = alias_match(norm, catalogue)
    if key is None:
        entries[norm] = {'name': raw_name.strip(), 'aliases': [],
                         'last_seen': today}
        return norm
    entry = entries[key]
    entry['last_seen'] = today
    if raw_name.strip() != entry['name'] and \
            raw_name.strip() not in entry.get('aliases', []):
        entry.setdefault('aliases', []).append(raw_name.strip())
    return key
