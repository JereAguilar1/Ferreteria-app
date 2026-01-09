# MEJORA 1 - Testing: Fotos por Producto

## ✅ Checklist de Pruebas

### **1. Preparación**
- [ ] Aplicación corriendo en http://localhost:5000
- [ ] Base de datos con productos existentes
- [ ] Tener imágenes de prueba listas (JPG, PNG)

---

### **2. Crear Producto CON Imagen**

#### Pasos:
1. Ir a: http://localhost:5000/products
2. Click en "Nuevo Producto"
3. Llenar formulario:
   - Nombre: "Martillo con Foto"
   - SKU: "MART-FOTO-001"
   - Categoría: Herramientas
   - UOM: Unidad
   - Precio: $1500.00
   - **Seleccionar una imagen JPG o PNG**
4. Click "Crear Producto"

#### Resultado esperado:
- ✅ Mensaje "Producto creado exitosamente"
- ✅ En el listado, el producto muestra el thumbnail de la imagen
- ✅ Imagen se ve correctamente (no distorsionada)
- ✅ Tamaño del thumbnail: 60x60px

---

### **3. Crear Producto SIN Imagen**

#### Pasos:
1. Ir a: http://localhost:5000/products/new
2. Llenar formulario:
   - Nombre: "Destornillador sin Foto"
   - SKU: "DEST-SIN-001"
   - Categoría: Herramientas
   - UOM: Unidad
   - Precio: $450.00
   - **NO seleccionar imagen**
3. Click "Crear Producto"

#### Resultado esperado:
- ✅ Mensaje "Producto creado exitosamente"
- ✅ En el listado, el producto muestra el placeholder "Sin imagen"
- ✅ Placeholder es un SVG gris con texto "Sin imagen"

---

### **4. Editar Producto - Agregar Imagen**

#### Pasos:
1. En el listado, buscar "Destornillador sin Foto"
2. Click en "Editar"
3. **Seleccionar una imagen**
4. Click "Guardar Cambios"

#### Resultado esperado:
- ✅ Mensaje "Producto actualizado exitosamente"
- ✅ En el listado, ahora muestra la imagen (no el placeholder)
- ✅ En edición, muestra "Imagen actual" con preview

---

### **5. Editar Producto - Reemplazar Imagen**

#### Pasos:
1. Editar el "Destornillador sin Foto" (que ahora tiene imagen)
2. En la sección de imagen, debe mostrar:
   - Preview de imagen actual
   - Texto "Imagen actual"
   - Input para nueva imagen con texto "Si selecciona una nueva imagen, reemplazará la actual"
3. **Seleccionar una imagen DIFERENTE**
4. Click "Guardar Cambios"

#### Resultado esperado:
- ✅ Mensaje "Producto actualizado exitosamente"
- ✅ En el listado, muestra la NUEVA imagen (no la anterior)
- ✅ La imagen anterior fue eliminada del servidor

---

### **6. Validación - Formato Inválido**

#### Pasos:
1. Crear o editar un producto
2. Intentar subir un archivo .GIF o .BMP

#### Resultado esperado:
- ✅ Mensaje de error: "Formato de imagen no permitido. Use JPG, JPEG o PNG"
- ✅ El producto NO se crea/actualiza
- ✅ El archivo NO se guarda en el servidor

---

### **7. Validación - Archivo Muy Grande**

#### Pasos:
1. Crear o editar un producto
2. Intentar subir una imagen > 2MB

#### Resultado esperado:
- ✅ Mensaje de error: "La imagen es demasiado grande. Máximo 2MB"
- ✅ El producto NO se crea/actualiza
- ✅ El archivo NO se guarda en el servidor

---

### **8. Verificación de Archivos en Servidor**

#### Pasos:
1. Con Docker corriendo, ejecutar:
```bash
docker compose exec web ls -la /app/app/static/uploads/products/
```

#### Resultado esperado:
- ✅ Se ven archivos con nombres tipo: `1704835200_imagen.jpg`
- ✅ Los nombres tienen timestamp para evitar colisiones
- ✅ Solo existen las imágenes de productos actuales (las reemplazadas fueron eliminadas)

---

### **9. Listado de Productos - Visual**

#### Pasos:
1. Ir a: http://localhost:5000/products
2. Observar la tabla

#### Resultado esperado:
- ✅ Columna "Imagen" visible y bien alineada
- ✅ Thumbnails de 60x60px
- ✅ Imágenes con `object-fit: cover` (no se estiran)
- ✅ Productos sin imagen muestran placeholder SVG
- ✅ Tabla se ve profesional y ordenada

---

### **10. Búsqueda - Funcionalidad Existente**

#### Pasos:
1. En /products, usar barra de búsqueda
2. Buscar "Martillo"

#### Resultado esperado:
- ✅ Búsqueda sigue funcionando correctamente
- ✅ Imágenes se muestran en resultados filtrados
- ✅ No hay errores

---

## 📊 Resumen de Implementación

### ✅ Completado:
- [x] Columna `image_path` agregada a tabla `product`
- [x] Directorio `static/uploads/products/` creado
- [x] Placeholder SVG "Sin imagen" creado
- [x] Modelo `Product` actualizado
- [x] Blueprint `catalog.py` con funciones de upload
- [x] Validaciones: formato (JPG/JPEG/PNG) y tamaño (2MB)
- [x] Formulario actualizado (enctype multipart)
- [x] Listado con columna de thumbnails
- [x] Preview en edición
- [x] Eliminación de imagen anterior al reemplazar

### 🎯 No Rompe Funcionalidades Existentes:
- [x] Crear producto sin imagen funciona
- [x] Editar producto sin tocar imagen funciona
- [x] Búsqueda funciona
- [x] Listado funciona
- [x] Stock se muestra correctamente

---

## 🚀 Siguiente Mejora

Una vez validada la MEJORA 1, continuar con:
**MEJORA 2: Filtro por categoría en listado de productos**
