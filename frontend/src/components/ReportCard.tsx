import type { ReporteResumenPublico } from '../types/api';
import { Icon } from './Icon';
import { RecurrentBadge, SeverityBadge, StatusBadge, TypeBadge } from './ui';
import { antiguedadTexto, distanciaTexto, tonoDeTipo } from '../utils/formato';

/** `distanciaMetros` sólo se pasa en «¿Cómo está mi zona?» (HU-04.3). */
export function ReportCard({ reporte, distanciaMetros }: { reporte: ReporteResumenPublico; distanciaMetros?: number }) {
  const encharcamiento = reporte.tipo_dano === 'Encharcamiento';
  const intransitable = encharcamiento && reporte.nivel_agua?.toLowerCase() === 'intransitable';
  const href = `/reportes/${reporte.folio}`;
  return (
    <article className={`report-card report-card--${tonoDeTipo(reporte.tipo_dano)}${intransitable ? ' report-card--critical' : ''}`}>
      <header className="report-card__top">
        <TypeBadge tipo={reporte.tipo_dano} />
        <StatusBadge estado={reporte.estado} etiqueta={reporte.etiqueta_publica} />
      </header>
      <div className="report-card__place">
        <h3 className="report-card__street"><a href={href} className="report-card__link">{reporte.calle}</a></h3>
        <p className="report-card__colonia"><Icon name="pin" size={16} />{reporte.colonia?.nombre ?? 'Colonia sin registrar'}</p>
        {distanciaMetros !== undefined && <p className="report-card__colonia"><Icon name="locate" size={16} /><span><span className="visually-hidden">Distancia: </span>a <span className="tabular">{distanciaTexto(distanciaMetros)}</span></span></p>}
        {encharcamiento && reporte.nivel_agua && !intransitable && <p className="report-card__colonia"><Icon name="water" size={16} />Nivel del agua: {reporte.nivel_agua}</p>}
        {encharcamiento && reporte.es_punto_recurrente && <p className="report-card__colonia"><RecurrentBadge dias={reporte.dias_distintos_anio} /></p>}
        <p className="report-card__folio">Folio <span className="tabular">{reporte.folio}</span></p>
      </div>
      {encharcamiento && reporte.vigencia && (
        <p className="report-card__votes">
          <span><Icon name="thumbsUp" size={15} /><span className="tabular">{reporte.vigencia.sigue_ahi}</span> “sigue ahí”</span>
          <span><Icon name="sun" size={15} /><span className="tabular">{reporte.vigencia.ya_no_hay_agua}</span> “ya no hay agua”</span>
        </p>
      )}
      <footer className="report-card__foot">
        <SeverityBadge severidad={reporte.severidad} intransitable={intransitable} />
        <span className="report-card__age"><Icon name="clock" size={15} /><span className="visually-hidden">Antigüedad: </span>{antiguedadTexto(reporte.longevidad_dias, reporte.created_at)}</span>
        <span className="report-card__cta" aria-hidden="true">Ver detalle <Icon name="arrowRight" size={16} /></span>
      </footer>
    </article>
  );
}
