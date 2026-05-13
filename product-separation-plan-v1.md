# Salon Max Product Separation Plan v1

Salon Max should stay as one owner platform, but the products must be separated so every customer business is repeatable and clean.

## Target Structure

- `platform`: Salon Max owner/admin console, billing, support, health checks, suspension, updates, and business setup.
- `salon`: salon back office, till API, customers, sunbeds, packages, sales, ledgers, reports, and terminal sync.
- `gym`: gym public customer portal, staff portal, reception check-in, classes, packages, payments, and membership state.

## Business Model

Every customer starts as a `cloud_business_accounts` row.

Important fields:

- `business_account_public_id`: stable account id, for example `ultra-violet` or `kado-fitness`.
- `business_name`: customer-facing name.
- `product_type`: `salon` or `gym`.
- `status`: active, suspended, archived.
- `subscription_status`: trial, active, suspended, cancelled.

The product code must read `product_type` and route the account into the correct product area. We should not copy files per customer.

## Canonical URLs

Platform owner:

- `/platform`
- `/platform/gyms`
- `/platform/business/<business_account_public_id>`
- `/platform/business/<business_account_public_id>/gym-access`

Gym product:

- `/gym/<business_account_public_id>`
- `/gym/<business_account_public_id>/customer`
- `/gym/<business_account_public_id>/staff`
- `/gym/<business_account_public_id>/check-in`

Salon product:

- `/backoffice` for the current online salon back office entry point.
- Future multi-salon URL should be `/salon/<business_account_public_id>/backoffice`.
- Till API remains `/v1/...`, but must always authenticate with business, site, terminal, and licence headers.

## Rules

- No product should hard-code KADO Fitness, Ultra Violet, or any other customer as the system default.
- Friendly shortcuts such as `/staff` and `/check-in` may exist only for a single branded deployment, and must redirect to a real canonical account URL.
- Gym state and salon state must not share tables unless the table is deliberately platform-level.
- Salon Max owner admin can manage both product types from one console, but customer-facing/staff-facing pages must remain product-specific.

## Current Separation Pass

Completed in this pass:

- Added generic default gym helpers.
- Moved the gym deployment defaults into `salonmax_products/gym.py` so KADO-specific behaviour is no longer embedded directly in `app.py`.
- Kept `KADO_GYM_BUSINESS_ID` as a backwards-compatible deploy setting only.
- Added `SALONMAX_DEFAULT_GYM_BUSINESS_ID`, `SALONMAX_DEFAULT_GYM_BUSINESS_NAME`, and `SALONMAX_DEFAULT_GYM_STAFF_PASSWORD`.
- Added `SALONMAX_GYM_FRIENDLY_SHORTCUTS=0` option so generic deployments can disable `/kado`, `/staff`, `/check-in`, and `/gym` shortcuts.
- Added canonical `/gym/<business_account_public_id>/check-in` route.
- Added generic `/gym` default shortcut.
- Kept `/kado`, `/staff`, and `/check-in` as deployment shortcuts, not product architecture.
- Added `/backoffice` as the online salon back office entry point.

## Next Pass

- Move gym routes/helpers into a separate module or blueprint.
- Move platform routes/helpers into a separate module or blueprint.
- Move salon back-office routes/helpers into a separate module or blueprint.
- Introduce proper persistent database storage before connecting live tills to hosted cloud.
