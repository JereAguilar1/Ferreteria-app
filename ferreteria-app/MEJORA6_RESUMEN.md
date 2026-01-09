# ✅ MEJORA 6 – Filtro por Año en Balance Mensual

---

## 📋 **Resumen Ejecutivo**

**Objetivo:** Agregar filtro de Año en la vista Balance Mensual para consultar solo los meses de un año específico de forma eficiente.

**Estado:** ✅ **COMPLETADO**

**Fecha:** Enero 2026

---

## 🎯 **Cambios Implementados**

### **1. Servicio de Balance - Nueva Función**

**Archivo:** `app/services/balance_service.py`

#### **Función agregada:**

**`get_year_date_range(year)`**
```python
def get_year_date_range(year: int):
    """
    Get start and end dates for a specific year.
    
    Args:
        year: Year (int)
        
    Returns:
        Tuple of (start_date, end_date)
        start_date: First day of year (Jan 1)
        end_date: Last day of year (Dec 31)
    """
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    
    return start, end
```

**Características:**
- ✅ Calcula primer día del año (`YYYY-01-01`)
- ✅ Calcula último día del año (`YYYY-12-31`)
- ✅ Retorna tupla `(start_date, end_date)`

**Ejemplo:**
```python
start, end = get_year_date_range(2026)
# start = date(2026, 1, 1)
# end = date(2026, 12, 31)
```

---

### **2. Blueprint de Balance - Lógica de Filtros**

**Archivo:** `app/blueprints/balance.py`

#### **Cambios principales:**

**1. Importación de nueva función:**
```python
from app.services.balance_service import (
    get_balance_series, get_default_date_range, get_totals,
    get_available_years, get_available_months, get_month_date_range,
    get_year_date_range  # NUEVO
)
```

---

**2. Lógica de prioridad de filtros (Monthly View):**

```python
elif view == 'monthly':
    # MEJORA 6: Handle year filter for monthly view
    if year_str:
        try:
            selected_year = int(year_str)
            
            # Validate year is reasonable (1900-2100)
            if selected_year < 1900 or selected_year > 2100:
                flash('Año inválido.', 'warning')
                selected_year = None
            
            # If valid, get date range from year
            if selected_year:
                start, end = get_year_date_range(selected_year)
                
        except (ValueError, TypeError):
            flash('Año inválido.', 'warning')
            selected_year = None
    
    # If no year or it was invalid, try start/end or defaults
    if not selected_year:
        if start_str and end_str:
            # Use start/end (legacy)
            start = ...
            end = ...
        else:
            # Use defaults: current year or last year with data
            today = date.today()
            if available_years:
                current_year = today.year
                
                if current_year in available_years:
                    selected_year = current_year
                else:
                    selected_year = available_years[0]
                
                start, end = get_year_date_range(selected_year)
            else:
                # No data at all, use current year
                selected_year = today.year
                start, end = get_year_date_range(selected_year)
```

**Prioridad implementada:**
1. **`year` param** → construir start/end desde año (ignora start/end params)
2. **`start` + `end` params** (si no hay year) → usar directamente (legacy)
3. **Defaults** (si nada viene) → año actual o último año con datos

---

**3. Defaults inteligentes:**
```python
if available_years:
    # Try current year if we have data
    today = date.today()
    current_year = today.year
    
    if current_year in available_years:
        selected_year = current_year
    else:
        # Use last year with data
        selected_year = available_years[0]
    
    start, end = get_year_date_range(selected_year)
else:
    # No data at all, use current year
    selected_year = today.year
    start, end = get_year_date_range(selected_year)
```

**Lógica:**
- Si hay datos en el año actual → usar año actual
- Si no, usar último año con datos
- Si DB vacía, usar año actual del sistema

---

### **3. Template de Balance - UI de Filtros**

**Archivo:** `app/templates/balance/index.html`

#### **Cambios:**

**1. Formulario condicional para monthly:**
```html
{% elif view == 'monthly' %}
    <!-- MEJORA 6: Monthly view with Year filter -->
    <form method="GET" action="{{ url_for('balance.index') }}" class="row g-3">
        <input type="hidden" name="view" value="monthly">
        
        <div class="col-md-4">
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
        
        <div class="col-md-8 d-flex align-items-end">
            <button type="submit" class="btn btn-primary me-2">
                <i class="bi bi-funnel"></i> Aplicar Filtro
            </button>
            <a href="{{ url_for('balance.index', view='monthly') }}" class="btn btn-outline-secondary">
                <i class="bi bi-x-circle"></i> Limpiar
            </a>
        </div>
        
        {% if selected_year %}
        <div class="col-12">
            <div class="alert alert-info alert-sm d-flex align-items-center mb-0" role="alert">
                <i class="bi bi-info-circle-fill me-2"></i>
                <small>
                    Mostrando balance mensual para el año <strong>{{ selected_year }}</strong>
                </small>
            </div>
        </div>
        {% endif %}
    </form>
{% else %}
    <!-- Yearly view with date range filters (unchanged) -->
{% endif %}
```

**Características:**
- ✅ **Select de Año:** Poblado dinámicamente desde `available_years`
- ✅ **Precarga:** `selected_year` si existe
- ✅ **Botón "Aplicar Filtro":** Envía form con year
- ✅ **Botón "Limpiar":** Resetea a defaults (sin params)
- ✅ **Mensaje informativo:** "Mostrando balance mensual para el año **2026**"

**Screenshot de filtros (Monthly):**
```
┌─────────────────────────────────────────────┐
│ 📅 Año        │ Acciones                    │
├───────────────┼─────────────────────────────┤
│ [2026 ▼]     │ [Aplicar Filtro] [Limpiar]  │
└─────────────────────────────────────────────┘
ℹ️ Mostrando balance mensual para el año 2026
```

---

## 🔒 **Query SQL Generado**

**URL:** `/balance?view=monthly&year=2026`

**Query ejecutado:**
```sql
SELECT 
    date_trunc('month', finance_ledger.datetime) AS period,
    SUM(CASE WHEN finance_ledger.type = 'INCOME' THEN amount ELSE 0 END) AS income,
    SUM(CASE WHEN finance_ledger.type = 'EXPENSE' THEN amount ELSE 0 END) AS expense
FROM finance_ledger
WHERE finance_ledger.datetime >= '2026-01-01 00:00:00'
  AND finance_ledger.datetime <= '2026-12-31 23:59:59'
GROUP BY date_trunc('month', finance_ledger.datetime)
ORDER BY period ASC;
```

**Resultado actual (2026):**
```
   month    |  income   | expense |    net
------------+-----------+---------+-----------
 2026-01    | 127665.00 |    0.00 | 127665.00
------------+-----------+---------+-----------
TOTAL:      | 127665.00 |    0.00 | 127665.00
```

**Características:**
- ✅ **Agregación en PostgreSQL** (no en Python)
- ✅ `date_trunc('month', ...)` para agrupar por mes
- ✅ `WHERE` con rango exacto del año
- ✅ `GROUP BY` + `SUM` + `CASE` eficiente
- ✅ Solo retorna meses con datos (no meses vacíos)

---

## ✅ **Validaciones Implementadas**

| Parámetro | Validación | Acción |
|-----------|------------|--------|
| `year < 1900` | ❌ Inválido | Flash warning + fallback a defaults |
| `year > 2100` | ❌ Inválido | Flash warning + fallback |
| `year = "abc"` | ❌ No numérico | Flash warning + fallback |
| Sin parámetro | ✅ Válido | Defaults inteligentes |

**Mensajes de error:**
- ⚠️ "Año inválido."

---

## 📊 **Prioridad de Filtros (Documentada)**

### **Regla de Prioridad en Monthly View:**

1. **Si viene `year` en query params:**
   - ✅ Construir `start` = `YYYY-01-01`
   - ✅ Construir `end` = `YYYY-12-31`
   - ❌ **Ignorar** cualquier `start`/`end` en query params
   - **Razón:** year es más específico y fácil de usar

2. **Si NO viene `year` pero vienen `start`/`end`:**
   - ✅ Usar `start` y `end` directamente (compatibilidad legacy)

3. **Si NO viene nada:**
   - ✅ Defaults inteligentes:
     - Año actual (si hay datos)
     - O último año con datos
     - O año actual del sistema (si DB vacío)

---

## 📁 **Archivos Modificados/Creados**

```
app/
├── services/
│   └── balance_service.py             ← +1 función (get_year_date_range)
├── blueprints/
│   └── balance.py                     ← Lógica year para monthly
└── templates/
    └── balance/
        └── index.html                 ← Select year para monthly

MEJORA6_TESTING.md                     ← Checklist 50+ tests (NEW)
MEJORA6_RESUMEN.md                     ← Este archivo (NEW)
```

---

## 🚀 **Cómo Usar**

### **1. Acceder a Balance Mensual:**
```
http://localhost:5000/balance?view=monthly
```

**Comportamiento:**
- ✅ Carga con defaults (año actual o último año con datos)
- ✅ Select precargado

---

### **2. Filtrar por Año Específico:**
1. Seleccionar **Año:** 2026
2. Click **"Aplicar Filtro"**

**URL resultante:**
```
http://localhost:5000/balance?view=monthly&year=2026
```

**Resultado:**
- ✅ Tabla muestra solo meses de 2026
- ✅ Formato: `2026-01`, `2026-02`, etc.
- ✅ Totales calculados para ese año
- ✅ Mensaje: "Mostrando balance mensual para el año **2026**"

---

### **3. Cambiar Año:**
1. Cambiar select a **2025**
2. Click **"Aplicar Filtro"**

**URL:**
```
http://localhost:5000/balance?view=monthly&year=2025
```

---

### **4. Limpiar Filtros:**
Click **"Limpiar"**

**URL:**
```
http://localhost:5000/balance?view=monthly
```

**Resultado:**
- ✅ Vuelve a defaults

---

## 🎨 **UX Mejorado**

### **1. Filtros específicos por vista:**
- **Daily:** Year + Month (MEJORA 5)
- **Monthly:** Year (MEJORA 6) ✅
- **Yearly:** Start + End (sin cambios)

### **2. Mensajes informativos:**
- ✅ "Mostrando balance mensual para el año **2026**"
- ✅ "No hay datos financieros para el rango seleccionado."

### **3. Defaults inteligentes:**
- ✅ Año actual si tiene datos
- ✅ Último año con datos si el actual está vacío
- ✅ Nunca muestra vista vacía sin explicación

### **4. Botón "Limpiar":**
- ✅ Un click para volver a defaults
- ✅ URL limpia sin params

---

## 🔄 **Compatibilidad con Vistas Anteriores**

### **Daily View (MEJORA 5):**
- ✅ **NO afectado**
- ✅ Sigue usando filtros `year`+`month`
- ✅ Formulario muestra selects de año y mes

### **Yearly View:**
- ✅ **NO afectado**
- ✅ Sigue usando filtros `start`/`end`
- ✅ Funciona como antes

**Código condicional en template:**
```html
{% if view == 'daily' %}
    <!-- Year + Month filters (MEJORA 5) -->
{% elif view == 'monthly' %}
    <!-- Year filter (MEJORA 6) -->
{% else %}
    <!-- Start + End filters (Yearly) -->
{% endif %}
```

---

## 📌 **Casos Edge Manejados**

| Caso | Comportamiento |
|------|----------------|
| DB vacía (sin finance_ledger) | ✅ Select años: "Sin datos" + mensaje claro |
| Solo 1 mes con datos en el año | ✅ Tabla con 1 fila |
| 12 meses con datos | ✅ Tabla con 12 filas |
| Año sin datos | ✅ Tabla vacía + mensaje informativo |
| year=1899 | ⚠️ Flash warning + fallback |
| year=2101 | ⚠️ Flash warning + fallback |
| year=abc | ⚠️ Flash warning + fallback |

---

## ✅ **Testing Realizado**

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

1. **Monthly sin params:**
   - ✅ Carga 2026 (default: último año con datos)
   - ✅ Select muestra años: [2026, 2025]
   - ✅ Año seleccionado: 2026

2. **Filtrar por 2025:**
   - ✅ URL: `/balance?view=monthly&year=2025`
   - ✅ Tabla actualizada con meses de 2025 (Nov, Dic)

3. **Limpiar filtros:**
   - ✅ Vuelve a defaults (2026)

4. **Query SQL verificado:**
   ```sql
   SELECT date_trunc('month', datetime) as month, 
          SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END) as income, 
          SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END) as expense 
   FROM finance_ledger 
   WHERE datetime >= '2026-01-01' AND datetime <= '2026-12-31 23:59:59' 
   GROUP BY month 
   ORDER BY month;
   ```
   
   **Resultado:**
   ```
      month    |  income   | expense 
   ------------+-----------+---------
    2026-01    | 127665.00 |    0.00
   ```

---

## ✅ **Checklist de Completitud**

- [x] Servicio: `get_year_date_range()` ✅
- [x] Blueprint: Lectura de year param ✅
- [x] Blueprint: Validación de year (1900-2100) ✅
- [x] Blueprint: Prioridad year > start/end ✅
- [x] Blueprint: Defaults inteligentes ✅
- [x] Blueprint: Reutilizar `get_available_years()` ✅
- [x] Template: Select de Año dinámico ✅
- [x] Template: Botón "Aplicar Filtro" ✅
- [x] Template: Botón "Limpiar" ✅
- [x] Template: Mensaje informativo ✅
- [x] Template: UI condicional (daily/monthly/yearly) ✅
- [x] Query SQL eficiente (date_trunc + WHERE) ✅
- [x] Validaciones robustas ✅
- [x] Mensajes de error claros ✅
- [x] Daily (MEJORA 5) no afectada ✅
- [x] Yearly no afectada ✅
- [x] Documentación: TESTING.md (50+ tests) ✅
- [x] Documentación: RESUMEN.md ✅
- [x] Sin errores de linting ✅
- [x] Docker reconstruido ✅
- [x] Logs limpios ✅
- [x] Query SQL verificado ✅

---

## 🎉 **MEJORA 6 COMPLETADA EXITOSAMENTE**

- ✅ **Filtro year en monthly view funcionando**
- ✅ **Query SQL eficiente (date_trunc + WHERE + agregación en DB)**
- ✅ **Validación robusta (year 1900-2100)**
- ✅ **Prioridad de filtros clara: year > start/end > defaults**
- ✅ **Reutiliza `get_available_years()` de MEJORA 5**
- ✅ **Defaults inteligentes (año actual o último con datos)**
- ✅ **Daily (MEJORA 5) y Yearly no afectadas (UI condicional)**
- ✅ **UX mejorado (mensajes, botón limpiar)**
- ✅ **Sin regresiones en funcionalidades existentes**
- ✅ **Documentación exhaustiva (TESTING + RESUMEN)**
- ✅ **Código limpio y bien organizado**

---

## 🔜 **Próxima Mejora**

**MEJORA 7:** Formato de fechas argentino (DD/MM/YYYY)

---

**Autor:** Sistema Ferretería  
**Fecha:** Enero 2026  
**Versión:** 1.0
