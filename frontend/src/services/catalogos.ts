import { api } from './api';
import type { Colonia, ColoniasResponse, MotivoRechazo } from '../types/api';
import { guardarConsulta, leerConsulta } from './offline';

const POR_PAGINA = 100; // máximo que acepta la API

let cache: Promise<Colonia[]> | null = null;

/** Catálogo completo de colonias activas (recorre todas las páginas); se reutiliza durante la sesión. */
export function cargarColonias(): Promise<Colonia[]> {
  cache ??= (async () => {
    const primera = await api.get<ColoniasResponse>(`/api/v1/catalogos/colonias?pagina=1&por_pagina=${POR_PAGINA}`);
    const resto = await Promise.all(
      Array.from({ length: Math.max(0, primera.paginacion.total_paginas - 1) }, (_, i) =>
        api.get<ColoniasResponse>(`/api/v1/catalogos/colonias?pagina=${i + 2}&por_pagina=${POR_PAGINA}`)),
    );
    const todas = [primera, ...resto].flatMap((pagina) => pagina.datos).sort((a, b) => a.nombre.localeCompare(b.nombre, 'es-MX'));
    guardarConsulta('catalogo-colonias', todas); // catálogo público: permite crear borradores sin conexión
    return todas;
  })().catch((error: unknown) => {
    cache = null;
    const guardado = leerConsulta<Colonia[]>('catalogo-colonias');
    if (guardado) return guardado.datos; // sin red: último catálogo guardado
    throw error;
  });
  return cache;
}

let motivos: Promise<MotivoRechazo[]> | null = null;

/** HU-06.3: motivos de rechazo ACTIVOS (se reutilizan durante la sesión). */
export function cargarMotivos(): Promise<MotivoRechazo[]> {
  motivos ??= api.get<{ datos: MotivoRechazo[] }>('/api/v1/catalogos/motivos-rechazo').then((r) => r.datos).catch((e: unknown) => { motivos = null; throw e; });
  return motivos;
}

/** Busca colonias por nombre (sin acentos ni mayúsculas) o por código postal. */
export function filtrarColonias(colonias: Colonia[], texto: string, limite = 8): Colonia[] {
  const q = sinAcentos(texto.trim());
  if (q.length < 2) return [];
  return colonias.filter((c) => (/^\d+$/.test(q) ? (c.codigo_postal ?? '').startsWith(q) : sinAcentos(c.nombre).includes(q))).slice(0, limite);
}

const sinAcentos = (t: string) => t.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

/** Colonias agrupadas por sector para un <select> con <optgroup>. */
export function agruparPorSector(colonias: Colonia[]): Array<[string, Colonia[]]> {
  const grupos = new Map<string, Colonia[]>();
  for (const colonia of colonias) grupos.set(colonia.sector.nombre, [...(grupos.get(colonia.sector.nombre) ?? []), colonia]);
  return [...grupos.entries()].sort(([a], [b]) => a.localeCompare(b, 'es-MX'));
}

/** Texto de la opción: nombre y, si se conoce, el código postal. */
export const etiquetaColonia = (colonia: Colonia) => (colonia.codigo_postal ? `${colonia.nombre} (C.P. ${colonia.codigo_postal})` : colonia.nombre);
