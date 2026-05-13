# Cloud Ledger Write Path V1

This document describes the first live write path into the new Salon Max cloud ledger tables.

## What Is Live In This Step

When `POST /v1/sync/events/push` accepts a brand-new till event, the cloud now projects certain event types into the ledger tables.

Current live projection:

- `package_sale` -> writes to `cloud_customer_minute_ledger`
- `tanning_sale` with `account_minutes_used > 0` -> writes to `cloud_customer_minute_ledger`

## What This Means

If a till sends:

- a package/course purchase
- or a tanning sale that consumes account minutes

the cloud now does more than just store the raw sync event. It also:

1. ensures a cloud customer stub exists
2. writes a minute ledger entry
3. updates the minute summary cache

## Current Entry Mapping

### Package Sale

Source:

- `transaction.completed`
- `transaction_type = package_sale`

Projection:

- ledger `entry_type = minutes_purchased`
- `delta_minutes = minutes_included`
- summary `minutes_available += minutes_included`

### Tanning Sale Using Account Minutes

Source:

- `transaction.completed`
- `transaction_type = tanning_sale`
- `account_minutes_used > 0`

Projection:

- ledger `entry_type = minutes_redeemed`
- `delta_minutes = -account_minutes_used`
- summary `minutes_available -= account_minutes_used`

## Idempotency Rule

Projection only happens when the sync event is newly inserted into `cloud_sync_events`.

If the same till event is retried later:

- the cloud event is recognized as existing
- the ledger projection does not run again

This prevents duplicate minute credits or redemptions from retries.

## Customer Identity In This Step

The current write path uses a deterministic cloud customer stub ID based on:

- `business_account_public_id`
- local `customer_id`

This is only the first bridge.

Later, customer sync should replace these minimal stubs with fuller cloud customer records.

## What Is Not Live Yet

Not yet projected:

- retail sales
- manual support adjustments
- refunds
- account money top-ups from a proper synced event
- back-office-only customer changes

The money ledger tables exist, but should only be written when the upstream source events are in place and trustworthy.

## Next Follow-On Work

1. add synced customer identity enrichment
2. add explicit balance/top-up cloud events
3. project refunds and manual corrections into ledgers
4. expose customer ledger inspection in the provider console
