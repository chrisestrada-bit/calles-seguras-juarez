import { useState } from 'react';
import { api } from '../services/api';
import { ApiError } from '../services/api';
import { ReportCard } from './ReportCard';
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
const prioridad = (r: ReporteResumenPublico) => (esIntransitable(r) ? 2 : esEncharcamientoActivo(r) ? 1 : 0);

export function ZoneSection() {
  const [zona, setZona] = useState<ReporteResumenPublico[] | null>(null);
  const [mensaje, setMensaje] = useState('');
  const [cargando, setCargando] = useState(false);
  const [origen, setOrigen] = useState('');

  const consultar = async (lat: number, lng: number, nombre: string) => {
    if (!dentroDeJuarez(lat, lng)) {
      setZona(null);
      setMensaje('Tu ubicación está fuera de Ciudad Juárez. Elige una ubicación de referencia de la lista para consultar el radio de 1 km.');
      return;
    }
    setCargando(true); setMensaje(''); setOrigen(nombre);
    const dLat = RADIO_KM / 111; const dLng = RADIO_KM / (111 * Math.cos(lat * Math.PI / 180));
    try {
      const bbox = `${lng - dLng},${lat - dLat},${lng + dLng},${lat + dLat}`;
      const respuesta = await api.get<RespuestaPaginada<ReporteResumenPublico>>(`/api/v1/reportes?bbox=${bbox}&por_pagina=100`);
      const cerca = respuesta.datos
        .filter((r) => distanciaKm(lat, lng, r.ubicacion.latitud, r.ubicacion.longitud) <= RADIO_KM)
        .sort((a, b) => prioridad(b) - prioridad(a));
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
      <div><h2 id="zona-titulo">¿Cómo está mi zona?</h2><p>Consulta reportes en un radio de 1 km y revisa primero los encharcamientos activos.</p></div>
      <button className="button button--secondary" type="button" onClick={usarGps} disabled={cargando}>Usar mi ubicación</button>
      <fieldset className="zone-references">
        <legend>O elige una ubicación de referencia en Ciudad Juárez</legend>
        {REFERENCIAS.map((ref) => <button key={ref.id} className="button button--quiet" type="button" disabled={cargando} onClick={() => void consultar(ref.lat, ref.lng, ref.nombre)}>{ref.nombre}</button>)}
      </fieldset>
      {cargando && <p className="state-message" role="status">Consultando reportes cercanos…</p>}
      {mensaje && !cargando && <p role="status">{mensaje}</p>}
      {zona && zona.length > 0 && <><p role="status">{zona.length} reporte(s) a 1 km de {origen}.</p><div className="report-grid">{zona.map((r) => <ReportCard key={r.folio} reporte={r} />)}</div></>}
    </section>
  );
}
