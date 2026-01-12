# MEJORA 18: Módulo de Productos Faltantes - Testing Guide

## Objetivo del Módulo
Permitir registrar y hacer seguimiento de productos que los clientes solicitan pero que NO están en el catálogo del sistema (no son productos sin stock, sino productos que nunca se han cargado).

---

## Pre-requisitos
- Sistema corriendo en Docker
- Acceso a la interfaz web
- Acceso a la base de datos para verificaciones
- Tener algunos productos en el catálogo para el test de advertencia

---

## TEST 1: Registrar Nuevo Producto Faltante
**Objetivo:** Verificar creación de nuevo registro

**Pasos:**
1. Navegar a **Productos Faltantes** desde el navbar
2. En el formulario superior, ingresar: `"Tornillo hexagonal 10mm"`
3. Click "Registrar Pedido"

**Resultado Esperado:**
- ✅ Flash message verde: "Registrado pedido: "Tornillo hexagonal 10mm" (1 pedido)"
- ✅ Producto aparece en la tabla con:
  - Nombre: Tornillo hexagonal 10mm
  - Pedidos: badge azul con "1"
  - Último Pedido: fecha/hora actual
  - Estado: badge amarillo "Pendiente"
- ✅ Estadísticas: Pendientes = 1, Total Pedidos = 1

**Verificación SQL:**
```sql
SELECT * FROM missing_product_request WHERE normalized_name = 'tornillo hexagonal 10mm';
-- Debe retornar 1 fila con request_count = 1, status = 'OPEN'
```

---

## TEST 2: Registrar Mismo Producto (Incremento de Contador)
**Objetivo:** Verificar deduplicación y auto-incremento

**Pasos:**
1. En el mismo formulario, ingresar: `"  TORNILLO HEXAGONAL 10MM  "` (con espacios y mayúsculas)
2. Click "Registrar Pedido"

**Resultado Esperado:**
- ✅ Flash message: "Registrado pedido: "Tornillo hexagonal 10mm" (ahora 2 pedidos)"
- ✅ NO se crea un nuevo registro
- ✅ El contador del producto existente ahora muestra badge azul con "2"
- ✅ "Último Pedido" se actualiza a la hora actual

**Verificación SQL:**
```sql
SELECT name, request_count, last_requested_at 
FROM missing_product_request 
WHERE normalized_name = 'tornillo hexagonal 10mm';
-- Debe retornar 1 fila con request_count = 2
-- last_requested_at debe ser más reciente que created_at
```

---

## TEST 3: Normalización de Nombres (Variaciones)
**Objetivo:** Verificar que variaciones se deduplican correctamente

**Pasos:**
1. Registrar: `"Cable  UTP   cat5e"` (espacios múltiples)
2. Registrar: `"CABLE UTP CAT5E"`
3. Registrar: `"cable utp cat5e"`

**Resultado Esperado:**
- ✅ Solo 1 registro creado
- ✅ Contador final: 3 pedidos
- ✅ Nombre mostrado: el del primer registro ("Cable UTP cat5e")

**Verificación SQL:**
```sql
SELECT COUNT(*) FROM missing_product_request WHERE normalized_name LIKE '%cable utp cat5e%';
-- Debe retornar 1 (una sola fila)

SELECT request_count FROM missing_product_request WHERE normalized_name = 'cable utp cat5e';
-- Debe retornar 3
```

---

## TEST 4: Buscar por Nombre
**Objetivo:** Verificar filtro de búsqueda

**Pasos:**
1. Tener varios productos registrados (Tornillo, Cable, Martillo, etc.)
2. En el campo "Buscar por nombre...", ingresar: `"cable"`
3. Click "Filtrar"

**Resultado Esperado:**
- ✅ Solo se muestran productos que contienen "cable" (case-insensitive)
- ✅ URL contiene: `?q=cable`
- ✅ Campo de búsqueda mantiene el valor "cable"
- ✅ Botón "Limpiar" visible

---

## TEST 5: Filtrar por Estado - Solo Pendientes
**Objetivo:** Verificar filtro de estado OPEN

**Pasos:**
1. Tener productos con diferentes estados (algunos OPEN, algunos RESOLVED)
2. Click en botón "Solo Pendientes"
3. O usar dropdown: seleccionar "Pendientes" y click "Filtrar"

**Resultado Esperado:**
- ✅ Solo se muestran productos con estado OPEN (badge amarillo)
- ✅ URL contiene: `?status=OPEN`
- ✅ No se muestran productos RESOLVED
- ✅ Estadísticas siguen mostrando totales correctos

---

## TEST 6: Marcar como Resuelto
**Objetivo:** Verificar cambio de estado OPEN → RESOLVED

**Pasos:**
1. Encontrar un producto con estado "Pendiente"
2. Click en botón "✓ Resolver"
3. Confirmar en el dialog de confirmación

**Resultado Esperado:**
- ✅ Flash message verde: "✓ [Producto] marcado como resuelto"
- ✅ Estado cambia a badge verde "Resuelto"
- ✅ Fila se muestra en gris (table-secondary)
- ✅ Botón "Resolver" cambia a "↻ Reabrir"
- ✅ Contador de pedidos NO se resetea (se mantiene el historial)

**Verificación SQL:**
```sql
SELECT status, request_count, updated_at 
FROM missing_product_request 
WHERE id = <id_producto>;
-- status debe ser 'RESOLVED'
-- request_count no debe cambiar
-- updated_at debe ser más reciente que created_at
```

---

## TEST 7: Reabrir Producto Resuelto
**Objetivo:** Verificar cambio de estado RESOLVED → OPEN

**Pasos:**
1. Encontrar un producto con estado "Resuelto"
2. Click en botón "↻ Reabrir"
3. Confirmar en el dialog

**Resultado Esperado:**
- ✅ Flash message: "[Producto] reabierto correctamente"
- ✅ Estado vuelve a "Pendiente" (badge amarillo)
- ✅ Fila ya no se muestra en gris
- ✅ Botón vuelve a ser "✓ Resolver"
- ✅ Contador se mantiene

---

## TEST 8: Editar Notas
**Objetivo:** Verificar actualización de campo notes

**Pasos:**
1. En un producto cualquiera, click en botón 📌 (Editar notas)
2. En el modal, escribir: `"Proveedor: Acme SA - Consultar precio"`
3. Click "Guardar Notas"

**Resultado Esperado:**
- ✅ Modal se cierra
- ✅ Flash message: "Notas actualizadas para [Producto]"
- ✅ Debajo del nombre del producto ahora aparece:
  ```
  📌 Proveedor: Acme SA - Consultar precio
  ```
- ✅ Si se abre el modal nuevamente, el texto persiste

**Verificación SQL:**
```sql
SELECT notes FROM missing_product_request WHERE id = <id_producto>;
-- Debe contener el texto ingresado
```

---

## TEST 9: Validación - Nombre Vacío
**Objetivo:** Verificar que no se permite nombre vacío

**Pasos:**
1. Intentar registrar producto con campo nombre vacío
2. Click "Registrar Pedido"

**Resultado Esperado:**
- ✅ Validación HTML5 impide submit
- ✅ Mensaje del navegador: "Rellena este campo"
- ✅ No se crea ningún registro

---

## TEST 10: Orden Correcto por Contador (DESC)
**Objetivo:** Verificar que productos más pedidos aparecen primero

**Pasos:**
1. Tener varios productos con diferentes cantidades de pedidos:
   - Producto A: 10 pedidos
   - Producto B: 3 pedidos
   - Producto C: 15 pedidos
   - Producto D: 1 pedido
2. Ir al listado sin filtros

**Resultado Esperado:**
- ✅ Orden de aparición:
  1. Producto C (15) con badge rojo
  2. Producto A (10) con badge rojo
  3. Producto B (3) con badge azul
  4. Producto D (1) con badge azul
- ✅ Los de >= 10 pedidos tienen badge rojo
- ✅ Los de >= 5 pedidos tienen badge amarillo
- ✅ Los de < 5 pedidos tienen badge azul

---

## TEST 11: Destacado Visual por Cantidad
**Objetivo:** Verificar resaltado de productos muy pedidos

**Pasos:**
1. Registrar un producto hasta que tenga 5+ pedidos
2. Observar el color del badge y la fila

**Resultado Esperado:**
- ✅ request_count >= 10: badge rojo (bg-danger)
- ✅ request_count >= 5: badge amarillo (bg-warning) + fila amarilla (table-warning)
- ✅ request_count < 5: badge azul (bg-info)
- ✅ Status RESOLVED: fila gris (table-secondary text-muted)

---

## TEST 12: Advertencia de Producto Existente en Catálogo
**Objetivo:** Verificar que se muestra advertencia si el producto ya existe

**Pasos:**
1. Asegurarse de tener un producto en el catálogo, ej: "Martillo de Goma"
2. En Productos Faltantes, registrar: `"Martillo de Goma"`

**Resultado Esperado:**
- ✅ Flash message AMARILLO (warning):
  ```
  ⚠️ Advertencia: El producto "Martillo de Goma" ya existe en el catálogo (ID: X).
  Considera usar el producto existente en vez de registrarlo como faltante.
  ```
- ✅ El producto SÍ se registra (no se bloquea)
- ✅ Permite al usuario decidir si continuar

**Nota:** Si se prefiere BLOQUEAR el registro, modificar el blueprint para hacer `return redirect` antes de crear el registro.

---

## TEST 13: Estadísticas en Cards
**Objetivo:** Verificar que las cards de resumen muestran datos correctos

**Pasos:**
1. Tener:
   - 5 productos OPEN
   - 3 productos RESOLVED
   - Total de 42 pedidos acumulados
2. Ver la sección inferior de estadísticas

**Resultado Esperado:**
- ✅ Card "Pendientes" (amarillo): 5
- ✅ Card "Resueltos" (verde): 3
- ✅ Card "Total Pedidos" (azul): 42

**Verificación SQL:**
```sql
-- Pendientes
SELECT COUNT(*) FROM missing_product_request WHERE status = 'OPEN';

-- Resueltos
SELECT COUNT(*) FROM missing_product_request WHERE status = 'RESOLVED';

-- Total pedidos
SELECT SUM(request_count) FROM missing_product_request;
```

---

## TEST 14: Filtros Combinados (Búsqueda + Estado)
**Objetivo:** Verificar que filtros funcionan en conjunto

**Pasos:**
1. Buscar: `"tornillo"` + Estado: `"Pendientes"`
2. Click "Filtrar"

**Resultado Esperado:**
- ✅ Solo muestra productos que:
  - Contienen "tornillo" en el nombre, Y
  - Tienen status = OPEN
- ✅ URL: `?q=tornillo&status=OPEN`
- ✅ Botón "Limpiar" visible

---

## TEST 15: Limpiar Filtros
**Objetivo:** Verificar botón "Limpiar"

**Pasos:**
1. Aplicar filtros (búsqueda y/o estado)
2. Click en botón "✕ Limpiar"

**Resultado Esperado:**
- ✅ Redirige a `/missing-products` (sin query params)
- ✅ Muestra todos los productos
- ✅ Campos de filtro vacíos/default
- ✅ Botón "Limpiar" desaparece

---

## QUERIES DE VERIFICACIÓN

### Ver todos los productos faltantes
```sql
SELECT 
    id,
    name,
    normalized_name,
    request_count,
    status,
    last_requested_at,
    notes
FROM missing_product_request
ORDER BY request_count DESC, last_requested_at DESC;
```

### Top 10 más pedidos
```sql
SELECT 
    name,
    request_count,
    status
FROM missing_product_request
ORDER BY request_count DESC
LIMIT 10;
```

### Productos pendientes con muchos pedidos (priorizar)
```sql
SELECT 
    name,
    request_count,
    last_requested_at
FROM missing_product_request
WHERE status = 'OPEN' AND request_count >= 5
ORDER BY request_count DESC;
```

### Historial de cambios (updated_at vs created_at)
```sql
SELECT 
    name,
    request_count,
    created_at,
    updated_at,
    updated_at - created_at AS time_active,
    status
FROM missing_product_request
WHERE updated_at > created_at
ORDER BY updated_at DESC;
```

---

## CRITERIOS DE ÉXITO

### Funcionalidad
- ✅ Registrar nuevo producto faltante crea registro con count=1
- ✅ Registrar mismo producto (variaciones) incrementa contador
- ✅ Normalización funciona (espacios, mayúsculas)
- ✅ Búsqueda por nombre funciona (case-insensitive)
- ✅ Filtros por estado (OPEN/RESOLVED/ALL) funcionan
- ✅ Resolver marca status=RESOLVED, mantiene historial
- ✅ Reabrir vuelve a status=OPEN
- ✅ Editar notas persiste correctamente
- ✅ Orden por request_count DESC funciona
- ✅ Advertencia se muestra para productos existentes

### UI/UX
- ✅ Productos muy pedidos se destacan visualmente
- ✅ Productos resueltos se muestran en gris
- ✅ Badges de contador con colores (azul/amarillo/rojo)
- ✅ Estadísticas en cards son correctas
- ✅ Formulario de registro rápido y simple
- ✅ Confirmaciones antes de resolver/reabrir
- ✅ Modal de notas funciona correctamente

### Integridad
- ✅ No crea productos en tabla `product` automáticamente
- ✅ No afecta stock real ni ledger
- ✅ unique constraint en normalized_name previene duplicados
- ✅ Timestamps se actualizan correctamente
- ✅ Check constraints funcionan (count >= 0, status in OPEN/RESOLVED)

---

## ARCHIVOS MODIFICADOS/CREADOS

1. **DB Migration:**
   - `db/migrations/MEJORA18_missing_products.sql` (NUEVO)
   - `db/init/001_schema.sql` (actualizado con tabla)

2. **Models:**
   - `app/models/missing_product_request.py` (NUEVO)
   - `app/models/__init__.py` (actualizado)

3. **Blueprint:**
   - `app/blueprints/missing_products.py` (NUEVO)

4. **Templates:**
   - `app/templates/missing_products/list.html` (NUEVO)

5. **App Factory:**
   - `app/__init__.py` (registrado blueprint)

6. **Navbar:**
   - `app/templates/base.html` (agregado link)

7. **Testing:**
   - `MEJORA18_TESTING.md` (este archivo)

---

## ROLLBACK (si es necesario)

Si surge algún problema:

```bash
# Eliminar blueprint y templates
rm app/blueprints/missing_products.py
rm -r app/templates/missing_products/

# Revertir cambios en app/__init__.py
git checkout HEAD -- app/__init__.py

# Revertir cambios en base.html
git checkout HEAD -- app/templates/base.html

# Revertir cambios en models
git checkout HEAD -- app/models/__init__.py
rm app/models/missing_product_request.py

# Eliminar tabla en DB
docker compose exec -T db psql -U ferreteria -d ferreteria -c "DROP TABLE IF EXISTS missing_product_request CASCADE;"

# Rebuild
docker compose up --build -d web
```

---

## NOTAS ADICIONALES

### Casos de Uso Reales
1. **Cliente pide "Cable HDMI 10m"** → No lo tengo → Registro
2. **Otro cliente pide lo mismo** → Contador sube → Veo que hay demanda
3. **Consigo el producto** → Marco como "Resuelto"
4. **Luego lo cargo al catálogo** → Ya tengo historial de cuántos lo pidieron

### Mejoras Futuras (Opcionales)
- Agregar campo "proveedor_potencial" (FK a supplier)
- Exportar a CSV para compras
- Integración con módulo de compras (crear orden automática)
- Notificaciones cuando un producto llega a X pedidos
- Gráficos de tendencias

---

**Estado: TESTING COMPLETO DOCUMENTADO** ✅
