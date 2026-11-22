import type { ReporteResumenPublico } from '../types/api';

/** Filtros de la consulta pública (HU-04.2). Se comparten con el mapa y con la fusión de eventos en vivo. */
export interface FiltrosLista { busqueda: string; tipo: string; estado: string; colonia: string; desde: string; hasta: string; }
export const SIN_FILTROS: FiltrosLista = { busqueda: '', tipo: '', estado: '', colonia: '', desde: '', hasta: '' };
export const PATRON_FOLIO = /^(BCH|ENC)-\d{4}-\d{6}$/i;

/** Estado de cada folio recibido en vivo: el resumen público, o `null` si el reporte fue retirado (rechazado). */
export type Vivos = Record<string, ReporteResumenPublico | null>;

/** ¿Un encharcamiento recibido en vivo cumple los filtros activos? Misma lógica que aplica el servidor. */
export function coincideConFiltros(r: ReporteResumenPublico, f: FiltrosLista): boolean {
  if (r.tipo_dano !== 'Encharcamiento') return false;
  if (f.tipo && f.tipo !== r.tipo_dano) return false;
  if (f.estado && f.estado !== r.estado) return false;
  if (f.colonia && String(r.colonia.id) !== f.colonia) return false;
  const texto = f.busqueda.trim();
  if (PATRON_FOLIO.test(texto)) { if (r.folio.toUpperCase() !== texto.toUpperCase()) return false; }
  else if (texto.length >= 3 && !r.calle.toLowerCase().includes(texto.toLowerCase())) return false;
  const dia = r.created_at.slice(0, 10); // el servidor ya envía la fecha en hora de Ciudad Juárez
  if (f.desde && dia < f.desde) return false;
  if (f.hasta && dia > f.hasta) return false;
  return true;
}

/**
 * Mezcla los eventos en vivo con la lista consultada, sin duplicar folios y respetando los filtros activos:
 * actualiza los existentes, retira los rechazados o que ya no cumplen el filtro, e inserta los nuevos al inicio.
 * Sólo se inserta en la primera página (orden «recientes»); en las demás sólo se actualizan/retiran.
 */
export function fusionarEnVivo<T extends { folio: string; created_at?: string }>(base: T[], vivos: Vivos, filtros: FiltrosLista, insertar: boolean, limite?: number): T[] {
  const presentes = new Set<string>();
  const resultado: T[] = [];
  for (const item of base) {
    if (presentes.has(item.folio)) continue; // nunca duplicar
    const vivo = vivos[item.folio];
    if (vivo === null) continue;
    if (vivo !== undefined && !coincideConFiltros(vivo, filtros)) continue;
    presentes.add(item.folio);
    resultado.push(vivo ? { ...item, ...vivo } : item);
  }
  if (insertar) {
    // Con una página llena sólo se insertan los más recientes que el último visible (el sondeo trae también reportes viejos).
    const corte = limite && base.length >= limite ? base[base.length - 1]?.created_at ?? '' : '';
    const nuevos = Object.values(vivos)
      .filter((v): v is ReporteResumenPublico => v !== null && !presentes.has(v.folio) && v.created_at >= corte && coincideConFiltros(v, filtros))
      .sort((a, b) => b.created_at.localeCompare(a.created_at)) as unknown as T[];
    resultado.unshift(...nuevos);
  }
  return limite ? resultado.slice(0, limite) : resultado;
}
