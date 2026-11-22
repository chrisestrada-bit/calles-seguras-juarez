import type { ReporteResumenPublico } from '../types/api';

export function ReportCard({ reporte }: { reporte: ReporteResumenPublico }) {
  const encharcamiento = reporte.tipo_dano === 'Encharcamiento';
  return <article className={`report-card ${encharcamiento ? 'report-card--water' : 'report-card--road'}`}>
    <div className="report-card__title"><span className="damage-icon" aria-hidden="true">{encharcamiento ? '🌊' : '🕳️'}</span><span>{reporte.tipo_dano}</span></div>
    <p className="report-card__folio"><strong>{reporte.folio}</strong> · {reporte.calle}</p>
    <p><span className="status-label">Estado:</span> {reporte.etiqueta_publica ?? reporte.estado}</p>
    {encharcamiento && reporte.vigencia && <p><strong>Confirmaciones:</strong> {reporte.vigencia.sigue_ahi} “sigue ahí” · {reporte.vigencia.ya_no_hay_agua} “ya no hay agua”</p>}
    <a className="text-link" href={`/reportes/${reporte.folio}`}>Ver detalle e historial <span aria-hidden="true">→</span></a>
  </article>;
}
