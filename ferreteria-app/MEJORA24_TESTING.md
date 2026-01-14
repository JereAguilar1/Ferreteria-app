# MEJORA 24 – Formato AR con 2 decimales en Boletas

Checklist de pruebas manuales para validar entrada, cálculo y visualización con formato argentino (miles con punto, decimales con coma y siempre 2 decimales).

## 1. Crear línea en draft (HTMX) con `1.234,56`
- Ir a `Boletas > Nueva`.
- Seleccionar proveedor y producto, qty `1`, unit_cost `1.234,56`.
- Al agregar ítem: la línea muestra `1.234,56` y subtotal correcto `1.234,56`.
- Total en tabla y modal de confirmación mantienen `1.234,56`.
- Crear boleta: en detalle se ve unit_cost y subtotal con 2 decimales, total igual.

## 2. Normalización de enteros `150` → `150,00`
- En el input de costo, escribir `150` y salir del campo (blur).
- El campo se autoformatea a `150,00`.
- Al agregar ítem, subtotal y total muestran `150,00`.

## 3. Normalización `150,5` → `150,50`
- Ingresar `150,5` en costo unitario.
- Al blur, el campo pasa a `150,50`.
- Subtotal/total reflejan `150,50`.

## 4. Rechazos de formato/valor
- Probar agregar línea con:
  - `1,5`
  - `abc`
  - `1.23,00`
  - `-10,00`
- Debe mostrar mensaje de error y no agregar la línea.

## 5. Edición de boleta (líneas y stock)
- Editar una boleta PENDING existente.
- Modificar costos con formato AR (ej: `1.500,00`), agregar y quitar líneas.
- Previsualizar: difs de totales con 2 decimales y deltas de stock correctos.
- Guardar: stock ajustado (altas/bajas) y totales recalculados a 2 decimales.

## 5.1. Cantidades en formato AR (edición)
- En editar boleta, modificar cantidad de una línea existente:
  - Escribir `1.500,5` → se formatea a `1.500,5` (mantiene decimales variables).
  - Escribir `1500` → se formatea a `1.500` (sin decimales).
  - Escribir `1.234,567` → se formatea a `1.234,567` (permite más de 2 decimales).
- Al agregar nueva línea desde el formulario:
  - Ingresar cantidad `2.500,75` en formato AR.
  - La línea se crea con cantidad formateada correctamente.
- Verificar que los cálculos de subtotales funcionan correctamente con cantidades en formato AR.
- Guardar boleta: las cantidades se guardan correctamente en la base de datos.

## 6. Render en UI
- En listas, detalle, modales de confirmación/pago/eliminación: unit_cost, subtotales y totales muestran `X.XXX,YY` siempre con dos decimales.

## 7. Backend / DB
- Crear y editar boleta con valores decimales; verificar en DB:
  - `purchase_invoice_line.unit_cost` y `line_total` guardan 2 decimales.
  - `purchase_invoice.total_amount` guarda 2 decimales.
- Validar que `create`/`update` rechazan costos con más de 2 decimales.
