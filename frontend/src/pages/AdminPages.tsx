import { useEffect, useState, type FormEvent } from 'react';
import { api, ApiError } from '../services/api';
import type { AuditoriaItem, EstadoReporte, IndicadorSector, IndicadoresResumen, ReporteModeracionDetalle, ReporteModeracionResumen, RespuestaPaginada, TransicionResponse } from '../types/api';
import { Guard, ErrorMessage, PageIntro, Pagination } from '../components/AdminShared';
import { Icon, type IconName } from '../components/Icon';
import { BlockSkeleton, EmptyState, Notice, SeverityBadge, StatusBadge, TableSkeleton, TypeBadge } from '../components/ui';

const PAGE_SIZE = 10;
const formatDate = (value: string) => new Date(value).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' });
const makeQuery = (values: Record<string, string | number | undefined>) => Object.entries(values).filter(([, value]) => value !== undefined && value !== '').map(([key, value]) => `${key}=${encodeURIComponent(value as string | number)}`).join('&');

function TransitionForm({ report, onComplete }: { report: ReporteModeracionResumen; onComplete: (response: TransicionResponse) => void }) {
  const [next, setNext] = useState<EstadoReporte>(report.transiciones_disponibles[0] ?? report.estado); const [reason, setReason] = useState(''); const [scheduled, setScheduled] = useState(''); const [repaired, setRepaired] = useState(''); const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  if (!report.transiciones_disponibles.length) return <p className="field-help">Sin transiciones disponibles para tu rol.</p>;
  const submit = async (event: FormEvent) => { event.preventDefault(); setError(''); if (next === 'Rechazado' && reason.trim().length < 10) { setError('El motivo del rechazo es obligatorio y debe tener al menos 10 caracteres.'); return; } setBusy(true); try { const response = await api.post<TransicionResponse>(`/api/v1/moderacion/reportes/${encodeURIComponent(report.folio)}/transiciones`, { estado_nuevo: next, motivo: next === 'Rechazado' ? reason.trim() : null, fecha_programada: scheduled || null, fecha_reparacion: repaired || null }); onComplete(response); } catch (exception) { setError(exception instanceof ApiError ? exception.message : 'No fue posible actualizar el reporte.'); } finally { setBusy(false); } };
  return (
    <form className="admin-action" onSubmit={submit}>
      <label>Acción<select value={next} onChange={(event) => setNext(event.target.value as EstadoReporte)}>{report.transiciones_disponibles.map((state) => <option key={state}>{state}</option>)}</select></label>
      {next === 'Rechazado' && <label>Motivo obligatorio<textarea required minLength={10} maxLength={500} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Explica por qué se rechaza el reporte" /></label>}
      {next === 'Programado' && <label>Fecha programada<input type="date" value={scheduled} onChange={(event) => setScheduled(event.target.value)} /></label>}
      {next === 'Reparado' && <label>Fecha de reparación<input required type="date" value={repaired} onChange={(event) => setRepaired(event.target.value)} /></label>}
      {error && <ErrorMessage message={error} />}
      <button className={`button ${next === 'Rechazado' ? 'button--danger' : 'button--primary'}`} disabled={busy} type="submit">{busy ? 'Guardando…' : 'Aplicar acción'}</button>
    </form>
  );
}

function useModerationQueue(state: string, page: number, refresh: number) {
  const [data, setData] = useState<ReporteModeracionResumen[]>([]); const [total, setTotal] = useState(1); const [status, setStatus] = useState('cargando'); const [error, setError] = useState('');
  useEffect(() => { let active = true; setStatus('cargando'); api.get<RespuestaPaginada<ReporteModeracionResumen>>(`/api/v1/moderacion/reportes?${makeQuery({ estado: state, pagina: page, por_pagina: PAGE_SIZE })}`).then((response) => { if (active) { setData(response.datos); setTotal(response.paginacion.total_paginas || 1); setStatus('listo'); } }).catch((exception) => { if (active) { setError(exception instanceof ApiError ? exception.message : 'No fue posible cargar los reportes.'); setStatus('error'); } }); return () => { active = false; }; }, [state, page, refresh]);
  return { data, total, status, error };
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
        <Notice tone="info"><strong>Seguimiento:</strong> el contrato registra asignación mediante el estado y el historial inmutable. La API actual no expone una asignación individual de cuadrilla.</Notice>
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

export function DashboardPage() {
  const [from, setFrom] = useState(''); const [to, setTo] = useState(''); const [sector, setSector] = useState(''); const [summary, setSummary] = useState<IndicadoresResumen | null>(null); const [sectors, setSectors] = useState<IndicadorSector[]>([]); const [status, setStatus] = useState('cargando'); const [error, setError] = useState('');
  useEffect(() => { let active = true; setStatus('cargando'); const params = makeQuery({ desde: from, hasta: to, sector_id: sector }); Promise.all([api.get<IndicadoresResumen>(`/api/v1/indicadores/resumen?${params}`), api.get<{ datos: IndicadorSector[] }>(`/api/v1/indicadores/sectores?${makeQuery({ desde: from, hasta: to })}`)]).then(([data, zones]) => { if (active) { setSummary(data); setSectors(zones.datos); setStatus('listo'); } }).catch((exception) => { if (active) { setError(exception instanceof ApiError ? exception.message : 'No fue posible cargar las métricas.'); setStatus('error'); } }); return () => { active = false; }; }, [from, to, sector]);
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
            <div className="field"><label htmlFor="dash-zona">Zona</label><select id="dash-zona" value={sector} onChange={(event) => setSector(event.target.value)}><option value="">Todas las zonas</option>{sectors.map((item) => <option key={item.sector.id} value={item.sector.id}>{item.sector.nombre}</option>)}</select></div>
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

export function AuditPage() {
  const [page, setPage] = useState(1); const [items, setItems] = useState<AuditoriaItem[]>([]); const [total, setTotal] = useState(1); const [status, setStatus] = useState('cargando'); const [error, setError] = useState('');
  useEffect(() => { let active = true; setStatus('cargando'); api.get<RespuestaPaginada<ReporteModeracionResumen>>(`/api/v1/moderacion/reportes?estado=Recibido&estado=Validado&estado=Programado&estado=En%20reparaci%C3%B3n&estado=Reparado&estado=Rechazado&pagina=${page}&por_pagina=${PAGE_SIZE}`).then(async (response) => { const details = await Promise.all(response.datos.map((item) => api.get<ReporteModeracionDetalle>(`/api/v1/moderacion/reportes/${encodeURIComponent(item.folio)}`))); const history = details.flatMap((detail) => detail.historial.map((event) => ({ ...event, folio: detail.folio }))).sort((a, b) => new Date(b.fecha).getTime() - new Date(a.fecha).getTime()); if (active) { setItems(history); setTotal(response.paginacion.total_paginas || 1); setStatus('listo'); } }).catch((exception) => { if (active) { setError(exception instanceof ApiError ? exception.message : 'No fue posible cargar la auditoría.'); setStatus('error'); } }); return () => { active = false; }; }, [page]);
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
