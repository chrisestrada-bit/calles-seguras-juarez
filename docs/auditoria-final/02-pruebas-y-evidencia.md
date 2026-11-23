# 02 · Pruebas ejecutadas y evidencia

Todas las corridas de integración usaron un **PostgreSQL 16 desechable** (contenedor efímero en el puerto 55432, base `calles_seguras_test`), nunca la base de desarrollo ni la de producción.

## 1. Las 106 pruebas omitidas de pytest

Con el `.env` local, `pytest` reporta **90 aprobadas y 106 omitidas**. No es un fallo de la aplicación:

- `DATABASE_URL` en `.env` apunta a `…@db:5432/calles_seguras`. El host `db` solo se resuelve dentro de la red de Docker y el nombre de la base no termina en `_test`.
- `backend/tests/conftest.py` (fixture `client`) omite toda la integración si la base no termina en `_test` o si PostgreSQL no responde. Es una protección deliberada para no ensuciar datos reales.
- Las 90 que sí corren son unitarias y no tocan la base de datos.
- En CI no se pueden colar: el job `backend` falla si `pytest.log` contiene `skipped`.

Para ejecutarlas localmente:

```bash
docker run --rm -d --name csj-pg-test -e POSTGRES_DB=calles_seguras_test -e POSTGRES_USER=csj_ci \
  -e POSTGRES_PASSWORD=csj_ci_local -p 127.0.0.1:55432:5432 postgres:16-alpine
export DATABASE_URL=postgresql+psycopg://csj_ci:csj_ci_local@127.0.0.1:55432/calles_seguras_test \
       APP_ENV=test JWT_SECRET_KEY=<clave-de-pruebas-de-32+-caracteres> SEED_PASSWORD=<la-que-elijas>
alembic -c db/alembic.ini upgrade head && python db/seed.py
python -m pytest backend/tests -q -rs
```

## 2. Resultados

| Suite | Antes de corregir | Después de corregir |
|---|---|---|
| `pytest` (BD `_test`) | 196 aprobadas · 0 omitidas | **212 aprobadas** · 0 omitidas (`test_auditoria_final.py`: 16 nuevas) |
| Vitest | 43/43 | **45/45** (`AuthContext.test.tsx`: sesión deslizante) |
| Playwright (aislado: API 18000, web 14173, BD `_test`) | 22/22 | **22/22** |
| `oxlint` / `tsc` (app, node, e2e) | 0 errores | 0 errores |
| `vite build` | OK | OK |
| `npm audit --audit-level=high` / `pip-audit` | 0 / 0 | sin dependencias nuevas |
| `docker compose config -q` / `infra/validar_k8s.py` | OK | OK |

## 3. Sondeos que confirmaron los hallazgos

`evidencia/sondeo_auditoria.py` se ejecutó contra la base `_test` antes de corregir. Hoy cada sondeo tiene su prueba de regresión en `backend/tests/test_auditoria_final.py`:

| Sondeo | Resultado antes | Prueba de regresión |
|---|---|---|
| S1 | Enlace: `cerrar-sesion`, `renovar` y `yo` → 403; el token seguía válido (200 en `/enlace/reportes`) | `test_enlace_municipal_consulta_renueva_y_cierra_sesion` |
| S2 | 25 registros seguidos desde una IP → todos 201 | `test_registro_limitado_por_ip` |
| S3 | 5 fallos de un tercero → la víctima recibe 429 por 900 s | `test_un_tercero_no_puede_bloquear_la_cuenta_de_otra_persona` |
| S4 | Coordinador: transición directa → 403, pero vía fusión → 200 (rechazo) | `test_coordinacion_no_rechaza_via_fusion` |
| S5 | Un visitante descarga la foto con EXIF intacto y ve `Juan_Perez_Calle_Falsa_123.jpg` | `test_foto_publica_sin_exif_y_sin_nombre_original` y 4 pruebas unitarias del saneador |
| S6 | WebSocket sin `Origin` aceptado y sin tope | `test_websocket_respeta_el_tope_de_conexiones_por_ip` |
| S7 | API sin `X-Frame-Options`, CSP ni `Referrer-Policy` | `test_cabeceras_de_seguridad_de_la_api` |
| S8 | Limitador de geocodificación por `request.client.host` | `test_ip_cliente_solo_confia_en_cabeceras_declaradas` |
| S9 | `seq_folio_*` con `MAXVALUE 999999` | — (B1, documentado) |

Pruebas adicionales: `test_cuerpo_demasiado_grande_responde_413_sin_procesarlo` (M7) y `test_limite_de_fallos_por_ip_frena_el_relleno_de_credenciales` (M2).

**Volví a correr el script después de corregir** (con `LIMITE_REGISTROS_POR_HORA_IP=1000`). El script es heurístico y fue escrito para el estado anterior: la evidencia válida son las pruebas de regresión de la tabla anterior.

| Sondeo | Salida | Lectura correcta |
|---|---|---|
| S1 | no reproducido (logout 204, token anterior → 401) | Corregido |
| S2 | «confirmado» | Solo porque el límite se elevó a 1000 para la corrida. Con el valor por omisión (10), el registro 11 → 429 |
| S3 | «confirmado» | Atacante y víctima comparten la IP `testclient`, así que el bloqueo por cuenta+IP aplica a los dos. Desde otra IP la víctima entra (regresión) |
| S4 | no reproducido (fusión por coordinación → 403) | Corregido |
| S5 | no reproducido | La JPEG artesanal del script no tiene estructura válida y ahora se rechaza (422). Con una imagen válida, el EXIF se elimina (regresión) |
| S6 | «confirmado» | `Origin` sigue siendo opcional a propósito; el control real es el tope de conexiones (regresión con cierre 1013) |
| S7 | Solo falta HSTS | HSTS se envía únicamente con `APP_ENV=production` |
| S8 | «confirmado» | Sin `CLIENT_IP_HEADER`/`TRUSTED_PROXY_HOPS`, `X-Forwarded-For` se ignora: no se puede falsificar. Es el comportamiento esperado |
| S9 | confirmado | B1: documentado, sin cambios |

## 4. Lecturas seguras en producción (solo GET/OPTIONS, sin sesión)

| Verificación | Resultado (2026-11-22) |
|---|---|
| `GET /salud` | 200 (arranque en frío de 47 s) |
| `/docs`, `/openapi.json` | 404 (deshabilitados en producción) |
| Preflight CORS con `Origin: https://evil.example` | 400 sin `Access-Control-Allow-Origin` |
| Preflight CORS desde Vercel | 200 con el origen exacto |
| Rutas protegidas sin token (`/auth/yo`, `/moderacion/reportes`, `/admin/usuarios`, `/enlace/reportes`, `/cuadrillas`) | 401 |
| Token basura | 401 |
| `DELETE /reportes/{folio}` | 405 (RN-07) |
| `GET /reportes?estado=Rechazado` | 422 (RN-09) |
| JSON público (lista y detalle) | Sin correo, nombre, `usuario_id` ni autor (RN-04) |
| Fechas | `-07:00`, es decir `America/Ciudad_Juarez` en noviembre (RN-02) |
| Bundle JS | Sin llaves de LocationIQ ni secretos. El token vive en `localStorage` (ver M5) |
| Lighthouse móvil y escritorio | Accesibilidad 100 · Buenas prácticas 100 · SEO 100 |

**Repetir tras desplegar:** las cabeceras de Vercel (`curl -sD - -o /dev/null https://calles-seguras-juarez.vercel.app/`), las cabeceras de la API (`X-Frame-Options`, CSP en JSON, HSTS) y Lighthouse.

## 5. Validación de la CSP antes de desplegar

Para probar la CSP serví la build de producción con las cabeceras de `vercel.json` (solo cambié `connect-src` para que apuntara a la API local) y la recorrí en Chrome:

- La lista cargó con datos y el WebSocket quedó «En vivo».
- El tema oscuro se aplicó antes del primer pintado mediante `/tema-inicial.js`.
- En el mapa cargaron las 12 teselas de OpenStreetMap, con marcadores y clusters.
- El service worker quedó activo.
- **Sin violaciones de CSP en consola.**

El saneador de imágenes se probó además con 38 JPG/PNG reales del equipo: quitó EXIF en las 10 que lo traían, dejó idénticas byte por byte las 28 sin metadatos, y la JPEG limpia decodificó correctamente en Chrome (2736×1539).
