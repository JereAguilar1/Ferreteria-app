# MEJORA 7 – Formato de Fechas Argentino (DD/MM/YYYY)

## 📋 **Testing Checklist**

---

## **Objetivo**
Validar que todas las fechas visibles en la UI se muestran en formato argentino DD/MM/YYYY, manteniendo la funcionalidad de los inputs `type="date"` y sin romper filtros ni parseos.

---

## **1. Filtros Jinja Implementados**

### ✅ **Filtros disponibles:**
- `date_ar` - Formatea date/datetime a DD/MM/YYYY
- `datetime_ar(with_time=False)` - Formatea datetime a DD/MM/YYYY o DD/MM/YYYY HH:MM
- `month_ar` - Formatea a MM/YYYY (para períodos mensuales)
- `year_ar` - Formatea a YYYY (para períodos anuales)

### ✅ **Test 1.1: Verificar registro de filtros**
**Objetivo:** Asegurar que los filtros están registrados en Jinja.

**Método:** Inspeccionar código o probar en template.

**Archivo:** `app/__init__.py`

**Resultado esperado:**
```python
app.jinja_env.filters['date_ar'] = date_ar
app.jinja_env.filters['datetime_ar'] = datetime_ar
app.jinja_env.filters['month_ar'] = month_ar
app.jinja_env.filters['year_ar'] = year_ar
```

---

## **2. Boletas de Compra (Invoices)**

### ✅ **Test 2.1: Listado de boletas**
**Objetivo:** Verificar que las fechas en el listado usan formato DD/MM/YYYY.

**Pasos:**
1. Navegar a `http://localhost:5000/invoices`
2. Observar columnas "Fecha" y "Vencimiento"

**Resultado esperado:**
- ✅ Columna "Fecha": formato DD/MM/YYYY (ej: `02/01/2026`)
- ✅ Columna "Vencimiento": formato DD/MM/YYYY o `-` si es null
- ✅ Sin errores de template

**Template:** `invoices/list.html`
**Líneas modificadas:**
```html
<td>{{ invoice.invoice_date|date_ar }}</td>
<td>{{ invoice.due_date|date_ar }}</td>
```

---

### ✅ **Test 2.2: Detalle de boleta**
**Objetivo:** Verificar formato en vista de detalle.

**Pasos:**
1. Navegar a `/invoices/<id>` (elegir cualquier boleta)
2. Observar:
   - Fecha Boleta
   - Vencimiento
   - Fecha de Pago (si está pagada)

**Resultado esperado:**
- ✅ **Fecha Boleta:** DD/MM/YYYY
- ✅ **Vencimiento:** DD/MM/YYYY o `-`
- ✅ **Fecha de Pago:** DD/MM/YYYY o `-` (si no está pagada)

**Template:** `invoices/detail.html`
**Líneas modificadas:**
```html
<dd>{{ invoice.invoice_date|date_ar }}</dd>
<dd>{{ invoice.due_date|date_ar }}</dd>
<dd>{{ invoice.paid_at|date_ar }}</dd>
```

---

### ✅ **Test 2.3: Inputs de fecha NO cambian**
**Objetivo:** Verificar que los `<input type="date">` siguen usando formato YYYY-MM-DD.

**Pasos:**
1. En `/invoices/new`, observar el formulario
2. Verificar que los inputs de fecha (invoice_date, due_date) funcionan normalmente

**Resultado esperado:**
- ✅ Inputs `type="date"` funcionan con calendario del navegador
- ✅ Formato interno YYYY-MM-DD (no se ve, es manejado por el navegador)
- ✅ Envío del form funciona correctamente

**Pasos de verificación:**
1. Crear una nueva boleta con fechas
2. Verificar que se guarda correctamente
3. Ver detalle → fechas se muestran en DD/MM/YYYY

---

## **3. Balance Financiero**

### ✅ **Test 3.1: Balance Diario - Períodos**
**Objetivo:** Verificar que los períodos diarios se muestran como DD/MM/YYYY.

**Pasos:**
1. Navegar a `/balance?view=daily`
2. Observar columna "Período"

**Resultado esperado:**
- ✅ Formato: `DD/MM/YYYY` (ej: `02/01/2026`, `04/01/2026`)
- ✅ No hay formato YYYY-MM-DD

**Template:** `balance/index.html`
**Código:**
```html
{% if view == 'daily' %}
    {{ item.period|date_ar }}
{% endif %}
```

---

### ✅ **Test 3.2: Balance Mensual - Períodos**
**Objetivo:** Verificar que los períodos mensuales se muestran como MM/YYYY.

**Pasos:**
1. Navegar a `/balance?view=monthly`
2. Observar columna "Período"

**Resultado esperado:**
- ✅ Formato: `MM/YYYY` (ej: `01/2026`, `12/2025`)
- ✅ Representa el mes completo, no un día específico

**Código:**
```html
{% elif view == 'monthly' %}
    {{ item.period|month_ar }}
{% endif %}
```

---

### ✅ **Test 3.3: Balance Anual - Períodos**
**Objetivo:** Verificar que los períodos anuales se muestran como YYYY.

**Pasos:**
1. Navegar a `/balance?view=yearly`
2. Observar columna "Período"

**Resultado esperado:**
- ✅ Formato: `YYYY` (ej: `2026`, `2025`)
- ✅ Solo el año

**Código:**
```html
{% else %}
    {{ item.period|year_ar }}
{% endif %}
```

---

### ✅ **Test 3.4: Balance - Mensaje de rango**
**Objetivo:** Verificar que las fechas de rango (start/end) se muestran en DD/MM/YYYY.

**Pasos:**
1. En cualquier vista de balance, observar el mensaje:
   "Mostrando X período(s) desde **fecha** hasta **fecha**"

**Resultado esperado:**
- ✅ Ambas fechas en formato DD/MM/YYYY
- ✅ Ej: "desde **01/01/2026** hasta **31/01/2026**"

**Código:**
```html
desde <strong>{{ start|date_ar }}</strong> hasta <strong>{{ end|date_ar }}</strong>
```

---

## **4. Libro Mayor (Ledger)**

### ✅ **Test 4.1: Listado de movimientos**
**Objetivo:** Verificar que datetime se muestra con formato DD/MM/YYYY HH:MM.

**Pasos:**
1. Navegar a `/balance/ledger`
2. Observar columna "Fecha/Hora"

**Resultado esperado:**
- ✅ Formato: `DD/MM/YYYY HH:MM` (ej: `02/01/2026 10:30`)
- ✅ Incluye hora y minuto

**Template:** `balance/ledger_list.html`
**Código:**
```html
<td>{{ entry.datetime|datetime_ar(with_time=True) }}</td>
```

---

## **5. Casos Edge y Validaciones**

### ✅ **Test 5.1: Fecha null**
**Objetivo:** Verificar que valores null se manejan correctamente.

**Pasos:**
1. Ver una boleta sin fecha de vencimiento (due_date null)
2. Ver una boleta PENDING sin fecha de pago (paid_at null)

**Resultado esperado:**
- ✅ Muestra `-` en lugar de error o "None"
- ✅ No hay excepciones en logs

**Código en filtro:**
```python
if value is None:
    return "-"
```

---

### ✅ **Test 5.2: Formato string (edge case)**
**Objetivo:** Verificar que si viene un string con formato ISO, se parsea correctamente.

**Método:** Test unitario o caso manual.

**Casos:**
| Input | Resultado esperado |
|-------|-------------------|
| `date(2026, 1, 9)` | `09/01/2026` |
| `datetime(2026, 1, 9, 15, 30)` | `09/01/2026` (sin time) |
| `datetime(2026, 1, 9, 15, 30)` con `with_time=True` | `09/01/2026 15:30` |
| `"2026-01-09"` (string) | `09/01/2026` |
| `None` | `-` |

---

### ✅ **Test 5.3: Diferentes meses**
**Objetivo:** Verificar que el formato funciona para todos los meses.

**Casos:**
| Fecha | Formato DD/MM/YYYY |
|-------|-------------------|
| 2026-01-15 | 15/01/2026 |
| 2026-02-28 | 28/02/2026 |
| 2026-12-31 | 31/12/2026 |
| 2025-11-05 | 05/11/2025 |

---

## **6. Consistencia Entre Vistas**

### ✅ **Test 6.1: Misma boleta en lista y detalle**
**Objetivo:** Verificar que las fechas son consistentes.

**Pasos:**
1. Ver lista de boletas → anotar fecha de una boleta
2. Entrar al detalle de esa boleta → verificar fecha

**Resultado esperado:**
- ✅ Ambas muestran el mismo formato DD/MM/YYYY
- ✅ La fecha es la misma (no hay cambios de timezone inadvertidos)

---

### ✅ **Test 6.2: Balance diario vs mensual**
**Objetivo:** Verificar coherencia en fechas entre vistas.

**Pasos:**
1. Ver balance diario de Enero 2026
2. Sumar mentalmente los totales de días
3. Ver balance mensual de 2026
4. Verificar que el total de Enero coincide

**Resultado esperado:**
- ✅ Los totales coinciden (las fechas son correctas, no hay problemas de rango)

---

## **7. Filtros y Parseo Backend (No Romper)**

### ✅ **Test 7.1: Filtros de balance funcionan**
**Objetivo:** Asegurar que los filtros year/month siguen funcionando.

**Pasos:**
1. En daily, cambiar año y mes
2. Click "Aplicar Filtros"
3. Verificar que los datos cambian correctamente

**Resultado esperado:**
- ✅ Filtros funcionan
- ✅ Fechas se muestran en DD/MM/YYYY
- ✅ Backend parsea correctamente (no hay errores)

---

### ✅ **Test 7.2: Crear boleta con fechas**
**Objetivo:** Verificar que el parseo en backend sigue funcionando.

**Pasos:**
1. Crear nueva boleta
2. Seleccionar fecha de boleta con el date picker
3. Agregar ítems y guardar

**Resultado esperado:**
- ✅ Boleta se crea sin errores
- ✅ Al ver detalle, fecha se muestra en DD/MM/YYYY
- ✅ Backend parseó correctamente el formato YYYY-MM-DD del input

---

### ✅ **Test 7.3: Pagar boleta con fecha**
**Objetivo:** Verificar que el pago de boletas sigue funcionando.

**Pasos:**
1. Ir a una boleta PENDING
2. Marcar como pagada, seleccionar fecha de pago
3. Confirmar

**Resultado esperado:**
- ✅ Boleta marcada como PAID
- ✅ Fecha de pago se muestra en DD/MM/YYYY en detalle

---

## **8. Regresión (No Romper)**

### ✅ **Test 8.1: Productos CRUD**
**Pasos:** Crear, editar, listar productos

**Resultado esperado:** ✅ Funcional

---

### ✅ **Test 8.2: Ventas (POS)**
**Pasos:** Crear venta, confirmar

**Resultado esperado:** ✅ Funcional

---

### ✅ **Test 8.3: MEJORA 1, 2, 3, 4, 5, 6**
**Pasos:** Verificar fotos, filtros, top vendidos, unit_cost entero, daily/monthly filters

**Resultado esperado:** ✅ Todas funcionales

---

## **9. Casos de Test Unitario (Opcional)**

Si se quiere validar los filtros de forma aislada:

```python
from app.utils.formatters import date_ar, datetime_ar, month_ar, year_ar
from datetime import date, datetime

def test_date_ar():
    assert date_ar(date(2026, 1, 9)) == "09/01/2026"
    assert date_ar(None) == "-"
    assert date_ar("2026-01-09") == "09/01/2026"

def test_datetime_ar():
    dt = datetime(2026, 1, 9, 15, 30)
    assert datetime_ar(dt, with_time=False) == "09/01/2026"
    assert datetime_ar(dt, with_time=True) == "09/01/2026 15:30"
    assert datetime_ar(None) == "-"

def test_month_ar():
    assert month_ar(datetime(2026, 1, 15)) == "01/2026"
    assert month_ar(None) == "-"

def test_year_ar():
    assert year_ar(datetime(2026, 1, 15)) == "2026"
    assert year_ar(None) == "-"
```

---

## **✅ Testing Completo: Checklist Final**

- [ ] Filtros registrados en Jinja ✅
- [ ] Boletas list: invoice_date y due_date en DD/MM/YYYY
- [ ] Boletas detail: todas las fechas en DD/MM/YYYY
- [ ] Inputs type="date" siguen funcionando
- [ ] Balance daily: períodos en DD/MM/YYYY
- [ ] Balance monthly: períodos en MM/YYYY
- [ ] Balance yearly: períodos en YYYY
- [ ] Balance: rango (start/end) en DD/MM/YYYY
- [ ] Ledger: datetime en DD/MM/YYYY HH:MM
- [ ] Fechas null muestran "-"
- [ ] Parseo de strings funciona
- [ ] Diferentes meses formatean correctamente
- [ ] Consistencia lista/detalle
- [ ] Filtros de balance funcionan
- [ ] Crear boleta funciona
- [ ] Pagar boleta funciona
- [ ] Regresión: Todas las mejoras anteriores funcionan

---

## **🎯 Resultado Esperado Final**

Al finalizar todos los tests:
- ✅ **Todas las fechas visibles en formato DD/MM/YYYY**
- ✅ **Períodos mensuales en MM/YYYY**
- ✅ **Períodos anuales en YYYY**
- ✅ **Inputs type="date" funcionan (YYYY-MM-DD interno)**
- ✅ **Filtros Jinja centralizados y reutilizables**
- ✅ **Valores null manejan correctamente**
- ✅ **Sin regresiones en funcionalidades existentes**

---

**Última actualización:** Enero 2026  
**Autor:** Sistema Ferretería - MEJORA 7
