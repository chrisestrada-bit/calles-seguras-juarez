# 04 · Matriz de cuentas y roles

Cuentas de prueba sembradas (contraseña = `SEED_PASSWORD` del entorno; **nunca** se documenta):
`coordinador@ejemplo.mx`, `moderador@ejemplo.mx`, `moderador2@ejemplo.mx`, `enlace@ejemplo.mx` (rol `enlace_municipal`),
`ciudadano01@ejemplo.mx` … `ciudadano12@ejemplo.mx`.

Evidencia: `requiere_rol` en `backend/app/core/dependencies.py`, pruebas `test_api.py`, `test_fase3.py`,
`test_auditoria_final.py` y E2E `04-roles-y-403.spec.ts`. No se inició sesión en producción con estas cuentas.

| Recurso | Visitante | Ciudadano | Moderador | Coordinador | Enlace municipal |
|---|---|---|---|---|---|
| Consulta pública, detalle, historial, mapa, indicadores públicos, trayecto | ✅ | ✅ | ✅ | ✅ | ✅ |
| Crear reporte · confirmar · editar el propio en `Recibido` | 401 | ✅ (editar ajeno → 403) | ✅ | ✅ | 403 |
| `/auth/yo` · `/auth/renovar` · `/auth/cerrar-sesion` | 401 | ✅ | ✅ | ✅ | **403 → ✅ (A2)** |
| Notificaciones · colonias favoritas | 401 | ✅ | ✅ | ✅ | 403 (sin uso para el rol) |
| Fotos de un reporte `Recibido` | 403 | autor ✅ / otros 403 | ✅ | ✅ | 403 |
| `nombre_original` de una foto | — | quien la subió y el autor | ✅ | ✅ | — **(A3)** |
| Cola y detalle de moderación | 401 | 403 | ✅ | ✅ | 403 |
| `Recibido → Validado / Rechazado` | 401 | 403 | ✅ | 403 | 403 |
| `Validado → Programado / En reparación` · `Programado → En reparación` · `En reparación → Reparado` | 401 | 403 | ✅ | ✅ | sólo baches de sus cuadrillas, desde `Programado` |
| Fusión de duplicados | 401 | 403 | ✅ | **✅ → 403 (M3)** | 403 |
| Usuarios, sectores, colonias, catálogos, importación XML, cuadrillas, puntos recurrentes | 401 | 403 | 403 | ✅ | 403 |
| `/enlace/reportes` · avance | 401 | 403 | 403 | 403 | ✅ (bache ajeno → 403) |
| `DELETE /reportes/{folio}` | 405 | 405 | 405 | 405 | 405 |

## Controles transversales verificados

- **401 vs 403:** token ausente, inválido, vencido o revocado (`token_version`) → 401; cuenta suspendida → 403 `CUENTA_SUSPENDIDA`; rol sin permiso → 403 `ROL_NO_AUTORIZADO`.
- **Cambio de rol o suspensión** incrementa `token_version`: la sesión anterior queda revocada al instante.
- **IDOR:** edición sólo del autor (`SIN_PERMISO`), fotos con `exigir_acceso`, enlace limitado a `reporte_del_enlace`, reportes `Rechazado` responden 404 al público (no revelan existencia).
- **Asignación masiva:** todos los esquemas de entrada heredan `Esquema` (`extra="forbid"`); el rol de un registro siempre es `ciudadano`; folio, tipo, autor, fecha y ubicación son inmutables también por trigger.
- **Aislamiento de datos:** respuestas públicas y WebSocket sin autor; moderación sólo ve el UUID del autor y su conteo de 24 h.
