import { useEffect, useState } from 'react';

/**
 * HU-08.4: almacenamiento local de lo PÚBLICO consultado por última vez (modo de sólo lectura sin conexión).
 * Privacidad: sólo se guardan respuestas públicas (sin token ni datos de la sesión); se borra al cerrar sesión.
 */
const PREFIJO = 'csj.cache.';
const CLAVE_INDICE = `${PREFIJO}indice`;
const MAX_CONSULTAS = 8;

export interface ConsultaGuardada<T> { datos: T; sincronizado_en: string; }

function leerIndice(): string[] {
  try { return JSON.parse(localStorage.getItem(CLAVE_INDICE) ?? '[]') as string[]; } catch { return []; }
}

export function guardarConsulta<T>(clave: string, datos: T): void {
  try {
    const indice = [clave, ...leerIndice().filter((c) => c !== clave)];
    for (const vieja of indice.slice(MAX_CONSULTAS)) localStorage.removeItem(PREFIJO + vieja);
    localStorage.setItem(CLAVE_INDICE, JSON.stringify(indice.slice(0, MAX_CONSULTAS)));
    localStorage.setItem(PREFIJO + clave, JSON.stringify({ datos, sincronizado_en: new Date().toISOString() } satisfies ConsultaGuardada<T>));
  } catch { /* almacenamiento lleno o bloqueado: la app sigue funcionando sin caché */ }
}

export function leerConsulta<T>(clave: string): ConsultaGuardada<T> | null {
  try {
    const crudo = localStorage.getItem(PREFIJO + clave);
    return crudo ? JSON.parse(crudo) as ConsultaGuardada<T> : null;
  } catch { return null; }
}

/** Al cerrar sesión: borra las consultas guardadas y pide al Service Worker vaciar su caché pública. */
export function limpiarCachesSensibles(): void {
  try {
    for (const clave of Object.keys(localStorage)) if (clave.startsWith(PREFIJO)) localStorage.removeItem(clave);
  } catch { /* nada que limpiar */ }
  if ('serviceWorker' in navigator) {
    void navigator.serviceWorker.ready.then((r) => r.active?.postMessage({ tipo: 'limpiar-caches' })).catch(() => undefined);
  }
  if ('caches' in window) void caches.keys().then((nombres) => nombres.filter((n) => n.startsWith('csj-publico')).forEach((n) => void caches.delete(n)));
}

/** Estado de la conexión del navegador; `reconexiones` sube cada vez que vuelve la red (para recargar datos). */
export function useEnLinea() {
  const [enLinea, setEnLinea] = useState(() => navigator.onLine);
  const [reconexiones, setReconexiones] = useState(0);
  useEffect(() => {
    const alVolver = () => { setEnLinea(true); setReconexiones((n) => n + 1); };
    const alPerder = () => setEnLinea(false);
    window.addEventListener('online', alVolver);
    window.addEventListener('offline', alPerder);
    return () => { window.removeEventListener('online', alVolver); window.removeEventListener('offline', alPerder); };
  }, []);
  return { enLinea, reconexiones };
}
