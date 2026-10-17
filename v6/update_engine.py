"""v6 update engine (lane: core-engine) — hardened.

Post-connect flow: after the user connects Strava, each finished run updates
the Strava activity **description** only — never the title. The description
carries the countdown (days-to-go), the optional goal, and a one-line run
classification.

Rules inherited from v5/worker-contracts.md:
- Description only. No code path here reads or writes an activity title.
  `preview_update()` never accesses the activity's `title` key — this is
  enforced by construction (only `id` / `distance_km` / `description` are
  read) and pinned by a self-test that trips on any `title` access.
- OAuth scopes are `read` + `activity:read` + `activity:write` (minimal:
  read identity, read activities to find the new run, write description
  only); only the authenticated user's own activities; only after explicit
  connect consent.
- No real Strava tokens, no network calls. `connect()` is a local stub that
  records consent as a boolean; `disconnect()` drops it. This module imports
  nothing beyond stdlib value types (`dataclasses`, `datetime`, `math`,
  `re`, `ast`/`inspect`/`sys` for the self-tests only).
- Brand label is `MOCK · Compatible with Strava` (mock only). No logo,
  no endorsement claims.

Pure stdlib logic — importable and unit-testable with no I/O.

Runnable self-tests (no network, no tokens, no secrets):

    python3 v6/update_engine.py
    python3 v6/update_engine.py --self-test
"""

from __future__ import annotations

import ast
import inspect
import math
import re
import sys
from dataclasses import dataclass, field, fields
from datetime import date

SCOPES = ("read", "activity:read", "activity:write")
BRAND_TAG = "MOCK · Compatible with Strava"
MAX_DESCRIPTION_CHARS = 500

APPEND = "append"  # keep the runner's own text, add the countdown block after it
REPLACE = "replace"  # description becomes the countdown block only
UPDATE_STYLES = (APPEND, REPLACE)

SEPARATOR = "\n\n"

# Keys this engine is ever allowed to read from an activity dict.
# `title` is deliberately absent: description-only by construction.
_ACTIVITY_KEYS = ("id", "distance_km", "description")

_ISO_DAY_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")

# Import roots that would imply network I/O. Pinned absent by self-test.
_NETWORK_IMPORT_ROOTS = ("urllib", "requests", "httpx", "socket", "http")


def parse_iso_day(value: str) -> date:
    """Parse a strict YYYY-MM-DD string; raises on bad input.

    Raises:
        TypeError: if `value` is not a string.
        ValueError: if the text is not a real calendar day in YYYY-MM-DD
            form (wrong shape, non-numeric parts, or impossible date such
            as month 13 or Feb 30).
    """
    if not isinstance(value, str):
        raise TypeError("date must be a YYYY-MM-DD string")
    text = value.strip()
    match = _ISO_DAY_RE.fullmatch(text)
    if not match:
        raise ValueError(f"bad date {value!r}: expected YYYY-MM-DD")
    year, month, day = (int(part) for part in match.groups())
    return date(year, month, day)  # raises ValueError for impossible dates


def days_to_go(race_date_iso: str, today_iso: str | None = None) -> int:
    """Whole days from today until race day (<=0 means race day / past)."""
    today = parse_iso_day(today_iso) if today_iso is not None else date.today()
    return (parse_iso_day(race_date_iso) - today).days


# Nominal race distances (km) for goal-time → target-pace conversion.
RACE_DIST_KM = {
    "5k": 5.0,
    "10k": 10.0,
    "half": 21.0975,
    "full": 42.195,
}


def goal_to_pace(goal: str, race_dist_km: float | None) -> str:
    """Convert a goal time (`H:MM` or `H:MM:SS`) into a `M:SS/km` pace.

    Returns "" when the goal is not a parseable time or the race distance
    is unknown, so callers can fall back to echoing the raw goal text.
    """
    if race_dist_km is None or isinstance(race_dist_km, bool):
        return ""
    try:
        dist = float(race_dist_km)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(dist) or dist <= 0:
        return ""
    text = goal.strip() if isinstance(goal, str) else str(goal).strip()
    parts = text.split(":")
    if len(parts) not in (2, 3) or not all(
            part.strip().isdigit() for part in parts):
        return ""
    nums = [int(part.strip()) for part in parts]
    if len(nums) == 2:
        hours, minutes, seconds = nums[0], nums[1], 0
    else:
        hours, minutes, seconds = nums
    if minutes >= 60 or seconds >= 60:
        return ""
    total_minutes = hours * 60 + minutes + seconds / 60
    if total_minutes <= 0:
        return ""
    pace_min = total_minutes / dist
    whole = int(pace_min)
    secs = int((pace_min - whole) * 60 + 0.5)
    if secs == 60:
        whole += 1
        secs = 0
    return f"{whole}:{secs:02d}"


def fmt_km(value: float | None) -> str:
    """Format a kilometre total; unknown totals render as an em dash."""
    if value is None or isinstance(value, bool):
        return "–"
    try:
        km = float(value)
    except (TypeError, ValueError):
        return "–"
    if not math.isfinite(km) or km < 0:
        return "–"
    if km == int(km):
        return f"{int(km)}"
    return f"{km:.1f}"


# Promo footer on every stamped activity.
PROMO_LINE = "Set up tracking for your goal race at mynextpr.com"


def totals_line(month_km: float | None = None,
                year_km: float | None = None,
                today_iso: str | None = None) -> str:
    """`Month so far: N km · YYYY so far: M km`, the second description line."""
    today = parse_iso_day(today_iso) if today_iso is not None else date.today()
    month = today.strftime("%B")
    return (f"{month} so far: {fmt_km(month_km)} km · "
            f"{today.year} so far: {fmt_km(year_km)} km.")


def countdown_line(race_name: str, race_date_iso: str,
                   goal: str = "",
                   race_dist_km: float | None = None,
                   today_iso: str | None = None) -> str:
    """`<N> days to go — <Race>, target <H:MM> at <M:SS>/km.`

    An unparseable goal (or unknown distance) falls back to echoing the
    raw goal text as `, target <goal>.` so nothing the runner typed is lost.
    """
    if not isinstance(race_name, str):
        raise TypeError("race_name must be a string")
    name = race_name.strip()
    if not name:
        raise ValueError("race_name is required")
    days = days_to_go(race_date_iso, today_iso)
    if days <= 0:
        head = f"Race day today — {name}"
    elif days == 1:
        head = f"1 day to go — {name}"
    else:
        head = f"{days} days to go — {name}"
    goal_text = goal.strip() if isinstance(goal, str) else str(goal).strip()
    if not goal_text:
        return head + "."
    pace = goal_to_pace(goal_text, race_dist_km)
    if pace:
        return f"{head}, target {goal_text} at {pace}/km."
    return f"{head}, target {goal_text}."


def classify_run(distance_km: float | None = None) -> str:
    """One-line run classification from a finished run's distance.

    Distance-only heuristic; a later lane may fold in pace/HR without
    changing the call shape (extra params stay optional).

    Non-numeric, missing, boolean, NaN, or infinite inputs all map to the
    neutral "Training run" instead of raising, so a malformed activity
    payload can never break stamping. Negative distances raise ValueError.
    """
    if distance_km is None or isinstance(distance_km, bool):
        return "Training run"
    try:
        km = float(distance_km)
    except (TypeError, ValueError):
        return "Training run"
    if math.isnan(km) or math.isinf(km):
        return "Training run"
    if km < 0:
        raise ValueError("distance_km must be >= 0")
    if km < 3:
        return "Shakeout"
    if km < 8:
        return "Easy miles"
    if km < 15:
        return "Steady run"
    if km < 25:
        return "Long run"
    return "Big long run"


def build_description(race_name: str, race_date_iso: str, goal: str = "",
                      race_dist_km: float | None = None,
                      month_km: float | None = None,
                      year_km: float | None = None,
                      today_iso: str | None = None) -> str:
    """Countdown block: countdown + target, month/year km, promo footer.

    The totals line is omitted only when both totals are unknown; the
    promo line always closes the block. `classify_run` stays available
    for the run-kind update style but is no longer part of the block.
    """
    head = countdown_line(race_name, race_date_iso, goal, race_dist_km,
                          today_iso)
    lines = [head]
    if month_km is not None or year_km is not None:
        lines.append(totals_line(month_km, year_km, today_iso))
    lines.append(PROMO_LINE)
    return "\n".join(lines)


# Lines that can only come from a block we wrote (both the current shape
# and retired ones). Used to strip our own prior stamp before re-stamping
# so an activity never accumulates stacked blocks.
_OWN_LINE_MARKERS = (
    "days to go",
    "mynextpr",
    "target pace",
    "target ",
    "so far:",
    " km \u00b7 ",
    "countdown by",
    "training run",
    "easy run",
    "race day",
    "goal ",
)


def strip_prior_block(existing_description: str) -> str:
    """Remove our own previously stamped block from a description.

    Only strips when the text carries our signature (the promo footer or
    the retired countdown-by line), and only trailing lines — the
    runner's own notes above are always preserved. Anything unrecognized
    is returned untouched.
    """
    text = existing_description or ""
    if not isinstance(text, str) or not text.strip():
        return ""
    lowered = text.lower()
    signed = (PROMO_LINE.lower() in lowered
              or "countdown by mynextpr" in lowered
              or ("days to go" in lowered
                  and ("target " in lowered or "so far:" in lowered
                       or " km \u00b7 " in lowered)))
    if not signed:
        return text.strip()
    lines = text.strip().split("\n")
    i = len(lines)
    while i > 0:
        line = lines[i - 1].strip()
        if not line:
            i -= 1
            continue
        if any(marker in line.lower() for marker in _OWN_LINE_MARKERS):
            i -= 1
            continue
        break
    return "\n".join(lines[:i]).strip()


def apply_style(existing_description: str, block: str,
                style: str = APPEND) -> str:
    """Merge the countdown block into a description per the update style.

    Never touches the activity title — descriptions only. Over-long
    results are truncated from the runner's own text first so the
    countdown block always survives intact.
    """
    if style not in UPDATE_STYLES:
        raise ValueError(f"style must be one of {UPDATE_STYLES}")
    if not isinstance(block, str) or not block:
        raise ValueError("block is required")
    own = (existing_description or "").strip() if isinstance(
        existing_description, str) else ""
    if style == REPLACE or not own:
        merged = block
    else:
        merged = f"{own}{SEPARATOR}{block}"
    if len(merged) <= MAX_DESCRIPTION_CHARS:
        return merged
    # Truncate the runner's own text; the countdown block is never cut.
    room = MAX_DESCRIPTION_CHARS - len(SEPARATOR) - len(block)
    if room <= 0:  # block itself exceeds the cap; still return it whole
        return block
    return f"{own[:room].rstrip()}{SEPARATOR}{block}"


@dataclass
class EngineState:
    """Local post-connect state. No tokens: consent is a boolean stub."""
    race_name: str = ""
    race_date_iso: str = ""
    goal: str = ""
    # Nominal race distance (km) for goal → target-pace conversion, plus
    # month/year run totals (km) from athlete stats for the totals line.
    race_dist_km: float | None = None
    month_km: float | None = None
    year_km: float | None = None
    style: str = APPEND
    connected: bool = False
    paused: bool = False
    # Names of activities already stamped, so a retry never double-writes.
    stamped: set = field(default_factory=set)

    def validated_selection(self) -> tuple[str, str]:
        if not isinstance(self.race_name, str) or not self.race_name.strip():
            raise ValueError("Pick a race first — then connect.")
        if not self.race_date_iso:
            raise ValueError("Race date is required.")
        parse_iso_day(self.race_date_iso)  # fail fast on bad dates
        if self.style not in UPDATE_STYLES:
            raise ValueError(f"style must be one of {UPDATE_STYLES}")
        return self.race_name.strip(), self.race_date_iso


def connect(state: EngineState) -> EngineState:
    """Mock OAuth consent. Gated on a selected race; stores no token."""
    state.validated_selection()
    state.connected = True
    state.paused = False
    return state


def disconnect(state: EngineState) -> EngineState:
    """Disconnect: clear consent and history. Nothing to revoke remotely."""
    state.connected = False
    state.paused = False
    state.stamped.clear()
    return state


def pause(state: EngineState) -> EngineState:
    """Pause updates; the runner's activities are left untouched."""
    state.paused = True
    return state


def resume(state: EngineState) -> EngineState:
    """Resume updates after a pause."""
    state.paused = False
    return state


def preview_update(state: EngineState, activity: dict,
                   today_iso: str | None = None) -> tuple[str | None, str]:
    """Compute the new description for a finished run, or skip with a reason.

    Returns (new_description, reason). `new_description` is None when the
    update is skipped. The activity dict is never mutated, and its `title`
    key is never read or written — description-only by construction: only
    the keys in `_ACTIVITY_KEYS` (`id`, `distance_km`, `description`) are
    ever accessed.
    """
    if not isinstance(activity, dict):
        raise TypeError("activity must be a dict")
    if not state.connected:
        return None, "skipped: not connected"
    if state.paused:
        return None, "skipped: paused"
    race_name, race_iso = state.validated_selection()
    raw_id = activity.get("id", "")
    key = str(raw_id) if raw_id != "" else ""
    if key and key in state.stamped:
        return None, "skipped: already stamped"
    block = build_description(race_name, race_iso, state.goal,
                              state.race_dist_km, state.month_km,
                              state.year_km, today_iso)
    new_description = apply_style(str(activity.get("description") or ""),
                                  block, state.style)
    if key:
        state.stamped.add(key)
    return new_description, "ok"


# ---------------------------------------------------------------------------
# Runnable self-tests (stdlib only: no pytest, no network, no tokens).
# ---------------------------------------------------------------------------

def _fresh_state(**overrides) -> EngineState:
    base = {
        "race_name": "Delhi Half Marathon",
        "race_date_iso": "2026-10-18",
        "goal": "sub-2",
        "style": APPEND,
    }
    base.update(overrides)
    state = EngineState(**base)
    return connect(state)


class _TitleTripwire(dict):
    """Dict that explodes if anything reads the `title` key."""

    def __getitem__(self, key):
        if key == "title":
            raise AssertionError("engine read activity['title']")
        return super().__getitem__(key)

    def get(self, key, *args):
        if key == "title":
            raise AssertionError("engine read activity.get('title')")
        return super().get(key, *args)

    def __contains__(self, key):
        if key == "title":
            raise AssertionError("engine probed 'title' in activity")
        return super().__contains__(key)


def _module_ast():
    return ast.parse(inspect.getsource(sys.modules[__name__]))


def run_self_tests() -> tuple[int, int, list[str]]:
    """Run every check; returns (passed, failed, failure_names)."""
    passed = 0
    failures: list[str] = []

    def check(name: str, cond: bool) -> None:
        nonlocal passed
        if cond:
            passed += 1
        else:
            failures.append(name)

    def raises(name: str, exc, fn, *args, **kwargs) -> None:
        nonlocal passed
        try:
            fn(*args, **kwargs)
        except exc:
            passed += 1
        except Exception as other:  # noqa: BLE001 — test reports, never raises
            failures.append(f"{name} (wrong exc: {type(other).__name__})")
        else:
            failures.append(f"{name} (no exception)")

    # -- countdown template -------------------------------------------------
    check("countdown plural+goal",
          countdown_line("Delhi Half Marathon", "2026-10-18", "sub-2",
                         today_iso="2026-10-10") == "8 days to go \u2014 Delhi Half Marathon, target sub-2.")
    check("countdown singular",
          countdown_line("5K Test", "2026-10-11", today_iso="2026-10-10") == "1 day to go \u2014 5K Test.")
    check("countdown race-day",
          countdown_line("Marathon", "2026-10-10", today_iso="2026-10-10") == "Race day today — Marathon.")
    check("countdown past",
          countdown_line("Marathon", "2026-10-01", today_iso="2026-10-10") == "Race day today — Marathon.")
    check("countdown blank goal omitted",
          countdown_line("Marathon", "2026-10-18", "   ",
                         today_iso="2026-10-10") == "8 days to go \u2014 Marathon.")
    check("countdown pace from goal+dist",
          countdown_line("Delhi Half Marathon", "2026-10-18", "2:00",
                         RACE_DIST_KM["half"], "2026-10-10") == "8 days to go \u2014 Delhi Half Marathon, target 2:00 at 5:41/km.")
    check("countdown tmm pace",
          countdown_line("Tata Mumbai Marathon", "2027-01-17", "3:30",
                         RACE_DIST_KM["full"], "2026-10-10") == "99 days to go \u2014 Tata Mumbai Marathon, target 3:30 at 4:59/km.")

    # -- goal time to target pace ---------------------------------------------
    check("pace half", goal_to_pace("2:00", 21.0975) == "5:41")
    check("pace full", goal_to_pace("3:30", 42.195) == "4:59")
    check("pace seconds", goal_to_pace("1:45:00", 21.0975) == "4:59")
    check("pace unparseable", goal_to_pace("sub-2", 21.0975) == "")
    check("pace no dist", goal_to_pace("2:00", None) == "")
    check("pace bad dist", goal_to_pace("2:00", 0) == "")
    check("pace bad minutes", goal_to_pace("2:75", 21.0975) == "")
    check("pace zero", goal_to_pace("0:00", 21.0975) == "")

    # -- totals line ------------------------------------------------------------
    check("totals shape",
          totals_line(42, 310, "2026-10-10") == "October so far: 42 km · 2026 so far: 310 km.")
    check("totals fraction", totals_line(42.5, 310, "2026-10-10") == "October so far: 42.5 km · 2026 so far: 310 km.")
    check("totals unknown", totals_line(None, None, "2026-10-10") == "October so far: – km · 2026 so far: – km.")
    check("totals garbage", totals_line("junk", -3, "2026-10-10") == "October so far: – km · 2026 so far: – km.")
    check("days_to_go math", days_to_go("2026-10-18", "2026-10-10") == 8)
    raises("countdown blank name", ValueError,
           countdown_line, "   ", "2026-10-18")
    raises("countdown bad date", ValueError,
           countdown_line, "Race", "not-a-date")
    raises("parse non-string", TypeError, parse_iso_day, 20261018)
    raises("parse wrong shape", ValueError, parse_iso_day, "10/18/2026")
    raises("parse impossible", ValueError, parse_iso_day, "2026-02-30")
    check("parse padded ok", parse_iso_day("2026-10-18") == date(2026, 10, 18))

    # -- run classification --------------------------------------------------
    for km, want in [(0, "Shakeout"), (2.9, "Shakeout"), (3, "Easy miles"),
                     (7.9, "Easy miles"), (8, "Steady run"), (14.9, "Steady run"),
                     (15, "Long run"), (24.9, "Long run"), (25, "Big long run"),
                     (42.2, "Big long run")]:
        check(f"classify {km}km", classify_run(km) == want)
    check("classify None", classify_run(None) == "Training run")
    check("classify garbage", classify_run("junk") == "Training run")
    check("classify bool", classify_run(True) == "Training run")
    check("classify nan", classify_run(float("nan")) == "Training run")
    check("classify inf", classify_run(float("inf")) == "Training run")
    raises("classify negative", ValueError, classify_run, -1)

    # -- prior-block stripping ------------------------------------------------
    stacked = ("92 days to go for Tata Mumbai Marathon. Target pace 5:41/km (goal 4:00).\n"
               "October: 127.4 km · 2026: 1423.3 km.\n"
               "\n"
               "92 days to go — Tata Mumbai Marathon, target 4:00 at 5:41/km.\n"
               "October so far: 127.4 km · 2026 so far: 1423.3 km.\n"
               + PROMO_LINE)
    check("strip stacked to fresh",
          strip_prior_block(stacked) == "")
    check("strip preserves notes",
          strip_prior_block("Felt strong today\n" + stacked) == "Felt strong today")
    check("strip untouched without signature",
          strip_prior_block("Easy miles around the park") == "Easy miles around the park")
    check("strip empty", strip_prior_block("   ") == "")

    # -- description block ---------------------------------------------------
    check("block shape",
          build_description("Delhi Half Marathon", "2026-10-18", "2:00",
                            RACE_DIST_KM["half"], 42, 310,
                            "2026-10-10") == "8 days to go — Delhi Half Marathon, target 2:00 at 5:41/km.\nOctober so far: 42 km · 2026 so far: 310 km.\nSet up tracking for your goal race at mynextpr.com")
    check("block no totals",
          build_description("Delhi Half Marathon", "2026-10-18", "sub-2",
                            today_iso="2026-10-10") == "8 days to go \u2014 Delhi Half Marathon, target sub-2.\n" + PROMO_LINE)

    # -- append / replace styles ---------------------------------------------
    block = ("8 days to go — Delhi Half Marathon, target 2:00 at 5:41/km.\n"
             "October so far: 42 km · 2026 so far: 310 km.\n"
             "Set up tracking for your goal race at mynextpr.com")
    check("append keeps notes",
          apply_style("Easy miles around the park", block, APPEND)
          == f"Easy miles around the park{SEPARATOR}{block}")
    check("replace drops notes",
          apply_style("Easy miles around the park", block, REPLACE) == block)
    check("append empty existing", apply_style("   ", block, APPEND) == block)
    raises("bad style", ValueError, apply_style, "notes", block, "prepend")
    long_own = "x" * 600
    trimmed = apply_style(long_own, block, APPEND)
    check("truncate keeps block whole",
          trimmed.endswith(f"{SEPARATOR}{block}") and len(trimmed) <= MAX_DESCRIPTION_CHARS)
    check("oversize block returned whole",
          apply_style("notes", "B" * 600, APPEND) == "B" * 600)

    # -- connect gating -------------------------------------------------------
    raises("connect needs race", ValueError, connect, EngineState())
    st = EngineState(race_name="R", race_date_iso="2026-10-18")
    connect(st)
    check("connect sets flags", st.connected and not st.paused)

    # -- no-double-stamp ------------------------------------------------------
    st = _fresh_state()
    act = {"id": "a1", "description": "Morning notes", "distance_km": 10}
    first, reason1 = preview_update(st, dict(act), "2026-10-10")
    second, reason2 = preview_update(st, dict(act), "2026-10-10")
    check("first stamp ok",
          reason1 == "ok" and first is not None and "8 days to go" in first
          and first.startswith("Morning notes"))
    check("no-double-stamp", second is None and reason2 == "skipped: already stamped")
    other, reason3 = preview_update(st, {"id": "a2", "description": "", "distance_km": 5}, "2026-10-10")
    check("different id stamps", reason3 == "ok" and other is not None)
    noid1, _ = preview_update(st, {"description": "x", "distance_km": 5}, "2026-10-10")
    check("missing id still computes", noid1 is not None and "days to go" in noid1)

    # -- pause / resume skip ---------------------------------------------------
    st = _fresh_state()
    pause(st)
    skipped, why = preview_update(st, {"id": "p1", "description": "", "distance_km": 5}, "2026-10-10")
    check("pause skips", skipped is None and why == "skipped: paused")
    check("pause stamps nothing", "p1" not in st.stamped)
    resume(st)
    resumed, why2 = preview_update(st, {"id": "p1", "description": "", "distance_km": 5}, "2026-10-10")
    check("resume re-stamps", resumed is not None and why2 == "ok")

    # -- disconnect skip -------------------------------------------------------
    st = _fresh_state()
    preview_update(st, {"id": "d1", "description": "", "distance_km": 5}, "2026-10-10")
    disconnect(st)
    skipped_d, why_d = preview_update(st, {"id": "d2", "description": "", "distance_km": 5}, "2026-10-10")
    check("disconnect skips", skipped_d is None and why_d == "skipped: not connected")
    check("disconnect clears history", len(st.stamped) == 0)
    connect(st)
    again, why_a = preview_update(st, {"id": "d1", "description": "", "distance_km": 5}, "2026-10-10")
    check("reconnect restamps cleared id", again is not None and why_a == "ok")

    # -- not-connected skip ----------------------------------------------------
    cold = EngineState(race_name="R", race_date_iso="2026-10-18")
    skipped_c, why_c = preview_update(cold, {"id": "c1"}, "2026-10-10")
    check("not-connected skips", skipped_c is None and why_c == "skipped: not connected")

    # -- description-only by construction --------------------------------------
    st = _fresh_state()
    wired = _TitleTripwire({"id": "t1", "title": "SACRED — do not touch",
                            "description": "notes", "distance_km": 6})
    snapshot = dict(wired)
    out, why_t = preview_update(st, wired, "2026-10-10")
    check("title never touched", why_t == "ok" and out is not None
          and "SACRED" not in out
          and dict.get(wired, "title") == "SACRED — do not touch")
    check("input never mutated", dict(wired) == snapshot)
    raises("non-dict activity", TypeError, preview_update, st, [("id", "x")])

    tree = _module_ast()

    def accesses_title(node: ast.AST) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.Subscript):
                sl = child.slice
                if isinstance(sl, ast.Constant) and sl.value == "title":
                    return True
            if isinstance(child, ast.Attribute) and child.attr == "title":
                return True
        return False

    check("AST: no title access in code", not accesses_title(tree))
    check("only allowed activity keys",
          all(fn.__code__.co_names.count("title") == 0
              for fn in (preview_update, build_description, apply_style)))
    check("activity key allowlist", _ACTIVITY_KEYS == ("id", "distance_km", "description"))

    # -- no tokens / no network --------------------------------------------------
    imported_roots = set()
    for child in ast.walk(tree):
        if isinstance(child, ast.Import):
            imported_roots.update(a.name.split(".")[0] for a in child.names)
        elif isinstance(child, ast.ImportFrom) and child.module:
            imported_roots.add(child.module.split(".")[0])
    check("no network imports", not (imported_roots & set(_NETWORK_IMPORT_ROOTS)))
    check("no token fields",
          not any("token" in f.name or "secret" in f.name for f in fields(EngineState)))
    check("scopes stay minimal", SCOPES == ("read", "activity:read", "activity:write"))

    # -- replace style end-to-end ----------------------------------------------
    st = _fresh_state(style=REPLACE)
    rep, why_r = preview_update(st, {"id": "r1", "description": "my notes", "distance_km": 30},
                                "2026-10-10")
    check("replace end-to-end",
          why_r == "ok" and rep == "8 days to go \u2014 Delhi Half Marathon, target sub-2.\n" + PROMO_LINE)

    # -- hardening edge cases ----------------------------------------------------
    check("parse padded whitespace", parse_iso_day("  2026-10-18  ") == date(2026, 10, 18))
    raises("parse month 13", ValueError, parse_iso_day, "2026-13-01")
    raises("parse day 00", ValueError, parse_iso_day, "2026-10-00")
    raises("countdown non-string name", TypeError,
           countdown_line, 42, "2026-10-18", "", "2026-10-10")
    check("countdown numeric goal",
          countdown_line("R", "2026-10-18", 42, today_iso="2026-10-10") == "8 days to go \u2014 R, target 42.")
    check("classify numeric string", classify_run("10") == "Steady run")
    check("classify False", classify_run(False) == "Training run")
    check("apply None existing", apply_style(None, block, APPEND) == block)
    raises("apply empty block", ValueError, apply_style, "notes", "")
    raises("selection bad style", ValueError,
           EngineState(race_name="R", race_date_iso="2026-10-18", style="prepend").validated_selection)
    st = _fresh_state()
    first_i, _ = preview_update(st, {"id": 123, "description": "", "distance_km": 5}, "2026-10-10")
    second_i, why_i = preview_update(st, {"id": "123", "description": "", "distance_km": 5}, "2026-10-10")
    check("int/str id dedupe", first_i is not None and second_i is None
          and why_i == "skipped: already stamped")
    st = _fresh_state(goal="2:00", race_dist_km=RACE_DIST_KM["half"],
                      month_km=42, year_km=310)
    full, why_f = preview_update(st, {"id": "f1", "description": "", "distance_km": 10},
                                 "2026-10-10")
    check("end-to-end totals block",
          why_f == "ok" and full == "8 days to go — Delhi Half Marathon, target 2:00 at 5:41/km.\nOctober so far: 42 km · 2026 so far: 310 km.\nSet up tracking for your goal race at mynextpr.com")
    st = _fresh_state()
    nodist, why_n = preview_update(st, {"id": "m1", "description": ""}, "2026-10-10")
    check("missing distance trains on",
          why_n == "ok" and nodist is not None and nodist.endswith(PROMO_LINE))
    nonedesc, why_o = preview_update(st, {"id": "n1", "description": None, "distance_km": 5},
                                     "2026-10-10")
    check("None description ok",
          why_o == "ok" and nonedesc is not None and "8 days to go" in nonedesc)
    st = _fresh_state()
    pause(st)
    disconnect(st)
    check("disconnect clears pause", st.connected is False and st.paused is False)
    import contextlib as _cl
    import io as _io
    with _cl.redirect_stderr(_io.StringIO()):
        check("main bad flag exits 2", main(["--bogus"]) == 2)

    total = passed + len(failures)
    return passed, len(failures), failures


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if args and args not in (["--self-test"], []):
        print(f"usage: {sys.argv[0]} [--self-test]", file=sys.stderr)
        return 2
    passed, failed, failures = run_self_tests()
    print(f"v6 self-tests: {passed} passed, {failed} failed")
    for name in failures:
        print(f"  FAIL: {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
