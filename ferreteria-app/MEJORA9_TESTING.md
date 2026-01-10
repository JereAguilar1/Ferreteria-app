# 🧪 MEJORA 9 - Testing: Administración de Categorías y UOM

## 📋 **Objetivo**

Validar que el sistema permite administrar Categorías y Unidades de Medida desde la UI sin depender de scripts de seed.

---

## ✅ **Testing de Unidades de Medida (UOM)**

### **Test 1.1: Acceder a Lista de UOM (vacía)**

**Pasos:**
1. Login en la aplicación
2. Click en "Configuración" → "Unidades de Medida"

**Resultado esperado:**
- ✅ URL: `/settings/uoms`
- ✅ Se muestra alert: "No hay unidades de medida registradas"
- ✅ Botón "Nueva Unidad" visible
- ✅ Link "Crear primera unidad de medida" funcionalsql
"Unidad" (ud) para productos individuales
- "Metro" (m) para longitudes
- "Kilogramo" (kg) para peso
- "Litro" (l) para volumen

---

### **Test 1.2: Crear Primera UOM**

**Pasos:**
1. Desde lista vacía, click "Nueva Unidad" o link
2. Ingresar:
   - Nombre: `Unidad`
   - Símbolo: `ud`
3. Click "Crear"

**Resultado esperado:**
- ✅ Flash message verde: "Unidad de medida "Unidad" creada exitosamente"
- ✅ Redirige a `/settings/uoms`
- ✅ Se muestra tabla con 1 UOM
- ✅ Columna "Productos": muestra `0`

---

### **Test 1.3: Crear Más UOM**

**Pasos:**
Crear las siguientes UOM:

| Nombre | Símbolo |
|--------|---------|
| Metro | m |
| Kilogramo | kg |
| Litro | l |
| Caja | caja |

**Resultado esperado:**
- ✅ 5 UOM en total
- ✅ Ordenadas alfabéticamente por nombre

---

### **Test 1.4: Validación - Nombre Duplicado**

**Pasos:**
1. Click "Nueva Unidad"
2. Ingresar:
   - Nombre: `Unidad` (ya existe)
   - Símbolo: `u`
3. Click "Crear"

**Resultado esperado:**
- ✅ Flash message rojo: "Ya existe una unidad de medida con el nombre "Unidad""
- ✅ Queda en el formulario
- ✅ NO se crea la UOM duplicada

---

### **Test 1.5: Validación - Símbolo Duplicado**

**Pasos:**
1. Click "Nueva Unidad"
2. Ingresar:
   - Nombre: `Unidades`
   - Símbolo: `ud` (ya existe)
3. Click "Crear"

**Resultado esperado:**
- ✅ Flash message rojo: "Ya existe una unidad de medida con el símbolo "ud""
- ✅ NO se crea la UOM duplicada

---

### **Test 1.6: Validación - Campos Vacíos**

**Pasos:**
1. Click "Nueva Unidad"
2. Dejar nombre o símbolo vacío
3. Click "Crear"

**Resultado esperado:**
- ✅ HTML5 validation previene submit
- ✅ O backend muestra: "El nombre es obligatorio" / "El símbolo es obligatorio"

---

### **Test 1.7: Editar UOM**

**Pasos:**
1. En lista de UOM, click ícono "Editar" (lápiz) en "Unidad"
2. Cambiar nombre a: `Unidad Individual`
3. Cambiar símbolo a: `uni`
4. Click "Actualizar"

**Resultado esperado:**
- ✅ Flash message verde: "Unidad de medida "Unidad Individual" actualizada exitosamente"
- ✅ Redirige a lista
- ✅ Se muestra con nuevo nombre y símbolo

---

### **Test 1.8: Eliminar UOM Sin Productos**

**Pasos:**
1. En lista de UOM, identificar una sin productos asociados
2. Click botón "Eliminar" (ícono basura)
3. Confirmar en el diálogo

**Resultado esperado:**
- ✅ Alert JavaScript: "¿Está seguro de eliminar la unidad "..."?"
- ✅ Al confirmar: Flash message verde: "Unidad de medida "..." eliminada exitosamente"
- ✅ UOM desaparece de la lista

---

### **Test 1.9: Intentar Eliminar UOM Con Productos**

**Prerequisito:** Crear al menos un producto con una UOM (ej: "Metro")

**Pasos:**
1. En lista de UOM, click "Eliminar" en UOM con productos
2. Confirmar

**Resultado esperado:**
- ✅ Flash message rojo: "No se puede eliminar la unidad "Metro" porque está asociada a N producto(s)"
- ✅ UOM NO se elimina
- ✅ Botón de eliminar debe estar deshabilitado (gris) si product_count > 0

---

### **Test 1.10: Contador de Productos**

**Pasos:**
1. Ver columna "Productos" en lista de UOM
2. Crear un producto con UOM "Metro"
3. Volver a lista de UOM

**Resultado esperado:**
- ✅ Contador aumenta de `0` a `1` para "Metro"
- ✅ Se muestra como badge azul
- ✅ Botón eliminar se deshabilita

---

## ✅ **Testing de Categorías**

### **Test 2.1: Acceder a Lista de Categorías (vacía)**

**Pasos:**
1. Click en "Configuración" → "Categorías"

**Resultado esperado:**
- ✅ URL: `/settings/categories`
- ✅ Se muestra alert: "No hay categorías registradas"
- ✅ Botón "Nueva Categoría" visible

---

### **Test 2.2: Crear Primera Categoría**

**Pasos:**
1. Click "Nueva Categoría"
2. Ingresar nombre: `Herramientas Manuales`
3. Click "Crear"

**Resultado esperado:**
- ✅ Flash message verde: "Categoría "Herramientas Manuales" creada exitosamente"
- ✅ Redirige a `/settings/categories`
- ✅ Se muestra tabla con 1 categoría
- ✅ Columna "Productos": muestra `0`

---

### **Test 2.3: Crear Más Categorías**

**Pasos:**
Crear las siguientes categorías:
- Herramientas Eléctricas
- Pintura y Accesorios
- Electricidad
- Plomería

**Resultado esperado:**
- ✅ 5 categorías en total
- ✅ Ordenadas alfabéticamente

---

### **Test 2.4: Validación - Nombre Duplicado (Case-Insensitive)**

**Pasos:**
1. Click "Nueva Categoría"
2. Ingresar: `herramientas manuales` (minúsculas)
3. Click "Crear"

**Resultado esperado:**
- ✅ Flash message rojo: "Ya existe una categoría con el nombre "herramientas manuales""
- ✅ NO se crea duplicada

---

### **Test 2.5: Validación - Máximo 120 Caracteres**

**Pasos:**
1. Click "Nueva Categoría"
2. Ingresar nombre de 121+ caracteres
3. Click "Crear"

**Resultado esperado:**
- ✅ HTML5 validation previene submit (maxlength="120")
- ✅ O backend muestra error

---

### **Test 2.6: Editar Categoría**

**Pasos:**
1. Click "Editar" en "Herramientas Manuales"
2. Cambiar nombre a: `Herramientas de Mano`
3. Click "Actualizar"

**Resultado esperado:**
- ✅ Flash message verde: "Categoría "Herramientas de Mano" actualizada exitosamente"
- ✅ Se muestra con nuevo nombre

---

### **Test 2.7: Eliminar Categoría Sin Productos**

**Pasos:**
1. Click "Eliminar" en categoría sin productos
2. Confirmar

**Resultado esperado:**
- ✅ Alert JavaScript de confirmación
- ✅ Flash message verde: "Categoría "..." eliminada exitosamente"
- ✅ Desaparece de la lista

---

### **Test 2.8: Intentar Eliminar Categoría Con Productos**

**Prerequisito:** Crear producto con categoría "Electricidad"

**Pasos:**
1. Click "Eliminar" en "Electricidad"
2. Confirmar

**Resultado esperado:**
- ✅ Flash message rojo: "No se puede eliminar la categoría "Electricidad" porque está asociada a N producto(s)"
- ✅ Categoría NO se elimina
- ✅ Botón debe estar deshabilitado si product_count > 0

---

## ✅ **Testing de Integración con Productos**

### **Test 3.1: Crear Producto SIN UOM Existentes**

**Prerequisito:** NO tener UOM en el sistema (o eliminarlas todas)

**Pasos:**
1. Ir a "Productos" → "Nuevo Producto"

**Resultado esperado:**
- ✅ Redirige automáticamente a `/settings/uoms`
- ✅ Flash message amarillo: "No hay unidades de medida registradas. Debe crear al menos una..."
- ✅ NO permite acceder al formulario de producto

---

### **Test 3.2: Crear Producto CON UOM**

**Prerequisito:** Tener al menos 1 UOM

**Pasos:**
1. Ir a "Productos" → "Nuevo Producto"
2. Select de "Unidad de Medida" debe tener opciones
3. Completar formulario y crear producto

**Resultado esperado:**
- ✅ Formulario se muestra correctamente
- ✅ Select UOM tiene opciones
- ✅ Producto se crea exitosamente

---

### **Test 3.3: Alert en Formulario si NO Hay UOM**

**Prerequisito:** Acceder directamente a URL `/products/new` sin UOM

**Pasos:**
1. En navegador, ir a: `http://localhost:5000/products/new`

**Resultado esperado:**
- ✅ Backend redirige a `/settings/uoms` (ver Test 3.1)
- ✅ O template muestra alert: "No hay unidades de medida registradas..."
- ✅ Select UOM deshabilitado
- ✅ Botón "Crear Producto" deshabilitado

---

### **Test 3.4: Categoría Opcional**

**Pasos:**
1. Crear producto sin seleccionar categoría (dejar "Sin categoría")
2. Guardar

**Resultado esperado:**
- ✅ Producto se crea exitosamente
- ✅ `category_id` queda NULL en DB
- ✅ En lista de productos muestra "-" o "Sin categoría"

---

### **Test 3.5: Categoría Obligatoria (si así lo defines)**

**Si decides hacer categoría obligatoria:**

**Pasos:**
1. Intentar crear producto sin categoría

**Resultado esperado:**
- ✅ Validation error: "La categoría es requerida"
- ✅ O si no hay categorías: redirigir a `/settings/categories`

---

## ✅ **Testing de Navegación**

### **Test 4.1: Menú Configuración**

**Pasos:**
1. Verificar navbar
2. Click dropdown "Configuración"

**Resultado esperado:**
- ✅ Dropdown "Configuración" visible (con ícono engranaje)
- ✅ Opciones:
  - Categorías
  - Unidades de Medida

---

### **Test 4.2: Breadcrumbs**

**Pasos:**
1. Ir a "Unidades de Medida" → "Nueva Unidad"
2. Verificar breadcrumb

**Resultado esperado:**
- ✅ Breadcrumb: `Unidades de Medida > Nueva`
- ✅ Link "Unidades de Medida" funcional
- ✅ Similar para Categorías

---

### **Test 4.3: Botón Cancelar**

**Pasos:**
1. En formulario de UOM o Categoría, click "Cancelar"

**Resultado esperado:**
- ✅ Redirige a lista correspondiente
- ✅ Sin guardar cambios

---

## ✅ **Testing de Restricciones de Integridad**

### **Test 5.1: Eliminar Producto Libera UOM para Eliminar**

**Pasos:**
1. Crear UOM "Test"
2. Crear producto con UOM "Test"
3. Verificar que "Test" NO puede eliminarse
4. Eliminar el producto
5. Intentar eliminar "Test"

**Resultado esperado:**
- ✅ Después de eliminar producto, UOM puede eliminarse
- ✅ Contador de productos vuelve a `0`

---

### **Test 5.2: Cambiar UOM de Producto Libera UOM Anterior**

**Pasos:**
1. Producto A usa UOM "Metro"
2. Editar Producto A, cambiar UOM a "Unidad"
3. Si "Metro" no tiene más productos, debería poder eliminarse

**Resultado esperado:**
- ✅ Contador de "Metro" disminuye
- ✅ Botón eliminar de "Metro" se habilita si contador = 0

---

### **Test 5.3: Similar para Categorías**

**Pasos:**
1. Producto B tiene categoría "Pintura"
2. Editar Producto B, cambiar a "Electricidad"
3. Si "Pintura" no tiene más productos, debería poder eliminarse

**Resultado esperado:**
- ✅ Contador actualizado
- ✅ Botón eliminar habilitado

---

## ✅ **Testing de Seed (Opcional)**

### **Test 6.1: Seed Sigue Funcionando**

**Pasos:**
1. Ejecutar `python seed_initial_data.py`

**Resultado esperado:**
- ✅ Script ejecuta sin errores
- ✅ Si ya existen UOM/categorías con mismo nombre, maneja duplicados (INSERT ... ON CONFLICT DO NOTHING)

---

### **Test 6.2: Sistema Funciona Sin Seed**

**Pasos:**
1. Base de datos vacía (sin UOM ni categorías)
2. Login
3. Crear todo desde UI

**Resultado esperado:**
- ✅ Sistema funcional
- ✅ No muestra errores de "debe ejecutar seed"

---

## 📊 **Resumen de Validaciones**

### **UOM:**
- [x] Nombre requerido (máx 80 chars)
- [x] Símbolo requerido (máx 16 chars)
- [x] Nombre único (case-insensitive)
- [x] Símbolo único (case-insensitive)
- [x] NO eliminar si tiene productos
- [x] Contador de productos correcto

### **Categorías:**
- [x] Nombre requerido (máx 120 chars)
- [x] Nombre único (case-insensitive)
- [x] NO eliminar si tiene productos
- [x] Contador de productos correcto

### **Integración:**
- [x] Producto requiere UOM (obligatorio)
- [x] Categoría opcional para producto
- [x] Redirige a settings si no hay UOM
- [x] Alert en formulario si no hay UOM
- [x] Submit deshabilitado si no hay UOM

---

## 🎯 **Checklist Final**

| # | Test | Estado |
|---|------|--------|
| 1.1 | Lista UOM vacía | ⬜ |
| 1.2 | Crear primera UOM | ⬜ |
| 1.3 | Crear más UOM | ⬜ |
| 1.4 | Validar nombre duplicado | ⬜ |
| 1.5 | Validar símbolo duplicado | ⬜ |
| 1.6 | Validar campos vacíos | ⬜ |
| 1.7 | Editar UOM | ⬜ |
| 1.8 | Eliminar UOM sin productos | ⬜ |
| 1.9 | Bloquear eliminar UOM con productos | ⬜ |
| 1.10 | Contador de productos | ⬜ |
| 2.1 | Lista categorías vacía | ⬜ |
| 2.2 | Crear primera categoría | ⬜ |
| 2.3 | Crear más categorías | ⬜ |
| 2.4 | Validar duplicado case-insensitive | ⬜ |
| 2.5 | Validar máximo caracteres | ⬜ |
| 2.6 | Editar categoría | ⬜ |
| 2.7 | Eliminar categoría sin productos | ⬜ |
| 2.8 | Bloquear eliminar categoría con productos | ⬜ |
| 3.1 | Crear producto sin UOM → redirige | ⬜ |
| 3.2 | Crear producto con UOM → funciona | ⬜ |
| 3.3 | Alert en formulario sin UOM | ⬜ |
| 3.4 | Categoría opcional funciona | ⬜ |
| 4.1 | Menú Configuración | ⬜ |
| 4.2 | Breadcrumbs | ⬜ |
| 4.3 | Botón Cancelar | ⬜ |
| 5.1 | Eliminar producto libera UOM | ⬜ |
| 5.2 | Cambiar UOM libera anterior | ⬜ |
| 5.3 | Cambiar categoría libera anterior | ⬜ |

---

**Última actualización:** Enero 2026  
**Autor:** Sistema Ferretería - MEJORA 9
