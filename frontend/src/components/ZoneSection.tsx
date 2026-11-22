import { useState } from 'react';
import { api } from '../services/api';
import { ApiError } from '../services/api';
import { ReportCard } from './ReportCard';
import { Icon } from './Icon';
import { EmptyState, ReportGridSkeleton } from './ui';
import { tonoDeTipo } from '../utils/formato';
import type { ReporteResumenPublico, RespuestaPaginada } from '../types/api';

const LIMITES = { latMin: 31.45, latMax: 31.8, lngMin: -106.65, lngMax: -106.25 };
const RADIO_KM = 1;
const REFERENCIAS = [
  { id: 'pronaf', nombre: 'Av. Tecnológico / Pronaf', lat: 31.7458, lng: -106.4472 },
  { id: 'centro', nombre: 'Zona Centro (Catedral / Av. Juárez)', lat: 31.7393, lng: -106.4869 },
  { id: 'torres', nombre: 'Av. de las Torres / Santiago Troncoso', lat: 31.6534, lng: -106.3821 },
];

const dentroDeJuarez = (lat: number, lng: number) => lat >= LIMITES.latMin && lat <= LIMITES.latMax && lng >= LIMITES.lngMin && lng <= LIMITES.lngMax;
const distanciaKm = (aLat: number, aLng: number, bLat: number, bLng: number) => {
  const rad = (g: number) => g * Math.PI / 180;
  const h = Math.sin(rad(bLat - aLat) / 2) ** 2 + Math.cos(rad(aLat)) * Math.cos(rad(bLat)) * Math.sin(rad(bLng - aLng) / 2) ** 2;
  return 12742 * Math.asin(Math.sqrt(h));
};
const esIntransitable = (r: ReporteResumenPublico) => r.tipo_dano === 'Encharcamiento' && r.nivel_agua?.toLowerCase() === 'intransitable';
const esEncharcamientoActivo = (r: ReporteResumenPublico) => r.tipo_dano === 'Encharcamiento' && r.estado === 'Activo';
/** Reporte con su distancia (m) al punto consultado. */
type Cercano = ReporteResumenPublico & { distancia_m: number };

function Resumen({ zona, origen }: { zona: ReporteResumenPublico[]; origen: string }) {
  const intransitables = zona.filter(esIntransitable);
  const activos = zona.filter(esEncharcamientoActivo).length;
  const pavimento = zona.filter((r) => r.tipo_dano !== 'Encharcamiento').length;
  return (
    <>
      {intransitables.length > 0 && (
        <div className="zone-alert" role="alert">
          <span className="zone-alert__icon"><Icon name="ban" size={24} /></span>
          <div>
            <strong>{intransitables.length === 1 ? 'Hay 1 calle intransitable' : `Hay ${intransitables.length} calles intransitables`} cerca de {origen}</strong>
            <p>Evita circular por: {Array.from(new Set(intransitables.map((r) => r.calle))).join(', ')}.</p>
          </div>
        </div>
      )}
      <dl className="zone-stats" aria-label={`Resumen a 1 km de ${origen}`}>
        <div className="zone-stat"><dt><Icon name="layers" size={16} />Reportes</dt><dd className="tabular">{zona.length}</dd></div>
        <div className="zone-stat zone-stat--water"><dt><Icon name="water" size={16} />Encharcamientos activos</dt><dd className="tabular">{activos}</dd></div>
        <div className={`zone-stat${intransitables.length ? ' zone-stat--critical' : ''}`}><dt><Icon name="ban" size={16} />Intransitables</dt><dd className="tabular">{intransitables.length}</dd></div>
        <div className="zone-stat zone-stat--road"><dt><Icon name="pothole" size={16} />Baches y alcantarillas</dt><dd className="tabular">{pavimento}</dd></div>
      </dl>
    </>
  );
}


/** Radar de zona: barre mientras consulta y grafica los reportes reales a escala (radio = 1 km). Decorativo para lectores de pantalla: el resumen textual lleva la información. */
function Radar({ estado, centro, zona }: { estado: 'espera' | 'escaneando' | 'listo'; centro: { lat: number; lng: number } | null; zona: ReporteResumenPublico[] | null }) {
  const R = 100;
  const puntos = centro && zona ? zona.map((r) => {
    const este = (r.ubicacion.longitud - centro.lng) * 111 * Math.cos(centro.lat * Math.PI / 180);
    const norte = (r.ubicacion.latitud - centro.lat) * 111;
    return { folio: r.folio, x: 120 + Math.max(-1, Math.min(1, este / RADIO_KM)) * R, y: 120 - Math.max(-1, Math.min(1, norte / RADIO_KM)) * R, tono: tonoDeTipo(r.tipo_dano), critico: esIntransitable(r) };
  }) : [];
  return (
    <div className={`zone-radar zone-radar--${estado}`} aria-hidden="true">
      <svg viewBox="0 0 240 240" focusable="false">
        <defs>
          <radialGradient id="radar-fondo" cx="50%" cy="50%" r="50%"><stop offset="0" stopColor="#13214a" /><stop offset="1" stopColor="#070d1a" /></radialGradient>
          <linearGradient id="radar-haz" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stopColor="#6ea8ff" stopOpacity="0" /><stop offset="1" stopColor="#6ea8ff" stopOpacity="0.5" /></linearGradient>
        </defs>
        <circle cx="120" cy="120" r="112" fill="url(#radar-fondo)" />
        <path d="M120 8v224M8 120h224" className="radar-axis" />
        <circle cx="120" cy="120" r="100" className="radar-ring radar-ring--edge" />
        <circle cx="120" cy="120" r="75" className="radar-ring radar-ring--faint" />
        <circle cx="120" cy="120" r="50" className="radar-ring" />
        <circle cx="120" cy="120" r="25" className="radar-ring radar-ring--faint" />
        <text x="124" y="66" className="radar-label">500 m</text>
        <text x="124" y="16" className="radar-label">1 km</text>
        <g className="radar-waves">
          <circle cx="120" cy="120" r="100" className="radar-wave" />
          <circle cx="120" cy="120" r="100" className="radar-wave" />
          <circle cx="120" cy="120" r="100" className="radar-wave" />
        </g>
        <g className="radar-beam"><path d="M120 120 120 20A100 100 0 0 1 206.6 70Z" fill="url(#radar-haz)" /><path d="M120 120 206.6 70" className="radar-beam-edge" /></g>
        {puntos.map((p, i) => (
          <g key={p.folio} className={`radar-blip radar-blip--${p.tono}${p.critico ? ' radar-blip--critical' : ''}`} style={{ ['--i' as string]: i }}>
            {p.critico && <circle cx={p.x} cy={p.y} r="12" className="radar-blip-ring" />}
            <circle cx={p.x} cy={p.y} r={p.critico ? 6 : 4.5} className="radar-blip-dot" />
          </g>
        ))}
        <circle cx="120" cy="120" r="9" className="radar-core-halo" />
        <circle cx="120" cy="120" r="5" className="radar-core" />
      </svg>
      <p className="zone-radar__caption">
        {estado === 'escaneando' ? 'Escaneando 1 km…' : estado === 'listo' && zona ? (zona.length ? `${zona.length} ${zona.length === 1 ? 'reporte' : 'reportes'} en el radio` : 'Sin reportes en el radio') : 'Radio de consulta: 1 km'}
      </p>
    </div>
  );
}

export function ZoneSection() {
  const [zona, setZona] = useState<Cercano[] | null>(null);
  const [mensaje, setMensaje] = useState('');
  const [cargando, setCargando] = useState(false);
  const [origen, setOrigen] = useState('');
  const [centro, setCentro] = useState<{ lat: number; lng: number } | null>(null);

  const consultar = async (lat: number, lng: number, nombre: string) => {
    if (!dentroDeJuarez(lat, lng)) {
      setZona(null);
      setMensaje('Tu ubicación está fuera de Ciudad Juárez. Elige una ubicación de referencia de la lista para consultar el radio de 1 km.');
      return;
    }
    setCargando(true); setMensaje(''); setOrigen(nombre); setCentro({ lat, lng });
    const dLat = RADIO_KM / 111; const dLng = RADIO_KM / (111 * Math.cos(lat * Math.PI / 180));
    try {
      const bbox = `${lng - dLng},${lat - dLat},${lng + dLng},${lat + dLat}`;
      const respuesta = await api.get<RespuestaPaginada<ReporteResumenPublico>>(`/api/v1/reportes?bbox=${bbox}&por_pagina=100`);
      // HU-04.3: del más cercano al más lejano (Haversine); los intransitables se resaltan en la alerta y la tarjeta.
      const cerca = respuesta.datos
        .map((r) => ({ ...r, distancia_m: distanciaKm(lat, lng, r.ubicacion.latitud, r.ubicacion.longitud) * 1000 }))
        .filter((r) => r.distancia_m <= RADIO_KM * 1000)
        .sort((a, b) => a.distancia_m - b.distancia_m);
      setZona(cerca);
      if (!cerca.length) setMensaje(`No encontramos reportes en un radio de 1 km de ${nombre}.`);
    } catch (e) {
      setZona(null);
      setMensaje(e instanceof ApiError ? e.message : 'No fue posible consultar tu zona. Intenta de nuevo.');
    } finally { setCargando(false); }
  };

  const usarGps = () => {
    if (!navigator.geolocation) { setMensaje('Tu navegador no permite consultar tu ubicación. Elige una referencia de la lista.'); return; }
    setMensaje('Solicitando tu ubicación…');
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => void consultar(coords.latitude, coords.longitude, 'tu ubicación'),
      () => setMensaje('No pudimos obtener tu ubicación. Revisa el permiso del navegador o elige una referencia de la lista.'),
    );
  };

  return (
    <section className="zone-section" aria-labelledby="zona-titulo">
      <div className="zone-section__layout">
        <Radar estado={cargando ? 'escaneando' : zona ? 'listo' : 'espera'} centro={centro} zona={zona} />
        <div className="zone-section__main">
          <div className="zone-section__intro">
            <h2 id="zona-titulo">¿Cómo está mi zona?</h2>
            <p>Consulta reportes en un radio de 1 km y revisa primero los encharcamientos activos.</p>
          </div>
          <div className="zone-section__controls">
            <button className="button button--primary button--lg" type="button" onClick={usarGps} disabled={cargando}><Icon name="locate" size={20} />Usar mi ubicación</button>
            <fieldset className="zone-references">
              <legend>O elige una ubicación de referencia en Ciudad Juárez</legend>
              <div className="pill-group">
                {REFERENCIAS.map((ref) => (
                  <button key={ref.id} className="pill" type="button" aria-pressed={origen === ref.nombre && zona !== null} disabled={cargando} onClick={() => void consultar(ref.lat, ref.lng, ref.nombre)}>
                    <Icon name="pin" size={16} />{ref.nombre}
                  </button>
                ))}
              </div>
            </fieldset>
          </div>
        </div>
      </div>

      <div className="zone-section__results">
        {cargando && <ReportGridSkeleton count={3} label="Consultando reportes cercanos…" />}
        {!cargando && zona && zona.length === 0 && <EmptyState art="map" title="Tu zona se ve despejada">{mensaje} Si ves un daño, ayúdanos a registrarlo.</EmptyState>}
        {!cargando && mensaje && !(zona && zona.length === 0) && <p className="zone-note" role="status"><Icon name="info" size={18} />{mensaje}</p>}
        {!cargando && zona && zona.length > 0 && (
          <>
            <p className="zone-summary" role="status"><span className="tabular">{zona.length}</span> reporte(s) a 1 km de <strong>{origen}</strong>, del más cercano al más lejano.</p>
            <Resumen zona={zona} origen={origen} />
            <div className="report-grid">{zona.map((r) => <ReportCard key={r.folio} reporte={r} distanciaMetros={r.distancia_m} />)}</div>
          </>
        )}
      </div>
    </section>
  );
}
