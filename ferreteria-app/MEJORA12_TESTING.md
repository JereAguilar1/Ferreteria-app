# 🧪 **MEJORA 12: Método de Pago/Cobro - Casos de Prueba**

---

## **📋 Resumen de la Mejora**

**Objetivo**: Permitir registrar el método de pago/cobro (Efectivo o Transferencia) en ventas, pagos de boletas y movimientos manuales, y poder filtrar el balance por método.

**Cambios implementados**:
- ✅ Columna `payment_method` agregada a `finance_ledger` (CASH/TRANSFER)
- ✅ Enum `PaymentMethod` en modelo `FinanceLedger`
- ✅ Selector de método en ventas (POS)
- ✅ Selector de método en pago de boletas
- ✅ Selector de método en movimientos manuales
- ✅ Filtro de método en Balance (daily/monthly/yearly)
- ✅ Filtro de método en Libro Mayor (Ledger List)

---

## **🎯 PARTE 1: Ventas (POS) - Registrar Método**

### **Caso 1.1: Venta con Efectivo**
**Objetivo**: Verificar que una venta se registre correctamente con método CASH.

**Pasos**:
1. Ir a `/sales/new`
2. Agregar productos al carrito
3. En el carrito, seleccionar **"Efectivo"** (debe estar seleccionado por defecto)
4. Hacer clic en "Confirmar Venta"

**Resultado esperado**:
- ✅ Venta confirmada exitosamente
- ✅ Flash message: "Venta #X confirmada exitosamente..."
- ✅ En la tabla `finance_ledger`, el registro de INCOME debe tener `payment_method='CASH'`
- ✅ Stock actualizado correctamente

**Verificación en DB**:
```sql
SELECT id, type, amount, payment_method, reference_type, reference_id
FROM finance_ledger
WHERE reference_type = 'SALE'
ORDER BY id DESC
LIMIT 1;
```
Debe mostrar `payment_method = CASH`.

---

### **Caso 1.2: Venta con Transferencia**
**Objetivo**: Verificar que una venta se registre correctamente con método TRANSFER.

**Pasos**:
1. Ir a `/sales/new`
2. Agregar productos al carrito
3. En el carrito, seleccionar **"Transferencia"**
4. Hacer clic en "Confirmar Venta"

**Resultado esperado**:
- ✅ Venta confirmada exitosamente
- ✅ En `finance_ledger`, el registro debe tener `payment_method='TRANSFER'`
- ✅ Stock actualizado correctamente

**Verificación en DB**:
```sql
SELECT id, type, amount, payment_method, reference_type, reference_id
FROM finance_ledger
WHERE reference_type = 'SALE'
ORDER BY id DESC
LIMIT 1;
```
Debe mostrar `payment_method = TRANSFER`.

---

### **Caso 1.3: Validación - Método inválido**
**Objetivo**: Verificar que el sistema rechace métodos de pago inválidos.

**Pasos**:
1. Enviar un POST a `/sales/confirm` con `payment_method=INVALID` (usar herramienta de dev o curl)

**Resultado esperado**:
- ✅ Flash message de error: "Método de pago inválido."
- ✅ Redirección a `/sales/new`
- ✅ NO se crea la venta ni el registro en `finance_ledger`

---

## **🎯 PARTE 2: Balance - Filtrar por Método**

### **Caso 2.1: Balance Diario - Filtro "Todos"**
**Objetivo**: Verificar que sin filtro se muestren todos los movimientos.

**Pasos**:
1. Ir a `/balance?view=daily`
2. Asegurarse de que "Método" esté en **"Todos"**
3. Aplicar filtros

**Resultado esperado**:
- ✅ Se muestran todos los ingresos y egresos (CASH + TRANSFER)
- ✅ Totales incluyen ambos métodos

---

### **Caso 2.2: Balance Diario - Filtro "Efectivo"**
**Objetivo**: Verificar que solo se muestren movimientos en efectivo.

**Prerequisitos**:
- Debe haber al menos 1 venta en efectivo y 1 en transferencia

**Pasos**:
1. Ir a `/balance?view=daily`
2. Seleccionar **"Método: Efectivo"**
3. Aplicar filtros

**Resultado esperado**:
- ✅ Solo se muestran movimientos con `payment_method='CASH'`
- ✅ Los movimientos en transferencia NO aparecen
- ✅ Mensaje informativo muestra: "Método: **Efectivo**"
- ✅ Totales reflejan solo efectivo

**Verificación**:
- El total de ingresos debe coincidir con la suma de ventas en efectivo del período

---

### **Caso 2.3: Balance Diario - Filtro "Transferencia"**
**Objetivo**: Verificar que solo se muestren movimientos por transferencia.

**Prerequisitos**:
- Debe haber al menos 1 venta en transferencia

**Pasos**:
1. Ir a `/balance?view=daily`
2. Seleccionar **"Método: Transferencia"**
3. Aplicar filtros

**Resultado esperado**:
- ✅ Solo se muestran movimientos con `payment_method='TRANSFER'`
- ✅ Los movimientos en efectivo NO aparecen
- ✅ Mensaje informativo muestra: "Método: **Transferencia**"

---

### **Caso 2.4: Balance Mensual - Filtro por Método**
**Objetivo**: Verificar que el filtro funcione en vista mensual.

**Pasos**:
1. Ir a `/balance?view=monthly`
2. Seleccionar un año con datos
3. Seleccionar **"Método: Efectivo"**
4. Aplicar filtros

**Resultado esperado**:
- ✅ Se agrupan por mes solo los movimientos en efectivo
- ✅ Query params persisten: `view=monthly&year=2026&method=cash`
- ✅ Mensaje informativo muestra año y método

---

### **Caso 2.5: Balance Anual - Filtro por Método**
**Objetivo**: Verificar que el filtro funcione en vista anual.

**Pasos**:
1. Ir a `/balance?view=yearly`
2. Seleccionar rango de fechas
3. Seleccionar **"Método: Transferencia"**
4. Aplicar filtros

**Resultado esperado**:
- ✅ Se agrupan por año solo los movimientos por transferencia
- ✅ Filtro se combina correctamente con `start` y `end`

---

### **Caso 2.6: Limpiar Filtros - Balance**
**Objetivo**: Verificar que el botón "Limpiar" resetee el filtro de método.

**Pasos**:
1. Aplicar filtro `method=cash`
2. Hacer clic en "Limpiar"

**Resultado esperado**:
- ✅ Redirección a `/balance?view=daily` (sin método ni otros filtros)
- ✅ Se muestran todos los movimientos
- ✅ Select de método vuelve a "Todos"

---

### **Caso 2.7: Validación - Método inválido en Balance**
**Objetivo**: Verificar que el sistema maneje métodos inválidos.

**Pasos**:
1. Ir a `/balance?view=daily&method=invalid`

**Resultado esperado**:
- ✅ Flash message: "Método de pago inválido. Mostrando todos."
- ✅ Se muestran todos los movimientos (fallback a `method=all`)
- ✅ NO se rompe la aplicación

---

## **🎯 PARTE 3: Libro Mayor (Ledger List) - Filtrar por Método**

### **Caso 3.1: Ledger List - Filtro por Efectivo**
**Objetivo**: Verificar que el libro mayor filtre por método.

**Pasos**:
1. Ir a `/balance/ledger`
2. Seleccionar **"Método: Efectivo"**
3. Hacer clic en "Filtrar"

**Resultado esperado**:
- ✅ Solo se muestran entradas con `payment_method='CASH'`
- ✅ Columna "Método" muestra badge "Efectivo" en todas las filas
- ✅ Query params persisten: `method=cash`

---

### **Caso 3.2: Ledger List - Mostrar columna "Método"**
**Objetivo**: Verificar que la columna "Método" se muestre correctamente.

**Pasos**:
1. Ir a `/balance/ledger`
2. Ver listado completo (sin filtros)

**Resultado esperado**:
- ✅ Columna "Método" visible en la tabla
- ✅ Para `CASH`: badge con ícono 💵 "Efectivo"
- ✅ Para `TRANSFER`: badge con ícono 🏦 "Transferencia"

---

### **Caso 3.3: Ledger List - Filtro combinado (Tipo + Método)**
**Objetivo**: Verificar que los filtros se combinen correctamente.

**Pasos**:
1. Ir a `/balance/ledger`
2. Seleccionar **"Tipo: Ingreso"**
3. Seleccionar **"Método: Transferencia"**
4. Hacer clic en "Filtrar"

**Resultado esperado**:
- ✅ Solo se muestran INGRESOS por TRANSFERENCIA
- ✅ Query params: `type=INCOME&method=transfer`
- ✅ Ambos filtros aplicados a nivel SQL (verificar con EXPLAIN)

---

## **🎯 PARTE 4: Pago de Boletas - Elegir Método**

### **Caso 4.1: Pagar boleta con Efectivo**
**Objetivo**: Verificar que el pago de una boleta registre el método correctamente.

**Prerequisitos**:
- Debe haber una boleta con status PENDING

**Pasos**:
1. Ir a `/invoices/<id>` (una boleta PENDING)
2. En "Registrar Pago", seleccionar **"Método: Efectivo"**
3. Ingresar fecha de pago
4. Hacer clic en "Marcar como Pagada"

**Resultado esperado**:
- ✅ Boleta marcada como PAID
- ✅ Flash message: "Boleta #X marcada como pagada (Efectivo)..."
- ✅ En `finance_ledger`, el EXPENSE debe tener `payment_method='CASH'`
- ✅ Columna `paid_at` actualizada

**Verificación en DB**:
```sql
SELECT id, type, amount, payment_method, reference_type, reference_id
FROM finance_ledger
WHERE reference_type = 'INVOICE_PAYMENT'
ORDER BY id DESC
LIMIT 1;
```
Debe mostrar `payment_method = CASH`.

---

### **Caso 4.2: Pagar boleta con Transferencia**
**Objetivo**: Verificar que el pago por transferencia funcione.

**Pasos**:
1. Ir a `/invoices/<id>` (una boleta PENDING)
2. Seleccionar **"Método: Transferencia"**
3. Ingresar fecha de pago
4. Confirmar pago

**Resultado esperado**:
- ✅ Boleta marcada como PAID
- ✅ Flash message incluye "(Transferencia)"
- ✅ En `finance_ledger`, el EXPENSE debe tener `payment_method='TRANSFER'`

---

### **Caso 4.3: Validación - Método requerido en pago**
**Objetivo**: Verificar que el método sea obligatorio.

**Pasos**:
1. Inspeccionar elemento en DevTools
2. Remover `required` del select
3. Enviar formulario sin seleccionar método

**Resultado esperado**:
- ✅ Backend valida y rechaza: "Método de pago inválido."
- ✅ NO se actualiza la boleta

---

## **🎯 PARTE 5: Movimientos Manuales - Elegir Método**

### **Caso 5.1: Movimiento Manual - Ingreso en Efectivo**
**Objetivo**: Verificar que un movimiento manual registre el método.

**Pasos**:
1. Ir a `/balance/ledger/new`
2. Tipo: **"Ingreso"**
3. Método: **"Efectivo"**
4. Monto: 1000
5. Categoría: "Otro ingreso"
6. Guardar

**Resultado esperado**:
- ✅ Movimiento creado exitosamente
- ✅ Flash message: "... (Efectivo) registrado exitosamente"
- ✅ En `finance_ledger`, el registro debe tener `payment_method='CASH'`

**Verificación en DB**:
```sql
SELECT id, type, amount, payment_method, reference_type
FROM finance_ledger
WHERE reference_type = 'MANUAL'
ORDER BY id DESC
LIMIT 1;
```
Debe mostrar `payment_method = CASH`.

---

### **Caso 5.2: Movimiento Manual - Egreso en Transferencia**
**Objetivo**: Verificar egreso manual por transferencia.

**Pasos**:
1. Ir a `/balance/ledger/new`
2. Tipo: **"Egreso"**
3. Método: **"Transferencia"**
4. Monto: 500
5. Notas: "Pago de servicio"
6. Guardar

**Resultado esperado**:
- ✅ Movimiento creado exitosamente
- ✅ En `finance_ledger`, el EXPENSE debe tener `payment_method='TRANSFER'`

---

### **Caso 5.3: Validación - Método requerido en manual**
**Objetivo**: Verificar que el método sea obligatorio en movimientos manuales.

**Pasos**:
1. Intentar enviar formulario sin seleccionar método (manipular HTML)

**Resultado esperado**:
- ✅ Backend valida: "Método de pago inválido."
- ✅ NO se crea el movimiento

---

## **🎯 PARTE 6: Compatibilidad y Migración**

### **Caso 6.1: Movimientos históricos (sin método)**
**Objetivo**: Verificar que movimientos creados antes de la mejora tengan default CASH.

**Pasos**:
1. Verificar en DB movimientos antiguos (si existen)

**Resultado esperado**:
- ✅ Todos los registros antiguos deben tener `payment_method='CASH'` (por DEFAULT)
- ✅ Se muestran correctamente en el ledger

**Verificación en DB**:
```sql
SELECT payment_method, COUNT(*)
FROM finance_ledger
GROUP BY payment_method;
```

---

### **Caso 6.2: Filtros combinados - Compatibilidad con mejoras anteriores**
**Objetivo**: Verificar que el filtro de método NO rompa otros filtros.

**Pasos**:
1. Balance Daily: filtrar por **Año/Mes + Método**
2. Balance Monthly: filtrar por **Año + Método**
3. Balance Yearly: filtrar por **Rango de fechas + Método**

**Resultado esperado**:
- ✅ Todos los filtros funcionan correctamente en conjunto
- ✅ Query params persisten al navegar
- ✅ NO hay conflictos entre filtros

---

## **🎯 PARTE 7: Performance y SQL**

### **Caso 7.1: Verificar índice en payment_method**
**Objetivo**: Asegurar que las consultas sean eficientes.

**Verificación en DB**:
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'finance_ledger'
AND indexname LIKE '%payment_method%';
```

**Resultado esperado**:
- ✅ Existe índice `idx_finance_ledger_payment_method`

---

### **Caso 7.2: EXPLAIN query con filtro de método**
**Objetivo**: Verificar que el índice se use en las consultas.

**Verificación en DB**:
```sql
EXPLAIN ANALYZE
SELECT date_trunc('day', datetime) AS period,
       SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END) AS income,
       SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) AS expense
FROM finance_ledger
WHERE datetime >= '2026-01-01' AND datetime < '2026-02-01'
AND payment_method = 'CASH'
GROUP BY 1
ORDER BY 1;
```

**Resultado esperado**:
- ✅ El plan de ejecución debe usar `idx_finance_ledger_payment_method`
- ✅ Tiempo de ejecución razonable (< 50ms para 1000 registros)

---

## **🎯 PARTE 8: UX y UI**

### **Caso 8.1: Badges y estilos**
**Objetivo**: Verificar que los badges de método sean consistentes.

**Pasos**:
1. Ir a `/balance/ledger`
2. Ver columna "Método"

**Resultado esperado**:
- ✅ "Efectivo": badge claro con ícono 💵
- ✅ "Transferencia": badge azul con ícono 🏦
- ✅ Estilos consistentes en toda la aplicación

---

### **Caso 8.2: Mensajes flash informativos**
**Objetivo**: Verificar que los mensajes incluyan el método.

**Pasos**:
1. Hacer una venta con transferencia
2. Pagar una boleta con efectivo
3. Crear un movimiento manual con transferencia

**Resultado esperado**:
- ✅ Flash messages incluyen método entre paréntesis:
  - "Venta confirmada... (Efectivo/Transferencia)"
  - "Boleta pagada (Efectivo/Transferencia)..."
  - "Movimiento registrado (Efectivo/Transferencia)..."

---

## **🎯 PARTE 9: Edge Cases**

### **Caso 9.1: Carrito vacío con método seleccionado**
**Objetivo**: Verificar que no se pueda confirmar venta sin productos.

**Pasos**:
1. Ir a `/sales/new` sin agregar productos
2. Intentar confirmar venta

**Resultado esperado**:
- ✅ Error: "El carrito está vacío..."
- ✅ NO se crea registro en `finance_ledger`

---

### **Caso 9.2: Cambiar método después de agregar productos**
**Objetivo**: Verificar que el método se persista correctamente.

**Pasos**:
1. Agregar productos al carrito
2. Seleccionar "Transferencia"
3. Cambiar a "Efectivo"
4. Confirmar venta

**Resultado esperado**:
- ✅ El método final (Efectivo) se registra correctamente
- ✅ El valor enviado en el POST es el último seleccionado

---

## **📊 Resumen de Pruebas**

| Categoría | Casos | Críticos |
|-----------|-------|----------|
| **Ventas (POS)** | 3 | ✅ 1.1, 1.2 |
| **Balance** | 7 | ✅ 2.2, 2.3 |
| **Ledger List** | 3 | ✅ 3.1, 3.2 |
| **Pago Boletas** | 3 | ✅ 4.1, 4.2 |
| **Movimientos Manuales** | 3 | ✅ 5.1, 5.2 |
| **Compatibilidad** | 2 | ✅ 6.1, 6.2 |
| **Performance** | 2 | ✅ 7.1 |
| **UX** | 2 | 8.1, 8.2 |
| **Edge Cases** | 2 | 9.1, 9.2 |
| **TOTAL** | **27** | **13** |

---

## **✅ Criterios de Aceptación (Checklist Final)**

- ✅ Ventas registran método correctamente (CASH/TRANSFER)
- ✅ Pagos de boletas registran método correctamente
- ✅ Movimientos manuales registran método correctamente
- ✅ Balance filtra por método en daily/monthly/yearly
- ✅ Ledger list filtra por método
- ✅ Columna "Método" visible en ledger con badges
- ✅ Validaciones de backend para métodos inválidos
- ✅ Filtros se combinan correctamente sin conflictos
- ✅ Query params persisten correctamente
- ✅ Flash messages informativos incluyen método
- ✅ Índice en `payment_method` creado y usado
- ✅ Movimientos históricos tienen default CASH
- ✅ NO se rompen funcionalidades existentes
- ✅ `/health` sigue accesible sin autenticación

---

## **🚀 Comandos Útiles para Pruebas**

### Verificar estructura de DB:
```sql
\d finance_ledger
```

### Ver últimos 10 movimientos con método:
```sql
SELECT id, datetime, type, amount, payment_method, reference_type
FROM finance_ledger
ORDER BY id DESC
LIMIT 10;
```

### Contar movimientos por método:
```sql
SELECT payment_method, type, COUNT(*), SUM(amount) as total
FROM finance_ledger
GROUP BY payment_method, type
ORDER BY payment_method, type;
```

### Verificar constraint:
```sql
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'finance_ledger'::regclass
AND conname LIKE '%payment%';
```

---

**✅ FIN DE TESTING MEJORA 12**
