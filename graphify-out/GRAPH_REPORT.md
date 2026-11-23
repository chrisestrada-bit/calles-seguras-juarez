# Graph Report - calles-seguras-juarez  (2026-11-22)

## Corpus Check
- 202 files · ~116,057 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 31 file(s) not represented in the graph (top: (none) 11, .css 11, .xsd 2)

## Summary
- 2221 nodes · 5680 edges · 108 communities (94 shown, 14 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 113 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103

## God Nodes (most connected - your core abstractions)
1. `Icon()` - 76 edges
2. `Reporte` - 65 edges
3. `punto_unico()` - 56 edges
4. `react` - 44 edges
5. `crear_reporte()` - 42 edges
6. `payload_bache()` - 39 edges
7. `get_settings()` - 38 edges
8. `ErrorAPI` - 31 edges
9. `ApiError` - 29 edges
10. `api` - 29 edges

## Surprising Connections (you probably didn't know these)
- `sembrar_operacion()` --calls--> `AsignacionCuadrilla`  [INFERRED]
  db/seed.py → backend/app/models/operacion.py
- `run_migrations_offline()` --calls--> `get_settings()`  [EXTRACTED]
  db/migrations/env.py → backend/app/core/config.py
- `run_migrations_online()` --calls--> `get_settings()`  [EXTRACTED]
  db/migrations/env.py → backend/app/core/config.py
- `sembrar_operacion()` --calls--> `Cuadrilla`  [INFERRED]
  db/seed.py → backend/app/models/operacion.py
- `sembrar_operacion()` --calls--> `UsuarioCuadrilla`  [INFERRED]
  db/seed.py → backend/app/models/operacion.py

## Import Cycles
- None detected.

## Communities (108 total, 14 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (52): App(), ErrorMessage(), Guard(), PageIntro(), Pagination(), BuscadorColonia(), Icon(), BlockSkeleton() (+44 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (62): CambiarEstadoRequest, CambiarEstadoResponse, CambiarRolRequest, CambiarRolResponse, CampoFormulario, Centro, ClimaActual, ColoniaFavorita (+54 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (41): crear_reporte(), payload_bache(), payload_enc(), punto_unico(), claves(), test_alcantarilla_alta_y_cliente_no_fija_severidad(), test_bloqueo_por_intentos_fallidos(), test_confirmar_bache() (+33 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (12): Base, columna_fecha_creacion(), pg_enum(), CacheClima, ConfirmacionReporte, OrigenCambio, TipoConfirmacion, HistorialEstado (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (25): contrasena_valida(), crear_token(), decodificar_token(), hashear_contrasena(), verificar_contrasena(), Usuario, cerrar_sesion(), login() (+17 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (23): CarrilAfectado, EstadoReporte, NivelAgua, ProfundidadBache, Severidad, TamanoBache, TipoDano, ColoniaFavorita (+15 more)

### Community 6 - "Community 6"
Cohesion: 0.10
Nodes (24): cercanos(), confirmar(), crear(), descargar_foto(), eliminar(), _exportar(), exportar_csv(), exportar_xml() (+16 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (21): cambiar_estado(), cambiar_rol(), _colonia(), crear_colonia(), crear_motivo(), crear_sector(), crear_tipo(), editar_colonia() (+13 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (39): cargar(), catalogo, cargarCatalogo(), cargarTipos(), enJuarez(), ErrorApiTexto(), LIMITES, ReportCreatePage() (+31 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (44): apiVersion, env, image, imagePullPolicy, livenessProbe, name, ports, readinessProbe (+36 more)

### Community 10 - "Community 10"
Cohesion: 0.10
Nodes (23): longevidad(), moderacion(), puntos_recurrentes(), resumen(), sectores(), IndicadoresLongevidad, IndicadoresModeracion, IndicadoresResumen (+15 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (33): motivo_id(), asignar(), avance(), bache(), confirmaciones_de(), confirmar(), escenario_enlace(), este() (+25 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (26): ErrorAPI, Colonia, ColoniaAdmin, _ColoniaBase, ColoniaCrear, ColoniaEditar, EstadoUsuarioIn, EstadoUsuarioOut (+18 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (23): fuera_de_juarez(), SectorRef, Ubicacion, ColoniaCercana, ColoniaSugerida, RespuestaGeocodificacion, RespuestaGeocodificacionInversa, ResultadoGeocodificacion (+15 more)

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (28): agregar_colonia(), asignar(), avanzar(), _bache(), crear_cuadrilla(), _cuadrilla(), desvincular(), _detalle() (+20 more)

### Community 15 - "Community 15"
Cohesion: 0.11
Nodes (32): FotosReporte(), LEYENDA, LIMITES, MapaReportes(), ReportMap, ReportCard(), AVISO, ESTADO (+24 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (33): devDependencies, jsdom@^31.0.1, oxlint@^1.90.0, @testing-library/jest-dom@^8.0.0, @testing-library/react@^16.3.3, @testing-library/user-event@^14.6.13, @types/leaflet@^1.9.22, @types/leaflet.markercluster@^1.5.6 (+25 more)

### Community 17 - "Community 17"
Cohesion: 0.06
Nodes (35): apiVersion, image, imagePullPolicy, livenessProbe, name, ports, readinessProbe, resources (+27 more)

### Community 18 - "Community 18"
Cohesion: 0.13
Nodes (27): Estado, AuthArt(), AuthProvider(), AuthContext, AuthContextValue, LoginPage(), contraseñaValida(), RegisterPage() (+19 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (28): HeroMap(), Nodo, NODOS, Props, EstadoEnVivo, INTERVALO_SONDEO_MS, useEncharcamientosEnVivo(), cargarCatalogo() (+20 more)

### Community 20 - "Community 20"
Cohesion: 0.12
Nodes (5): Generador, main(), sembrar_reportes(), sembrar_territorio(), sembrar_usuarios()

### Community 21 - "Community 21"
Cohesion: 0.10
Nodes (16): Reporte, anotar_principales(), buscar_cercanos(), condiciones_publicas(), crear_reporte(), editar_reporte(), historial_publico(), listar_mios() (+8 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (15): leer(), leer_todas(), listar(), _out(), LeerTodasOut, NotificacionOut, PaginaNotificaciones, contar_no_leidas() (+7 more)

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (8): run_migrations_offline(), run_migrations_online(), _ejecutar(), upgrade(), cargar(), error(), main(), nombre()

### Community 24 - "Community 24"
Cohesion: 0.17
Nodes (23): BannerRed(), BACHE, sesion, actualizar(), Borrador, cargarCola(), clave(), descartar() (+15 more)

### Community 25 - "Community 25"
Cohesion: 0.17
Nodes (18): AsignacionCuadrilla, _asignacion_del_enlace(), asignaciones(), asignar(), avanzar(), crear(), cuadrillas_de_enlace(), desvincular_enlace() (+10 more)

### Community 26 - "Community 26"
Cohesion: 0.10
Nodes (12): get_settings(), Settings, reiniciar_retroceso(), test_geocoding_fallback_sin_llave(), test_geocoding_limite_de_busquedas(), _limpiar_limitador_geocoding(), test_clima_no_reintenta_durante_el_retroceso(), test_fallback_de_geocoding_no_remite_a_un_mapa() (+4 more)

### Community 27 - "Community 27"
Cohesion: 0.12
Nodes (20): revisar_trayecto(), AsignacionIn, AvanceIn, CriteriosResumen, _CuadrillaCampos, CuadrillaCrear, CuadrillaEditar, EncharcamientoEnTrayecto (+12 more)

### Community 28 - "Community 28"
Cohesion: 0.11
Nodes (13): analizar(), _bool(), _error(), importar(), Resultado, _validar_integridad(), cargar_esquema(), _celda_segura() (+5 more)

### Community 29 - "Community 29"
Cohesion: 0.12
Nodes (22): CampanaNotificaciones(), IconName, PATHS, EventoInstalacion, InstalarApp(), ClimaIcono(), RainBanner(), actual() (+14 more)

### Community 30 - "Community 30"
Cohesion: 0.16
Nodes (15): a_local(), ahora_utc(), fecha_local(), hoy_local(), _armar(), _consultar_proveedor(), _degradado(), hay_alerta_lluvia() (+7 more)

### Community 31 - "Community 31"
Cohesion: 0.14
Nodes (14): ReporteFoto, agregar_fotos(), autorizado_a_ver(), contar_de_usuario(), directorio_fotos(), exigir_acceso(), FotoRechazada, listar() (+6 more)

### Community 32 - "Community 32"
Cohesion: 0.17
Nodes (18): desplazar(), avisos(), detalle(), nuevo_bache(), sembrar_enc(), test_aislamiento_estricto_entre_usuarios(), test_cada_cambio_de_estado_avisa_al_autor(), test_dia_se_cuenta_en_hora_de_ciudad_juarez_no_en_utc() (+10 more)

### Community 33 - "Community 33"
Cohesion: 0.14
Nodes (20): _directorio_fotos(), importar(), nuevo_bache(), subir(), test_foto_valida_jpg_y_png_se_guardan_con_nombre_uuid(), test_fotos_al_confirmar_un_reporte_existente(), test_fotos_de_reporte_rechazado_no_se_revelan(), test_fotos_en_recibido_solo_autor_y_moderacion_luego_publicas() (+12 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (27): Service postgres, Service backend, Service frontend, app.kubernetes.io/name, app.kubernetes.io/part-of, labels, name, namespace (+19 more)

### Community 35 - "Community 35"
Cohesion: 0.10
Nodes (4): LimitadorVentana, emitir(), _firma(), GestorConexiones

### Community 36 - "Community 36"
Cohesion: 0.14
Nodes (14): RolUsuario, calcular_severidad(), severidad_bache(), severidad_encharcamiento(), disponibles(), tabla(), validar_transicion(), _resultado() (+6 more)

### Community 37 - "Community 37"
Cohesion: 0.15
Nodes (14): detalle(), editar(), ReportePublico, ReporteResumenPublico, Vigencia, a_mi_reporte(), a_publico(), a_resumen() (+6 more)

### Community 38 - "Community 38"
Cohesion: 0.15
Nodes (14): colonia_catalogo(), colonias(), estados(), sectores(), tipos_dano(), CampoFormulario, CatalogoEstados, CatalogoTiposDano (+6 more)

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (24): FusionarDialog(), AuditPage(), cargarAuditoria(), cargarTablero(), CoordinationPage(), DashboardPage(), DatosTablero, ESTADOS_AUDITADOS (+16 more)

### Community 40 - "Community 40"
Cohesion: 0.08
Nodes (24): apiVersion, data, ACCESS_TOKEN_EXPIRE_MINUTES, APP_ENV, APP_TIMEZONE, FRONTEND_URL, GEOCODING_API_URL, GEOCODING_TIMEOUT_SECONDS (+16 more)

### Community 41 - "Community 41"
Cohesion: 0.15
Nodes (12): CalleRiesgo, ClimaActual, ClimaHora, Pronostico, RiesgoInundacion, ColoniaRef, CuerpoError, DetalleError (+4 more)

### Community 42 - "Community 42"
Cohesion: 0.19
Nodes (16): CatalogoMotivoRechazo, CatalogoTipoDano, Cuadrilla, UsuarioCuadrilla, crear_motivo(), crear_tipo(), editar_motivo(), editar_tipo() (+8 more)

### Community 43 - "Community 43"
Cohesion: 0.11
Nodes (7): cola(), detalle(), fusionar(), transicionar(), _bloquear(), fusionar(), obtener_por_folio()

### Community 44 - "Community 44"
Cohesion: 0.18
Nodes (15): fijarUbicacion(), API, ciudadanoNuevo(), CLAVE, CLAVE_SEMILLA, correoUnico(), iniciarSesion(), PNG_1X1 (+7 more)

### Community 45 - "Community 45"
Cohesion: 0.13
Nodes (6): _ciclo_vencimiento(), encabezados_de_seguridad(), _expirar_encharcamientos(), lifespan(), salud(), canal_encharcamientos()

### Community 46 - "Community 46"
Cohesion: 0.15
Nodes (13): ciudadano(), ciudadanos(), client(), coordinador(), crear_cuenta(), Cuenta, db(), moderador() (+5 more)

### Community 47 - "Community 47"
Cohesion: 0.20
Nodes (18): ATRIBUCION, CENTRO_JUAREZ, descripcionMarcador(), ERRORES_PARA_FALLAR, GLIFO, iconoDe(), LIMITES, TILES_URL (+10 more)

### Community 48 - "Community 48"
Cohesion: 0.23
Nodes (10): _base(), _filtros(), mas_antiguos(), moderacion(), por_sector(), _redondear(), resumen(), fecha_local_sql() (+2 more)

### Community 49 - "Community 49"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 50 - "Community 50"
Cohesion: 0.13
Nodes (19): PersistentVolumeClaim postgres-datos, PersistentVolumeClaim backend-fotos, app.kubernetes.io/name, app.kubernetes.io/part-of, labels, name, namespace, apiVersion (+11 more)

### Community 51 - "Community 51"
Cohesion: 0.11
Nodes (19): environment, ACCESS_TOKEN_EXPIRE_MINUTES, APP_ENV, APP_TIMEZONE, DATABASE_URL, FRONTEND_URL, GEOCODING_API_KEY, GEOCODING_API_URL (+11 more)

### Community 52 - "Community 52"
Cohesion: 0.18
Nodes (9): caja_envolvente(), es_codigo_postal_juarez(), haversine_m(), distancia_a_polilinea(), encharcamientos_cercanos(), _linea_recta(), obtener_ruta(), Ruta (+1 more)

### Community 53 - "Community 53"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, moduleResolution, noEmit (+9 more)

### Community 54 - "Community 54"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 55 - "Community 55"
Cohesion: 0.23
Nodes (6): _cuenta_suspendida(), get_db(), requiere_rol(), usuario_actual(), _usuario_desde_token(), usuario_opcional()

### Community 56 - "Community 56"
Cohesion: 0.17
Nodes (3): buscar(), inversa(), _limitar()

### Community 57 - "Community 57"
Cohesion: 0.23
Nodes (11): FotoPicker(), Props, ErroresFotos, filtrarArchivos(), formatoTamano(), MAX_BYTES_FOTO, MAX_FOTOS, SIN_ERRORES_FOTOS (+3 more)

### Community 58 - "Community 58"
Cohesion: 0.22
Nodes (8): _campo(), _cuerpo(), registrar_manejadores(), _error_api(), _http(), _inesperado(), _validacion(), _traducir_validacion()

### Community 59 - "Community 59"
Cohesion: 0.22
Nodes (7): detalle(), _folio_principal(), _item(), listar_cola(), _obtener(), _reportes_por_autor_24h(), transicionar()

### Community 60 - "Community 60"
Cohesion: 0.24
Nodes (13): ReportGridSkeleton(), Cercano, dentroDeJuarez(), distanciaKm(), esEncharcamientoActivo(), esIntransitable(), LIMITES, Radar() (+5 more)

### Community 61 - "Community 61"
Cohesion: 0.20
Nodes (9): BuscadorPunto(), enJuarez(), Punto, TrayectoMapa, TrayectoPage(), GeocodingResponse, GeocodingResultado, TrayectoResponse (+1 more)

### Community 62 - "Community 62"
Cohesion: 0.27
Nodes (14): steps, steps, steps, VITE_API_BASE_URL, steps, steps, steps, env (+6 more)

### Community 63 - "Community 63"
Cohesion: 0.22
Nodes (6): resumen_colonia(), agregar(), favoritas(), ids_favoritas(), quitar(), resumen_colonia()

### Community 64 - "Community 64"
Cohesion: 0.18
Nodes (6): armar_pagina(), ParametrosPagina, listar_usuarios(), buscar_colonias(), es_prefijo_cp(), listar_sectores()

### Community 65 - "Community 65"
Cohesion: 0.15
Nodes (13): name, runs-on, services, timeout-minutes, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, e2e (+5 more)

### Community 66 - "Community 66"
Cohesion: 0.17
Nodes (11): concurrency, cancel-in-progress, group, name, runs-on, timeout-minutes, jobs, dependencias (+3 more)

### Community 67 - "Community 67"
Cohesion: 0.17
Nodes (12): run, defaults, name, defaults, name, runs-on, timeout-minutes, runs-on (+4 more)

### Community 68 - "Community 68"
Cohesion: 0.17
Nodes (12): command, env, envFrom, image, imagePullPolicy, name, ports, resources (+4 more)

### Community 70 - "Community 70"
Cohesion: 0.25
Nodes (11): env, env, APP_ENV, CI, DATABASE_URL, FRONTEND_URL, GEOCODING_API_KEY, JWT_SECRET_KEY (+3 more)

### Community 72 - "Community 72"
Cohesion: 0.20
Nodes (10): environment, image, ports, restart, volumes, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER (+2 more)

### Community 74 - "Community 74"
Cohesion: 0.20
Nodes (10): claimName, fsGroup, runAsGroup, runAsNonRoot, runAsUser, securityContext, volumes, spec (+2 more)

### Community 75 - "Community 75"
Cohesion: 0.22
Nodes (9): scripts, build, dev, lint, preview, test, test:e2e, test:e2e:install (+1 more)

### Community 76 - "Community 76"
Cohesion: 0.22
Nodes (9): with, cache, cache-dependency-path, if-no-files-found, name, node-version, path, python-version (+1 more)

### Community 77 - "Community 77"
Cohesion: 0.22
Nodes (9): securityContext, command, image, imagePullPolicy, name, securityContext, allowPrivilegeEscalation, capabilities (+1 more)

### Community 79 - "Community 79"
Cohesion: 0.25
Nodes (8): command, depends_on, ports, restart, volumes, condition, db, backend

### Community 80 - "Community 80"
Cohesion: 0.43
Nodes (4): FotoOut, FotoRechazadaOut, FotosSubidas, ListaFotos

### Community 81 - "Community 81"
Cohesion: 0.48
Nodes (7): healthcheck, healthcheck, interval, retries, start_period, test, timeout

### Community 82 - "Community 82"
Cohesion: 0.29
Nodes (7): dependencies, leaflet@^1.9.4, leaflet.markercluster@^1.5.3, react@^19.3.1, react-dom@^19.3.1, leaflet.markercluster, react-dom

### Community 83 - "Community 83"
Cohesion: 0.29
Nodes (7): app.kubernetes.io/name, matchLabels, spec, replicas, selector, strategy, type

### Community 84 - "Community 84"
Cohesion: 0.29
Nodes (6): apiVersion, kind, app.kubernetes.io/part-of, metadata, labels, name

### Community 86 - "Community 86"
Cohesion: 0.33
Nodes (5): name, services, volumes, pgdata, uploads

### Community 87 - "Community 87"
Cohesion: 0.40
Nodes (6): VITE_API_BASE_URL, build, args, context, dockerfile, build

### Community 88 - "Community 88"
Cohesion: 0.33
Nodes (6): condition, backend, depends_on, ports, restart, frontend

### Community 89 - "Community 89"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 90 - "Community 90"
Cohesion: 0.33
Nodes (5): apiVersion, kind, metadata, name, namespace

### Community 91 - "Community 91"
Cohesion: 0.50
Nodes (3): recortar(), redPrimero(), SHELL

### Community 92 - "Community 92"
Cohesion: 0.40
Nodes (5): name, runs-on, services, timeout-minutes, backend

### Community 93 - "Community 93"
Cohesion: 0.40
Nodes (5): on, pull_request, push, branches, branches

### Community 94 - "Community 94"
Cohesion: 0.40
Nodes (5): livenessProbe, failureThreshold, httpGet, periodSeconds, timeoutSeconds

### Community 95 - "Community 95"
Cohesion: 0.40
Nodes (5): readinessProbe, failureThreshold, httpGet, periodSeconds, timeoutSeconds

### Community 96 - "Community 96"
Cohesion: 0.40
Nodes (5): app.kubernetes.io/name, app.kubernetes.io/part-of, labels, template, metadata

### Community 97 - "Community 97"
Cohesion: 0.50
Nodes (4): name, runs-on, timeout-minutes, infraestructura

### Community 98 - "Community 98"
Cohesion: 0.50
Nodes (4): startupProbe, failureThreshold, httpGet, periodSeconds

## Knowledge Gaps
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Reporte` connect `Community 21` to `Community 32`, `Community 35`, `Community 5`, `Community 37`, `Community 10`, `Community 43`, `Community 52`, `Community 20`, `Community 22`, `Community 25`, `Community 59`, `Community 28`, `Community 30`, `Community 31`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Reporte` (e.g. with `CarrilAfectado` and `EstadoReporte`) actually correct?**
  _`Reporte` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.10913461538461539 - nodes in this community are weakly interconnected._
- **Why does `get_settings()` connect `Community 26` to `Community 2`, `Community 3`, `Community 4`, `Community 102`, `Community 45`, `Community 13`, `Community 48`, `Community 52`, `Community 23`, `Community 28`, `Community 30`, `Community 31`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.03635432667690732 - nodes in this community are weakly interconnected._
- **Why does `cola()` connect `Community 43` to `Community 59`, `Community 5`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.09023569023569024 - nodes in this community are weakly interconnected._