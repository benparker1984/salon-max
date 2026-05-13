# Production Data Safety V1

This document sets the minimum safety rules for Salon Max once real salon businesses, real customer balances, and real monetary value are at stake.

It is not enough for the system to be convenient or fast. It must be recoverable, auditable, and hard to corrupt silently.

## Goal

Protect:

- customer balances
- minutes and packages
- sales and refunds
- staff actions that affect value
- site and terminal identity
- sync integrity across tills and salons

## Core Safety Principle

The Raspberry Pi is an edge device, not the master source of truth.

The permanent model is:

- `Salon Max cloud database` = master record
- `Pi local SQLite` = working offline copy
- `ledger and event history` = final authority for high-risk values

## Production Data Layout

### Cloud Master

Store centrally in hosted production infrastructure:

- business accounts
- sites
- terminals
- staff identities
- customers
- customer ledger
- transactions
- package and minutes history
- licence records
- sync events
- support and audit history

Recommended core database:

- `PostgreSQL`

### Local Pi Copy

Store locally on each Pi:

- current working customer cache
- local sync outbox
- local config cache
- active till session state
- relay and hardware runtime state
- last valid licence lease

Local storage is for continuity, not final authority.

## High-Risk Data Must Be Ledger-Based

Do not trust a single current-value field for anything with customer value attached.

Examples:

- `remaining_minutes`
- `package_balance`
- `account_balance`

These can exist as convenience values, but the real protection must come from append-only history.

### Safe Model

Store value changes as events or ledger entries:

- `+30 minutes purchased`
- `-6 minutes redeemed at site A`
- `-9 minutes redeemed at site B`
- `+10 goodwill adjustment`
- `-1 package session used`

This allows:

- reconstruction
- dispute resolution
- fraud investigation
- recovery after device failure

## Backup Rules

### Database Backups

For the cloud production database:

- automatic daily full backups
- point-in-time recovery if available
- tested restore procedure
- backup retention policy

Recommended starting retention:

- daily backups kept for 30 days
- weekly backups kept for 12 weeks
- monthly backups kept for 12 months

### Off-Platform Copies

Backups should not live only on the same host as production.

Keep copies in separate managed storage.

### Local Pi Risk

Do not depend on Pi SD cards as a reliable long-term archive.

They can fail, corrupt, or be lost.

## Restore Rules

You need two restore paths:

### Full Platform Restore

Used when the production database or host fails.

Must recover:

- all tenants
- all ledgers
- all device and site identity
- all sync events needed for continuity

### Single-Business Recovery

Used when one salon business has a support disaster or data dispute.

Must support:

- ledger inspection
- export of one tenant
- recovery investigation without affecting other tenants

## Tenant Isolation

Every salon business must be isolated from every other salon business.

Isolation rules:

- every row carries `business_account_id`
- every API path validates business scope
- staff access is tenant-scoped
- customer portal access is tenant-scoped
- support access is explicit and audited

Provider support must be able to inspect when justified, but not through a hidden back door.

## Audit Rules

The system should always be able to answer:

- who changed this value
- when it changed
- from which terminal or site
- why it changed
- what the balance was before and after

That means keeping audit history for:

- manual customer adjustments
- package/minute changes
- refunds
- licence changes
- pairing and replacement actions
- site and terminal admin changes

## Sync Safety Rules

### Never Sync By Blind Overwrite

Do not let one till simply replace another till's values.

Use:

- local outbox
- cloud acceptance
- ordered replay
- ledger conflict review when needed

### Acknowledgement Rule

A local event should only be marked successful when the cloud explicitly accepts it.

### Duplicate Protection

Every sync event needs an idempotent unique key so retrying does not duplicate monetary changes.

## Pi Failure Model

Assume eventually:

- an SD card dies
- a Pi is stolen
- a till app crashes during trading
- internet drops during a sale

The system should still protect value.

### When A Pi Dies

The recovery path should be:

1. provision replacement Pi
2. pair it to the correct terminal or replacement flow
3. pull latest business config
4. replay or rebuild state from cloud
5. continue trading

This is why cloud master data matters.

## Archive Vs Delete

Operational entities should generally archive, not hard-delete.

Examples:

- sites
- terminals
- business records

Why:

- history matters
- support cases need old context
- hard deletion can damage ledgers and reports

Live UI should hide archived entities by default, but recovery and support tools should still see them.

## Security Minimums

Before live rollout:

- TLS for all cloud traffic
- hashed staff credentials
- signed device leases
- secret management outside source code
- tenant-scoped permissions
- audit logging for privileged support access

## Monitoring Minimums

At production level you should be able to see:

- failed sync rate
- stale licence check-ins
- terminals not seen recently
- repeated event retries
- database backup success/failure
- restore test history

## Operational Checklist Before Live Customers

Do not launch with real money/value until all of this is true:

- cloud database is the master
- backups run automatically
- restore procedure is written and tested
- ledger model is in place for balances/minutes
- event retries are idempotent
- tenant isolation is enforced
- archive rules are clear
- support and audit access is logged

## Recommended Next Implementation Order

1. formalize cloud ledger tables
2. define backup and restore runbook
3. add support/audit actions to provider console
4. improve sync conflict visibility
5. only then move further into customer self-service payments
