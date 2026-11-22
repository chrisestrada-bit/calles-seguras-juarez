# Evidencia de auditoría de frontend (navegador real)

- **Fecha:** 2026-11-22
- **URL auditada:** `https://calles-seguras-juarez.vercel.app` (frontend) → API `https://calles-seguras-juarez-api.onrender.com/api/v1`
- **Método:** MCP `chrome-devtools` (snapshot del árbol de accesibilidad, `evaluate_script` sobre el DOM, lista de red, emulación de viewport, Lighthouse) y lectura de `frontend/src/`. No se modificó código.
- **Limitaciones:**
  - `HU-07.1` `CA1`–`CA5` y `HU-04.x` a `HU-08.1` no están definidos en el repositorio (el «Documento 1» no está incluido), por lo que los criterios se evaluaron con lo que describe el enunciado y `CLAUDE.md`.
  - El navegador de la auditoría estaba en una zona horaria distinta a la de Juárez (ver defecto FE-11).
  - Lighthouse sólo audita la carga anónima de `/`; las vistas con sesión se verificaron por DOM/código.
  - No se crearon reportes ni se modificaron colonias/usuarios desde la interfaz.

## 1. Resumen por flujo

| Flujo | Estado | Resumen |
|---|---|---|
| 1. Visitante (`HU-04.1`–`HU-04.4`, `HU-08.1`, `RN-04`, `RN-09`) | **Parcial** | Carga, sin PII, sin `Rechazado`, tipo distinguible por texto + ícono, filtros básicos y paginación de 20 funcionan. Faltan colonia/severidad/antigüedad en tarjetas, filtros de colonia y fechas, botón limpiar, orden/distancia en «Mi zona», longevidad en detalle. |
| 2. Sesión por rol (`HU-01.x`, `HU-02.5`, `HU-05.x`–`HU-07.1`) | **Parcial** | Login/registro/logout/Atrás correctos. «Editar» de `/mis-reportes` no tiene destino funcional. Moderación, colonias y usuarios operan. Tablero incompleto. `/aviso-de-privacidad` sin contenido. |
| 3a. Responsividad `360 px` / `1280 px` (`RNF-01`) | **Parcial** | `/`, `/reportar`, `/mi-zona`, `/moderacion`, `/tablero` sin desbordamiento de página a 360 px; **`/admin/colonias` y `/admin/usuarios` desbordan** (751 y 786 px). Cabecera de 261 px de alto a 360 px para coordinador. |
| 3b. Lighthouse (`RNF-02`) | **Cumple** (en `/` anónima) | Accesibilidad 100, Buenas prácticas 100, Rendimiento 100 (móvil y escritorio). SEO 82. |

## 2. Lighthouse (puntajes exactos)

Página: `https://calles-seguras-juarez.vercel.app/` (carga de navegación, sin sesión).

| Dispositivo | Accesibilidad | Buenas prácticas | Rendimiento | SEO | FCP | LCP | TBT | CLS |
|---|---|---|---|---|---|---|---|---|
| Móvil (360×800 emulado; Lighthouse 13.6.0 CLI para rendimiento) | **100** | **100** | **100** | 82 | 0.8 s | 0.8 s | 60 ms | 0 |
| Escritorio | **100** | **100** | **100** | 82 | 0.2 s | 0.2 s | 0 ms | 0.033 |

- Accesibilidad y Buenas prácticas y SEO provienen de `lighthouse_audit` del MCP; la herramienta excluye Rendimiento, que se obtuvo con `npx lighthouse` (v13.6.0) contra la misma URL. Reportes: `scratchpad/lh_mobile`, `lh_desktop`, `lhcli`.
- Meta unidad ≥ 80 y meta excelente ≥ 90: **cumplidas** en Accesibilidad, Buenas prácticas y Rendimiento.
- Fallos de Lighthouse (no afectan los tres puntajes pedidos): `meta-description` ausente; `robots-txt` inválido (14 errores: el rewrite SPA de `frontend/vercel.json` devuelve `index.html` para `/robots.txt`); CLS móvil 0.044 (agentic-browsing); `llms.txt` y `ard.json` inválidos (no aplican al proyecto).
- Lighthouse no detecta los defectos FE-06, FE-07, FE-08, FE-10, FE-12 (son de contenido y de vistas con sesión).

## 3. Flujo 1 — Visitante

| Comprobación | Resultado | Evidencia |
|---|---|---|
| `/` carga sin sesión | Cumple | 200; peticiones `GET /clima/pronostico` 200 y `GET /reportes?pagina=1&por_pagina=20` 200. |
| Banner de clima | Cumple | `RainBanner.tsx`: muestra «Consultando el pronóstico…», error «Pronóstico no disponible…» o aviso de lluvia; sin alerta no pinta nada (el API devolvió `alerta_lluvia:false`). |
| Sin PII del autor (`RN-04`) | Cumple | Texto de las 20 tarjetas y del detalle sin nombre/correo/ID. |
| Sin `Rechazado` (`RN-09`) | Cumple | Opciones del filtro Estado: Todos, Recibido, Validado, Programado, En reparación, Reparado, Activo, Histórico. Reportes `Recibido` se rotulan «Sin validar». |
| Tipo por texto/ícono, no sólo color | Cumple | Tarjeta: ícono `🕳️`/`🌊` (`aria-hidden`) + texto «Bache»/«Encharcamiento»; leyenda «🕳️ Bache o alcantarilla / 🌊 Encharcamiento». |
| Tarjeta: tipo, calle, colonia, severidad/nivel, antigüedad | **No cumple** | Tarjeta (`ReportCard.tsx`) sólo muestra tipo, folio, calle, estado y confirmaciones. **No muestra colonia, severidad, nivel de agua ni antigüedad.** |
| Filtros combinados | **Parcial** | Existen sólo: Calle o folio, Tipo de daño, Estado. **No hay filtro de colonia ni de fechas** (inputs del DOM: `busqueda`, `tipo`, `estado`). Combinación calle+tipo funciona: `GET …/reportes?pagina=1&por_pagina=20&calle=lerd&tipo_dano=Bache` 200. |
| Búsqueda parcial calle / folio | Cumple | `lerd` → petición con `calle=lerd`; `BCH-2026-000033` (regex en `PublicHomePage.tsx:12`) → localiza el reporte. |
| Paginación de 20 | Cumple | 20 `article` por página; «Página 1 de 11», Anterior deshabilitado. |
| Botón limpiar filtros | **No cumple** | Sólo existe el botón «Buscar». |
| «¿Cómo está mi zona?» | **Parcial** | Referencias Pronaf / Centro / Torres y GPS. Pronaf: «No encontramos reportes en un radio de 1 km» (estado vacío correcto). Centro: «11 reporte(s) a 1 km». Radio de 1 km filtrado con Haversine (`ZoneSection.tsx:18-22`). **No se muestra la distancia** (ninguna tarjeta contiene m/km) y **no se ordena por cercanía**: `.sort((a,b)=>prioridad(b)-prioridad(a))` sólo ordena por prioridad (`ZoneSection.tsx:46-47`). Los encharcamientos `intransitable` sólo suben en el orden; no hay resalte visual propio (no hay datos activos intransitables en producción para observarlo). |
| `/mi-zona` | Cumple | Ruta directa carga (`vercel.json` con rewrite a `index.html`). |
| Detalle `/reportes/:folio` | **Parcial** | `BCH-2026-000172`: folio, estado, calle, colonia, fecha e **historial de 5 estados** (Recibido→…→Reparado, con origen). **No muestra longevidad en días (`RN-10`), severidad ni detalle del daño**, y «Descripción» aparece como etiqueta vacía. Muestra «Cargando detalle…» mientras llega la respuesta (≈1–3 s). |

## 4. Flujo 2 — Sesión por rol

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Navegación directa `/login` y `/registro` | Cumple | Cargan sin 404 (rewrite de `vercel.json`). |
| Login incorrecto | Cumple | «Correo o contraseña incorrectos.» (`role="alert"`). |
| Registro con contraseña `abc` | Cumple | «La contraseña debe tener al menos 8 caracteres e incluir letras y números.» |
| Cierre de sesión | Cumple | Botón «Cerrar sesión» → `/login`; `localStorage` y `sessionStorage` vacíos. |
| Botón Atrás tras salir | Cumple | `/mis-reportes` muestra «Inicia sesión para consultar el historial de tus reportes.» sin datos. |
| Ruta privada sin sesión | Cumple | Mismo mensaje con botón «Iniciar sesión» (no redirige, avisa). |
| `/reportar` (ciudadano) | Cumple | 3 tipos; Bache → Tamaño/Profundidad/Carril; Alcantarilla → «Severidad Alta fija»; Encharcamiento → «Nivel del agua». Campos deshabilitados hasta elegir ubicación; 46 colonias; descripción con contador `0/500`. Aviso de duplicado por código (`hayDuplicados`, `forzar_nuevo`) — no se envió ningún reporte, por lo que no se observó en vivo. Geocodificación degradada: «…no está disponible… ajusta el marcador en el mapa», pero **no existe mapa** (0 elementos de mapa ni dependencia de mapas). |
| `/mis-reportes` | **Parcial** | 10 tarjetas por página, «Página 1 de 2». «Editar» habilitado sólo en `Recibido`, «Eliminar» siempre deshabilitado (correcto por `RN-07`). **El enlace «Editar» apunta a `/reportar?editar=BCH-…`, pero `ReportCreatePage.tsx` no maneja `editar` (0 apariciones) y el API no tiene `PATCH /reportes/{folio}` (405)**: el flujo de edición no existe. |
| Moderación (coordinador) | Cumple | `/moderacion`: cola con Folio, tipo y ubicación, estado, confirmaciones, severidad; para coordinador en `Recibido` indica «Sin transiciones disponibles para tu rol» (coherente con `RN-05`). |
| Coordinación | Cumple (con ruido) | `/coordinacion`: bandeja con Programar/En reparación y fecha. Muestra al público un aviso técnico: «el contrato registra asignación mediante el estado… La API actual no expone una asignación individual de cuadrilla». |
| `HU-06.1` Colonias | **Parcial** | `/admin/colonias`: lista de 46 colonias con sector, C. P., estado; filtros nombre/sector; botones Editar/Desactivar; formulario «Nueva colonia» (Nombre, Sector, C. P., Latitud, Longitud). **Desborda horizontalmente a 360 px** (FE-03). |
| `HU-06.2` Usuarios y roles | **Parcial** | `/admin/usuarios`: filtros rol/estado/búsqueda, selector de rol por usuario, Suspender/Reactivar; se ven las 3 cuentas de prueba de la auditoría de backend como «Suspendido». **Desborda a 360 px** (FE-03). |
| `HU-07.1` Tablero (`/tablero`, `/dashboard`) | **Parcial** | Filtros Desde/Hasta/Zona; tarjetas: pavimento 158, encharcamientos 54, activos 0, reparación promedio 20.9 días; desglose por estado; tabla por zona. Sólo consume `/indicadores/resumen` y `/indicadores/sectores` (red). **No usa `/indicadores/longevidad`**, no muestra longevidad promedio de abiertos, desglose por tipo ni gráficas (0 `svg`/`canvas`). No se pudo mapear a `CA1`–`CA5` sin su definición. |

## 5. Flujo 3 — Responsividad

Medición de `scrollWidth` de `document.documentElement` frente al ancho del viewport.

| Vista | 360×800 | 1280×800 / ancho completo |
|---|---|---|
| `/` | 360 — sin desbordamiento | sin desbordamiento |
| `/reportar` | 360 | sin desbordamiento |
| `/mi-zona` | 360 | sin desbordamiento |
| `/moderacion` | 360; tabla de 850 px dentro de contenedor `overflow-x:auto` (desplaza sólo la tabla) | sin desbordamiento |
| `/tablero` | 360; tabla de 850 px en contenedor con scroll | sin desbordamiento |
| `/admin/colonias` | **751 px de ancho de documento → desbordamiento horizontal de página** | 1265 de 1280 (sin desbordamiento) |
| `/admin/usuarios` | **786 px → desbordamiento horizontal de página** | sin desbordamiento |

- A 360 px, la cabecera con sesión de coordinador mide **261.6 px de alto** (10 enlaces de navegación apilados) ≈ 33 % del viewport.
- Objetivos táctiles menores a 24 px (WCAG 2.2 `2.5.8`) a 360 px: 10 elementos en `/` y, en `/reportar`, los 10 enlaces de navegación y los 3 radios de tipo de daño.
- Pruebas en `/` a 1280 px y verificación Lighthouse: sin problemas.
- Nota de método: `resize_page` no cambió el viewport en la primera ventana (1692 px); se usó `emulate` con `360x800x2,mobile,touch` y `1280x800x1`.

## 6. Defectos y brechas

| ID | Ubicación | Defecto | Tipo | Evidencia |
|---|---|---|---|---|
| FE-01 | `HU-04.1` Tarjetas de `/` | No se muestran colonia, severidad/nivel de agua ni antigüedad. | Funcional | `ReportCard.tsx`; texto de tarjeta del DOM. |
| FE-02 | `HU-04.2` Filtros de `/` | Faltan filtros de colonia y fechas y el botón «Limpiar filtros». | Funcional | Inputs del DOM: `busqueda`, `tipo`, `estado`. |
| FE-03 | **`HU-06.1` y `HU-06.2`** | `/admin/colonias` y `/admin/usuarios` desbordan horizontalmente la página a 360 px (751/786 px). | Visual / `RNF-01` | `scrollWidth` 751 y 786 con viewport 360. |
| FE-04 | `HU-04.3` «¿Cómo está mi zona?» | No muestra distancia y no ordena de más cercano a más lejano; sólo por prioridad. Sin resalte visual de `intransitable`. | Funcional | `ZoneSection.tsx:46-47`; ninguna tarjeta con m/km. |
| FE-05 | `HU-04.4` / `RN-10` Detalle | Falta longevidad en días, severidad y detalle del daño; «Descripción» vacía. | Funcional | Texto del detalle de `BCH-2026-000172`. |
| FE-06 | `HU-02.5` `/mis-reportes` | «Editar» (sólo `Recibido`) enlaza a `/reportar?editar=…`, que no implementa edición; el API no tiene `PATCH` de reportes. | Funcional | `MyReportsPage.tsx`; 0 apariciones de `editar` en `ReportCreatePage.tsx`; backend `405`. |
| FE-07 | **`HU-07.1`** Tablero | Sólo resumen y por sector; sin longevidad, sin desglose por tipo, sin gráficas; `CA1`–`CA5` no verificables. | Funcional | Red: sólo `/indicadores/resumen` y `/sectores`. |
| FE-08 | `/aviso-de-privacidad` | La casilla de registro enlaza a una ruta inexistente que muestra la página de inicio; no hay aviso de privacidad (LFPDPPP). | Ruta | `App.tsx` (sin ruta); `h1` de la ruta = «Consulta y reporta…». |
| FE-09 | `/reportar` | Aviso de geocodificación degradada remite a «ajusta el marcador en el mapa», pero no hay mapa. | UX | 0 elementos de mapa; texto del DOM. |
| FE-10 | `/reportar`, `/coordinacion` | Texto interno visible al ciudadano: eyebrow «HU-02 · HU-03», aviso técnico sobre «contrato» y «API actual». | Contenido | Snapshot de `/reportar`; texto de `/coordinacion`. |
| FE-11 | `RN-02` Fechas | `toLocaleString('es-MX')` sin `timeZone` en `AdminPages.tsx:6` y en detalle/«Mis reportes»; sólo `AdminUsuariosPage.tsx:10` fija `America/Ciudad_Juarez`. En este navegador `BCH-2026-000172` aparece «2:39 p.m.» cuando el API lo emitió a las `13:39-07:00`. | Funcional | Detalle del DOM frente a la respuesta del API. |
| FE-12 | `<html>` / `<title>` | `lang="en"` y título «frontend» en todas las rutas (`RNF-08`, WCAG 3.1.1 y 2.4.2); sin `meta description`. | Accesibilidad | `document.documentElement.lang`, `document.title`; Lighthouse SEO `meta-description`. |
| FE-13 | Navegación móvil | Cabecera de coordinador de 261 px a 360 px; objetivos táctiles < 24 px (enlaces de navegación y radios). | Visual / WCAG 2.5.8 | Mediciones de la sección 5. |
| FE-14 | `robots.txt` | El rewrite SPA sirve `index.html` en `/robots.txt` (Lighthouse: 14 errores). | Ruta | `frontend/vercel.json`; Lighthouse `robots-txt`. |

## 7. Datos residuales

- No se crearon reportes ni se editaron datos en esta auditoría.
- Las 3 cuentas `auditoria-0a8363-*` y los folios `BCH-2026-000172` y `ENC-2026-000056` siguen en producción desde la auditoría de backend (`docs/evidencia_backend_auditoria.md`).
- La sesión de `coordinador@ejemplo.mx` del navegador de pruebas se mantuvo sólo en memoria (sin `localStorage`).
