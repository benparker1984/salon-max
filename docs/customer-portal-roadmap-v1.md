# Customer Portal Roadmap V1

This document captures how customer self-service should fit into Salon Max without derailing the current owner platform, salon back office, and Pi till rollout.

## Goal

Add a customer-facing layer where salon customers can:

- sign in securely
- view their account balance and minutes
- view package history and visit history
- top up online
- update their own contact details
- later: book, reserve, or manage preferences

This should sit on top of the same central Salon Max ledger and tenant model, not as a separate side database.

## Platform Shape

The full product stack becomes:

- `Salon Max owner platform`
- `salon business back office`
- `Pi till client`
- `customer portal`

The customer portal belongs to a single salon business tenant. A customer should never accidentally see another salon's data.

## Non-Negotiable Rule

Customer money, minutes, and packages must use the same central ledger model as staff-side trading.

Examples:

- `+30 minutes purchased online`
- `-6 minutes used in salon`
- `+10 goodwill adjustment by manager`
- `-1 package session redeemed`

Do not build customer top-up against a simple `remaining_minutes` number alone.

## What Customers Should Eventually See

Phase-ready customer views:

- account summary
- remaining balance
- remaining minutes
- active packages
- recent transactions
- visit history
- profile/contact details

Later possible views:

- preferred salon/site
- booking history
- membership or subscription status
- device usage summaries if you choose to expose them

## Authentication Requirements

Before rollout, customer login must support:

- unique customer identity per salon business
- password or magic-link style login
- email and/or mobile verification
- password reset or recovery
- session expiry
- audit trail for login-sensitive changes

Do not let the customer portal depend on Pi-local credentials.

## Payments And Risk

The moment customers can top up themselves, Salon Max takes on more responsibility.

Needed before public launch:

- proper hosted payment provider integration
- payment success / failure / reversal handling
- duplicate-payment protection
- refund and dispute workflow
- reconciliation against the customer ledger
- support tooling for payment-linked account problems

## Recommended Rollout Order

### Phase A: Read-Only Customer Access

Build first:

- customer login
- account summary
- minutes/package visibility
- visit history
- contact details view

This gives value without immediately exposing payment risk.

### Phase B: Self-Service Profile Updates

Add:

- update phone/email
- communication preferences
- optional marketing consent handling

### Phase C: Online Top-Up

Add only after the ledger and support tooling are fully trusted:

- card payment
- package purchase
- balance top-up
- confirmation emails
- transaction receipts

### Phase D: Optional Booking Layer

Only if commercially useful:

- reserve appointments or beds
- waitlists
- booking cancellations

## Data Ownership

Customer portal data should live centrally in Salon Max cloud:

- customer identity
- authentication state
- ledger entries
- payment references
- profile changes
- consents

Pi tills should only consume synced customer/account data required for trading and offline continuity.

## Support Requirements

Owner/support tools should eventually be able to answer:

- what did this customer buy?
- when was it redeemed?
- did online payment succeed?
- who adjusted the account?
- which site used the minutes?
- what was the ledger before and after the dispute?

That means the provider platform should later include:

- customer ledger inspector
- payment event view
- adjustment history
- export tools

## Multi-Site Consideration

Some salon businesses will run one site, others several.

Customer sharing across sites should be configurable per salon business:

- `single-site only`
- `shared across all sites in this business`
- `selected linked sites only`

This is the right place to add the user's site-linking idea later. It should be a business-level rule, not a Pi-level hack.

## Decision Boundary

Do not start building customer-facing payments until:

- cloud master data is trusted
- multi-site sync is trusted
- support/audit tooling is trusted
- reconciliation rules are clear

## Next Build Trigger

Only begin implementation after the current core platform sequence is stable:

1. owner platform
2. business account management
3. site and terminal management
4. sync and licensing maturity
5. support/audit visibility
6. then customer portal Phase A
