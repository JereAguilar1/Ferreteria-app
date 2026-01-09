# MEJORA 4 – Costo Unitario Sin Decimales en Compras

## 📋 **Testing Checklist**

---

## **Objetivo**
Validar que el campo `unit_cost` en la carga de boletas de compra **solo acepte números enteros** (sin decimales), tanto en frontend como en backend.

---

## **1. Frontend - Campo unit_cost**

### ✅ **Test 1.1: Input con step="1"**
**Objetivo:** Verificar que el campo solo permita números enteros en UI.

**Pasos:**
1. Navegar a `/invoices/new`
2. Inspeccionar el campo "Costo Unitario"
3. Verificar atributos HTML:
   - `type="number"`
   - `step="1"`
   - `min="0"`
   - `inputmode="numeric"`

**Resultado esperado:**
- ✅ Campo configurado correctamente
- ✅ Mensaje de ayuda visible: "Solo números enteros (sin decimales)"

---

### ✅ **Test 1.2: Intentar ingresar decimales con teclado**
**Objetivo:** Verificar comportamiento del input al escribir decimales.

**Pasos:**
1. En `/invoices/new`, seleccionar un producto
2. Intentar escribir en "Costo Unitario": `120.5`
3. Observar comportamiento del navegador

**Resultado esperado (varía por navegador):**
- Chrome/Edge: puede permitir escribir pero no enviar el form (validación HTML5)
- Firefox: similar, puede mostrar error en submit
- **Backend debe rechazar** en todos los casos

---

### ✅ **Test 1.3: Incrementar/decrementar con flechas**
**Objetivo:** Verificar que los controles arriba/abajo del input solo incrementen/decrementen de 1 en 1.

**Pasos:**
1. En campo "Costo Unitario", ingresar `100`
2. Usar flecha arriba del input
3. Usar flecha abajo del input

**Resultado esperado:**
- Arriba: `100 → 101 → 102` (incrementos de 1)
- Abajo: `102 → 101 → 100 → 99` (decrementos de 1)

---

## **2. Backend - Validación en add_draft_line**

### ✅ **Test 2.1: Agregar línea con unit_cost entero válido**
**Objetivo:** Verificar que valores enteros válidos sean aceptados.

**Casos:**
| unit_cost | Producto | Qty | Resultado |
|-----------|----------|-----|-----------|
| `120` | Martillo | 1 | ✅ OK |
| `0` | Clavo | 10 | ✅ OK |
| `9999` | Cable | 2 | ✅ OK |
| `1` | Tornillo | 100 | ✅ OK |

**Pasos:**
1. Navegar a `/invoices/new`
2. Seleccionar proveedor y completar datos de boleta
3. Seleccionar producto
4. Ingresar qty y unit_cost según tabla
5. Click "Agregar Ítem"

**Resultado esperado:**
- ✅ Ítem agregado a la tabla de líneas
- ✅ Total calculado correctamente: `line_total = qty * unit_cost`
- ✅ Sin mensajes de error
- ✅ Línea visible en draft

---

### ✅ **Test 2.2: Rechazar unit_cost con decimales**
**Objetivo:** Validar que el backend rechace cualquier valor con decimales.

**Casos a probar:**

#### **Caso A: unit_cost = 120.5**
**Pasos:**
1. En `/invoices/new`, seleccionar producto
2. Ingresar qty = 1
3. En "Costo Unitario" ingresar `120.5` (forzar vía DevTools si es necesario)
4. Click "Agregar Ítem"

**Resultado esperado:**
- ❌ Línea NO agregada
- ⚠️ Flash message (rojo): **"El costo unitario debe ser un número entero (sin decimales)."**
- ✅ Formulario permanece con datos ingresados
- ✅ Draft NO contiene la línea errónea

---

#### **Caso B: unit_cost = 50.99**
**Pasos:** (igual que Caso A, pero con `50.99`)

**Resultado esperado:**
- ❌ Rechazado con mismo mensaje de error

---

#### **Caso C: unit_cost = 100.0**
**Política elegida:** ACEPTAR valores sin parte fraccionaria (aunque se escriban con `.0`)

**Pasos:**
1. Ingresar `100.0` en "Costo Unitario"
2. Click "Agregar Ítem"

**Resultado esperado:**
- ✅ Aceptado (convertido a `100`)
- Línea agregada al draft

**Justificación:** 
- Matemáticamente, `100.0` es un entero (sin parte fraccionaria).
- `Decimal('100.0') % 1 == 0` → válido.
- Política pragmática: validar el **valor matemático**, no el formato de entrada.
- El input HTML con `step="1"` debería prevenir esto de todas formas.

---

#### **Caso D: unit_cost con coma europea (100,5)**
**Pasos:**
1. Ingresar `100,5` en "Costo Unitario"
2. Click "Agregar Ítem"

**Resultado esperado:**
- ❌ Rechazado con mensaje: **"El costo unitario debe ser un número entero válido."**
- (La conversión a Decimal falla o detecta el problema)

---

### ✅ **Test 2.3: Rechazar unit_cost no numérico**
**Objetivo:** Validar que valores no numéricos sean rechazados.

**Casos:**
| unit_cost | Resultado |
|-----------|-----------|
| `abc` | ❌ "El costo unitario debe ser un número entero válido." |
| `12a5` | ❌ "El costo unitario debe ser un número entero válido." |
| `` (vacío) | ❌ Error (o tratar como 0 y validar) |
| `-50` | ❌ "El costo unitario no puede ser negativo" |

**Pasos:** (para cada caso)
1. Seleccionar producto
2. Ingresar qty = 1
3. Ingresar unit_cost según tabla (forzar vía DevTools si necesario)
4. Click "Agregar Ítem"

**Resultado esperado:**
- ❌ Línea NO agregada
- ⚠️ Flash message apropiado según error

---

### ✅ **Test 2.4: unit_cost = 0 (caso borde)**
**Objetivo:** Validar que `0` sea aceptado (puede ser una donación/muestra).

**Pasos:**
1. Seleccionar producto
2. Ingresar qty = 10
3. Ingresar unit_cost = `0`
4. Click "Agregar Ítem"

**Resultado esperado:**
- ✅ Línea agregada
- line_total = 0.00
- Sin errores

---

## **3. Servicio Transaccional (Validación Defensiva)**

### ✅ **Test 3.1: create_invoice_with_lines con unit_cost entero**
**Objetivo:** Verificar que el servicio acepte valores enteros.

**Pasos:**
1. Crear una boleta completa con 3 líneas:
   - Producto A: qty=2, unit_cost=100
   - Producto B: qty=5, unit_cost=50
   - Producto C: qty=1, unit_cost=0
2. Click "Crear Boleta"

**Resultado esperado:**
- ✅ Boleta creada exitosamente
- ✅ ID de boleta retornado
- ✅ Líneas en `purchase_invoice_line` con unit_cost enteros
- ✅ Stock actualizado (IN movement)
- ✅ Flash message: "Boleta #X creada exitosamente. Stock actualizado."

**Verificar en DB:**
```sql
SELECT id, invoice_number, total_amount, status FROM purchase_invoice ORDER BY id DESC LIMIT 1;
SELECT product_id, qty, unit_cost, line_total FROM purchase_invoice_line WHERE invoice_id = X;
```

---

### ✅ **Test 3.2: Servicio rechaza unit_cost con decimales (defensivo)**
**Objetivo:** Verificar que el servicio valida unit_cost incluso si el blueprint falla.

**Método:** Simulación mediante test unitario o forzando payload incorrecto.

**Payload malicioso:**
```python
payload = {
    'supplier_id': 1,
    'invoice_number': 'TEST-001',
    'invoice_date': date.today(),
    'due_date': None,
    'lines': [
        {'product_id': 1, 'qty': 10, 'unit_cost': 50.75}  # DECIMAL!
    ]
}
```

**Resultado esperado:**
- ❌ `ValueError` lanzado por `create_invoice_with_lines`
- Mensaje: **"El costo unitario debe ser un número entero (sin decimales) para [nombre_producto]"**
- ✅ Transacción rollback
- ✅ No se crea boleta ni movimiento de stock

---

## **4. Persistencia y Cálculos**

### ✅ **Test 4.1: line_total y total_amount calculados correctamente**
**Objetivo:** Asegurar que los totales se calculan bien con unit_cost enteros.

**Caso:** Crear boleta con:
- Línea 1: qty=2.5, unit_cost=100 → line_total = 250.00
- Línea 2: qty=10, unit_cost=15 → line_total = 150.00
- **total_amount = 400.00**

**Pasos:**
1. Agregar ambas líneas al draft
2. Verificar totales en la UI (debajo de la tabla)
3. Crear boleta
4. Verificar en DB

**Resultado esperado:**
- ✅ `line_total` redondeado a 2 decimales
- ✅ `total_amount` correcto (suma de line_totals)
- ✅ Constraint `invoice_line_total_consistency` respetado

**SQL:**
```sql
SELECT qty, unit_cost, line_total, (qty * unit_cost) as calc
FROM purchase_invoice_line WHERE invoice_id = X;
```
- `line_total` debe ser igual a `ROUND(qty * unit_cost, 2)`

---

### ✅ **Test 4.2: Draft en session no guarda decimales**
**Objetivo:** Verificar que el draft en session almacena unit_cost como entero.

**Pasos:**
1. Agregar línea con unit_cost=120
2. Inspeccionar Flask session (vía debug o logs)

**Resultado esperado:**
```python
session['invoice_draft'] = {
    'lines': [
        {'product_id': 5, 'qty': 10.0, 'unit_cost': 120}  # int, no float
    ]
}
```

---

## **5. Integración HTMX**

### ✅ **Test 5.1: HTMX add-line con unit_cost inválido**
**Objetivo:** Verificar que el error se muestre correctamente sin romper la UI.

**Pasos:**
1. En `/invoices/new`, agregar líneas válidas
2. Intentar agregar línea con unit_cost=50.5 (forzar vía DevTools)
3. Click "Agregar Ítem"

**Resultado esperado:**
- ❌ Línea NO agregada
- ⚠️ Flash message rojo visible en top de página
- ✅ Tabla de líneas existentes se mantiene intacta (HTMX no rompe)
- ✅ Formulario de "Agregar Ítem" sigue funcional

---

### ✅ **Test 5.2: HTMX remove-line no afectado**
**Objetivo:** Asegurar que eliminar líneas sigue funcionando.

**Pasos:**
1. Agregar 3 líneas con unit_cost válidos (enteros)
2. Eliminar la línea del medio (click en ❌ o botón eliminar)
3. Verificar que se elimina correctamente

**Resultado esperado:**
- ✅ Línea eliminada del draft
- ✅ Total recalculado
- ✅ HTMX refresca la tabla sin errores

---

## **6. Casos Edge y Compatibilidad**

### ✅ **Test 6.1: Actualizar línea existente con unit_cost inválido**
**Objetivo:** Verificar que al agregar un producto ya existente con unit_cost decimal, se rechace.

**Pasos:**
1. Agregar Producto A con qty=5, unit_cost=100 (OK)
2. Intentar agregar Producto A nuevamente con qty=10, unit_cost=50.5 (INVÁLIDO)

**Resultado esperado:**
- ❌ Actualización rechazada
- ⚠️ Flash error
- ✅ Línea original se mantiene sin cambios (qty=5, unit_cost=100)

---

### ✅ **Test 6.2: Múltiples productos, uno con unit_cost inválido**
**Objetivo:** Verificar que la validación ocurre línea por línea.

**Pasos:**
1. Agregar Producto A: qty=5, unit_cost=100 (OK, agregado)
2. Agregar Producto B: qty=2, unit_cost=50.75 (ERROR, rechazado)
3. Agregar Producto C: qty=10, unit_cost=20 (OK, agregado)

**Resultado esperado:**
- ✅ Draft contiene Producto A y C
- ❌ Producto B NO está en el draft
- Flash error mostrado solo para Producto B

---

### ✅ **Test 6.3: Crear boleta completa sin decimales**
**Objetivo:** Verificar flujo end-to-end exitoso.

**Pasos:**
1. Navegar a `/invoices/new`
2. Seleccionar proveedor: "Ferretería Central"
3. Número de boleta: "FC-2026-001"
4. Fecha boleta: hoy
5. Agregar 5 líneas diferentes con unit_cost enteros variados
6. Verificar total calculado
7. Click "Crear Boleta"

**Resultado esperado:**
- ✅ Boleta creada
- ✅ Redirección a `/invoices/{id}`
- ✅ Detalle muestra todas las líneas con unit_cost enteros
- ✅ Status: PENDING
- ✅ Stock actualizado (verificar en `/products`)
- ✅ Movimiento de stock registrado (tipo IN)

**SQL verificación:**
```sql
SELECT p.name, sml.qty, sml.unit_cost
FROM stock_move_line sml
JOIN product p ON p.id = sml.product_id
JOIN stock_move sm ON sm.id = sml.stock_move_id
WHERE sm.reference_type = 'INVOICE' AND sm.reference_id = X;
```
- `unit_cost` debe ser entero en todas las filas

---

## **7. Compatibilidad con Funcionalidades Existentes**

### ✅ **Test 7.1: MEJORA 1 (Fotos) no afectada**
**Pasos:**
1. Verificar que imágenes de productos se muestren correctamente en select de productos
2. Crear boleta con productos que tienen y no tienen imágenes

**Resultado esperado:**
- ✅ Fotos visibles (si existen) en UI de productos
- Sin errores

---

### ✅ **Test 7.2: MEJORA 2 (Filtro categorías) no afectada**
**Pasos:**
1. Navegar a `/products`
2. Filtrar por categoría
3. Verificar que el filtro funciona

**Resultado esperado:**
- ✅ Filtro funcional
- Sin errores

---

### ✅ **Test 7.3: MEJORA 3 (Top vendidos) no afectada**
**Pasos:**
1. Navegar a `/sales/new`
2. Verificar que "Más vendidos" se muestra
3. Agregar un top product al carrito

**Resultado esperado:**
- ✅ Top products visibles
- ✅ Agregar al carrito funciona
- Sin errores

---

### ✅ **Test 7.4: Pagar boleta creada (Fase 4)**
**Objetivo:** Verificar que boletas con unit_cost enteros se pueden pagar normalmente.

**Pasos:**
1. Crear boleta con unit_cost enteros
2. Ir a detalle de boleta
3. Marcar como PAID con fecha de hoy

**Resultado esperado:**
- ✅ Boleta marcada como PAID
- ✅ Egreso registrado en `finance_ledger`
- ✅ Flash success
- Sin errores

---

## **8. Regresión (No Romper)**

### ✅ **Test 8.1: Proveedores CRUD**
**Pasos:** Crear, editar, listar proveedores

**Resultado esperado:** ✅ Funcional

---

### ✅ **Test 8.2: Productos CRUD**
**Pasos:** Crear, editar, listar, filtrar productos

**Resultado esperado:** ✅ Funcional

---

### ✅ **Test 8.3: Ventas (POS)**
**Pasos:** Crear venta, agregar productos, confirmar

**Resultado esperado:** ✅ Funcional

---

### ✅ **Test 8.4: Balance**
**Pasos:** Ver balance diario, mensual, anual

**Resultado esperado:** ✅ Funcional

---

## **9. Resumen de Política: Decimales en unit_cost**

### **Política Implementada (Pragmática):**
- ✅ **Solo enteros permitidos** (matemáticamente: sin parte fraccionaria)
- ✅ **Aceptar `100.0`** (se convierte a `100`, ya que `100.0 % 1 == 0`)
- ❌ **Rechazar valores con parte fraccionaria** (ej. `120.5`, `50.99`)
- ❌ **Rechazar valores con coma** (ej. `100,5`)
- ✅ **Permitir `0`** (casos especiales: donaciones, muestras)
- ✅ **Validación en frontend (HTML5)** y **backend (Python)**
- ✅ **Validación defensiva en servicio transaccional**

### **Mensajes de Error:**
1. Con decimales: **"El costo unitario debe ser un número entero (sin decimales)."**
2. No numérico: **"El costo unitario debe ser un número entero válido."**
3. Negativo: **"El costo unitario no puede ser negativo."**

---

## **10. Archivos Modificados**

```
app/
├── templates/
│   └── invoices/
│       └── new.html                   ← step="1", inputmode="numeric", help text
├── blueprints/
│   └── invoices.py                    ← Validación en add_draft_line, guardar como int
└── services/
    └── invoice_service.py             ← Validación defensiva en create_invoice_with_lines

MEJORA4_TESTING.md                     ← Este archivo
```

---

## **✅ Testing Completo: Checklist Final**

- [ ] Frontend: input con step="1"
- [ ] Frontend: mensaje de ayuda visible
- [ ] Backend: acepta enteros válidos (120, 0, 9999)
- [ ] Backend: rechaza decimales (120.5, 50.99, 100.0)
- [ ] Backend: rechaza no numéricos (abc, 12a5)
- [ ] Backend: rechaza negativos (-50)
- [ ] Backend: acepta cero (0)
- [ ] Servicio: rechaza decimales (validación defensiva)
- [ ] Cálculos: line_total y total_amount correctos
- [ ] Session: draft guarda unit_cost como int
- [ ] HTMX: errores se muestran sin romper UI
- [ ] HTMX: eliminar líneas funciona
- [ ] Edge: actualizar línea existente valida unit_cost
- [ ] Edge: múltiples productos, validación individual
- [ ] End-to-end: crear boleta completa exitosamente
- [ ] Regresión: MEJORA 1, 2, 3 funcionan
- [ ] Regresión: Proveedores, Productos, Ventas, Balance funcionan
- [ ] Regresión: Pagar boleta funciona

---

## **🎯 Resultado Esperado Final**

Al finalizar todos los tests:
- ✅ **unit_cost en UI solo acepta enteros**
- ✅ **Validaciones backend robustas (blueprint + servicio)**
- ✅ **Cálculos de totales correctos**
- ✅ **Session draft no contiene decimales**
- ✅ **HTMX funciona sin errores**
- ✅ **No se rompen funcionalidades existentes**
- ✅ **Política clara y documentada**

---

**Última actualización:** Enero 2026  
**Autor:** Sistema Ferretería - MEJORA 4
