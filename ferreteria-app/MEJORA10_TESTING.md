# 🧪 MEJORA 10 - Testing: Filtros de Stock en Productos

## 📋 **Objetivo**

Validar que el sistema permite filtrar productos por estado de stock (sin stock / poco stock) en combinación con los filtros existentes (categoría y búsqueda).

---

## ⚙️ **Configuración Previa**

### **Verificar Configuración**

**Archivo:** `.env`

```env
LOW_STOCK_THRESHOLD=10
```

**Verificación:**
1. Confirmar que existe la variable en `.env`
2. Si no existe, agregarla con valor `10`
3. Reiniciar aplicación si se modificó

---

## ✅ **Testing de Filtro de Stock**

### **Test 1.1: Filtro "Todos" (Default)**

**Pasos:**
1. Ir a `/products`
2. No seleccionar ningún filtro de stock
3. Verificar select "Stock" en "Todos"

**Resultado esperado:**
- ✅ Se muestran todos los productos (con stock, sin stock, poco stock)
- ✅ No hay badge de filtro activo de stock
- ✅ URL: `/products` (sin `stock_filter`)

---

### **Test 1.2: Filtro "Sin Stock"**

**Prerequisito:** Tener productos con `stock = 0` o `NULL`

**Pasos:**
1. Ir a `/products`
2. Seleccionar "Stock" → "Sin stock"
3. Click "Aplicar"

**Resultado esperado:**
- ✅ URL: `/products?stock_filter=out`
- ✅ Se muestran SOLO productos con `stock <= 0`
- ✅ Badge activo: "Stock: Sin stock"
- ✅ Productos con `stock > 0` NO aparecen

**Verificación SQL (manual):**
```sql
SELECT p.name, COALESCE(ps.on_hand_qty, 0) as stock
FROM product p
LEFT JOIN product_stock ps ON p.id = ps.product_id
WHERE COALESCE(ps.on_hand_qty, 0) <= 0;
```

---

### **Test 1.3: Filtro "Poco Stock"**

**Prerequisito:** Tener productos con `0 < stock <= 10` (o el umbral definido)

**Pasos:**
1. Ir a `/products`
2. Seleccionar "Stock" → "Poco stock (≤ 10)"
3. Click "Aplicar"

**Resultado esperado:**
- ✅ URL: `/products?stock_filter=low`
- ✅ Se muestran SOLO productos con `0 < stock <= 10`
- ✅ Badge activo: "Stock: Poco stock (≤ 10)"
- ✅ Productos con `stock = 0` NO aparecen
- ✅ Productos con `stock > 10` NO aparecen

**Verificación SQL (manual):**
```sql
SELECT p.name, COALESCE(ps.on_hand_qty, 0) as stock
FROM product p
LEFT JOIN product_stock ps ON p.id = ps.product_id
WHERE COALESCE(ps.on_hand_qty, 0) > 0
  AND COALESCE(ps.on_hand_qty, 0) <= 10;
```

---

### **Test 1.4: Productos Sin Fila en product_stock**

**Prerequisito:** Crear producto SIN crear fila en `product_stock` (o eliminar fila)

**Pasos:**
1. Filtrar por "Sin stock"
2. Verificar que el producto aparece

**Resultado esperado:**
- ✅ Productos sin `product_stock` se tratan como `stock = 0`
- ✅ Aparecen en filtro "Sin stock"
- ✅ NO aparecen en filtro "Poco stock"

---

### **Test 1.5: Cambiar Umbral (LOW_STOCK_THRESHOLD)**

**Pasos:**
1. Modificar `.env`: `LOW_STOCK_THRESHOLD=5`
2. Reiniciar aplicación: `docker compose restart web`
3. Ir a `/products`
4. Verificar select "Poco stock (≤ 5)"

**Resultado esperado:**
- ✅ El select muestra el nuevo umbral: "Poco stock (≤ 5)"
- ✅ Al filtrar por "Poco stock", solo muestra `0 < stock <= 5`

---

## ✅ **Testing de Combinación de Filtros**

### **Test 2.1: Stock + Categoría**

**Pasos:**
1. Seleccionar Categoría: "Herramientas Manuales"
2. Seleccionar Stock: "Sin stock"
3. Click "Aplicar"

**Resultado esperado:**
- ✅ URL: `/products?category_id=3&stock_filter=out`
- ✅ Se muestran SOLO productos de "Herramientas Manuales" SIN stock
- ✅ 2 badges activos:
  - "Categoría: Herramientas Manuales"
  - "Stock: Sin stock"

---

### **Test 2.2: Stock + Búsqueda**

**Pasos:**
1. Ingresar búsqueda: `martillo`
2. Seleccionar Stock: "Poco stock"
3. Click "Aplicar"

**Resultado esperado:**
- ✅ URL: `/products?q=martillo&stock_filter=low`
- ✅ Se muestran SOLO productos que:
  - Contengan "martillo" en nombre/SKU/barcode
  - Y tengan poco stock (0 < stock <= 10)
- ✅ 2 badges activos:
  - "Búsqueda: martillo"
  - "Stock: Poco stock (≤ 10)"

---

### **Test 2.3: Stock + Categoría + Búsqueda (Triple Filtro)**

**Pasos:**
1. Seleccionar Categoría: "Electricidad"
2. Seleccionar Stock: "Sin stock"
3. Ingresar búsqueda: `cable`
4. Click "Aplicar"

**Resultado esperado:**
- ✅ URL: `/products?category_id=4&stock_filter=out&q=cable`
- ✅ Se muestran SOLO productos que cumplan LAS 3 condiciones:
  - Categoría = "Electricidad"
  - Stock = 0
  - Nombre/SKU/barcode contiene "cable"
- ✅ 3 badges activos

---

### **Test 2.4: Orden de Filtros (Query Params)**

**Pasos:**
Probar diferentes órdenes de parámetros en URL:
- `/products?stock_filter=low&category_id=3&q=test`
- `/products?q=test&stock_filter=low`
- `/products?category_id=3&stock_filter=out`

**Resultado esperado:**
- ✅ Todas las combinaciones funcionan igual
- ✅ El orden de los parámetros no afecta el resultado

---

## ✅ **Testing de UI/UX**

### **Test 3.1: Select de Stock Persiste**

**Pasos:**
1. Seleccionar Stock: "Poco stock"
2. Click "Aplicar"
3. Verificar que el select sigue en "Poco stock (≤ 10)"

**Resultado esperado:**
- ✅ El select mantiene la opción seleccionada
- ✅ `selected` attribute en la opción correcta

---

### **Test 3.2: Botón "Limpiar"**

**Pasos:**
1. Aplicar Stock: "Sin stock" + Categoría: "Pintura" + Búsqueda: "blanca"
2. Click "Limpiar"

**Resultado esperado:**
- ✅ Redirige a `/products` (sin query params)
- ✅ Todos los filtros se resetean:
  - Stock: "Todos"
  - Categoría: "Todas"
  - Búsqueda: vacía
- ✅ No hay badges activos
- ✅ Se muestran todos los productos

---

### **Test 3.3: Badge de Filtro Activo**

**Pasos:**
1. Aplicar Stock: "Poco stock"
2. Verificar badge en la alerta de filtros activos

**Resultado esperado:**
- ✅ Badge amarillo con texto: "Stock: Poco stock (≤ 10)"
- ✅ El número 10 corresponde al `LOW_STOCK_THRESHOLD` configurado

---

### **Test 3.4: Sin Resultados**

**Pasos:**
1. Aplicar un filtro que no tenga productos (ej: Categoría inexistente + Sin stock)
2. Verificar mensaje

**Resultado esperado:**
- ✅ Tabla vacía
- ✅ Mensaje: "No hay productos para los filtros seleccionados." (o similar)
- ✅ Filtros siguen visibles y aplicados

---

## ✅ **Testing de Validación**

### **Test 4.1: stock_filter Inválido**

**Pasos:**
1. Navegar manualmente a: `/products?stock_filter=invalid`

**Resultado esperado:**
- ✅ Flash message (info): "Filtro de stock inválido. Mostrando todos los productos."
- ✅ Se muestran todos los productos
- ✅ Select de Stock vuelve a "Todos"
- ✅ URL se mantiene pero filtro no se aplica

---

### **Test 4.2: stock_filter Vacío**

**Pasos:**
1. Navegar a: `/products?stock_filter=`

**Resultado esperado:**
- ✅ Se trata como "Todos"
- ✅ No hay flash message
- ✅ Se muestran todos los productos

---

### **Test 4.3: Múltiples stock_filter**

**Pasos:**
1. Navegar a: `/products?stock_filter=out&stock_filter=low`

**Resultado esperado:**
- ✅ Flask toma el último valor (`low`)
- ✅ Solo se aplica un filtro (el último)

---

## ✅ **Testing de Casos Borde**

### **Test 5.1: Stock Exactamente en Umbral**

**Prerequisito:** Producto con `stock = 10` (valor del umbral)

**Pasos:**
1. Filtrar por "Poco stock (≤ 10)"
2. Verificar que aparece

**Resultado esperado:**
- ✅ Productos con `stock = umbral` aparecen en "Poco stock"
- ✅ Operador `<=` (menor o igual)

---

### **Test 5.2: Stock = 0.5 (Decimal)**

**Prerequisito:** Producto con `stock = 0.5`

**Pasos:**
1. Filtrar por "Poco stock"
2. Verificar que aparece

**Resultado esperado:**
- ✅ `0.5 > 0` y `0.5 <= 10` → aparece en "Poco stock"

---

### **Test 5.3: Stock Negativo (Raro)**

**Prerequisito:** Producto con `stock < 0` (por error o ajuste manual)

**Pasos:**
1. Filtrar por "Sin stock"
2. Verificar que aparece

**Resultado esperado:**
- ✅ `stock < 0` cumple `stock <= 0` → aparece en "Sin stock"

---

### **Test 5.4: Todos los Productos Sin Stock**

**Prerequisito:** Base de datos con TODOS los productos en `stock = 0`

**Pasos:**
1. Sin filtros: ver todos
2. Filtrar "Sin stock": ver todos
3. Filtrar "Poco stock": ver lista vacía

**Resultado esperado:**
- ✅ "Sin stock" muestra todos
- ✅ "Poco stock" muestra mensaje de sin resultados

---

## ✅ **Testing de Integración**

### **Test 6.1: Crear Producto y Filtrar**

**Pasos:**
1. Crear producto nuevo: "Martillo Test" con stock inicial 0
2. Ir a `/products?stock_filter=out`
3. Verificar que aparece

**Resultado esperado:**
- ✅ Productos recién creados son filtrados correctamente

---

### **Test 6.2: Actualizar Stock y Re-filtrar**

**Pasos:**
1. Producto "Martillo" tiene `stock = 0`
2. Filtrar "Sin stock" → aparece
3. Hacer una compra para agregar stock: `stock = 5`
4. Refrescar filtro "Sin stock"
5. Filtrar "Poco stock"

**Resultado esperado:**
- ✅ Después de actualizar stock a 5:
  - Ya NO aparece en "Sin stock"
  - SÍ aparece en "Poco stock"

---

### **Test 6.3: Venta Reduce Stock**

**Pasos:**
1. Producto "Pincel" tiene `stock = 11`
2. Filtrar "Poco stock" → NO aparece
3. Hacer venta de 5 unidades → `stock = 6`
4. Refrescar filtro "Poco stock"

**Resultado esperado:**
- ✅ Después de venta:
  - Ahora SÍ aparece en "Poco stock" (6 <= 10)

---

## ✅ **Testing de Performance**

### **Test 7.1: Query SQL Eficiente**

**Pasos:**
1. Aplicar filtro de stock
2. Verificar en logs PostgreSQL (si está habilitado) o con EXPLAIN

**Resultado esperado:**
- ✅ El filtro se hace en SQL (WHERE clause)
- ✅ NO se filtran resultados en Python
- ✅ Uso correcto de `COALESCE` para NULLs
- ✅ JOIN optimizado con `product_stock`

**Ejemplo Query esperado:**
```sql
SELECT product.* 
FROM product 
LEFT OUTER JOIN product_stock ON product.id = product_stock.product_id 
WHERE COALESCE(product_stock.on_hand_qty, 0) <= 0 
ORDER BY product.name;
```

---

### **Test 7.2: Gran Volumen de Datos**

**Prerequisito:** Base de datos con 1000+ productos

**Pasos:**
1. Aplicar filtro "Poco stock"
2. Medir tiempo de carga

**Resultado esperado:**
- ✅ Respuesta en < 1 segundo
- ✅ Sin errores de timeout
- ✅ Query SQL eficiente (verificar índices si es lento)

---

## ✅ **Testing de Compatibilidad**

### **Test 8.1: Productos Inactivos**

**Pasos:**
1. Crear producto con `active = False` y `stock = 0`
2. Filtrar "Sin stock"
3. Verificar comportamiento

**Resultado esperado:**
- ✅ Si actualmente el listado muestra productos inactivos, deben aparecer en filtro de stock
- ✅ Si actualmente el listado NO muestra inactivos, NO deben aparecer (mantener lógica existente)
- ✅ El filtro de stock NO modifica la lógica de `active`

---

### **Test 8.2: Productos con/sin Imagen**

**Pasos:**
1. Filtrar por stock
2. Verificar que productos con y sin imagen se muestran correctamente

**Resultado esperado:**
- ✅ Placeholder "Sin imagen" sigue funcionando
- ✅ Imágenes se muestran correctamente
- ✅ No hay conflictos con MEJORA 1 (fotos)

---

### **Test 8.3: Productos sin Categoría**

**Pasos:**
1. Producto con `category_id = NULL` y `stock = 0`
2. Filtrar "Sin stock"
3. Verificar que aparece

**Resultado esperado:**
- ✅ Productos sin categoría son filtrados correctamente por stock
- ✅ Muestra "-" o "Sin categoría" en columna de categoría

---

## 📊 **Resumen de URLs a Probar**

| URL | Descripción | Resultado Esperado |
|-----|-------------|-------------------|
| `/products` | Sin filtros | Todos los productos |
| `/products?stock_filter=out` | Sin stock | Solo stock <= 0 |
| `/products?stock_filter=low` | Poco stock | Solo 0 < stock <= 10 |
| `/products?stock_filter=invalid` | Inválido | Todos + flash warning |
| `/products?category_id=3&stock_filter=out` | Categoría + sin stock | Intersección |
| `/products?q=cable&stock_filter=low` | Búsqueda + poco stock | Intersección |
| `/products?category_id=3&stock_filter=low&q=test` | Triple filtro | Intersección 3 condiciones |

---

## 🎯 **Checklist Final**

| # | Test | Estado |
|---|------|--------|
| 1.1 | Filtro "Todos" default | ⬜ |
| 1.2 | Filtro "Sin stock" | ⬜ |
| 1.3 | Filtro "Poco stock" | ⬜ |
| 1.4 | Productos sin product_stock | ⬜ |
| 1.5 | Cambiar umbral threshold | ⬜ |
| 2.1 | Stock + Categoría | ⬜ |
| 2.2 | Stock + Búsqueda | ⬜ |
| 2.3 | Stock + Categoría + Búsqueda | ⬜ |
| 2.4 | Orden de query params | ⬜ |
| 3.1 | Select persiste valor | ⬜ |
| 3.2 | Botón "Limpiar" funciona | ⬜ |
| 3.3 | Badge de filtro activo | ⬜ |
| 3.4 | Sin resultados mensaje correcto | ⬜ |
| 4.1 | stock_filter inválido | ⬜ |
| 4.2 | stock_filter vacío | ⬜ |
| 4.3 | Múltiples stock_filter | ⬜ |
| 5.1 | Stock = umbral exacto | ⬜ |
| 5.2 | Stock decimal (0.5) | ⬜ |
| 5.3 | Stock negativo | ⬜ |
| 5.4 | Todos sin stock | ⬜ |
| 6.1 | Crear producto y filtrar | ⬜ |
| 6.2 | Actualizar stock y re-filtrar | ⬜ |
| 6.3 | Venta reduce stock | ⬜ |
| 7.1 | Query SQL eficiente | ⬜ |
| 7.2 | Gran volumen de datos | ⬜ |
| 8.1 | Productos inactivos | ⬜ |
| 8.2 | Productos con/sin imagen | ⬜ |
| 8.3 | Productos sin categoría | ⬜ |

---

**Última actualización:** Enero 2026  
**Autor:** Sistema Ferretería - MEJORA 10
