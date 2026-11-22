# Auditoría obligatoria — Calles Seguras Juárez (AEB-1055)

## 1. Datos generales

| Campo | Valor |
|---|---|
| Proyecto | Calles Seguras Juárez — plataforma ciudadana de baches y encharcamientos |
| Fecha de auditoría | 2026-11-22 |
| Rama / commit auditado | `docs/auditoria-obligatoria` sobre `1beecb1` (merge PR #28) |
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

### 1.2 Limitaciones

- El **Documento 1 de Auditoría no está en el repositorio**. La estructura de este informe se reconstruyó a partir de los IDs citados en las instrucciones. Los títulos de HU y RNF se infirieron de `CLAUDE.md`, `docs/arquitectura.md`, `docs/api-contract.md` y las auditorías previas.
- Los casos **`F-01` a `F-14`** del Documento 1 no tienen definición disponible: se marcan `No evaluado`. Los IDs `FE-01`…`FE-14` de `docs/evidencia_frontend_auditoria.md` son defectos internos de esa auditoría, **no** los casos oficiales.
- `RNF-03`, `RNF-04` y `RNF-07` no tienen definición en ninguna fuente del repositorio: `No evaluado`. `RNF-09` se interpretó como volumen de datos de demostración (sección 6.3 del Documento 1, según las instrucciones de la auditoría de backend).
- Los criterios `CA1`–`CA5` de `HU-07.1` no están definidos en el repositorio.

## 2. Historias de usuario indispensables (`HU-01.1` a `HU-08.1`)

| ID | Criterio (resumen) | Estado | Evidencia verificable | Motivo si no cumple (causa raíz) |
|---|---|---|---|---|
| HU-01.1 | Iniciar sesión con mensaje genérico, JWT 30 min | Cumple | Backend A1/A2: `401 CREDENCIALES_INVALIDAS` idéntico para contraseña mala y correo inexistente; token de 1800 s. Frontend: «Correo o contraseña incorrectos.»; logout limpia almacenamiento y Atrás no muestra datos. | — |
| HU-01.2 | Registro con política de contraseña y aceptación del aviso de privacidad | Parcial | Backend A3: contraseñas débiles → 422 con mensaje en español. A4: registro **sin** consentimiento → 201. Frontend: `/aviso-de-privacidad` muestra la página de inicio (FE-08). | `RegistroIn` (`backend/app/schemas/auth.py:12-14`) no define ni exige el campo de consentimiento; sólo lo valida el cliente. No existe ruta ni página de aviso de privacidad en `frontend/src/App.tsx`. |
| HU-01.3 | Roles únicos; control de acceso con 403 | Cumple | Backend R1–R5, R4c: ciudadano/moderador → 403 en moderación y admin; visitante → 401; `rol` en registro → 422 (A6). Pytest `test_sin_token_401_y_rol_incorrecto_403`, `test_admin`. | — (observación: `PATCH`/`DELETE` de reportes responden 405 y no 403 porque la operación no existe para ningún rol). |
| HU-02.1 | Reportar con ubicación dentro de Juárez | Parcial | Backend T1/T1b: fuera de Juárez → `422 FUERA_DE_JUAREZ`. Frontend `/reportar`: búsqueda de dirección y GPS; la geocodificación respondió «no está disponible» y remite a «ajusta el marcador en el mapa», pero no hay mapa (FE-09). | No existe componente de mapa en `ReportCreatePage.tsx` ni dependencia de mapas; en producción la geocodificación cae al modo degradado (causa no verificada: probablemente `GEOCODING_API_KEY` ausente en Render). |
| HU-02.2 | Formulario dinámico por tipo de daño y descripción ≤ 500 | Cumple | Backend T2–T7: campos obligatorios por tipo, severidad del cliente rechazada, alcantarilla `Alta`, 501 caracteres → 422. Frontend: campos cambian por tipo; contador `0/500`. Pytest `test_validaciones_formulario_dinamico`. | — |
| HU-02.3 | Duplicado de bache ≤ 30 m y confirmación única | Cumple | Backend D1–D5b: 20 m → 409; 40 m → 201; doble confirmación → 409; autoconfirmación → 400. Pytest `test_duplicado_bache_30_metros`, `test_confirmar_bache`. Aviso de duplicado en UI verificado sólo por código (`hayDuplicados`, `forzar_nuevo`). | — |
| HU-02.5 | Mis reportes: paginación de 10 y edición sólo en `Recibido` | Parcial | Frontend: 10 tarjetas, «Página 1 de 2»; «Editar» sólo en `Recibido`; «Eliminar» deshabilitado (RN-07). Backend R6: `PATCH /reportes/{folio}` → 405. | El enlace «Editar» lleva a `/reportar?editar=…`, pero `ReportCreatePage.tsx` no maneja el parámetro y la API no expone edición: la funcionalidad no existe. |
| HU-03.1 | Reportar encharcamiento; duplicado ≤ 50 m; pregunta de riesgo si intransitable | Cumple | Backend E1–E3, T4: 45 m → 409; 60 m → 201; intransitable sin riesgo → 422. Pytest `test_duplicado_encharcamiento_50_metros`. | — |
| HU-03.2 | «Sigue ahí» reinicia vigencia de 6 h; autor no confirma | Cumple | Backend E4/E5: autor → 400. Pytest `test_sigue_ahi_reinicia_6_horas_y_votos` y `test_vencimiento_a_las_6_horas_se_evalua_en_consulta` (118 passed). Código `services/confirmaciones.py:93-98`, `services/vigencia.py:20-45`. | — |
| HU-03.3 | 3 «Ya no hay agua» de usuarios distintos → `Histórico` | Cumple | Backend E6–E10b: tercer usuario distinto → `Histórico`, historial con origen `sistema`; repetición del mismo usuario → 409. Pytest `test_encharcamiento_tres_desmentidos_lo_pasan_a_historico`. | — |
| HU-04.1 | Lista pública con tipo, calle, colonia, severidad/nivel y antigüedad, sin PII | Parcial | Frontend: tipo con ícono + texto, folio, calle, estado; sin PII; sin `Rechazado`. Backend R0/RN-04: sin PII. | `ReportCard.tsx` no renderiza colonia, severidad, nivel de agua ni antigüedad aunque la API los devuelve (`colonia`, `severidad`, `nivel_agua`, `longevidad_dias`). |
| HU-04.2 | Filtros combinados, búsqueda parcial, paginación 20, limpiar filtros | Parcial | Frontend: calle/folio + tipo + estado combinados (`calle=lerd&tipo_dano=Bache`); folio exacto localizado; 20 por página, «Página 1 de 11». | `PublicHomePage.tsx` sólo tiene `busqueda`, `tipo`, `estado`: faltan filtros de colonia y fechas (la API acepta `colonia_id`, `desde`, `hasta`) y el botón «Limpiar filtros». |
| HU-04.3 | «¿Cómo está mi zona?» en 1 km, del más cercano al más lejano, distancia visible, intransitable resaltado | Parcial | Frontend: radio de 1 km con Haversine; Centro → 11 reportes; Pronaf → estado vacío. Ninguna tarjeta muestra distancia. | `ZoneSection.tsx:46-47` ordena sólo por `prioridad` y no por distancia; la distancia calculada no se muestra; no hay estilo propio para `intransitable`. |
| HU-04.4 | Detalle con datos del daño, longevidad en días e historial | Parcial | Frontend `/reportes/BCH-2026-000172`: estado, calle, colonia, fecha e historial de 5 estados. | `ReportDetailPage.tsx` no muestra `longevidad_dias`, severidad ni `detalle` (tamaño/profundidad/carril); «Descripción» se rotula aunque esté vacía. |
| HU-05.1 | Bandeja de moderación | Cumple | Frontend `/moderacion` (coordinador): cola con folio, tipo, ubicación, severidad, confirmaciones, fecha y transiciones por rol. Backend R1: ciudadano → 403. | — |
| HU-05.2 | Transiciones de estado, motivo de rechazo, fecha de reparación | Cumple | Backend S0–S13: matriz RN-05 completa, fechas inválidas → 422, rechazo sin motivo → 422. Frontend `/coordinacion`: acciones Programado/En reparación con fecha. Pytest `test_maquina_de_estados_completa`. | — |
| HU-06.1 | Administración de colonias | Parcial | Frontend `/admin/colonias`: 46 colonias, filtros, Editar/Desactivar, formulario «Nueva colonia». Backend R3b/R4b: ciudadano → 403. | A 360 px el documento mide 751 px: la tabla de 850 px desborda la página (el contenedor no limita su ancho en móvil). |
| HU-06.2 | Administración de usuarios y roles | Parcial | Frontend `/admin/usuarios`: filtros, cambio de rol, Suspender/Reactivar. Backend R2/R4/R4c: no coordinador → 403. Pytest `test_admin`. | A 360 px el documento mide 786 px (mismo patrón de tabla que HU-06.1). |
| HU-07.1 | Tablero de indicadores (`CA1`–`CA5`) | Parcial | Frontend `/tablero`: filtros Desde/Hasta/Zona, totales, desglose por estado, tabla por sector. Red: sólo `/indicadores/resumen` y `/indicadores/sectores`. | No consume `/indicadores/longevidad` ni muestra longevidad de abiertos, desglose por tipo ni gráficas; `CA1`–`CA5` no verificables por falta de definición. |
| HU-08.1 | Pronóstico de lluvia con caché de 1 h y degradación elegante | Parcial | Backend W1/W2: 200 con `desactualizado: true` y `obtenido_en` de ≈ 11 h antes. Pytest `test_clima_cache_y_degradacion`. Frontend: banner sólo con alerta. | En producción el proveedor falla desde Render y se sirve la caché vencida; el TTL es 30 min (`core/config.py:27`, `.env.example:47`, `docker-compose.yml`) en vez de 60. |

## 3. Reglas de negocio (`RN-01` a `RN-10`)

| ID | Regla | Estado | Evidencia verificable | Motivo si no cumple (causa raíz) |
|---|---|---|---|---|
| RN-01 | Sólo coordenadas dentro de Juárez | Cumple | Backend T1 (`32.5,-107.0`) y T1b (`31.4499`) → `422 FUERA_DE_JUAREZ` con rango. `services/geo.py:5-6`; CHECK en BD. Pytest `test_fuera_de_juarez_422`. | — |
| RN-02 | UTC en BD; mostrar en `America/Ciudad_Juarez` | Parcial | API emite `-07:00` (p. ej. `13:39:14-07:00`). Frontend mostró «2:39 p.m.» para el mismo reporte. | `toLocaleString('es-MX')` sin `timeZone` en `AdminPages.tsx:6`, detalle y «Mis reportes»; depende de la zona del navegador. Sólo `AdminUsuariosPage.tsx:10` la fija. |
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
| RNF-01 | Responsivo de 360 px a escritorio | Parcial | Frontend: `/`, `/reportar`, `/mi-zona`, `/moderacion`, `/tablero` sin desbordamiento a 360 px; desktop sin desbordamiento. | `/admin/colonias` (751 px) y `/admin/usuarios` (786 px) desbordan a 360 px; cabecera de coordinador de 261 px de alto. |
| RNF-02 | WCAG 2.2 AA; Lighthouse ≥ 90 | Parcial | Lighthouse `/` móvil y escritorio: Accesibilidad 100, Buenas prácticas 100, Rendimiento 100. | `<html lang="en">` en un sitio en español (WCAG 3.1.1); objetivos táctiles < 24 px a 360 px (WCAG 2.5.8); Lighthouse sólo cubre la carga anónima de `/`. |
| RNF-03 | (sin definición disponible) | No evaluado | — | Definición no presente en el repositorio. |
| RNF-04 | (sin definición disponible) | No evaluado | — | Definición no presente en el repositorio. |
| RNF-05 | Seguridad: hash, JWT, 403 por rol | Cumple | Argon2id (`core/security.py`), JWT 30 min con `token_version` (logout revoca), bloqueo tras 5 intentos. Backend R1–R11. Pytest `test_cerrar_sesion_revoca_token`, `test_bloqueo_por_intentos_fallidos`. | — |
| RNF-06 | Respuesta < 3 s | Cumple | Backend P*: `/reportes` 0.12–0.61 s; `/indicadores/resumen` 0.12–0.13 s. Lighthouse LCP 0.8 s móvil / 0.2 s escritorio. | — |
| RNF-07 | (sin definición disponible) | No evaluado | — | Definición no presente en el repositorio. |
| RNF-08 | Todo en español de México | Parcial | Mensajes de error, validaciones y etiquetas en español (backend y frontend). | `lang="en"` y `<title>frontend</title>` en `frontend/index.html`; textos internos visibles («HU-02 · HU-03» en `/reportar`, aviso técnico de «contrato»/«API actual» en `/coordinacion`). |
| RNF-09 | Datos de demostración (≥ 20 colonias, ≥ 500 reportes) *(interpretado)* | No cumple | Producción: 46 colonias, `total: 225` reportes públicos. Docker local: `total: 211`. | `db/seed.py:143-144` fija `N_PAVIMENTO = 170` y `N_ENCHARCAMIENTOS = 55` (225 + 14 rechazados < 500). |

## 5. Requisitos técnicos (Sección 6 del Documento 1)

| ID | Requisito | Estado | Evidencia verificable | Motivo si no cumple (causa raíz) |
|---|---|---|---|---|
| 6.1 | Arquitectura y planificación | Cumple | `docs/arquitectura.md` (567 líneas: diagramas, modelo de datos, mapeo RN→implementación, OWASP), `docs/api-contract.md` (1321 líneas). Backend en capas `routers/`, `services/`, `models/`, `schemas/`. | — |
| 6.2 | Frontend React + TypeScript (Vite), HTML semántico, CSS externo, estados de carga/error/vacío | Parcial | `npm run build` sin errores; `header`/`nav`/`main`/`section`/`footer` en el DOM; `styles/global.css`; estados «Cargando…», error y vacío observados. Lighthouse 100/100/100. | Defectos funcionales de HU-04.x, HU-02.5, HU-07.1 y responsividad de admin; enrutamiento manual por `window.location.pathname` en `App.tsx`; 4 advertencias de lint. |
| 6.3 | Backend FastAPI + Pydantic v2 + SQLAlchemy 2.0 en capas | Cumple | `requirements.txt` (FastAPI 0.165, Pydantic 2.14, SQLAlchemy 2.1); 118 pruebas pasan; evidencia HTTP de backend completa. | — |
| 6.4 | PostgreSQL + Alembic + semilla | Parcial | `alembic upgrade head` y `db/seed.py` ejecutados sin error en Docker; triggers de RN-05/RN-07 en migración 0001. | La semilla genera 225 reportes, por debajo de los 500 requeridos (ver RNF-09). |
| 6.5 | API externa (clima) con caché y degradación | Parcial | Pytest `test_clima_cache_y_degradacion` y pruebas de geocodificación pasan. Producción: clima con `desactualizado: true` (≈ 11 h) y geocodificación degradada. | Proveedor de clima falla desde Render (causa a revisar en logs/variables de Render); TTL 30 min en lugar de 60; sin retroceso tras un fallo (cada petición reintenta con timeout de 5 s). |
| 6.6 | Seguridad OWASP A01/A02/A03 (2025) | Parcial | A01: 403 por rol verificado (R1–R5). A02: OpenAPI/docs deshabilitados en producción, CORS a `FRONTEND_URL`, `nosniff`, `no-store`. A03: dependencias Python con versión fija y `package-lock.json`. | A02: contraseña por omisión de la semilla (`Juarez2026`) escrita en `db/seed.py:58` y `docker-compose.yml:53`, contra la regla de `CLAUDE.md`. A03: sin escaneo automatizado de dependencias (no hay CI). |
| 6.7 | Contenedores; recuperación < 3 min con `docker compose up` | Parcial | `docker compose up --build --wait` → `db` y `backend` sanos en 26 s (con caché), migraciones y semilla automáticas. | No existe Dockerfile de frontend ni servicio de frontend en `docker-compose.yml`; `infra/` vacío (el único Dockerfile está en `backend/`). No se midió una construcción en frío. |
| 6.8 | Pruebas Pytest y CI en GitHub Actions | Parcial | `pytest` → 118 passed en 7.70 s contra PostgreSQL con migraciones y semilla. | `.github/workflows/` sólo contiene `.gitkeep`: no hay pipeline de CI. Sin pruebas de frontend. |
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
| Historias de usuario (HU) | 20 | 9 | 11 | 0 | 0 |
| Reglas de negocio (RN) | 10 | 9 | 1 | 0 | 0 |
| No funcionales (RNF) | 9 | 2 | 3 | 1 | 3 |
| Técnicos (6.1–6.9) | 9 | 2 | 6 | 1 | 0 |
| Casos F-01–F-14 | 14 | 0 | 0 | 0 | 14 |
| **Total** | **62** | **22** | **21** | **2** | **17** |

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
