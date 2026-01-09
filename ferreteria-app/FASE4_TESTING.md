# FASE 4 - Testing: Pago de Boletas

## Objetivo
Verificar que el módulo de pago de boletas funciona correctamente:
- Marcar boleta como PAID
- Guardar fecha de pago (paid_at)
- Registrar egreso en finance_ledger
- Validaciones de negocio
- Transaccionalidad

---

## Pre-requisitos

1. **Base de datos PostgreSQL corriendo:**
```bash
cd c:\jere\Ferreteria\Ferreteria-db
docker-compose up -d
```

2. **Aplicación Flask corriendo:**
```bash
cd c:\jere\Ferreteria\ferreteria-app
python app.py
```

3. **Datos de prueba:**
   - Al menos 1 proveedor creado
   - Al menos 2-3 boletas creadas (Fase 3)
   - Algunas boletas en estado PENDING

4. **Acceder a la aplicación:**
   - URL: http://127.0.0.1:5000

---

## Caso 1: Pagar Boleta PENDING (Caso Normal)

### Pre-condición:
- Tener al menos 1 boleta en estado PENDING
- Anotar su ID y total_amount

### Verificación previa en DB:
```sql
SELECT 
    id, 
    invoice_number, 
    total_amount, 
    status, 
    paid_at 
FROM purchase_invoice 
WHERE status = 'PENDING' 
ORDER BY id DESC 
LIMIT 1;
```

**Anotar:**
- Invoice ID: ___
- Total Amount: ___
- Status: PENDING
- paid_at: NULL

### Pasos:
1. Navegar a: **Compras → Boletas**
2. Localizar una boleta con estado **Pendiente**
3. Click en **"Ver detalle"** (ícono ojo)
4. En la sección **"Registrar Pago"**:
   - Verificar que aparece el formulario amarillo
   - Fecha de pago está pre-llenada con hoy
   - Cambiar a una fecha válida (ej: hoy o ayer)
5. Click en **"Marcar como Pagada"**
6. Confirmar en el diálogo

### Resultado esperado:
- ✅ Mensaje: "Boleta #X marcada como pagada exitosamente. Egreso registrado en el libro mayor."
- ✅ Redirige a detalle de boleta
- ✅ Estado ahora muestra **"Pagada"** (badge verde)
- ✅ Aparece alert verde con:
  - "Boleta Pagada"
  - Fecha de pago mostrada
  - Monto mostrado
  - Mensaje sobre egreso registrado
- ✅ El formulario de pago ya NO aparece

### Verificación en DB:

**1. Invoice actualizada:**
```sql
SELECT 
    id, 
    invoice_number, 
    total_amount, 
    status, 
    paid_at 
FROM purchase_invoice 
WHERE id = <invoice_id>;

-- status debe ser 'PAID'
-- paid_at debe tener la fecha ingresada (no NULL)
```

**2. Registro de egreso en finance_ledger:**
```sql
SELECT 
    id,
    datetime,
    type,
    amount,
    reference_type,
    reference_id,
    notes
FROM finance_ledger 
WHERE reference_type = 'INVOICE_PAYMENT' 
  AND reference_id = <invoice_id>
ORDER BY id DESC;

-- Debe existir exactamente 1 registro
-- type debe ser 'EXPENSE'
-- amount debe ser igual a invoice.total_amount
-- reference_id debe ser igual a invoice.id
-- notes debe contener "Pago boleta #..." y nombre del proveedor
```

**3. Verificar totales:**
```sql
SELECT 
    pi.total_amount as invoice_amount,
    fl.amount as ledger_amount
FROM purchase_invoice pi
JOIN finance_ledger fl ON fl.reference_id = pi.id 
    AND fl.reference_type = 'INVOICE_PAYMENT'
WHERE pi.id = <invoice_id>;

-- invoice_amount debe ser IGUAL a ledger_amount
```

---

## Caso 2: Intentar Pagar Boleta Ya PAID (Error Esperado)

### Pre-condición:
- Tener una boleta ya pagada (del Caso 1)

### Pasos:
1. Navegar a detalle de una boleta **Pagada**
2. Verificar que NO aparece el formulario de pago
3. Solo aparece el alert verde de "Boleta Pagada"

### Resultado esperado:
- ✅ NO hay formulario de pago
- ✅ Solo se muestra información de pago realizado

### Intentar pagar directamente (POST manual - opcional):
Si se intenta hacer POST directamente a `/invoices/<id>/pay`:

```bash
# Desde terminal o herramienta HTTP
curl -X POST http://127.0.0.1:5000/invoices/<id>/pay \
  -d "paid_at=2026-01-09" \
  --cookie "session=..."
```

### Resultado esperado:
- ❌ Error: "La boleta ya está PAID. Solo se pueden pagar boletas PENDING."
- ✅ NO se duplica el registro en finance_ledger

### Verificación en DB:
```sql
SELECT COUNT(*) as num_ledger_entries
FROM finance_ledger 
WHERE reference_type = 'INVOICE_PAYMENT' 
  AND reference_id = <invoice_id>;

-- Debe ser 1 (no duplicado)
```

---

## Caso 3: Fecha de Pago Inválida (Error de Validación)

### Pasos:
1. Navegar a detalle de una boleta **PENDING**
2. En el formulario de pago:
   - Dejar el campo **Fecha de pago** vacío
3. Click en **"Marcar como Pagada"**

### Resultado esperado:
- ❌ Error de validación HTML5: "Por favor, rellene este campo"
- ✅ No se procesa el pago

### Alternativa (si se deshabilita validación HTML5):
Si se envía sin fecha o con formato inválido:

### Resultado esperado:
- ❌ Error: "La fecha de pago es requerida" o "Formato de fecha inválido"
- ✅ No se actualiza invoice
- ✅ No se crea ledger entry

---

## Caso 4: Verificar Transaccionalidad (Rollback si Falla)

### Concepto:
Si algo falla durante el proceso de pago (ej: error al insertar en finance_ledger), la boleta NO debe quedar marcada como PAID.

### Simulación (requiere modificar temporalmente el código):
**Opción 1: Desconectar DB justo antes de insertar ledger**
- Esto es difícil de simular en testing manual

**Opción 2: Verificar mediante logs**
- Si ocurre un error, debe haber rollback

### Verificación defensiva:
Ejecutar query para verificar consistencia:

```sql
SELECT 
    pi.id as invoice_id,
    pi.status,
    pi.paid_at,
    COUNT(fl.id) as ledger_count
FROM purchase_invoice pi
LEFT JOIN finance_ledger fl ON fl.reference_id = pi.id 
    AND fl.reference_type = 'INVOICE_PAYMENT'
GROUP BY pi.id, pi.status, pi.paid_at
HAVING (pi.status = 'PAID' AND COUNT(fl.id) = 0)
    OR (pi.status = 'PENDING' AND COUNT(fl.id) > 0);

-- Este query NO debe retornar ninguna fila
-- Si retorna filas, hay inconsistencia:
--   - Boleta PAID sin ledger entry
--   - Boleta PENDING con ledger entry
```

---

## Caso 5: Filtro "Solo Pendientes" en Listado

### Pasos:
1. Navegar a: **Compras → Boletas**
2. Click en botón **"Solo Pendientes"**

### Resultado esperado:
- ✅ URL cambia a `/invoices?status=PENDING`
- ✅ Solo se muestran boletas con estado **Pendiente**
- ✅ Boletas pagadas NO aparecen
- ✅ El botón "Solo Pendientes" aparece activo (resaltado)

### Verificación en DB:
```sql
SELECT COUNT(*) FROM purchase_invoice WHERE status = 'PENDING';
-- Debe coincidir con el número de boletas mostradas en la UI
```

---

## Caso 6: Botón "Pagar" Rápido desde Listado

### Pasos:
1. Navegar a: **Compras → Boletas**
2. Verificar que las boletas PENDING tienen:
   - ✅ Botón **"Ver"** (ícono ojo)
   - ✅ Botón **"Pagar"** (ícono tarjeta, amarillo)
3. Click en botón **"Pagar"** de una boleta PENDING

### Resultado esperado:
- ✅ Redirige a detalle de boleta
- ✅ El ancla `#pago` lleva al formulario de pago (si el navegador soporta scroll)

---

## Caso 7: Boletas Pagadas NO Tienen Botón "Pagar"

### Pasos:
1. Navegar a: **Compras → Boletas**
2. Localizar boletas con estado **Pagada**

### Resultado esperado:
- ✅ Solo tienen botón **"Ver"** (ícono ojo)
- ✅ NO tienen botón **"Pagar"**

---

## Caso 8: Verificar Nota (notes) en finance_ledger

### Pasos:
1. Pagar una boleta (cualquier caso normal)
2. Anotar el invoice_id y invoice_number

### Verificación en DB:
```sql
SELECT 
    fl.notes,
    pi.invoice_number,
    s.name as supplier_name
FROM finance_ledger fl
JOIN purchase_invoice pi ON fl.reference_id = pi.id
JOIN supplier s ON pi.supplier_id = s.id
WHERE fl.reference_type = 'INVOICE_PAYMENT' 
  AND fl.reference_id = <invoice_id>;

-- notes debe contener:
--   "Pago boleta #<invoice_number> - <supplier_name>"
```

### Resultado esperado:
- ✅ El campo `notes` tiene información descriptiva
- ✅ Incluye número de boleta y nombre del proveedor

---

## Caso 9: Múltiples Boletas - Pagar en Secuencia

### Pasos:
1. Crear 3 boletas PENDING (desde Fase 3)
2. Pagar la primera
3. Verificar en DB que tiene 1 ledger entry
4. Pagar la segunda
5. Verificar en DB que tiene 1 ledger entry
6. Pagar la tercera
7. Verificar en DB que tiene 1 ledger entry

### Resultado esperado:
- ✅ Cada boleta pagada tiene exactamente 1 entrada en finance_ledger
- ✅ Cada entrada tiene el reference_id correcto
- ✅ La suma de amounts en ledger coincide con la suma de total_amounts de las boletas pagadas

### Verificación en DB:
```sql
SELECT 
    pi.id,
    pi.invoice_number,
    pi.total_amount,
    pi.status,
    fl.id as ledger_id,
    fl.amount as ledger_amount
FROM purchase_invoice pi
LEFT JOIN finance_ledger fl ON fl.reference_id = pi.id 
    AND fl.reference_type = 'INVOICE_PAYMENT'
ORDER BY pi.id;

-- Todas las boletas PAID deben tener ledger_id NOT NULL
-- Todas las boletas PENDING deben tener ledger_id NULL
```

---

## Caso 10: Concurrencia Simple (Lock FOR UPDATE)

### Concepto:
El servicio `pay_invoice` usa `SELECT ... FOR UPDATE` para evitar que dos usuarios paguen la misma boleta simultáneamente.

### Simulación (requiere 2 navegadores/sesiones):
**Difícil de simular manualmente**, pero el código está preparado con lock.

### Verificación del lock en código:
Revisar en `app/services/payment_service.py`:

```python
invoice = (
    session.query(PurchaseInvoice)
    .filter(PurchaseInvoice.id == invoice_id)
    .with_for_update()  # <-- Lock para prevenir concurrencia
    .first()
)
```

### Verificación teórica:
- ✅ Si dos usuarios intentan pagar la misma boleta al mismo tiempo:
  1. El primero adquiere el lock
  2. El segundo espera hasta que el primero termine
  3. Cuando el segundo intenta, la boleta ya está PAID
  4. El segundo recibe error: "La boleta ya está PAID"
  5. NO se duplica el ledger entry

---

## Resumen de Verificaciones Críticas

### ✅ Checklist Final:

- [ ] Pagar boleta PENDING → cambia a PAID, paid_at seteado
- [ ] Se crea registro EXPENSE en finance_ledger con monto correcto
- [ ] Intentar pagar boleta ya PAID → error, no duplica ledger
- [ ] Fecha de pago requerida → validación funciona
- [ ] Filtro "Solo Pendientes" funciona
- [ ] Botón "Pagar" solo aparece en boletas PENDING
- [ ] Formulario de pago solo aparece en detalle de boletas PENDING
- [ ] Boletas pagadas muestran alert verde con info de pago
- [ ] Campo `notes` en ledger tiene información descriptiva
- [ ] Transaccionalidad: si falla algo, rollback completo
- [ ] Lock FOR UPDATE previene doble pago concurrente
- [ ] Consistencia: todas las boletas PAID tienen 1 ledger entry
- [ ] Consistencia: ninguna boleta PENDING tiene ledger entry

---

## Queries Útiles para Debugging

### Ver todas las boletas con su estado de pago:
```sql
SELECT 
    pi.id,
    pi.invoice_number,
    s.name as proveedor,
    pi.total_amount,
    pi.status,
    pi.paid_at,
    fl.id as ledger_id,
    fl.amount as ledger_amount
FROM purchase_invoice pi
JOIN supplier s ON pi.supplier_id = s.id
LEFT JOIN finance_ledger fl ON fl.reference_id = pi.id 
    AND fl.reference_type = 'INVOICE_PAYMENT'
ORDER BY pi.created_at DESC;
```

### Ver todos los egresos registrados:
```sql
SELECT 
    fl.id,
    fl.datetime,
    fl.amount,
    fl.reference_type,
    fl.reference_id,
    fl.notes
FROM finance_ledger 
WHERE type = 'EXPENSE'
ORDER BY datetime DESC;
```

### Ver solo egresos de pagos de boletas:
```sql
SELECT 
    fl.id,
    fl.datetime,
    fl.amount,
    pi.invoice_number,
    s.name as proveedor
FROM finance_ledger fl
JOIN purchase_invoice pi ON fl.reference_id = pi.id
JOIN supplier s ON pi.supplier_id = s.id
WHERE fl.type = 'EXPENSE' 
  AND fl.reference_type = 'INVOICE_PAYMENT'
ORDER BY fl.datetime DESC;
```

### Verificar consistencia (NO debe retornar filas):
```sql
-- Boletas PAID sin ledger entry (INCONSISTENCIA)
SELECT 
    pi.id,
    pi.invoice_number,
    pi.status,
    COUNT(fl.id) as ledger_count
FROM purchase_invoice pi
LEFT JOIN finance_ledger fl ON fl.reference_id = pi.id 
    AND fl.reference_type = 'INVOICE_PAYMENT'
WHERE pi.status = 'PAID'
GROUP BY pi.id, pi.invoice_number, pi.status
HAVING COUNT(fl.id) = 0;

-- Boletas PENDING con ledger entry (INCONSISTENCIA)
SELECT 
    pi.id,
    pi.invoice_number,
    pi.status,
    COUNT(fl.id) as ledger_count
FROM purchase_invoice pi
LEFT JOIN finance_ledger fl ON fl.reference_id = pi.id 
    AND fl.reference_type = 'INVOICE_PAYMENT'
WHERE pi.status = 'PENDING'
GROUP BY pi.id, pi.invoice_number, pi.status
HAVING COUNT(fl.id) > 0;
```

### Ver balance de egresos vs ingresos:
```sql
SELECT 
    type,
    COUNT(*) as num_entries,
    SUM(amount) as total_amount
FROM finance_ledger
GROUP BY type;

-- type='INCOME' → ingresos de ventas
-- type='EXPENSE' → egresos de pagos de boletas (y otros)
```

### Ver detalle de un pago específico:
```sql
SELECT 
    pi.id as invoice_id,
    pi.invoice_number,
    pi.invoice_date,
    pi.paid_at,
    pi.total_amount as invoice_amount,
    pi.status,
    s.name as proveedor,
    fl.id as ledger_id,
    fl.datetime as ledger_datetime,
    fl.amount as ledger_amount,
    fl.notes
FROM purchase_invoice pi
JOIN supplier s ON pi.supplier_id = s.id
LEFT JOIN finance_ledger fl ON fl.reference_id = pi.id 
    AND fl.reference_type = 'INVOICE_PAYMENT'
WHERE pi.id = <invoice_id>;
```

---

## Notas Importantes

1. **Stock NO cambia al pagar:** El stock ya se actualizó al crear la boleta en Fase 3. El pago solo cambia el estado y registra el egreso financiero.

2. **Transaccionalidad:** El servicio `pay_invoice` ejecuta todo en una transacción. Si falla el insert en `finance_ledger`, el update de `purchase_invoice` también hace rollback.

3. **Lock FOR UPDATE:** Previene condiciones de carrera (race conditions) donde dos usuarios podrían intentar pagar la misma boleta simultáneamente.

4. **Validación defensiva:** El servicio valida que la boleta tenga líneas y total_amount válido, aunque esto ya se validó al crear la boleta.

5. **Fecha de pago:** Solo se guarda la fecha, no la hora. El campo `paid_at` es de tipo `date`.

6. **finance_ledger.datetime:** Guarda fecha y hora actual del sistema (`datetime.now()`), no la fecha ingresada por el usuario.

---

## ¿Qué sigue? → FASE 5

En la Fase 5 se implementará:
- **Balance financiero:** Pantalla con ingresos/egresos y neto
- **Tabs:** Diario, Mensual, Anual
- **Consultas eficientes:** `date_trunc` para agrupar por período
- **Opcional:** Movimientos manuales en finance_ledger

