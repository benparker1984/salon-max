# DigitalOcean Launch Plan v1

## Decision

Use DigitalOcean as the main production home for Salon Max Platform and KADO/Gym Access.

Recommended target stack:

- DigitalOcean App Platform for the Flask web app
- DigitalOcean Managed PostgreSQL for production data
- Stripe Checkout + Stripe webhooks for payments
- Raspberry Pi tills remain local clients only; they must not host the public cloud

## Why

The Raspberry Pi is fine for shop-floor testing, but it is not the permanent public host. The production system needs a stable public URL, managed HTTPS, backups, logs, deploy history, and a database designed for customer balances, payments, and business records.

## Current Repo Prep

The repository now includes:

- `requirements.txt` for DigitalOcean Python detection
- `runtime.txt` for Python runtime selection
- `wsgi.py` as the Gunicorn entrypoint
- `Procfile` with the App Platform run command
- `.gitignore` to keep local databases, logs, and secrets out of source control

## App Platform Run Command

```bash
gunicorn --worker-tmp-dir /dev/shm --bind 0.0.0.0:$PORT wsgi:app
```

## Required Environment Variables

Set these in DigitalOcean as encrypted runtime variables:

```text
SALONMAX_APP_ROLE=cloud
SALONMAX_SECRET_KEY=<long-random-secret>
SALONMAX_PLATFORM_ADMIN_USERNAME=admin
SALONMAX_PLATFORM_ADMIN_PASSWORD=<strong-password>
KADO_GYM_BUSINESS_ID=biz_test-2
SALONMAX_STRIPE_SECRET_KEY=<stripe-secret-key-later>
SALONMAX_STRIPE_WEBHOOK_SECRET=<stripe-webhook-secret-later>
```

## Important Database Warning

The current app still uses SQLite files. That is acceptable for local/Pi testing, but it is not the final production storage for customer balances, memberships, payments, and salon data on App Platform.

Before real customer money or customer balances are hosted live, move the app data layer to DigitalOcean Managed PostgreSQL and add backup/restore checks.

## Practical Launch Order

1. Create a DigitalOcean account.
2. Create a DigitalOcean project named `Salon Max`.
3. Put this repo into GitHub so App Platform can deploy it.
4. Create an App Platform web service from the GitHub repo.
5. Add the encrypted environment variables.
6. Deploy and check `/platform-login`, `/kado`, and `/gym/biz_test-2/customer`.
7. Add Managed PostgreSQL and migrate the app from SQLite before taking real payments.
8. Add Stripe webhook endpoint after the public URL exists.
9. Add the final domain names.
10. Disable the temporary Pi Funnel.
