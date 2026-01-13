# PACK DE MEJORAS - Testing

Este documento describe las pruebas para validar el paquete de mejoras implementadas.

## Mejoras Incluidas

1. Búsqueda en tiempo real (live search) con HTMX
2. Modal de confirmación para pago de presupuestos (quotes)
3. Modal de confirmación para pago de boletas (invoices)
4. Eliminación segura de productos
5. Formato argentino de números en toda la UI

---

## 1. Búsqueda en Tiempo Real (Live Search)

### 1.1 Búsqueda en Productos (`/products`)

**Objetivo:** Verificar que la búsqueda actualiza los resultados sin recargar la página.

#### Caso 1.1.1: Búsqueda por nombre
**Pasos:**
1. Navegar a `/products`
2. En el campo de búsqueda, escribir "mart" (sin presionar Enter)
3. Esperar aprox. 350ms

**Resultado Esperado:**
- La tabla se actualiza automáticamente mostrando solo productos que contengan "mart" en el nombre
- La URL cambia para incluir `?q=mart`
- No hay recarga completa de la página
- Los filtros de categoría y stock se mantienen si estaban activos

#### Caso 1.1.2: Búsqueda por SKU
**Pasos:**
1. Navegar a `/products`
2. Escribir un SKU parcial (ej: "CAB")
3. Esperar aprox. 350ms

**Resultado Esperado:**
- Muestra solo productos cuyo SKU contenga "CAB"
- La búsqueda funciona combinada con otros filtros

#### Caso 1.1.3: Combinación búsqueda + categoría
**Pasos:**
1. Navegar a `/products`
2. Seleccionar una categoría del dropdown
3. Escribir algo en el campo de búsqueda

**Resultado Esperado:**
- Ambos filtros se aplican simultáneamente
- La URL refleja ambos parámetros: `?q=...&category_id=...`
- Los cambios en cualquier filtro actualizan la tabla sin recargar

#### Caso 1.1.4: Búsqueda sin resultados
**Pasos:**
1. Navegar a `/products`
2. Escribir texto que no coincida con ningún producto (ej: "xxxxnoexiste")

**Resultado Esperado:**
- Muestra mensaje: "No se encontraron productos que coincidan con: 'xxxxnoexiste'"
- No se rompe la UI
- Al borrar el texto, vuelven a aparecer todos los productos

---

### 1.2 Búsqueda en Boletas (`/invoices`)

#### Caso 1.2.1: Búsqueda por número de boleta
**Pasos:**
1. Navegar a `/invoices`
2. Escribir parte de un número de boleta en el campo "Buscar por número..."
3. Esperar aprox. 350ms

**Resultado Esperado:**
- La tabla se actualiza mostrando solo boletas que coincidan
- URL incluye `?q=...`
- Funciona combinado con filtros de proveedor y estado

#### Caso 1.2.2: Búsqueda combinada con filtro de estado
**Pasos:**
1. Navegar a `/invoices`
2. Seleccionar "Pendiente" en el dropdown de estado
3. Escribir parte de un número de boleta

**Resultado Esperado:**
- Muestra solo boletas PENDIENTE que coincidan con la búsqueda
- Ambos filtros se mantienen en la URL

---

### 1.3 Búsqueda en Presupuestos (`/quotes`)

#### Caso 1.3.1: Búsqueda por número de presupuesto
**Pasos:**
1. Navegar a `/quotes`
2. Escribir parte de un número de presupuesto
3. Esperar aprox. 350ms

**Resultado Esperado:**
- Muestra solo presupuestos que coincidan con el número
- URL actualizada con `?q=...`

#### Caso 1.3.2: Búsqueda por nombre de cliente
**Pasos:**
1. Navegar a `/quotes`
2. Escribir parte del nombre de un cliente (ej: "Juan")

**Resultado Esperado:**
- Muestra presupuestos para clientes cuyo nombre contenga "Juan"
- Búsqueda case-insensitive

#### Caso 1.3.3: Búsqueda por teléfono
**Pasos:**
1. Navegar a `/quotes`
2. Escribir parte de un número de teléfono

**Resultado Esperado:**
- Muestra presupuestos que contengan ese teléfono
- Búsqueda funciona en todos los campos configurados

---

## 2. Modal de Confirmación para Pago de Boletas

### 2.1 Apertura del Modal

#### Caso 2.1.1: Abrir modal desde listado
**Pasos:**
1. Navegar a `/invoices`
2. Identificar una boleta con estado "Pendiente"
3. Hacer clic en el botón "Pagar" (ícono de tarjeta de crédito)

**Resultado Esperado:**
- Se abre un modal Bootstrap con título "Confirmar Pago de Boleta #[ID]"
- El modal muestra:
  - Información del proveedor
  - Número de boleta
  - Fecha de la boleta
  - Total a pagar (formato argentino)
  - Tabla detallada con todos los ítems
  - Campo "Fecha de Pago" (prellenado con hoy)
  - Dropdown "Método de Pago" (Efectivo/Transferencia)
  - Advertencia sobre el registro de egreso
- Botones: "Cancelar" y "Confirmar Pago"

#### Caso 2.1.2: Modal no aparece para boletas pagadas
**Pasos:**
1. Navegar a `/invoices`
2. Identificar una boleta con estado "Pagada"

**Resultado Esperado:**
- No hay botón de "Pagar" visible
- Solo aparece el botón "Ver detalle"

### 2.2 Contenido del Modal

#### Caso 2.2.1: Verificar formato argentino en modal
**Pasos:**
1. Abrir modal de pago de una boleta con total `1500.50`

**Resultado Esperado:**
- El total aparece como `$1.500,5` (o `$1.500,50`)
- Los costos unitarios usan coma decimal y punto para miles
- Las cantidades se muestran sin decimales innecesarios

#### Caso 2.2.2: Detalle de ítems completo
**Pasos:**
1. Abrir modal de una boleta con múltiples ítems

**Resultado Esperado:**
- Cada ítem muestra: Producto, Cantidad, Costo Unit., Subtotal
- El pie de tabla muestra el TOTAL correcto
- SKU visible debajo del nombre del producto

### 2.3 Confirmación de Pago

#### Caso 2.3.1: Pagar con efectivo
**Pasos:**
1. Abrir modal de pago
2. Verificar que "Fecha de Pago" tiene la fecha de hoy
3. Seleccionar "Efectivo" en Método de Pago
4. Hacer clic en "Confirmar Pago"

**Resultado Esperado:**
- Modal se cierra
- Redirect a detalle de la boleta o listado
- Flash message: "Boleta #[ID] marcada como pagada (Efectivo). Egreso registrado en el libro mayor."
- La boleta ahora aparece con estado "Pagada"
- En `/balance/ledger`: existe un registro EXPENSE con payment_method=CASH

#### Caso 2.3.2: Pagar con transferencia
**Pasos:**
1. Abrir modal de pago
2. Seleccionar "Transferencia"
3. Confirmar

**Resultado Esperado:**
- Similar al anterior pero con payment_method=TRANSFER
- Flash message incluye "(Transferencia)"

#### Caso 2.3.3: Cancelar pago
**Pasos:**
1. Abrir modal de pago
2. Hacer clic en "Cancelar"

**Resultado Esperado:**
- Modal se cierra
- No se registra ningún pago
- La boleta sigue en estado PENDING

#### Caso 2.3.4: Doble clic en confirmar
**Pasos:**
1. Abrir modal de pago
2. Hacer doble clic rápido en "Confirmar Pago"

**Resultado Esperado:**
- El botón se deshabilita tras el primer clic
- Muestra spinner: "Procesando..."
- No se duplica el egreso en el libro mayor
- Solo se registra un pago

---

## 3. Eliminación Segura de Productos

### 3.1 Eliminar Producto sin Referencias

#### Caso 3.1.1: Producto recién creado sin movimientos
**Pasos:**
1. Navegar a `/products`
2. Crear un producto nuevo "Test Delete" (SKU: "DEL001")
3. Sin realizar ninguna venta ni compra, hacer clic en el botón "Eliminar" (ícono de basura)
4. En el modal de confirmación, revisar los datos y hacer clic en "Eliminar Producto"

**Resultado Esperado:**
- Modal de confirmación muestra:
  - Nombre: "Test Delete"
  - SKU: "DEL001"
  - Advertencia de irreversibilidad
  - Nota sobre que no se puede eliminar si tiene movimientos
- Al confirmar:
  - Flash message: "Producto 'Test Delete' eliminado exitosamente"
  - El producto ya no aparece en la lista
  - Si tenía imagen, el archivo también se eliminó del servidor
  - El registro desaparece de la BD (DELETE físico)

### 3.2 Intentar Eliminar Producto con Referencias

#### Caso 3.2.1: Producto con ventas
**Pasos:**
1. Crear una venta que incluya un producto existente (ej: "Cable 2.5mm")
2. Intentar eliminar ese producto desde `/products`
3. Hacer clic en "Eliminar" y confirmar en el modal

**Resultado Esperado:**
- Flash message (warning): "No se puede eliminar el producto 'Cable 2.5mm' porque tiene movimientos, ventas o compras asociadas. Use la opción 'Desactivar' en su lugar."
- El producto sigue existiendo en la BD
- El estado no cambia

#### Caso 3.2.2: Producto con compras (boletas)
**Pasos:**
1. Crear una boleta que incluya un producto
2. Intentar eliminarlo

**Resultado Esperado:**
- Similar al caso anterior
- Mensaje recomienda usar "Desactivar"

#### Caso 3.2.3: Producto con movimientos de stock
**Pasos:**
1. Producto con entradas de stock registradas
2. Intentar eliminarlo

**Resultado Esperado:**
- Bloqueado por foreign key constraint
- Mensaje de advertencia claro

### 3.3 Cancelar Eliminación

#### Caso 3.3.1: Modal y cancelación
**Pasos:**
1. Hacer clic en "Eliminar" de cualquier producto
2. En el modal, hacer clic en "Cancelar"

**Resultado Esperado:**
- Modal se cierra
- No se elimina nada
- El producto sigue visible

---

## 4. Formato Argentino de Números

### 4.1 Productos

#### Caso 4.1.1: Precio de venta
**Pasos:**
1. Navegar a `/products`
2. Observar columna "Precio Venta"

**Resultado Esperado:**
- Productos con precios enteros (ej: `1500`) se muestran como `1.500` (sin decimales)
- Productos con decimales (ej: `1500.5`) se muestran como `1.500,5`
- Productos con dos decimales (ej: `1500.75`) se muestran como `1.500,75`

#### Caso 4.1.2: Stock actual
**Pasos:**
1. Observar columna "Stock" en `/products`

**Resultado Esperado:**
- Cantidades enteras sin decimales: `185`
- Cantidades con decimales: `12,5`
- Badge con colores según nivel de stock

#### Caso 4.1.3: Stock mínimo
**Pasos:**
1. Observar columna "Stock Mín."

**Resultado Esperado:**
- Similar al stock actual
- Si es 0 o no definido: muestra "—"

### 4.2 Ventas (POS)

#### Caso 4.2.1: Carrito
**Pasos:**
1. Navegar a `/sales/new`
2. Agregar productos al carrito

**Resultado Esperado:**
- Precio unitario en formato argentino
- Subtotal en formato argentino
- Total del carrito en formato argentino
- Botón "Confirmar Venta" muestra total con formato argentino

#### Caso 4.2.2: Modal de confirmación de venta
**Pasos:**
1. Con productos en el carrito, hacer clic en "Confirmar Venta"
2. Revisar el modal

**Resultado Esperado:**
- Todas las cantidades y montos en formato argentino
- Total destacado en formato argentino
- Resumen: "Monto total: $[formato argentino]"

### 4.3 Boletas

#### Caso 4.3.1: Listado de boletas
**Pasos:**
1. Navegar a `/invoices`
2. Observar columna "Total"

**Resultado Esperado:**
- Todos los totales en formato argentino
- Consistencia en toda la tabla

#### Caso 4.3.2: Detalle de boleta
**Pasos:**
1. Abrir detalle de una boleta

**Resultado Esperado:**
- Total de la boleta: formato argentino
- Cada línea:
  - Cantidad: formato argentino
  - Costo unitario: formato argentino
  - Subtotal: formato argentino
- Subtotal y total final consistentes

### 4.4 Presupuestos

#### Caso 4.4.1: Listado de presupuestos
**Pasos:**
1. Navegar a `/quotes`
2. Observar columna "Total"

**Resultado Esperado:**
- Formato argentino en todos los totales

#### Caso 4.4.2: Detalle de presupuesto
**Pasos:**
1. Ver detalle de un presupuesto

**Resultado Esperado:**
- Similar a boletas: cantidades, precios y totales en formato argentino

### 4.5 Balance

#### Caso 4.5.1: Balance diario/mensual/anual
**Pasos:**
1. Navegar a `/balance`
2. Ver las columnas de Ingresos, Egresos, Neto

**Resultado Esperado:**
- Todos los montos en formato argentino
- Número sin decimales innecesarios
- Coma para decimales, punto para miles

#### Caso 4.5.2: Libro mayor (ledger)
**Pasos:**
1. Navegar a `/balance/ledger`
2. Observar columna "Monto"

**Resultado Esperado:**
- Formato argentino en todos los asientos

### 4.6 Casos Especiales

#### Caso 4.6.1: Número cero
**Valor:** `0` o `0.00`

**Resultado Esperado:**
- Se muestra simplemente como `0`
- No muestra `0,00` ni `0.000`

#### Caso 4.6.2: Números grandes
**Valor:** `100550.00`

**Resultado Esperado:**
- Se muestra como `100.550`

#### Caso 4.6.3: Valores NULL
**Valor:** `None` / `NULL`

**Resultado Esperado:**
- Se muestra como `-` o string vacío (según contexto)
- No genera error

---

## 5. Pruebas de Integración

### 5.1 Flujo completo: Venta + Búsqueda + Formato

**Pasos:**
1. Navegar a `/products`
2. Buscar un producto escribiendo en tiempo real (ej: "mar")
3. Verificar que aparece con formato argentino en precio y stock
4. Ir a `/sales/new`
5. Agregar ese producto al carrito
6. Verificar formato argentino en carrito
7. Confirmar venta (modal con formato argentino)
8. Completar venta
9. Verificar que aparece en `/balance/ledger` con formato argentino

**Resultado Esperado:**
- Todo el flujo funciona sin errores
- Formato argentino consistente en todos los pasos
- Búsqueda en tiempo real funciona
- Venta se registra correctamente

### 5.2 Flujo completo: Compra + Pago + Formato

**Pasos:**
1. Navegar a `/invoices/new`
2. Crear una boleta con ítems
3. Verificar formato argentino en el formulario
4. Guardar la boleta
5. Desde `/invoices`, buscar la boleta recién creada (búsqueda en tiempo real)
6. Hacer clic en "Pagar" (modal)
7. Verificar formato argentino en el modal
8. Confirmar pago
9. Verificar en `/balance` y `/balance/ledger` que el egreso tiene formato argentino

**Resultado Esperado:**
- Flujo completo sin errores
- Modal de pago funciona correctamente
- Formato argentino en todos los pasos

### 5.3 Flujo completo: Delete de producto

**Pasos:**
1. Crear un producto "Test XYZ"
2. Intentar eliminarlo (debe funcionar)
3. Crear otro producto "Test ABC"
4. Usarlo en una venta
5. Intentar eliminarlo (debe bloquearse con mensaje claro)
6. Desactivar "Test ABC" en su lugar
7. Verificar que no aparece en búsquedas de POS

**Resultado Esperado:**
- Eliminación funciona solo cuando es seguro
- Mensajes claros en ambos casos
- Desactivar sigue siendo la opción recomendada para productos con historial

---

## 6. Verificaciones SQL (Opcional)

### 6.1 Verificar payment_method en ledger

```sql
SELECT id, datetime, type, amount, payment_method, notes
FROM finance_ledger
WHERE type = 'EXPENSE'
ORDER BY datetime DESC
LIMIT 10;
```

**Resultado Esperado:**
- Los pagos de boletas tienen payment_method='CASH' o 'TRANSFER'

### 6.2 Verificar que productos eliminados no existen

```sql
-- Antes de eliminar "Test Delete"
SELECT id, name, sku FROM product WHERE sku = 'DEL001';

-- Después de eliminar
SELECT id, name, sku FROM product WHERE sku = 'DEL001';
```

**Resultado Esperado:**
- Después de eliminar: 0 rows

### 6.3 Verificar integridad al intentar delete con referencias

```sql
-- Intentar delete manual de un producto con ventas
DELETE FROM product WHERE id = [ID_PRODUCTO_CON_VENTAS];
```

**Resultado Esperado:**
- Error: `violates foreign key constraint` (o similar)
- El producto no se elimina

---

## 7. Pruebas de Regresión

### 7.1 Funcionalidades existentes no rotas

#### Verificar que siguen funcionando:
- ✅ Crear productos
- ✅ Editar productos
- ✅ Toggle active/inactive de productos
- ✅ Crear ventas completas
- ✅ Editar ventas (si existe)
- ✅ Crear boletas completas
- ✅ Crear presupuestos
- ✅ Convertir presupuestos a ventas
- ✅ Balance diario/mensual/anual
- ✅ Libro mayor
- ✅ Filtros existentes (categoría, stock, estado, etc.)

### 7.2 Performance

#### Caso 7.2.1: Live search no genera lag excesivo
**Pasos:**
1. Con 100+ productos en DB
2. Escribir rápidamente en el campo de búsqueda

**Resultado Esperado:**
- El debounce de 350ms evita requests excesivas
- La UI no se congela
- Los resultados aparecen suavemente

---

## 8. Errores Esperados y Manejo

### 8.1 Error en búsqueda
**Simular:** Error en la BD durante búsqueda

**Resultado Esperado:**
- Flash message: "Error al cargar [recurso]"
- La UI no se rompe
- Se muestra mensaje claro al usuario

### 8.2 Error en modal de pago
**Simular:** Intentar pagar una boleta ya pagada manipulando la request

**Resultado Esperado:**
- Mensaje de error claro
- No se duplica el pago

### 8.3 Error en delete de producto
**Simular:** ID de producto inexistente

**Resultado Esperado:**
- Flash message: "Producto no encontrado"
- Redirect a listado sin romper

---

## 9. Checklist Final

- [ ] Live search funciona en productos (nombre, SKU, barcode)
- [ ] Live search funciona en boletas (número)
- [ ] Live search funciona en presupuestos (número, cliente, teléfono)
- [ ] Modal de pago de boletas se abre correctamente
- [ ] Modal muestra detalles completos y correctos
- [ ] Pago con efectivo funciona y registra correctamente
- [ ] Pago con transferencia funciona y registra correctamente
- [ ] Delete de producto sin referencias funciona
- [ ] Delete de producto con referencias se bloquea con mensaje claro
- [ ] Formato argentino en productos (precio, stock)
- [ ] Formato argentino en ventas (carrito, modal, detalle)
- [ ] Formato argentino en boletas (listado, detalle, modal)
- [ ] Formato argentino en presupuestos (listado, detalle)
- [ ] Formato argentino en balance (daily/monthly/yearly, ledger)
- [ ] Números sin decimales no muestran `.00`
- [ ] Números con 1 decimal muestran `,X`
- [ ] Números con 2 decimales muestran `,XX`
- [ ] Miles separados con punto
- [ ] Valores NULL/None muestran `-` sin error
- [ ] Flujo completo venta funciona
- [ ] Flujo completo compra+pago funciona
- [ ] Performance aceptable con búsqueda en tiempo real
- [ ] No hay regresiones en funcionalidades existentes

---

## Conclusión

Este documento cubre todas las pruebas necesarias para validar las 5 mejoras del pack.  
Cada caso debe ejecutarse manualmente para confirmar que la implementación es correcta y robusta.

Para reportar bugs, incluir:
- Caso de prueba que falló
- Pasos para reproducir
- Resultado esperado vs resultado real
- Screenshots/logs si aplica
