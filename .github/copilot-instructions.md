# CLAUDE.md — Calles Seguras Juárez (AEB-1055)

## 1. Contexto del Proyecto y Stack Obligatorio
- **Cliente:** Asociación Civil "Calles Seguras Juárez" (Ciudad Juárez, Chihuahua, México).
- **Objetivo:** Plataforma web ciudadana para reportar baches y encharcamientos, dar seguimiento a reparaciones y consultar calles con riesgo de inundación antes de circular.
- **Stack estricto:**
  - `frontend/`: React + TypeScript (Vite), HTML semántico, hojas de estilo externas responsivas (desde 360 px hasta escritorio, WCAG 2.2 AA).
  - `backend/`: Python + FastAPI, Pydantic v2, SQLAlchemy 2.0, arquitectura en capas (`routers/`, `services/`, `models/`, `schemas/`).
  - `db/`: PostgreSQL + migraciones con Alembic + script de datos semilla (`seed`).
  - `infra/`: Dockerfiles para frontend y backend + `docker-compose.yml` funcional con un solo comando.
- **Idioma:** Todo el código visible al usuario, mensajes de error, validaciones, etiquetas y documentación deben estar en **español de México** (`RNF-08`).

## 2. Reglas de Negocio Inquebrantables (`RN-01` a `RN-10`)
- **RN-01 Territorio:** Solo se aceptan coordenadas/reportes dentro de los límites geográficos del municipio de Ciudad Juárez, Chihuahua (latitud `31.45` a `31.80`, longitud `-106.65` a `-106.25`). Rechazar puntos fuera de Juárez con mensaje claro.
- **RN-02 Hora Oficial:** Todas las marcas de tiempo (`created_at`, actualizaciones, confirmaciones, vigencia) se almacenan en UTC y se muestran/calculan en zona horaria `America/Ciudad_Juarez`.
- **RN-03 Folios Únicos:** Generados automáticamente por el servidor e inmutables: `BCH-YYYY-NNNNNN` para daños en pavimento y `ENC-YYYY-NNNNNN` para encharcamientos. Nunca se reutilizan.
- **RN-04 Privacidad (LFPDPPP):** Ninguna vista pública ni respuesta JSON pública puede exponer nombre, correo, ID personal ni datos del ciudadano que reportó.
- **RN-05 Ciclo de Vida de Baches (Máquina de Estados Estricta):**
  - `Recibido` -> `Validado` o `Rechazado` (Moderador)
  - `Validado` -> `Programado` o `En reparación` (Moderador, Coordinador)
  - `Programado` -> `En reparación` (Moderador, Coordinador)
  - `En reparación` -> `Reparado` (Moderador, Coordinador, requiere fecha de reparación >= fecha de reporte y <= hoy)
  - `Reparado` y `Rechazado` son estados finales. Cualquier transición inválida devuelve HTTP `400`/`422`.
- **RN-06 y HU-03.2 / HU-03.3 Vigencia de Encharcamientos:** Nacen en estado `Activo` sin esperar validación. Pasan a `Histórico` automáticamente tras **6 horas** sin confirmaciones (cada confirmación *"Sigue ahí"* de otro usuario reinicia las 6 h) o cuando **3 usuarios distintos** marcan *"Ya no hay agua"* en la vigencia actual. El autor no puede confirmar/desmentir su propio reporte. Los históricos siguen contando en métricas.
- **RN-07 Trazabilidad Inmutable:** Un reporte que salió de `Recibido` nunca se elimina (`DELETE` prohibido); solo puede pasar a `Rechazado` con motivo obligatorio. Todo cambio de estado se registra de forma permanente e inmutable en `historial_estados`.
- **RN-08 Anti-abuso:** Máximo **10 reportes por hora** por cuenta de usuario. Al superar el límite, rechazar con HTTP `429`.
- **RN-09 Visibilidad Pública:** Baches en `Recibido` se muestran al público con etiqueta `"Sin validar"`. Los reportes en `Rechazado` nunca se muestran en consultas públicas.
- **RN-10 Longevidad:** La fecha/hora original del reporte es inmutable para todos los roles. La longevidad de un bache se calcula en días desde `created_at` hasta `fecha_reparacion` (si está `Reparado`) o hasta el momento actual (si sigue abierto).

## 3. Reglas de Duplicados y Formularios Dinámicos
- **Duplicados:** Antes de crear un reporte, verificar si existe un bache abierto a **<= 30 metros** (`HU-02.3`) o un encharcamiento vigente a **<= 50 metros** (`HU-03.1`) usando fórmula de Haversine. Permitir confirmar el existente (1 confirmación por usuario) o forzar reporte nuevo si es un daño distinto.
- **Formulario Dinámico (`HU-02.2` y `HU-03.1`):**
  - `Bache`: exige `tamano` (`chico`, `mediano`, `grande`), `profundidad` y `carril_afectado`.
  - `Alcantarilla sin tapa`: fija `severidad = Alta` automáticamente en backend y exige booleano `esta_senalizado`.
  - `Encharcamiento`: exige `nivel_agua` (`a un lado de la calle`, `cubre un carril`, `a media llanta`, `intransitable`). Si es `intransitable`, exige campo obligatorio `hay_riesgo_personas_vehiculos`.
  - Descripción: máximo `500` caracteres validados tanto en frontend como en Pydantic.

## 4. Seguridad y Control de Acceso (`OWASP Top 10:2025`)
- Roles únicos por usuario: `visitante` (sin token), `ciudadano`, `moderador`, `coordinador`.
- Contraseñas hasheadas con `bcrypt` o `Argon2` (mínimo 8 caracteres, combinación de letras y números).
- Autenticación mediante JWT con expiración por inactividad documentada (30 minutos).
- Toda ruta protegida valida el rol en FastAPI y devuelve HTTP `403 Forbidden` si el rol no tiene permiso.
- CORS restringido estrictamente al origen del frontend (`FRONTEND_URL`).
- **PROHIBIDO** escribir secretos, contraseñas o API keys reales en código, logs o prompts. Usar siempre variables de entorno definidas en `.env.example`.

## 5. Flujo de Git y Uso de Skills
- **Conventional Commits:** Usar `feat:`, `fix:`, `docs:`, `test:`, `chore:` + pie de firma `Assisted-by: <Herramienta/Modelo>`.
- **Graphify:** Antes de leer múltiples archivos o integrar cambios del backend, consultar el grafo generado por `graphify` para minimizar consumo de contexto.
- **Frontend (`Impeccable` + `Vercel React Best Practices` + `Vercel Composition Patterns`):** Usar etiquetas HTML5 semánticas (`header`, `nav`, `main`, `section`, `footer`), atributos `label` vinculados, texto alternativo e íconos/texto además de color (`RNF-02`). Implementar estados `loading`, `error` y `empty` en toda vista conectada a la API.
- **Verificación (`Chrome DevTools MCP`):** Validar responsividad en viewport de `360px` y escritorio, accesibilidad Lighthouse >= 90 y respuestas HTTP `403` en red.
