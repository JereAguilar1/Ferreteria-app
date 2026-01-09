# Sistema de Ferretería - Aplicación Web

Sistema web completo para gestión de ferretería con control de stock, ventas, compras y balance financiero.

## Stack Técnico

- **Backend**: Python 3.13+
- **Framework**: Flask 3.0.0
- **Templates**: Jinja2
- **UX Dinámica**: HTMX
- **Base de Datos**: PostgreSQL 16
- **ORM**: SQLAlchemy 2.0.36
- **Migraciones**: Alembic (opcional)

## Requisitos Previos

### Para Desarrollo Local
- Python 3.11 o superior
- PostgreSQL 16

### Para Docker (Recomendado)
- Docker Desktop o Docker Engine
- Docker Compose V2

## Configuración Local

### 1. Clonar el repositorio

```bash
cd c:\jere\Ferreteria\ferreteria-app
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=ferreteria
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123

# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key-change-in-production
```

### 4. Iniciar la base de datos PostgreSQL

Si usas Docker:

```bash
cd ..\Ferreteria-db
docker compose up -d
```

Verificar que el contenedor esté corriendo:

```bash
docker ps
```

### 5. Ejecutar la aplicación

```bash
python app.py
```

La aplicación estará disponible en:
- http://127.0.0.1:5000 (página principal)
- http://127.0.0.1:5000/health (verificación de salud y conexión DB)

---

## 🐳 Configuración con Docker (Recomendado)

### Ventajas de Docker
- ✅ No requiere instalar Python ni PostgreSQL localmente
- ✅ Entorno consistente en cualquier sistema operativo
- ✅ Fácil de iniciar, detener y reiniciar
- ✅ Aislamiento completo del sistema host

### Modo A: App + PostgreSQL en Docker (Todo en Contenedores)

Este es el modo más simple y recomendado para desarrollo y testing.

#### 1. Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp env.example .env

# Editar .env si necesitas cambiar algo (opcional)
# Los valores por defecto están listos para usar
```

#### 2. Iniciar Todo con Docker Compose

```bash
# Construir e iniciar ambos contenedores (app + db)
docker compose up --build

# O en modo detached (background)
docker compose up --build -d
```

#### 3. Verificar que Funciona

```bash
# Ver logs
docker compose logs -f web

# Verificar health
curl http://localhost:5000/health
```

#### 4. Acceder a la Aplicación

- **Aplicación:** http://localhost:5000
- **Health Check:** http://localhost:5000/health

#### 5. Inicializar Base de Datos

**Opción A: Restaurar desde backup**
```bash
# Copiar backup SQL al contenedor
docker compose cp backup.sql db:/tmp/

# Restaurar
docker compose exec db psql -U ferreteria -d ferreteria -f /tmp/backup.sql
```

**Opción B: Ejecutar seeds manualmente**
```bash
# Desde tu terminal local
docker compose exec web python seed_initial_data.py
```

**Opción C: Conectar con pgAdmin/DBeaver**
- Host: `localhost`
- Port: `5432`
- Database: `ferreteria`
- User: `ferreteria`
- Password: `ferreteria`

#### 6. Comandos Útiles

```bash
# Ver logs en tiempo real
docker compose logs -f

# Ver solo logs de la app
docker compose logs -f web

# Ver solo logs de la DB
docker compose logs -f db

# Entrar al contenedor de la app
docker compose exec web bash

# Entrar a psql
docker compose exec db psql -U ferreteria -d ferreteria

# Reiniciar servicios
docker compose restart

# Detener servicios
docker compose down

# Detener y eliminar volúmenes (⚠️ BORRA DATOS)
docker compose down -v

# Reconstruir imagen
docker compose build --no-cache
```

---

### Modo B: Solo App en Docker + PostgreSQL Externo

Si ya tienes PostgreSQL corriendo localmente o en un servidor externo.

#### 1. Configurar Variables de Entorno

Edita `.env`:

```env
# Para Windows/Mac con Docker Desktop
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=ferreteria
DB_USER=tu_usuario
DB_PASSWORD=tu_password

# Para Linux
# DB_HOST=172.17.0.1
# O la IP de tu host

SECRET_KEY=change-me
FLASK_DEBUG=0
```

#### 2. Iniciar Solo la App

```bash
# Iniciar solo el servicio web (sin db)
docker compose up web --build

# O en detached
docker compose up web --build -d
```

#### 3. Verificar Conexión

```bash
# La app debe conectarse a tu PostgreSQL externo
curl http://localhost:5000/health
```

---

### Troubleshooting Docker

#### Error: "Connection refused" o "could not connect to server"

**Problema:** La app no puede conectarse a la base de datos.

**Soluciones:**

1. **Modo A (DB en Docker):**
```bash
# Verificar que el contenedor db está corriendo
docker compose ps

# Ver logs de la DB
docker compose logs db

# Verificar health de DB
docker compose exec db pg_isready -U ferreteria
```

2. **Modo B (DB externa):**
- Verificar que `DB_HOST` está correctamente configurado
- Windows/Mac: usar `host.docker.internal`
- Linux: usar `172.17.0.1` o IP del host
- Verificar que el firewall permite conexiones al puerto de PostgreSQL

#### Error: "port is already allocated"

**Problema:** El puerto 5000 o 5432 ya está en uso.

**Solución:**
```bash
# Cambiar puerto en docker-compose.yml
# Para la app, cambiar:
ports:
  - "8000:5000"  # Acceder en http://localhost:8000

# Para la DB, cambiar:
ports:
  - "5433:5432"  # Y actualizar DB_PORT=5433 en .env
```

#### Error: Los scripts de init no se ejecutan

**Problema:** La base de datos ya tiene un volumen existente.

**Solución:**
```bash
# Eliminar volumen y recrear
docker compose down -v
docker compose up --build
```

#### Error: "exec format error" o "no such file"

**Problema:** Problemas con line endings en Windows.

**Solución:**
```bash
# Convertir line endings si es necesario
git config core.autocrlf input
git rm --cached -r .
git reset --hard
```

#### Ver estado de salud de contenedores

```bash
# Ver health checks
docker compose ps

# Inspeccionar un contenedor
docker inspect ferreteria-web

# Ver uso de recursos
docker stats
```

---

### Datos Persistentes

Los datos de PostgreSQL se guardan en un volumen Docker llamado `postgres_data`.

```bash
# Ver volúmenes
docker volume ls

# Inspeccionar volumen
docker volume inspect ferreteria-app_postgres_data

# Backup de datos
docker compose exec db pg_dump -U ferreteria -d ferreteria > backup_$(date +%Y%m%d).sql

# Restore de datos
docker compose exec -T db psql -U ferreteria -d ferreteria < backup.sql
```

#### Resetear Base de Datos Completamente

```bash
# ⚠️ ADVERTENCIA: Esto BORRA TODOS LOS DATOS

# Detener y eliminar volúmenes
docker compose down -v

# Iniciar de nuevo (DB vacía)
docker compose up --build

# Restaurar backup o ejecutar seeds
```

---

## Estructura del Proyecto

```
ferreteria-app/
├── app/
│   ├── __init__.py           # Factory de la aplicación
│   ├── database.py           # Configuración de SQLAlchemy
│   ├── blueprints/           # Módulos de rutas
│   │   ├── main.py           # Rutas principales y health check
│   │   └── ...               # Otros blueprints (próximamente)
│   ├── models/               # Modelos SQLAlchemy
│   ├── services/             # Lógica de negocio y transacciones
│   ├── templates/            # Plantillas Jinja2
│   └── static/               # CSS, JS, imágenes
├── app.py                    # Punto de entrada
├── config.py                 # Configuración
├── requirements.txt          # Dependencias Python
├── .env                      # Variables de entorno (no versionado)
└── README.md                 # Este archivo
```

## Verificación de Funcionamiento

### Health Check

Para verificar que la aplicación está funcionando y conectada a la base de datos:

```bash
curl http://127.0.0.1:5000/health
```

O con Python:

```bash
python -c "import urllib.request; import json; response = urllib.request.urlopen('http://127.0.0.1:5000/health'); print(json.loads(response.read().decode()))"
```

Respuesta esperada:

```json
{
  "status": "healthy",
  "database": "connected",
  "message": "Database connection successful"
}
```

## Estado del Proyecto

### ✅ Fase 0: Bootstrapping (COMPLETADA)
- [x] Estructura del proyecto Flask
- [x] Configuración de dependencias
- [x] Configuración de variables de entorno
- [x] Conexión a PostgreSQL
- [x] Endpoint `/health` funcional

### ✅ Fase 1: Módulo de Productos + Stock (COMPLETADA)
- [x] Modelos SQLAlchemy (UOM, Category, Product, ProductStock)
- [x] Blueprint catalog con rutas CRUD
- [x] Listado de productos con stock actual
- [x] Búsqueda por nombre/SKU/barcode
- [x] Productos sin stock en gris con badge
- [x] Validaciones server-side
- [x] Formularios de creación/edición
- [x] Activar/desactivar productos
- [x] UI con Bootstrap 5

Ver [FASE1_TESTING.md](FASE1_TESTING.md) para instrucciones de prueba.

### ✅ Fase 2: Módulo de Ventas - POS (COMPLETADA)
- [x] Modelos SQLAlchemy (Sale, SaleLine, StockMove, StockMoveLine, FinanceLedger)
- [x] Blueprint sales con POS completo
- [x] Carrito en Flask session
- [x] Búsqueda de productos para venta
- [x] HTMX para agregar/actualizar/remover del carrito
- [x] Servicio transaccional `confirm_sale` con locking
- [x] Descuento automático de stock al confirmar
- [x] Registro de ingreso en finance_ledger
- [x] Validaciones de stock en tiempo real
- [x] UI responsive con Bootstrap 5

Ver [FASE2_TESTING.md](FASE2_TESTING.md) para instrucciones de prueba.

### ✅ Fase 3: Módulo de Compras/Boletas (COMPLETADA)
- [x] Modelos SQLAlchemy (Supplier, PurchaseInvoice, PurchaseInvoiceLine)
- [x] Blueprint suppliers con CRUD completo
- [x] Blueprint invoices con gestión de boletas
- [x] Nueva boleta con ítems obligatorios (draft en session)
- [x] Servicio transaccional `create_invoice_with_lines`
- [x] Aumento automático de stock (StockMove IN)
- [x] Validaciones: mínimo 1 ítem, qty > 0, producto activo
- [x] Validación de duplicado (supplier_id + invoice_number)
- [x] UI con HTMX para agregar/remover ítems
- [x] Listado con filtros (proveedor, estado)
- [x] Detalle de boleta
- [x] Estado PENDING por defecto (paid_at NULL)

Ver [FASE3_TESTING.md](FASE3_TESTING.md) para instrucciones de prueba.

### ✅ Fase 4: Pago de Boletas (COMPLETADA)
- [x] Servicio transaccional `pay_invoice` con lock FOR UPDATE
- [x] Ruta POST `/invoices/<id>/pay`
- [x] Actualización de boleta: status=PAID, paid_at=fecha
- [x] Registro de egreso en finance_ledger (EXPENSE, INVOICE_PAYMENT)
- [x] Validaciones: solo PENDING, fecha requerida, no duplicar
- [x] UI: formulario de pago en detalle de boleta
- [x] Filtro "Solo Pendientes" en listado
- [x] Botón "Pagar" para boletas pendientes
- [x] Transaccionalidad completa (rollback si falla)

Ver [FASE4_TESTING.md](FASE4_TESTING.md) para instrucciones de prueba.

### ✅ Fase 5: Balance Financiero (COMPLETADA)
- [x] Servicio `balance_service` con `get_balance_series`
- [x] Consultas eficientes con `date_trunc` (day/month/year)
- [x] Blueprint balance con ruta `/balance`
- [x] Vistas: Diaria, Mensual, Anual (tabs)
- [x] Filtros por rango de fechas (start/end)
- [x] Cálculo de ingresos, egresos y neto por período
- [x] Tarjetas de resumen con totales
- [x] Libro Mayor (ledger) para auditoría (`/balance/ledger`)
- [x] Movimientos manuales (INCOME/EXPENSE) con categoría y notas
- [x] Validaciones: start <= end, amount > 0
- [x] UI con Bootstrap y tabs interactivos

Ver [FASE5_TESTING.md](FASE5_TESTING.md) para instrucciones de prueba.

### ✅ Fase 6: Dockerización Completa (COMPLETADA)
- [x] Dockerfile con Python 3.11-slim + gunicorn
- [x] docker-compose.yml con servicios web y db
- [x] Healthchecks para web y db
- [x] Volumen persistente para PostgreSQL
- [x] Soporte para Modo A (todo en Docker) y Modo B (DB externa)
- [x] Variables de entorno flexibles (DATABASE_URL, DB_*, POSTGRES_*)
- [x] Estructura db/init para scripts de inicialización
- [x] .dockerignore optimizado
- [x] Usuario no-root por seguridad
- [x] README completo con instrucciones Docker
- [x] Troubleshooting y comandos útiles

Ver [FASE6_TESTING.md](FASE6_TESTING.md) para instrucciones de prueba Docker.

---

## 🎉 Proyecto Completado

Todas las fases del proyecto han sido implementadas exitosamente:
- ✅ **Fase 0:** Bootstrapping
- ✅ **Fase 1:** Módulo de Productos
- ✅ **Fase 2:** Módulo de Ventas (POS)
- ✅ **Fase 3:** Módulo de Compras/Boletas
- ✅ **Fase 4:** Pago de Boletas
- ✅ **Fase 5:** Balance Financiero
- ✅ **Fase 6:** Dockerización Completa

El sistema está listo para producción o desarrollo continuo.

## Notas de Desarrollo

- La aplicación usa `pool_pre_ping=True` en SQLAlchemy para verificar las conexiones antes de usarlas
- El modo debug está habilitado para desarrollo (`FLASK_DEBUG=1`)
- No hay autenticación por el momento (se agregará en futuras fases)

## Troubleshooting

### Error de conexión a la base de datos

Verificar que:
1. PostgreSQL está corriendo: `docker ps`
2. Las credenciales en `.env` son correctas
3. El puerto en `.env` coincide con el puerto mapeado en Docker

### Error de importación de módulos

Reinstalar dependencias:

```bash
pip install --upgrade -r requirements.txt
```

---

**Versión**: 0.1.0 - Fase 0 Completada  
**Última actualización**: Enero 2026

