-- Migration: Add concept column to finance_ledger
-- Date: 2026-01-26

BEGIN;

-- 1. Add column as nullable first
ALTER TABLE finance_ledger ADD COLUMN IF NOT EXISTS concept VARCHAR(255);

-- 2. Backfill existing data
-- For Sales
UPDATE finance_ledger 
SET concept = 'Venta #' || reference_id 
WHERE reference_type = 'SALE' AND concept IS NULL;

-- For Invoice Payments
UPDATE finance_ledger 
SET concept = 'Pago Boleta #' || reference_id 
WHERE reference_type = 'INVOICE_PAYMENT' AND concept IS NULL;

-- For Manual entries
UPDATE finance_ledger 
SET concept = COALESCE(category, 'Movimiento Manual') 
WHERE reference_type = 'MANUAL' AND concept IS NULL;

-- Fallback for any other case
UPDATE finance_ledger 
SET concept = 'Movimiento' 
WHERE concept IS NULL;

-- 3. Set as NOT NULL
ALTER TABLE finance_ledger ALTER COLUMN concept SET NOT NULL;

COMMIT;
