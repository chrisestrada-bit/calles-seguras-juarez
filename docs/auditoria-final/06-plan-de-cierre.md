# 06 · Plan de cierre

## Estado: cierre `v1.1.1`

Lo aplicado en `fix/registro-y-rate-limit` se integró en `main` (PR #33), junto con los PR #34–#38. La rama
`chore/auditoria-final-v1-1` agrega el autocompletado de `/trayecto`, el `User-Agent` del clima (D-10) y la documentación de
cierre. La etiqueta final es **`v1.1.1`** porque `v1.1.0` ya está publicada en `f831eb4`.

### Pasos para publicar `v1.1.1`

1. Revisar y fusionar el PR de `chore/auditoria-final-v1-1` en `main`.
2. Esperar a que la CI quede en verde (pytest con PostgreSQL, Vitest, Playwright y validación de infraestructura).
3. Crear la etiqueta anotada sobre el merge en `main`: `git tag -a v1.1.1 -m "v1.1.1"` y `git push origin v1.1.1`.
4. No mover ni borrar `v1.1.0`.

## Aplicado en `fix/registro-y-rate-limit`

| Hallazgo | Archivos |
|---|---|
| A1 | `docker-compose.yml`, `.env.example`, `db/seed.py`, `README.md`, `docs/kubernetes.md`, `frontend/e2e/ayudas.ts`, `docs/AUDITORIA_OBLIGATORIA.md` (fe de erratas) |
| A2 | `backend/app/core/dependencies.py`, `backend/app/routers/auth.py` |
| A3 | `backend/app/services/imagenes.py` (nuevo), `services/fotos.py`, `routers/reportes.py`, `db/limpiar_fotos.py` (nuevo) |
| A4 | `backend/app/core/red.py` (nuevo), `core/config.py`, `routers/geocoding.py` |
| M1, M2 | `backend/app/services/auth.py`, `services/limitador.py`, `routers/auth.py` |
| M3 | `backend/app/services/fusion.py`, `docs/api-contract.md` §12.2 |
| M4 | `frontend/src/context/AuthContext.tsx` (+ `AuthContext.test.tsx`) |
| M5 | `frontend/vercel.json`, `frontend/index.html`, `frontend/public/tema-inicial.js` (nuevo), `frontend/public/sw.js` (shell v2), `frontend/nginx.conf`, `backend/app/main.py` |
| M6 | `backend/app/routers/ws.py`, `services/tiempo_real.py` |
| M7 | `backend/app/core/limite_cuerpo.py` (nuevo), `main.py` |
| M9 | `frontend/playwright.config.ts`, `frontend/e2e/ayudas.ts`, `.gitignore`, `.dockerignore` |
| B5 | `backend/app/main.py` (`version="1.1.1"`) |
| Pruebas | `backend/tests/test_auditoria_final.py` (nuevo, 16), `tests/conftest.py`, `tests/test_fase1.py` (las fixtures de imagen ahora son estructuralmente válidas) |

## Antes de desplegar

### Lista de verificación operativa en Render (`v1.1.1`)

Marca cada punto en el panel de Render; ninguno se puede resolver desde el repositorio.

- [ ] `RUN_SEED=false` en producción. Si se necesita sembrar, usar una `SEED_PASSWORD` nueva de 12 caracteres o más y volver a `false` después.
- [ ] Rotar o desactivar las cuentas `@ejemplo.mx` de producción, sobre todo si se sembraron con la contraseña publicada antes de A1.
- [ ] Confirmar qué cabecera trae la IP real y fijar **una** de estas variables: `CLIENT_IP_HEADER` (por ejemplo, `CF-Connecting-IP`) o `TRUSTED_PROXY_HOPS=1`.
- [ ] Montar un disco persistente en `UPLOADS_DIR`, o migrar las fotos a almacenamiento de objetos. Sin esto, las fotos se pierden en cada despliegue.
- [ ] Limpiar las fotos existentes: `python db/limpiar_fotos.py --simular`, revisar la salida y luego ejecutarlo sin `--simular`.
- [ ] Comprobar que `GET /api/v1/clima/pronostico` responde con `desactualizado: false` (prueba de D-10 con el nuevo `User-Agent`).

### Detalle por hallazgo

1. **Producción (A1):**
   - Fijar `RUN_SEED=false`, o bien una `SEED_PASSWORD` nueva de 12 caracteres o más.
   - Rotar o desactivar las cuentas `@ejemplo.mx` existentes.
   - `.env` local: si usa `SEED_PASSWORD=Juarez2026`, sigue funcionando en desarrollo, pero conviene cambiarla.
2. **Render (A4):**
   - Revisar la cabecera con la IP real (por ejemplo, registrar temporalmente `request.headers` en un entorno de prueba).
   - Fijar `CLIENT_IP_HEADER` o `TRUSTED_PROXY_HOPS=1`.
   - Sin esto, los límites por IP siguen agrupando a todas las personas en la IP del proxy. No es un fallo de seguridad, pero sí puede causar 429 colectivos en registro y login con tráfico alto.
3. **Render (M8):** montar un disco persistente en `UPLOADS_DIR` o migrar a almacenamiento de objetos.
4. **Fotos existentes (A3):** `python db/limpiar_fotos.py --simular` y luego sin `--simular`.
5. **Vercel (M5):** si la URL de la API cambia, actualizar `connect-src` en `frontend/vercel.json`.

## Verificación después de desplegar

```bash
curl -sD - -o /dev/null https://calles-seguras-juarez.vercel.app/ | grep -iE "content-security|x-frame|permissions"
curl -sD - -o /dev/null https://calles-seguras-juarez-api.onrender.com/salud | grep -iE "x-frame|strict-transport|referrer"
```

- Lighthouse móvil y escritorio: accesibilidad 90 o más (antes: 100).
- Recorrer en el navegador la lista, el mapa, el detalle con foto, el registro y el login. Verificar que no haya violaciones de CSP en consola.
- Con la cuenta de enlace: iniciar sesión, cerrar sesión y comprobar que el token anterior responde 401.

## Recomendaciones para la siguiente versión

- Pasar el token a una cookie `HttpOnly` con `SameSite=Strict` y protección CSRF.
- Limitadores compartidos (Redis) si hay más de una réplica.
- Usar `--no-access-log` o un filtro de cadena de consulta en producción (B4).
- Aclarar con el cliente B1 (folio anual y tope 999999) y B2 (¿`Validado → Rechazado`?).
