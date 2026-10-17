# v6 Backend Options — Strava Integration (proposal memo, description-only)

Status: PROPOSAL ONLY — no code, no secrets, no network calls. Nothing in this
memo is implemented or approved. Compatible with Strava only (no other
providers considered). Brand wording per plan: `Compatible with Strava` only;
no endorsement, partnership, or logo claims. Source of truth for the consented
flow: `v6/strava-plan.md`; mock reference: `v6/connect.html` (mock only).

## 0. What this memo decides (and does not)

- Proposes backend shape options for production Strava wiring: OAuth SSO flow,
  webhook receiver, token storage, scopes, privacy/deletion, rate-limit, and
  app-review readiness.
- Does NOT authorize implementation. Stop at the approval gate (§8).
- Does NOT introduce code, config, secrets, migrations, or endpoints.

## 1. OAuth SSO flow (proposed)

- Proposed flow: user picks an upcoming race first, then clicks connect, then
  grants consent on strava.com via the official OAuth authorization redirect,
  then the server completes the code exchange over HTTPS and stores tokens.
- Proposed redirect handling: one allow-listed callback URI; the authorization
  request carries only `client_id`, `redirect_uri`, `response_type=code`,
  `scope=read,activity:write`, and `approval_prompt=force` on first connect.
- Proposed decline path: cancel/decline stores nothing and attempts no writes.
- Proposed disconnect path: in-app disconnect revokes and deletes stored
  tokens and stops all future writes immediately.
- Effort note: small — one callback handler plus one exchange routine, both
  server-side; main cost is review and secret-handling setup, not logic.
- Risk note: medium — any client-side leak of the exchange (client secret or
  tokens in browser/logs) is a finding; mitigation is to keep the entire
  exchange server-side over HTTPS with no token exposure to the client.

## 2. Webhook receiver (proposed)

- Proposed subscription: subscribe to Strava webhooks for the app's own
  activity-create events and for deauthorization notices; verify the subscription
  callback per Strava's verification handshake (description only, no payloads
  recorded here).
- Proposed receiver behavior: on activity-create, verify ownership (activity
  athlete matches token athlete), then queue at most one countdown refresh of
  the activity description; on deauthorization notice, purge that athlete's
  stored record within 7 days.
- Proposed non-behavior: no polling loops, no backfill of other athletes'
  history, no writes to clubs/friends/tagged activities, never activity title.
- Effort note: small-to-medium — one receiver endpoint plus a small queue;
  verification handshake and idempotency handling are the bulk of the work.
- Risk note: medium — spoofed or replayed events could trigger wrong writes;
  mitigation is signature/handshake verification plus the per-write ownership
  check before any update call.

## 3. Token storage (proposed)

- Proposed stored data (minimum): OAuth access + refresh tokens encrypted at
  rest, selected race + goal, Strava athlete ID. Nothing else — no followers,
  kudos, segments, or activity contents beyond the write itself.
- Proposed lifecycle: short-lived access tokens, refresh on expiry, re-prompt
  consent on revoked/expired grants; tokens used solely for the consented
  description updates; never logged, never sent to the browser, never committed.
- Proposed deletion: in-app disconnect deletes tokens + race/goal mapping
  immediately; deauthorization webhook triggers purge within 7 days.
- Effort note: small — encrypted store plus encrypt/decrypt-on-use; main cost
  is key management and deletion-path testing.
- Risk note: high — token store is the highest-value target; mitigation is
  encryption at rest, least-access server handling, no client exposure, and an
  auditable delete path.

## 4. Scopes: `read` + `activity:write` (proposed, minimum)

- Proposed request: exactly `read` and `activity:write`; no `read_all`,
  `profile:read_all`, `activity:read_all`, or broader scopes.
- Proposed rationale: `read` covers baseline visibility; `activity:write` is
  the narrowest scope permitting description updates on the user's own
  activities.
- Proposed consent copy: fine print adjacent to the CTA states scopes in plain
  words (e.g. reads profile, updates descriptions on own activities only),
  plus what is written, what is never touched (title), own-only rule, and how
  to disconnect/delete.
- Effort note: trivial — scope string plus adjacent copy; cost is review only.
- Risk note: low-to-medium — requesting more than the minimum risks app-review
  rejection; mitigation is to hold the two-scope minimum and re-review rather
  than widen if the API ever narrows.

## 5. Privacy and deletion (proposed)

- Proposed policy: no sale or sharing of Strava data; no analytics on activity
  contents; use limited to the consented countdown description updates.
- Proposed deletion: in-app disconnect deletes immediately; documented
  data-deletion contact; deauthorization purges within 7 days.
- Proposed prerequisite: privacy policy + deletion instructions must ship
  before Strava app review is submitted.
- Effort note: small — policy text plus delete path; cost is legal/copy review.
- Risk note: medium — missing policy or a broken delete path blocks approval
  and erodes trust; mitigation is shipping both before review and testing the
  disconnect path end to end.

## 6. Rate-limit and app-review readiness (proposed)

- Proposed rate behavior: daily per-user writes bounded (one countdown refresh
  per new activity, no polling); backoff on HTTP 429; respect rate-limit
  response headers; no scraping; cache per Strava terms.
- Proposed pre-review checklist: scopes are exactly the two minimum; no code
  path sets activity name/title (automated grep in CI); ownership check on
  every write; connect gated on upcoming-race selection; fine print adjacent
  to CTA; disconnect + deletion works; no secrets in repo/client; privacy
  policy live; brand screen says `Compatible with Strava` only; production
  copy says description everywhere; mock button verified to make zero network
  calls.
- Effort note: small — checklist plus backoff behavior; cost is verification,
  not new systems.
- Risk note: low-to-medium — bursty writes or title-touching code risk
  throttling or rejection; mitigation is the bounded write budget plus the
  title-grep CI gate.

## 7. Options summary

| Option | Shape | Effort | Risk |
|---|---|---|---|
| A — Webhook-driven refresh (Recommended) | Subscribe, queue one description refresh per new own activity, purge on deauthorization | Small-medium | Medium, contained by verification + ownership check |
| B — Connect-time only, no receiver | Exchange tokens at connect, write only in direct response to user action, no background receiver | Smallest | Lower ops risk, but loses automatic per-run refresh and still needs delete path |

- Recommendation basis (proposal only): Option A matches the consented
  per-run countdown behavior with bounded writes; Option B is simpler but
  leaves the refresh story incomplete. Either way, scopes, storage, privacy,
  and brand constraints above hold unchanged.

## 8. Approval gate — STOP HERE

- No implementation, no endpoint, no schema, no secret, and no network call
  is authorized by this memo.
- Do not proceed past this point without explicit coordinator approval.
