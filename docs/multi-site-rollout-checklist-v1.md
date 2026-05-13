# Multi-Site Rollout Checklist v1

Use this when setting up one Salon Max business with multiple stores and one Raspberry Pi till per store.

## Goal

Set up:

- one business
- multiple sites
- one terminal per site
- one paired Raspberry Pi per terminal
- shared customer and value data across all sites

## Before hardware arrives

Confirm:

- the business exists in Salon Max owner platform
- all intended sites are created
- each site has at least one terminal provisioned
- pairing codes can be generated for each terminal
- the business customer import is ready if migrating from another system

Prepare:

- business name
- site names and codes
- terminal names
- internet access details for each store
- any migrated customer list

## One-time platform setup

1. Create or confirm the business account.
2. Create all business sites.
3. Create one terminal per site.
4. Decide which terminals are:
   - fresh install
   - replacement Pi
5. Generate pairing codes for each terminal.

## Per-Pi setup

Repeat these steps for each Raspberry Pi:

1. Boot the Pi into the till app.
2. Confirm it is on the `Device Setup` / pairing flow.
3. Enter the correct pairing code for that site and terminal.
4. Confirm the Pi shows the correct:
   - business
   - site
   - terminal
5. If this is a new salon install, confirm it goes through:
   - first staff setup
   - then normal login

## Shared data proof

Once all Pis are paired:

1. Create or import a test customer.
2. Open the same customer on site 1.
3. Add value or minutes.
4. Use some minutes on site 1.
5. Open the same customer on site 2.
6. Confirm the minutes/value match the shared central record.
7. Use some minutes on site 2.
8. Recheck on site 1.
9. Confirm the totals still match.

## Owner-platform checks

For each site/terminal, confirm in the owner platform:

- terminal appears under the correct business
- terminal appears under the correct site
- licence is active
- check-in is recent
- app version is reported
- sync status is healthy

## Suspension checks

These can wait until full hardware is available, but should be tested later:

### Business suspension

1. Suspend the business.
2. Confirm all tills lock.
3. Reactivate the business.
4. Confirm all tills return to trading.

### Site suspension

1. Suspend one site.
2. Confirm only tills at that site lock.
3. Confirm other sites keep trading.
4. Reactivate the site.
5. Confirm that site returns to trading.

### Terminal suspension

1. Suspend one terminal.
2. Confirm only that till locks.
3. Reactivate the terminal.
4. Confirm it returns to trading.

## Update and health checks

For each terminal:

1. Confirm it appears on:
   - `Updates`
   - `Diagnostics`
   - `Licences`
2. Confirm version status is correct.
3. Confirm sync/outbox health is visible.
4. Confirm the terminal can be identified by site and business.

## Customer import check

If migrating a salon:

1. Import a customer CSV into the business.
2. Confirm imported customers appear in the owner platform.
3. Confirm each Pi receives the shared customer directory.
4. Open at least one imported customer from two different sites.
5. Confirm shared minutes/balance match.

## Machine catalogue check

Once the machine catalogue is fully used in back office:

1. Open `Sunbed Settings`.
2. Assign a manufacturer and model to each bed.
3. Use `Custom Machine` only where needed.
4. Later, confirm default machine images appear once the image pack is added.

## Success criteria

The rollout is considered good when:

- every Pi pairs to the correct site and terminal
- every Pi checks in successfully
- shared customers and minutes stay consistent across stores
- owner platform shows healthy diagnostics
- support controls can suspend and reactivate at business, site, and terminal level

## What still needs real hardware to prove

These items should be retested once more Pis arrive:

- simultaneous use on separate physical tills
- real multi-store networking conditions
- site-level locking without sharing one local Pi database
- repeated cross-site customer usage under live load
