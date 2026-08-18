# Specification: Agregar Costo de Flete a Boleta

## Overview
Esta funcionalidad permite a los usuarios registrar el costo de envío (flete) al momento de crear una boleta/venta, sumando este valor al total general a pagar por el cliente. Esto mejorará la precisión de los cobros y la transparencia en el detalle de las transacciones.

## Functional Requirements
- Agregar un campo numérico opcional para el "Costo de Flete" (con valor por defecto 0) en la interfaz (UI) de creación de boletas.
- En el resumen de la boleta (tanto al momento de la creación como en la vista de detalle), mostrar un desglose claro de los valores: "Subtotal" (suma de productos), "Flete" y "Total" (Subtotal + Flete).
- Actualizar la lógica del backend para recibir, validar y sumar el costo de flete al calcular el total de la transacción.

## Database Changes
- Añadir una nueva columna (ej. `shipping_cost` o `flete`) de tipo numérico a la tabla que almacena las Boletas/Ventas en la base de datos PostgreSQL mediante una migración (Alembic).

## Non-Functional Requirements
- Si el frontend realiza cálculos en vivo, estos deben actualizar el "Total" dinámicamente cuando el usuario modifique el valor en el campo "Costo de Flete", respetando la arquitectura de la aplicación (HTMX o Vanilla JS según corresponda).

## Acceptance Criteria
- [ ] Un usuario puede ingresar un monto de flete mayor o igual a cero al crear una nueva boleta.
- [ ] Si el campo no se modifica o queda vacío, el sistema asume que el costo de flete es 0.
- [ ] El sistema calcula el "Total" correctamente: Subtotal de los ítems + Flete.
- [ ] El desglose (Subtotal, Flete, Total) es claramente visible en la interfaz de creación y en cualquier vista de detalle posterior.
- [ ] El dato de flete se guarda en la base de datos y se recupera intacto al consultar el histórico de la venta.

## Out of Scope
- Configuración de tarifas de envío automáticas según zonas, comunas o distancias.
- Gestión de múltiples tipos de cargos adicionales (se limitará exclusivamente a flete).
