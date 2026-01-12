# ✅ MEJORA 10 – Filtros de Stock en Productos

---

## 📋 **Resumen Ejecutivo**

**Objetivo:** Agregar filtros de stock (sin stock / poco stock) en el listado de productos, manteniendo compatibilidad con filtros existentes (categoría y búsqueda).

**Estado:** ✅ **COMPLETADO**

**Fecha:** Enero 2026

---

## 🎯 **Funcionalidad Implementada**

### **1. Filtro de Stock en Lista de Productos**

**Opciones:**
- ✅ **Todos** (default) - Muestra todos los productos
- ✅ **Sin stock** - Solo productos con `stock <= 0`
- ✅ **Poco stock** - Solo productos con `0 < stock <= umbral`

### **2. Umbral Configurable**

**Variable de Entorno:**
```env
LOW_STOCK_THRESHOLD=10
```

**Características:**
- ✅ Configurable en `.env`
- ✅ Default: `10` si no está definido
- ✅ Se muestra en UI: "Poco stock (≤ 10)"
- ✅ Leído desde `config.py`

### **3. Combinación de Filtros**

**Compatibilidad total con:**
- ✅ Búsqueda por texto (`q`)
- ✅ Filtro por categoría (`category_id`)
- ✅ Productos con/sin imagen (MEJORA 1)
- ✅ Productos activos/inactivos (lógica existente)

### **4. Filtrado a Nivel SQL**

**Eficiencia:**
- ✅ Filtros aplicados en PostgreSQL (no en Python)
- ✅ Uso de `COALESCE` para manejar productos sin `product_stock`
- ✅ LEFT JOIN optimizado
- ✅ Query eficiente con múltiples filtros

---

## 📁 **Archivos Modificados**

### **1. config.py**
```python
# MEJORA 10 - Stock Filters
LOW_STOCK_THRESHOLD = int(os.getenv('LOW_STOCK_THRESHOLD', '10'))
```

### **2. env.example**
```env
# MEJORA 10 - Stock Configuration
LOW_STOCK_THRESHOLD=10
```

### **3. app/blueprints/catalog.py**

**Cambios en `list_products()`:**
- Leer parámetro `stock_filter` de `request.args`
- Obtener `LOW_STOCK_THRESHOLD` de `current_app.config`
- Aplicar filtros SQL según `stock_filter`:
  - `'out'` → `COALESCE(product_stock.on_hand_qty, 0) <= 0`
  - `'low'` → `COALESCE(product_stock.on_hand_qty, 0) > 0 AND <= threshold`
- Validar `stock_filter` inválido
- Pasar `selected_stock_filter` y `low_stock_threshold` al template

### **4. app/templates/products/list.html**

**Cambios:**
- Agregado `<select name="stock_filter">` con 3 opciones
- Ajustado layout de formulario (col-md-2 para categoría y stock)
- Actualizado botón "Limpiar" para incluir `selected_stock_filter`
- Agregado badge en "Filtros activos" para stock
- Badge amarillo con icono para distinguir de otros filtros

---

## 🗂️ **Lógica de Filtrado**

### **Caso 1: Sin Stock (`stock_filter=out`)**

```python
query = query.filter(
    func.coalesce(ProductStock.on_hand_qty, 0) <= 0
)
```

**SQL Generado:**
```sql
WHERE COALESCE(product_stock.on_hand_qty, 0) <= 0
```

**Incluye:**
- Productos con `stock = 0`
- Productos con `stock < 0` (casos raros)
- Productos sin fila en `product_stock` (tratados como 0)

---

### **Caso 2: Poco Stock (`stock_filter=low`)**

```python
query = query.filter(
    func.coalesce(ProductStock.on_hand_qty, 0) > 0,
    func.coalesce(ProductStock.on_hand_qty, 0) <= low_stock_threshold
)
```

**SQL Generado:**
```sql
WHERE COALESCE(product_stock.on_hand_qty, 0) > 0
  AND COALESCE(product_stock.on_hand_qty, 0) <= 10
```

**Incluye:**
- Productos con `0 < stock <= 10`
- Rango: `1, 2, 3, ..., 10` (si threshold=10)

---

### **Caso 3: Todos (`stock_filter=''` o ausente)**

```python
# No se aplica filtro de stock
```

**Comportamiento:**
- Muestra todos los productos (con o sin stock)

---

## 💡 **Manejo de Casos Especiales**

### **Productos sin `product_stock`**

**Problema:** Algunos productos pueden no tener fila en `product_stock`

**Solución:**
```sql
LEFT OUTER JOIN product_stock ON product.id = product_stock.product_id
COALESCE(product_stock.on_hand_qty, 0)
```

**Comportamiento:**
- Se tratan como `stock = 0`
- Aparecen en filtro "Sin stock"
- NO aparecen en filtro "Poco stock"

---

### **Validación de `stock_filter` Inválido**

**Código:**
```python
elif stock_filter not in ['', 'out', 'low']:
    flash('Filtro de stock inválido. Mostrando todos los productos.', 'info')
    stock_filter = ''
```

**Comportamiento:**
- Si `stock_filter=invalid` → flash warning + mostrar todos
- No rompe la aplicación
- Usuario informado del error

---

## 🎨 **Interfaz de Usuario**

### **Formulario de Filtros**

```
┌────────────────────────────────────────────────────────────────┐
│ Categoría [Todas ▼] Stock [Todos ▼] Buscar [...........] [Aplicar] [Limpiar] [Nuevo] │
└────────────────────────────────────────────────────────────────┘
```

**Layout:**
- Categoría: `col-md-2`
- Stock: `col-md-2`
- Buscar: `col-md-4`
- Botones: `col-md-4`

---

### **Select de Stock**

```html
<select class="form-select" id="stock_filter" name="stock_filter">
    <option value="">Todos</option>
    <option value="out">Sin stock</option>
    <option value="low">Poco stock (≤ 10)</option>
</select>
```

**Características:**
- Valor actual se mantiene (`selected` attribute)
- Umbral dinámico: `{{ low_stock_threshold }}`

---

### **Badge de Filtro Activo**

```html
{% if selected_stock_filter %}
<span class="badge bg-warning text-dark">
    Stock: 
    {% if selected_stock_filter == 'out' %}Sin stock
    {% elif selected_stock_filter == 'low' %}Poco stock (≤ {{ low_stock_threshold }})
    {% endif %}
</span>
{% endif %}
```

**Estilo:**
- Badge amarillo (`bg-warning`) para distinguir de otros filtros
- Muestra el umbral actual

---

## 🔄 **Flujos de Usuario**

### **Flujo 1: Filtrar por Poco Stock**

```
1. Usuario va a /products
   ↓
2. Selecciona Stock: "Poco stock (≤ 10)"
   ↓
3. Click "Aplicar"
   ↓
4. URL: /products?stock_filter=low
   ↓
5. Se muestran solo productos con 0 < stock <= 10
   ↓
6. Badge amarillo: "Stock: Poco stock (≤ 10)"
```

---

### **Flujo 2: Combinar Filtros**

```
1. Usuario selecciona:
   - Categoría: "Electricidad"
   - Stock: "Sin stock"
   - Búsqueda: "cable"
   ↓
2. Click "Aplicar"
   ↓
3. URL: /products?category_id=4&stock_filter=out&q=cable
   ↓
4. Se muestran productos que cumplan LAS 3 condiciones:
   - Categoría = Electricidad
   - Stock <= 0
   - Nombre/SKU/barcode contiene "cable"
   ↓
5. 3 badges activos:
   - "Categoría: Electricidad"
   - "Stock: Sin stock"
   - "Búsqueda: cable"
```

---

### **Flujo 3: Limpiar Todos los Filtros**

```
1. Usuario tiene filtros activos
   ↓
2. Click "Limpiar"
   ↓
3. Redirige a /products (sin query params)
   ↓
4. Todos los filtros resetean:
   - Stock: "Todos"
   - Categoría: "Todas"
   - Búsqueda: vacía
   ↓
5. Se muestran todos los productos
```

---

## ✅ **Validaciones Implementadas**

| Validación | Comportamiento |
|------------|----------------|
| `stock_filter` vacío | Muestra todos (no aplica filtro) |
| `stock_filter=out` | Solo `stock <= 0` |
| `stock_filter=low` | Solo `0 < stock <= threshold` |
| `stock_filter=invalid` | Flash warning + muestra todos |
| Productos sin `product_stock` | Tratados como `stock = 0` |
| Combinación con otros filtros | Intersección (AND logic) |
| Umbral personalizado | Lee de `.env` o usa default 10 |

---

## 📊 **Ejemplos de Queries SQL**

### **Sin Stock:**

```sql
SELECT product.* 
FROM product 
LEFT OUTER JOIN product_stock 
  ON product.id = product_stock.product_id 
WHERE COALESCE(product_stock.on_hand_qty, 0) <= 0 
ORDER BY product.name;
```

### **Poco Stock:**

```sql
SELECT product.* 
FROM product 
LEFT OUTER JOIN product_stock 
  ON product.id = product_stock.product_id 
WHERE COALESCE(product_stock.on_hand_qty, 0) > 0 
  AND COALESCE(product_stock.on_hand_qty, 0) <= 10 
ORDER BY product.name;
```

### **Combinación (Categoría + Poco Stock + Búsqueda):**

```sql
SELECT product.* 
FROM product 
LEFT OUTER JOIN product_stock 
  ON product.id = product_stock.product_id 
WHERE product.category_id = 3 
  AND COALESCE(product_stock.on_hand_qty, 0) > 0 
  AND COALESCE(product_stock.on_hand_qty, 0) <= 10 
  AND (
    LOWER(product.name) LIKE '%cable%' 
    OR LOWER(product.sku) LIKE '%cable%'
    OR LOWER(product.barcode) LIKE '%cable%'
  )
ORDER BY product.name;
```

---

## 🧪 **Testing**

**Documento:** `MEJORA10_TESTING.md`

**Cobertura:**
- ✅ 30+ casos de prueba
- ✅ Filtros individuales (sin stock, poco stock, todos)
- ✅ Combinaciones de filtros (stock + categoría + búsqueda)
- ✅ Validación de valores inválidos
- ✅ Casos borde (stock = 0, stock = umbral, stock NULL)
- ✅ Integración con compras/ventas
- ✅ Performance con gran volumen de datos
- ✅ Compatibilidad con funcionalidades existentes

---

## 📈 **Mejoras Sobre el Sistema Anterior**

### **Antes (sin filtros de stock):**
- ❌ Difícil identificar productos sin stock
- ❌ No hay alertas de poco stock
- ❌ Usuario debe revisar columna manualmente
- ❌ No se puede filtrar rápidamente

### **Después (MEJORA 10):**
- ✅ Filtro rápido de productos sin stock
- ✅ Identificación inmediata de poco stock
- ✅ Umbral configurable según negocio
- ✅ Combinable con otros filtros
- ✅ Query SQL eficiente
- ✅ UI clara y consistente

---

## 🔐 **Seguridad y Robustez**

### **1. Validación de Entrada:**
- `stock_filter` validado en backend
- Valores inválidos no rompen la aplicación
- Flash message informativo al usuario

### **2. Manejo de NULL:**
- `COALESCE` previene errores con productos sin `product_stock`
- Comportamiento predecible y consistente

### **3. Inyección SQL:**
- Uso de SQLAlchemy ORM (parámetros seguros)
- No hay concatenación de strings en queries

---

## 🚀 **Próximos Pasos Sugeridos (Futuro)**

1. **Indicador Visual en Tabla:**
   - Marcar filas con poco stock (color amarillo)
   - Marcar filas sin stock (color rojo)

2. **Alertas Proactivas:**
   - Dashboard con total de productos sin stock
   - Notificación cuando productos llegan a poco stock

3. **Umbral Personalizado por Producto:**
   - Campo `low_stock_alert` en tabla `product`
   - Umbral diferente para cada tipo de producto

4. **Exportar Listado:**
   - Botón para exportar productos filtrados a CSV/Excel
   - Útil para realizar pedidos a proveedores

5. **Historial de Stock:**
   - Gráfico de evolución de stock por producto
   - Predicción de cuándo se quedará sin stock

---

## ✅ **Checklist de Completitud**

- [x] Variable `LOW_STOCK_THRESHOLD` en config ✅
- [x] Variable en `.env.example` con documentación ✅
- [x] Lógica de filtrado en `catalog.py` ✅
- [x] Filtros SQL eficientes con `COALESCE` ✅
- [x] Select de stock en template ✅
- [x] Badge de filtro activo ✅
- [x] Botón "Limpiar" actualizado ✅
- [x] Validación de valores inválidos ✅
- [x] Compatibilidad con filtros existentes ✅
- [x] Documentación de testing ✅
- [x] Documentación de resumen ✅

---

## 🎯 **Resultado Final**

**Sistema con Gestión de Stock Mejorada:**
- ✅ Filtros rápidos y eficientes por estado de stock
- ✅ Umbral configurable para "poco stock"
- ✅ Combinación con búsqueda y categoría
- ✅ Query SQL optimizada
- ✅ UI clara y consistente
- ✅ Manejo robusto de casos especiales

**Todas las funcionalidades anteriores (MEJORA 1-9) siguen funcionando.**

---

**Última actualización:** Enero 2026  
**Versión:** 1.0  
**Autor:** Sistema Ferretería - MEJORA 10
