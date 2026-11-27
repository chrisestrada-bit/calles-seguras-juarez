# Autoevaluación con la rúbrica — Calles Seguras Juárez (AEB-1055)

**Integrantes:** Chris Aaron Dionisio Estrada (23111598, `chrisestrada-bit`, 60 %) · Christian Daniel Salazar Mendoza (23111502, `Khrixgm`, 40 %)

> Copia de la última sección de `docs/REPORTE_BORRADOR.md` (§10), como pide la especificación. Mantener ambas sincronizadas.

Escala TecNM: Excelente 100 %, Notable 90 %, Bueno 80 %, Suficiente 70 %, Insuficiente 40 % (existe pero no cumple) o 0 %
(no existe). Puntos = peso × porcentaje. Cada nivel se propone a partir de la evidencia del repositorio y del despliegue en
producción al 26 de noviembre de 2026. Las rutas son relativas a la raíz del repositorio
<https://github.com/chrisestrada-bit/calles-seguras-juarez>.

| # | Criterio | Peso | Nivel autoasignado | % | Puntos | Evidencia (enlace) |
|---|---|---|---|---|---|---|
| 1 | Planeación y arquitectura | 6 | Excelente | 100 | 6.0 | 34 HU con criterios: [`docs/AUDITORIA_OBLIGATORIA.md`](AUDITORIA_OBLIGATORIA.md); diagramas: [`docs/arquitectura.png`](arquitectura.png), [`docs/modelo-er.png`](modelo-er.png), [`docs/arquitectura.md`](arquitectura.md) §1–2; gestión: issues #1–#22 en GitHub Issues (Figuras 1 y 2) |
| 2 | HTML, CSS y responsividad | 8 | Notable | 90 | 7.2 | Lighthouse `v1.1.1` (26-11-2026): 96 / 100 / 100 / 100 en móvil y escritorio (Figuras 14 y 15); estilos: `frontend/src/styles/`; vistas con sesión validadas con pruebas automatizadas y revisión del DOM, no con Lighthouse |
| 3 | Frontend en React | 14 | Notable | 90 | 12.6 | 21 rutas en `frontend/src/App.tsx`; `frontend/src/components/`; `hooks/useCargaDatos.ts`; formulario dinámico `pages/ReportCreatePage.tsx`; enrutamiento manual concentrado en `App.tsx` |
| 4 | Backend en FastAPI | 14 | Excelente | 100 | 14.0 | 74 operaciones en `backend/app/routers/`; capas `routers/ services/ models/ schemas/`; [`docs/api-contract.md`](api-contract.md); `/docs` en local; `backend/app/core/errores.py` |
| 5 | Base de datos | 12 | Excelente | 100 | 12.0 | `backend/app/models/` (1:N y cuatro N:M); 5 migraciones en `db/migrations/versions/`; `db/seed.py`; migración `0005` aplicada en Neon (Figura 5); triggers y `CHECK`: [`docs/arquitectura.md`](arquitectura.md) §5 |
| 6 | Seguridad e interoperabilidad | 10 | Excelente | 100 | 10.0 | `backend/app/core/security.py`, `dependencies.py`, `main.py` (CORS); E2E `frontend/e2e/04-roles-y-403.spec.ts`; [`docs/auditoria-final/05-seguridad-owasp.md`](auditoria-final/05-seguridad-owasp.md). A1, A3 y A4 resueltos en producción (cuentas semilla rotadas, `RUN_SEED=false`, EXIF/GPS limpiado, IP real tras el proxy); la cadena antigua del historial ya no da acceso |
| 7 | Contenedores y despliegue | 10 | Excelente | 100 | 10.0 | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`; <https://calles-seguras-juarez.vercel.app>; <https://calles-seguras-juarez-api.onrender.com/salud>; despliegue operativo y configuración en Vercel, Render y Neon (Figuras 6–12) |
| 8 | Calidad y DevOps | 8 | Bueno | 80 | 6.4 | `.github/workflows/ci.yml` (6 trabajos, CI #26 en verde, Figura 13); 212 pytest aprobadas; 19 PR (#23–#41); Conventional Commits. Insignia de CI en el `README.md`. Commits concentrados del 20 al 25 de noviembre |
| 9 | Declaración de uso de IA | 5 | Excelente | 100 | 5.0 | [`AI_USAGE.md`](../AI_USAGE.md) con los 7 puntos (herramientas por integrante incluido Copilot, modo de uso, archivos de contexto, bitácora en tabla, marcado en commits, estimación por carpeta y reflexión crítica con el caso A1); `CLAUDE.md`; 29 commits con `Assisted-by`/`Co-Authored-By` |
| 10 | Reporte técnico | 5 | Excelente | 100 | 5.0 | [`docs/REPORTE.pdf`](REPORTE.pdf) y [`docs/REPORTE.docx`](REPORTE.docx), generados de `docs/REPORTE_BORRADOR.md` |
| 11 | Demo y defensa (individual) — Chris Aaron Dionisio Estrada | 8 | Excelente | 100 | 8.0 | Demo del 26-11-2026; cuenta sólo en la boleta de Chris |
| 11 | Demo y defensa (individual) — Christian Daniel Salazar Mendoza | 8 | Excelente | 100 | 8.0 | Demo del 26-11-2026; cuenta sólo en la boleta de Christian |
| Extra | Puntos extra: pruebas del frontend (Vitest + Playwright), mapa interactivo (Leaflet), intercambio XML (exportación con XSD e importación de catálogos), WebSockets; Kubernetes sólo con manifiestos validados | +5 | Cumple | 100 | +5.0 | `frontend/src/**/*.test.tsx`, `frontend/e2e/`; `components/MapaReportes.tsx`; [`docs/esquemas/`](esquemas/); `backend/app/routers/ws.py`; `infra/k8s/` |
| | **Total por integrante** | **100** | | | **100.0** | 88.2 (criterios 1–10) + 8.0 (su criterio 11) + 5.0 extra = 101.2, con tope de 100 |

Cálculo de los criterios de equipo (1–10): 6.0 + 7.2 + 12.6 + 14.0 + 12.0 + 10.0 + 10.0 + 6.4 + 5.0 + 5.0 = **88.2**.
El criterio 11 es individual: aparece en dos filas porque cada integrante tiene el suyo, pero **cada boleta suma un solo
criterio 11 de 8.0 puntos** (nunca 8.0 + 8.0). Así, la calificación de cada integrante es 88.2 + 8.0 + 5.0 extra = **101.2**,
acotada al máximo de **100.0**. Si el criterio 6 se dejara en Notable (9.0) por la cadena que permanece en el historial antiguo
de Git, el total de equipo sería 87.2 y cada boleta sumaría 100.2, también acotada a 100.0. El docente puede ajustar la
calificación final conforme a la defensa en vivo, la tabla de contribución (60 % / 40 %), la coevaluación y el historial de Git.

### Párrafo final por integrante

**Chris Aaron Dionisio Estrada (60 %).** Mi aporte fue la codificación y la integración. Implementé y corregí los cambios en
colaboración directa con Claude Code y co-propuse soluciones con Christian. El criterio que más me costó fue **Calidad y DevOps**:
concentré los commits entre el 20 y el 25 de noviembre y no siempre marqué los commits asistidos. Además, aprendí que una
prueba en verde no basta si la documentación afirma algo que el código no cumple, como en el hallazgo A1. Lo haría distinto en
dos puntos: empezaría a hacer commits desde la aprobación de la propuesta, con el tablero actualizado cada semana, y crearía la
etiqueta `v1.0.0` al cerrar el alcance mínimo, antes de las fases opcionales. En la competencia de la materia me ubico en nivel
**Notable**. Puedo explicar el flujo completo de una petición, desde React hasta PostgreSQL, y desplegarlo en la nube, pero
todavía dependo de la IA para escribir con rapidez partes que debo dominar sin ella.

**Christian Daniel Salazar Mendoza (40 %).** Mi aporte fue la revisión de errores, las pruebas y la validación del
funcionamiento: revisé y fusioné 15 de los 19 pull requests y co-propuse soluciones. Al inicio también construí la base del
frontend con GitHub Copilot. El criterio que más me costó fue **HTML, CSS y responsividad**, porque varios defectos sólo
aparecían a 360 px o en vistas con sesión, que Lighthouse no audita, y había que reproducirlos a mano. Lo haría distinto en dos
puntos: dejaría por escrito cada defecto encontrado como *issue* con pasos para reproducirlo, para que mi trabajo de revisión
quede como evidencia en GitHub, y escribiría la prueba de regresión junto con el reporte del error. En la competencia de la
materia me ubico en nivel **Notable**. Puedo validar de punta a punta que una funcionalidad cumple sus reglas de negocio y
detectar dónde falla, y quiero fortalecer la implementación del lado del servidor.
