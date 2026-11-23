# Contrato de API REST — Calles Seguras Juárez (AEB-1055)

> Versión `v1`. Prefijo base: `/api/v1`.
> Modelo de datos y reglas: [`docs/arquitectura.md`](./arquitectura.md). Reglas normativas: [`CLAUDE.md`](../CLAUDE.md).

---

## 1. Convenciones generales

### 1.1 Formato

- `Content-Type: application/json; charset=utf-8` en peticiones y respuestas.
- Nombres de campos en `snake_case` y en español; valores de enumeraciones **idénticos** a los de `CLAUDE.md` (p. ej. `"En reparación"`, `"a media llanta"`).
- **Fechas y horas (RN-02):** se reciben y devuelven en ISO 8601 **con desplazamiento** de `America/Ciudad_Juarez` (`-07:00` en horario de invierno, `-06:00` en verano). Internamente se almacenan en UTC. Las fechas sin hora (`fecha_reparacion`, `fecha_programada`) son fechas locales `YYYY-MM-DD`.
- Identificador público de reportes: `folio` (`BCH-YYYY-NNNNNN` / `ENC-YYYY-NNNNNN`). El `id` interno nunca se expone.
- Todos los esquemas de petición rechazan campos desconocidos (`extra="forbid"` → `422`).

### 1.2 Autenticación

- Encabezado `Authorization: Bearer <access_token>`.
- JWT firmado con `JWT_ALGORITHM` (HS256) y `JWT_SECRET_KEY`. Claims: `sub` (UUID del usuario), `rol`, `ver` (`token_version`), `iat`, `exp`.
- **Expiración por inactividad: 30 minutos** (`ACCESS_TOKEN_EXPIRE_MINUTES`). El frontend llama a `POST /auth/renovar` mientras haya actividad; si pasan 30 min sin renovar, el token expira y se responde `401`.
- "Rol mínimo" = roles permitidos. `visitante` significa *sin token requerido*. Los roles no son estrictamente jerárquicos (ver matriz en `arquitectura.md` §8).

### 1.3 Paginación

Parámetros `pagina` (≥ 1, default `1`) y `por_pagina` (1–100, default `20`). Envoltura:

```json
{
  "datos": [],
  "paginacion": { "pagina": 1, "por_pagina": 20, "total": 0, "total_paginas": 0 }
}
```

### 1.4 Formato de error

Todas las respuestas de error usan la misma envoltura, con mensajes en español de México:

```json
{
  "error": {
    "codigo": "VALIDACION",
    "mensaje": "Revisa los datos marcados.",
    "detalles": [
      { "campo": "nivel_agua", "mensaje": "Selecciona el nivel del agua." }
    ]
  }
}
```

### 1.5 Códigos de estado

| Código | Uso | `codigo` de error típico |
|--------|-----|--------------------------|
| `200` | Consulta o actualización exitosa | — |
| `201` | Recurso creado (encabezado `Location`) | — |
| `204` | Éxito sin cuerpo | — |
| `400` | Regla de negocio violada con datos bien formados | `TRANSICION_INVALIDA`, `AUTOCONFIRMACION_NO_PERMITIDA`, `REPORTE_NO_CONFIRMABLE`, `CONFIRMACION_NO_APLICA` |
| `401` | Sin token, token inválido/expirado/revocado o credenciales incorrectas | `NO_AUTENTICADO`, `CREDENCIALES_INVALIDAS` |
| `403` | Token válido pero el rol no tiene permiso | `ROL_NO_AUTORIZADO` |
| `404` | Recurso inexistente **o** no visible para el solicitante (p. ej. folio `Rechazado` en vista pública) | `NO_ENCONTRADO` |
| `405` | Método no permitido (p. ej. `DELETE` sobre reportes, RN-07) | `METODO_NO_PERMITIDO` |
| `409` | Conflicto: duplicado cercano, confirmación repetida, correo ya registrado | `POSIBLE_DUPLICADO`, `CONFIRMACION_DUPLICADA`, `CORREO_REGISTRADO` |
| `422` | Validación de esquema o de campos (RN-01, HU-02.2, HU-03.1, longitud, fechas) | `VALIDACION`, `FUERA_DE_JUAREZ`, `FECHA_REPARACION_INVALIDA` |
| `429` | Límite excedido (RN-08, bloqueo de inicio de sesión o búsquedas de geocodificación); incluye `Retry-After` | `LIMITE_REPORTES`, `DEMASIADOS_INTENTOS`, `LIMITE_BUSQUEDAS` |
| `503` | Proveedor de clima no disponible y sin caché | `CLIMA_NO_DISPONIBLE` |

### 1.6 Mensajes estándar de reglas de negocio

| `codigo` | `mensaje` |
|----------|-----------|
| `FUERA_DE_JUAREZ` | `La ubicación está fuera de los límites de Ciudad Juárez, Chihuahua. Selecciona un punto dentro del municipio.` |
| `LIMITE_REPORTES` | `Alcanzaste el máximo de 10 reportes por hora. Intenta de nuevo más tarde.` |
| `TRANSICION_INVALIDA` | `No es posible cambiar el estado de "{estado_actual}" a "{estado_nuevo}".` |
| `ROL_NO_AUTORIZADO` | `Tu rol no tiene permiso para realizar esta acción.` |
| `AUTOCONFIRMACION_NO_PERMITIDA` | `No puedes confirmar ni desmentir tu propio reporte.` |
| `POSIBLE_DUPLICADO` | `Ya existe un reporte abierto muy cerca de este punto. Confírmalo o indica que se trata de un daño distinto.` |
| `FECHA_REPARACION_INVALIDA` | `La fecha de reparación debe ser igual o posterior a la fecha del reporte y no puede ser futura.` |

---

## 2. Esquemas compartidos

### 2.1 `ReportePublico` (RN-04, RN-09, RN-10)

```json
{
  "folio": "BCH-2026-000418",
  "tipo_dano": "Bache",
  "estado": "Recibido",
  "etiqueta_publica": "Sin validar",
  "severidad": "Alta",
  "ubicacion": { "latitud": 31.690412, "longitud": -106.424873 },
  "calle": "Av. Tecnológico",
  "referencia": "Frente a la estación de bomberos, carril con dirección al sur",
  "colonia": { "id": 112, "nombre": "Partido Romero" },
  "sector": { "id": 3, "nombre": "Centro" },
  "descripcion": "Bache profundo que obliga a frenar de golpe.",
  "detalle": {
    "tamano": "grande",
    "profundidad": "más de 10 cm",
    "carril_afectado": "carril derecho"
  },
  "confirmaciones": 4,
  "created_at": "2026-11-18T07:42:10-07:00",
  "fecha_programada": null,
  "fecha_reparacion": null,
  "longevidad_dias": 3,
  "vigencia": null
}
```

- `etiqueta_publica`: `"Sin validar"` si `estado = "Recibido"`; en otro caso igual a `estado`.
- `detalle` varía por `tipo_dano`:
  - `Bache`: `tamano`, `profundidad`, `carril_afectado`.
  - `Alcantarilla sin tapa`: `esta_senalizado`.
  - `Encharcamiento`: `nivel_agua`, `hay_riesgo_personas_vehiculos` (`null` si no es `intransitable`).
- `vigencia` (sólo `Encharcamiento`, si no, `null`):

```json
{ "vigente_hasta": "2026-11-21T15:20:00-07:00", "sigue_ahi": 2, "ya_no_hay_agua": 1 }
```

  `ya_no_hay_agua` cuenta sólo la vigencia actual.
- `longevidad_dias`: `null` para encharcamientos.
- **No contiene** `usuario_id`, `autor_id`, `nombre`, `correo`, `motivo_rechazo` ni el `id` interno.

### 2.2 `ReporteResumenPublico` (listas y mapa)

Subconjunto de `ReportePublico`: `folio`, `tipo_dano`, `estado`, `etiqueta_publica`, `severidad`, `ubicacion`, `calle`, `colonia`, `created_at`, `longevidad_dias`, `vigencia`.

### 2.3 `HistorialPublico`

```json
{ "estado_anterior": "Validado", "estado_nuevo": "Programado", "origen": "moderacion", "fecha": "2026-11-19T10:05:00-07:00" }
```

Sin `usuario_id` ni `motivo`.

---

## 3. Dominio `auth`

### 3.1 `POST /api/v1/auth/registro`

| Rol | Descripción |
|-----|-------------|
| `visitante` | Crea una cuenta con rol `ciudadano` (el cliente **no** puede elegir rol). |

**Petición**

```json
{ "nombre": "María Fernanda López", "correo": "maria.lopez@ejemplo.mx", "contrasena": "Lluvia2026", "acepta_aviso_privacidad": true }
```

Validaciones: `nombre` 2–120; `correo` válido; `contrasena` 8–128 caracteres con al menos una letra y un número; `acepta_aviso_privacidad` **obligatorio y `true`** (HU-01.2, LFPDPPP). Si falta o es `false` → `422` («Debes aceptar el aviso de privacidad para crear tu cuenta.»). El servidor guarda la fecha de aceptación (`usuarios.aviso_privacidad_aceptado_at`, UTC). El aviso se publica en `/aviso-de-privacidad` del frontend.

**Códigos:** `201`, `409 CORREO_REGISTRADO`, `422`.

**`201`**

```json
{ "id": "6f1c2a9e-3b7d-4e55-9a10-2c8f0d4b7e21", "nombre": "María Fernanda López", "rol": "ciudadano", "created_at": "2026-11-21T09:12:44-07:00" }
```

**`422`**

```json
{
  "error": {
    "codigo": "VALIDACION",
    "mensaje": "Revisa los datos marcados.",
    "detalles": [{ "campo": "contrasena", "mensaje": "La contraseña debe tener al menos 8 caracteres e incluir letras y números." }]
  }
}
```

### 3.2 `POST /api/v1/auth/login`

| Rol | Descripción |
|-----|-------------|
| `visitante` | Inicia sesión y obtiene un JWT. |

**Petición**

```json
{ "correo": "maria.lopez@ejemplo.mx", "contrasena": "Lluvia2026" }
```

**Códigos:** `200`, `401 CREDENCIALES_INVALIDAS` (mensaje genérico, sin revelar si el correo existe), `422`, `429 DEMASIADOS_INTENTOS` (5 fallos en 15 min).

**`200`**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.<carga>.<firma>",
  "token_type": "bearer",
  "expira_en_segundos": 1800,
  "usuario": { "id": "6f1c2a9e-3b7d-4e55-9a10-2c8f0d4b7e21", "nombre": "María Fernanda López", "rol": "ciudadano" }
}
```

**`401`**

```json
{ "error": { "codigo": "CREDENCIALES_INVALIDAS", "mensaje": "Correo o contraseña incorrectos.", "detalles": [] } }
```

### 3.3 `POST /api/v1/auth/renovar`

| Rol | Descripción |
|-----|-------------|
| `ciudadano`, `moderador`, `coordinador` | Emite un nuevo token con 30 min de vigencia a partir de ahora (sesión deslizante). Requiere token aún vigente. |

**Petición:** sin cuerpo. **Códigos:** `200`, `401`.
**`200`:** igual que `login`.

### 3.4 `POST /api/v1/auth/cerrar-sesion`

| Rol | Descripción |
|-----|-------------|
| `ciudadano`, `moderador`, `coordinador` | Incrementa `token_version`, invalidando todos los tokens emitidos. |

**Códigos:** `204`, `401`.

### 3.5 `GET /api/v1/auth/yo`

| Rol | Descripción |
|-----|-------------|
| `ciudadano`, `moderador`, `coordinador` | Datos de la propia cuenta (vista privada). |

**Códigos:** `200`, `401`.

```json
{ "id": "6f1c2a9e-3b7d-4e55-9a10-2c8f0d4b7e21", "nombre": "María Fernanda López", "correo": "maria.lopez@ejemplo.mx", "rol": "ciudadano", "reportes_ultima_hora": 2, "limite_reportes_hora": 10 }
```

---

## 4. Dominio `reportes`

### 4.1 `GET /api/v1/reportes`

| Rol | Descripción |
|-----|-------------|
| `visitante` | Lista pública para mapa y tabla. **Nunca** incluye `Rechazado` (RN-09). |

**Query**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `tipo_dano` | enum, repetible | `Bache`, `Alcantarilla sin tapa`, `Encharcamiento` |
| `estado` | enum, repetible | Cualquiera excepto `Rechazado` (si se envía → `422`) |
| `solo_vigentes` | bool | Encharcamientos con `estado = "Activo"` y `vigente_hasta > ahora` |
| `colonia_id` / `sector_id` | int | Filtro territorial |
| `calle` | string (≥ 3) | Búsqueda aproximada por calle |
| `bbox` | string | `lon_min,lat_min,lon_max,lat_max` (recortado a los límites de RN-01) |
| `desde` / `hasta` | fecha `YYYY-MM-DD` | Rango local de `created_at` |
| `orden` | enum | `recientes` (default), `longevidad`, `severidad` |
| `pagina`, `por_pagina` | int | Paginación |

**Códigos:** `200`, `422`.

**`200`**

```json
{
  "datos": [
    {
      "folio": "ENC-2026-000097",
      "tipo_dano": "Encharcamiento",
      "estado": "Activo",
      "etiqueta_publica": "Activo",
      "severidad": "Alta",
      "ubicacion": { "latitud": 31.718230, "longitud": -106.452910 },
      "calle": "Av. de las Torres",
      "colonia": { "id": 57, "nombre": "Infonavit Casas Grandes" },
      "created_at": "2026-11-21T08:55:00-07:00",
      "longevidad_dias": null,
      "vigencia": { "vigente_hasta": "2026-11-21T15:20:00-07:00", "sigue_ahi": 2, "ya_no_hay_agua": 0 }
    },
    {
      "folio": "BCH-2026-000418",
      "tipo_dano": "Bache",
      "estado": "Recibido",
      "etiqueta_publica": "Sin validar",
      "severidad": "Alta",
      "ubicacion": { "latitud": 31.690412, "longitud": -106.424873 },
      "calle": "Av. Tecnológico",
      "colonia": { "id": 112, "nombre": "Partido Romero" },
      "created_at": "2026-11-18T07:42:10-07:00",
      "longevidad_dias": 3,
      "vigencia": null
    }
  ],
  "paginacion": { "pagina": 1, "por_pagina": 20, "total": 2, "total_paginas": 1 }
}
```

### 4.2 `GET /api/v1/reportes/cercanos` (HU-02.3, HU-03.1)

| Rol | Descripción |
|-----|-------------|
| `ciudadano`, `moderador`, `coordinador` | Verificación previa de duplicados antes de mostrar el formulario completo. |

**Query:** `latitud` (req.), `longitud` (req.), `tipo_dano` (req.).
Radio aplicado por el servidor: **30 m** para `Bache` / `Alcantarilla sin tapa` (abiertos), **50 m** para `Encharcamiento` (vigentes). El cliente no puede cambiar el radio.

**Códigos:** `200`, `401`, `422` (incluye `FUERA_DE_JUAREZ`).

**`200`**

```json
{
  "radio_metros": 30,
  "candidatos": [
    {
      "folio": "BCH-2026-000418",
      "tipo_dano": "Bache",
      "estado": "Recibido",
      "etiqueta_publica": "Sin validar",
      "severidad": "Alta",
      "calle": "Av. Tecnológico",
      "distancia_metros": 12.4,
      "confirmaciones": 4,
      "ya_confirmado_por_mi": false,
      "es_mio": false,
      "created_at": "2026-11-18T07:42:10-07:00"
    }
  ]
}
```

### 4.3 `POST /api/v1/reportes` (HU-02.2, HU-02.3, HU-03.1)

| Rol | Descripción |
|-----|-------------|
| `ciudadano`, `moderador`, `coordinador` | Crea un reporte. Folio, estado, severidad y fechas los asigna el servidor. |

**Petición — `Bache`**

```json
{
  "tipo_dano": "Bache",
  "latitud": 31.690412,
  "longitud": -106.424873,
  "colonia_id": 112,
  "calle": "Av. Tecnológico",
  "referencia": "Frente a la estación de bomberos",
  "descripcion": "Bache profundo que obliga a frenar de golpe.",
  "tamano": "grande",
  "profundidad": "más de 10 cm",
  "carril_afectado": "carril derecho",
  "forzar_nuevo": false
}
```

**Petición — `Alcantarilla sin tapa`**

```json
{
  "tipo_dano": "Alcantarilla sin tapa",
  "latitud": 31.737650,
  "longitud": -106.487120,
  "colonia_id": 8,
  "calle": "Calle Mariscal",
  "descripcion": "Registro abierto junto a la banqueta.",
  "esta_senalizado": false,
  "forzar_nuevo": false
}
```

**Petición — `Encharcamiento`**

```json
{
  "tipo_dano": "Encharcamiento",
  "latitud": 31.718230,
  "longitud": -106.452910,
  "colonia_id": 57,
  "calle": "Av. de las Torres",
  "referencia": "Bajo puente de Av. de las Torres y Tecnológico",
  "nivel_agua": "intransitable",
  "hay_riesgo_personas_vehiculos": true,
  "forzar_nuevo": false
}
```

**Reglas de validación**

| Regla | Código si falla |
|-------|-----------------|
| `latitud` 31.45–31.80 y `longitud` -106.65 – -106.25 (RN-01) | `422 FUERA_DE_JUAREZ` |
| Campos obligatorios/prohibidos por `tipo_dano` (`arquitectura.md` §5.1) | `422 VALIDACION` |
| `hay_riesgo_personas_vehiculos` obligatorio sólo si `nivel_agua = "intransitable"` | `422 VALIDACION` |
| `descripcion` ≤ 500 caracteres | `422 VALIDACION` |
| `colonia_id` existente y activa | `422 VALIDACION` |
| Enviar `folio`, `estado`, `severidad`, `created_at` u otros campos no definidos | `422 VALIDACION` |
| Más de 10 reportes en la última hora por cuenta (RN-08) | `429 LIMITE_REPORTES` + `Retry-After` |
| Reporte abierto/vigente a ≤ 30 m / ≤ 50 m y `forzar_nuevo = false` | `409 POSIBLE_DUPLICADO` |

**Códigos:** `201`, `401`, `409`, `422`, `429`. (No hay `403`: todos los roles autenticados pueden reportar; una cuenta desactivada tiene su token revocado y recibe `401`.)

**`201`** (encabezado `Location: /api/v1/reportes/BCH-2026-000419`) — cuerpo `ReportePublico` + `es_mio`:

```json
{
  "folio": "BCH-2026-000419",
  "tipo_dano": "Alcantarilla sin tapa",
  "estado": "Recibido",
  "etiqueta_publica": "Sin validar",
  "severidad": "Alta",
  "ubicacion": { "latitud": 31.737650, "longitud": -106.487120 },
  "calle": "Calle Mariscal",
  "referencia": null,
  "colonia": { "id": 8, "nombre": "Centro" },
  "sector": { "id": 3, "nombre": "Centro" },
  "descripcion": "Registro abierto junto a la banqueta.",
  "detalle": { "esta_senalizado": false },
  "confirmaciones": 0,
  "created_at": "2026-11-21T09:30:02-07:00",
  "fecha_programada": null,
  "fecha_reparacion": null,
  "longevidad_dias": 0,
  "vigencia": null,
  "es_mio": true
}
```

**`409`**

```json
{
  "error": {
    "codigo": "POSIBLE_DUPLICADO",
    "mensaje": "Ya existe un reporte abierto muy cerca de este punto. Confírmalo o indica que se trata de un daño distinto.",
    "detalles": [
      { "folio": "BCH-2026-000418", "tipo_dano": "Bache", "etiqueta_publica": "Sin validar", "distancia_metros": 12.4, "calle": "Av. Tecnológico" }
    ]
  }
}
```

**`422`**

```json
{
  "error": {
    "codigo": "FUERA_DE_JUAREZ",
    "mensaje": "La ubicación está fuera de los límites de Ciudad Juárez, Chihuahua. Selecciona un punto dentro del municipio.",
    "detalles": [{ "campo": "latitud", "mensaje": "Debe estar entre 31.45 y 31.80." }]
  }
}
```

**`429`** (encabezado `Retry-After: 1260`)

```json
{ "error": { "codigo": "LIMITE_REPORTES", "mensaje": "Alcanzaste el máximo de 10 reportes por hora. Intenta de nuevo más tarde.", "detalles": [] } }
```

### 4.4 `GET /api/v1/reportes/mios`

| Rol | Descripción |
|-----|-------------|
| `ciudadano`, `moderador`, `coordinador` | Reportes creados por el usuario autenticado, **incluidos** los `Rechazado` con su motivo (es su propio dato). |

**Query:** `estado`, `tipo_dano`, `pagina`, `por_pagina`. **Códigos:** `200`, `401`, `422`.

```json
{
  "datos": [
    {
      "folio": "BCH-2026-000377",
      "tipo_dano": "Bache",
      "estado": "Rechazado",
      "etiqueta_publica": null,
      "severidad": "Baja",
      "calle": "Calle Ignacio Mejía",
      "colonia": { "id": 8, "nombre": "Centro" },
      "created_at": "2026-11-10T18:03:51-07:00",
      "motivo_rechazo": "La ubicación corresponde a una obra en proceso ya señalizada por el municipio.",
      "longevidad_dias": null,
      "es_mio": true
    }
  ],
  "paginacion": { "pagina": 1, "por_pagina": 20, "total": 1, "total_paginas": 1 }
}
```

### 4.5 `GET /api/v1/reportes/{folio}`

| Rol | Descripción |
|-----|-------------|
| `visitante` | Detalle público. Si el folio está `Rechazado` o no existe → `404` (no revela existencia). |

**Ruta:** `folio` con patrón `^(BCH|ENC)-[0-9]{4}-[0-9]{6}$` (si no cumple → `422`).
**Códigos:** `200`, `404`, `422`.
**`200`:** `ReportePublico` (§2.1). Si hay token válido, se agregan `es_mio` y `ya_confirmado_por_mi`.

Ejemplo `Reparado`:

```json
{
  "folio": "BCH-2026-000201",
  "tipo_dano": "Bache",
  "estado": "Reparado",
  "etiqueta_publica": "Reparado",
  "severidad": "Media",
  "ubicacion": { "latitud": 31.653110, "longitud": -106.392400 },
  "calle": "Blvd. Independencia",
  "referencia": "Cruce con Calle Valle del Sol",
  "colonia": { "id": 203, "nombre": "Parajes del Sur" },
  "sector": { "id": 5, "nombre": "Suroriente" },
  "descripcion": "Bache mediano en carril de alta velocidad.",
  "detalle": { "tamano": "mediano", "profundidad": "5 a 10 cm", "carril_afectado": "carril izquierdo" },
  "confirmaciones": 9,
  "created_at": "2026-09-14T21:10:00-06:00",
  "fecha_programada": "2026-10-20",
  "fecha_reparacion": "2026-10-23",
  "longevidad_dias": 39,
  "vigencia": null
}
```

### 4.6 `GET /api/v1/reportes/{folio}/historial`

| Rol | Descripción |
|-----|-------------|
| `visitante` | Línea de tiempo pública del reporte. `404` si `Rechazado`. |

**Códigos:** `200`, `404`, `422`.

```json
{
  "folio": "BCH-2026-000201",
  "historial": [
    { "estado_anterior": null, "estado_nuevo": "Recibido", "origen": "ciudadano", "fecha": "2026-09-14T21:10:00-06:00" },
    { "estado_anterior": "Recibido", "estado_nuevo": "Validado", "origen": "moderacion", "fecha": "2026-09-15T09:02:13-06:00" },
    { "estado_anterior": "Validado", "estado_nuevo": "Programado", "origen": "moderacion", "fecha": "2026-10-02T11:40:00-06:00" },
    { "estado_anterior": "Programado", "estado_nuevo": "En reparación", "origen": "moderacion", "fecha": "2026-10-22T08:15:00-06:00" },
    { "estado_anterior": "En reparación", "estado_nuevo": "Reparado", "origen": "moderacion", "fecha": "2026-10-23T16:47:30-06:00" }
  ]
}
```

### 4.7 `POST /api/v1/reportes/{folio}/confirmaciones` (HU-02.3, HU-03.2, HU-03.3)

| Rol | Descripción |
|-----|-------------|
| `ciudadano`, `moderador`, `coordinador` | Confirma un bache existente o indica "Sigue ahí" / "Ya no hay agua" en un encharcamiento. |

**Petición**

```json
{ "tipo": "sigue_ahi" }
```

| `tipo` | Aplica a | Efecto |
|--------|----------|--------|
| `confirmacion_dano` | `Bache`, `Alcantarilla sin tapa` abiertos | +1 confirmación (una por usuario). |
| `sigue_ahi` | `Encharcamiento` `Activo` | Reinicia la vigencia: `vigente_hasta = ahora + 6 h`; inicia nueva vigencia (los "Ya no hay agua" previos dejan de contar). |
| `ya_no_hay_agua` | `Encharcamiento` `Activo` | Al llegar a 3 usuarios distintos en la vigencia actual → `Histórico`. |

**Códigos**

| Código | Caso |
|--------|------|
| `201` | Confirmación registrada |
| `400 AUTOCONFIRMACION_NO_PERMITIDA` | El usuario es el autor del reporte |
| `400 CONFIRMACION_NO_APLICA` | `tipo` no corresponde al `tipo_dano` |
| `400 REPORTE_NO_CONFIRMABLE` | Reporte en estado final (`Reparado`, `Histórico`) o encharcamiento vencido |
| `401` | Sin token |
| `404` | Folio inexistente o `Rechazado` |
| `409 CONFIRMACION_DUPLICADA` | Ya confirmó este reporte (o esta vigencia) |
| `422` | Cuerpo inválido |

**`201` — "Ya no hay agua" que cierra el encharcamiento**

```json
{
  "folio": "ENC-2026-000097",
  "tipo": "ya_no_hay_agua",
  "estado_reporte": "Histórico",
  "vigencia": { "vigente_hasta": "2026-11-21T15:20:00-07:00", "sigue_ahi": 2, "ya_no_hay_agua": 3 },
  "mensaje": "Gracias. Con tu confirmación, el encharcamiento pasó a histórico."
}
```

**`201` — "Sigue ahí"**

```json
{
  "folio": "ENC-2026-000097",
  "tipo": "sigue_ahi",
  "estado_reporte": "Activo",
  "vigencia": { "vigente_hasta": "2026-11-21T16:05:12-07:00", "sigue_ahi": 3, "ya_no_hay_agua": 0 },
  "mensaje": "Gracias. La vigencia del encharcamiento se extendió 6 horas."
}
```

**`400`**

```json
{ "error": { "codigo": "AUTOCONFIRMACION_NO_PERMITIDA", "mensaje": "No puedes confirmar ni desmentir tu propio reporte.", "detalles": [] } }
```

### 4.8 `PATCH /api/v1/reportes/{folio}` (HU-02.5)

| Rol | Descripción |
|-----|-------------|
| Autor (`ciudadano`, `moderador`, `coordinador`) | Corrige su propio reporte **mientras está en `Recibido`**. |

Campos opcionales (al menos uno): `colonia_id`, `calle` (3–150), `referencia` (≤ 200, `""` → `null`), `descripcion` (≤ 500, `""` → `null`); sólo `Bache`: `tamano`, `profundidad`, `carril_afectado`; sólo `Alcantarilla sin tapa`: `esta_senalizado`. Folio, tipo, ubicación, autor y fecha original son **inmutables** (RN-03, RN-10): enviarlos → `422` (campo no permitido). La severidad se recalcula en el servidor. La edición no cambia el estado, por lo que no genera historial.

**Códigos:** `200` (`ReportePublico`), `401`, `403 SIN_PERMISO` (no es el autor), `404`, `409 REPORTE_NO_EDITABLE` (ya no está en `Recibido`; los encharcamientos nacen `Activo` y no son editables), `422`.

### 4.9 `DELETE /api/v1/reportes/{folio}`

**No existe.** Responde `405 METODO_NO_PERMITIDO` (encabezado `Allow: GET, PATCH`) para todos los roles (RN-07). Un reporte improcedente se lleva a `Rechazado` desde moderación.

---

## 5. Dominio `moderacion`

### 5.1 `GET /api/v1/moderacion/reportes`

| Rol | Descripción |
|-----|-------------|
| `moderador`, `coordinador` | Cola de trabajo. Incluye **todos** los estados, también `Rechazado`. |

**Query:** `estado` (repetible, default `Recibido`), `tipo_dano`, `sector_id`, `colonia_id`, `severidad`, `desde`, `hasta`, `autor_id` (UUID), `orden` (`antiguos` default, `recientes`, `severidad`, `confirmaciones`), `pagina`, `por_pagina`.
**Códigos:** `200`, `401`, `403`, `422`.

```json
{
  "datos": [
    {
      "folio": "BCH-2026-000418",
      "tipo_dano": "Bache",
      "estado": "Recibido",
      "severidad": "Alta",
      "calle": "Av. Tecnológico",
      "colonia": { "id": 112, "nombre": "Partido Romero" },
      "sector": { "id": 3, "nombre": "Centro" },
      "confirmaciones": 4,
      "forzado_como_nuevo": false,
      "autor_id": "6f1c2a9e-3b7d-4e55-9a10-2c8f0d4b7e21",
      "reportes_autor_ultimas_24h": 2,
      "created_at": "2026-11-18T07:42:10-07:00",
      "transiciones_disponibles": ["Validado", "Rechazado"]
    }
  ],
  "paginacion": { "pagina": 1, "por_pagina": 20, "total": 1, "total_paginas": 1 }
}
```

`transiciones_disponibles` se calcula según el estado actual **y** el rol del solicitante (un `coordinador` vería `[]` para un `Recibido`).

### 5.2 `GET /api/v1/moderacion/reportes/{folio}`

| Rol | Descripción |
|-----|-------------|
| `moderador`, `coordinador` | Detalle completo + historial con actores. |

**Códigos:** `200`, `401`, `403`, `404`, `422`.

```json
{
  "folio": "BCH-2026-000377",
  "tipo_dano": "Bache",
  "estado": "Rechazado",
  "severidad": "Baja",
  "ubicacion": { "latitud": 31.741020, "longitud": -106.484300 },
  "calle": "Calle Ignacio Mejía",
  "referencia": null,
  "colonia": { "id": 8, "nombre": "Centro" },
  "sector": { "id": 3, "nombre": "Centro" },
  "descripcion": "Hoyo en la calle.",
  "detalle": { "tamano": "chico", "profundidad": "menos de 5 cm", "carril_afectado": "acotamiento" },
  "confirmaciones": 0,
  "forzado_como_nuevo": true,
  "motivo_rechazo": "La ubicación corresponde a una obra en proceso ya señalizada por el municipio.",
  "autor_id": "6f1c2a9e-3b7d-4e55-9a10-2c8f0d4b7e21",
  "reportes_autor_ultimas_24h": 0,
  "created_at": "2026-11-10T18:03:51-07:00",
  "historial": [
    { "estado_anterior": null, "estado_nuevo": "Recibido", "origen": "ciudadano", "actor_id": "6f1c2a9e-3b7d-4e55-9a10-2c8f0d4b7e21", "actor_rol": "ciudadano", "motivo": null, "fecha": "2026-11-10T18:03:51-07:00" },
    { "estado_anterior": "Recibido", "estado_nuevo": "Rechazado", "origen": "moderacion", "actor_id": "0b9d1e44-7a2c-4f0e-b1c3-55e8a9d2c610", "actor_rol": "moderador", "motivo": "La ubicación corresponde a una obra en proceso ya señalizada por el municipio.", "fecha": "2026-11-11T08:20:05-07:00" }
  ],
  "transiciones_disponibles": []
}
```

> Aun en moderación **no** se exponen `nombre` ni `correo` del autor (minimización de datos, LFPDPPP).

### 5.3 `POST /api/v1/moderacion/reportes/{folio}/transiciones` (RN-05, RN-07)

| Rol | Descripción |
|-----|-------------|
| `moderador`, `coordinador` | Cambia el estado. La combinación (estado actual → nuevo, rol) se valida contra la tabla de `arquitectura.md` §7. |

**Petición**

```json
{
  "estado_nuevo": "Reparado",
  "fecha_reparacion": "2026-11-20",
  "motivo": null,
  "fecha_programada": null
}
```

| `estado_nuevo` | Campos requeridos |
|----------------|-------------------|
| `Validado` | — |
| `Rechazado` | `motivo` (10–500 caracteres) |
| `Programado` | `fecha_programada` opcional (≥ hoy local) |
| `En reparación` | — |
| `Reparado` | `fecha_reparacion` (≥ fecha local del reporte y ≤ hoy local) |

**Códigos**

| Código | Caso |
|--------|------|
| `200` | Transición aplicada y registrada en `historial_estados` |
| `400 TRANSICION_INVALIDA` | Par de estados no permitido (incluye salir de `Reparado`, `Rechazado`, `Histórico`) |
| `401` | Sin token |
| `403 ROL_NO_AUTORIZADO` | Rol sin permiso para esa transición (p. ej. `coordinador` → `Validado`) |
| `404` | Folio inexistente |
| `422` | Falta `motivo`/`fecha_reparacion`, fecha fuera de rango (`FECHA_REPARACION_INVALIDA`), `estado_nuevo` desconocido |

**`200`**

```json
{
  "folio": "BCH-2026-000402",
  "estado_anterior": "En reparación",
  "estado": "Reparado",
  "fecha_reparacion": "2026-11-20",
  "longevidad_dias": 2,
  "registrado_en": "2026-11-21T10:02:48-07:00",
  "mensaje": "El reporte BCH-2026-000402 cambió a \"Reparado\"."
}
```

**`400`**

```json
{ "error": { "codigo": "TRANSICION_INVALIDA", "mensaje": "No es posible cambiar el estado de \"Reparado\" a \"En reparación\".", "detalles": [] } }
```

**`403`**

```json
{ "error": { "codigo": "ROL_NO_AUTORIZADO", "mensaje": "Tu rol no tiene permiso para realizar esta acción.", "detalles": [] } }
```

**`422`**

```json
{
  "error": {
    "codigo": "FECHA_REPARACION_INVALIDA",
    "mensaje": "La fecha de reparación debe ser igual o posterior a la fecha del reporte y no puede ser futura.",
    "detalles": [{ "campo": "fecha_reparacion", "mensaje": "La fecha 2026-11-25 es posterior a hoy (2026-11-21)." }]
  }
}
```

---

## 6. Dominio `catalogos`

### 6.1 `GET /api/v1/catalogos/sectores`

| Rol | `visitante` |
|-----|-------------|

**Códigos:** `200`.

```json
{ "datos": [ { "id": 3, "clave": "CENTRO", "nombre": "Centro" }, { "id": 5, "clave": "SURORIENTE", "nombre": "Suroriente" } ] }
```

### 6.2 `GET /api/v1/catalogos/colonias`

| Rol | `visitante` |
|-----|-------------|

Catálogo local de colonias. Lo usa el formulario de reporte (selector de `colonia_id`), los filtros del mapa y el *fallback* de `GET /geocoding/buscar` (§10).

**Query**

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|:-----------:|-------------|
| `q` | string (2–80) | No | **Código postal:** si `q` son sólo dígitos (2 a 5), filtra por código postal completo o prefijo (`?q=32310`, `?q=325`), ordenado por código postal y nombre. **En otro caso, filtro por nombre.** Coincidencia parcial sin distinguir mayúsculas (`ILIKE '%q%'`) más similitud por trigramas (`pg_trgm`, índice `idx_colonias_nombre_trgm`), para tolerar errores de escritura (`"partdo romro"` → `Partido Romero`). Orden: coincidencia exacta, luego mayor similitud, luego alfabético. |
| `sector_id` | int | No | **Filtro por sector.** Sólo colonias de ese sector. Si el sector no existe → `422`. |
| `pagina`, `por_pagina` | int | No | Paginación (§1.3). |

Ambos filtros son combinables (`?q=infonavit&sector_id=4`). Sólo se devuelven colonias con `activo = true`.

**Códigos:** `200` (lista vacía si no hay coincidencias), `422` (`q` de 1 carácter o > 80, `sector_id` inexistente o no numérico).

**`200`** — `GET /api/v1/catalogos/colonias?q=romero&sector_id=3`

```json
{
  "datos": [
    { "id": 112, "nombre": "Partido Romero", "codigo_postal": "32030", "sector": { "id": 3, "nombre": "Centro" }, "centro": { "latitud": 31.692000, "longitud": -106.430500 } }
  ],
  "paginacion": { "pagina": 1, "por_pagina": 20, "total": 1, "total_paginas": 1 }
}
```

**`422`**

```json
{
  "error": {
    "codigo": "VALIDACION",
    "mensaje": "Revisa los datos marcados.",
    "detalles": [{ "campo": "sector_id", "mensaje": "El sector 99 no existe." }]
  }
}
```

### 6.3 `GET /api/v1/catalogos/tipos-dano` (HU-02.2, HU-03.1)

| Rol | `visitante` |
|-----|-------------|

Describe el formulario dinámico; el frontend lo usa para pintar campos y validar antes de enviar.

**Códigos:** `200`.

```json
{
  "limites_territorio": { "latitud_min": 31.45, "latitud_max": 31.80, "longitud_min": -106.65, "longitud_max": -106.25 },
  "descripcion_max_caracteres": 500,
  "datos": [
    {
      "tipo_dano": "Bache",
      "prefijo_folio": "BCH",
      "radio_duplicados_metros": 30,
      "campos": [
        { "nombre": "tamano", "etiqueta": "Tamaño", "tipo": "enum", "obligatorio": true, "opciones": ["chico", "mediano", "grande"] },
        { "nombre": "profundidad", "etiqueta": "Profundidad", "tipo": "enum", "obligatorio": true, "opciones": ["menos de 5 cm", "5 a 10 cm", "más de 10 cm"] },
        { "nombre": "carril_afectado", "etiqueta": "Carril afectado", "tipo": "enum", "obligatorio": true, "opciones": ["carril derecho", "carril central", "carril izquierdo", "varios carriles", "acotamiento"] }
      ]
    },
    {
      "tipo_dano": "Alcantarilla sin tapa",
      "prefijo_folio": "BCH",
      "radio_duplicados_metros": 30,
      "severidad_fija": "Alta",
      "campos": [
        { "nombre": "esta_senalizado", "etiqueta": "¿Está señalizada?", "tipo": "booleano", "obligatorio": true }
      ]
    },
    {
      "tipo_dano": "Encharcamiento",
      "prefijo_folio": "ENC",
      "radio_duplicados_metros": 50,
      "vigencia_horas": 6,
      "desmentidos_para_historico": 3,
      "campos": [
        { "nombre": "nivel_agua", "etiqueta": "Nivel del agua", "tipo": "enum", "obligatorio": true, "opciones": ["a un lado de la calle", "cubre un carril", "a media llanta", "intransitable"] },
        { "nombre": "hay_riesgo_personas_vehiculos", "etiqueta": "¿Hay riesgo para personas o vehículos?", "tipo": "booleano", "obligatorio": true, "visible_si": { "nivel_agua": "intransitable" } }
      ]
    }
  ]
}
```

### 6.4 `GET /api/v1/catalogos/estados`

| Rol | `visitante` |
|-----|-------------|

**Códigos:** `200`.

```json
{
  "pavimento": {
    "estados": ["Recibido", "Validado", "Programado", "En reparación", "Reparado", "Rechazado"],
    "finales": ["Reparado", "Rechazado"],
    "transiciones": [
      { "desde": "Recibido", "hacia": "Validado", "roles": ["moderador"] },
      { "desde": "Recibido", "hacia": "Rechazado", "roles": ["moderador"] },
      { "desde": "Validado", "hacia": "Programado", "roles": ["moderador", "coordinador"] },
      { "desde": "Validado", "hacia": "En reparación", "roles": ["moderador", "coordinador"] },
      { "desde": "Programado", "hacia": "En reparación", "roles": ["moderador", "coordinador"] },
      { "desde": "En reparación", "hacia": "Reparado", "roles": ["moderador", "coordinador"] }
    ],
    "etiquetas_publicas": { "Recibido": "Sin validar" }
  },
  "encharcamiento": {
    "estados": ["Activo", "Histórico", "Rechazado"],
    "finales": ["Histórico", "Rechazado"],
    "transiciones": [
      { "desde": "Activo", "hacia": "Histórico", "roles": ["sistema"] },
      { "desde": "Activo", "hacia": "Rechazado", "roles": ["moderador"] }
    ]
  }
}
```

---

## 7. Dominio `admin`

Todas las rutas: rol **`coordinador`**. Otros roles autenticados → `403`; sin token → `401`.

### 7.1 `GET /api/v1/admin/usuarios`

**Query:** `rol`, `activo`, `q` (nombre o correo), `pagina`, `por_pagina`. **Códigos:** `200`, `401`, `403`, `422`.

```json
{
  "datos": [
    { "id": "0b9d1e44-7a2c-4f0e-b1c3-55e8a9d2c610", "nombre": "José Luis Carrasco", "correo": "jl.carrasco@ejemplo.mx", "rol": "moderador", "activo": true, "created_at": "2026-08-02T12:00:00-06:00" }
  ],
  "paginacion": { "pagina": 1, "por_pagina": 20, "total": 1, "total_paginas": 1 }
}
```

> Vista **privada** de administración (no pública). No se combina con datos de reportes en la misma respuesta.

### 7.2 `PATCH /api/v1/admin/usuarios/{usuario_id}/rol`

**Petición:** `{ "rol": "moderador" }` (valores: `ciudadano`, `moderador`, `coordinador`).
Incrementa `token_version` del usuario afectado. Un coordinador no puede cambiar su propio rol (`400`).
**Códigos:** `200`, `400`, `401`, `403`, `404`, `422`.

```json
{ "id": "0b9d1e44-7a2c-4f0e-b1c3-55e8a9d2c610", "rol": "moderador", "mensaje": "El rol se actualizó. El usuario deberá iniciar sesión de nuevo." }
```

### 7.3 `PATCH /api/v1/admin/usuarios/{usuario_id}/estado`

**Petición:** `{ "activo": false }`. Desactivar incrementa `token_version`. No puede desactivarse a sí mismo (`400`).
**Códigos:** `200`, `400`, `401`, `403`, `404`, `422`.

```json
{ "id": "6f1c2a9e-3b7d-4e55-9a10-2c8f0d4b7e21", "activo": false, "mensaje": "La cuenta fue desactivada." }
```

### 7.4 `POST /api/v1/admin/sectores` · `PATCH /api/v1/admin/sectores/{sector_id}`

**Petición (POST)**

```json
{ "clave": "NORPONIENTE", "nombre": "Norponiente" }
```

PATCH acepta `nombre`, `activo`. `clave` es inmutable.
**Códigos:** `201` / `200`, `401`, `403`, `404` (PATCH), `409` (clave o nombre repetido), `422`.

```json
{ "id": 7, "clave": "NORPONIENTE", "nombre": "Norponiente", "activo": true }
```

### 7.5 `POST /api/v1/admin/colonias` · `PATCH /api/v1/admin/colonias/{colonia_id}`

**Petición (POST)**

```json
{ "sector_id": 7, "nombre": "Felipe Ángeles", "codigo_postal": "32090", "latitud_centro": 31.744300, "longitud_centro": -106.501200 }
```

PATCH acepta `nombre`, `codigo_postal`, `latitud_centro`, `longitud_centro`, `sector_id`, `activo`. El centro debe cumplir RN-01.
**Códigos:** `201` / `200`, `401`, `403`, `404`, `409` (nombre repetido en el sector), `422` (incluye `FUERA_DE_JUAREZ`).

```json
{ "id": 318, "nombre": "Felipe Ángeles", "codigo_postal": "32090", "sector": { "id": 7, "nombre": "Norponiente" }, "centro": { "latitud": 31.744300, "longitud": -106.501200 }, "activo": true }
```

> No hay `DELETE` de catálogos: se desactivan (`activo = false`) para conservar la integridad de reportes históricos.

---

## 8. Dominio `indicadores`

Los **históricos y reparados cuentan** en todas las métricas (RN-06). Los `Rechazado` se excluyen de las métricas públicas. No existe `GET /api/v1/indicadores` (responde `404`): usa las subrutas `/resumen`, `/sectores`, `/longevidad` y `/moderacion`.

### 8.1 `GET /api/v1/indicadores/resumen`

| Rol | `visitante` |
|-----|-------------|

**Query:** `desde`, `hasta` (fechas locales), `sector_id`. **Códigos:** `200`, `422`.

```json
{
  "periodo": { "desde": "2026-01-01", "hasta": "2026-11-21", "zona_horaria": "America/Ciudad_Juarez" },
  "pavimento": {
    "total": 418,
    "por_estado": { "Recibido": 37, "Validado": 52, "Programado": 41, "En reparación": 18, "Reparado": 270 },
    "por_tipo": { "Bache": 389, "Alcantarilla sin tapa": 29 },
    "longevidad_promedio_abiertos_dias": 24.6,
    "tiempo_promedio_reparacion_dias": 31.2
  },
  "encharcamientos": {
    "total": 97,
    "activos": 4,
    "historicos": 93,
    "intransitables": 11
  },
  "actualizado_en": "2026-11-21T10:05:00-07:00"
}
```

### 8.2 `GET /api/v1/indicadores/sectores`

| Rol | `visitante` |
|-----|-------------|

**Query:** `desde`, `hasta`. **Códigos:** `200`, `422`.

```json
{
  "datos": [
    { "sector": { "id": 5, "nombre": "Suroriente" }, "baches_abiertos": 61, "reparados": 88, "longevidad_promedio_abiertos_dias": 33.1, "encharcamientos_total": 41, "encharcamientos_activos": 2 },
    { "sector": { "id": 3, "nombre": "Centro" }, "baches_abiertos": 27, "reparados": 95, "longevidad_promedio_abiertos_dias": 14.8, "encharcamientos_total": 19, "encharcamientos_activos": 1 }
  ]
}
```

### 8.3 `GET /api/v1/indicadores/longevidad`

| Rol | `visitante` |
|-----|-------------|

Baches abiertos más antiguos (RN-10). **Query:** `sector_id`, `limite` (1–50, default 10). **Códigos:** `200`, `422`.

```json
{
  "datos": [
    { "folio": "BCH-2026-000012", "tipo_dano": "Bache", "estado": "Validado", "severidad": "Alta", "calle": "Av. Manuel J. Clouthier", "colonia": { "id": 240, "nombre": "Riberas del Bravo" }, "created_at": "2026-01-09T08:30:00-07:00", "longevidad_dias": 316 }
  ]
}
```

### 8.4 `GET /api/v1/indicadores/moderacion`

| Rol | `moderador`, `coordinador` |
|-----|----------------------------|

**Query:** `desde`, `hasta`. **Códigos:** `200`, `401`, `403`, `422`.

```json
{
  "pendientes_validacion": 37,
  "antiguedad_max_pendiente_horas": 52.4,
  "tiempo_promedio_validacion_horas": 9.7,
  "rechazados_periodo": 23,
  "tasa_rechazo_pct": 5.2,
  "reportes_forzados_como_nuevos": 14,
  "encharcamientos_rechazados": 3
}
```

---

## 9. Dominio `clima`

### 9.1 `GET /api/v1/clima/pronostico`

| Rol | `visitante` |
|-----|-------------|

Consulta `WEATHER_API_URL` a lo sumo una vez cada `WEATHER_CACHE_TTL_MINUTES` (**60 min** por omisión, HU-08.1) y guarda en `cache_clima`. Si el proveedor falla, durante `WEATHER_BACKOFF_MINUTES` (5 min) no se vuelve a consultar: se responde de inmediato con la última caché marcada `desactualizado: true`, o `503` si no hay ninguna.
**Códigos:** `200`, `503 CLIMA_NO_DISPONIBLE` (proveedor caído **y** sin caché).

```json
{
  "ubicacion": "Ciudad Juárez, Chihuahua",
  "actual": { "temperatura_c": 14.2, "precipitacion_mm": 0.8, "descripcion": "Lluvia ligera" },
  "proximas_horas": [
    { "hora": "2026-11-21T11:00:00-07:00", "probabilidad_lluvia_pct": 70, "precipitacion_mm": 2.1 },
    { "hora": "2026-11-21T12:00:00-07:00", "probabilidad_lluvia_pct": 85, "precipitacion_mm": 4.6 }
  ],
  "alerta_lluvia": true,
  "mensaje_alerta": "Se esperan lluvias en las próximas horas. Consulta las calles con riesgo de inundación antes de salir.",
  "obtenido_en": "2026-11-21T10:00:00-07:00",
  "desactualizado": false
}
```

### 9.2 `GET /api/v1/clima/riesgo-inundacion`

| Rol | `visitante` |
|-----|-------------|

Calles con riesgo de inundación: combina encharcamientos **activos**, la recurrencia **histórica** (últimos 12 meses) y el pronóstico.
**Query:** `sector_id`, `colonia_id`, `calle` (≥ 3), `bbox`, `limite` (1–100, default 20). **Códigos:** `200`, `422`.

```json
{
  "alerta_lluvia": true,
  "datos": [
    {
      "calle": "Av. de las Torres",
      "colonia": { "id": 57, "nombre": "Infonavit Casas Grandes" },
      "sector": { "id": 4, "nombre": "Poniente" },
      "nivel_riesgo": "Alto",
      "encharcamientos_activos": 1,
      "nivel_agua_maximo_activo": "intransitable",
      "encharcamientos_historicos_12_meses": 14,
      "ultimo_reporte": "2026-11-21T08:55:00-07:00",
      "folios_activos": ["ENC-2026-000097"],
      "recomendacion": "Evita circular por esta calle: hay un encharcamiento intransitable reportado."
    }
  ],
  "criterio": "Alto: activo 'intransitable' o 'a media llanta', o ≥ 10 históricos con alerta de lluvia; Medio: cualquier activo o ≥ 3 históricos; Bajo: resto.",
  "obtenido_en": "2026-11-21T10:05:00-07:00"
}
```

---

## 10. Dominio `geocoding`

Búsqueda de direcciones para ubicar un reporte en el mapa (**HU-02.1**) y para consultar una calle o lugar antes de circular (**HU-04.3**). FastAPI actúa como **proxy** hacia LocationIQ: el navegador **nunca** llama a LocationIQ ni conoce la llave.

### 10.1 `GET /api/v1/geocoding/buscar`

| Rol | Descripción |
|-----|-------------|
| `visitante` | Convierte un texto libre (calle, cruce, lugar, colonia) o un **código postal de Juárez** en coordenadas **dentro de Ciudad Juárez**. |

**Query**

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|:-----------:|-------------|
| `q` | string (3–120) | Sí | Texto a buscar. Ej.: `Av. Tecnológico y Ejército Nacional` o `32310`. Se le quitan espacios repetidos y caracteres de control. Un código postal de 5 dígitos se resuelve **siempre con el catálogo local** (`fuente: "catalogo_local"`, `degradado: false`, `precision: "colonia"`, centro de cada colonia); si está fuera de `32000`–`32730` → `422` («El código postal … no pertenece a Ciudad Juárez»). |
| `limite` | int (1–10) | No | Máximo de resultados. Default `5`. |

#### Llamada que hace el backend (no visible para el cliente)

```text
GET {GEOCODING_API_URL}/search
    ?key={GEOCODING_API_KEY}
    &q={q}, Ciudad Juárez, Chihuahua
    &format=json
    &addressdetails=1
    &countrycodes=mx
    &accept-language=es
    &viewbox=-106.65,31.80,-106.25,31.45     ← lon_min,lat_max,lon_max,lat_min (RN-01)
    &bounded=1                               ← sólo resultados dentro del viewbox
    &limit={limite}
```

- **Filtro territorial doble (RN-01):** además de `viewbox` + `bounded=1`, el backend descarta cualquier resultado con `latitud ∉ [31.45, 31.80]` o `longitud ∉ [-106.65, -106.25]` antes de responder.
- **Normalización:** la respuesta de LocationIQ **no se reenvía tal cual**. Se transforma al esquema de abajo; se omiten `place_id`, `osm_id`, `licence`, `boundingbox` y cualquier otro campo del proveedor.
- **Colonia sugerida:** se intenta relacionar el resultado con el catálogo local, primero por nombre (`address.neighbourhood` / `address.suburb` contra `colonias.nombre` con `pg_trgm`) y, si no hay coincidencia, con la colonia cuyo centro esté más cerca (Haversine, máx. 1 500 m). Si no hay ninguna, `colonia_sugerida = null` y el ciudadano la elige manualmente.
- **Tiempo de espera:** `GEOCODING_TIMEOUT_SECONDS` (default 5 s).

#### Fallback si LocationIQ falla

Se activa cuando el proveedor tarda más que el tiempo de espera, responde `401/403` (llave inválida), `429` (cuota agotada) o `5xx`, o cuando `GEOCODING_API_KEY` no está configurada.

1. El backend registra el incidente (código HTTP del proveedor y duración) **sin** la URL completa, porque la llave viaja en el *query string*.
2. Responde **`200`** con resultados del **catálogo local de colonias** (misma búsqueda que `GET /catalogos/colonias?q=...`), usando el centro de cada colonia como coordenada aproximada.
3. Marca la respuesta con `"fuente": "catalogo_local"`, `"degradado": true` y un `mensaje` para que el frontend pida al usuario **ajustar el marcador en el mapa** (las coordenadas son aproximadas).
4. Si tampoco hay coincidencias locales → `200` con `datos: []`. El usuario siempre puede colocar el marcador manualmente, así que la creación de reportes no depende del geocodificador.

Nunca se responde `5xx` por falla del proveedor; el error del proveedor no se propaga al cliente.

**Códigos**

| Código | Caso |
|--------|------|
| `200` | Resultados de LocationIQ (`fuente: "locationiq"`), resultados de respaldo (`fuente: "catalogo_local"`) o lista vacía |
| `422` | `q` ausente, < 3 o > 120 caracteres; `limite` fuera de rango |
| `429 LIMITE_BUSQUEDAS` | Más de 30 búsquedas por minuto desde la misma IP (protege la cuota de LocationIQ); incluye `Retry-After` |

No aplica `401`/`403`: es público para que el visitante pueda consultar calles (HU-04.3).

**`200` — LocationIQ disponible**

```json
{
  "fuente": "locationiq",
  "degradado": false,
  "datos": [
    {
      "etiqueta": "Avenida Tecnológico, Partido Romero, Ciudad Juárez, Chihuahua",
      "calle": "Avenida Tecnológico",
      "ubicacion": { "latitud": 31.690520, "longitud": -106.425010 },
      "precision": "calle",
      "colonia_sugerida": { "id": 112, "nombre": "Partido Romero", "sector": { "id": 3, "nombre": "Centro" } }
    },
    {
      "etiqueta": "Avenida Tecnológico, Fuentes del Valle, Ciudad Juárez, Chihuahua",
      "calle": "Avenida Tecnológico",
      "ubicacion": { "latitud": 31.703180, "longitud": -106.418770 },
      "precision": "calle",
      "colonia_sugerida": null
    }
  ],
  "atribucion": "Búsqueda por LocationIQ.com · Datos © colaboradores de OpenStreetMap",
  "mensaje": null
}
```

`precision`: `direccion` (número exterior), `calle`, `colonia` o `aproximada` (centro de colonia).

**`200` — Fallback por falla del proveedor**

```json
{
  "fuente": "catalogo_local",
  "degradado": true,
  "datos": [
    {
      "etiqueta": "Partido Romero, Centro, Ciudad Juárez, Chihuahua",
      "calle": null,
      "ubicacion": { "latitud": 31.692000, "longitud": -106.430500 },
      "precision": "aproximada",
      "colonia_sugerida": { "id": 112, "nombre": "Partido Romero", "sector": { "id": 3, "nombre": "Centro" } }
    }
  ],
  "atribucion": null,
  "mensaje": "El buscador de direcciones no está disponible en este momento. Te mostramos colonias que coinciden (ubicación aproximada al centro de la colonia); para indicar el punto exacto usa tu ubicación GPS estando en el lugar del daño."
}
```

**`422`**

```json
{
  "error": {
    "codigo": "VALIDACION",
    "mensaje": "Revisa los datos marcados.",
    "detalles": [{ "campo": "q", "mensaje": "Escribe al menos 3 caracteres para buscar." }]
  }
}
```

**`429`** (encabezado `Retry-After: 40`)

```json
{ "error": { "codigo": "LIMITE_BUSQUEDAS", "mensaje": "Hiciste demasiadas búsquedas en poco tiempo. Espera unos segundos e intenta de nuevo.", "detalles": [] } }
```

### 10.2 `GET /api/v1/geocoding/inversa`

| Rol | Descripción |
|-----|-------------|
| `visitante` | Convierte una coordenada **dentro de Juárez** (RN-01) en calle y colonia sugeridas. El formulario la usa tras obtener el GPS. |

**Query:** `latitud`, `longitud` (obligatorios). Fuera de los límites → `422 FUERA_DE_JUAREZ`. Comparte el límite de 30 consultas por minuto por IP (`429 LIMITE_BUSQUEDAS`).

Con `GEOCODING_API_KEY`, el backend consulta `/reverse` de LocationIQ (`fuente: "locationiq"`); sin llave o si falla, responde con la colonia registrada más cercana (≤ 1.5 km) del catálogo local (`fuente: "catalogo_local"`, `degradado: true`).

```json
{
  "fuente": "catalogo_local",
  "degradado": true,
  "ubicacion": { "latitud": 31.733, "longitud": -106.463 },
  "calle": null,
  "etiqueta": "Partido Romero, Ciudad Juárez, Chihuahua",
  "colonia_sugerida": { "id": 4, "nombre": "Partido Romero", "codigo_postal": "32030", "sector": { "id": 3, "nombre": "Centro" } },
  "colonias_cercanas": [
    { "id": 4, "nombre": "Partido Romero", "codigo_postal": "32030", "sector": { "id": 3, "nombre": "Centro" }, "distancia_metros": 0.0 }
  ],
  "atribucion": null,
  "mensaje": "Sugerimos la colonia registrada más cercana al punto. Confirma la colonia y escribe el nombre de la calle."
}
```

**Códigos:** `200`, `422`, `429`.

### 10.3 Protección de la llave de LocationIQ

| Control | Detalle |
|---------|---------|
| Sólo backend | `GEOCODING_API_KEY` se lee únicamente en la configuración de FastAPI (`pydantic-settings`, tipo `SecretStr`). No tiene prefijo `VITE_`, por lo que Vite **no** la incluye en el *bundle*. |
| Sin paso al frontend | El Dockerfile y el servicio `frontend` de docker-compose sólo reciben `VITE_API_BASE_URL`; `GEOCODING_*` se inyecta exclusivamente al servicio `backend`. |
| Sin eco en respuestas | Ninguna respuesta (éxito, error o *fallback*) incluye la URL del proveedor, la llave ni el cuerpo de error de LocationIQ. |
| Sin eco en registros | Los logs del cliente HTTP enmascaran el parámetro `key` (`key=***`); la consulta `q` tampoco se registra completa porque puede contener el domicilio del usuario (dato personal). |
| CSP del frontend | `connect-src` permite sólo el origen de la API; una llamada directa del navegador a `*.locationiq.com` sería bloqueada. |
| Rotación | La llave se puede cambiar en `.env` y reiniciar el backend, sin recompilar el frontend. |

---

## 11. Verificación de privacidad (RN-04)

### 11.1 Respuestas públicas (sin token) revisadas

| Endpoint | Esquema | ¿Contiene `usuario_id` / `autor_id`? | ¿Nombre / correo? | ¿Otro dato personal? |
|----------|---------|:---:|:---:|:---:|
| `GET /reportes` | `ReporteResumenPublico` | No | No | No |
| `GET /reportes/{folio}` | `ReportePublico` | No | No | No |
| `GET /reportes/{folio}/historial` | `HistorialPublico` (sólo `origen`) | No | No | No |
| `GET /catalogos/*` | Catálogos | No | No | No |
| `GET /indicadores/resumen`, `/sectores`, `/longevidad` | Agregados / `ReporteResumenPublico` | No | No | No |
| `GET /clima/pronostico`, `/clima/riesgo-inundacion` | Clima y agregados por calle | No | No | No |
| `GET /geocoding/buscar` | Resultados normalizados de dirección | No | No | No (la consulta `q` no se almacena ni se registra completa) |
| Errores `404` de folio `Rechazado` | Envoltura de error | No | No | No (no revela existencia) |

### 11.2 Respuestas autenticadas

| Endpoint | Datos de identidad incluidos | Justificación |
|----------|------------------------------|---------------|
| `POST /reportes`, `GET /reportes/mios` | Sólo `es_mio: true` | El autor ve lo propio; no se repite su nombre/correo. |
| `GET /reportes/cercanos`, `POST /reportes/{folio}/confirmaciones` | `es_mio`, `ya_confirmado_por_mi` (booleanos respecto al solicitante) | No revelan identidad de terceros. |
| `GET /auth/yo` | Nombre y correo **del propio usuario** | Vista privada de la cuenta. |
| `GET /moderacion/*` | `autor_id`, `actor_id` (UUID) | Detección de abuso; sin nombre ni correo. |
| `GET /admin/usuarios` | Nombre y correo | Sólo `coordinador`; no se cruza con reportes. |

### 11.3 Garantías de implementación

1. Los esquemas públicos se definen como clases Pydantic **independientes** (no heredan de los modelos internos) con `model_config = ConfigDict(extra="forbid")`, y los routers declaran `response_model=` explícito para que FastAPI filtre cualquier atributo no declarado.
2. Prueba automatizada (`backend/tests/test_api.py::test_respuestas_publicas_sin_datos_personales`): recorre las rutas públicas con datos semilla y falla si algún JSON contiene las llaves `usuario_id`, `autor_id`, `actor_id`, `correo`, `password_hash`, `token_version` o `motivo_rechazo`, o cualquier nombre o correo de los usuarios registrados (`nombre` es llave legítima en los catálogos de sectores y colonias).
3. Los registros (logs) nunca incluyen correo completo, contraseña ni token.
4. Prueba automatizada (`backend/tests/test_api.py::test_geocoding_locationiq_filtra_juarez_y_no_expone_la_llave`): con `GEOCODING_API_KEY` configurada con un valor centinela, provoca éxito y *fallback* en `/geocoding/buscar` y falla si ese valor aparece en algún cuerpo de respuesta o encabezado. En el frontend, CI debe fallar si `grep -rE "GEOCODING_API_KEY|locationiq\.com/v1" frontend/dist` encuentra coincidencias (pendiente: aún no existe el frontend).

---

## 12. Resumen de endpoints

| Dominio | Método | Ruta | Roles | Éxito |
|---------|--------|------|-------|-------|
| auth | POST | `/api/v1/auth/registro` | visitante | 201 |
| auth | POST | `/api/v1/auth/login` | visitante | 200 |
| auth | POST | `/api/v1/auth/renovar` | ciudadano, moderador, coordinador | 200 |
| auth | POST | `/api/v1/auth/cerrar-sesion` | ciudadano, moderador, coordinador | 204 |
| auth | GET | `/api/v1/auth/yo` | ciudadano, moderador, coordinador | 200 |
| reportes | GET | `/api/v1/reportes` | visitante | 200 |
| reportes | GET | `/api/v1/reportes/cercanos` | ciudadano, moderador, coordinador | 200 |
| reportes | POST | `/api/v1/reportes` | ciudadano, moderador, coordinador | 201 |
| reportes | GET | `/api/v1/reportes/mios` | ciudadano, moderador, coordinador | 200 |
| reportes | GET | `/api/v1/reportes/{folio}` | visitante | 200 |
| reportes | GET | `/api/v1/reportes/{folio}/historial` | visitante | 200 |
| reportes | PATCH | `/api/v1/reportes/{folio}` | autor del reporte (sólo en `Recibido`) | 200 |
| reportes | POST | `/api/v1/reportes/{folio}/confirmaciones` | ciudadano, moderador, coordinador | 201 |
| reportes | DELETE | `/api/v1/reportes/{folio}` | — | 405 siempre |
| moderacion | GET | `/api/v1/moderacion/reportes` | moderador, coordinador | 200 |
| moderacion | GET | `/api/v1/moderacion/reportes/{folio}` | moderador, coordinador | 200 |
| moderacion | POST | `/api/v1/moderacion/reportes/{folio}/transiciones` | moderador, coordinador (según transición) | 200 |
| catalogos | GET | `/api/v1/catalogos/sectores` | visitante | 200 |
| catalogos | GET | `/api/v1/catalogos/colonias` | visitante | 200 |
| catalogos | GET | `/api/v1/catalogos/tipos-dano` | visitante | 200 |
| catalogos | GET | `/api/v1/catalogos/estados` | visitante | 200 |
| admin | GET | `/api/v1/admin/usuarios` | coordinador | 200 |
| admin | PATCH | `/api/v1/admin/usuarios/{usuario_id}/rol` | coordinador | 200 |
| admin | PATCH | `/api/v1/admin/usuarios/{usuario_id}/estado` | coordinador | 200 |
| admin | POST / PATCH | `/api/v1/admin/sectores[/{sector_id}]` | coordinador | 201 / 200 |
| admin | POST / PATCH | `/api/v1/admin/colonias[/{colonia_id}]` | coordinador | 201 / 200 |
| indicadores | GET | `/api/v1/indicadores/resumen` | visitante | 200 |
| indicadores | GET | `/api/v1/indicadores/sectores` | visitante | 200 |
| indicadores | GET | `/api/v1/indicadores/longevidad` | visitante | 200 |
| indicadores | GET | `/api/v1/indicadores/moderacion` | moderador, coordinador | 200 |
| clima | GET | `/api/v1/clima/pronostico` | visitante | 200 |
| clima | GET | `/api/v1/clima/riesgo-inundacion` | visitante | 200 |
| geocoding | GET | `/api/v1/geocoding/buscar` | visitante | 200 (incluye *fallback*) |
| geocoding | GET | `/api/v1/geocoding/inversa` | visitante | 200 (incluye *fallback*) |

---

## 10. Extensiones opcionales · Fase 1

> Todas las rutas están en `/api/v1`, documentadas en `/docs` (OpenAPI) y devuelven errores con la envoltura estándar (§1.4).

### 10.1 `POST /api/v1/reportes/{folio}/fotos` (HU-02.4)

`multipart/form-data` con el campo repetido `archivos` (hasta 3 imágenes **JPG/PNG**, ≤ 5 MB = `5 * 1024 * 1024` bytes cada una). Requiere sesión; sólo quien creó o confirmó el reporte.

| Código | Cuándo |
|--------|--------|
| `201` | Al menos una foto válida. Cuerpo: `{ folio, aceptadas: [FotoOut], rechazadas: [{nombre, motivo}], mensaje }`. |
| `401` | Sin sesión. |
| `403` | La persona no creó ni confirmó el reporte. |
| `404` | Folio inexistente (o `Rechazado` ajeno). |
| `409` | Reporte `Rechazado` (propio): ya no admite fotos. |
| `422` | Ninguna foto válida (`FOTOS_INVALIDAS`, un detalle por archivo: formato, tamaño, vacío o límite de 3). |

`FotoOut`: `{ id, url, nombre_original, mime_type, tamano_bytes, created_at }` (sin datos de quien la subió).

### 10.2 `GET /api/v1/reportes/{folio}/fotos` y `GET /api/v1/reportes/{folio}/fotos/{foto_id}`

Lista de metadatos (`{ folio, maximo_por_persona, datos }`) y archivo binario (`image/jpeg` o `image/png`, `Cache-Control: private`). Con el reporte en `Recibido` sólo el autor, moderación y coordinación (`200`); visitantes y otros ciudadanos reciben `403 FOTO_NO_DISPONIBLE`. Desde `Validado` son públicas. `404` si el reporte está `Rechazado` (para quien no sea autor/moderación) o la foto no existe.

### 10.3 `GET /api/v1/reportes/mapa` (HU-04.5)

Acepta los **mismos parámetros que `GET /api/v1/reportes`** (`tipo_dano`, `estado`, `solo_vigentes`, `colonia_id`, `sector_id`, `calle`, `bbox`, `desde`, `hasta`, `orden`) sin paginación. Público.

```json
{
  "total": 1240, "mostrados": 1240, "limite": 2000,
  "datos": [{
    "folio": "BCH-2026-000418", "tipo_dano": "Bache", "estado": "Recibido",
    "etiqueta_publica": "Sin validar", "severidad": "Alta",
    "ubicacion": { "latitud": 31.7201, "longitud": -106.4602 },
    "calle": "Av. Tecnológico", "colonia": { "id": 3, "nombre": "Partido Escobedo" },
    "nivel_agua": null, "created_at": "2026-11-22T09:15:00-07:00"
  }]
}
```

Nunca incluye `Rechazado` (`422` si se pide ese estado) ni datos de la persona reportante (RN-04, RN-09).

### 10.4 `GET /api/v1/reportes/exportar/csv` · `GET /api/v1/reportes/exportar/xml` (HU-07.3)

Roles `moderador` y `coordinador` (`401` sin sesión, `403` para ciudadanos). Mismos filtros que la consulta.

* CSV: `text/csv; charset=utf-8` con BOM; columnas `folio, tipo_dano, ubicacion, colonia, estado, fecha_creacion, fecha_actualizacion`.
* XML: `application/xml`, validado contra `docs/esquemas/reportes_v1.xsd` (`<reportes version total generado zona_horaria><reporte>…</reporte></reportes>`).
* Cabeceras: `Content-Disposition: attachment`, `X-Total-Registros`, `X-Registros-Exportados` (tope 50 000).

### 10.5 `POST /api/v1/admin/catalogos/importar-xml` (extra 4.4)

Sólo `coordinador`. `multipart/form-data` con el campo `archivo` (XML ≤ 2 MB validado contra `docs/esquemas/catalogos_v1.xsd`).

| Código | Cuándo |
|--------|--------|
| `200` | `{ sectores_creados, sectores_actualizados, colonias_creadas, colonias_actualizadas, mensaje }`. Idempotente. |
| `401` / `403` | Sin sesión / rol distinto de coordinador. |
| `413` | Archivo mayor de 2 MB. |
| `422 XML_INVALIDO` | Vacío, mal formado, con `DOCTYPE`, fuera del XSD o con integridad referencial rota. `detalles[]` trae `linea`, `campo` y `mensaje`. No se importa nada. |

---

## 11. Extensiones opcionales · Fase 2

### 11.1 Recurrencia en `ReporteResumenPublico` y `ReportePublico` (HU-03.4)

Sólo en encharcamientos (en pavimento los tres campos son `null`):

```json
{ "es_punto_recurrente": true, "dias_distintos_anio": 4, "ultima_ocurrencia": "2026-11-20T18:05:00-07:00" }
```

### 11.2 `GET /api/v1/indicadores/puntos-recurrentes` (HU-03.4, sólo `coordinador`)

`401` sin sesión, `403` para otros roles. Respuesta: `{ anio, radio_metros: 50, minimo_dias: 3, datos: [{ ubicacion, calle, colonia, dias_distintos_anio, total_reportes, ultima_ocurrencia, folios }] }`.

### 11.3 Notificaciones (HU-08.2) · `GET /api/v1/notificaciones`, `PATCH /api/v1/notificaciones/{id}/leer`, `PATCH /api/v1/notificaciones/leer-todas`

Todas requieren sesión (`401`) y operan **sólo sobre los avisos de quien las llama**.

| Ruta | Respuesta |
|------|-----------|
| `GET /notificaciones?solo_no_leidas=&pagina=&por_pagina=` | `{ datos: [{ id, folio, mensaje, leida, created_at }], paginacion, no_leidas }` (más recientes primero). |
| `PATCH /notificaciones/{id}/leer` | `200` con el aviso en `leida: true`; **`404`** si es de otra persona o no existe. |
| `PATCH /notificaciones/leer-todas` | `{ marcadas, no_leidas: 0, mensaje }`. |

### 11.4 WebSocket `GET /api/v1/ws/encharcamientos` (HU-08.3 · extra 4.5)

Protocolo y garantías en `arquitectura.md` §11.3. Mensajes del servidor (JSON):

```json
{ "tipo": "hola", "heartbeat_segundos": 20 }
{ "tipo": "ping" }
{ "tipo": "encharcamiento.creado", "event_id": "7d0c…", "folio": "ENC-2026-000210", "emitido_en": "2026-11-22T17:02:11-07:00", "reporte": { "...ReporteResumenPublico..." } }
{ "tipo": "encharcamiento.actualizado", "event_id": "…", "folio": "ENC-2026-000210", "emitido_en": "…", "reporte": { "...": "…" } }
{ "tipo": "encharcamiento.retirado", "event_id": "…", "folio": "ENC-2026-000210", "emitido_en": "…", "reporte": null }
```

El cliente responde `{"tipo":"pong"}` a cada `ping`. Un `Origin` distinto de `FRONTEND_URL` se cierra con el código 1008. Los eventos no contienen autor, correo ni identificadores internos.

### 11.5 `POST /api/v1/reportes` con `idempotency_key` (HU-08.4)

Campo opcional `idempotency_key` (UUID) en el cuerpo de cualquiera de los tres tipos. Primera vez: `201`. Reenvío con la misma llave de la misma persona: **`200`** con el mismo reporte (mismo folio), sin crear otro ni consumir el límite de 10/hora. Llaves iguales de personas distintas no se relacionan. Una llave que no es UUID responde `422`. La llave nunca aparece en las respuestas.

---

## 12. Extensiones opcionales · Fase 3

### 12.1 Cambio en `POST /api/v1/moderacion/reportes/{folio}/transiciones` (HU-06.3)

Para `estado_nuevo: "Rechazado"` es obligatorio `motivo_id` (motivo **activo** de `GET /api/v1/catalogos/motivos-rechazo`); `motivo` pasa a ser un detalle opcional (máx. 300). Sin `motivo_id` → `422`; inactivo o inexistente → `422 MOTIVO_NO_AUTORIZADO`.

### 12.2 `POST /api/v1/moderacion/reportes/fusionar` (HU-05.3 · sólo moderador)

Cuerpo `{ "folio_principal": "BCH-2026-000418", "folio_secundario": "BCH-2026-000421" }`. Respuesta `200`: `{ folio_principal, folio_secundario, estado_secundario: "Rechazado", confirmaciones_transferidas, confirmaciones_principal, registrado_en, mensaje }`. Errores: `403 ROL_NO_AUTORIZADO` si el rol no puede rechazar un reporte `Recibido` (RN-05: sólo moderación; antes coordinación lo hacía por esta vía), `404` folio inexistente, `409 SECUNDARIO_NO_FUSIONABLE` / `PRINCIPAL_NO_VALIDO`, `422 FUSION_INVALIDA` (mismo folio, tipos distintos o encharcamientos). `MiReporte` y el detalle de moderación incluyen `folio_principal`.

### 12.3 Cuadrillas (HU-05.4 · sólo coordinador)

| Ruta | Descripción |
|------|-------------|
| `GET /cuadrillas?solo_activas=` · `POST /cuadrillas` | Lista (con `pendientes`) y alta `{ nombre, responsable, telefono_contacto }`. Nombre repetido → `409`. |
| `GET /cuadrillas/{id}` | Detalle con `enlaces` y `baches` (activos e historial, sin datos del ciudadano). |
| `PATCH /cuadrillas/{id}` | Editar o `{ "activa": false }`. |
| `DELETE /cuadrillas/{id}` | `204`; `409 CUADRILLA_CON_PENDIENTES` o `409 CUADRILLA_CON_HISTORIAL`. |
| `POST /cuadrillas/{id}/asignaciones` | `{ folio, fecha_programada }`: `Validado → Programado` (o reasignación). `409` si no está `Validado`/`Programado` o la cuadrilla está inactiva; `422` fecha pasada. |
| `POST /cuadrillas/{id}/enlaces` · `DELETE /cuadrillas/{id}/enlaces/{usuario_id}` | Vincular/desvincular cuentas `enlace_municipal` (`422 ROL_INCOMPATIBLE` para otros roles). |

### 12.4 Enlace municipal (HU-05.5 · sólo `enlace_municipal`)

`GET /enlace/reportes?incluir_reparados=` → `{ cuadrillas, datos: [BacheAsignado] }`; `GET /enlace/reportes/{folio}`; `POST /enlace/reportes/{folio}/avance` con `{ estado_nuevo: "En reparación" | "Reparado", fecha_reparacion? }`. Ajenos → `403 REPORTE_AJENO`; cuenta suspendida → `403 CUENTA_SUSPENDIDA`; paso inválido → `400`; fecha inválida → `422`.

### 12.5 Catálogos (HU-06.3)

Públicos: `GET /catalogos/tipos-dano` (sólo activos, ahora con `nombre` y `descripcion`) y `GET /catalogos/motivos-rechazo` (activos). Coordinador: `GET|POST /admin/catalogos/tipos-dano`, `PATCH /admin/catalogos/tipos-dano/{id}`, `GET|POST /admin/catalogos/motivos-rechazo`, `PATCH /admin/catalogos/motivos-rechazo/{id}` (`{ nombre?, descripcion?, activo? }`). No hay `DELETE`.

### 12.6 Colonias de interés (HU-01.4 · con sesión)

`GET /perfil/colonias-favoritas` → `{ maximo: 20, datos: [{ colonia, sector, codigo_postal, activa, agregada_en }] }`; `POST` `{ colonia_id }` → `201` (o `200` si ya estaba; `422` si la colonia no está activa); `DELETE /perfil/colonias-favoritas/{colonia_id}` → `204` / `404`. En `GET /reportes` con sesión cada elemento puede traer `en_tus_colonias`.

### 12.7 `GET /api/v1/trayecto/revisar` (HU-04.6 · público)

Parámetros `origen_latitud`, `origen_longitud`, `destino_latitud`, `destino_longitud` (RN-01). Respuesta: `{ origen, destino, radio_metros: 100, ruta: { fuente: "osrm" | "linea_recta", degradado, mensaje, distancia_metros, duracion_segundos, puntos: [[lat, lon], …] }, total, datos: [{ folio, calle, colonia, ubicacion, nivel_agua, es_intransitable, hay_riesgo_personas_vehiculos, distancia_metros, vigente_hasta }], mensaje }`. Con `total = 0`, `mensaje` es «No hay encharcamientos reportados cerca del trayecto».

### 12.8 `GET /api/v1/publico/colonias/{colonia_id}/resumen` (HU-07.2 · público)

`{ colonia, sector, codigo_postal, activa, abiertos, abiertos_por_estado, reparados, tiempo_promedio_reparacion_dias, encharcamientos_activos, criterios, actualizado_en }`. `404` si la colonia no existe.

## 13. Cambios de la auditoría final (rama `fix/registro-y-rate-limit`, API 1.1.1)

| Ruta | Cambio |
|------|--------|
| `POST /auth/registro` | Nuevo `429 LIMITE_REGISTROS` con `Retry-After` (10 por hora por IP, `LIMITE_REGISTROS_POR_HORA_IP`). |
| `POST /auth/login` | `429 DEMASIADOS_INTENTOS` + `Retry-After` tras 5 fallos de la misma cuenta desde la misma IP, o 30 fallos desde una IP, en 15 min. El bloqueo de la cuenta en BD (desde cualquier IP) sube a 20 fallos. |
| `GET /auth/yo` · `POST /auth/renovar` · `POST /auth/cerrar-sesion` | También para `enlace_municipal` (antes `403`). |
| `GET /reportes/{folio}/fotos` | `nombre_original` real sólo para quien subió la foto, el autor y moderación; el resto recibe `fotografia-N.jpg/png`. |
| `POST /reportes/{folio}/fotos` | Las imágenes se guardan sin EXIF/GPS/XMP ni comentarios (se conserva la orientación). Una estructura inválida se rechaza: «La imagen está dañada o no es un JPG/PNG válido.». `tamano_bytes` es el del archivo limpio. |
| Cualquier ruta | `413 CUERPO_DEMASIADO_GRANDE` si el cuerpo supera `MAX_CUERPO_BYTES` (16 MB). |
| `POST /moderacion/reportes/fusionar` | `403 ROL_NO_AUTORIZADO` para coordinación (RN-05), ver §12.2. |
| `WS /ws/encharcamientos` | Cierre `1013` al superar `WS_MAX_CONEXIONES` o `WS_MAX_CONEXIONES_POR_IP`; el cliente recurre al sondeo HTTP. |
