import { useEffect, useState } from 'react';
import { api, ApiError } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Icon, type IconName } from '../components/Icon';
import { BlockSkeleton, EmptyState, SeverityBadge, StatusBadge, TypeBadge, antiguedadTexto } from '../components/ui';
import type { HistorialResponse, ReportePublico } from '../types/api';

const fechaLarga = (valor: string) => new Date(valor).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' });
const ORIGEN: Record<string, { texto: string; icon: IconName }> = {
  ciudadano: { texto: 'Reporte ciudadano', icon: 'user' },
  moderacion: { texto: 'Actualización de moderación', icon: 'shield' },
};

export function ReportDetailPage({ folio }: { folio: string }) {
  const { autenticado } = useAuth();
  const [reporte, setReporte] = useState<ReportePublico | null>(null); const [historial, setHistorial] = useState<HistorialResponse | null>(null); const [estado, setEstado] = useState<'cargando' | 'listo' | 'error'>('cargando');
  const [confirmando, setConfirmando] = useState<'sigue_ahi' | 'ya_no_hay_agua' | null>(null); const [confirmacionError, setConfirmacionError] = useState('');
  useEffect(() => { let activo = true; Promise.all([api.get<ReportePublico>(`/api/v1/reportes/${folio}`), api.get<HistorialResponse>(`/api/v1/reportes/${folio}/historial`)]).then(([detalle, linea]) => { if (activo) { setReporte(detalle); setHistorial(linea); setEstado('listo'); } }).catch(() => { if (activo) setEstado('error'); }); return () => { activo = false; }; }, [folio]);
  if (estado === 'cargando') return <main className="detail-page"><div className="detail-layout"><div className="detail-card"><BlockSkeleton label="Cargando detalle…" lines={4} /></div><div className="timeline"><BlockSkeleton label="Cargando historial…" lines={3} /></div></div></main>;
  if (estado === 'error' || !reporte || !historial) return <main className="detail-page"><EmptyState art="search" title="Reporte no disponible" action={<a className="button button--primary" href="/"><Icon name="arrowLeft" size={18} />Volver a reportes</a>}><span role="alert">{new ApiError(404, 'No encontramos ese reporte o no está disponible públicamente.').message}</span></EmptyState></main>;
  const confirmar = async (tipo: 'sigue_ahi' | 'ya_no_hay_agua') => { setConfirmando(tipo); setConfirmacionError(''); try { const respuesta = await api.post<{ estado_reporte: ReportePublico['estado']; vigencia: ReportePublico['vigencia']; mensaje: string }>(`/api/v1/reportes/${encodeURIComponent(reporte.folio)}/confirmaciones`, { tipo }); setReporte((actual) => actual ? { ...actual, estado: respuesta.estado_reporte, etiqueta_publica: respuesta.estado_reporte, vigencia: respuesta.vigencia } : actual); } catch (e) { setConfirmacionError(e instanceof ApiError ? e.message : 'No fue posible registrar tu confirmación.'); } finally { setConfirmando(null); } };
  const puedeConfirmar = autenticado && reporte.tipo_dano === 'Encharcamiento' && reporte.estado === 'Activo' && !reporte.es_mio;
  const encharcamiento = reporte.tipo_dano === 'Encharcamiento';
  const intransitable = encharcamiento && 'nivel_agua' in (reporte.detalle ?? {}) && (reporte.detalle as { nivel_agua?: string }).nivel_agua === 'intransitable';

  return (
    <main className="detail-page">
      <a className="back-link" href="/"><Icon name="arrowLeft" size={16} />Volver a reportes</a>
      <div className="detail-layout">
        <article className={`detail-card detail-card--${encharcamiento ? 'water' : 'road'}`}>
          <header className="detail-card__head">
            <div className="detail-card__badges"><TypeBadge tipo={reporte.tipo_dano} /><StatusBadge estado={reporte.estado} etiqueta={reporte.etiqueta_publica} size="lg" /></div>
            <h1 className="detail-card__street">{reporte.calle}</h1>
            <p className="detail-card__colonia"><Icon name="pin" size={18} />{reporte.colonia.nombre}</p>
            <p className="detail-card__folio">Folio <span className="tabular">{reporte.folio}</span></p>
          </header>

          <dl className="fact-grid">
            <div className="fact"><dt>Severidad</dt><dd><SeverityBadge severidad={reporte.severidad} intransitable={intransitable} /></dd></div>
            <div className="fact"><dt>Reportado</dt><dd><Icon name="calendar" size={16} />{fechaLarga(reporte.created_at)}</dd></div>
            <div className="fact"><dt>Antigüedad</dt><dd><Icon name="clock" size={16} />{antiguedadTexto(reporte.longevidad_dias, reporte.created_at)}</dd></div>
            {reporte.vigencia && <div className="fact"><dt>Confirmaciones</dt><dd className="fact__votes"><span><Icon name="thumbsUp" size={16} /><span className="tabular">{reporte.vigencia.sigue_ahi}</span> “sigue ahí”</span><span><Icon name="sun" size={16} /><span className="tabular">{reporte.vigencia.ya_no_hay_agua}</span> “ya no hay agua”</span></dd></div>}
          </dl>

          <section className="detail-card__description" aria-labelledby="descripcion-titulo">
            <h2 id="descripcion-titulo">Descripción</h2>
            <p>{reporte.descripcion || 'Sin descripción adicional.'}</p>
          </section>

          {puedeConfirmar && (
            <section className="confirmation-panel" aria-labelledby="confirmaciones-titulo">
              <h2 id="confirmaciones-titulo">¿Sigue el encharcamiento?</h2>
              <p>Tu confirmación ayuda a mantener vigente la información de la calle.</p>
              {confirmacionError && <div className="form-error" role="alert">{confirmacionError}</div>}
              <div className="confirmation-actions">
                <button className="button button--primary" type="button" disabled={Boolean(confirmando)} onClick={() => void confirmar('sigue_ahi')}><Icon name="water" size={18} />{confirmando === 'sigue_ahi' ? 'Enviando…' : 'Sigue ahí'}</button>
                <button className="button button--secondary" type="button" disabled={Boolean(confirmando)} onClick={() => void confirmar('ya_no_hay_agua')}><Icon name="sun" size={18} />{confirmando === 'ya_no_hay_agua' ? 'Enviando…' : 'Ya no hay agua'}</button>
              </div>
            </section>
          )}
        </article>

        <section className="timeline" aria-labelledby="historial-titulo">
          <h2 id="historial-titulo"><Icon name="history" size={20} />Historial del reporte</h2>
          {historial.historial.length === 0 ? <EmptyState art="inbox" title="Sin movimientos todavía">Aún no hay movimientos registrados en el historial de este reporte.</EmptyState> : (
            <ol className="timeline__list">
              {historial.historial.map((evento, indice) => {
                const origen = ORIGEN[evento.origen] ?? { texto: 'Actualización automática', icon: 'clock' as IconName };
                return (
                  <li className={`timeline__item${indice === historial.historial.length - 1 ? ' is-latest' : ''}`} key={`${evento.fecha}-${indice}`}>
                    <span className="timeline__marker" aria-hidden="true"><Icon name={origen.icon} size={14} /></span>
                    <div className="timeline__body">
                      <StatusBadge estado={evento.estado_nuevo} />
                      <p>{origen.texto}</p>
                      <time dateTime={evento.fecha}>{fechaLarga(evento.fecha)}</time>
                    </div>
                  </li>
                );
              })}
            </ol>
          )}
        </section>
      </div>
    </main>
  );
}
