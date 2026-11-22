# Graph Report - calles-seguras-juarez  (2026-11-21)

## Corpus Check
- Corpus is ~34,444 words - fits in a single context window. You may not need a graph.

## Summary
- 718 nodes · 2247 edges · 19 communities (14 shown, 5 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 90 edges (avg confidence: 0.93)
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

## God Nodes (most connected - your core abstractions)
1. `Usuario` - 51 edges
2. `ErrorAPI` - 46 edges
3. `TipoDano` - 35 edges
4. `Reporte` - 35 edges
5. `ahora_utc()` - 32 edges
6. `SectorRef` - 27 edges
7. `EstadoReporte` - 26 edges
8. `get_settings()` - 24 edges
9. `expirar_vencidos()` - 24 edges
10. `ParametrosPagina` - 22 edges

## Surprising Connections (you probably didn't know these)
- `run_migrations_offline()` --calls--> `get_settings()`  [EXTRACTED]
  db/migrations/env.py → backend/app/core/config.py
- `run_migrations_online()` --calls--> `get_settings()`  [EXTRACTED]
  db/migrations/env.py → backend/app/core/config.py
- `sembrar_territorio()` --calls--> `Sector`  [INFERRED]
  db/seed.py → backend/app/models/territorio.py
- `sembrar_usuarios()` --calls--> `hashear_contrasena()`  [EXTRACTED]
  db/seed.py → backend/app/core/security.py
- `sembrar_reportes()` --references--> `Colonia`  [EXTRACTED]
  db/seed.py → backend/app/models/territorio.py

## Import Cycles
- None detected.

## Communities (19 total, 5 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (37): fuera_de_juarez(), Base, columna_fecha_creacion(), pg_enum(), CacheClima, ConfirmacionReporte, CarrilAfectado, EstadoReporte (+29 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (37): cercanos(), confirmar(), crear(), detalle(), eliminar(), historial(), listar(), mios() (+29 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (26): buscar(), CalleRiesgo, ClimaActual, ClimaHora, Pronostico, RiesgoInundacion, CuerpoError, DetalleError (+18 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (40): requiere_rol(), _dependencia(), ErrorAPI, RolUsuario, cambiar_estado(), cambiar_rol(), _colonia(), crear_colonia() (+32 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (27): get_settings(), Settings, a_local(), ahora_utc(), fecha_local(), hoy_local(), _armar(), _consultar_proveedor() (+19 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (35): ciudadano(), ciudadanos(), client(), coordinador(), crear_cuenta(), crear_reporte(), Cuenta, db() (+27 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (25): get_db(), usuario_actual(), _usuario_desde_token(), usuario_opcional(), crear_token(), decodificar_token(), hashear_contrasena(), verificar_contrasena() (+17 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (47): build, command, depends_on, environment, healthcheck, ports, restart, context (+39 more)

### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (20): cola(), detalle(), transicionar(), armar_pagina(), ParametrosPagina, HistorialModeracionItem, ReporteModeracion, ReporteModeracionItem (+12 more)

### Community 9 - "Community 9"
Cohesion: 0.10
Nodes (10): Usuario, run_migrations_offline(), run_migrations_online(), _ejecutar(), upgrade(), Generador, main(), sembrar_reportes() (+2 more)

### Community 10 - "Community 10"
Cohesion: 0.09
Nodes (13): _campo(), _cuerpo(), registrar_manejadores(), _error_api(), _http(), _inesperado(), _validacion(), _traducir_validacion() (+5 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (16): contrasena_valida(), caja_envolvente(), dentro_de_juarez(), haversine_m(), test_alcantarilla_siempre_alta(), test_bache_exige_campos_condicionales(), test_descripcion_maximo_500_y_campos_extra(), test_encharcamiento_activo_a_historico_no_es_manual() (+8 more)

### Community 12 - "Community 12"
Cohesion: 0.14
Nodes (15): colonia_catalogo(), colonias(), estados(), sectores(), tipos_dano(), CampoFormulario, CatalogoEstados, CatalogoTiposDano (+7 more)

### Community 13 - "Community 13"
Cohesion: 0.19
Nodes (13): longevidad(), moderacion(), resumen(), sectores(), IndicadoresLongevidad, IndicadoresModeracion, IndicadoresResumen, IndicadoresSectores (+5 more)

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ErrorAPI` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 4`, `Community 6`, `Community 8`, `Community 10`, `Community 11`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `ErrorAPI` (e.g. with `hay_alerta_lluvia()` and `_resultado()`) actually correct?**
  _`ErrorAPI` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.0761904761904762 - nodes in this community are weakly interconnected._
- **Why does `Usuario` connect `Community 9` to `Community 0`, `Community 1`, `Community 3`, `Community 6`, `Community 8`, `Community 13`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Reporte` (e.g. with `CarrilAfectado` and `EstadoReporte`) actually correct?**
  _`Reporte` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06442058496853018 - nodes in this community are weakly interconnected._
- **Why does `ahora_utc()` connect `Community 4` to `Community 0`, `Community 1`, `Community 5`, `Community 6`, `Community 8`, `Community 9`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._