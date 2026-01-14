-- MEJORA 24: unit_cost con decimales y total_amount ampliado
-- Ajusta columnas para permitir 2 decimales obligatorios en boletas

BEGIN;

-- purchase_invoice_line.unit_cost a NUMERIC(14,2)
ALTER TABLE purchase_invoice_line
    ALTER COLUMN unit_cost TYPE NUMERIC(14,2)
    USING unit_cost::numeric;

-- purchase_invoice_line.line_total a NUMERIC(14,2) (consistente con unit_cost)
ALTER TABLE purchase_invoice_line
    ALTER COLUMN line_total TYPE NUMERIC(14,2)
    USING line_total::numeric;

-- purchase_invoice.total_amount a NUMERIC(14,2)
ALTER TABLE purchase_invoice
    ALTER COLUMN total_amount TYPE NUMERIC(14,2)
    USING total_amount::numeric;

COMMIT;
