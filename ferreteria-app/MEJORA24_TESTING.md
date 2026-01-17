# MEJORA 24: Stock Inicial + Ajuste Manual sin afectar Balance - Testing

## Objetivo
Verificar que se puede setear stock inicial al crear productos y ajustar stock manualmente desde edición, sin que estos ajustes afecten el balance financiero (`finance_ledger`).

---

## Preparación

### Datos necesarios:
- Usuario autenticado con permisos
- Al menos 1 UOM activa (ej: "Unidad")
- Acceso a la base de datos para queries de verificación

### Queries útiles para verificación:

```sql
-- Ver stock de un producto
SELECT p.id, p.name, ps.on_hand_qty 
FROM product p 
JOIN product_stock ps ON ps.product_id = p.id 
WHERE p.id = <PRODUCT_ID>;

-- Ver movimientos de stock ADJUST MANUAL
SELECT sm.id, sm.type, sm.reference_type, sm.date, sm.notes, 
       sml.product_id, sml.qty
FROM stock_move sm
JOIN stock_move_line sml ON sml.stock_move_id = sm.id
WHERE sm.type = 'ADJUST' 
  AND sm.reference_type = 'MANUAL'
ORDER BY sm.id DESC 
LIMIT 10;

-- Ver últimos registros de finance_ledger (NO debe cambiar por ajustes)
SELECT id, type, reference_type, reference_id, amount, created_at
FROM finance_ledger
ORDER BY id DESC
LIMIT 10;

-- Contar registros de finance_ledger (antes y después)
SELECT COUNT(*) FROM finance_ledger;
```

---

## Casos de Prueba

### 1. Crear producto con stock inicial = 10

**Pasos:**
1. Ir a `/products/new`
2. Completar:
   - Nombre: "Producto Test Stock Inicial"
   - UOM: "Unidad"
   - Precio venta: 100
   - **Stock Inicial: 10**
3. Click "Crear Producto"

**Resultado esperado:**
- ✅ Producto creado exitosamente
- ✅ Flash message: "Producto ... creado exitosamente con stock inicial de 10"
- ✅ `product_stock.on_hand_qty = 10`
- ✅ Existe `stock_move` con:
  - `type = 'ADJUST'`
  - `reference_type = 'MANUAL'`
  - `notes = 'Stock inicial'`
- ✅ Existe `stock_move_line` con:
  - `qty = 10` (delta desde 0 a 10)
  - `unit_cost = 0`
- ✅ **NO se creó ningún registro en `finance_ledger`**

**Query verificación:**
```sql
SELECT ps.on_hand_qty 
FROM product_stock ps 
WHERE ps.product_id = <NEW_PRODUCT_ID>;
-- Debe retornar: 10

SELECT COUNT(*) 
FROM stock_move sm
JOIN stock_move_line sml ON sml.stock_move_id = sm.id
WHERE sm.type = 'ADJUST' 
  AND sm.reference_type = 'MANUAL'
  AND sml.product_id = <NEW_PRODUCT_ID>;
-- Debe retornar: 1
```

---

### 2. Crear producto sin stock inicial (vacío)

**Pasos:**
1. Ir a `/products/new`
2. Completar datos básicos
3. Dejar campo "Stock Inicial" **vacío**
4. Click "Crear Producto"

**Resultado esperado:**
- ✅ Producto creado exitosamente
- ✅ `product_stock.on_hand_qty = 0`
- ✅ NO se creó `stock_move` de tipo ADJUST
- ✅ NO se afectó `finance_ledger`

---

### 3. Crear producto con stock inicial = 0

**Pasos:**
1. Ir a `/products/new`
2. Completar datos básicos
3. Stock Inicial: **0**
4. Click "Crear Producto"

**Resultado esperado:**
- ✅ Producto creado exitosamente
- ✅ `product_stock.on_hand_qty = 0`
- ✅ NO se creó `stock_move` (delta = 0, no es necesario)
- ✅ NO se afectó `finance_ledger`

---

### 4. Validación: stock inicial negativo

**Pasos:**
1. Ir a `/products/new`
2. Completar datos básicos
3. Stock Inicial: **-5**
4. Click "Crear Producto"

**Resultado esperado:**
- ❌ Error: "El stock inicial debe ser mayor o igual a 0"
- ✅ Producto NO creado

---

### 5. Validación: stock inicial no numérico

**Pasos:**
1. Ir a `/products/new`
2. Completar datos básicos
3. Stock Inicial: **"abc"**
4. Click "Crear Producto"

**Resultado esperado:**
- ❌ Error: "El stock inicial debe ser un número válido"
- ✅ Producto NO creado

---

### 6. Editar producto: ajustar stock de 0 a 25

**Preparación:**
- Crear producto sin stock inicial (stock = 0)
- Contar registros actuales en `finance_ledger`: `COUNT_BEFORE`

**Pasos:**
1. Ir a `/products/<id>/edit`
2. En sección "Ajuste Manual de Stock":
   - Ver "Stock Actual: 0"
   - Campo "Nuevo Stock": ingresar **25**
3. Click "Aplicar Ajuste"

**Resultado esperado:**
- ✅ Flash message: "Stock ajustado exitosamente: 0 → 25 (+25)"
- ✅ Redirige a `/products/<id>/edit`
- ✅ Ahora muestra "Stock Actual: 25"
- ✅ `product_stock.on_hand_qty = 25`
- ✅ Existe `stock_move` con:
  - `type = 'ADJUST'`
  - `reference_type = 'MANUAL'`
  - `notes = 'Ajuste manual desde edición de producto'`
- ✅ Existe `stock_move_line` con:
  - `qty = 25` (delta)
  - `unit_cost = 0`
- ✅ **`COUNT(finance_ledger) = COUNT_BEFORE`** (sin cambios)

**Query verificación:**
```sql
SELECT COUNT(*) FROM finance_ledger;
-- Debe ser igual a COUNT_BEFORE
```

---

### 7. Editar producto: ajustar stock de 25 a 5 (reducción)

**Preparación:**
- Producto con stock = 25 (del caso anterior)

**Pasos:**
1. Ir a `/products/<id>/edit`
2. Nuevo Stock: **5**
3. Click "Aplicar Ajuste"

**Resultado esperado:**
- ✅ Flash message: "Stock ajustado exitosamente: 25 → 5 (-20)"
- ✅ `product_stock.on_hand_qty = 5`
- ✅ Existe `stock_move_line` con:
  - `qty = -20` (delta negativo)
- ✅ **NO se afectó `finance_ledger`**

---

### 8. Editar producto: ajustar al mismo valor (sin cambio)

**Preparación:**
- Producto con stock = 5

**Pasos:**
1. Ir a `/products/<id>/edit`
2. Nuevo Stock: **5** (mismo valor)
3. Click "Aplicar Ajuste"

**Resultado esperado:**
- ✅ Flash message: "El stock ya estaba en 5. No se realizó ningún ajuste."
- ✅ `product_stock.on_hand_qty = 5` (sin cambios)
- ✅ NO se creó nuevo `stock_move` (delta = 0)
- ✅ NO se afectó `finance_ledger`

---

### 9. Validación: ajustar a stock negativo

**Pasos:**
1. Ir a `/products/<id>/edit`
2. Nuevo Stock: **-10**
3. Click "Aplicar Ajuste"

**Resultado esperado:**
- ❌ Error: "El stock no puede ser negativo"
- ✅ Stock NO cambia

---

### 10. Validación: ajustar con valor no numérico

**Pasos:**
1. Ir a `/products/<id>/edit`
2. Nuevo Stock: **"xyz"**
3. Click "Aplicar Ajuste"

**Resultado esperado:**
- ❌ Error: "El stock debe ser un número válido"
- ✅ Stock NO cambia

---

### 11. Auditoría: ver últimos ajustes manuales

**Preparación:**
- Realizar 3 ajustes manuales en un producto:
  - 0 → 10
  - 10 → 25
  - 25 → 15

**Pasos:**
1. Ir a `/products/<id>/edit`
2. Scroll down a sección "Últimos Ajustes Manuales"

**Resultado esperado:**
- ✅ Se muestran los últimos 5 ajustes (o menos si no hay tantos)
- ✅ Cada ajuste muestra:
  - Fecha/hora en formato argentino
  - Delta con signo (+/-) y color (verde/rojo)
  - Notas (si existen)
- ✅ Ordenados por fecha DESC (más reciente primero)

**Ejemplo visual esperado:**
```
Últimos Ajustes Manuales:
- 17/01/2026 15:30  -10  (Ajuste manual desde edición de producto)
- 17/01/2026 15:25  +15  (Ajuste manual desde edición de producto)
- 17/01/2026 15:20  +10  (Stock inicial)
```

---

### 12. Integración: Venta después de ajuste manual

**Preparación:**
- Producto con stock = 20 (ajustado manualmente)
- Contar registros en `finance_ledger`: `COUNT_BEFORE`

**Pasos:**
1. Ir a POS `/sales/new`
2. Agregar el producto, cantidad: 5
3. Confirmar venta

**Resultado esperado:**
- ✅ Venta creada exitosamente
- ✅ `product_stock.on_hand_qty = 15` (20 - 5)
- ✅ Se creó `stock_move` tipo `OUT` (venta)
- ✅ **Se creó registro en `finance_ledger` tipo `INCOME`** (la venta sí afecta balance)
- ✅ `COUNT(finance_ledger) = COUNT_BEFORE + 1`

**Verificación:**
```sql
-- El ajuste manual previo NO creó ledger, pero la venta SÍ
SELECT type, reference_type, amount 
FROM finance_ledger 
ORDER BY id DESC 
LIMIT 1;
-- Debe mostrar: type='INCOME', reference_type='SALE'
```

---

### 13. Integración: Compra (boleta) después de ajuste manual

**Preparación:**
- Producto con stock = 15
- Contar registros en `finance_ledger`: `COUNT_BEFORE`

**Pasos:**
1. Ir a `/invoices/new`
2. Crear boleta con el producto, cantidad: 10, costo: 50
3. Confirmar creación
4. Pagar la boleta

**Resultado esperado:**
- ✅ Boleta creada y pagada
- ✅ `product_stock.on_hand_qty = 25` (15 + 10)
- ✅ Se creó `stock_move` tipo `IN` (compra)
- ✅ **Se creó registro en `finance_ledger` tipo `EXPENSE`** (el pago de boleta sí afecta balance)
- ✅ `COUNT(finance_ledger) = COUNT_BEFORE + 1`

---

### 14. Stock con decimales (fracciones)

**Pasos:**
1. Crear producto con stock inicial: **12.75**
2. Editar y ajustar a: **20.5**
3. Ajustar a: **8.25**

**Resultado esperado:**
- ✅ Todos los ajustes funcionan correctamente
- ✅ Stock final: 8.25
- ✅ Deltas calculados correctamente:
  - 0 → 12.75: delta = +12.75
  - 12.75 → 20.5: delta = +7.75
  - 20.5 → 8.25: delta = -12.25

---

### 15. Trigger DB: verificar que ADJUST suma delta

**Preparación:**
- Producto con stock = 10

**Pasos:**
1. Insertar manualmente en DB un `stock_move` tipo ADJUST con delta = +5:
```sql
INSERT INTO stock_move (date, type, reference_type, notes)
VALUES (now(), 'ADJUST', 'MANUAL', 'Test manual DB');

INSERT INTO stock_move_line (stock_move_id, product_id, qty, unit_cost, uom_id)
VALUES (
  (SELECT id FROM stock_move ORDER BY id DESC LIMIT 1),
  <PRODUCT_ID>,
  5,  -- delta positivo
  0,
  <UOM_ID>
);
```

2. Verificar stock después:
```sql
SELECT on_hand_qty FROM product_stock WHERE product_id = <PRODUCT_ID>;
```

**Resultado esperado:**
- ✅ `on_hand_qty = 15` (10 + 5)
- ✅ El trigger aplicó correctamente el delta

**Repetir con delta negativo:**
```sql
-- Delta = -3
INSERT INTO stock_move_line (stock_move_id, product_id, qty, unit_cost, uom_id)
VALUES (..., -3, 0, ...);
```

**Resultado esperado:**
- ✅ `on_hand_qty = 12` (15 - 3)

---

## Resumen de Verificaciones Críticas

### ✅ Checklist Final

- [ ] Stock inicial se aplica correctamente al crear producto
- [ ] Ajuste manual funciona (aumentar, disminuir, sin cambio)
- [ ] Validaciones funcionan (negativos, no numéricos)
- [ ] **`finance_ledger` NO cambia con ajustes manuales**
- [ ] Ventas posteriores SÍ afectan `finance_ledger` (INCOME)
- [ ] Compras/pagos posteriores SÍ afectan `finance_ledger` (EXPENSE)
- [ ] Auditoría de ajustes manuales visible en UI
- [ ] Trigger DB maneja correctamente `type='ADJUST'` con deltas positivos/negativos
- [ ] Stock con decimales funciona correctamente
- [ ] UI muestra advertencia: "Los ajustes manuales NO afectan el balance financiero"

---

## Queries de Verificación Final

```sql
-- 1. Verificar que TODOS los ajustes manuales tienen unit_cost = 0
SELECT sml.id, sml.qty, sml.unit_cost
FROM stock_move_line sml
JOIN stock_move sm ON sm.id = sml.stock_move_id
WHERE sm.type = 'ADJUST' AND sm.reference_type = 'MANUAL'
  AND sml.unit_cost != 0;
-- Debe retornar 0 filas

-- 2. Verificar que NO existe ledger con reference_type = 'MANUAL' o relacionado a ADJUST
SELECT * 
FROM finance_ledger 
WHERE reference_type = 'MANUAL' 
   OR reference_type LIKE '%ADJUST%';
-- Debe retornar 0 filas

-- 3. Contar movimientos ADJUST MANUAL vs registros en ledger
SELECT 
  (SELECT COUNT(*) FROM stock_move WHERE type='ADJUST' AND reference_type='MANUAL') AS adjust_count,
  (SELECT COUNT(*) FROM finance_ledger) AS ledger_count;
-- adjust_count puede ser > 0, pero ledger_count NO debe aumentar por ajustes
```

---

## Notas Importantes

1. **Balance NO se afecta:** Los ajustes manuales solo corrigen inventario físico, no generan ingresos ni egresos.
2. **Auditoría:** Todos los ajustes quedan registrados en `stock_move` / `stock_move_line` para trazabilidad.
3. **Trigger DB:** Debe estar configurado para que `type='ADJUST'` sume el `qty` (delta) al stock actual.
4. **UX:** La UI debe mostrar claramente que los ajustes no afectan el balance.

---

## Fin del Testing
