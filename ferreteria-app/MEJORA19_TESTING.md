# MEJORA 19: Modal Confirmación Pago Boleta + Fechas Argentinas - Testing Guide

## Mejoras Implementadas

### 1. Modal de Confirmación de Pago
Antes de pagar una boleta, se abre un modal Bootstrap con todos los detalles de la compra para confirmación.

### 2. Fechas en Formato Argentino
Todas las fechas en el módulo de boletas se muestran en formato DD/MM/YYYY.

---

## Pre-requisitos
- Tener al menos una boleta PENDING en el sistema
- Tener al menos una boleta PAID para verificar visualización
- Acceso a la interfaz web
- Acceso a la base de datos para verificaciones

---

## PARTE 1: MODAL DE CONFIRMACIÓN DE PAGO

### Test 1: Abrir Modal desde Boleta PENDING
**Objetivo:** Verificar que el modal se abre correctamente con todos los detalles

**Pasos:**
1. Navegar a **Compras → Listado de Boletas**
2. Click en el ícono 👁️ (Ver) de una boleta PENDING
3. En la sección "Registrar Pago", click en el botón **"Pagar Boleta"**

**Resultado Esperado:**
- ✅ Se abre un modal con título "Confirmar Pago de Boleta #X"
- ✅ Modal muestra:
  - Proveedor (nombre correcto)
  - Nº Boleta (número correcto)
  - Fecha Boleta (en formato DD/MM/YYYY)
  - Total a Pagar (monto correcto en rojo)
- ✅ Tabla de ítems visible con:
  - Nombre de producto
  - SKU
  - Cantidad
  - Costo unitario
  - Subtotal por línea
  - Total general al pie
- ✅ Formulario con:
  - Campo "Fecha de Pago" (prellenado con hoy)
  - Campo "Método de Pago" (Efectivo/Transferencia)
- ✅ Alert amarillo con advertencia de registro de EGRESO
- ✅ Botones: "Cancelar" y "Confirmar Pago"

---

### Test 2: Cancelar Modal
**Objetivo:** Verificar que cancelar no registra el pago

**Pasos:**
1. Abrir modal de pago (Test 1)
2. Click en botón **"Cancelar"** o botón X del modal

**Resultado Esperado:**
- ✅ Modal se cierra
- ✅ Vuelve a la vista de detalle de boleta
- ✅ Boleta sigue en estado PENDING
- ✅ No se crea entrada en `finance_ledger`
- ✅ Botón "Pagar Boleta" sigue visible

**Verificación SQL:**
```sql
SELECT COUNT(*) FROM finance_ledger 
WHERE reference_type = 'INVOICE_PAYMENT' 
  AND reference_id = <invoice_id>;
-- Debe ser 0 si es la primera vez que intentas pagar
```

---

### Test 3: Confirmar Pago con Efectivo
**Objetivo:** Verificar que el pago se registra correctamente

**Pasos:**
1. Abrir modal de pago (Test 1)
2. Dejar fecha de pago con el valor de hoy
3. Seleccionar método: **"Efectivo"**
4. Click en botón **"Confirmar Pago"**

**Resultado Esperado:**
- ✅ Modal se cierra
- ✅ Muestra flash message verde: "Boleta #X marcada como pagada (Efectivo). Egreso registrado..."
- ✅ Redirige a vista de detalle de la boleta
- ✅ Boleta ahora muestra estado "Pagada" (badge verde)
- ✅ Sección de pago reemplazada por alert verde con:
  - "Boleta Pagada"
  - Fecha de pago: DD/MM/YYYY
  - Monto
- ✅ Botón "Pagar Boleta" ya no visible

**Verificación SQL:**
```sql
-- Verificar estado de boleta
SELECT id, status, paid_at FROM purchase_invoice WHERE id = <invoice_id>;
-- Debe mostrar: status='PAID', paid_at=<fecha_seleccionada>

-- Verificar entrada en ledger
SELECT id, type, amount, payment_method, notes 
FROM finance_ledger 
WHERE reference_type = 'INVOICE_PAYMENT' 
  AND reference_id = <invoice_id>;
-- Debe mostrar: type='EXPENSE', amount=<total_boleta>, payment_method='CASH'
```

---

### Test 4: Confirmar Pago con Transferencia
**Objetivo:** Verificar método de pago TRANSFER

**Pasos:**
1. Crear/encontrar otra boleta PENDING
2. Abrir modal de pago
3. Seleccionar método: **"Transferencia"**
4. Click en "Confirmar Pago"

**Resultado Esperado:**
- ✅ Pago se registra correctamente
- ✅ Flash message: "...marcada como pagada (Transferencia)..."
- ✅ En ledger: `payment_method='TRANSFER'`

**Verificación SQL:**
```sql
SELECT payment_method FROM finance_ledger 
WHERE reference_type = 'INVOICE_PAYMENT' 
  AND reference_id = <invoice_id>;
-- Debe mostrar: 'TRANSFER'
```

---

### Test 5: Cambiar Fecha de Pago
**Objetivo:** Verificar que se puede especificar fecha de pago histórica

**Pasos:**
1. Abrir modal de pago
2. Cambiar fecha de pago a una fecha anterior (ej: hace 3 días)
3. Confirmar pago

**Resultado Esperado:**
- ✅ Pago se registra con la fecha especificada
- ✅ `paid_at` en DB = fecha seleccionada
- ✅ En detalle muestra la fecha correcta en formato DD/MM/YYYY

**Verificación SQL:**
```sql
SELECT paid_at FROM purchase_invoice WHERE id = <invoice_id>;
-- Debe ser la fecha seleccionada en el modal
```

---

### Test 6: Intentar Pagar Boleta ya PAID
**Objetivo:** Verificar que no se puede pagar dos veces

**Pasos:**
1. Navegar a detalle de una boleta ya PAID (del Test 3)
2. Verificar la interfaz

**Resultado Esperado:**
- ✅ NO se muestra el botón "Pagar Boleta"
- ✅ Se muestra alert verde "Boleta Pagada"
- ✅ No hay forma de abrir el modal de pago

---

### Test 7: Prevención de Doble Click
**Objetivo:** Verificar que no se puede procesar dos veces el mismo pago

**Pasos:**
1. Abrir modal de pago
2. Click en "Confirmar Pago"
3. Inmediatamente hacer click otra vez (rápido, doble click)

**Resultado Esperado:**
- ✅ Botón se deshabilita después del primer click
- ✅ Texto cambia a "Procesando..."
- ✅ Spinner visible
- ✅ Solo se crea UNA entrada en `finance_ledger`
- ✅ Boleta se marca PAID solo una vez

---

### Test 8: Validación de Fecha Requerida
**Objetivo:** Verificar validación del formulario

**Pasos:**
1. Abrir modal de pago
2. Borrar la fecha de pago
3. Intentar confirmar

**Resultado Esperado:**
- ✅ Validación HTML5 impide submit
- ✅ Muestra mensaje: "Por favor, rellena este campo"
- ✅ No se envía el formulario
- ✅ Modal permanece abierto

---

### Test 9: Modal con Muchos Ítems
**Objetivo:** Verificar scroll en modal con boletas grandes

**Pasos:**
1. Crear boleta con 10+ líneas de productos
2. Abrir modal de pago

**Resultado Esperado:**
- ✅ Modal es scrolleable (`modal-dialog-scrollable`)
- ✅ Todos los ítems son visibles scrolleando
- ✅ Footer con botones siempre visible (fijo al fondo)
- ✅ Tabla responsive muestra todos los datos correctamente

---

## PARTE 2: FECHAS EN FORMATO ARGENTINO

### Test 10: Listado de Boletas - Formato de Fechas
**Objetivo:** Verificar formato DD/MM/YYYY en listado

**Pasos:**
1. Navegar a **Compras → Listado de Boletas**
2. Observar columnas "Fecha" y "Vencimiento"

**Resultado Esperado:**
- ✅ Todas las fechas se muestran como DD/MM/YYYY
- ✅ Ejemplo: 12/01/2026 (no 2026-01-12)
- ✅ Si una fecha es `None`, muestra "-"

**Verificación Visual:**
```
ID | Proveedor | Nº Boleta | Fecha       | Vencimiento | Total    | Estado
1  | ACME SA   | FC-001    | 10/01/2026 | 20/01/2026  | $1000.00 | Pendiente
```

---

### Test 11: Detalle de Boleta - Formato de Fechas
**Objetivo:** Verificar formato en vista de detalle

**Pasos:**
1. Click en una boleta del listado
2. Observar sección "Información General"

**Resultado Esperado:**
- ✅ "Fecha:" muestra DD/MM/YYYY
- ✅ "Vencimiento:" muestra DD/MM/YYYY
- ✅ "Fecha de Pago:" (si está pagada) muestra DD/MM/YYYY

**Ejemplo:**
```
Proveedor: Ferretería Central
Nº Boleta: FC-2026-001
Fecha: 10/01/2026
Vencimiento: 20/01/2026
Estado: Pagada
Fecha de pago: 12/01/2026
```

---

### Test 12: Modal de Confirmación - Formato de Fechas
**Objetivo:** Verificar formato en el modal

**Pasos:**
1. Abrir modal de pago de una boleta PENDING
2. Observar "Fecha Boleta" en la información

**Resultado Esperado:**
- ✅ "Fecha Boleta:" muestra DD/MM/YYYY
- ✅ Consistente con el formato en detalle

---

### Test 13: Fechas con Valores NULL
**Objetivo:** Verificar manejo de fechas nulas

**Pasos:**
1. Crear boleta sin `due_date` (NULL)
2. Ver en listado y detalle

**Resultado Esperado:**
- ✅ En listado, columna "Vencimiento" muestra "-"
- ✅ En detalle, "Vencimiento:" muestra "-"
- ✅ No muestra "None" ni valores vacíos

---

## PARTE 3: INTEGRACIÓN COMPLETA

### Test 14: Flujo Completo End-to-End
**Objetivo:** Verificar todo el flujo funciona correctamente

**Pasos:**
1. Crear nueva boleta desde "Nueva Boleta"
2. Agregar varios ítems
3. Guardar y revisar boleta
4. Navegar al detalle
5. Click "Pagar Boleta"
6. Revisar modal (fechas, ítems, totales)
7. Seleccionar método de pago
8. Confirmar
9. Verificar estado final

**Resultado Esperado:**
- ✅ Toda la secuencia funciona sin errores
- ✅ Todas las fechas en formato DD/MM/YYYY
- ✅ Modal muestra información correcta
- ✅ Pago se registra correctamente
- ✅ Ledger entry creado
- ✅ Estado cambia a PAID

---

## QUERIES DE VERIFICACIÓN

### Ver boletas recientes con fechas
```sql
SELECT 
    id, 
    invoice_number,
    invoice_date,
    due_date,
    paid_at,
    status,
    total_amount
FROM purchase_invoice
ORDER BY id DESC
LIMIT 10;
```

### Ver pagos registrados
```sql
SELECT 
    fl.id,
    fl.datetime,
    fl.type,
    fl.amount,
    fl.payment_method,
    fl.notes,
    pi.invoice_number,
    s.name as supplier_name
FROM finance_ledger fl
JOIN purchase_invoice pi ON fl.reference_id = pi.id
JOIN supplier s ON pi.supplier_id = s.id
WHERE fl.reference_type = 'INVOICE_PAYMENT'
ORDER BY fl.id DESC
LIMIT 10;
```

### Verificar consistencia de pagos
```sql
-- Todas las boletas PAID deben tener fecha de pago
SELECT id, invoice_number, status, paid_at 
FROM purchase_invoice 
WHERE status = 'PAID' AND paid_at IS NULL;
-- Debe retornar 0 filas

-- Todas las boletas PAID deben tener entrada en ledger
SELECT pi.id, pi.invoice_number
FROM purchase_invoice pi
LEFT JOIN finance_ledger fl ON fl.reference_id = pi.id AND fl.reference_type = 'INVOICE_PAYMENT'
WHERE pi.status = 'PAID' AND fl.id IS NULL;
-- Debe retornar 0 filas
```

---

## CRITERIOS DE ÉXITO

### Modal de Confirmación
- ✅ Modal se abre correctamente desde detalle de boleta PENDING
- ✅ Muestra todos los datos: proveedor, número, fecha, ítems, total
- ✅ Tabla de ítems completa con cantidades y costos
- ✅ Formulario permite seleccionar fecha y método de pago
- ✅ Botón "Cancelar" cierra sin registrar
- ✅ Botón "Confirmar" ejecuta el pago correctamente
- ✅ Se previene doble click/doble procesamiento
- ✅ Validaciones de formulario funcionan
- ✅ Después del pago, redirige y muestra confirmación

### Fechas Argentinas
- ✅ Listado muestra fechas en DD/MM/YYYY
- ✅ Detalle muestra fechas en DD/MM/YYYY
- ✅ Modal muestra fechas en DD/MM/YYYY
- ✅ Fechas NULL muestran "-"
- ✅ Consistencia en todo el módulo de boletas

### Integración
- ✅ No se rompieron funcionalidades existentes
- ✅ Pago de boletas funciona end-to-end
- ✅ Ledger entries se crean correctamente
- ✅ Estado PENDING → PAID funciona
- ✅ Flash messages apropiados
- ✅ No hay errores en consola del navegador

---

## ARCHIVOS MODIFICADOS

1. **`app/blueprints/invoices.py`**
   - Agregado endpoint `GET /invoices/<id>/pay/preview`
   - Endpoint existente `POST /invoices/<id>/pay` sin cambios

2. **`app/templates/invoices/_pay_confirm_modal.html`** (NUEVO)
   - Modal Bootstrap completo
   - Tabla de ítems
   - Formulario de pago
   - JavaScript para auto-open

3. **`app/templates/invoices/detail.html`**
   - Reemplazado formulario inline por botón con HTMX
   - Agregado contenedor `#invoice-modal-container`
   - Eliminado JavaScript de confirmación inline
   - Fechas ya en formato argentino (MEJORA 7)

4. **`app/templates/invoices/list.html`**
   - Fechas ya en formato argentino (MEJORA 7)

5. **Filtros de fecha** (ya existentes desde MEJORA 7)
   - `app/utils/formatters.py` con `date_ar`, `datetime_ar`
   - Registrados en `app/__init__.py`

---

## ROLLBACK (si es necesario)

Si surge algún problema, restaurar versiones anteriores:

```bash
git checkout HEAD~1 -- app/blueprints/invoices.py
git checkout HEAD~1 -- app/templates/invoices/detail.html
rm app/templates/invoices/_pay_confirm_modal.html
docker compose up --build -d web
```

---

## NOTAS ADICIONALES

### UX Mejorado
- ✅ Usuario revisa todos los detalles antes de confirmar pago
- ✅ Menor probabilidad de errores (pago por equivocación)
- ✅ Transparencia total del impacto financiero
- ✅ Experiencia consistente con modal de ventas (MEJORA 17)

### Fechas Consistentes
- ✅ Todo el módulo de boletas usa formato local argentino
- ✅ Más fácil de leer para usuarios argentinos
- ✅ Alineado con MEJORA 7 (fechas en balance y ventas)
