# FIX: Eliminación de Productos - Testing

## Objetivo
Verificar que se puede eliminar un producto correctamente cuando no tiene referencias, y que el sistema previene la eliminación cuando el producto está en uso.

---

## Preparación

### 1. Aplicar Migración SQL

**IMPORTANTE:** Antes de probar, ejecutar la migración:

```bash
psql -U <usuario> -d <database> -f db/migrations/FIX_product_stock_cascade_delete.sql
```

O desde psql:
```sql
\i db/migrations/FIX_product_stock_cascade_delete.sql
```

### 2. Verificar Migración

```sql
-- Verificar que la FK tiene ON DELETE CASCADE
SELECT 
  tc.constraint_name,
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS foreign_table_name,
  rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
  ON rc.constraint_name = tc.constraint_name
WHERE tc.table_name = 'product_stock' 
  AND tc.constraint_type = 'FOREIGN KEY';
```

**Resultado esperado:**
- `delete_rule = 'CASCADE'`

---

## Casos de Prueba

### 1. Eliminar producto SIN referencias (éxito)

**Preparación:**
- Crear un producto nuevo "Producto Test Delete"
- NO venderlo, NO comprarlo, NO hacer ajustes de stock

**Pasos:**
1. Ir a `/products`
2. Buscar "Producto Test Delete"
3. Click botón "Eliminar" (ícono trash)
4. Se abre modal de confirmación

**Resultado esperado en modal:**
- ✅ Título: "Confirmar Eliminación" (fondo rojo)
- ✅ Mensaje: "¡Atención! Esta acción es irreversible"
- ✅ Muestra datos del producto (nombre, SKU, stock, precio)
- ✅ Mensaje verde: "Este producto NO tiene ventas, compras ni movimientos de stock asociados. Es seguro eliminarlo."
- ✅ Botón "Eliminar Producto" habilitado

**Pasos (continuación):**
5. Click "Eliminar Producto"

**Resultado esperado:**
- ✅ Flash message verde: "Producto 'Producto Test Delete' eliminado exitosamente"
- ✅ Redirige a `/products`
- ✅ El producto ya NO aparece en el listado

**Verificación DB:**
```sql
-- Verificar que el producto fue eliminado
SELECT * FROM product WHERE name = 'Producto Test Delete';
-- Debe retornar 0 filas

-- Verificar que product_stock también fue eliminado (CASCADE)
SELECT * FROM product_stock WHERE product_id = <PRODUCT_ID>;
-- Debe retornar 0 filas
```

---

### 2. Eliminar producto CON ventas (bloqueado)

**Preparación:**
- Crear producto "Producto Con Ventas"
- Hacer al menos 1 venta de ese producto

**Pasos:**
1. Ir a `/products`
2. Buscar "Producto Con Ventas"
3. Click botón "Eliminar"
4. Se abre modal

**Resultado esperado en modal:**
- ✅ Título: "No se puede Eliminar" (fondo amarillo/warning)
- ✅ Mensaje: "No se puede eliminar este producto"
- ✅ Motivo: "El producto tiene X venta(s) asociada(s)"
- ✅ Sección "Referencias en el Sistema":
  - Muestra "X venta(s)" con ícono de carrito
- ✅ Mensaje info: "Alternativa: Use la opción 'Desactivar' para ocultar el producto sin perder el historial"
- ✅ Botón "Eliminar Producto" NO visible
- ✅ Botón "Ir a Editar (Desactivar)" visible

**Pasos (continuación):**
5. Click "Cancelar" o cerrar modal

**Resultado esperado:**
- ✅ Modal se cierra
- ✅ Producto NO fue eliminado (sigue en listado)

---

### 3. Eliminar producto CON boletas (bloqueado)

**Preparación:**
- Crear producto "Producto Con Boletas"
- Crear una boleta de compra con ese producto

**Pasos:**
1. Ir a `/products`
2. Buscar "Producto Con Boletas"
3. Click "Eliminar"

**Resultado esperado en modal:**
- ✅ Título: "No se puede Eliminar"
- ✅ Motivo: "El producto tiene X línea(s) de boleta asociada(s)"
- ✅ Sección "Referencias en el Sistema":
  - Muestra "X línea(s) de boleta" con ícono de recibo
- ✅ Botón "Eliminar" NO visible

---

### 4. Eliminar producto CON movimientos de stock (bloqueado)

**Preparación:**
- Crear producto "Producto Con Movimientos"
- Hacer un ajuste manual de stock (setear stock inicial a 10)

**Pasos:**
1. Ir a `/products`
2. Buscar "Producto Con Movimientos"
3. Click "Eliminar"

**Resultado esperado en modal:**
- ✅ Título: "No se puede Eliminar"
- ✅ Motivo: "El producto tiene X movimiento(s) de stock asociado(s)"
- ✅ Sección "Referencias en el Sistema":
  - Muestra "X movimiento(s) de stock" con ícono de caja
- ✅ Botón "Eliminar" NO visible

---

### 5. Eliminar producto CON múltiples referencias (bloqueado)

**Preparación:**
- Crear producto "Producto Muy Usado"
- Hacer 2 ventas
- Crear 1 boleta
- Hacer 3 ajustes de stock

**Pasos:**
1. Ir a `/products`
2. Buscar "Producto Muy Usado"
3. Click "Eliminar"

**Resultado esperado en modal:**
- ✅ Título: "No se puede Eliminar"
- ✅ Motivo incluye todas las referencias
- ✅ Sección "Referencias en el Sistema" muestra:
  - "2 venta(s)"
  - "1 línea(s) de boleta"
  - "3 movimiento(s) de stock"
- ✅ Total: 6 referencias

---

### 6. Eliminar producto con imagen (éxito)

**Preparación:**
- Crear producto "Producto Con Imagen"
- Subir una imagen al producto
- NO hacer ventas/compras

**Pasos:**
1. Verificar que la imagen existe en `static/uploads/products/`
2. Ir a `/products`
3. Buscar "Producto Con Imagen"
4. Click "Eliminar"
5. Confirmar eliminación

**Resultado esperado:**
- ✅ Producto eliminado exitosamente
- ✅ Flash message verde
- ✅ Archivo de imagen también fue eliminado del disco

**Verificación:**
```bash
# Verificar que la imagen fue eliminada
ls static/uploads/products/<nombre_imagen>
# Debe retornar: No such file or directory
```

---

### 7. Cancelar eliminación

**Preparación:**
- Producto sin referencias

**Pasos:**
1. Click "Eliminar"
2. Se abre modal de confirmación
3. Click "Cancelar"

**Resultado esperado:**
- ✅ Modal se cierra
- ✅ Producto NO fue eliminado
- ✅ Sigue visible en listado

---

### 8. Alternativa: Desactivar en lugar de eliminar

**Preparación:**
- Producto con ventas

**Pasos:**
1. Click "Eliminar"
2. Modal muestra que no se puede eliminar
3. Click "Ir a Editar (Desactivar)"

**Resultado esperado:**
- ✅ Redirige a `/products/<id>/edit`
- ✅ En el formulario, desmarcar checkbox "Producto activo"
- ✅ Guardar cambios
- ✅ Producto queda inactivo (no aparece en ventas)
- ✅ Historial de ventas/compras se mantiene intacto

---

### 9. Verificar cascade en DB (directo)

**Preparación:**
- Crear producto de prueba vía SQL

```sql
-- Crear producto
INSERT INTO product (name, uom_id, sale_price, active)
VALUES ('Test Cascade', 1, 100, true)
RETURNING id;

-- Verificar que se creó product_stock (vía trigger)
SELECT * FROM product_stock WHERE product_id = <PRODUCT_ID>;
```

**Pasos:**
```sql
-- Eliminar producto
DELETE FROM product WHERE id = <PRODUCT_ID>;

-- Verificar que product_stock también fue eliminado
SELECT * FROM product_stock WHERE product_id = <PRODUCT_ID>;
```

**Resultado esperado:**
- ✅ `DELETE` exitoso (sin error)
- ✅ `product_stock` retorna 0 filas (fue eliminado en cascade)
- ✅ NO hay error "blank-out primary key"

---

### 10. Producto con stock > 0 pero sin movimientos (edge case)

**Preparación:**
- Crear producto
- Setear stock inicial a 50 (esto crea movimiento ADJUST)

**Pasos:**
1. Click "Eliminar"

**Resultado esperado:**
- ❌ Modal muestra "No se puede Eliminar"
- ❌ Motivo: "El producto tiene 1 movimiento(s) de stock asociado(s)"
- ✅ Esto es correcto: el ajuste de stock inicial crea un movimiento

**Nota:** Si se quiere permitir eliminar productos con solo movimientos ADJUST MANUAL, habría que modificar `can_hard_delete_product` para excluir esos movimientos. Pero por seguridad, es mejor bloquear cualquier movimiento.

---

## Queries de Verificación

### Verificar integridad después de eliminación

```sql
-- 1. Verificar que no hay product_stock huérfanos
SELECT ps.product_id 
FROM product_stock ps
LEFT JOIN product p ON p.id = ps.product_id
WHERE p.id IS NULL;
-- Debe retornar 0 filas

-- 2. Verificar que productos eliminados no tienen referencias
-- (esto no debería pasar si can_hard_delete_product funciona bien)
SELECT 
  (SELECT COUNT(*) FROM sale_line WHERE product_id NOT IN (SELECT id FROM product)) AS orphan_sales,
  (SELECT COUNT(*) FROM purchase_invoice_line WHERE product_id NOT IN (SELECT id FROM product)) AS orphan_invoices,
  (SELECT COUNT(*) FROM stock_move_line WHERE product_id NOT IN (SELECT id FROM product)) AS orphan_moves;
-- Todos deben ser 0
```

---

## Checklist Final

- [ ] Migración SQL aplicada correctamente
- [ ] FK `product_stock.product_id` tiene `ON DELETE CASCADE`
- [ ] Modelo `Product` tiene `cascade='all, delete-orphan'` en relationship
- [ ] Servicio `can_hard_delete_product` funciona correctamente
- [ ] Modal de confirmación se abre vía HTMX
- [ ] Modal muestra información correcta (puede/no puede eliminar)
- [ ] Eliminación exitosa cuando no hay referencias
- [ ] Eliminación bloqueada cuando hay ventas
- [ ] Eliminación bloqueada cuando hay boletas
- [ ] Eliminación bloqueada cuando hay movimientos de stock
- [ ] Imagen del producto se elimina del disco
- [ ] `product_stock` se elimina automáticamente (cascade)
- [ ] NO hay error "blank-out primary key"
- [ ] Alternativa "Desactivar" funciona correctamente

---

## Notas Importantes

1. **Cascade solo en product_stock:** La FK cascade SOLO se aplica a `product_stock`, que es una relación 1:1 dependiente. Otras tablas (`sale_line`, `purchase_invoice_line`, `stock_move_line`) mantienen `RESTRICT` o `NO ACTION` para prevenir eliminación accidental de productos en uso.

2. **Validación en aplicación:** La función `can_hard_delete_product` es la primera línea de defensa. La FK cascade es solo para evitar el error "blank-out primary key".

3. **Soft delete recomendado:** Para productos con historial, siempre se recomienda "Desactivar" en lugar de eliminar.

4. **Auditoría:** No hay log de eliminaciones. Si se requiere, implementar tabla `product_deletion_log` con trigger.

---

## Fin del Testing
