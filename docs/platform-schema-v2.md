# Salon Max Platform Schema V2

This document turns the platform architecture into a more concrete schema plan.

It is not a final migration file yet. It is the next design layer between:

- the current single-business local schema
- and the future cloud + offline-sync platform

## Objectives

Schema V2 should support:

- many businesses on one platform
- many salons per business
- one or more tills per salon
- cloud master data
- local offline trading
- reliable sync
- support/audit access
- device licensing
- analytics/reporting

## Split The Data Model

Salon Max should be designed as two related schemas:

### 1. Cloud Schema

This is the source of truth.

It stores:

- tenants/businesses
- sites
- devices
- customers
- staff
- transactions
- ledgers
- products/pricing
- support/audit
- subscription/licensing
- sync event log

### 2. Local Till Schema

This is the offline working copy on each device.

It stores:

- local copy of current business data
- active bed state
- local queue state
- local till session state
- local event outbox
- sync checkpoint
- current device licence lease

## Cloud Core Tables

### BusinessAccount

- `id`
- `public_id`
- `name`
- `legal_name`
- `status`
- `timezone`
- `currency_code`
- `country_code`
- `created_at`
- `updated_at`

Notes:

- `public_id` should be safe to expose in APIs
- `status` could be `active`, `trial`, `suspended`, `closed`

### BusinessSettings

- `id`
- `business_account_id`
- `business_name`
- `receipt_footer_text`
- `phone`
- `email`
- `address_line_1`
- `address_line_2`
- `city`
- `postcode`
- `vat_number`
- `logo_asset_id`
- `updated_at`

### Site

- `id`
- `business_account_id`
- `public_id`
- `name`
- `code`
- `address_line_1`
- `address_line_2`
- `city`
- `postcode`
- `phone`
- `email`
- `is_active`
- `created_at`
- `updated_at`

### TerminalDevice

- `id`
- `business_account_id`
- `site_id`
- `public_id`
- `device_name`
- `device_serial`
- `hardware_fingerprint`
- `app_version`
- `status`
- `last_seen_at`
- `last_sync_at`
- `created_at`
- `updated_at`

### StaffUser

- `id`
- `business_account_id`
- `public_id`
- `first_name`
- `last_name`
- `display_name`
- `pin_code_hash`
- `role_code`
- `is_active`
- `created_at`
- `updated_at`

### StaffSiteAccess

- `id`
- `business_account_id`
- `staff_user_id`
- `site_id`
- `created_at`

## Customer Tables

### Customer

- `id`
- `business_account_id`
- `public_id`
- `customer_number`
- `account_number`
- `first_name`
- `last_name`
- `phone`
- `email`
- `birthday`
- `marketing_opt_in`
- `notes`
- `is_active`
- `created_at`
- `updated_at`

### CustomerBalanceLedger

This replaces any unsafe “just store current balance” approach.

- `id`
- `business_account_id`
- `customer_id`
- `site_id`
- `terminal_device_id`
- `staff_user_id`
- `transaction_id`
- `source_event_id`
- `entry_type`
- `delta_amount`
- `balance_after`
- `created_at`
- `notes`

### CustomerMinuteLedger

This becomes the real cross-site truth for tanning minutes/courses.

- `id`
- `business_account_id`
- `customer_id`
- `site_id`
- `terminal_device_id`
- `staff_user_id`
- `transaction_id`
- `source_event_id`
- `package_product_id`
- `entry_type`
- `delta_minutes`
- `minutes_after`
- `created_at`
- `notes`

### CustomerMinuteBalance

Optional materialized convenience table for quick lookup.

- `customer_id`
- `business_account_id`
- `minutes_available`
- `updated_at`

Important:

- this is a cached summary
- the ledger remains the true source

## Product and Pricing Tables

### ProductGroup

- `id`
- `business_account_id`
- `name`
- `sort_order`
- `is_active`

### RetailProduct

- `id`
- `business_account_id`
- `group_id`
- `name`
- `sku`
- `size_label`
- `unit_label`
- `price`
- `commission_rate`
- `is_active`
- `created_at`
- `updated_at`

### StockLedger

- `id`
- `business_account_id`
- `site_id`
- `product_id`
- `staff_user_id`
- `transaction_id`
- `source_event_id`
- `entry_type`
- `delta_quantity`
- `quantity_after`
- `created_at`
- `notes`

### PackageProduct

- `id`
- `business_account_id`
- `name`
- `code`
- `minutes_included`
- `price`
- `validity_days`
- `is_active`
- `created_at`
- `updated_at`

### PricingRule

- `id`
- `business_account_id`
- `site_id`
- `device_id`
- `price_per_minute`
- `starts_at`
- `ends_at`
- `is_active`
- `created_at`
- `updated_at`

## Transaction Tables

### Transaction

- `id`
- `business_account_id`
- `site_id`
- `terminal_device_id`
- `staff_user_id`
- `customer_id`
- `transaction_number`
- `transaction_type`
- `status`
- `subtotal_amount`
- `discount_amount`
- `total_amount`
- `currency_code`
- `notes`
- `created_at`
- `updated_at`

### TransactionLine

- `id`
- `business_account_id`
- `transaction_id`
- `line_type`
- `product_code`
- `description`
- `quantity`
- `unit_price`
- `line_total`
- `device_id`
- `tanning_minutes`

### TransactionPayment

- `id`
- `business_account_id`
- `transaction_id`
- `payment_type`
- `amount`
- `reference_type`
- `reference_id`
- `created_at`

## Till and Bed Operation Tables

### TillSession

- `id`
- `business_account_id`
- `site_id`
- `terminal_device_id`
- `opened_by_user_id`
- `closed_by_user_id`
- `opened_at`
- `closed_at`
- `opening_float`
- `expected_cash`
- `counted_cash`
- `variance`
- `status`
- `closing_notes`

### TillMovement

- `id`
- `business_account_id`
- `till_session_id`
- `movement_type`
- `amount`
- `reason`
- `linked_transaction_id`
- `created_by_user_id`
- `created_at`

### QueueBooking

- `id`
- `business_account_id`
- `site_id`
- `terminal_device_id`
- `device_id`
- `customer_id`
- `transaction_id`
- `minutes`
- `payment_method`
- `status`
- `created_at`
- `updated_at`

### ActiveSession

- `id`
- `business_account_id`
- `site_id`
- `terminal_device_id`
- `device_id`
- `customer_id`
- `transaction_id`
- `phase`
- `minutes`
- `started_at`
- `expected_end_at`
- `status`
- `updated_at`

### DeviceConfig

- `id`
- `business_account_id`
- `site_id`
- `device_id`
- `relay_output_pin`
- `trigger_output_pin`
- `feedback_input_pin`
- `prep_minutes`
- `cooldown_minutes`
- `auto_start_after_prep`
- `is_active`
- `updated_at`

## Sync Tables

These are essential for offline-first rollout.

### CloudEvent

This is the platform-wide ordered event stream.

- `id`
- `business_account_id`
- `site_id`
- `terminal_device_id`
- `event_type`
- `entity_type`
- `entity_id`
- `payload_json`
- `created_by_user_id`
- `created_at`

### LocalSyncOutbox

Local till table.

- `id`
- `local_event_uuid`
- `business_account_id`
- `site_id`
- `terminal_device_id`
- `event_type`
- `payload_json`
- `status`
- `attempt_count`
- `last_attempt_at`
- `created_at`
- `acknowledged_at`

### LocalSyncCheckpoint

Local till table.

- `id`
- `terminal_device_id`
- `last_cloud_event_id`
- `last_synced_at`

### SyncConflict

Cloud table for exceptions that need review.

- `id`
- `business_account_id`
- `event_id`
- `conflict_type`
- `entity_type`
- `entity_id`
- `status`
- `details_json`
- `created_at`
- `resolved_at`
- `resolved_by_user_id`

## Licensing Tables

### SubscriptionAccount

- `id`
- `business_account_id`
- `plan_code`
- `billing_status`
- `trial_ends_at`
- `current_period_ends_at`
- `grace_ends_at`
- `created_at`
- `updated_at`

### DeviceLicence

- `id`
- `business_account_id`
- `terminal_device_id`
- `licence_status`
- `signed_token`
- `issued_at`
- `expires_at`
- `last_check_in_at`
- `revoked_at`

### LocalLicenceLease

Local till table.

- `id`
- `terminal_device_id`
- `licence_status`
- `signed_token`
- `issued_at`
- `expires_at`
- `last_verified_at`

## Audit and Support Tables

### AuditEvent

- `id`
- `business_account_id`
- `actor_type`
- `actor_id`
- `action_type`
- `entity_type`
- `entity_id`
- `reason`
- `metadata_json`
- `created_at`

### SupportUser

- `id`
- `email`
- `name`
- `role_code`
- `is_active`
- `created_at`

### SupportAccessEvent

- `id`
- `business_account_id`
- `support_user_id`
- `access_type`
- `reason`
- `started_at`
- `ended_at`
- `metadata_json`

### ExportJob

- `id`
- `business_account_id`
- `requested_by_actor_type`
- `requested_by_actor_id`
- `export_type`
- `status`
- `file_uri`
- `created_at`
- `completed_at`

## Local Till Schema Additions

The current local SQLite app can evolve into the full offline till by adding:

- `local_sync_outbox`
- `local_sync_checkpoint`
- `local_licence_lease`
- `device_registration`
- `bed_feedback_event_log`

### DeviceRegistration

- `id`
- `business_account_id`
- `site_id`
- `terminal_device_id`
- `device_serial`
- `hardware_fingerprint`
- `registered_at`

### BedFeedbackEventLog

- `id`
- `device_id`
- `phase`
- `feedback_state`
- `relay_state`
- `trigger_state`
- `created_at`

This helps with:

- support diagnostics
- proving safety sequences
- hardware debugging

## Suggested Indexing Rules

At minimum, index:

- every `business_account_id`
- every `site_id`
- every `customer_id`
- every `transaction_number`
- every ledger table on `(business_account_id, customer_id, created_at)`
- sync tables on status and created time
- device licence by `(terminal_device_id, expires_at)`

## Migration Strategy

Do not try to jump directly from the current local-only schema to full cloud sync in one go.

### Step 1

Add business/tenant awareness to the current conceptual schema.

### Step 2

Move customer minutes and account money to proper ledgers.

### Step 3

Introduce local outbox and cloud event log.

### Step 4

Introduce device licence lease and cloud check-in.

### Step 5

Add provider support/audit tables and admin tooling.

## Immediate Next Build Order

The best next build sequence is:

1. Add `business_account_id` to the conceptual model everywhere.
2. Add `customer_minute_ledger` and stop thinking in “one number only”.
3. Add `local_sync_outbox` to the till SQLite database.
4. Define cloud API contracts for:
   - customer sync
   - transaction push
   - minute ledger push
   - config pull
5. Add `device_licence` and `local_licence_lease`.
6. Add audit/support tables before real rollout.

## Final Position

Schema V2 should keep the current app practical while preparing for:

- 1 salon now
- 3 salons synced next
- 100 salons later

The important shift is:

- from local transactional tables only
- to a tenant-aware, ledger-driven, sync-aware platform schema

without losing the local speed and offline resilience the Pi tills need.
