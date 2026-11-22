import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, ApiError } from '../services/api';
import type { ReporteMio, RespuestaPaginada } from '../types/api';
import { Pagination } from '../components/AdminShared';
import { Icon } from '../components/Icon';
import { BlockSkeleton, EmptyState, StatusBadge, TypeBadge } from '../components/ui';

const TAMANO_PAGINA = 10;

export function MyReportsPage() {
  const { autenticado } = useAuth();
  const [reportes, setReportes] = useState<ReporteMio[]>([]);
  const [pagina, setPagina] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);
  const [estado, setEstado] = useState<'cargando' | 'listo' | 'error'>('cargando');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!autenticado) return;
    let activo = true;
    setEstado('cargando'); setError('');
    api.get<RespuestaPaginada<ReporteMio>>(`/api/v1/reportes/mios?pagina=${pagina}&por_pagina=${TAMANO_PAGINA}`)
      .then((respuesta) => { if (activo) { setReportes(respuesta.datos); setTotalPaginas(respuesta.paginacion.total_paginas || 1); setEstado('listo'); } })
      .catch((e) => { if (activo) { setError(e instanceof ApiError ? e.message : 'No fue posible cargar tus reportes.'); setEstado('error'); } });
    return () => { activo = false; };
  }, [autenticado, pagina]);

  if (!autenticado) return <main className="report-page"><section className="auth-card auth-card--center"><span className="auth-card__icon"><Icon name="inbox" size={28} /></span><h1>Mis reportes</h1><p>Inicia sesión para consultar el historial de tus reportes.</p><a className="button button--primary" href="/login">Iniciar sesión</a></section></main>;

  return <main className="my-reports-page"><header className="page-intro"><div><h1>Mis reportes</h1><p>Consulta el estado de tus reportes y el motivo si alguno fue rechazado.</p></div><div className="page-intro__actions"><a className="button button--primary" href="/reportar"><Icon name="plus" size={18} />Reportar daño</a></div></header>
    {estado === 'cargando' && <div className="my-report-list"><div className="my-report-card"><BlockSkeleton label="Cargando tus reportes…" /></div></div>}
    {estado === 'error' && <div className="form-error" role="alert">{error}</div>}
    {estado === 'listo' && reportes.length === 0 && <EmptyState art="road" title="Todavía no tienes reportes registrados" action={<a className="button button--primary" href="/reportar"><Icon name="plus" size={18} />Reportar mi primer daño</a>}>Cuando reportes un bache, una alcantarilla sin tapa o un encharcamiento, aquí verás su avance.</EmptyState>}
    {estado === 'listo' && reportes.length > 0 && <section aria-labelledby="mis-reportes-titulo"><h2 id="mis-reportes-titulo" className="visually-hidden">Reportes registrados</h2><div className="my-report-list">{reportes.map((reporte) => {
      const puedeEditar = reporte.estado === 'Recibido';
      return <article className="my-report-card" key={reporte.folio}><div className="my-report-card__heading"><div className="my-report-card__title"><TypeBadge tipo={reporte.tipo_dano} /><h2 className="tabular">{reporte.folio}</h2></div><StatusBadge estado={reporte.estado} etiqueta={reporte.etiqueta_publica} size="lg" /></div><dl className="detail-list"><div><dt>Calle</dt><dd>{reporte.calle}</dd></div><div><dt>Colonia</dt><dd>{reporte.colonia.nombre}</dd></div><div><dt>Reportado</dt><dd>{new Date(reporte.created_at).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' })}</dd></div></dl>{reporte.estado === 'Rechazado' && reporte.motivo_rechazo && <div className="rejection-reason" role="note"><Icon name="xCircle" size={20} /><div><strong>Motivo del rechazo</strong><p>{reporte.motivo_rechazo}</p></div></div>}<div className="my-report-actions"><a className="button button--secondary" href={`/reportes/${encodeURIComponent(reporte.folio)}`}>Ver detalle<Icon name="arrowRight" size={16} /></a>{puedeEditar ? <a className="button button--primary" href={`/reportar?editar=${encodeURIComponent(reporte.folio)}`}><Icon name="edit" size={16} />Editar</a> : <button className="button button--quiet" type="button" disabled title="Sólo se puede editar mientras el reporte está Recibido."><Icon name="edit" size={16} />Editar</button>}<button className="button button--quiet" type="button" disabled title="RN-07: los reportes no se eliminan; se conservan para trazabilidad."><Icon name="trash" size={16} />Eliminar</button></div>{!puedeEditar && <p className="field-help">La edición sólo está disponible mientras el reporte está en estado Recibido. Los reportes se conservan por trazabilidad.</p>}</article>;
    })}</div><Pagination page={pagina} total={totalPaginas} onChange={setPagina} label="Paginación de mis reportes" /></section>}
  </main>;
}
