# Specification: Mover Costo de Flete de Ventas a Compras

## Overview
El proyecto actual implementó por error el concepto de "Costo de Flete" en el módulo de Ventas (`Sale`). Este track tiene como objetivo revertir por completo los cambios realizados en el módulo de Ventas (Base de Datos, Backend y Frontend) y, en su lugar, implementar la misma funcionalidad en el módulo de Compras (`PurchaseInvoice`). Esto se debe a que el negocio asume los costos de flete provenientes de los proveedores, pero no cobra fletes en las ventas a clientes.

## Functional Requirements
1. **Reversión en Ventas:**
   - Eliminar el campo `shipping_cost` de la tabla `sale` en la base de datos (y del script de esquema).
   - Revertir los cambios en el trigger `chk_sale_total_matches_lines` para que vuelva a validar solo `total = sum(line_total)`.
   - Eliminar el campo `shipping_cost` del modelo SQLAlchemy `Sale`.
   - Quitar la lógica de cálculo de flete en `sales_service.py` (`confirm_sale`).
   - Remover el campo de ingreso de flete y el desglose de totales en las vistas HTMX/Jinja de ventas (`_cart.html`, `_confirm_modal.html`, `detail.html`).

2. **Implementación en Compras:**
   - Agregar el campo `shipping_cost` (Numeric, default 0.00) a la tabla `purchase_invoice` y al script de esquema.
   - Modificar el trigger `chk_invoice_total_matches_lines` (o similar) para que valide `total = sum(line_total) + shipping_cost`.
   - Agregar el atributo `shipping_cost` al modelo SQLAlchemy `PurchaseInvoice`.
   - Modificar el backend de compras (e.g., `purchase_service.py` o similar) para sumar `shipping_cost` al cálculo total de la factura.
   - Modificar el frontend de compras para incluir un campo numérico opcional de "Flete" antes de confirmar la compra y actualizar el desglose de totales ("Subtotal", "Flete", "Total") en las vistas de registro y detalles de compra.

## Acceptance Criteria
- [ ] La creación de ventas vuelve a funcionar de forma estándar sin solicitar ni registrar fletes.
- [ ] La base de datos no contiene referencias a fletes en la tabla de ventas.
- [ ] Al crear una compra, el usuario puede ingresar un costo de flete opcional.
- [ ] El costo de flete introducido en la compra se suma al "Total" y se registra correctamente en la base de datos.
- [ ] La visualización de detalle de una factura de compra pasada y nueva muestra el desglose del Subtotal y del Flete sumados en el Total.
- [ ] Los tests automatizados actualizados/nuevos corren exitosamente (sin errores en ventas, testeando flete en compras).

## Out of Scope
- Prorrateo del costo del flete para afectar el "precio de costo" individual de cada producto. El flete solo afectará el total general a pagar de la factura.
