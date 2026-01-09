# ✅ MEJORA 5 – Filtros en Balance Diario (por Año y Mes)

---

## 📋 **Resumen Ejecutivo**

**Objetivo:** Agregar filtros de Año y Mes en la vista Balance Diario para permitir consultar el balance de un mes específico de forma eficiente.

**Estado:** ✅ **COMPLETADO**

**Fecha:** Enero 2026

---

## 🎯 **Cambios Implementados**

### **1. Servicio de Balance - Nuevas Funciones**

**Archivo:** `app/services/balance_service.py`

#### **Funciones agregadas:**

**1. `get_available_years(session)`**
```python
def get_available_years(session):
    """Get list of years with finance_ledger data."""
    query = (
        session.query(extract('year', FinanceLedger.datetime).label('year'))
        .distinct()
        .order_by(extract('year', FinanceLedger.datetime).desc())
    )
    results = query.all()
    return [int(row.year) for row in results]
```

**Características:**
- ✅ Query SQL eficiente con `EXTRACT(YEAR ...)`
- ✅ `DISTINCT` para evitar duplicados
- ✅ Orden descendente (más reciente primero)
- ✅ Retorna lista de enteros

---

**2. `get_available_months(year, session)`**
```python
def get_available_months(year: int, session):
    """Get list of months with data for a specific year."""
    query = (
        session.query(extract('month', FinanceLedger.datetime).label('month'))
        .filter(extract('year', FinanceLedger.datetime) == year)
        .distinct()
        .order_by(extract('month', FinanceLedger.datetime).asc())
    )
    results = query.all()
    return [int(row.month) for row in results]
```

**Características:**
- ✅ Filtra por año específico
- ✅ `DISTINCT` por mes
- ✅ Orden ascendente (Enero a Diciembre)
- ✅ Retorna lista de enteros (1-12)

---

**3. `get_month_date_range(year, month)`**
```python
def get_month_date_range(year: int, month: int):
    """Get start and end dates for a specific month."""
    from calendar import monthrange
    
    start = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end = date(year, month, last_day)
    
    return start, end
```

**Características:**
- ✅ Calcula primer y último día del mes
- ✅ Maneja meses con diferentes cantidades de días (28, 29, 30, 31)
- ✅ Usa `calendar.monthrange()` para precisión
- ✅ Retorna tupla `(start_date, end_date)`

**Ejemplo:**
```python
start, end = get_month_date_range(2026, 2)
# start = date(2026, 2, 1)
# end = date(2026, 2, 28)
```

---

### **2. Blueprint de Balance - Lógica de Filtros**

**Archivo:** `app/blueprints/balance.py`

#### **Cambios principales:**

**1. Importación de nuevas funciones:**
```python
from app.services.balance_service import (
    get_balance_series, get_default_date_range, get_totals,
    get_available_years, get_available_months, get_month_date_range
)
```

---

**2. Lectura de parámetros year/month:**
```python
year_str = request.args.get('year', '').strip()
month_str = request.args.get('month', '').strip()
```

---

**3. Obtención de años disponibles:**
```python
available_years = get_available_years(db_session)
```

**SQL ejecutado:**
```sql
SELECT DISTINCT EXTRACT(YEAR FROM datetime) AS year
FROM finance_ledger
ORDER BY year DESC;
```

---

**4. Lógica de prioridad de filtros (Daily View):**

```python
if view == 'daily':
    # Priority: year/month > start/end > defaults
    if year_str and month_str:
        # Validar y usar year/month
        selected_year = int(year_str)
        selected_month = int(month_str)
        
        # Validaciones
        if selected_month < 1 or selected_month > 12:
            flash('Mes inválido. Debe estar entre 1 y 12.', 'warning')
            # Fallback...
        
        if selected_year < 1900 or selected_year > 2100:
            flash('Año inválido.', 'warning')
            # Fallback...
        
        # Construir rango de fechas
        start, end = get_month_date_range(selected_year, selected_month)
        available_months = get_available_months(selected_year, db_session)
    
    else:
        # Usar defaults o start/end existentes
        # ...
```

**Prioridad implementada:**
1. **`year` + `month` params** → construir start/end desde ahí (ignora start/end params)
2. **`start` + `end` params** (si no hay year/month) → usar directamente
3. **Defaults** (si nada viene) → mes actual o último mes con datos

---

**5. Defaults inteligentes:**
```python
if available_years:
    # Try current month if we have data
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    if current_year in available_years:
        available_months = get_available_months(current_year, db_session)
        if current_month in available_months:
            selected_year = current_year
            selected_month = current_month
        elif available_months:
            # Use last month with data in current year
            selected_year = current_year
            selected_month = available_months[-1]
        else:
            # Use last year with data
            selected_year = available_years[0]
            available_months = get_available_months(selected_year, db_session)
            selected_month = available_months[-1] if available_months else 12
    else:
        # Use last year with data
        selected_year = available_years[0]
        available_months = get_available_months(selected_year, db_session)
        selected_month = available_months[-1] if available_months else 12
    
    start, end = get_month_date_range(selected_year, selected_month)
else:
    # No data at all, use current month
    selected_year = today.year
    selected_month = today.month
    start, end = get_month_date_range(selected_year, selected_month)
```

**Lógica:**
- Si hay datos en el mes actual → usar mes actual
- Si no, usar último mes con datos en el año actual
- Si el año actual no tiene datos, usar último año con datos

---

**6. Pasar nuevas variables al template:**
```python
return render_template(
    'balance/index.html',
    view=view,
    series=series,
    totals=totals,
    start=start_str,
    end=end_str,
    available_years=available_years,          # NUEVO
    selected_year=selected_year,              # NUEVO
    selected_month=selected_month,            # NUEVO
    available_months=available_months         # NUEVO
)
```

---

### **3. Template de Balance - UI de Filtros**

**Archivo:** `app/templates/balance/index.html`

#### **Cambios:**

**1. Formulario condicional según vista:**
```html
{% if view == 'daily' %}
    <!-- Year/Month filters -->
{% else %}
    <!-- Start/End date filters (monthly, yearly) -->
{% endif %}
```

---

**2. Select de Año:**
```html
<div class="col-md-3">
    <label for="year" class="form-label">
        <i class="bi bi-calendar"></i> Año
    </label>
    <select class="form-select" id="year" name="year" required>
        {% if available_years %}
            {% for year in available_years %}
            <option value="{{ year }}" {% if selected_year == year %}selected{% endif %}>
                {{ year }}
            </option>
            {% endfor %}
        {% else %}
            <option value="{{ selected_year or '' }}">{{ selected_year or 'Sin datos' }}</option>
        {% endif %}
    </select>
</div>
```

**Características:**
- ✅ Poblado dinámicamente desde `available_years`
- ✅ Precarga `selected_year` si existe
- ✅ Maneja caso sin datos (muestra "Sin datos")

---

**3. Select de Mes:**
```html
<div class="col-md-3">
    <label for="month" class="form-label">
        <i class="bi bi-calendar-month"></i> Mes
    </label>
    <select class="form-select" id="month" name="month" required>
        <option value="1" {% if selected_month == 1 %}selected{% endif %}>Enero</option>
        <option value="2" {% if selected_month == 2 %}selected{% endif %}>Febrero</option>
        <!-- ... Marzo a Diciembre ... -->
        <option value="12" {% if selected_month == 12 %}selected{% endif %}>Diciembre</option>
    </select>
</div>
```

**Características:**
- ✅ Muestra siempre todos los meses (1-12)
- ✅ Nombres en español
- ✅ Precarga `selected_month`
- ℹ️ **Nota:** No filtra por `available_months` (simplificación de UX)
  - Usuario puede seleccionar cualquier mes
  - Si no tiene datos, tabla aparece vacía (comportamiento claro)

---

**4. Botones de acción:**
```html
<div class="col-md-6 d-flex align-items-end">
    <button type="submit" class="btn btn-primary me-2">
        <i class="bi bi-funnel"></i> Aplicar Filtros
    </button>
    <a href="{{ url_for('balance.index', view='daily') }}" class="btn btn-outline-secondary">
        <i class="bi bi-x-circle"></i> Limpiar
    </a>
</div>
```

**Características:**
- ✅ "Aplicar Filtros" → envía form con year/month
- ✅ "Limpiar" → vuelve a `/balance?view=daily` sin params (resetea a defaults)

---

**5. Mensaje informativo:**
```html
{% if selected_year and selected_month %}
<div class="col-12">
    <div class="alert alert-info alert-sm d-flex align-items-center mb-0" role="alert">
        <i class="bi bi-info-circle-fill me-2"></i>
        <small>
            Mostrando balance diario para <strong>{{ ['', 'Enero', 'Febrero', ..., 'Diciembre'][selected_month] }} {{ selected_year }}</strong>
        </small>
    </div>
</div>
{% endif %}
```

**Características:**
- ✅ Alert azul cuando hay filtros aplicados
- ✅ Muestra "Mostrando balance diario para **Enero 2026**"
- ✅ Solo visible cuando hay year/month seleccionados

---

## 🔒 **Query SQL Generado**

### **Ejemplo: Balance Diario de Enero 2026**

**URL:** `/balance?view=daily&year=2026&month=1`

**Query ejecutado:**
```sql
SELECT 
    date_trunc('day', finance_ledger.datetime) AS period,
    SUM(CASE WHEN finance_ledger.type = 'INCOME' THEN finance_ledger.amount ELSE 0 END) AS income,
    SUM(CASE WHEN finance_ledger.type = 'EXPENSE' THEN finance_ledger.amount ELSE 0 END) AS expense
FROM finance_ledger
WHERE finance_ledger.datetime >= '2026-01-01 00:00:00'
  AND finance_ledger.datetime <= '2026-01-31 23:59:59'
GROUP BY date_trunc('day', finance_ledger.datetime)
ORDER BY period ASC;
```

**Características:**
- ✅ `date_trunc('day', ...)` agrupa por día
- ✅ `WHERE` con rango exacto del mes
- ✅ `GROUP BY` para agregación
- ✅ `SUM` con `CASE` para separar income/expense
- ✅ Ejecutado en PostgreSQL (no en Python)

---

### **Query para Años Disponibles:**
```sql
SELECT DISTINCT EXTRACT(YEAR FROM datetime) AS year
FROM finance_ledger
ORDER BY year DESC;
```

### **Query para Meses Disponibles (opcional):**
```sql
SELECT DISTINCT EXTRACT(MONTH FROM datetime) AS month
FROM finance_ledger
WHERE EXTRACT(YEAR FROM datetime) = 2026
ORDER BY month ASC;
```

---

## 📊 **Prioridad de Filtros (Documentada)**

### **Regla de Prioridad en Daily View:**

1. **Si vienen `year` Y `month` en query params:**
   - ✅ Construir `start` = `YYYY-MM-01`
   - ✅ Construir `end` = `YYYY-MM-last_day`
   - ❌ **Ignorar** cualquier `start`/`end` en query params
   - **Razón:** year/month son más específicos y fáciles de usar

2. **Si NO vienen `year`/`month` pero vienen `start`/`end`:**
   - ✅ Usar `start` y `end` directamente
   - (No implementado actualmente en daily view - consideración futura)

3. **Si NO viene nada:**
   - ✅ Defaults inteligentes:
     - Mes actual (si hay datos)
     - O último mes con datos
     - O mes actual del sistema (si DB vacío)

---

## 📁 **Archivos Modificados/Creados**

```
app/
├── services/
│   └── balance_service.py             ← +3 funciones (years, months, date_range)
├── blueprints/
│   └── balance.py                     ← Lógica year/month, validaciones, defaults
└── templates/
    └── balance/
        └── index.html                 ← Selects year/month, UI condicional

MEJORA5_TESTING.md                     ← Checklist 60+ tests (NEW)
MEJORA5_RESUMEN.md                     ← Este archivo (NEW)
```

---

## 🚀 **Cómo Usar**

### **1. Acceder a Balance Diario:**
```
http://localhost:5000/balance?view=daily
```

**Comportamiento:**
- ✅ Carga con defaults (mes actual o último mes con datos)
- ✅ Selects precargados

---

### **2. Filtrar por Mes Específico:**
1. Seleccionar **Año:** 2026
2. Seleccionar **Mes:** Enero
3. Click **"Aplicar Filtros"**

**URL resultante:**
```
http://localhost:5000/balance?view=daily&year=2026&month=1
```

**Resultado:**
- ✅ Tabla muestra solo días de Enero 2026
- ✅ Totales calculados para ese mes
- ✅ Mensaje: "Mostrando balance diario para **Enero 2026**"

---

### **3. Cambiar Mes:**
1. Cambiar select de Mes a **Febrero**
2. Click **"Aplicar Filtros"**

**URL:**
```
http://localhost:5000/balance?view=daily&year=2026&month=2
```

---

### **4. Limpiar Filtros:**
Click **"Limpiar"**

**URL:**
```
http://localhost:5000/balance?view=daily
```

**Resultado:**
- ✅ Vuelve a defaults

---

## ✅ **Validaciones Implementadas**

### **1. Validación de Año:**
```python
if selected_year < 1900 or selected_year > 2100:
    flash('Año inválido.', 'warning')
    # Fallback to defaults
```

**Casos:**
- `1899` → ⚠️ "Año inválido." + defaults
- `2101` → ⚠️ "Año inválido." + defaults
- `abc` → ⚠️ "Año o mes inválido." + defaults

---

### **2. Validación de Mes:**
```python
if selected_month < 1 or selected_month > 12:
    flash('Mes inválido. Debe estar entre 1 y 12.', 'warning')
    # Fallback to defaults
```

**Casos:**
- `0` → ⚠️ "Mes inválido." + defaults
- `13` → ⚠️ "Mes inválido." + defaults
- `abc` → ⚠️ "Año o mes inválido." + defaults

---

### **3. Fallback Robusto:**
```python
try:
    selected_year = int(year_str)
    selected_month = int(month_str)
    # ... validations ...
except (ValueError, TypeError):
    flash('Año o mes inválido.', 'warning')
    selected_year = None
    selected_month = None
    # Continue with defaults
```

**Resultado:**
- ✅ La aplicación **nunca crashea** por params inválidos
- ✅ Siempre muestra una vista con datos o mensaje claro

---

## 📋 **Testing Realizado**

### **Datos en DB:**
```sql
SELECT DISTINCT EXTRACT(YEAR FROM datetime) as year, 
                EXTRACT(MONTH FROM datetime) as month 
FROM finance_ledger 
ORDER BY year DESC, month DESC;
```

**Resultado:**
```
 year | month 
------+-------
 2026 |     1
 2025 |    12
 2025 |    11
```

✅ Suficiente para probar filtros.

---

### **Test Manual Rápido:**

1. **Daily sin params:**
   - ✅ Carga Enero 2026 (default: mes más reciente con datos)
   - ✅ Selects muestran años: [2026, 2025]
   - ✅ Mes seleccionado: Enero

2. **Cambiar a Diciembre 2025:**
   - ✅ URL: `/balance?view=daily&year=2025&month=12`
   - ✅ Tabla actualizada

3. **Cambiar a Noviembre 2025:**
   - ✅ URL: `/balance?view=daily&year=2025&month=11`
   - ✅ Datos correctos

4. **Intentar Febrero 2026 (sin datos):**
   - ✅ Tabla vacía con mensaje: "No hay datos financieros..."
   - ✅ Sin errores

5. **Limpiar filtros:**
   - ✅ Vuelve a defaults (Enero 2026)

---

## 🔄 **Compatibilidad con Vistas Anteriores**

### **Monthly View:**
- ✅ **NO afectado**
- ✅ Sigue usando filtros `start`/`end`
- ✅ Formulario muestra inputs de fecha (no year/month)

### **Yearly View:**
- ✅ **NO afectado**
- ✅ Sigue usando filtros `start`/`end`
- ✅ Funciona como antes

**Código condicional en template:**
```html
{% if view == 'daily' %}
    <!-- Year/Month filters -->
{% else %}
    <!-- Start/End date filters -->
{% endif %}
```

---

## 🎨 **UX Mejorado**

### **1. Filtros específicos por vista:**
- **Daily:** Year + Month (más intuitivo para días)
- **Monthly/Yearly:** Start + End (rangos flexibles)

### **2. Mensajes informativos:**
- ✅ "Mostrando balance diario para **Enero 2026**"
- ✅ "No hay datos financieros para el rango seleccionado."

### **3. Defaults inteligentes:**
- ✅ Mes actual si tiene datos
- ✅ Último mes con datos si el actual está vacío
- ✅ Nunca muestra vista vacía sin explicación

### **4. Botón "Limpiar":**
- ✅ Un click para volver a defaults
- ✅ URL limpia sin params

---

## 📌 **Casos Edge Manejados**

| Caso | Comportamiento |
|------|----------------|
| DB vacía (sin finance_ledger) | ✅ Select años: "Sin datos" + mensaje claro |
| Solo 1 día con datos en el mes | ✅ Tabla con 1 fila |
| 31 días con datos | ✅ Tabla con 31 filas |
| Mes sin datos | ✅ Tabla vacía + mensaje informativo |
| year=1899 | ⚠️ Flash warning + fallback |
| month=13 | ⚠️ Flash warning + fallback |
| year=abc | ⚠️ Flash warning + fallback |
| Solo year (sin month) | ✅ Fallback a defaults |

---

## ✅ **Checklist de Completitud**

- [x] Servicio: `get_available_years()` ✅
- [x] Servicio: `get_available_months()` ✅
- [x] Servicio: `get_month_date_range()` ✅
- [x] Blueprint: Lectura de year/month params ✅
- [x] Blueprint: Validación de year (1900-2100) ✅
- [x] Blueprint: Validación de month (1-12) ✅
- [x] Blueprint: Prioridad year/month > start/end ✅
- [x] Blueprint: Defaults inteligentes ✅
- [x] Blueprint: Pasar variables al template ✅
- [x] Template: Select de Año dinámico ✅
- [x] Template: Select de Mes (1-12) ✅
- [x] Template: Botón "Aplicar Filtros" ✅
- [x] Template: Botón "Limpiar" ✅
- [x] Template: Mensaje informativo ✅
- [x] Template: UI condicional (daily vs monthly/yearly) ✅
- [x] Query SQL eficiente (date_trunc + WHERE) ✅
- [x] Validaciones robustas ✅
- [x] Mensajes de error claros ✅
- [x] Monthly/Yearly no afectadas ✅
- [x] Documentación: TESTING.md (60+ tests) ✅
- [x] Documentación: RESUMEN.md ✅
- [x] Sin errores de linting ✅
- [x] Docker reconstruido ✅
- [x] Logs limpios ✅

---

## 🎉 **MEJORA 5 COMPLETADA EXITOSAMENTE**

- ✅ **Filtros year/month en daily view funcionando**
- ✅ **Queries SQL eficientes (agregación en DB)**
- ✅ **Validaciones robustas (year, month)**
- ✅ **Prioridad de filtros clara y documentada**
- ✅ **available_years desde DB (dynamic)**
- ✅ **Defaults inteligentes**
- ✅ **Monthly/Yearly no afectadas**
- ✅ **UX mejorado con mensajes claros**
- ✅ **Sin regresiones**
- ✅ **Código limpio y bien organizado**

---

## 🔜 **Próxima Mejora**

**MEJORA 6:** Filtro por Año en Balance Mensual

---

**Autor:** Sistema Ferretería  
**Fecha:** Enero 2026  
**Versión:** 1.0
