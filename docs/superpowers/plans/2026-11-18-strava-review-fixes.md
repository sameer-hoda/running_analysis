# Strava Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply Strava review fixes 1, 2, 3, 4 and 6 plus GA consent hygiene to mynextpr in one reviewable local branch, without deploying or submitting anything.

**Architecture:** Small surgical edits to `v6/server.py` (remove poller thread, keep webhook path), static HTML/JS demo content (fictional date-aware examples), docs updates (README, deploy notes, approval drafts), and a separate minimal patch for the legacy `sameer-hoda/mynextpr` repo. Prove webhook stamping with mocked events.

**Tech Stack:** Python 3.11 dependency-free backend (`v6/server.py`, `v6/update_engine.py`), static HTML/JS pages, nginx + systemd on EC2 (untouched).

**Spec:** This user message of 2026-11-18 (fixes 0–6 inline). No separate spec file; the message is the spec and travels with this plan.

## Global Constraints

- Work locally on a branch; show diff and test results. Do not push.
- Do not deploy, change account/repository settings, create/delete webhook subscriptions, reconnect OAuth, modify real activities or athlete settings, send messages, or submit an application. List such steps for owner approval.
- Never expose tokens, secrets, or other athletes' data.
- Do not redesign the product or add features.
- Retain GA measurement ID `G-B63L6BJZLY`. Do not remove it, replace the provider, or add tracking.
- Do not pass Strava athlete/activity data, tokens, identifiers, or personal data in analytics events/URLs.
- Preserve essential login/session behaviour when analytics is rejected.
- Claim webhook-only operation only once both code and deployment are verified; webhook health and live EC2 revision are currently unverified.
- Treat October 17–30 checks as historical, not fresh tests.
- Do not claim support-inbox monitoring is fixed (unverified).
- Distinguish Strava's app-description/screenshots asks from rate-limit risk and recommended repo/demo/privacy hygiene.
- Do not claim application readiness or guaranteed review/approval, invent a user-growth forecast, or submit anything.
- Fix 2 math for context only: 3 reads per qualifying athlete/cycle, 8,640 background reads/day if all 10 qualify continuously; paused/disconnected/race-less/past-race athletes skipped; reviewed cap 2,000/day reads — verify current limits before rollout.

## Review Focus

- Webhook arriving twice concurrently for the same activity could double-stamp or race the description-block replace — expect exactly-once visible block.
- Strava retrying a failed webhook after our fetch failed could stamp stale data — expect bounded retry/backoff and no corrupt description.
- Deauthorization arriving mid-stamp could leave a half-written state — expect revoke-then-wipe to win and no further writes.
- A run logged exactly on race day vs day after could stamp when it should stop — expect race-day stamps, post-race stops.
- Rejecting analytics consent could break login/session cookies — expect full app function with zero analytics storage.

---

### Task 0: Inspect first, branch, baseline

**Files:**
- Modify: none (read-only) — `v6/server.py`, `v6/update_engine.py`, `v6/*.html`, `v6/strava*.js`, `README.md`, `deploy/*`, `strava-application/*`
- Test: `python3 v6/server.py --self-test`, `python3 v6/update_engine.py --self-test`

**Interfaces:**
- Consumes: `git branch -a`, `git status`, GitHub repo `sameer-hoda/running_analysis` + `sameer-hoda/mynextpr` availability
- Produces: branch name + file inventory + behaviour notes consumed by Tasks 1–6

- [ ] **Step 1: Create local branch from main and record base SHA**

Run: `git status --short; git log --oneline -3; git checkout -b strava-review-fixes-<date>`
Expected: clean tree or explicitly listed dirt; base SHA noted in plan PR text.

- [ ] **Step 2: Inventory actual branches, files, and behaviour**

Run: `git branch -a; ls v6/; grep -n "_poller\|interval_seconds\|threading\|Thread" v6/server.py; grep -rn "Sameer\|Delhi Half\|G-B63L6BJZLY\|googletag\|consent" v6/ --include="*.html" --include="*.js" | head -50`
Expected: confirmed poller symbol lines, demo-content hits, GA hits; note if `sameer-hoda/mynextpr` checkout exists locally or not.

- [ ] **Step 3: Run baseline self-tests and record results as historical-plus-baseline**

Run: `python3 v6/server.py --self-test; python3 v6/update_engine.py --self-test`
Expected: PASS/FAIL counts recorded; Oct 17–30 numbers not reused as fresh.

### Task 1: Correct the Strava app description

**Files:**
- Modify: conflicting product descriptions in `README.md`, `v6/*.html` consent/scope copy where it over-promises, `strava-application/06-approval-pack.md` (or equivalent draft), `deploy/strava-approval-tracker.md` if it repeats the description
- Test: `grep -rn "countdown" README.md v6/*.html strava-application/ | head -30` review

**Interfaces:**
- Consumes: final code behaviour from Task 0 inventory
- Produces: replacement description string + manual settings step for handoff

- [ ] **Step 1: Write a failing content check for over-promising description copy**

```python
def test_no_overpromising_description():
    text = open("README.md").read() + open("strava-application/06-approval-pack.md").read()
    assert "never stored" not in text.lower() or "activity content" in text.lower()
```

- [ ] **Step 2: Run check to confirm current copy conflicts**

Run: `python3 /tmp/mnp-desc-check.py`
Expected: FAIL listing the conflicting lines.

- [ ] **Step 3: Update docs to match replacement description `mynextpr adds a countdown to your chosen race to the description of your Strava runs. Activity titles are never changed.` in `README.md`, app consent copy, approval draft; remove unsupported promises about coverage, storage, API compliance**

Replacement string is exact (including periods). Manual step (do not execute): owner pastes it into Strava API Settings → Application Description and saves.

- [ ] **Step 4: Re-run check**

Run: `python3 /tmp/mnp-desc-check.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md v6/connect.html v6/picker.html strava-application/06-approval-pack.md
git commit -m "docs: align Strava app description, remove unsupported promises"
```

### Task 2: Remove automatic five-minute polling, keep webhooks

**Files:**
- Modify: `v6/server.py` (remove `_poller(interval_seconds=300)`, its unconditional thread startup in `main()`, other scheduled scan paths)
- Modify: `README.md`, `deploy/*`, `strava-application/*` application drafts (webhook-only reality)
- Test: existing self-tests + new mocked webhook test in `/tmp/mnp-webhook-proof.py` (not committed) and any committed test sibling if repo convention requires it

**Interfaces:**
- Consumes: `main()` startup, webhook verify/handle, `update_engine` stamp function signatures
- Produces: webhook-only `server.py` with HTTP threading retained; manual pre-rollout/deployment/rollback steps

- [ ] **Step 1: Write failing test proving poller exists**

```python
def test_no_recurring_scan():
    src = open("v6/server.py").read()
    assert "_poller" not in src and "interval_seconds" not in src
```

- [ ] **Step 2: Run it to confirm it fails on current code**

Run: `python3 /tmp/mnp-nopoller-check.py`
Expected: FAIL (poller present).

- [ ] **Step 3: Implement removal in `v6/server.py`: delete `_poller()` def, its thread startup in `main()`, any other scheduled scan/loop; retain `threading` only for the HTTP server; no default-on flag, no interval change, no replacement poller**

- [ ] **Step 4: Verify webhook path intact with mocked events: OAuth, token refresh, webhook verification + activity handling, race/goal selection, pause, disconnect, deletion/export, description-only stamping; check duplicate/concurrent delivery, self-triggered update loops, ownership/isolation, non-run handling, failed fetches, deauthorization, race-day cutoffs**

Run: `python3 v6/server.py --self-test; python3 v6/update_engine.py --self-test; python3 /tmp/mnp-webhook-proof.py`
Expected: all PASS; regressions fixed in this task, unrelated defects flagged separately.

- [ ] **Step 5: Update `README.md`, deployment notes, application drafts to webhook-only reality; add manual-steps section (subscription/callback checks, deployment verification, rollback) without executing**

- [ ] **Step 6: Commit**

```bash
git add v6/server.py README.md deploy/ strava-application/
git commit -m "fix: remove 5-min poller, webhook-only stamping"
```

### Task 3: Legacy mynextpr RunForm confusion

**Files:**
- Modify (only if local checkout exists): legacy repo `README.md` + homepage banner
- Else produce: separate patch file `docs/superpowers/plans/mynextpr-legacy-banner.patch` with exact proposed edit
- Test: visual read of rendered README/banner; never rename/archive/delete/change visibility

**Interfaces:**
- Consumes: availability of `sameer-hoda/mynextpr` checkout
- Produces: minimal legacy-repo edit OR exact patch text, plus current-repo untouched guarantee

- [ ] **Step 1: Check legacy repo availability**

Run: `ls ../mynextpr/README.md 2>/dev/null || echo "unavailable"`
Expected: either path or `unavailable` recorded.

- [ ] **Step 2: If available, apply minimal `README.md`/banner change identifying it as the separate legacy RunForm project and removing claims/badges that it is live at mynextpr.com; preserve history and code**

- [ ] **Step 3: If unavailable, write exact proposed edit as a separate patch file; do not claim completion**

- [ ] **Step 4: Commit (current repo only holds the patch file if legacy unavailable)**

```bash
git add docs/superpowers/plans/mynextpr-legacy-banner.patch
git commit -m "docs: legacy RunForm repo banner proposal"
```

### Task 4: Fictional demo content everywhere

**Files:**
- Modify: source templates/assets behind no-JS HTML fallback (old Delhi Half card + real name), signed-out manage demo (expired countdown), homepage hero if needed, relevant `meta`/preview text
- Test: manual mobile/desktop + JS-disabled views; `grep -rn "Sameer" v6/ --include="*.html"` must return only fictional/cleared hits

**Interfaces:**
- Consumes: template inventory from Task 0
- Produces: consistently fictional, clearly demo-labelled examples (date-aware future or timeless)

- [ ] **Step 1: Write failing demo-content check**

```python
def test_no_real_demo_names():
    import re, glob
    blob = "".join(open(f).read() for f in glob.glob("v6/*.html"))
    assert "Sameer" not in blob and "Delhi Half" not in blob
```

- [ ] **Step 2: Run to confirm FAIL on current fallback/demo**

Run: `python3 /tmp/mnp-demo-check.py`
Expected: FAIL with file:line hits.

- [ ] **Step 3: Replace with fictional clearly-labelled demos in `v6/*.html` + assets: e.g. `You · Example race · DEMO` with a date-aware future example (computed from today) or timeless labelled example; never another hard-coded countdown; never touch real athletes' data; check meta/preview text**

- [ ] **Step 4: Re-run check + manual views (mobile/desktop widths, JS disabled)**

Run: `python3 /tmp/mnp-demo-check.py`
Expected: PASS; manual view notes recorded.

- [ ] **Step 5: Commit**

```bash
git add v6/index.html v6/manage.html v6/assets/
git commit -m "fix: fictional clearly-labelled demo content"
```

### Task 5: GA consent hygiene (keep G-B63L6BJZLY)

**Files:**
- Modify: `v6/*.html` banner/consent copy, consent JS, privacy page disclosure
- Test: acceptance / rejection / withdrawal probes in `/tmp/mnp-consent-proof.py` + manual browser checks

**Interfaces:**
- Consumes: existing `G-B63L6BJZLY` snippet locations
- Produces: opt-in-only analytics with change-of-choice control

- [ ] **Step 1: Write failing consent check (no analytics storage before opt-in)**

```python
def test_no_analytics_before_optin():
    src = open("v6/index.html").read()
    assert "G-B63L6BJZLY" in src and "consent" in src.lower()
```

- [ ] **Step 2: Implement plain-language disclosure, accept/reject controls, no analytics loading/storage before opt-in, change-choice control; preserve login/session when rejected**

- [ ] **Step 3: Prove no Strava data in analytics events/URLs via grep + test**

Run: `grep -rn "gtag\|analytics" v6/ --include="*.html" --include="*.js"; python3 /tmp/mnp-consent-proof.py`
Expected: PASS for accept/reject/withdraw; login works with analytics rejected.

- [ ] **Step 4: Commit**

```bash
git add v6/index.html v6/privacy.html v6/assets/
git commit -m "privacy: GA opt-in consent, no pre-consent storage"
```

### Task 6: Refresh review evidence (checklist, no new writes)

**Files:**
- Create: `docs/superpowers/plans/strava-evidence-checklist.md` (or `deploy/` equivalent)
- Test: none automated; manual capture list only

**Interfaces:**
- Consumes: every place Strava data appears (Task 0–5 outputs)
- Produces: checklist separating synthetic-local vs real-integration evidence; missing-capture approval list

- [ ] **Step 1: Write checklist covering homepage/demo, race picker, connect page/button + scope explanation, connected manage view, stamped activity description, OAuth consent screen**

- [ ] **Step 2: Mark existing five private-folder captures as `captured-before-fixes` (preserve originals); list which need refreshing and the approval needed (no reconnect, no activity writes to obtain evidence)**

- [ ] **Step 3: Note OAuth walkthrough video as optional (older pack, not a stated form requirement)**

- [ ] **Step 4: Commit checklist**

```bash
git add docs/superpowers/plans/strava-evidence-checklist.md
git commit -m "docs: Strava evidence refresh checklist"
```
