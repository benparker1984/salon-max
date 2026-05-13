# Gym Access Online Launch Checklist

This is the practical order for putting the first gym site online after merging the gym module into Salon Max Platform.

## 1. Restart Salon Max Platform

The merged routes are:

- `/platform/gyms`
- `/platform/business/<business_account_public_id>/gym-access`
- `/gym/<business_account_public_id>/join`
- `/kado`

The running Flask process must be restarted before those routes appear on the live Tailscale/server URL.

## 2. Set The KADO Business ID

Set this environment variable on the server:

```text
KADO_GYM_BUSINESS_ID=biz_test-2
```

Change it later if KADO gets a different business account id.

## 3. Put Salon Max Behind HTTPS

Do not use plain HTTP for real member logins, PINs, admin pages, or payment callbacks.

Minimum production shape:

- domain name pointed at the server
- HTTPS certificate
- reverse proxy to Flask app on port `5001`
- admin login enabled before exposing `/platform/*`

Set these environment variables on the server:

```text
SALONMAX_SECRET_KEY=<long-random-secret>
SALONMAX_PLATFORM_ADMIN_USERNAME=admin
SALONMAX_PLATFORM_ADMIN_PASSWORD=<strong-password>
```

Do not set `SALONMAX_PLATFORM_AUTH_DISABLED=1` in production.

## 4. Protect Owner/Admin Pages

Before public launch:

- require login for `/platform/*` (implemented with `/platform-login`)
- restrict owner console access to Salon Max staff only
- keep public gym pages separate from admin pages

## 5. Move Prototype Gym Data Into Real Tables

The current public KADO page uses prototype class/package data. Before paid members:

- create gym member table
- create gym class table
- create class session table
- create gym package/purchase table
- create access log table
- connect Stripe for each gym account

## 6. Backups

Before launch:

- automatic daily database backup
- off-server backup copy
- test restore once

## 7. First Public URL

Initial KADO route:

```text
https://YOUR-DOMAIN/kado
```

Business-specific route:

```text
https://YOUR-DOMAIN/gym/biz_test-2/join
```
