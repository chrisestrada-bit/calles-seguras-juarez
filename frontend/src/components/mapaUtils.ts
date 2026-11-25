import L from 'leaflet';
import type { MarcadorMapa, TipoDano } from '../types/api';
import { tonoDeTipo } from '../utils/formato';

/** Cartografía: OpenStreetMap (política de uso aceptable y atribución en docs/arquitectura.md §10). */
export const TILES_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
export const ATRIBUCION = '&copy; <a href="https://www.openstreetmap.org/copyright">colaboradores de OpenStreetMap</a>';
export const CENTRO_JUAREZ: [number, number] = [31.69, -106.42];
// Límites de Ciudad Juárez (RN-01) con un pequeño margen para que el mapa no se salga del municipio.
export const LIMITES: L.LatLngBoundsExpression = [[31.4, -106.7], [31.85, -106.2]];
export const ERRORES_PARA_FALLAR = 4;

/** Glifos (mismos trazos que los íconos de la plataforma) + una letra: ícono, texto y color, nunca sólo color. */
const GLIFO: Record<TipoDano, { letra: string; trazo: string }> = {
  Bache: { letra: 'B', trazo: '<path d="M2.5 18.5 6 8.5h12l3.5 10Z"/><path d="M8 15.2c.5-1.5 2.1-2.4 4-2.4s3.5.9 4 2.4c-.4 1.3-2 2-4 2s-3.6-.7-4-2Z"/>' },
  'Alcantarilla sin tapa': { letra: 'A', trazo: '<ellipse cx="12" cy="16.5" rx="8.5" ry="3.8"/><ellipse cx="15" cy="6.8" rx="4.6" ry="2.1" transform="rotate(-16 15 6.8)"/>' },
  Encharcamiento: { letra: 'E', trazo: '<path d="M3 17c1.5 0 1.5-1 3-1s1.5 1 3 1 1.5-1 3-1 1.5 1 3 1 1.5-1 3-1 1.5 1 3 1"/><path d="M12 3.5s-3 3.4-3 5.5a3 3 0 0 0 6 0c0-2.1-3-5.5-3-5.5Z"/>' },
};

/** Gota de agua para encharcamientos (HU-03.x): forma propia, glifo + letra; anillo si es intransitable, atenuada si es histórica. */
function iconoEncharcamiento(m: MarcadorMapa, seleccionado: boolean): L.DivIcon {
  const g = GLIFO.Encharcamiento;
  const clases = ['map-drop', seleccionado && 'is-selected', m.nivel_agua === 'intransitable' && 'map-drop--critico', m.estado !== 'Activo' && 'map-drop--historico'].filter(Boolean).join(' ');
  const html = `<span class="${clases}" aria-hidden="true"><span class="map-drop__cuerpo"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${g.trazo}</svg><b>${g.letra}</b></span></span>`;
  return L.divIcon({ html, className: 'map-pin-wrap', iconSize: [40, 46], iconAnchor: [20, 44] });
}

export function iconoDe(m: MarcadorMapa, seleccionado: boolean): L.DivIcon {
  if (m.tipo_dano === 'Encharcamiento') return iconoEncharcamiento(m, seleccionado);
  const g = GLIFO[m.tipo_dano];
  const html = `<span class="map-pin map-pin--${tonoDeTipo(m.tipo_dano)}${seleccionado ? ' is-selected' : ''}" aria-hidden="true"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">${g.trazo}</svg><b>${g.letra}</b></span>`;
  return L.divIcon({ html, className: 'map-pin-wrap', iconSize: [44, 30], iconAnchor: [22, 15] });
}

export function descripcionMarcador(m: MarcadorMapa): string {
  return `${m.tipo_dano} en ${m.calle}, ${m.colonia.nombre}. Estado: ${m.etiqueta_publica ?? m.estado}.`;
}

