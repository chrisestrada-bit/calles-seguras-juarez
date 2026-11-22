import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, ApiError } from '../services/api';
import type { ReporteMio, RespuestaPaginada } from '../types/api';

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

  if (!autenticado) return <main className="report-page"><section className="auth-card"><h1>Mis reportes</h1><p>Inicia sesión para consultar el historial de tus reportes.</p><a className="button" href="/login">Iniciar sesión</a></section></main>;

  return <main className="my-reports-page"><section className="report-intro"><p className="eyebrow">Seguimiento ciudadano</p><h1>Mis reportes</h1><p>Consulta el estado de tus reportes y el motivo si alguno fue rechazado.</p></section>
    {estado === 'cargando' && <p className="state-message" role="status">Cargando tus reportes…</p>}
    {estado === 'error' && <div className="form-error" role="alert">{error}</div>}
    {estado === 'listo' && reportes.length === 0 && <p className="state-message">Todavía no tienes reportes registrados.</p>}
    {estado === 'listo' && reportes.length > 0 && <section aria-labelledby="mis-reportes-titulo"><h2 id="mis-reportes-titulo" className="visually-hidden">Reportes registrados</h2><div className="my-report-list">{reportes.map((reporte) => {
      const puedeEditar = reporte.estado === 'Recibido';
      return <article className="my-report-card" key={reporte.folio}><div className="my-report-card__heading"><div><p className="eyebrow">{reporte.tipo_dano}</p><h2>{reporte.folio}</h2></div><span className="status-large">{reporte.etiqueta_publica ?? reporte.estado}</span></div><dl className="detail-list"><div><dt>Calle</dt><dd>{reporte.calle}</dd></div><div><dt>Colonia</dt><dd>{reporte.colonia.nombre}</dd></div><div><dt>Reportado</dt><dd>{new Date(reporte.created_at).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' })}</dd></div></dl>{reporte.estado === 'Rechazado' && reporte.motivo_rechazo && <div className="rejection-reason"><strong>Motivo del rechazo</strong><p>{reporte.motivo_rechazo}</p></div>}<div className="my-report-actions"><a className="button button--secondary" href={`/reportes/${encodeURIComponent(reporte.folio)}`}>Ver detalle</a>{puedeEditar ? <a className="button" href={`/reportar?editar=${encodeURIComponent(reporte.folio)}`}>Editar</a> : <button className="button" type="button" disabled title="Sólo se puede editar mientras el reporte está Recibido.">Editar</button>}<button className="button button--danger" type="button" disabled title="RN-07: los reportes no se eliminan; se conservan para trazabilidad.">Eliminar</button></div>{!puedeEditar && <p className="field-help">La edición sólo está disponible mientras el reporte está en estado Recibido. Los reportes se conservan por trazabilidad.</p>}</article>;
    })}</div><nav className="pagination" aria-label="Paginación de mis reportes"><button type="button" disabled={pagina <= 1} onClick={() => setPagina((actual) => actual - 1)}>Anterior</button><span>Página {pagina} de {totalPaginas}</span><button type="button" disabled={pagina >= totalPaginas} onClick={() => setPagina((actual) => actual + 1)}>Siguiente</button></nav></section>}
  </main>;
}
