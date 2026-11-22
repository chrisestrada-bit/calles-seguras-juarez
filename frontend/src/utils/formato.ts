import type { TipoDano } from '../types/api';

/** RN-02: toda fecha se muestra en la hora oficial de Ciudad Juárez, sin importar la zona del navegador. */
export const ZONA_HORARIA = 'America/Ciudad_Juarez';

export type Tono = 'road' | 'manhole' | 'water';
const TONO: Record<TipoDano, Tono> = { Bache: 'road', 'Alcantarilla sin tapa': 'manhole', Encharcamiento: 'water' };
export const tonoDeTipo = (tipo: TipoDano): Tono => TONO[tipo] ?? 'road';

/** Fecha y hora de un instante (ISO con zona) en hora de Ciudad Juárez. */
export const fechaHora = (valor: string) => new Date(valor).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short', timeZone: ZONA_HORARIA });

/** Sólo la fecha de un instante, en hora de Ciudad Juárez. */
export const fechaDeInstante = (valor: string) => new Date(valor).toLocaleDateString('es-MX', { dateStyle: 'medium', timeZone: ZONA_HORARIA });

/** Fecha de calendario (AAAA-MM-DD, p. ej. fecha de reparación): se muestra tal cual, sin desplazarla de día. */
export const fechaCalendario = (valor: string) => new Date(`${valor}T12:00:00Z`).toLocaleDateString('es-MX', { dateStyle: 'medium', timeZone: 'UTC' });

/** Antigüedad (RN-10): usa longevidad_dias del servidor; si falta, la calcula desde created_at. */
export function antiguedadTexto(longevidad: number | null | undefined, creado: string) {
  const dias = longevidad ?? Math.max(0, Math.floor((Date.now() - new Date(creado).getTime()) / 86_400_000));
  if (dias < 1) return 'Hoy';
  return dias === 1 ? '1 día' : `${dias} días`;
}

export const distanciaTexto = (metros: number) => (metros < 1000 ? `${Math.round(metros)} m` : `${(metros / 1000).toFixed(1)} km`);
