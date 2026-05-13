# Salon Max Platform API V1

This is the first API contract plan for the Salon Max platform.

Important naming rule:

- **Salon Max** is the software platform/company
- each customer salon business has its **own business name**
- API data must never assume the salon business itself is called Salon Max

Example:

- platform: `Salon Max`
- tenant/business: `Bronze Bay Tanning`
- site 1: `Bronze Bay - Basildon`
- site 2: `Bronze Bay - Rayleigh`

The API must always treat the business as a tenant/customer of Salon Max, not as Salon Max itself.

## Goals

API V1 should support:

- device registration
- licence renewal
- config pull
- event sync up from till to cloud
- event sync down from cloud to till
- customer and ledger retrieval
- provider-safe support operations later

## Design Principles

- JSON over HTTPS
- tenant-aware every time
- device-authenticated every time
- append events, do not overwrite history blindly
- local till remains usable offline
- API responses should be small and incremental where possible

## Identity Model

Every request should be scoped by:

- `business_account_id`
- `terminal_device_id`
- authenticated device token or signed licence token

Suggested auth layers:

### Device Auth

Used by tills:

- signed device token
- rotated by licence renewal/check-in

### Staff Auth

Used by back office:

- email/password
- optional MFA later

### Provider Auth

Used by Salon Max support/admin:

- named support user
- explicit business scope
- audited access

## Base URL

Example:

```text
https://api.salonmax.co.uk/v1/
```

## Standard Request Headers

```text
Authorization: Bearer <device-or-user-token>
Content-Type: application/json
X-SalonMax-Device-Id: <terminal_device_public_id>
X-SalonMax-Business-Id: <business_account_public_id>
X-SalonMax-App-Version: <app-version>
```

## Standard Response Shape

Success:

```json
{
  "ok": true,
  "data": {},
  "meta": {}
}
```

Error:

```json
{
  "ok": false,
  "error": {
    "code": "LICENCE_EXPIRED",
    "message": "This till licence has expired."
  }
}
```

## Core Endpoints

## 1. Device Registration

Used when a new Pi/till is first installed.

### `POST /devices/register`

Request:

```json
{
  "business_account_code": "bronze-bay",
  "site_code": "basildon",
  "device_name": "Front Desk Till",
  "device_serial": "PI-123456789",
  "hardware_fingerprint": "sha256:abcdef...",
  "app_version": "1.0.0"
}
```

Response:

```json
{
  "ok": true,
  "data": {
    "business_account_id": "biz_123",
    "site_id": "site_123",
    "terminal_device_id": "term_123",
    "device_token": "eyJ...",
    "licence": {
      "status": "active",
      "issued_at": "2026-05-07T10:00:00Z",
      "expires_at": "2026-05-14T10:00:00Z"
    }
  }
}
```

Notes:

- this should be a controlled onboarding flow
- not every random device should self-register without approval

## 2. Licence Check-In / Renewal

Used regularly by tills to remain active.

### `POST /licence/check-in`

Request:

```json
{
  "terminal_device_id": "term_123",
  "app_version": "1.0.0",
  "last_seen_at": "2026-05-07T10:15:00Z",
  "last_sync_at": "2026-05-07T10:14:22Z"
}
```

Response:

```json
{
  "ok": true,
  "data": {
    "licence_status": "active",
    "signed_token": "eyJ...",
    "issued_at": "2026-05-07T10:15:00Z",
    "expires_at": "2026-05-14T10:15:00Z",
    "grace_ends_at": "2026-05-21T10:15:00Z"
  }
}
```

Rules:

- till caches latest valid token locally
- till can trade offline until token/grace expires
- cloud can revoke or suspend a device

## 3. Device Config Pull

Used by tills to fetch their site/device config.

### `GET /devices/{terminal_device_id}/config`

Response:

```json
{
  "ok": true,
  "data": {
    "platform_name": "Salon Max",
    "business": {
      "business_name": "Bronze Bay Tanning",
      "timezone": "Europe/London",
      "currency_code": "GBP",
      "receipt_footer_text": "Thank you for visiting"
    },
    "site": {
      "site_name": "Bronze Bay - Basildon"
    },
    "terminal": {
      "terminal_name": "Front Desk Till"
    },
    "beds": [
      {
        "device_id": "bed_1",
        "device_name": "Room 1",
        "prep_minutes": 3,
        "cooldown_minutes": 3,
        "auto_start_after_prep": true,
        "relay_output_pin": 17,
        "trigger_output_pin": 7,
        "feedback_input_pin": 4
      }
    ],
    "pricing": [
      {
        "device_id": "bed_1",
        "price_per_minute": 1.5
      }
    ]
  }
}
```

Important:

- this is where each salon gets its own business name and settings
- the till UI and receipts should read the tenant business name here, not “Salon Max”

## 4. Push Local Events Up

This is the heart of offline sync.

### `POST /sync/events/push`

Request:

```json
{
  "terminal_device_id": "term_123",
  "events": [
    {
      "local_event_id": "evt_local_001",
      "event_type": "transaction.completed",
      "created_at": "2026-05-07T10:20:00Z",
      "payload": {
        "transaction_number": "TXN-1001",
        "customer_id": "cust_123",
        "site_id": "site_123",
        "staff_user_id": "staff_44",
        "total_amount": 13.5,
        "payment_method": "cash"
      }
    },
    {
      "local_event_id": "evt_local_002",
      "event_type": "minutes.used",
      "created_at": "2026-05-07T10:20:02Z",
      "payload": {
        "customer_id": "cust_123",
        "device_id": "bed_1",
        "minutes": 9,
        "transaction_number": "TXN-1001"
      }
    }
  ]
}
```

Response:

```json
{
  "ok": true,
  "data": {
    "accepted": [
      {
        "local_event_id": "evt_local_001",
        "cloud_event_id": 50101
      },
      {
        "local_event_id": "evt_local_002",
        "cloud_event_id": 50102
      }
    ],
    "rejected": []
  }
}
```

Rules:

- cloud must be idempotent for repeated event submissions
- `local_event_id` should be unique per till
- cloud assigns global event order

## 5. Pull Cloud Events Down

Used by tills to catch up from the cloud.

### `GET /sync/events/pull?after_event_id=50100&limit=500`

Response:

```json
{
  "ok": true,
  "data": {
    "events": [
      {
        "cloud_event_id": 50101,
        "event_type": "customer.updated",
        "created_at": "2026-05-07T10:22:00Z",
        "payload": {
          "customer_id": "cust_123",
          "phone": "07123 456789"
        }
      }
    ],
    "last_event_id": 50101,
    "has_more": false
  }
}
```

Rules:

- tills only pull events for their own business account
- tills ignore events they originated if already applied locally
- cloud should support incremental sync only

## 6. Customer Summary Fetch

Used when a till needs a fresh customer snapshot.

### `GET /customers/{customer_id}`

Response:

```json
{
  "ok": true,
  "data": {
    "customer": {
      "id": "cust_123",
      "customer_number": "C-10023",
      "first_name": "Jane",
      "last_name": "Smith",
      "phone": "07123 456789",
      "email": "jane@example.com",
      "birthday": "1990-03-12"
    },
    "balances": {
      "account_balance": 0.0,
      "minutes_available": 24
    },
    "last_visit_at": "2026-05-06T15:20:00Z"
  }
}
```

## 7. Customer Ledger Fetch

Used for support, history, and cross-site reconciliation.

### `GET /customers/{customer_id}/minute-ledger?limit=100`

Response:

```json
{
  "ok": true,
  "data": {
    "entries": [
      {
        "id": "ml_9001",
        "entry_type": "purchase",
        "delta_minutes": 90,
        "minutes_after": 90,
        "site_name": "Bronze Bay - Basildon",
        "created_at": "2026-05-01T12:00:00Z",
        "notes": "90 minute course"
      },
      {
        "id": "ml_9002",
        "entry_type": "usage",
        "delta_minutes": -9,
        "minutes_after": 81,
        "site_name": "Bronze Bay - Rayleigh",
        "created_at": "2026-05-04T16:00:00Z",
        "notes": "Bed 1 session"
      }
    ]
  }
}
```

## 8. Business Export Request

Used later for account exit or data retrieval.

### `POST /exports`

Request:

```json
{
  "export_type": "business_full"
}
```

Response:

```json
{
  "ok": true,
  "data": {
    "export_job_id": "exp_123",
    "status": "queued"
  }
}
```

## 9. Support Access Logging

Used by Salon Max provider tools, not by tills.

### `POST /support/access/start`

Request:

```json
{
  "business_account_id": "biz_123",
  "reason": "Investigating missing minutes after offline sync"
}
```

Response:

```json
{
  "ok": true,
  "data": {
    "support_access_event_id": "sae_123",
    "started_at": "2026-05-07T11:00:00Z"
  }
}
```

This is the safe replacement for the idea of a hidden back door.

## Suggested Event Types

Start with these:

- `customer.created`
- `customer.updated`
- `transaction.completed`
- `transaction.voided`
- `minutes.purchased`
- `minutes.used`
- `minutes.adjusted`
- `account.credit_added`
- `account.credit_used`
- `queue.booking_created`
- `session.started`
- `session.ended`
- `stock.adjusted`
- `till.session_opened`
- `till.session_closed`

## Error Codes To Standardise Early

- `AUTH_INVALID`
- `AUTH_EXPIRED`
- `LICENCE_EXPIRED`
- `LICENCE_SUSPENDED`
- `DEVICE_NOT_REGISTERED`
- `TENANT_MISMATCH`
- `EVENT_DUPLICATE`
- `EVENT_REJECTED`
- `SYNC_CONFLICT`
- `CUSTOMER_NOT_FOUND`
- `EXPORT_NOT_ALLOWED`
- `RATE_LIMITED`

## Offline Behaviour Rules

If cloud is unavailable:

- till continues using local DB
- events remain in local outbox
- receipts and hardware control continue
- licence remains valid until local expiry/grace

If grace expires:

- till should block new trading
- till may allow limited read-only access
- support instructions should be visible to staff

## Recommended Build Order For The API

### API Step 1

- `POST /devices/register`
- `POST /licence/check-in`
- `GET /devices/{terminal_device_id}/config`

### API Step 2

- `POST /sync/events/push`
- `GET /sync/events/pull`

### API Step 3

- `GET /customers/{customer_id}`
- `GET /customers/{customer_id}/minute-ledger`

### API Step 4

- exports
- support access
- analytics/reporting endpoints

## Final Position

API V1 should let the current Pi till evolve into a real Salon Max platform device.

It should:

- know which business it belongs to
- pull that business’s branding and rules
- trade offline locally
- sync safely to the cloud
- renew its licence
- support many salons without mixing their data

And it should always preserve the naming split:

- Salon Max = the platform
- the salon business = the customer account using the platform
