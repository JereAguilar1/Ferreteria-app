# MEJORA 20: Modal de Confirmación para Creación de Boleta

## Objetivo
Verificar que el modal de confirmación funciona correctamente antes de crear una boleta de compra, mostrando todos los detalles y permitiendo revisar antes de confirmar.

---

## Casos de Prueba

### 1. Abrir Modal con Draft Completo

**Descripción:** Verificar que el modal se abre correctamente cuando el draft tiene todos los datos necesarios.

**Pasos:**
1. Navegar a `/invoices/new`
2. Seleccionar un proveedor del dropdown
3. Ingresar número de boleta (ej: "FAC-2026-001")
4. Seleccionar fecha de boleta
5. Agregar al menos un ítem:
   - Seleccionar producto
   - Ingresar cantidad (ej: 10)
   - Ingresar costo unitario entero (ej: 150)
   - Hacer clic en "Agregar Ítem"
6. Verificar que el ítem aparece en la tabla
7. Hacer clic en "Revisar y Confirmar"

**Resultado Esperado:**
- Se abre un modal Bootstrap con título "Confirmar Creación de Boleta"
- El modal muestra:
  - **Proveedor:** Nombre del proveedor seleccionado
  - **Nº Boleta:** El número ingresado
  - **Fecha Boleta:** Fecha en formato DD/MM/YYYY
  - **Vencimiento:** Si fue ingresado, en formato DD/MM/YYYY
  - **Total:** Monto total en formato argentino (ej: $1.500)
- Tabla de ítems con:
  - Producto (nombre + SKU + UOM)
  - Cantidad (formato argentino)
  - Costo Unit. (formato argentino, sin decimales)
  - Subtotal (formato argentino)
  - Total final destacado
- Advertencia: "Al confirmar, se registrará automáticamente un INGRESO de stock..."
- Botones: "Cancelar" y "Confirmar Creación"

---

### 2. Validación: Falta Proveedor

**Descripción:** Verificar que no se abre el modal si falta el proveedor.

**Pasos:**
1. Navegar a `/invoices/new`
2. NO seleccionar proveedor
3. Ingresar número de boleta
4. Seleccionar fecha
5. Agregar un ítem
6. Hacer clic en "Revisar y Confirmar"

**Resultado Esperado:**
- NO se abre el modal
- Se muestra un alert de error: "Debe seleccionar un proveedor"
- El formulario permanece visible

---

### 3. Validación: Falta Número de Boleta

**Descripción:** Verificar que no se abre el modal si falta el número de boleta.

**Pasos:**
1. Navegar a `/invoices/new`
2. Seleccionar proveedor
3. NO ingresar número de boleta (dejar vacío)
4. Seleccionar fecha
5. Agregar un ítem
6. Hacer clic en "Revisar y Confirmar"

**Resultado Esperado:**
- NO se abre el modal
- Se muestra un alert de error: "El número de boleta es requerido"
- El formulario permanece visible

---

### 4. Validación: Falta Fecha

**Descripción:** Verificar que no se abre el modal si falta la fecha de boleta.

**Pasos:**
1. Navegar a `/invoices/new`
2. Seleccionar proveedor
3. Ingresar número de boleta
4. NO seleccionar fecha (dejar vacío)
5. Agregar un ítem
6. Hacer clic en "Revisar y Confirmar"

**Resultado Esperado:**
- NO se abre el modal
- Se muestra un alert de error: "La fecha de boleta es requerida"
- El formulario permanece visible

---

### 5. Validación: Sin Ítems

**Descripción:** Verificar que no se abre el modal si no hay ítems agregados.

**Pasos:**
1. Navegar a `/invoices/new`
2. Seleccionar proveedor
3. Ingresar número de boleta
4. Seleccionar fecha
5. NO agregar ningún ítem
6. Hacer clic en "Revisar y Confirmar"

**Resultado Esperado:**
- NO se abre el modal
- Se muestra un alert de error: "Debe agregar al menos un ítem a la boleta"
- El formulario permanece visible

---

### 6. Validación Múltiple

**Descripción:** Verificar que se muestran todos los errores si faltan múltiples campos.

**Pasos:**
1. Navegar a `/invoices/new`
2. NO seleccionar proveedor
3. NO ingresar número de boleta
4. NO seleccionar fecha
5. NO agregar ítems
6. Hacer clic en "Revisar y Confirmar"

**Resultado Esperado:**
- NO se abre el modal
- Se muestra un alert con lista de errores:
  - "Debe seleccionar un proveedor"
  - "El número de boleta es requerido"
  - "La fecha de boleta es requerida"
  - "Debe agregar al menos un ítem a la boleta"

---

### 7. Cancelar Creación

**Descripción:** Verificar que cancelar no crea la boleta.

**Pasos:**
1. Completar el draft con todos los datos
2. Hacer clic en "Revisar y Confirmar"
3. En el modal, hacer clic en "Cancelar"

**Resultado Esperado:**
- El modal se cierra
- NO se crea ninguna boleta
- El formulario permanece con los datos ingresados
- El draft en session se mantiene intacto
- No hay redirect

---

### 8. Confirmar Creación

**Descripción:** Verificar que confirmar crea la boleta correctamente.

**Pasos:**
1. Completar el draft con:
   - Proveedor: "Proveedor Test"
   - Número: "FAC-2026-001"
   - Fecha: Hoy
   - Ítem 1: Producto A, cantidad 10, costo 150
   - Ítem 2: Producto B, cantidad 5, costo 200
2. Hacer clic en "Revisar y Confirmar"
3. En el modal, verificar que los datos son correctos
4. Hacer clic en "Confirmar Creación"

**Resultado Esperado:**
- El botón muestra "Procesando..." y se deshabilita
- Se crea la boleta en la BD:
  - `purchase_invoice` con supplier_id, invoice_number, invoice_date correctos
  - `purchase_invoice_line` con 2 líneas (producto A y B)
  - `stock_move` tipo IN
  - `stock_move_line` para cada producto con qty correcta
- Se actualiza `product_stock`:
  - Producto A: stock aumenta en 10
  - Producto B: stock aumenta en 5
- Flash message: "Boleta creada exitosamente"
- Redirect a `/invoices/<id>` (detalle de la boleta creada)
- El draft en session se limpia

---

### 9. Totales Correctos en Modal

**Descripción:** Verificar que los totales en el modal coinciden con los del formulario.

**Pasos:**
1. Crear draft con múltiples ítems:
   - Ítem 1: qty=10, unit_cost=150 → subtotal=1500
   - Ítem 2: qty=5, unit_cost=200 → subtotal=1000
   - Total esperado: 2500
2. Hacer clic en "Revisar y Confirmar"
3. Verificar totales en el modal

**Resultado Esperado:**
- Cada línea muestra subtotal correcto:
  - Línea 1: $1.500 (formato argentino)
  - Línea 2: $1.000 (formato argentino)
- Total final: $2.500 (formato argentino)
- Los totales coinciden exactamente con los del formulario

---

### 10. Formato Argentino en Modal

**Descripción:** Verificar que todos los números se muestran en formato argentino.

**Pasos:**
1. Crear draft con:
   - Ítem: qty=10.5, unit_cost=1500 → subtotal=15750
2. Hacer clic en "Revisar y Confirmar"
3. Observar formato en el modal

**Resultado Esperado:**
- Cantidad: `10,5` (coma decimal)
- Costo unitario: `$1.500` (punto miles, sin decimales porque es entero)
- Subtotal: `$15.750` (punto miles)
- Total: `$15.750` (punto miles)
- Fechas: `DD/MM/YYYY`

---

### 11. Múltiples Ítems en Modal

**Descripción:** Verificar que el modal muestra correctamente múltiples ítems.

**Pasos:**
1. Agregar 5 ítems diferentes al draft
2. Hacer clic en "Revisar y Confirmar"
3. Revisar la tabla en el modal

**Resultado Esperado:**
- La tabla muestra las 5 líneas
- Cada línea tiene:
  - Nombre del producto
  - SKU (si existe) o "-"
  - Símbolo de UOM
  - Cantidad, costo unitario y subtotal correctos
- El encabezado muestra: "Detalle de Ítems (5)"
- El total es la suma de los 5 subtotales

---

### 12. Prevención de Doble Click

**Descripción:** Verificar que no se puede hacer doble click en "Confirmar Creación".

**Pasos:**
1. Completar draft y abrir modal
2. Hacer doble click rápido en "Confirmar Creación"

**Resultado Esperado:**
- Tras el primer click:
  - El botón se deshabilita
  - Muestra spinner: "Procesando..."
- Solo se crea UNA boleta (no duplicados)
- No hay errores de integridad

---

### 13. Producto No Encontrado

**Descripción:** Verificar manejo cuando un producto del draft ya no existe.

**Pasos:**
1. Agregar un producto al draft
2. Eliminar o desactivar ese producto desde otra pestaña
3. Hacer clic en "Revisar y Confirmar"

**Resultado Esperado:**
- El modal se abre pero NO muestra el producto eliminado
- Solo muestra los productos que aún existen
- El total se recalcula sin incluir el producto eliminado
- Si todos los productos fueron eliminados, muestra error: "Debe agregar al menos un ítem"

---

### 14. Proveedor No Encontrado

**Descripción:** Verificar manejo cuando el proveedor del draft ya no existe.

**Pasos:**
1. Seleccionar un proveedor y completar el draft
2. Eliminar ese proveedor desde otra pestaña
3. Hacer clic en "Revisar y Confirmar"

**Resultado Esperado:**
- NO se abre el modal
- Se muestra error: "Proveedor no encontrado"
- El formulario permanece visible

---

### 15. Fecha Inválida en Draft

**Descripción:** Verificar manejo cuando la fecha en el draft tiene formato inválido.

**Pasos:**
1. Manipular el draft en session para tener fecha inválida
2. Hacer clic en "Revisar y Confirmar"

**Resultado Esperado:**
- NO se abre el modal
- Se muestra error: "Fecha inválida en el draft"
- El formulario permanece visible

---

### 16. Integración con Stock

**Descripción:** Verificar que al confirmar, el stock se actualiza correctamente.

**Pasos:**
1. Verificar stock inicial de un producto (ej: Producto A tiene 50 unidades)
2. Crear boleta con:
   - Producto A: cantidad 10, costo 150
3. Abrir modal y confirmar
4. Verificar stock después

**Resultado Esperado:**
- Stock de Producto A aumenta de 50 a 60
- Existe un `stock_move` tipo IN
- Existe un `stock_move_line` con qty=10
- `product_stock.on_hand_qty` se actualiza correctamente

---

### 17. Costo Unitario Entero

**Descripción:** Verificar que el costo unitario se muestra sin decimales (ya implementado en MEJORA 4).

**Pasos:**
1. Agregar ítem con unit_cost=150 (entero)
2. Abrir modal

**Resultado Esperado:**
- En el modal, costo unitario se muestra como `$150` (no `$150,00`)
- Si unit_cost=1500, se muestra como `$1.500` (punto miles)

---

### 18. Advertencia de Stock Visible

**Descripción:** Verificar que la advertencia sobre stock es clara.

**Pasos:**
1. Completar draft y abrir modal
2. Revisar la sección de advertencia

**Resultado Esperado:**
- Hay un alert warning (amarillo) con ícono de exclamación
- Texto: "Al confirmar, se registrará automáticamente un INGRESO de stock para cada producto y se creará la boleta en el sistema."
- Es visible y claro

---

### 19. Modal Responsive

**Descripción:** Verificar que el modal se ve bien en diferentes tamaños de pantalla.

**Pasos:**
1. Completar draft y abrir modal
2. Redimensionar la ventana del navegador

**Resultado Esperado:**
- El modal se adapta correctamente
- La tabla es responsive (scroll horizontal si es necesario)
- Los botones son accesibles
- No se rompe el layout

---

### 20. Limpieza de Modal al Cerrar

**Descripción:** Verificar que el modal se limpia del DOM al cerrarse.

**Pasos:**
1. Abrir modal
2. Cerrar modal (Cancelar o X)
3. Abrir modal nuevamente

**Resultado Esperado:**
- El modal se elimina del DOM al cerrarse
- Al abrir nuevamente, se crea un nuevo modal
- No hay duplicados ni elementos residuales

---

## Verificaciones SQL (Opcional)

### Verificar Boleta Creada

```sql
-- Ver la boleta recién creada
SELECT id, supplier_id, invoice_number, invoice_date, total_amount, status
FROM purchase_invoice
ORDER BY id DESC
LIMIT 1;

-- Ver las líneas
SELECT pil.id, pil.product_id, pil.qty, pil.unit_cost, pil.line_total
FROM purchase_invoice_line pil
JOIN purchase_invoice pi ON pi.id = pil.invoice_id
WHERE pi.id = [ID_BOLETA]
ORDER BY pil.id;
```

### Verificar Stock Actualizado

```sql
-- Ver stock antes y después
SELECT ps.product_id, p.name, ps.on_hand_qty
FROM product_stock ps
JOIN product p ON p.id = ps.product_id
WHERE ps.product_id IN ([ID_PRODUCTO_1], [ID_PRODUCTO_2]);
```

### Verificar Movimientos de Stock

```sql
-- Ver stock_move IN creado
SELECT sm.id, sm.type, sm.date, sm.reference_type, sm.reference_id
FROM stock_move sm
WHERE sm.reference_type = 'INVOICE'
ORDER BY sm.id DESC
LIMIT 1;

-- Ver stock_move_line
SELECT sml.id, sml.product_id, sml.qty, p.name
FROM stock_move_line sml
JOIN stock_move sm ON sm.id = sml.stock_move_id
JOIN product p ON p.id = sml.product_id
WHERE sm.id = [ID_STOCK_MOVE]
ORDER BY sml.id;
```

---

## Checklist Final

- [ ] Modal se abre con draft completo
- [ ] Validación: falta proveedor → no abre modal
- [ ] Validación: falta número → no abre modal
- [ ] Validación: falta fecha → no abre modal
- [ ] Validación: sin ítems → no abre modal
- [ ] Validación múltiple muestra todos los errores
- [ ] Cancelar no crea boleta
- [ ] Confirmar crea boleta correctamente
- [ ] Totales correctos en modal
- [ ] Formato argentino en todos los números
- [ ] Múltiples ítems se muestran correctamente
- [ ] Prevención de doble click funciona
- [ ] Producto no encontrado se maneja
- [ ] Proveedor no encontrado se maneja
- [ ] Fecha inválida se maneja
- [ ] Stock se actualiza al confirmar
- [ ] Costo unitario sin decimales
- [ ] Advertencia de stock visible
- [ ] Modal responsive
- [ ] Limpieza de modal al cerrar

---

## Conclusión

Este documento cubre todos los casos de prueba necesarios para validar el modal de confirmación de creación de boleta.  
Cada caso debe ejecutarse manualmente para confirmar que la implementación es correcta y robusta.

Para reportar bugs, incluir:
- Caso de prueba que falló
- Pasos para reproducir
- Resultado esperado vs resultado real
- Screenshots/logs si aplica
