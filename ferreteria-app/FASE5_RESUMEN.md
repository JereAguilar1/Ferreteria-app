# FASE 5 - RESUMEN EJECUTIVO
## Balance Financiero (Diario / Mensual / Anual)

---

## ✅ Completado

La **Fase 5** está **100% implementada y funcional**. Se ha desarrollado el módulo completo de balance financiero con reportes dinámicos, libro mayor y movimientos manuales.

---

## 📦 Componentes Implementados

### 1. **Servicio de Balance `balance_service.py`**

#### `get_balance_series(view, start, end, session)`
Consulta eficiente con agregación en base de datos:

```python
# Usa date_trunc para agrupar por período
period = date_trunc('day'|'month'|'year', datetime)

# Suma condicional para ingresos y egresos
income = SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END)
expense = SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END)

# Calcula neto
net = income - expense
```

**Características:**
- ✅ Agregación en DB (no en Python)
- ✅ Filtrado por rango de fechas
- ✅ Soporte para 3 granularidades (día, mes, año)
- ✅ Retorna serie ordenada por período

#### `get_default_date_range(view)`
Rangos por defecto según vista:
- **Diario:** Últimos 30 días
- **Mensual:** Últimos 12 meses
- **Anual:** Últimos 5 años

#### `get_totals(series)`
Calcula totales de una serie:
- total_income
- total_expense
- total_net

**Ubicación:** `app/services/balance_service.py`

---

### 2. **Blueprint Balance**

#### Rutas Principales:

**`GET /balance`**
- Vista principal con tabs (diario/mensual/anual)
- Query params: `view`, `start`, `end`
- Validaciones de fechas
- Renderiza tabla con períodos y totales

**`GET /balance/ledger`**
- Listado completo de finance_ledger
- Filtros: tipo (INCOME/EXPENSE), fechas
- Ordenado por datetime desc
- Para auditoría

**`GET /balance/ledger/new`**
- Formulario para movimiento manual

**`POST /balance/ledger/new`**
- Crea movimiento manual
- Validaciones: tipo válido, amount > 0
- reference_type = MANUAL
- reference_id = NULL

**Ubicación:** `app/blueprints/balance.py`

---

### 3. **Templates UI**

#### `balance/index.html`
- **Tabs:** Diario, Mensual, Anual
- **Filtros:** Fecha inicio, fecha fin, botón aplicar
- **Tarjetas de resumen:**
  - Ingresos Totales (verde)
  - Egresos Totales (rojo)
  - Neto (azul/amarillo según signo)
- **Tabla de balance:**
  - Período
  - Ingresos
  - Egresos
  - Neto
  - Fila de TOTALES
- **Botón:** Ver Libro Mayor

#### `balance/ledger_list.html`
- Tabla con todos los asientos
- Columnas: ID, Fecha/Hora, Tipo, Monto, Origen, Ref ID, Categoría, Notas
- Filtros: Tipo, Fechas
- Badges de colores para tipo y origen
- Botón: Movimiento Manual

#### `balance/ledger_form.html`
- Formulario para crear movimiento manual
- Campos:
  - Tipo (INCOME/EXPENSE) *
  - Monto *
  - Fecha/Hora (default: ahora)
  - Categoría (opcional)
  - Notas (opcional)
- Validación HTML5
- Card de ayuda

**Ubicación:** `app/templates/balance/`

---

## 🔑 Características Clave

### ✅ Consultas Eficientes con `date_trunc`
- Agregación en PostgreSQL (no en Python)
- Uso de `CASE WHEN` para sumas condicionales
- Filtrado por rango de fechas con timestamps
- Ordenamiento por período

### ✅ Tres Vistas Dinámicas
- **Diaria:** Períodos YYYY-MM-DD
- **Mensual:** Períodos YYYY-MM
- **Anual:** Períodos YYYY

### ✅ Filtros Flexibles
- Rango de fechas personalizado
- Validación: start <= end
- Fallback a defaults si fechas inválidas

### ✅ Tarjetas de Resumen
- Ingresos totales del rango
- Egresos totales del rango
- Neto (ingresos - egresos)
- Colores dinámicos según valores

### ✅ Libro Mayor Completo
- Todos los asientos de finance_ledger
- Filtros por tipo y fechas
- Origen identificado (Venta/Pago Boleta/Manual)
- Ordenado por fecha descendente

### ✅ Movimientos Manuales
- Crear INCOME o EXPENSE manual
- Categoría y notas opcionales
- Fecha/hora personalizable
- Validación amount > 0
- NO afectan stock (solo finanzas)

---

## 📊 Flujo Completo

```
Usuario → Balance
  ↓
Selecciona Vista (Diario/Mensual/Anual)
  ↓
Opcionalmente ajusta filtros (start/end)
  ↓
Servicio: get_balance_series()
  ↓
Query DB con date_trunc + agregación:
  - Agrupa por período
  - Suma INCOME
  - Suma EXPENSE
  - Calcula neto
  ↓
Renderiza:
  - Tarjetas de resumen
  - Tabla de períodos
  - Totales
  ↓
Usuario puede:
  - Ver Libro Mayor (auditoría)
  - Crear movimiento manual
```

---

## 🧪 Testing

### Documento de Pruebas
Ver **[FASE5_TESTING.md](FASE5_TESTING.md)** para:
- 16 casos de prueba detallados
- Queries de verificación SQL
- Checklist de aceptación
- Verificación de consistencia
- Debugging queries

### Casos Críticos Probados:
1. ✅ Balance mensual con datos correctos
2. ✅ Balance diario últimos 30 días
3. ✅ Balance anual últimos 5 años
4. ✅ Filtros de rango de fechas
5. ✅ Validación start > end
6. ✅ Balance sin datos (rango vacío)
7. ✅ Libro Mayor completo
8. ✅ Filtros de Libro Mayor
9. ✅ Crear movimiento manual INCOME
10. ✅ Crear movimiento manual EXPENSE
11. ✅ Validación amount <= 0
12. ✅ Movimientos manuales en balance
13. ✅ Integración con ventas
14. ✅ Integración con pagos de boletas
15. ✅ Consistencia de totales
16. ✅ Verificación de períodos

---

## 📁 Archivos Creados/Modificados

### Nuevos:
```
app/services/balance_service.py
app/blueprints/balance.py
app/templates/balance/index.html
app/templates/balance/ledger_list.html
app/templates/balance/ledger_form.html
FASE5_TESTING.md
FASE5_RESUMEN.md
```

### Modificados:
```
app/__init__.py
  - Registrar balance_bp

app/templates/base.html
  - Agregar link "Balance" en menú

README.md
  - Agregar Fase 5 completada
```

---

## 🚀 Comandos para Ejecutar

### 1. Iniciar Base de Datos:
```bash
cd c:\jere\Ferreteria\Ferreteria-db
docker-compose up -d
```

### 2. Iniciar Aplicación:
```bash
cd c:\jere\Ferreteria\ferreteria-app
python app.py
```

### 3. Acceder:
```
http://127.0.0.1:5000
```

### 4. Navegar a Balance:
- Click en **"Balance"** en el menú superior
- O ir directamente a: `http://127.0.0.1:5000/balance`

### 5. Probar Funcionalidades:

**Balance Mensual:**
```
http://127.0.0.1:5000/balance?view=monthly
```

**Balance Diario:**
```
http://127.0.0.1:5000/balance?view=daily
```

**Libro Mayor:**
```
http://127.0.0.1:5000/balance/ledger
```

**Movimiento Manual:**
```
http://127.0.0.1:5000/balance/ledger/new
```

---

## ✅ Criterios de Aceptación (CUMPLIDOS)

- [x] Balance diario, mensual y anual funcionan
- [x] Consultas usan `date_trunc` (eficientes)
- [x] Filtros por rango de fechas funcionan
- [x] Validación start <= end
- [x] Tarjetas de resumen muestran totales correctos
- [x] Tabla de períodos con ingresos, egresos, neto
- [x] Totales de tabla coinciden con tarjetas
- [x] Totales coinciden con SUM en DB
- [x] Libro Mayor muestra todos los asientos
- [x] Filtros de Libro Mayor funcionan
- [x] Crear movimiento manual INCOME funciona
- [x] Crear movimiento manual EXPENSE funciona
- [x] Validación amount > 0
- [x] Movimientos manuales aparecen en balance
- [x] Integración con ventas (INCOME automático)
- [x] Integración con pagos (EXPENSE automático)
- [x] UI responsive con Bootstrap

---

## 🔍 Verificación de Consistencia

### Query de Verificación (Totales):
```sql
-- Totales en finance_ledger
SELECT 
    type,
    COUNT(*) AS num_entries,
    SUM(amount) AS total
FROM finance_ledger
GROUP BY type;

-- Debe coincidir con tarjetas de resumen en Balance
```

### Query de Verificación (Consistencia Ventas):
```sql
-- Total de ventas confirmadas
SELECT SUM(total_amount) FROM sale WHERE status = 'CONFIRMED';

-- Total de ingresos de ventas en ledger
SELECT SUM(amount) FROM finance_ledger 
WHERE type = 'INCOME' AND reference_type = 'SALE';

-- Deben ser iguales
```

### Query de Verificación (Consistencia Pagos):
```sql
-- Total de boletas pagadas
SELECT SUM(total_amount) FROM purchase_invoice WHERE status = 'PAID';

-- Total de egresos de pagos en ledger
SELECT SUM(amount) FROM finance_ledger 
WHERE type = 'EXPENSE' AND reference_type = 'INVOICE_PAYMENT';

-- Deben ser iguales
```

---

## 🎯 Próximo Paso: FASE 6

En la **Fase 6** se implementará:
- **Dockerfile** para la aplicación Flask
- **docker-compose.yml** completo (app + postgres)
- Variables de entorno en Docker
- Volúmenes para persistencia de datos
- Redes Docker para comunicación
- README actualizado con instrucciones Docker
- Scripts de inicialización (seeds)

---

## 📝 Notas Técnicas

1. **date_trunc:** Función de PostgreSQL que trunca timestamp a la granularidad especificada (day, month, year).

2. **Agregación en DB:** Las sumas se hacen en PostgreSQL, no en Python. Esto es mucho más eficiente.

3. **CASE WHEN:** Permite sumar condicionalmente (solo INCOME o solo EXPENSE).

4. **Movimientos manuales:** Tienen `reference_type=MANUAL` y `reference_id=NULL`.

5. **Períodos vacíos:** Si no hay datos para un período, no aparece en la tabla. Esto es normal.

6. **Filtros de fecha:** Son inclusivos (start y end incluidos en el rango).

7. **Timestamps:** Se convierten correctamente para comparación (start a 00:00:00, end a 23:59:59).

8. **Colores dinámicos:** Neto positivo (azul), neto negativo (amarillo).

---

**Estado:** ✅ **FASE 5 COMPLETADA**  
**Fecha:** Enero 2026  
**Próximo:** Fase 6 - Dockerización Completa

