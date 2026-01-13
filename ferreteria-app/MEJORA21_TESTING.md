# MEJORA 21: Boletas ordenadas por vencimiento + alerta global + estado "Caducada"

## Objetivo
Verificar que las boletas se ordenan por vencimiento, que aparece un indicador global en el navbar para boletas críticas, y que el estado "Caducada" se muestra correctamente.

---

## Casos de Prueba

### 1. Orden por Vencimiento en Listado

**Descripción:** Verificar que las boletas se ordenan por fecha de vencimiento (más próxima primero).

**Pasos:**
1. Crear 3 boletas PENDING con diferentes fechas de vencimiento:
   - Boleta A: `due_date` = hoy + 5 días
   - Boleta B: `due_date` = hoy + 1 día
   - Boleta C: `due_date` = hoy + 2 días
2. Navegar a `/invoices`
3. Verificar el orden en el listado

**Resultado Esperado:**
- Las boletas aparecen ordenadas por vencimiento ascendente:
  1. Boleta B (hoy + 1 día) - vence más pronto
  2. Boleta C (hoy + 2 días)
  3. Boleta A (hoy + 5 días) - vence más tarde
- La columna "Vencimiento" muestra las fechas en formato DD/MM/YYYY

---

### 2. Boletas sin Vencimiento al Final

**Descripción:** Verificar que las boletas sin `due_date` aparecen al final del listado.

**Pasos:**
1. Crear una boleta PENDING con `due_date = NULL`
2. Crear otra boleta PENDING con `due_date = hoy + 3 días`
3. Navegar a `/invoices`
4. Verificar el orden

**Resultado Esperado:**
- Primero aparece la boleta con vencimiento (hoy + 3 días)
- Al final aparece la boleta sin vencimiento
- La columna "Vencimiento" muestra "-" para la boleta sin fecha

---

### 3. Estado "Caducada" en Listado

**Descripción:** Verificar que las boletas vencidas muestran el estado "Caducada" en rojo.

**Pasos:**
1. Crear una boleta PENDING con `due_date = ayer` (fecha pasada)
2. Navegar a `/invoices`
3. Buscar la boleta en el listado

**Resultado Esperado:**
- La fila de la boleta tiene fondo rojo claro (`table-danger`)
- En la columna "Estado" aparece badge rojo: **"Caducada"**
- NO aparece "Pendiente" (el estado "Caducada" sobrescribe "Pendiente")
- En la columna "Vencimiento" aparece un badge rojo pequeño con ícono de exclamación

---

### 4. Estado "Caducada" en Detalle

**Descripción:** Verificar que el detalle de una boleta caducada muestra el estado correcto.

**Pasos:**
1. Crear una boleta PENDING con `due_date = ayer`
2. Navegar a `/invoices/<id>` (detalle de la boleta)
3. Revisar la sección de información

**Resultado Esperado:**
- En "Estado" aparece badge rojo: **"Caducada"**
- En "Vencimiento" aparece la fecha en formato DD/MM/YYYY
- Junto a la fecha de vencimiento aparece un badge rojo: "Vencida" con ícono de exclamación
- La boleta sigue siendo pagable (botón "Pagar Boleta" visible)

---

### 5. Indicador Global en Navbar - Por Vencer

**Descripción:** Verificar que aparece un badge en el navbar cuando hay boletas por vencer mañana.

**Pasos:**
1. Crear una boleta PENDING con `due_date = mañana` (hoy + 1 día)
2. Navegar a cualquier página de la aplicación (ej: `/products`, `/sales/new`)
3. Observar el navbar

**Resultado Esperado:**
- En el dropdown "Compras" aparece un badge rojo con el número "1"
- Al hacer hover sobre "Compras", el badge es visible
- Al abrir el dropdown "Compras":
  - En el item "Boletas" aparece un badge rojo con "1"
  - Aparece un item adicional: "Por vencer (1)" con link a `/invoices?due_soon=1`
- El badge persiste en todas las páginas hasta que se pague la boleta

---

### 6. Indicador Global en Navbar - Caducadas

**Descripción:** Verificar que aparece un badge en el navbar cuando hay boletas caducadas.

**Pasos:**
1. Crear una boleta PENDING con `due_date = ayer`
2. Navegar a cualquier página
3. Observar el navbar

**Resultado Esperado:**
- En el dropdown "Compras" aparece un badge rojo con el número "1"
- Al abrir el dropdown:
  - En "Boletas" aparece badge rojo con "1"
  - Aparece un item: "Caducadas (1)" con link a `/invoices?overdue=1`
- El badge persiste hasta que se pague la boleta

---

### 7. Indicador Global - Múltiples Alertas

**Descripción:** Verificar que el badge suma correctamente cuando hay múltiples alertas.

**Pasos:**
1. Crear:
   - 2 boletas PENDING con `due_date = mañana`
   - 1 boleta PENDING con `due_date = ayer`
2. Navegar a cualquier página
3. Observar el navbar

**Resultado Esperado:**
- Badge en "Compras" muestra "3" (2 + 1)
- Al abrir dropdown:
  - "Boletas" muestra badge "3"
  - Aparece "Por vencer (2)" con link a `/invoices?due_soon=1`
  - Aparece "Caducadas (1)" con link a `/invoices?overdue=1`
- Tooltip (si existe) muestra: "2 por vencer / 1 caducada"

---

### 8. Indicador Desaparece al Pagar

**Descripción:** Verificar que el badge desaparece cuando se paga la boleta crítica.

**Pasos:**
1. Crear una boleta PENDING con `due_date = mañana`
2. Verificar que aparece el badge en navbar
3. Pagar la boleta
4. Navegar a cualquier página
5. Verificar el navbar

**Resultado Esperado:**
- El badge desaparece del navbar
- El dropdown "Compras" ya no muestra badge
- El item "Por vencer" desaparece del dropdown

---

### 9. Filtro "Por vencer (mañana)"

**Descripción:** Verificar que el filtro muestra solo boletas que vencen mañana.

**Pasos:**
1. Crear:
   - Boleta A: `due_date = mañana`, PENDING
   - Boleta B: `due_date = hoy + 3 días`, PENDING
   - Boleta C: `due_date = ayer`, PENDING
2. Navegar a `/invoices`
3. Hacer clic en el botón "Por vencer (mañana)"

**Resultado Esperado:**
- Solo aparece Boleta A en el listado
- La URL incluye `?due_soon=1`
- El botón "Por vencer (mañana)" aparece activo (highlighted)
- Las boletas están ordenadas por vencimiento (en este caso solo hay una)

---

### 10. Filtro "Caducadas"

**Descripción:** Verificar que el filtro muestra solo boletas caducadas.

**Pasos:**
1. Crear:
   - Boleta A: `due_date = ayer`, PENDING
   - Boleta B: `due_date = hace 5 días`, PENDING
   - Boleta C: `due_date = mañana`, PENDING
2. Navegar a `/invoices`
3. Hacer clic en el botón "Caducadas"

**Resultado Esperado:**
- Solo aparecen Boleta A y Boleta B
- La URL incluye `?overdue=1`
- El botón "Caducadas" aparece activo
- Ambas boletas muestran estado "Caducada" en rojo
- Las boletas están ordenadas por vencimiento (más antigua primero)

---

### 11. Filtro "Pendientes"

**Descripción:** Verificar que el filtro de pendientes funciona correctamente.

**Pasos:**
1. Crear boletas con diferentes estados y vencimientos
2. Navegar a `/invoices`
3. Hacer clic en "Pendientes"

**Resultado Esperado:**
- Muestra todas las boletas PENDING (incluyendo caducadas y por vencer)
- Están ordenadas por vencimiento
- Las caducadas muestran badge rojo "Caducada"
- Las no caducadas muestran badge amarillo "Pendiente"

---

### 12. Filtro "Todas"

**Descripción:** Verificar que el filtro "Todas" muestra todas las boletas.

**Pasos:**
1. Crear boletas PENDING y PAID
2. Navegar a `/invoices`
3. Hacer clic en "Todas"

**Resultado Esperado:**
- Muestra todas las boletas (PENDING y PAID)
- Están ordenadas por vencimiento (NULLS LAST)
- Las boletas PAID aparecen al final si no tienen vencimiento, o según su vencimiento

---

### 13. Combinación de Filtros

**Descripción:** Verificar que los filtros se pueden combinar.

**Pasos:**
1. Crear boletas con diferentes proveedores y estados
2. Navegar a `/invoices`
3. Seleccionar un proveedor en el dropdown
4. Hacer clic en "Caducadas"

**Resultado Esperado:**
- Muestra solo las boletas caducadas del proveedor seleccionado
- La URL incluye ambos parámetros: `?supplier_id=X&overdue=1`
- Los filtros funcionan correctamente combinados

---

### 14. Boletas Pagadas No Cuentan en Alertas

**Descripción:** Verificar que las boletas pagadas no aparecen en el contador de alertas.

**Pasos:**
1. Crear una boleta PENDING con `due_date = ayer`
2. Verificar que aparece en el badge del navbar
3. Pagar la boleta
4. Verificar el navbar

**Resultado Esperado:**
- Antes de pagar: badge muestra "1"
- Después de pagar: badge desaparece o muestra "0"
- La boleta pagada NO aparece en el filtro "Caducadas"
- La boleta pagada muestra estado "Pagada" (verde)

---

### 15. Live Search con Filtros de Vencimiento

**Descripción:** Verificar que la búsqueda en tiempo real funciona con los filtros de vencimiento.

**Pasos:**
1. Navegar a `/invoices`
2. Hacer clic en "Caducadas"
3. Escribir en el campo de búsqueda (sin presionar Enter)

**Resultado Esperado:**
- La búsqueda filtra dentro de las boletas caducadas
- La URL mantiene `?overdue=1&q=...`
- Los resultados se actualizan sin recargar la página

---

### 16. Orden Persiste con Filtros

**Descripción:** Verificar que el orden por vencimiento se mantiene con cualquier filtro.

**Pasos:**
1. Crear múltiples boletas con diferentes vencimientos
2. Aplicar diferentes filtros (proveedor, estado, caducadas, etc.)
3. Verificar el orden en cada caso

**Resultado Esperado:**
- En todos los casos, las boletas están ordenadas por `due_date ASC NULLS LAST`
- Las boletas sin vencimiento siempre aparecen al final
- El orden se mantiene independientemente del filtro aplicado

---

### 17. Visual de Fila Caducada

**Descripción:** Verificar que las filas caducadas tienen un resaltado visual claro.

**Pasos:**
1. Crear una boleta PENDING con `due_date = ayer`
2. Navegar a `/invoices`
3. Observar la fila de la boleta

**Resultado Esperado:**
- La fila tiene fondo rojo claro (`table-danger` de Bootstrap)
- El estado "Caducada" es claramente visible
- El badge de vencimiento con ícono es visible
- La fila se destaca visualmente del resto

---

### 18. Boletas sin Vencimiento en Filtros

**Descripción:** Verificar que las boletas sin vencimiento no aparecen en filtros de vencimiento.

**Pasos:**
1. Crear:
   - Boleta A: `due_date = NULL`, PENDING
   - Boleta B: `due_date = mañana`, PENDING
2. Aplicar filtro "Por vencer (mañana)"
3. Aplicar filtro "Caducadas"

**Resultado Esperado:**
- En "Por vencer": solo aparece Boleta B
- En "Caducadas": no aparece ninguna (Boleta A no tiene vencimiento, no cuenta como caducada)
- Boleta A solo aparece en "Todas" o "Pendientes"

---

### 19. Context Processor Funciona en Todas las Páginas

**Descripción:** Verificar que el indicador de alertas aparece en todas las páginas.

**Pasos:**
1. Crear una boleta PENDING con `due_date = mañana`
2. Navegar a diferentes páginas:
   - `/products`
   - `/sales/new`
   - `/balance`
   - `/quotes`
3. Verificar el navbar en cada página

**Resultado Esperado:**
- El badge aparece en el navbar en TODAS las páginas
- El badge muestra el mismo número en todas las páginas
- Al hacer clic en "Por vencer" desde cualquier página, redirige a `/invoices?due_soon=1`

---

### 20. Performance con Muchas Boletas

**Descripción:** Verificar que el sistema funciona correctamente con muchas boletas.

**Pasos:**
1. Crear 50+ boletas con diferentes vencimientos
2. Navegar a `/invoices`
3. Aplicar filtros y verificar tiempos de carga

**Resultado Esperado:**
- El listado carga en tiempo razonable (< 2 segundos)
- El orden por vencimiento es correcto
- El badge del navbar se calcula rápidamente
- Los filtros funcionan sin lag

---

## Verificaciones SQL (Opcional)

### Verificar Orden por Vencimiento

```sql
-- Ver boletas ordenadas por vencimiento
SELECT id, invoice_number, due_date, status, total_amount
FROM purchase_invoice
WHERE status = 'PENDING'
ORDER BY due_date ASC NULLS LAST, created_at DESC;
```

**Resultado Esperado:**
- Las boletas con `due_date` más cercano aparecen primero
- Las boletas con `due_date = NULL` aparecen al final

### Verificar Boletas Críticas

```sql
-- Boletas por vencer (mañana)
SELECT COUNT(*) 
FROM purchase_invoice
WHERE status = 'PENDING'
  AND due_date = CURRENT_DATE + INTERVAL '1 day';

-- Boletas caducadas
SELECT COUNT(*) 
FROM purchase_invoice
WHERE status = 'PENDING'
  AND due_date < CURRENT_DATE
  AND due_date IS NOT NULL;
```

**Resultado Esperado:**
- Los conteos coinciden con los mostrados en el navbar

### Verificar Estado Caducada

```sql
-- Ver boletas caducadas
SELECT id, invoice_number, due_date, status
FROM purchase_invoice
WHERE status = 'PENDING'
  AND due_date < CURRENT_DATE
  AND due_date IS NOT NULL
ORDER BY due_date ASC;
```

**Resultado Esperado:**
- Solo aparecen boletas PENDING con fecha pasada
- Las boletas PAID no aparecen aunque tengan fecha pasada

---

## Checklist Final

- [ ] Orden por vencimiento funciona (más próxima primero)
- [ ] Boletas sin vencimiento aparecen al final
- [ ] Estado "Caducada" se muestra en rojo en listado
- [ ] Estado "Caducada" se muestra en rojo en detalle
- [ ] Filas caducadas tienen fondo rojo claro
- [ ] Badge en navbar aparece cuando hay boletas por vencer
- [ ] Badge en navbar aparece cuando hay boletas caducadas
- [ ] Badge suma correctamente múltiples alertas
- [ ] Badge desaparece al pagar boleta crítica
- [ ] Filtro "Por vencer (mañana)" funciona
- [ ] Filtro "Caducadas" funciona
- [ ] Filtro "Pendientes" funciona
- [ ] Filtro "Todas" funciona
- [ ] Filtros se pueden combinar
- [ ] Live search funciona con filtros de vencimiento
- [ ] Orden persiste con todos los filtros
- [ ] Boletas pagadas no cuentan en alertas
- [ ] Boletas sin vencimiento no aparecen en filtros de vencimiento
- [ ] Context processor funciona en todas las páginas
- [ ] Performance aceptable con muchas boletas
- [ ] Columna "Vencimiento" muestra "-" cuando es NULL
- [ ] Fechas se muestran en formato DD/MM/YYYY

---

## Conclusión

Este documento cubre todos los casos de prueba necesarios para validar la mejora 21.  
Cada caso debe ejecutarse manualmente para confirmar que la implementación es correcta y robusta.

Para reportar bugs, incluir:
- Caso de prueba que falló
- Pasos para reproducir
- Resultado esperado vs resultado real
- Screenshots/logs si aplica
