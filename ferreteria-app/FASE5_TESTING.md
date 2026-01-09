# FASE 5 - Testing: Balance Financiero

## Objetivo
Verificar que el módulo de balance financiero funciona correctamente:
- Balance diario, mensual y anual
- Cálculo correcto de ingresos, egresos y neto
- Filtros por rango de fechas
- Libro mayor (ledger) para auditoría
- Movimientos manuales

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
   - Al menos 1-2 ventas confirmadas (generan INCOME)
   - Al menos 1-2 boletas pagadas (generan EXPENSE)
   - Datos distribuidos en diferentes días/meses (ideal)

4. **Acceder a la aplicación:**
   - URL: http://127.0.0.1:5000

---

## Caso 1: Ver Balance Mensual (Vista por Defecto)

### Pasos:
1. Navegar a: **Balance** (menú superior)

### Resultado esperado:
- ✅ Se abre vista de Balance con tab "Mensual" activo
- ✅ Muestra 3 tarjetas de resumen:
  - Ingresos Totales (verde)
  - Egresos Totales (rojo)
  - Neto (azul o amarillo según signo)
- ✅ Tabla con columnas:
  - Período (YYYY-MM)
  - Ingresos
  - Egresos
  - Neto
- ✅ Fila de TOTALES al final coincide con las tarjetas
- ✅ Filtros muestran fechas por defecto (últimos 12 meses)

### Verificación en DB:
```sql
SELECT 
    date_trunc('month', datetime) AS period,
    SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END) AS income,
    SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) AS expense
FROM finance_ledger
WHERE datetime >= NOW() - INTERVAL '12 months'
GROUP BY 1
ORDER BY 1;
```

**Comparar con UI:**
- Los montos por período deben coincidir
- Los totales deben coincidir

---

## Caso 2: Balance Diario (Últimos 30 Días)

### Pasos:
1. En Balance, click en tab **"Diario"**

### Resultado esperado:
- ✅ URL cambia a `/balance?view=daily`
- ✅ Tab "Diario" está activo
- ✅ Tabla muestra períodos en formato YYYY-MM-DD
- ✅ Filtros muestran últimos 30 días
- ✅ Ingresos, egresos y neto correctos por día

### Verificación en DB:
```sql
SELECT 
    date_trunc('day', datetime) AS period,
    SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END) AS income,
    SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) AS expense
FROM finance_ledger
WHERE datetime >= NOW() - INTERVAL '30 days'
GROUP BY 1
ORDER BY 1;
```

---

## Caso 3: Balance Anual (Últimos 5 Años)

### Pasos:
1. En Balance, click en tab **"Anual"**

### Resultado esperado:
- ✅ URL cambia a `/balance?view=yearly`
- ✅ Tab "Anual" está activo
- ✅ Tabla muestra períodos en formato YYYY
- ✅ Filtros muestran últimos 5 años
- ✅ Ingresos, egresos y neto correctos por año

### Verificación en DB:
```sql
SELECT 
    date_trunc('year', datetime) AS period,
    SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END) AS income,
    SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) AS expense
FROM finance_ledger
WHERE datetime >= NOW() - INTERVAL '5 years'
GROUP BY 1
ORDER BY 1;
```

---

## Caso 4: Filtros de Rango de Fechas (Mensual)

### Pasos:
1. En Balance Mensual
2. Ingresar fechas:
   - **Fecha Inicio:** 2026-01-01
   - **Fecha Fin:** 2026-01-31
3. Click **"Aplicar Filtros"**

### Resultado esperado:
- ✅ URL incluye `?view=monthly&start=2026-01-01&end=2026-01-31`
- ✅ Solo muestra datos de enero 2026
- ✅ Totales calculados solo para ese período

### Verificación en DB:
```sql
SELECT 
    date_trunc('month', datetime) AS period,
    SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END) AS income,
    SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) AS expense
FROM finance_ledger
WHERE datetime >= '2026-01-01 00:00:00'
  AND datetime <= '2026-01-31 23:59:59'
GROUP BY 1
ORDER BY 1;
```

---

## Caso 5: Validación de Fechas (start > end)

### Pasos:
1. En Balance
2. Ingresar fechas:
   - **Fecha Inicio:** 2026-01-31
   - **Fecha Fin:** 2026-01-01
3. Click **"Aplicar Filtros"**

### Resultado esperado:
- ⚠️ Mensaje: "La fecha de inicio debe ser menor o igual a la fecha de fin"
- ✅ Se muestran datos con rango por defecto
- ✅ No crash de la aplicación

---

## Caso 6: Balance sin Datos (Rango Vacío)

### Pasos:
1. En Balance
2. Ingresar fechas futuras:
   - **Fecha Inicio:** 2027-01-01
   - **Fecha Fin:** 2027-12-31
3. Click **"Aplicar Filtros"**

### Resultado esperado:
- ✅ Alert info: "No hay datos financieros para el rango de fechas seleccionado"
- ✅ Tarjetas de resumen muestran $0.00
- ✅ No muestra tabla de períodos

---

## Caso 7: Ver Libro Mayor (Ledger List)

### Pasos:
1. En Balance, click en **"Ver Libro Mayor"**

### Resultado esperado:
- ✅ Redirige a `/balance/ledger`
- ✅ Tabla con todos los asientos contables
- ✅ Columnas:
  - ID
  - Fecha/Hora
  - Tipo (INGRESO/EGRESO con badges)
  - Monto
  - Origen (Venta/Pago Boleta/Manual)
  - Ref ID
  - Categoría
  - Notas
- ✅ Ordenados por fecha descendente (más reciente primero)
- ✅ Botón "Movimiento Manual" visible

### Verificación en DB:
```sql
SELECT 
    id,
    datetime,
    type,
    amount,
    reference_type,
    reference_id,
    category,
    notes
FROM finance_ledger
ORDER BY datetime DESC
LIMIT 20;
```

---

## Caso 8: Filtrar Libro Mayor por Tipo (Solo Ingresos)

### Pasos:
1. En Libro Mayor
2. Filtro **Tipo:** Ingreso
3. Click **"Filtrar"**

### Resultado esperado:
- ✅ Solo muestra asientos con type=INCOME
- ✅ Todos con badge "INGRESO" verde
- ✅ Origen debería ser "Venta" o "Manual" (no "Pago Boleta")

### Verificación en DB:
```sql
SELECT COUNT(*) FROM finance_ledger WHERE type = 'INCOME';
-- Debe coincidir con el número de filas en la UI
```

---

## Caso 9: Filtrar Libro Mayor por Rango de Fechas

### Pasos:
1. En Libro Mayor
2. Ingresar:
   - **Fecha Desde:** 2026-01-01
   - **Fecha Hasta:** 2026-01-31
3. Click **"Filtrar"**

### Resultado esperado:
- ✅ Solo muestra asientos de enero 2026
- ✅ Número de asientos mostrado es correcto

### Verificación en DB:
```sql
SELECT COUNT(*) 
FROM finance_ledger
WHERE datetime >= '2026-01-01 00:00:00'
  AND datetime <= '2026-01-31 23:59:59';
```

---

## Caso 10: Crear Movimiento Manual (Ingreso)

### Pasos:
1. En Libro Mayor, click **"Movimiento Manual"**
2. Llenar formulario:
   - **Tipo:** Ingreso
   - **Monto:** 5000.00
   - **Fecha/Hora:** (dejar por defecto o elegir)
   - **Categoría:** Préstamo Bancario
   - **Notas:** Préstamo recibido para capital de trabajo
3. Click **"Registrar Movimiento"**

### Resultado esperado:
- ✅ Mensaje: "Movimiento manual de tipo INCOME por $5000.00 registrado exitosamente"
- ✅ Redirige a Libro Mayor
- ✅ El nuevo asiento aparece en la lista
- ✅ Tipo: INGRESO (badge verde)
- ✅ Origen: Manual (badge gris)
- ✅ Ref ID: - (sin referencia)
- ✅ Categoría: Préstamo Bancario
- ✅ Notas: Préstamo recibido...

### Verificación en DB:
```sql
SELECT * 
FROM finance_ledger 
WHERE reference_type = 'MANUAL'
ORDER BY id DESC 
LIMIT 1;

-- type debe ser 'INCOME'
-- amount debe ser 5000.00
-- reference_id debe ser NULL
-- category debe ser 'Préstamo Bancario'
```

---

## Caso 11: Crear Movimiento Manual (Egreso)

### Pasos:
1. En Libro Mayor, click **"Movimiento Manual"**
2. Llenar formulario:
   - **Tipo:** Egreso
   - **Monto:** 1500.00
   - **Categoría:** Sueldos
   - **Notas:** Pago de sueldo enero
3. Click **"Registrar Movimiento"**

### Resultado esperado:
- ✅ Mensaje: "Movimiento manual de tipo EXPENSE por $1500.00 registrado exitosamente"
- ✅ El nuevo asiento aparece en Libro Mayor
- ✅ Tipo: EGRESO (badge rojo)
- ✅ Origen: Manual

### Verificación en DB:
```sql
SELECT * 
FROM finance_ledger 
WHERE reference_type = 'MANUAL' 
  AND type = 'EXPENSE'
ORDER BY id DESC 
LIMIT 1;
```

---

## Caso 12: Validación Monto <= 0 en Movimiento Manual

### Pasos:
1. En Libro Mayor, click **"Movimiento Manual"**
2. Ingresar:
   - **Tipo:** Ingreso
   - **Monto:** 0 o -100
3. Click **"Registrar Movimiento"**

### Resultado esperado:
- ❌ Error: "El monto debe ser mayor a 0"
- ✅ No se crea el movimiento

---

## Caso 13: Movimientos Manuales Aparecen en Balance

### Pre-condición:
- Haber creado al menos 1 movimiento manual de INGRESO
- Haber creado al menos 1 movimiento manual de EGRESO

### Pasos:
1. Navegar a **Balance**
2. Ver Balance Mensual del mes actual

### Resultado esperado:
- ✅ El ingreso manual se suma a los ingresos del balance
- ✅ El egreso manual se suma a los egresos del balance
- ✅ El neto refleja ambos movimientos

### Verificación en DB:
```sql
-- Totales incluyendo manuales
SELECT 
    SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END) AS total_income,
    SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) AS total_expense
FROM finance_ledger
WHERE date_trunc('month', datetime) = date_trunc('month', NOW());

-- Debe coincidir con tarjetas de resumen en UI
```

---

## Caso 14: Verificar Totales Globales

### Pasos:
1. Navegar a **Balance**
2. Ver Balance sin filtros (rango por defecto)

### Verificación en DB:
```sql
-- Totales globales
SELECT 
    type,
    COUNT(*) AS num_entries,
    SUM(amount) AS total
FROM finance_ledger
GROUP BY type;

-- type='INCOME' → debe coincidir con suma de ingresos en balance
-- type='EXPENSE' → debe coincidir con suma de egresos en balance
```

### Resultado esperado:
- ✅ Total de ingresos en tarjeta = SUM de INCOME en DB
- ✅ Total de egresos en tarjeta = SUM de EXPENSE en DB
- ✅ Neto = Ingresos - Egresos

---

## Caso 15: Integración: Confirmar Venta → Ver en Balance

### Pasos:
1. Crear y confirmar una venta (Fase 2)
   - Anotar el total de la venta
2. Navegar a **Balance → Diario**
3. Buscar el día de hoy en la tabla

### Resultado esperado:
- ✅ El ingreso del día incluye el total de la venta
- ✅ En Libro Mayor, aparece asiento con:
  - Tipo: INGRESO
  - Origen: Venta
  - Ref ID: ID de la venta
  - Monto: Total de la venta

### Verificación en DB:
```sql
SELECT * 
FROM finance_ledger 
WHERE reference_type = 'SALE'
ORDER BY id DESC 
LIMIT 1;
```

---

## Caso 16: Integración: Pagar Boleta → Ver en Balance

### Pasos:
1. Pagar una boleta pendiente (Fase 4)
   - Anotar el total de la boleta
2. Navegar a **Balance → Diario**
3. Buscar el día del pago en la tabla

### Resultado esperado:
- ✅ El egreso del día incluye el total de la boleta
- ✅ En Libro Mayor, aparece asiento con:
  - Tipo: EGRESO
  - Origen: Pago Boleta
  - Ref ID: ID de la boleta
  - Monto: Total de la boleta

### Verificación en DB:
```sql
SELECT * 
FROM finance_ledger 
WHERE reference_type = 'INVOICE_PAYMENT'
ORDER BY id DESC 
LIMIT 1;
```

---

## Resumen de Verificaciones Críticas

### ✅ Checklist Final:

- [ ] Balance mensual muestra datos correctos con períodos YYYY-MM
- [ ] Balance diario muestra datos correctos con períodos YYYY-MM-DD
- [ ] Balance anual muestra datos correctos con períodos YYYY
- [ ] Filtros de fecha funcionan correctamente
- [ ] Validación start > end muestra error
- [ ] Tarjetas de resumen (ingresos, egresos, neto) coinciden con totales de tabla
- [ ] Totales de tabla coinciden con SUM en DB
- [ ] Libro Mayor muestra todos los asientos ordenados por fecha desc
- [ ] Filtros de Libro Mayor (tipo, fechas) funcionan
- [ ] Crear movimiento manual INCOME funciona
- [ ] Crear movimiento manual EXPENSE funciona
- [ ] Validación monto <= 0 funciona
- [ ] Movimientos manuales aparecen en balance
- [ ] Ventas confirmadas aparecen como INCOME en ledger y balance
- [ ] Boletas pagadas aparecen como EXPENSE en ledger y balance
- [ ] Consistencia: SUM(ledger INCOME) = Total Ingresos en Balance
- [ ] Consistencia: SUM(ledger EXPENSE) = Total Egresos en Balance

---

## Queries Útiles para Debugging

### Ver todos los movimientos agrupados por tipo:
```sql
SELECT 
    type,
    reference_type,
    COUNT(*) AS num_entries,
    SUM(amount) AS total
FROM finance_ledger
GROUP BY type, reference_type
ORDER BY type, reference_type;
```

### Ver balance mensual con desglose:
```sql
SELECT 
    date_trunc('month', datetime) AS period,
    type,
    reference_type,
    COUNT(*) AS num_entries,
    SUM(amount) AS total
FROM finance_ledger
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 2, 3;
```

### Verificar consistencia (ingresos):
```sql
-- Total de ventas confirmadas
SELECT SUM(total_amount) 
FROM sale 
WHERE status = 'CONFIRMED';

-- Total de ingresos de ventas en ledger
SELECT SUM(amount) 
FROM finance_ledger 
WHERE type = 'INCOME' AND reference_type = 'SALE';

-- Deben ser iguales
```

### Verificar consistencia (egresos):
```sql
-- Total de boletas pagadas
SELECT SUM(total_amount) 
FROM purchase_invoice 
WHERE status = 'PAID';

-- Total de egresos de pagos en ledger
SELECT SUM(amount) 
FROM finance_ledger 
WHERE type = 'EXPENSE' AND reference_type = 'INVOICE_PAYMENT';

-- Deben ser iguales
```

### Ver detalle de movimientos de un día específico:
```sql
SELECT 
    id,
    datetime,
    type,
    amount,
    reference_type,
    reference_id,
    category,
    notes
FROM finance_ledger
WHERE date_trunc('day', datetime) = '2026-01-08'
ORDER BY datetime DESC;
```

---

## Notas Importantes

1. **Períodos vacíos:** Si no hay datos para un período, no aparece en la tabla. Esto es normal y esperado.

2. **Movimientos manuales:** NO afectan stock. Solo se registran en finance_ledger para el balance.

3. **Consistencia:** Los totales en Balance deben coincidir exactamente con SUM en finance_ledger.

4. **Filtros de fecha:** Son inclusivos (start y end incluidos en el rango).

5. **Visualización de origen:** 
   - Venta = SALE
   - Pago Boleta = INVOICE_PAYMENT
   - Manual = MANUAL

6. **Neto positivo vs negativo:**
   - Positivo (azul): Ganancia (ingresos > egresos)
   - Negativo (amarillo): Pérdida (egresos > ingresos)

---

## ¿Qué sigue? → FASE 6

En la Fase 6 se implementará:
- **Dockerización completa:** Dockerfile + docker-compose.yml
- Contenedorización de la aplicación Flask
- Orquestación con PostgreSQL
- Variables de entorno en Docker
- Volúmenes para persistencia
- README actualizado con instrucciones Docker

