# Uso de asistentes de IA

Este documento declara cómo se usó IA en el proyecto, quién la usó, qué produjo y cómo se verificó. Sigue los siete puntos
obligatorios de la especificación del curso y la política de autoría de la ACM. La IA no es autora: los dos integrantes
responden por la exactitud de todo el material, incluido el generado por las herramientas. Los criterios de producto, las reglas
de negocio (`RN-01` a `RN-10`) y la decisión de aceptar cada cambio fueron del equipo.

## Equipo y forma de colaborar

| Integrante | Número de control | GitHub | Contribución acordada | Responsabilidad |
|---|---|---|---|---|
| Chris Aaron Dionisio Estrada | 23111598 | `chrisestrada-bit` | 60 % | Codificación: implementó y corrigió los cambios en colaboración directa con Claude Code |
| Christian Daniel Salazar Mendoza | 23111502 | `Khrixgm` | 40 % | Revisión de errores, pruebas y validación de funcionamiento; revisó y fusionó 15 de los 19 pull requests |

Ambos integrantes co-propusieron las soluciones. El flujo de cada cambio fue el siguiente:

1. El equipo acordaba la solución.
2. Chris la implementaba con Claude Code en una rama y abría el pull request.
3. Christian revisaba el cambio, lo probaba y validaba el funcionamiento.
4. Con la CI en verde, Christian fusionaba el pull request.

## 1. Herramientas y modelos

| Herramienta | Modelo o versión | Quién la usó | Para qué |
|---|---|---|---|
| **Claude Code** (Anthropic) | Claude Sonnet 5.5 y Claude Opus 5.5 | Chris Aaron Dionisio Estrada | Diseño e implementación incremental, pruebas, documentación, auditoría y revisión |
| **GitHub Copilot** | `[CONFIRMAR: versión o modelo configurado en el editor]` | Christian Daniel Salazar Mendoza | Estructura base del frontend, layout, autenticación, formulario de reportes y paneles (commits `493260f`, `41c9551` y `b55bc5a`, 2026-11-21) |
| **graphify** | *Skill* de Claude Code | Chris Aaron Dionisio Estrada | Grafo de dependencias del repositorio (`graphify-out/`) para consultarlo sin releer archivos; se actualizó al inicio o al cierre de cada fase |
| **Impeccable** | *Skill* de Claude Code | Chris Aaron Dionisio Estrada | Revisión de diseño de hojas de estilo y componentes nuevos |

## 2. Harness y modo de uso

* **Claude Code:** modo agente que edita archivos y ejecuta comandos (pruebas, migraciones, Git) desde la terminal (CLI) en
  Windows, con permisos aprobados por el usuario. Se trabajó **una fase por vez**, con revisión humana y commit propio entre
  fases.
* **GitHub Copilot:** autocompletado y chat dentro del editor `[CONFIRMAR: IDE, p. ej. Visual Studio Code]`.

## 3. Archivos de contexto e instrucciones

| Archivo o recurso | Uso |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Stack obligatorio, reglas de negocio RN-01 a RN-10, seguridad, idioma y flujo de Git |
| *Skills* de Claude Code | `graphify`, `impeccable`, `vercel-react-best-practices`, `vercel-composition-patterns` (citados en `CLAUDE.md` §5) |
| Servidor MCP `chrome-devtools` | Revisión en navegador real, viewport de 360 px, Lighthouse y verificación de respuestas 403 |
| `graphify-out/` | Grafo del repositorio que consultó el asistente antes de leer varios archivos |

No se usaron `AGENTS.md`, `.github/copilot-instructions.md` ni reglas de Cursor.

## 4. Bitácora de prompts significativos

El prompt se resume con fidelidad a partir del mensaje del commit y de la sección por fases de este documento. Los prompts
completos no se conservaron.

| Fecha | Integrante | Herramienta / modelo | Prompt (resumen) | Archivos afectados | Ajustes humanos |
|---|---|---|---|---|---|
| 2026-11-21 | Chris | Claude Code / Opus | Definir modelo de datos, contrato de API y plantilla de variables a partir de `CLAUDE.md` | `docs/arquitectura.md`, `docs/api-contract.md`, `.env.example` | Revisión de reglas RN-01 a RN-10 y de la matriz de acceso |
| 2026-11-21 | Christian | GitHub Copilot | Layout, autenticación, banner de lluvia, formulario de reportes y paneles de moderación | `frontend/src/` (`pages/`, `components/`, `context/`) | Se corrigió después la redirección en 401 del inicio de sesión (`ae9eefb`) |
| 2026-11-21 | Chris | Claude Code / Sonnet | Implementar la API FastAPI por capas con migraciones Alembic, semilla y pruebas | `backend/app/`, `db/`, `backend/tests/` | Revisión de la máquina de estados y de los esquemas públicos sin datos personales |
| 2026-11-22 | Chris | Claude Code / Sonnet | Contenedor del frontend, Compose completo y pipeline de CI | `frontend/Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml` | Node 22 LTS en CI tras el fallo con Vitest 5 (`8e5e5ff`) |
| 2026-11-22 | Chris | Claude Code / Sonnet y Opus | Requisitos opcionales, fases 1 a 4 (fotos, mapa, CSV/XML, WebSocket, PWA, cuadrillas, Kubernetes, Vitest y Playwright) | `backend/`, `frontend/`, `db/migrations/`, `infra/k8s/` | Tope de 5 MB, XML sin entidades externas, caché sin tokens, motivo de rechazo obligatorio (ver «Requisitos opcionales») |
| 2026-11-22 | Chris | Claude Code / Opus | Auditoría de seguridad de sólo lectura y corrección de hallazgos | `backend/app/core/`, `backend/tests/`, `docs/auditoria-final/` | Quitar el valor por omisión de `SEED_PASSWORD`; documentar en lugar de forzar la configuración de Render |
| 2026-11-23 | Chris | Claude Code / Opus 5.5 | Rechazar imágenes anómalas y cubrir archivos disfrazados, políglotas, bombas y *path traversal* | `backend/app/services/imagenes.py`, `backend/tests/test_seguridad_fotos.py` | Revisión de los límites `MAX_LADO_PX` y `MAX_PIXELES` |
| 2026-11-25 | Chris | Claude Code / Opus | Identidad visual con dos temas y portada editorial | `frontend/src/styles/`, `frontend/src/components/` | Paleta y tipografía elegidas por el equipo; íconos y texto además del color |
| 2026-11-25 | Chris | Claude Code / Sonnet 5.5 | Botón «Instalar app» e instalación guiada por navegador | `frontend/src/hooks/useInstalacion.ts`, `InstalarApp.tsx`, `escritorio.css` | El botón se muestra siempre; si no hay aviso nativo, abre la guía |
| 2026-11-26 | Chris | Claude Code / Opus 5.5 | Generar el borrador del reporte técnico y la autoevaluación a partir de la especificación y el repositorio | `docs/REPORTE_BORRADOR.md`, `docs/AUTOEVALUACION.md`, `docs/REPORTE.docx`, `docs/REPORTE.pdf`, este archivo | El equipo confirmó integrantes, números de control y porcentajes de contribución, y revisa los párrafos de autoevaluación |

La validación de cada fila la hizo Christian Daniel Salazar Mendoza antes de fusionar el pull request correspondiente.

## 5. Marcado en commits

Los commits asistidos llevan una línea final `Assisted-by: <herramienta/modelo>` o `Co-Authored-By: <modelo>`. Según el
historial del 2026-11-26, **29 de 37 commits sin merge** están marcados: 26 de Claude Code y 3 de GitHub Copilot. Cuatro de los de Claude Code llevan
ambos pies. Hay 8 commits sin marca:

* Sin IA: `2ee4a8e` (commit inicial), `1aa0ba7` (estructura del monorepo) y `3a98a35` (estructura base del frontend).
* Asistidos con Claude Code sin el pie: `ce9b869` (PR #37, descrito en «PR #37 y #38») y `2e75cc0` (*cherry-pick* del
  autocompletado, descrito en «Cierre v1.1.1»).
* Por confirmar: `8d0bc32`, `55831dd` y `7263df5`. `[CONFIRMAR: si fueron asistidos, se declaran aquí como Claude Code.]`

## 6. Estimación por carpeta

Se midió la proporción de líneas agregadas en commits marcados frente al total de líneas agregadas en cada carpeta. Es una cota
superior, porque un commit marcado también incluye ajustes humanos.

| Carpeta | Líneas en commits marcados / totales | Código generado por IA (aprox.) |
|---|---|---|
| `frontend/` (sin `package-lock.json`) | 9 808 / 11 213 | ≈ 87 % |
| `backend/` | 10 819 / 10 819 | ≈ 100 %, con revisión y ajustes humanos |
| `db/` | 1 578 / 1 578 | ≈ 100 %, con revisión y ajustes humanos |
| `infra/` | 545 / 545 | ≈ 100 %, con revisión y ajustes humanos |

## 7. Reflexión crítica

**Un error que introdujo la IA y cómo se detectó.** El código asistido dejó la contraseña de las cuentas semilla como valor por
omisión en `docker-compose.yml` y `.env.example` (hallazgo A1). Además, la documentación que también generó la IA
(`AUDITORIA_OBLIGATORIA.md`) afirmaba que el repositorio no tenía contraseñas. Ninguna prueba falló, porque el defecto no
rompía ninguna funcionalidad. Se detectó en la auditoría final al contrastar lo que decía la documentación con lo que hacía el
código. Se corrigió quitando el valor por omisión: si `SEED_PASSWORD` está vacía, las cuentas reciben una contraseña aleatoria.
Como la cadena sigue en el historial de Git, debe rotarse en producción. Un segundo caso fue un `<form>` anidado en la vista
de moderación: compilaba y pasaba pytest, pero lo detectaron las pruebas E2E de Playwright.

**Qué aprendimos que no habríamos aprendido sin la IA.** La IA produce rápido mucho código coherente y documentación convincente.
Eso nos obligó a separar dos funciones: quien pide el cambio no es quien lo valida. Aprendimos a tratar lo que la IA afirma
sobre su propio código como una hipótesis que se comprueba con una prueba ejecutada. También aprendimos a leer y defender
decisiones que no habríamos tomado solos, como el hash de relleno contra la enumeración de cuentas, los triggers que respaldan
las reglas de negocio y el escape de fórmulas en CSV. Cada una tuvimos que entenderla para poder explicarla en la demo.

## Requisitos opcionales (Fases 1–4)

Se trabajó **una fase por vez**, con revisión humana y commit propio entre fases. Cada fase terminó con la misma verificación:
`alembic upgrade head`, `db/seed.py` dos veces (idempotencia), `pytest backend/tests -v`, `npm run lint` y `npm run build`.

### Fase 1 — Fotografías, mapa y exportación (HU-02.4, HU-04.5, HU-07.3, extras 4.3 y 4.4)

* **La IA generó:** tabla `reporte_fotos` y su migración; validación de imágenes por contenido (*magic bytes*), almacenamiento
  con nombres UUID y acceso controlado; endpoint de mapa con los filtros de la consulta; exportación CSV (UTF-8 con BOM y
  protección contra inyección de fórmulas) y XML validado con XSD; importación XML de catálogos; componentes de React
  (selector de fotos, mapa con Leaflet y agrupación).
* **Decisiones revisadas por personas:** tope exacto de 5 MB, fotos privadas mientras el reporte está `Recibido`, importación XML
  transaccional y sin entidades externas (XXE), proveedor de mosaicos OpenStreetMap con atribución.

### Fase 2 — Recurrentes, avisos, tiempo real y PWA (HU-03.4, HU-08.2, HU-08.3, HU-08.4, extra 4.5)

* **La IA generó:** cálculo de puntos recurrentes (radio de 50 m, días distintos en hora de Juárez); notificaciones creadas en
  la misma transacción del cambio de estado; canal WebSocket con latido, deduplicación y respaldo por sondeo cada 15 s;
  `manifest.webmanifest`, Service Worker, cola de envíos sin conexión con `idempotency_key` y los íconos PWA (generados con
  código, sin imágenes de terceros).
* **Decisiones revisadas por personas:** la caché nunca guarda tokens ni respuestas autenticadas; un borrador rechazado se
  conserva con su motivo; el WebSocket sólo transmite datos públicos.

### Fase 3 — Operación y catálogos (HU-05.3, HU-05.4, HU-05.5, HU-06.3, HU-01.4, HU-04.6, HU-07.2)

* **La IA generó:** fusión atómica de duplicados; cuadrillas con historial de asignaciones; rol `enlace_municipal` con
  aislamiento por cuadrilla; catálogos administrables; colonias de interés; revisión de trayecto (distancia punto–polilínea con
  respaldo si falla el proveedor de rutas); resumen público por colonia; y los datos semilla, incluida la cuenta
  `enlace@ejemplo.mx`.
* **Decisiones revisadas por personas:** rechazar exige un motivo activo del catálogo; los encharcamientos no se fusionan; una
  cuenta suspendida recibe `403`; las cuadrillas con trabajo pendiente no se eliminan, se desactivan.

### Fase 4 — Kubernetes y pruebas del frontend (extras 4.1 y 4.2)

* **La IA generó:** manifiestos de `infra/k8s/`, `docs/kubernetes.md` y el validador `infra/validar_k8s.py`; configuración de
  Vitest y Playwright, 39 pruebas de componentes/lógica, pruebas E2E de los cuatro flujos pedidos, y los jobs nuevos de CI.
* **Hallazgo útil de las pruebas E2E:** detectaron un defecto real que las pruebas de backend no ven (un `<form>` anidado en
  moderación), corregido y cubierto con una prueba de regresión.

## Mantenimiento posterior a `v1.1.0` (PR #33–#38) y cierre `v1.1.1`

`v1.1.0` quedó publicada en `f831eb4` (PR #32) y no se reescribe; los cambios siguientes se cierran con la etiqueta `v1.1.1`.

### PR #33 y #34 — Auditoría final, seguridad y fotos

* **La IA generó:** la auditoría de `docs/auditoria-final/` (hallazgos A1–A4, M1–M9, B1–B6); el endurecimiento de sesión, límites
  por IP, cabeceras y tamaño de cuerpo; el limpiado de EXIF/GPS y del nombre original de las fotos (`db/limpiar_fotos.py`); el
  rechazo de imágenes con dimensiones anómalas (`MAX_LADO_PX`, `MAX_PIXELES`); y pruebas de regresión para archivos disfrazados,
  políglotas, «bombas» de descompresión y *path traversal*.
* **Decisiones revisadas por personas:** quitar el valor por omisión de `SEED_PASSWORD`; documentar, en lugar de forzar, la
  configuración de Render (`TRUSTED_PROXY_HOPS`/`CLIENT_IP_HEADER`, disco persistente para `UPLOADS_DIR`).

### PR #35 — Identidad visual

* **La IA generó:** los temas «Claro editorial» (claro) y «Grafito turquesa» (oscuro), la portada editorial y los tokens de
  color compartidos por ambos temas.
* **Decisiones revisadas por personas:** la paleta y la tipografía; mantener íconos y texto además del color (`RNF-02`).

### PR #36 — Pulido de portada y ajustes E2E

* **La IA generó:** radar en «Mi zona», cabecera sin desbordes, foco visible en la píldora de búsqueda, filas compactas y
  búsqueda en vivo; además acotó las aserciones E2E del mapa a la región de reportes.
* **Hallazgo útil de las pruebas E2E:** las aserciones del mapa coincidían con elementos fuera de la región de reportes; se
  acotaron sin debilitar lo que validan.

### PR #37 y #38 — Instalación PWA y distribución de escritorio

* **La IA generó:** el hook `useInstalacion`, el botón «Instalar app» junto a la marca, el apartado de instalación en el pie de
  página (con instrucciones para iPhone/iPad) y la agrupación de acciones de la cabecera en escritorio (`escritorio.css`).
* **Decisiones revisadas por personas:** el botón se muestra siempre; si el navegador no ofrece el aviso automático, lleva al
  apartado del pie en lugar de desaparecer.

### Cierre `v1.1.1` (rama `chore/auditoria-final-v1-1`)

* **Se integraron dos ramas pendientes** con `git cherry-pick -x`:
  - `55333f1` (`fix/autocompletado-trayecto`): autocompletado accesible (combobox/listbox) en origen y destino de `/trayecto`.
    Hubo un conflicto sólo de CSS en `pages.css`: se conservó lo de `main` y se añadió el bloque del autocompletado. La regla
    `.hero-map .hm-label` de la rama no se recuperó porque `main` ya no tiene ese elemento.
  - `4bae380` (`fix/clima-user-agent`): `User-Agent` para Open-Meteo (defecto D-10), fechas de caché sin zona tratadas como UTC
    (RN-02) y hora de actualización en el aviso de clima.
* **Corrección menor:** comentario con mojibake en `frontend/src/main.tsx`.
* **Documentación:** `README.md`, este archivo y `docs/auditoria-final/` (00, 01 y 06).
* **Verificación:** ver `docs/auditoria-final/00-resumen-ejecutivo.md`.

## Qué se verificó y cómo

* Las pruebas automatizadas (pytest, Vitest, Playwright) **se ejecutaron**, no sólo se escribieron; sus resultados están en los
  reportes de cada fase y en los artefactos de CI.
* Las pruebas se corrigieron cuando fallaron **por un defecto del código**; cuando el fallo era del propio supuesto de la prueba
  (por ejemplo, datos que crecen en la base de pruebas), se hizo la prueba más robusta, sin debilitar lo que valida.
* Los manifiestos de Kubernetes se validaron de forma **estática** (esquema oficial offline y coherencia entre objetos). **No se
  desplegaron en un clúster real** durante el desarrollo asistido: esa comprobación queda pendiente para quien tenga un clúster.

## Riesgos y límites que se tuvieron presentes

* **Privacidad:** ninguna respuesta pública ni evento de WebSocket incluye nombre, correo ni identificadores del autor (RN-04);
  hay pruebas que lo comprueban.
* **Secretos:** no se escribió ningún secreto real; las plantillas usan valores ficticios y el `Secret` de Kubernetes se crea
  con valores propios en el momento del despliegue.
* **Servicios externos:** OpenStreetMap, OSRM, Open-Meteo y LocationIQ no tienen SLA garantizado en sus versiones públicas; el
  sistema degrada con elegancia (línea recta, catálogo local, caché) y la documentación indica qué sustituir en producción.
* **Revisión humana pendiente recomendada:** las pantallas nuevas no se auditaron aún con Lighthouse ni en dispositivos reales.
