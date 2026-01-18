# MEJORA B: Pagos Parciales de Boletas - Testing

## Objetivo
Verificar que se pueden registrar múltiples pagos parciales (adelantos) para una boleta de compra, que el saldo se calcula correctamente, y que el estado se actualiza automáticamente cuando el saldo llega a cero.

---

## Preparación

### 1. Aplicar Migración SQL

**OBLIGATORIO:** Ejecutar la migración antes de probar:

```bash
psql -U usuario -d ferreteria_db -f db/migrations/MEJORA_B_pagos_parciales.sql
```

### 2. Verificar Migración

```sql
-- Verificar que la tabla existe
\d purchase_invoice_payment

-- Verificar índices
\di purchase_invoice_payment*

-- Verificar que se migraron pagos existentes (si había boletas PAID)
SELECT COUNT(*) FROM purchase_invoice_payment;
```

---

## Casos de Prueba

### 1. Crear boleta de prueba

**Preparación:**
- Crear una boleta nueva con total $10,000
- Proveedor: cualquiera
- Fecha: hoy
- Vencimiento: en 30 días
- 2-3 ítems

**Resultado esperado:**
- ✅ Boleta creada exitosamente
- ✅ Status: PENDING
- ✅ Total: $10,000
- ✅ Pagado: $0
- ✅ Saldo: $10,000

---

### 2. Registrar primer pago parcial (adelanto)

**Pasos:**
1. Ir a detalle de la boleta `/invoices/<id>`
2. En sección "Registrar Pago":
   - Fecha: hoy
   - Monto: **$3,000**
   - Método: Efectivo
   - Notas: "Adelanto 1"
3. Click "Registrar Pago"

**Resultado esperado:**
- ✅ Flash message: "Pago de $3,000 registrado exitosamente. Saldo pendiente: $7,000"
- ✅ En card "Balance":
  - Total: $10,000
  - Pagado: $3,000 (verde)
  - Saldo: $7,000 (rojo)
- ✅ En "Historial de Pagos":
  - 1 fila con fecha, monto $3,000, notas "Adelanto 1"
- ✅ Status de boleta: PENDING
- ✅ En listado de boletas:
  - Columna "Pagado": $3,000
  - Columna "Saldo": $7,000

**Verificación DB:**
```sql
-- Ver pago registrado
SELECT * FROM purchase_invoice_payment WHERE invoice_id = <INVOICE_ID>;
-- Debe mostrar 1 fila con amount = 3000

-- Ver asiento en ledger
SELECT * FROM finance_ledger 
WHERE reference_type = 'INVOICE_PAYMENT' 
  AND reference_id = <INVOICE_ID>
ORDER BY id DESC LIMIT 1;
-- Debe mostrar: type = 'EXPENSE', amount = 3000
```

---

### 3. Registrar segundo pago parcial

**Pasos:**
1. En la misma boleta, registrar otro pago:
   - Fecha: hoy + 1 día
   - Monto: **$4,500**
   - Método: Transferencia
   - Notas: "Adelanto 2"
2. Click "Registrar Pago"

**Resultado esperado:**
- ✅ Flash message: "Pago de $4,500 registrado exitosamente. Saldo pendiente: $2,500"
- ✅ En card "Balance":
  - Total: $10,000
  - Pagado: $7,500
  - Saldo: $2,500
- ✅ En "Historial de Pagos":
  - 2 filas (ordenadas por fecha)
  - Total Pagado: $7,500
- ✅ Status: PENDING (aún hay saldo)

**Verificación DB:**
```sql
-- Ver pagos
SELECT paid_at, amount, notes 
FROM purchase_invoice_payment 
WHERE invoice_id = <INVOICE_ID>
ORDER BY paid_at;
-- Debe mostrar 2 filas

-- Ver asientos en ledger
SELECT date, amount, notes 
FROM finance_ledger 
WHERE reference_type = 'INVOICE_PAYMENT' 
  AND reference_id = <INVOICE_ID>
ORDER BY date;
-- Debe mostrar 2 asientos EXPENSE (3000 y 4500)
```

---

### 4. Pago final (completar boleta)

**Pasos:**
1. Registrar pago final:
   - Fecha: hoy + 2 días
   - Monto: **$2,500** (el saldo exacto)
   - Método: Efectivo
   - Notas: "Pago final"
2. Click "Registrar Pago"

**Resultado esperado:**
- ✅ Flash message: "Pago de $2,500 registrado exitosamente. Boleta pagada completamente."
- ✅ En card "Balance":
  - Total: $10,000
  - Pagado: $10,000
  - Saldo: $0 (verde)
  - Badge verde: "Boleta pagada completamente"
- ✅ Status: **PAID** (cambió automáticamente)
- ✅ `invoice.paid_at` = fecha del último pago
- ✅ Formulario "Registrar Pago" ya NO visible
- ✅ Mensaje: "Boleta Pagada Completamente"
- ✅ En listado:
  - Badge verde "Pagada"
  - Saldo: $0

**Verificación DB:**
```sql
-- Ver status actualizado
SELECT id, status, paid_at, total_amount 
FROM purchase_invoice 
WHERE id = <INVOICE_ID>;
-- Debe mostrar: status = 'PAID', paid_at = fecha último pago

-- Ver todos los pagos
SELECT SUM(amount) AS total_paid 
FROM purchase_invoice_payment 
WHERE invoice_id = <INVOICE_ID>;
-- Debe ser: 10000

-- Ver todos los asientos
SELECT SUM(amount) AS total_expense 
FROM finance_ledger 
WHERE reference_type = 'INVOICE_PAYMENT' 
  AND reference_id = <INVOICE_ID>;
-- Debe ser: 10000
```

---

### 5. Validación: No permitir sobrepago

**Preparación:**
- Crear nueva boleta con total $5,000
- Registrar pago de $3,000 (saldo: $2,000)

**Pasos:**
1. Intentar registrar pago de **$3,000** (más que el saldo)
2. Click "Registrar Pago"

**Resultado esperado:**
- ❌ Flash message error: "El monto del pago ($3,000) excede el saldo pendiente ($2,000). Total boleta: $5,000, Ya pagado: $3,000"
- ✅ Pago NO registrado
- ✅ Saldo sigue siendo $2,000

---

### 6. Validación: Monto debe ser mayor a 0

**Pasos:**
1. Intentar registrar pago con monto **$0** o negativo
2. Click "Registrar Pago"

**Resultado esperado:**
- ❌ Error de validación (HTML5 o backend)
- ✅ Pago NO registrado

---

### 7. Validación: Fecha obligatoria

**Pasos:**
1. Dejar fecha vacía
2. Intentar registrar pago

**Resultado esperado:**
- ❌ Error: "La fecha de pago es obligatoria"
- ✅ Pago NO registrado

---

### 8. Cambiar fecha de vencimiento

**Preparación:**
- Boleta con vencimiento en 30 días

**Pasos:**
1. En sección "Vencimiento", cambiar fecha a: hoy + 60 días
2. Click "Actualizar Vencimiento"

**Resultado esperado:**
- ✅ Flash message: "Fecha de vencimiento actualizada a DD/MM/YYYY"
- ✅ `invoice.due_date` actualizado
- ✅ NO se creó ningún registro en `finance_ledger` (solo cambió vencimiento)
- ✅ Pagos NO afectados

**Verificación DB:**
```sql
SELECT due_date FROM purchase_invoice WHERE id = <INVOICE_ID>;
-- Debe mostrar la nueva fecha
```

---

### 9. Quitar fecha de vencimiento

**Pasos:**
1. En sección "Vencimiento", borrar la fecha (dejar vacío)
2. Click "Actualizar Vencimiento"

**Resultado esperado:**
- ✅ Flash message: "Fecha de vencimiento eliminada"
- ✅ `invoice.due_date` = NULL
- ✅ En listado: columna "Vencimiento" muestra "-"

---

### 10. Validación: Vencimiento no puede ser anterior a fecha boleta

**Preparación:**
- Boleta con fecha: 01/01/2026

**Pasos:**
1. Intentar setear vencimiento a: 31/12/2025 (anterior)
2. Click "Actualizar Vencimiento"

**Resultado esperado:**
- ❌ Flash message warning: "La fecha de vencimiento no puede ser anterior a la fecha de la boleta"
- ✅ Vencimiento NO cambia

---

### 11. Historial de pagos ordenado por fecha

**Preparación:**
- Boleta con 3 pagos en fechas distintas:
  - Pago 1: 01/01/2026 - $1,000
  - Pago 2: 05/01/2026 - $2,000
  - Pago 3: 03/01/2026 - $1,500

**Resultado esperado:**
- ✅ En "Historial de Pagos", los pagos aparecen ordenados por fecha:
  1. 01/01/2026 - $1,000
  2. 03/01/2026 - $1,500
  3. 05/01/2026 - $2,000
- ✅ Total Pagado: $4,500

---

### 12. Listado de boletas muestra saldo correcto

**Preparación:**
- 3 boletas:
  - Boleta A: Total $10,000, Pagado $0, Saldo $10,000, Status PENDING
  - Boleta B: Total $5,000, Pagado $3,000, Saldo $2,000, Status PENDING
  - Boleta C: Total $8,000, Pagado $8,000, Saldo $0, Status PAID

**Pasos:**
1. Ir a `/invoices`

**Resultado esperado:**
- ✅ Tabla muestra:
  - Boleta A: Total $10,000 | Pagado $0 | Saldo $10,000 | Badge "Pendiente"
  - Boleta B: Total $5,000 | Pagado $3,000 | Saldo $2,000 | Badge "Pendiente"
  - Boleta C: Total $8,000 | Pagado $8,000 | Saldo $0 | Badge "Pagada"

---

### 13. Editar boleta NO afecta pagos

**Preparación:**
- Boleta con total $10,000
- 2 pagos: $3,000 y $4,000 (total pagado: $7,000)

**Pasos:**
1. Editar la boleta: cambiar cantidad de un ítem
2. Nuevo total: $12,000
3. Guardar cambios

**Resultado esperado:**
- ✅ Boleta actualizada con nuevo total $12,000
- ✅ Pagos NO se eliminan ni modifican
- ✅ Total Pagado: $7,000 (sin cambios)
- ✅ Nuevo Saldo: $5,000 ($12,000 - $7,000)
- ✅ Status: PENDING (porque hay saldo)

---

### 14. Eliminar boleta elimina pagos en cascade

**Preparación:**
- Boleta PENDING con 2 pagos

**Pasos:**
1. Eliminar la boleta

**Resultado esperado:**
- ✅ Boleta eliminada
- ✅ Pagos también eliminados (CASCADE)
- ✅ Stock revertido
- ✅ Asientos de ledger NO se eliminan (mantener historial financiero)

**Verificación DB:**
```sql
-- Verificar que los pagos fueron eliminados
SELECT * FROM purchase_invoice_payment WHERE invoice_id = <DELETED_ID>;
-- Debe retornar 0 filas
```

---

### 15. Migración de boletas existentes

**Preparación:**
- Antes de migración: 5 boletas PAID

**Pasos:**
1. Ejecutar migración
2. Verificar que se crearon pagos automáticos

**Resultado esperado:**
- ✅ Para cada boleta PAID, se creó 1 registro en `purchase_invoice_payment`
- ✅ Monto del pago = `total_amount` de la boleta
- ✅ Fecha del pago = `paid_at` o `invoice_date`
- ✅ Notas: "Pago migrado desde sistema anterior"

**Verificación DB:**
```sql
-- Ver pagos migrados
SELECT pip.*, pi.invoice_number, pi.total_amount
FROM purchase_invoice_payment pip
JOIN purchase_invoice pi ON pi.id = pip.invoice_id
WHERE pip.notes LIKE '%migrado%'
ORDER BY pip.created_at;
```

---

## Queries de Verificación Final

### Balance correcto para todas las boletas

```sql
SELECT 
    pi.id,
    pi.invoice_number,
    pi.total_amount,
    COALESCE(SUM(pip.amount), 0) AS total_paid,
    pi.total_amount - COALESCE(SUM(pip.amount), 0) AS balance,
    pi.status
FROM purchase_invoice pi
LEFT JOIN purchase_invoice_payment pip ON pip.invoice_id = pi.id
GROUP BY pi.id, pi.invoice_number, pi.total_amount, pi.status
ORDER BY pi.id DESC;
```

**Resultado esperado:**
- ✅ Para boletas PAID: `balance = 0`
- ✅ Para boletas PENDING: `balance > 0` o `balance = total_amount` (sin pagos)

### Consistencia ledger vs payments

```sql
-- Comparar suma de pagos vs suma de asientos EXPENSE
SELECT 
    pip.invoice_id,
    SUM(pip.amount) AS total_payments,
    (SELECT SUM(fl.amount) 
     FROM finance_ledger fl 
     WHERE fl.reference_type = 'INVOICE_PAYMENT' 
       AND fl.reference_id = pip.invoice_id) AS total_ledger
FROM purchase_invoice_payment pip
GROUP BY pip.invoice_id
HAVING SUM(pip.amount) != (SELECT SUM(fl.amount) 
                            FROM finance_ledger fl 
                            WHERE fl.reference_type = 'INVOICE_PAYMENT' 
                              AND fl.reference_id = pip.invoice_id);
```

**Resultado esperado:**
- ✅ Debe retornar 0 filas (todos los pagos tienen su asiento correspondiente)

---

## Checklist Final

- [ ] Migración SQL aplicada correctamente
- [ ] Tabla `purchase_invoice_payment` creada
- [ ] Relación `invoice.payments` funciona
- [ ] Registrar pago parcial actualiza balance
- [ ] Múltiples pagos parciales funcionan
- [ ] Pago final cambia status a PAID
- [ ] No se permite sobrepago
- [ ] Validaciones funcionan (monto > 0, fecha obligatoria)
- [ ] Cambiar vencimiento funciona sin afectar pagos
- [ ] Historial de pagos se muestra ordenado
- [ ] Listado muestra columnas Pagado y Saldo
- [ ] Cada pago crea 1 asiento EXPENSE en ledger
- [ ] Editar boleta NO elimina pagos
- [ ] Eliminar boleta elimina pagos (CASCADE)
- [ ] Migración de boletas PAID funcionó

---

## Notas Importantes

1. **Un pago = Un asiento:** Cada pago parcial genera exactamente 1 asiento EXPENSE en `finance_ledger`. NO se crea un asiento por el total al primer pago.

2. **Status automático:** El status PENDING/PAID se actualiza automáticamente basado en el saldo. NO es necesario cambiar manualmente.

3. **Vencimiento independiente:** Cambiar el vencimiento NO afecta los pagos ni el ledger. Es solo informativo.

4. **Cascade delete:** Al eliminar una boleta, los pagos se eliminan automáticamente (ON DELETE CASCADE).

5. **Balance en tiempo real:** El balance siempre se calcula en tiempo real: `total_amount - SUM(payments)`.

---

## Fin del Testing
