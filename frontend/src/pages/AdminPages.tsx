import { useEffect, useState, type FormEvent } from 'react';
import { cargarMotivos } from '../services/catalogos';
import { FusionarDialog } from '../components/FusionarDialog';
import { api, ApiError } from '../services/api';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { antiguedadTexto, fechaHora } from '../utils/formato';
import type { MotivoRechazo, AuditoriaItem, EstadoReporte, IndicadorSector, IndicadoresLongevidad, IndicadoresResumen, ReporteModeracionDetalle, ReporteModeracionResumen, RespuestaPaginada, TransicionResponse } from '../types/api';
import { Guard, ErrorMessage, PageIntro, Pagination } from '../components/AdminShared';
import { Icon, type IconName } from '../components/Icon';
import { BlockSkeleton, EmptyState, Notice, SeverityBadge, StatusBadge, TableSkeleton, TypeBadge } from '../components/ui';

const PAGE_SIZE = 10;
const formatDate = fechaHora; // RN-02: siempre en hora de Ciudad Juárez
const makeQuery = (values: Record<string, string | number | undefined>) => Object.entries(values).filter(([, value]) => value !== undefined && value !== '').map(([key, value]) => `${key}=${encodeURIComponent(value as string | number)}`).join('&');

function TransitionForm({ report, onComplete }: { report: ReporteModeracionResumen; onComplete: (response: TransicionResponse) => void }) {
  const [next, setNext] = useState<EstadoReporte>(report.transiciones_disponibles[0] ?? report.estado); const [reason, setReason] = useState(''); const [motivoId, setMotivoId] = useState(''); const [motivos, setMotivos] = useState<MotivoRechazo[] | null>(null); const [motivosError, setMotivosError] = useState('');
  useEffect(() => { if (next !== 'Rechazado' || motivos) return; let vivo = true; cargarMotivos().then((m) => { if (vivo) setMotivos(m); }).catch(() => { if (vivo) setMotivosError('No pudimos cargar los motivos de rechazo.'); }); return () => { vivo = false; }; }, [next, motivos]); const [scheduled, setScheduled] = useState(''); const [repaired, setRepaired] = useState(''); const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  if (!report.transiciones_disponibles.length) return <p className="field-help">Sin transiciones disponibles para tu rol.</p>;
  const submit = async (event: FormEvent) => { event.preventDefault(); setError(''); if (next === 'Rechazado' && !motivoId) { setError('Elige el motivo del rechazo del catálogo.'); return; } setBusy(true); try { const response = await api.post<TransicionResponse>(`/api/v1/moderacion/reportes/${encodeURIComponent(report.folio)}/transiciones`, { estado_nuevo: next, motivo_id: next === 'Rechazado' ? Number(motivoId) : null, motivo: next === 'Rechazado' && reason.trim() ? reason.trim() : null, fecha_programada: scheduled || null, fecha_reparacion: repaired || null }); onComplete(response); } catch (exception) { setError(exception instanceof ApiError ? exception.message : 'No fue posible actualizar el reporte.'); } finally { setBusy(false); } };
  return (
    <form className="admin-action" onSubmit={submit}>
      <label>Acción<select value={next} onChange={(event) => setNext(event.target.value as EstadoReporte)}>{report.transiciones_disponibles.map((state) => <option key={state}>{state}</option>)}</select></label>
      {next === 'Rechazado' && <><label>Motivo del catálogo<select required value={motivoId} onChange={(event) => setMotivoId(event.target.value)}><option value="">{motivos ? 'Elige un motivo' : 'Cargando motivos…'}</option>{(motivos ?? []).map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}</select></label>{motivosError && <ErrorMessage message={motivosError} />}<label>Detalle (opcional)<textarea maxLength={300} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Agrega contexto para la persona que reportó" /></label></>}
      {next === 'Programado' && <label>Fecha programada<input type="date" value={scheduled} onChange={(event) => setScheduled(event.target.value)} /></label>}
      {next === 'Reparado' && <label>Fecha de reparación<input required type="date" value={repaired} onChange={(event) => setRepaired(event.target.value)} /></label>}
      {error && <ErrorMessage message={error} />}
      <button className={`button ${next === 'Rechazado' ? 'button--danger' : 'button--primary'}`} disabled={busy} type="submit">{busy ? 'Guardando…' : 'Aplicar acción'}</button>
      {report.estado === 'Recibido' && report.tipo_dano !== 'Encharcamiento' && <FusionarDialog folioSecundario={report.folio} onDone={(r) => onComplete({ folio: r.folio_secundario, estado_anterior: 'Recibido', estado: 'Rechazado', fecha_reparacion: null, longevidad_dias: null, registrado_en: r.registrado_en, mensaje: `${r.mensaje} Se sumaron ${r.confirmaciones_transferidas} confirmación(es) al principal.` })} />}
    </form>
  );
}

function useModerationQueue(state: string, page: number, refresh: number) {
  const result = useCargaDatos<RespuestaPaginada<ReporteModeracionResumen>>(`/api/v1/moderacion/reportes?${makeQuery({ estado: state, pagina: page, por_pagina: PAGE_SIZE })}#${refresh}`, obtenerJson, 'No fue posible cargar los reportes.');
  return { data: result.datos?.datos ?? [], total: result.datos?.paginacion.total_paginas || 1, status: result.estado, error: result.error };
}

function QueueTable({ data, onComplete }: { data: ReporteModeracionResumen[]; onComplete: (folio: string, response: TransicionResponse) => void }) {
  return (
    <div className="admin-table-wrap">
      <table className="admin-table">
        <caption className="visually-hidden">Reportes en la cola administrativa</caption>
        <thead><tr><th scope="col">Folio</th><th scope="col">Tipo y ubicación</th><th scope="col">Estado</th><th scope="col">Reportado</th><th scope="col">Acción</th></tr></thead>
        <tbody>
          {data.map((report) => (
            <tr key={report.folio}>
              <td><a className="tabular" href={`/reportes/${encodeURIComponent(report.folio)}`}>{report.folio}</a><div className="cell-sub"><SeverityBadge severidad={report.severidad} /></div></td>
              <td><TypeBadge tipo={report.tipo_dano} /><div className="cell-main">{report.calle}</div><small>{report.colonia.nombre}</small></td>
              <td><StatusBadge estado={report.estado} /><div className="cell-sub"><small><span className="tabular">{report.confirmaciones}</span> confirmaciones</small></div></td>
              <td className="tabular">{formatDate(report.created_at)}</td>
              <td><TransitionForm report={report} onComplete={(response) => onComplete(report.folio, response)} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function QueueView({ result, page, setPage, emptyText, loadingText, onComplete }: { result: ReturnType<typeof useModerationQueue>; page: number; setPage: (n: number) => void; emptyText: string; loadingText: string; onComplete: (folio: string, response: TransicionResponse) => void }) {
  if (result.status === 'cargando') return <TableSkeleton label={loadingText} />;
  if (result.status === 'error') return <ErrorMessage message={result.error} />;
  if (!result.data.length) return <EmptyState art="inbox" title={emptyText}>Cuando lleguen reportes a esta bandeja aparecerán aquí. Prueba con otro estado.</EmptyState>;
  return <><QueueTable data={result.data} onComplete={onComplete} /><Pagination page={page} total={result.total} onChange={setPage} /></>;
}

export function ModerationPage() {
  const [state, setState] = useState('Recibido'); const [page, setPage] = useState(1); const [refresh, setRefresh] = useState(0); const [message, setMessage] = useState(''); const result = useModerationQueue(state, page, refresh);
  return (
    <Guard roles={['moderador', 'coordinador']}>
      <main className="admin-page">
        <PageIntro title="Panel de moderación">Valida los reportes recibidos o recházalos con un motivo que quedará en la trazabilidad.</PageIntro>
        <section className="filter-bar filter-bar--inline" aria-label="Filtro de cola">
          <div className="field"><label htmlFor="moderation-state">Estado de la cola</label><select id="moderation-state" value={state} onChange={(event) => { setState(event.target.value); setPage(1); }}><option>Recibido</option><option>Validado</option><option>Rechazado</option><option>Programado</option><option>En reparación</option><option>Reparado</option></select></div>
        </section>
        {message && <div className="form-success" role="status">{message}</div>}
        <QueueView result={result} page={page} setPage={setPage} emptyText="No hay reportes en esta cola." loadingText="Cargando reportes…" onComplete={(folio, response) => { setMessage(`${folio}: ${response.mensaje}`); setRefresh((value) => value + 1); }} />
      </main>
    </Guard>
  );
}

export function CoordinationPage() {
  const [state, setState] = useState('Validado'); const [page, setPage] = useState(1); const [refresh, setRefresh] = useState(0); const [message, setMessage] = useState(''); const result = useModerationQueue(state, page, refresh);
  return (
    <Guard roles={['coordinador']}>
      <main className="admin-page">
        <PageIntro title="Panel de coordinación">Da seguimiento a reportes validados, programa trabajos y registra el avance operativo por folio.</PageIntro>
        <Notice tone="info"><strong>Seguimiento:</strong> cada cambio de estado queda registrado con su fecha y responsable en el historial del reporte, que no se puede modificar.</Notice>
        <section className="filter-bar filter-bar--inline" aria-label="Filtro de bandeja">
          <div className="field"><label htmlFor="coordination-state">Bandeja operativa</label><select id="coordination-state" value={state} onChange={(event) => { setState(event.target.value); setPage(1); }}><option>Validado</option><option>Programado</option><option>En reparación</option><option>Reparado</option></select></div>
        </section>
        {message && <div className="form-success" role="status">{message}</div>}
        <QueueView result={result} page={page} setPage={setPage} emptyText="No hay reportes en esta bandeja." loadingText="Cargando seguimiento…" onComplete={(folio, response) => { setMessage(`${folio}: ${response.mensaje}`); setRefresh((value) => value + 1); }} />
      </main>
    </Guard>
  );
}

const KPI: Array<{ key: string; label: string; icon: IconName; tone: string }> = [
  { key: 'pav', label: 'Reportes de pavimento', icon: 'pothole', tone: 'road' },
  { key: 'enc', label: 'Encharcamientos', icon: 'water', tone: 'water' },
  { key: 'act', label: 'Activos ahora', icon: 'alert', tone: 'water' },
  { key: 'rep', label: 'Reparación promedio', icon: 'wrench', tone: 'success' },
];


/* Gráfica de barras agrupadas por sector. Decorativa para lectores de pantalla: la tabla siguiente contiene los mismos datos. */
const SERIES: Array<{ key: 'baches_abiertos' | 'reparados' | 'encharcamientos_activos'; label: string; tone: string }> = [
  { key: 'baches_abiertos', label: 'Baches abiertos', tone: 'road' },
  { key: 'encharcamientos_activos', label: 'Encharcamientos activos', tone: 'water' },
  { key: 'reparados', label: 'Reparados', tone: 'success' },
];
function SectorChart({ items }: { items: IndicadorSector[] }) {
  const max = Math.max(1, ...items.flatMap((item) => SERIES.map((serie) => item[serie.key])));
  return (
    <figure className="bar-chart" aria-hidden="true">
      <ul className="chart-legend">{SERIES.map((serie) => <li key={serie.key} className={`chart-legend__item chart-legend__item--${serie.tone}`}><span className="chart-swatch" />{serie.label}</li>)}</ul>
      <div className="bar-chart__rows">
        {items.map((item) => (
          <div className="bar-chart__group" key={item.sector.id}>
            <p className="bar-chart__label">{item.sector.nombre}</p>
            <div className="bar-chart__bars">
              {SERIES.map((serie) => (
                <div className={`bar-chart__bar bar-chart__bar--${serie.tone}`} key={serie.key} data-tip={`${serie.label}: ${item[serie.key]}`}>
                  <span className="bar-chart__fill" style={{ inlineSize: `${(item[serie.key] / max) * 100}%` }} />
                  <span className="bar-chart__value tabular">{item[serie.key]}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </figure>
  );
}

interface DatosTablero { summary: IndicadoresResumen; sectors: IndicadorSector[]; longevity: IndicadoresLongevidad }

/** Clave: `desde|hasta|sector`. Definida fuera del componente para que sea estable (useCargaDatos). */
async function cargarTablero(clave: string): Promise<DatosTablero> {
  const [desde, hasta, sector] = clave.split('|');
  const [summary, zones, longevity] = await Promise.all([
    api.get<IndicadoresResumen>(`/api/v1/indicadores/resumen?${makeQuery({ desde, hasta, sector_id: sector })}`),
    api.get<{ datos: IndicadorSector[] }>(`/api/v1/indicadores/sectores?${makeQuery({ desde, hasta })}`),
    api.get<IndicadoresLongevidad>(`/api/v1/indicadores/longevidad?${makeQuery({ sector_id: sector, limite: 10 })}`),
  ]);
  return { summary, sectors: zones.datos, longevity };
}

export function DashboardPage() {
  const [from, setFrom] = useState(''); const [to, setTo] = useState(''); const [sector, setSector] = useState('');
  const tablero = useCargaDatos(`${from}|${to}|${sector}`, cargarTablero, 'No fue posible cargar las métricas.');
  const status = tablero.estado; const error = tablero.error;
  const summary = tablero.datos?.summary ?? null; const longest = tablero.datos?.longevity.datos ?? [];
  // Las zonas del filtro salen del catálogo (estable): no se vacían mientras se recargan las métricas.
  const zonas = useCargaDatos<{ datos: Array<{ id: number; nombre: string }> }>('/api/v1/catalogos/sectores', obtenerJson).datos?.datos ?? [];
  const sectors = tablero.datos?.sectors ?? [];
  const valores = summary ? { pav: summary.pavimento.total, enc: summary.encharcamientos.total, act: summary.encharcamientos.activos, rep: summary.pavimento.tiempo_promedio_reparacion_dias.toFixed(1) } : null;
  const totalEstados = summary ? Object.values(summary.pavimento.por_estado).reduce((a, b) => a + b, 0) : 0;
  return (
    <Guard roles={['moderador', 'coordinador']}>
      <main className="admin-page">
        <PageIntro title="Dashboard estadístico">Consulta el volumen de reportes y el desempeño operativo por periodo.</PageIntro>
        <section className="filter-bar" aria-label="Filtros de periodo">
          <div className="filters filters--three">
            <div className="field"><label htmlFor="dash-desde">Desde</label><input id="dash-desde" type="date" value={from} onChange={(event) => setFrom(event.target.value)} /></div>
            <div className="field"><label htmlFor="dash-hasta">Hasta</label><input id="dash-hasta" type="date" value={to} onChange={(event) => setTo(event.target.value)} /></div>
            <div className="field"><label htmlFor="dash-zona">Zona</label><select id="dash-zona" value={sector} onChange={(event) => setSector(event.target.value)}><option value="">Todas las zonas</option>{zonas.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></div>
          </div>
        </section>
        {status === 'cargando' && <div className="kpi-grid">{KPI.map((k) => <div className="kpi-card" key={k.key}><BlockSkeleton label="Cargando indicadores…" lines={1} /></div>)}</div>}
        {status === 'error' && <ErrorMessage message={error} />}
        {status === 'listo' && summary && valores && (
          <>
            <section className="kpi-grid" aria-label="Métricas principales">
              {KPI.map((k) => (
                <article className={`kpi-card kpi-card--${k.tone}`} key={k.key}>
                  <span className="kpi-card__label"><Icon name={k.icon} size={18} />{k.label}</span>
                  <strong className="tabular">{valores[k.key as keyof typeof valores]}{k.key === 'rep' && <small> días</small>}</strong>
                </article>
              ))}
            </section>
            <section className="panel" aria-labelledby="desglose-titulo">
              <h2 id="desglose-titulo">Desglose por estado</h2>
              <dl className="metric-list">
                {Object.entries(summary.pavimento.por_estado).map(([key, value]) => (
                  <div key={key}>
                    <dt><StatusBadge estado={key} /></dt>
                    <span className="metric-list__bar" aria-hidden="true"><span style={{ inlineSize: `${totalEstados ? (value / totalEstados) * 100 : 0}%` }} /></span>
                    <dd className="tabular">{value}<small>{totalEstados ? ` · ${Math.round((value / totalEstados) * 100)} %` : ''}</small></dd>
                  </div>
                ))}
              </dl>
            </section>
            <section className="panel" aria-labelledby="tipo-titulo">
              <h2 id="tipo-titulo">Desglose por tipo de daño</h2>
              <dl className="metric-list">
                {([...Object.entries(summary.pavimento.por_tipo), ['Encharcamiento', summary.encharcamientos.total]] as Array<[string, number]>).map(([key, value]) => {
                  const total = summary.pavimento.total + summary.encharcamientos.total;
                  return (
                    <div key={key}>
                      <dt><TypeBadge tipo={key as ReporteModeracionResumen['tipo_dano']} /></dt>
                      <span className="metric-list__bar" aria-hidden="true"><span style={{ inlineSize: `${total ? (value / total) * 100 : 0}%` }} /></span>
                      <dd className="tabular">{value}<small>{total ? ` · ${Math.round((value / total) * 100)} %` : ''}</small></dd>
                    </div>
                  );
                })}
              </dl>
              <p className="field-help">Encharcamientos intransitables en el periodo: <strong className="tabular">{summary.encharcamientos.intransitables}</strong>.</p>
            </section>
            <section className="panel" aria-labelledby="longevidad-titulo">
              <h2 id="longevidad-titulo">Longevidad de baches abiertos</h2>
              <p>Promedio de días sin reparar: <strong className="tabular">{summary.pavimento.longevidad_promedio_abiertos_dias.toFixed(1)}</strong> días. Los más antiguos:</p>
              {longest.length ? (
                <div className="admin-table-wrap admin-table-wrap--flat">
                  <table className="admin-table admin-table--compact">
                    <caption className="visually-hidden">Baches y alcantarillas abiertos con más días sin reparar</caption>
                    <thead><tr><th scope="col">Folio</th><th scope="col">Ubicación</th><th scope="col">Estado</th><th scope="col" className="num">Longevidad</th></tr></thead>
                    <tbody>{longest.map((item) => <tr key={item.folio}><th scope="row"><a className="tabular" href={`/reportes/${encodeURIComponent(item.folio)}`}>{item.folio}</a></th><td>{item.calle}<br /><small>{item.colonia.nombre}</small></td><td><StatusBadge estado={item.estado} /></td><td className="num tabular">{antiguedadTexto(item.longevidad_dias, item.created_at)}</td></tr>)}</tbody>
                  </table>
                </div>
              ) : <EmptyState art="road" title="Sin baches abiertos">No hay baches ni alcantarillas pendientes de reparar.</EmptyState>}
            </section>
            <section className="panel" aria-labelledby="zona-desempeno-titulo">
              <h2 id="zona-desempeno-titulo">Desempeño por zona</h2>
              {sectors.length ? (
                <>
                <SectorChart items={sectors.filter((item) => !sector || String(item.sector.id) === sector)} />
                <div className="admin-table-wrap admin-table-wrap--flat">
                  <table className="admin-table admin-table--compact">
                    <thead><tr><th scope="col">Sector</th><th scope="col" className="num">Baches abiertos</th><th scope="col" className="num">Reparados</th><th scope="col" className="num">Encharcamientos activos</th></tr></thead>
                    <tbody>{sectors.filter((item) => !sector || String(item.sector.id) === sector).map((item) => <tr key={item.sector.id}><th scope="row">{item.sector.nombre}</th><td className="num tabular">{item.baches_abiertos}</td><td className="num tabular">{item.reparados}</td><td className="num tabular">{item.encharcamientos_activos}</td></tr>)}</tbody>
                  </table>
                </div>
                </>
              ) : <EmptyState art="search" title="Sin datos para el periodo">No hay datos para el periodo seleccionado.</EmptyState>}
            </section>
          </>
        )}
      </main>
    </Guard>
  );
}

const ESTADOS_AUDITADOS = ['Recibido', 'Validado', 'Programado', 'En reparación', 'Reparado', 'Rechazado'];

async function cargarAuditoria(pagina: string): Promise<{ items: AuditoriaItem[]; total: number }> {
  const response = await api.get<RespuestaPaginada<ReporteModeracionResumen>>(`/api/v1/moderacion/reportes?${ESTADOS_AUDITADOS.map((e) => `estado=${encodeURIComponent(e)}`).join('&')}&pagina=${pagina}&por_pagina=${PAGE_SIZE}`);
  const details = await Promise.all(response.datos.map((item) => api.get<ReporteModeracionDetalle>(`/api/v1/moderacion/reportes/${encodeURIComponent(item.folio)}`)));
  const items = details.flatMap((detail) => detail.historial.map((event) => ({ ...event, folio: detail.folio }))).sort((a, b) => new Date(b.fecha).getTime() - new Date(a.fecha).getTime());
  return { items, total: response.paginacion.total_paginas || 1 };
}

export function AuditPage() {
  const [page, setPage] = useState(1);
  const auditoria = useCargaDatos(String(page), cargarAuditoria, 'No fue posible cargar la auditoría.');
  const status = auditoria.estado; const error = auditoria.error;
  const items = auditoria.datos?.items ?? []; const total = auditoria.datos?.total ?? 1;
  return (
    <Guard roles={['coordinador']}>
      <main className="admin-page">
        <PageIntro title="Vista de auditoría">Historial append-only de cambios de estado, actores y motivos registrados por la API.</PageIntro>
        {status === 'cargando' && <TableSkeleton label="Cargando historial…" rows={8} />}
        {status === 'error' && <ErrorMessage message={error} />}
        {status === 'listo' && !items.length && <EmptyState art="inbox" title="Sin acciones registradas">No hay acciones administrativas para mostrar.</EmptyState>}
        {status === 'listo' && items.length > 0 && (
          <>
            <div className="admin-table-wrap">
              <table className="admin-table">
                <caption className="visually-hidden">Historial de acciones administrativas</caption>
                <thead><tr><th scope="col">Fecha</th><th scope="col">Folio</th><th scope="col">Transición</th><th scope="col">Actor</th><th scope="col">Motivo</th></tr></thead>
                <tbody>
                  {items.map((item, index) => (
                    <tr key={`${item.folio}-${item.fecha}-${index}`}>
                      <td className="tabular">{formatDate(item.fecha)}</td>
                      <th scope="row"><a className="tabular" href={`/reportes/${encodeURIComponent(item.folio)}`}>{item.folio}</a></th>
                      <td><span className="transition">{item.estado_anterior ? <StatusBadge estado={item.estado_anterior} /> : <span className="status-badge status-badge--neutral"><Icon name="plus" size={15} />Creación</span>}<Icon name="arrowRight" size={16} className="transition__arrow" /><span className="visually-hidden"> a </span><StatusBadge estado={item.estado_nuevo} /></span></td>
                      <td>{item.actor_rol}<br /><small className="tabular">{item.actor_id}</small></td>
                      <td>{item.motivo ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} total={total} onChange={setPage} />
          </>
        )}
      </main>
    </Guard>
  );
}
