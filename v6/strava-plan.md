# v6 Strava Plan — OAuth SSO, Scopes, Consent & Compliance (finalized)

> Update 2026-10-17: this plan is kept as history. Current truth lives in
> `strava-application/`. Known deltas: scopes are now
> `read,activity:read,activity:write` (§3's two-scope set was widened because
> reading the new run's description needs `activity:read`); the connect flow,
> webhook receiver, per-athlete store, policy pages, official Connect buttons,
> and `View on Strava` links are implemented (§10.8 TODO-1 and TODO-3 done).

Source of truth: `v6/connect.html` (this lane's mock connect flow).
Read-only reference: `v5/mock.html`, `v5/worker-contracts.md` (§3–§4), `v5/events.snapshot.json`.
Scope of this doc: plan only. No real secrets, no network calls, no production code.

## 1. Goals and non-goals

Goals: define the production Strava connection flow that the `v6/connect.html`
`Connect with Strava` button stands in for, with minimum scopes, own-activity-only
writes, explicit consent, and description-only writes.

Non-goals: no client ID/secret in the repo, no live token exchange in the mock,
no activity-title writes, no endorsement claims, no broader scopes.

## 2. OAuth SSO flow (production)

All steps use the official Strava OAuth flow; the mock button (`v6/connect.html`
`#connect`) stays a mock — it only flips preview text and never initiates this flow.

1. **Gate on race selection.** Connect is disabled until an upcoming race is
   picked. Clicking with no race shows `Pick a race first — then connect.`
   A race whose date has passed (`daysLeft < 0`) keeps Connect disabled with
   `<Race> — race date has passed. Pick an upcoming race.` and lists as
   `date passed`; race-day itself (`daysLeft == 0`) remains connectable.
   (matches `connect.html` gated-button behavior).
2. **Authorization request.** Redirect the user to Strava's authorization URL with:
   - `client_id` (server-side config, never in the repo or client JS),
   - `redirect_uri` (registered allow-listed callback),
   - `response_type=code`,
   - `scope=read,activity:write` (minimum; see §3),
   - `approval_prompt=force` on first connect so the consent screen always shows.
3. **User grants consent on strava.com.** User sees exactly what the app requests
   (read + write own activities) and approves or declines there.
4. **Callback + code exchange (server side only).** The server exchanges `code`
   for `access_token` + `refresh_token` over HTTPS, stores tokens encrypted,
   never exposes them to the browser or logs them.
5. **Token lifecycle.** Short-lived access tokens; refresh on expiry; re-prompt
   consent on revoked/expired grants. Disconnect button revokes and deletes
   stored tokens (§7).
6. **Post-connect behavior.** Only then does the countdown writer run, per §5.

Mock rule: the v6 mock `Connect with Strava` button MUST NOT contain a real
`client_id`, MUST NOT link to `strava.com/oauth`, and MUST NOT `fetch`/`XHR`
anything. It only renders `[mock] Connected. <statusText>`.

## 3. Minimum scopes: `read` + `activity:write`

- Request exactly `read` and `activity:write`. No `read_all`, `profile:read_all`,
  `activity:read_all`, or any broader scope — per `worker-contracts.md` §4.
- Why these two: `read` covers the baseline profile/activity visibility the app
  needs; `activity:write` is the narrowest scope permitting description updates.
- Fine print adjacent to the CTA must state the scopes in plain words, e.g.
  `Reads your profile and updates descriptions on your own activities only.`
  (`connect.html` `#consent` carries this adjacent to `#connect`.)
- If Strava ever narrows `activity:write`, re-review rather than widening scopes.

## 4. Own-activities-only

- Update ONLY activities belonging to the authenticated athlete
  (`activity.athlete.id == token.athlete.id`). Never touch clubs, friends,
  tagged-others, or any activity not owned by the token holder.
- Enforcement: pre-write ownership check on every update call; skip + log any
  non-owned ID without writing. No bulk endpoints that bypass the check.
- Only act on new uploads by the connected user after connect; never backfill
  other athletes' history.

## 5. Explicit consent

- Consent is a distinct, affirmative step: user picks a race, reads the fine
  print, clicks connect, and approves on strava.com. Pre-ticked boxes or
  implied consent do not count.
- Fine print stays adjacent to the CTA (per contracts §4) and must say:
  (a) what is written (countdown string into description),
  (b) what is never touched (title),
  (c) own-activities-only,
  (d) scopes,
  (e) how to disconnect/delete (§7).
- First write happens only after the OAuth grant completes. Decline/cancel =
  no tokens stored, no writes attempted.
- Disconnect/revoke stops all future writes immediately.

## 6. Description-only writes — NEVER title

Per `worker-contracts.md` §3 (subtitle-only rule):

- Production writes `statusText()` output into the activity **description**
  only (Strava `description` field via update-activity call). Verdict-free
  4-line template (see `hero-copy.md` §2 for slot rules):
  `<Race> — N days to go (<date>)` / `Target: <dist> · Goal <goal>[ · Goal pace <pace>]`
  / `Today: <kind> <distance> @ <pace>` / `— countdown by mynextpr`.
  Goal/pace lines appear only when the user set a goal; the Today line echoes
  the written activity's own data.
- Verdict ban: never write training-status judgments (`on track`, `behind`,
  `faded`), coaching, or predictions — arithmetic and echoes only, per
  Strava API Policy §5.11.
- Write-once: stamp the countdown when the activity first appears; never
  rewrite old descriptions as days-left changes.
- NEVER write to, overwrite, prepend, or append to the activity **title**.
  The user's own title is sacred. No code path may set the `name`/`title`
  parameter — pass description alone.
- The mock `.preview` header reads `YOUR STRAVA DESCRIPTION AFTER EVERY RUN`
  and the lede reads `written into its Strava description`. Production copy
  must likewise say **description** everywhere.
- Guard: code review checklist item — `grep` the Strava update call for any
  `name`/`title` key; if present, the build fails.
- Idempotency: recompute the countdown string per activity (days-left changes
  daily); append/replace only our own countdown line, preserving the rest of
  the user's description text.

## 7. Privacy and deletion

- Data stored: OAuth tokens (encrypted at rest), selected race + goal,
  Strava athlete ID. Nothing else. No scraping of followers, kudos, or segments.
- Use: tokens are used solely for the consented description updates.
- Deletion: in-app Disconnect deletes tokens + race/goal mapping immediately;
  document a data-deletion contact/root; on Strava deauthorization webhook
  (if subscribed), purge that athlete's record within 7 days.
- No sale/sharing of Strava data with third parties; no analytics on activity
  contents beyond the write itself.
- Privacy policy + deletion instructions must ship before app review (§9).

## 8. No endorsement claims (brand)

Per contracts §4 and the mock tag `MOCK · Compatible with Strava`:

- Allowed wording only: `Compatible with Strava`, `Connect with Strava`
  (button label), `Find more races on MyNextBib`.
- NEVER claim endorsement, partnership, sponsorship, or `powered by Strava`.
  Do not use the Strava logo; the CTA uses `--accent` (`#fc5200`) as a plain
  color reference, not logo art.
- Attribution footer stays: `Race data: MyNextBib feed snapshot · generated
  <date> · …` plus `Register for <race> on MyNextBib` bib link and
  `Find more races on MyNextBib` link (`https://mynextbib.com`).
- App name/icon must not contain `Strava`.

## 9. Rate-limit and app-review checklist

- [ ] Scopes are exactly `read,activity:write`; authorization URL reviewed.
- [ ] No code path sets activity `name`/`title` (automated grep in CI).
- [ ] Ownership check (`athlete.id` match) on every write; non-owned skipped.
- [ ] Connect gated on upcoming-race selection (past races unconnectable); decline path stores nothing.
- [ ] Fine print (scopes, own-only, description-only, disconnect) adjacent to CTA.
- [ ] Disconnect + deletion flow works; deauthorization purges within 7 days.
- [ ] Rate limits: daily per-user writes bounded (one countdown refresh per new
  activity, no polling loops); backoff on HTTP 429; respect `X-RateLimit-*`
  headers; stay within Strava API guidelines (no scraping, caching per terms).
- [ ] No secrets in repo/client; token exchange server-side over HTTPS.
- [ ] Privacy policy + deletion contact live before submitting for Strava review.
- [ ] Brand screen: `Compatible with Strava` only; no logo, no endorsement copy.
- [ ] Production copy says description everywhere the old v5 mock said title.
- [ ] Mock button verified to make zero network calls (devtools: no requests
  on click).

## 10. Brand audit vs official Strava API Brand Guidelines (2026-10-10)

Source fetched 2026-10-10 from `https://developers.strava.com/guidelines/`
(page notes last revision 2025-09-29). Rules applied: (§1.1) Connect button
must be the official asset (orange/white, 48px height @1x) linking to
`strava.com/oauth/authorize` (or `.../oauth/mobile/authorize`); (§1.2) API
logos only in official orange/white/black, unmodified; (§2) no endorsement
implication, logos separate from and less prominent than the app name, never
as app icon, never modified/animated; (§3) links to Strava data must read
exactly `View on Strava` in bold, underline, or orange `#FC5200`; (§4)
plain-text factual references OK, never in the app name, Strava name not
larger than surrounding text and not more prominent than the app name, and
interoperability wording only `Powered by Strava` / `Compatible with Strava`.
Note: the guidelines govern logos and name use; they state no general ban on
red or gold UI text, so accent-color route art and CTA color are not violations.
All verdicts below cover the v6 mocks as built; every production TODO is listed
in §10.8. This audit appended by lane 05-strava without touching any page code.

### 10.1 connect.html — PASS (mock; production TODO open)

- Interoperability wording: `MOCK · Compatible with Strava` — allowed phrase
  (§4). No `powered by`, partnership, or sponsorship claim.
- Plain-text references (`written into its Strava description`, `official
  Strava OAuth flow`) are factual, same size as surrounding copy, and the
  mynextpr wordmark stays dominant (§4).
- No Strava logo art, no app-icon use, nothing modified (§1.2/§2 trivially met).
- Connect button is a custom-styled mock (`15px` bold, accent fill, no link,
  zero network by design) — NOT the official 48px asset. Acceptable only
  because it is a mock; see TODO-1.
- No links to Strava data on the page, so the `View on Strava` rule (§3) is N/A.

### 10.2 index.html — PASS (mock; production TODO open)

- `MOCK · Compatible with Strava` plain-text line (`.compat`, 13px — same size
  as surrounding copy, no badge, no logo). Footer states `Not endorsed by
  Strava`. No endorsement claim anywhere (§2/§4).
- No Connect button on this page (CTA routes to `picker.html`) — §1.1 N/A here.
- The `#fc5200` map-route stroke is decorative route art, not a data link and
  not logo art; no `View on Strava` links exist, so §3 is N/A.
- No logo, no app-name use of `Strava`.

### 10.3 picker.html — PASS (mock; production TODO open)

- `Strava description preview` is a factual plain-text label (§4).
- `Connect with Strava (mock)` is a custom button with no OAuth link and no
  network (by design). Acceptable as a mock; see TODO-1.
- No logo, no endorsement wording.

### 10.4 goal.html — PASS

- Sole reference is factual plain text (`writes to the Strava activity
  description, never the title`, plus a code comment). No compat label needed,
  no button, no logo, no endorsement claim, normal type sizes.

### 10.5 hero.html — PASS with note

- Body copy is factual plain text (`added to its Strava description`, `We never
  touch the Strava title`); no endorsement claim; no Connect button; no logo art.
- Note: the phone mock loads `assets/strava-before-5k.jpeg` (a screenshot-style
  asset with a poster fallback), not Strava logo art — not a §1.2/§2 violation
  as a mock. For production, prefer the generic SVG activity card pattern used
  in `index.html` or confirm screenshot use; see TODO-3.

### 10.6 manage.html — PASS (mock; production TODO open)

- `MOCK · Compatible with Strava` header plus footer `Compatible with Strava
  (no endorsement claimed)` — allowed phrase with explicit non-endorsement (§4).
- `Production uses the official Strava OAuth flow (read + activity:write)` is a
  factual statement, not an endorsement claim.
- Connect button is a custom mock with no OAuth link (by design); see TODO-1.
- No logo art anywhere.

### 10.7 watchboard.html — PASS / N/A (ops board, not user-facing)

- Coordinator-owned review board; only navigational text (`Strava connect`
  tour link, lane labels, `never the Strava title` footer rule). No button, no
  logo, no endorsement claim, no data links. Untouched by this lane.

### 10.8 Production logo-pack integration TODO (blocks Strava review, not mocks)

- TODO-1 (Connect button): download the official Connect-button pack from the
  guidelines page, serve the asset locally, and replace every mock Connect
  button (`connect.html`, `picker.html`, `manage.html`) with the official
  orange/white asset at 48px height (@2x 96px for retina), wired to
  `https://www.strava.com/oauth/authorize` (or the mobile endpoint).
- TODO-2 (API logos): no v6 page currently uses an API logo. If one is added,
  use only the official orange/white/black files, unmodified, kept separate
  from and less prominent than the mynextpr wordmark — never as the app icon.
- TODO-3 (data links & screenshots): no `View on Strava` link exists yet
  (zero instances repo-wide). Any future link to Strava data must use the exact
  text `View on Strava` with bold weight, underline, or `#FC5200`. Prefer the
  generic activity card over app-screenshot assets per §10.5.
- TODO-4 (copy freeze): keep `Compatible with Strava` as the only
  interoperability label; `hero-copy.md` already vetoes `powered by`,
  partnership, and endorsement phrasing — hold that veto through production.
