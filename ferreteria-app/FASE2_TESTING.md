# FASE 2: Testing - Ventas (POS + Confirmar Venta)

## ✅ Estado: COMPLETADA

### Comandos para ejecutar

#### 1. Asegurarse de que PostgreSQL esté corriendo

```powershell
cd C:\jere\Ferreteria\Ferreteria-db
docker ps
```

#### 2. Ejecutar la aplicación Flask

```powershell
cd C:\jere\Ferreteria\ferreteria-app
python app.py
```

La aplicación estará disponible en: **http://127.0.0.1:5000**

---

## 🧪 Pruebas Manuales

### Test 1: Venta simple de 1 producto con stock disponible

**Objetivo**: Verificar que se puede crear una venta y que el stock se descuenta correctamente.

1. Navegar a: **http://127.0.0.1:5000/sales/new**
2. En el buscador escribir: `martillo`
3. Click en "Buscar"
4. Verificar que aparece "Martillo de Goma" con stock disponible (15 unidades)
5. En el campo cantidad, escribir `2`
6. Click en el botón `+` para agregar al carrito
7. **Verificación del carrito**:
   - Debe aparecer el producto en el carrito
   - Cantidad: 2
   - Precio unitario: $150.00
   - Subtotal: $300.00
   - Total: $300.00
8. Click en "Confirmar Venta ($300.00)"
9. Confirmar en el diálogo
10. **Verificación**:
    - Mensaje verde: "Venta #X confirmada exitosamente. Stock actualizado."
    - El carrito se vacía automáticamente
11. **Verificar stock en base de datos**:

```powershell
# En el terminal, ejecutar:
docker exec -it ferreteria-postgres psql -U admin -d ferreteria -c "SELECT p.name, ps.on_hand_qty FROM product p JOIN product_stock ps ON p.id = ps.product_id WHERE p.name = 'Martillo de Goma';"
```

**Resultado esperado**: Stock debe ser `13.00` (15 - 2)

---

### Test 2: Venta múltiple (2 productos, total correcto)

**Objetivo**: Verificar que se pueden agregar múltiples productos y el total se calcula correctamente.

1. En el POS, buscar `pintura`
2. Agregar "Pintura Vinílica Blanca" cantidad `3`
3. Buscar `cemento`
4. Agregar "Cemento Gris" cantidad `5`
5. **Verificación del carrito**:
   - 2 productos en el carrito
   - Pintura: 3 × $320.00 = $960.00
   - Cemento: 5 × $185.00 = $925.00
   - **Total: $1,885.00**
6. Confirmar venta
7. **Verificar en BD**:

```sql
SELECT * FROM sale ORDER BY id DESC LIMIT 1;
-- Debe mostrar total = 1885.00

SELECT * FROM sale_line WHERE sale_id = (SELECT MAX(id) FROM sale);
-- Debe mostrar 2 líneas

SELECT p.name, ps.on_hand_qty FROM product p 
JOIN product_stock ps ON p.id = ps.product_id 
WHERE p.name IN ('Pintura Vinilica Blanca', 'Cemento Gris');
-- Pintura: 22.00 (25-3)
-- Cemento: 495.00 (500-5)
```

---

### Test 3: Intentar vender más qty que stock (debe fallar)

**Objetivo**: Verificar que no se puede vender más de lo que hay en stock.

1. Buscar producto "Clavos de 3 pulgadas" (Stock actual: 8 o según lo que quede)
2. Intentar agregar cantidad `100` al carrito
3. **Verificación**:
   - Debe mostrar mensaje de advertencia: "Stock insuficiente para..."
   - El producto NO se agrega al carrito
   - El stock en BD NO cambia

---

### Test 4: Producto sin stock no se puede agregar

**Objetivo**: Verificar que productos sin stock no permiten crear ventas.

1. Buscar "Destornillador Phillips" (tiene stock 0)
2. **Verificación en lista de resultados**:
   - Badge rojo "Sin stock"
   - Botón "Sin stock" deshabilitado (gris)
   - No se puede agregar al carrito

---

### Test 5: Confirmar carrito vacío (error)

**Objetivo**: Verificar que no se puede confirmar una venta sin productos.

1. Asegurarse de que el carrito esté vacío (nueva sesión o después de confirmar venta)
2. Ir directamente a la URL de confirm: **http://127.0.0.1:5000/sales/confirm** (POST)
3. O navegar al POS y observar que no hay botón "Confirmar Venta" si el carrito está vacío
4. **Verificación**:
   - Si el carrito está vacío, muestra mensaje: "El carrito está vacío"
   - No se crea ninguna venta en BD

---

### Test 6: HTMX - Actualizar cantidad en carrito

**Objetivo**: Verificar que se puede modificar la cantidad sin recargar la página.

1. Agregar "Martillo de Goma" cantidad `1` al carrito
2. En el campo de cantidad del carrito, cambiar a `3`
3. Presionar Enter o hacer blur del campo
4. **Verificación**:
   - El carrito se actualiza sin recargar la página completa (HTMX)
   - El subtotal se recalcula: 3 × $150.00 = $450.00
   - El total se actualiza correctamente

---

### Test 7: HTMX - Remover producto del carrito

**Objetivo**: Verificar que se puede eliminar un producto del carrito.

1. Agregar 2 productos al carrito
2. Click en el ícono de basura (trash) de uno de los productos
3. **Verificación**:
   - El producto se elimina del carrito sin recargar la página
   - El total se recalcula automáticamente
   - Si se eliminan todos los productos, muestra "El carrito está vacío"

---

### Test 8: Validación de stock al confirmar venta

**Objetivo**: Verificar que se valida el stock en el momento de confirmar (con locking).

**Escenario**: Dos usuarios intentan vender el mismo producto al mismo tiempo.

Este test es difícil de hacer manualmente, pero se puede verificar el locking en el código:

```python
# En sales_service.py línea ~50
# Se usa SELECT ... FOR UPDATE para bloquear las filas de product_stock
```

Para testear manualmente:
1. Agregar "Clavos de 3 pulgadas" (stock: 8) cantidad `6` al carrito
2. **Sin confirmar**, abrir otra pestaña del navegador
3. En la nueva pestaña, agregar "Clavos de 3 pulgadas" cantidad `5`
4. Intentar confirmar en ambas pestañas simultáneamente
5. **Resultado esperado**:
   - Una venta se procesa correctamente
   - La otra falla con "Stock insuficiente"
   - El stock final debe ser correcto (no negativo)

---

### Test 9: Verificar registro en finance_ledger

**Objetivo**: Verificar que se registra un ingreso en el ledger cuando se confirma una venta.

1. Hacer una venta de $500.00
2. **Verificar en BD**:

```sql
SELECT * FROM finance_ledger 
WHERE type = 'INCOME' 
AND reference_type = 'SALE'
ORDER BY id DESC LIMIT 1;
```

**Resultado esperado**:
- `type`: INCOME
- `amount`: 500.00
- `reference_type`: SALE
- `reference_id`: (ID de la venta)
- `category`: 'Ventas'

---

### Test 10: Verificar registro en stock_move y stock_move_line

**Objetivo**: Verificar que se crean los movimientos de stock correctamente.

1. Hacer una venta con 2 productos diferentes
2. **Verificar en BD**:

```sql
-- Verificar stock_move
SELECT * FROM stock_move 
WHERE type = 'OUT' 
AND reference_type = 'SALE'
ORDER BY id DESC LIMIT 1;

-- Verificar stock_move_line
SELECT sml.*, p.name 
FROM stock_move_line sml
JOIN product p ON sml.product_id = p.id
WHERE stock_move_id = (SELECT MAX(id) FROM stock_move WHERE type = 'OUT');
```

**Resultado esperado**:
- stock_move: type='OUT', reference_type='SALE'
- stock_move_line: 2 líneas, una por cada producto
- Las cantidades deben coincidir con las vendidas

---

## 📊 Datos de Prueba

Los productos creados en Fase 1 son suficientes para probar:

| Producto | Stock Inicial | UOM | Precio |
|----------|---------------|-----|--------|
| Martillo de Goma | 15 | UN | $150.00 |
| Destornillador Phillips | 0 | UN | $85.50 |
| Pintura Vinílica Blanca | 25 | L | $320.00 |
| Cemento Gris | 500 | KG | $185.00 |
| Tubo PVC 1/2 pulgada | 0 | M | $45.00 |
| Clavos de 3 pulgadas | 8 | KG | $95.00 |

---

## 🔧 Funcionalidades Implementadas

### ✅ Modelos SQLAlchemy
- `Sale`, `SaleLine`
- `StockMove`, `StockMoveLine`
- `FinanceLedger`
- ENUMs: SaleStatus, StockMoveType, StockReferenceType, LedgerType, LedgerReferenceType

### ✅ Blueprint Sales
- `GET /sales/new` - POS con buscador y carrito
- `POST /sales/cart/add` - Agregar al carrito (HTMX)
- `POST /sales/cart/update` - Actualizar cantidad (HTMX)
- `POST /sales/cart/remove` - Remover producto (HTMX)
- `POST /sales/confirm` - Confirmar venta (transacción completa)

### ✅ Servicio Transaccional (sales_service.py)
- `confirm_sale(cart, session)` con:
  - Validaciones de negocio
  - Locking de stock (FOR UPDATE)
  - Transacción atómica
  - Rollback en caso de error

### ✅ Carrito en Session
- Almacenado en Flask session
- Estructura: `{'items': {'product_id': {'qty': float}}}`
- Se limpia automáticamente al confirmar venta

### ✅ UI/UX
- POS responsivo con Bootstrap 5
- Búsqueda de productos en tiempo real
- HTMX para actualizaciones parciales sin recarga
- Validación de stock en tiempo real
- Productos sin stock deshabilitados
- Mensajes flash informativos

### ✅ Validaciones
- Stock suficiente antes de agregar al carrito
- Stock suficiente al confirmar (con locking)
- Cantidad > 0
- Productos activos
- Carrito no vacío

---

## 🎯 Criterios de Aceptación (TODOS CUMPLIDOS)

- [x] Crear venta con carrito (productos + cantidades)
- [x] Calcular total correctamente
- [x] Confirmar venta persiste en DB
- [x] Stock se descuenta automáticamente
- [x] Ingreso registrado en finance_ledger
- [x] Validación de stock con locking (FOR UPDATE)
- [x] HTMX actualiza carrito sin recarga completa
- [x] Productos sin stock no se pueden agregar
- [x] Carrito vacío no se puede confirmar
- [x] Transacción atómica (rollback en error)

---

## 📝 Queries Útiles para Verificar

```sql
-- Ver últimas ventas
SELECT * FROM sale ORDER BY id DESC LIMIT 5;

-- Ver detalles de venta específica
SELECT sl.*, p.name, p.sale_price 
FROM sale_line sl 
JOIN product p ON sl.product_id = p.id 
WHERE sale_id = X;

-- Ver stock actual de productos
SELECT p.name, ps.on_hand_qty, u.symbol
FROM product p
JOIN product_stock ps ON p.id = ps.product_id
JOIN uom u ON p.uom_id = u.id
ORDER BY p.name;

-- Ver últimos movimientos de stock
SELECT sm.*, sr.type as ref_type
FROM stock_move sm
WHERE sm.type = 'OUT'
ORDER BY sm.id DESC
LIMIT 5;

-- Ver ingresos en ledger
SELECT * FROM finance_ledger 
WHERE type = 'INCOME' 
ORDER BY datetime DESC 
LIMIT 10;
```

---

## 🚀 Siguiente Fase

**FASE 3**: Módulo de Compras/Boletas (proveedores + aumento de stock)

---

## 🐛 Problemas Conocidos / Notas

1. **Session Secret Key**: La aplicación usa una secret_key de desarrollo. En producción debe cambiarse.

2. **Trigger de stock_move_line**: La base de datos debe tener un trigger que actualice automáticamente `product_stock.on_hand_qty` cuando se inserta en `stock_move_line`. Si no existe, el stock no se actualizará.

3. **Cantidades decimales**: El sistema soporta cantidades decimales (ej: 2.5 KG), pero asegúrese de que la UI permita decimales en los inputs.

4. **Validación de stock**: Se usa `SELECT ... FOR UPDATE` para prevenir race conditions. Esto funciona correctamente con transacciones de SQLAlchemy.

---

**Versión**: 0.2.0 - Fase 2 Completada  
**Última actualización**: Enero 2026

