# Auditoría obligatoria — Calles Seguras Juárez (AEB-1055)

## 1. Datos generales

| Campo | Valor |
|---|---|
| Proyecto | Calles Seguras Juárez — plataforma ciudadana de baches y encharcamientos |
| Fecha de auditoría | 2026-11-22 |
| Rama / commit auditado | `docs/auditoria-obligatoria` sobre `1beecb1` (merge PR #28). **Re-verificación de cierre:** rama `fix/cierre-auditoria-y-cp` sobre `aaa2e11` (merge PR #30), ver §1.3. |
| Frontend en producción | `https://calles-seguras-juarez.vercel.app` |
| API en producción | `https://calles-seguras-juarez-api.onrender.com/api/v1` |
| Fuentes de evidencia | `docs/evidencia_backend_auditoria.md` (peticiones HTTP reales, IDs `A*`, `R*`, `T*`, `D*`, `E*`, `S*`, `L*`, `P*`, `W*`), `docs/evidencia_frontend_auditoria.md` (navegador real con Chrome DevTools MCP y Lighthouse; defectos `FE-01`…`FE-14`), y verificación directa del repositorio en esta auditoría (sección 1.1). |
| Escala | `Cumple` · `Parcial` · `No cumple` · `No evaluado` |

### 1.1 Verificaciones ejecutadas en esta auditoría (repositorio)

| Verificación | Comando | Resultado |
|---|---|---|
| Arranque con contenedores | `docker compose -p csj-auditoria up --build -d --wait` (puertos 55432/18000, proyecto aislado) | `rc=0` en **26 s**; `db` y `backend` `Healthy`; `GET /salud` → `200 {"estado":"ok"}`; `GET /api/v1/reportes` → 200 en 0.015 s, `total: 211`. Capas de imagen ya en caché (no se midió una construcción en frío). Entorno destruido con `down -v`. |
| Pruebas backend | `alembic upgrade head` + `db/seed.py` sobre `calles_seguras_test`; `python -m pytest -q` en `backend/` | **118 passed in 7.70 s** (29 pruebas de API en `tests/test_api.py` + unitarias en `tests/test_unitarias.py`). |
| Build frontend | `npm run build` (`tsc -b && vite build`) | Compila sin errores; bundle JS 286.32 kB (83.86 kB gzip). |
| Lint frontend | `npm run lint` (`oxlint`) | 0 errores, 4 advertencias `react(set-state-in-effect)` (`AdminPages.tsx:29,31`, `AdminColoniasPage.tsx:94`, `ReportCreatePage.tsx:43`). |
| CI | `ls .github/workflows` | Sólo `.gitkeep`: **no hay workflows**. |
| Etiquetas | `git tag` | **Vacío** (no existe `v1.0.0`). |
| `AI_USAGE.md` | `wc -l AI_USAGE.md` | **0 líneas**. |
| `README.md` | `cat README.md` | 2 líneas (título y nombres); sin instrucciones de instalación ni despliegue. |
| `infra/` | `git ls-files infra` | Sólo `.gitkeep`. Único Dockerfile: `backend/Dockerfile`. `docker-compose.yml` sin servicio de frontend. |
| Conventional Commits | `git log --no-merges` | 9 de 10 commits con prefijo convencional (`2ee4a8e Initial commit` es el inicial de GitHub). Sin pie `Assisted-by`: `3a98a35`, `1aa0ba7`. |
| Secretos | `git grep` | `.env` no versionado (ignorado en `.gitignore:153`). Contraseña de semilla por omisión `Juarez2026` escrita en `db/seed.py:58`, `docker-compose.yml:53` y `.env.example:75`. |
| Dependencias | `backend/requirements.txt` | Versiones fijas (`==`). Frontend con rangos `^` y `package-lock.json`. |

### 1.3 Re-verificación de cierre (2026-11-22, rama `fix/cierre-auditoria-y-cp`)

| Verificación | Comando | Resultado |
|---|---|---|
| Migraciones y semilla | PostgreSQL 16 desechable (`postgres:16-alpine`, base `calles_seguras_test`); `alembic -c db/alembic.ini upgrade head` y `python db/seed.py` dos veces | `0001 → 0002` sin error. Semilla: 6 sectores, **119 colonias** (99 con código postal 32000–32730), **580 reportes** (546 públicos; 34 `Rechazado`). Segunda ejecución: 0 colonias nuevas y «Ya existen 580 reportes: no se vuelven a sembrar». Sobre una colonia con CP antiguo (`Felipe Ángeles` = `32090`) la semilla lo corrigió a `32100` sin duplicarla. Sin `SEED_PASSWORD` no falla ni revela contraseña. |
| Pruebas backend | `python -m pytest backend/tests -q -rs` contra esa base | **131 passed in 15.01 s**, 0 omitidas (118 previas + 13 de regresión en `tests/test_correcciones_auditoria.py`). |
| Lint frontend | `npm run lint` (`oxlint`) | **0 errores, 0 advertencias** (antes de esta rama había 12: las 4 citadas en D-26 más 8 surgidas con el rediseño). |
| Build frontend | `npm run build` (`tsc -b && vite build`) | Compila sin errores; JS 347.93 kB (99.08 kB gzip), CSS 87.29 kB. |
| Dependencias (OWASP A03) | `pip-audit -r backend/requirements.txt`; `npm audit --audit-level=high` | «No known vulnerabilities found»; «found 0 vulnerabilities». Ambos pasos quedan en el job `dependencias` de `.github/workflows/ci.yml`. |
| Humo HTTP | API (`uvicorn`) + Vite contra la base de prueba | `GET /catalogos/colonias?q=32310` → 200; `GET /geocoding/buscar?q=32000` → 200 `catalogo_local`; `GET /geocoding/inversa` dentro de Juárez → 200, fuera → `422 FUERA_DE_JUAREZ`; `GET /indicadores/longevidad` → 200; preflight CORS de `PATCH` desde el origen del frontend → 200. |
| Navegador (Chrome DevTools MCP) | — | **No ejecutado:** el perfil del navegador del MCP estaba en uso por otra instancia. Queda pendiente medir 360 px, Lighthouse y el aspecto visual de las vistas nuevas (aviso de privacidad, edición, filtros). |

Fuente de los códigos postales: catálogo de SEPOMEX consultado en micodigopostal.org (páginas por código postal, 2026-11-22). Las coordenadas del centro de cada colonia son aproximadas. Samalayuca (32730) y San Isidro Río Grande (32720) quedan fuera del recuadro de RN-01 (latitud ≥ 31.45, longitud ≤ −106.25) y no se siembran.

### 1.2 Limitaciones

- El **Documento 1 de Auditoría no está en el repositorio**. La estructura de este informe se reconstruyó a partir de los IDs citados en las instrucciones. Los títulos de HU y RNF se infirieron de `CLAUDE.md`, `docs/arquitectura.md`, `docs/api-contract.md` y las auditorías previas.
- Los casos **`F-01` a `F-14`** del Documento 1 no tienen definición disponible: se marcan `No evaluado`. Los IDs `FE-01`…`FE-14` de `docs/evidencia_frontend_auditoria.md` son defectos internos de esa auditoría, **no** los casos oficiales.
- `RNF-03`, `RNF-04` y `RNF-07` no tienen definición en ninguna fuente del repositorio: `No evaluado`. `RNF-09` se interpretó como volumen de datos de demostración (sección 6.3 del Documento 1, según las instrucciones de la auditoría de backend).
- Los criterios `CA1`–`CA5` de `HU-07.1` no están definidos en el repositorio.

## 2. Historias de usuario indispensables (`HU-01.1` a `HU-08.1`)

| ID | Criterio (resumen) | Estado | Evidencia verificable | Motivo si no cumple (causa raíz) |
|---|---|---|---|---|
| HU-01.1 | Iniciar sesión con mensaje genérico, JWT 30 min | Cumple | Backend A1/A2: `401 CREDENCIALES_INVALIDAS` idéntico para contraseña mala y correo inexistente; token de 1800 s. Frontend: «Correo o contraseña incorrectos.»; logout limpia almacenamiento y Atrás no muestra datos. | — |
| HU-01.2 | Registro con política de contraseña y aceptación del aviso de privacidad | Cumple | Backend: `acepta_aviso_privacidad` obligatorio y `true` en `RegistroIn`; sin él o en `false` → 422 «Debes aceptar el aviso de privacidad…»; se guarda `usuarios.aviso_privacidad_aceptado_at` (migración 0002). Pytest `test_registro_exige_aceptar_aviso_de_privacidad`. Frontend: ruta `/aviso-de-privacidad` (`PrivacyNoticePage.tsx`) y el registro envía el consentimiento. | — (D-06 y D-07 corregidos; vista nueva sin revisión visual en navegador, §1.3). |
| HU-01.3 | Roles únicos; control de acceso con 403 | Cumple | Backend R1–R5, R4c: ciudadano/moderador → 403 en moderación y admin; visitante → 401; `rol` en registro → 422 (A6). Pytest `test_sin_token_401_y_rol_incorrecto_403`, `test_admin`. | — (observación: `PATCH`/`DELETE` de reportes responden 405 y no 403 porque la operación no existe para ningún rol). |
| HU-02.1 | Reportar con ubicación dentro de Juárez | Cumple | Backend T1/T1b + `GET /geocoding/inversa` (422 fuera de Juárez) y búsqueda por código postal con catálogo local. Pytest `test_geocoding_inversa_dentro_de_juarez`, `test_geocoding_por_codigo_postal`, `test_fallback_de_geocoding_no_remite_a_un_mapa`. Frontend: tras el GPS se sugieren calle y colonia; el mensaje degradado ya no remite a un mapa inexistente. | — (D-13 corregido en código). Observación operativa: la búsqueda de direcciones exactas en producción depende de `GEOCODING_API_KEY` en Render (no verificable desde el repositorio); sin ella funcionan GPS, colonia y código postal. |
| HU-02.2 | Formulario dinámico por tipo de daño y descripción ≤ 500 | Cumple | Backend T2–T7: campos obligatorios por tipo, severidad del cliente rechazada, alcantarilla `Alta`, 501 caracteres → 422. Frontend: campos cambian por tipo; contador `0/500`. Pytest `test_validaciones_formulario_dinamico`. | — |
| HU-02.3 | Duplicado de bache ≤ 30 m y confirmación única | Cumple | Backend D1–D5b: 20 m → 409; 40 m → 201; doble confirmación → 409; autoconfirmación → 400. Pytest `test_duplicado_bache_30_metros`, `test_confirmar_bache`. Aviso de duplicado en UI verificado sólo por código (`hayDuplicados`, `forzar_nuevo`). | — |
| HU-02.5 | Mis reportes: paginación de 10 y edición sólo en `Recibido` | Cumple | Backend: `PATCH /reportes/{folio}` sólo para el autor y sólo en `Recibido` (403 a terceros, 409 `REPORTE_NO_EDITABLE` tras validar, 422 en campos inmutables o ajenos al tipo); severidad recalculada; sin historial nuevo. Pytest `test_editar_reporte_recibido_solo_autor`, `test_encharcamiento_no_es_editable`. Frontend: `/reportar?editar=FOLIO` abre `ReportEditPage.tsx`. | — (D-08 corregido). |
| HU-03.1 | Reportar encharcamiento; duplicado ≤ 50 m; pregunta de riesgo si intransitable | Cumple | Backend E1–E3, T4: 45 m → 409; 60 m → 201; intransitable sin riesgo → 422. Pytest `test_duplicado_encharcamiento_50_metros`. | — |
| HU-03.2 | «Sigue ahí» reinicia vigencia de 6 h; autor no confirma | Cumple | Backend E4/E5: autor → 400. Pytest `test_sigue_ahi_reinicia_6_horas_y_votos` y `test_vencimiento_a_las_6_horas_se_evalua_en_consulta` (118 passed). Código `services/confirmaciones.py:93-98`, `services/vigencia.py:20-45`. | — |
| HU-03.3 | 3 «Ya no hay agua» de usuarios distintos → `Histórico` | Cumple | Backend E6–E10b: tercer usuario distinto → `Histórico`, historial con origen `sistema`; repetición del mismo usuario → 409. Pytest `test_encharcamiento_tres_desmentidos_lo_pasan_a_historico`. | — |
| HU-04.1 | Lista pública con tipo, calle, colonia, severidad/nivel y antigüedad, sin PII | Cumple | `ReportCard.tsx`: tipo con ícono y texto, calle, colonia, folio, severidad con medidor (o «Intransitable»), nivel del agua en encharcamientos y antigüedad (`longevidad_dias`). Sin PII (RN-04). | — (D-14 corregido). |
| HU-04.2 | Filtros combinados, búsqueda parcial, paginación 20, limpiar filtros | Cumple | `PublicHomePage.tsx`: calle/folio, tipo, estado, **colonia** (catálogo completo agrupado por sector), **desde/hasta** y botón **«Limpiar filtros»**; todos se combinan en `GET /reportes` (`colonia_id`, `desde`, `hasta`), 20 por página. | — (D-15 corregido; sin revisión visual en navegador, §1.3). |
| HU-04.3 | «¿Cómo está mi zona?» en 1 km, del más cercano al más lejano, distancia visible, intransitable resaltado | Cumple | `ZoneSection.tsx`: Haversine en 1 km, orden ascendente por distancia, distancia visible en cada tarjeta («a 240 m»), alerta de calles intransitables y tarjeta `report-card--critical`. | — (D-09 corregido). |
| HU-04.4 | Detalle con datos del daño, longevidad en días e historial | Cumple | `ReportDetailPage.tsx`: severidad, fecha (hora de Juárez), **longevidad** («N días sin reparar / hasta su reparación»), sector, tamaño/profundidad/carril, señalización, nivel de agua y riesgo, referencia, fechas programada y de reparación; «Descripción» sólo si existe; historial. | — (D-16 corregido). |
| HU-05.1 | Bandeja de moderación | Cumple | Frontend `/moderacion` (coordinador): cola con folio, tipo, ubicación, severidad, confirmaciones, fecha y transiciones por rol. Backend R1: ciudadano → 403. | — |
| HU-05.2 | Transiciones de estado, motivo de rechazo, fecha de reparación | Cumple | Backend S0–S13: matriz RN-05 completa, fechas inválidas → 422, rechazo sin motivo → 422. Frontend `/coordinacion`: acciones Programado/En reparación con fecha. Pytest `test_maquina_de_estados_completa`. | — |
| HU-06.1 | Administración de colonias | Parcial | Frontend `/admin/colonias`: filtros (nombre **o código postal**), Editar/Desactivar, «Nueva colonia» con CP validado 32000–32730. Backend: CP fuera de rango → 422 (`test_admin`). La tabla está dentro de `.admin-table-wrap` con `overflow-x: auto` (rediseño PR #29). | Pendiente re-medir el ancho del documento a 360 px en navegador (D-17); en esta rama no se modificó el CSS. |
| HU-06.2 | Administración de usuarios y roles | Parcial | Frontend `/admin/usuarios`: filtros, cambio de rol, Suspender/Reactivar. Backend R2/R4/R4c: no coordinador → 403. Pytest `test_admin`. | Igual que HU-06.1: pendiente re-medir a 360 px (D-17). |
| HU-07.1 | Tablero de indicadores (`CA1`–`CA5`) | Cumple | `/tablero`: filtros Desde/Hasta/Zona, totales, desglose por estado, **desglose por tipo de daño**, **longevidad promedio de abiertos** y tabla de los más antiguos (consume `/indicadores/longevidad`), gráfica de barras por sector y tabla equivalente. | — (D-18 corregido). Observación: `CA1`–`CA5` siguen sin definición en el repositorio (§1.2). |
| HU-08.1 | Pronóstico de lluvia con caché de 1 h y degradación elegante | Parcial | TTL **60 min** (`core/config.py`, `.env.example`, `docker-compose.yml`); tras un fallo del proveedor no se reintenta en 5 min y se sirve la caché marcada `desactualizado`. Pytest `test_ttl_de_clima_es_de_una_hora`, `test_clima_no_reintenta_durante_el_retroceso`, `test_clima_cache_y_degradacion`. | D-12 y D-24 corregidos. Sigue pendiente D-10: el fallo de Open-Meteo desde Render es operativo y no se puede verificar desde el repositorio. |

## 3. Reglas de negocio (`RN-01` a `RN-10`)

| ID | Regla | Estado | Evidencia verificable | Motivo si no cumple (causa raíz) |
|---|---|---|---|---|
| RN-01 | Sólo coordenadas dentro de Juárez | Cumple | Backend T1 (`32.5,-107.0`) y T1b (`31.4499`) → `422 FUERA_DE_JUAREZ` con rango. `services/geo.py:5-6`; CHECK en BD. Pytest `test_fuera_de_juarez_422`. | — |
| RN-02 | UTC en BD; mostrar en `America/Ciudad_Juarez` | Cumple | API emite `-07:00`. Frontend: todo formateo de fechas pasa por `utils/formato.ts` con `timeZone: 'America/Ciudad_Juarez'` (las fechas de calendario se muestran sin desplazamiento); `grep` no encuentra `toLocale*` sin `timeZone`. | — (D-19 corregido). |
| RN-03 | Folios únicos `BCH-`/`ENC-YYYY-NNNNNN` | Cumple | Backend T7/T8/E1: `BCH-2026-000171…183`, `ENC-2026-000056/57`. Secuencias PostgreSQL (`services/folios.py`); trigger `fn_reportes_inmutables`. | — |
| RN-04 | Sin PII en vistas públicas | Cumple | Backend R8/verificación por regex: sin `usuario_id`, correo, nombre, hash ni token. Frontend: tarjetas y detalle sin datos del autor. Pytest `test_respuestas_publicas_sin_datos_personales`. | — |
| RN-05 | Máquina de estados estricta | Cumple | Backend S0–S10: inválidas → 400; rol no autorizado → 403. `services/transiciones.py:11-17` + trigger `fn_reportes_transicion`. | — |
| RN-06 | Vigencia de 6 h y 3 desmentidos | Cumple | Backend E6–E10. Pytest `test_sigue_ahi_reinicia_6_horas_y_votos`, `test_vencimiento_a_las_6_horas_se_evalua_en_consulta`. Vencimiento también cada 300 s (`main.py:21,37`). | — |
| RN-07 | Sin DELETE; historial inmutable; rechazo con motivo | Cumple | Backend R7–R7c → 405; S13 → 422 sin motivo. Triggers append-only (migración 0001). Pytest `test_delete_prohibido_y_base_de_datos_inmutable`. | — |
| RN-08 | Máx. 10 reportes/hora → 429 | Cumple | Backend L1–L11: 10 × 201 y el 11.º → `429 LIMITE_REPORTES` con `Retry-After`. Pytest `test_limite_de_10_reportes_por_hora`. | — |
| RN-09 | `Recibido` = «Sin validar»; `Rechazado` nunca público | Cumple | Backend T8: `etiqueta_publica: "Sin validar"`; Rechazado → 404 en detalle público. Frontend: el filtro no ofrece `Rechazado`. | — |
| RN-10 | Fecha original inmutable; longevidad en días | Cumple | Backend S3–S9: `longevidad_dias` en respuestas; trigger impide cambiar `created_at`. (La falta de visualización en el detalle se registra en HU-04.4.) | — |

## 4. Requisitos no funcionales (`RNF-01` a `RNF-09`)

| ID | Requisito | Estado | Evidencia verificable | Motivo si no cumple (causa raíz) |
|---|---|---|---|---|
| RNF-01 | Responsivo de 360 px a escritorio | Parcial | Frontend: `/`, `/reportar`, `/mi-zona`, `/moderacion`, `/tablero` sin desbordamiento a 360 px (auditoría previa). Tablas administrativas dentro de contenedor con desplazamiento horizontal. | Pendiente re-medir `/admin/*` y la cabecera a 360 px en navegador (D-17, D-23); no se pudo usar Chrome DevTools MCP en el cierre (§1.3). |
| RNF-02 | WCAG 2.2 AA; Lighthouse ≥ 90 | Parcial | Lighthouse `/` previo: 100/100/100. `index.html` con `lang="es-MX"`. Controles nuevos con `label` vinculado, `aria-describedby`, texto además de color. | Falta Lighthouse en vistas autenticadas y nuevas, y re-medir objetivos táctiles a 360 px (D-23). |
| RNF-03 | (sin definición disponible) | No evaluado | — | Definición no presente en el repositorio. |
| RNF-04 | (sin definición disponible) | No evaluado | — | Definición no presente en el repositorio. |
| RNF-05 | Seguridad: hash, JWT, 403 por rol | Cumple | Argon2id (`core/security.py`), JWT 30 min con `token_version` (logout revoca), bloqueo tras 5 intentos. Backend R1–R11. Pytest `test_cerrar_sesion_revoca_token`, `test_bloqueo_por_intentos_fallidos`. | — |
| RNF-06 | Respuesta < 3 s | Cumple | Backend P*: `/reportes` 0.12–0.61 s; `/indicadores/resumen` 0.12–0.13 s. Lighthouse LCP 0.8 s móvil / 0.2 s escritorio. | — |
| RNF-07 | (sin definición disponible) | No evaluado | — | Definición no presente en el repositorio. |
| RNF-08 | Todo en español de México | Cumple | `lang="es-MX"` y título «Calles Seguras Juárez» en `index.html`; aviso de `/coordinacion` reescrito en lenguaje ciudadano; mensajes nuevos de API y UI en español. | — (D-20 y D-22 corregidos). |
| RNF-09 | Datos de demostración (≥ 20 colonias, ≥ 500 reportes) *(interpretado)* | Cumple | Semilla: 119 colonias, 580 reportes (546 públicos). Pytest `test_volumen_de_datos_de_demostracion`. La semilla completa la meta en bases ya sembradas (p. ej. producción con 225). | — (D-05 corregido; producción se actualiza al volver a ejecutar la semilla en el despliegue). |

## 5. Requisitos técnicos (Sección 6 del Documento 1)

| ID | Requisito | Estado | Evidencia verificable | Motivo si no cumple (causa raíz) |
|---|---|---|---|---|
| 6.1 | Arquitectura y planificación | Cumple | `docs/arquitectura.md` (567 líneas: diagramas, modelo de datos, mapeo RN→implementación, OWASP), `docs/api-contract.md` (1321 líneas). Backend en capas `routers/`, `services/`, `models/`, `schemas/`. | — |
| 6.2 | Frontend React + TypeScript (Vite), HTML semántico, CSS externo, estados de carga/error/vacío | Cumple | `npm run build` sin errores; `npm run lint` 0/0; estados de carga/error/vacío en las vistas nuevas mediante `hooks/useCargaDatos.ts`. | — (D-26 corregido). Observación: el enrutamiento sigue siendo manual (`window.location.pathname` en `App.tsx`). |
| 6.3 | Backend FastAPI + Pydantic v2 + SQLAlchemy 2.0 en capas | Cumple | `requirements.txt` (FastAPI 0.165, Pydantic 2.14, SQLAlchemy 2.1); 118 pruebas pasan; evidencia HTTP de backend completa. | — |
| 6.4 | PostgreSQL + Alembic + semilla | Cumple | Migraciones `0001` y `0002` (consentimiento y CP 32000–32730 con índice); semilla idempotente con 119 colonias y 580 reportes (§1.3). | — |
| 6.5 | API externa (clima) con caché y degradación | Parcial | Clima: TTL 60 min, retroceso de 5 min, caché vencida marcada `desactualizado`. Geocodificación: búsqueda por CP e inversa con respaldo local. Pytest de clima y geocodificación pasan. | D-10: el fallo del proveedor de clima desde Render es operativo (revisar logs/variables de Render). |
| 6.6 | Seguridad OWASP A01/A02/A03 (2025) | Cumple | A01: 403 por rol y por autoría (`PATCH` ajeno → 403). A02: sin contraseña por omisión en `db/seed.py`, `docker-compose.yml` ni `.env.example` (se exige `SEED_PASSWORD`; sin ella, contraseña aleatoria no revelada). **Fe de erratas (auditoría final, A1):** la afirmación era incorrecta para `docker-compose.yml` (`${SEED_PASSWORD:-Juarez2026}`) y `.env.example` (`SEED_PASSWORD=Juarez2026`); se corrigió en `fix/registro-y-rate-limit` — ver `docs/auditoria-final/03-hallazgos.md`. A03: job `dependencias` en CI con `pip-audit` y `npm audit --audit-level=high` (ambos limpios en local). | — (D-03 parte A03 y D-21 corregidos). |
| 6.7 | Contenedores; recuperación < 3 min con `docker compose up` | Parcial | `docker compose up --build --wait` → `db` y `backend` sanos en 26 s (con caché), migraciones y semilla automáticas. | No existe Dockerfile de frontend ni servicio de frontend en `docker-compose.yml`; `infra/` vacío (el único Dockerfile está en `backend/`). No se midió una construcción en frío. |
| 6.8 | Pruebas Pytest y CI en GitHub Actions | Cumple | `.github/workflows/ci.yml`: jobs `backend` (PostgreSQL 16, migraciones, semilla, pytest que falla si hay omitidas), `dependencias` (OWASP A03) y `frontend` (lint + build). Local: 131 passed. | — Observación: sin pruebas de frontend; la primera ejecución del job `dependencias` en GitHub queda por confirmar. |
| 6.9 | Repositorio, Conventional Commits, `AI_USAGE.md`, etiqueta `v1.0.0` | No cumple | 9/10 commits convencionales; PRs #23–#28 por ramas `feature/*` y `fix/*`. | `AI_USAGE.md` vacío (0 líneas); no existe etiqueta `v1.0.0`; `README.md` de 2 líneas sin instrucciones; commits `3a98a35` y `1aa0ba7` sin pie `Assisted-by`. |

## 6. Casos de prueba `F-01` a `F-14`

| ID | Estado | Evidencia verificable | Motivo si no cumple (causa raíz) |
|---|---|---|---|
| F-01 | No evaluado | — | Caso definido sólo en el Documento 1, no disponible en el repositorio. |
| F-02 | No evaluado | — | Ídem. |
| F-03 | No evaluado | — | Ídem. |
| F-04 | No evaluado | — | Ídem. |
| F-05 | No evaluado | — | Ídem. |
| F-06 | No evaluado | — | Ídem. |
| F-07 | No evaluado | — | Ídem. |
| F-08 | No evaluado | — | Ídem. |
| F-09 | No evaluado | — | Ídem. |
| F-10 | No evaluado | — | Ídem. |
| F-11 | No evaluado | — | Ídem. |
| F-12 | No evaluado | — | Ídem. |
| F-13 | No evaluado | — | Ídem. |
| F-14 | No evaluado | — | Ídem. |

Para evaluarlos, agregar el Documento 1 (o su lista de casos) al repositorio; la mayoría de las comprobaciones ya están cubiertas por la evidencia de las secciones 2–5.

## 7. Resumen de resultados

| Bloque | Total | Cumple | Parcial | No cumple | No evaluado |
|---|---|---|---|---|---|
| Historias de usuario (HU) | 20 | 17 | 3 | 0 | 0 |
| Reglas de negocio (RN) | 10 | 10 | 0 | 0 | 0 |
| No funcionales (RNF) | 9 | 4 | 2 | 0 | 3 |
| Técnicos (6.1–6.9) | 9 | 6 | 2 | 1 | 0 |
| Casos F-01–F-14 | 14 | 0 | 0 | 0 | 14 |
| **Total** | **62** | **37** | **7** | **1** | **17** |

Resumen tras el cierre del 2026-11-22 (§1.3). Antes: 22 Cumple · 21 Parcial · 2 No cumple · 17 No evaluado.

## 8. Registro de ejecución y defectos

Severidad: **Bloqueante** (impide la entrega o un requisito obligatorio de la rúbrica), **Alta** (criterio de aceptación incumplido), **Media** (cumplimiento parcial visible), **Baja** (calidad o mantenimiento).

| Defecto | ID afectado | Motivo técnico exacto | Archivo / endpoint | Severidad |
|---|---|---|---|---|
| D-01 | 6.9 | No existe la etiqueta `v1.0.0` (`git tag` vacío). | Repositorio | Bloqueante |
| D-02 | 6.9 | `AI_USAGE.md` existe pero tiene 0 líneas. | `AI_USAGE.md` | Bloqueante |
| D-03 | 6.8, 6.6 (A03) | No hay workflow de GitHub Actions (pruebas, build ni escaneo de dependencias). | `.github/workflows/` (sólo `.gitkeep`) | Bloqueante |
| D-04 | 6.7 | Sin Dockerfile de frontend ni servicio de frontend en compose; `infra/` vacío. | `docker-compose.yml`, `infra/`, `frontend/` | Bloqueante |
| D-05 | RNF-09, 6.4 | La semilla genera 225 reportes visibles (< 500). | `db/seed.py:143-144` | Alta |
| D-06 | HU-01.2 | El backend acepta registros sin consentimiento de privacidad. | `backend/app/schemas/auth.py:12-14`, `POST /auth/registro` | Alta |
| D-07 | HU-01.2 | El enlace «aviso de privacidad» lleva a una ruta inexistente que muestra el inicio. | `frontend/src/App.tsx`, `/aviso-de-privacidad` | Alta |
| D-08 | HU-02.5 | «Editar» apunta a `/reportar?editar=…` sin implementación y la API no tiene `PATCH /reportes/{folio}` (405). | `frontend/src/pages/MyReportsPage.tsx`, `ReportCreatePage.tsx`, `backend/app/routers/reportes.py` | Alta |
| D-09 | HU-04.3 | «Mi zona» no ordena por distancia ni muestra la distancia; sin resalte de `intransitable`. | `frontend/src/components/ZoneSection.tsx:46-47` | Alta |
| D-10 | HU-08.1, 6.5 | Producción sirve pronóstico de ≈ 11 h (`desactualizado: true`): la llamada a Open-Meteo falla desde Render. | `GET /clima/pronostico`, `backend/app/services/clima.py:115-122`, variables de Render | Alta |
| D-11 | 6.9 | `README.md` de 2 líneas sin instalación, variables, despliegue ni cuentas de prueba. | `README.md` | Alta |
| D-12 | HU-08.1, 6.5 | TTL de caché de clima de 30 min en lugar de 60. | `backend/app/core/config.py:27`, `.env.example:47`, `docker-compose.yml` | Media |
| D-13 | HU-02.1, 6.5 | Geocodificación degradada en producción; el mensaje remite a un mapa que no existe. | `frontend/src/pages/ReportCreatePage.tsx`, `GET /geocoding/*`, `GEOCODING_API_KEY` en Render | Media |
| D-14 | HU-04.1 | Tarjetas sin colonia, severidad/nivel ni antigüedad. | `frontend/src/components/ReportCard.tsx` | Media |
| D-15 | HU-04.2 | Faltan filtros de colonia y fechas y el botón «Limpiar filtros». | `frontend/src/pages/PublicHomePage.tsx` | Media |
| D-16 | HU-04.4, RN-10 | Detalle sin `longevidad_dias`, severidad ni detalle del daño; «Descripción» vacía. | `frontend/src/pages/ReportDetailPage.tsx` | Media |
| D-17 | HU-06.1, HU-06.2, RNF-01 | Desbordamiento horizontal de página a 360 px (751 px y 786 px). | `/admin/colonias`, `/admin/usuarios`, contenedor de `.admin-table` en `frontend/src/styles/global.css` | Media |
| D-18 | HU-07.1 | Tablero sin longevidad, desglose por tipo ni gráficas; no usa `/indicadores/longevidad`. | `frontend/src/pages/AdminPages.tsx` (`DashboardPage`) | Media |
| D-19 | RN-02 | Fechas formateadas sin `timeZone: 'America/Ciudad_Juarez'`. | `frontend/src/pages/AdminPages.tsx:6`, `ReportDetailPage.tsx`, `MyReportsPage.tsx` | Media |
| D-20 | RNF-08, RNF-02 | `lang="en"` y título «frontend». | `frontend/index.html` | Media |
| D-21 | 6.6 (A02) | Contraseña por omisión de la semilla escrita en código y compose. | `db/seed.py:58`, `docker-compose.yml:53`, `.env.example:75` | Media |
| D-22 | RNF-08 | Texto interno visible para el usuario («HU-02 · HU-03», aviso de «contrato»/«API actual»). | `ReportCreatePage.tsx`, `AdminPages.tsx` (`CoordinationPage`) | Baja |
| D-23 | RNF-02, RNF-01 | Objetivos táctiles < 24 px y cabecera de 261 px a 360 px. | `frontend/src/components/SiteHeader.tsx`, `global.css` | Baja |
| D-24 | 6.5 | Sin retroceso tras fallo del proveedor: cada petición reintenta (timeout 5 s). | `backend/app/services/clima.py:107-122` | Baja |
| D-25 | 6.9 | Commits sin pie `Assisted-by`. | `3a98a35`, `1aa0ba7` | Baja |
| D-26 | 6.2 | 4 advertencias `set-state-in-effect` de oxlint. | `AdminPages.tsx:29,31`, `AdminColoniasPage.tsx:94`, `ReportCreatePage.tsx:43` | Baja |
| D-27 | 6.2 | El rewrite SPA sirve `index.html` en `/robots.txt` (Lighthouse: 14 errores); sin `meta description`. | `frontend/vercel.json`, `frontend/index.html` | Baja |
| D-28 | Documentación | `GET /api/v1/indicadores` responde 404; la ruta real es `/indicadores/resumen`. | `docs/api-contract.md`, `backend/app/routers/indicadores.py` | Baja |
| D-29 | Operación | Datos de prueba residuales en producción que no se pueden rechazar por RN-05/RN-07: `BCH-2026-000172` (`Reparado`), `ENC-2026-000056` (`Histórico`); 3 cuentas `auditoria-0a8363-*` suspendidas. | Base de datos de producción | Baja |

### 8.1 Registro de ejecución

| Fecha | Ejecución | Resultado | Evidencia |
|---|---|---|---|
| 2026-11-22 | Auditoría HTTP del backend en producción (≈ 90 peticiones) | 0 fallos de reglas RN; brechas de privacidad, datos y clima | `docs/evidencia_backend_auditoria.md` |
| 2026-11-22 | Auditoría de frontend en navegador real + Lighthouse | Lighthouse 100/100/100; defectos FE-01…FE-14 | `docs/evidencia_frontend_auditoria.md` |
| 2026-11-22 | `docker compose up --build --wait` (proyecto aislado) | Sano en 26 s; sin frontend | Sección 1.1 |
| 2026-11-22 | `pytest` sobre PostgreSQL de prueba | 118 passed en 7.70 s | Sección 1.1 |
| 2026-11-22 | `npm run build` / `npm run lint` | Build correcto; 0 errores, 4 advertencias | Sección 1.1 |
| 2026-11-22 | Revisión de Git (`log`, `tag`, estructura) | Sin tag, sin CI, `AI_USAGE.md` vacío | Sección 1.1 |
| 2026-11-22 | Cierre: migraciones + semilla (×2) + `pytest` sobre PostgreSQL desechable | 131 passed en 15.01 s; semilla idempotente | Sección 1.3 |
| 2026-11-22 | Cierre: `npm run lint` / `npm run build` | 0 errores, 0 advertencias; build correcto | Sección 1.3 |
| 2026-11-22 | Cierre: `pip-audit` / `npm audit --audit-level=high` | Sin vulnerabilidades | Sección 1.3 |

### 8.2 Estado de los defectos tras el cierre (rama `fix/cierre-auditoria-y-cp`)

| Defecto | Estado | Corrección / motivo |
|---|---|---|
| D-01, D-02, D-11, D-25 | Pendiente | Fuera del alcance de código de esta rama (etiqueta `v1.0.0`, `AI_USAGE.md`, `README.md`, pies `Assisted-by` históricos). |
| D-03 | Corregido | CI con pruebas y build (PR #30) más job `dependencias` con `pip-audit` y `npm audit --audit-level=high`. |
| D-04 | Corregido en PR #30 | `frontend/Dockerfile` y servicio `frontend` en `docker-compose.yml`; no se re-midió el arranque en frío en este cierre. |
| D-05 | Corregido | `N_PAVIMENTO = 420`, `N_ENCHARCAMIENTOS = 160`; la semilla completa la meta en bases existentes. |
| D-06 | Corregido | `acepta_aviso_privacidad` obligatorio en `RegistroIn` + `usuarios.aviso_privacidad_aceptado_at` (migración 0002). |
| D-07 | Corregido | `PrivacyNoticePage.tsx` en `/aviso-de-privacidad`. Los datos de contacto ARCO definitivos debe completarlos la asociación. |
| D-08 | Corregido | `PATCH /reportes/{folio}` + `ReportEditPage.tsx`. |
| D-09 | Corregido | Orden por distancia y distancia visible en `ZoneSection.tsx` / `ReportCard.tsx`. |
| D-10 | Pendiente (operativo) | Requiere revisar logs y salida de red de Render; el código ya degrada sin reintentos en cascada. |
| D-12 | Corregido | TTL de clima de 60 min. |
| D-13 | Corregido (código) | Mensaje sin mapa; búsqueda por código postal y geocodificación inversa con respaldo local. `GEOCODING_API_KEY` en Render sigue siendo operativo. |
| D-14, D-15, D-16 | Corregido | Tarjeta, filtros (colonia, fechas, limpiar) y detalle completos. |
| D-17, D-23 | Pendiente de verificación | Sin cambios de CSS en esta rama; requiere medir a 360 px en navegador. |
| D-18 | Corregido | Tablero con desglose por tipo, longevidad promedio y `/indicadores/longevidad`. |
| D-19 | Corregido | `utils/formato.ts` con `timeZone: 'America/Ciudad_Juarez'`. |
| D-20 | Corregido en PR #29 | `lang="es-MX"`, título y `meta description` en `index.html`. |
| D-21 | Corregido | Sin contraseña de semilla en código, compose ni `.env.example`. |
| D-22 | Corregido | Aviso de `/coordinacion` en lenguaje ciudadano. |
| D-24 | Corregido | Retroceso de 5 min (`WEATHER_BACKOFF_MINUTES`) tras un fallo del proveedor. |
| D-26 | Corregido | `npm run lint`: 0 advertencias (hook `useCargaDatos`, `useAuth` y utilidades en archivos propios). |
| D-27 | Corregido (código) | `frontend/public/robots.txt` (Vercel sirve archivos estáticos antes del *rewrite*); `meta description` ya existía. Sin re-medir Lighthouse. |
| D-28 | Corregido | `docs/api-contract.md` §8 aclara que `/indicadores` no existe; además documenta `PATCH /reportes/{folio}`, `/geocoding/inversa` y la búsqueda por código postal. |
| D-29 | Pendiente (operativo) | Datos residuales en producción; RN-05/RN-07 impiden borrarlos. |
