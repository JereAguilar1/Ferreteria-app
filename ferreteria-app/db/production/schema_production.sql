-- ============================================================================
-- Sistema Ferretería - PostgreSQL Schema de Producción
-- ============================================================================
-- Versión: 1.0
-- Fecha: Enero 2026
-- PostgreSQL: 16+ (recomendado)
-- Mejoras incluidas: 1-8 (Fotos, Filtros, Top vendidos, Unit cost, Balance, Fechas, Auth)
-- ============================================================================

BEGIN;

-- ============================================================================
-- EXTENSIONES OPCIONALES
-- ============================================================================
-- Descomentar si se requiere búsqueda fuzzy de productos
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- TIPOS ENUM
-- ============================================================================

-- Estados de ventas
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sale_status') THEN
    CREATE TYPE sale_status AS ENUM ('CONFIRMED', 'CANCELLED');
  END IF;
END$$;

-- Estados de facturas de compra
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'invoice_status') THEN
    CREATE TYPE invoice_status AS ENUM ('PENDING', 'PAID');
  END IF;
END$$;

-- Tipos de movimiento de stock
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'stock_move_type') THEN
    CREATE TYPE stock_move_type AS ENUM ('IN', 'OUT', 'ADJUST');
  END IF;
END$$;

-- Tipos de referencia para movimientos de stock
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'stock_ref_type') THEN
    CREATE TYPE stock_ref_type AS ENUM ('SALE', 'INVOICE', 'MANUAL');
  END IF;
END$$;

-- Tipos de entrada en libro mayor
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ledger_type') THEN
    CREATE TYPE ledger_type AS ENUM ('INCOME', 'EXPENSE');
  END IF;
END$$;

-- Tipos de referencia para libro mayor
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ledger_ref_type') THEN
    CREATE TYPE ledger_ref_type AS ENUM ('SALE', 'INVOICE_PAYMENT', 'MANUAL');
  END IF;
END$$;

-- ============================================================================
-- TABLAS MAESTRAS
-- ============================================================================

-- Unidades de medida
CREATE TABLE IF NOT EXISTS uom (
  id          BIGSERIAL PRIMARY KEY,
  name        VARCHAR(80)  NOT NULL UNIQUE,
  symbol      VARCHAR(16)  NOT NULL,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE uom IS 'Unidades de medida (metros, unidades, litros, etc.)';
COMMENT ON COLUMN uom.symbol IS 'Símbolo de la unidad (m, ud, l, kg, etc.)';

-- Categorías de productos
CREATE TABLE IF NOT EXISTS category (
  id          BIGSERIAL PRIMARY KEY,
  name        VARCHAR(120) NOT NULL UNIQUE,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE category IS 'Categorías de productos (Herramientas, Pintura, Electricidad, etc.)';

-- Productos
CREATE TABLE IF NOT EXISTS product (
  id          BIGSERIAL PRIMARY KEY,
  sku         VARCHAR(64) UNIQUE,
  barcode     VARCHAR(64) UNIQUE,
  name        VARCHAR(200) NOT NULL,
  category_id BIGINT REFERENCES category(id) ON UPDATE RESTRICT ON DELETE SET NULL,
  uom_id      BIGINT NOT NULL REFERENCES uom(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  active      BOOLEAN NOT NULL DEFAULT TRUE,
  sale_price  NUMERIC(12,2) NOT NULL CHECK (sale_price >= 0),
  image_path  VARCHAR(255),  -- MEJORA 1: Ruta de imagen del producto
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE product IS 'Catálogo de productos';
COMMENT ON COLUMN product.sku IS 'Código interno del producto';
COMMENT ON COLUMN product.barcode IS 'Código de barras';
COMMENT ON COLUMN product.active IS 'Indica si el producto está disponible para venta';
COMMENT ON COLUMN product.image_path IS 'Ruta relativa de la imagen del producto (MEJORA 1)';

-- Stock actual de productos (snapshot)
CREATE TABLE IF NOT EXISTS product_stock (
  product_id  BIGINT PRIMARY KEY REFERENCES product(id) ON UPDATE RESTRICT ON DELETE CASCADE,
  on_hand_qty NUMERIC(12,3) NOT NULL DEFAULT 0 CHECK (on_hand_qty >= 0),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE product_stock IS 'Stock actual de cada producto (mantenido por triggers)';
COMMENT ON COLUMN product_stock.on_hand_qty IS 'Cantidad disponible en stock';

-- Trigger: Auto-crear fila en product_stock al insertar producto
CREATE OR REPLACE FUNCTION trg_product_init_stock()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO product_stock(product_id, on_hand_qty)
  VALUES (NEW.id, 0)
  ON CONFLICT (product_id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS product_init_stock ON product;
CREATE TRIGGER product_init_stock
AFTER INSERT ON product
FOR EACH ROW
EXECUTE FUNCTION trg_product_init_stock();

-- ============================================================================
-- VENTAS (POS)
-- ============================================================================

-- Encabezado de venta
CREATE TABLE IF NOT EXISTS sale (
  id         BIGSERIAL PRIMARY KEY,
  datetime   TIMESTAMPTZ NOT NULL DEFAULT now(),
  total      NUMERIC(12,2) NOT NULL CHECK (total >= 0),
  status     sale_status NOT NULL DEFAULT 'CONFIRMED',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE sale IS 'Encabezado de ventas (POS)';
COMMENT ON COLUMN sale.datetime IS 'Fecha y hora de la venta';
COMMENT ON COLUMN sale.total IS 'Total de la venta (debe coincidir con suma de líneas)';

-- Líneas de venta
CREATE TABLE IF NOT EXISTS sale_line (
  id          BIGSERIAL PRIMARY KEY,
  sale_id     BIGINT NOT NULL REFERENCES sale(id) ON UPDATE RESTRICT ON DELETE CASCADE,
  product_id  BIGINT NOT NULL REFERENCES product(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  qty         NUMERIC(12,3) NOT NULL CHECK (qty > 0),
  unit_price  NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
  line_total  NUMERIC(12,2) NOT NULL CHECK (line_total >= 0),
  CONSTRAINT sale_line_total_consistency CHECK (line_total = round(qty * unit_price, 2))
);

COMMENT ON TABLE sale_line IS 'Líneas de detalle de ventas';
COMMENT ON COLUMN sale_line.qty IS 'Cantidad vendida';
COMMENT ON COLUMN sale_line.unit_price IS 'Precio unitario al momento de la venta';
COMMENT ON COLUMN sale_line.line_total IS 'Total de la línea (qty * unit_price redondeado)';

-- ============================================================================
-- PROVEEDORES Y BOLETAS DE COMPRA
-- ============================================================================

-- Proveedores
CREATE TABLE IF NOT EXISTS supplier (
  id         BIGSERIAL PRIMARY KEY,
  name       VARCHAR(200) NOT NULL UNIQUE,
  tax_id     VARCHAR(64),
  phone      VARCHAR(64),
  email      VARCHAR(200),
  notes      TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE supplier IS 'Proveedores de mercadería';
COMMENT ON COLUMN supplier.tax_id IS 'CUIT/DNI del proveedor';

-- Boletas/Facturas de compra
CREATE TABLE IF NOT EXISTS purchase_invoice (
  id             BIGSERIAL PRIMARY KEY,
  supplier_id    BIGINT NOT NULL REFERENCES supplier(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  invoice_number VARCHAR(80) NOT NULL,
  invoice_date   DATE NOT NULL,
  due_date       DATE,
  total_amount   NUMERIC(12,2) NOT NULL CHECK (total_amount >= 0),
  status         invoice_status NOT NULL DEFAULT 'PENDING',
  paid_at        DATE,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT invoice_paid_at_consistency CHECK (
    (status = 'PAID' AND paid_at IS NOT NULL) OR 
    (status = 'PENDING' AND paid_at IS NULL)
  ),
  CONSTRAINT supplier_invoice_number_uniq UNIQUE (supplier_id, invoice_number)
);

COMMENT ON TABLE purchase_invoice IS 'Facturas de compra a proveedores';
COMMENT ON COLUMN purchase_invoice.invoice_number IS 'Número de factura del proveedor';
COMMENT ON COLUMN purchase_invoice.total_amount IS 'Monto total (debe coincidir con suma de líneas)';
COMMENT ON COLUMN purchase_invoice.paid_at IS 'Fecha de pago efectivo';

-- Líneas de boleta/factura de compra
CREATE TABLE IF NOT EXISTS purchase_invoice_line (
  id          BIGSERIAL PRIMARY KEY,
  invoice_id  BIGINT NOT NULL REFERENCES purchase_invoice(id) ON UPDATE RESTRICT ON DELETE CASCADE,
  product_id  BIGINT NOT NULL REFERENCES product(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  qty         NUMERIC(12,3) NOT NULL CHECK (qty > 0),
  unit_cost   NUMERIC(12,4) NOT NULL CHECK (unit_cost >= 0),  -- MEJORA 4: Sin decimales en UI, entero en DB
  line_total  NUMERIC(12,2) NOT NULL CHECK (line_total >= 0),
  CONSTRAINT invoice_line_total_consistency CHECK (line_total = round(qty * unit_cost, 2))
);

COMMENT ON TABLE purchase_invoice_line IS 'Líneas de detalle de facturas de compra';
COMMENT ON COLUMN purchase_invoice_line.unit_cost IS 'Costo unitario (MEJORA 4: validado como entero en backend)';

-- ============================================================================
-- MOVIMIENTOS DE STOCK (Auditoría)
-- ============================================================================

-- Encabezado de movimiento de stock
CREATE TABLE IF NOT EXISTS stock_move (
  id             BIGSERIAL PRIMARY KEY,
  date           TIMESTAMPTZ NOT NULL DEFAULT now(),
  type           stock_move_type NOT NULL,
  reference_type stock_ref_type NOT NULL,
  reference_id   BIGINT,  -- Referencia polimórfica (sale.id, purchase_invoice.id, etc.)
  notes          TEXT
);

COMMENT ON TABLE stock_move IS 'Encabezado de movimientos de stock';
COMMENT ON COLUMN stock_move.type IS 'Tipo: IN (entrada), OUT (salida), ADJUST (ajuste)';
COMMENT ON COLUMN stock_move.reference_type IS 'Tipo de documento origen';
COMMENT ON COLUMN stock_move.reference_id IS 'ID del documento origen (polimórfico)';

-- Líneas de movimiento de stock
CREATE TABLE IF NOT EXISTS stock_move_line (
  id             BIGSERIAL PRIMARY KEY,
  stock_move_id  BIGINT NOT NULL REFERENCES stock_move(id) ON UPDATE RESTRICT ON DELETE CASCADE,
  product_id     BIGINT NOT NULL REFERENCES product(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  qty            NUMERIC(12,3) NOT NULL CHECK (qty > 0),
  uom_id         BIGINT NOT NULL REFERENCES uom(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  unit_cost      NUMERIC(12,4) CHECK (unit_cost >= 0)
);

COMMENT ON TABLE stock_move_line IS 'Líneas de detalle de movimientos de stock';
COMMENT ON COLUMN stock_move_line.unit_cost IS 'Costo unitario (para valorización)';

-- ============================================================================
-- LIBRO MAYOR FINANCIERO
-- ============================================================================

-- Asientos contables
CREATE TABLE IF NOT EXISTS finance_ledger (
  id             BIGSERIAL PRIMARY KEY,
  datetime       TIMESTAMPTZ NOT NULL DEFAULT now(),
  type           ledger_type NOT NULL,
  amount         NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
  category       VARCHAR(80),
  reference_type ledger_ref_type NOT NULL,
  reference_id   BIGINT,  -- Referencia polimórfica
  notes          TEXT
);

COMMENT ON TABLE finance_ledger IS 'Libro mayor de ingresos y egresos';
COMMENT ON COLUMN finance_ledger.type IS 'INCOME (ingreso) o EXPENSE (egreso)';
COMMENT ON COLUMN finance_ledger.amount IS 'Monto del movimiento';
COMMENT ON COLUMN finance_ledger.reference_type IS 'Tipo de documento origen';
COMMENT ON COLUMN finance_ledger.reference_id IS 'ID del documento origen (polimórfico)';

-- ============================================================================
-- ÍNDICES (Optimización de Consultas)
-- ============================================================================

-- Índices en productos
CREATE INDEX IF NOT EXISTS idx_product_category ON product(category_id);
CREATE INDEX IF NOT EXISTS idx_product_uom ON product(uom_id);
CREATE INDEX IF NOT EXISTS idx_product_active ON product(active);
CREATE INDEX IF NOT EXISTS idx_product_name ON product(name);

-- Índice para búsqueda fuzzy (si pg_trgm está habilitado)
-- CREATE INDEX IF NOT EXISTS idx_product_name_trgm ON product USING gin (name gin_trgm_ops);

-- Índices en stock
CREATE INDEX IF NOT EXISTS idx_stock_move_date ON stock_move(date DESC);
CREATE INDEX IF NOT EXISTS idx_stock_move_ref ON stock_move(reference_type, reference_id);
CREATE INDEX IF NOT EXISTS idx_stock_move_line_move ON stock_move_line(stock_move_id);
CREATE INDEX IF NOT EXISTS idx_stock_move_line_prod ON stock_move_line(product_id);

-- Índices en ventas
CREATE INDEX IF NOT EXISTS idx_sale_datetime ON sale(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_sale_status ON sale(status);
CREATE INDEX IF NOT EXISTS idx_sale_line_sale ON sale_line(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_line_product ON sale_line(product_id);

-- Índices en proveedores y boletas
CREATE INDEX IF NOT EXISTS idx_invoice_supplier ON purchase_invoice(supplier_id);
CREATE INDEX IF NOT EXISTS idx_invoice_status ON purchase_invoice(status);
CREATE INDEX IF NOT EXISTS idx_invoice_due_date ON purchase_invoice(due_date);
CREATE INDEX IF NOT EXISTS idx_invoice_date ON purchase_invoice(invoice_date);
CREATE INDEX IF NOT EXISTS idx_invoice_line_invoice ON purchase_invoice_line(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_line_product ON purchase_invoice_line(product_id);

-- Índice para consultas de deuda pendiente
CREATE INDEX IF NOT EXISTS idx_invoice_pending_supplier ON purchase_invoice(supplier_id) WHERE status = 'PENDING';

-- Índices en libro mayor (MEJORA 5 y 6: Balance por período)
CREATE INDEX IF NOT EXISTS idx_ledger_datetime ON finance_ledger(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_ledger_type ON finance_ledger(type);
CREATE INDEX IF NOT EXISTS idx_ledger_ref ON finance_ledger(reference_type, reference_id);

-- Índices para consultas de balance por período (MEJORA 5 y 6)
CREATE INDEX IF NOT EXISTS idx_ledger_datetime_type ON finance_ledger(datetime, type);

-- ============================================================================
-- TRIGGERS DE VALIDACIÓN (Constraint Triggers)
-- ============================================================================

-- Validación: sale debe tener al menos 1 línea
CREATE OR REPLACE FUNCTION chk_sale_has_lines()
RETURNS TRIGGER AS $$
DECLARE
  v_count BIGINT;
BEGIN
  SELECT COUNT(*) INTO v_count FROM sale_line WHERE sale_id = NEW.id;
  IF v_count < 1 THEN
    RAISE EXCEPTION 'SALE % must have at least one sale_line', NEW.id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sale_has_lines ON sale;
CREATE CONSTRAINT TRIGGER trg_sale_has_lines
AFTER INSERT OR UPDATE ON sale
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION chk_sale_has_lines();

-- Validación: sale.total debe coincidir con suma de líneas
CREATE OR REPLACE FUNCTION chk_sale_total_matches_lines()
RETURNS TRIGGER AS $$
DECLARE
  v_sum NUMERIC(12,2);
BEGIN
  SELECT COALESCE(SUM(line_total), 0) INTO v_sum FROM sale_line WHERE sale_id = NEW.id;
  IF NEW.total <> v_sum THEN
    RAISE EXCEPTION 'SALE % total (%) does not match sum(lines) (%)', NEW.id, NEW.total, v_sum;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sale_total_matches_lines ON sale;
CREATE CONSTRAINT TRIGGER trg_sale_total_matches_lines
AFTER INSERT OR UPDATE ON sale
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION chk_sale_total_matches_lines();

-- Validación: purchase_invoice debe tener al menos 1 línea
CREATE OR REPLACE FUNCTION chk_invoice_has_lines()
RETURNS TRIGGER AS $$
DECLARE
  v_count BIGINT;
BEGIN
  SELECT COUNT(*) INTO v_count FROM purchase_invoice_line WHERE invoice_id = NEW.id;
  IF v_count < 1 THEN
    RAISE EXCEPTION 'INVOICE % must have at least one purchase_invoice_line', NEW.id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_invoice_has_lines ON purchase_invoice;
CREATE CONSTRAINT TRIGGER trg_invoice_has_lines
AFTER INSERT OR UPDATE ON purchase_invoice
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION chk_invoice_has_lines();

-- Validación: purchase_invoice.total_amount debe coincidir con suma de líneas
CREATE OR REPLACE FUNCTION chk_invoice_total_matches_lines()
RETURNS TRIGGER AS $$
DECLARE
  v_sum NUMERIC(12,2);
BEGIN
  SELECT COALESCE(SUM(line_total), 0) INTO v_sum FROM purchase_invoice_line WHERE invoice_id = NEW.id;
  IF NEW.total_amount <> v_sum THEN
    RAISE EXCEPTION 'INVOICE % total_amount (%) does not match sum(lines) (%)', NEW.id, NEW.total_amount, v_sum;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_invoice_total_matches_lines ON purchase_invoice;
CREATE CONSTRAINT TRIGGER trg_invoice_total_matches_lines
AFTER INSERT OR UPDATE ON purchase_invoice
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION chk_invoice_total_matches_lines();

-- ============================================================================
-- TRIGGERS DE ACTUALIZACIÓN DE STOCK
-- ============================================================================

-- Función auxiliar: aplicar delta a product_stock
CREATE OR REPLACE FUNCTION apply_stock_delta(p_product_id BIGINT, p_delta NUMERIC)
RETURNS VOID AS $$
BEGIN
  -- Insertar o actualizar stock
  INSERT INTO product_stock(product_id, on_hand_qty, updated_at)
  VALUES (p_product_id, GREATEST(p_delta, 0), now())
  ON CONFLICT (product_id) DO UPDATE 
  SET on_hand_qty = product_stock.on_hand_qty + EXCLUDED.on_hand_qty,
      updated_at = now();
  
  -- Si el delta es negativo, ajustar
  IF p_delta < 0 THEN
    UPDATE product_stock
    SET on_hand_qty = on_hand_qty + p_delta,
        updated_at = now()
    WHERE product_id = p_product_id;
    
    -- Prevenir stock negativo
    IF (SELECT on_hand_qty FROM product_stock WHERE product_id = p_product_id) < 0 THEN
      RAISE EXCEPTION 'Stock would become negative for product_id %', p_product_id;
    END IF;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Trigger: actualizar stock al insertar stock_move_line
CREATE OR REPLACE FUNCTION trg_stock_move_line_after_ins()
RETURNS TRIGGER AS $$
DECLARE
  v_type stock_move_type;
  v_delta NUMERIC(12,3);
BEGIN
  SELECT type INTO v_type FROM stock_move WHERE id = NEW.stock_move_id;
  
  IF v_type = 'IN' THEN
    v_delta := NEW.qty;
  ELSIF v_type = 'OUT' THEN
    v_delta := -NEW.qty;
  ELSE -- ADJUST
    v_delta := NEW.qty;
  END IF;
  
  PERFORM apply_stock_delta(NEW.product_id, v_delta);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS stock_move_line_after_ins ON stock_move_line;
CREATE TRIGGER stock_move_line_after_ins
AFTER INSERT ON stock_move_line
FOR EACH ROW
EXECUTE FUNCTION trg_stock_move_line_after_ins();

-- Trigger: revertir stock al eliminar stock_move_line
CREATE OR REPLACE FUNCTION trg_stock_move_line_after_del()
RETURNS TRIGGER AS $$
DECLARE
  v_type stock_move_type;
  v_delta NUMERIC(12,3);
BEGIN
  SELECT type INTO v_type FROM stock_move WHERE id = OLD.stock_move_id;
  
  IF v_type = 'IN' THEN
    v_delta := -OLD.qty;
  ELSIF v_type = 'OUT' THEN
    v_delta := OLD.qty;
  ELSE -- ADJUST
    v_delta := -OLD.qty;
  END IF;
  
  PERFORM apply_stock_delta(OLD.product_id, v_delta);
  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS stock_move_line_after_del ON stock_move_line;
CREATE TRIGGER stock_move_line_after_del
AFTER DELETE ON stock_move_line
FOR EACH ROW
EXECUTE FUNCTION trg_stock_move_line_after_del();

-- ============================================================================
-- TRIGGER DE UPDATED_AT PARA PRODUCTOS
-- ============================================================================

CREATE OR REPLACE FUNCTION trg_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS product_set_updated_at ON product;
CREATE TRIGGER product_set_updated_at
BEFORE UPDATE ON product
FOR EACH ROW
EXECUTE FUNCTION trg_set_updated_at();

COMMIT;

-- ============================================================================
-- CONSULTAS ÚTILES PARA ADMINISTRACIÓN
-- ============================================================================

-- Balance Diario (últimos 30 días)
-- SELECT 
--   date_trunc('day', datetime) AS day,
--   SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END) AS income,
--   SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) AS expense,
--   SUM(CASE WHEN type='INCOME' THEN amount ELSE -amount END) AS net
-- FROM finance_ledger
-- WHERE datetime >= now() - interval '30 days'
-- GROUP BY 1
-- ORDER BY 1;

-- Balance Mensual (últimos 12 meses)
-- SELECT 
--   date_trunc('month', datetime) AS month,
--   SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END) AS income,
--   SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) AS expense,
--   SUM(CASE WHEN type='INCOME' THEN amount ELSE -amount END) AS net
-- FROM finance_ledger
-- WHERE datetime >= now() - interval '12 months'
-- GROUP BY 1
-- ORDER BY 1;

-- Balance Anual (todos los años)
-- SELECT 
--   date_trunc('year', datetime) AS year,
--   SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END) AS income,
--   SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) AS expense,
--   SUM(CASE WHEN type='INCOME' THEN amount ELSE -amount END) AS net
-- FROM finance_ledger
-- GROUP BY 1
-- ORDER BY 1;

-- Top 10 productos más vendidos
-- SELECT 
--   p.id,
--   p.name,
--   SUM(sl.qty) as total_sold,
--   ps.on_hand_qty as current_stock
-- FROM product p
-- INNER JOIN sale_line sl ON sl.product_id = p.id
-- INNER JOIN sale s ON s.id = sl.sale_id
-- LEFT JOIN product_stock ps ON ps.product_id = p.id
-- WHERE s.status = 'CONFIRMED' AND p.active = TRUE
-- GROUP BY p.id, p.name, ps.on_hand_qty
-- ORDER BY total_sold DESC
-- LIMIT 10;

-- Productos con stock bajo (menos de 10 unidades)
-- SELECT 
--   p.id,
--   p.name,
--   p.sale_price,
--   ps.on_hand_qty
-- FROM product p
-- INNER JOIN product_stock ps ON ps.product_id = p.id
-- WHERE ps.on_hand_qty < 10 AND p.active = TRUE
-- ORDER BY ps.on_hand_qty ASC;

-- Boletas pendientes de pago
-- SELECT 
--   i.id,
--   s.name as supplier,
--   i.invoice_number,
--   i.invoice_date,
--   i.due_date,
--   i.total_amount,
--   (CURRENT_DATE - i.due_date) as days_overdue
-- FROM purchase_invoice i
-- INNER JOIN supplier s ON s.id = i.supplier_id
-- WHERE i.status = 'PENDING'
-- ORDER BY i.due_date ASC;

-- ============================================================================
-- FIN DEL SCHEMA
-- ============================================================================
