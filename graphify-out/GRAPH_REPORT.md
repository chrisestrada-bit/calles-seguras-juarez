# Graph Report - calles-seguras-juarez  (2026-11-22)

## Corpus Check
- 123 files · ~70,948 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 25 file(s) not represented in the graph (top: (none) 11, .css 8, .woff2 2)

## Summary
- 1202 nodes · 3407 edges · 52 communities (45 shown, 7 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 116 edges (avg confidence: 0.92)
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

## God Nodes (most connected - your core abstractions)
1. `Usuario` - 53 edges
2. `ErrorAPI` - 47 edges
3. `Icon()` - 42 edges
4. `Reporte` - 36 edges
5. `ahora_utc()` - 33 edges
6. `get_settings()` - 31 edges
7. `SectorRef` - 26 edges
8. `expirar_vencidos()` - 24 edges
9. `react` - 24 edges
10. `ParametrosPagina` - 22 edges

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

## Communities (52 total, 7 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (35): get_db(), Base, columna_fecha_creacion(), pg_enum(), CacheClima, ConfirmacionReporte, CarrilAfectado, EstadoReporte (+27 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (44): requiere_rol(), _dependencia(), ErrorAPI, RolUsuario, cambiar_estado(), cambiar_rol(), _colonia(), crear_colonia() (+36 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (26): fuera_de_juarez(), buscar(), inversa(), _limitar(), ColoniaCercana, ColoniaSugerida, RespuestaGeocodificacion, ResultadoGeocodificacion (+18 more)

### Community 3 - "Community 3"
Cohesion: 0.04
Nodes (53): DatosTablero, AuditoriaItem, CambiarEstadoRequest, CambiarRolRequest, CampoFormulario, Centro, ClimaActual, Colonia (+45 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (46): HeroMap(), Nodo, NODOS, TypeGlyph(), EstadoCarga, Resultado, cargarCatalogo(), cargarReportes() (+38 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (26): ahora_utc(), pronostico(), riesgo_inundacion(), longevidad(), moderacion(), resumen(), sectores(), _armar() (+18 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (18): usuario_actual(), _usuario_desde_token(), usuario_opcional(), Usuario, generar_folio(), calcular_severidad(), crear_reporte(), editar_reporte() (+10 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (45): ErrorMessage(), Guard(), PageIntro(), Pagination(), BlockSkeleton(), EmptyState(), Notice(), SeverityBadge() (+37 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (24): colonia_catalogo(), colonias(), estados(), sectores(), tipos_dano(), CampoFormulario, CatalogoEstados, CatalogoTiposDano (+16 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (23): contrasena_valida(), crear_token(), decodificar_token(), hashear_contrasena(), verificar_contrasena(), cerrar_sesion(), login(), registro() (+15 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (27): crear_reporte(), desplazar(), payload_bache(), payload_enc(), primera_colonia(), punto_unico(), claves(), test_alcantarilla_alta_y_cliente_no_fija_severidad() (+19 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (13): get_settings(), Settings, test_geocoding_fallback_sin_llave(), test_geocoding_limite_de_busquedas(), test_geocoding_locationiq_filtra_juarez_y_no_expone_la_llave(), _limpiar_limitador_geocoding(), test_fallback_de_geocoding_no_remite_a_un_mapa(), test_geocoding_inversa_con_proveedor_y_sin_exponer_llave() (+5 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (13): _campo(), _cuerpo(), registrar_manejadores(), _error_api(), _http(), _inesperado(), _validacion(), _traducir_validacion() (+5 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (28): ReportCard(), AVISO, ESTADO, Illustration(), Ilustracion, NIVEL, ReportGridSkeleton(), TIPO (+20 more)

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (16): historial(), ReporteModeracion, AlcantarillaIn, BacheIn, DetalleAlcantarilla, DetalleBache, DetalleEncharcamiento, EncharcamientoIn (+8 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (28): dependencies, react@^19.3.1, react-dom@^19.3.1, devDependencies, oxlint@^1.90.0, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0 (+20 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (22): App(), Icon(), IconName, PATHS, ClimaIcono(), RainBanner(), actual(), Enlace (+14 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (9): cercanos(), detalle(), editar(), eliminar(), listar(), mios(), CandidatoDuplicado, CercanosRespuesta (+1 more)

### Community 18 - "Community 18"
Cohesion: 0.15
Nodes (14): CalleRiesgo, ClimaActual, ClimaHora, Pronostico, RiesgoInundacion, ColoniaRef, CuerpoError, DetalleError (+6 more)

### Community 19 - "Community 19"
Cohesion: 0.15
Nodes (19): AuthArt(), AuthContext, AuthContextValue, useAuth(), consulta(), ROLES, LoginPage(), contraseñaValida() (+11 more)

### Community 20 - "Community 20"
Cohesion: 0.18
Nodes (11): HistorialModeracionItem, ReporteModeracionItem, TransicionIn, TransicionOut, detalle(), _item(), listar_cola(), _obtener() (+3 more)

### Community 21 - "Community 21"
Cohesion: 0.16
Nodes (12): AuthProvider(), API_BASE_URL, ApiError, apiFetch(), configurarSesionExpirada(), eliminarToken(), guardarToken(), leerError() (+4 more)

### Community 22 - "Community 22"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 23 - "Community 23"
Cohesion: 0.15
Nodes (4): cola(), detalle(), transicionar(), expirar_vencidos()

### Community 24 - "Community 24"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 25 - "Community 25"
Cohesion: 0.21
Nodes (9): ciudadano(), ciudadanos(), client(), coordinador(), crear_cuenta(), Cuenta, db(), moderador() (+1 more)

### Community 26 - "Community 26"
Cohesion: 0.12
Nodes (16): environment, ACCESS_TOKEN_EXPIRE_MINUTES, APP_ENV, APP_TIMEZONE, DATABASE_URL, FRONTEND_URL, GEOCODING_API_KEY, GEOCODING_API_URL (+8 more)

### Community 27 - "Community 27"
Cohesion: 0.21
Nodes (9): test_bache_exige_campos_condicionales(), test_descripcion_maximo_500_y_campos_extra(), test_encharcamiento_activo_a_historico_no_es_manual(), test_encharcamiento_intransitable_exige_riesgo(), test_encharcamiento_no_intransitable_rechaza_riesgo(), test_fuera_de_juarez_se_rechaza(), test_haversine_30_metros(), test_limites_de_juarez() (+1 more)

### Community 28 - "Community 28"
Cohesion: 0.19
Nodes (15): steps, steps, VITE_API_BASE_URL, steps, env, name, run, shell (+7 more)

### Community 29 - "Community 29"
Cohesion: 0.29
Nodes (8): Reporte, a_mi_reporte(), a_publico(), a_resumen(), etiqueta_publica(), longevidad_dias(), vigencia_de(), esta_vigente()

### Community 30 - "Community 30"
Cohesion: 0.17
Nodes (11): concurrency, cancel-in-progress, group, name, runs-on, timeout-minutes, jobs, dependencias (+3 more)

### Community 32 - "Community 32"
Cohesion: 0.18
Nodes (11): env, name, runs-on, timeout-minutes, APP_ENV, DATABASE_URL, FRONTEND_URL, GEOCODING_API_KEY (+3 more)

### Community 33 - "Community 33"
Cohesion: 0.22
Nodes (5): confirmar(), crear(), ConfirmacionOut, confirmar(), _no_confirmable()

### Community 34 - "Community 34"
Cohesion: 0.20
Nodes (10): environment, image, ports, restart, volumes, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER (+2 more)

### Community 35 - "Community 35"
Cohesion: 0.36
Nodes (3): a_local(), fecha_local(), hoy_local()

### Community 36 - "Community 36"
Cohesion: 0.22
Nodes (9): services, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, env, image, options, ports (+1 more)

### Community 37 - "Community 37"
Cohesion: 0.29
Nodes (7): command, depends_on, ports, restart, condition, db, backend

### Community 38 - "Community 38"
Cohesion: 0.48
Nodes (7): healthcheck, healthcheck, interval, retries, start_period, test, timeout

### Community 39 - "Community 39"
Cohesion: 0.29
Nodes (7): run, defaults, name, runs-on, timeout-minutes, frontend, working-directory

### Community 40 - "Community 40"
Cohesion: 0.40
Nodes (6): VITE_API_BASE_URL, build, args, context, dockerfile, build

### Community 41 - "Community 41"
Cohesion: 0.33
Nodes (6): condition, backend, depends_on, ports, restart, frontend

### Community 42 - "Community 42"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 43 - "Community 43"
Cohesion: 0.40
Nodes (3): reiniciar_retroceso(), test_clima_cache_y_degradacion(), test_clima_no_reintenta_durante_el_retroceso()

### Community 44 - "Community 44"
Cohesion: 0.40
Nodes (4): name, services, volumes, pgdata

### Community 45 - "Community 45"
Cohesion: 0.40
Nodes (5): on, pull_request, push, branches, branches

## Knowledge Gaps
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ErrorAPI` connect `Community 1` to `Community 0`, `Community 33`, `Community 2`, `Community 5`, `Community 6`, `Community 8`, `Community 9`, `Community 12`, `Community 17`, `Community 20`, `Community 27`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `ErrorAPI` (e.g. with `hay_alerta_lluvia()` and `_resultado()`) actually correct?**
  _`ErrorAPI` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.07109106529209622 - nodes in this community are weakly interconnected._
- **Why does `get_settings()` connect `Community 11` to `Community 0`, `Community 2`, `Community 35`, `Community 5`, `Community 9`, `Community 10`, `Community 12`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Reporte` (e.g. with `CarrilAfectado` and `EstadoReporte`) actually correct?**
  _`Reporte` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.07293594964827842 - nodes in this community are weakly interconnected._
- **Why does `Usuario` connect `Community 6` to `Community 0`, `Community 1`, `Community 33`, `Community 5`, `Community 8`, `Community 9`, `Community 17`, `Community 20`, `Community 23`, `Community 29`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._