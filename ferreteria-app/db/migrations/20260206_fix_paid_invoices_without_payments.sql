-- Migration to fix invoices marked as PAID but missing payment records
-- This ensures that balance calculations (total_amount - sum(payments)) are correct.

INSERT INTO purchase_invoice_payment (invoice_id, amount, paid_at, notes, created_at)
SELECT 
    id as invoice_id, 
    total_amount as amount, 
    COALESCE(paid_at, CURRENT_DATE) as paid_at, 
    'Corrección automática: Pago faltante en boleta marcada como PAGADA' as notes,
    now() as created_at
FROM purchase_invoice 
WHERE status = 'PAID' 
AND id NOT IN (SELECT DISTINCT invoice_id FROM purchase_invoice_payment);
