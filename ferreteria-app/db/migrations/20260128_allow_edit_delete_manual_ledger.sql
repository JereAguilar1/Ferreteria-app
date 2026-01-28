-- Migration: Allow edit/delete of manual ledger entries
-- Adds soft delete and updated_at to finance_ledger

BEGIN;

ALTER TABLE finance_ledger ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE finance_ledger ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION trg_finance_ledger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS finance_ledger_set_updated_at ON finance_ledger;
CREATE TRIGGER finance_ledger_set_updated_at
    BEFORE UPDATE ON finance_ledger
    FOR EACH ROW
    EXECUTE FUNCTION trg_finance_ledger_set_updated_at();

COMMIT;
