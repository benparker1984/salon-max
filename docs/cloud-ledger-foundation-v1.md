# Cloud Ledger Foundation V1

This document explains the first cloud ledger tables added to Salon Max for customer money and customer minutes.

These tables are the beginning of the production-safe value model. They exist so Salon Max can move away from trusting a single mutable number on a till database.

## Why This Exists

Customer value is too risky to model only as:

- `account_balance`
- `package_minutes`
- `remaining_minutes`

Those are useful summaries, but not safe enough as the only record.

The safer model is:

- append ledger entries
- derive current balance from that history
- keep a summary table only as a convenience cache

## Tables Added

### `cloud_customers`

Basic cloud customer identity per salon business.

Main purpose:

- give the ledgers a stable customer reference
- support future sync, support tools, and customer portal work

### `cloud_customer_balance_ledger`

Money-value history for customer accounts.

Use this for entries like:

- account top-up
- goodwill credit
- refund reversal
- manual correction
- balance redemption if that ever exists

Key fields:

- `business_account_public_id`
- `customer_public_id`
- `site_public_id`
- `terminal_device_public_id`
- `staff_user_public_id`
- `source_event_id`
- `entry_type`
- `delta_amount`
- `balance_after`
- `currency_code`
- `created_at`

### `cloud_customer_minute_ledger`

Minutes/package history for tanning value.

Use this for entries like:

- package purchase
- minutes top-up
- session redemption
- manual minute adjustment
- cross-site minute correction

Key fields:

- `business_account_public_id`
- `customer_public_id`
- `site_public_id`
- `terminal_device_public_id`
- `staff_user_public_id`
- `source_event_id`
- `package_code`
- `entry_type`
- `delta_minutes`
- `minutes_after`
- `created_at`

### `cloud_customer_balance_summary`

Current money balance cache.

Important:

- this is a convenience table
- it is not the authority
- the ledger remains the authority

### `cloud_customer_minute_summary`

Current available minutes cache.

Important:

- this is also a convenience table
- it should be rebuildable from the ledger if needed

## Design Rule

When the application is fully wired:

1. write ledger entry
2. update summary table
3. keep `source_event_id` so retries stay idempotent

Do not update summaries without a corresponding ledger entry.

## Entry Types

Suggested balance entry types:

- `account_topup`
- `manual_credit`
- `manual_debit`
- `refund`
- `correction`

Suggested minute entry types:

- `minutes_purchased`
- `minutes_redeemed`
- `manual_minutes_credit`
- `manual_minutes_debit`
- `package_awarded`
- `package_correction`

## Multi-Site Safety

These ledgers are business-level, not single-site-level.

That means:

- a customer can be shared across multiple sites if the business rules allow it
- the ledger can still record which site and terminal made the change
- cross-site support problems remain traceable

This is the right base for later linked-site customer sharing.

## What This Does Not Yet Do

This step only adds the cloud schema foundation.

It does not yet:

- sync customers into these cloud tables
- write till sales into the cloud ledgers
- rebuild the summary tables automatically
- expose ledger views in the provider console

Those are the next steps after the schema foundation.

## Next Follow-On Work

1. add write services for balance and minute ledger entries
2. connect relevant till events to those services
3. add provider-side ledger inspection screen
4. add archive-safe export and dispute tooling
