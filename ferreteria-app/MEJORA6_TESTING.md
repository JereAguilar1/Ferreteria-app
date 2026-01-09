# MEJORA 6 – Filtro por Año en Balance Mensual

## 📋 **Testing Checklist**

---

## **Objetivo**
Validar que el Balance Mensual permite filtrar por Año de forma eficiente, sin romper las vistas diaria/anual ni los filtros existentes.

---

## **1. Filtro de Año en Vista Mensual**

### ✅ **Test 1.1: Monthly sin parámetros (Default)**
**Objetivo:** Verificar comportamiento por defecto al acceder a `/balance?view=monthly` sin filtros.

**Pasos:**
1. Navegar a `http://localhost:5000/balance?view=monthly`
2. Observar el select de Año
3. Observar los datos mostrados

**Resultado esperado:**
- ✅ Select de Año: Muestra años con datos (desde `finance_ledger`)
- ✅ Año seleccionado por defecto:
  - Si hay datos en el año actual → año actual
  - Si no, el último año con datos
- ✅ Tabla muestra los meses del año seleccionado
- ✅ Mensaje informativo: "Mostrando balance mensual para el año **2026**"
- ✅ Meses sin movimientos NO aparecen (solo meses con income/expense)

---

### ✅ **Test 1.2: Seleccionar año manualmente**
**Objetivo:** Validar que se puede filtrar por año específico.

**Casos a probar:**

#### **Caso A: Año con datos**
**Pasos:**
1. En `/balance?view=monthly`
2. Seleccionar Año: `2026`
3. Click "Aplicar Filtro"

**Resultado esperado:**
- ✅ URL actualizada: `/balance?view=monthly&year=2026`
- ✅ Tabla muestra solo meses de 2026
- ✅ Formato de período: `2026-01`, `2026-02`, etc.
- ✅ Totales calculados correctamente para el año
- ✅ Mensaje: "Mostrando balance mensual para el año **2026**"

---

#### **Caso B: Año sin datos**
**Pasos:**
1. Seleccionar un año que no tenga datos (ej: 2024)
2. Click "Aplicar Filtro"

**Resultado esperado:**
- ✅ Tabla vacía con mensaje: "No hay datos financieros para el rango de fechas seleccionado."
- ✅ Totales en $0.00
- Sin errores

---

### ✅ **Test 1.3: Cambiar año**
**Objetivo:** Verificar que cambiar el año funciona correctamente.

**Pasos:**
1. Filtrar por 2026
2. Cambiar año a 2025
3. Click "Aplicar Filtro"

**Resultado esperado:**
- ✅ URL: `/balance?view=monthly&year=2025`
- ✅ Tabla actualizada con meses de 2025
- ✅ Select de Año muestra 2025 seleccionado
- ✅ Totales recalculados

---

### ✅ **Test 1.4: Botón "Limpiar"**
**Objetivo:** Verificar que el botón "Limpiar" restablece los filtros a defaults.

**Pasos:**
1. Aplicar filtro personalizado (ej: Año 2025)
2. Click "Limpiar"

**Resultado esperado:**
- ✅ URL: `/balance?view=monthly` (sin year param)
- ✅ Filtros vuelven a defaults (año actual o último año con datos)
- ✅ Tabla actualizada

---

## **2. Validaciones de Parámetros**

### ✅ **Test 2.1: year inválido**
**Objetivo:** Validar manejo de año fuera de rango razonable.

**Casos:**
| year | Resultado |
|------|-----------|
| `1899` | ⚠️ Flash warning: "Año inválido." + Fallback a defaults |
| `2101` | ⚠️ Flash warning: "Año inválido." + Fallback a defaults |
| `abc` | ⚠️ Flash warning: "Año inválido." + Fallback a defaults |
| `` (vacío) | Fallback a defaults (sin warning) |

**Pasos:**
1. Forzar URL: `/balance?view=monthly&year=1899`
2. Observar comportamiento

**Resultado esperado:**
- ⚠️ Flash message rojo: "Año inválido."
- ✅ Página carga con defaults (no crash)
- ✅ Select muestra valor por defecto

---

## **3. Integración con Filtros Existentes**

### ✅ **Test 3.1: Prioridad year sobre start/end**
**Objetivo:** Verificar que year tiene prioridad sobre start/end.

**Política definida:**
- **Si viene `year`** → construir start/end desde año, ignorar start/end params
- **Si NO viene `year` pero vienen `start`/`end`** → usar start/end
- **Si NO viene nada** → usar defaults

**Pasos:**
1. URL: `/balance?view=monthly&year=2026&start=2025-01-01&end=2025-12-31`
2. Observar datos mostrados

**Resultado esperado:**
- ✅ Tabla muestra **solo meses de 2026** (ignora start/end)
- ✅ Select: Año=2026
- ✅ URL mantiene todos los params (pero year toma prioridad)

**SQL Query esperado:**
```sql
WHERE datetime >= '2026-01-01 00:00:00' 
  AND datetime <= '2026-12-31 23:59:59'
GROUP BY date_trunc('month', datetime)
```

---

### ✅ **Test 3.2: Sin year, con start/end (legacy)**
**Objetivo:** Verificar que start/end funcionan si no hay year.

**Pasos:**
1. URL: `/balance?view=monthly&start=2025-06-01&end=2025-12-31`
2. Observar datos

**Resultado esperado:**
- ✅ Tabla muestra meses desde Junio a Diciembre 2025
- ✅ Funciona como antes (compatibilidad con filtros legacy)

**Nota:** Como monthly ahora usa defaults basados en año, es posible que este caso sea sobrescrito. Documentar comportamiento real.

---

### ✅ **Test 3.3: Sin filtros en monthly**
**Objetivo:** Verificar defaults.

**Pasos:**
1. URL: `/balance?view=monthly`

**Resultado esperado:**
- ✅ Usa año actual (si hay datos) o último año con datos
- ✅ Select precargado

---

## **4. Queries SQL Eficientes**

### ✅ **Test 4.1: Verificar query SQL**
**Objetivo:** Asegurar que el filtrado se hace a nivel SQL, no en Python.

**Query esperado para monthly, año 2026:**
```sql
SELECT 
    date_trunc('month', finance_ledger.datetime) AS period,
    SUM(CASE WHEN finance_ledger.type = 'INCOME' THEN finance_ledger.amount ELSE 0 END) AS income,
    SUM(CASE WHEN finance_ledger.type = 'EXPENSE' THEN finance_ledger.amount ELSE 0 END) AS expense
FROM finance_ledger
WHERE finance_ledger.datetime >= '2026-01-01 00:00:00'
  AND finance_ledger.datetime <= '2026-12-31 23:59:59'
GROUP BY date_trunc('month', finance_ledger.datetime)
ORDER BY period ASC;
```

**Verificaciones:**
- ✅ `date_trunc('month', ...)` se usa correctamente
- ✅ `WHERE` con rango de fechas del año completo
- ✅ `GROUP BY` por mes
- ✅ Agregación `SUM` + `CASE` para income/expense
- ✅ No hay fetch de todos los registros en Python seguido de filtrado

---

### ✅ **Test 4.2: Rango de fechas exacto**
**Objetivo:** Verificar que el rango es correcto.

**Para year=2026:**
- `start = 2026-01-01 00:00:00`
- `end = 2026-12-31 23:59:59`

**Verificación SQL:**
```sql
SELECT 
    MIN(datetime) as first_entry,
    MAX(datetime) as last_entry
FROM finance_ledger
WHERE datetime >= '2026-01-01 00:00:00'
  AND datetime <= '2026-12-31 23:59:59';
```

**Resultado esperado:**
- ✅ `first_entry` está en 2026
- ✅ `last_entry` está en 2026
- ✅ No hay datos de 2025 ni 2027

---

## **5. Años Disponibles**

### ✅ **Test 5.1: available_years desde DB**
**Objetivo:** Verificar que los años disponibles vienen desde `finance_ledger`.

**Pasos:**
1. Verificar datos en DB:
```sql
SELECT DISTINCT EXTRACT(YEAR FROM datetime) AS year 
FROM finance_ledger 
ORDER BY year DESC;
```
2. Navegar a `/balance?view=monthly`
3. Inspeccionar select de Año

**Resultado esperado:**
- ✅ Select muestra solo años con datos
- ✅ Orden descendente (más reciente primero)
- Si DB vacío: select muestra año actual o "Sin datos"

---

## **6. Vistas Daily y Yearly No Afectadas**

### ✅ **Test 6.1: Vista Diaria funciona igual**
**Objetivo:** Asegurar que los cambios NO rompieron daily view.

**Pasos:**
1. Navegar a `/balance?view=daily`
2. Verificar que muestra selects de year/month (MEJORA 5)
3. Aplicar filtro
4. Verificar datos

**Resultado esperado:**
- ✅ Filtros year/month visibles (como en MEJORA 5)
- ✅ Tabla muestra balance agrupado por día
- ✅ Totales correctos
- Sin errores

---

### ✅ **Test 6.2: Vista Anual funciona igual**
**Objetivo:** Asegurar que yearly view no se rompió.

**Pasos:**
1. Navegar a `/balance?view=yearly`
2. Verificar filtros start/end
3. Verificar tabla agrupa por año

**Resultado esperado:**
- ✅ Funciona como antes
- ✅ Filtros start/end visibles
- ✅ No se ve afectada por year param
- Sin errores

---

## **7. Persistencia de Query Params**

### ✅ **Test 7.1: Query params persisten en URL**
**Objetivo:** Verificar que los filtros se mantienen en la URL.

**Pasos:**
1. Filtrar por 2026 en monthly
2. Verificar URL: `/balance?view=monthly&year=2026`
3. Copiar URL
4. Abrir en nueva pestaña

**Resultado esperado:**
- ✅ Carga con filtro aplicado (año 2026)
- ✅ Datos correctos

---

### ✅ **Test 7.2: Navegación entre tabs**
**Objetivo:** Verificar comportamiento al cambiar de vista.

**Pasos:**
1. Filtrar monthly por 2026
2. Click en tab "Diario"
3. Observar filtros
4. Volver a tab "Mensual"

**Resultado esperado:**
- Al ir a Daily: ✅ Carga con sus propios defaults (no hereda year de monthly)
- Al volver a Monthly: ⚠️ Puede volver a defaults o mantener year (depende de implementación de tabs)
- **Decisión:** Los tabs actuales son enlaces directos, NO mantienen params entre vistas (aceptable)

---

## **8. Mensajes y UX**

### ✅ **Test 8.1: Mensaje informativo de filtro activo**
**Objetivo:** Verificar que se muestra un mensaje claro cuando hay filtro aplicado.

**Pasos:**
1. Filtrar por 2026

**Resultado esperado:**
- ✅ Alert azul visible: "Mostrando balance mensual para el año **2026**"
- ✅ Íconos apropiados
- ✅ Estilo claro y legible

---

### ✅ **Test 8.2: Sin datos para el año seleccionado**
**Objetivo:** Verificar mensaje claro cuando no hay datos.

**Pasos:**
1. Seleccionar un año sin datos (ej: 2024)

**Resultado esperado:**
- ℹ️ Alert info: "No hay datos financieros para el rango de fechas seleccionado."
- ✅ Explicación: "Los ingresos provienen de ventas confirmadas..."
- ✅ Totales en $0.00
- Sin confusión

---

## **9. Casos Edge y Compatibilidad**

### ✅ **Test 9.1: Base de datos vacía (sin finance_ledger)**
**Objetivo:** Verificar comportamiento sin datos.

**Pasos:**
1. Vaciar `finance_ledger` (o usar DB limpia)
2. Navegar a `/balance?view=monthly`

**Resultado esperado:**
- ✅ available_years = [] → Select muestra año actual o "Sin datos"
- ✅ Mensaje: "No hay datos financieros..."
- Sin crash

---

### ✅ **Test 9.2: Solo un mes con datos en el año**
**Objetivo:** Verificar que muestra correctamente si hay solo 1 mes con datos.

**Pasos:**
1. Asegurar que 2026 tiene datos solo en Enero
2. Filtrar por 2026

**Resultado esperado:**
- ✅ Tabla muestra 1 fila: "2026-01" con income/expense
- ✅ Totales correctos
- Sin meses vacíos

---

### ✅ **Test 9.3: Año completo con datos todos los meses**
**Objetivo:** Verificar que muestra hasta 12 filas si todos los meses tienen movimientos.

**Pasos:**
1. Crear datos para todos los meses de 2025
2. Filtrar por 2025

**Resultado esperado:**
- ✅ Tabla muestra 12 filas (1 por mes)
- ✅ Formato: 2025-01, 2025-02, ..., 2025-12
- ✅ Totales suman correctamente

---

### ✅ **Test 9.4: Año con solo income (sin expense)**
**Objetivo:** Verificar que muestra correctamente si solo hay un tipo de movimiento.

**Pasos:**
1. Filtrar por año que solo tenga ventas (sin pagos de boletas)

**Resultado esperado:**
- ✅ Columna Income con valores
- ✅ Columna Expense en $0.00
- ✅ Neto = Income
- Sin errores

---

## **10. Regresión (No Romper)**

### ✅ **Test 10.1: Productos CRUD**
**Pasos:** Crear, editar, listar productos

**Resultado esperado:** ✅ Funcional

---

### ✅ **Test 10.2: Ventas (POS)**
**Pasos:** Crear venta, confirmar

**Resultado esperado:** ✅ Funcional + genera INCOME en ledger

---

### ✅ **Test 10.3: Compras (Boletas)**
**Pasos:** Crear boleta, pagar

**Resultado esperado:** ✅ Funcional + genera EXPENSE en ledger al pagar

---

### ✅ **Test 10.4: Ledger manual**
**Pasos:** Crear movimiento manual

**Resultado esperado:** ✅ Funcional + aparece en balance

---

### ✅ **Test 10.5: MEJORA 1, 2, 3, 4, 5**
**Pasos:** Verificar fotos, filtros, top vendidos, unit_cost entero, daily year/month

**Resultado esperado:** ✅ Todas funcionales

---

## **11. Comparación Monthly vs Daily**

### ✅ **Test 11.1: Totales coinciden**
**Objetivo:** Verificar que los totales de monthly coinciden con la suma de daily.

**Pasos:**
1. Filtrar daily por Enero 2026
2. Sumar manualmente los totales de todos los días
3. Filtrar monthly por 2026
4. Verificar que el total de Enero en monthly coincide con la suma de daily

**Resultado esperado:**
- ✅ Total Income Enero (monthly) = SUM(Income todos los días de Enero en daily)
- ✅ Total Expense Enero (monthly) = SUM(Expense todos los días de Enero en daily)
- ✅ Neto coincide

---

## **12. Documentación de Prioridad de Filtros**

### **Prioridad Implementada (Monthly View):**

1. **Si viene `year` param:**
   - Construir `start` = `YYYY-01-01`
   - Construir `end` = `YYYY-12-31`
   - **Ignorar** cualquier `start`/`end` que venga en query params

2. **Si NO viene `year` pero vienen `start`/`end`:**
   - Usar `start` y `end` directamente

3. **Si NO viene nada:**
   - Defaults:
     - Año actual (si hay datos en finance_ledger)
     - Si no, último año con datos
     - Si no hay datos, año actual del sistema

**Rango exacto:**
```python
start = date(year, 1, 1)     # Primer día del año, 00:00:00
end = date(year, 12, 31)     # Último día del año, 23:59:59
```

**Query SQL WHERE:**
```sql
WHERE datetime >= 'YYYY-01-01 00:00:00' 
  AND datetime <= 'YYYY-12-31 23:59:59'
GROUP BY date_trunc('month', datetime)
```

---

## **✅ Testing Completo: Checklist Final**

- [ ] Monthly sin params → defaults cargados (año actual o último con datos)
- [ ] Seleccionar year → datos filtrados
- [ ] Cambiar año → actualiza datos
- [ ] Botón "Limpiar" → vuelve a defaults
- [ ] year inválido → warning + fallback
- [ ] year tiene prioridad sobre start/end
- [ ] available_years desde DB (query SQL)
- [ ] Query SQL eficiente (date_trunc('month') + WHERE)
- [ ] Daily view no afectada (MEJORA 5 funciona)
- [ ] Yearly view no afectada (start/end funcionan)
- [ ] Query params persisten (al copiar URL)
- [ ] Mensaje informativo visible
- [ ] Sin datos → mensaje claro
- [ ] DB vacía → no crash
- [ ] Solo 1 mes con datos → muestra 1 fila
- [ ] 12 meses con datos → muestra 12 filas
- [ ] Totales monthly = SUM(totales daily del año)
- [ ] Regresión: Productos, Ventas, Compras, Ledger funcionan
- [ ] MEJORA 1, 2, 3, 4, 5 funcionan

---

## **🎯 Resultado Esperado Final**

Al finalizar todos los tests:
- ✅ **Filtro year funciona en monthly view**
- ✅ **Queries SQL eficientes (agregación en DB)**
- ✅ **Validaciones robustas (year 1900-2100)**
- ✅ **Prioridad de filtros clara y documentada**
- ✅ **available_years desde DB**
- ✅ **Daily y Yearly no afectadas**
- ✅ **UX clara con mensajes informativos**
- ✅ **Sin regresiones en funcionalidades existentes**

---

**Última actualización:** Enero 2026  
**Autor:** Sistema Ferretería - MEJORA 6
