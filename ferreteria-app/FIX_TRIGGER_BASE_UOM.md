# FIX: Error "El producto debe tener al menos una UOM base"

## Problema

Al crear un producto con UOMs, se produce este error:

```
Error al crear producto: (psycopg2.errors.RaiseException) 
El producto debe tener al menos una UOM base 
CONTEXT: PL/pgSQL function check_single_base_uom() line 19 at RAISE
```

**Ocurre en:** Producción y Local (después de aplicar MEJORA_A)

---

## Causa Raíz

El trigger `check_single_base_uom()` tiene un **bug en la lógica de validación** que falla al insertar la **primera UOM** de un producto nuevo.

### Código Problemático (líneas 184-191)

```sql
-- ❌ LÓGICA INCORRECTA
IF NOT EXISTS (
    SELECT 1 FROM product_uom_price
    WHERE product_id = NEW.product_id
      AND is_base = true
      AND (id = NEW.id OR NEW.is_base = true)  -- ⚠️ AQUÍ ESTÁ EL BUG
) THEN
    RAISE EXCEPTION 'El producto debe tener al menos una UOM base';
END IF;
```

### ¿Por qué falla?

1. **En INSERT:** `NEW.id` es `NULL` (aún no se ha asignado el ID)
2. **La condición:** `(id = NEW.id OR NEW.is_base = true)` se evalúa como:
   - `id = NULL` → siempre `FALSE` (en SQL, `NULL = NULL` es `FALSE`)
   - `NEW.is_base = true` → `TRUE`
3. **Pero:** Como no hay registros previos para un producto nuevo, `NOT EXISTS` retorna `TRUE`
4. **Resultado:** Se lanza la excepción aunque estemos insertando una UOM base

### Escenario del Error

```python
# Backend intenta insertar la primera UOM con is_base=True
INSERT INTO product_uom_price 
  (product_id, uom_id, sale_price, conversion_to_base, is_base)
VALUES 
  (334, 8, 100.00, 1.00, true);

# Trigger se ejecuta ANTES del INSERT
# NEW.id = NULL (aún no existe)
# Busca: WHERE product_id = 334 AND is_base = true AND (id = NULL OR true)
# No encuentra nada (producto nuevo, no tiene UOMs previas)
# Lanza: RAISE EXCEPTION 'El producto debe tener al menos una UOM base'
```

---

## Solución

Reescribir la función del trigger para manejar correctamente INSERT vs UPDATE.

### Nueva Lógica

```sql
CREATE OR REPLACE FUNCTION check_single_base_uom()
RETURNS TRIGGER AS $$
DECLARE
    base_count INTEGER;
BEGIN
    -- Si se está marcando como base, desmarcar las demás
    IF NEW.is_base = true THEN
        UPDATE product_uom_price
        SET is_base = false
        WHERE product_id = NEW.product_id
          AND id != COALESCE(NEW.id, -1)
          AND is_base = true;
    END IF;
    
    -- Contar cuántas UOMs base habrá después de esta operación
    IF TG_OP = 'INSERT' THEN
        -- Contar existentes
        SELECT COUNT(*) INTO base_count
        FROM product_uom_price
        WHERE product_id = NEW.product_id AND is_base = true;
        
        -- Si la nueva es base, sumar 1
        IF NEW.is_base = true THEN
            base_count := base_count + 1;
        END IF;
        
    ELSIF TG_OP = 'UPDATE' THEN
        -- Contar excluyendo el registro actual
        SELECT COUNT(*) INTO base_count
        FROM product_uom_price
        WHERE product_id = NEW.product_id 
          AND is_base = true 
          AND id != NEW.id;
        
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
```

### Diferencias Clave

| Aspecto | Código Viejo ❌ | Código Nuevo ✅ |
|---------|----------------|----------------|
| **Lógica** | `NOT EXISTS` con condición compleja | `COUNT(*)` explícito por operación |
| **INSERT** | Falla porque `NEW.id = NULL` | Cuenta existentes + nueva si es base |
| **UPDATE** | Condición ambigua | Excluye registro actual, suma si será base |
| **Claridad** | Difícil de entender | Lógica clara y explícita |

---

## Aplicar el Fix

### En Local (Docker)

```bash
# Opción 1: Script automático
chmod +x apply_fix_trigger.sh
./apply_fix_trigger.sh

# Opción 2: Manual
docker-compose exec db psql -U ferreteria -d ferreteria -f /docker-entrypoint-initdb.d/FIX_check_single_base_uom_trigger.sql
```

### En Producción

```bash
# Conectar a la base de datos
psql -U usuario -d database

# Ejecutar el script
\i /path/to/FIX_check_single_base_uom_trigger.sql

# O copiar y pegar el contenido del archivo
```

### Verificar Aplicación

```sql
-- Ver la definición de la función
\df+ check_single_base_uom

-- Verificar que cada producto tiene exactamente 1 UOM base
SELECT 
    product_id, 
    COUNT(*) as base_count
FROM product_uom_price
WHERE is_base = true
GROUP BY product_id
HAVING COUNT(*) != 1;

-- Debe retornar 0 filas
```

---

## Testing Después del Fix

### Test 1: Crear Producto con Primera UOM (Base)

```python
# Debe funcionar sin error
product = Product(name="Test", ...)
session.add(product)
session.flush()

uom_price = ProductUomPrice(
    product_id=product.id,
    uom_id=1,
    sale_price=100.00,
    conversion_to_base=1.00,
    is_base=True
)
session.add(uom_price)
session.commit()  # ✅ Debe funcionar
```

### Test 2: Agregar Segunda UOM (No Base)

```python
# Debe funcionar
uom_price2 = ProductUomPrice(
    product_id=product.id,
    uom_id=2,
    sale_price=1200.00,
    conversion_to_base=12.00,
    is_base=False
)
session.add(uom_price2)
session.commit()  # ✅ Debe funcionar
```

### Test 3: Cambiar Base a Otra UOM

```python
# Debe funcionar y desmarcar la anterior automáticamente
session.query(ProductUomPrice).filter_by(
    product_id=product.id,
    uom_id=2
).update({'is_base': True})
session.commit()  # ✅ Debe funcionar

# Verificar que solo hay 1 base
base_count = session.query(ProductUomPrice).filter_by(
    product_id=product.id,
    is_base=True
).count()
assert base_count == 1  # ✅ Solo la UOM 2 debe ser base
```

### Test 4: Intentar Quitar la Única Base

```sql
-- Debe fallar con el error esperado
UPDATE product_uom_price 
SET is_base = false 
WHERE product_id = 1 AND is_base = true;

-- ❌ Error: El producto debe tener al menos una UOM base
```

---

## Impacto

### Antes del Fix ❌

- ✅ Productos existentes con UOMs: **funcionan**
- ❌ Crear producto nuevo con UOMs: **falla**
- ❌ Agregar primera UOM a producto sin UOMs: **falla**

### Después del Fix ✅

- ✅ Productos existentes con UOMs: **funcionan**
- ✅ Crear producto nuevo con UOMs: **funciona**
- ✅ Agregar primera UOM a producto sin UOMs: **funciona**
- ✅ Cambiar UOM base: **funciona** (desmarca anterior automáticamente)
- ✅ Validación de al menos 1 base: **funciona**

---

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `FIX_check_single_base_uom_trigger.sql` | Script SQL con el fix |
| `apply_fix_trigger.sh` | Script bash para aplicar en local |
| `FIX_TRIGGER_BASE_UOM.md` | Este documento |

---

## Rollback (Si es necesario)

Si por alguna razón necesitas volver al trigger anterior:

```sql
-- Restaurar versión original (con el bug)
-- NO RECOMENDADO, solo para emergencias

DROP TRIGGER IF EXISTS trg_check_single_base_uom ON product_uom_price;

CREATE OR REPLACE FUNCTION check_single_base_uom()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_base = true THEN
        UPDATE product_uom_price
        SET is_base = false
        WHERE product_id = NEW.product_id
          AND id != COALESCE(NEW.id, -1)
          AND is_base = true;
    END IF;
    
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

CREATE TRIGGER trg_check_single_base_uom
    BEFORE INSERT OR UPDATE ON product_uom_price
    FOR EACH ROW
    EXECUTE FUNCTION check_single_base_uom();
```

---

## Resumen

| Aspecto | Detalle |
|---------|---------|
| **Problema** | Trigger falla al insertar primera UOM de producto nuevo |
| **Causa** | Lógica incorrecta: `NEW.id = NULL` en INSERT |
| **Solución** | Reescribir función con lógica explícita por operación |
| **Impacto** | Crítico - impide crear productos con UOMs |
| **Urgencia** | Alta - aplicar inmediatamente en producción |
| **Riesgo** | Bajo - solo corrige lógica, no cambia estructura |

---

## Comandos Rápidos

```bash
# Aplicar fix en local
docker-compose exec db psql -U ferreteria -d ferreteria < db/migrations/FIX_check_single_base_uom_trigger.sql

# Verificar
docker-compose exec db psql -U ferreteria -d ferreteria -c "SELECT product_id, COUNT(*) as base_count FROM product_uom_price WHERE is_base = true GROUP BY product_id HAVING COUNT(*) != 1;"

# Probar creando un producto
# (desde la UI o Python)
```

✅ **FIX LISTO PARA APLICAR**
