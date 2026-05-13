# Salon Max Platform Architecture V1

This document describes the bigger system shape for Salon Max when it grows beyond a single Pi on a desk.

The goal is to support:

- one business with one salon
- one business with many salons
- many businesses on the same platform
- local trading when internet is down
- cloud sync when internet returns
- licensing and subscription control
- business support, audit, export, and recovery
- provider analytics without unsafe hidden access patterns

## Core Principles

- every salon business gets its own account
- every business account is isolated from every other business account
- cloud is the master record for business data
- each till keeps a local working copy for speed and offline trading
- sync is event-driven, not whole-database copy/paste
- balances are tracked as ledgers, not just current totals
- support access must be explicit, role-based, and audited
- analytics access must be deliberate and documented, not a secret back door

## Tenant Model

Salon Max should be a multi-tenant platform.

Hierarchy:

- Platform
- Business Account
- Site
- Terminal Device
- Staff User

Each business account owns:

- company profile
- sites/salons
- terminals
- staff
- customers
- transactions
- package/course ledger
- pricing
- stock
- reporting
- subscription/licensing state

Suggested key fields:

### BusinessAccount

- `id`
- `name`
- `legal_name`
- `status`
- `timezone`
- `currency_code`
- `subscription_plan`
- `subscription_status`
- `created_at`
- `updated_at`

### Site

- `id`
- `business_account_id`
- `name`
- `code`
- `address`
- `timezone_override`
- `is_active`

### TerminalDevice

- `id`
- `business_account_id`
- `site_id`
- `device_name`
- `device_serial`
- `licence_key_id`
- `last_seen_at`
- `last_sync_at`
- `status`

## Data Ownership

Cloud should be the master for:

- customers
- courses / minutes / packages
- sales transactions
- staff accounts
- pricing and product catalogue
- stock rules and stock movements
- audit log
- device registrations
- subscription and licence records
- support/export history

Local tills should keep:

- active working customer cache
- local copy of products/pricing
- local queue and active bed state
- unsynced local events
- printer state
- hardware relay/opto state
- last valid licence token

## Recommended Storage Model

### Cloud

- PostgreSQL
- API service between tills and cloud database
- append-only event tables for high-risk business actions
- nightly backups plus point-in-time recovery

### Local Till

- SQLite
- one database per till device
- local event outbox table
- local inbound sync checkpoint

## Sync Design

Do not sync by comparing and overwriting full rows where avoidable.

Use:

- local write
- append event
- background upload
- cloud acceptance
- cloud fan-out to other sites

### Flow

1. Staff completes action on till.
2. Till writes the result to local SQLite immediately.
3. Till writes an event into `sync_outbox`.
4. Background sync sends events to cloud.
5. Cloud validates, persists, and assigns global ordering.
6. Other salons pull events since their last checkpoint.
7. Each salon applies those changes locally.

### Why Events Matter

Shared balances must be ledger-driven.

Example:

- `+90 minutes purchased`
- `-9 minutes used at Salon 1`
- `-6 minutes used at Salon 2`
- `+30 minutes manual goodwill adjustment`

This is safer than syncing a single `remaining_minutes` number.

## High-Risk Ledgers

These should be append-only with audit history:

- package/course minute changes
- account balance changes
- stock adjustments
- till cash movements
- manual admin corrections

Suggested ledger fields:

- `id`
- `business_account_id`
- `customer_id`
- `site_id`
- `terminal_id`
- `staff_user_id`
- `source_event_id`
- `entry_type`
- `delta_value`
- `balance_after`
- `notes`
- `created_at`

## Offline Trading Rules

The platform should be local-first, but not trust local copies forever.

### Allowed Offline

- customer search against local cache
- tanning sale
- package redemption
- product sale
- till open/close
- printing
- sunbed control

### Restricted Offline

- cross-site conflict resolution
- licence renewal
- cloud reporting
- central support actions

### Conflict Handling

Conflicts should be rare but planned for.

Examples:

- two sites use the same remaining minutes while both are offline
- one site edits customer details while another edits the same record

Rules:

- ledger events are never silently discarded
- cloud decides final accepted ordering
- conflicting customer profile fields use version/timestamp rules
- conflicting balance usage creates a flagged exception for review
- support/admin tools must expose these exceptions clearly

## Support and Admin Access

Do not build a secret back door.

Build a proper provider admin layer with:

- named support roles
- reason-for-access prompt
- tenant scope controls
- full audit logging
- optional customer-facing account setting for support consent

Suggested provider roles:

- `platform_support_readonly`
- `platform_support_operator`
- `platform_finance_admin`
- `platform_engineering_admin`

Every provider-side access should log:

- who accessed
- which business
- which customer or record
- what action was taken
- why it was done
- when it happened
- originating IP/session

### Break-Glass Support

Allow a controlled break-glass mode for urgent support cases.

Requirements:

- explicit reason entered
- elevated session time-limited
- actions audited
- visible in business audit log if desired

## Analytics Access

For analytics, build a provider reporting warehouse rather than a hidden data siphon.

Recommended model:

- operational cloud database remains the system of record
- analytics warehouse receives replicated/reporting data
- default dashboards use aggregated business metrics
- personally identifiable customer data is restricted

### Provider Analytics Levels

#### Level 1: Platform Metrics

Safe by default:

- active salons
- active terminals
- sync health
- sales volume totals
- feature usage
- printer usage
- relay/opto hardware event rates

#### Level 2: Business Metrics

Available to provider staff where commercially justified:

- per-business usage
- plan adoption
- churn risk
- hardware fault trends
- support burden

#### Level 3: Customer-Level Investigation

Only for support/debugging, not casual analytics:

- named customer history
- minute ledger
- transaction review
- sync incident investigation

This level should require:

- privileged role
- reason entry
- audit trail

### Important Rule

If you want broad cross-business analytics, default to aggregated or pseudonymised reporting.

If you want direct customer-level provider access across all businesses, your contracts, privacy notices, and internal controls need to support that.

So the product should be designed for:

- analytics by design
- support by design
- audit by design

Not:

- hidden universal access with no trace

## Export and Exit

Every business will expect support around data retrieval.

You should support:

- customer data export
- full business export
- transaction export
- ledger export
- support audit export

### Customer Export

Should include:

- profile
- visit history
- package/course ledger
- transactions
- notes/consents where appropriate

### Business Export

Should include:

- customers
- staff
- products
- pricing
- transactions
- till sessions
- package ledger
- stock ledger

Recommended export formats:

- CSV for tables
- JSON for full structured export

### Exit Flow

When a business leaves:

1. subscription cancelled
2. final export prepared
3. export downloaded and acknowledged
4. account enters retention period
5. data archived or deleted according to policy

## Licensing and Subscription Control

Each till should use a signed licence lease.

Recommended behaviour:

- cloud issues signed token per device
- token tied to device identity
- till stores token locally
- till renews token every few days
- short offline grace allowed
- no permanent offline use

Suggested states:

- `active`
- `grace`
- `expired`
- `suspended`

Suggested rules:

- normal renewal every 3 to 7 days
- offline grace 7 to 14 days depending on plan
- expired blocks new trading but may allow limited read-only access

## Security Baseline

- business-level tenant isolation in every table/query
- strong password rules for back office
- PIN plus role for tills
- TLS everywhere external
- at-rest backups encrypted
- admin actions audited
- secrets not stored in code
- device registration revocable

## Suggested Cloud Modules

- Auth and Tenant Service
- Device and Licensing Service
- Sync API
- Customer Service
- Ledger Service
- Reporting Service
- Support/Admin Console
- Export Service
- Analytics Pipeline

## Suggested Tables Beyond V1

Add these platform-level concepts:

### DeviceLicence

- `id`
- `business_account_id`
- `terminal_device_id`
- `licence_status`
- `signed_token`
- `issued_at`
- `expires_at`
- `last_check_in_at`

### SyncOutbox

- `id`
- `local_event_id`
- `event_type`
- `payload_json`
- `created_at`
- `sent_at`
- `acknowledged_at`
- `status`

### SyncInboxCheckpoint

- `id`
- `terminal_device_id`
- `last_cloud_event_id`
- `last_synced_at`

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

### SupportAccessEvent

- `id`
- `business_account_id`
- `support_user_id`
- `access_type`
- `reason`
- `started_at`
- `ended_at`

## Rollout Plan

### Phase A: Single Business, Single Cloud

- one business account
- one cloud database
- one local SQLite cache per till
- manual support tools
- signed licence lease

### Phase B: Multi-Site Sync

- shared customers across sites
- shared minute ledger
- event outbox/inbox sync
- conflict queue

### Phase C: Multi-Tenant Platform

- many businesses
- tenant-aware admin console
- self-service exports
- provider analytics
- support access controls

### Phase D: Provider Operations

- health dashboards
- sync repair tools
- device transfer tooling
- business billing integration
- retention/deletion workflows

## Recommended Decision

Build Salon Max as:

- multi-tenant
- cloud-master
- local-first
- event-synced
- ledger-driven
- auditable

And for the “back door” requirement, replace that idea with:

- a proper provider admin and analytics layer
- explicit permissions
- recorded support access
- aggregated analytics by default
- customer-level drill-down only when justified and logged

That gives you the control you need without creating a dangerous hidden access model that could come back to bite you later.
