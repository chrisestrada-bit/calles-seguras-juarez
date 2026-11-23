# 03 · Hallazgos

Estado: ✅ corregido en `fix/registro-y-rate-limit` · ⏳ requiere acción fuera del repositorio · 📝 documentado (sin cambio de código).

## Alto

### A1 · Contraseña semilla por omisión publicada ✅ ⏳
- **Evidencia:**
  - `docker-compose.yml` tenía `SEED_PASSWORD: ${SEED_PASSWORD:-Juarez2026}` con `RUN_SEED` en `true` por omisión.
  - El mismo valor aparecía en `.env.example`, `README.md`, `docs/kubernetes.md` y `frontend/e2e/ayudas.ts`.
  - `docs/AUDITORIA_OBLIGATORIA.md` §6.6 afirmaba que no existía tal valor por omisión.
- **Riesgo:** si producción se sembró con ese valor, `coordinador@ejemplo.mx` es accesible con una contraseña publicada. Eso es crítico.
- **Corrección:**
  - Se quitó el valor por omisión de compose y `.env.example`. La documentación ya no muestra ninguna contraseña.
  - E2E exige `SEED_PASSWORD` explícita.
  - `db/seed.py` aborta en `APP_ENV=production` si la contraseña es un valor publicado (`CONTRASENAS_PUBLICADAS`) o tiene menos de 12 caracteres.
  - Se agregó una fe de erratas en `AUDITORIA_OBLIGATORIA.md`.
- **Pendiente ⏳:** rotar las contraseñas de las cuentas `@ejemplo.mx` de producción, o desactivarlas desde `/admin/usuarios`. La semilla no cambia contraseñas de cuentas que ya existen.

### A2 · El enlace municipal no podía cerrar sesión ni renovar ✅
- **Evidencia:** `CUALQUIER_ROL` (`core/dependencies.py`) excluye `enlace_municipal`, así que `/auth/yo`, `/auth/renovar` y `/auth/cerrar-sesion` respondían 403. Después de «cerrar sesión», el token seguía sirviendo.
- **Corrección:** nueva dependencia `CUALQUIER_SESION = requiere_rol(*RolUsuario)` para las tres rutas de la propia sesión (`routers/auth.py`).

### A3 · Metadatos personales en fotos públicas (RN-04) ✅
- **Evidencia:** `services/fotos.py` guardaba los bytes tal como llegaban, con EXIF (GPS, dispositivo, hora). Además, `FotoOut.nombre_original` (por ejemplo `Juan_Perez_….jpg`) se mostraba a visitantes.
- **Corrección:** nuevo `services/imagenes.py`, que reescribe la estructura sin decodificar ni recomprimir y no agrega dependencias:
  - **JPEG:** elimina APP1 (EXIF/XMP), el resto de APPn salvo JFIF, ICC y Adobe, y los comentarios. Reinserta solo la orientación EXIF para que las fotos verticales no aparezcan giradas.
  - **PNG:** conserva una lista blanca de fragmentos y descarta `tEXt`, `zTXt`, `iTXt`, `eXIf`, `tIME` y desconocidos.
  - **Ambos:** descarta lo que venga después de EOI o IEND (archivos políglotas). Una estructura inválida se rechaza con «La imagen está dañada…».
  - **Nombre:** `nombre_original` solo lo ven quien subió la foto, el autor del reporte y moderación. El resto ve `fotografia-N.ext`.
- **Nota:** las fotos subidas **antes** de esta corrección siguen en disco con sus metadatos. Se recomienda reprocesarlas con `limpiar_metadatos` antes del siguiente despliegue (ver `06-plan-de-cierre.md`).

### A4 · IP del cliente detrás de proxy ✅ ⏳
- **Evidencia:** `routers/geocoding.py` usaba `request.client.host`. En Render, detrás de Cloudflare, esa es la IP del proxy, así que todas las personas compartían 30 búsquedas por minuto. Configurar uvicorn con `--forwarded-allow-ips='*'` habría permitido falsificar la IP.
- **Corrección:** `core/red.py::ip_cliente`. Solo confía en una cabecera si el despliegue la declara (`CLIENT_IP_HEADER`, o `TRUSTED_PROXY_HOPS` para la entrada de `X-Forwarded-For` que agregó el proxy más cercano) y valida que el valor sea una IP. Lo usan geocodificación, registro, login y WebSocket.
- **Pendiente ⏳:** confirmar en Render qué cabecera trae la IP real del cliente y fijar la variable. Mientras no se fije, el comportamiento es el anterior: IP de la conexión.

## Medio

| # | Hallazgo | Corrección | Estado |
|---|---|---|---|
| M1 | `/auth/registro` sin límite de tasa (también permitía enumerar correos con 409) | `limitador_registro` por IP (`LIMITE_REGISTROS_POR_HORA_IP=10`) → `429 LIMITE_REGISTROS` + `Retry-After` | ✅ |
| M2 | Bloqueo por cuenta: un tercero bloqueaba a cualquiera 15 min con 5 intentos | Bloqueo fino por cuenta+IP (5 fallos en 15 min); límite por IP (30 fallos en 15 min) contra relleno de credenciales; respaldo en BD por cuenta subido a 20 fallos (ataques distribuidos) | ✅ |
| M3 | La fusión permitía a coordinación rechazar un `Recibido` (RN-05: solo moderación) | `fusion.py` llama a `transiciones.validar_transicion(…, RECHAZADO, actor.rol)` → 403. Contrato §12.2 actualizado. La interfaz ya ocultaba el botón a coordinación | ✅ |
| M4 | El JWT no se deslizaba: `renovarSesion` nunca se llamaba y una persona activa perdía la sesión a los 30 min | `AuthContext`: con actividad, renueva si pasaron 10 min o más desde la última emisión. Sin actividad, vence a los 30 min | ✅ |
| M5 | Vercel sin CSP, `frame-ancestors`, `nosniff`, `Referrer-Policy` ni `Permissions-Policy`; token en `localStorage` | `vercel.json` con CSP estricta (sin `unsafe-inline` en scripts; el script del tema pasó a `/tema-inicial.js`), `X-Frame-Options`, `Permissions-Policy` y COOP. La API agrega `X-Frame-Options`, `Referrer-Policy`, CSP en JSON y HSTS en producción. Nginx con las cabeceras que no dependen del despliegue | ✅ |
| M6 | WebSocket sin tope de conexiones (y `Origin` opcional) | Topes `WS_MAX_CONEXIONES` y `WS_MAX_CONEXIONES_POR_IP` → cierre `1013`; el frontend recurre al sondeo HTTP. `Origin` sigue siendo opcional a propósito: un cliente que no es navegador lo falsifica | ✅ |
| M7 | Subidas sin límite de cuerpo ni de partes | Middleware `core/limite_cuerpo.py` (`MAX_CUERPO_BYTES`, 16 MB) → `413 CUERPO_DEMASIADO_GRANDE`, también con cuerpos chunked | ✅ |
| M8 | Fotos en el disco efímero de Render | Requiere un disco persistente o almacenamiento de objetos | ⏳ |
| M9 | Playwright reutilizaba el backend de `docker compose` (puerto 8000) y escribía en la BD de desarrollo; `.uploads_e2e/` sin ignorar | Puerto por omisión de E2E: 18000; límites por IP elevados solo en E2E; `.uploads_e2e/` en `.gitignore` y `.dockerignore` | ✅ |

## Bajo

| # | Hallazgo | Estado |
|---|---|---|
| B1 | `seq_folio_*` tiene `MAXVALUE 999999 NO CYCLE` y es global (no se reinicia por año). Al agotarse, crear reportes daría 500. Interpretación de RN-03 a confirmar con el cliente | 📝 |
| B2 | Discrepancia RN-07/RN-05: RN-07 dice que un reporte que salió de `Recibido` «solo puede pasar a Rechazado»; la máquina de estados prohíbe `Validado → Rechazado` | 📝 aclarar con el cliente |
| B3 | El rol de enlace municipal amplía RN-05 (`Programado → En reparación → Reparado`); es una extensión de Prioridad D que `CLAUDE.md` no recoge | 📝 |
| B4 | El log de acceso de uvicorn registra la cadena de consulta (direcciones de geocodificación, coordenadas de `/cercanos`) | 📝 se recomienda `--no-access-log` o un filtro en producción |
| B5 | `FastAPI(version="1.0.0")` no coincidía con `v1.1.0` | ✅ ahora `1.1.1` |
| B6 | Arranque en frío de 47 s en Render | 📝 |
| B7 | Dos usuarios coludidos pueden prolongar un encharcamiento alternando «Sigue ahí» | 📝 conforme a RN-06 |
