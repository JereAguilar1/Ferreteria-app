# MEJORA C - Testing: Fondo de Comercio (Goodwill) en Balance

## Objetivo
Verificar que el sistema calcula y muestra correctamente el "Fondo de Comercio" (valoración del inventario a precio de venta) en la sección de Balance.

---

## Pre-requisitos
- Sistema levantado y funcionando
- MEJORA A (múltiples UOMs) implementada y funcionando
- Al menos 2-3 productos con stock > 0
- Cada producto debe tener al menos 1 UOM base con precio definido
- Usuario autenticado

---

## Test 1: Verificar cálculo básico de Goodwill

### Pasos:
1. Verificar productos existentes con stock:
   - Producto A: Stock 100 unidades, Precio base $50
   - Producto B: Stock 50 unidades, Precio base $200
2. Calcular manualmente el goodwill esperado:
   - Goodwill = (100 * 50) + (50 * 200) = 5.000 + 10.000 = **$15.000**
3. Ir a `/balance`

### Resultado esperado:
- ✅ Se muestra tarjeta "Fondo de Comercio (Goodwill)"
- ✅ Valor mostrado: **$15.000** (formato argentino)
- ✅ Texto descriptivo: "Valoración del inventario actual a precio de venta (unidad base)"
- ✅ Indicador: "Calculado al momento"

---

## Test 2: Goodwill con producto sin stock

### Pasos:
1. Crear un producto nuevo con:
   - Stock: 0
   - Precio base: $1.000
2. Ir a `/balance`

### Resultado esperado:
- ✅ El producto con stock 0 **NO** suma al goodwill
- ✅ Goodwill sigue siendo $15.000 (del Test 1)

---

## Test 3: Goodwill con producto inactivo

### Pasos:
1. Desactivar Producto A (que tiene stock 100)
2. Ir a `/balance`

### Resultado esperado:
- ✅ Producto A (inactivo) **NO** suma al goodwill
- ✅ Goodwill ahora es: 50 * 200 = **$10.000**
- ✅ Solo productos activos con stock > 0 se incluyen

---

## Test 4: Goodwill con múltiples UOMs (usa precio base)

### Pasos:
1. Producto C con múltiples UOMs:
   - UOM Base: Metro (m), Precio $100, Factor 1, is_base=true
   - UOM Secundaria: Rollo, Precio $9.500, Factor 100, is_base=false
2. Stock actual: 150 m (unidad base)
3. Ir a `/balance`

### Resultado esperado:
- ✅ Goodwill usa **solo el precio de la UOM base**
- ✅ Producto C suma: 150 * 100 = **$15.000**
- ✅ **NO** usa el precio de "Rollo" ($9.500)

---

## Test 5: Actualización de goodwill tras venta

### Pasos:
1. Goodwill inicial: $25.000 (ejemplo acumulado)
2. Realizar una venta de:
   - Producto B: 10 unidades @ $200 (precio base)
3. Stock de Producto B baja de 50 a 40
4. Ir a `/balance`

### Resultado esperado:
- ✅ Goodwill disminuye en: 10 * 200 = $2.000
- ✅ Nuevo goodwill: $25.000 - $2.000 = **$23.000**
- ✅ El cálculo es dinámico y refleja el stock actual

---

## Test 6: Actualización de goodwill tras compra

### Pasos:
1. Goodwill inicial: $23.000 (del Test 5)
2. Crear una boleta de compra:
   - Producto B: 20 unidades @ $150 (costo unitario)
3. Stock de Producto B sube de 40 a 60
4. Ir a `/balance`

### Resultado esperado:
- ✅ Goodwill aumenta en: 20 * 200 = $4.000 (usa **precio de venta**, no costo)
- ✅ Nuevo goodwill: $23.000 + $4.000 = **$27.000**
- ✅ Nota: El goodwill usa `sale_price`, no `unit_cost`

---

## Test 7: Goodwill con stock decimal

### Pasos:
1. Producto D:
   - Stock: 15.5 unidades
   - Precio base: $80
2. Ir a `/balance`

### Resultado esperado:
- ✅ Goodwill suma: 15.5 * 80 = **$1.240**
- ✅ Soporta cantidades decimales correctamente

---

## Test 8: Goodwill con múltiples productos

### Pasos:
1. Estado actual:
   - Producto A (inactivo): No suma
   - Producto B: 60 unidades @ $200 = $12.000
   - Producto C: 150 m @ $100 = $15.000
   - Producto D: 15.5 unidades @ $80 = $1.240
2. Ir a `/balance`

### Resultado esperado:
- ✅ Goodwill total: $12.000 + $15.000 + $1.240 = **$28.240**
- ✅ Formato argentino: **$28.240**

---

## Test 9: Goodwill sin productos con stock

### Pasos:
1. Vender todo el stock de todos los productos
2. Verificar que todos los productos tienen `on_hand_qty = 0`
3. Ir a `/balance`

### Resultado esperado:
- ✅ Goodwill: **$0** o **$0,00**
- ✅ No muestra error
- ✅ Tarjeta sigue visible con valor $0

---

## Test 10: Verificar query SQL del goodwill

### Pasos:
1. Ejecutar query manual en DB:

```sql
SELECT 
    SUM(ps.on_hand_qty * pup.sale_price) as goodwill
FROM product_stock ps
JOIN product_uom_price pup ON pup.product_id = ps.product_id
JOIN product p ON p.id = ps.product_id
WHERE ps.on_hand_qty > 0
  AND p.active = true
  AND pup.is_base = true;
```

2. Comparar resultado con el valor mostrado en `/balance`

### Resultado esperado:
- ✅ El valor de la query coincide exactamente con el mostrado en la UI
- ✅ Diferencia máxima aceptable: $0,01 (por redondeo)

---

## Test 11: Formato argentino en goodwill

### Pasos:
1. Producto con stock que genere un goodwill de $123.456,78
2. Ir a `/balance`

### Resultado esperado:
- ✅ Se muestra como: **$123.456,78**
- ✅ Punto para miles, coma para decimales
- ✅ Si el valor es entero (ej: $100.000,00), puede mostrarse como **$100.000**

---

## Test 12: Goodwill no afecta ledger

### Pasos:
1. Ir a `/balance/ledger` (Libro Mayor)
2. Buscar entradas de tipo "Goodwill" o "Fondo de Comercio"

### Resultado esperado:
- ✅ **NO** debe haber entradas en `finance_ledger` relacionadas con goodwill
- ✅ El goodwill es solo un indicador calculado, no un movimiento contable

---

## Test 13: Goodwill con cambio de precio de venta

### Pasos:
1. Producto E: Stock 100, Precio base $50
2. Goodwill inicial incluye: 100 * 50 = $5.000
3. Editar Producto E y cambiar precio base a $60
4. Ir a `/balance`

### Resultado esperado:
- ✅ Goodwill ahora incluye: 100 * 60 = $6.000
- ✅ Incremento de $1.000 en el goodwill total
- ✅ El cálculo usa siempre el precio actual

---

## Resumen de Validaciones Críticas

| # | Validación | Esperado |
|---|------------|----------|
| 1 | Goodwill calcula correctamente (stock * precio_base) | ✅ Correcto |
| 2 | Productos con stock = 0 no suman | ✅ No suman |
| 3 | Productos inactivos no suman | ✅ No suman |
| 4 | Usa precio de UOM base (is_base=true) | ✅ Correcto |
| 5 | Goodwill se actualiza tras venta | ✅ Disminuye |
| 6 | Goodwill se actualiza tras compra | ✅ Aumenta |
| 7 | Soporta cantidades decimales | ✅ Correcto |
| 8 | Formato argentino (punto miles, coma decimales) | ✅ Correcto |
| 9 | Goodwill = 0 cuando no hay stock | ✅ Muestra $0 |
| 10 | No crea entradas en finance_ledger | ✅ Solo indicador |
| 11 | Se actualiza con cambios de precio | ✅ Usa precio actual |
| 12 | Tarjeta visible en todas las vistas de balance | ✅ Visible |

---

## Queries útiles para verificación

```sql
-- Ver goodwill detallado por producto
SELECT 
    p.name,
    ps.on_hand_qty as stock,
    pup.sale_price as precio_base,
    (ps.on_hand_qty * pup.sale_price) as valor_producto,
    p.active
FROM product p
JOIN product_stock ps ON ps.product_id = p.id
JOIN product_uom_price pup ON pup.product_id = p.id AND pup.is_base = true
WHERE ps.on_hand_qty > 0
ORDER BY valor_producto DESC;

-- Goodwill total
SELECT 
    SUM(ps.on_hand_qty * pup.sale_price) as goodwill_total
FROM product_stock ps
JOIN product_uom_price pup ON pup.product_id = ps.product_id
JOIN product p ON p.id = ps.product_id
WHERE ps.on_hand_qty > 0
  AND p.active = true
  AND pup.is_base = true;

-- Productos que contribuyen al goodwill
SELECT 
    p.id,
    p.name,
    p.active,
    ps.on_hand_qty,
    pup.sale_price,
    pup.is_base
FROM product p
JOIN product_stock ps ON ps.product_id = p.id
JOIN product_uom_price pup ON pup.product_id = p.id
WHERE ps.on_hand_qty > 0 AND p.active = true;
```

---

## Notas Finales
- El goodwill es un indicador de valoración, **no** un movimiento contable
- Se calcula en tiempo real cada vez que se carga `/balance`
- Usa siempre el precio de la UOM base (`is_base=true`)
- Solo incluye productos activos con stock > 0
- El valor puede cambiar dinámicamente con ventas, compras y ajustes de precio
- Es útil para conocer el "potencial de ingresos" del inventario actual
