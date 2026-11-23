# Graph Report - calles-seguras-juarez  (2026-11-22)

## Corpus Check
- 176 files · ~105,915 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 31 file(s) not represented in the graph (top: (none) 11, .css 11, .xsd 2)

## Summary
- 1886 nodes · 5219 edges · 88 communities (79 shown, 9 thin omitted)
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
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
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

## God Nodes (most connected - your core abstractions)
1. `Icon()` - 78 edges
2. `Reporte` - 65 edges
3. `punto_unico()` - 56 edges
4. `react` - 43 edges
5. `crear_reporte()` - 42 edges
6. `get_settings()` - 39 edges
7. `payload_bache()` - 39 edges
8. `ErrorAPI` - 31 edges
9. `TipoDano` - 28 edges
10. `ApiError` - 26 edges

## Surprising Connections (you probably didn't know these)
- `run_migrations_offline()` --calls--> `get_settings()`  [EXTRACTED]
  db/migrations/env.py → backend/app/core/config.py
- `run_migrations_online()` --calls--> `get_settings()`  [EXTRACTED]
  db/migrations/env.py → backend/app/core/config.py
- `sembrar_operacion()` --calls--> `CatalogoTipoDano`  [INFERRED]
  db/seed.py → backend/app/models/operacion.py
- `sembrar_operacion()` --calls--> `CatalogoMotivoRechazo`  [INFERRED]
  db/seed.py → backend/app/models/operacion.py
- `sembrar_operacion()` --calls--> `Cuadrilla`  [INFERRED]
  db/seed.py → backend/app/models/operacion.py

## Import Cycles
- None detected.

## Communities (88 total, 9 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (9): run_migrations_offline(), run_migrations_online(), _ejecutar(), upgrade(), Generador, main(), sembrar_reportes(), sembrar_territorio() (+1 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (59): AvanceResponse, BacheAsignado, CambiarEstadoRequest, CambiarEstadoResponse, CambiarRolRequest, CambiarRolResponse, CampoFormulario, Centro (+51 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (14): Base, pg_enum(), ConfirmacionReporte, EstadoReporte, RolUsuario, TipoConfirmacion, HistorialEstado, AsignacionCuadrilla (+6 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (25): pronostico(), riesgo_inundacion(), longevidad(), moderacion(), puntos_recurrentes(), resumen(), sectores(), IndicadoresLongevidad (+17 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (23): cambiar_estado(), cambiar_rol(), _colonia(), crear_colonia(), crear_motivo(), crear_sector(), crear_tipo(), editar_colonia() (+15 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (38): HeroMap(), Nodo, NODOS, LEYENDA, LIMITES, MapaReportes(), Props, ReportMap (+30 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (16): cola(), detalle(), fusionar(), transicionar(), _bloquear(), fusionar(), detalle(), _folio_principal() (+8 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (20): _cuenta_suspendida(), get_db(), requiere_rol(), usuario_actual(), _usuario_desde_token(), usuario_opcional(), colonia_catalogo(), colonias() (+12 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (23): fuera_de_juarez(), Ubicacion, ColoniaCercana, ColoniaSugerida, RespuestaGeocodificacion, RespuestaGeocodificacionInversa, ResultadoGeocodificacion, dentro_de_juarez() (+15 more)

### Community 9 - "Community 9"
Cohesion: 0.15
Nodes (27): agregar_colonia(), asignar(), avanzar(), _bache(), crear_cuadrilla(), _cuadrilla(), desvincular(), _detalle() (+19 more)

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (35): crear_reporte(), payload_bache(), payload_enc(), punto_unico(), test_confirmar_bache(), test_crear_bache(), test_delete_prohibido_y_base_de_datos_inmutable(), test_duplicado_bache_30_metros() (+27 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (35): App(), Icon(), ClimaIcono(), RainBanner(), AdminCatalogosPage(), FilaEditable(), FilasCatalogo(), AuditPage() (+27 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (15): CarrilAfectado, NivelAgua, ProfundidadBache, TamanoBache, Sector, estados(), tipos_dano(), _transiciones_publicas() (+7 more)

### Community 13 - "Community 13"
Cohesion: 0.12
Nodes (30): motivo_id(), asignar(), avance(), bache(), confirmaciones_de(), confirmar(), escenario_enlace(), este() (+22 more)

### Community 14 - "Community 14"
Cohesion: 0.12
Nodes (29): Estado, AuthArt(), AuthProvider(), AuthContext, AuthContextValue, LoginPage(), contraseñaValida(), RegisterPage() (+21 more)

### Community 15 - "Community 15"
Cohesion: 0.13
Nodes (20): hashear_contrasena(), verificar_contrasena(), cerrar_sesion(), login(), registro(), renovar(), yo(), LoginIn (+12 more)

### Community 16 - "Community 16"
Cohesion: 0.10
Nodes (17): Reporte, anotar_principales(), buscar_cercanos(), condiciones_publicas(), crear_reporte(), editar_reporte(), historial_publico(), listar_mios() (+9 more)

### Community 17 - "Community 17"
Cohesion: 0.12
Nodes (17): confirmar(), crear(), descargar_foto(), detalle(), editar(), eliminar(), _exportar(), exportar_csv() (+9 more)

### Community 18 - "Community 18"
Cohesion: 0.19
Nodes (26): ErrorMessage(), Guard(), PageIntro(), Pagination(), EmptyState(), Notice(), TableSkeleton(), useAuth() (+18 more)

### Community 19 - "Community 19"
Cohesion: 0.11
Nodes (30): FotosReporte(), ReportCard(), AVISO, BlockSkeleton(), ESTADO, Illustration(), Ilustracion, NIVEL (+22 more)

### Community 20 - "Community 20"
Cohesion: 0.09
Nodes (13): get_settings(), Settings, reiniciar_retroceso(), test_geocoding_fallback_sin_llave(), test_geocoding_limite_de_busquedas(), test_geocoding_locationiq_filtra_juarez_y_no_expone_la_llave(), _limpiar_limitador_geocoding(), test_clima_no_reintenta_durante_el_retroceso() (+5 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (15): leer(), leer_todas(), listar(), _out(), LeerTodasOut, NotificacionOut, PaginaNotificaciones, contar_no_leidas() (+7 more)

### Community 22 - "Community 22"
Cohesion: 0.12
Nodes (17): AlcantarillaIn, BacheIn, CandidatoDuplicado, CercanosRespuesta, ConfirmacionIn, ConfirmacionOut, EncharcamientoIn, HistorialPublico (+9 more)

### Community 23 - "Community 23"
Cohesion: 0.11
Nodes (21): revisar_trayecto(), AsignacionIn, AvanceIn, AvanceOut, CriteriosResumen, _CuadrillaCampos, CuadrillaCrear, CuadrillaEditar (+13 more)

### Community 24 - "Community 24"
Cohesion: 0.15
Nodes (20): desplazar(), primera_colonia(), avisos(), detalle(), nuevo_bache(), sembrar_enc(), test_aislamiento_estricto_entre_usuarios(), test_cada_cambio_de_estado_avisa_al_autor() (+12 more)

### Community 25 - "Community 25"
Cohesion: 0.14
Nodes (14): ReporteFoto, agregar_fotos(), autorizado_a_ver(), contar_de_usuario(), directorio_fotos(), exigir_acceso(), FotoRechazada, listar() (+6 more)

### Community 26 - "Community 26"
Cohesion: 0.12
Nodes (13): analizar(), _bool(), _error(), importar(), Resultado, _validar_integridad(), cargar_esquema(), _celda_segura() (+5 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (25): FotoPicker(), Props, cargarCatalogo(), cargarTipos(), enJuarez(), ErrorApiTexto(), LIMITES, ReportCreatePage() (+17 more)

### Community 28 - "Community 28"
Cohesion: 0.15
Nodes (20): _directorio_fotos(), importar(), nuevo_bache(), subir(), test_foto_valida_jpg_y_png_se_guardan_con_nombre_uuid(), test_fotos_al_confirmar_un_reporte_existente(), test_fotos_de_reporte_rechazado_no_se_revelan(), test_fotos_en_recibido_solo_autor_y_moderacion_luego_publicas() (+12 more)

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (23): BuscadorColonia(), cargar(), Aviso(), cargarCatalogo(), CARRILES, FormularioEdicion(), PROFUNDIDADES, ReportEditPage() (+15 more)

### Community 30 - "Community 30"
Cohesion: 0.10
Nodes (5): buscar(), inversa(), _limitar(), respuestas(), LimitadorVentana

### Community 31 - "Community 31"
Cohesion: 0.22
Nodes (17): ErrorAPI, Usuario, ColoniaCrear, ColoniaEditar, cambiar_estado(), cambiar_rol(), _confirmar(), crear_colonia() (+9 more)

### Community 32 - "Community 32"
Cohesion: 0.11
Nodes (23): devDependencies, oxlint@^1.90.0, @types/leaflet@^1.9.22, @types/leaflet.markercluster@^1.5.6, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@~7.0.2 (+15 more)

### Community 33 - "Community 33"
Cohesion: 0.14
Nodes (19): CampanaNotificaciones(), IconName, PATHS, EventoInstalacion, InstalarApp(), actual(), Enlace, Marca() (+11 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (10): claves(), test_alcantarilla_alta_y_cliente_no_fija_severidad(), test_bloqueo_por_intentos_fallidos(), test_cerrar_sesion_revoca_token(), test_clima_cache_y_degradacion(), test_fuera_de_juarez_422(), test_maquina_de_estados_completa(), test_rechazo_exige_motivo_y_oculta_el_reporte() (+2 more)

### Community 35 - "Community 35"
Cohesion: 0.21
Nodes (11): Severidad, TipoDano, HistorialModeracionItem, ReporteModeracion, ReporteModeracionItem, TransicionIn, TransicionOut, DetalleAlcantarilla (+3 more)

### Community 36 - "Community 36"
Cohesion: 0.17
Nodes (14): _asignacion_del_enlace(), asignar(), avanzar(), crear(), cuadrillas_de_enlace(), desvincular_enlace(), editar(), eliminar() (+6 more)

### Community 37 - "Community 37"
Cohesion: 0.14
Nodes (13): ciudadano(), ciudadanos(), client(), coordinador(), crear_cuenta(), Cuenta, db(), moderador() (+5 more)

### Community 38 - "Community 38"
Cohesion: 0.23
Nodes (20): BannerRed(), actualizar(), Borrador, cargarCola(), clave(), descartar(), descartarAvisoEnviados(), encolar() (+12 more)

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (21): FusionarDialog(), cargarAuditoria(), cargarTablero(), DatosTablero, ESTADOS_AUDITADOS, KPI, makeQuery(), QueueTable() (+13 more)

### Community 40 - "Community 40"
Cohesion: 0.14
Nodes (6): _ciclo_vencimiento(), encabezados_de_seguridad(), _expirar_encharcamientos(), lifespan(), salud(), canal_encharcamientos()

### Community 41 - "Community 41"
Cohesion: 0.18
Nodes (12): CalleRiesgo, ClimaActual, ClimaHora, Pronostico, RiesgoInundacion, ColoniaRef, CuerpoError, DetalleError (+4 more)

### Community 42 - "Community 42"
Cohesion: 0.21
Nodes (17): ATRIBUCION, CENTRO_JUAREZ, descripcionMarcador(), ERRORES_PARA_FALLAR, GLIFO, iconoDe(), LIMITES, TILES_URL (+9 more)

### Community 43 - "Community 43"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 44 - "Community 44"
Cohesion: 0.11
Nodes (19): environment, ACCESS_TOKEN_EXPIRE_MINUTES, APP_ENV, APP_TIMEZONE, DATABASE_URL, FRONTEND_URL, GEOCODING_API_KEY, GEOCODING_API_URL (+11 more)

### Community 45 - "Community 45"
Cohesion: 0.18
Nodes (11): ColoniaAdmin, _ColoniaBase, EstadoUsuarioIn, EstadoUsuarioOut, ImportacionCatalogos, RolIn, RolOut, SectorAdmin (+3 more)

### Community 46 - "Community 46"
Cohesion: 0.16
Nodes (3): emitir(), _firma(), GestorConexiones

### Community 47 - "Community 47"
Cohesion: 0.14
Nodes (3): CacheClima, Colonia, parsear_bbox()

### Community 48 - "Community 48"
Cohesion: 0.27
Nodes (12): CatalogoMotivoRechazo, CatalogoTipoDano, crear_motivo(), crear_tipo(), editar_motivo(), editar_tipo(), exigir_tipo_activo(), _guardar() (+4 more)

### Community 49 - "Community 49"
Cohesion: 0.13
Nodes (3): cercanos(), mios(), confirmados_por_usuario()

### Community 50 - "Community 50"
Cohesion: 0.28
Nodes (10): _base(), _filtros(), mas_antiguos(), moderacion(), por_sector(), _redondear(), resumen(), fecha_local_sql() (+2 more)

### Community 51 - "Community 51"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 52 - "Community 52"
Cohesion: 0.21
Nodes (4): a_local(), fecha_local(), hoy_local(), generar_folio()

### Community 53 - "Community 53"
Cohesion: 0.21
Nodes (4): OrigenCambio, confirmar(), _no_confirmable(), fijar_contexto()

### Community 54 - "Community 54"
Cohesion: 0.24
Nodes (13): ReportGridSkeleton(), Cercano, dentroDeJuarez(), distanciaKm(), esEncharcamientoActivo(), esIntransitable(), LIMITES, Radar() (+5 more)

### Community 55 - "Community 55"
Cohesion: 0.19
Nodes (15): steps, steps, VITE_API_BASE_URL, steps, env, name, run, shell (+7 more)

### Community 56 - "Community 56"
Cohesion: 0.27
Nodes (10): ahora_utc(), _armar(), _consultar_proveedor(), _degradado(), hay_alerta_lluvia(), _nivel(), obtener_pronostico(), _proximas_horas() (+2 more)

### Community 57 - "Community 57"
Cohesion: 0.16
Nodes (9): armar_pagina(), caja_envolvente(), haversine_m(), distancia_a_polilinea(), encharcamientos_cercanos(), _linea_recta(), obtener_ruta(), Ruta (+1 more)

### Community 58 - "Community 58"
Cohesion: 0.22
Nodes (9): _campo(), _cuerpo(), registrar_manejadores(), _error_api(), _http(), _inesperado(), _validacion(), _traducir_validacion() (+1 more)

### Community 59 - "Community 59"
Cohesion: 0.22
Nodes (6): resumen_colonia(), agregar(), favoritas(), ids_favoritas(), quitar(), resumen_colonia()

### Community 60 - "Community 60"
Cohesion: 0.21
Nodes (4): contrasena_valida(), crear_token(), decodificar_token(), test_politica_de_contrasena()

### Community 61 - "Community 61"
Cohesion: 0.17
Nodes (11): concurrency, cancel-in-progress, group, name, runs-on, timeout-minutes, jobs, dependencias (+3 more)

### Community 62 - "Community 62"
Cohesion: 0.20
Nodes (4): ParametrosPagina, buscar_colonias(), es_prefijo_cp(), listar_sectores()

### Community 63 - "Community 63"
Cohesion: 0.18
Nodes (11): env, name, runs-on, timeout-minutes, APP_ENV, DATABASE_URL, FRONTEND_URL, GEOCODING_API_KEY (+3 more)

### Community 64 - "Community 64"
Cohesion: 0.33
Nodes (6): a_mi_reporte(), a_publico(), a_resumen(), etiqueta_publica(), longevidad_dias(), vigencia_de()

### Community 65 - "Community 65"
Cohesion: 0.20
Nodes (10): environment, image, ports, restart, volumes, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER (+2 more)

### Community 67 - "Community 67"
Cohesion: 0.22
Nodes (9): services, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, env, image, options, ports (+1 more)

### Community 68 - "Community 68"
Cohesion: 0.25
Nodes (8): command, depends_on, ports, restart, volumes, condition, db, backend

### Community 69 - "Community 69"
Cohesion: 0.25
Nodes (8): dependencies, leaflet@^1.9.4, leaflet.markercluster@^1.5.3, react@^19.3.1, react-dom@^19.3.1, leaflet, leaflet.markercluster, react-dom

### Community 70 - "Community 70"
Cohesion: 0.43
Nodes (4): FotoOut, FotoRechazadaOut, FotosSubidas, ListaFotos

### Community 71 - "Community 71"
Cohesion: 0.48
Nodes (7): healthcheck, healthcheck, interval, retries, start_period, test, timeout

### Community 72 - "Community 72"
Cohesion: 0.29
Nodes (7): run, defaults, name, runs-on, timeout-minutes, frontend, working-directory

### Community 73 - "Community 73"
Cohesion: 0.33
Nodes (5): name, services, volumes, pgdata, uploads

### Community 74 - "Community 74"
Cohesion: 0.40
Nodes (6): VITE_API_BASE_URL, build, args, context, dockerfile, build

### Community 75 - "Community 75"
Cohesion: 0.33
Nodes (6): condition, backend, depends_on, ports, restart, frontend

### Community 76 - "Community 76"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 77 - "Community 77"
Cohesion: 0.40
Nodes (5): scripts, build, dev, lint, preview

### Community 78 - "Community 78"
Cohesion: 0.50
Nodes (3): recortar(), redPrimero(), SHELL

### Community 79 - "Community 79"
Cohesion: 0.40
Nodes (5): on, pull_request, push, branches, branches

## Knowledge Gaps
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Reporte` connect `Community 16` to `Community 64`, `Community 0`, `Community 2`, `Community 35`, `Community 36`, `Community 3`, `Community 6`, `Community 12`, `Community 46`, `Community 49`, `Community 17`, `Community 21`, `Community 56`, `Community 25`, `Community 26`, `Community 24`, `Community 57`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Reporte` (e.g. with `CarrilAfectado` and `EstadoReporte`) actually correct?**
  _`Reporte` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.055191256830601096 - nodes in this community are weakly interconnected._
- **Why does `get_settings()` connect `Community 20` to `Community 0`, `Community 34`, `Community 40`, `Community 8`, `Community 12`, `Community 47`, `Community 50`, `Community 52`, `Community 56`, `Community 25`, `Community 26`, `Community 60`, `Community 57`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.03672316384180791 - nodes in this community are weakly interconnected._
- **Why does `cola()` connect `Community 6` to `Community 35`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.11990950226244344 - nodes in this community are weakly interconnected._