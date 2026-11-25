import type { ReporteResumenPublico, Vigencia } from '../types/api';
import { ZONA_HORARIA } from './formato';

/** RN-06: un encharcamiento vigente dura 6 h desde la última confirmación «Sigue ahí». */
export const HORAS_VIGENCIA = 6;
/** RN-06: con 3 «Ya no hay agua» de personas distintas pasa a histórico. */
export const DESMENTIDOS_PARA_HISTORICO = 3;

const NIVELES = ['a un lado de la calle', 'cubre un carril', 'a media llanta', 'intransitable'] as const;

/** Posición 0–3 del nivel de agua (para el indicador de 4 barras); -1 si no se conoce. */
export const indiceNivel = (nivel: string | null | undefined) => NIVELES.indexOf((nivel ?? '') as (typeof NIVELES)[number]);

export const textoNivel = (nivel: string | null | undefined) => (nivel ? nivel.charAt(0).toUpperCase() + nivel.slice(1) : 'Nivel no indicado');

export const esIntransitable = (r: Pick<ReporteResumenPublico, 'nivel_agua'>) => r.nivel_agua === 'intransitable';

export const horaLocal = (valor: string) => new Date(valor).toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: ZONA_HORARIA });

/** Vigencia restante calculada contra `ahora` (milisegundos). */
export function restante(vigencia: Vigencia | null, ahora: number) {
  if (!vigencia) return null;
  const minutos = Math.max(0, Math.round((Date.parse(vigencia.vigente_hasta) - ahora) / 60_000));
  return {
    minutos,
    fraccion: Math.min(1, minutos / (HORAS_VIGENCIA * 60)),
    texto: `${Math.floor(minutos / 60)} h ${String(minutos % 60).padStart(2, '0')} min`,
    vence: horaLocal(vigencia.vigente_hasta),
  };
}

/** Encharcamientos aún vigentes (estado Activo y sin vencer), los intransitables primero. */
export function vigentesOrdenados(lista: ReporteResumenPublico[], ahora: number): ReporteResumenPublico[] {
  return lista
    .filter((r) => r.tipo_dano === 'Encharcamiento' && r.estado === 'Activo' && (!r.vigencia || Date.parse(r.vigencia.vigente_hasta) > ahora))
    .sort((a, b) => Number(esIntransitable(b)) - Number(esIntransitable(a)) || Date.parse(b.created_at) - Date.parse(a.created_at));
}
