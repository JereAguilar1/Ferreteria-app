# 🧪 **MEJORA 13: Presupuestos Persistidos - Casos de Prueba**

---

## **📋 Resumen de la Mejora**

**Objetivo**: Evolucionar la funcionalidad de "Presupuesto PDF" a un módulo completo de presupuestos persistidos en base de datos con capacidad de conversión a ventas.

**Funcionalidades implementadas**:
- ✅ Guardar presupuestos desde el carrito (sin afectar stock ni finanzas)
- ✅ Listado de presupuestos con filtros por estado y búsqueda
- ✅ Detalle de presupuesto con líneas, totales y acciones
- ✅ Descargar PDF desde presupuesto guardado
- ✅ Convertir presupuesto a venta (transaccional con validación de stock)
- ✅ Estados: DRAFT, SENT, ACCEPTED, CANCELED
- ✅ Expiración calculada (no persistida)
- ✅ Snapshot de precios y nombres de productos

---

## **🎯 PARTE 1: Crear Presupuesto desde Carrito**

### **Caso 1.1: Carrito Vacío - Bloqueado**
**Objetivo**: Verificar que no se puede crear presupuesto sin productos.

**Pasos**:
1. Ir a `/sales/new`
2. No agregar ningún producto al carrito
3. Intentar hacer clic en "Guardar como Presupuesto"

**Resultado esperado**:
- ✅ El botón no debería estar visible (carrito vacío)
- ✅ Si se accede directo al endpoint: flash message "El carrito está vacío..."
- ✅ Redirección a `/sales/new`
- ✅ NO se crea registro en DB

---

### **Caso 1.2: Crear Presupuesto con 1 Producto**
**Objetivo**: Verificar creación básica de presupuesto.

**Pasos**:
1. Ir a `/sales/new`
2. Agregar 1 producto al carrito (ej: 5 unidades de Tornillo)
3. Seleccionar método de pago: Efectivo
4. Hacer clic en "Guardar como Presupuesto"

**Resultado esperado**:
- ✅ Redirección a `/quotes/<id>`
- ✅ Flash message: "Presupuesto creado exitosamente."
- ✅ Carrito se vacía después de guardar
- ✅ En DB:
  - Quote creado con status DRAFT
  - quote_number único (PRES-YYYYMMDD-HHMMSS-####)
  - valid_until = issued_at + 7 días (default)
  - payment_method = CASH
  - total_amount correcto
- ✅ QuoteLine creado con:
  - product_name_snapshot = nombre actual
  - uom_snapshot = símbolo UOM actual
  - unit_price = sale_price actual del producto
  - line_total = qty * unit_price
- ✅ NO se crea sale
- ✅ NO se crea stock_move
- ✅ NO se crea finance_ledger
- ✅ Stock NO descontado

**Verificación en DB**:
```sql
SELECT id, quote_number, status, issued_at, valid_until, total_amount, payment_method, sale_id
FROM quote
ORDER BY id DESC
LIMIT 1;

SELECT id, quote_id, product_name_snapshot, uom_snapshot, qty, unit_price, line_total
FROM quote_line
WHERE quote_id = <último_id>
ORDER BY id;
```

---

### **Caso 1.3: Crear Presupuesto con Múltiples Productos**
**Objetivo**: Verificar cálculo correcto de totales con varias líneas.

**Pasos**:
1. Agregar 3-5 productos diferentes al carrito
2. Con cantidades variadas (enteros y decimales)
3. Seleccionar método: Transferencia
4. Guardar como presupuesto

**Resultado esperado**:
- ✅ Quote con total = suma de todos line_total
- ✅ Todas las líneas creadas correctamente
- ✅ payment_method = TRANSFER
- ✅ Snapshot de nombres y UOM correcto

**Verificación Manual**:
- Sumar manualmente qty * unit_price de cada línea
- Confirmar que coincide con quote.total_amount

---

### **Caso 1.4: Quote Number Único**
**Objetivo**: Verificar unicidad de números de presupuesto.

**Pasos**:
1. Crear 3 presupuestos consecutivos (rápido, mismo minuto si es posible)

**Resultado esperado**:
- ✅ Cada quote_number es único
- ✅ Formato: `PRES-YYYYMMDD-HHMMSS-0001`, `PRES-YYYYMMDD-HHMMSS-0002`, etc.
- ✅ La secuencia incrementa correctamente

**Verificación en DB**:
```sql
SELECT quote_number, created_at
FROM quote
ORDER BY created_at DESC
LIMIT 5;
```

---

## **🎯 PARTE 2: Listado de Presupuestos**

### **Caso 2.1: Listado Sin Filtros**
**Objetivo**: Verificar que el listado muestra todos los presupuestos.

**Pasos**:
1. Ir a `/quotes`

**Resultado esperado**:
- ✅ Tabla con todos los presupuestos
- ✅ Columnas: Número, Fecha Emisión, Válido Hasta, Total, Estado, Acciones
- ✅ Ordenados por fecha de emisión (más reciente primero)
- ✅ Badges de estado con colores correctos:
  - DRAFT: gris
  - SENT: azul
  - ACCEPTED: verde
  - CANCELED: rojo

---

### **Caso 2.2: Filtro por Estado**
**Objetivo**: Verificar filtro de estado.

**Pasos**:
1. Ir a `/quotes`
2. Seleccionar "Estado: Borrador"
3. Aplicar filtro

**Resultado esperado**:
- ✅ Solo muestra presupuestos con status = DRAFT
- ✅ Query params persisten: `status=DRAFT`
- ✅ Select mantiene el valor seleccionado

**Repetir con**: SENT, ACCEPTED, CANCELED

---

### **Caso 2.3: Búsqueda por Número**
**Objetivo**: Verificar búsqueda por quote_number.

**Pasos**:
1. Copiar un quote_number existente (ej: PRES-20260112-143000-0001)
2. Pegarlo en el campo de búsqueda
3. Aplicar filtro

**Resultado esperado**:
- ✅ Solo muestra ese presupuesto
- ✅ Búsqueda es case-insensitive (ILIKE)
- ✅ También funciona con búsqueda parcial (ej: "PRES-20260112")

---

### **Caso 2.4: Presupuesto Vencido - Badge**
**Objetivo**: Verificar que se muestra badge "Vencido" cuando aplica.

**Pre-condición**: Tener un presupuesto DRAFT con `valid_until` en el pasado
(Se puede hacer manualmente en DB para testing rápido)

```sql
UPDATE quote
SET valid_until = '2025-12-31'
WHERE id = <id_de_prueba>;
```

**Pasos**:
1. Ir a `/quotes`

**Resultado esperado**:
- ✅ El presupuesto muestra badge amarillo "⚠ Vencido" junto a la fecha
- ✅ Solo se muestra para DRAFT y SENT
- ✅ NO se muestra para ACCEPTED o CANCELED

---

## **🎯 PARTE 3: Detalle de Presupuesto**

### **Caso 3.1: Ver Detalle**
**Objetivo**: Verificar información completa del presupuesto.

**Pasos**:
1. Desde el listado, hacer clic en "Ver" (ícono ojo)
2. Ir a `/quotes/<id>`

**Resultado esperado**:
- ✅ Muestra información de cabecera:
  - Número, Estado, Fecha Emisión, Válido Hasta
  - Método de Pago (si existe)
  - Total destacado
  - Notas (si existen)
- ✅ Tabla de líneas con todos los productos
- ✅ Columnas: Producto (con ID), UOM, Cantidad, Precio Unit., Subtotal
- ✅ Total al pie coincide con suma de subtotales
- ✅ Snapshot de nombres se muestra correctamente

---

### **Caso 3.2: Botones de Acción - DRAFT**
**Objetivo**: Verificar botones disponibles para presupuesto DRAFT.

**Pasos**:
1. Ver detalle de un presupuesto DRAFT no vencido

**Resultado esperado**:
- ✅ Botones visibles:
  - "Descargar PDF"
  - "Convertir a Venta"
  - "Marcar como Enviado"
  - "Cancelar Presupuesto"

---

### **Caso 3.3: Botones de Acción - ACCEPTED**
**Objetivo**: Verificar que presupuesto aceptado no tiene acciones destructivas.

**Pre-condición**: Tener un presupuesto ACCEPTED

**Pasos**:
1. Ver detalle

**Resultado esperado**:
- ✅ Solo botón "Descargar PDF" visible
- ✅ NO se muestran: Convertir, Marcar, Cancelar
- ✅ Muestra alert verde: "Presupuesto Aceptado: Venta #X"
- ✅ Si existe ruta de ventas, podría mostrar link

---

## **🎯 PARTE 4: Descargar PDF desde DB**

### **Caso 4.1: PDF de Presupuesto Guardado**
**Objetivo**: Verificar generación de PDF desde quote persistido.

**Pasos**:
1. Ir a detalle de cualquier presupuesto
2. Hacer clic en "Descargar PDF"

**Resultado esperado**:
- ✅ Se descarga archivo `presupuesto_PRES-YYYYMMDD-HHMMSS-####.pdf`
- ✅ PDF contiene:
  - Número de presupuesto (desde DB)
  - Fecha emisión (DD/MM/YYYY)
  - Válido hasta (DD/MM/YYYY)
  - Estado del presupuesto
  - Método de pago (si existe)
  - Todas las líneas con nombres snapshot
  - Total correcto
  - Notas (si existen)
- ✅ NO afecta base de datos (solo lectura)

**Verificación**:
- Comparar total del PDF con el mostrado en detalle
- Verificar que nombres de productos vienen del snapshot, no de la tabla `product` actual

---

### **Caso 4.2: PDF de Presupuesto CANCELED**
**Objetivo**: Verificar que se puede descargar PDF incluso si está cancelado.

**Pasos**:
1. Crear presupuesto
2. Cancelarlo
3. Descargar PDF

**Resultado esperado**:
- ✅ PDF descarga correctamente
- ✅ Muestra estado "Cancelado"

---

## **🎯 PARTE 5: Convertir a Venta**

### **Caso 5.1: Conversión Exitosa - DRAFT con Stock Suficiente**
**Objetivo**: Verificar flujo completo de conversión.

**Pre-condición**: 
- Presupuesto DRAFT con producto que tiene stock >= qty
- Ejemplo: Presupuesto con 5 unidades de producto X, stock actual 10

**Pasos**:
1. Ir a detalle del presupuesto
2. Hacer clic en "Convertir a Venta"
3. Confirmar en el diálogo

**Resultado esperado**:
- ✅ Flash message: "Presupuesto convertido a venta #X exitosamente..."
- ✅ Permanece en `/quotes/<id>` pero actualizado
- ✅ En DB - Quote:
  - status = ACCEPTED
  - sale_id = <id_de_venta_creada>
- ✅ En DB - Sale:
  - Nueva venta creada
  - total = quote.total_amount
  - status = CONFIRMED
  - datetime = ahora
- ✅ En DB - SaleLine:
  - Líneas creadas desde quote_line
  - Mismos qty, unit_price, line_total (snapshot)
- ✅ En DB - StockMove:
  - type = OUT
  - reference_type = SALE
  - reference_id = sale.id
  - notes menciona presupuesto
- ✅ En DB - StockMoveLine:
  - Líneas de movimiento creadas
  - qty correcta
- ✅ En DB - ProductStock:
  - on_hand_qty descontado vía trigger
  - Ejemplo: si tenía 10, ahora tiene 5
- ✅ En DB - FinanceLedger:
  - type = INCOME
  - amount = quote.total_amount
  - reference_type = SALE
  - reference_id = sale.id
  - payment_method = quote.payment_method (o CASH default)
  - notes menciona presupuesto

**Verificación SQL**:
```sql
-- Ver quote actualizado
SELECT id, quote_number, status, sale_id
FROM quote
WHERE id = <quote_id>;

-- Ver venta creada
SELECT id, datetime, total, status
FROM sale
WHERE id = (SELECT sale_id FROM quote WHERE id = <quote_id>);

-- Ver líneas de venta
SELECT id, sale_id, product_id, qty, unit_price, line_total
FROM sale_line
WHERE sale_id = <sale_id>;

-- Ver stock actualizado
SELECT product_id, on_hand_qty
FROM product_stock
WHERE product_id IN (
  SELECT product_id FROM quote_line WHERE quote_id = <quote_id>
);

-- Ver movimiento de stock
SELECT id, type, reference_type, reference_id, notes
FROM stock_move
WHERE reference_type = 'SALE' AND reference_id = <sale_id>;

-- Ver registro financiero
SELECT id, type, amount, payment_method, reference_type, reference_id, notes
FROM finance_ledger
WHERE reference_type = 'SALE' AND reference_id = <sale_id>;
```

---

### **Caso 5.2: Conversión Bloqueada - Stock Insuficiente**
**Objetivo**: Verificar que la conversión falla si no hay stock.

**Pre-condición**:
- Presupuesto DRAFT con producto que tiene stock < qty
- Ejemplo: Presupuesto con 10 unidades, stock actual 3

**Pasos**:
1. Intentar convertir a venta

**Resultado esperado**:
- ✅ Flash message error: "Stock insuficiente para <producto>. Requerido: 10, Disponible: 3"
- ✅ Permanece en detalle del presupuesto
- ✅ En DB:
  - Quote NO cambia (status sigue DRAFT, sale_id sigue NULL)
  - NO se crea sale
  - NO se crea stock_move
  - NO se crea finance_ledger
  - Stock NO se modifica
- ✅ Transacción rollback completo

**Verificación SQL**:
```sql
-- Quote debe seguir igual
SELECT id, status, sale_id
FROM quote
WHERE id = <quote_id>;
-- Resultado: status=DRAFT, sale_id=NULL

-- No debe haber venta nueva
SELECT COUNT(*)
FROM sale
WHERE id > <último_id_antes_de_intentar>;
-- Resultado: 0
```

---

### **Caso 5.3: Conversión Bloqueada - Quote ACCEPTED**
**Objetivo**: Verificar que no se puede convertir dos veces.

**Pre-condición**: Presupuesto ya ACCEPTED con sale_id

**Pasos**:
1. Intentar acceder al endpoint de conversión directamente
(El botón no debería estar visible en UI)

**Resultado esperado**:
- ✅ Flash message: "Este presupuesto ya fue convertido a una venta."
- ✅ NO crea nueva venta
- ✅ Redirect a detalle

---

### **Caso 5.4: Conversión Bloqueada - Quote CANCELED**
**Objetivo**: Verificar que presupuesto cancelado no se puede convertir.

**Pre-condición**: Presupuesto CANCELED

**Pasos**:
1. Intentar conversión (botón no debería estar visible)

**Resultado esperado**:
- ✅ Flash message: "El presupuesto está en estado CANCELED..."
- ✅ NO crea venta

---

### **Caso 5.5: Conversión Bloqueada - Quote Vencido**
**Objetivo**: Verificar que presupuesto vencido no se puede convertir.

**Pre-condición**: 
- Presupuesto DRAFT con `valid_until` en el pasado

**Pasos**:
1. Intentar conversión (botón debería estar deshabilitado o no visible)

**Resultado esperado**:
- ✅ Flash message: "Este presupuesto está vencido..."
- ✅ NO crea venta

---

### **Caso 5.6: Conversión con Múltiples Productos - Validación Atómica**
**Objetivo**: Verificar que si un producto no tiene stock, nada se crea.

**Pre-condición**:
- Presupuesto con 3 productos:
  - Producto A: qty=5, stock=10 ✅
  - Producto B: qty=2, stock=1 ❌
  - Producto C: qty=3, stock=20 ✅

**Pasos**:
1. Intentar conversión

**Resultado esperado**:
- ✅ Error en producto B
- ✅ Rollback completo:
  - NO se descuenta stock de A ni C
  - NO se crea venta
  - Quote sigue DRAFT
- ✅ Todos o nada (transacción atómica)

---

## **🎯 PARTE 6: Cancelar Presupuesto**

### **Caso 6.1: Cancelar DRAFT**
**Objetivo**: Verificar cancelación de presupuesto borrador.

**Pasos**:
1. Ver detalle de presupuesto DRAFT
2. Hacer clic en "Cancelar Presupuesto"
3. Confirmar

**Resultado esperado**:
- ✅ Flash message: "Presupuesto cancelado exitosamente."
- ✅ En DB:
  - status = CANCELED
  - sale_id sigue NULL
- ✅ Botones de acción desaparecen (solo queda PDF)
- ✅ Muestra alert rojo: "Presupuesto Cancelado"

---

### **Caso 6.2: Cancelar SENT**
**Objetivo**: Verificar que SENT también se puede cancelar.

**Pasos**:
1. Marcar DRAFT como enviado
2. Cancelar

**Resultado esperado**:
- ✅ Se cancela correctamente

---

### **Caso 6.3: No Cancelar ACCEPTED**
**Objetivo**: Verificar que presupuesto aceptado no se puede cancelar.

**Pasos**:
1. Intentar cancelar presupuesto ACCEPTED (botón no debería existir)

**Resultado esperado**:
- ✅ Si se accede directo al endpoint: error
- ✅ "No se puede cancelar un presupuesto en estado ACCEPTED."

---

## **🎯 PARTE 7: Marcar como Enviado**

### **Caso 7.1: DRAFT → SENT**
**Objetivo**: Verificar cambio de estado a enviado.

**Pasos**:
1. Ver detalle de presupuesto DRAFT
2. Hacer clic en "Marcar como Enviado"

**Resultado esperado**:
- ✅ Flash message: "Presupuesto marcado como enviado."
- ✅ En DB: status = SENT
- ✅ Badge cambia a azul "Enviado"
- ✅ Botón "Marcar como Enviado" desaparece
- ✅ Botón "Convertir a Venta" sigue disponible

---

### **Caso 7.2: No Marcar como Enviado si NO es DRAFT**
**Objetivo**: Verificar que solo DRAFT puede marcarse como enviado.

**Pasos**:
1. Intentar marcar ACCEPTED como enviado

**Resultado esperado**:
- ✅ Flash message: "Solo presupuestos en estado DRAFT pueden marcarse..."

---

## **🎯 PARTE 8: Validación de Expiración**

### **Caso 8.1: Cálculo de valid_until**
**Objetivo**: Verificar que valid_until se calcula correctamente.

**Pre-configuración**: `QUOTE_VALID_DAYS=7` en `.env`

**Pasos**:
1. Crear presupuesto hoy

**Resultado esperado**:
- ✅ issued_at = hoy
- ✅ valid_until = hoy + 7 días

**Verificación SQL**:
```sql
SELECT issued_at::date, valid_until, 
       (valid_until - issued_at::date) AS dias_validez
FROM quote
WHERE id = <ultimo_id>;
-- Resultado: dias_validez = 7
```

---

### **Caso 8.2: Cambiar QUOTE_VALID_DAYS**
**Objetivo**: Verificar que config es respetada.

**Pre-configuración**: `QUOTE_VALID_DAYS=15`

**Pasos**:
1. Reiniciar Docker
2. Crear presupuesto

**Resultado esperado**:
- ✅ valid_until = issued_at + 15 días

---

## **🎯 PARTE 9: Snapshot de Datos**

### **Caso 9.1: Precio Cambia Después de Quote**
**Objetivo**: Verificar que snapshot preserva precio original.

**Pasos**:
1. Crear presupuesto con producto A que cuesta $100
2. Guardar presupuesto
3. Cambiar precio del producto A a $150 en DB
4. Ver detalle del presupuesto
5. Descargar PDF
6. Convertir a venta

**Resultado esperado**:
- ✅ Detalle muestra $100 (unit_price snapshot)
- ✅ PDF muestra $100
- ✅ Venta se crea con $100 (no $150)
- ✅ Finance_ledger registra ingreso basado en precio snapshot

**Verificación SQL**:
```sql
-- Ver precio actual vs precio snapshot
SELECT p.id, p.name, p.sale_price AS precio_actual,
       ql.unit_price AS precio_snapshot
FROM product p
JOIN quote_line ql ON ql.product_id = p.id
WHERE ql.quote_id = <quote_id>;
```

---

### **Caso 9.2: Nombre de Producto Cambia**
**Objetivo**: Verificar que snapshot preserva nombre.

**Pasos**:
1. Crear presupuesto con producto "Tornillo M10"
2. Cambiar nombre a "Tornillo M10 - NUEVO"
3. Ver presupuesto

**Resultado esperado**:
- ✅ Detalle muestra "Tornillo M10" (snapshot)
- ✅ PDF muestra "Tornillo M10"

---

### **Caso 9.3: Producto Eliminado**
**Objetivo**: Verificar que presupuesto mantiene info aunque producto se elimine.

**Nota**: Esto fallará con ON DELETE RESTRICT en product_id FK.
El diseño actual protege contra eliminación.

**Comportamiento esperado**:
- ✅ No se puede eliminar producto si existe en quote_line
- ✅ Error: "violates foreign key constraint"

---

## **📊 Resumen de Pruebas**

| Categoría | Casos | Críticos |
|-----------|-------|----------|
| **Crear Presupuesto** | 4 | ✅ 1.2, 1.3 |
| **Listado** | 4 | ✅ 2.1 |
| **Detalle** | 3 | ✅ 3.1 |
| **PDF** | 2 | ✅ 4.1 |
| **Convertir a Venta** | 6 | ✅ 5.1, 5.2, 5.6 |
| **Cancelar** | 3 | ✅ 6.1 |
| **Marcar Enviado** | 2 | 7.1 |
| **Expiración** | 2 | 8.1 |
| **Snapshot** | 3 | ✅ 9.1 |
| **TOTAL** | **29** | **10** |

---

## **✅ Checklist de Aceptación Final**

### **Funcionalidades Core**
- [ ] Guardar presupuesto desde POS crea quote + lines
- [ ] Carrito se vacía después de guardar
- [ ] NO afecta stock ni finanzas al crear quote
- [ ] Listado muestra todos los presupuestos
- [ ] Filtros por estado funcionan
- [ ] Búsqueda por número funciona
- [ ] Detalle muestra info completa
- [ ] PDF descarga desde quote guardado
- [ ] PDF usa snapshot de precios/nombres
- [ ] Convertir a venta crea sale + stock_move + ledger
- [ ] Conversión descuenta stock (vía trigger)
- [ ] Conversión falla con stock insuficiente (rollback)
- [ ] No se puede convertir dos veces
- [ ] No se puede convertir presupuesto vencido
- [ ] No se puede convertir presupuesto cancelado
- [ ] Cancelar presupuesto funciona (DRAFT/SENT)
- [ ] Marcar como enviado funciona (DRAFT → SENT)

### **Datos y Validaciones**
- [ ] quote_number único con timestamp + secuencia
- [ ] valid_until calculado correctamente (issued_at + X días)
- [ ] Expiración calculada en UI (no persistida)
- [ ] Snapshot preserva precio aunque cambie
- [ ] Snapshot preserva nombre aunque cambie
- [ ] Método de pago persiste si se selecciona
- [ ] Totales correctos en quote y sale

### **Transaccionalidad**
- [ ] Conversión es atómica (todo o nada)
- [ ] Usa SELECT FOR UPDATE en quote y product_stock
- [ ] Rollback correcto en error de stock
- [ ] No deja registros huérfanos si falla

### **UI/UX**
- [ ] Link "Presupuestos" en navbar
- [ ] Botón "Guardar como Presupuesto" en POS
- [ ] Badges de estado con colores correctos
- [ ] Badge "Vencido" se muestra cuando aplica
- [ ] Botones de acción apropiados según estado
- [ ] Flash messages informativos
- [ ] Confirmaciones antes de acciones irreversibles

---

## **🚀 Flujo de Prueba Manual Completo**

### **Flujo 1: Happy Path - Crear y Convertir**
```
1. Login
2. Ir a /sales/new
3. Agregar 2-3 productos (con stock suficiente)
4. Seleccionar método: Efectivo
5. Click "Guardar como Presupuesto"
6. Verificar redirección a detalle
7. Verificar info correcta (número, total, líneas)
8. Descargar PDF y revisar
9. Click "Convertir a Venta"
10. Confirmar
11. Verificar flash success
12. Verificar estado = ACCEPTED
13. Verificar sale_id visible
14. Verificar en DB:
    - Stock descontado
    - Sale creada
    - Ledger INCOME creado
```

### **Flujo 2: Stock Insuficiente**
```
1. Crear presupuesto con producto que tiene poco stock
2. (Opcional) Reducir stock manualmente en DB para simular
3. Intentar convertir
4. Verificar error y rollback
5. Verificar quote sigue DRAFT
6. Verificar stock no cambió
```

### **Flujo 3: Cancelación**
```
1. Crear presupuesto
2. Marcar como enviado
3. Cancelar
4. Verificar estado CANCELED
5. Verificar botón convertir NO disponible
6. Verificar PDF aún descargable
```

---

**✅ FIN DE TESTING MEJORA 13**
