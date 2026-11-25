import type { ReporteResumenPublico } from '../types/api';
import { Icon } from './Icon';
import { RecurrentBadge, SeverityBadge, StatusBadge, TypeBadge } from './ui';
import { antiguedadTexto, distanciaTexto, tonoDeTipo } from '../utils/formato';

/**
 * Fila compacta y escaneable de un reporte público (sin datos de quien reporta, RN-04):
 * tipo · folio + calle + colonia · estado y severidad · votos, antigüedad y acceso al detalle.
 * `distanciaMetros` sólo se pasa en «¿Cómo está mi zona?» (HU-04.3).
 */
export function ReportCard({ reporte, distanciaMetros }: { reporte: ReporteResumenPublico; distanciaMetros?: number }) {
  const encharcamiento = reporte.tipo_dano === 'Encharcamiento';
  const intransitable = encharcamiento && reporte.nivel_agua?.toLowerCase() === 'intransitable';
  const href = `/reportes/${reporte.folio}`;
  return (
    <article className={`report-card report-card--${tonoDeTipo(reporte.tipo_dano)}${intransitable ? ' report-card--critical' : ''}`}>
      <div className="report-card__tipo"><TypeBadge tipo={reporte.tipo_dano} /></div>

      <div className="report-card__place">
        <p className="report-card__folio"><span className="visually-hidden">Folio </span><span className="tabular">{reporte.folio}</span></p>
        <h3 className="report-card__street"><a href={href} className="report-card__link">{reporte.calle}</a></h3>
        <p className="report-card__meta">
          <span className="report-card__colonia"><Icon name="pin" size={14} />{reporte.colonia?.nombre ?? 'Colonia sin registrar'}</span>
          {distanciaMetros !== undefined && <span className="report-card__colonia"><Icon name="locate" size={14} /><span><span className="visually-hidden">Distancia: </span>a <span className="tabular">{distanciaTexto(distanciaMetros)}</span></span></span>}
          {encharcamiento && reporte.nivel_agua && !intransitable && <span className="report-card__colonia"><Icon name="water" size={14} />Nivel del agua: {reporte.nivel_agua}</span>}
          {encharcamiento && reporte.es_punto_recurrente && <RecurrentBadge dias={reporte.dias_distintos_anio} />}
        </p>
      </div>

      <div className="report-card__estado">
        <StatusBadge estado={reporte.estado} etiqueta={reporte.etiqueta_publica} />
        <SeverityBadge severidad={reporte.severidad} intransitable={intransitable} />
      </div>

      <div className="report-card__foot">
        {encharcamiento && reporte.vigencia && (
          <span className="report-card__votes">
            <span><Icon name="thumbsUp" size={14} /><span className="tabular">{reporte.vigencia.sigue_ahi}</span><span className="visually-hidden"> “sigue ahí”</span></span>
            <span><Icon name="sun" size={14} /><span className="tabular">{reporte.vigencia.ya_no_hay_agua}</span><span className="visually-hidden"> “ya no hay agua”</span></span>
          </span>
        )}
        <span className="report-card__age"><Icon name="clock" size={14} /><span className="visually-hidden">Antigüedad: </span>{antiguedadTexto(reporte.longevidad_dias, reporte.created_at)}</span>
        <span className="report-card__cta" aria-hidden="true">Ver detalle <Icon name="arrowRight" size={16} /></span>
      </div>
    </article>
  );
}
