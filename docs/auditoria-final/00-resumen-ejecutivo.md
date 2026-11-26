# Auditoría final — Resumen ejecutivo

**Proyecto:** Calles Seguras Juárez (AEB-1055) · **Base auditada:** tag `v1.1.0` (`f831eb4`) + rama `fix/registro-y-rate-limit` (`8d0bc32`) · **Fecha:** 2026-11-22 · **Modalidad:** primero sólo lectura; correcciones aplicadas con autorización en la misma rama.

## Estado de cierre: `v1.1.1` (2026-11-25)

- **Rama:** `chore/auditoria-final-v1-1`, sobre `main` `e7710ed` (merge del PR #38).
- **Commits del cierre:** `2e75cc0` (autocompletado de `/trayecto`, *cherry-pick* de `55333f1`), `7361526` (clima con `User-Agent`, *cherry-pick* de `4bae380`) y el commit de documentación de este cierre.
- **Etiqueta:** `v1.1.1` se crea sobre el merge de esta rama en `main`. No se usa `v1.1.0` porque ya está publicada en `f831eb4` (PR #32) y le siguen 19 commits en `main`; mover una etiqueta publicada rompería a quien ya la descargó.
- **Cambios de código del cierre:** autocompletado accesible en `/trayecto`, `User-Agent` de Open-Meteo y hora de actualización del clima, y un comentario con mojibake en `frontend/src/main.tsx`. No cambian contratos de API, reglas RN-01 a RN-10 ni configuración de seguridad.

| Verificación del cierre (local, Windows) | Resultado |
|---|---|
| `npm run lint` (`oxlint`) | 0 errores |
| `npx tsc --noEmit` | 0 errores |
| `npm test` (Vitest) | **64/64** en 12 archivos (incluye 2 pruebas nuevas de autocompletado en `TrayectoPage.test.tsx`) |
| `npm run build` | correcto |
| `pytest backend/tests` sin PostgreSQL | **106 aprobadas**, 0 fallos, 125 omitidas (requieren una base `_test`; Docker no estaba disponible) |
| `git grep` de secretos en los archivos modificados | sin secretos ni contraseñas reales |
| Playwright y Lighthouse | no se ejecutaron en este cierre: quedan para CI y para después de desplegar |

La lista de verificación operativa en Render está en `06-plan-de-cierre.md` («Antes de desplegar»).

## Veredicto (auditoría del 2026-11-22)

No hubo hallazgos bloqueantes en lo funcional: las reglas de negocio RN-01 a RN-10 se cumplen y están respaldadas por triggers de PostgreSQL. Las brechas encontradas eran de **seguridad, privacidad y sesión**: 4 de prioridad alta, 9 de prioridad media y 7 de prioridad baja. Todas las altas y medias se corrigieron con pruebas de regresión, salvo dos puntos que dependen del panel de Render (ver «Pendiente»).

| Indicador | Antes | Después |
|---|---|---|
| pytest (PostgreSQL 16 `_test`) | 196 aprobadas · 0 omitidas | **212 aprobadas** · 0 omitidas (+16 regresiones) |
| pytest con el `.env` local | 90 aprobadas · 106 omitidas (ver `02-pruebas-y-evidencia.md`) | igual (comportamiento esperado del `conftest`) |
| Vitest | 43/43 | **45/45** |
| Playwright (escritorio + 360 px) | 22/22 | **22/22** |
| `oxlint` · `tsc` · `vite build` · `docker compose config` · `validar_k8s.py` | OK | OK |
| `npm audit` / `pip-audit` | 0 / 0 | sin dependencias nuevas |
| Lighthouse producción (accesibilidad · buenas prácticas · SEO) | 100 · 100 · 100 | por medir tras desplegar |

## Hallazgos de prioridad alta (todos corregidos en código)

1. **A1** — La contraseña semilla `Juarez2026` estaba publicada como valor por omisión, y `AUDITORIA_OBLIGATORIA.md` afirmaba lo contrario.
2. **A2** — La cuenta de enlace municipal no podía cerrar sesión ni renovar su token (respondía 403), así que su token no se podía revocar.
3. **A3** — Las fotos públicas conservaban EXIF/GPS y mostraban el nombre original del archivo (RN-04).
4. **A4** — El límite de geocodificación tomaba la IP del proxy: todas las personas compartían una sola cubeta.

## Pendiente (acción del equipo, fuera del repositorio)

- **Rotar o desactivar** las cuentas `@ejemplo.mx` en producción si se sembraron con `Juarez2026`. La auditoría no inició sesión en producción.
- En Render: confirmar **qué cabecera trae la IP real** y fijar `CLIENT_IP_HEADER` o `TRUSTED_PROXY_HOPS`. Confirmar también si hay **disco persistente** para `UPLOADS_DIR` (M8).
- Desplegar y repetir las lecturas de `02-pruebas-y-evidencia.md` §4 (cabeceras CSP en Vercel y Lighthouse).

## Índice

| Archivo | Contenido |
|---|---|
| `01-inventario-git.md` | Ramas, tags, migraciones, versiones, secretos y despliegue |
| `02-pruebas-y-evidencia.md` | Comandos, resultados y explicación de las 106 omitidas |
| `03-hallazgos.md` | Hallazgos con evidencia, corrección y prueba de regresión |
| `04-matriz-roles.md` | Matriz de cuentas y roles (antes y después) |
| `05-seguridad-owasp.md` | Revisión OWASP Top 10:2025 y perímetro tipo Cloudflare |
| `06-plan-de-cierre.md` | Lo aplicado, lo pendiente y la lista de verificación de despliegue |
| `evidencia/sondeo_auditoria.py` | Script de sondeos que confirmó los hallazgos (sólo contra una BD `_test`) |
