-- MEJORA A: Múltiples UOM y Precios por Producto
-- Permite que un producto se venda en diferentes unidades de medida
-- con precios distintos (ej: Cable por metro o por rollo)

BEGIN;

-- ============================================================================
-- 1. Crear tabla product_uom_price
-- ============================================================================

CREATE TABLE IF NOT EXISTS product_uom_price (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    uom_id BIGINT NOT NULL,
    sale_price NUMERIC(12, 2) NOT NULL CHECK (sale_price >= 0),
    conversion_to_base NUMERIC(12, 4) NOT NULL DEFAULT 1 CHECK (conversion_to_base > 0),
    is_base BOOLEAN NOT NULL DEFAULT false,
    sku VARCHAR(255),
    barcode VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    CONSTRAINT fk_product_uom_price_product
        FOREIGN KEY (product_id)
        REFERENCES product(id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_product_uom_price_uom
        FOREIGN KEY (uom_id)
        REFERENCES uom(id),
    
    CONSTRAINT uq_product_uom
        UNIQUE (product_id, uom_id)
);

-- Índices para optimizar queries
CREATE INDEX IF NOT EXISTS idx_product_uom_price_product_id 
    ON product_uom_price(product_id);

CREATE INDEX IF NOT EXISTS idx_product_uom_price_uom_id 
    ON product_uom_price(uom_id);

CREATE INDEX IF NOT EXISTS idx_product_uom_price_is_base 
    ON product_uom_price(product_id, is_base) 
    WHERE is_base = true;

-- Comentarios
COMMENT ON TABLE product_uom_price IS 
    'Precios y UOMs por producto. Permite vender un producto en múltiples unidades.';

COMMENT ON COLUMN product_uom_price.conversion_to_base IS 
    'Factor de conversión a la unidad base. Ej: 1 rollo = 100 metros → conversion_to_base = 100';

COMMENT ON COLUMN product_uom_price.is_base IS 
    'Indica si esta es la UOM base del producto (solo una por producto debe ser true)';

-- ============================================================================
-- 2. Poblar con datos existentes
-- ============================================================================

-- Para cada producto existente, crear una entrada con su UOM actual
-- como UOM base
INSERT INTO product_uom_price (
    product_id, 
    uom_id, 
    sale_price, 
    conversion_to_base, 
    is_base,
    sku,
    barcode,
    created_at
)
SELECT 
    p.id AS product_id,
    p.uom_id,
    p.sale_price,
    1.0 AS conversion_to_base,  -- La UOM actual es la base
    true AS is_base,
    p.sku,
    p.barcode,
    p.created_at
FROM product p
WHERE NOT EXISTS (
    SELECT 1 FROM product_uom_price pup 
    WHERE pup.product_id = p.id AND pup.uom_id = p.uom_id
);

-- ============================================================================
-- 3. Agregar columnas a sale_line (para guardar UOM usada en venta)
-- ============================================================================

-- Agregar uom_id si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sale_line' AND column_name = 'uom_id'
    ) THEN
        ALTER TABLE sale_line 
        ADD COLUMN uom_id BIGINT;
        
        ALTER TABLE sale_line
        ADD CONSTRAINT fk_sale_line_uom
        FOREIGN KEY (uom_id) REFERENCES uom(id);
    END IF;
END $$;

-- Agregar unit_price si no existe (para congelar precio al momento de venta)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sale_line' AND column_name = 'unit_price'
    ) THEN
        ALTER TABLE sale_line 
        ADD COLUMN unit_price NUMERIC(12, 2);
    END IF;
END $$;

-- Backfill: Setear uom_id y unit_price para ventas existentes
UPDATE sale_line sl
SET uom_id = p.uom_id,
    unit_price = COALESCE(sl.unit_price, p.sale_price)
FROM product p
WHERE sl.product_id = p.id
  AND sl.uom_id IS NULL;

-- Hacer columnas NOT NULL después del backfill
ALTER TABLE sale_line 
ALTER COLUMN uom_id SET NOT NULL;

ALTER TABLE sale_line 
ALTER COLUMN unit_price SET NOT NULL;

-- ============================================================================
-- 4. Agregar columnas a stock_move_line (para trazabilidad)
-- ============================================================================

-- Agregar uom_id si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'stock_move_line' AND column_name = 'uom_id'
    ) THEN
        ALTER TABLE stock_move_line 
        ADD COLUMN uom_id BIGINT;
        
        ALTER TABLE stock_move_line
        ADD CONSTRAINT fk_stock_move_line_uom
        FOREIGN KEY (uom_id) REFERENCES uom(id);
    END IF;
END $$;

-- Backfill: Setear uom_id para movimientos existentes
UPDATE stock_move_line sml
SET uom_id = p.uom_id
FROM product p
WHERE sml.product_id = p.id
  AND sml.uom_id IS NULL;

-- Hacer columna NOT NULL después del backfill
ALTER TABLE stock_move_line 
ALTER COLUMN uom_id SET NOT NULL;

-- ============================================================================
-- 5. Constraint: Solo una UOM base por producto
-- ============================================================================

-- Crear función para validar
CREATE OR REPLACE FUNCTION check_single_base_uom()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_base = true THEN
        -- Si se está marcando como base, desmarcar las demás del mismo producto
        UPDATE product_uom_price
        SET is_base = false
        WHERE product_id = NEW.product_id
          AND id != COALESCE(NEW.id, -1)
          AND is_base = true;
    END IF;
    
    -- Validar que al menos una sea base
    IF NOT EXISTS (
        SELECT 1 FROM product_uom_price
        WHERE product_id = NEW.product_id
          AND is_base = true
          AND (id = NEW.id OR NEW.is_base = true)
    ) THEN
        RAISE EXCEPTION 'El producto debe tener al menos una UOM base';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger
DROP TRIGGER IF EXISTS trg_check_single_base_uom ON product_uom_price;
CREATE TRIGGER trg_check_single_base_uom
    BEFORE INSERT OR UPDATE ON product_uom_price
    FOR EACH ROW
    EXECUTE FUNCTION check_single_base_uom();

-- ============================================================================
-- 6. Verificación
-- ============================================================================

-- Query de verificación (ejecutar después de migración):
-- 
-- -- Ver UOMs por producto
-- SELECT 
--     p.id,
--     p.name,
--     pup.uom_id,
--     u.symbol,
--     pup.sale_price,
--     pup.conversion_to_base,
--     pup.is_base
-- FROM product p
-- JOIN product_uom_price pup ON pup.product_id = p.id
-- JOIN uom u ON u.id = pup.uom_id
-- ORDER BY p.id, pup.is_base DESC, pup.uom_id;
--
-- -- Verificar que cada producto tiene exactamente 1 UOM base
-- SELECT product_id, COUNT(*) as base_count
-- FROM product_uom_price
-- WHERE is_base = true
-- GROUP BY product_id
-- HAVING COUNT(*) != 1;
-- -- Debe retornar 0 filas

COMMIT;

-- ============================================================================
-- Rollback (si es necesario deshacer la migración)
-- ============================================================================

-- BEGIN;
-- DROP TRIGGER IF EXISTS trg_check_single_base_uom ON product_uom_price;
-- DROP FUNCTION IF EXISTS check_single_base_uom();
-- ALTER TABLE stock_move_line DROP COLUMN IF EXISTS uom_id;
-- ALTER TABLE sale_line DROP COLUMN IF EXISTS unit_price;
-- ALTER TABLE sale_line DROP COLUMN IF EXISTS uom_id;
-- DROP TABLE IF EXISTS product_uom_price CASCADE;
-- COMMIT;
