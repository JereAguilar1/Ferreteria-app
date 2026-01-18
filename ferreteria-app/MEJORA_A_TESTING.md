# MEJORA A - Testing: Múltiples Unidades de Medida (UOM) por Producto

## Objetivo
Verificar que el sistema permite definir y vender productos en múltiples unidades de medida, cada una con su propio precio y factor de conversión a una unidad base.

---

## Pre-requisitos
- Sistema levantado y funcionando
- Migración `MEJORA_A_multiple_uom_prices.sql` aplicada
- Al menos 2 unidades de medida creadas en el sistema (ej: "Metro", "Rollo")
- Usuario autenticado

---

## Test 1: Crear producto con múltiples UOMs

### Pasos:
1. Ir a `/products/new`
2. Completar datos básicos del producto:
   - Nombre: "Cable Eléctrico 2x1.5"
   - SKU: "CABLE-2X15"
   - Categoría: (seleccionar una)
3. En la sección "Unidades de Medida y Precios":
   - **Primera UOM (Base)**:
     - Unidad: Metro (m)
     - Precio: 150
     - Factor: 1
     - ¿Base?: Sí (marcado)
   - Click en "Agregar Unidad"
   - **Segunda UOM**:
     - Unidad: Rollo
     - Precio: 14000
     - Factor: 100
     - ¿Base?: No
4. Click en "Crear Producto"

### Resultado esperado:
- ✅ Producto creado exitosamente
- ✅ Mensaje: "Producto 'Cable Eléctrico 2x1.5' creado exitosamente"
- ✅ Redirige a `/products`
- ✅ En DB: `product_uom_price` tiene 2 filas para este producto
- ✅ Una fila con `is_base=true`, otra con `is_base=false`

### Validaciones:
- ❌ No permitir crear producto sin ninguna UOM
- ❌ No permitir crear producto con más de una UOM base
- ❌ No permitir UOMs duplicadas
- ❌ No permitir `conversion_to_base <= 0`
- ❌ No permitir `sale_price < 0`

---

## Test 2: Editar producto y modificar UOMs

### Pasos:
1. Ir a `/products/<id>/edit` del producto creado en Test 1
2. Verificar que se cargan las 2 UOMs existentes
3. Modificar precio de "Metro" a 160
4. Agregar una tercera UOM:
   - Unidad: Caja (si existe)
   - Precio: 7000
   - Factor: 50
   - ¿Base?: No
5. Click en "Actualizar Producto"

### Resultado esperado:
- ✅ Producto actualizado exitosamente
- ✅ Ahora tiene 3 UOMs en `product_uom_price`
- ✅ Precio de "Metro" actualizado a 160
- ✅ "Caja" agregada correctamente

---

## Test 3: Venta con UOM base (Metro)

### Pasos:
1. Ir a `/sales/new` (POS)
2. Buscar "Cable Eléctrico 2x1.5"
3. Click en "Agregar"
4. **Verificar que se abre modal de selección de UOM**
5. En el modal:
   - Seleccionar "Metro (m)" (debe estar marcado por defecto como base)
   - Cantidad: 10
   - Verificar que muestra precio: $160
6. Click en "Agregar al Carrito"

### Resultado esperado:
- ✅ Modal se cierra automáticamente
- ✅ Producto aparece en carrito:
   - Nombre: "Cable Eléctrico 2x1.5"
   - UOM: "m" (badge)
   - Precio Unit.: $160
   - Cantidad: 10
   - Subtotal: $1.600
- ✅ Total del carrito: $1.600

---

## Test 4: Venta con UOM no base (Rollo)

### Pasos:
1. En el mismo carrito del Test 3
2. Buscar nuevamente "Cable Eléctrico 2x1.5"
3. Click en "Agregar"
4. En el modal:
   - Seleccionar "Rollo"
   - Cantidad: 2
   - Verificar que muestra precio: $14.000
   - Verificar que muestra "Factor: 100 m"
6. Click en "Agregar al Carrito"

### Resultado esperado:
- ✅ Ahora hay **2 líneas** en el carrito para el mismo producto:
   - Línea 1: 10 m @ $160 = $1.600
   - Línea 2: 2 Rollo @ $14.000 = $28.000
- ✅ Total del carrito: $29.600

---

## Test 5: Confirmar venta con múltiples UOMs

### Pasos:
1. Con el carrito del Test 4 (2 líneas, mismo producto, diferentes UOMs)
2. Seleccionar método de pago: Efectivo
3. Click en "Confirmar Venta"
4. En el modal de confirmación, verificar:
   - Se muestran ambas líneas correctamente
   - Total: $29.600
5. Click en "Confirmar"

### Resultado esperado:
- ✅ Venta creada exitosamente
- ✅ Redirige a `/sales/<id>`
- ✅ En DB:
   - `sale`: 1 fila con `total=29600`
   - `sale_line`: 2 filas:
     - Línea 1: `product_id=X, uom_id=Metro, qty=10, unit_price=160, line_total=1600`
     - Línea 2: `product_id=X, uom_id=Rollo, qty=2, unit_price=14000, line_total=28000`
   - `stock_move_line`: 2 filas:
     - Línea 1: `qty=10` (qty_base para Metro)
     - Línea 2: `qty=200` (qty_base para Rollo: 2 * 100)
   - `product_stock`: `on_hand_qty` disminuye en **210** (10 + 200)
   - `finance_ledger`: 1 entrada INCOME por $29.600

---

## Test 6: Validación de stock con conversión

### Pasos:
1. Producto "Cable Eléctrico 2x1.5" tiene stock actual (ej: 50 m)
2. Ir a POS
3. Intentar agregar 1 Rollo (= 100 m en base)

### Resultado esperado:
- ❌ No debe permitir agregar
- ✅ Mensaje: "Stock insuficiente para 'Cable Eléctrico 2x1.5'. Disponible: 50"
- ✅ Modal se cierra o muestra error

---

## Test 7: Producto con una sola UOM (comportamiento legacy)

### Pasos:
1. Crear un producto nuevo con una sola UOM (la base)
   - Nombre: "Tornillo 8mm"
   - UOM: Unidad (u)
   - Precio: 5
   - Factor: 1
   - ¿Base?: Sí
2. Ir a POS
3. Buscar "Tornillo 8mm"
4. Click en "Agregar"

### Resultado esperado:
- ✅ **NO se abre modal** (solo tiene 1 UOM)
- ✅ Se agrega directamente al carrito con qty=1
- ✅ Precio: $5
- ✅ UOM: "u"

---

## Test 8: Editar producto y eliminar UOM

### Pasos:
1. Ir a `/products/<id>/edit` del "Cable Eléctrico 2x1.5"
2. Intentar eliminar todas las UOMs (dejar 0)
3. Click en "Actualizar Producto"

### Resultado esperado:
- ❌ No debe permitir
- ✅ Mensaje de error: "Debe mantener al menos una unidad de medida"

---

## Test 9: Cambiar UOM base

### Pasos:
1. Editar "Cable Eléctrico 2x1.5"
2. Cambiar el radio button de "Base" de "Metro" a "Rollo"
3. Ajustar factores de conversión:
   - Rollo: Factor 1 (ahora base)
   - Metro: Factor 0.01 (1 metro = 0.01 rollos)
4. Click en "Actualizar Producto"

### Resultado esperado:
- ✅ Producto actualizado
- ✅ En DB: `product_uom_price`:
   - Rollo: `is_base=true`, `conversion_to_base=1`
   - Metro: `is_base=false`, `conversion_to_base=0.01`
- ✅ Stock ahora se interpreta en "Rollos" (unidad base)

---

## Test 10: Verificar compatibilidad con productos existentes

### Pasos:
1. Listar todos los productos existentes antes de MEJORA A
2. Verificar que cada uno tiene al menos 1 fila en `product_uom_price`
3. Verificar que la UOM y precio coinciden con `product.uom_id` y `product.sale_price`
4. Intentar vender un producto legacy (creado antes de MEJORA A)

### Resultado esperado:
- ✅ Todos los productos legacy tienen 1 UOM base en `product_uom_price`
- ✅ Se pueden vender normalmente
- ✅ No hay errores en POS ni en confirmación de venta

---

## Test 11: Validación de duplicados en edición

### Pasos:
1. Editar "Cable Eléctrico 2x1.5"
2. Intentar agregar una UOM que ya existe (ej: agregar "Metro" nuevamente)
3. Click en "Actualizar Producto"

### Resultado esperado:
- ❌ No debe permitir
- ✅ Mensaje de error: "No puede haber unidades de medida duplicadas"
- ✅ JavaScript debe validar antes de enviar

---

## Test 12: Verificar formato argentino en modal de UOM

### Pasos:
1. Crear producto con UOM "Rollo" a precio 14550.75
2. Ir a POS y abrir modal de selección

### Resultado esperado:
- ✅ Precio se muestra como: **$14.550,75** (punto miles, coma decimales)
- ✅ Factor se muestra correctamente

---

## Resumen de Validaciones Críticas

| # | Validación | Esperado |
|---|------------|----------|
| 1 | Crear producto con múltiples UOMs | ✅ Permitido |
| 2 | Crear producto sin UOMs | ❌ Bloqueado |
| 3 | Crear producto con 2+ UOMs base | ❌ Bloqueado |
| 4 | UOMs duplicadas | ❌ Bloqueado |
| 5 | `conversion_to_base <= 0` | ❌ Bloqueado |
| 6 | `sale_price < 0` | ❌ Bloqueado |
| 7 | Venta con UOM no base descuenta stock correcto (qty_base) | ✅ Correcto |
| 8 | Modal solo aparece si producto tiene 2+ UOMs | ✅ Correcto |
| 9 | Carrito permite mismo producto con diferentes UOMs | ✅ Permitido |
| 10 | Stock se valida en unidad base | ✅ Correcto |
| 11 | `sale_line` guarda `uom_id` y `unit_price` correctos | ✅ Correcto |
| 12 | `stock_move_line` usa `qty_base` | ✅ Correcto |
| 13 | Productos legacy siguen funcionando | ✅ Compatible |

---

## Queries útiles para verificación

```sql
-- Ver UOMs de un producto
SELECT p.name, u.name as uom_name, pup.sale_price, pup.conversion_to_base, pup.is_base
FROM product p
JOIN product_uom_price pup ON pup.product_id = p.id
JOIN uom u ON u.id = pup.uom_id
WHERE p.id = <PRODUCT_ID>
ORDER BY pup.is_base DESC;

-- Ver líneas de venta con UOM
SELECT s.id as sale_id, p.name, u.name as uom, sl.qty, sl.unit_price, sl.line_total
FROM sale s
JOIN sale_line sl ON sl.sale_id = s.id
JOIN product p ON p.id = sl.product_id
JOIN uom u ON u.id = sl.uom_id
WHERE s.id = <SALE_ID>;

-- Ver movimientos de stock con qty_base
SELECT sm.id, sm.type, p.name, sml.qty as qty_base, u.name as uom
FROM stock_move sm
JOIN stock_move_line sml ON sml.stock_move_id = sm.id
JOIN product p ON p.id = sml.product_id
JOIN uom u ON u.id = sml.uom_id
WHERE sm.reference_type = 'SALE' AND sm.reference_id = <SALE_ID>;
```

---

## Notas Finales
- Todos los tests deben pasar sin errores
- El sistema debe mantener compatibilidad con productos legacy
- El stock siempre se maneja en unidad base
- Los precios y cantidades en ventas reflejan la UOM seleccionada
- La conversión a unidad base es automática y transparente para el usuario
