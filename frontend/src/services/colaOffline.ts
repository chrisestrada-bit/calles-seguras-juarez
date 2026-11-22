import { useSyncExternalStore } from 'react';
import { api, ApiError } from './api';
import type { CrearReporteRequest, ReportePublico } from '../types/api';

/**
 * HU-08.4: cola local de reportes creados sin conexión.
 * - Cada borrador lleva un `idempotency_key` (UUID): reenviarlo nunca duplica el folio (el servidor devuelve el mismo reporte).
 * - La cola es por persona (`csj.cola.<usuario>`); un borrador rechazado se CONSERVA con el motivo para que no se pierda.
 * - Las fotografías no se guardan sin conexión (no caben de forma segura en el almacenamiento local).
 */
export type EstadoBorrador = 'pendiente' | 'enviando' | 'error' | 'conflicto';

export interface Borrador {
  id: string; // = idempotency_key
  payload: CrearReporteRequest & { idempotency_key: string };
  estado: EstadoBorrador;
  mensaje?: string;
  candidatos?: string[]; // folios cercanos cuando el servidor detecta un posible duplicado
  creado_en: string;
}

export interface InstantaneaCola { usuarioId: string | null; borradores: Borrador[]; sincronizando: boolean; ultimosFolios: string[]; }

const clave = (usuarioId: string) => `csj.cola.${usuarioId}`;
let estado: InstantaneaCola = { usuarioId: null, borradores: [], sincronizando: false, ultimosFolios: [] };
const oyentes = new Set<() => void>();

function publicar(cambio: Partial<InstantaneaCola>): void {
  estado = { ...estado, ...cambio };
  oyentes.forEach((o) => o());
}
function leer(usuarioId: string): Borrador[] {
  try { return JSON.parse(localStorage.getItem(clave(usuarioId)) ?? '[]') as Borrador[]; } catch { return []; }
}
function guardar(usuarioId: string, borradores: Borrador[]): void {
  try { localStorage.setItem(clave(usuarioId), JSON.stringify(borradores)); } catch { /* almacenamiento lleno */ }
  publicar({ usuarioId, borradores });
}

/** Carga la cola de la persona con sesión (o la vacía si no hay sesión). */
export function cargarCola(usuarioId: string | null): void {
  publicar({ usuarioId, borradores: usuarioId ? leer(usuarioId) : [], ultimosFolios: [] });
}

export function encolar(usuarioId: string, payload: CrearReporteRequest, idempotencyKey: string): Borrador {
  const borrador: Borrador = { id: idempotencyKey, payload: { ...payload, idempotency_key: idempotencyKey }, estado: 'pendiente', creado_en: new Date().toISOString() };
  guardar(usuarioId, [...leer(usuarioId).filter((b) => b.id !== idempotencyKey), borrador]);
  return borrador;
}

function actualizar(usuarioId: string, id: string, cambio: Partial<Borrador>): void {
  guardar(usuarioId, leer(usuarioId).map((b) => (b.id === id ? { ...b, ...cambio } : b)));
}

export function descartar(usuarioId: string, id: string): void {
  guardar(usuarioId, leer(usuarioId).filter((b) => b.id !== id));
}

/** El borrador en conflicto se reenvía como «daño distinto» (misma llave: sigue siendo un único folio). */
export function enviarComoDistinto(usuarioId: string, id: string): void {
  guardar(usuarioId, leer(usuarioId).map((b) => (b.id === id ? { ...b, estado: 'pendiente', mensaje: undefined, candidatos: undefined, payload: { ...b.payload, forzar_nuevo: true } } : b)));
}

export function reintentar(usuarioId: string, id: string): void {
  actualizar(usuarioId, id, { estado: 'pendiente', mensaje: undefined });
}

let enCurso = false;

/** Envía en orden los borradores pendientes. Devuelve cuando termina o cuando detecta que no hay red/sesión. */
export async function sincronizar(usuarioId: string): Promise<void> {
  if (enCurso || !navigator.onLine) return;
  enCurso = true;
  const enviados: string[] = [];
  publicar({ sincronizando: true });
  try {
    for (const borrador of leer(usuarioId).filter((b) => b.estado === 'pendiente')) {
      actualizar(usuarioId, borrador.id, { estado: 'enviando' });
      try {
        const reporte = await api.post<ReportePublico>('/api/v1/reportes', borrador.payload);
        enviados.push(reporte.folio);
        descartar(usuarioId, borrador.id);
      } catch (e) {
        if (!(e instanceof ApiError) || e.status === 0) { actualizar(usuarioId, borrador.id, { estado: 'pendiente' }); break; } // sin red: reintentar luego
        if (e.status === 401) { actualizar(usuarioId, borrador.id, { estado: 'pendiente', mensaje: 'Inicia sesión para enviar este reporte.' }); break; }
        if (e.status === 429) { actualizar(usuarioId, borrador.id, { estado: 'pendiente', mensaje: 'Alcanzaste el límite de 10 reportes por hora. Se reintentará más tarde.' }); break; }
        if (e.status === 409 && e.codigo === 'POSIBLE_DUPLICADO') {
          const folios = e.detalles.map((d) => String((d as { folio?: unknown }).folio ?? '')).filter(Boolean);
          actualizar(usuarioId, borrador.id, { estado: 'conflicto', candidatos: folios, mensaje: 'Ya existe un reporte abierto muy cerca de este punto.' });
        } else {
          actualizar(usuarioId, borrador.id, { estado: 'error', mensaje: e.message });
        }
      }
    }
  } finally {
    enCurso = false;
    publicar({ sincronizando: false, ultimosFolios: enviados.length ? enviados : estado.ultimosFolios });
  }
}

export function descartarAvisoEnviados(): void { publicar({ ultimosFolios: [] }); }

export function useColaOffline(): InstantaneaCola {
  return useSyncExternalStore((cb) => { oyentes.add(cb); return () => oyentes.delete(cb); }, () => estado);
}
