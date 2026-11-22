import { lazy, Suspense, useMemo, useState } from 'react';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { Icon } from './Icon';
import { EmptyState, StatusBadge, TypeBadge, TypeGlyph } from './ui';
import { fechaHora } from '../utils/formato';
import type { MapaResponse, TipoDano, Ubicacion } from '../types/api';

// Leaflet pesa ~150 kB: sólo se descarga cuando alguien abre la vista de mapa.
const ReportMap = lazy(() => import('./ReportMap').then((m) => ({ default: m.ReportMap })));

const LEYENDA: TipoDano[] = ['Bache', 'Alcantarilla sin tapa', 'Encharcamiento'];
const LIMITES = { latMin: 31.45, latMax: 31.8, lonMin: -106.65, lonMax: -106.25 };

interface Props {
  /** Mismos filtros de la lista (HU-04.2), ya serializados como query string. */
  filtros: string;
  onVerLista: () => void;
}

/** HU-04.5: mapa interactivo con los mismos filtros que la lista, sin datos personales (RN-04). */
export function MapaReportes({ filtros, onVerLista }: Props) {
  const consulta = useCargaDatos<MapaResponse>(`/api/v1/reportes/mapa?${filtros}`, obtenerJson, 'No fue posible cargar el mapa de reportes.');
  const [seleccionado, setSeleccionado] = useState<string | null>(null);
  const [mapaCaido, setMapaCaido] = useState(false);
  const [miUbicacion, setMiUbicacion] = useState<Ubicacion | null>(null);
  const [avisoGps, setAvisoGps] = useState('');
  const marcadores = useMemo(() => consulta.datos?.datos ?? [], [consulta.datos]);
  const elegido = marcadores.find((m) => m.folio === seleccionado) ?? null;

  const centrar = () => {
    if (!navigator.geolocation) { setAvisoGps('Tu navegador no permite obtener la ubicación. Puedes seguir usando el mapa sin ella.'); return; }
    setAvisoGps('Tu navegador te pedirá permiso para usar tu ubicación. Sólo se usa para centrar el mapa en tu pantalla; no se envía ni se guarda.');
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      const punto = { latitud: coords.latitude, longitud: coords.longitude };
      const dentro = punto.latitud >= LIMITES.latMin && punto.latitud <= LIMITES.latMax && punto.longitud >= LIMITES.lonMin && punto.longitud <= LIMITES.lonMax;
      if (!dentro) { setAvisoGps('Tu ubicación está fuera de Ciudad Juárez, por lo que no se centró el mapa.'); return; }
      setMiUbicacion(punto);
      setAvisoGps('Mapa centrado en tu ubicación.');
    }, (err) => setAvisoGps(err.code === err.PERMISSION_DENIED ? 'No diste permiso de ubicación. El mapa sigue disponible sin ella.' : 'No pudimos obtener tu ubicación. Intenta de nuevo.'), { timeout: 10_000 });
  };

  return (
    <section className="map-section" aria-labelledby="mapa-titulo">
      <h3 id="mapa-titulo" className="visually-hidden">Mapa de reportes</h3>
      <div className="map-toolbar">
        <ul className="legend" aria-label="Simbología del mapa">
          {LEYENDA.map((t) => <li key={t} className={`legend__item legend__item--${t === 'Bache' ? 'road' : t === 'Encharcamiento' ? 'water' : 'manhole'}`}><TypeGlyph tipo={t} size={18} />{t}</li>)}
        </ul>
        <button className="button button--secondary button--sm" type="button" onClick={centrar}><Icon name="locate" size={18} />Centrar en mi ubicación</button>
      </div>
      {avisoGps && <p className="field-help" role="status"><Icon name="info" size={16} />{avisoGps}</p>}

      {consulta.estado === 'cargando' && <div className="map-state" role="status" aria-live="polite"><span className="spinner" aria-hidden="true" />Cargando mapa…</div>}
      {consulta.estado === 'error' && <div className="form-error" role="alert">{consulta.error}</div>}
      {consulta.estado === 'listo' && marcadores.length === 0 && (
        <EmptyState art="search" title="No hay reportes en el mapa con estos filtros" action={<button className="button button--secondary" type="button" onClick={onVerLista}><Icon name="list" size={18} />Ver lista</button>}>Prueba con otros filtros o limpia la búsqueda.</EmptyState>
      )}

      {mapaCaido && (
        <div className="form-error" role="alert">
          <Icon name="alert" size={16} />No pudimos cargar los mosaicos del mapa (proveedor no disponible). Consulta los mismos reportes en la lista de abajo o{' '}
          <button className="link-button" type="button" onClick={onVerLista}>cambia a la vista de lista</button>.
        </div>
      )}

      {consulta.estado === 'listo' && marcadores.length > 0 && (
        <div className="map-layout">
          <Suspense fallback={<div className="map-state" role="status"><span className="spinner" aria-hidden="true" />Cargando mapa…</div>}>
            <ReportMap marcadores={marcadores} seleccionado={seleccionado} onSeleccionar={setSeleccionado} miUbicacion={miUbicacion} onFalloMapa={() => setMapaCaido(true)} />
          </Suspense>
          <aside className="map-panel" aria-live="polite" aria-label="Resumen del reporte seleccionado">
            {elegido ? (
              <>
                <div className="map-panel__badges"><TypeBadge tipo={elegido.tipo_dano} /><StatusBadge estado={elegido.estado} etiqueta={elegido.etiqueta_publica} /></div>
                <h4>{elegido.calle}</h4>
                <p><Icon name="pin" size={16} />{elegido.colonia.nombre}</p>
                <p><Icon name="calendar" size={16} />{fechaHora(elegido.created_at)}</p>
                {elegido.nivel_agua && <p><Icon name="water" size={16} />Nivel del agua: {elegido.nivel_agua}</p>}
                <a className="button button--primary button--sm" href={`/reportes/${encodeURIComponent(elegido.folio)}`}>Ver {elegido.folio}<Icon name="arrowRight" size={16} /></a>
              </>
            ) : <p className="field-help">Selecciona un punto del mapa para ver su resumen.</p>}
          </aside>
        </div>
      )}

      {consulta.estado === 'listo' && marcadores.length > 0 && (
        <>
          {consulta.datos && consulta.datos.total > consulta.datos.mostrados && <p className="field-help" role="status">Se muestran {consulta.datos.mostrados} de {consulta.datos.total} reportes. Acota con los filtros para ver el resto.</p>}
          <details className="map-list" open={mapaCaido}>
            <summary>Ver los {marcadores.length} puntos como lista accesible</summary>
            <ul>
              {marcadores.map((m) => <li key={m.folio}><a href={`/reportes/${encodeURIComponent(m.folio)}`}><strong>{m.tipo_dano}</strong> · {m.calle}, {m.colonia.nombre} · {m.etiqueta_publica ?? m.estado}</a></li>)}
            </ul>
          </details>
        </>
      )}
    </section>
  );
}
