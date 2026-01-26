# CONTEXTO MAESTRO: Sistema de Gestión de Stock (Ferretería / SaaS)

> **ARCHIVO DE AUTORIDAD TÉCNICA**
> Este documento define la verdad absoluta sobre la arquitectura, alcance y reglas del proyecto. Debe ser consultado y respetado por cualquier agente de IA que trabaje en este código.

────────────────────────────────────────────────────────────────────────────────
## 1. Visión General

Este proyecto es un **Sistema de Gestión de Stock y Ventas** diseñado con el siguiente proposito:
1.  **Solución Inmediata**: Operar una ferretería minorista real con control estricto de inventario.escalable.

### Usuario Objetivo
-   **Perfil**: Dueño o empleado de ferretería / corralón.
-   **Entorno**: Mostrador de atención con alto tráfico.
-   **Necesidad**: Rapidez en la carga de ventas, búsqueda ágil de productos y confianza absoluta en la cantidad de stock real.

### Principios Fundamentales
-   **Velocidad Operativa**: La UI debe permitir vender en segundos.
-   **Integridad de Datos**: El stock es sagrado. No se permiten inconsistencias matemáticas.
-   **Evolutividad**: El código nace modular para soportar múltiples inquilinos (tenants) en el futuro sin reescribir el núcleo.

────────────────────────────────────────────────────────────────────────────────
## 2. Alcance Funcional Actual

### 📦 Gestión de Productos
-   **Identificación**: SKU, Código de Barras, Nombre, Categoría.
-   **Unidades de Medida (UOM)**: Soporte avanzado para múltiples unidades (ej. vender cables por metro o por rollo).
-   **Precios**: Cada producto tiene una lista de precios por unidad de medida.
-   **Faltantes**: Registro de "Solicitudes de Productos Faltantes" para capturar demanda insatisfecha.

### 📊 Gestión de Stock
-   **Tiempo Real**: Tabla de snapshot (`product_stock`) actualizada por triggers.
-   **Movimientos**: Todo cambio de stock genera u registro en `stock_move` (IN, OUT, ADJUST).
-   **Trazabilidad**: Referencias cruzadas a Ventas o Compras.

### 💰 Ventas y Presupuestos
-   **Venta Rápida**: Carrito de compras, cálculo de totales, validación de stock.
-   **Presupuestos (Quotes)**: Ciclo de vida completo (Borrador -> Enviado -> Aceptado -> Convertido en Venta).
-   **Validaciones**: Triggers de base de datos aseguran que los totales coincidan con las líneas.

### 🚚 Compras y Proveedores
-   **Proveedores**: Gestión de datos maestros.
-   **Facturas de Compra**: Registro de facturas con detalle de ítems.
-   **Cuentas Corrientes**: Registro de pagos parciales (`purchase_invoice_payment`) y estado de deuda.

### 📉 Finanzas
-   **Ledger**: Libro diario unificado (`finance_ledger`) para ingresos y egresos de caja.

────────────────────────────────────────────────────────────────────────────────
## 3. Reglas de Negocio Clave

1.  **Integridad de Stock**:
    -   El stock físico (`on_hand_qty`) se calcula exclusivamente a partir de movimientos (`stock_move`).
    -   Está prohibido modificar `product_stock` directamente desde la aplicación; solo los triggers de DB pueden hacerlo.
    -   **Stock Negativo**: No se permite stock negativo (validado por constraint `CHECK` y lógica en función `apply_stock_delta`, salvo configuraciones específicas en transiciones).

2.  **Unidades de Medida**:
    -   Todo producto debe tener **una y solo una** Unidad Base (`is_base = true`).
    -   Las conversiones de precios y stock se normalizan internamente, pero se visualizan en la unidad seleccionada.

3.  **Ventas y Facturación**:
    -   Una venta (`sale`) o factura (`purchase_invoice`) **DEBE** tener al menos una línea de detalle. (Validado por Trigger Deferrable).
    -   El total de la cabecera **DEBE** coincidir matemáticamente con la suma de los detalles. (Validado por Trigger).
    -   Una Presupuesto Aceptado se convierte en Venta y reserva/descuenta stock en ese momento.

4.  **Auditoría**:
    -   Los ajustes manuales de stock deben tener una nota explicativa obligatoria.
    -   No se borran registros de ventas confirmadas (soft delete o anulación con contra-movimiento).

────────────────────────────────────────────────────────────────────────────────
## 4. Modelo de Datos (Conceptual)

El esquema de base de datos (`PostgreSQL`) es el corazón de la lógica de negocio.

-   **`product`**: Maestro de productos.
-   **`uom`**: Maestro de unidades de medida (Unidad, Metro, Kilo, Litro).
-   **`product_uom_price`**: Tabla pivote clave. Define qué unidades tiene activas un producto y sus precios específicos.
-   **`product_stock`**: *Snapshot* de solo lectura rápida para saber "cuánto hay".
-   **`stock_move`** / **`stock_move_line`**: La verdad histórica. Inserciones aquí disparan actualizaciones en `product_stock`.
-   **`sale`** / **`sale_line`**: Cabecera y detalle de ventas.
-   **`quote`** / **`quote_line`**: Presupuestos previos a la venta.
-   **`supplier`** / **`purchase_invoice`**: Gestión de compras.
-   **`finance_ledger`**: Caja chica y movimientos financieros.

────────────────────────────────────────────────────────────────────────────────
## 5. Arquitectura Técnica

### Stack Tecnológico
-   **Backend**: Python 3.x + Flask.
-   **Base de Datos**: PostgreSQL 13+ (Lógica pesada en PL/pgSQL: Triggers, Functions).
-   **Frontend**: Server-side rendering con **Jinja2** + HTML5 + CSS (Vanilla/Bootstrap). JS mínimo para interactividad (HTMX o Vanilla). **NO SPA**.
-   **Infraestructura**: Containerización total con Docker y Docker Compose.

### Filosofía de Arquitectura
-   **"Thick Database"**: Las reglas críticas de integridad (stock, totales, restricciones) residen en la base de datos, no en el código Python. Esto previene corrupción de datos por errores de aplicación.
-   **Monolito Modular**: Estructura de carpetas organizada por dominios (blueprints) para fácil extracción futura a servicios si fuera necesario (aunque no es el objetivo actual).

────────────────────────────────────────────────────────────────────────────────
## 6. Estado Actual del Proyecto

-   ✅ **Esquema de Base de Datos**: Definido, estable y con triggers complejos de validación.
-   ✅ **Gestión de Stock**: Funcional (entradas/salidas/ajustes).
-   ✅ **Ventas**: Flujo básico operativo.
-   ✅ **Compras**: Registro de facturas y proveedores.
-   Construction **Reportes**: Básicos implementados.

────────────────────────────────────────────────────────────────────────────────
## 7. Roadmap Evolutivo

1.  **Fase 1: MVP Local (ACTUAL)**
    -   Estabilizar flujo de caja y control de inventario para un solo comercio.
    -   Refinar UX de carga rápida.

────────────────────────────────────────────────────────────────────────────────
## 8. Convenciones y Filosofía de Desarrollo

-   **Mantenibilidad > Astucia**: Código aburrido y legible es mejor que "trucos" de una línea.
-   **Español en Código**:
    -   Comentarios y Documentación: **Español**.
    -   Variables y Tablas de BD: **Inglés** (ej. `stock_move`, `get_product_by_id`).
-   **Testing**:
    -   Pruebas unitarias para reglas de negocio complejas.
    -   Pruebas de integración para flujos de base de datos (verificar que los triggers disparen).

────────────────────────────────────────────────────────────────────────────────
## 9. Glosario del Dominio

| Término | Definición |
| :--- | :--- |
| **UOM** | Unit of Measure (Unidad de Medida). |
| **Snapshot** | Estado actual de una variable calculado a partir de un historial (ej. `product_stock`). |
| **Movimiento de Ajuste** | Corrección manual de stock por robo, pérdida o error de conteo. |
| **Ledger** | Libro mayor financiero donde se asientan todos los movimientos de dinero. |
| **Precio Base** | Precio asociado a la unidad principal del producto. |

────────────────────────────────────────────────────────────────────────────────
## 10. Instrucciones para IAs (META-INSTRUCCIONES)

Al recibir este archivo como contexto, tú (IA) debes:

1.  **Asumir Autoridad**: Este archivo mata cualquier suposición previa. Si el código dice algo diferente a este archivo en un aspecto arquitectónico, **prioriza este archivo** y sugiere corregir el código.
2.  **Respetar la DB**: Nunca sugieras lógica de aplicación que duplique o ignore los Triggers existentes (ej. no calcules stock en Python, lee `product_stock`).
3.  **No Sobre-ingenierizar**: No sugieras React, Microservicios o Kubernetes a menos que se justifique explícitamente por un cambio de escala masivo. Mantén el stack Flask/Postgres/Render-side.
4.  **Preguntar ante Duda**: Si una solicitud del usuario parece violar una regla de este contexto (ej. "Permitir stock negativo"), advierte sobre la contradicción antes de proceder.

**FIN DEL CONTEXTO MAESTRO**
