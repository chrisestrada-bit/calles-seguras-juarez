import { lazy, Suspense, useState, type FormEvent } from 'react';
import { api, ApiError } from '../services/api';
import { PageIntro } from '../components/AdminShared';
import { Icon } from '../components/Icon';
import { EmptyState, Notice } from '../components/ui';
import { distanciaTexto, fechaHora } from '../utils/formato';
import type { GeocodingResponse, GeocodingResultado, TrayectoResponse, Ubicacion } from '../types/api';

const TrayectoMapa = lazy(() => import('../components/TrayectoMapa').then((m) => ({ default: m.TrayectoMapa })));
const VACIO = 'No hay encharcamientos reportados cerca del trayecto';
const enJuarez = (p: Ubicacion) => p.latitud >= 31.45 && p.latitud <= 31.8 && p.longitud >= -106.65 && p.longitud <= -106.25;

type Punto = { ubicacion: Ubicacion; etiqueta: string } | null;

function BuscadorPunto({ id, etiqueta, valor, onElegir, conGps }: { id: string; etiqueta: string; valor: Punto; onElegir: (p: Punto) => void; conGps?: boolean }) {
  const [texto, setTexto] = useState('');
  const [resultados, setResultados] = useState<GeocodingResultado[]>([]);
  const [estado, setEstado] = useState('');
  const buscar = async () => {
    if (texto.trim().length < 3) { setEstado('Escribe al menos 3 caracteres.'); return; }
    setEstado('Buscando…');
    try { const r = await api.get<GeocodingResponse>(`/api/v1/geocoding/buscar?q=${encodeURIComponent(texto.trim())}&limite=5`); setResultados(r.datos); setEstado(r.datos.length ? '' : r.mensaje ?? 'Sin resultados dentro de Ciudad Juárez.'); }
    catch (e) { setEstado(e instanceof ApiError ? e.message : 'No pudimos buscar la dirección.'); }
  };
  const gps = () => {
    if (!navigator.geolocation) { setEstado('Tu navegador no permite obtener la ubicación.'); return; }
    setEstado('Tu navegador te pedirá permiso para usar tu ubicación; sólo se usa como punto de origen.');
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      const u = { latitud: Number(coords.latitude.toFixed(6)), longitud: Number(coords.longitude.toFixed(6)) };
      if (!enJuarez(u)) { setEstado('Tu ubicación está fuera de Ciudad Juárez.'); return; }
      onElegir({ ubicacion: u, etiqueta: 'Mi ubicación' }); setEstado('');
    }, () => setEstado('No pudimos obtener tu ubicación.'));
  };
  return (
    <fieldset className="trayecto-punto">
      <legend>{etiqueta}</legend>
      {valor && <p className="location-readout"><Icon name="pin" size={16} /><span>{valor.etiqueta} ({valor.ubicacion.latitud.toFixed(5)}, {valor.ubicacion.longitud.toFixed(5)})</span></p>}
      <label htmlFor={id}>Dirección, cruce o colonia</label>
      <div className="inline-form">
        <input id={id} value={texto} onChange={(e) => setTexto(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); void buscar(); } }} placeholder="Ej. Tecnológico y Ejército Nacional" />
        <button className="button button--secondary" type="button" onClick={() => void buscar()}><Icon name="search" size={18} />Buscar</button>
      </div>
      {conGps && <button className="button button--quiet button--sm" type="button" onClick={gps}><Icon name="locate" size={16} />Usar mi ubicación</button>}
      {estado && <p className="field-help" role="status">{estado}</p>}
      {resultados.length > 0 && <ul className="search-results">{resultados.map((r) => <li key={`${r.etiqueta}-${r.ubicacion.latitud}`}><button type="button" onClick={() => { onElegir({ ubicacion: r.ubicacion, etiqueta: r.etiqueta }); setResultados([]); setTexto(''); }}><Icon name="pin" size={18} /><strong>{r.etiqueta}</strong></button></li>)}</ul>}
    </fieldset>
  );
}

/** HU-04.6: revisar mi trayecto antes de circular. */
export function TrayectoPage() {
  const [origen, setOrigen] = useState<Punto>(null);
  const [destino, setDestino] = useState<Punto>(null);
  const [resultado, setResultado] = useState<TrayectoResponse | null>(null);
  const [estado, setEstado] = useState<'inactivo' | 'cargando' | 'error'>('inactivo');
  const [error, setError] = useState('');

  const clicMapa = (u: Ubicacion) => {
    setResultado(null);
    if (!origen || (origen && destino)) { setOrigen({ ubicacion: u, etiqueta: 'Punto en el mapa' }); setDestino(null); }
    else setDestino({ ubicacion: u, etiqueta: 'Punto en el mapa' });
  };
  const revisar = async (e: FormEvent) => {
    e.preventDefault();
    if (!origen || !destino) { setError('Elige el origen y el destino (búsqueda, ubicación o clic en el mapa).'); setEstado('error'); return; }
    setEstado('cargando'); setError('');
    const p = new URLSearchParams({ origen_latitud: String(origen.ubicacion.latitud), origen_longitud: String(origen.ubicacion.longitud), destino_latitud: String(destino.ubicacion.latitud), destino_longitud: String(destino.ubicacion.longitud) });
    try { setResultado(await api.get<TrayectoResponse>(`/api/v1/trayecto/revisar?${p}`)); setEstado('inactivo'); }
    catch (err) { setError(err instanceof ApiError ? err.message : 'No pudimos revisar el trayecto.'); setEstado('error'); }
  };

  return (
    <main className="admin-page">
      <PageIntro title="Revisar mi trayecto">Antes de salir, revisa si hay encharcamientos vigentes a 100 metros o menos de tu ruta. Primero verás los intransitables.</PageIntro>
      <form className="panel trayecto-form" onSubmit={revisar}>
        <BuscadorPunto id="tr-origen" etiqueta="Origen" valor={origen} onElegir={(p) => { setOrigen(p); setResultado(null); }} conGps />
        <BuscadorPunto id="tr-destino" etiqueta="Destino" valor={destino} onElegir={(p) => { setDestino(p); setResultado(null); }} />
        <button className="button button--primary button--lg" type="submit" disabled={estado === 'cargando'}><Icon name="route" size={20} />{estado === 'cargando' ? 'Revisando…' : 'Revisar trayecto'}</button>
      </form>
      {estado === 'error' && <div className="form-error" role="alert">{error}</div>}
      <Suspense fallback={<div className="map-state" role="status"><span className="spinner" aria-hidden="true" />Cargando mapa…</div>}>
        <TrayectoMapa origen={origen?.ubicacion ?? null} destino={destino?.ubicacion ?? null} ruta={resultado?.ruta.puntos ?? []} encharcamientos={resultado?.datos ?? []} onClic={clicMapa} />
      </Suspense>
      {resultado && (
        <section aria-labelledby="trayecto-resultados" aria-live="polite">
          <h2 id="trayecto-resultados">Resultados</h2>
          <p className="field-help">Ruta de {distanciaTexto(resultado.ruta.distancia_metros)}{resultado.ruta.duracion_segundos ? ` · ≈ ${Math.round(resultado.ruta.duracion_segundos / 60)} min en auto` : ''} · radio de revisión {resultado.radio_metros} m.</p>
          {resultado.ruta.degradado && <Notice tone="warning">{resultado.ruta.mensaje ?? 'Revisamos la línea recta entre los puntos porque el servicio de rutas no respondió.'}</Notice>}
          {resultado.datos.length === 0 ? <EmptyState art="map" title={VACIO}>Aun así, maneja con precaución si está lloviendo.</EmptyState> : (
            <ol className="trayecto-lista">
              {resultado.datos.map((e) => (
                <li key={e.folio} className={e.es_intransitable ? 'is-critical' : ''}>
                  <Icon name={e.es_intransitable ? 'ban' : 'water'} size={20} />
                  <div>
                    <strong>{e.es_intransitable ? 'Intransitable' : `Nivel: ${e.nivel_agua}`}</strong> · a {distanciaTexto(e.distancia_metros)} del trayecto
                    <span className="table-sub">{e.calle}, {e.colonia.nombre} · vigente hasta {fechaHora(e.vigente_hasta)}{e.hay_riesgo_personas_vehiculos ? ' · riesgo para personas o vehículos' : ''}</span>
                  </div>
                  <a href={`/reportes/${e.folio}`}>Ver {e.folio}</a>
                </li>
              ))}
            </ol>
          )}
        </section>
      )}
    </main>
  );
}
