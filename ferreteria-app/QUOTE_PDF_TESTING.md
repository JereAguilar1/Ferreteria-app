# 🧪 **Presupuestos en PDF - Casos de Prueba**

---

## **📋 Resumen de la Funcionalidad**

**Objetivo**: Permitir generar presupuestos en formato PDF desde el carrito de ventas (POS) sin crear ventas, descontar stock ni registrar movimientos financieros.

**Características implementadas**:
- ✅ Endpoint `/sales/quote.pdf` para generar PDF
- ✅ Servicio `quote_service.py` con ReportLab
- ✅ Botón "Generar Presupuesto (PDF)" en carrito
- ✅ Configuración del negocio (`BUSINESS_NAME`, `BUSINESS_ADDRESS`, etc.)
- ✅ PDF con formato profesional y información detallada
- ✅ Validación: carrito vacío no permite generar PDF

---

## **🎯 PARTE 1: Generación de PDF - Casos Básicos**

### **Caso 1.1: Carrito Vacío - Botón No Visible**
**Objetivo**: Verificar que el botón no aparece cuando el carrito está vacío.

**Pasos**:
1. Ir a `/sales/new`
2. No agregar ningún producto al carrito

**Resultado esperado**:
- ✅ El botón "Generar Presupuesto (PDF)" NO es visible
- ✅ Solo se muestra el mensaje "El carrito está vacío"

---

### **Caso 1.2: Carrito Vacío - Endpoint Protegido**
**Objetivo**: Verificar que el endpoint rechace solicitudes con carrito vacío.

**Pasos**:
1. Vaciar el carrito completamente
2. Intentar acceder directamente a `/sales/quote.pdf`

**Resultado esperado**:
- ✅ Flash message: "El carrito está vacío. Agregue productos para generar un presupuesto."
- ✅ Redirección a `/sales/new`
- ✅ NO se genera PDF
- ✅ NO se crea registro en DB

---

### **Caso 1.3: Generar PDF con 1 Producto**
**Objetivo**: Verificar generación básica de PDF con un solo producto.

**Pasos**:
1. Ir a `/sales/new`
2. Agregar 1 producto al carrito (ej: 5 unidades de Tornillo)
3. Hacer clic en "Generar Presupuesto (PDF)"

**Resultado esperado**:
- ✅ Se descarga un archivo PDF
- ✅ Nombre de archivo: `presupuesto_YYYYMMDD_HHMMSS.pdf`
- ✅ El PDF contiene:
  - Título "PRESUPUESTO"
  - Número de presupuesto: `PRES-YYYYMMDD-HHMMSS`
  - Fecha actual en formato DD/MM/YYYY
  - Tabla con 1 fila de producto
  - Columnas: Producto | Unidad | Cantidad | Precio Unit. | Subtotal
  - Total correcto
  - Texto legal con validez (7 días por defecto)

**Verificación**:
- Abrir el PDF y confirmar que el total = `qty * precio`
- Verificar que NO se creó registro en `sale`
- Verificar que NO se creó registro en `stock_move`
- Verificar que NO se creó registro en `finance_ledger`

---

### **Caso 1.4: Generar PDF con Múltiples Productos**
**Objetivo**: Verificar generación de PDF con varios productos.

**Pasos**:
1. Agregar 3-5 productos diferentes al carrito
2. Cada producto con cantidades diferentes (algunos enteros, algunos con decimales)
3. Hacer clic en "Generar Presupuesto (PDF)"

**Resultado esperado**:
- ✅ Se descarga PDF correctamente
- ✅ Tabla con todas las líneas de productos
- ✅ Cantidades formateadas correctamente:
  - Enteros: sin decimales (ej: "5")
  - Decimales: 2 decimales (ej: "2.50")
- ✅ Total = suma de todos los subtotales
- ✅ UOM visible para cada producto

**Verificación Manual**:
- Sumar manualmente los subtotales y confirmar que coincide con el TOTAL
- Verificar que el carrito NO se limpió después de generar el PDF

---

## **🎯 PARTE 2: Contenido del PDF**

### **Caso 2.1: Encabezado con Información del Negocio**
**Objetivo**: Verificar que la información del negocio aparece correctamente.

**Pre-configuración en `.env`**:
```ini
BUSINESS_NAME=Ferretería El Tornillo
BUSINESS_ADDRESS=Av. Principal 123, CABA
BUSINESS_PHONE=+54 11 1234-5678
BUSINESS_EMAIL=contacto@eltornillo.com.ar
QUOTE_VALID_DAYS=15
```

**Pasos**:
1. Reiniciar Docker para que lea el `.env` actualizado
2. Agregar productos al carrito
3. Generar PDF

**Resultado esperado**:
- ✅ PDF muestra:
  - Nombre del negocio: "Ferretería El Tornillo"
  - Dirección: "Av. Principal 123, CABA"
  - Contacto: "Tel: +54 11 1234-5678 | Email: contacto@eltornillo.com.ar"
  - Validez: "15 días desde la fecha de emisión"

---

### **Caso 2.2: Sin Información del Negocio**
**Objetivo**: Verificar que el PDF funciona con config mínima.

**Pre-configuración**: Remover todas las variables `BUSINESS_*` del `.env`

**Pasos**:
1. Reiniciar Docker
2. Generar PDF

**Resultado esperado**:
- ✅ PDF genera correctamente
- ✅ Nombre del negocio: "Ferretería" (default)
- ✅ NO se muestran dirección/teléfono/email (vacíos)
- ✅ Validez: 7 días (default)

---

### **Caso 2.3: Fecha y Número de Presupuesto**
**Objetivo**: Verificar unicidad y formato de identificadores.

**Pasos**:
1. Generar 3 PDFs consecutivos (con segundos de diferencia)

**Resultado esperado**:
- ✅ Cada PDF tiene número único:
  - `PRES-20260112-091500`
  - `PRES-20260112-091505`
  - `PRES-20260112-091510`
- ✅ Fecha siempre en formato `DD/MM/YYYY`
- ✅ Los números son diferentes (incluyen segundos)

---

### **Caso 2.4: UOM (Unidades de Medida)**
**Objetivo**: Verificar que las unidades se muestran correctamente.

**Pasos**:
1. Agregar productos con diferentes UOM:
   - Producto con UOM "UN" (unidad)
   - Producto con UOM "KG" (kilogramo)
   - Producto sin UOM (si existe)
2. Generar PDF

**Resultado esperado**:
- ✅ Columna "Unidad" muestra el símbolo correcto
- ✅ Para productos sin UOM: muestra "—"
- ✅ Formato consistente en toda la tabla

---

### **Caso 2.5: Formato de Cantidades**
**Objetivo**: Verificar formato correcto de cantidades.

**Pasos**:
1. Agregar al carrito:
   - 10 unidades de producto A (entero)
   - 2.50 kg de producto B (decimal)
   - 1 unidad de producto C (entero)
2. Generar PDF

**Resultado esperado**:
- ✅ Producto A: cantidad "10" (sin decimales)
- ✅ Producto B: cantidad "2.50" (con decimales)
- ✅ Producto C: cantidad "1" (sin decimales)
- ✅ NO mostrar ".00" para cantidades enteras

---

### **Caso 2.6: Formato de Precios**
**Objetivo**: Verificar formato monetario.

**Pasos**:
1. Agregar productos con precios variados:
   - Precio $10.00
   - Precio $125.50
   - Precio $2500.99
2. Generar PDF

**Resultado esperado**:
- ✅ Todos los precios con "$" y 2 decimales
- ✅ "$10.00", "$125.50", "$2500.99"
- ✅ Alineación a la derecha en columnas de precio
- ✅ Total con formato monetario destacado

---

## **🎯 PARTE 3: Integración con MEJORA 12 (Método de Pago)**

### **Caso 3.1: Método de Pago NO Incluido (Comportamiento Actual)**
**Objetivo**: Verificar que el PDF funciona sin método de pago seleccionado.

**Pasos**:
1. Agregar productos al carrito
2. NO seleccionar método de pago en la UI (o dejarlo en default)
3. Generar PDF

**Resultado esperado**:
- ✅ PDF genera correctamente
- ✅ NO muestra "Método de Pago" (porque no está en session)
- ✅ Todo el resto funciona normal

**Nota**: El método de pago actualmente solo se envía al confirmar venta, no se persiste en session durante la navegación.

---

### **Caso 3.2: Método de Pago Incluido (Si se Implementa Persistencia)**
**Objetivo**: Si se modifica la UI para persistir el método en session, verificar que aparece en el PDF.

**Pre-condición**: Modificar `_cart.html` para guardar el método en session cuando cambia el radio button.

**Pasos**:
1. Seleccionar "Transferencia"
2. Generar PDF

**Resultado esperado**:
- ✅ PDF muestra "Método de Pago: Transferencia"

**Pasos**:
1. Seleccionar "Efectivo"
2. Generar PDF

**Resultado esperado**:
- ✅ PDF muestra "Método de Pago: Efectivo"

---

## **🎯 PARTE 4: Comportamiento y UX**

### **Caso 4.1: PDF No Modifica el Carrito**
**Objetivo**: Verificar que generar PDF no afecta el carrito.

**Pasos**:
1. Agregar 3 productos al carrito
2. Generar PDF
3. Verificar el carrito después

**Resultado esperado**:
- ✅ El carrito mantiene los 3 productos
- ✅ Las cantidades NO cambiaron
- ✅ El usuario puede seguir editando o confirmar la venta normalmente

---

### **Caso 4.2: Múltiples PDFs del Mismo Carrito**
**Objetivo**: Verificar que se pueden generar varios PDFs del mismo carrito.

**Pasos**:
1. Agregar productos al carrito
2. Generar PDF (guardarlo como PDF1)
3. Sin modificar el carrito, generar otro PDF (guardarlo como PDF2)
4. Agregar 1 producto más
5. Generar PDF3

**Resultado esperado**:
- ✅ PDF1 y PDF2 tienen el mismo contenido pero diferente número de presupuesto
- ✅ PDF3 incluye el producto adicional
- ✅ Todos los PDFs se descargan correctamente

---

### **Caso 4.3: Botón Target _blank**
**Objetivo**: Verificar que el PDF se abre en nueva pestaña/descarga sin dejar la página.

**Pasos**:
1. Generar PDF

**Resultado esperado**:
- ✅ El navegador descarga el PDF O lo abre en nueva pestaña
- ✅ La página `/sales/new` se mantiene abierta
- ✅ El carrito sigue visible y funcional

---

### **Caso 4.4: Después de Confirmar Venta**
**Objetivo**: Verificar que después de confirmar una venta, el botón desaparece.

**Pasos**:
1. Agregar productos al carrito
2. Confirmar venta
3. Verificar el carrito

**Resultado esperado**:
- ✅ El carrito se vacía (comportamiento normal de confirmación)
- ✅ El botón "Generar Presupuesto" ya NO es visible
- ✅ Solo se muestra "El carrito está vacío"

---

## **🎯 PARTE 5: Validación y Seguridad**

### **Caso 5.1: Endpoint Requiere Autenticación**
**Objetivo**: Verificar que el endpoint está protegido por el password gate.

**Pasos**:
1. Cerrar sesión (logout)
2. Intentar acceder directamente a `/sales/quote.pdf`

**Resultado esperado**:
- ✅ Redirección a `/login`
- ✅ NO se genera PDF
- ✅ Solicita autenticación

---

### **Caso 5.2: Productos Eliminados Durante la Sesión**
**Objetivo**: Verificar comportamiento si un producto ya no existe en DB.

**Pasos**:
1. Agregar producto al carrito
2. (Desde otro navegador o consola DB) eliminar ese producto de la DB
3. Intentar generar PDF

**Resultado esperado**:
- ✅ El endpoint maneja el error gracefully
- ✅ El producto eliminado NO aparece en el PDF
- ✅ Los otros productos sí aparecen
- ✅ Total correcto (solo productos existentes)

**Alternativa**: Flash message de error si todos los productos fueron eliminados.

---

### **Caso 5.3: Precios Actualizados**
**Objetivo**: Verificar que el PDF usa precios actuales de la DB.

**Pasos**:
1. Agregar producto A con precio $100 al carrito
2. (Desde otro lugar) actualizar precio de producto A a $150 en la DB
3. Generar PDF

**Resultado esperado**:
- ✅ El PDF usa el precio actualizado de la DB ($150)
- ✅ El subtotal refleja el nuevo precio
- ✅ Total correcto

**Nota**: Esto es correcto porque el carrito solo guarda qty, no el precio.

---

## **🎯 PARTE 6: Performance y Estabilidad**

### **Caso 6.1: PDF con Muchos Productos**
**Objetivo**: Verificar que el sistema maneja carritos grandes.

**Pasos**:
1. Agregar 50+ productos al carrito
2. Generar PDF

**Resultado esperado**:
- ✅ PDF genera correctamente (puede tardar unos segundos)
- ✅ Todas las líneas aparecen en la tabla
- ✅ ReportLab maneja paginación automáticamente si es necesario
- ✅ Total correcto

---

### **Caso 6.2: Caracteres Especiales en Nombres**
**Objetivo**: Verificar que el PDF maneja Unicode correctamente.

**Pasos**:
1. Agregar productos con nombres especiales:
   - "Tornillo ½ pulgada"
   - "Ángulo 90° acero"
   - "Tuerca M10 – alta resistencia"
2. Generar PDF

**Resultado esperado**:
- ✅ Todos los caracteres especiales se muestran correctamente
- ✅ NO hay errores de encoding
- ✅ Símbolos (½, °, –) visibles

---

## **🎯 PARTE 7: Casos Edge y Errores**

### **Caso 7.1: Cantidad = 0**
**Objetivo**: Verificar comportamiento con cantidades inválidas.

**Pasos**:
1. (Manipulando el carrito en session o vía código) setear qty=0
2. Intentar generar PDF

**Resultado esperado**:
- **Opción A**: El sistema filtra productos con qty=0 y NO los incluye
- **Opción B**: Flash message de error: "Carrito inválido"

---

### **Caso 7.2: Precio Negativo**
**Objetivo**: Verificar que no se permiten precios negativos.

**Prerequisito**: Los productos en DB tienen constraint `sale_price >= 0`

**Resultado esperado**:
- ✅ NO es posible tener precios negativos en DB
- ✅ PDF siempre muestra precios válidos

---

### **Caso 7.3: Error en Generación de PDF**
**Objetivo**: Simular un error en ReportLab.

**Pasos**:
1. (Requiere modificar código temporalmente) forzar excepción en `generate_quote_pdf()`
2. Intentar generar PDF

**Resultado esperado**:
- ✅ Flash message: "Error al generar presupuesto: <detalle>"
- ✅ Redirección a `/sales/new`
- ✅ NO se descarga archivo corrupto
- ✅ Carrito se mantiene intacto

---

## **📊 Resumen de Pruebas**

| Categoría | Casos | Críticos |
|-----------|-------|----------|
| **Generación Básica** | 4 | ✅ 1.3, 1.4 |
| **Contenido del PDF** | 6 | ✅ 2.1, 2.5, 2.6 |
| **Método de Pago** | 2 | 3.1 |
| **Comportamiento/UX** | 4 | ✅ 4.1, 4.3 |
| **Seguridad** | 3 | ✅ 5.1 |
| **Performance** | 2 | 6.1 |
| **Edge Cases** | 3 | 7.1, 7.3 |
| **TOTAL** | **24** | **10** |

---

## **✅ Checklist de Aceptación Final**

- [ ] Botón "Generar Presupuesto" visible cuando carrito tiene productos
- [ ] Botón NO visible cuando carrito está vacío
- [ ] PDF descarga correctamente
- [ ] Nombre de archivo con timestamp correcto
- [ ] Encabezado incluye información del negocio (si está configurada)
- [ ] Número de presupuesto único con formato `PRES-YYYYMMDD-HHMMSS`
- [ ] Fecha en formato argentino `DD/MM/YYYY`
- [ ] Tabla con todas las líneas del carrito
- [ ] UOM visible para cada producto
- [ ] Cantidades formateadas (sin .00 para enteros)
- [ ] Precios con $ y 2 decimales
- [ ] Total correcto y destacado
- [ ] Texto legal de validez
- [ ] NO se crea registro en `sale`
- [ ] NO se crea registro en `stock_move`
- [ ] NO se crea registro en `finance_ledger`
- [ ] Stock NO se descuenta
- [ ] Carrito NO se modifica después de generar PDF
- [ ] Endpoint protegido por autenticación
- [ ] Manejo de errores con flash messages

---

## **🚀 Pruebas Manuales Rápidas**

### **Test Rápido 1: Happy Path**
```
1. Login
2. Ir a /sales/new
3. Agregar 2-3 productos
4. Click "Generar Presupuesto (PDF)"
5. Verificar descarga y contenido
6. Confirmar que carrito sigue igual
```

### **Test Rápido 2: Carrito Vacío**
```
1. /sales/new sin productos
2. Verificar que botón NO aparece
3. Intentar acceder a /sales/quote.pdf
4. Verificar flash + redirect
```

### **Test Rápido 3: Configuración del Negocio**
```
1. Editar .env con datos del negocio
2. docker compose restart
3. Generar PDF
4. Verificar que datos aparecen en encabezado
```

---

**✅ FIN DE TESTING - PRESUPUESTOS EN PDF**
