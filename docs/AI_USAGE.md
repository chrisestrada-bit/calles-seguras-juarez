# Uso de asistentes de IA

Este documento declara cómo se usó IA en el proyecto, qué produjo y cómo se verificó. Los criterios de producto, las reglas de
negocio (`RN-01` a `RN-10`) y la decisión de aceptar cada cambio fueron de las personas del equipo.

## Herramientas

| Herramienta | Uso |
|-------------|-----|
| **Claude Code** (modelos Claude Sonnet 5.5 y Opus 5.5 de Anthropic) | Diseño e implementación incremental, pruebas, documentación y revisión |
| **graphify** | Grafo de dependencias del repositorio para consultarlo sin releer archivos; se actualizó al inicio o al cierre de cada fase |
| **Impeccable** (revisión de diseño) | Revisión automática de las hojas de estilo y componentes nuevos para mantener la identidad visual |

Los commits asistidos llevan el pie `Co-Authored-By` de la herramienta, según `CLAUDE.md`.

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
