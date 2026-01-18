# FIX: Actualización de Cantidad en Carrito (MEJORA A Compatibility)

## Problema
Después de implementar MEJORA A (múltiples UOMs), el carrito no permitía cambiar la cantidad de productos. Al intentar modificar la cantidad, volvía a 1.

## Causa Raíz
Con MEJORA A, el formato del carrito cambió:
- **Antes:** `cart_key = product_id` (ej: "42")
- **Después:** `cart_key = product_id_uom_id` (ej: "42_3")

Las funciones `cart_update` y `cart_remove` seguían usando solo `product_id`, por lo que no encontraban el item correcto en el carrito.

## Solución Aplicada

### Archivos Modificados:

1. **`app/templates/sales/_cart.html`**
   - Cambiado: `<input type="hidden" name="product_id">` → `<input type="hidden" name="cart_key">`
   - Actualizado: `hx-include="[name='product_id']"` → `hx-include="[name='cart_key']"`
   - Aplicado en: input de cantidad y botón de eliminar

2. **`app/blueprints/sales.py`**
   - **Función `cart_update()`:**
     - Ahora recibe `cart_key` en lugar de `product_id`
     - Extrae `product_id` y `uom_id` del cart_key o del item
     - Calcula `qty_base` usando `conversion_to_base` para validación de stock
     - Actualiza el item usando el `cart_key` correcto
     - Mantiene compatibilidad con formato legacy
   
   - **Función `cart_remove()`:**
     - Ahora recibe `cart_key` en lugar de `product_id`
     - Elimina el item usando el `cart_key` correcto

### Mejoras Adicionales:
- Validación de stock usando `qty_base` (unidad base) en lugar de `qty` directa
- Compatibilidad con formato legacy del carrito (productos agregados antes de MEJORA A)
- Manejo robusto de errores

---

## Testing

### Pre-requisitos
- Sistema levantado
- MEJORA A implementada (múltiples UOMs)
- Al menos 1 producto con múltiples UOMs
- Al menos 1 producto con una sola UOM

---

### Test 1: Cambiar cantidad de producto con UOM base

**Pasos:**
1. Ir a POS (`/sales/new`)
2. Agregar producto con UOM base (ej: Metro)
3. En el carrito, cambiar cantidad de 1 a 5
4. Esperar 500ms (delay del HTMX)

**Resultado esperado:**
- ✅ La cantidad se actualiza a 5
- ✅ El subtotal se recalcula correctamente
- ✅ El total del carrito se actualiza
- ✅ La cantidad NO vuelve a 1

---

### Test 2: Cambiar cantidad de producto con UOM no base

**Pasos:**
1. Agregar producto con UOM "Rollo" (factor 100)
2. Cambiar cantidad de 1 a 2
3. Verificar que el stock se valida correctamente

**Resultado esperado:**
- ✅ La cantidad se actualiza a 2
- ✅ Subtotal = 2 * precio_rollo
- ✅ Stock se valida en unidad base (200 metros, no 2)

---

### Test 3: Cambiar cantidad con stock insuficiente

**Pasos:**
1. Producto con stock de 50 unidades base
2. Agregar 1 unidad al carrito
3. Intentar cambiar cantidad a 100

**Resultado esperado:**
- ✅ Mensaje: "Stock insuficiente para [producto]. Disponible: 50"
- ✅ La cantidad NO cambia (se mantiene en 1)
- ✅ El carrito se refresca sin cambios

---

### Test 4: Cambiar cantidad a 0 (eliminar automático)

**Pasos:**
1. Agregar producto al carrito
2. Cambiar cantidad a 0

**Resultado esperado:**
- ✅ Producto se elimina automáticamente del carrito
- ✅ Mensaje: "Producto eliminado del carrito"
- ✅ El carrito se actualiza sin ese producto

---

### Test 5: Cambiar cantidad con decimales

**Pasos:**
1. Agregar producto al carrito
2. Cambiar cantidad a 2.5

**Resultado esperado:**
- ✅ La cantidad se actualiza a 2.5
- ✅ Subtotal = 2.5 * precio_unitario
- ✅ Total correcto

---

### Test 6: Eliminar producto del carrito

**Pasos:**
1. Agregar 2 productos al carrito
2. Click en botón de eliminar (🗑️) del primer producto

**Resultado esperado:**
- ✅ Producto se elimina del carrito
- ✅ Mensaje: "Producto removido del carrito"
- ✅ El otro producto permanece
- ✅ Total se recalcula

---

### Test 7: Mismo producto con diferentes UOMs

**Pasos:**
1. Agregar "Cable" con UOM "Metro" (qty: 10)
2. Agregar "Cable" con UOM "Rollo" (qty: 2)
3. Cambiar cantidad de "Metro" a 20
4. Cambiar cantidad de "Rollo" a 3

**Resultado esperado:**
- ✅ Ambas líneas se mantienen separadas en el carrito
- ✅ Cada línea se actualiza independientemente
- ✅ Totales correctos para cada línea
- ✅ Total general = (20 * precio_metro) + (3 * precio_rollo)

---

### Test 8: Cambiar cantidad rápidamente (debounce)

**Pasos:**
1. Agregar producto al carrito
2. Cambiar cantidad rápidamente: 1 → 2 → 3 → 5 (sin esperar)

**Resultado esperado:**
- ✅ Solo se envía la última actualización (5)
- ✅ No se spamea el servidor con requests intermedias
- ✅ Cantidad final: 5

---

### Test 9: Compatibilidad con productos legacy

**Pasos:**
1. Si hay productos en carrito agregados ANTES de MEJORA A
2. Intentar cambiar su cantidad

**Resultado esperado:**
- ✅ La cantidad se actualiza correctamente
- ✅ El sistema detecta formato legacy y lo maneja
- ✅ No hay errores

---

### Test 10: Validación de entrada vacía

**Pasos:**
1. Agregar producto al carrito
2. Borrar completamente el valor del input (dejar vacío)
3. Click fuera del input

**Resultado esperado:**
- ✅ El carrito se refresca sin cambios
- ✅ La cantidad se mantiene como estaba
- ✅ No hay error

---

## Queries de Verificación

### Verificar estructura del carrito en session
```python
# En Flask shell o debug
from flask import session
print(session.get('cart'))

# Formato esperado:
{
  'items': {
    '42_3': {
      'product_id': 42,
      'uom_id': 3,
      'qty': 5.0,
      'qty_base': 500.0,
      'unit_price': 9500.0
    },
    '42_1': {
      'product_id': 42,
      'uom_id': 1,
      'qty': 10.0,
      'qty_base': 10.0,
      'unit_price': 100.0
    }
  }
}
```

---

## Resumen de Cambios

| Componente | Antes | Después |
|------------|-------|---------|
| **Template input** | `name="product_id"` | `name="cart_key"` |
| **Template include** | `[name='product_id']` | `[name='cart_key']` |
| **cart_update()** | Busca por `product_id` | Busca por `cart_key` |
| **cart_remove()** | Busca por `product_id` | Busca por `cart_key` |
| **Validación stock** | Usa `qty` directa | Usa `qty_base` (conversión) |
| **Compatibilidad** | Solo formato nuevo | Legacy + nuevo |

---

## Notas Importantes

1. **cart_key** es la clave única del item en el carrito:
   - Formato nuevo: `"product_id_uom_id"` (ej: `"42_3"`)
   - Formato legacy: `"product_id"` (ej: `"42"`)

2. **qty vs qty_base:**
   - `qty`: Cantidad en la UOM seleccionada por el usuario
   - `qty_base`: Cantidad en la unidad base (para stock)
   - Ejemplo: 2 Rollos (factor 100) = qty:2, qty_base:200

3. **Debounce de 500ms:**
   - Evita requests excesivas al servidor
   - El usuario puede escribir sin interrupciones

4. **Compatibilidad backward:**
   - Productos agregados antes de MEJORA A siguen funcionando
   - El sistema detecta automáticamente el formato

---

## Estado

✅ **RESUELTO** - El carrito ahora permite cambiar cantidades correctamente con MEJORA A implementada.
