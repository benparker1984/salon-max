# Salon Max Platform Boundary Split V1

This document defines the clean split between:

- the Salon Max cloud platform
- the salon-owned business system
- the Raspberry Pi till client in each branch

The goal is to stop designing the Raspberry Pi like it is the permanent host of the whole product.

## The Big Rule

The Raspberry Pi is a client.

It is not:

- the permanent Salon Max server
- the owner platform
- the cross-salon source of truth
- the place where provider support and analytics should live long term

The Pi should be able to trade locally, cache what it needs, and report back to Salon Max cloud.

## The Three Layers

### 1. Salon Max Cloud Platform

This is your company-owned platform.

It is for:

- Salon Max owners
- Salon Max support staff
- Salon Max finance/admin staff
- platform analytics
- subscription and licence control

It should be hosted separately from any customer salon.

It owns:

- all tenant/business accounts
- site registrations
- terminal registrations
- licence records
- subscription state
- global sync ingestion
- cloud event ordering
- support tools
- export tooling
- provider analytics
- audit trail for platform-side actions

It should eventually have its own:

- web app
- API
- database
- auth system
- admin roles

### 2. Salon Business System

This is the customer-facing management layer for one salon business.

It is for:

- salon owners
- salon managers
- authorised staff

It should feel like the salon’s own system, not your internal owner console.

It owns the business-facing experience for:

- customers
- sales
- packages
- products
- pricing
- stock
- staff
- reports
- site settings
- device settings for that business

This layer may be partly local-first and partly cloud-backed, but conceptually it belongs to the customer business, not to Salon Max support staff.

### 3. Raspberry Pi Till Client

This is the branch-floor operational client.

It is for:

- reception staff
- day-to-day sales
- sunbed control
- cash drawer
- receipt printer
- local offline operation

It should be fast, resilient, and able to trade without constant internet.

It owns:

- immediate till flow
- local hardware control
- local session timing
- local queue state
- local cache of customer/business config
- local sync outbox
- last valid licence lease

It should not own:

- long-term provider reporting
- multi-business analytics
- cross-tenant management
- permanent master customer records

## Permanent Hosting Model

The final production shape should be:

1. Salon Max cloud platform hosted on your infrastructure
2. each salon Pi connecting outward to it
3. each salon business seeing only its own data and tools

So the production relationship becomes:

- Pi till -> Salon Max cloud API
- salon business back office -> Salon Max cloud API
- Salon Max owner console -> Salon Max cloud API

Not:

- Pi till hosting the owner platform
- Pi till acting as the business master database

## What We Built On The Pi

The current Pi-hosted Flask app is a prototype harness.

It proved:

- sync event push works
- config pull works
- licence check-in works
- a provider console can exist

That is useful.

But it is still only a proving ground.

It should be treated as:

- local development server
- integration test harness
- demo environment

It should not be mistaken for the final deployment target.

## Ownership Matrix

### Salon Max Cloud Platform Owns

- `BusinessAccount`
- `Site`
- `TerminalDevice`
- `CloudDeviceLicence`
- `CloudSyncEvent`
- subscription records
- provider support audit
- provider analytics warehouse later

### Salon Business System Owns

- business branding
- business operating preferences
- staff roles inside that business
- customer communication settings
- local business reporting views

### Pi Till Client Owns

- GPIO and hardware state
- live room/sunbed state
- receipt printing
- cash drawer firing
- optocoupler feedback handling
- local session state
- offline trading continuity

## Data Flow Between Layers

### Config Flow

Salon Max cloud stores master config.

Pi pulls:

- business name
- site name
- terminal name
- bed setup
- pricing
- prep/cooldown rules

The salon business layer edits the business-owned settings.

The Pi consumes them.

### Licence Flow

Salon Max cloud issues leases.

Pi:

- checks in
- stores the returned lease locally
- keeps trading during allowed offline grace

Salon business users should not manage low-level platform licensing directly unless you explicitly expose a limited view.

### Sync Flow

Pi:

- writes local events
- pushes them to Salon Max cloud

Cloud:

- stores them
- orders them
- makes them available to the salon business layer and other sites

### Support Flow

Salon Max support should access customer-business data through the provider platform, not by logging into a salon Pi as if it were the server.

## UI Boundaries

These three UIs should feel distinct.

### A. Salon Max Owner Console

For your company only.

Should contain:

- customer businesses
- subscription status
- terminal fleet health
- sync failures
- support actions
- exports
- provider analytics

Should not feel like a salon’s back office with one more tab added.

### B. Salon Business Back Office

For the customer salon business.

Should contain:

- customer records
- pricing
- staff
- packages
- stock
- sales reports
- site/device config within that business scope

Should not show provider-only controls.

### C. Pi Till Interface

For branch-floor staff.

Should contain only what helps trade and control the hardware safely.

## Security Boundary

The split also matters for security.

### Provider Platform

Needs:

- provider authentication
- role-based access
- support audit
- tenant scoping

### Salon Business Layer

Needs:

- business-scoped accounts
- site/manager/staff permissions
- no access to other businesses

### Pi Client

Needs:

- device identity
- cached lease
- limited credentials
- no permanent provider-admin capability

## Recommended Repo Direction

As the project matures, the codebase should conceptually split into:

- `native_till_app/`
  - Pi client
- `salon_business_app/`
  - customer back office and business web/API
- `salonmax_platform/`
  - provider platform and owner console

You do not need to physically split the repo today.

But from now on, decisions should be tagged mentally as:

- Pi client concern
- salon business concern
- Salon Max owner-platform concern

That will stop accidental leakage between layers.

## Immediate Practical Rule For Current Work

From this point onward:

- if a feature is for salon staff or managers, it belongs to the salon business side
- if a feature is for hardware/till operation, it belongs to the Pi client
- if a feature is for you as the software company owner, it belongs to the Salon Max platform side

## What To Build Next

The next clean design steps are:

1. create a proper provider-only route group and navigation style
2. define a business-account list view instead of showing one salon’s data as if it were the platform
3. define a separate salon business app shell
4. keep the Pi using only API calls and local cache, not hosting provider features
5. move the current Flask prototype mentally into "temporary local dev server" status

## Final Position

The Pi-hosted provider console is temporary.

The permanent model is:

- hosted Salon Max platform above
- salon business layer below it
- Pi clients at the edge

That is the correct shape for one salon today and one hundred salons later.
