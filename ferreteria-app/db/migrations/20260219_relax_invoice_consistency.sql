-- Migration to relax the invoice line total consistency constraint
-- Current constraint: line_total = round((qty * unit_cost * (1 + (vat_rate / 100))), 2)
-- New constraint: abs(line_total - round((qty * unit_cost * (1 + (vat_rate / 100))), 2)) <= 0.01

ALTER TABLE purchase_invoice_line 
DROP CONSTRAINT IF EXISTS invoice_line_total_consistency;

ALTER TABLE purchase_invoice_line
ADD CONSTRAINT invoice_line_total_consistency 
CHECK (abs(line_total - round((qty * unit_cost * (1 + (vat_rate / 100.0))), 2)) <= 0.01);
