# FASE 1: Testing - Módulo de Productos + Stock

## ✅ Estado: COMPLETADA

### Comandos para ejecutar

#### 1. Asegurarse de que PostgreSQL esté corriendo

```powershell
cd C:\jere\Ferreteria\Ferreteria-db
docker ps
```

hola hola hola

Si no está corriendo:

```powershell
docker compose up -d
```

#### 2. Inicializar datos base (UOM y Categorías)

```powershell
cd C:\jere\Ferreteria\ferreteria-app
python seed_initial_data.py
```

Resultado esperado:
```
UOM table already has 8 records. Skipping.
Category table already has 6 records. Skipping.
[SUCCESS] Seed data completed successfully!
```

#### 3. Crear productos de prueba (opcional)

```powershell
python create_test_products_v2.py
```

Esto crea 6 productos de ejemplo, incluyendo 2 sin stock.

#### 4. Ejecutar la aplicación Flask

```powershell
python app.py
```

La aplicación estará disponible en: **http://127.0.0.1:5000**

---

## 🧪 Pruebas Manuales

### Test 1: Ver listado de productos

1. Navegar a: http://127.0.0.1:5000/products
2. Verificar que se muestran todos los productos
3. **Verificación**: Productos sin stock (Destornillador Phillips y Tubo PVC) deben aparecer con:
   - Fila gris (`out-of-stock` class)
   - Badge "Sin stock"
   - Stock con badge rojo mostrando "0"

### Test 2: Búsqueda de productos

#### Por nombre:
1. En el campo de búsqueda escribir: `martillo`
2. Click en "Buscar"
3. **Verificación**: Debe mostrar solo "Martillo de Goma"

#### Por SKU:
1. En el campo de búsqueda escribir: `CEM-004`
2. Click en "Buscar"
3. **Verificación**: Debe mostrar solo "Cemento Gris"

#### Por Barcode:
1. En el campo de búsqueda escribir: `7501234567892`
2. Click en "Buscar"
3. **Verificación**: Debe mostrar solo "Pintura Vinilica Blanca"

#### Búsqueda sin resultados:
1. En el campo de búsqueda escribir: `producto inexistente`
2. Click en "Buscar"
3. **Verificación**: Debe mostrar mensaje "No se encontraron productos"

### Test 3: Crear nuevo producto

1. Click en "Nuevo Producto"
2. Completar formulario:
   - **Nombre**: `Taladro Eléctrico` (requerido)
   - **SKU**: `TAL-007` (opcional pero debe ser único)
   - **Código de Barras**: `7501234567894` (opcional pero debe ser único)
   - **Categoría**: Seleccionar "Herramientas"
   - **Unidad de Medida**: Seleccionar "Unidad (UN)" (requerido)
   - **Precio de Venta**: `1250.00` (requerido, debe ser >= 0)
   - **Estado**: Dejar marcado "Producto activo"
3. Click en "Crear Producto"
4. **Verificación**: 
   - Mensaje verde: "Producto "Taladro Eléctrico" creado exitosamente"
   - Redirige a listado
   - Nuevo producto aparece en la lista con Stock = 0

### Test 4: Editar producto existente

1. En el listado, click en ícono de lápiz (editar) del producto "Martillo de Goma"
2. Modificar:
   - **Precio de Venta**: Cambiar a `175.00`
3. Click en "Guardar Cambios"
4. **Verificación**:
   - Mensaje verde: "Producto "Martillo de Goma" actualizado exitosamente"
   - En el listado, el precio aparece actualizado

### Test 5: Validación de SKU único

1. Click en "Nuevo Producto"
2. Completar formulario con:
   - **Nombre**: `Producto Test`
   - **SKU**: `MART-001` (ya existe)
   - **UOM**: Cualquiera
   - **Precio**: 100
3. Click en "Crear Producto"
4. **Verificación**:
   - Mensaje rojo: "El SKU "MART-001" ya está en uso. Por favor, use otro SKU."
   - El formulario permanece abierto con los datos ingresados

### Test 6: Validación de Barcode único

1. Intentar crear producto con barcode `7501234567890` (ya existe)
2. **Verificación**: Mensaje de error similar al SKU

### Test 7: Validación de campos requeridos

1. Click en "Nuevo Producto"
2. Intentar crear dejando el nombre vacío
3. **Verificación**: Error de validación del navegador (HTML5 required)
4. Intentar sin seleccionar UOM
5. **Verificación**: Error de validación

### Test 8: Validación de precio negativo

1. Intentar crear producto con precio `-50`
2. **Verificación**: Error "El precio de venta debe ser mayor o igual a 0"

### Test 9: Activar/Desactivar producto

1. En el listado, click en ícono de toggle del producto "Clavos de 3 pulgadas"
2. Confirmar en el diálogo
3. **Verificación**:
   - Mensaje: "Producto "Clavos de 3 pulgadas" desactivado exitosamente"
   - Badge cambia de "Activo" (verde) a "Inactivo" (gris)
4. Click de nuevo para reactivar
5. **Verificación**: Vuelve a "Activo"

### Test 10: Producto sin categoría

1. Ver producto "Cemento Gris" en el listado
2. **Verificación**: En la columna Categoría debe mostrar "-"

### Test 11: Mostrar stock actual en formulario de edición

1. Editar cualquier producto existente
2. **Verificación**: 
   - Debe mostrar un alert azul con "Stock actual: X.XX UN"
   - Debe incluir el mensaje "El stock se actualiza automáticamente con las ventas y compras"

---

## 📊 Datos de Prueba Creados

| ID | Nombre | SKU | Barcode | UOM | Categoría | Precio | Stock | Estado |
|----|--------|-----|---------|-----|-----------|--------|-------|--------|
| 3 | Martillo de Goma | MART-001 | 7501234567890 | UN | Herramientas | $150.00 | 15 | ✓ |
| 4 | Destornillador Phillips | DEST-002 | 7501234567891 | UN | Herramientas | $85.50 | **0** | ✓ |
| 5 | Pintura Vinilica Blanca | PINT-003 | 7501234567892 | L | Pintura | $320.00 | 25 | ✓ |
| 6 | Cemento Gris | CEM-004 | - | KG | - | $185.00 | 500 | ✓ |
| 7 | Tubo PVC 1/2 pulgada | PVC-005 | 7501234567893 | M | Plomeria | $45.00 | **0** | ✓ |
| 8 | Clavos de 3 pulgadas | CLAV-006 | - | KG | Herramientas | $95.00 | 8 | ✓ |

**Nota**: Los productos con stock = 0 deben verse con fila gris y badge "Sin stock"

---

## 🔧 Funcionalidades Implementadas

### ✅ Modelos SQLAlchemy
- `UOM` (Unidad de Medida)
- `Category` (Categoría)
- `Product` (Producto)
- `ProductStock` (Stock 1:1 con Product)

### ✅ Blueprint Catalog
- `GET /products` - Listado con stock y búsqueda
- `GET /products/new` - Formulario de creación
- `POST /products/new` - Crear producto
- `GET /products/<id>/edit` - Formulario de edición
- `POST /products/<id>/edit` - Actualizar producto
- `POST /products/<id>/toggle-active` - Activar/desactivar

### ✅ Validaciones Server-Side
- Nombre requerido
- UOM requerido y existente
- Precio >= 0
- SKU único (mensaje claro si duplicado)
- Barcode único (mensaje claro si duplicado)

### ✅ UI Features
- Bootstrap 5 responsive
- Flash messages con auto-dismiss
- Búsqueda por nombre/SKU/barcode (case-insensitive)
- Productos sin stock en gris con badge
- Badges de colores para stock (rojo=0, amarillo<10, verde>=10)
- Iconos Bootstrap Icons
- Formularios con validación HTML5

### ✅ Reglas de Negocio
- Stock viene de `product_stock.on_hand_qty` (LEFT JOIN)
- Si no hay stock → fila gris + badge "Sin stock"
- Producto nunca se elimina (solo se desactiva)
- Stock se crea automáticamente por trigger de BD con valor 0

---

## 🎯 Criterios de Aceptación (TODOS CUMPLIDOS)

- [x] Navego a /products y veo lista con stock
- [x] Productos sin stock aparecen en gris con badge
- [x] Puedo crear producto con UOM existente
- [x] Búsqueda q= filtra por nombre/SKU/barcode
- [x] Errores de SKU/barcode duplicado muestran mensaje claro
- [x] Puedo editar productos existentes
- [x] Validaciones funcionan correctamente
- [x] No se permite crear producto sin UOM disponibles
- [x] UI es usable y clara

---

## 📝 Notas Técnicas

1. **Trigger automático**: La base de datos tiene un trigger que crea automáticamente un registro en `product_stock` cuando se inserta un producto, con `on_hand_qty = 0`.

2. **No usar Alembic**: Los modelos solo mapean tablas existentes, no se crean migraciones.

3. **Session management**: Se usa `scoped_session` de SQLAlchemy con `teardown_appcontext` para cerrar sesiones automáticamente.

4. **HTMX**: Está incluido en base.html pero no se usa en Fase 1 (se usará en Fase 2 para el carrito de ventas).

---

## 🚀 Siguiente Fase

**FASE 2**: Nueva venta (carrito) + confirmar venta (transacción + movimientos + ledger)

