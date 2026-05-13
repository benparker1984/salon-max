# Schema V1

This is the first-pass domain model for the system.

## Core Reference Tables

### Site

- `id`
- `name`
- `code`
- `is_active`

### Device

- `id`
- `site_id`
- `device_number`
- `device_name`
- `is_active`

### StaffUser

- `id`
- `name`
- `pin_code`
- `role`
- `is_active`

### StaffSiteAccess

- `id`
- `staff_user_id`
- `site_id`

## Customer Tables

### Customer

- `id`
- `customer_number`
- `account_number`
- `first_name`
- `last_name`
- `phone`
- `email`
- `created_at`
- `is_active`

### CustomerAccount

- `id`
- `customer_id`
- `current_balance`
- `updated_at`

### AccountLedgerEntry

- `id`
- `customer_id`
- `transaction_id`
- `site_id`
- `staff_user_id`
- `entry_type`
- `entry_direction`
- `amount`
- `balance_after`
- `created_at`
- `notes`

## Package / Course Tables

### PackageProduct

- `id`
- `name`
- `code`
- `minutes_included`
- `price`
- `validity_days`
- `is_active`

### CustomerPackage

- `id`
- `customer_id`
- `package_product_id`
- `site_id`
- `sold_by_user_id`
- `purchase_transaction_id`
- `original_minutes`
- `remaining_minutes`
- `valid_until`
- `status`
- `created_at`

### PackageMovement

- `id`
- `customer_package_id`
- `customer_id`
- `transaction_id`
- `site_id`
- `staff_user_id`
- `movement_type`
- `minutes_change`
- `remaining_minutes_after`
- `created_at`
- `notes`

## Transaction Tables

### Transaction

- `id`
- `transaction_number`
- `customer_id`
- `site_id`
- `terminal_id`
- `staff_user_id`
- `transaction_date`
- `status`
- `subtotal_amount`
- `discount_amount`
- `total_amount`
- `notes`

### TransactionLine

- `id`
- `transaction_id`
- `line_type`
- `product_code`
- `description`
- `quantity`
- `unit_price`
- `line_total`
- `device_id`
- `tanning_minutes`

### TransactionPayment

- `id`
- `transaction_id`
- `payment_type`
- `amount`
- `reference_type`
- `reference_id`
- `notes`

## Till Tables

### Terminal

- `id`
- `site_id`
- `name`
- `is_active`

### TillSession

- `id`
- `site_id`
- `terminal_id`
- `opened_by_user_id`
- `closed_by_user_id`
- `opened_at`
- `closed_at`
- `opening_float`
- `expected_cash`
- `counted_cash`
- `variance`
- `status`
- `closing_notes`

### TillMovement

- `id`
- `till_session_id`
- `movement_date`
- `movement_type`
- `amount`
- `reason`
- `linked_transaction_id`
- `created_by_user_id`

## Pricing Tables

### PricingRule

- `id`
- `site_id`
- `device_id`
- `price_per_minute`
- `is_active`
- `starts_at`
- `ends_at`

## Queue / Operation Tables

### QueueBooking

- `id`
- `site_id`
- `device_id`
- `customer_id`
- `transaction_id`
- `minutes`
- `payment_method`
- `status`
- `created_at`

### ActiveSession

- `id`
- `site_id`
- `device_id`
- `customer_id`
- `transaction_id`
- `phase`
- `minutes`
- `started_at`
- `expected_end_at`
- `status`

## Reporting Principle

Reports should be built mainly from:

- `Transaction`
- `TransactionLine`
- `TransactionPayment`
- `TillSession`
- `TillMovement`
- `AccountLedgerEntry`
- `PackageMovement`
