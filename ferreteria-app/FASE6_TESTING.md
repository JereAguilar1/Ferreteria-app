# FASE 6 - Testing: Dockerización Completa

## Objetivo
Verificar que la aplicación funciona correctamente con Docker en ambos modos:
- **Modo A:** App + PostgreSQL en contenedores
- **Modo B:** Solo app en contenedor + PostgreSQL externo

---

## Pre-requisitos

1. **Docker Desktop o Docker Engine instalado**
```bash
docker --version
docker compose version
```

2. **Código fuente descargado**
```bash
cd c:\jere\Ferreteria\ferreteria-app
```

---

## MODO A: App + PostgreSQL en Docker

### Caso 1: Iniciar Sistema Completo (Primera Vez)

#### Pasos:
1. **Configurar variables de entorno:**
```bash
# Copiar archivo de ejemplo
cp env.example .env

# Verificar contenido (valores por defecto están bien)
cat .env
```

2. **Construir e iniciar contenedores:**
```bash
docker compose up --build
```

#### Resultado esperado:
- ✅ Se descargan imágenes (primera vez)
- ✅ Se construye imagen de la app
- ✅ Se inician 2 contenedores: `ferreteria-db` y `ferreteria-web`
- ✅ Logs muestran:
  - `ferreteria-db`: "database system is ready to accept connections"
  - `ferreteria-web`: "Booting worker with pid: X" (gunicorn)
- ✅ Health checks pasan (verde en `docker compose ps`)

#### Verificación:
```bash
# En otra terminal
docker compose ps

# Output esperado:
# NAME              STATUS                    PORTS
# ferreteria-db     Up (healthy)             0.0.0.0:5432->5432/tcp
# ferreteria-web    Up (healthy)             0.0.0.0:5000->5000/tcp
```

---

### Caso 2: Verificar Health Endpoint

#### Pasos:
```bash
# Desde navegador o curl
curl http://localhost:5000/health
```

#### Resultado esperado:
```json
{
  "status": "healthy",
  "database": "connected",
  "message": "Database connection successful"
}
```

---

### Caso 3: Inicializar Base de Datos

#### Pasos:
```bash
# Opción A: Ejecutar seeds
docker compose exec web python seed_initial_data.py

# Opción B: Conectar con pgAdmin/DBeaver
# Host: localhost
# Port: 5432
# DB: ferreteria
# User: ferreteria
# Pass: ferreteria
```

#### Resultado esperado:
- ✅ Seeds se ejecutan sin error
- ✅ Tablas `uom` y `category` tienen datos

#### Verificación:
```bash
# Entrar a psql
docker compose exec db psql -U ferreteria -d ferreteria

# Ejecutar query
SELECT COUNT(*) FROM uom;
-- Debe retornar > 0
```

---

### Caso 4: Navegar por la Aplicación

#### Pasos:
1. Abrir navegador en: http://localhost:5000
2. Verificar endpoints:
   - `/` - Página principal
   - `/products` - Listado de productos
   - `/sales/new` - Nueva venta
   - `/invoices` - Boletas
   - `/balance` - Balance financiero

#### Resultado esperado:
- ✅ Todas las páginas cargan correctamente
- ✅ Sin errores 500
- ✅ Bootstrap/CSS carga bien

---

### Caso 5: Ver Logs

#### Pasos:
```bash
# Logs de todos los servicios
docker compose logs -f

# Solo logs de la app
docker compose logs -f web

# Solo logs de la DB
docker compose logs -f db
```

#### Resultado esperado:
- ✅ Logs muestran requests HTTP
- ✅ No hay errores de conexión
- ✅ Queries SQL se ejecutan (si SQLALCHEMY_ECHO=True)

---

### Caso 6: Reiniciar Servicios

#### Pasos:
```bash
# Detener
Ctrl+C  # Si está en foreground

# O
docker compose down

# Iniciar de nuevo
docker compose up
```

#### Resultado esperado:
- ✅ Contenedores se detienen limpiamente
- ✅ Datos persisten (volumen no se elimina)
- ✅ Al reiniciar, la app conecta a la DB con datos existentes

---

### Caso 7: Persistencia de Datos

#### Pasos:
1. **Crear un producto:**
   - Ir a `/products/new`
   - Crear producto "Martillo Docker"
   - Guardar

2. **Detener contenedores:**
```bash
docker compose down
```

3. **Iniciar de nuevo:**
```bash
docker compose up
```

4. **Verificar producto existe:**
   - Ir a `/products`
   - Buscar "Martillo Docker"

#### Resultado esperado:
- ✅ El producto persiste
- ✅ Datos NO se pierden al reiniciar

---

### Caso 8: Resetear Base de Datos (Eliminar Volumen)

#### Pasos:
```bash
# ⚠️ ADVERTENCIA: Esto borra todos los datos

# Detener y eliminar volúmenes
docker compose down -v

# Verificar que el volumen fue eliminado
docker volume ls | grep ferreteria

# Iniciar de nuevo
docker compose up --build
```

#### Resultado esperado:
- ✅ Volumen `ferreteria-app_postgres_data` fue eliminado
- ✅ Al iniciar, DB está vacía
- ✅ Necesita re-ejecutar seeds

---

### Caso 9: Ejecutar Seeds desde Docker

#### Pasos:
```bash
# Con contenedores corriendo
docker compose exec web python seed_initial_data.py
```

#### Resultado esperado:
- ✅ Output: "Inserted X UOM records", "Inserted Y Category records"
- ✅ Sin errores

#### Verificación:
```bash
docker compose exec db psql -U ferreteria -d ferreteria -c "SELECT COUNT(*) FROM uom;"
```

---

### Caso 10: Entrar al Contenedor de la App

#### Pasos:
```bash
# Entrar a bash
docker compose exec web bash

# Dentro del contenedor
ls -la
env | grep DB
exit
```

#### Resultado esperado:
- ✅ Shell dentro del contenedor funciona
- ✅ Variables de entorno están configuradas
- ✅ Archivos de la app están presentes

---

## MODO B: Solo App + PostgreSQL Externo

### Caso 11: Configurar para DB Externa

#### Pre-condición:
- PostgreSQL corriendo en tu máquina local (no en Docker)
- Base de datos `ferreteria` creada

#### Pasos:
1. **Editar `.env`:**
```env
# Windows/Mac
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=ferreteria
DB_USER=admin
DB_PASSWORD=admin123

SECRET_KEY=change-me
FLASK_DEBUG=0
```

2. **Iniciar solo la app:**
```bash
docker compose up web --build
```

#### Resultado esperado:
- ✅ Solo contenedor `ferreteria-web` inicia
- ✅ NO inicia contenedor `ferreteria-db`
- ✅ La app conecta a tu PostgreSQL local

---

### Caso 12: Verificar Conexión a DB Externa

#### Pasos:
```bash
# Verificar health
curl http://localhost:5000/health
```

#### Resultado esperado:
```json
{
  "status": "healthy",
  "database": "connected",
  "message": "Database connection successful"
}
```

#### Verificación en logs:
```bash
docker compose logs web

# Debe mostrar conexión exitosa a DB externa
```

---

### Caso 13: Linux - Usar IP del Host

#### Pasos (solo Linux):
1. **Obtener IP del host:**
```bash
ip addr show docker0
# Anotar la IP (ej: 172.17.0.1)
```

2. **Editar `.env`:**
```env
DB_HOST=172.17.0.1
# ... resto de config
```

3. **Reiniciar:**
```bash
docker compose restart web
```

#### Resultado esperado:
- ✅ Conexión exitosa desde contenedor Docker a PostgreSQL del host

---

## Troubleshooting

### Error: "Connection refused"

#### Síntomas:
```
psycopg2.OperationalError: connection to server at "db" (xxx.xxx.xxx.xxx), port 5432 failed: Connection refused
```

#### Soluciones:

**Modo A:**
```bash
# Verificar que db está corriendo
docker compose ps

# Ver logs de db
docker compose logs db

# Verificar health de db
docker compose exec db pg_isready -U ferreteria

# Si db no está healthy, reiniciar:
docker compose restart db
```

**Modo B:**
```bash
# Verificar que PostgreSQL está corriendo en host
# Windows
services.msc  # Buscar PostgreSQL

# Linux
sudo systemctl status postgresql

# Verificar configuración de DB_HOST en .env
```

---

### Error: "port is already allocated"

#### Síntomas:
```
Error: bind: address already in use
```

#### Solución:
```bash
# Opción 1: Detener proceso usando el puerto
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill <PID>

# Opción 2: Cambiar puerto en docker-compose.yml
ports:
  - "8000:5000"  # Usar puerto 8000 en host
```

---

### Error: Scripts de init no se ejecutan

#### Síntomas:
- Base de datos vacía después de iniciar
- Scripts en `db/init/` no se ejecutan

#### Causa:
El volumen ya existe de una ejecución anterior.

#### Solución:
```bash
# Eliminar volumen y recrear
docker compose down -v
docker compose up --build
```

---

### Error: "exec format error"

#### Síntomas:
```
exec format error
```

#### Causa:
Line endings incorrectos (CRLF vs LF)

#### Solución:
```bash
# Configurar git para LF
git config core.autocrlf input

# Reconvertir archivos
git rm --cached -r .
git reset --hard

# Reconstruir imagen
docker compose build --no-cache
```

---

### Error: "no such file or directory"

#### Síntomas:
```
python: can't open file '/app/app.py': [Errno 2] No such file or directory
```

#### Causa:
Archivos no copiados correctamente

#### Solución:
```bash
# Verificar .dockerignore
cat .dockerignore

# Reconstruir sin caché
docker compose build --no-cache

# Verificar archivos en contenedor
docker compose run --rm web ls -la
```

---

## Queries de Verificación

### Ver estado de contenedores:
```bash
docker compose ps
docker compose top
docker stats
```

### Ver volúmenes:
```bash
docker volume ls
docker volume inspect ferreteria-app_postgres_data
```

### Ver redes:
```bash
docker network ls
docker network inspect ferreteria-app_ferreteria-network
```

### Ver logs con filtros:
```bash
# Últimas 100 líneas
docker compose logs --tail=100

# Desde timestamp
docker compose logs --since 2026-01-08T21:00:00

# Solo errores (si están en stderr)
docker compose logs 2>&1 | grep -i error
```

---

## Resumen de Verificaciones Críticas

### ✅ Checklist Final:

- [ ] Imagen de la app se construye sin errores
- [ ] Contenedores inician correctamente
- [ ] Health checks pasan (verde en `docker compose ps`)
- [ ] `/health` retorna status 200 con DB connected
- [ ] Seeds se ejecutan correctamente
- [ ] Todas las páginas cargan sin error 500
- [ ] Datos persisten al reiniciar contenedores
- [ ] Volumen se puede eliminar y recrear
- [ ] Modo B (DB externa) funciona
- [ ] Logs no muestran errores de conexión
- [ ] Se puede entrar a contenedores con exec
- [ ] Backup y restore de datos funciona

---

## Backup y Restore con Docker

### Backup:
```bash
# Backup completo
docker compose exec db pg_dump -U ferreteria -d ferreteria > backup_$(date +%Y%m%d_%H%M%S).sql

# Solo esquema
docker compose exec db pg_dump -U ferreteria -d ferreteria --schema-only > schema.sql

# Solo datos
docker compose exec db pg_dump -U ferreteria -d ferreteria --data-only > data.sql
```

### Restore:
```bash
# Restaurar desde backup
docker compose exec -T db psql -U ferreteria -d ferreteria < backup.sql

# O copiar al contenedor primero
docker compose cp backup.sql db:/tmp/
docker compose exec db psql -U ferreteria -d ferreteria -f /tmp/backup.sql
```

---

## Notas Importantes

1. **Primera vez:** La imagen se construye y puede tardar unos minutos.
2. **Volúmenes:** Persisten entre reinicios. Usar `docker compose down -v` para eliminarlos.
3. **Healthchecks:** Pueden tardar ~40s en pasar la primera vez.
4. **Gunicorn:** Usa 2 workers por defecto. Ajustar en Dockerfile si necesitas más.
5. **Logs:** Gunicorn loguea accesos y errores a stdout/stderr.
6. **User:** El contenedor corre con usuario no-root (appuser) por seguridad.

---

**Fase 6 Completada - Sistema completamente dockerizado** ✅

