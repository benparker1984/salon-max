# Salon Max Platform Implementation Plan V1

This document is the first practical build plan for turning Salon Max from a local Pi till into a real multi-tenant platform.

It follows:

- [platform-architecture-v1.md](C:\Users\benpa\Documents\Codex\Salon-Max\docs\platform-architecture-v1.md)
- [platform-schema-v2.md](C:\Users\benpa\Documents\Codex\Salon-Max\docs\platform-schema-v2.md)
- [platform-api-v1.md](C:\Users\benpa\Documents\Codex\Salon-Max\docs\platform-api-v1.md)

## Goal

Build the smallest useful cloud platform that:

- knows which business each till belongs to
- issues and renews device licences
- sends the correct business branding/config to each till
- accepts local till events for later cross-site sync
- keeps the current Pi till usable while the cloud side grows

## Recommended Tech Stack

### Cloud API

- Python `FastAPI`
- `Pydantic` for request/response validation
- `SQLAlchemy` or `SQLModel` for ORM/data access
- `PostgreSQL` for cloud database
- `Alembic` for migrations

Why:

- close to your current Python world
- fast to build
- clear request validation
- good async/background options later

### Background Jobs

Start simple:

- API writes events directly
- sync pull is request-driven

Later:

- `RQ` or `Celery` for export jobs, analytics feeds, and heavier background work

### Auth and Tokens

- signed JWT access tokens
- separate token types:
  - `device`
  - `staff`
  - `support`
- token signing via server-side secret/private key

### Local Till

- keep `SQLite`
- add sync/licence tables inside the current local DB
- keep current `PySide6` till app

## First Delivery Scope

Do not try to build everything at once.

### Phase 2A

Build only:

1. business account awareness
2. terminal device registration
3. licence check-in
4. config pull
5. local sync outbox table
6. one event push endpoint

That gives you:

- a licensed Pi
- tenant-aware branding
- future sync foundation

## Recommended Project Layout

```text
salonmax-platform/
  app/
    api/
      routes/
        devices.py
        licences.py
        config.py
        sync.py
    core/
      settings.py
      security.py
      database.py
    models/
      business.py
      site.py
      terminal.py
      licence.py
      sync.py
    schemas/
      devices.py
      licences.py
      config.py
      sync.py
    services/
      device_service.py
      licence_service.py
      config_service.py
      sync_service.py
  migrations/
  tests/
```

## First Cloud Tables To Build

Start with the minimum required to let one Pi identify itself and receive business settings.

### BusinessAccount

- `id`
- `public_id`
- `name`
- `status`
- `timezone`
- `currency_code`
- `created_at`
- `updated_at`

### BusinessSettings

- `id`
- `business_account_id`
- `business_name`
- `phone`
- `email`
- `address_line_1`
- `address_line_2`
- `city`
- `postcode`
- `receipt_footer_text`
- `updated_at`

### Site

- `id`
- `business_account_id`
- `public_id`
- `name`
- `code`
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
- `status`
- `last_seen_at`
- `last_sync_at`
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
- `updated_at`

### CloudEvent

- `id`
- `business_account_id`
- `site_id`
- `terminal_device_id`
- `event_type`
- `entity_type`
- `entity_id`
- `payload_json`
- `created_at`

## First Local Till Changes

Keep the current local schema and add only what is needed.

### local_sync_outbox

- `id integer primary key autoincrement`
- `local_event_uuid text not null unique`
- `event_type text not null`
- `payload_json text not null`
- `status text not null default 'pending'`
- `attempt_count integer not null default 0`
- `last_attempt_at text`
- `created_at text not null default current_timestamp`
- `acknowledged_at text`

### local_sync_checkpoint

- `id integer primary key autoincrement`
- `last_cloud_event_id integer not null default 0`
- `last_synced_at text`

### local_licence_lease

- `id integer primary key autoincrement`
- `terminal_device_public_id text not null`
- `licence_status text not null`
- `signed_token text not null`
- `issued_at text not null`
- `expires_at text not null`
- `last_verified_at text not null`

### local_device_identity

- `id integer primary key autoincrement`
- `business_account_public_id text`
- `site_public_id text`
- `terminal_device_public_id text`
- `device_serial text`
- `hardware_fingerprint text`
- `created_at text not null default current_timestamp`

## Event Payload Shape

Make event payloads predictable from the start.

All events should include:

```json
{
  "local_event_id": "evt_123",
  "event_type": "transaction.completed",
  "occurred_at": "2026-05-07T12:00:00Z",
  "business_account_id": "biz_123",
  "site_id": "site_123",
  "terminal_device_id": "term_123",
  "staff_user_id": "staff_123",
  "payload": {}
}
```

### First event types to actually implement

- `transaction.completed`
- `minutes.used`
- `minutes.purchased`
- `customer.updated`
- `till.session_opened`
- `till.session_closed`

## Token Strategy

Do not overcomplicate the first version.

### Device Token

Issued after device registration or licence check-in.

Contains:

- `sub`: terminal device public id
- `business_account_id`
- `site_id`
- `token_type`: `device`
- `exp`

### Local Licence Lease

Contains:

- signed token from cloud
- expiry timestamp
- grace policy derived from server response

### Verification Rule

The till should:

- use the cached signed token while valid
- renew when online
- refuse new trading after grace expiry

## Config Pull Contract For Till

The till should be able to bootstrap itself from config pull.

Minimum config to consume:

- business name
- site name
- terminal name
- timezone
- currency
- receipt footer
- bed pin mappings
- prep/cooldown minutes
- auto-start rules
- price-per-minute

## First API Endpoints To Actually Build

### 1. `POST /devices/register`

Purpose:

- link a till to a tenant/site
- create terminal device record
- return first token and licence lease

### 2. `POST /licence/check-in`

Purpose:

- refresh licence lease
- update device heartbeat

### 3. `GET /devices/{terminal_device_id}/config`

Purpose:

- deliver tenant branding and till config

### 4. `POST /sync/events/push`

Purpose:

- accept local till events into cloud event store

Do not build event pull yet unless needed immediately.

## First Till App Changes

The current native till app should get:

### Step 1

Add helper methods in the repository for:

- writing sync outbox rows
- reading pending outbox rows
- marking outbox rows acknowledged
- storing local licence lease
- loading current local device identity

### Step 2

Wrap important business actions so they also enqueue sync events:

- completed sale
- minutes used
- customer edit
- till open
- till close

### Step 3

Add a background timer in the app for:

- licence check every few hours
- config refresh daily
- sync push every minute or on key events

## Failure Handling

### If cloud is down

- keep trading locally
- queue events in outbox
- show small sync warning in staff UI

### If licence renew fails but lease still valid

- keep trading
- warn quietly

### If licence/grace expires

- block new trading
- allow limited admin/support screen

### If event push partially fails

- acknowledge accepted events
- leave rejected/pending ones in outbox
- record reason

## Support and Analytics Guardrails

For now:

- do not build a hidden provider shortcut
- do build audit fields from day one
- do design reporting tables so Salon Max can analyse usage later

The first implementation can defer full provider console UI, but should still capture:

- `business_account_id`
- `site_id`
- `terminal_device_id`
- `staff_user_id`
- `created_at`

on all important records/events.

## Suggested Build Order For Code

### Build 1

- create cloud project skeleton
- create Postgres models for business/site/device/licence/config
- create register/check-in/config endpoints

### Build 2

- add local till tables:
  - `local_sync_outbox`
  - `local_sync_checkpoint`
  - `local_licence_lease`
  - `local_device_identity`

### Build 3

- add till-side service layer:
  - `enqueue_event()`
  - `store_licence_lease()`
  - `load_device_identity()`

### Build 4

- make sale completion enqueue cloud events
- make till open/close enqueue cloud events

### Build 5

- add `/sync/events/push`
- add background sync timer in till app

## Definition of Done For Phase 2A

Phase 2A is successful when:

- a Pi can register to the Salon Max cloud
- the Pi receives its own tenant business name and config
- the Pi stores and renews a valid licence lease
- local completed sales create sync outbox rows
- the Pi can push those events to cloud
- the business branding on receipt/till comes from tenant config, not hard-coded values

## Immediate Next Coding Task

The best next real coding task after this plan is:

1. extend local SQLite schema with:
   - `local_sync_outbox`
   - `local_sync_checkpoint`
   - `local_licence_lease`
   - `local_device_identity`
2. add repository helpers for these tables
3. enqueue one event on completed sale

That is the smallest real platform step that still builds on the working till you already have.
