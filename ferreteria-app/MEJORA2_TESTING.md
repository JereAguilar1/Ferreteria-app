# MEJORA 2 - Testing: Filtro por Categoría en Listado de Productos

## ✅ Checklist de Pruebas

### **1. Preparación**
- [ ] Aplicación corriendo en http://localhost:5000
- [ ] Base de datos con productos de varias categorías
- [ ] Verificar que existan productos sin categoría (category_id NULL)

---

### **2. Visualización del Filtro**

#### Pasos:
1. Ir a: http://localhost:5000/products
2. Observar la barra de filtros

#### Resultado esperado:
- ✅ Se muestra un `<select>` con label "Categoría"
- ✅ Primera opción: "Todas las categorías"
- ✅ Resto de opciones: categorías ordenadas alfabéticamente
- ✅ Input de búsqueda sigue visible y funcional
- ✅ Botón "Aplicar Filtros"
- ✅ Botón "Nuevo" para crear productos

---

### **3. Filtrar por Categoría (Sin Búsqueda)**

#### Pasos:
1. En /products, seleccionar "Herramientas" del dropdown
2. Click en "Aplicar Filtros"

#### Resultado esperado:
- ✅ URL cambia a: `/products?category_id=1` (o el ID de Herramientas)
- ✅ Solo se muestran productos de categoría "Herramientas"
- ✅ Productos de otras categorías NO aparecen
- ✅ Productos sin categoría (NULL) NO aparecen
- ✅ El select mantiene "Herramientas" seleccionado
- ✅ Aparece badge informativo: "Filtros activos: Categoría: Herramientas"
- ✅ Se muestra contador: "Mostrando X producto(s)"
- ✅ Botón "Limpiar" está visible

---

### **4. Filtrar por Otra Categoría**

#### Pasos:
1. Cambiar el filtro a "Electricidad"
2. Click en "Aplicar Filtros"

#### Resultado esperado:
- ✅ URL: `/products?category_id=3` (o ID de Electricidad)
- ✅ Solo productos de "Electricidad"
- ✅ Badge muestra: "Categoría: Electricidad"
- ✅ Contador actualizado

---

### **5. Volver a "Todas las Categorías"**

#### Pasos:
1. Seleccionar "Todas las categorías" del dropdown
2. Click en "Aplicar Filtros"

#### Resultado esperado:
- ✅ URL: `/products` (sin query params)
- ✅ Se muestran TODOS los productos (incluyendo sin categoría)
- ✅ Badge de filtros activos NO aparece
- ✅ Botón "Limpiar" NO aparece (si no hay búsqueda)

---

### **6. Buscar SIN Filtro de Categoría**

#### Pasos:
1. En /products, escribir "martillo" en el buscador
2. Dejar "Todas las categorías" seleccionado
3. Click en "Aplicar Filtros"

#### Resultado esperado:
- ✅ URL: `/products?q=martillo`
- ✅ Se muestran productos con "martillo" en nombre/SKU/barcode
- ✅ De TODAS las categorías (si hay martillos en varias)
- ✅ Badge: "Búsqueda: martillo"
- ✅ Input de búsqueda mantiene el valor "martillo"
- ✅ Select mantiene "Todas las categorías"

---

### **7. Buscar + Filtrar por Categoría (COMBINACIÓN)**

#### Pasos:
1. Escribir "cable" en el buscador
2. Seleccionar "Electricidad" en categorías
3. Click en "Aplicar Filtros"

#### Resultado esperado:
- ✅ URL: `/products?q=cable&category_id=3`
- ✅ Solo productos que:
  - Contengan "cable" en nombre/SKU/barcode Y
  - Sean de categoría "Electricidad"
- ✅ Badge muestra ambos: "Categoría: Electricidad" y "Búsqueda: cable"
- ✅ Input de búsqueda mantiene "cable"
- ✅ Select mantiene "Electricidad" seleccionado
- ✅ Contador correcto de productos

---

### **8. Limpiar Filtros (Búsqueda + Categoría)**

#### Pasos:
1. Con filtros activos (ejemplo anterior)
2. Click en botón "Limpiar"

#### Resultado esperado:
- ✅ URL: `/products` (sin query params)
- ✅ Se muestran TODOS los productos
- ✅ Input de búsqueda vacío
- ✅ Select en "Todas las categorías"
- ✅ Badge de filtros NO aparece
- ✅ Botón "Limpiar" desaparece

---

### **9. Limpiar Solo con Badge (Alternativa)**

#### Pasos:
1. Aplicar filtros
2. En el badge informativo, click en la "X" (cerrar alerta)

#### Resultado esperado:
- ✅ El badge desaparece
- ✅ Los filtros siguen activos (URL no cambia)
- ✅ Es solo visual - para limpiar filtros reales usar botón "Limpiar"

---

### **10. Category ID Inválido**

#### Pasos:
1. En el navegador, ir manualmente a: `http://localhost:5000/products?category_id=9999`

#### Resultado esperado:
- ✅ Mensaje flash warning: "La categoría seleccionada no existe. Mostrando todos los productos."
- ✅ Se muestran TODOS los productos
- ✅ Select vuelve a "Todas las categorías"
- ✅ No hay error 500
- ✅ La aplicación no se rompe

---

### **11. Category ID No Numérico**

#### Pasos:
1. Ir manualmente a: `http://localhost:5000/products?category_id=abc`

#### Resultado esperado:
- ✅ Mensaje flash warning: "ID de categoría inválido. Mostrando todos los productos."
- ✅ Se muestran TODOS los productos
- ✅ Select en "Todas las categorías"
- ✅ No hay error 500

---

### **12. Persistencia en Navegación**

#### Pasos:
1. Aplicar filtro: Categoría "Construcción"
2. Buscar: "cemento"
3. Click en "Editar" un producto
4. Click en "Volver" (desde el formulario)

#### Resultado esperado:
- ✅ Vuelve a /products (sin filtros)
- ℹ️ **Nota:** Los filtros NO persisten al navegar a otras páginas y volver
- ℹ️ Esto es correcto - los filtros solo se mantienen en la URL actual

---

### **13. Crear Nuevo Producto con Filtros Activos**

#### Pasos:
1. Aplicar filtro: Categoría "Herramientas"
2. Click en botón "Nuevo"
3. Crear un producto de categoría "Herramientas"
4. Click "Crear Producto"

#### Resultado esperado:
- ✅ Producto se crea exitosamente
- ✅ Redirige a /products (sin filtros activos)
- ✅ El nuevo producto aparece en el listado completo
- ℹ️ **Nota:** Si deseas que vuelva con filtros, se requeriría ajustar el redirect, pero no es parte de esta mejora

---

### **14. Columnas e Imágenes (MEJORA 1 No Rota)**

#### Pasos:
1. Aplicar cualquier filtro
2. Observar el listado

#### Resultado esperado:
- ✅ Columna "Imagen" sigue visible
- ✅ Thumbnails se muestran correctamente
- ✅ Placeholder "Sin imagen" para productos sin foto
- ✅ Stock se muestra con badges de colores
- ✅ Botones "Editar" y toggle "Activo" funcionan

---

### **15. Productos Sin Categoría (NULL)**

#### Pasos:
1. Verificar en DB que hay productos con category_id = NULL:
```bash
docker compose exec db psql -U ferreteria -d ferreteria -c "SELECT COUNT(*) FROM product WHERE category_id IS NULL;"
```
2. En /products, sin filtros, verificar que esos productos aparecen
3. Aplicar filtro de cualquier categoría
4. Verificar que esos productos NO aparecen

#### Resultado esperado:
- ✅ Sin filtro: productos NULL aparecen
- ✅ Con filtro: productos NULL NO aparecen
- ✅ SQL WHERE category_id = X excluye NULL correctamente

---

### **16. Performance - Query SQL**

#### Verificación (Opcional):
Si tienes SQLAlchemy echo activado, verificar en logs:

```sql
-- Sin filtro
SELECT * FROM product ORDER BY name

-- Con filtro
SELECT * FROM product WHERE category_id = 1 ORDER BY name

-- Con búsqueda + filtro
SELECT * FROM product 
WHERE category_id = 3 
  AND (LOWER(name) LIKE '%cable%' OR ...)
ORDER BY name
```

#### Resultado esperado:
- ✅ Filtro se aplica a nivel SQL (no en Python)
- ✅ No hay N+1 queries
- ✅ Performance rápida incluso con 100+ productos

---

### **17. Dropdown de Categorías**

#### Pasos:
1. Verificar opciones del select

#### Resultado esperado:
- ✅ Primera opción: "Todas las categorías" (value="")
- ✅ Categorías ordenadas alfabéticamente:
  - Construcción
  - Electricidad
  - Herramientas
  - Jardinería
  - Pintura
  - Plomería
- ✅ Cada opción tiene value=ID de la categoría
- ✅ No hay categorías hardcodeadas (vienen de DB)

---

### **18. UX - Labels e Iconos**

#### Verificación visual:
- ✅ Select tiene label "🔽 Categoría"
- ✅ Input búsqueda tiene label "🔍 Buscar"
- ✅ Botón "Aplicar Filtros" con icono de funnel
- ✅ Botón "Limpiar" con icono X
- ✅ Botón "Nuevo" con icono +
- ✅ Badge informativo con icono ℹ️
- ✅ UI responsive y profesional

---

## 📊 Resumen de Implementación

### ✅ Completado:

**Backend (`catalog.py`):**
- [x] Lectura de `category_id` desde query string
- [x] Query de categorías para dropdown
- [x] Filtro SQL: `WHERE category_id = X`
- [x] Validación de category_id inválido
- [x] Validación de category_id no numérico
- [x] Flash messages informativos
- [x] Combinación con búsqueda existente

**Frontend (`list.html`):**
- [x] Select de categorías con label
- [x] Opción "Todas las categorías" por defecto
- [x] Categorías ordenadas alfabéticamente
- [x] Persistencia de valores seleccionados (q y category_id)
- [x] Badge informativo de filtros activos
- [x] Contador de productos mostrados
- [x] Botón "Aplicar Filtros"
- [x] Botón "Limpiar" condicional
- [x] UI mejorada y responsive

### 🎯 No Rompe Funcionalidades Existentes:
- [x] Búsqueda por texto funciona
- [x] Columna de imágenes (MEJORA 1)
- [x] Thumbnails y placeholders
- [x] Stock con badges
- [x] Toggle active
- [x] Crear/editar productos
- [x] Sin filtros muestra todos (incluyendo NULL)

---

## 🔍 Casos Edge Verificados:

- ✅ category_id = ""  → Muestra todos
- ✅ category_id = 9999  → Warning + muestra todos
- ✅ category_id = "abc"  → Warning + muestra todos
- ✅ q + category_id  → Intersección correcta
- ✅ Productos con category_id NULL manejados correctamente

---

## 🚀 Siguiente Mejora

Una vez validada la MEJORA 2, continuar con:
**MEJORA 3: Productos más vendidos en Ventas (POS)**
