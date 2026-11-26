# 01 · Inventario de Git, versiones y despliegue

## Git

| Elemento | Valor |
|---|---|
| Rama de trabajo (auditoría del 2026-11-22) | `fix/registro-y-rate-limit` (1 commit sobre `v1.1.0`: `8d0bc32 fix(frontend): mostrar errores 422/429 en 360px y proteger confirmacion`) |
| Tag | `v1.1.0` → `f831eb4` (= `origin/main`, merge del PR #32) |
| Cambios previos sin commit | `.gitignore` y `.dockerignore` (`uploads/`, `.uploads_test/`); `.uploads_e2e/` sin rastrear (3 PNG de una corrida E2E local) |
| Ramas locales | `chore/docker-frontend-y-ci`, `docs/auditoria-obligatoria`, `docs/cierre-v1`, `fix/auditoria-y-codigos-postales`, `fix/autocompletado-trayecto`, `fix/clima-user-agent`, `fix/rutas-zona-y-admin`, `fix/spa-rutas-y-detalle`, `main` |

### Actualización al cierre `v1.1.1` (2026-11-25)

| Elemento | Valor |
|---|---|
| Rama de cierre | `chore/auditoria-final-v1-1`, sobre `main` `e7710ed` (merge del PR #38) |
| Tags | `v1.1.0` → `f831eb4` (sin cambios). **`v1.1.1`** se crea sobre el merge de esta rama en `main` |
| Por qué `v1.1.1` | `v1.1.0` ya estaba publicada y `main` tiene 19 commits posteriores (13 sin contar merges, PR #33–#38). Mover una etiqueta publicada rompería a quien ya la descargó |
| PR integrados después de `v1.1.0` | #33 `fix/registro-y-rate-limit`, #34 `fix/seguridad-fotos`, #35 `feat/identidad-visual`, #36–#38 `fix/portada-busqueda-y-mapa` |
| Ramas integradas en el cierre | `fix/autocompletado-trayecto` (`55333f1` → `2e75cc0`) y `fix/clima-user-agent` (`4bae380` → `7361526`), con `git cherry-pick -x`. Único conflicto: CSS en `frontend/src/styles/pages.css`, resuelto conservando `main` y añadiendo el bloque del autocompletado |
| Archivos sin rastrear fuera del alcance | `docs/visual-lab/` y `new 1.txt` (personales; no se agregan ni se borran) |
| Versión de la API | `1.1.1` (`backend/app/main.py`, sin cambios en el cierre) |

## Migraciones Alembic

Cadena lineal sin bifurcaciones: `0001` (esquema, enums, secuencias de folio, Haversine, triggers RN-03/05/06/07/10) → `0002` (aviso de privacidad, CP) → `0003` (fotos) → `0004` (notificaciones, idempotencia offline) → `0005` (fusión, cuadrillas, enlace, catálogos, favoritas). `alembic upgrade head` aplica sin errores en PostgreSQL 16.

## Semilla (`db/seed.py`)

- Es idempotente: la segunda ejecución no crea colonias, usuarios ni reportes nuevos.
- Datos sembrados: 6 sectores, 119 colonias, ≈ 580 reportes repartidos en los 8 estados, 3 cuadrillas y 16 cuentas `@ejemplo.mx`.
- `RUN_SEED=true` hace que el contenedor ejecute la semilla al arrancar.
- `SEED_PASSWORD` es la contraseña común de las cuentas de prueba:
  - **Antes:** valor por omisión publicado (A1).
  - **Ahora:** no tiene valor por omisión. Si está vacía, cada cuenta recibe una contraseña aleatoria que no se revela.
  - Con `APP_ENV=production` se exigen 12 caracteres o más y se rechazan los valores de ejemplo publicados.

## Versiones

| Componente | Local | Docker / CI |
|---|---|---|
| Python | 3.14.5 | 3.12 (`python:3.12-slim`, `setup-python 3.12`) |
| Node | 24.16 | 22 LTS |
| PostgreSQL | 16 (`postgres:16-alpine`) | 16 |
| API (`FastAPI.version`) | `1.0.0` → **`1.1.1`** (B5) | — |

## Secretos

- `.env` no está versionado (está en `.gitignore`). `infra/k8s/secret.yaml` está ignorado y solo se versiona `secret.example.yaml`.
- El bundle de producción no contiene llaves: lo verifiqué buscando `locationiq`, `api_key` y patrones `pk.`.
- La única contraseña real publicada era `SEED_PASSWORD=Juarez2026` (A1, corregido).

## Despliegue

| Capa | URL | Observaciones |
|---|---|---|
| Frontend | `https://calles-seguras-juarez.vercel.app` | HSTS de Vercel. Antes no había CSP ni otras cabeceras (M5, corregido en `vercel.json`) |
| API | `https://calles-seguras-juarez-api.onrender.com/api/v1` | Detrás de Cloudflare (`Server: cloudflare`). Arranque en frío de ≈ 47 s (B6) |
| Base de datos | Neon (la URL no está en el repo, como corresponde) | — |
