import { api } from './api';
import type { FotosSubidasResponse } from '../types/api';

/** Reglas de HU-02.4: se validan aquí para dar un mensaje inmediato y de nuevo en el servidor. */
export const MAX_FOTOS = 3;
export const MAX_BYTES_FOTO = 5 * 1024 * 1024;
export const TIPOS_FOTO = ['image/jpeg', 'image/png'];

export interface ErroresFotos { formato: string[]; tamano: string[]; limite: string[]; }
export const SIN_ERRORES_FOTOS: ErroresFotos = { formato: [], tamano: [], limite: [] };

export function formatoTamano(bytes: number): string {
  return bytes >= 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

/** Separa los archivos elegidos en válidos y errores por categoría (formato, tamaño y límite de 3). */
export function filtrarArchivos(actuales: File[], nuevos: File[]): { aceptados: File[]; errores: ErroresFotos } {
  const errores: ErroresFotos = { formato: [], tamano: [], limite: [] };
  const aceptados = [...actuales];
  for (const archivo of nuevos) {
    if (!TIPOS_FOTO.includes(archivo.type)) { errores.formato.push(archivo.name); continue; }
    if (archivo.size > MAX_BYTES_FOTO) { errores.tamano.push(archivo.name); continue; }
    if (aceptados.length >= MAX_FOTOS) { errores.limite.push(archivo.name); continue; }
    aceptados.push(archivo);
  }
  return { aceptados, errores };
}

export function subirFotos(folio: string, archivos: File[]): Promise<FotosSubidasResponse> {
  const form = new FormData();
  archivos.forEach((archivo) => form.append('archivos', archivo, archivo.name));
  return api.postForm<FotosSubidasResponse>(`/api/v1/reportes/${encodeURIComponent(folio)}/fotos`, form);
}
