# Calles Seguras Juárez

Plataforma web ciudadana de la Asociación Civil «Calles Seguras Juárez» (Ciudad Juárez, Chihuahua) para **reportar baches,
alcantarillas sin tapa y encharcamientos**, dar seguimiento a las reparaciones y **consultar calles con riesgo de
inundación** antes de circular.

| Capa | Tecnología |
|------|------------|
| `frontend/` | React + TypeScript (Vite), HTML semántico, CSS externo responsivo desde 360 px, WCAG 2.2 AA |
| `backend/` | Python + FastAPI, Pydantic v2, SQLAlchemy 2.0, arquitectura en capas (`routers/`, `services/`, `models/`, `schemas/`) |
| `db/` | PostgreSQL + migraciones Alembic (`db/migrations/`) + datos semilla idempotentes (`db/seed.py`) |
| `infra/` | Dockerfiles, `docker-compose.yml` y manifiestos de Kubernetes (`infra/k8s/`) |

## Estado actual: `v1.1.1`

`v1.1.1` es la versión de cierre. Se etiqueta como `v1.1.1` porque `v1.1.0` ya está publicada en `f831eb4` (PR #32) y no se
reescribe. Incluye la auditoría final (PR #33–#34) y estas novedades visibles:

* **Identidad visual** con dos temas: «Claro editorial» (modo claro) y «Grafito turquesa» (modo oscuro). Ambos se diseñaron con
  contraste WCAG 2.2 AA, y el estado nunca se comunica sólo con color (íconos y texto).
* **Instalación como aplicación (PWA):** botón «Instalar app» junto a la marca en la cabecera y un apartado con instrucciones en el
  pie de página (incluye el caso de iOS, que no ofrece el aviso automático).
* **Distribución responsiva** probada desde **360 px** (móvil) hasta **1920 px o más** (escritorio amplio), con las acciones de la
  cabecera agrupadas en escritorio.
* **Autocompletado en `/trayecto`:** origen y destino sugieren direcciones mientras se escribe (desde 3 caracteres, con espera
  de 400 ms), se eligen con el teclado (flechas, Enter y Esc) y sólo aceptan puntos dentro de Ciudad Juárez (RN-01).
* **Clima:** la consulta a Open-Meteo se identifica con `User-Agent` (antes fallaba desde Render) y el aviso muestra la hora de
  actualización en hora de Ciudad Juárez (RN-02).
* **Fotos:** se rechazan imágenes con dimensiones anómalas y archivos disfrazados; las fotos públicas no conservan EXIF/GPS (RN-04).

Las tareas de despliegue que dependen del panel de Render están en
[`docs/auditoria-final/06-plan-de-cierre.md`](docs/auditoria-final/06-plan-de-cierre.md).

## Arranque rápido (Docker Compose, menos de 3 minutos)

```bash
cp .env.example .env          # opcional: personaliza puertos y contraseñas (todo es ficticio)
docker compose up --build
```

* Aplicación: <http://localhost:5173> · API y documentación (`/docs`): <http://localhost:8000/docs>
* El contenedor del backend aplica las migraciones y carga los datos semilla (≈ 500 reportes públicos) al iniciar.

### Cuentas de prueba

La contraseña de todas es el valor que pongas en `SEED_PASSWORD` dentro de tu `.env` (no hay valor por omisión: si la dejas vacía, las cuentas reciben una contraseña aleatoria y no podrás entrar con ellas). Defínela **antes** del primer `docker compose up`; si ya sembraste, la semilla no cambia contraseñas de cuentas existentes.

| Correo | Rol | Qué probar |
|--------|-----|------------|
| `coordinador@ejemplo.mx` | `coordinador` | Usuarios, colonias, cuadrillas, catálogos, puntos recurrentes, auditoría |
| `moderador@ejemplo.mx` / `moderador2@ejemplo.mx` | `moderador` | Cola de moderación, validar, rechazar con motivo, fusionar duplicados, exportar CSV/XML |
| **`enlace@ejemplo.mx`** | `enlace_municipal` | Vista `/enlace`: sólo los baches de sus cuadrillas (Norte y Sur) y su avance `Programado → En reparación → Reparado` |
| `ciudadano01@ejemplo.mx` … `ciudadano12@ejemplo.mx` | `ciudadano` | Reportar, confirmar, avisos, colonias de interés, modo sin conexión |

Sin sesión (visitante) se consultan reportes, mapa, trayecto y resúmenes por colonia.

## Desarrollo sin Docker

```bash
# Base de datos: un PostgreSQL 16 y DATABASE_URL en .env (ver .env.example)
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
alembic -c db/alembic.ini upgrade head && python db/seed.py
python -m uvicorn app.main:app --reload --app-dir backend      # API en :8000

cd frontend && npm ci && npm run dev                           # frontend en :5173
```

## Pruebas

| Qué | Comando | Dónde |
|-----|---------|-------|
| Backend (pytest, requiere una base cuyo nombre termine en `_test`) | `pytest backend/tests -v` | `backend/tests/` |
| Frontend: lint y build | `npm run lint` · `npm run build` | `frontend/` |
| Frontend: componentes y lógica (Vitest + Testing Library) | `npm test` | `frontend/src/**/*.test.ts(x)` |
| Frontend: flujos extremo a extremo (Playwright) | `npx playwright install chromium` y `npm run test:e2e` | `frontend/e2e/` |
| Manifiestos de Kubernetes | `python infra/validar_k8s.py` | `infra/k8s/` |

Las pruebas E2E levantan la API y el frontend (ver `frontend/playwright.config.ts`); necesitan PostgreSQL con migraciones y
semilla (`DATABASE_URL`, `SEED_PASSWORD`). La integración continua (`.github/workflows/ci.yml`) ejecuta pytest, lint, build,
auditoría de dependencias, Vitest, Playwright (con reportes, capturas, videos y trazas de fallos como artefactos) y la
validación de la infraestructura.

## Documentación

* [`docs/arquitectura.md`](docs/arquitectura.md) — modelo de datos, reglas de negocio, matriz de acceso y decisiones por fase.
* [`docs/api-contract.md`](docs/api-contract.md) — contrato de la API (`/api/v1`).
* [`docs/kubernetes.md`](docs/kubernetes.md) — despliegue en Kubernetes (kind, minikube o k3d): comandos de despliegue, acceso y limpieza.
* [`docs/AUDITORIA_OBLIGATORIA.md`](docs/AUDITORIA_OBLIGATORIA.md) — auditoría de los requisitos obligatorios.
* [`docs/AI_USAGE.md`](docs/AI_USAGE.md) — uso de asistentes de IA (incluye las fases de requisitos opcionales).
* **Esquemas XSD** (intercambio XML): [`docs/esquemas/reportes_v1.xsd`](docs/esquemas/reportes_v1.xsd) (exportación de reportes) y
  [`docs/esquemas/catalogos_v1.xsd`](docs/esquemas/catalogos_v1.xsd) (importación de colonias y sectores).

## Requisitos opcionales implementados

| Fase | Historias | Resumen |
|------|-----------|---------|
| 1 | HU-02.4, HU-04.5, HU-07.3 · extras 4.3 y 4.4 | Fotografías de reportes, mapa interactivo (Leaflet), exportación CSV/XML con XSD e importación XML de catálogos |
| 2 | HU-03.4, HU-08.2, HU-08.3, HU-08.4 · extra 4.5 | Puntos recurrentes, avisos sobre mis reportes, WebSocket en vivo, PWA y envíos sin conexión idempotentes |
| 3 | HU-05.3, HU-05.4, HU-05.5, HU-06.3, HU-01.4, HU-04.6, HU-07.2 | Fusión de duplicados, cuadrillas, rol `enlace_municipal`, catálogos administrables, colonias de interés, revisar mi trayecto, resumen por colonia |
| 4 | Extras 4.1 y 4.2 | Despliegue en Kubernetes y pruebas automatizadas del frontend (Vitest + Playwright) en CI |

## Reglas que no se negocian

Territorio de Ciudad Juárez (RN-01), hora oficial `America/Ciudad_Juarez` (RN-02), folios únicos (RN-03), **privacidad: ninguna
respuesta pública expone datos de quien reporta (RN-04)**, máquina de estados estricta (RN-05), vigencia de encharcamientos de
6 h (RN-06), trazabilidad inmutable (RN-07), 10 reportes por hora (RN-08), visibilidad pública (RN-09) y longevidad (RN-10).
No hay secretos en el repositorio: todo se configura con variables de entorno (`.env.example`).
