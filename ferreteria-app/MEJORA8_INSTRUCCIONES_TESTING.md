# 🧪 MEJORA 8 - Instrucciones de Testing

## ⚠️ IMPORTANTE: Docker debe estar iniciado

Antes de comenzar el testing, asegúrate de que Docker Desktop esté corriendo.

---

## 📋 **Paso 1: Iniciar Docker**

### **Windows:**
1. Abrir Docker Desktop
2. Esperar a que el ícono de Docker en la bandeja del sistema esté verde

### **Verificar que Docker está corriendo:**
```powershell
docker ps
```

**Resultado esperado:** Lista de contenedores (puede estar vacía, pero no debe dar error)

---

## 📋 **Paso 2: Reconstruir y Levantar Contenedores**

```powershell
cd c:\jere\Ferreteria\ferreteria-app

# Detener contenedores existentes (si los hay)
docker compose down

# Reconstruir imagen con cambios de MEJORA 8
docker compose up --build -d

# Verificar que los contenedores están corriendo
docker compose ps
```

**Resultado esperado:**
```
NAME              STATUS         PORTS
ferreteria-db     healthy        5432/tcp
ferreteria-web    healthy        0.0.0.0:5000->5000/tcp
```

---

## 📋 **Paso 3: Verificar Logs**

```powershell
# Ver logs del contenedor web
docker compose logs web --tail=20

# Verificar que no hay errores de APP_PASSWORD
```

**Resultado esperado:**
```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:5000
[INFO] Booting worker with pid: X
```

**NO debe aparecer:**
```
ERROR - APP_PASSWORD not configured
```

---

## 📋 **Paso 4: Test 1 - Acceso a raíz redirige a login**

### **Pasos:**
1. Abrir navegador en modo privado/incógnito
2. Ir a: `http://localhost:5000`

### **Resultado esperado:**
- ✅ Redirige automáticamente a `http://localhost:5000/login`
- ✅ Se muestra página de login con:
  - Título "Sistema Ferretería"
  - Subtítulo "Acceso Restringido"
  - Campo de contraseña
  - Botón "Ingresar"
  - Gradiente púrpura/violeta

---

## 📋 **Paso 5: Test 2 - Login con contraseña incorrecta**

### **Pasos:**
1. En `/login`, ingresar contraseña: `incorrecta123`
2. Click "Ingresar"

### **Resultado esperado:**
- ✅ Queda en la página `/login`
- ✅ Aparece alerta roja (danger):
  ```
  ⚠ Contraseña incorrecta. Intente nuevamente.
  ```
- ✅ No hay redirect a `/products`
- ✅ URL sigue siendo `/login`

---

## 📋 **Paso 6: Test 3 - Login con contraseña correcta**

### **Pasos:**
1. En `/login`, ingresar contraseña: `ferreteria123` (la configurada en `.env`)
2. Click "Ingresar"

### **Resultado esperado:**
- ✅ Aparece alerta verde (success):
  ```
  ✓ Acceso concedido. Bienvenido.
  ```
- ✅ Redirige automáticamente a `http://localhost:5000/products`
- ✅ Se muestra navbar completo con:
  - Productos
  - Ventas
  - Compras (dropdown)
  - Balance
  - **Botón "Salir"** en la esquina superior derecha
- ✅ Se muestra listado de productos

---

## 📋 **Paso 7: Test 4 - Navegación autenticada**

### **Pasos:**
1. Después del login exitoso, navegar a:
   - `/sales/new`
   - `/invoices`
   - `/balance`
   - `/suppliers`

### **Resultado esperado:**
- ✅ Todas las secciones son accesibles
- ✅ Sin redirects a `/login`
- ✅ Navbar siempre visible con botón "Salir"

---

## 📋 **Paso 8: Test 5 - Logout**

### **Pasos:**
1. Estando autenticado, click en botón "Salir" (esquina superior derecha)

### **Resultado esperado:**
- ✅ Aparece alerta azul (info):
  ```
  ℹ Sesión cerrada correctamente.
  ```
- ✅ Redirige a `http://localhost:5000/login`
- ✅ Si intentas acceder a `/products` → redirige a `/login`

---

## 📋 **Paso 9: Test 6 - Intento de acceso sin autenticación**

### **Pasos:**
1. Después de logout (o en navegador privado nuevo)
2. Intentar acceder directamente a:
   - `http://localhost:5000/products`
   - `http://localhost:5000/sales/new`
   - `http://localhost:5000/invoices`
   - `http://localhost:5000/balance`

### **Resultado esperado:**
- ✅ Todas redirigen a `/login`
- ✅ Sin errores 404 o 500
- ✅ URL cambia a `/login`

---

## 📋 **Paso 10: Test 7 - /health sin autenticación**

### **Pasos:**
1. Sin autenticar (navegador privado)
2. Ir a: `http://localhost:5000/health`

### **Resultado esperado:**
- ✅ HTTP 200 OK
- ✅ Respuesta JSON:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "message": "Database connection successful"
  }
  ```
- ✅ **NO redirige a /login** (esto es crítico para Docker healthcheck)

---

## 📋 **Paso 11: Test 8 - Archivos estáticos sin autenticación**

### **Pasos:**
1. Sin autenticar
2. Ir a: `http://localhost:5000/static/img/no-image.svg`

### **Resultado esperado:**
- ✅ Se muestra la imagen SVG
- ✅ HTTP 200 OK
- ✅ **NO redirige a /login** (los assets del login.html necesitan ser accesibles)

---

## 📋 **Paso 12: Test 9 - Sesión persiste al cerrar navegador**

### **Pasos:**
1. Login exitoso en navegador normal (no privado)
2. Cerrar navegador completamente
3. Abrir navegador nuevamente
4. Ir a: `http://localhost:5000`

### **Resultado esperado:**
- ✅ Redirige directamente a `/products` (sin pedir contraseña)
- ✅ La sesión persiste (`session.permanent = True`)

**Nota:** Si quieres forzar re-login, debes hacer logout explícito o borrar cookies.

---

## 📋 **Paso 13: Test 10 - HTMX protegido (agregar al carrito)**

### **Pasos:**
1. Logout
2. En navegador, usar DevTools Console:
   ```javascript
   fetch('/sales/cart/add', {
     method: 'POST',
     headers: {'Content-Type': 'application/x-www-form-urlencoded'},
     body: 'product_id=1&qty=1'
   })
   ```

### **Resultado esperado:**
- ✅ Respuesta: redirect a `/login` (HTTP 302)
- ✅ El middleware protege también los endpoints HTMX

---

## 📋 **Paso 14: Test 11 - APP_PASSWORD no configurada (opcional)**

### **⚠️ Este test requiere editar .env y reiniciar Docker**

### **Pasos:**
1. Comentar `APP_PASSWORD` en `.env`:
   ```env
   # APP_PASSWORD=ferreteria123
   ```
2. Reiniciar contenedores:
   ```powershell
   docker compose down
   docker compose up --build -d
   ```
3. Ir a: `http://localhost:5000/login`
4. Ingresar cualquier contraseña
5. Click "Ingresar"

### **Resultado esperado:**
- ✅ Alerta roja (danger):
  ```
  Error de configuración: APP_PASSWORD no está definida. Contacte al administrador.
  ```
- ✅ HTTP 500
- ✅ En logs del contenedor:
  ```
  ERROR - APP_PASSWORD not configured in environment
  ```
- ✅ Acceso completamente bloqueado

### **Restaurar:**
```env
APP_PASSWORD=ferreteria123
```
```powershell
docker compose down
docker compose up --build -d
```

---

## ✅ **Checklist Completo de Testing**

| # | Test | Resultado |
|---|------|-----------|
| 1 | Acceso a `/` redirige a `/login` | ⬜ |
| 2 | Login con contraseña incorrecta → error | ⬜ |
| 3 | Login con contraseña correcta → `/products` | ⬜ |
| 4 | Navegación autenticada (sales, invoices, balance) | ⬜ |
| 5 | Logout → redirige a `/login` | ⬜ |
| 6 | Intento de acceso sin auth → redirige a `/login` | ⬜ |
| 7 | `/health` accesible sin auth | ⬜ |
| 8 | Archivos estáticos accesibles sin auth | ⬜ |
| 9 | Sesión persiste al cerrar navegador | ⬜ |
| 10 | Endpoints HTMX protegidos | ⬜ |
| 11 | APP_PASSWORD no configurada → error 500 (opcional) | ⬜ |

---

## 🎯 **Resultado Final Esperado**

Si todos los tests pasan:

- ✅ **Protección completa:** Sin autenticación, no se puede acceder a ninguna sección
- ✅ **Login funcional:** Contraseña correcta permite acceso
- ✅ **Logout funcional:** Cierra sesión y bloquea acceso
- ✅ **UX fluida:** Flash messages claros, redirects apropiados
- ✅ **Sesión persistente:** No pide contraseña constantemente
- ✅ **Healthcheck funciona:** Docker puede verificar salud del contenedor
- ✅ **Seguridad:** APP_PASSWORD no configurada → acceso bloqueado
- ✅ **Sin regresiones:** Todas las funcionalidades previas (ventas, productos, balance) siguen funcionando

---

## 🐛 **Troubleshooting**

### **Problema: "APP_PASSWORD no está definida"**
**Solución:**
1. Verificar que `.env` tenga:
   ```env
   APP_PASSWORD=ferreteria123
   ```
2. Reiniciar contenedores:
   ```powershell
   docker compose down
   docker compose up --build -d
   ```

---

### **Problema: Login no redirige a /products**
**Solución:**
1. Verificar logs:
   ```powershell
   docker compose logs web --tail=50
   ```
2. Verificar que `SECRET_KEY` esté configurado en `.env`

---

### **Problema: Navbar no muestra botón "Salir"**
**Solución:**
1. Verificar que estás viendo la página DESPUÉS de login exitoso
2. Hacer hard refresh: `Ctrl + F5` (limpiar caché del navegador)

---

### **Problema: /health redirige a /login**
**Solución:**
- Esto NO debe pasar. Si pasa, hay un error en el middleware.
- Verificar que `app/__init__.py` tenga:
  ```python
  if request.path == '/health':
      return None
  ```

---

**Última actualización:** Enero 2026  
**Autor:** Sistema Ferretería - MEJORA 8
