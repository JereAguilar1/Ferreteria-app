# FIX: Product UOM Price Schema - Columnas faltantes (sku/barcode)

## Problema
El modelo SQLAlchemy `ProductUomPrice` incluía columnas `sku` y `barcode` que no existían en la tabla de la base de datos, causando errores al cargar/editar productos.

## Causa Raíz
- La migración `MEJORA_A_multiple_uom_prices.sql` creó la tabla sin las columnas `sku` y `barcode`
- El modelo Python incluía estas columnas por error
- No había funcionalidad real que usara SKU/barcode por variante UOM

## Solución Aplicada
**Estrategia A**: Eliminar `sku` y `barcode` del modelo (no se necesitan)

### Cambios realizados:
1. **Modelo `ProductUomPrice`** (`app/models/product_uom_price.py`):
   - ❌ Eliminado: `sku = Column(String(255), nullable=True)`
   - ❌ Eliminado: `barcode = Column(String(255), nullable=True)`
   - ✅ Mantenido: `updated_at` (existe en DB)

2. **Servicio `product_uom_service.py`**:
   - Actualizada documentación para no mencionar `sku`/`barcode`

3. **Blueprint `catalog.py`**:
   - Eliminadas referencias a `'sku': sku` y `'barcode': barcode` en `uom_prices_data`

## Esquema Final de `product_uom_price`

```sql
Table "public.product_uom_price"
       Column       |           Type           | Nullable |                    Default                    
--------------------+--------------------------+----------+-----------------------------------------------
 id                 | bigint                   | not null | nextval('product_uom_price_id_seq'::regclass)
 product_id         | bigint                   | not null | 
 uom_id             | bigint                   | not null | 
 sale_price         | numeric(12,2)            | not null | 
 conversion_to_base | numeric(12,4)            | not null | 1
 is_base            | boolean                  | not null | false
 created_at         | timestamp with time zone | not null | now()
 updated_at         | timestamp with time zone | not null | now()
```

---

## Testing

### Pre-requisitos
- Sistema levantado
- Base de datos con productos existentes
- Migración MEJORA_A aplicada

---

### Test 1: Listar productos sin error

**Pasos:**
1. Ir a `/products`

**Resultado esperado:**
- ✅ La página carga sin errores
- ✅ Se muestran todos los productos
- ✅ No aparece error de columna inexistente

---

### Test 2: Editar producto con UOMs existentes

**Pasos:**
1. Seleccionar un producto que tenga múltiples UOMs
2. Click en "Editar"
3. Verificar que se cargan las UOMs existentes

**Resultado esperado:**
- ✅ Página de edición carga correctamente
- ✅ Se muestran todas las UOMs del producto
- ✅ Precios, factores de conversión y "¿Base?" se cargan correctamente
- ✅ No hay error de columna `sku` o `barcode`

---

### Test 3: Crear producto con múltiples UOMs

**Pasos:**
1. Ir a `/products/new`
2. Completar datos básicos del producto
3. Agregar 2 UOMs:
   - UOM 1: Metro, Precio 100, Factor 1, Base: Sí
   - UOM 2: Rollo, Precio 9500, Factor 100, Base: No
4. Click en "Crear Producto"

**Resultado esperado:**
- ✅ Producto se crea exitosamente
- ✅ Mensaje: "Producto creado exitosamente"
- ✅ En DB: 2 filas en `product_uom_price` para este producto

**Verificación en DB:**
```sql
SELECT id, product_id, uom_id, sale_price, conversion_to_base, is_base
FROM product_uom_price
WHERE product_id = <NUEVO_PRODUCT_ID>;
```

---

### Test 4: Actualizar UOMs de un producto

**Pasos:**
1. Editar un producto existente
2. Modificar precio de una UOM existente
3. Agregar una nueva UOM
4. Eliminar una UOM (si tiene más de 1)
5. Click en "Actualizar Producto"

**Resultado esperado:**
- ✅ Producto se actualiza sin errores
- ✅ Cambios reflejados en DB
- ✅ No aparece error de columnas faltantes

---

### Test 5: Vender producto con UOM seleccionada

**Pasos:**
1. Ir a POS (`/sales/new`)
2. Buscar un producto con múltiples UOMs
3. Agregar al carrito (debe abrir modal de selección)
4. Seleccionar una UOM
5. Confirmar venta

**Resultado esperado:**
- ✅ Modal de UOM se abre correctamente
- ✅ Se muestran todas las UOMs con sus precios
- ✅ Venta se confirma sin errores
- ✅ En DB: `sale_line` tiene `uom_id` correcto

---

### Test 6: Verificar integridad de datos existentes

**Pasos:**
1. Ejecutar query para verificar todos los `product_uom_price`:

```sql
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT product_id) as productos_con_uom,
    SUM(CASE WHEN is_base THEN 1 ELSE 0 END) as uoms_base
FROM product_uom_price;
```

**Resultado esperado:**
- ✅ Todos los productos tienen al menos 1 UOM
- ✅ Cada producto tiene exactamente 1 UOM base
- ✅ No hay valores NULL en columnas obligatorias

---

### Test 7: Verificar que no se intenta acceder a columnas inexistentes

**Pasos:**
1. Revisar logs de la aplicación
2. Realizar operaciones CRUD en productos
3. Buscar errores relacionados con `sku` o `barcode`

**Resultado esperado:**
- ✅ No aparecen errores de columna inexistente
- ✅ No hay menciones a `product_uom_price.sku` o `product_uom_price.barcode` en logs

---

## Queries de Verificación

### Verificar esquema de la tabla
```sql
\d product_uom_price
```

### Verificar datos
```sql
-- Ver todas las UOMs de un producto
SELECT 
    p.name as producto,
    u.name as uom,
    pup.sale_price,
    pup.conversion_to_base,
    pup.is_base
FROM product_uom_price pup
JOIN product p ON p.id = pup.product_id
JOIN uom u ON u.id = pup.uom_id
WHERE pup.product_id = <PRODUCT_ID>
ORDER BY pup.is_base DESC;

-- Verificar integridad: cada producto debe tener exactamente 1 UOM base
SELECT 
    product_id,
    COUNT(*) as total_uoms,
    SUM(CASE WHEN is_base THEN 1 ELSE 0 END) as base_uoms
FROM product_uom_price
GROUP BY product_id
HAVING SUM(CASE WHEN is_base THEN 1 ELSE 0 END) != 1;
-- Debe retornar 0 filas (todos tienen exactamente 1 base)
```

---

## Notas Importantes

1. **No se requiere migración SQL** porque solo se corrigió el modelo Python
2. **Compatibilidad total** con datos existentes
3. **SKU y Barcode** siguen existiendo a nivel de `product` (tabla principal), no por variante UOM
4. Si en el futuro se necesita SKU/barcode por UOM:
   - Crear migración para agregar columnas
   - Actualizar modelo
   - Actualizar UI y servicios

---

## Archivos Modificados

- `app/models/product_uom_price.py` - Eliminadas columnas `sku` y `barcode`
- `app/services/product_uom_service.py` - Actualizada documentación
- `app/blueprints/catalog.py` - Eliminadas referencias a `sku`/`barcode` en payloads
- `FIX_UOM_PRICE_SCHEMA_TESTING.md` - Este documento

---

## Resumen

| Antes | Después |
|-------|---------|
| ❌ Error al cargar productos | ✅ Carga sin errores |
| ❌ Modelo con columnas inexistentes | ✅ Modelo alineado con DB |
| ❌ Referencias a sku/barcode no usadas | ✅ Código limpio |

**Estado:** ✅ **RESUELTO**
