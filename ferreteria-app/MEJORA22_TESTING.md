# MEJORA 22: Editar Presupuesto (Quotes) con Transacción, Validaciones y UI Completa

## Objetivo
Verificar que la funcionalidad de editar presupuestos funciona correctamente, permitiendo modificar líneas, datos generales y manteniendo precios congelados.

---

## Casos de Prueba

### 1. Acceso a Edición - Presupuesto DRAFT

**Descripción:** Verificar que se puede acceder a editar un presupuesto en estado DRAFT.

**Pasos:**
1. Crear un presupuesto con estado DRAFT
2. Navegar a `/quotes/<id>` (detalle)
3. Verificar que aparece el botón "Editar Presupuesto"

**Resultado Esperado:**
- El botón "Editar Presupuesto" es visible
- Al hacer clic, redirige a `/quotes/<id>/edit`
- El formulario de edición se carga correctamente

---

### 2. Acceso a Edición - Presupuesto SENT

**Descripción:** Verificar que se puede acceder a editar un presupuesto en estado SENT.

**Pasos:**
1. Crear un presupuesto DRAFT
2. Marcarlo como SENT
3. Navegar a `/quotes/<id>`
4. Verificar que aparece el botón "Editar Presupuesto"

**Resultado Esperado:**
- El botón "Editar Presupuesto" es visible
- Se puede acceder al formulario de edición

---

### 3. Bloqueo de Edición - Presupuesto ACCEPTED

**Descripción:** Verificar que NO se puede editar un presupuesto ya convertido a venta.

**Pasos:**
1. Crear un presupuesto DRAFT
2. Convertirlo a venta (ACCEPTED)
3. Navegar a `/quotes/<id>`
4. Intentar acceder a `/quotes/<id>/edit` directamente

**Resultado Esperado:**
- NO aparece el botón "Editar Presupuesto" en el detalle
- Si se intenta acceder directamente a `/quotes/<id>/edit`:
  - Flash message: "El presupuesto está en estado ACCEPTED. Solo se pueden editar presupuestos en estado DRAFT o SENT."
  - Redirect a `/quotes/<id>`

---

### 4. Bloqueo de Edición - Presupuesto CANCELED

**Descripción:** Verificar que NO se puede editar un presupuesto cancelado.

**Pasos:**
1. Crear un presupuesto DRAFT
2. Cancelarlo (CANCELED)
3. Intentar acceder a `/quotes/<id>/edit`

**Resultado Esperado:**
- NO aparece el botón "Editar Presupuesto"
- Si se intenta acceder directamente:
  - Flash message: "El presupuesto está en estado CANCELED. Solo se pueden editar presupuestos en estado DRAFT o SENT."
  - Redirect a `/quotes/<id>`

---

### 5. Bloqueo de Edición - Presupuesto Vencido

**Descripción:** Verificar que NO se puede editar un presupuesto vencido.

**Pasos:**
1. Crear un presupuesto DRAFT con `valid_until = ayer`
2. Intentar acceder a `/quotes/<id>/edit`

**Resultado Esperado:**
- NO aparece el botón "Editar Presupuesto"
- Si se intenta acceder directamente:
  - Flash message: "Este presupuesto está vencido (válido hasta DD/MM/YYYY). No se puede editar."
  - Redirect a `/quotes/<id>`

---

### 6. Editar Notas

**Descripción:** Verificar que se pueden editar las notas del presupuesto.

**Pasos:**
1. Crear un presupuesto DRAFT con notas "Notas originales"
2. Ir a `/quotes/<id>/edit`
3. Modificar el campo "Notas" a "Notas actualizadas"
4. Hacer clic en "Revisar y Guardar"
5. En el modal, verificar que muestra el cambio
6. Confirmar cambios

**Resultado Esperado:**
- El modal muestra: "Notas: Notas originales → Notas actualizadas"
- Al confirmar:
  - Flash message: "Presupuesto actualizado exitosamente"
  - Redirect a `/quotes/<id>`
  - En el detalle, las notas muestran "Notas actualizadas"

---

### 7. Editar Método de Pago

**Descripción:** Verificar que se puede cambiar el método de pago.

**Pasos:**
1. Crear un presupuesto DRAFT con `payment_method = CASH`
2. Ir a `/quotes/<id>/edit`
3. Cambiar método de pago a "Transferencia"
4. Revisar y guardar

**Resultado Esperado:**
- El modal muestra el cambio de método de pago
- Al confirmar, el presupuesto se actualiza con `payment_method = TRANSFER`
- En el detalle, se muestra "Transferencia"

---

### 8. Editar Fecha de Validez

**Descripción:** Verificar que se puede modificar la fecha de validez.

**Pasos:**
1. Crear un presupuesto DRAFT con `valid_until = hoy + 7 días`
2. Ir a `/quotes/<id>/edit`
3. Cambiar `valid_until` a `hoy + 14 días`
4. Revisar y guardar

**Resultado Esperado:**
- El modal muestra el cambio de fecha
- Al confirmar, el presupuesto se actualiza
- En el detalle, se muestra la nueva fecha

---

### 9. Validación: Fecha de Validez Anterior a Emisión

**Descripción:** Verificar que no se puede poner una fecha de validez anterior a la fecha de emisión.

**Pasos:**
1. Crear un presupuesto DRAFT emitido hoy
2. Ir a `/quotes/<id>/edit`
3. Intentar poner `valid_until = ayer`
4. Revisar y guardar

**Resultado Esperado:**
- Flash message: "La fecha de validez (DD/MM/YYYY) no puede ser anterior a la fecha de emisión (DD/MM/YYYY)."
- No se guarda el cambio
- Permanece en el formulario de edición

---

### 10. Aumentar Cantidad de Línea Existente

**Descripción:** Verificar que al aumentar la cantidad, el precio unitario se mantiene congelado.

**Pasos:**
1. Crear un presupuesto DRAFT con:
   - Producto A: qty=10, unit_price=150 (snapshot)
2. Cambiar el precio de venta del Producto A en el catálogo a 200
3. Ir a `/quotes/<id>/edit`
4. Modificar la cantidad de Producto A a 15
5. Revisar y guardar

**Resultado Esperado:**
- En el formulario, el precio unitario muestra $150 (precio congelado, no $200)
- El subtotal se recalcula: 15 * 150 = 2250
- El modal muestra: "Producto A: Cantidad: 10 → 15, Subtotal: $1.500 → $2.250"
- Al confirmar:
  - La línea mantiene `unit_price = 150` (no 200)
  - El total se actualiza correctamente

---

### 11. Disminuir Cantidad de Línea Existente

**Descripción:** Verificar que al disminuir la cantidad, el precio se mantiene.

**Pasos:**
1. Crear un presupuesto DRAFT con:
   - Producto A: qty=10, unit_price=150
2. Ir a `/quotes/<id>/edit`
3. Modificar la cantidad a 5
4. Revisar y guardar

**Resultado Esperado:**
- El precio unitario sigue siendo $150
- El subtotal se recalcula: 5 * 150 = 750
- El modal muestra el cambio
- Al confirmar, la línea se actualiza correctamente

---

### 12. Eliminar Línea Existente

**Descripción:** Verificar que se puede eliminar una línea del presupuesto.

**Pasos:**
1. Crear un presupuesto DRAFT con 3 líneas:
   - Producto A: qty=10, unit_price=150
   - Producto B: qty=5, unit_price=200
   - Producto C: qty=2, unit_price=100
2. Ir a `/quotes/<id>/edit`
3. Hacer clic en el botón "Eliminar" de Producto B
4. Revisar y guardar

**Resultado Esperado:**
- Producto B desaparece de la lista
- El modal muestra: "Productos Eliminados: Producto B - Cantidad: 5 - Subtotal: $1.000"
- El total se recalcula (sin incluir Producto B)
- Al confirmar:
  - Solo quedan Producto A y Producto C en el presupuesto
  - El total es correcto

---

### 13. Agregar Producto Nuevo

**Descripción:** Verificar que al agregar un producto nuevo, usa el precio actual del catálogo.

**Pasos:**
1. Crear un presupuesto DRAFT con:
   - Producto A: qty=10, unit_price=150
2. Verificar que Producto B tiene `sale_price = 200` en el catálogo
3. Ir a `/quotes/<id>/edit`
4. Agregar Producto B con cantidad 3
5. Revisar y guardar

**Resultado Esperado:**
- En el formulario, Producto B muestra precio $200 (precio actual, no congelado)
- El subtotal es: 3 * 200 = 600
- El modal muestra: "Productos Agregados: Producto B - Cantidad: 3 - Precio: $200 - Subtotal: $600"
- Al confirmar:
  - Se crea nueva línea con `unit_price = 200`
  - `product_name_snapshot = product.name` (actual)
  - El total incluye el nuevo producto

---

### 14. Precio Congelado vs Precio Actual

**Descripción:** Verificar la lógica de precios congelados vs actuales.

**Pasos:**
1. Crear un presupuesto DRAFT con:
   - Producto A: qty=10, unit_price=150 (snapshot)
2. Cambiar `product.sale_price` de Producto A a 200 en el catálogo
3. Ir a `/quotes/<id>/edit`
4. Agregar Producto B (nuevo) con cantidad 5
5. Verificar precios en el formulario

**Resultado Esperado:**
- Producto A (existente): precio muestra $150 (congelado)
- Producto B (nuevo): precio muestra $200 (actual del catálogo)
- Al guardar:
  - Producto A mantiene `unit_price = 150`
  - Producto B tiene `unit_price = 200` (precio actual)

---

### 15. Total Recalculado Correctamente

**Descripción:** Verificar que el total se recalcula correctamente al modificar líneas.

**Pasos:**
1. Crear un presupuesto DRAFT con:
   - Producto A: qty=10, unit_price=150 → subtotal=1500
   - Producto B: qty=5, unit_price=200 → subtotal=1000
   - Total: 2500
2. Ir a `/quotes/<id>/edit`
3. Modificar:
   - Producto A: qty=15 (subtotal nuevo: 2250)
   - Eliminar Producto B
4. Revisar y guardar

**Resultado Esperado:**
- Total anterior: $2.500
- Total nuevo: $2.250
- Diferencia: -$250
- El modal muestra correctamente los totales
- Al confirmar, el presupuesto tiene `total_amount = 2250`

---

### 16. Modal Preview - Sin Cambios

**Descripción:** Verificar que si no hay cambios, no se abre el modal.

**Pasos:**
1. Crear un presupuesto DRAFT
2. Ir a `/quotes/<id>/edit`
3. NO hacer ningún cambio
4. Hacer clic en "Revisar y Guardar"

**Resultado Esperado:**
- NO se abre el modal
- Se muestra mensaje: "No hay cambios para aplicar."
- Permanece en el formulario

---

### 17. Modal Preview - Cancelar

**Descripción:** Verificar que cancelar no guarda cambios.

**Pasos:**
1. Crear un presupuesto DRAFT
2. Ir a `/quotes/<id>/edit`
3. Modificar notas
4. Revisar y guardar (abre modal)
5. En el modal, hacer clic en "Cancelar"

**Resultado Esperado:**
- El modal se cierra
- NO se guardan los cambios
- Permanece en el formulario de edición
- Los cambios en el formulario se mantienen (no se pierden)

---

### 18. Modal Preview - Confirmar

**Descripción:** Verificar que confirmar guarda los cambios.

**Pasos:**
1. Crear un presupuesto DRAFT con notas "Original"
2. Ir a `/quotes/<id>/edit`
3. Cambiar notas a "Actualizado"
4. Revisar y guardar
5. En el modal, hacer clic en "Confirmar Cambios"

**Resultado Esperado:**
- El botón muestra "Procesando..." y se deshabilita
- Flash message: "Presupuesto actualizado exitosamente"
- Redirect a `/quotes/<id>`
- En el detalle, las notas muestran "Actualizado"

---

### 19. Validación: Líneas Vacías

**Descripción:** Verificar que no se puede guardar sin líneas.

**Pasos:**
1. Crear un presupuesto DRAFT con 1 línea
2. Ir a `/quotes/<id>/edit`
3. Eliminar la única línea
4. Intentar revisar y guardar

**Resultado Esperado:**
- Flash message: "Debe agregar al menos una línea."
- No se abre el modal
- Permanece en el formulario

---

### 20. Validación: Cantidad <= 0

**Descripción:** Verificar que no se puede poner cantidad <= 0.

**Pasos:**
1. Crear un presupuesto DRAFT
2. Ir a `/quotes/<id>/edit`
3. Modificar cantidad de una línea a 0
4. Intentar revisar y guardar

**Resultado Esperado:**
- Flash message: "La cantidad debe ser mayor a 0 en la línea X."
- No se abre el modal
- Permanece en el formulario

---

### 21. Validación: Producto Inactivo

**Descripción:** Verificar que no se puede agregar un producto inactivo.

**Pasos:**
1. Desactivar un producto en el catálogo
2. Crear un presupuesto DRAFT
3. Ir a `/quotes/<id>/edit`
4. Intentar agregar el producto inactivo

**Resultado Esperado:**
- El producto inactivo NO aparece en el selector (o aparece deshabilitado)
- Si se intenta agregar de otra forma:
  - Flash message: "El producto 'X' está inactivo y no puede agregarse."
  - No se agrega a las líneas

---

### 22. Validación: Producto Duplicado

**Descripción:** Verificar que no se puede agregar el mismo producto dos veces.

**Pasos:**
1. Crear un presupuesto DRAFT con Producto A
2. Ir a `/quotes/<id>/edit`
3. Intentar agregar Producto A nuevamente

**Resultado Esperado:**
- JavaScript muestra alert: "Este producto ya está en las líneas. Modifique la cantidad de la línea existente."
- No se agrega duplicado
- Se puede modificar la cantidad de la línea existente

---

### 23. Product Name Snapshot Preservado

**Descripción:** Verificar que el snapshot del nombre se preserva para líneas existentes.

**Pasos:**
1. Crear un presupuesto DRAFT con:
   - Producto A: nombre "Cable 2.5mm" (snapshot)
2. Cambiar el nombre del Producto A en el catálogo a "Cable Unipolar 2.5mm"
3. Ir a `/quotes/<id>/edit`
4. Modificar cantidad de Producto A
5. Guardar

**Resultado Esperado:**
- En el formulario, se muestra "Cable 2.5mm" (snapshot, no el nombre nuevo)
- Al guardar, `product_name_snapshot` sigue siendo "Cable 2.5mm"
- El PDF del presupuesto muestra "Cable 2.5mm"

---

### 24. Product Name Snapshot para Productos Nuevos

**Descripción:** Verificar que los productos nuevos usan el nombre actual como snapshot.

**Pasos:**
1. Crear un presupuesto DRAFT
2. Ir a `/quotes/<id>/edit`
3. Agregar Producto B (nombre actual: "Tornillo 8mm")
4. Guardar
5. Cambiar el nombre de Producto B a "Tornillo Cabeza Fresada 8mm"
6. Ver el presupuesto editado

**Resultado Esperado:**
- El presupuesto muestra "Tornillo 8mm" (snapshot al momento de agregar)
- NO muestra "Tornillo Cabeza Fresada 8mm" (nombre nuevo)

---

### 25. Transacción Atómica

**Descripción:** Verificar que los cambios se aplican de forma atómica.

**Pasos:**
1. Crear un presupuesto DRAFT con 2 líneas
2. Ir a `/quotes/<id>/edit`
3. Modificar líneas y agregar una nueva
4. Guardar cambios
5. Verificar en BD

**Resultado Esperado:**
- Todas las líneas viejas se eliminan
- Todas las líneas nuevas se insertan
- El total se actualiza
- Los metadatos se actualizan
- Todo ocurre en una sola transacción (todo o nada)

---

### 26. Lock de Quote Row

**Descripción:** Verificar que se usa lock FOR UPDATE para evitar condiciones de carrera.

**Pasos:**
1. Crear un presupuesto DRAFT
2. Abrir dos pestañas con `/quotes/<id>/edit`
3. En ambas pestañas, modificar diferentes campos
4. Guardar en ambas casi simultáneamente

**Resultado Esperado:**
- Una de las transacciones espera a que la otra termine
- No hay pérdida de datos
- Los cambios se aplican correctamente

---

### 27. Recalcular Total Server-Side

**Descripción:** Verificar que el total se recalcula en el servidor, no se confía en el cliente.

**Pasos:**
1. Crear un presupuesto DRAFT
2. Ir a `/quotes/<id>/edit`
3. Modificar manualmente el HTML para cambiar el total mostrado (manipulación)
4. Guardar cambios

**Resultado Esperado:**
- El total se recalcula en el servidor
- El total guardado es correcto (no el manipulado)
- No hay vulnerabilidad de seguridad

---

### 28. UI - Agregar Producto con JavaScript

**Descripción:** Verificar que el JavaScript funciona correctamente para agregar productos.

**Pasos:**
1. Ir a `/quotes/<id>/edit`
2. Seleccionar un producto del dropdown
3. Ingresar cantidad
4. Hacer clic en "Agregar a Líneas"

**Resultado Esperado:**
- El producto se agrega a la lista de líneas
- Se muestra nombre, SKU, UOM
- Se muestra precio actual (no congelado)
- Se calcula subtotal automáticamente
- El total se actualiza
- El formulario de agregar se limpia

---

### 29. UI - Eliminar Línea con JavaScript

**Descripción:** Verificar que se puede eliminar líneas dinámicamente.

**Pasos:**
1. Ir a `/quotes/<id>/edit`
2. Agregar varias líneas
3. Hacer clic en "Eliminar" de una línea

**Resultado Esperado:**
- La línea desaparece de la lista
- Los índices se reindexan correctamente
- El total se recalcula
- Los inputs mantienen nombres correctos: `lines[0][product_id]`, `lines[1][product_id]`, etc.

---

### 30. UI - Actualizar Subtotal al Cambiar Cantidad

**Descripción:** Verificar que el subtotal se actualiza automáticamente.

**Pasos:**
1. Ir a `/quotes/<id>/edit`
2. Modificar la cantidad de una línea existente
3. Observar el subtotal

**Resultado Esperado:**
- El subtotal se actualiza inmediatamente
- El total se recalcula
- Los cálculos son correctos

---

## Verificaciones SQL (Opcional)

### Verificar Líneas Actualizadas

```sql
-- Ver líneas del presupuesto después de editar
SELECT ql.id, ql.product_id, ql.product_name_snapshot, ql.qty, ql.unit_price, ql.line_total
FROM quote_line ql
WHERE ql.quote_id = [ID_PRESUPUESTO]
ORDER BY ql.id;
```

**Resultado Esperado:**
- Las líneas viejas fueron eliminadas
- Las líneas nuevas tienen los datos correctos
- `product_name_snapshot` es correcto
- `unit_price` es correcto (congelado para existentes, actual para nuevos)

### Verificar Total Actualizado

```sql
-- Ver total del presupuesto
SELECT id, quote_number, total_amount, payment_method, valid_until, notes
FROM quote
WHERE id = [ID_PRESUPUESTO];
```

**Resultado Esperado:**
- `total_amount` coincide con la suma de `line_total` de todas las líneas
- `payment_method`, `valid_until`, `notes` se actualizaron correctamente

### Verificar Precios Congelados

```sql
-- Comparar precio en presupuesto vs precio actual del producto
SELECT 
    ql.product_id,
    ql.product_name_snapshot,
    ql.unit_price AS price_in_quote,
    p.name AS current_product_name,
    p.sale_price AS current_sale_price
FROM quote_line ql
JOIN product p ON p.id = ql.product_id
WHERE ql.quote_id = [ID_PRESUPUESTO];
```

**Resultado Esperado:**
- Para productos que existían antes: `price_in_quote` puede ser diferente de `current_sale_price` (congelado)
- Para productos nuevos: `price_in_quote` = `current_sale_price` (o muy cercano)

---

## Checklist Final

- [ ] Acceso a edición funciona para DRAFT
- [ ] Acceso a edición funciona para SENT
- [ ] Bloqueo correcto para ACCEPTED
- [ ] Bloqueo correcto para CANCELED
- [ ] Bloqueo correcto para vencidos
- [ ] Editar notas funciona
- [ ] Editar método de pago funciona
- [ ] Editar fecha de validez funciona
- [ ] Validación: fecha validez >= emisión
- [ ] Aumentar cantidad mantiene precio congelado
- [ ] Disminuir cantidad mantiene precio congelado
- [ ] Eliminar línea funciona
- [ ] Agregar producto nuevo usa precio actual
- [ ] Precio congelado vs actual funciona correctamente
- [ ] Total recalculado correctamente
- [ ] Modal preview sin cambios muestra mensaje
- [ ] Cancelar modal no guarda
- [ ] Confirmar modal guarda cambios
- [ ] Validación: líneas vacías
- [ ] Validación: cantidad <= 0
- [ ] Validación: producto inactivo
- [ ] Validación: producto duplicado
- [ ] Product name snapshot preservado para existentes
- [ ] Product name snapshot correcto para nuevos
- [ ] Transacción atómica
- [ ] Lock de quote row funciona
- [ ] Total recalculado server-side
- [ ] UI: agregar producto funciona
- [ ] UI: eliminar línea funciona
- [ ] UI: actualizar subtotal funciona

---

## Conclusión

Este documento cubre todos los casos de prueba necesarios para validar la funcionalidad de edición de presupuestos.  
Cada caso debe ejecutarse manualmente para confirmar que la implementación es correcta y robusta.

Para reportar bugs, incluir:
- Caso de prueba que falló
- Pasos para reproducir
- Resultado esperado vs resultado real
- Screenshots/logs si aplica
