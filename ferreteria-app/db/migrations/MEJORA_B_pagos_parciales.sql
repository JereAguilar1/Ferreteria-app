-- MEJORA B: Pagos Parciales de Boletas (Adelantos)
-- Permite registrar múltiples pagos parciales para una boleta
-- y calcular el saldo pendiente dinámicamente

BEGIN;

-- ============================================================================
-- 1. Crear tabla purchase_invoice_payment
-- ============================================================================

CREATE TABLE IF NOT EXISTS purchase_invoice_payment (
    id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT NOT NULL,
    paid_at DATE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    notes VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    CONSTRAINT fk_invoice_payment_invoice
        FOREIGN KEY (invoice_id)
        REFERENCES purchase_invoice(id)
        ON DELETE CASCADE
);

-- Índices para optimizar queries
CREATE INDEX IF NOT EXISTS idx_invoice_payment_invoice_id 
    ON purchase_invoice_payment(invoice_id);

CREATE INDEX IF NOT EXISTS idx_invoice_payment_paid_at 
    ON purchase_invoice_payment(paid_at);

COMMENT ON TABLE purchase_invoice_payment IS 
    'Pagos parciales de boletas de compra. Permite adelantos y pagos en cuotas.';

COMMENT ON COLUMN purchase_invoice_payment.invoice_id IS 
    'Referencia a la boleta que se está pagando';

COMMENT ON COLUMN purchase_invoice_payment.paid_at IS 
    'Fecha en que se realizó el pago (puede ser distinta a created_at)';

COMMENT ON COLUMN purchase_invoice_payment.amount IS 
    'Monto del pago parcial. Debe ser > 0 y <= saldo pendiente';

-- ============================================================================
-- 2. Migrar pagos existentes (si existen)
-- ============================================================================

-- Si purchase_invoice tiene un campo paid_at y status='PAID',
-- crear un pago por el total_amount

INSERT INTO purchase_invoice_payment (invoice_id, paid_at, amount, notes, created_at)
SELECT 
    id AS invoice_id,
    COALESCE(paid_at, invoice_date) AS paid_at,  -- Si no hay paid_at, usar invoice_date
    total_amount AS amount,
    'Pago migrado desde sistema anterior' AS notes,
    COALESCE(paid_at, created_at) AS created_at
FROM purchase_invoice
WHERE status = 'PAID'
  AND id NOT IN (SELECT DISTINCT invoice_id FROM purchase_invoice_payment);

-- ============================================================================
-- 3. Verificar integridad
-- ============================================================================

-- Query de verificación (ejecutar después de migración):
-- 
-- -- Ver pagos por boleta
-- SELECT 
--     pi.id,
--     pi.invoice_number,
--     pi.total_amount,
--     COALESCE(SUM(pip.amount), 0) AS total_paid,
--     pi.total_amount - COALESCE(SUM(pip.amount), 0) AS balance,
--     pi.status
-- FROM purchase_invoice pi
-- LEFT JOIN purchase_invoice_payment pip ON pip.invoice_id = pi.id
-- GROUP BY pi.id, pi.invoice_number, pi.total_amount, pi.status
-- ORDER BY pi.id DESC
-- LIMIT 20;

COMMIT;

-- ============================================================================
-- Rollback (si es necesario deshacer la migración)
-- ============================================================================

-- BEGIN;
-- DROP TABLE IF EXISTS purchase_invoice_payment CASCADE;
-- COMMIT;
