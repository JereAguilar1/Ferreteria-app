# 🧪 **MEJORA 16: Corrección de Ventas Confirmadas - Casos de Prueba**

---

## **📋 Resumen de la Mejora**

**Objetivo**: Permitir corregir ventas ya confirmadas cuando hubo errores en el POS, manteniendo trazabilidad completa.

**Funcionalidades implementadas**:
- ✅ Listado de ventas confirmadas con búsqueda
- ✅ Detalle de venta con información completa
- ✅ Formulario de edición de venta (aumentar/disminuir qty, eliminar/agregar líneas)
- ✅ Servicio transaccional `adjust_sale()` que:
  - Recalcula total de venta
  - Crea movimientos de stock tipo ADJUST con delta
  - Crea asientos contables compensatorios (INCOME o EXPENSE)
  - Mantiene trazabilidad (no borra historia)
- ✅ Validaciones robustas (stock, qty, productos inactivos)

---

## **🎯 PARTE 1: Listado y Detalle de Ventas**

### **Caso 1.1: Ver Listado de Ventas**
**Objetivo**: Verificar que se muestran todas las ventas confirmadas.

**Pasos**:
1. Ir a "Ventas" → "Gestión de Ventas" en navbar
2. O navegar directamente a `/sales`

**Resultado esperado**:
- ✅ Se muestra tabla con ventas confirmadas
- ✅ Columnas: ID, Fecha, Total, Estado, Acciones
- ✅ Ventas ordenadas por más reciente primero
- ✅ Botones: Ver Detalle (👁️) y Editar (✏️)

**Verificación DB**:
```sql
SELECT id, datetime, total, status 
FROM sale 
WHERE status = 'CONFIRMED' 
ORDER BY datetime DESC;
```

---

### **Caso 1.2: Buscar Venta por ID**
**Objetivo**: Verificar búsqueda por ID de venta.

**Pasos**:
1. En listado de ventas
2. Ingresar ID: 123 en campo de búsqueda
3. Click "Buscar"

**Resultado esperado**:
- ✅ Solo se muestra venta #123
- ✅ Botón "Limpiar" aparece
- ✅ Si no existe: mensaje "No se encontraron ventas con ID: 123"

---

### **Caso 1.3: Ver Detalle de Venta**
**Objetivo**: Verificar que se muestra toda la información de la venta.

**Pasos**:
1. En listado, click en 👁️ de una venta
2. O navegar a `/sales/<id>`

**Resultado esperado**:
- ✅ Card con información: ID, Fecha, Total, Estado
- ✅ Tabla de productos vendidos con: Nombre, Cantidad, Precio Unit., Subtotal
- ✅ Total destacado al final
- ✅ Botón "Editar/Ajustar" visible si status=CONFIRMED
- ✅ Alert informativo sobre ajustes

---

## **🎯 PARTE 2: Editar Venta - Disminuir Cantidades**

### **Caso 2.1: Disminuir Qty de un Producto - Stock Aumenta**
**Objetivo**: Verificar que al disminuir qty se devuelve stock y se ajusta ledger.

**Setup Inicial**:
```sql
-- Venta original:
-- Producto A: qty=10, precio=$5, subtotal=$50
-- Total: $50
-- Stock antes: 20
-- Ledger INCOME original: $50
```

**Pasos**:
1. Ir a `/sales/<id>/edit`
2. Cambiar qty de Producto A de 10 a 5
3. Verificar subtotal se recalcula: $25
4. Verificar total se recalcula: $25
5. Click "Guardar Cambios"
6. Confirmar en prompt

**Resultado esperado**:
- ✅ Flash: "Venta #X ajustada exitosamente"
- ✅ Redirect a `/sales/<id>` (detalle)
- ✅ Venta muestra qty=5 y total=$25

**Verificación DB**:
```sql
-- Sale line actualizada
SELECT qty, unit_price, line_total 
FROM sale_line 
WHERE sale_id=<id> AND product_id=<product_a>;
-- Resultado: qty=5, line_total=$25

-- Sale total actualizado
SELECT total FROM sale WHERE id=<id>;
-- Resultado: total=$25

-- Stock aumentó (devolvió 5 unidades)
SELECT on_hand_qty FROM product_stock WHERE product_id=<product_a>;
-- Resultado: 20 + 5 = 25

-- Stock move ADJUST creado
SELECT * FROM stock_move 
WHERE type='ADJUST' 
  AND notes LIKE '%Ajuste de venta #<id>%';
-- Existe 1 fila

-- Stock move line con delta
SELECT product_id, qty 
FROM stock_move_line 
WHERE stock_move_id=<adjust_move_id>;
-- Producto A: qty=5 (devuelto)

-- Ledger EXPENSE creado (venta menor = menos ingreso = gasto)
SELECT type, amount, notes 
FROM finance_ledger 
WHERE reference_type='MANUAL' 
  AND reference_id=<id> 
  AND notes LIKE '%Ajuste negativo%';
-- type=EXPENSE, amount=25 (50 - 25)
```

---

### **Caso 2.2: Disminuir Qty de Múltiples Productos**
**Objetivo**: Verificar que se pueden ajustar varios productos simultáneamente.

**Setup**:
```
Venta original:
- Producto A: qty=10, precio=$5, subtotal=$50
- Producto B: qty=2, precio=$20, subtotal=$40
Total: $90
```

**Pasos**:
1. Editar venta
2. Cambiar:
   - Producto A: 10 → 8 (reducir 2)
   - Producto B: 2 → 1 (reducir 1)
3. Guardar

**Resultado esperado**:
- ✅ Total nuevo: (8×$5) + (1×$20) = $60
- ✅ Stock Producto A aumenta en 2
- ✅ Stock Producto B aumenta en 1
- ✅ Ledger EXPENSE: $30 (90 - 60)

---

## **🎯 PARTE 3: Editar Venta - Aumentar Cantidades**

### **Caso 3.1: Aumentar Qty - Stock Disminuye (Con Stock Suficiente)**
**Objetivo**: Verificar que al aumentar qty se descuenta más stock.

**Setup**:
```
Venta original:
- Producto A: qty=5, precio=$10, subtotal=$50
Total: $50
Stock actual Producto A: 20
```

**Pasos**:
1. Editar venta
2. Cambiar Producto A qty de 5 a 10 (aumentar 5)
3. Guardar

**Resultado esperado**:
- ✅ Total nuevo: $100
- ✅ Stock Producto A disminuye en 5: 20 → 15
- ✅ Ledger INCOME: $50 (100 - 50)

**Verificación DB**:
```sql
-- Sale
SELECT total FROM sale WHERE id=<id>;
-- total=$100

-- Stock
SELECT on_hand_qty FROM product_stock WHERE product_id=<product_a>;
-- on_hand_qty=15

-- Ledger INCOME adicional
SELECT type, amount FROM finance_ledger 
WHERE reference_type='MANUAL' AND reference_id=<id> AND type='INCOME';
-- amount=50
```

---

### **Caso 3.2: Aumentar Qty - Stock Insuficiente - ERROR**
**Objetivo**: Verificar que se valida stock antes de permitir aumento.

**Setup**:
```
Venta original:
- Producto A: qty=5, precio=$10
Stock actual Producto A: 3 (insuficiente)
```

**Pasos**:
1. Editar venta
2. Cambiar Producto A qty de 5 a 10 (necesita 5 adicionales)
3. Guardar

**Resultado esperado**:
- ✅ Flash error: "Stock insuficiente para [Producto A]. Necesita 5 adicionales, disponible: 3"
- ✅ **Rollback completo**: NO se actualiza venta
- ✅ Stock NO cambia
- ✅ Total NO cambia
- ✅ NO se crea stock_move
- ✅ NO se crea ledger entry

**Verificación DB**:
```sql
-- Sale line sin cambios
SELECT qty FROM sale_line WHERE sale_id=<id> AND product_id=<product_a>;
-- qty=5 (sin cambios)

-- No nuevos stock_move desde el error
SELECT COUNT(*) FROM stock_move 
WHERE type='ADJUST' AND reference_id=<id> 
  AND date >= '<timestamp_intento>';
-- COUNT=0
```

---

## **🎯 PARTE 4: Editar Venta - Eliminar Líneas**

### **Caso 4.1: Eliminar una Línea - Stock se Devuelve**
**Objetivo**: Verificar que al eliminar una línea se devuelve todo el stock.

**Setup**:
```
Venta original:
- Producto A: qty=10, precio=$5, subtotal=$50
- Producto B: qty=2, precio=$20, subtotal=$40
Total: $90
```

**Pasos**:
1. Editar venta
2. Click en 🗑️ de Producto B
3. Verificar total se recalcula a $50
4. Guardar

**Resultado esperado**:
- ✅ Venta solo tiene Producto A
- ✅ Total: $50
- ✅ Stock Producto B aumenta en 2 (devuelto)
- ✅ Ledger EXPENSE: $40

**Verificación DB**:
```sql
-- Solo 1 línea en sale_line
SELECT COUNT(*) FROM sale_line WHERE sale_id=<id>;
-- COUNT=1

-- Producto B no está
SELECT COUNT(*) FROM sale_line WHERE sale_id=<id> AND product_id=<product_b>;
-- COUNT=0

-- Stock Producto B devuelto
SELECT on_hand_qty FROM product_stock WHERE product_id=<product_b>;
-- aumentó en 2
```

---

### **Caso 4.2: Eliminar Todas las Líneas - ERROR**
**Objetivo**: Verificar que no se puede guardar venta sin líneas.

**Pasos**:
1. Editar venta con 2 productos
2. Eliminar ambas líneas (click 🗑️ × 2)
3. Intentar guardar

**Resultado esperado**:
- ✅ JavaScript alert: "Debe haber al menos una línea en la venta"
- ✅ Form no se envía
- ✅ Usuario debe agregar al menos 1 producto antes de guardar

---

## **🎯 PARTE 5: Editar Venta - Agregar Productos Nuevos**

### **Caso 5.1: Agregar Producto Nuevo a la Venta**
**Objetivo**: Verificar que se pueden agregar productos que no estaban en la venta original.

**Setup**:
```
Venta original:
- Producto A: qty=5, precio=$10, subtotal=$50
Total: $50

Productos disponibles:
- Producto B: stock=20, precio=$15
```

**Pasos**:
1. Editar venta
2. En sección "Agregar Producto Nuevo":
   - Seleccionar Producto B
   - Cantidad: 3
   - Click "Agregar"
3. Verificar aparece en tabla con subtotal $45
4. Verificar total se recalcula: $95
5. Guardar

**Resultado esperado**:
- ✅ Venta tiene 2 líneas: Producto A (5) y Producto B (3)
- ✅ Total: $95
- ✅ Stock Producto B disminuye en 3: 20 → 17
- ✅ Ledger INCOME: $45

**Verificación DB**:
```sql
-- 2 líneas
SELECT COUNT(*) FROM sale_line WHERE sale_id=<id>;
-- COUNT=2

-- Producto B agregado
SELECT qty, unit_price, line_total 
FROM sale_line 
WHERE sale_id=<id> AND product_id=<product_b>;
-- qty=3, unit_price=15, line_total=45

-- Sale total
SELECT total FROM sale WHERE id=<id>;
-- total=95

-- Stock descontado
SELECT on_hand_qty FROM product_stock WHERE product_id=<product_b>;
-- 20 - 3 = 17
```

---

### **Caso 5.2: Agregar Producto con Stock Insuficiente - ERROR Frontend**
**Objetivo**: Verificar validación frontend antes de agregar.

**Pasos**:
1. Editar venta
2. Seleccionar Producto C con stock=5
3. Ingresar cantidad: 10
4. Click "Agregar"

**Resultado esperado**:
- ✅ JavaScript alert: "Stock insuficiente. Disponible: 5"
- ✅ Producto NO se agrega a la tabla
- ✅ Usuario debe corregir cantidad

---

### **Caso 5.3: Agregar Producto Ya Existente - ERROR**
**Objetivo**: Verificar que no se puede duplicar productos en la lista.

**Pasos**:
1. Editar venta que ya tiene Producto A
2. Intentar agregar Producto A nuevamente
3. Click "Agregar"

**Resultado esperado**:
- ✅ JavaScript alert: "Este producto ya está en la lista. Modifique la cantidad en la tabla."
- ✅ Producto NO se duplica
- ✅ Usuario debe editar qty del Producto A existente

---

## **🎯 PARTE 6: Validaciones y Consistencia**

### **Caso 6.1: Total se Recalcula Automáticamente en UI**
**Objetivo**: Verificar que el total se actualiza en tiempo real al editar.

**Pasos**:
1. Editar venta con Producto A qty=5, precio=$10 (total=$50)
2. Cambiar qty a 8 (sin guardar aún)

**Resultado esperado**:
- ✅ Subtotal se actualiza a $80
- ✅ Total se actualiza a $80 en el display (JavaScript)
- ✅ Usuario ve cambios antes de guardar

---

### **Caso 6.2: Confirmar Cambios - Prompt de Seguridad**
**Objetivo**: Verificar que se pide confirmación antes de guardar.

**Pasos**:
1. Editar venta y hacer cambios
2. Click "Guardar Cambios"

**Resultado esperado**:
- ✅ Prompt de confirmación: "¿Está seguro de guardar los cambios? Esto generará movimientos de ajuste..."
- ✅ Si usuario cancela: NO se envía form
- ✅ Si usuario confirma: Form se envía y se aplican cambios

---

### **Caso 6.3: Sale.total Coincide con Sum(sale_lines)**
**Objetivo**: Verificar consistencia de datos.

**Verificación SQL**:
```sql
-- Para una venta ajustada:
SELECT 
    s.id,
    s.total AS sale_total,
    COALESCE(SUM(sl.line_total), 0) AS sum_lines
FROM sale s
LEFT JOIN sale_line sl ON sl.sale_id = s.id
WHERE s.id = <id>
GROUP BY s.id, s.total;

-- sale_total DEBE ser igual a sum_lines
```

**Resultado esperado**:
- ✅ `sale_total = sum_lines`
- ✅ Si no coinciden, hay error en el servicio

---

### **Caso 6.4: Stock Final Coherente**
**Objetivo**: Verificar que el stock refleja correctamente todos los ajustes.

**Setup**:
```
Stock inicial Producto A: 100
Venta original: vendió 10 → stock=90
Ajuste: cambia qty de 10 a 15 (vende 5 más) → stock=85
```

**Verificación**:
```sql
SELECT on_hand_qty FROM product_stock WHERE product_id=<product_a>;
-- Debe ser 85
```

**Verificación Manual**:
- ✅ Calcular manualmente: inicio - venta_original - ajuste = resultado esperado
- ✅ Comparar con on_hand_qty actual

---

## **🎯 PARTE 7: Trazabilidad y Auditoría**

### **Caso 7.1: Movimientos de Ajuste Registrados Correctamente**
**Objetivo**: Verificar que los stock_move ADJUST existen y tienen notas claras.

**Pasos**:
1. Ajustar una venta
2. Consultar stock_move

**Verificación SQL**:
```sql
SELECT id, date, type, reference_type, reference_id, notes
FROM stock_move
WHERE type = 'ADJUST'
  AND notes LIKE '%Ajuste de venta #<id>%';
```

**Resultado esperado**:
- ✅ Existe 1 fila por cada ajuste
- ✅ `type = 'ADJUST'`
- ✅ `reference_type = 'MANUAL'` (o 'SALE_ADJUSTMENT' si extendiste enum)
- ✅ `reference_id = <sale_id>`
- ✅ Notas descriptivas: "Ajuste de venta #X - Corrección de líneas"

---

### **Caso 7.2: Ledger Entries Trazables**
**Objetivo**: Verificar que ajustes contables están registrados con notas claras.

**Verificación SQL**:
```sql
SELECT datetime, type, amount, category, notes
FROM finance_ledger
WHERE reference_type = 'MANUAL'
  AND reference_id = <sale_id>
  AND notes LIKE '%Ajuste%';
```

**Resultado esperado**:
- ✅ Si total aumentó: `type=INCOME`, `amount=diferencia`, nota "Ajuste positivo..."
- ✅ Si total disminuyó: `type=EXPENSE`, `amount=abs(diferencia)`, nota "Ajuste negativo..."
- ✅ Category: "Ajuste de Venta"

---

### **Caso 7.3: Historia Original No Se Borra**
**Objetivo**: Verificar que los registros contables y movimientos originales permanecen.

**Setup**:
```
Venta #123 original:
- Ledger INCOME: $100 (fecha X)
Ajuste:
- Ledger EXPENSE: $20 (fecha Y)
```

**Verificación SQL**:
```sql
SELECT datetime, type, amount, notes
FROM finance_ledger
WHERE reference_id = 123
  AND reference_type IN ('SALE', 'MANUAL')
ORDER BY datetime;
```

**Resultado esperado**:
- ✅ 2 registros (o más si hubo múltiples ajustes):
  1. INCOME $100 (original)
  2. EXPENSE $20 (ajuste)
- ✅ Fecha del ajuste > fecha original
- ✅ Ambos registros existen (nada borrado)

---

## **🎯 PARTE 8: Edge Cases y Errores**

### **Caso 8.1: Editar Venta CANCELLED - Bloqueado**
**Objetivo**: Verificar que solo ventas CONFIRMED se pueden ajustar.

**Pasos**:
1. Intentar acceder a `/sales/<id_cancelled>/edit`

**Resultado esperado**:
- ✅ Flash error: "Solo se pueden ajustar ventas confirmadas..."
- ✅ Redirect a listado
- ✅ NO se muestra formulario de edición

---

### **Caso 8.2: Qty = 0 en Formulario - ERROR**
**Objetivo**: Verificar que qty debe ser > 0.

**Pasos**:
1. Editar venta
2. Cambiar qty a 0
3. Guardar

**Resultado esperado**:
- ✅ HTML validation: `min="0.01"` impide guardar
- ✅ Si se bypasea: Backend valida y error "La cantidad debe ser mayor a 0..."

---

### **Caso 8.3: Producto Inactivo - No se Puede Agregar**
**Objetivo**: Verificar que productos inactivos no se pueden agregar.

**Setup**:
```
Producto C: active=False
```

**Pasos**:
1. Editar venta
2. Intentar agregar Producto C

**Resultado esperado**:
- ✅ Producto C NO aparece en el select de productos disponibles
- ✅ O si aparece (error UI): Backend valida y rechaza con error

---

### **Caso 8.4: Transacción Rollback en Error**
**Objetivo**: Verificar atomicidad de la transacción.

**Pasos**:
1. Editar venta con 2 productos
2. Aumentar qty Producto A: OK (stock suficiente)
3. Aumentar qty Producto B: ERROR (stock insuficiente)
4. Intentar guardar

**Resultado esperado**:
- ✅ **Rollback completo**: NADA se guarda
- ✅ Venta sin cambios (ni Producto A ni B)
- ✅ Stock sin cambios
- ✅ NO se crean stock_move ni ledger
- ✅ Flash error claro sobre Producto B

---

## **📊 Resumen de Pruebas**

| Categoría | Casos | Críticos |
|-----------|-------|----------|
| **Listado y Detalle** | 3 | ✅ 1.1, 1.3 |
| **Disminuir Qty** | 2 | ✅ 2.1 |
| **Aumentar Qty** | 2 | ✅ 3.1, 3.2 |
| **Eliminar Líneas** | 2 | ✅ 4.1 |
| **Agregar Productos** | 3 | ✅ 5.1 |
| **Validaciones** | 4 | ✅ 6.3, 6.4 |
| **Trazabilidad** | 3 | ✅ 7.1, 7.2, 7.3 |
| **Edge Cases** | 4 | ✅ 8.2, 8.4 |
| **TOTAL** | **23** | **13** |

---

## **✅ Checklist de Aceptación Final**

### **Funcionalidad**
- [ ] Listado de ventas muestra todas las confirmadas
- [ ] Búsqueda por ID funciona
- [ ] Detalle muestra toda la info de la venta
- [ ] Botón "Editar" visible solo para CONFIRMED
- [ ] Formulario de edición carga correctamente
- [ ] Cambiar qty recalcula subtotal y total en UI
- [ ] Eliminar línea actualiza total
- [ ] Agregar producto nuevo funciona
- [ ] Validación de stock frontend funciona
- [ ] Guardar cambios aplica ajustes correctamente

### **Ajustes de Stock**
- [ ] Disminuir qty devuelve stock
- [ ] Aumentar qty descuenta stock
- [ ] Eliminar línea devuelve stock completo
- [ ] Agregar producto descuenta stock
- [ ] Stock_move ADJUST creado
- [ ] Stock_move_line con delta correcto
- [ ] Stock nunca negativo

### **Ajustes Contables**
- [ ] Total nuevo > total anterior → INCOME creado
- [ ] Total nuevo < total anterior → EXPENSE creado
- [ ] amount = abs(diferencia)
- [ ] Category: "Ajuste de Venta"
- [ ] Notas descriptivas

### **Trazabilidad**
- [ ] Ledger original NO se borra
- [ ] Stock_move original NO se borra
- [ ] Ajustes quedan como registros adicionales
- [ ] Notas claras en ajustes
- [ ] reference_id apunta a la venta

### **Validaciones**
- [ ] Solo CONFIRMED se pueden editar
- [ ] Qty > 0 obligatorio
- [ ] Stock suficiente validado
- [ ] Productos inactivos rechazados
- [ ] Al menos 1 línea requerida
- [ ] Transacción atómica (rollback en error)

### **UX/UI**
- [ ] Total se recalcula en tiempo real
- [ ] Prompt de confirmación antes de guardar
- [ ] Flash messages claros
- [ ] Botones remove funcionan
- [ ] Agregar producto con validación
- [ ] No duplicar productos
- [ ] Navbar actualizado con dropdown

---

## **🚀 Flujo de Prueba Manual Completo**

### **Escenario Completo: Corrección de Venta con Error**
```
1. Crear venta original:
   - Producto A: qty=10, precio=$5 → $50
   - Producto B: qty=2, precio=$20 → $40
   Total: $90
   
2. Navegar a "Ventas" → "Gestión de Ventas"
   ✅ Venta aparece en listado

3. Click 👁️ Ver Detalle
   ✅ Muestra 2 productos, total $90

4. Click "Editar/Ajustar"
   ✅ Formulario carga con 2 líneas

5. Hacer correcciones:
   - Producto A: cambiar qty de 10 a 8 (error en POS, vendió menos)
   - Producto B: eliminar (nunca se vendió, error)
   - Agregar Producto C: qty=3, precio=$15
   
6. Verificar cálculos:
   - Subtotal A: 8 × $5 = $40
   - Subtotal C: 3 × $15 = $45
   - Total: $85
   
7. Click "Guardar Cambios"
   ✅ Prompt de confirmación

8. Confirmar
   ✅ Flash: "Venta ajustada exitosamente"
   ✅ Redirect a detalle

9. Verificar detalle:
   ✅ Solo 2 productos: A (qty=8) y C (qty=3)
   ✅ Total: $85

10. Verificar DB:
    Stock A: +2 (devuelto)
    Stock B: +2 (devuelto)
    Stock C: -3 (nuevo)
    Ledger EXPENSE: $5 (90 - 85)
    Stock_move ADJUST creado
```

---

**✅ FIN DE TESTING MEJORA 16**
