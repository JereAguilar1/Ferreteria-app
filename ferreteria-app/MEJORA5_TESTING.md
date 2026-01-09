# MEJORA 5 – Filtros en Balance Diario (por Año y Mes)

## 📋 **Testing Checklist**

---

## **Objetivo**
Validar que el Balance Diario permite filtrar por Año y Mes de forma eficiente, sin romper los filtros existentes y manteniendo consultas SQL optimizadas.

---

## **1. Filtros de Año y Mes en Vista Diaria**

### ✅ **Test 1.1: Daily sin parámetros (Default)**
**Objetivo:** Verificar comportamiento por defecto al acceder a `/balance?view=daily` sin filtros.

**Pasos:**
1. Navegar a `http://localhost:5000/balance?view=daily`
2. Observar los selects de Año y Mes
3. Observar los datos mostrados

**Resultado esperado:**
- ✅ Select de Año: Muestra años con datos (desde `finance_ledger`)
- ✅ Select de Mes: Muestra todos los meses (1-12)
- ✅ Año y mes seleccionados por defecto:
  - Si hay datos en el mes actual → mes y año actual
  - Si no, el último mes con datos
- ✅ Tabla muestra los días del mes seleccionado
- ✅ Mensaje informativo: "Mostrando balance diario para [Mes Año]"

---

### ✅ **Test 1.2: Seleccionar año y mes manualmente**
**Objetivo:** Validar que se puede filtrar por año/mes específico.

**Casos a probar:**

#### **Caso A: Mes con datos**
**Pasos:**
1. En `/balance?view=daily`
2. Seleccionar Año: `2026`
3. Seleccionar Mes: `Enero (1)`
4. Click "Aplicar Filtros"

**Resultado esperado:**
- ✅ URL actualizada: `/balance?view=daily&year=2026&month=1`
- ✅ Tabla muestra solo días de enero 2026
- ✅ Días sin movimientos NO aparecen (solo días con income/expense)
- ✅ Totales calculados correctamente para el mes
- ✅ Mensaje: "Mostrando balance diario para Enero 2026"

---

#### **Caso B: Mes sin datos**
**Pasos:**
1. Seleccionar un mes que no tenga datos (ej: Diciembre 2025)
2. Click "Aplicar Filtros"

**Resultado esperado:**
- ✅ Tabla vacía con mensaje: "No hay datos financieros para el rango de fechas seleccionado."
- ✅ Totales en $0.00
- Sin errores

---

### ✅ **Test 1.3: Cambiar mes manteniendo año**
**Objetivo:** Verificar que cambiar solo el mes funciona correctamente.

**Pasos:**
1. Filtrar por Enero 2026
2. Cambiar mes a Febrero
3. Click "Aplicar Filtros"

**Resultado esperado:**
- ✅ URL: `/balance?view=daily&year=2026&month=2`
- ✅ Tabla actualizada con días de febrero 2026
- ✅ Select de Año mantiene 2026
- ✅ Select de Mes muestra Febrero seleccionado

---

### ✅ **Test 1.4: Cambiar año**
**Objetivo:** Verificar que cambiar año funciona.

**Pasos:**
1. Filtrar por Enero 2026
2. Cambiar año a 2025
3. Click "Aplicar Filtros"

**Resultado esperado:**
- ✅ URL: `/balance?view=daily&year=2025&month=1`
- ✅ Tabla muestra datos de enero 2025 (si existen)
- ✅ Selects actualizados

---

### ✅ **Test 1.5: Botón "Limpiar"**
**Objetivo:** Verificar que el botón "Limpiar" restablece los filtros a defaults.

**Pasos:**
1. Aplicar filtro personalizado (ej: Marzo 2025)
2. Click "Limpiar"

**Resultado esperado:**
- ✅ URL: `/balance?view=daily` (sin year/month params)
- ✅ Filtros vuelven a defaults (mes actual o último mes con datos)
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
| `abc` | ⚠️ Flash warning: "Año o mes inválido." + Fallback a defaults |
| `` (vacío) | Fallback a defaults (sin warning) |

**Pasos:**
1. Forzar URL: `/balance?view=daily&year=1899&month=1`
2. Observar comportamiento

**Resultado esperado:**
- ⚠️ Flash message rojo: "Año inválido."
- ✅ Página carga con defaults (no crash)
- ✅ Selects muestran valores por defecto

---

### ✅ **Test 2.2: month inválido**
**Objetivo:** Validar manejo de mes fuera de rango 1-12.

**Casos:**
| month | Resultado |
|-------|-----------|
| `0` | ⚠️ Flash warning: "Mes inválido. Debe estar entre 1 y 12." + Fallback |
| `13` | ⚠️ Flash warning: "Mes inválido. Debe estar entre 1 y 12." + Fallback |
| `-1` | ⚠️ Flash warning: "Mes inválido." + Fallback |
| `abc` | ⚠️ Flash warning: "Año o mes inválido." + Fallback |

**Pasos:**
1. Forzar URL: `/balance?view=daily&year=2026&month=13`
2. Observar comportamiento

**Resultado esperado:**
- ⚠️ Flash message rojo
- ✅ Fallback a defaults
- Sin crash

---

### ✅ **Test 2.3: Solo year (sin month)**
**Objetivo:** Verificar comportamiento si viene solo year.

**Pasos:**
1. URL: `/balance?view=daily&year=2026` (sin month)

**Resultado esperado:**
- ✅ Fallback a defaults (ignora year incompleto)
- O alternativamente: usa month actual
- (Depende de la lógica implementada - documentar)

---

### ✅ **Test 2.4: Solo month (sin year)**
**Objetivo:** Verificar comportamiento si viene solo month.

**Pasos:**
1. URL: `/balance?view=daily&month=3` (sin year)

**Resultado esperado:**
- ✅ Fallback a defaults (ignora month incompleto)
- Sin crash

---

## **3. Integración con Filtros Existentes**

### ✅ **Test 3.1: Prioridad year/month sobre start/end**
**Objetivo:** Verificar que year/month tienen prioridad sobre start/end.

**Política definida:**
- **Si vienen `year` y `month`** → usar esos, ignorar `start`/`end`
- **Si NO vienen `year`/`month`** → usar `start`/`end` si existen, o defaults

**Pasos:**
1. URL: `/balance?view=daily&year=2026&month=1&start=2025-01-01&end=2025-12-31`
2. Observar datos mostrados

**Resultado esperado:**
- ✅ Tabla muestra **solo enero 2026** (ignora start/end)
- ✅ Selects: Año=2026, Mes=Enero
- ✅ URL mantiene todos los params (pero year/month toman prioridad)

**SQL Query esperado:**
```sql
WHERE datetime >= '2026-01-01 00:00:00' 
  AND datetime < '2026-02-01 00:00:00'
```

---

### ✅ **Test 3.2: Sin year/month, con start/end**
**Objetivo:** Verificar que start/end funcionan si no hay year/month.

**Pasos:**
1. URL: `/balance?view=daily&start=2026-01-15&end=2026-01-20`
2. Observar datos

**Resultado esperado:**
- ✅ Tabla muestra días del 15 al 20 de enero 2026
- ⚠️ **IMPORTANTE:** Como no hay year/month, el comportamiento actual es que el blueprint intenta construir year/month desde los defaults, lo que podría sobrescribir start/end.
- **Decisión de diseño:** En daily view, preferir year/month sobre start/end. Si se desea un rango custom, usar monthly o yearly view.

**Nota para documentación:** Daily view ahora está orientado a year/month. Para rangos custom de días, considerar agregar una opción adicional o usar filtros en monthly view.

---

### ✅ **Test 3.3: Sin filtros en daily**
**Objetivo:** Verificar defaults.

**Pasos:**
1. URL: `/balance?view=daily`

**Resultado esperado:**
- ✅ Usa mes actual (si hay datos) o último mes con datos
- ✅ Selects precargados

---

## **4. Queries SQL Eficientes**

### ✅ **Test 4.1: Verificar query SQL**
**Objetivo:** Asegurar que el filtrado se hace a nivel SQL, no en Python.

**Método:** Revisar logs de SQL o usar herramienta de profiling.

**Query esperado para daily, enero 2026:**
```sql
SELECT 
    date_trunc('day', finance_ledger.datetime) AS period,
    SUM(CASE WHEN finance_ledger.type = 'INCOME' THEN finance_ledger.amount ELSE 0 END) AS income,
    SUM(CASE WHEN finance_ledger.type = 'EXPENSE' THEN finance_ledger.amount ELSE 0 END) AS expense
FROM finance_ledger
WHERE finance_ledger.datetime >= '2026-01-01 00:00:00'
  AND finance_ledger.datetime < '2026-02-01 00:00:00'
GROUP BY date_trunc('day', finance_ledger.datetime)
ORDER BY period ASC;
```

**Verificaciones:**
- ✅ `date_trunc('day', ...)` se usa correctamente
- ✅ `WHERE` con rango de fechas calculado desde year/month
- ✅ `GROUP BY` por día
- ✅ Agregación `SUM` + `CASE` para income/expense
- ✅ No hay fetch de todos los registros en Python seguido de filtrado

---

### ✅ **Test 4.2: Performance con grandes volúmenes**
**Objetivo:** Verificar que la query es rápida incluso con muchos registros.

**Método (opcional):**
1. Insertar ~10,000 registros en `finance_ledger` (script de carga)
2. Filtrar por un mes específico
3. Medir tiempo de respuesta

**Resultado esperado:**
- ✅ Respuesta < 500ms (idealmente < 200ms)
- ✅ Query usa índices en `finance_ledger.datetime`

**SQL para verificar índices:**
```sql
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'finance_ledger';
```

**Índice esperado:**
```sql
CREATE INDEX idx_ledger_datetime ON finance_ledger(datetime DESC);
```

---

## **5. Años y Meses Disponibles**

### ✅ **Test 5.1: available_years desde DB**
**Objetivo:** Verificar que los años disponibles vienen desde `finance_ledger`.

**Pasos:**
1. Verificar datos en DB:
```sql
SELECT DISTINCT EXTRACT(YEAR FROM datetime) AS year 
FROM finance_ledger 
ORDER BY year DESC;
```
2. Navegar a `/balance?view=daily`
3. Inspeccionar select de Año

**Resultado esperado:**
- ✅ Select muestra solo años con datos
- ✅ Orden descendente (más reciente primero)
- Si DB vacío: select muestra año actual o "Sin datos"

---

### ✅ **Test 5.2: available_months para un año**
**Objetivo:** Verificar que los meses disponibles se obtienen correctamente.

**Implementación actual:** Meses 1-12 siempre (no filtrados por disponibilidad).

**Resultado esperado:**
- ✅ Select de Mes muestra Enero a Diciembre
- ✅ Usuario puede seleccionar cualquier mes (aunque no tenga datos)
- Si se selecciona mes sin datos → tabla vacía (comportamiento correcto)

**Mejora opcional futura:** Filtrar meses por disponibilidad (solo mostrar meses con datos en el año seleccionado).

---

## **6. Vistas Monthly y Yearly No Afectadas**

### ✅ **Test 6.1: Vista Mensual funciona igual**
**Objetivo:** Asegurar que los cambios NO rompieron monthly view.

**Pasos:**
1. Navegar a `/balance?view=monthly`
2. Verificar que muestra selects de start/end (NO year/month)
3. Aplicar filtro de rango
4. Verificar datos

**Resultado esperado:**
- ✅ Filtros start/end visibles (como antes)
- ✅ Tabla muestra balance agrupado por mes
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
- ✅ No se ve afectada por year/month params
- Sin errores

---

## **7. Persistencia de Query Params**

### ✅ **Test 7.1: Query params persisten en navegación**
**Objetivo:** Verificar que los filtros se mantienen al navegar.

**Pasos:**
1. Filtrar por Enero 2026 en daily
2. Click en tab "Mensual"
3. Volver a tab "Diario"

**Resultado esperado:**
- ✅ Al volver a Diario, mantiene Enero 2026 (si los params persisten en URL)
- ⚠️ O vuelve a defaults (si el tab limpia los params)
- **Decisión:** Los tabs actuales NO mantienen params (enlaces directos). Esto es aceptable.

---

### ✅ **Test 7.2: Compartir URL con filtros**
**Objetivo:** Verificar que se puede compartir una URL filtrada.

**Pasos:**
1. Filtrar por Marzo 2026
2. Copiar URL: `/balance?view=daily&year=2026&month=3`
3. Abrir en nueva pestaña/ventana

**Resultado esperado:**
- ✅ Carga con filtros aplicados (Marzo 2026)
- ✅ Datos correctos

---

## **8. Mensajes y UX**

### ✅ **Test 8.1: Mensaje informativo de filtro activo**
**Objetivo:** Verificar que se muestra un mensaje claro cuando hay filtros aplicados.

**Pasos:**
1. Filtrar por Febrero 2026

**Resultado esperado:**
- ✅ Alert azul visible: "Mostrando balance diario para **Febrero 2026**"
- ✅ Íconos apropiados
- ✅ Estilo claro y legible

---

### ✅ **Test 8.2: Sin datos para el mes seleccionado**
**Objetivo:** Verificar mensaje claro cuando no hay datos.

**Pasos:**
1. Seleccionar un mes sin datos

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
2. Navegar a `/balance?view=daily`

**Resultado esperado:**
- ✅ available_years = [] → Select muestra año actual o "Sin datos"
- ✅ Mensaje: "No hay datos financieros..."
- Sin crash

---

### ✅ **Test 9.2: Solo un día con datos en el mes**
**Objetivo:** Verificar que muestra correctamente si hay solo 1 día con datos.

**Pasos:**
1. Asegurar que enero 2026 tiene datos solo en el día 10
2. Filtrar por enero 2026

**Resultado esperado:**
- ✅ Tabla muestra 1 fila: "2026-01-10" con income/expense
- ✅ Totales correctos
- Sin días vacíos (el query solo retorna días con datos)

---

### ✅ **Test 9.3: Mes completo con datos todos los días**
**Objetivo:** Verificar que muestra hasta 31 filas si todos los días tienen movimientos.

**Pasos:**
1. Crear datos para todos los días de enero 2026
2. Filtrar por enero 2026

**Resultado esperado:**
- ✅ Tabla muestra 31 filas (1 por día)
- ✅ Scroll si es necesario
- ✅ Totales suman correctamente

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

### ✅ **Test 10.5: MEJORA 1, 2, 3, 4**
**Pasos:** Verificar fotos, filtros, top vendidos, unit_cost entero

**Resultado esperado:** ✅ Todas funcionales

---

## **11. Documentación de Prioridad de Filtros**

### **Prioridad Implementada (Daily View):**

1. **Si vienen `year` Y `month`:**
   - Construir `start` = `YYYY-MM-01`
   - Construir `end` = último día del mes `YYYY-MM-last_day`
   - **Ignorar** cualquier `start`/`end` que venga en query params

2. **Si NO vienen `year`/`month` pero vienen `start`/`end`:**
   - Usar `start` y `end` directamente
   - Intentar derivar `year`/`month` del `start` para precargar selects

3. **Si NO viene nada:**
   - Defaults:
     - Mes actual (si hay datos en finance_ledger)
     - Si no, último mes con datos
     - Si no hay datos, mes actual del sistema

**Rango exacto:**
```python
start = date(year, month, 1)  # Primer día del mes, 00:00:00
last_day = monthrange(year, month)[1]
end = date(year, month, last_day)  # Último día del mes, 23:59:59
```

**Query SQL WHERE:**
```sql
WHERE datetime >= 'YYYY-MM-01 00:00:00' 
  AND datetime <= 'YYYY-MM-last_day 23:59:59'
```

---

## **✅ Testing Completo: Checklist Final**

- [ ] Daily sin params → defaults cargados
- [ ] Seleccionar year/month → datos filtrados
- [ ] Cambiar mes → actualiza datos
- [ ] Cambiar año → actualiza datos
- [ ] Botón "Limpiar" → vuelve a defaults
- [ ] year inválido → warning + fallback
- [ ] month inválido → warning + fallback
- [ ] year/month tiene prioridad sobre start/end
- [ ] available_years desde DB (query SQL)
- [ ] Query SQL eficiente (date_trunc + WHERE)
- [ ] Monthly view no afectada
- [ ] Yearly view no afectada
- [ ] Query params persisten (al copiar URL)
- [ ] Mensaje informativo visible
- [ ] Sin datos → mensaje claro
- [ ] DB vacía → no crash
- [ ] Solo 1 día con datos → muestra 1 fila
- [ ] 31 días con datos → muestra 31 filas
- [ ] Regresión: Productos, Ventas, Compras, Ledger funcionan
- [ ] MEJORA 1, 2, 3, 4 funcionan

---

## **🎯 Resultado Esperado Final**

Al finalizar todos los tests:
- ✅ **Filtros year/month funcionan en daily view**
- ✅ **Queries SQL eficientes (agregación en DB)**
- ✅ **Validaciones robustas (year 1900-2100, month 1-12)**
- ✅ **Prioridad de filtros clara y documentada**
- ✅ **available_years desde DB**
- ✅ **Monthly/Yearly no afectadas**
- ✅ **UX clara con mensajes informativos**
- ✅ **Sin regresiones en funcionalidades existentes**

---

**Última actualización:** Enero 2026  
**Autor:** Sistema Ferretería - MEJORA 5
