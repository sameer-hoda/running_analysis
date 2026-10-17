# Webhook Receiver — Design Memo (Proposal)

Status: PROPOSAL ONLY. Nothing in this memo is implemented. No code, no
receiver endpoint, no subscription, and no network calls exist. This memo
describes intended behavior so a later lane can review and approve it
before any implementation begins.

## 1. Purpose

Propose a webhook receiver that wakes the engine when a connected
runner finishes (or deletes) a relevant activity, so the race-day
follow-up does not depend solely on polling.

## 2. Proposed event types

Only the following event classes would be handled; everything else
would be acknowledged and ignored:

- Activity created or finished — candidate trigger for the post-race flow.
- Activity updated (title, time, or distance changed) — candidate
  re-evaluation trigger when the recorded result materially changes.
- Activity deleted — candidate trigger to withdraw or correct a
  previously recorded result.
- Authorization revoked (deauthorization) — proposed trigger to purge
  that athlete's tokens and race/goal mapping, consistent with the
  deletion commitment in the Strava plan.

No other event classes (kudos, comments, segments, clubs, followers)
would be subscribed to or stored.

## 3. Proposed verification

- Subscription handshake: the receiver would answer the provider's
  one-time challenge only on the dedicated callback path, and the
  subscription would be created out of band by an operator, never
  self-registered by the running app.
- Per-delivery authenticity: every incoming delivery would be checked
  against the shared subscription secret before any parsing or state
  change. Deliveries that fail verification would be rejected without
  further processing and counted for monitoring only.
- Transport: the callback would accept deliveries only over encrypted
  transport; plain-HTTP deliveries would be refused.
- Scope discipline: the receiver would hold no tokens and perform no
  privileged reads; its only job would be to validate, classify, and
  enqueue.

## 4. Proposed idempotency (no-double-stamp)

- Each delivery carries a provider event identity. The receiver would
  record that identity in a deduplication log before acting on it, and
  any repeat delivery of the same identity would be acknowledged as a
  duplicate with no further effect.
- Stamping (the "race recorded" mark) would be conditional: the engine
  would stamp an activity result only if no stamp already exists for
  that athlete-plus-activity pair. A duplicate or retried delivery can
  therefore never produce a second stamp.
- Out-of-order deliveries (e.g., an update arriving before the create)
  would resolve to a single current state per activity, not to
  sequential stamps: the last validated description of the activity
  wins, and earlier ones are superseded, never appended.
- Backfill or replay of old events would be bounded by the same rule:
  replays referencing an already-stamped pair are no-ops.

## 5. Proposed failure handling

- Verification failures: reject immediately, log only the delivery
  metadata (never activity contents), no retry requested.
- Transient downstream outages (queue or store unavailable): hold the
  delivery unacknowledged where the provider protocol permits a retry,
  with bounded retries and backoff; after the bound, park the delivery
  identifier in a dead-letter record for operator review rather than
  retrying forever.
- Poison or malformed deliveries: acknowledge-and-drop after logging
  the rejection reason, so one bad payload cannot block the queue.
- Duplicate storms (provider retry floods): absorbed by the
  deduplication log; no additional work per repeat.
- Full loss of the deduplication log: treated as a stop-the-line
  incident — stamping would pause until the log is restored, because
  the no-double-stamp guarantee cannot be upheld without it.
- Monitoring (proposed): counts of received, verified, duplicated,
  rejected, and dead-lettered deliveries, plus age of the oldest
  unprocessed delivery.

## 6. Proposed data stored

Minimal by design. For each delivery, at most:

- Provider event identity and receipt timestamp (deduplication log).
- Classification outcome (handled class vs. ignored, and reason).
- For handled activity events: athlete identifier, activity
  identifier, event class, and activity timestamps relevant to
  race matching. No activity contents beyond what matching needs.
- For deauthorization events: athlete identifier and purge timestamp.
- Rejection metadata for failed verifications (time, reason code) —
  never the payload body.

Nothing else would be persisted: no tokens (the receiver holds none),
no kudos/comments/segments/followers, no analytics derived from
activity contents.

## 7. Explicit non-goals

- No polling changes in this memo; polling remains the fallback until
  a later lane approves and implements webhooks.
- No token storage, refresh, or vault design here.
- No fetch or write calls to the provider from the receiver.
- No retention beyond the deduplication window and the purge audit
  record; exact windows are left for the implementing lane to propose.

## 8. Approval gate

This memo stops here by instruction. No implementation follows until
the coordinator approves the proposal, in whole or with amendments.
