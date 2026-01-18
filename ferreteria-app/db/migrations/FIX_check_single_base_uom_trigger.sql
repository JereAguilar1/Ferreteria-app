-- ============================================================================
-- FIX: Trigger check_single_base_uom - Bug al insertar primera UOM
-- ============================================================================
-- 
-- PROBLEMA:
-- El trigger falla al insertar la primera UOM de un producto nuevo porque
-- la validación busca un registro con NEW.id que aún no existe en INSERT.
--
-- ERROR:
-- "El producto debe tener al menos una UOM base"
-- 
-- CAUSA:
-- La condición (id = NEW.id OR NEW.is_base = true) falla en INSERT porque
-- NEW.id es NULL antes de que se complete la inserción.
--
-- SOLUCIÓN:
-- Reescribir la lógica para manejar correctamente INSERT vs UPDATE.
-- ============================================================================

BEGIN;

-- Eliminar trigger existente
DROP TRIGGER IF EXISTS trg_check_single_base_uom ON product_uom_price;

-- Recrear función con lógica corregida
CREATE OR REPLACE FUNCTION check_single_base_uom()
RETURNS TRIGGER AS $$
DECLARE
    base_count INTEGER;
BEGIN
    -- Si se está marcando como base, desmarcar las demás del mismo producto
    IF NEW.is_base = true THEN
        UPDATE product_uom_price
        SET is_base = false
        WHERE product_id = NEW.product_id
          AND id != COALESCE(NEW.id, -1)  -- En INSERT, NEW.id es NULL, usa -1
          AND is_base = true;
    END IF;
    
    -- Validar que después de esta operación haya al menos una UOM base
    -- Contar cuántas UOMs base habrá después de esta operación
    
    IF TG_OP = 'INSERT' THEN
        -- En INSERT, contar las existentes + la nueva si es base
        SELECT COUNT(*) INTO base_count
        FROM product_uom_price
        WHERE product_id = NEW.product_id
          AND is_base = true;
        
        -- Si la nueva es base, sumar 1
        IF NEW.is_base = true THEN
            base_count := base_count + 1;
        END IF;
        
    ELSIF TG_OP = 'UPDATE' THEN
        -- En UPDATE, contar incluyendo el cambio actual
        SELECT COUNT(*) INTO base_count
        FROM product_uom_price
        WHERE product_id = NEW.product_id
          AND is_base = true
          AND id != NEW.id;  -- Excluir el registro actual
        
        -- Si el registro actual será base, sumar 1
        IF NEW.is_base = true THEN
            base_count := base_count + 1;
        END IF;
    END IF;
    
    -- Validar que haya al menos una base
    IF base_count = 0 THEN
        RAISE EXCEPTION 'El producto debe tener al menos una UOM base';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recrear trigger
CREATE TRIGGER trg_check_single_base_uom
    BEFORE INSERT OR UPDATE ON product_uom_price
    FOR EACH ROW
    EXECUTE FUNCTION check_single_base_uom();

COMMIT;

-- ============================================================================
-- Verificación
-- ============================================================================

-- Verificar que cada producto tiene exactamente 1 UOM base
SELECT 
    product_id, 
    COUNT(*) as base_count,
    STRING_AGG(uom_id::text, ', ') as uom_ids
FROM product_uom_price
WHERE is_base = true
GROUP BY product_id
HAVING COUNT(*) != 1;

-- Debe retornar 0 filas
-- Si retorna filas, hay productos con 0 o más de 1 UOM base (problema de datos)

-- Ver todos los productos y sus UOMs base
SELECT 
    p.id,
    p.name,
    COUNT(pup.id) FILTER (WHERE pup.is_base = true) as base_count,
    COUNT(pup.id) as total_uoms
FROM product p
LEFT JOIN product_uom_price pup ON pup.product_id = p.id
GROUP BY p.id, p.name
ORDER BY base_count, p.id;

-- ============================================================================
-- Testing
-- ============================================================================

-- Test 1: Insertar primera UOM con is_base=true (debe funcionar)
-- INSERT INTO product_uom_price (product_id, uom_id, sale_price, conversion_to_base, is_base)
-- VALUES (1, 1, 100.00, 1.00, true);

-- Test 2: Insertar segunda UOM con is_base=false (debe funcionar)
-- INSERT INTO product_uom_price (product_id, uom_id, sale_price, conversion_to_base, is_base)
-- VALUES (1, 2, 1200.00, 12.00, false);

-- Test 3: Intentar cambiar la única UOM base a false (debe fallar)
-- UPDATE product_uom_price SET is_base = false WHERE product_id = 1 AND is_base = true;

-- Test 4: Cambiar la base a otra UOM (debe funcionar y desmarcar la anterior)
-- UPDATE product_uom_price SET is_base = true WHERE product_id = 1 AND uom_id = 2;
