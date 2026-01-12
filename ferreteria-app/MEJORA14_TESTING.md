# 🧪 **MEJORA 14: Datos de Cliente en Presupuestos - Casos de Prueba**

---

## **📋 Resumen de la Mejora**

**Objetivo**: Agregar datos básicos del cliente (nombre y teléfono) a cada presupuesto y permitir buscar presupuestos por cliente, sin implementar un módulo completo de CRM.

**Funcionalidades implementadas**:
- ✅ Columnas `customer_name` (obligatorio) y `customer_phone` (opcional) en tabla `quote`
- ✅ Inputs de cliente en formulario de crear presupuesto (POS)
- ✅ Validación obligatoria de nombre del cliente
- ✅ Búsqueda por número, nombre o teléfono en listado
- ✅ Visualización de datos del cliente en detalle y listado
- ✅ Datos del cliente incluidos en PDF

---

## **🎯 PARTE 1: Crear Presupuesto con Datos de Cliente**

### **Caso 1.1: Guardar Sin Nombre - Bloqueado**
**Objetivo**: Verificar que customer_name es obligatorio.

**Pasos**:
1. Ir a `/sales/new`
2. Agregar productos al carrito
3. En "Datos del Cliente", dejar el nombre vacío
4. Intentar hacer clic en "Guardar como Presupuesto"

**Resultado esperado**:
- ✅ HTML5 validation impide envío (campo required)
- ✅ Si se bypasea: backend valida y muestra flash "El nombre del cliente es obligatorio..."
- ✅ Redirección a `/sales/new`
- ✅ NO se crea presupuesto

---

### **Caso 1.2: Guardar con Nombre - OK**
**Objetivo**: Verificar creación exitosa con nombre del cliente.

**Pasos**:
1. Agregar productos al carrito
2. Ingresar:
   - Nombre: "Juan Pérez"
   - Teléfono: (dejar vacío)
3. Seleccionar método: Efectivo
4. Guardar presupuesto

**Resultado esperado**:
- ✅ Presupuesto creado exitosamente
- ✅ Redirección a `/quotes/<id>`
- ✅ En DB:
  - `customer_name = 'Juan Pérez'`
  - `customer_phone = NULL`
- ✅ Flash message: "Presupuesto creado exitosamente."

**Verificación SQL**:
```sql
SELECT id, quote_number, customer_name, customer_phone
FROM quote
ORDER BY id DESC
LIMIT 1;
```

---

### **Caso 1.3: Guardar con Nombre y Teléfono - OK**
**Objetivo**: Verificar que teléfono opcional se persiste correctamente.

**Pasos**:
1. Agregar productos al carrito
2. Ingresar:
   - Nombre: "María García"
   - Teléfono: "11-5555-1234"
3. Guardar presupuesto

**Resultado esperado**:
- ✅ Presupuesto creado exitosamente
- ✅ En DB:
  - `customer_name = 'María García'`
  - `customer_phone = '11-5555-1234'`

**Verificación SQL**:
```sql
SELECT customer_name, customer_phone
FROM quote
WHERE id = <ultimo_id>;
```

---

### **Caso 1.4: Nombre con Espacios - Trimmed**
**Objetivo**: Verificar que se eliminan espacios al inicio/final.

**Pasos**:
1. Ingresar nombre: "  Carlos López  "
2. Teléfono: "  15-6666-7890  "
3. Guardar

**Resultado esperado**:
- ✅ En DB:
  - `customer_name = 'Carlos López'` (sin espacios extras)
  - `customer_phone = '15-6666-7890'` (sin espacios extras)

---

### **Caso 1.5: Teléfono Vacío = NULL**
**Objetivo**: Verificar que teléfono vacío se guarda como NULL.

**Pasos**:
1. Nombre: "Ana Martínez"
2. Teléfono: "" (vacío o solo espacios)
3. Guardar

**Resultado esperado**:
- ✅ `customer_phone = NULL` (no string vacío)

---

## **🎯 PARTE 2: Búsqueda por Cliente en Listado**

### **Caso 2.1: Búsqueda por Nombre Completo**
**Objetivo**: Verificar búsqueda por nombre exacto.

**Pre-condición**: Existir presupuesto con cliente "Juan Pérez"

**Pasos**:
1. Ir a `/quotes`
2. En campo de búsqueda, ingresar: "Juan Pérez"
3. Filtrar

**Resultado esperado**:
- ✅ Se muestra el presupuesto de Juan Pérez
- ✅ NO se muestran otros presupuestos

---

### **Caso 2.2: Búsqueda por Nombre Parcial**
**Objetivo**: Verificar búsqueda parcial (ILIKE).

**Pre-condición**: Presupuestos con:
- "Juan Pérez"
- "María García"
- "Juana López"

**Pasos**:
1. Buscar: "juan"

**Resultado esperado**:
- ✅ Se muestran:
  - Juan Pérez
  - Juana López
- ✅ NO se muestra María García

---

### **Caso 2.3: Búsqueda por Teléfono Completo**
**Objetivo**: Verificar búsqueda por teléfono.

**Pre-condición**: Presupuesto con teléfono "11-5555-1234"

**Pasos**:
1. Buscar: "11-5555-1234"

**Resultado esperado**:
- ✅ Se muestra el presupuesto con ese teléfono

---

### **Caso 2.4: Búsqueda por Teléfono Parcial**
**Objetivo**: Verificar búsqueda parcial de teléfono.

**Pre-condición**: Presupuestos con:
- "11-5555-1234"
- "11-6666-7890"
- "15-7777-8901"

**Pasos**:
1. Buscar: "11-"

**Resultado esperado**:
- ✅ Se muestran los dos presupuestos con "11-"
- ✅ NO se muestra el "15-"

---

### **Caso 2.5: Búsqueda por Número de Presupuesto (Compatibilidad)**
**Objetivo**: Verificar que búsqueda por número sigue funcionando.

**Pasos**:
1. Copiar un quote_number (ej: PRES-20260112-100000-0001)
2. Buscar por ese número

**Resultado esperado**:
- ✅ Se muestra solo ese presupuesto
- ✅ Búsqueda por número NO afectada

---

### **Caso 2.6: Búsqueda Sin Resultados**
**Objetivo**: Verificar mensaje cuando no hay coincidencias.

**Pasos**:
1. Buscar: "Cliente Inexistente XYZ"

**Resultado esperado**:
- ✅ Tabla vacía o mensaje "No se encontraron presupuestos."

---

### **Caso 2.7: Búsqueda Combinada con Filtro de Estado**
**Objetivo**: Verificar que búsqueda se combina con filtro de estado.

**Pre-condición**:
- Presupuesto DRAFT de "Juan Pérez"
- Presupuesto ACCEPTED de "Juan Pérez"

**Pasos**:
1. Filtrar por Estado: "Aceptado"
2. Buscar: "Juan Pérez"

**Resultado esperado**:
- ✅ Solo se muestra el presupuesto ACCEPTED de Juan Pérez
- ✅ NO se muestra el DRAFT

---

## **🎯 PARTE 3: Visualización en Listado**

### **Caso 3.1: Columna Cliente Visible**
**Objetivo**: Verificar que columna "Cliente" se muestra en tabla.

**Pasos**:
1. Ir a `/quotes`

**Resultado esperado**:
- ✅ Columna "Cliente" visible entre "Número" y "Fecha Emisión"
- ✅ Muestra el nombre del cliente en negrita
- ✅ Si tiene teléfono, se muestra debajo en gris con ícono 📞

---

### **Caso 3.2: Cliente Sin Teléfono**
**Objetivo**: Verificar visualización cuando customer_phone es NULL.

**Pasos**:
1. Ver listado con presupuesto que NO tiene teléfono

**Resultado esperado**:
- ✅ Solo se muestra el nombre
- ✅ NO se muestra línea de teléfono vacía

---

## **🎯 PARTE 4: Visualización en Detalle**

### **Caso 4.1: Detalle Muestra Cliente**
**Objetivo**: Verificar que detalle incluye datos del cliente.

**Pasos**:
1. Ir a `/quotes/<id>` de presupuesto con cliente

**Resultado esperado**:
- ✅ En sección "Información del Presupuesto"
- ✅ Campo "Cliente:" muestra nombre en negrita
- ✅ Si tiene teléfono, se muestra debajo con ícono 📞
- ✅ Ubicado después de "Válido Hasta" y antes de "Método de Pago"

---

### **Caso 4.2: Cliente Sin Teléfono en Detalle**
**Objetivo**: Verificar visualización cuando no hay teléfono.

**Pasos**:
1. Ver detalle de presupuesto sin teléfono

**Resultado esperado**:
- ✅ Solo se muestra el nombre del cliente
- ✅ NO se muestra línea de teléfono vacía

---

## **🎯 PARTE 5: PDF con Datos del Cliente**

### **Caso 5.1: PDF Incluye Cliente**
**Objetivo**: Verificar que PDF muestra datos del cliente.

**Pre-condición**: Presupuesto con:
- Cliente: "Roberto Gómez"
- Teléfono: "11-1234-5678"

**Pasos**:
1. Ir a detalle del presupuesto
2. Descargar PDF

**Resultado esperado**:
- ✅ PDF descarga correctamente
- ✅ En sección de información del presupuesto (parte superior), después del método de pago:
  - **Cliente:** Roberto Gómez
  - **Teléfono:** 11-1234-5678
- ✅ Formato alineado con el resto de la info

---

### **Caso 5.2: PDF Sin Teléfono**
**Objetivo**: Verificar PDF cuando customer_phone es NULL.

**Pasos**:
1. Descargar PDF de presupuesto sin teléfono

**Resultado esperado**:
- ✅ PDF muestra **Cliente:** [Nombre]
- ✅ NO muestra línea de Teléfono vacía

---

### **Caso 5.3: PDF de Presupuesto Viejo (Sin Cliente)**
**Objetivo**: Verificar compatibilidad con presupuestos creados antes de MEJORA 14.

**Pre-condición**: Presupuesto creado antes de aplicar migración (customer_name='')

**Pasos**:
1. Intentar descargar PDF

**Resultado esperado**:
- ✅ PDF genera sin errores
- ✅ Muestra "Cliente:" [vacío o placeholder]
- ✅ O NO muestra sección de cliente si está vacío

**Nota**: Esto solo aplica si hay datos legacy. Nuevos presupuestos siempre tienen customer_name.

---

## **🎯 PARTE 6: Conversión a Venta (Compatibilidad)**

### **Caso 6.1: Convertir Presupuesto con Cliente - OK**
**Objetivo**: Verificar que conversión funciona con customer_name/phone.

**Pasos**:
1. Crear presupuesto con cliente
2. Convertir a venta

**Resultado esperado**:
- ✅ Conversión exitosa
- ✅ Sale creada correctamente
- ✅ Stock descontado
- ✅ Ledger INCOME creado
- ✅ Quote marcado como ACCEPTED
- ✅ customer_name y customer_phone NO se copian a sale (correcto, sale no tiene esos campos)

---

### **Caso 6.2: Venta NO Tiene Datos de Cliente**
**Objetivo**: Confirmar que sale no tiene customer_name/phone.

**Pasos**:
1. Después de convertir presupuesto a venta
2. Verificar tabla sale

**Resultado esperado**:
- ✅ Tabla `sale` NO tiene columnas customer_name ni customer_phone (correcto)
- ✅ Datos de cliente solo existen en quote

**Verificación SQL**:
```sql
\d sale
-- NO debe mostrar customer_name ni customer_phone
```

---

## **🎯 PARTE 7: Validaciones y Edge Cases**

### **Caso 7.1: Nombre Muy Largo**
**Objetivo**: Verificar límite de 255 caracteres.

**Pasos**:
1. Intentar ingresar nombre con 300 caracteres

**Resultado esperado**:
- ✅ HTML maxlength=255 impide ingresar más
- ✅ Si se bypasea: backend trunca o valida

---

### **Caso 7.2: Teléfono Muy Largo**
**Objetivo**: Verificar límite de 50 caracteres.

**Pasos**:
1. Intentar ingresar teléfono con 60 caracteres

**Resultado esperado**:
- ✅ HTML maxlength=50 impide ingresar más

---

### **Caso 7.3: Caracteres Especiales en Nombre**
**Objetivo**: Verificar que acepta acentos, ñ, etc.

**Pasos**:
1. Ingresar nombre: "José María Peña"
2. Guardar presupuesto

**Resultado esperado**:
- ✅ Se guarda correctamente sin errores
- ✅ Se muestra correctamente en listado, detalle y PDF

---

### **Caso 7.4: Búsqueda Case-Insensitive**
**Objetivo**: Verificar que búsqueda no distingue mayúsculas/minúsculas.

**Pre-condición**: Presupuesto de "Juan Pérez"

**Pasos**:
1. Buscar: "juan perez" (minúsculas)
2. Buscar: "JUAN PEREZ" (mayúsculas)
3. Buscar: "JuAn PeReZ" (mixto)

**Resultado esperado**:
- ✅ Las 3 búsquedas encuentran el presupuesto
- ✅ ILIKE funciona correctamente

---

## **🎯 PARTE 8: Migración de Datos**

### **Caso 8.1: Presupuestos Existentes Antes de MEJORA 14**
**Objetivo**: Verificar que presupuestos sin cliente se migran con DEFAULT.

**Pre-condición**: Presupuestos creados antes de aplicar migración

**Resultado esperado**:
- ✅ Migración SQL agrega columnas con DEFAULT ''
- ✅ Presupuestos viejos tienen customer_name='' y customer_phone=NULL
- ✅ Listado los muestra con nombre vacío (aceptable para datos legacy)

**Verificación SQL**:
```sql
SELECT COUNT(*) FROM quote WHERE customer_name = '';
-- Si hay presupuestos legacy, este count > 0
```

**Recomendación**: 
- Para producción, actualizar presupuestos legacy con un script manual si es necesario
- O marcarlos visualmente como "Sin cliente" en UI

---

### **Caso 8.2: Índices Creados Correctamente**
**Objetivo**: Verificar que índices existen para búsqueda eficiente.

**Verificación SQL**:
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'quote'
AND indexname IN ('idx_quote_customer_name', 'idx_quote_customer_phone');
```

**Resultado esperado**:
- ✅ idx_quote_customer_name existe
- ✅ idx_quote_customer_phone existe

---

## **📊 Resumen de Pruebas**

| Categoría | Casos | Críticos |
|-----------|-------|----------|
| **Crear con Cliente** | 5 | ✅ 1.1, 1.2, 1.3 |
| **Búsqueda** | 7 | ✅ 2.1, 2.2, 2.3, 2.5 |
| **Visualización Listado** | 2 | ✅ 3.1 |
| **Visualización Detalle** | 2 | ✅ 4.1 |
| **PDF** | 3 | ✅ 5.1 |
| **Conversión a Venta** | 2 | ✅ 6.1 |
| **Validaciones** | 4 | 7.1, 7.3, 7.4 |
| **Migración** | 2 | ✅ 8.2 |
| **TOTAL** | **27** | **13** |

---

## **✅ Checklist de Aceptación Final**

### **Base de Datos**
- [ ] Columna `customer_name` agregada (NOT NULL)
- [ ] Columna `customer_phone` agregada (nullable)
- [ ] Índices creados correctamente
- [ ] Migración se ejecuta sin errores

### **Modelo**
- [ ] Quote tiene customer_name y customer_phone
- [ ] Validación de customer_name en servicio

### **POS - Crear Presupuesto**
- [ ] Inputs de cliente visibles en carrito
- [ ] customer_name marcado como required
- [ ] customer_phone opcional
- [ ] Validación frontend y backend funciona
- [ ] NO se puede guardar sin nombre
- [ ] Datos se persisten correctamente

### **Búsqueda**
- [ ] Búsqueda por nombre funciona
- [ ] Búsqueda por teléfono funciona
- [ ] Búsqueda por número sigue funcionando
- [ ] Case-insensitive (ILIKE)
- [ ] Búsqueda parcial funciona
- [ ] Combinable con filtro de estado

### **Visualización**
- [ ] Listado muestra columna Cliente
- [ ] Detalle muestra datos del cliente
- [ ] Teléfono solo se muestra si existe
- [ ] Formato consistente

### **PDF**
- [ ] PDF incluye nombre del cliente
- [ ] PDF incluye teléfono (si existe)
- [ ] Formato profesional
- [ ] Compatible con presupuestos sin teléfono

### **Compatibilidad**
- [ ] Conversión a venta funciona sin cambios
- [ ] NO se copian datos a sale
- [ ] Presupuestos legacy migran OK
- [ ] NO rompe funcionalidad existente

---

## **🚀 Flujo de Prueba Manual Completo**

### **Happy Path: Crear Presupuesto con Cliente**
```
1. Login
2. /sales/new
3. Agregar 2-3 productos
4. En "Datos del Cliente":
   - Nombre: "Patricia Rodríguez"
   - Teléfono: "11-9999-0000"
5. Método: Transferencia
6. Click "Guardar como Presupuesto"
7. Verificar redirección a detalle
8. Verificar nombre y teléfono visibles
9. Descargar PDF → verificar datos cliente
10. Volver a /quotes
11. Buscar "Patricia" → verificar aparece
12. Buscar "11-9999" → verificar aparece
```

### **Test: Búsqueda Múltiple**
```
1. Crear 3 presupuestos con nombres diferentes
2. Buscar por nombre parcial
3. Buscar por teléfono
4. Buscar por número de presupuesto
5. Verificar que cada búsqueda devuelve correctos resultados
```

### **Test: Conversión con Cliente**
```
1. Crear presupuesto con cliente "Luis Fernández"
2. Convertir a venta
3. Verificar quote.status = ACCEPTED
4. Verificar sale creada sin customer_name (correcto)
5. Detalle del quote sigue mostrando "Luis Fernández"
```

---

**✅ FIN DE TESTING MEJORA 14**
