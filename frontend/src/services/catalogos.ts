import { api } from './api';
import type { Colonia, ColoniasResponse } from '../types/api';

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
    return [primera, ...resto].flatMap((pagina) => pagina.datos).sort((a, b) => a.nombre.localeCompare(b.nombre, 'es-MX'));
  })().catch((error: unknown) => { cache = null; throw error; });
  return cache;
}

/** Colonias agrupadas por sector para un <select> con <optgroup>. */
export function agruparPorSector(colonias: Colonia[]): Array<[string, Colonia[]]> {
  const grupos = new Map<string, Colonia[]>();
  for (const colonia of colonias) grupos.set(colonia.sector.nombre, [...(grupos.get(colonia.sector.nombre) ?? []), colonia]);
  return [...grupos.entries()].sort(([a], [b]) => a.localeCompare(b, 'es-MX'));
}

/** Texto de la opción: nombre y, si se conoce, el código postal. */
export const etiquetaColonia = (colonia: Colonia) => (colonia.codigo_postal ? `${colonia.nombre} (C.P. ${colonia.codigo_postal})` : colonia.nombre);
