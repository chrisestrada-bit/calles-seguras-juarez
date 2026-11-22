# Evidencia de auditoría de backend y reglas de negocio

- **Fecha:** 2026-11-22 (hora local Ciudad Juárez ≈ 13:38–13:45)
- **Objetivo auditado:** `https://calles-seguras-juarez-api.onrender.com/api/v1` (producción en Render)
- **Método:** scripts temporales de Python con `httpx` + lectura de código en `backend/app/` y `db/`. No se modificó código de aplicación.
- **Nota sobre `F-01` a `F-14`:** el «Documento 1 de Auditoría» no existe en el repositorio, por lo que esos IDs no se pudieron mapear uno a uno; la verificación se organizó por `RN-xx`, `HU-xx` y `RNF-xx`.

## 1. Tabla de verificación

| ID | Estado | Evidencia HTTP / Código |
|---|---|---|
| HU-01.1 login correcto | Cumple | `POST /auth/login` ciudadano/moderador/coordinador → 200 con JWT; expira en 1800 s (`security.py` `crear_token`, `iat`/`exp`). |
| HU-01.1 mensaje genérico | Cumple | Contraseña incorrecta y correo inexistente → mismo `401 CREDENCIALES_INVALIDAS` «Correo o contraseña incorrectos.» (A1, A2). `services/auth.py:43-44` y `:69-80` (hash de relleno iguala tiempos; cuenta inactiva también genérico). Bloqueo tras 5 intentos / 15 min (`auth.py:20-21`). |
| HU-01.2 política de contraseña | Cumple | `Ab1`, `abcdefghij`, `1234567890` → 422 «La contraseña debe tener al menos 8 caracteres e incluir letras y números.» (A3). `security.py` `contrasena_valida`. Argon2id (`PasswordHasher`). |
| HU-01.2 aceptación de privacidad | **No cumple** | `POST /auth/registro` sin ningún campo de privacidad → **201** (A4). Con `acepta_privacidad:false` → 422 «Campo no permitido.» (A5): el esquema `RegistroIn` (`schemas/auth.py:12-14`) ni lo define ni lo exige (`extra="forbid"`). La casilla sólo se valida en el cliente (`frontend/src/pages/RegisterPage.tsx:8`); cualquier cliente directo se salta el consentimiento. |
| HU-01.3 rol no elegible en registro | Cumple | `rol:"coordinador"` en registro → 422 «Campo no permitido.» (A6); `services/auth.py:32` fija `CIUDADANO`. |
| RBAC moderación (A01) | Cumple | Ciudadano `GET /moderacion/reportes` → 403 `ROL_NO_AUTORIZADO` (R1); `POST …/transiciones` → 403 (R5); visitante → 401 (R1b). `dependencies.py:81` (`MODERACION`). |
| RBAC administración (A01) | Cumple | Ciudadano `GET /admin/usuarios`, `POST /admin/sectores`, `POST /admin/colonias`, `PATCH /admin/usuarios/{id}/rol`, `PATCH /admin/colonias/1` → todos 403 (R2–R4b). Moderador `GET /admin/usuarios` → 403 (R4c). `routers/admin.py` usa `SOLO_COORDINADOR` en las 7 rutas. |
| Editar/borrar reporte ajeno | Cumple (con matiz) | No existe ruta de edición: `PATCH /reportes/{folio}` → **405** (R6). `DELETE /reportes/{folio}` → **405** para ciudadano, moderador **y visitante** (R7, R7b, R7c; `routers/reportes.py:207-219`). No se altera nada (R8: el reporte sigue igual). Matiz: el enunciado esperaba `403`; el servidor responde `405` porque la operación no existe para ningún rol. |
| Token inválido | Cumple | `GET /auth/yo` con token basura → 401 (R11). `dependencies.py:30-44` valida `sub`, usuario activo y `token_version`. |
| RN-04 privacidad | Cumple | Lista (100 filas) y detalle públicos sin `usuario_id`, `autor_id`, `correo`, `nombre`, hash ni token (búsqueda por regex, resultado vacío). Detalle de `BCH-2026-000172` sólo trae booleanos `es_mio`/`ya_confirmado_por_mi` con sesión (`schemas/reportes.py:131-132`). `GET /admin/usuarios` (sólo coordinador) expone `nombre`/`correo` — vista privada esperada. Moderación expone `autor_id` (UUID) sin nombre/correo (`services/moderacion.py:61`). El hash nunca está en un esquema de salida. |
| RN-01 territorio | Cumple | `32.5,-107.0` → **422 `FUERA_DE_JUAREZ`** «La ubicación está fuera de los límites de Ciudad Juárez, Chihuahua…» con rango del campo (T1). Borde `31.4499` → 422 (T1b). `services/geo.py:5-6`, `services/reportes.py:71`; CHECK también en BD. |
| HU-02.2 Bache | Cumple | Sin `tamano` / `profundidad` / `carril_afectado` → 422 «Este campo es obligatorio.» por campo (T2, T2b, T2c). `schemas/reportes.py` clase `BacheIn`. |
| HU-02.2 Alcantarilla | Cumple | Sin `esta_senalizado` → 422 (T3). Cliente que manda `severidad:"Baja"` → 422 «Campo no permitido.» (T6); alcantarilla válida → `severidad:"Alta"` (T7). `services/reportes.py:62-68`. |
| HU-03.1 Encharcamiento intransitable | Cumple | `nivel_agua:"intransitable"` sin `hay_riesgo_personas_vehiculos` → 422 «Indica si hay riesgo para personas o vehículos.» (T4). `schemas/reportes.py:65` (`_riesgo_si_intransitable`). |
| HU-02.2 descripción ≤ 500 | Cumple | 501 caracteres → 422 «Debe tener máximo 500 caracteres.» (T5); 500 caracteres → 201 (T7). `schemas/reportes.py:37`. |
| RN-03 folios | Cumple | `BCH-2026-000171…000183`, `ENC-2026-000056/57` generados por el servidor (T7, T8, E1). Secuencias PostgreSQL `nextval` (`services/folios.py:16-21`, nunca se reutilizan); trigger `fn_reportes_inmutables` impide cambiar folio (`migración 0001:217-231`). |
| RN-02 hora oficial | Cumple | Todas las fechas salen con offset `-07:00` (p. ej. `2026-11-22T13:39:14-07:00`); `core/tiempo.py` almacena UTC y presenta en `America/Ciudad_Juarez`. |
| HU-02.3 duplicado bache ≤ 30 m | Cumple | `GET /reportes/cercanos` a 20.0 m → `radio_metros:30` con candidato (D1). `POST` sin `forzar_nuevo` a 20 m → **409 `POSIBLE_DUPLICADO`** (D2). A ~40 m → 201 (D3). `services/reportes.py:90-110`, `geo.py:9`. |
| HU-03.1 duplicado encharcamiento ≤ 50 m | Cumple | A ~45 m → 409 (E2); a ~60 m → 201 (E3). `geo.py:10`. |
| Doble confirmación | Cumple | Mismo usuario confirma bache dos veces → 201 y luego **409 `CONFIRMACION_DUPLICADA`** (D4, D5); idem «Ya no hay agua» (E6, E7). `services/confirmaciones.py:80-90` + UNIQUE en BD. |
| Autoconfirmación | Cumple | Autor confirma su bache → 400 `AUTOCONFIRMACION_NO_PERMITIDA` (D5b); autor `sigue_ahi` y `ya_no_hay_agua` en su encharcamiento → 400 (E4, E5). `confirmaciones.py:53-58`; trigger `fn_confirmacion_valida`. |
| HU-03.3 3 «Ya no hay agua» → Histórico | Cumple | 3 usuarios distintos (b, c, moderador): estados `Activo`, `Activo`, **`Histórico`** (E6, E8, E9); historial con origen `sistema` (E10b). `confirmaciones.py:104-117` (`DESMENTIDOS_PARA_HISTORICO = 3`, el autor no cuenta, sólo ciclo vigente). |
| RN-06 vigencia 6 h | Cumple (por código) | No se esperó 6 h en vivo. Nace `Activo` con `vigente_hasta = created + 6 h` (`reportes.py:192-193`, `vigencia.py:12-13`); E6 devuelve `vigente_hasta` 6 h después de la creación. Cada «Sigue ahí» de otro usuario reinicia 6 h y abre ciclo nuevo (`confirmaciones.py:93-98`). Vencimiento materializado en cada consulta (`vigencia.py:20-45`) y cada 300 s (`main.py:21,37`); además la consulta de duplicados exige `vigente_hasta > now` (`reportes.py:102`). Históricos siguen en métricas (`indicadores/resumen`: `historicos:54`). |
| RN-05 matriz de transiciones | Cumple | `Recibido→Reparado` y `Recibido→En reparación` → 400 `TRANSICION_INVALIDA` (S0, S1); coordinador `Recibido→Validado` → 403 (S2); moderador `→Validado` 200 (S3); `Validado→Reparado` 400 (S4); coordinador `Validado→Programado` y `Programado→En reparación` 200 (S5, S6); `Reparado→Validado` 400 (S10); `Reparado→Rechazado` y `Histórico→Rechazado` 400 (limpieza). Tabla exacta en `services/transiciones.py:11-17`; respaldada por trigger `fn_reportes_transicion` (migración 0001:233-253). |
| RN-05 fecha de reparación | Cumple | Futura (2027-01-01) → 422 `FECHA_REPARACION_INVALIDA` (S7); anterior al reporte (2026-01-01) → 422 (S8); ausente → 422 (S8b); hoy → 200 (S9). `services/moderacion.py:187-204` (`inicio <= fecha <= hoy_local()`). |
| RN-07 trazabilidad / sin DELETE | Cumple | DELETE → 405 (R7*). Rechazar sin motivo → 422 «El motivo de rechazo es obligatorio (mínimo 10 caracteres).» (S13). Historial: triggers `trg_reportes_historial` (AFTER INSERT/UPDATE de estado), `trg_historial_append_only` (bloquea UPDATE/DELETE), `trg_reportes_sin_borrado` (migración 0001:256-262, 288-292, 330-336). Historial público de `BCH-2026-000172` muestra Recibido→Validado→Programado→En reparación→Reparado (S11). La inmutabilidad a nivel BD no se puede ejercitar por HTTP; se verificó por código. |
| RN-08 10 reportes/hora | Cumple | Cuenta nueva: reportes 1–10 → 201, el 11.º → **429 `LIMITE_REPORTES`** «Alcanzaste el máximo de 10 reportes por hora…» con `Retry-After` (L1–L11). `services/reportes.py:117-135` (candado asesor `pg_advisory_xact_lock`) y test `backend/tests/test_api.py:336`. |
| RN-09 visibilidad | Cumple | Bache `Recibido` público con `etiqueta_publica:"Sin validar"` (T8, D1). Reporte `Rechazado` → `GET /reportes/BCH-2026-000171` → **404**; `?estado=Rechazado` → 422 (`services/reportes.py`, `listar_publicos`). |
| RN-10 longevidad | Cumple | `longevidad_dias` en respuestas (`TransicionOut`, S3–S9); `created_at` inmutable por trigger `fn_reportes_inmutables`. `presentacion.longevidad_dias`. |
| RNF-06 `GET /reportes` < 3 s | Cumple | 0.12, 0.12, 0.14 s (página 5/por_pagina 20) y 0.13, 0.18, 0.61 s (`por_pagina=100`). |
| RNF-06 `GET /indicadores` < 3 s | Cumple (ruta distinta) | `GET /indicadores` → **404**; la ruta real es `/indicadores/resumen` → 0.12–0.13 s, `/indicadores/sectores` → 0.11–0.12 s. |
| Sec. 6.3 ≥ 20 colonias | Cumple | `GET /catalogos/colonias` → `total: 46`. |
| Sec. 6.3 ≥ 500 reportes | **No cumple** | `GET /reportes?por_pagina=1` → `paginacion.total: 225` (excluye Rechazado); `indicadores/resumen`: pavimento 170 + encharcamientos 55 = 225. `db/seed.py:143-144` fija `N_PAVIMENTO = 170`, `N_ENCHARCAMIENTOS = 55`. Faltan ≈ 275 (el total incluye 2 reportes de esta auditoría que no se pueden rechazar, ver §4). |
| HU-08.1 clima: respuesta y degradación | Parcial | `GET /clima/pronostico` → 200 en 0.27–0.35 s. **`desactualizado: true` y `obtenido_en: 2026-11-22T02:39:03-07:00`** (≈ 11 h de antigüedad) en W1/W2 y en la verificación posterior: producción sirve la caché vencida porque el proveedor falla desde Render (`services/clima.py:115-122`); `open-meteo` sí responde 200 desde otra red (0.43 s). La degradación elegante funciona (200 + bandera, 503 sólo sin caché), pero la integración con el proveedor está rota en producción. |
| HU-08.1 clima: caché de 1 h | **No cumple** | TTL por defecto **30 min** (`core/config.py:27`, `.env.example:47`); el requisito es 1 h (`WEATHER_CACHE_TTL_MINUTES=60`). El valor real de producción no es observable; con la caché vencida, además, cada petición reintenta al proveedor (timeout 5 s, `config.py:28`) sin retroceso. |
| RNF-05 / CORS / cabeceras | Cumple (código) | CORS sólo `settings.frontend_url` (`main.py:61-68`); `X-Content-Type-Options` y `Cache-Control: no-store` (`main.py:72-75`); docs/OpenAPI deshabilitados en producción (`main.py:52-54`). No se verificó con petición `Origin` externa. |

## 2. Fallos y brechas detectadas en el servidor

1. **Consentimiento de privacidad sin validación en backend (HU-01.2, LFPDPPP).** `POST /auth/registro` crea la cuenta sin ninguna prueba de aceptación; sólo la UI la exige. Falta un campo booleano `acepta_aviso_privacidad` (obligatorio y `true`) en `RegistroIn` y, idealmente, su fecha/versión persistida.
2. **Base de datos de producción con 225 reportes, no ≥ 500 (Sec. 6.3).** El seed (`db/seed.py:143-144`) genera 170 + 55.
3. **Clima en producción sirve datos de ~11 h con `desactualizado: true`.** La llamada a Open-Meteo falla desde Render (causa no determinada desde fuera: revisar `WEATHER_API_URL`, `WEATHER_TIMEOUT_SECONDS` y logs `calles_seguras.clima`). Lo que se ve al usuario: alerta de lluvia basada en datos viejos.
4. **TTL de caché de clima de 30 min en lugar de 1 h** (`core/config.py:27`, `.env.example:47`).
5. **Sin retroceso ante fallo del proveedor:** con la caché vencida cada petición vuelve a llamar al proveedor (hasta 5 s de espera) en vez de reutilizar la caché y reintentar tras un intervalo.
6. **`PATCH`/`DELETE` ajeno devuelven `405`, no `403`.** Funcionalmente seguro (no hay ruta de edición y DELETE se rechaza para todos, incluso el visitante), pero si el criterio de auditoría exige literalmente `403`, no se cumple; documentarlo como decisión (RN-07).
7. **`GET /api/v1/indicadores` no existe (404).** La ruta es `/indicadores/resumen`; alinear documentación o añadir alias.
8. **Datos de prueba residuales que no se pueden limpiar por diseño (RN-05/RN-07).** Ver §4.

## 3. Datos de prueba creados y limpieza

Usuarios (cuentas de prueba, **desactivadas** con `PATCH /admin/usuarios/{id}/estado`; no existe borrado de usuarios): `auditoria-0a8363-a@ejemplo.mx`, `auditoria-0a8363-b@ejemplo.mx`, `auditoria-0a8363-c@ejemplo.mx`. Login posterior → 401.

| Folio | Resultado de la limpieza |
|---|---|
| BCH-2026-000171, 000173, 000174–000183 | Rechazados (motivo «Prueba de auditoria backend (limpieza)»); ya no aparecen en consultas públicas (404). |
| ENC-2026-000057 | Rechazado. |
| **BCH-2026-000172** | **Queda en `Reparado`** (estado final, usado para probar el ciclo completo). No se puede rechazar ni eliminar. |
| **ENC-2026-000056** | **Queda en `Histórico`** (estado final tras 3 «Ya no hay agua»). No se puede rechazar ni eliminar. |

Ambos folios residuales usan calle «Calle Auditoria Prueba/Enc» (colonia Altavista) y cuentan en las métricas públicas. Marcar manualmente si se desea excluirlos de la demostración.

## 4. Resultados crudos

Tokens JWT redactados (`<JWT>`). Cuerpos truncados a 700 caracteres. Los pasos A1–R11 (autenticación y RBAC) se ejecutaron en una primera corrida; el log completo no se guardó en archivo, por lo que se transcribe abajo el resumen de la salida de consola (código HTTP y `codigo` de error exactos):

```
A1 login contraseña incorrecta                401 {"error":{"codigo":"CREDENCIALES_INVALIDAS","mensaje":"Correo o contraseña incorrectos."}}
A2 login correo inexistente                   401 {"error":{"codigo":"CREDENCIALES_INVALIDAS","mensaje":"Correo o contraseña incorrectos."}}
A3 registro contraseña "Ab1"                  422 {"campo":"contrasena","mensaje":"La contraseña debe tener al menos 8 caracteres e incluir letras y números."}
A3 registro "abcdefghij"                      422 (idem)
A3 registro "1234567890"                      422 (idem)
A4 registro válido sin campo de privacidad    201 {"id":"245c49ad-…","nombre":"Usuario Auditoria","rol":"ciudadano",…}
A5 registro con acepta_privacidad=false       422 {"campo":"acepta_privacidad","mensaje":"Campo no permitido."}
A6 registro con rol=coordinador               422 {"campo":"rol","mensaje":"Campo no permitido."}
R1  ciudadano GET /moderacion/reportes        403 ROL_NO_AUTORIZADO
R1b visitante GET /moderacion/reportes        401 NO_AUTENTICADO
R2  ciudadano GET /admin/usuarios             403 ROL_NO_AUTORIZADO
R3  ciudadano POST /admin/sectores            403 ROL_NO_AUTORIZADO
R3b ciudadano POST /admin/colonias            403 ROL_NO_AUTORIZADO
R4  ciudadano PATCH /admin/usuarios/{id}/rol  403 ROL_NO_AUTORIZADO
R4b ciudadano PATCH /admin/colonias/1         403 ROL_NO_AUTORIZADO
R4c moderador GET /admin/usuarios             403 ROL_NO_AUTORIZADO
R5  ciudadano POST /moderacion/reportes/ENC-2026-000018/transiciones 403 ROL_NO_AUTORIZADO
R5b ciudadano PATCH /moderacion/reportes/{f}  405 METODO_NO_PERMITIDO
R6  ciudadano PATCH /reportes/{f} ajeno       405 METODO_NO_PERMITIDO
R7  ciudadano DELETE /reportes/{f} ajeno      405 "Los reportes no se pueden eliminar…"
R7b moderador DELETE /reportes/{f}            405 (idem)
R7c visitante DELETE /reportes/{f}            405 (idem)
R8  GET /reportes/ENC-2026-000018 tras intentos 200 estado "Histórico" (sin cambios)
R11 token basura GET /auth/yo                 401 NO_AUTENTICADO
```

Segunda y tercera corrida (formularios, duplicados, estados, límite, rendimiento, clima):


### login moderador
`POST /auth/login` -> **200** (1.66s)
```
{"access_token": "<JWT>", "token_type": "bearer", "expira_en_segundos": 1800, "usuario": {"id": "2d6e2dca-a494-40f3-9024-2abf72cce96e", "nombre": "Moderación Uno", "rol": "moderador"}}
```

### login coordinador
`POST /auth/login` -> **200** (1.59s)
```
{"access_token": "<JWT>", "token_type": "bearer", "expira_en_segundos": 1800, "usuario": {"id": "12f0648f-71b5-45bb-a9dc-fb1aeb2ab238", "nombre": "Coordinación Calles Seguras", "rol": "coordinador"}}
```

### U0 coordinador lista usuarios auditoria
`GET /admin/usuarios?q=Auditoria&por_pagina=50` -> **200** (0.11s)
```
{"datos": [{"id": "314f8da2-9ec2-4007-ad76-64d6a2f504b7", "nombre": "Usuario Auditoria", "correo": "auditoria-0a8363-c@ejemplo.mx", "rol": "ciudadano", "activo": true, "created_at": "2026-11-22T13:38:26.413225-07:00"}, {"id": "0194a372-bdff-4886-b4a7-7e507debef3b", "nombre": "Usuario Auditoria", "correo": "auditoria-0a8363-b@ejemplo.mx", "rol": "ciudadano", "activo": true, "created_at": "2026-11-22T13:38:24.911376-07:00"}, {"id": "245c49ad-d9c4-4c6d-9105-647067ab6df2", "nombre": "Usuario Auditoria", "correo": "auditoria-0a8363-a@ejemplo.mx", "rol": "ciudadano", "activo": true, "created_at": "2026-11-22T13:38:23.350885-07:00"}], "paginacion": {"pagina": 1, "por_pagina": 50, "total": 3, "total
```

### login auditoria-0a8363-a
`POST /auth/login` -> **200** (1.49s)
```
{"access_token": "<JWT>", "token_type": "bearer", "expira_en_segundos": 1800, "usuario": {"id": "245c49ad-d9c4-4c6d-9105-647067ab6df2", "nombre": "Usuario Auditoria", "rol": "ciudadano"}}
```

### login auditoria-0a8363-b
`POST /auth/login` -> **200** (1.50s)
```
{"access_token": "<JWT>", "token_type": "bearer", "expira_en_segundos": 1800, "usuario": {"id": "0194a372-bdff-4886-b4a7-7e507debef3b", "nombre": "Usuario Auditoria", "rol": "ciudadano"}}
```

### login auditoria-0a8363-c
`POST /auth/login` -> **200** (1.40s)
```
{"access_token": "<JWT>", "token_type": "bearer", "expira_en_segundos": 1800, "usuario": {"id": "314f8da2-9ec2-4007-ad76-64d6a2f504b7", "nombre": "Usuario Auditoria", "rol": "ciudadano"}}
```

### C0 colonias
`GET /catalogos/colonias?por_pagina=100` -> **200** (0.11s)
```
{"datos": [{"id": 21, "nombre": "Altavista", "codigo_postal": null, "sector": {"id": 3, "nombre": "Centro"}, "centro": {"latitud": 31.722, "longitud": -106.49}}, {"id": 1, "nombre": "Anapra", "codigo_postal": "32100", "sector": {"id": 1, "nombre": "Norponiente"}, "centro": {"latitud": 31.7868, "longitud": -106.547}}, {"id": 6, "nombre": "Azteca", "codigo_postal": null, "sector": {"id": 1, "nombre": "Norponiente"}, "centro": {"latitud": 31.727, "longitud": -106.51}}, {"id": 20, "nombre": "Barrio Alto", "codigo_postal": null, "sector": {"id": 3, "nombre": "Centro"}, "centro": {"latitud": 31.745, "longitud": -106.493}}, {"id": 19, "nombre": "Bellavista", "codigo_postal": null, "sector": {"id": 
```

### T1 fuera de Juarez 32.5,-107.0
`POST /reportes` -> **422** (0.10s)
```
{"error": {"codigo": "FUERA_DE_JUAREZ", "mensaje": "La ubicación está fuera de los límites de Ciudad Juárez, Chihuahua. Selecciona un punto dentro del municipio.", "detalles": [{"campo": "latitud", "mensaje": "Debe estar entre 31.45 y 31.80."}, {"campo": "longitud", "mensaje": "Debe estar entre -106.65 y -106.25."}]}}
```

### T1b lat 31.4499
`POST /reportes` -> **422** (0.10s)
```
{"error": {"codigo": "FUERA_DE_JUAREZ", "mensaje": "La ubicación está fuera de los límites de Ciudad Juárez, Chihuahua. Selecciona un punto dentro del municipio.", "detalles": [{"campo": "latitud", "mensaje": "Debe estar entre 31.45 y 31.80."}]}}
```

### T2 bache sin tamano
`POST /reportes` -> **422** (0.10s)
```
{"error": {"codigo": "VALIDACION", "mensaje": "Revisa los datos marcados.", "detalles": [{"campo": "tamano", "mensaje": "Este campo es obligatorio."}]}}
```

### T2b bache sin profundidad
`POST /reportes` -> **422** (0.10s)
```
{"error": {"codigo": "VALIDACION", "mensaje": "Revisa los datos marcados.", "detalles": [{"campo": "profundidad", "mensaje": "Este campo es obligatorio."}]}}
```

### T2c bache sin carril
`POST /reportes` -> **422** (0.10s)
```
{"error": {"codigo": "VALIDACION", "mensaje": "Revisa los datos marcados.", "detalles": [{"campo": "carril_afectado", "mensaje": "Este campo es obligatorio."}]}}
```

### T3 alcantarilla sin esta_senalizado
`POST /reportes` -> **422** (0.11s)
```
{"error": {"codigo": "VALIDACION", "mensaje": "Revisa los datos marcados.", "detalles": [{"campo": "esta_senalizado", "mensaje": "Este campo es obligatorio."}]}}
```

### T4 enc intransitable sin riesgo
`POST /reportes` -> **422** (0.11s)
```
{"error": {"codigo": "VALIDACION", "mensaje": "Revisa los datos marcados.", "detalles": [{"campo": "hay_riesgo_personas_vehiculos", "mensaje": "Indica si hay riesgo para personas o vehículos."}]}}
```

### T5 descripcion 501 chars
`POST /reportes` -> **422** (0.10s)
```
{"error": {"codigo": "VALIDACION", "mensaje": "Revisa los datos marcados.", "detalles": [{"campo": "descripcion", "mensaje": "Debe tener máximo 500 caracteres."}]}}
```

### T6 alcantarilla con severidad=Baja del cliente
`POST /reportes` -> **422** (0.11s)
```
{"error": {"codigo": "VALIDACION", "mensaje": "Revisa los datos marcados.", "detalles": [{"campo": "severidad", "mensaje": "Campo no permitido."}]}}
```

### T7 alcantarilla valida, desc 500
`POST /reportes` -> **201** (0.22s)
```
{"folio": "BCH-2026-000171", "tipo_dano": "Alcantarilla sin tapa", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Alta", "ubicacion": {"latitud": 31.701, "longitud": -106.4}, "calle": "Calle Auditoria Prueba", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:14.385067-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### T8 bache valido
`POST /reportes` -> **201** (0.21s)
```
{"folio": "BCH-2026-000172", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.702, "longitud": -106.4}, "calle": "Calle Auditoria Prueba", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:14.601785-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "confirmaciones": 0, "fecha_programada": null, "fecha_reparacion": null, "es_mio": true, "ya_confirmado_por_mi": false}
```

### D1 cercanos ~20m del bache
`GET /reportes/cercanos?latitud=31.70218&longitud=-106.40&tipo_dano=Bache` -> **200** (0.17s)
```
{"radio_metros": 30, "candidatos": [{"folio": "BCH-2026-000172", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "calle": "Calle Auditoria Prueba", "distancia_metros": 20.0, "confirmaciones": 0, "ya_confirmado_por_mi": false, "es_mio": false, "created_at": "2026-11-22T13:39:14.601785-07:00"}]}
```

### D2 crear sin forzar a ~20m
`POST /reportes` -> **409** (0.17s)
```
{"error": {"codigo": "POSIBLE_DUPLICADO", "mensaje": "Ya existe un reporte abierto muy cerca de este punto. Confírmalo o indica que se trata de un daño distinto.", "detalles": [{"folio": "BCH-2026-000172", "tipo_dano": "Bache", "etiqueta_publica": "Sin validar", "distancia_metros": 20.0, "calle": "Calle Auditoria Prueba"}]}}
```

### D3 sin forzar a ~40m (debe crear)
`POST /reportes` -> **201** (0.17s)
```
{"folio": "BCH-2026-000173", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.7024, "longitud": -106.4}, "calle": "Calle Auditoria Prueba", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:15.161990-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "confirmaciones": 0, "fecha_programada": null, "fecha_reparacion": null, "es_mio": true, "ya_confirmado_por_mi": false}
```

### D4 confirmar bache usuario b
`POST /reportes/BCH-2026-000172/confirmaciones` -> **201** (0.12s)
```
{"folio": "BCH-2026-000172", "tipo": "confirmacion_dano", "estado_reporte": "Recibido", "vigencia": null, "mensaje": "Gracias. Tu confirmación quedó registrada."}
```

### D5 doble confirmar usuario b
`POST /reportes/BCH-2026-000172/confirmaciones` -> **409** (0.11s)
```
{"error": {"codigo": "CONFIRMACION_DUPLICADA", "mensaje": "Ya confirmaste este reporte.", "detalles": []}}
```

### D5b autoconfirmar bache (autor a)
`POST /reportes/BCH-2026-000172/confirmaciones` -> **400** (0.11s)
```
{"error": {"codigo": "AUTOCONFIRMACION_NO_PERMITIDA", "mensaje": "No puedes confirmar ni desmentir tu propio reporte.", "detalles": []}}
```

### E1 encharcamiento
`POST /reportes` -> **201** (0.15s)
```
{"folio": "ENC-2026-000056", "tipo_dano": "Encharcamiento", "estado": "Activo", "etiqueta_publica": "Activo", "severidad": "Baja", "ubicacion": {"latitud": 31.65, "longitud": -106.35}, "calle": "Calle Auditoria Enc", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:15.648928-07:00", "longevidad_dias": null, "vigencia": {"vigente_hasta": "2026-11-22T19:39:15.648928-07:00", "sigue_ahi": 0, "ya_no_hay_agua": 0}, "nivel_agua": "cubre un carril", "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"nivel_agua": "cubre un carril", "hay_riesgo_personas_vehiculos": null}, "confirmaciones": 0, "fecha_programada": null, "fecha_repa
```

### E2 dup enc a ~45m (<=50)
`POST /reportes` -> **409** (0.14s)
```
{"error": {"codigo": "POSIBLE_DUPLICADO", "mensaje": "Ya existe un reporte abierto muy cerca de este punto. Confírmalo o indica que se trata de un daño distinto.", "detalles": [{"folio": "ENC-2026-000056", "tipo_dano": "Encharcamiento", "etiqueta_publica": "Activo", "distancia_metros": 44.5, "calle": "Calle Auditoria Enc"}]}}
```

### E3 dup enc a ~60m (>50) debe crear
`POST /reportes` -> **201** (0.14s)
```
{"folio": "ENC-2026-000057", "tipo_dano": "Encharcamiento", "estado": "Activo", "etiqueta_publica": "Activo", "severidad": "Baja", "ubicacion": {"latitud": 31.65054, "longitud": -106.35}, "calle": "Calle Auditoria Prueba", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:15.937299-07:00", "longevidad_dias": null, "vigencia": {"vigente_hasta": "2026-11-22T19:39:15.937299-07:00", "sigue_ahi": 0, "ya_no_hay_agua": 0}, "nivel_agua": "cubre un carril", "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"nivel_agua": "cubre un carril", "hay_riesgo_personas_vehiculos": null}, "confirmaciones": 0, "fecha_programada": null, "fech
```

### E4 autor sigue_ahi
`POST /reportes/ENC-2026-000056/confirmaciones` -> **400** (0.12s)
```
{"error": {"codigo": "AUTOCONFIRMACION_NO_PERMITIDA", "mensaje": "No puedes confirmar ni desmentir tu propio reporte.", "detalles": []}}
```

### E5 autor ya_no_hay_agua
`POST /reportes/ENC-2026-000056/confirmaciones` -> **400** (0.10s)
```
{"error": {"codigo": "AUTOCONFIRMACION_NO_PERMITIDA", "mensaje": "No puedes confirmar ni desmentir tu propio reporte.", "detalles": []}}
```

### E5b enc + confirmacion_dano
`POST /reportes/ENC-2026-000056/confirmaciones` -> **400** (0.11s)
```
{"error": {"codigo": "CONFIRMACION_NO_APLICA", "mensaje": "Este tipo de confirmación no corresponde al tipo de daño del reporte.", "detalles": []}}
```

### E6 ya_no_hay_agua b
`POST /reportes/ENC-2026-000056/confirmaciones` -> **201** (0.12s)
```
{"folio": "ENC-2026-000056", "tipo": "ya_no_hay_agua", "estado_reporte": "Activo", "vigencia": {"vigente_hasta": "2026-11-22T19:39:15.648928-07:00", "sigue_ahi": 0, "ya_no_hay_agua": 1}, "mensaje": "Gracias. Registramos que ya no hay agua."}
```

### E7 ya_no_hay_agua b otra vez
`POST /reportes/ENC-2026-000056/confirmaciones` -> **409** (0.11s)
```
{"error": {"codigo": "CONFIRMACION_DUPLICADA", "mensaje": "Ya confirmaste este reporte.", "detalles": []}}
```

### E8 ya_no_hay_agua c
`POST /reportes/ENC-2026-000056/confirmaciones` -> **201** (0.13s)
```
{"folio": "ENC-2026-000056", "tipo": "ya_no_hay_agua", "estado_reporte": "Activo", "vigencia": {"vigente_hasta": "2026-11-22T19:39:15.648928-07:00", "sigue_ahi": 0, "ya_no_hay_agua": 2}, "mensaje": "Gracias. Registramos que ya no hay agua."}
```

### E9 ya_no_hay_agua moderador (3o distinto)
`POST /reportes/ENC-2026-000056/confirmaciones` -> **201** (0.13s)
```
{"folio": "ENC-2026-000056", "tipo": "ya_no_hay_agua", "estado_reporte": "Histórico", "vigencia": {"vigente_hasta": "2026-11-22T19:39:15.648928-07:00", "sigue_ahi": 0, "ya_no_hay_agua": 3}, "mensaje": "Gracias. Con tu confirmación, el encharcamiento pasó a histórico."}
```

### E10 estado enc tras 3
`GET /reportes/ENC-2026-000056` -> **200** (0.11s)
```
{"folio": "ENC-2026-000056", "tipo_dano": "Encharcamiento", "estado": "Histórico", "etiqueta_publica": "Histórico", "severidad": "Baja", "ubicacion": {"latitud": 31.65, "longitud": -106.35}, "calle": "Calle Auditoria Enc", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:15.648928-07:00", "longevidad_dias": null, "vigencia": {"vigente_hasta": "2026-11-22T19:39:15.648928-07:00", "sigue_ahi": 0, "ya_no_hay_agua": 3}, "nivel_agua": "cubre un carril", "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"nivel_agua": "cubre un carril", "hay_riesgo_personas_vehiculos": null}, "confirmaciones": 0, "fecha_programada": null, "fech
```

### E10b historial enc
`GET /reportes/ENC-2026-000056/historial` -> **200** (0.13s)
```
{"folio": "ENC-2026-000056", "historial": [{"estado_anterior": null, "estado_nuevo": "Activo", "origen": "ciudadano", "fecha": "2026-11-22T13:39:15.648928-07:00"}, {"estado_anterior": "Activo", "estado_nuevo": "Histórico", "origen": "sistema", "fecha": "2026-11-22T13:39:16.739357-07:00"}]}
```

### S0 Recibido->Reparado
`POST /moderacion/reportes/BCH-2026-000172/transiciones` -> **400** (0.12s)
```
{"error": {"codigo": "TRANSICION_INVALIDA", "mensaje": "No es posible cambiar el estado de \"Recibido\" a \"Reparado\".", "detalles": []}}
```

### S1 Recibido->En reparacion
`POST /moderacion/reportes/BCH-2026-000172/transiciones` -> **400** (0.12s)
```
{"error": {"codigo": "TRANSICION_INVALIDA", "mensaje": "No es posible cambiar el estado de \"Recibido\" a \"En reparación\".", "detalles": []}}
```

### S2 coordinador Recibido->Validado
`POST /moderacion/reportes/BCH-2026-000172/transiciones` -> **403** (0.12s)
```
{"error": {"codigo": "ROL_NO_AUTORIZADO", "mensaje": "Tu rol no tiene permiso para realizar esta acción.", "detalles": []}}
```

### S3 moderador Recibido->Validado
`POST /moderacion/reportes/BCH-2026-000172/transiciones` -> **200** (0.13s)
```
{"folio": "BCH-2026-000172", "estado_anterior": "Recibido", "estado": "Validado", "fecha_reparacion": null, "longevidad_dias": 0, "registrado_en": "2026-11-22T13:39:17.492130-07:00", "mensaje": "El reporte BCH-2026-000172 cambió a \"Validado\"."}
```

### S4 Validado->Reparado
`POST /moderacion/reportes/BCH-2026-000172/transiciones` -> **400** (0.12s)
```
{"error": {"codigo": "TRANSICION_INVALIDA", "mensaje": "No es posible cambiar el estado de \"Validado\" a \"Reparado\".", "detalles": []}}
```

### S5 coord Validado->Programado
`POST /moderacion/reportes/BCH-2026-000172/transiciones` -> **200** (0.13s)
```
{"folio": "BCH-2026-000172", "estado_anterior": "Validado", "estado": "Programado", "fecha_reparacion": null, "longevidad_dias": 0, "registrado_en": "2026-11-22T13:39:17.739890-07:00", "mensaje": "El reporte BCH-2026-000172 cambió a \"Programado\"."}
```

### S6 coord Programado->En reparacion
`POST /moderacion/reportes/BCH-2026-000172/transiciones` -> **200** (0.13s)
```
{"folio": "BCH-2026-000172", "estado_anterior": "Programado", "estado": "En reparación", "fecha_reparacion": null, "longevidad_dias": 0, "registrado_en": "2026-11-22T13:39:17.869004-07:00", "mensaje": "El reporte BCH-2026-000172 cambió a \"En reparación\"."}
```

### S7 Reparado fecha futura
`POST /moderacion/reportes/BCH-2026-000172/transiciones` -> **422** (0.12s)
```
{"error": {"codigo": "FECHA_REPARACION_INVALIDA", "mensaje": "La fecha de reparación debe ser igual o posterior a la fecha del reporte y no puede ser futura.", "detalles": [{"campo": "fecha_reparacion", "mensaje": "La fecha 2027-01-01 debe estar entre 2026-11-22 y 2026-11-22."}]}}
```

### S8 Reparado fecha anterior al reporte
`POST /moderacion/reportes/BCH-2026-000172/transiciones` -> **422** (0.11s)
```
{"error": {"codigo": "FECHA_REPARACION_INVALIDA", "mensaje": "La fecha de reparación debe ser igual o posterior a la fecha del reporte y no puede ser futura.", "detalles": [{"campo": "fecha_reparacion", "mensaje": "La fecha 2026-01-01 debe estar entre 2026-11-22 y 2026-11-22."}]}}
```

### S8b Reparado sin fecha
`POST /moderacion/reportes/BCH-2026-000172/transiciones` -> **422** (0.12s)
```
{"error": {"codigo": "VALIDACION", "mensaje": "Revisa los datos marcados.", "detalles": [{"campo": "fecha_reparacion", "mensaje": "La fecha de reparación es obligatoria."}]}}
```

### S9 Reparado valido (hoy)
`POST /moderacion/reportes/BCH-2026-000172/transiciones` -> **200** (0.13s)
```
{"folio": "BCH-2026-000172", "estado_anterior": "En reparación", "estado": "Reparado", "fecha_reparacion": "2026-11-22", "longevidad_dias": 0, "registrado_en": "2026-11-22T13:39:18.351456-07:00", "mensaje": "El reporte BCH-2026-000172 cambió a \"Reparado\"."}
```

### S10 Reparado->Validado (final)
`POST /moderacion/reportes/BCH-2026-000172/transiciones` -> **400** (0.12s)
```
{"error": {"codigo": "TRANSICION_INVALIDA", "mensaje": "No es posible cambiar el estado de \"Reparado\" a \"Validado\".", "detalles": []}}
```

### S11 historial publico bache
`GET /reportes/BCH-2026-000172/historial` -> **200** (0.12s)
```
{"folio": "BCH-2026-000172", "historial": [{"estado_anterior": null, "estado_nuevo": "Recibido", "origen": "ciudadano", "fecha": "2026-11-22T13:39:14.601785-07:00"}, {"estado_anterior": "Recibido", "estado_nuevo": "Validado", "origen": "moderacion", "fecha": "2026-11-22T13:39:17.492130-07:00"}, {"estado_anterior": "Validado", "estado_nuevo": "Programado", "origen": "moderacion", "fecha": "2026-11-22T13:39:17.739890-07:00"}, {"estado_anterior": "Programado", "estado_nuevo": "En reparación", "origen": "moderacion", "fecha": "2026-11-22T13:39:17.869004-07:00"}, {"estado_anterior": "En reparación", "estado_nuevo": "Reparado", "origen": "moderacion", "fecha": "2026-11-22T13:39:18.351456-07:00"}]}
```

### S12 moderacion detalle bache
`GET /moderacion/reportes/BCH-2026-000172` -> **200** (0.12s)
```
{"folio": "BCH-2026-000172", "tipo_dano": "Bache", "estado": "Reparado", "severidad": "Baja", "calle": "Calle Auditoria Prueba", "colonia": {"id": 21, "nombre": "Altavista"}, "sector": {"id": 3, "nombre": "Centro"}, "confirmaciones": 1, "forzado_como_nuevo": true, "autor_id": "245c49ad-d9c4-4c6d-9105-647067ab6df2", "reportes_autor_ultimas_24h": 3, "created_at": "2026-11-22T13:39:14.601785-07:00", "transiciones_disponibles": [], "ubicacion": {"latitud": 31.702, "longitud": -106.4}, "referencia": null, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "motivo_rechazo": null, "fecha_programada": "2026-12-01", "fecha_reparac
```

### S13 Rechazar sin motivo
`POST /moderacion/reportes/BCH-2026-000171/transiciones` -> **422** (0.10s)
```
{"error": {"codigo": "VALIDACION", "mensaje": "Revisa los datos marcados.", "detalles": [{"campo": null, "mensaje": "El motivo de rechazo es obligatorio (mínimo 10 caracteres)."}]}}
```

### L1 rate-limit usuario c
`POST /reportes` -> **201** (0.14s)
```
{"folio": "BCH-2026-000174", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.6, "longitud": -106.3}, "calle": "Calle Limite 0", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:18.938147-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "confirmaciones": 0, "fecha_programada": null, "fecha_reparacion": null, "es_mio": true, "ya_confirmado_por_mi": false}
```

### L2 rate-limit usuario c
`POST /reportes` -> **201** (0.14s)
```
{"folio": "BCH-2026-000175", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.601, "longitud": -106.3}, "calle": "Calle Limite 1", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:19.083274-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "confirmaciones": 0, "fecha_programada": null, "fecha_reparacion": null, "es_mio": true, "ya_confirmado_por_mi": false}
```

### L3 rate-limit usuario c
`POST /reportes` -> **201** (0.15s)
```
{"folio": "BCH-2026-000176", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.602, "longitud": -106.3}, "calle": "Calle Limite 2", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:19.229823-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "confirmaciones": 0, "fecha_programada": null, "fecha_reparacion": null, "es_mio": true, "ya_confirmado_por_mi": false}
```

### L4 rate-limit usuario c
`POST /reportes` -> **201** (0.16s)
```
{"folio": "BCH-2026-000177", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.603, "longitud": -106.3}, "calle": "Calle Limite 3", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:19.380673-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "confirmaciones": 0, "fecha_programada": null, "fecha_reparacion": null, "es_mio": true, "ya_confirmado_por_mi": false}
```

### L5 rate-limit usuario c
`POST /reportes` -> **201** (0.14s)
```
{"folio": "BCH-2026-000178", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.604, "longitud": -106.3}, "calle": "Calle Limite 4", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:19.532814-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "confirmaciones": 0, "fecha_programada": null, "fecha_reparacion": null, "es_mio": true, "ya_confirmado_por_mi": false}
```

### L6 rate-limit usuario c
`POST /reportes` -> **201** (0.15s)
```
{"folio": "BCH-2026-000179", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.605, "longitud": -106.3}, "calle": "Calle Limite 5", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:19.676549-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "confirmaciones": 0, "fecha_programada": null, "fecha_reparacion": null, "es_mio": true, "ya_confirmado_por_mi": false}
```

### L7 rate-limit usuario c
`POST /reportes` -> **201** (0.16s)
```
{"folio": "BCH-2026-000180", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.606, "longitud": -106.3}, "calle": "Calle Limite 6", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:19.832646-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "confirmaciones": 0, "fecha_programada": null, "fecha_reparacion": null, "es_mio": true, "ya_confirmado_por_mi": false}
```

### L8 rate-limit usuario c
`POST /reportes` -> **201** (0.14s)
```
{"folio": "BCH-2026-000181", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.607, "longitud": -106.3}, "calle": "Calle Limite 7", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:19.979242-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "confirmaciones": 0, "fecha_programada": null, "fecha_reparacion": null, "es_mio": true, "ya_confirmado_por_mi": false}
```

### L9 rate-limit usuario c
`POST /reportes` -> **201** (0.15s)
```
{"folio": "BCH-2026-000182", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.608, "longitud": -106.3}, "calle": "Calle Limite 8", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.123657-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "confirmaciones": 0, "fecha_programada": null, "fecha_reparacion": null, "es_mio": true, "ya_confirmado_por_mi": false}
```

### L10 rate-limit usuario c
`POST /reportes` -> **201** (0.15s)
```
{"folio": "BCH-2026-000183", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.609, "longitud": -106.3}, "calle": "Calle Limite 9", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.279491-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null, "referencia": null, "sector": {"id": 3, "nombre": "Centro"}, "descripcion": null, "detalle": {"tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "carril derecho"}, "confirmaciones": 0, "fecha_programada": null, "fecha_reparacion": null, "es_mio": true, "ya_confirmado_por_mi": false}
```

### L11 rate-limit usuario c
`POST /reportes` -> **429** (0.13s)
```
{"error": {"codigo": "LIMITE_REPORTES", "mensaje": "Alcanzaste el máximo de 10 reportes por hora. Intenta de nuevo más tarde.", "detalles": []}}
```

### P0 perf
`GET /reportes` -> **200** (0.12s)
```
{"datos": [{"folio": "BCH-2026-000183", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.609, "longitud": -106.3}, "calle": "Calle Limite 9", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.279491-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null}, {"folio": "BCH-2026-000182", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.608, "longitud": -106.3}, "calle": "Calle Limite 8", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.123657-07:00", "longevidad_dias
```

### P1 perf
`GET /reportes` -> **200** (0.12s)
```
{"datos": [{"folio": "BCH-2026-000183", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.609, "longitud": -106.3}, "calle": "Calle Limite 9", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.279491-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null}, {"folio": "BCH-2026-000182", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.608, "longitud": -106.3}, "calle": "Calle Limite 8", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.123657-07:00", "longevidad_dias
```

### P2 perf
`GET /reportes` -> **200** (0.14s)
```
{"datos": [{"folio": "BCH-2026-000183", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.609, "longitud": -106.3}, "calle": "Calle Limite 9", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.279491-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null}, {"folio": "BCH-2026-000182", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.608, "longitud": -106.3}, "calle": "Calle Limite 8", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.123657-07:00", "longevidad_dias
```

### P0 perf
`GET /reportes?por_pagina=100` -> **200** (0.13s)
```
{"datos": [{"folio": "BCH-2026-000183", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.609, "longitud": -106.3}, "calle": "Calle Limite 9", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.279491-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null}, {"folio": "BCH-2026-000182", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.608, "longitud": -106.3}, "calle": "Calle Limite 8", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.123657-07:00", "longevidad_dias
```

### P1 perf
`GET /reportes?por_pagina=100` -> **200** (0.18s)
```
{"datos": [{"folio": "BCH-2026-000183", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.609, "longitud": -106.3}, "calle": "Calle Limite 9", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.279491-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null}, {"folio": "BCH-2026-000182", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.608, "longitud": -106.3}, "calle": "Calle Limite 8", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.123657-07:00", "longevidad_dias
```

### P2 perf
`GET /reportes?por_pagina=100` -> **200** (0.61s)
```
{"datos": [{"folio": "BCH-2026-000183", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.609, "longitud": -106.3}, "calle": "Calle Limite 9", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.279491-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null}, {"folio": "BCH-2026-000182", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.608, "longitud": -106.3}, "calle": "Calle Limite 8", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.123657-07:00", "longevidad_dias
```

### P0 perf
`GET /indicadores/resumen` -> **200** (0.13s)
```
{"periodo": {"desde": null, "hasta": null, "zona_horaria": "America/Ciudad_Juarez"}, "pavimento": {"total": 170, "por_estado": {"Recibido": 37, "Validado": 26, "Programado": 21, "En reparación": 12, "Reparado": 74}, "por_tipo": {"Bache": 146, "Alcantarilla sin tapa": 24}, "longevidad_promedio_abiertos_dias": 90.3, "tiempo_promedio_reparacion_dias": 20.9}, "encharcamientos": {"total": 55, "activos": 1, "historicos": 54, "intransitables": 7}, "actualizado_en": "2026-11-22T13:39:21.863378-07:00"}
```

### P1 perf
`GET /indicadores/resumen` -> **200** (0.12s)
```
{"periodo": {"desde": null, "hasta": null, "zona_horaria": "America/Ciudad_Juarez"}, "pavimento": {"total": 170, "por_estado": {"Recibido": 37, "Validado": 26, "Programado": 21, "En reparación": 12, "Reparado": 74}, "por_tipo": {"Bache": 146, "Alcantarilla sin tapa": 24}, "longevidad_promedio_abiertos_dias": 90.3, "tiempo_promedio_reparacion_dias": 20.9}, "encharcamientos": {"total": 55, "activos": 1, "historicos": 54, "intransitables": 7}, "actualizado_en": "2026-11-22T13:39:21.984575-07:00"}
```

### P2 perf
`GET /indicadores/resumen` -> **200** (0.12s)
```
{"periodo": {"desde": null, "hasta": null, "zona_horaria": "America/Ciudad_Juarez"}, "pavimento": {"total": 170, "por_estado": {"Recibido": 37, "Validado": 26, "Programado": 21, "En reparación": 12, "Reparado": 74}, "por_tipo": {"Bache": 146, "Alcantarilla sin tapa": 24}, "longevidad_promedio_abiertos_dias": 90.3, "tiempo_promedio_reparacion_dias": 20.9}, "encharcamientos": {"total": 55, "activos": 1, "historicos": 54, "intransitables": 7}, "actualizado_en": "2026-11-22T13:39:22.101391-07:00"}
```

### P0 perf
`GET /indicadores/sectores` -> **200** (0.12s)
```
{"datos": [{"sector": {"id": 3, "nombre": "Centro"}, "baches_abiertos": 26, "reparados": 16, "longevidad_promedio_abiertos_dias": 64.6, "encharcamientos_total": 16, "encharcamientos_activos": 1}, {"sector": {"id": 4, "nombre": "Poniente"}, "baches_abiertos": 19, "reparados": 11, "longevidad_promedio_abiertos_dias": 104.1, "encharcamientos_total": 8, "encharcamientos_activos": 0}, {"sector": {"id": 2, "nombre": "Nororiente"}, "baches_abiertos": 12, "reparados": 3, "longevidad_promedio_abiertos_dias": 88.8, "encharcamientos_total": 7, "encharcamientos_activos": 0}, {"sector": {"id": 1, "nombre": "Norponiente"}, "baches_abiertos": 10, "reparados": 9, "longevidad_promedio_abiertos_dias": 81.1, "
```

### P1 perf
`GET /indicadores/sectores` -> **200** (0.11s)
```
{"datos": [{"sector": {"id": 3, "nombre": "Centro"}, "baches_abiertos": 26, "reparados": 16, "longevidad_promedio_abiertos_dias": 64.6, "encharcamientos_total": 16, "encharcamientos_activos": 1}, {"sector": {"id": 4, "nombre": "Poniente"}, "baches_abiertos": 19, "reparados": 11, "longevidad_promedio_abiertos_dias": 104.1, "encharcamientos_total": 8, "encharcamientos_activos": 0}, {"sector": {"id": 2, "nombre": "Nororiente"}, "baches_abiertos": 12, "reparados": 3, "longevidad_promedio_abiertos_dias": 88.8, "encharcamientos_total": 7, "encharcamientos_activos": 0}, {"sector": {"id": 1, "nombre": "Norponiente"}, "baches_abiertos": 10, "reparados": 9, "longevidad_promedio_abiertos_dias": 81.1, "
```

### P2 perf
`GET /indicadores/sectores` -> **200** (0.12s)
```
{"datos": [{"sector": {"id": 3, "nombre": "Centro"}, "baches_abiertos": 26, "reparados": 16, "longevidad_promedio_abiertos_dias": 64.6, "encharcamientos_total": 16, "encharcamientos_activos": 1}, {"sector": {"id": 4, "nombre": "Poniente"}, "baches_abiertos": 19, "reparados": 11, "longevidad_promedio_abiertos_dias": 104.1, "encharcamientos_total": 8, "encharcamientos_activos": 0}, {"sector": {"id": 2, "nombre": "Nororiente"}, "baches_abiertos": 12, "reparados": 3, "longevidad_promedio_abiertos_dias": 88.8, "encharcamientos_total": 7, "encharcamientos_activos": 0}, {"sector": {"id": 1, "nombre": "Norponiente"}, "baches_abiertos": 10, "reparados": 9, "longevidad_promedio_abiertos_dias": 81.1, "
```

### P0 perf
`GET /clima/pronostico` -> **200** (0.35s)
```
{"ubicacion": "Ciudad Juárez, Chihuahua", "actual": {"temperatura_c": 6.3, "precipitacion_mm": 0.0, "descripcion": "Cielo despejado"}, "proximas_horas": [{"hora": "2026-11-22T13:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T14:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T15:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T16:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T17:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T18:00:00-07:00", "probabilidad_lluvia_pct": 1
```

### P1 perf
`GET /clima/pronostico` -> **200** (0.28s)
```
{"ubicacion": "Ciudad Juárez, Chihuahua", "actual": {"temperatura_c": 6.3, "precipitacion_mm": 0.0, "descripcion": "Cielo despejado"}, "proximas_horas": [{"hora": "2026-11-22T13:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T14:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T15:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T16:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T17:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T18:00:00-07:00", "probabilidad_lluvia_pct": 1
```

### P2 perf
`GET /clima/pronostico` -> **200** (0.30s)
```
{"ubicacion": "Ciudad Juárez, Chihuahua", "actual": {"temperatura_c": 6.3, "precipitacion_mm": 0.0, "descripcion": "Cielo despejado"}, "proximas_horas": [{"hora": "2026-11-22T13:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T14:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T15:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T16:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T17:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T18:00:00-07:00", "probabilidad_lluvia_pct": 1
```

### P0 perf
`GET /clima/riesgo-inundacion` -> **200** (0.36s)
```
{"alerta_lluvia": false, "datos": [{"calle": "Calle Auditoria Prueba", "colonia": {"id": 21, "nombre": "Altavista"}, "sector": {"id": 3, "nombre": "Centro"}, "nivel_riesgo": "Medio", "encharcamientos_activos": 1, "nivel_agua_maximo_activo": "cubre un carril", "encharcamientos_historicos_12_meses": 0, "ultimo_reporte": "2026-11-22T13:39:15.937299-07:00", "folios_activos": ["ENC-2026-000057"], "recomendacion": "Circula con precaución: la calle ha presentado encharcamientos."}, {"calle": "Av. Ejército Nacional", "colonia": {"id": 15, "nombre": "Pronaf"}, "sector": {"id": 3, "nombre": "Centro"}, "nivel_riesgo": "Medio", "encharcamientos_activos": 0, "nivel_agua_maximo_activo": null, "encharcamie
```

### P1 perf
`GET /clima/riesgo-inundacion` -> **200** (0.42s)
```
{"alerta_lluvia": false, "datos": [{"calle": "Calle Auditoria Prueba", "colonia": {"id": 21, "nombre": "Altavista"}, "sector": {"id": 3, "nombre": "Centro"}, "nivel_riesgo": "Medio", "encharcamientos_activos": 1, "nivel_agua_maximo_activo": "cubre un carril", "encharcamientos_historicos_12_meses": 0, "ultimo_reporte": "2026-11-22T13:39:15.937299-07:00", "folios_activos": ["ENC-2026-000057"], "recomendacion": "Circula con precaución: la calle ha presentado encharcamientos."}, {"calle": "Av. Ejército Nacional", "colonia": {"id": 15, "nombre": "Pronaf"}, "sector": {"id": 3, "nombre": "Centro"}, "nivel_riesgo": "Medio", "encharcamientos_activos": 0, "nivel_agua_maximo_activo": null, "encharcamie
```

### P2 perf
`GET /clima/riesgo-inundacion` -> **200** (0.39s)
```
{"alerta_lluvia": false, "datos": [{"calle": "Calle Auditoria Prueba", "colonia": {"id": 21, "nombre": "Altavista"}, "sector": {"id": 3, "nombre": "Centro"}, "nivel_riesgo": "Medio", "encharcamientos_activos": 1, "nivel_agua_maximo_activo": "cubre un carril", "encharcamientos_historicos_12_meses": 0, "ultimo_reporte": "2026-11-22T13:39:15.937299-07:00", "folios_activos": ["ENC-2026-000057"], "recomendacion": "Circula con precaución: la calle ha presentado encharcamientos."}, {"calle": "Av. Ejército Nacional", "colonia": {"id": 15, "nombre": "Pronaf"}, "sector": {"id": 3, "nombre": "Centro"}, "nivel_riesgo": "Medio", "encharcamientos_activos": 0, "nivel_agua_maximo_activo": null, "encharcamie
```

### P9 total reportes
`GET /reportes?por_pagina=1` -> **200** (0.14s)
```
{"datos": [{"folio": "BCH-2026-000183", "tipo_dano": "Bache", "estado": "Recibido", "etiqueta_publica": "Sin validar", "severidad": "Baja", "ubicacion": {"latitud": 31.609, "longitud": -106.3}, "calle": "Calle Limite 9", "colonia": {"id": 21, "nombre": "Altavista"}, "created_at": "2026-11-22T13:39:20.279491-07:00", "longevidad_dias": 0, "vigencia": null, "nivel_agua": null}], "paginacion": {"pagina": 1, "por_pagina": 1, "total": 225, "total_paginas": 225}}
```

### P9b colonias
`GET /catalogos/colonias?por_pagina=100` -> **200** (0.10s)
```
{"datos": [{"id": 21, "nombre": "Altavista", "codigo_postal": null, "sector": {"id": 3, "nombre": "Centro"}, "centro": {"latitud": 31.722, "longitud": -106.49}}, {"id": 1, "nombre": "Anapra", "codigo_postal": "32100", "sector": {"id": 1, "nombre": "Norponiente"}, "centro": {"latitud": 31.7868, "longitud": -106.547}}, {"id": 6, "nombre": "Azteca", "codigo_postal": null, "sector": {"id": 1, "nombre": "Norponiente"}, "centro": {"latitud": 31.727, "longitud": -106.51}}, {"id": 20, "nombre": "Barrio Alto", "codigo_postal": null, "sector": {"id": 3, "nombre": "Centro"}, "centro": {"latitud": 31.745, "longitud": -106.493}}, {"id": 19, "nombre": "Bellavista", "codigo_postal": null, "sector": {"id": 
```

### P9c indicadores
`GET /indicadores/resumen` -> **200** (0.12s)
```
{"periodo": {"desde": null, "hasta": null, "zona_horaria": "America/Ciudad_Juarez"}, "pavimento": {"total": 170, "por_estado": {"Recibido": 37, "Validado": 26, "Programado": 21, "En reparación": 12, "Reparado": 74}, "por_tipo": {"Bache": 146, "Alcantarilla sin tapa": 24}, "longevidad_promedio_abiertos_dias": 90.3, "tiempo_promedio_reparacion_dias": 20.9}, "encharcamientos": {"total": 55, "activos": 1, "historicos": 54, "intransitables": 7}, "actualizado_en": "2026-11-22T13:39:24.897090-07:00"}
```

### W1 clima
`GET /clima/pronostico` -> **200** (0.27s)
```
{"ubicacion": "Ciudad Juárez, Chihuahua", "actual": {"temperatura_c": 6.3, "precipitacion_mm": 0.0, "descripcion": "Cielo despejado"}, "proximas_horas": [{"hora": "2026-11-22T13:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T14:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T15:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T16:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T17:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T18:00:00-07:00", "probabilidad_lluvia_pct": 1
```

### W2 clima
`GET /clima/pronostico` -> **200** (0.27s)
```
{"ubicacion": "Ciudad Juárez, Chihuahua", "actual": {"temperatura_c": 6.3, "precipitacion_mm": 0.0, "descripcion": "Cielo despejado"}, "proximas_horas": [{"hora": "2026-11-22T13:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T14:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T15:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T16:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T17:00:00-07:00", "probabilidad_lluvia_pct": 0.0, "precipitacion_mm": 0.0}, {"hora": "2026-11-22T18:00:00-07:00", "probabilidad_lluvia_pct": 1
```

### Verificaciones adicionales (tercera corrida)
```
`GET /reportes?por_pagina=1` -> paginacion.total = 225
`GET /catalogos/colonias?por_pagina=100` -> total = 46
`GET /indicadores` -> 404 ; `GET /indicadores/resumen` -> pavimento.total 170, encharcamientos.total 55 (activos 1, historicos 54)
`GET /clima/pronostico` -> obtenido_en 2026-11-22T02:39:03-07:00, desactualizado true
Rechazo de reportes de prueba -> 200 (excepto BCH-2026-000172 Reparado y ENC-2026-000056 Historico -> 400 TRANSICION_INVALIDA)
Desactivacion de 3 cuentas de prueba -> 200 ; login posterior -> 401 CREDENCIALES_INVALIDAS
GET /reportes/BCH-2026-000171 (Rechazado) -> 404
GET /admin/usuarios (coordinador) -> claves: id, nombre, correo, rol, activo, created_at
```
