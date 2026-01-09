# FASE 3 - Testing: Compras / Boletas (Proveedores + Ítems + Stock)

## Objetivo
Verificar que el módulo de compras funciona correctamente:
- CRUD de proveedores
- Creación de boletas con ítems obligatorios
- Aumento de stock automático
- Validaciones y transacciones

---

## Pre-requisitos

1. **Base de datos PostgreSQL corriendo:**
```bash
cd c:\jere\Ferreteria\Ferreteria-db
docker-compose up -d
```

2. **Aplicación Flask corriendo:**
```bash
cd c:\jere\Ferreteria\ferreteria-app
python app.py
```

3. **Datos iniciales cargados:**
```bash
# UOMs y categorías
python seed_initial_data.py

# Productos de prueba (opcional, si no hay)
# Asegurarse de tener al menos 3-4 productos activos
```

4. **Acceder a la aplicación:**
   - URL: http://127.0.0.1:5000

---

## Caso 1: Crear Proveedores

### Pasos:
1. Navegar a: **Compras → Proveedores**
2. Click en **"Nuevo Proveedor"**
3. Llenar formulario:
   - **Nombre:** Ferretería Central S.A.
   - **RFC/RUT:** RFC-123456789
   - **Teléfono:** +52 55 1234 5678
   - **Email:** ventas@ferreteria-central.com
   - **Notas:** Proveedor principal de herramientas
4. Click en **"Crear Proveedor"**

### Resultado esperado:
- ✅ Mensaje: "Proveedor 'Ferretería Central S.A.' creado exitosamente"
- ✅ Redirige a listado de proveedores
- ✅ Proveedor aparece en la tabla

### Verificación en DB:
```sql
SELECT * FROM supplier ORDER BY id DESC LIMIT 1;
```

**Repetir para crear más proveedores:**
- Distribuidora El Constructor (RFC-987654321)
- Pinturas y Acabados Ltda. (RFC-456789123)

---

## Caso 2: Listar Proveedores

### Pasos:
1. Navegar a: **Compras → Proveedores**

### Resultado esperado:
- ✅ Se muestra tabla con todos los proveedores
- ✅ Columnas: ID, Nombre, RFC/RUT, Teléfono, Email, Acciones
- ✅ Botón "Editar" funcional en cada fila

### Verificación en DB:
```sql
SELECT COUNT(*) as total_proveedores FROM supplier;
-- Debe mostrar al menos 3
```

---

## Caso 3: Editar Proveedor

### Pasos:
1. En listado de proveedores, click en **"Editar"** del primer proveedor
2. Modificar el teléfono: **+52 55 9999 9999**
3. Click en **"Guardar Cambios"**

### Resultado esperado:
- ✅ Mensaje: "Proveedor '...' actualizado exitosamente"
- ✅ Cambios reflejados en listado

### Verificación en DB:
```sql
SELECT name, phone FROM supplier WHERE id = 1;
-- phone debe ser '+52 55 9999 9999'
```

---

## Caso 4: Crear Boleta con 2 Ítems (Stock Aumenta)

### Pre-condición:
- Verificar stock actual de 2 productos:

```sql
SELECT p.id, p.name, p.sku, ps.on_hand_qty 
FROM product p 
JOIN product_stock ps ON p.id = ps.product_id 
WHERE p.active = true 
ORDER BY p.id 
LIMIT 2;
```

**Anotar:**
- Producto 1: ID=___, Stock inicial=___
- Producto 2: ID=___, Stock inicial=___

### Pasos:
1. Navegar a: **Compras → Nueva Boleta**
2. Llenar encabezado:
   - **Proveedor:** Ferretería Central S.A.
   - **Número de Boleta:** BOL-001
   - **Fecha Boleta:** (fecha actual)
   - **Vencimiento:** (fecha +30 días, opcional)

3. **Agregar Ítem 1:**
   - **Producto:** (Seleccionar primer producto)
   - **Cantidad:** 10
   - **Costo Unitario:** 50.00
   - Click **"Agregar Ítem"**

4. **Agregar Ítem 2:**
   - **Producto:** (Seleccionar segundo producto)
   - **Cantidad:** 5.5
   - **Costo Unitario:** 120.00
   - Click **"Agregar Ítem"**

5. Verificar que se muestra:
   - ✅ Tabla con 2 ítems
   - ✅ Subtotales calculados: $500.00 y $660.00
   - ✅ **TOTAL: $1,160.00**

6. Click en **"Crear Boleta"** (confirmar)

### Resultado esperado:
- ✅ Mensaje: "Boleta #1 creada exitosamente. Stock actualizado."
- ✅ Redirige a detalle de boleta
- ✅ Muestra información completa de la boleta
- ✅ Estado: **Pendiente**

### Verificación en DB:

**1. Boleta creada:**
```sql
SELECT * FROM purchase_invoice WHERE invoice_number = 'BOL-001';
-- status debe ser 'PENDING'
-- paid_at debe ser NULL
-- total_amount debe ser 1160.00
```

**2. Líneas de boleta:**
```sql
SELECT 
    pil.id,
    p.name,
    pil.qty,
    pil.unit_cost,
    pil.line_total
FROM purchase_invoice_line pil
JOIN product p ON pil.product_id = p.id
WHERE pil.invoice_id = (SELECT id FROM purchase_invoice WHERE invoice_number = 'BOL-001')
ORDER BY pil.id;

-- Debe mostrar 2 líneas con los datos correctos
```

**3. Stock Move creado:**
```sql
SELECT * FROM stock_move 
WHERE reference_type = 'INVOICE' 
  AND reference_id = (SELECT id FROM purchase_invoice WHERE invoice_number = 'BOL-001');

-- type debe ser 'IN'
-- notes debe contener 'Compra - Boleta #BOL-001'
```

**4. Stock Move Lines:**
```sql
SELECT 
    sml.id,
    p.name,
    sml.qty,
    sml.unit_cost
FROM stock_move_line sml
JOIN product p ON sml.product_id = p.id
WHERE sml.stock_move_id = (
    SELECT id FROM stock_move 
    WHERE reference_type = 'INVOICE' 
      AND reference_id = (SELECT id FROM purchase_invoice WHERE invoice_number = 'BOL-001')
);

-- Debe mostrar 2 líneas
```

**5. Stock AUMENTADO (CRÍTICO):**
```sql
SELECT 
    p.id,
    p.name,
    ps.on_hand_qty
FROM product p
JOIN product_stock ps ON p.id = ps.product_id
WHERE p.id IN (
    SELECT product_id FROM purchase_invoice_line 
    WHERE invoice_id = (SELECT id FROM purchase_invoice WHERE invoice_number = 'BOL-001')
);

-- on_hand_qty debe haber AUMENTADO:
-- Producto 1: stock_inicial + 10
-- Producto 2: stock_inicial + 5.5
```

---

## Caso 5: Ver Listado de Boletas

### Pasos:
1. Navegar a: **Compras → Boletas**

### Resultado esperado:
- ✅ Se muestra tabla con la boleta creada
- ✅ Columnas: ID, Proveedor, Nº Boleta, Fecha, Vencimiento, Total, Estado, Acciones
- ✅ Estado muestra badge **"Pendiente"** (amarillo)
- ✅ Total: **$1,160.00**

### Verificación en DB:
```sql
SELECT 
    pi.id,
    s.name as proveedor,
    pi.invoice_number,
    pi.invoice_date,
    pi.total_amount,
    pi.status
FROM purchase_invoice pi
JOIN supplier s ON pi.supplier_id = s.id
ORDER BY pi.created_at DESC;
```

---

## Caso 6: Ver Detalle de Boleta

### Pasos:
1. En listado de boletas, click en **"Ver detalle"** (ícono ojo)

### Resultado esperado:
- ✅ Muestra información general:
  - Proveedor, Nº Boleta, Fecha, Vencimiento, Estado
- ✅ Muestra tabla de ítems con:
  - Producto, SKU, UOM, Cantidad, Costo Unitario, Subtotal
- ✅ Total al final: **$1,160.00**
- ✅ Estado: **Pendiente**

---

## Caso 7: Boleta sin Ítems → Error

### Pasos:
1. Navegar a: **Compras → Nueva Boleta**
2. Llenar encabezado:
   - **Proveedor:** Distribuidora El Constructor
   - **Número de Boleta:** BOL-002
   - **Fecha Boleta:** (fecha actual)
3. **NO agregar ítems**
4. Click en **"Crear Boleta"**

### Resultado esperado:
- ❌ Mensaje de error: "Debe agregar al menos un ítem a la boleta"
- ✅ Permanece en formulario
- ✅ No se crea boleta en DB

### Verificación en DB:
```sql
SELECT COUNT(*) FROM purchase_invoice WHERE invoice_number = 'BOL-002';
-- Debe ser 0
```

---

## Caso 8: Duplicado invoice_number para mismo proveedor → Error

### Pasos:
1. Navegar a: **Compras → Nueva Boleta**
2. Llenar encabezado:
   - **Proveedor:** Ferretería Central S.A. (mismo que Caso 4)
   - **Número de Boleta:** BOL-001 (duplicado)
   - **Fecha Boleta:** (fecha actual)
3. Agregar 1 ítem cualquiera
4. Click en **"Crear Boleta"**

### Resultado esperado:
- ❌ Mensaje de error: "Ya existe una boleta con número 'BOL-001' para el proveedor 'Ferretería Central S.A.'"
- ✅ No se crea boleta duplicada

### Verificación en DB:
```sql
SELECT COUNT(*) FROM purchase_invoice 
WHERE supplier_id = (SELECT id FROM supplier WHERE name = 'Ferretería Central S.A.')
  AND invoice_number = 'BOL-001';
-- Debe ser 1 (solo la original)
```

---

## Caso 9: Filtros en Listado de Boletas

### Pasos:
1. Crear otra boleta con proveedor diferente (ej: Pinturas y Acabados Ltda.)
2. Navegar a: **Compras → Boletas**
3. Filtrar por **Proveedor:** Ferretería Central S.A.

### Resultado esperado:
- ✅ Solo muestra boletas de ese proveedor

4. Cambiar filtro a **Estado:** Pendiente

### Resultado esperado:
- ✅ Solo muestra boletas con estado PENDING

---

## Caso 10: Validación de Cantidad Negativa o Cero

### Pasos:
1. Navegar a: **Compras → Nueva Boleta**
2. Llenar encabezado
3. Intentar agregar ítem con **Cantidad: 0** o **Cantidad: -5**

### Resultado esperado:
- ❌ Mensaje de error: "La cantidad debe ser mayor a 0"
- ✅ No se agrega el ítem

---

## Caso 11: Validación de Producto Inactivo

### Pre-condición:
- Desactivar un producto desde **Productos → Editar → Desmarcar "Activo"**

### Pasos:
1. Navegar a: **Compras → Nueva Boleta**
2. Intentar agregar el producto inactivo

### Resultado esperado:
- ❌ El producto inactivo NO aparece en el dropdown de productos
- ✅ Solo productos activos son seleccionables

---

## Resumen de Verificaciones Críticas

### ✅ Checklist Final:

- [ ] Proveedores: CRUD completo funciona
- [ ] Boletas: Listado muestra todas las boletas
- [ ] Boletas: Filtros por proveedor y estado funcionan
- [ ] Boletas: Detalle muestra información completa
- [ ] Boletas: Creación con ítems funciona
- [ ] Boletas: Stock AUMENTA correctamente tras crear boleta
- [ ] Boletas: No permite crear sin ítems
- [ ] Boletas: No permite duplicar invoice_number para mismo proveedor
- [ ] Boletas: Validaciones de cantidad > 0
- [ ] Boletas: Solo productos activos son seleccionables
- [ ] Boletas: Estado inicial es PENDING, paid_at es NULL
- [ ] Stock Moves: Se crean con type=IN y reference_type=INVOICE
- [ ] Stock Move Lines: Se crean correctamente
- [ ] Transacciones: Si algo falla, rollback completo (no queda basura en DB)

---

## Queries Útiles para Debugging

### Ver todas las boletas con sus ítems:
```sql
SELECT 
    pi.id,
    pi.invoice_number,
    s.name as proveedor,
    pi.total_amount,
    pi.status,
    COUNT(pil.id) as num_items
FROM purchase_invoice pi
JOIN supplier s ON pi.supplier_id = s.id
LEFT JOIN purchase_invoice_line pil ON pi.id = pil.invoice_id
GROUP BY pi.id, s.name
ORDER BY pi.created_at DESC;
```

### Ver stock moves de tipo IN (compras):
```sql
SELECT 
    sm.id,
    sm.date,
    sm.type,
    sm.reference_type,
    sm.reference_id,
    sm.notes,
    COUNT(sml.id) as num_lines
FROM stock_move sm
LEFT JOIN stock_move_line sml ON sm.id = sml.stock_move_id
WHERE sm.type = 'IN'
GROUP BY sm.id
ORDER BY sm.date DESC;
```

### Ver historial de stock de un producto:
```sql
SELECT 
    sm.date,
    sm.type,
    sm.reference_type,
    sml.qty,
    p.name as producto
FROM stock_move_line sml
JOIN stock_move sm ON sml.stock_move_id = sm.id
JOIN product p ON sml.product_id = p.id
WHERE p.id = 1  -- Cambiar por ID del producto
ORDER BY sm.date DESC;
```

### Ver stock actual de todos los productos:
```sql
SELECT 
    p.id,
    p.name,
    p.sku,
    ps.on_hand_qty,
    p.active
FROM product p
LEFT JOIN product_stock ps ON p.id = ps.product_id
ORDER BY p.name;
```

---

## Notas Importantes

1. **Trigger de product_stock:** La base de datos tiene un trigger que actualiza `product_stock.on_hand_qty` automáticamente cuando se insertan `stock_move_line`. Verificar que funciona correctamente.

2. **Transacciones:** Todo el proceso de creación de boleta (invoice + lines + stock_move + stock_move_lines) debe ser transaccional. Si algo falla, nada se guarda.

3. **Estado PENDING:** Las boletas recién creadas siempre tienen status='PENDING' y paid_at=NULL. El pago se implementará en Fase 4.

4. **HTMX:** Los botones de "Agregar Ítem" y "Eliminar Ítem" usan HTMX para actualizar el draft sin recargar la página. Verificar que funciona correctamente.

5. **Session Draft:** Los ítems se guardan temporalmente en la sesión Flask hasta que se confirma la creación de la boleta.

---

## ¿Qué sigue? → FASE 4

En la Fase 4 se implementará:
- **Pago de boletas:** Marcar como PAID, guardar paid_at
- **Registro en finance_ledger:** EXPENSE al pagar boleta
- **Listado de boletas pendientes de pago**

