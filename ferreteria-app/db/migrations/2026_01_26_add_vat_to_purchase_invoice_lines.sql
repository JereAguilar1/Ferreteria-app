-- Migration: Add VAT columns to purchase_invoice_line
-- Date: 2026-01-26

BEGIN;

-- 1. Add columns
ALTER TABLE purchase_invoice_line ADD COLUMN IF NOT EXISTS vat_rate NUMERIC(5,2) NOT NULL DEFAULT 0;
ALTER TABLE purchase_invoice_line ADD COLUMN IF NOT EXISTS vat_amount NUMERIC(14,2) NOT NULL DEFAULT 0;
ALTER TABLE purchase_invoice_line ADD COLUMN IF NOT EXISTS net_amount NUMERIC(14,2) NOT NULL DEFAULT 0;

-- 2. Backfill existing data
-- Assume existing unit_cost was the total cost (no VAT recorded previously)
-- So net_amount = qty * unit_cost, and total matches.
UPDATE purchase_invoice_line 
SET net_amount = round(qty * unit_cost, 2),
    vat_amount = 0,
    vat_rate = 0
WHERE net_amount = 0 AND line_total > 0;

-- 3. Update the trigger constraint for future consistency
ALTER TABLE purchase_invoice_line DROP CONSTRAINT IF EXISTS invoice_line_total_consistency;
ALTER TABLE purchase_invoice_line ADD CONSTRAINT invoice_line_total_consistency 
CHECK (line_total = round(qty * unit_cost * (1 + vat_rate/100), 2));

COMMIT;
