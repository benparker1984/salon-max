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

## Salon Hardware Strategy

Primary build direction:

- Each salon gets a Raspberry Pi appliance.
- The Pi hosts the till app, salon back office, local working database, and hardware control.
- The Pi controls the Salon Max relay PCB for sunbed start/enable and feedback.
- Salon Max cloud provides owner platform access, licence/suspension, health checks, secure remote access, updates, and encrypted backup/restore.

Future product variants:

- `pi_relay_board`: full Salon Max appliance with Pi + Salon Max PCB. This is the current build target.
- `pc_to_pi_relay_board`: lighter PC install where the salon PC runs software and talks to a Pi hardware controller.
- `tmax_serial`: Lite+ mode for salons that keep an existing T-Max Manager/controller and connect through serial/RS-232 where supported.
- `manual`: software-only/manual operation with no direct hardware control.

Every salon business setting now includes `hardware_controller_type` so we can add these variants without redesigning the product later.

## Cloud Product Deployment Modes

Hosted apps now need an explicit product boundary so KADO/gym and Salon Max/salon do not leak into each other.

- `SALONMAX_PRODUCT_MODE=gym` makes the deployment gym-only. It keeps `/`, `/kado`, `/staff`, `/check-in`, and `/gym/...` available, but redirects Salon Max platform/backoffice pages away from the gym app.
- `SALONMAX_PRODUCT_MODE=salon` keeps the Salon Max platform/backoffice routes available for the salon product.
- If `SALONMAX_PRODUCT_MODE` is not set, `SALONMAX_CLOUD_HOME=default_gym`, `gym`, or `kado` is treated as gym-only for backwards compatibility.

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
- Moved the gym customer/staff/check-in/state/checkout/webhook routes into `salonmax_products/gym_routes.py`.
- Moved gym state storage, payment settings, checkout event saving, Stripe signature checking, and Stripe Checkout API calls into `salonmax_products/gym.py`.
- Left thin compatibility wrappers in `app.py` so existing platform pages still call the same helper names while the product logic now lives behind the gym module boundary.
- Added `salonmax_products/salon.py` and moved the first low-risk salon helpers into it: sunbed row preparation, business settings shaping, report date parsing, transaction-day rows, and best-seller rows.
- Disabled the legacy `/backoffice` salon shell on cloud deployments unless `SALONMAX_ENABLE_CLOUD_SALON_BACKOFFICE=1` is deliberately set. This stops the KADO Fitness deployment from exposing broken salon back-office screens.
- Added a gym-only deployment guard so KADO-style hosted apps redirect `/platform`, `/platform-login`, and salon backoffice URLs back to the gym public site.

## Next Pass

- Move platform routes/helpers into a separate module or blueprint.
- Continue moving salon back-office routes/helpers into `salonmax_products/salon.py` or a salon route module.
- Move remaining gym owner setup pages/forms out of `app.py`.
- Create a separate hosted Salon Max back-office deployment/domain when we are ready, instead of running it inside the KADO Fitness app.
- Introduce proper persistent database storage before connecting live tills to hosted cloud.
