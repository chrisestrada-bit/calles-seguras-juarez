# 05 · Seguridad web: OWASP Top 10:2025 y perímetro tipo Cloudflare

| Categoría | Estado tras la auditoría | Evidencia |
|---|---|---|
| A01 Control de acceso roto | Sólido. Se corrigieron A2 (revocación de la sesión del enlace) y M3 (rechazo vía fusión) | `dependencies.py`, `fusion.py`, `04-matriz-roles.md` |
| A02 Configuración insegura | Se corrigió A1 (contraseña semilla). JWT exige 32+ caracteres en producción; `/docs` y `/openapi.json` apagados en producción; CORS con un solo origen | `config.py`, `main.py`, `seed.py` |
| A03 Cadena de suministro | `pip-audit` y `npm audit` en CI, ambos limpios. Las correcciones no agregaron dependencias (el saneador de imágenes no usa Pillow) | `.github/workflows/ci.yml` |
| A04 Fallas criptográficas | Argon2id, hash de relleno para igualar tiempos, HS256 con secreto de entorno, HSTS (Vercel; API en producción) | `security.py`, `main.py` |
| A05 Inyección | ORM parametrizado, `LIKE` escapado, `nextval` sobre un nombre fijo, XML con `resolve_entities=False`/`no_network`/sin DTD, CSV con prefijo contra fórmulas | `sqlutil.py`, `catalogos_xml.py`, `exportacion.py` |
| A06 Diseño inseguro | Reglas de negocio duplicadas en triggers (RN-03/05/06/07/10). RN-08 con candado asesor | migración `0001` |
| A07 Fallas de autenticación | Se corrigieron M1 (registro), M2 (bloqueo por cuenta+IP y límite por IP) y M4 (sesión deslizante real) | `services/auth.py`, `AuthContext.tsx` |
| A08 Integridad de software y datos | Historial *append-only*, idempotencia offline por `idempotency_key`, imágenes reescritas (sin datos tras EOI/IEND) | `imagenes.py` |
| A09 Registro y alertas | No se registran llaves (log de `httpx` silenciado). B4 pendiente: el log de acceso incluye la cadena de consulta | `main.py` |
| A10 Manejo excepcional | Errores uniformes en español; transacciones con *rollback* total (fusión, fotos); un 413 lleva cabeceras CORS | `errores.py`, `limite_cuerpo.py` |

## Perímetro y anti-bots (enfoque Cloudflare)

La API en Render pasa por el Cloudflare **de Render**, cuyas reglas no controla el proyecto. Por eso la defensa vive en la aplicación:

| Superficie | Control |
|---|---|
| Registro | 10 por hora por IP (`LIMITE_REGISTROS_POR_HORA_IP`) |
| Login | 5 fallos por cuenta+IP en 15 min; 30 fallos por IP en 15 min; respaldo en BD de 20 fallos por cuenta |
| Reportes (RN-08) | 10 por hora por cuenta, en BD, con 429 y `Retry-After` |
| Geocodificación | 30 por minuto por IP real (protege la cuota de LocationIQ; hay respaldo local) |
| WebSocket | 1000 conexiones globales, 20 por IP |
| Cuerpos | 16 MB máximo (413) y 3 fotos de 5 MB por persona y reporte |

**IP real.** `core/red.py` sólo confía en una cabecera declarada (`CLIENT_IP_HEADER` o `TRUSTED_PROXY_HOPS`). Si se confiara en `X-Forwarded-For` sin más, cualquiera podría saltarse todos los límites cambiando la cabecera.

**Limitación conocida.** Los limitadores viven en memoria y son por proceso. Con varias réplicas (Kubernetes) el tope efectivo se multiplica por el número de réplicas, y un reinicio los borra. El límite de RN-08 no tiene ese problema porque vive en la base de datos.

**Si el proyecto tuviera dominio propio en Cloudflare**, se recomienda además:
- Reglas de *rate limiting* en `/api/v1/auth/*`.
- Turnstile en el registro.
- *Bot Fight Mode*.
- `CLIENT_IP_HEADER=CF-Connecting-IP`, pero solo si el origen acepta tráfico exclusivamente desde Cloudflare.

## Cabeceras

| Origen | Cabeceras |
|---|---|
| Vercel (frontend) | `Content-Security-Policy` (`script-src 'self'`, sin inline; `connect-src` limitado a la API y su `wss`; `img-src` con teselas OSM, `data:` y `blob:`; `frame-ancestors 'none'`), `X-Frame-Options: DENY`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`; HSTS lo pone Vercel |
| API | `X-Content-Type-Options`, `Cache-Control: no-store`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, CSP `default-src 'none'` en respuestas JSON, HSTS en producción |
| Nginx (Docker) | Las mismas cabeceras salvo la CSP: el origen de la API depende de `BACKEND_PORT` |

**Token en `localStorage`.** Se mantiene; migrarlo a cookie `HttpOnly` cambiaría el contrato y obligaría a agregar protección CSRF. La CSP sin scripts inline reduce mucho el impacto de un XSS. Es la mejora recomendada para la siguiente versión.

## Privacidad (RN-04 / LFPDPPP)

- JSON público y WebSocket sin datos del autor (verificado en producción).
- Fotos sin EXIF, GPS, XMP ni comentarios, y sin el nombre original del archivo para el público (A3).
- `db/limpiar_fotos.py` limpia las fotos subidas antes de la corrección.
