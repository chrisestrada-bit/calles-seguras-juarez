import { Icon } from './Icon';
import { esIntransitable, horaLocal, restante, textoNivel } from '../utils/vigencia';
import type { ReporteResumenPublico } from '../types/api';

interface Props {
  vigentes: ReporteResumenPublico[];
  estado: 'cargando' | 'listo' | 'error';
  ahora: number;
  onSeleccionar: (folio: string) => void;
}

/** Tarjeta de la portada con el aviso más importante: un encharcamiento intransitable, uno vigente o «sin avisos». */
export function AlertaPrioritaria({ vigentes, estado, ahora, onSeleccionar }: Props) {
  if (estado === 'cargando') {
    return <div className="alerta alerta--cargando" role="status"><span className="spinner" aria-hidden="true" />Revisando encharcamientos vigentes…</div>;
  }
  const principal = vigentes[0];
  const intransitables = vigentes.filter(esIntransitable).length;
  const nivel = estado === 'error' ? 'desconocido' : !principal ? 'bajo' : esIntransitable(principal) ? 'alto' : 'medio';
  const tiempo = principal ? restante(principal.vigencia, ahora) : null;

  return (
    <article className={`alerta alerta--${nivel}`} aria-labelledby="alerta-titulo">
      <header className="alerta__cabeza">
        <span className={`riesgo riesgo--${nivel}`}>
          <Icon name={nivel === 'bajo' ? 'checkCircle' : 'alert'} size={16} />
          {nivel === 'alto' ? 'Riesgo alto' : nivel === 'medio' ? 'Precaución' : nivel === 'bajo' ? 'Sin encharcamientos vigentes' : 'Sin datos'}
        </span>
        <span className="tabular alerta__hora">actualizado {horaLocal(new Date(ahora).toISOString())}</span>
      </header>

      {estado === 'error' ? (
        <>
          <h2 id="alerta-titulo">No pudimos revisar los encharcamientos</h2>
          <p>Revisa tu conexión. Mientras tanto puedes consultar tu zona o la lista de reportes.</p>
        </>
      ) : principal ? (
        <>
          <h2 id="alerta-titulo">{principal.calle}: {nivel === 'alto' ? 'evita el paso' : 'hay agua en la calle'}</h2>
          <p>{textoNivel(principal.nivel_agua)} en {principal.colonia.nombre}{principal.vigencia ? `, confirmado ${principal.vigencia.sigue_ahi} ${principal.vigencia.sigue_ahi === 1 ? 'vez' : 'veces'} con «Sigue ahí»` : ''}.</p>
        </>
      ) : (
        <>
          <h2 id="alerta-titulo">Ninguna calle reporta agua ahora</h2>
          <p>Revisa tu zona antes de salir: también verás baches y alcantarillas sin tapa cercanos.</p>
        </>
      )}

      <dl className="alerta__datos">
        <div><dt>Encharcamientos</dt><dd className="tabular">{estado === 'listo' ? vigentes.length : '—'}</dd></div>
        <div><dt>Intransitables</dt><dd className="tabular">{estado === 'listo' ? intransitables : '—'}</dd></div>
        <div><dt>Vigencia</dt><dd className="tabular">{tiempo ? tiempo.texto : '—'}</dd></div>
      </dl>

      <div className="alerta__acciones">
        {principal && <a className="button button--sm" href={`/reportes/${encodeURIComponent(principal.folio)}`} onClick={() => onSeleccionar(principal.folio)}>Ver {principal.folio}<Icon name="arrowRight" size={16} /></a>}
        <a className="button button--secondary button--sm" href="#zona-titulo"><Icon name="locate" size={16} />Revisar mi zona</a>
        <a className="button button--secondary button--sm" href="/reportar"><Icon name="plus" size={16} />Reportar un daño</a>
      </div>
    </article>
  );
}
