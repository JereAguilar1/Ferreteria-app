# Conversión Automática a Zona Horaria Argentina

## Objetivo
Convertir automáticamente todos los datetime a la zona horaria de Argentina (America/Argentina/Buenos_Aires, UTC-3) antes de renderizar en templates.

## Implementación

### Función Principal: `to_argentina()`

```python
from zoneinfo import ZoneInfo

def to_argentina(dt):
    """
    Convierte un datetime a la zona horaria de Argentina.
    - Si el datetime es naive (sin timezone), asume UTC
    - Convierte a America/Argentina/Buenos_Aires (UTC-3)
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Naive datetime, asumir UTC
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
```

### Integración Automática

**1. Filtro Jinja `datetime_ar`:**
- Ahora convierte automáticamente a zona horaria argentina antes de formatear
- Uso: `{{ sale.datetime|datetime_ar }}`
- Resultado: "18/01/2026 14:30" (hora argentina)

**2. Filtro Jinja `to_argentina`:**
- Disponible para conversión manual si se necesita
- Uso: `{{ sale.datetime|to_argentina }}`
- Resultado: datetime object en zona horaria argentina

### Archivos Modificados

1. **`app/utils/formatters.py`:**
   - ✅ Agregado: `from zoneinfo import ZoneInfo`
   - ✅ Nueva función: `to_argentina(dt)`
   - ✅ Actualizado: `datetime_ar()` ahora llama a `to_argentina()` automáticamente

2. **`app/__init__.py`:**
   - ✅ Importado: `to_argentina`
   - ✅ Registrado: `app.jinja_env.filters['to_argentina'] = to_argentina`

---

## Testing

### Pre-requisitos
- Sistema levantado
- Python 3.9+ (para `zoneinfo`)
- Datos con timestamps en la base de datos

---

### Test 1: Verificar conversión en ventas

**Pasos:**
1. Crear una venta en el sistema
2. Verificar el timestamp en DB (debe estar en UTC):
```sql
SELECT id, datetime, created_at 
FROM sale 
ORDER BY id DESC 
LIMIT 1;
```
3. Ir a `/sales` y ver el listado
4. Verificar que la hora mostrada es UTC-3

**Resultado esperado:**
- ✅ DB muestra: `2026-01-18 17:30:00+00` (UTC)
- ✅ UI muestra: `18/01/2026 14:30` (Argentina, UTC-3)
- ✅ Diferencia de 3 horas menos

---

### Test 2: Verificar conversión en boletas

**Pasos:**
1. Crear una boleta de compra
2. Verificar timestamp en DB:
```sql
SELECT id, invoice_date, created_at 
FROM purchase_invoice 
ORDER BY id DESC 
LIMIT 1;
```
3. Ir a `/invoices` y ver el detalle
4. Verificar hora de creación

**Resultado esperado:**
- ✅ Hora en UI = Hora en DB - 3 horas
- ✅ Formato: DD/MM/YYYY HH:MM

---

### Test 3: Verificar conversión en presupuestos

**Pasos:**
1. Crear un presupuesto
2. Ver detalle del presupuesto
3. Verificar `issued_at` y `valid_until`

**Resultado esperado:**
- ✅ Fechas y horas en zona horaria argentina
- ✅ Formato correcto

---

### Test 4: Verificar conversión en libro mayor (balance)

**Pasos:**
1. Ir a `/balance/ledger`
2. Ver entradas de finance_ledger
3. Verificar timestamps

**Resultado esperado:**
- ✅ Todas las fechas/horas en zona argentina
- ✅ Consistencia en todo el listado

---

### Test 5: Datetime naive (sin timezone)

**Pasos:**
1. Si hay algún datetime naive en DB (sin timezone info)
2. Verificar que se asume UTC y se convierte correctamente

**Resultado esperado:**
- ✅ Datetime naive se trata como UTC
- ✅ Se convierte a Argentina (UTC-3)
- ✅ No hay errores

---

### Test 6: Datetime ya en otra zona horaria

**Pasos:**
1. Crear un datetime con timezone explícito (ej: UTC, Europe/Madrid)
2. Convertir con `to_argentina()`

**Resultado esperado:**
- ✅ Se convierte correctamente a Argentina
- ✅ Mantiene el momento absoluto (solo cambia representación)

---

### Test 7: Valores None

**Pasos:**
1. Renderizar un template con datetime = None
2. Usar filtro `datetime_ar`

**Resultado esperado:**
- ✅ Retorna "-"
- ✅ No hay error

---

### Test 8: Horario de verano (DST)

**Pasos:**
1. Verificar comportamiento en fechas con cambio de horario
2. Argentina NO usa DST desde 2009, siempre UTC-3

**Resultado esperado:**
- ✅ Siempre UTC-3
- ✅ No hay cambios estacionales

---

### Test 9: Comparación con hora del servidor

**Pasos:**
1. En el servidor, ejecutar:
```python
from datetime import datetime
from zoneinfo import ZoneInfo

# Hora UTC
utc_now = datetime.now(ZoneInfo("UTC"))
print(f"UTC: {utc_now}")

# Hora Argentina
ar_now = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))
print(f"Argentina: {ar_now}")

# Diferencia
print(f"Diferencia: {(utc_now - ar_now).total_seconds() / 3600} horas")
```

**Resultado esperado:**
- ✅ Diferencia: 3 horas (o -3 dependiendo de la dirección)
- ✅ Argentina = UTC - 3

---

### Test 10: Formato completo en templates

**Pasos:**
1. Crear un template de prueba:
```html
<p>Hora UTC original: {{ sale.datetime }}</p>
<p>Hora Argentina (auto): {{ sale.datetime|datetime_ar }}</p>
<p>Hora Argentina (manual): {{ sale.datetime|to_argentina|datetime_ar }}</p>
<p>Solo fecha: {{ sale.datetime|datetime_ar(with_time=False) }}</p>
```

**Resultado esperado:**
- ✅ Todas las conversiones funcionan
- ✅ Formato correcto en cada caso

---

## Queries de Verificación

### Ver timestamps en DB (UTC)
```sql
-- Ventas
SELECT id, datetime, created_at 
FROM sale 
ORDER BY id DESC 
LIMIT 5;

-- Boletas
SELECT id, invoice_date, created_at 
FROM purchase_invoice 
ORDER BY id DESC 
LIMIT 5;

-- Libro mayor
SELECT id, datetime, type, amount 
FROM finance_ledger 
ORDER BY id DESC 
LIMIT 5;
```

### Verificar zona horaria del servidor
```sql
SHOW timezone;
-- Debe retornar: UTC o similar
```

### Verificar zona horaria en Python
```python
from datetime import datetime
from zoneinfo import ZoneInfo

# Crear datetime en UTC
dt_utc = datetime(2026, 1, 18, 17, 30, tzinfo=ZoneInfo("UTC"))
print(f"UTC: {dt_utc}")

# Convertir a Argentina
dt_ar = dt_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
print(f"Argentina: {dt_ar}")
print(f"Formato: {dt_ar.strftime('%d/%m/%Y %H:%M')}")
```

---

## Uso en Templates

### Automático (recomendado)
```html
<!-- El filtro datetime_ar ya convierte automáticamente -->
<p>Fecha de venta: {{ sale.datetime|datetime_ar }}</p>
<p>Creado: {{ invoice.created_at|datetime_ar }}</p>
```

### Manual (si se necesita el objeto datetime)
```html
<!-- Convertir primero, luego formatear -->
{% set dt_ar = sale.datetime|to_argentina %}
<p>Hora: {{ dt_ar.hour }}</p>
<p>Minuto: {{ dt_ar.minute }}</p>
```

### Solo fecha (sin hora)
```html
<!-- with_time=False para solo mostrar fecha -->
<p>Fecha: {{ sale.datetime|datetime_ar(with_time=False) }}</p>
```

---

## Notas Importantes

1. **Base de datos en UTC:**
   - PostgreSQL debe guardar timestamps en UTC
   - Configuración: `timezone = 'UTC'` en postgresql.conf
   - SQLAlchemy usa `DateTime(timezone=True)` para aware datetimes

2. **Zona horaria de Argentina:**
   - Código: `America/Argentina/Buenos_Aires`
   - Offset: UTC-3 (todo el año, sin DST)
   - No hay cambio de horario desde 2009

3. **Datetime naive vs aware:**
   - **Naive:** Sin información de timezone (ej: `datetime(2026, 1, 18, 17, 30)`)
   - **Aware:** Con timezone (ej: `datetime(2026, 1, 18, 17, 30, tzinfo=UTC)`)
   - La función `to_argentina()` asume UTC para naive datetimes

4. **Compatibilidad:**
   - Python 3.9+: `zoneinfo` es parte de la biblioteca estándar
   - Python 3.8 o menor: instalar `backports.zoneinfo`

5. **Performance:**
   - La conversión es muy rápida (microsegundos)
   - No hay impacto significativo en el rendimiento
   - Se hace solo al renderizar, no en queries

---

## Ejemplos de Conversión

| Hora UTC (DB) | Hora Argentina (UI) | Diferencia |
|---------------|---------------------|------------|
| 2026-01-18 17:30:00+00 | 18/01/2026 14:30 | -3 horas |
| 2026-01-18 03:00:00+00 | 18/01/2026 00:00 | -3 horas |
| 2026-01-18 00:00:00+00 | 17/01/2026 21:00 | -3 horas (día anterior) |
| 2026-01-18 23:59:00+00 | 18/01/2026 20:59 | -3 horas |

---

## Resumen

| Aspecto | Implementación |
|---------|----------------|
| **Función principal** | `to_argentina(dt)` en `formatters.py` |
| **Conversión automática** | `datetime_ar` filtro actualizado |
| **Conversión manual** | `to_argentina` filtro disponible |
| **Zona horaria** | America/Argentina/Buenos_Aires (UTC-3) |
| **Formato** | DD/MM/YYYY HH:MM |
| **Naive datetimes** | Asumidos como UTC |
| **Performance** | Sin impacto significativo |

✅ **IMPLEMENTADO** - Todos los datetime ahora se muestran en zona horaria argentina automáticamente.
