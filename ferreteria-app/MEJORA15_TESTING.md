# 🧪 **MEJORA 15: UX Mejorada en POS - Casos de Prueba**

---

## **📋 Resumen de la Mejora**

**Objetivo**: Mejorar la experiencia de usuario en el POS con dos funcionalidades:
1. **Actualización automática del carrito**: Al modificar cantidades, el carrito se actualiza sin presionar Enter
2. **Modal de confirmación**: Antes de confirmar venta, mostrar un modal con el detalle completo y solo confirmar al aceptarlo

**Funcionalidades implementadas**:
- ✅ Input de cantidad con `hx-trigger="input changed delay:500ms"` para actualización automática
- ✅ Validaciones UX: qty vacío, qty <= 0 (remueve automáticamente)
- ✅ Endpoint `GET /sales/confirm/preview` para el modal
- ✅ Template `_confirm_modal.html` con modal Bootstrap 5
- ✅ Botón "Confirmar Venta" abre modal con HTMX
- ✅ Modal muestra todos los productos, método de pago y total
- ✅ Confirmación final solo desde dentro del modal

---

## **🎯 PARTE 1: Actualización Automática del Carrito**

### **Caso 1.1: Cambiar Cantidad con Teclado (sin Enter) - Actualización Automática**
**Objetivo**: Verificar que al modificar qty el carrito se actualiza solo después de 500ms sin cambios.

**Pasos**:
1. Ir a `/sales/new`
2. Agregar un producto al carrito
3. En el input de cantidad, cambiar el valor de 1 a 3 usando teclado
4. NO presionar Enter
5. Esperar 500ms

**Resultado esperado**:
- ✅ Después de 500ms, el carrito se actualiza automáticamente
- ✅ El subtotal del producto se recalcula
- ✅ El total general se actualiza
- ✅ No se recarga toda la página, solo el carrito

**Verificación técnica**:
- HTMX dispara `POST /sales/cart/update` con el nuevo qty
- Response es el partial `_cart.html` actualizado

---

### **Caso 1.2: Cambiar Cantidad con Mouse (Flechas del Input) - Actualización Automática**
**Objetivo**: Verificar que las flechas up/down del input number también disparan actualización.

**Pasos**:
1. Agregar producto al carrito
2. Hacer click en la flecha ↑ del input qty varias veces
3. NO hacer nada más

**Resultado esperado**:
- ✅ Cada cambio dispara actualización después de 500ms
- ✅ Subtotal y total se actualizan correctamente

---

### **Caso 1.3: Cambiar Cantidad Rápido - No Spamea Server**
**Objetivo**: Verificar que el delay:500ms evita spam excesivo de requests.

**Pasos**:
1. Agregar producto al carrito
2. Cambiar qty rápidamente varias veces: 1 → 2 → 3 → 5 → 10
3. Observar Network Tab en DevTools

**Resultado esperado**:
- ✅ NO se envían requests por cada cambio individual
- ✅ Solo se envía request 500ms después del último cambio
- ✅ El servidor recibe solo 1-2 requests en vez de 5

---

### **Caso 1.4: Qty Vacío - No Rompe**
**Objetivo**: Verificar que borrar completamente el input no causa error.

**Pasos**:
1. Agregar producto al carrito con qty=2
2. Seleccionar todo el texto del input y borrarlo (queda vacío)
3. Esperar 500ms

**Resultado esperado**:
- ✅ El carrito se mantiene sin cambios
- ✅ El qty del input vuelve a mostrar el valor anterior (2)
- ✅ NO se muestra error 500
- ✅ NO se elimina el producto

**Verificación backend**:
```python
# En cart_update():
if not qty_str:
    # Return cart unchanged
    return render_template('sales/_cart.html', ...)
```

---

### **Caso 1.5: Qty = 0 - Remueve Producto Automáticamente**
**Objetivo**: Verificar que qty=0 remueve el ítem del carrito.

**Pasos**:
1. Agregar producto al carrito
2. Cambiar qty a 0
3. Esperar 500ms

**Resultado esperado**:
- ✅ El producto se elimina automáticamente del carrito
- ✅ Flash message: "Producto eliminado del carrito"
- ✅ Total se recalcula sin ese producto
- ✅ Si el carrito queda vacío, muestra mensaje "El carrito está vacío"

**Verificación backend**:
```python
# En cart_update():
if qty <= 0:
    # Remove item from cart
    del cart['items'][str(product_id)]
```

---

### **Caso 1.6: Qty Negativo - Remueve Producto**
**Objetivo**: Verificar que qty negativo también remueve el ítem.

**Pasos**:
1. Agregar producto
2. Cambiar qty a -5 (si el input lo permite)
3. Esperar

**Resultado esperado**:
- ✅ El producto se elimina del carrito
- ✅ Flash: "Producto eliminado..."

**Nota**: `min="0.01"` en HTML debería prevenir esto, pero el backend maneja defensivamente.

---

### **Caso 1.7: Qty Inválido (Texto) - No Rompe**
**Objetivo**: Verificar que ingresar texto en qty no causa error.

**Pasos**:
1. Agregar producto
2. Escribir "abc" en qty (bypaseando HTML validation)
3. Esperar

**Resultado esperado**:
- ✅ Flash warning: "Cantidad inválida"
- ✅ Carrito se mantiene sin cambios
- ✅ qty vuelve al valor anterior

---

### **Caso 1.8: Qty Mayor al Stock - Valida y Muestra Warning**
**Objetivo**: Verificar que la validación de stock sigue funcionando.

**Pasos**:
1. Agregar producto con stock=10
2. Cambiar qty a 20
3. Esperar

**Resultado esperado**:
- ✅ Flash warning: "Stock insuficiente para [Producto]. Disponible: 10"
- ✅ Qty se mantiene en el valor anterior
- ✅ NO se actualiza a 20

---

### **Caso 1.9: Múltiples Productos - Actualizar Uno No Afecta Otros**
**Objetivo**: Verificar que actualizar un producto no afecta a otros en el carrito.

**Pasos**:
1. Agregar 3 productos diferentes al carrito
2. Cambiar qty del segundo producto
3. Observar carrito actualizado

**Resultado esperado**:
- ✅ Solo el producto editado se actualiza
- ✅ Los otros dos mantienen sus cantidades
- ✅ Total general se recalcula correctamente

---

## **🎯 PARTE 2: Modal de Confirmación de Venta**

### **Caso 2.1: Click "Confirmar Venta" - Abre Modal (No Confirma Inmediatamente)**
**Objetivo**: Verificar que el botón NO confirma directamente, sino que abre un modal.

**Pasos**:
1. Agregar productos al carrito
2. Seleccionar método: Efectivo
3. Click en "Confirmar Venta"

**Resultado esperado**:
- ✅ NO se confirma la venta aún
- ✅ Se abre un modal Bootstrap con fondo oscuro (backdrop)
- ✅ El modal contiene:
  - Título: "Confirmar Venta"
  - Tabla de productos
  - Total
  - Método de pago
  - Botones: "Cancelar" y "Confirmar"

**Verificación técnica**:
- HTMX hace `GET /sales/confirm/preview`
- Response es el template `_confirm_modal.html`
- Modal se abre automáticamente con JavaScript inline

---

### **Caso 2.2: Modal Muestra Todos los Productos Correctamente**
**Objetivo**: Verificar que el modal lista todos los productos del carrito con detalles.

**Pasos**:
1. Agregar 3 productos diferentes:
   - Producto A: qty=2, precio=$10
   - Producto B: qty=1, precio=$25
   - Producto C: qty=5, precio=$3
2. Click "Confirmar Venta"

**Resultado esperado**:
- ✅ Modal muestra tabla con 3 filas
- ✅ Cada fila muestra:
  - Nombre del producto
  - SKU y UOM (en small text)
  - Cantidad en badge
  - Precio unitario
  - Subtotal correcto
- ✅ Fila total muestra:
  - Total: $20 + $25 + $15 = $60.00

**Verificación visual**:
```
Producto A
SKU: ABC-001 | UN          2       $10.00      $20.00

Producto B
SKU: XYZ-123 | KG          1       $25.00      $25.00

Producto C
SKU: DEF-456 | M           5        $3.00      $15.00
--------------------------------------------------------------
                           TOTAL:              $60.00
```

---

### **Caso 2.3: Modal Muestra Método de Pago Correcto - Efectivo**
**Objetivo**: Verificar que el método seleccionado se pasa al modal.

**Pasos**:
1. Agregar productos
2. Seleccionar "Efectivo"
3. Click "Confirmar Venta"

**Resultado esperado**:
- ✅ Modal muestra badge verde: "💵 Efectivo"
- ✅ Badge tiene class `bg-success`
- ✅ Ícono correcto: `bi-cash`

---

### **Caso 2.4: Modal Muestra Método de Pago Correcto - Transferencia**
**Objetivo**: Verificar método transferencia.

**Pasos**:
1. Agregar productos
2. Seleccionar "Transferencia"
3. Click "Confirmar Venta"

**Resultado esperado**:
- ✅ Modal muestra badge azul: "🏦 Transferencia"
- ✅ Badge tiene class `bg-info`
- ✅ Ícono correcto: `bi-bank`

---

### **Caso 2.5: Cancelar Modal - NO Crea Venta**
**Objetivo**: Verificar que cancelar cierra el modal sin confirmar venta.

**Pasos**:
1. Agregar productos
2. Click "Confirmar Venta" → abre modal
3. Click "Cancelar"

**Resultado esperado**:
- ✅ Modal se cierra
- ✅ Vuelve a la pantalla de POS
- ✅ Carrito sigue intacto con los productos
- ✅ NO se creó venta en DB
- ✅ NO se descontó stock

**Verificación DB**:
```sql
-- No debe haber nueva fila en sale
SELECT MAX(id) FROM sale;
-- Comparar antes y después: debe ser el mismo
```

---

### **Caso 2.6: Click Fuera del Modal (Backdrop) - NO Cierra**
**Objetivo**: Verificar que el modal tiene `data-bs-backdrop="static"` para evitar cierres accidentales.

**Pasos**:
1. Abrir modal de confirmación
2. Click fuera del modal (en el fondo oscuro)

**Resultado esperado**:
- ✅ Modal NO se cierra
- ✅ Requiere acción explícita (Cancelar o Confirmar)

---

### **Caso 2.7: Confirmar Dentro del Modal - Crea Venta Exitosamente**
**Objetivo**: Verificar que solo al confirmar dentro del modal se ejecuta la venta.

**Pasos**:
1. Agregar productos con stock suficiente
2. Método: Efectivo
3. Click "Confirmar Venta" → abre modal
4. Revisar detalles
5. Click "Confirmar" (botón azul dentro del modal)

**Resultado esperado**:
- ✅ Venta se crea exitosamente
- ✅ Stock se descuenta (triggers DB)
- ✅ Ledger INCOME se crea con payment_method='CASH'
- ✅ Modal se cierra
- ✅ Redirect a página de éxito o muestra flash "Venta confirmada..."
- ✅ Carrito se vacía

**Verificación DB**:
```sql
-- Nueva venta
SELECT * FROM sale ORDER BY id DESC LIMIT 1;

-- Líneas de venta
SELECT * FROM sale_line WHERE sale_id = <last_sale_id>;

-- Stock descontado
SELECT on_hand_qty FROM product_stock WHERE product_id = ...;

-- Ledger entry
SELECT * FROM finance_ledger 
WHERE reference_type = 'SALE' 
  AND reference_id = <last_sale_id>;
```

---

### **Caso 2.8: Confirmar con Stock Insuficiente - Muestra Error y NO Crea Venta**
**Objetivo**: Verificar que la validación de stock al confirmar funciona.

**Pasos**:
1. Producto A con stock=5
2. Agregar al carrito qty=10
3. Click "Confirmar Venta" → modal
4. Click "Confirmar"

**Resultado esperado**:
- ✅ Flash error: "Stock insuficiente para [Producto A]. Disponible: 5"
- ✅ Venta NO se crea
- ✅ Stock NO cambia
- ✅ Modal se cierra (por redirect) o se mantiene con error visible

**Nota**: Este caso solo ocurre si el stock cambió entre agregar al carrito y confirmar (ej: otra venta concurrente).

---

### **Caso 2.9: Carrito Vacío - Preview NO Abre Modal**
**Objetivo**: Verificar que no se puede abrir modal con carrito vacío.

**Pasos**:
1. Vaciar carrito completamente
2. Intentar click en "Confirmar Venta" (pero el botón no debería existir)

**Resultado esperado**:
- ✅ Si el carrito está vacío, el botón "Confirmar Venta" NO se muestra
- ✅ Si se bypasea y se llama a `/confirm/preview` con carrito vacío:
  - Response: mensaje "El carrito está vacío..."
  - NO se abre modal

---

### **Caso 2.10: Modal - Resumen Informativo Correcto**
**Objetivo**: Verificar que el alert de resumen muestra info útil.

**Pasos**:
1. Agregar 2 productos al carrito
2. Abrir modal

**Resultado esperado**:
- ✅ Alert verde con ícono de check
- ✅ Muestra:
  - "Total de productos: 2"
  - "Monto total: $X.XX"
  - "Se descontará stock automáticamente"
  - "Se registrará el ingreso en el libro contable"

---

### **Caso 2.11: Modal - Diseño Responsive y Profesional**
**Objetivo**: Verificar que el modal se ve bien en diferentes tamaños.

**Pasos**:
1. Abrir modal en desktop (1920x1080)
2. Abrir modal en tablet (768px)
3. Abrir modal en móvil (375px)

**Resultado esperado**:
- ✅ Modal `modal-lg` en desktop (más ancho)
- ✅ Modal responsive en tablet y móvil
- ✅ Tabla con scroll horizontal si es necesario (`table-responsive`)
- ✅ Botones apilados verticalmente en móvil
- ✅ Texto legible, sin overflow

---

## **🎯 PARTE 3: Integración y Flujo Completo**

### **Caso 3.1: Flujo Completo - Agregar Productos, Modificar Qty, Confirmar con Modal**
**Objetivo**: Verificar que todo el flujo funciona sin errores.

**Pasos**:
1. Ir a `/sales/new`
2. Buscar "Tornillo"
3. Agregar 2 tornillos al carrito
4. Modificar qty a 5 (sin Enter, esperar auto-update)
5. Agregar otro producto "Pintura"
6. Seleccionar método: Transferencia
7. Click "Confirmar Venta"
8. Revisar modal con detalles
9. Click "Confirmar" dentro del modal

**Resultado esperado**:
- ✅ Cada paso funciona correctamente
- ✅ Qty se actualiza automáticamente
- ✅ Modal muestra todo correcto
- ✅ Venta se confirma exitosamente
- ✅ Stock se descuenta
- ✅ Ledger con payment_method='TRANSFER'
- ✅ Carrito se vacía

---

### **Caso 3.2: Concurrencia - Cambiar Método de Pago Después de Agregar Productos**
**Objetivo**: Verificar que cambiar el método después de agregar productos funciona.

**Pasos**:
1. Agregar productos con método "Efectivo" seleccionado
2. Cambiar a "Transferencia"
3. Click "Confirmar Venta"

**Resultado esperado**:
- ✅ Modal muestra "Transferencia" correctamente
- ✅ Al confirmar, ledger se crea con payment_method='TRANSFER'

---

### **Caso 3.3: Top Vendidos + Auto-Update Qty + Modal**
**Objetivo**: Verificar que agregar desde "Más Vendidos" funciona con las nuevas mejoras.

**Pasos**:
1. Click en "Agregar" de un top vendido
2. Modificar qty en carrito sin Enter
3. Click "Confirmar Venta"
4. Confirmar en modal

**Resultado esperado**:
- ✅ Producto se agrega correctamente
- ✅ Qty se actualiza automáticamente
- ✅ Modal funciona igual

---

### **Caso 3.4: Guardar Presupuesto Sigue Funcionando**
**Objetivo**: Verificar que MEJORA 13/14 (presupuestos) no se rompió.

**Pasos**:
1. Agregar productos
2. Ingresar datos del cliente
3. Click "Guardar como Presupuesto"

**Resultado esperado**:
- ✅ Presupuesto se crea correctamente
- ✅ NO se abre modal de venta
- ✅ Redirect a detalle del presupuesto

---

### **Caso 3.5: Remover Producto Sigue Funcionando**
**Objetivo**: Verificar que el botón de remover (🗑️) funciona.

**Pasos**:
1. Agregar 2 productos
2. Click en 🗑️ de uno de ellos

**Resultado esperado**:
- ✅ Producto se elimina
- ✅ Carrito se actualiza con HTMX
- ✅ Total se recalcula

---

## **🎯 PARTE 4: Validaciones de Seguridad y Edge Cases**

### **Caso 4.1: HTMX Timeout - No Rompe UI**
**Objetivo**: Verificar comportamiento si HTMX tarda mucho o falla.

**Pasos**:
1. Simular latencia alta (Chrome DevTools > Network > Slow 3G)
2. Cambiar qty en carrito
3. Observar

**Resultado esperado**:
- ✅ Muestra indicador de carga (opcional)
- ✅ Cuando responde, actualiza carrito
- ✅ Si falla, no rompe la UI

---

### **Caso 4.2: Modal - Script de Auto-Open Funciona en Todos los Browsers**
**Objetivo**: Verificar compatibilidad del script inline.

**Pasos**:
1. Abrir modal en Chrome
2. Abrir modal en Firefox
3. Abrir modal en Edge

**Resultado esperado**:
- ✅ Modal se abre automáticamente en todos
- ✅ No hay errores en Console

---

### **Caso 4.3: CSRF Protection (Si Existe)**
**Objetivo**: Verificar que formularios funcionan con CSRF si está implementado.

**Nota**: Actualmente no hay CSRF implementado, pero si se agrega en el futuro:
- Los forms en modal deben incluir token CSRF
- HTMX debe pasar el token

---

### **Caso 4.4: Session Expiry - Manejo Graceful**
**Objetivo**: Verificar que si la sesión expira, no rompe.

**Pasos**:
1. Agregar productos al carrito
2. Esperar hasta que la sesión expire (o forzar borrado de cookie)
3. Click "Confirmar Venta"

**Resultado esperado**:
- ✅ Redirect a login
- ✅ O mensaje "Sesión expirada"
- ✅ No error 500

---

## **📊 Resumen de Pruebas**

| Categoría | Casos | Críticos |
|-----------|-------|----------|
| **Auto-Update Qty** | 9 | ✅ 1.1, 1.2, 1.4, 1.5, 1.8 |
| **Modal Confirmación** | 11 | ✅ 2.1, 2.2, 2.5, 2.7 |
| **Integración** | 5 | ✅ 3.1, 3.4 |
| **Edge Cases** | 4 | 4.1, 4.4 |
| **TOTAL** | **29** | **11** |

---

## **✅ Checklist de Aceptación Final**

### **Auto-Update Qty**
- [ ] Input qty con `hx-trigger="input changed delay:500ms"`
- [ ] Actualización sin presionar Enter funciona
- [ ] Delay de 500ms evita spam
- [ ] Qty vacío no rompe (devuelve carrito sin cambios)
- [ ] Qty = 0 remueve producto automáticamente
- [ ] Qty negativo remueve producto
- [ ] Qty inválido (texto) muestra warning
- [ ] Validación de stock sigue funcionando
- [ ] Múltiples productos se actualizan independientemente

### **Modal Confirmación**
- [ ] Endpoint `GET /sales/confirm/preview` existe y funciona
- [ ] Template `_confirm_modal.html` existe y es responsive
- [ ] Botón "Confirmar Venta" abre modal (NO confirma directo)
- [ ] Modal muestra todos los productos correctamente
- [ ] Modal muestra método de pago seleccionado
- [ ] Modal muestra total correcto
- [ ] Cancelar cierra modal sin crear venta
- [ ] Backdrop static (no cierra al click fuera)
- [ ] Confirmar dentro del modal crea venta
- [ ] Stock insuficiente al confirmar muestra error
- [ ] Carrito vacío no abre modal
- [ ] Resumen informativo correcto
- [ ] Diseño profesional y responsive

### **Integración**
- [ ] Flujo completo funciona end-to-end
- [ ] Guardar presupuesto sigue funcionando
- [ ] Remover producto sigue funcionando
- [ ] Top vendidos compatible con cambios
- [ ] Método de pago se sincroniza correctamente

### **UX/UI**
- [ ] No hay flash de contenido sin estilo (FOUC)
- [ ] Transiciones suaves de HTMX
- [ ] Loading indicators visibles cuando corresponde
- [ ] Flash messages claros y útiles
- [ ] Diseño consistente con resto del sistema

---

## **🚀 Flujo de Prueba Manual Completo**

### **Happy Path: Venta Completa con Nuevas Mejoras**
```
1. Login: ferreteria123
2. /sales/new
3. Buscar "Tornillo" → agregar 2 unidades
4. Modificar qty a 5 (SIN Enter, esperar 500ms)
   ✅ Carrito se actualiza automáticamente
5. Buscar "Pintura" → agregar 1 unidad
6. Seleccionar método: Transferencia
7. Click "Confirmar Venta"
   ✅ Se abre modal con detalles:
      - Tornillo: qty=5
      - Pintura: qty=1
      - Método: Transferencia
      - Total: $X.XX
8. Revisar detalles en modal
9. Click "Confirmar" (dentro del modal)
   ✅ Venta se confirma
   ✅ Stock se descuenta
   ✅ Flash: "Venta confirmada..."
   ✅ Carrito vacío
```

### **Test: Cancelar Modal**
```
1. Agregar productos
2. Click "Confirmar Venta" → modal
3. Click "Cancelar"
   ✅ Modal se cierra
   ✅ Carrito intacto
   ✅ NO se creó venta
```

### **Test: Auto-Update con Qty = 0**
```
1. Agregar producto qty=3
2. Cambiar qty a 0 (sin Enter)
3. Esperar 500ms
   ✅ Producto se elimina automáticamente
   ✅ Flash: "Producto eliminado..."
```

---

**✅ FIN DE TESTING MEJORA 15**
