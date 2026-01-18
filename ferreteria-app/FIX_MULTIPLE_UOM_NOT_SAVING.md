# FIX: Segunda UOM no se guarda al crear producto

## Problema Reportado

Al agregar un producto con más de una unidad de medida, la segunda unidad de medida agregada no se guarda al crear el producto.

## Diagnóstico Implementado

### 1. Logging Agregado en Backend

Se agregó logging detallado en `app/blueprints/catalog.py` para diagnosticar el problema:

```python
# DEBUG: Log all form data
logger.info(f"Creating product '{name}' - Form data keys: {list(request.form.keys())}")
logger.info(f"uom_base_index: {uom_base_index}")

# Para cada fila UOM
logger.info(f"Row {i}: uom_id={repr(uom_id)}, sale_price={repr(sale_price)}, conversion={repr(conversion)}")

# Total parseado
logger.info(f"Total UOM prices parsed: {len(uom_prices_data)}, data: {uom_prices_data}")
```

### 2. Validaciones Agregadas en Frontend

Se restauraron las validaciones del formulario que faltaban:

```javascript
// Solo validar el formulario de producto
if (form.id === 'product-form') {
  // Validar UOM prices
  const rows = form.querySelectorAll('.uom-price-row');
  
  // Check at least one row
  if (rows.length === 0) {
    e.preventDefault();
    alert('Debe definir al menos una unidad de medida con precio');
    return false;
  }
  
  // Check exactly one base
  const baseRadios = form.querySelectorAll('.is-base-radio:checked');
  if (baseRadios.length !== 1) {
    e.preventDefault();
    alert('Debe seleccionar exactamente una unidad de medida como base');
    return false;
  }
  
  // Check for duplicate UOMs
  const selectedUoms = Array.from(form.querySelectorAll('.uom-select'))
    .map(select => select.value)
    .filter(value => value !== '');
  
  const uniqueUoms = new Set(selectedUoms);
  if (selectedUoms.length !== uniqueUoms.size) {
    e.preventDefault();
    alert('No puede haber unidades de medida duplicadas');
    return false;
  }
  
  // Log form data for debugging
  console.log('Submitting product form with', rows.length, 'UOM rows');
  rows.forEach((row, idx) => {
    const uomSelect = row.querySelector('.uom-select');
    const priceInput = row.querySelector('input[name*="sale_price"]');
    const convInput = row.querySelector('input[name*="conversion_to_base"]');
    console.log(`Row ${idx}:`, {
      uom: uomSelect?.value,
      price: priceInput?.value,
      conversion: convInput?.value
    });
  });
}
```

### 3. Mejora en `attachNumArHandlers`

Se mejoró el manejo de valores vacíos y la inicialización:

```javascript
function attachNumArHandlers(input) {
  if (!input || input.dataset.numArBound === '1') return;
  input.dataset.numArBound = '1';

  input.addEventListener('focus', function() {
    const normalized = normalizeToBackend(this.value);
    this.value = normalized || '0.00';
    this.select?.();
  });

  input.addEventListener('blur', function() {
    const formatted = formatNumberAR(this.value);
    this.value = formatted || '0,00';
  });

  // formatear al cargar - solo si tiene valor
  if (input.value) {
    const formatted = formatNumberAR(input.value);
    if (formatted) {
      input.value = formatted;
    }
  }
}
```

---

## Testing Manual

### Pre-requisitos
- Sistema levantado
- Al menos 2 UOMs creadas en el sistema
- Navegador con DevTools abierto (Console y Network tabs)

---

### Test 1: Crear Producto con 2 UOMs

**Pasos:**
1. Ir a `/products/new`
2. Llenar:
   - Nombre: "Producto Test Multiple UOM"
   - Categoría: cualquiera (opcional)
3. En la primera fila UOM:
   - Seleccionar UOM: "Unidad"
   - Precio: `100,00`
   - Conversión: `1,00`
   - Marcar como base: ✓
4. Click "Agregar Unidad"
5. En la segunda fila UOM:
   - Seleccionar UOM: "Caja" (o cualquier otra)
   - Precio: `1.200,00`
   - Conversión: `12,00`
   - NO marcar como base
6. Abrir DevTools → Console
7. Click "Crear Producto"

**Verificaciones en Console:**
```
Submitting product form with 2 UOM rows
Row 0: {uom: "1", price: "100.00", conversion: "1.00"}
Row 1: {uom: "2", price: "1200.00", conversion: "12.00"}
```

**Verificaciones en Backend (logs):**
```
INFO: Creating product 'Producto Test Multiple UOM' - Form data keys: [...]
INFO: uom_base_index: 0
INFO: Row 0: uom_id='1', sale_price='100.00', conversion='1.00'
INFO: Row 1: uom_id='2', sale_price='1200.00', conversion='12.00'
INFO: Total UOM prices parsed: 2, data: [...]
```

**Resultado esperado:**
- ✅ Producto creado exitosamente
- ✅ Al editar el producto, se ven ambas UOMs
- ✅ En DB: 2 filas en `product_uom_price`

**Query de verificación:**
```sql
SELECT 
  pup.id,
  pup.product_id,
  u.name as uom_name,
  pup.sale_price,
  pup.conversion_to_base,
  pup.is_base
FROM product_uom_price pup
JOIN uom u ON u.id = pup.uom_id
WHERE pup.product_id = (SELECT id FROM product WHERE name = 'Producto Test Multiple UOM')
ORDER BY pup.is_base DESC, pup.id;
```

**Resultado esperado en DB:**
```
 id | product_id | uom_name | sale_price | conversion_to_base | is_base 
----+------------+----------+------------+--------------------+---------
  1 |        123 | Unidad   |     100.00 |               1.00 | t
  2 |        123 | Caja     |    1200.00 |              12.00 | f
```

---

### Test 2: Crear Producto con 3 UOMs

**Pasos:**
1. Ir a `/products/new`
2. Llenar nombre: "Producto Test 3 UOM"
3. Configurar primera UOM (base)
4. Click "Agregar Unidad" (2 veces)
5. Configurar segunda y tercera UOM
6. Verificar en Console que se envían 3 filas
7. Crear producto

**Resultado esperado:**
- ✅ 3 UOMs guardadas
- ✅ Logs muestran 3 filas parseadas

---

### Test 3: Agregar UOM y Remover

**Pasos:**
1. Ir a `/products/new`
2. Agregar 3 UOMs
3. Remover la segunda (click en botón trash)
4. Verificar que quedan 2 filas
5. Crear producto

**Resultado esperado:**
- ✅ Solo 2 UOMs guardadas (la 1ra y 3ra original)
- ✅ Índices reindexados correctamente

---

### Test 4: Cambiar Base UOM

**Pasos:**
1. Ir a `/products/new`
2. Agregar 2 UOMs
3. Marcar la segunda como base (radio button)
4. Crear producto

**Resultado esperado:**
- ✅ La segunda UOM tiene `is_base=true` en DB
- ✅ Solo una UOM marcada como base

---

### Test 5: Validación - Sin Base Seleccionada

**Pasos:**
1. Ir a `/products/new`
2. Agregar 2 UOMs
3. Desmarcar ambos radio buttons (si es posible, o usar DevTools)
4. Intentar crear producto

**Resultado esperado:**
- ✅ Alert: "Debe seleccionar exactamente una unidad de medida como base"
- ✅ No se crea el producto

---

### Test 6: Validación - UOMs Duplicadas

**Pasos:**
1. Ir a `/products/new`
2. Agregar 2 UOMs
3. Seleccionar la misma UOM en ambas filas
4. Intentar crear producto

**Resultado esperado:**
- ✅ Alert: "No puede haber unidades de medida duplicadas"
- ✅ No se crea el producto

---

### Test 7: Editar Producto - Agregar UOM

**Pasos:**
1. Editar un producto existente con 1 UOM
2. Click "Agregar Unidad"
3. Configurar segunda UOM
4. Guardar

**Resultado esperado:**
- ✅ Producto actualizado con 2 UOMs
- ✅ Ambas UOMs visibles al recargar

---

### Test 8: Valores con Formato AR

**Pasos:**
1. Ir a `/products/new`
2. Agregar 2 UOMs
3. En precios, escribir manualmente:
   - Primera UOM: `1.500,50` (con formato AR)
   - Segunda UOM: `15000,75`
4. Crear producto

**Resultado esperado:**
- ✅ Valores normalizados correctamente en backend
- ✅ DB guarda: `1500.50` y `15000.75`
- ✅ Al editar, se muestran con formato AR

---

## Posibles Causas del Problema

Si después de las correcciones el problema persiste, verificar:

### 1. **Nombres de inputs no se actualizan**
   - Problema: `addUomPriceRow()` no reindexó correctamente
   - Verificar: Los `name` attributes deben ser `uom_prices[0][...]`, `uom_prices[1][...]`, etc.
   - Solución: La función `reindexUomPriceRows()` debe ejecutarse después de agregar

### 2. **Inputs vacíos o con valores inválidos**
   - Problema: Los inputs tienen `value=""` o valores no numéricos
   - Verificar: En Console, ver los valores antes de submit
   - Solución: `normalizeToBackend()` debe retornar `"0.00"` para valores vacíos

### 3. **Backend no recibe los datos**
   - Problema: Los datos no llegan al servidor
   - Verificar: En Network tab, ver el payload del POST
   - Solución: Asegurar que el form tenga `id="product-form"` y los inputs estén dentro

### 4. **Parse falla en backend**
   - Problema: `parse_decimal_ar()` lanza excepción
   - Verificar: Logs del servidor
   - Solución: Ya implementado con try/catch y logging

### 5. **Servicio `create_or_update_uom_prices` falla**
   - Problema: Error en la creación de registros
   - Verificar: Logs del servidor después de "Total UOM prices parsed"
   - Solución: Revisar `app/services/product_uom_service.py`

---

## Debugging en Vivo

### En el Navegador (Console)

Antes de crear el producto, ejecutar en Console:

```javascript
// Ver todas las filas UOM
document.querySelectorAll('.uom-price-row').forEach((row, idx) => {
  const uomSelect = row.querySelector('.uom-select');
  const priceInput = row.querySelector('input[name*="sale_price"]');
  const convInput = row.querySelector('input[name*="conversion_to_base"]');
  const baseRadio = row.querySelector('.is-base-radio');
  
  console.log(`Row ${idx}:`, {
    uom_name: uomSelect.name,
    uom_value: uomSelect.value,
    price_name: priceInput.name,
    price_value: priceInput.value,
    conv_name: convInput.name,
    conv_value: convInput.value,
    is_base: baseRadio.checked
  });
});
```

### En el Servidor (Logs)

Ver logs en tiempo real:

```bash
# PowerShell
cd ferreteria-app
docker-compose logs -f web
```

Buscar líneas que contengan:
- `Creating product`
- `Row 0:`, `Row 1:`, etc.
- `Total UOM prices parsed`

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `app/blueprints/catalog.py` | ✅ Logging agregado en `create_product()` |
| `app/templates/products/form.html` | ✅ Validaciones de formulario restauradas<br>✅ `attachNumArHandlers()` mejorado<br>✅ Logging en Console agregado |

---

## Próximos Pasos

1. **Ejecutar Test 1** con DevTools abierto
2. **Revisar Console** para ver los valores enviados
3. **Revisar Logs del servidor** para ver los valores recibidos
4. **Verificar DB** con la query proporcionada
5. **Si falla:** Copiar los logs completos y reportar

---

## Notas Importantes

- Los logs agregados son **temporales** para diagnóstico
- Una vez resuelto el problema, se pueden eliminar los `logger.info()` y `console.log()`
- El problema más probable es que los inputs dinámicos no se estén normalizando correctamente antes del submit
- La función `attachNumArHandlers()` ahora maneja mejor los valores vacíos

---

## Resumen

✅ **Logging agregado** en backend y frontend
✅ **Validaciones restauradas** en el formulario
✅ **Manejo de valores vacíos** mejorado
✅ **Tests documentados** para verificar el problema

El usuario debe ejecutar **Test 1** y reportar:
1. Lo que ve en Console (navegador)
2. Lo que ve en Logs (servidor)
3. Lo que ve en DB (query)

Con esa información podremos identificar exactamente dónde falla el flujo.
