-- PostgreSQL DDL for Ferretería: Productos/Stock/Ventas/Proveedores/Boletas/Balance
-- Target: PostgreSQL 13+ (recommended 14+)
-- Notes:
-- 1) reference_type/reference_id are "polymorphic" references (no FK).
-- 2) We enforce: SALE must have >=1 line, PURCHASE_INVOICE must have >=1 line,
--    and totals must match sum(lines) via DEFERRABLE constraint triggers.
-- 3) product_stock is maintained automatically from stock_move + stock_move_line via triggers.

BEGIN;

-- Optional (recommended) for better product search:
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =========================
-- ENUM TYPES
-- =========================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sale_status') THEN
    CREATE TYPE sale_status AS ENUM ('CONFIRMED', 'CANCELLED');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'invoice_status') THEN
    CREATE TYPE invoice_status AS ENUM ('PENDING', 'PAID');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'stock_move_type') THEN
    CREATE TYPE stock_move_type AS ENUM ('IN', 'OUT', 'ADJUST');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'stock_ref_type') THEN
    CREATE TYPE stock_ref_type AS ENUM ('SALE', 'INVOICE', 'MANUAL');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ledger_type') THEN
    CREATE TYPE ledger_type AS ENUM ('INCOME', 'EXPENSE');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ledger_ref_type') THEN
    CREATE TYPE ledger_ref_type AS ENUM ('SALE', 'INVOICE_PAYMENT', 'MANUAL');
  END IF;
END$$;


-- =========================
-- MASTER DATA
-- =========================
CREATE TABLE IF NOT EXISTS uom (
  id          BIGSERIAL PRIMARY KEY,
  name        VARCHAR(80)  NOT NULL UNIQUE,
  symbol      VARCHAR(16)  NOT NULL,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS category (
  id          BIGSERIAL PRIMARY KEY,
  name        VARCHAR(120) NOT NULL UNIQUE,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product (
  id          BIGSERIAL PRIMARY KEY,
  sku         VARCHAR(64) UNIQUE,
  barcode     VARCHAR(64) UNIQUE,
  name        VARCHAR(200) NOT NULL,
  category_id BIGINT REFERENCES category(id) ON UPDATE RESTRICT ON DELETE SET NULL,
  uom_id      BIGINT NOT NULL REFERENCES uom(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  active      BOOLEAN NOT NULL DEFAULT TRUE,
  sale_price  NUMERIC(12,2) NOT NULL CHECK (sale_price >= 0),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Stock current snapshot (fast reads)
CREATE TABLE IF NOT EXISTS product_stock (
  product_id  BIGINT PRIMARY KEY REFERENCES product(id) ON UPDATE RESTRICT ON DELETE CASCADE,
  on_hand_qty NUMERIC(12,3) NOT NULL DEFAULT 0 CHECK (on_hand_qty >= 0),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Auto-create product_stock row on product creation (optional convenience)
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

-- =========================
-- SALES (no payment method, no ticket)
-- =========================
CREATE TABLE IF NOT EXISTS sale (
  id          BIGSERIAL PRIMARY KEY,
  datetime    TIMESTAMPTZ NOT NULL DEFAULT now(),
  total       NUMERIC(12,2) NOT NULL CHECK (total >= 0),
  status      sale_status NOT NULL DEFAULT 'CONFIRMED',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sale_line (
  id          BIGSERIAL PRIMARY KEY,
  sale_id     BIGINT NOT NULL REFERENCES sale(id) ON UPDATE RESTRICT ON DELETE CASCADE,
  product_id  BIGINT NOT NULL REFERENCES product(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  qty         NUMERIC(12,3) NOT NULL CHECK (qty > 0),
  unit_price  NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
  line_total  NUMERIC(12,2) NOT NULL CHECK (line_total >= 0),
  CONSTRAINT sale_line_total_consistency CHECK (line_total = round(qty * unit_price, 2))
);

-- =========================
-- SUPPLIERS + INVOICES (items mandatory)
-- =========================
CREATE TABLE IF NOT EXISTS supplier (
  id          BIGSERIAL PRIMARY KEY,
  name        VARCHAR(200) NOT NULL UNIQUE,
  tax_id      VARCHAR(64),
  phone       VARCHAR(64),
  email       VARCHAR(200),
  notes       TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS purchase_invoice (
  id            BIGSERIAL PRIMARY KEY,
  supplier_id   BIGINT NOT NULL REFERENCES supplier(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  invoice_number VARCHAR(80) NOT NULL,
  invoice_date  DATE NOT NULL,
  due_date      DATE,
  total_amount  NUMERIC(12,2) NOT NULL CHECK (total_amount >= 0),
  status        invoice_status NOT NULL DEFAULT 'PENDING',
  paid_at       DATE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT invoice_paid_at_consistency CHECK (
    (status = 'PAID' AND paid_at IS NOT NULL) OR
    (status = 'PENDING' AND paid_at IS NULL)
  ),
  CONSTRAINT supplier_invoice_number_uniq UNIQUE (supplier_id, invoice_number)
);

CREATE TABLE IF NOT EXISTS purchase_invoice_line (
  id          BIGSERIAL PRIMARY KEY,
  invoice_id  BIGINT NOT NULL REFERENCES purchase_invoice(id) ON UPDATE RESTRICT ON DELETE CASCADE,
  product_id  BIGINT NOT NULL REFERENCES product(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  qty         NUMERIC(12,3) NOT NULL CHECK (qty > 0),
  unit_cost   NUMERIC(12,4) NOT NULL CHECK (unit_cost >= 0),
  line_total  NUMERIC(12,2) NOT NULL CHECK (line_total >= 0),
  CONSTRAINT invoice_line_total_consistency CHECK (line_total = round(qty * unit_cost, 2))
);

-- =========================
-- STOCK MOVES (audit + source of truth)
-- =========================
CREATE TABLE IF NOT EXISTS stock_move (
  id             BIGSERIAL PRIMARY KEY,
  date           TIMESTAMPTZ NOT NULL DEFAULT now(),
  type           stock_move_type NOT NULL,
  reference_type stock_ref_type NOT NULL,
  reference_id   BIGINT,
  notes          TEXT
);

CREATE TABLE IF NOT EXISTS stock_move_line (
  id            BIGSERIAL PRIMARY KEY,
  stock_move_id BIGINT NOT NULL REFERENCES stock_move(id) ON UPDATE RESTRICT ON DELETE CASCADE,
  product_id    BIGINT NOT NULL REFERENCES product(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  qty           NUMERIC(12,3) NOT NULL CHECK (qty > 0),
  uom_id        BIGINT NOT NULL REFERENCES uom(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  unit_cost     NUMERIC(12,4) CHECK (unit_cost >= 0)
);

-- =========================
-- FINANCE LEDGER (Balance: daily/monthly/yearly)
-- =========================
CREATE TABLE IF NOT EXISTS finance_ledger (
  id             BIGSERIAL PRIMARY KEY,
  datetime       TIMESTAMPTZ NOT NULL DEFAULT now(),
  type           ledger_type NOT NULL,
  amount         NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
  category       VARCHAR(80),
  reference_type ledger_ref_type NOT NULL,
  reference_id   BIGINT,
  notes          TEXT
);

-- =========================
-- INDEXES
-- =========================
-- Product search & relations
CREATE INDEX IF NOT EXISTS idx_product_category     ON product(category_id);
CREATE INDEX IF NOT EXISTS idx_product_uom          ON product(uom_id);
CREATE INDEX IF NOT EXISTS idx_product_active       ON product(active);
CREATE INDEX IF NOT EXISTS idx_product_name         ON product(name);
-- Optional: fuzzy search
-- CREATE INDEX IF NOT EXISTS idx_product_name_trgm ON product USING gin (name gin_trgm_ops);

-- Stock
CREATE INDEX IF NOT EXISTS idx_stock_move_date      ON stock_move(date DESC);
CREATE INDEX IF NOT EXISTS idx_stock_move_ref       ON stock_move(reference_type, reference_id);
CREATE INDEX IF NOT EXISTS idx_stock_move_line_move ON stock_move_line(stock_move_id);
CREATE INDEX IF NOT EXISTS idx_stock_move_line_prod ON stock_move_line(product_id);

-- Sales
CREATE INDEX IF NOT EXISTS idx_sale_datetime        ON sale(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_sale_status          ON sale(status);
CREATE INDEX IF NOT EXISTS idx_sale_line_sale       ON sale_line(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_line_product    ON sale_line(product_id);

-- Suppliers / invoices
CREATE INDEX IF NOT EXISTS idx_invoice_supplier     ON purchase_invoice(supplier_id);
CREATE INDEX IF NOT EXISTS idx_invoice_status       ON purchase_invoice(status);
CREATE INDEX IF NOT EXISTS idx_invoice_due_date     ON purchase_invoice(due_date);
CREATE INDEX IF NOT EXISTS idx_invoice_date         ON purchase_invoice(invoice_date);
CREATE INDEX IF NOT EXISTS idx_invoice_line_invoice ON purchase_invoice_line(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_line_product ON purchase_invoice_line(product_id);
-- Fast "debt" queries
CREATE INDEX IF NOT EXISTS idx_invoice_pending_supplier
  ON purchase_invoice(supplier_id)
  WHERE status = 'PENDING';

-- Finance ledger balance
CREATE INDEX IF NOT EXISTS idx_ledger_datetime      ON finance_ledger(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_ledger_type          ON finance_ledger(type);
CREATE INDEX IF NOT EXISTS idx_ledger_ref           ON finance_ledger(reference_type, reference_id);

-- =========================
-- CONSTRAINT TRIGGERS (DEFERRABLE): enforce lines exist + totals match
-- =========================

-- Helper: sale must have >=1 line
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

-- Helper: sale.total must match sum(line_total)
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

-- Helper: invoice must have >=1 line (mandatory items)
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

-- Helper: invoice.total_amount must match sum(line_total)
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

-- DEFERRABLE constraint triggers on parent rows
DROP TRIGGER IF EXISTS trg_sale_has_lines ON sale;
CREATE CONSTRAINT TRIGGER trg_sale_has_lines
AFTER INSERT OR UPDATE ON sale
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION chk_sale_has_lines();

DROP TRIGGER IF EXISTS trg_sale_total_matches_lines ON sale;
CREATE CONSTRAINT TRIGGER trg_sale_total_matches_lines
AFTER INSERT OR UPDATE ON sale
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION chk_sale_total_matches_lines();

DROP TRIGGER IF EXISTS trg_invoice_has_lines ON purchase_invoice;
CREATE CONSTRAINT TRIGGER trg_invoice_has_lines
AFTER INSERT OR UPDATE ON purchase_invoice
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION chk_invoice_has_lines();

DROP TRIGGER IF EXISTS trg_invoice_total_matches_lines ON purchase_invoice;
CREATE CONSTRAINT TRIGGER trg_invoice_total_matches_lines
AFTER INSERT OR UPDATE ON purchase_invoice
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION chk_invoice_total_matches_lines();

-- =========================
-- STOCK SNAPSHOT MAINTENANCE (product_stock)
-- =========================
-- Applies delta to product_stock whenever stock_move_line is inserted/deleted.
-- IMPORTANT: This assumes stock_move_line rows are immutable after insert in normal operation.
CREATE OR REPLACE FUNCTION apply_stock_delta(p_product_id BIGINT, p_delta NUMERIC)
RETURNS VOID AS $$
BEGIN
  INSERT INTO product_stock(product_id, on_hand_qty, updated_at)
  VALUES (p_product_id, GREATEST(p_delta, 0), now())
  ON CONFLICT (product_id) DO UPDATE
    SET on_hand_qty = product_stock.on_hand_qty + EXCLUDED.on_hand_qty,
        updated_at  = now();

  -- If delta is negative, we must subtract (we handle separately to keep GREATEST logic simple)
  IF p_delta < 0 THEN
    UPDATE product_stock
      SET on_hand_qty = on_hand_qty + p_delta,
          updated_at  = now()
    WHERE product_id = p_product_id;

    -- Prevent negative stock at DB level
    IF (SELECT on_hand_qty FROM product_stock WHERE product_id = p_product_id) < 0 THEN
      RAISE EXCEPTION 'Stock would become negative for product_id %', p_product_id;
    END IF;
  END IF;
END;
$$ LANGUAGE plpgsql;

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
  ELSE
    -- ADJUST: treat as signed via notes? For simplicity, use qty as positive and require MANUAL logic in app.
    -- If you want signed adjustments, add column "signed_qty" instead.
    v_delta := NEW.qty;
  END IF;

  PERFORM apply_stock_delta(NEW.product_id, v_delta);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

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
  ELSE
    v_delta := -OLD.qty;
  END IF;

  PERFORM apply_stock_delta(OLD.product_id, v_delta);
  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS stock_move_line_after_ins ON stock_move_line;
CREATE TRIGGER stock_move_line_after_ins
AFTER INSERT ON stock_move_line
FOR EACH ROW
EXECUTE FUNCTION trg_stock_move_line_after_ins();

DROP TRIGGER IF EXISTS stock_move_line_after_del ON stock_move_line;
CREATE TRIGGER stock_move_line_after_del
AFTER DELETE ON stock_move_line
FOR EACH ROW
EXECUTE FUNCTION trg_stock_move_line_after_del();

-- =========================
-- UPDATED_AT helper for product
-- =========================
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

-- =========================
-- Recommended BALANCE queries (examples)
-- =========================
-- Daily:
-- SELECT date_trunc('day', datetime) AS day,
--        SUM(CASE WHEN type='INCOME'  THEN amount ELSE 0 END) AS income,
--        SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) AS expense,
--        SUM(CASE WHEN type='INCOME'  THEN amount ELSE -amount END) AS net
-- FROM finance_ledger
-- WHERE datetime >= now() - interval '30 days'
-- GROUP BY 1
-- ORDER BY 1;

-- Monthly:
-- SELECT date_trunc('month', datetime) AS month,
--        SUM(CASE WHEN type='INCOME'  THEN amount ELSE 0 END) AS income,
--        SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) AS expense,
--        SUM(CASE WHEN type='INCOME'  THEN amount ELSE -amount END) AS net
-- FROM finance_ledger
-- GROUP BY 1
-- ORDER BY 1;

-- Annual:
-- SELECT date_trunc('year', datetime) AS year,
--        SUM(CASE WHEN type='INCOME'  THEN amount ELSE 0 END) AS income,
--        SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) AS expense,
--        SUM(CASE WHEN type='INCOME'  THEN amount ELSE -amount END) AS net
-- FROM finance_ledger
-- GROUP BY 1
-- ORDER BY 1;
