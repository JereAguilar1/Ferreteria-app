# MEJORA 23: Editar y Eliminar Boletas (Purchase Invoices) con Ajuste de Stock y Balance

## Objetivo
Verificar que la funcionalidad de editar y eliminar boletas funciona correctamente, ajustando el stock automáticamente y respetando las reglas de negocio según el estado de la boleta (PENDING vs PAID).

---

## Reglas de Negocio Implementadas

### Boleta PENDING
- ✅ Se puede **editar** (datos + líneas)
- ✅ Se puede **eliminar**
- ✅ Al editar: stock se ajusta por la diferencia (deltas)
- ✅ Al eliminar: stock se revierte (se resta todo lo ingresado)

### Boleta PAID
- ❌ **NO** se puede eliminar (tiene asiento contable registrado)
- ❌ **NO** se pueden editar líneas/totales (tiene asiento contable registrado)
- ℹ️ Solo se muestran botones para boletas PENDING

---

## Casos de Prueba

### 1. Acceso a Edición - Boleta PENDING

**Descripción:** Verificar que se puede acceder a editar una boleta en estado PENDING.

**Pasos:**
1. Crear una boleta PENDING con algunos ítems
2. Ir a `/invoices/<id>` (detalle)
3. Verificar que aparecen los botones "Editar Boleta" y "Eliminar Boleta"
4. Click en "Editar Boleta"

**Resultado Esperado:**
- Los botones "Editar" y "Eliminar" son visibles en el detalle
- Los botones están en la sección "Acciones"
- Al hacer click en "Editar", redirige a `/invoices/<id>/edit`
- El formulario de edición se carga con los datos actuales de la boleta

---

### 2. Bloqueo de Edición/Eliminación - Boleta PAID

**Descripción:** Verificar que NO se puede editar ni eliminar una boleta en estado PAID.

**Pasos:**
1. Crear una boleta PENDING
2. Pagarla (cambiar estado a PAID)
3. Ir a `/invoices/<id>`
4. Verificar que NO aparecen botones de edición ni eliminación
5. Intentar acceder directamente a `/invoices/<id>/edit`

**Resultado Esperado:**
- NO aparecen botones "Editar" ni "Eliminar" en el detalle
- Si se intenta acceder directamente a `/invoices/<id>/edit`:
  - Flash message: "Solo se pueden editar boletas PENDING. Esta boleta está en estado PAID."
  - Redirect a `/invoices/<id>`
- Similar para eliminación

---

### 3. Editar Boleta - Aumentar Cantidad de Ítem Existente

**Descripción:** Verificar que al aumentar la cantidad de un ítem, el stock aumenta por el delta.

**Pasos:**
1. Crear producto "Tornillo 8mm" con stock inicial 100 UN
2. Crear boleta PENDING:
   - Proveedor: ACME
   - Fecha: hoy
   - Ítem: Tornillo 8mm, qty=10, unit_cost=50
3. Verificar stock después de crear: `stock = 100 + 10 = 110`
4. Ir a `/invoices/<id>/edit`
5. Modificar cantidad del ítem: `qty=10` → `qty=15`
6. Click "Revisar y Guardar"
7. Verificar modal muestra:
   - "Ítems Modificados: Tornillo 8mm, Cantidad: 10 → 15"
   - "Impacto en Stock: Tornillo 8mm: +5 UN"
8. Confirmar cambios

**Resultado Esperado:**
- Modal muestra correctamente el delta
- Al confirmar:
  - Flash message: "Boleta actualizada exitosamente. El stock se ha ajustado automáticamente."
  - Redirect a `/invoices/<id>`
  - Stock del producto: `110 + 5 = 115 UN`
  - Boleta muestra qty=15 en el detalle

**Verificación SQL:**
```sql
-- Verificar stock actualizado
SELECT ps.on_hand_qty 
FROM product_stock ps
JOIN product p ON p.id = ps.product_id
WHERE p.name = 'Tornillo 8mm';
-- Debe ser 115

-- Verificar stock_move ADJUST creado
SELECT sm.id, sm.type, sm.notes
FROM stock_move sm
WHERE sm.notes LIKE '%Ajuste por edición de Boleta%'
ORDER BY sm.id DESC LIMIT 1;
-- Debe existir type=ADJUST

-- Verificar stock_move_line con delta +5
SELECT sml.qty
FROM stock_move_line sml
JOIN stock_move sm ON sm.id = sml.stock_move_id
WHERE sm.notes LIKE '%Ajuste por edición de Boleta%'
AND sml.product_id = [ID_PRODUCTO]
ORDER BY sml.id DESC LIMIT 1;
-- Debe ser qty = +5.000
```

---

### 4. Editar Boleta - Disminuir Cantidad de Ítem Existente

**Descripción:** Verificar que al disminuir la cantidad, el stock disminuye por el delta (reversión parcial).

**Pasos:**
1. Crear producto "Cable 2.5mm" con stock inicial 50 MT
2. Crear boleta PENDING:
   - Ítem: Cable 2.5mm, qty=20, unit_cost=100
3. Stock después de crear: `50 + 20 = 70 MT`
4. Editar boleta:
   - Cambiar qty=20 → qty=12
5. Confirmar cambios

**Resultado Esperado:**
- Modal muestra: "Impacto en Stock: Cable 2.5mm: -8 MT"
- Al confirmar:
  - Stock del producto: `70 - 8 = 62 MT`
  - El delta es negativo (-8), así que el stock baja

**Verificación SQL:**
```sql
-- Verificar stock_move_line con qty negativa
SELECT sml.qty
FROM stock_move_line sml
JOIN stock_move sm ON sm.id = sml.stock_move_id
WHERE sm.type = 'ADJUST'
AND sm.notes LIKE '%Ajuste por edición de Boleta%'
ORDER BY sml.id DESC LIMIT 1;
-- Debe ser qty = -8.000 (negativo para restar stock)
```

---

### 5. Editar Boleta - Eliminar Ítem Completo

**Descripción:** Verificar que al eliminar un ítem, el stock disminuye por la cantidad completa del ítem eliminado.

**Pasos:**
1. Crear boleta PENDING con 2 ítems:
   - Tornillo 8mm: qty=10, stock antes=100, después=110
   - Clavo 3": qty=5, stock antes=200, después=205
2. Editar boleta:
   - Eliminar ítem "Clavo 3""
3. Confirmar cambios

**Resultado Esperado:**
- Modal muestra:
  - "Ítems Eliminados: Clavo 3", Cantidad: 5"
  - "Impacto en Stock: Clavo 3": -5 UN"
- Al confirmar:
  - Stock de Tornillo 8mm: sigue en 110 (sin cambios)
  - Stock de Clavo 3": `205 - 5 = 200 UN` (vuelve al valor previo)
  - Boleta solo muestra 1 ítem (Tornillo 8mm)

---

### 6. Editar Boleta - Agregar Nuevo Ítem

**Descripción:** Verificar que al agregar un ítem nuevo, el stock aumenta por la cantidad agregada.

**Pasos:**
1. Crear boleta PENDING con 1 ítem:
   - Tornillo 8mm: qty=10
2. Stock de "Martillo" antes: 30 UN
3. Editar boleta:
   - Agregar ítem: Martillo, qty=3, unit_cost=500
4. Confirmar cambios

**Resultado Esperado:**
- Modal muestra:
  - "Ítems Agregados: Martillo - Cantidad: 3 - Costo: $500 - Subtotal: $1.500"
  - "Impacto en Stock: Martillo: +3 UN"
- Al confirmar:
  - Stock de Martillo: `30 + 3 = 33 UN`
  - Boleta muestra 2 ítems (Tornillo + Martillo)
  - Total recalculado correctamente

---

### 7. Editar Boleta - Cambiar Proveedor

**Descripción:** Verificar que se puede cambiar el proveedor de una boleta PENDING.

**Pasos:**
1. Crear boleta PENDING con proveedor "ACME"
2. Editar boleta:
   - Cambiar proveedor a "SuperSupplier"
3. Confirmar cambios

**Resultado Esperado:**
- Modal muestra el cambio de proveedor
- Al confirmar, el detalle muestra el nuevo proveedor

---

### 8. Editar Boleta - Cambiar Número de Boleta

**Descripción:** Verificar que se puede cambiar el número de boleta.

**Pasos:**
1. Crear boleta PENDING con número "B-001"
2. Editar boleta:
   - Cambiar número a "B-002"
3. Confirmar cambios

**Resultado Esperado:**
- Boleta se actualiza con el nuevo número
- El listado muestra "B-002"

---

### 9. Editar Boleta - Validación: Número Duplicado

**Descripción:** Verificar que no se puede cambiar el número de boleta a uno que ya existe para el mismo proveedor.

**Pasos:**
1. Crear boleta #1: proveedor=ACME, número="B-001"
2. Crear boleta #2: proveedor=ACME, número="B-002"
3. Editar boleta #2:
   - Intentar cambiar número a "B-001" (ya existe para ACME)
4. Intentar guardar

**Resultado Esperado:**
- Flash message: "Ya existe una boleta con número 'B-001' para el proveedor 'ACME'"
- No se guarda el cambio
- Permanece en el formulario de edición

---

### 10. Editar Boleta - Validación: Líneas Vacías

**Descripción:** Verificar que no se puede guardar una boleta sin ítems.

**Pasos:**
1. Crear boleta PENDING con 1 ítem
2. Editar boleta:
   - Eliminar el único ítem
3. Intentar guardar

**Resultado Esperado:**
- Flash message: "Debe agregar al menos una línea."
- No se guarda
- Permanece en el formulario de edición

---

### 11. Editar Boleta - Validación: Cantidad <= 0

**Descripción:** Verificar que no se puede poner cantidad <= 0.

**Pasos:**
1. Editar boleta
2. Cambiar qty de un ítem a 0
3. Intentar guardar

**Resultado Esperado:**
- Flash message: "La cantidad debe ser mayor a 0 en la línea X."
- No se guarda

---

### 12. Editar Boleta - Validación: Producto Duplicado

**Descripción:** Verificar que no se puede agregar el mismo producto dos veces.

**Pasos:**
1. Editar boleta que ya tiene "Tornillo 8mm"
2. Intentar agregar otro ítem con "Tornillo 8mm"

**Resultado Esperado:**
- JavaScript muestra alert: "Este producto ya está en los ítems. Modifique la cantidad del ítem existente."
- No se agrega duplicado

---

### 13. Editar Boleta - Total Recalculado Server-Side

**Descripción:** Verificar que el total se recalcula en el servidor, no se confía en el cliente.

**Pasos:**
1. Editar boleta con 2 ítems:
   - Tornillo: qty=10, cost=50 → subtotal=500
   - Clavo: qty=5, cost=30 → subtotal=150
   - Total: 650
2. Modificar Tornillo a qty=15
3. Manipular manualmente el HTML del total (cambiar a 999)
4. Guardar

**Resultado Esperado:**
- El total guardado es el correcto (calculado server-side): 500 + 250 + 150 = 900
- NO es el manipulado (999)

---

### 14. Editar Boleta - Transacción Atómica

**Descripción:** Verificar que los cambios se aplican de forma atómica (todo o nada).

**Pasos:**
1. Crear boleta con 2 ítems
2. Editar boleta:
   - Modificar qty de ítem 1
   - Agregar ítem nuevo
3. Simular fallo durante commit (ej: desconectar DB justo antes)

**Resultado Esperado:**
- Si falla, NO hay cambios parciales:
  - Las líneas viejas siguen igual
  - El stock NO cambia
  - La boleta sigue con datos originales
- Si tiene éxito, todos los cambios se aplican

---

### 15. Eliminar Boleta - PENDING Sin Ítems

**Descripción:** Verificar que se puede eliminar una boleta sin ítems.

**Pasos:**
1. Crear boleta PENDING manualmente en DB sin ítems (edge case)
2. Ir a `/invoices/<id>`
3. Click "Eliminar Boleta"
4. Confirmar

**Resultado Esperado:**
- Boleta se elimina sin intentar crear stock_move (porque no hay ítems)
- Flash message: "Boleta #X eliminada exitosamente..."
- Redirect a listado

---

### 16. Eliminar Boleta - PENDING Con Ítems

**Descripción:** Verificar que al eliminar una boleta, el stock se revierte completamente.

**Pasos:**
1. Crear producto "Tornillo 8mm" con stock inicial 100 UN
2. Crear boleta PENDING:
   - Tornillo 8mm: qty=10, cost=50
3. Stock después de crear: `100 + 10 = 110 UN`
4. Ir a detalle de boleta
5. Click "Eliminar Boleta"
6. Verificar modal muestra:
   - Proveedor, número, total
   - "Impacto en Stock: Se revertirá el stock ingresado..."
   - Lista de productos con deltas negativos: "Tornillo 8mm: -10 UN"
7. Confirmar

**Resultado Esperado:**
- Flash message: "Boleta #X eliminada exitosamente. El stock se ha revertido automáticamente."
- Redirect a listado
- Stock de Tornillo 8mm: `110 - 10 = 100 UN` (vuelve al valor previo)
- Boleta desaparece del listado

**Verificación SQL:**
```sql
-- Verificar que la boleta fue eliminada
SELECT COUNT(*) FROM purchase_invoice WHERE id = [ID_INVOICE];
-- Debe ser 0

-- Verificar que las líneas fueron eliminadas (cascade)
SELECT COUNT(*) FROM purchase_invoice_line WHERE invoice_id = [ID_INVOICE];
-- Debe ser 0

-- Verificar stock_move de reversión
SELECT sm.id, sm.type, sm.notes
FROM stock_move sm
WHERE sm.notes LIKE '%Reversión por eliminación de Boleta%'
ORDER BY sm.id DESC LIMIT 1;
-- Debe existir type=ADJUST

-- Verificar stock_move_line con qty negativa
SELECT sml.qty
FROM stock_move_line sml
JOIN stock_move sm ON sm.id = sml.stock_move_id
WHERE sm.notes LIKE '%Reversión por eliminación de Boleta%'
ORDER BY sml.id DESC LIMIT 1;
-- Debe ser qty = -10.000 (negativo para restar stock)

-- Verificar stock final del producto
SELECT ps.on_hand_qty 
FROM product_stock ps
JOIN product p ON p.id = ps.product_id
WHERE p.name = 'Tornillo 8mm';
-- Debe ser 100 (valor original)
```

---

### 17. Eliminar Boleta - PAID Bloqueado

**Descripción:** Verificar que NO se puede eliminar una boleta PAID.

**Pasos:**
1. Crear boleta PENDING
2. Pagarla (estado PAID, crea ledger EXPENSE)
3. Intentar eliminar (accediendo directamente a DELETE o via UI si hubiera botón)

**Resultado Esperado:**
- NO aparece botón "Eliminar" en el detalle (solo para PENDING)
- Si se intenta acceder directamente a `/invoices/<id>/delete`:
  - Flash message: "Solo se pueden eliminar boletas PENDING. Esta boleta está en estado PAID. Si está PAID, tiene un asiento contable registrado."
  - Redirect a detalle
  - La boleta NO se elimina
  - El stock NO cambia
  - El ledger EXPENSE sigue existiendo

---

### 18. Eliminar Boleta - Múltiples Ítems

**Descripción:** Verificar que al eliminar una boleta con múltiples ítems, el stock de todos se revierte.

**Pasos:**
1. Crear boleta PENDING con 3 ítems:
   - Tornillo 8mm: qty=10, stock antes=100, después=110
   - Cable 2.5mm: qty=20, stock antes=50, después=70
   - Martillo: qty=3, stock antes=30, después=33
2. Eliminar boleta

**Resultado Esperado:**
- Stock de Tornillo 8mm: 110 → 100
- Stock de Cable 2.5mm: 70 → 50
- Stock de Martillo: 33 → 30
- Todos vuelven a valores previos

---

### 19. UI - Botones en Listado

**Descripción:** Verificar que los botones "Editar" y "Eliminar" aparecen correctamente en el listado.

**Pasos:**
1. Crear 2 boletas:
   - Boleta #1: PENDING
   - Boleta #2: PAID
2. Ir a `/invoices` (listado)

**Resultado Esperado:**
- Boleta #1 (PENDING) muestra:
  - Botón "Ver" (ojo)
  - Botón "Editar" (lápiz)
  - Botón "Pagar" (tarjeta)
  - Botón "Eliminar" (basura)
- Boleta #2 (PAID) muestra:
  - Botón "Ver" (ojo)
  - NO muestra "Editar", "Pagar" ni "Eliminar"

---

### 20. UI - Botones en Detalle

**Descripción:** Verificar que los botones aparecen correctamente en la vista de detalle.

**Pasos:**
1. Crear boleta PENDING
2. Ir a `/invoices/<id>` (detalle)

**Resultado Esperado:**
- Aparece sección "Acciones" con:
  - Botón "Editar Boleta" (link a edit)
  - Botón "Eliminar Boleta" (abre modal)
- Mensaje informativo: "Estas opciones solo están disponibles para boletas pendientes..."
- Aparece sección "Registrar Pago"

---

### 21. UI - Modal de Confirmación de Edición

**Descripción:** Verificar que el modal de confirmación de edición muestra toda la información correcta.

**Pasos:**
1. Editar boleta con varios cambios
2. Click "Revisar y Guardar"

**Resultado Esperado:**
- Modal se abre automáticamente
- Muestra:
  - Información de la boleta (proveedor, número, fecha)
  - Resumen de cambios (ítems agregados, eliminados, modificados)
  - Impacto en stock (deltas por producto)
  - Total anterior vs total nuevo
  - Diferencia resaltada en color
  - Warning sobre ajuste de stock
- Botones "Cancelar" y "Confirmar Cambios"

---

### 22. UI - Modal de Confirmación de Eliminación

**Descripción:** Verificar que el modal de confirmación de eliminación muestra toda la información correcta.

**Pasos:**
1. Ir a detalle de boleta PENDING
2. Click "Eliminar Boleta"

**Resultado Esperado:**
- Modal se abre automáticamente
- Muestra:
  - Alerta de peligro: "¡Atención! Esta acción es irreversible."
  - Detalles de la boleta (proveedor, número, fecha, total, cantidad de ítems)
  - Warning sobre impacto en stock con lista de productos y deltas negativos
- Botones "Cancelar" y "Eliminar Boleta" (rojo)

---

### 23. UI - Cancelar Modal de Edición

**Descripción:** Verificar que cancelar el modal no guarda cambios.

**Pasos:**
1. Editar boleta
2. Click "Revisar y Guardar"
3. En el modal, click "Cancelar"

**Resultado Esperado:**
- Modal se cierra
- NO se guardan cambios
- Permanece en el formulario de edición
- Los cambios en el formulario se mantienen (no se pierden)

---

### 24. UI - Cancelar Modal de Eliminación

**Descripción:** Verificar que cancelar el modal no elimina la boleta.

**Pasos:**
1. Click "Eliminar Boleta"
2. En el modal, click "Cancelar"

**Resultado Esperado:**
- Modal se cierra
- La boleta NO se elimina
- Permanece en la vista de detalle

---

### 25. Editar Boleta - Cambiar Fechas

**Descripción:** Verificar que se pueden cambiar las fechas de la boleta.

**Pasos:**
1. Crear boleta con invoice_date=2026-01-01, due_date=2026-01-15
2. Editar boleta:
   - Cambiar invoice_date a 2026-01-05
   - Cambiar due_date a 2026-01-20
3. Guardar

**Resultado Esperado:**
- Fechas se actualizan correctamente
- El detalle muestra las nuevas fechas

---

### 26. Ledger No Se Toca - Boleta PENDING

**Descripción:** Verificar que editar/eliminar una boleta PENDING NO crea ni modifica asientos en finance_ledger.

**Pasos:**
1. Crear boleta PENDING
2. Editar boleta (cambiar ítems)
3. Verificar finance_ledger

**Resultado Esperado:**
- NO hay asientos en finance_ledger con reference_type='INVOICE_PAYMENT' para esta boleta
- Al editar PENDING, NO se crea asiento (porque el egreso se registra al pagar)
- Al eliminar PENDING, NO se toca ledger (porque no había asiento)

**Verificación SQL:**
```sql
-- Verificar que NO hay ledger entries para esta invoice
SELECT COUNT(*) 
FROM finance_ledger 
WHERE reference_type = 'INVOICE_PAYMENT' 
AND reference_id = [ID_INVOICE];
-- Debe ser 0 (porque está PENDING, no se ha pagado)
```

---

### 27. Ledger Se Preserva - Boleta PAID No Editable

**Descripción:** Verificar que una boleta PAID no se puede editar ni eliminar, preservando el asiento contable.

**Pasos:**
1. Crear boleta PENDING
2. Pagarla (crea ledger EXPENSE)
3. Verificar ledger existe
4. Intentar editar/eliminar

**Resultado Esperado:**
- Ledger EXPENSE existe y NO se modifica
- NO se puede editar ni eliminar la boleta
- Mensaje claro en UI: "Si está PAID, tiene un asiento contable registrado."

**Verificación SQL:**
```sql
-- Verificar que el ledger entry existe y NO cambia
SELECT fl.id, fl.type, fl.amount, fl.reference_type, fl.reference_id
FROM finance_ledger fl
WHERE fl.reference_type = 'INVOICE_PAYMENT'
AND fl.reference_id = [ID_INVOICE];
-- Debe existir exactamente 1 row con type='EXPENSE' y amount=total_amount de la invoice
-- Y NO debe cambiar después de intentos de edición/eliminación
```

---

### 28. Auditoría - Stock Moves Creados

**Descripción:** Verificar que se crean stock_move correctos para auditoría.

**Pasos:**
1. Crear boleta → ver stock_move tipo IN
2. Editar boleta → ver stock_move tipo ADJUST
3. Eliminar boleta → ver stock_move tipo ADJUST (reversión)

**Resultado Esperado:**
- Al crear: `stock_move.type = IN`, `reference_type = INVOICE`, `notes = "Compra - Boleta #X"`
- Al editar: `stock_move.type = ADJUST`, `reference_type = MANUAL`, `notes = "Ajuste por edición de Boleta #X"`
- Al eliminar: `stock_move.type = ADJUST`, `reference_type = MANUAL`, `notes = "Reversión por eliminación de Boleta #X"`
- Todos los movimientos quedan registrados para auditoría

---

### 29. Performance - Lock de Invoice Row

**Descripción:** Verificar que se usa lock FOR UPDATE para evitar condiciones de carrera.

**Pasos:**
1. Abrir dos pestañas con la misma boleta PENDING
2. En ambas, ir a edit
3. Modificar diferentes campos
4. Guardar en ambas casi simultáneamente

**Resultado Esperado:**
- Una de las transacciones espera a que la otra termine (lock)
- No hay pérdida de datos
- Los cambios de la segunda sobrescriben los de la primera (last write wins), pero de forma segura

---

### 30. Integración - Flujo Completo

**Descripción:** Verificar el flujo completo de crear → editar → eliminar.

**Pasos:**
1. Crear producto "Tornillo 8mm" con stock=100
2. Crear boleta PENDING:
   - Tornillo 8mm: qty=10, cost=50
3. Stock después de crear: 110
4. Editar boleta:
   - Cambiar qty=10 a qty=15
5. Stock después de editar: 115
6. Eliminar boleta
7. Stock después de eliminar: 100

**Resultado Esperado:**
- Stock vuelve exactamente al valor original (100)
- Todos los movimientos quedan registrados en stock_move
- La boleta desaparece del listado
- No quedan datos huérfanos en la BD

---

## Verificaciones Generales

### Verificar Stock Moves Auditoría

```sql
-- Ver todos los stock moves relacionados con una boleta
SELECT 
    sm.id,
    sm.date,
    sm.type,
    sm.reference_type,
    sm.reference_id,
    sm.notes,
    sml.product_id,
    p.name AS product_name,
    sml.qty
FROM stock_move sm
JOIN stock_move_line sml ON sml.stock_move_id = sm.id
JOIN product p ON p.id = sml.product_id
WHERE sm.reference_type = 'INVOICE' AND sm.reference_id = [ID_INVOICE]
OR sm.notes LIKE '%Boleta #[NUMERO]%'
ORDER BY sm.id DESC;
```

### Verificar Stock Final Correcto

```sql
-- Comparar stock esperado vs real
SELECT 
    p.id,
    p.name,
    ps.on_hand_qty AS stock_actual,
    -- Calcular stock esperado sumando todos los movimientos
    COALESCE((
        SELECT SUM(
            CASE 
                WHEN sm.type = 'IN' THEN sml.qty
                WHEN sm.type = 'OUT' THEN -sml.qty
                WHEN sm.type = 'ADJUST' THEN sml.qty
            END
        )
        FROM stock_move_line sml
        JOIN stock_move sm ON sm.id = sml.stock_move_id
        WHERE sml.product_id = p.id
    ), 0) AS stock_calculado
FROM product p
JOIN product_stock ps ON ps.product_id = p.id
WHERE p.name IN ('Tornillo 8mm', 'Cable 2.5mm', 'Martillo');
-- stock_actual DEBE SER IGUAL a stock_calculado
```

### Verificar Integridad de Ledger

```sql
-- Verificar que solo boletas PAID tienen ledger entry
SELECT 
    pi.id AS invoice_id,
    pi.invoice_number,
    pi.status,
    pi.total_amount,
    COUNT(fl.id) AS ledger_count,
    SUM(fl.amount) AS ledger_total
FROM purchase_invoice pi
LEFT JOIN finance_ledger fl ON fl.reference_type = 'INVOICE_PAYMENT' AND fl.reference_id = pi.id
GROUP BY pi.id, pi.invoice_number, pi.status, pi.total_amount
ORDER BY pi.id;
-- Para PENDING: ledger_count = 0
-- Para PAID: ledger_count = 1, ledger_total = pi.total_amount
```

---

## Checklist Final

- [ ] Acceso a edición para PENDING
- [ ] Bloqueo de edición para PAID
- [ ] Bloqueo de eliminación para PAID
- [ ] Editar: aumentar cantidad → stock aumenta
- [ ] Editar: disminuir cantidad → stock disminuye
- [ ] Editar: eliminar ítem → stock disminuye
- [ ] Editar: agregar ítem → stock aumenta
- [ ] Editar: cambiar proveedor
- [ ] Editar: cambiar número de boleta
- [ ] Editar: validación número duplicado
- [ ] Editar: validación líneas vacías
- [ ] Editar: validación cantidad <= 0
- [ ] Editar: validación producto duplicado
- [ ] Editar: total recalculado server-side
- [ ] Editar: transacción atómica
- [ ] Eliminar: boleta sin ítems
- [ ] Eliminar: boleta con ítems → stock se revierte
- [ ] Eliminar: bloqueado para PAID
- [ ] Eliminar: múltiples ítems → todos se revierten
- [ ] UI: botones en listado correctos
- [ ] UI: botones en detalle correctos
- [ ] UI: modal edición completo
- [ ] UI: modal eliminación completo
- [ ] UI: cancelar modales funciona
- [ ] Editar: cambiar fechas
- [ ] Ledger NO se toca para PENDING
- [ ] Ledger se preserva para PAID
- [ ] Auditoría: stock moves creados correctamente
- [ ] Performance: lock FOR UPDATE funciona
- [ ] Integración: flujo completo crear → editar → eliminar

---

## Conclusión

Este documento cubre todos los casos de prueba necesarios para validar la funcionalidad de editar y eliminar boletas con ajuste automático de stock y respeto de las reglas de negocio.

Para reportar bugs, incluir:
- Caso de prueba que falló
- Pasos para reproducir
- Resultado esperado vs resultado real
- Screenshots/logs si aplica
- Estado de stock antes y después
- SQL queries de verificación
