# Graph Report - calles-seguras-juarez  (2026-11-22)

## Corpus Check
- 157 files · ~89,564 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 30 file(s) not represented in the graph (top: (none) 11, .css 10, .xsd 2)

## Summary
- 1588 nodes · 4182 edges · 81 communities (68 shown, 13 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 101 edges (avg confidence: 0.9)
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
- Community 73
- Community 74
- Community 75
- Community 76

## God Nodes (most connected - your core abstractions)
1. `Icon()` - 57 edges
2. `Reporte` - 48 edges
3. `ErrorAPI` - 37 edges
4. `get_settings()` - 37 edges
5. `react` - 34 edges
6. `Usuario` - 26 edges
7. `expirar_vencidos()` - 26 edges
8. `crear_reporte()` - 24 edges
9. `EmptyState()` - 24 edges
10. `punto_unico()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `sembrar_territorio()` --calls--> `Sector`  [INFERRED]
  db/seed.py → backend/app/models/territorio.py
- `run_migrations_offline()` --calls--> `get_settings()`  [EXTRACTED]
  db/migrations/env.py → backend/app/core/config.py
- `run_migrations_online()` --calls--> `get_settings()`  [EXTRACTED]
  db/migrations/env.py → backend/app/core/config.py
- `sembrar_usuarios()` --calls--> `contrasena_valida()`  [EXTRACTED]
  db/seed.py → backend/app/core/security.py
- `sembrar_usuarios()` --calls--> `hashear_contrasena()`  [EXTRACTED]
  db/seed.py → backend/app/core/security.py

## Import Cycles
- None detected.

## Communities (81 total, 13 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (71): Aviso(), cargarCatalogo(), CARRILES, PROFUNDIDADES, ReportEditPage(), TAMANOS, CambiarEstadoRequest, CambiarEstadoResponse (+63 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (29): fuera_de_juarez(), buscar(), inversa(), _limitar(), armar_pagina(), SectorRef, Ubicacion, ColoniaCercana (+21 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (40): analizar(), _bool(), _error(), importar(), Resultado, _validar_integridad(), cargar_esquema(), _celda_segura() (+32 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (13): usuario_actual(), _usuario_desde_token(), usuario_opcional(), a_local(), fecha_local(), hoy_local(), Usuario, generar_folio() (+5 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (43): ErrorMessage(), Guard(), PageIntro(), Pagination(), EmptyState(), TableSkeleton(), obtenerJson(), useCargaDatos() (+35 more)

### Community 5 - "Community 5"
Cohesion: 0.13
Nodes (8): Base, pg_enum(), ConfirmacionReporte, EstadoReporte, OrigenCambio, TipoConfirmacion, HistorialEstado, fijar_contexto()

### Community 6 - "Community 6"
Cohesion: 0.10
Nodes (22): contrasena_valida(), crear_token(), decodificar_token(), hashear_contrasena(), verificar_contrasena(), cerrar_sesion(), login(), registro() (+14 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (8): get_db(), _ciclo_vencimiento(), encabezados_de_seguridad(), _expirar_encharcamientos(), lifespan(), salud(), canal_encharcamientos(), LimitadorVentana

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (22): cambiar_estado(), cambiar_rol(), _colonia(), crear_colonia(), crear_sector(), editar_colonia(), editar_sector(), importar_catalogos_xml() (+14 more)

### Community 9 - "Community 9"
Cohesion: 0.10
Nodes (36): HeroMap(), Nodo, NODOS, LEYENDA, LIMITES, MapaReportes(), Props, ReportMap (+28 more)

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (31): Estado, AuthArt(), AuthProvider(), AuthContext, AuthContextValue, EstadoCarga, Resultado, EstadoEnVivo (+23 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (33): FotosReporte(), ReportCard(), AVISO, BlockSkeleton(), ESTADO, Illustration(), Ilustracion, NIVEL (+25 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (9): cola(), detalle(), transicionar(), detalle(), _item(), listar_cola(), _obtener(), _reportes_por_autor_24h() (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (13): get_settings(), Settings, test_geocoding_fallback_sin_llave(), test_geocoding_limite_de_busquedas(), test_geocoding_locationiq_filtra_juarez_y_no_expone_la_llave(), _limpiar_limitador_geocoding(), test_fallback_de_geocoding_no_remite_a_un_mapa(), test_geocoding_inversa_con_proveedor_y_sin_exponer_llave() (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (15): Reporte, buscar_cercanos(), condiciones_publicas(), contar_reportes_ultima_hora(), editar_reporte(), historial_publico(), listar_mios(), listar_publicos() (+7 more)

### Community 15 - "Community 15"
Cohesion: 0.15
Nodes (22): App(), CampanaNotificaciones(), Icon(), IconName, PATHS, EventoInstalacion, InstalarApp(), ClimaIcono() (+14 more)

### Community 16 - "Community 16"
Cohesion: 0.11
Nodes (14): leer(), leer_todas(), listar(), _out(), LeerTodasOut, NotificacionOut, contar_no_leidas(), _fecha() (+6 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (26): FotoPicker(), Props, cargarCatalogo(), enJuarez(), ErrorApiTexto(), LIMITES, ReportCreatePage(), TIPO_AYUDA (+18 more)

### Community 18 - "Community 18"
Cohesion: 0.13
Nodes (16): Severidad, HistorialModeracionItem, ReporteModeracion, ReporteModeracionItem, TransicionIn, TransicionOut, DetalleAlcantarilla, DetalleBache (+8 more)

### Community 19 - "Community 19"
Cohesion: 0.14
Nodes (14): ReporteFoto, agregar_fotos(), autorizado_a_ver(), contar_de_usuario(), directorio_fotos(), exigir_acceso(), FotoRechazada, listar() (+6 more)

### Community 20 - "Community 20"
Cohesion: 0.12
Nodes (17): colonia_catalogo(), colonias(), estados(), sectores(), tipos_dano(), CampoFormulario, CatalogoEstados, CatalogoTiposDano (+9 more)

### Community 21 - "Community 21"
Cohesion: 0.12
Nodes (13): CalleRiesgo, ClimaActual, ClimaHora, Pronostico, RiesgoInundacion, ColoniaRef, CuerpoError, DetalleError (+5 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (13): AlcantarillaIn, BacheIn, ConfirmacionIn, ConfirmacionOut, EncharcamientoIn, MapaRespuesta, MarcadorMapa, MiReporte (+5 more)

### Community 23 - "Community 23"
Cohesion: 0.16
Nodes (12): confirmar(), crear(), descargar_foto(), _exportar(), exportar_csv(), exportar_xml(), FiltrosReportes, listar() (+4 more)

### Community 24 - "Community 24"
Cohesion: 0.18
Nodes (21): crear_reporte(), desplazar(), payload_bache(), payload_enc(), primera_colonia(), punto_unico(), test_alcantarilla_alta_y_cliente_no_fija_severidad(), test_confirmar_bache() (+13 more)

### Community 25 - "Community 25"
Cohesion: 0.23
Nodes (14): ErrorAPI, Colonia, Sector, cambiar_estado(), cambiar_rol(), _confirmar(), crear_colonia(), crear_sector() (+6 more)

### Community 26 - "Community 26"
Cohesion: 0.13
Nodes (11): CarrilAfectado, NivelAgua, ProfundidadBache, TamanoBache, TipoDano, ParametrosPagina, listar_usuarios(), buscar_colonias() (+3 more)

### Community 27 - "Community 27"
Cohesion: 0.13
Nodes (11): longevidad(), moderacion(), puntos_recurrentes(), resumen(), sectores(), anotar(), inicio_de_anio(), listar_puntos() (+3 more)

### Community 28 - "Community 28"
Cohesion: 0.17
Nodes (10): detalle(), sembrar_enc(), test_dia_se_cuenta_en_hora_de_ciudad_juarez_no_en_utc(), test_no_cuenta_otro_anio_ni_rechazados_ni_pavimento(), test_pavimento_no_lleva_datos_de_recurrencia(), test_radio_exacto_de_50_metros(), test_tres_dias_distintos_es_punto_recurrente(), test_varios_reportes_el_mismo_dia_cuentan_como_un_dia() (+2 more)

### Community 29 - "Community 29"
Cohesion: 0.23
Nodes (20): BannerRed(), actualizar(), Borrador, cargarCola(), clave(), descartar(), descartarAvisoEnviados(), encolar() (+12 more)

### Community 30 - "Community 30"
Cohesion: 0.23
Nodes (11): ahora_utc(), _base(), _filtros(), mas_antiguos(), moderacion(), por_sector(), _redondear(), resumen() (+3 more)

### Community 31 - "Community 31"
Cohesion: 0.14
Nodes (19): devDependencies, oxlint@^1.90.0, @types/leaflet@^1.9.22, @types/leaflet.markercluster@^1.5.6, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@~7.0.2 (+11 more)

### Community 32 - "Community 32"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 33 - "Community 33"
Cohesion: 0.25
Nodes (11): CacheClima, _armar(), _consultar_proveedor(), _degradado(), hay_alerta_lluvia(), _nivel(), obtener_pronostico(), _proximas_horas() (+3 more)

### Community 34 - "Community 34"
Cohesion: 0.14
Nodes (7): claves(), test_bloqueo_por_intentos_fallidos(), test_cerrar_sesion_revoca_token(), test_maquina_de_estados_completa(), test_rechazo_exige_motivo_y_oculta_el_reporte(), test_respuestas_publicas_sin_datos_personales(), transicionar()

### Community 35 - "Community 35"
Cohesion: 0.21
Nodes (9): _foto_out(), historial(), subir_fotos(), FotoOut, FotoRechazadaOut, FotosSubidas, ListaFotos, HistorialPublico (+1 more)

### Community 36 - "Community 36"
Cohesion: 0.12
Nodes (17): environment, ACCESS_TOKEN_EXPIRE_MINUTES, APP_ENV, APP_TIMEZONE, DATABASE_URL, FRONTEND_URL, GEOCODING_API_KEY, GEOCODING_API_URL (+9 more)

### Community 37 - "Community 37"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 39 - "Community 39"
Cohesion: 0.15
Nodes (4): cercanos(), mios(), CandidatoDuplicado, CercanosRespuesta

### Community 40 - "Community 40"
Cohesion: 0.23
Nodes (8): ciudadano(), ciudadanos(), client(), coordinador(), crear_cuenta(), Cuenta, db(), moderador()

### Community 41 - "Community 41"
Cohesion: 0.21
Nodes (10): test_bache_exige_campos_condicionales(), test_descripcion_maximo_500_y_campos_extra(), test_encharcamiento_activo_a_historico_no_es_manual(), test_encharcamiento_intransitable_exige_riesgo(), test_encharcamiento_no_intransitable_rechaza_riesgo(), test_fuera_de_juarez_se_rechaza(), test_haversine_30_metros(), test_limites_de_juarez() (+2 more)

### Community 42 - "Community 42"
Cohesion: 0.24
Nodes (13): ReportGridSkeleton(), Cercano, dentroDeJuarez(), distanciaKm(), esEncharcamientoActivo(), esIntransitable(), LIMITES, Radar() (+5 more)

### Community 43 - "Community 43"
Cohesion: 0.19
Nodes (15): steps, steps, VITE_API_BASE_URL, steps, env, name, run, shell (+7 more)

### Community 44 - "Community 44"
Cohesion: 0.31
Nodes (11): IndicadoresLongevidad, IndicadoresModeracion, IndicadoresResumen, IndicadoresSectores, IndicadorSector, LongevidadItem, Periodo, PuntoRecurrenteOut (+3 more)

### Community 45 - "Community 45"
Cohesion: 0.27
Nodes (12): ATRIBUCION, CENTRO_JUAREZ, descripcionMarcador(), ERRORES_PARA_FALLAR, GLIFO, iconoDe(), LIMITES, TILES_URL (+4 more)

### Community 47 - "Community 47"
Cohesion: 0.27
Nodes (7): requiere_rol(), _dependencia(), RolUsuario, disponibles(), tabla(), validar_transicion(), _resultado()

### Community 48 - "Community 48"
Cohesion: 0.17
Nodes (11): concurrency, cancel-in-progress, group, name, runs-on, timeout-minutes, jobs, dependencias (+3 more)

### Community 49 - "Community 49"
Cohesion: 0.27
Nodes (8): _campo(), _cuerpo(), registrar_manejadores(), _error_api(), _http(), _inesperado(), _validacion(), _traducir_validacion()

### Community 50 - "Community 50"
Cohesion: 0.22
Nodes (5): calcular_severidad(), severidad_bache(), severidad_encharcamiento(), test_alcantarilla_siempre_alta(), test_severidad_bache()

### Community 51 - "Community 51"
Cohesion: 0.25
Nodes (8): crear_reporte(), _por_clave(), _verificar_limite_por_hora(), siguiente_evento(), test_duplicado_al_reenviar_conserva_el_conflicto_para_explicarlo(), test_ws_avisa_cuando_vence_la_vigencia(), test_ws_emite_encharcamiento_nuevo_sin_datos_personales(), test_ws_no_difunde_baches_y_si_confirmaciones_y_retiros()

### Community 52 - "Community 52"
Cohesion: 0.18
Nodes (11): env, name, runs-on, timeout-minutes, APP_ENV, DATABASE_URL, FRONTEND_URL, GEOCODING_API_KEY (+3 more)

### Community 54 - "Community 54"
Cohesion: 0.27
Nodes (5): detalle(), editar(), eliminar(), confirmados_por_usuario(), conteos_confirmaciones()

### Community 55 - "Community 55"
Cohesion: 0.20
Nodes (10): environment, image, ports, restart, volumes, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER (+2 more)

### Community 57 - "Community 57"
Cohesion: 0.22
Nodes (9): services, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, env, image, options, ports (+1 more)

### Community 58 - "Community 58"
Cohesion: 0.54
Nodes (8): avisos(), nuevo_bache(), test_aislamiento_estricto_entre_usuarios(), test_cada_cambio_de_estado_avisa_al_autor(), test_marcar_leida_y_marcar_todas(), test_quien_cambia_el_estado_no_se_notifica_a_si_mismo(), test_rechazo_avisa_con_motivo(), transicionar()

### Community 59 - "Community 59"
Cohesion: 0.25
Nodes (8): command, depends_on, ports, restart, volumes, condition, db, backend

### Community 60 - "Community 60"
Cohesion: 0.25
Nodes (8): dependencies, leaflet@^1.9.4, leaflet.markercluster@^1.5.3, react@^19.3.1, react-dom@^19.3.1, leaflet, leaflet.markercluster, react-dom

### Community 61 - "Community 61"
Cohesion: 0.48
Nodes (7): healthcheck, healthcheck, interval, retries, start_period, test, timeout

### Community 62 - "Community 62"
Cohesion: 0.29
Nodes (7): run, defaults, name, runs-on, timeout-minutes, frontend, working-directory

### Community 63 - "Community 63"
Cohesion: 0.33
Nodes (5): name, services, volumes, pgdata, uploads

### Community 64 - "Community 64"
Cohesion: 0.40
Nodes (6): VITE_API_BASE_URL, build, args, context, dockerfile, build

### Community 65 - "Community 65"
Cohesion: 0.33
Nodes (6): condition, backend, depends_on, ports, restart, frontend

### Community 66 - "Community 66"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 67 - "Community 67"
Cohesion: 0.40
Nodes (3): reiniciar_retroceso(), test_clima_cache_y_degradacion(), test_clima_no_reintenta_durante_el_retroceso()

### Community 68 - "Community 68"
Cohesion: 0.40
Nodes (4): vite@^8.3.6, @vitejs/plugin-react@^6.1.2, vite, @vitejs/plugin-react

### Community 69 - "Community 69"
Cohesion: 0.40
Nodes (5): scripts, build, dev, lint, preview

### Community 70 - "Community 70"
Cohesion: 0.50
Nodes (3): recortar(), redPrimero(), SHELL

### Community 71 - "Community 71"
Cohesion: 0.40
Nodes (5): on, pull_request, push, branches, branches

## Knowledge Gaps
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `react` connect `Community 10` to `Community 0`, `Community 4`, `Community 9`, `Community 42`, `Community 11`, `Community 45`, `Community 15`, `Community 17`, `Community 56`, `Community 60`, `Community 29`, `Community 31`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `ErrorAPI` (e.g. with `hay_alerta_lluvia()` and `_resultado()`) actually correct?**
  _`ErrorAPI` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.033866057838660577 - nodes in this community are weakly interconnected._
- **Why does `get_settings()` connect `Community 13` to `Community 33`, `Community 2`, `Community 3`, `Community 1`, `Community 5`, `Community 6`, `Community 7`, `Community 34`, `Community 19`, `Community 30`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06845238095238096 - nodes in this community are weakly interconnected._
- **Why does `expirar_vencidos()` connect `Community 23` to `Community 35`, `Community 5`, `Community 7`, `Community 39`, `Community 44`, `Community 12`, `Community 53`, `Community 21`, `Community 54`, `Community 27`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.062146892655367235 - nodes in this community are weakly interconnected._