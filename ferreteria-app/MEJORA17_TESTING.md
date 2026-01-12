# 🧪 **MEJORA 17: Modal de Confirmación en Editar Venta - Casos de Prueba**

---

## **📋 Resumen de la Mejora**

**Objetivo**: Agregar un modal de confirmación con vista previa completa ANTES de aplicar correcciones a una venta, mejorando la UX y previniendo errores.

**Funcionalidades implementadas**:
- ✅ Endpoint `POST /sales/<id>/edit/preview` que genera vista previa
- ✅ Modal Bootstrap con resumen completo de cambios
- ✅ Comparación antes/después en tablas lado a lado
- ✅ Lista de cambios: agregados, eliminados, modificados
- ✅ Impacto financiero: diferencia y tipo de asiento
- ✅ Validación de stock ANTES de confirmar
- ✅ Bloqueo del botón "Confirmar" si hay stock insuficiente
- ✅ Prevención de doble submit

---

## **🎯 PARTE 1: Modal de Preview - Apertura y Contenido**

### **Caso 1.1: Abrir Preview con Cambios Válidos**
**Objetivo**: Verificar que el modal se abre con contenido correcto.

**Setup**:
```
Venta original:
- Producto A: qty=5, precio=$10, subtotal=$50
Total: $50
```

**Pasos**:
1. Ir a `/sales/<id>/edit`
2. Cambiar Producto A qty de 5 a 8
3. Click "Guardar Cambios"

**Resultado esperado**:
- ✅ Modal se abre automáticamente
- ✅ Título: "Confirmar Corrección de Venta #X"
- ✅ Alert warning visible: "Esta corrección generará..."
- ✅ Sección "Resumen de Cambios" visible
- ✅ Tablas "Antes" y "Después" lado a lado
- ✅ Sección "Impacto Financiero"
- ✅ Botones: "Cancelar" y "Confirmar Corrección"

**Verificación técnica**:
- HTMX hace `POST /sales/<id>/edit/preview`
- Response es HTML del modal
- JavaScript inline abre el modal automáticamente

---

### **Caso 1.2: No Cambios - No Modal**
**Objetivo**: Verificar que si no hay cambios, se muestra mensaje sin modal.

**Pasos**:
1. Editar venta
2. NO hacer cambios (dejar cantidades igual)
3. Click "Guardar Cambios"

**Resultado esperado**:
- ✅ NO se abre modal
- ✅ Se muestra alert info: "No hay cambios para aplicar."
- ✅ Usuario permanece en formulario de edición

---

## **🎯 PARTE 2: Cambios - Productos Modificados**

### **Caso 2.1: Disminuir Cantidad - Preview Correcto**
**Objetivo**: Verificar que disminución se muestra correctamente.

**Setup**:
```
Venta original:
- Producto A: qty=10, precio=$5, subtotal=$50
Total: $50
```

**Pasos**:
1. Editar venta
2. Cambiar Producto A qty de 10 a 7
3. Click "Guardar Cambios"

**Resultado esperado en Modal**:
- ✅ **Sección "Cantidades Modificadas":**
  - Producto A: 10 → 7
  - Badge rojo: -3
- ✅ **Tabla "Antes":**
  - Producto A: qty=10, subtotal=$50
  - Total: $50
- ✅ **Tabla "Después":**
  - Producto A: qty=7, subtotal=$35
  - Total: $35
- ✅ **Impacto Financiero:**
  - Total Anterior: $50
  - Total Nuevo: $35
  - Diferencia: Badge rojo "Disminuye ingreso -$15"
  - Texto: "Se creará asiento EXPENSE por $15"

---

### **Caso 2.2: Aumentar Cantidad (Stock Suficiente)**
**Objetivo**: Verificar que aumento se muestra y valida stock.

**Setup**:
```
Venta original:
- Producto A: qty=5, precio=$10, subtotal=$50
Stock actual Producto A: 20
```

**Pasos**:
1. Editar venta
2. Cambiar Producto A qty de 5 a 10 (aumenta 5)
3. Click "Guardar Cambios"

**Resultado esperado en Modal**:
- ✅ **Sección "Cantidades Modificadas":**
  - Producto A: 5 → 10
  - Badge verde: +5
- ✅ **Tabla "Después":**
  - Total: $100
- ✅ **Impacto Financiero:**
  - Diferencia: Badge verde "Aumenta ingreso +$50"
  - Texto: "Se creará asiento INCOME por $50"
- ✅ **NO hay alert de stock insuficiente**
- ✅ Botón "Confirmar Corrección" **HABILITADO**

---

### **Caso 2.3: Aumentar Cantidad (Stock Insuficiente) - Bloqueado**
**Objetivo**: Verificar que se bloquea confirmación si falta stock.

**Setup**:
```
Venta original:
- Producto A: qty=5, precio=$10
Stock actual Producto A: 3
```

**Pasos**:
1. Editar venta
2. Cambiar Producto A qty de 5 a 10 (necesita 5 adicionales)
3. Click "Guardar Cambios"

**Resultado esperado en Modal**:
- ✅ **Alert danger visible en la parte superior:**
  - Título: "Stock Insuficiente:"
  - Lista:
    - Producto A: Necesita 5, disponible: 3
  - Texto: **"No se puede aplicar esta corrección."**
- ✅ Botón "Confirmar Corrección" **DESHABILITADO** (atributo `disabled`)
- ✅ Usuario solo puede cancelar

**Verificación**: No se puede hacer submit del form.

---

## **🎯 PARTE 3: Cambios - Productos Agregados**

### **Caso 3.1: Agregar Producto Nuevo**
**Objetivo**: Verificar que productos nuevos aparecen en "Agregados".

**Setup**:
```
Venta original:
- Producto A: qty=5, precio=$10, subtotal=$50
Total: $50

Producto B disponible: stock=20, precio=$15
```

**Pasos**:
1. Editar venta
2. Agregar Producto B con qty=3
3. Click "Guardar Cambios"

**Resultado esperado en Modal**:
- ✅ **Sección "Productos Agregados (1)":**
  - Producto B: 3 × $15.00 = **$45.00**
- ✅ **Tabla "Antes":**
  - Solo Producto A
  - Total: $50
- ✅ **Tabla "Después":**
  - Producto A: qty=5, subtotal=$50
  - Producto B: qty=3, subtotal=$45
  - Total: $95
- ✅ **Impacto Financiero:**
  - Diferencia: +$45
  - Badge verde "Aumenta ingreso +$45.00"

---

### **Caso 3.2: Agregar Producto con Stock Insuficiente**
**Objetivo**: Verificar validación de stock para productos nuevos.

**Setup**:
```
Producto C: stock=2, precio=$20
```

**Pasos**:
1. Editar venta
2. Agregar Producto C con qty=5
3. Click "Guardar Cambios"

**Resultado esperado en Modal**:
- ✅ Alert danger: "Stock Insuficiente"
  - Producto C: Necesita 5, disponible: 2
- ✅ Botón "Confirmar" deshabilitado

---

## **🎯 PARTE 4: Cambios - Productos Eliminados**

### **Caso 4.1: Eliminar un Producto**
**Objetivo**: Verificar que productos eliminados aparecen en "Eliminados".

**Setup**:
```
Venta original:
- Producto A: qty=5, precio=$10, subtotal=$50
- Producto B: qty=2, precio=$20, subtotal=$40
Total: $90
```

**Pasos**:
1. Editar venta
2. Click 🗑️ en Producto B
3. Click "Guardar Cambios"

**Resultado esperado en Modal**:
- ✅ **Sección "Productos Eliminados (1)":**
  - Producto B: 2 × $20.00 = **$40.00**
- ✅ **Tabla "Antes":**
  - Producto A y B
  - Total: $90
- ✅ **Tabla "Después":**
  - Solo Producto A
  - Total: $50
- ✅ **Impacto Financiero:**
  - Diferencia: -$40
  - Badge rojo "Disminuye ingreso -$40.00"
  - Texto: "Se creará asiento EXPENSE por $40.00"

---

## **🎯 PARTE 5: Cambios Combinados**

### **Caso 5.1: Múltiples Cambios Simultáneos**
**Objetivo**: Verificar que cambios combinados se muestran correctamente.

**Setup**:
```
Venta original:
- Producto A: qty=10, precio=$5, subtotal=$50
- Producto B: qty=2, precio=$20, subtotal=$40
Total: $90
```

**Pasos**:
1. Editar venta
2. Cambiar Producto A qty de 10 a 8 (reducir)
3. Eliminar Producto B
4. Agregar Producto C: qty=5, precio=$10
5. Click "Guardar Cambios"

**Resultado esperado en Modal**:
- ✅ **Sección "Productos Agregados (1)":**
  - Producto C: 5 × $10.00 = $50.00
- ✅ **Sección "Productos Eliminados (1)":**
  - Producto B: 2 × $20.00 = $40.00
- ✅ **Sección "Cantidades Modificadas (1)":**
  - Producto A: 10 → 8 (badge rojo: -2)
- ✅ **Tabla "Después":**
  - Producto A: qty=8, subtotal=$40
  - Producto C: qty=5, subtotal=$50
  - Total: $90
- ✅ **Impacto Financiero:**
  - Total Anterior: $90
  - Total Nuevo: $90
  - Diferencia: Badge gris "Sin cambio en total"

---

## **🎯 PARTE 6: Impacto Financiero**

### **Caso 6.1: Aumento de Total - INCOME**
**Objetivo**: Verificar cálculo y mensaje para aumento.

**Setup**: Total anterior $100, total nuevo $150

**Resultado esperado**:
- ✅ Card header: bg-success (verde)
- ✅ Diferencia: +$50
- ✅ Badge verde: "Aumenta ingreso +$50.00"
- ✅ Texto: "Se creará asiento INCOME por $50.00"

---

### **Caso 6.2: Disminución de Total - EXPENSE**
**Objetivo**: Verificar cálculo y mensaje para disminución.

**Setup**: Total anterior $100, total nuevo $75

**Resultado esperado**:
- ✅ Card header: bg-danger (rojo)
- ✅ Diferencia: -$25
- ✅ Badge rojo: "Disminuye ingreso -$25.00"
- ✅ Texto: "Se creará asiento EXPENSE por $25.00"

---

### **Caso 6.3: Sin Cambio en Total**
**Objetivo**: Verificar mensaje cuando total no cambia.

**Setup**: 
```
Antes:
- Producto A: 10 × $5 = $50
- Producto B: 2 × $25 = $50
Total: $100

Después (swap de productos):
- Producto C: 5 × $20 = $100
Total: $100
```

**Resultado esperado**:
- ✅ Card header: bg-secondary (gris)
- ✅ Badge gris: "Sin cambio en total"
- ✅ No texto adicional de asiento

---

## **🎯 PARTE 7: Acciones del Modal**

### **Caso 7.1: Cancelar Modal - No Aplica Cambios**
**Objetivo**: Verificar que cancelar no guarda nada.

**Pasos**:
1. Editar venta y hacer cambios
2. Click "Guardar Cambios" → modal abre
3. Click "Cancelar"

**Resultado esperado**:
- ✅ Modal se cierra
- ✅ Usuario vuelve al formulario de edición
- ✅ Cambios siguen visibles en el formulario (no se pierden)
- ✅ **NO se guardaron cambios en DB**

**Verificación DB**:
```sql
-- Venta sin cambios
SELECT total FROM sale WHERE id=<id>;
-- Debe tener valor original
```

---

### **Caso 7.2: Confirmar Cambios - Aplica Corrección**
**Objetivo**: Verificar que confirmar aplica todos los cambios.

**Pasos**:
1. Editar venta: disminuir Producto A de 10 a 8
2. Click "Guardar Cambios" → modal abre
3. Revisar preview
4. Click "Confirmar Corrección"

**Resultado esperado**:
- ✅ Modal se cierra
- ✅ Botón muestra spinner: "Procesando..."
- ✅ Redirect a `/sales/<id>` (detalle)
- ✅ Flash success: "Venta #X ajustada exitosamente"
- ✅ Venta muestra qty=8 y total actualizado
- ✅ Stock devuelto correctamente
- ✅ Ledger EXPENSE creado

**Verificación DB**:
```sql
-- Sale actualizada
SELECT total FROM sale WHERE id=<id>;
-- Debe ser nuevo total

-- Stock ajustado
SELECT on_hand_qty FROM product_stock WHERE product_id=<product_a>;
-- Debe haber aumentado

-- Stock_move ADJUST
SELECT * FROM stock_move WHERE type='ADJUST' AND reference_id=<id>;
-- Debe existir

-- Ledger EXPENSE
SELECT * FROM finance_ledger 
WHERE reference_type='MANUAL' AND reference_id=<id> 
  AND type='EXPENSE';
-- Debe existir con amount correcto
```

---

### **Caso 7.3: Doble Click en Confirmar - Prevención**
**Objetivo**: Verificar que no se puede hacer double submit.

**Pasos**:
1. Abrir modal de confirmación
2. Hacer doble click rápido en "Confirmar Corrección"

**Resultado esperado**:
- ✅ Botón se deshabilita inmediatamente después del primer click
- ✅ Botón muestra spinner: "Procesando..."
- ✅ Solo se envía **1 request** al servidor
- ✅ No se duplican ajustes

**Verificación técnica**:
- JavaScript deshabilita el botón en evento `submit`
- Network tab muestra solo 1 POST request

---

## **🎯 PARTE 8: Tablas Antes/Después**

### **Caso 8.1: Visualización Lado a Lado**
**Objetivo**: Verificar layout responsive de tablas.

**Resultado esperado**:
- ✅ En desktop (>768px): 2 columnas lado a lado
- ✅ Tabla "Antes" con header gris
- ✅ Tabla "Después" con header verde
- ✅ Ambas tablas muestran: Producto, Qty, Subtotal
- ✅ Total al pie de cada tabla
- ✅ En móvil (<768px): tablas apiladas verticalmente

---

### **Caso 8.2: Productos en Orden Correcto**
**Objetivo**: Verificar que productos se muestran en orden coherente.

**Resultado esperado**:
- ✅ Productos en tabla "Antes" en orden de la venta original
- ✅ Productos en tabla "Después" en orden lógico (mismo orden si existen)
- ✅ Totales correctos al pie

---

## **🎯 PARTE 9: Validaciones y Edge Cases**

### **Caso 9.1: Payload Vacío - Error**
**Objetivo**: Verificar manejo de formulario sin líneas.

**Pasos**:
1. Editar venta
2. Eliminar todas las líneas
3. Click "Guardar Cambios"

**Resultado esperado**:
- ✅ NO se abre modal
- ✅ Alert warning: "Debe haber al menos una línea en la venta."

---

### **Caso 9.2: Error en Preview - Mensaje Claro**
**Objetivo**: Verificar manejo de errores del endpoint.

**Simular**: Forzar error en backend (ej: DB desconectada)

**Resultado esperado**:
- ✅ NO se abre modal
- ✅ Alert danger: "Error al generar vista previa: [mensaje]"

---

### **Caso 9.3: Producto Inactivo - Bloqueado**
**Objetivo**: Verificar que productos inactivos no se pueden agregar.

**Setup**: Producto D con active=False

**Pasos**:
1. Intentar agregar Producto D en formulario

**Resultado esperado**:
- ✅ Producto D NO aparece en select de productos disponibles
- ✅ O si se bypasea frontend: backend rechaza en preview

---

## **🎯 PARTE 10: UX y Responsive**

### **Caso 10.1: Loading Indicator Visible**
**Objetivo**: Verificar feedback durante carga del preview.

**Pasos**:
1. Simular latencia (Chrome DevTools > Network > Slow 3G)
2. Click "Guardar Cambios"

**Resultado esperado**:
- ✅ Spinner visible debajo del botón: "Generando vista previa..."
- ✅ Cuando responde: spinner desaparece y modal abre

---

### **Caso 10.2: Modal Scrollable**
**Objetivo**: Verificar que modal con muchos productos es scrollable.

**Setup**: Venta con 20+ productos

**Resultado esperado**:
- ✅ Modal tiene `modal-dialog-scrollable`
- ✅ Body del modal tiene scroll vertical
- ✅ Header y footer permanecen fijos
- ✅ Usuario puede scrollear para ver todos los productos

---

### **Caso 10.3: Modal No Se Cierra al Click Fuera**
**Objetivo**: Verificar backdrop static.

**Pasos**:
1. Abrir modal
2. Click en el fondo oscuro (fuera del modal)

**Resultado esperado**:
- ✅ Modal NO se cierra
- ✅ Requiere acción explícita (Cancelar o Confirmar)

---

## **📊 Resumen de Pruebas**

| Categoría | Casos | Críticos |
|-----------|-------|----------|
| **Apertura Modal** | 2 | ✅ 1.1 |
| **Modificados** | 3 | ✅ 2.1, 2.2, 2.3 |
| **Agregados** | 2 | ✅ 3.1, 3.2 |
| **Eliminados** | 1 | ✅ 4.1 |
| **Combinados** | 1 | ✅ 5.1 |
| **Impacto Financiero** | 3 | ✅ 6.1, 6.2 |
| **Acciones** | 3 | ✅ 7.1, 7.2, 7.3 |
| **Tablas** | 2 | 8.1 |
| **Validaciones** | 3 | ✅ 9.1, 9.3 |
| **UX** | 3 | 10.1, 10.3 |
| **TOTAL** | **23** | **14** |

---

## **✅ Checklist de Aceptación Final**

### **Funcionalidad**
- [ ] Endpoint preview existe y funciona
- [ ] Modal se abre automáticamente
- [ ] "No cambios" muestra mensaje sin modal
- [ ] Sección "Agregados" muestra productos nuevos
- [ ] Sección "Eliminados" muestra productos quitados
- [ ] Sección "Modificados" muestra cambios de qty con deltas
- [ ] Tablas antes/después lado a lado
- [ ] Impacto financiero calcula correctamente
- [ ] Badge verde para aumento, rojo para disminución
- [ ] Stock insuficiente bloquea confirmación

### **Validaciones**
- [ ] Stock validado en preview
- [ ] Alert danger visible si falta stock
- [ ] Botón "Confirmar" deshabilitado si stock insuficiente
- [ ] Formulario sin líneas no abre modal
- [ ] Productos inactivos no se pueden agregar

### **Acciones**
- [ ] Cancelar cierra modal sin guardar
- [ ] Confirmar aplica corrección
- [ ] Doble submit prevenido
- [ ] Botón muestra spinner al procesar
- [ ] Redirect a detalle después de confirmar
- [ ] Flash success después de confirmar

### **Ajustes (MEJORA 16)**
- [ ] Stock_move ADJUST creado
- [ ] Stock ajustado correctamente
- [ ] Ledger INCOME o EXPENSE creado
- [ ] Trazabilidad completa

### **UX/UI**
- [ ] Modal responsive
- [ ] Scrollable con muchos productos
- [ ] Backdrop static (no cierra al click fuera)
- [ ] Loading indicator visible
- [ ] Estilos Bootstrap consistentes
- [ ] Badges de colores correctos

---

## **🚀 Flujo de Prueba Manual Completo**

### **Escenario Completo: Corrección con Preview**
```
1. Crear venta original:
   - Producto A: qty=10, precio=$5 → $50
   - Producto B: qty=2, precio=$20 → $40
   Total: $90
   
2. Ir a "Ventas" → "Gestión de Ventas"
3. Click "Editar" en la venta

4. Hacer correcciones:
   - Producto A: cambiar qty de 10 a 8
   - Producto B: eliminar (🗑️)
   - Agregar Producto C: qty=3, precio=$15
   
5. Click "Guardar Cambios"
   ✅ Loading spinner visible

6. Modal se abre con:
   ✅ Resumen de cambios:
      - Eliminados: Producto B
      - Modificados: Producto A (10 → 8, badge -2)
      - Agregados: Producto C
   ✅ Tabla "Antes": A + B, total $90
   ✅ Tabla "Después": A + C, total $85
   ✅ Impacto: -$5, badge rojo
   ✅ Texto: "Se creará asiento EXPENSE por $5.00"

7. Revisar preview y click "Confirmar Corrección"
   ✅ Botón deshabilita y muestra spinner

8. Redirect a detalle
   ✅ Flash: "Venta ajustada exitosamente"
   ✅ Venta muestra: A (qty=8) + C (qty=3), total $85

9. Verificar DB:
   Stock A: +2 (devuelto)
   Stock B: +2 (devuelto)
   Stock C: -3 (nuevo)
   Ledger EXPENSE: $5
```

---

**✅ FIN DE TESTING MEJORA 17**
