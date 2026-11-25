import { useSyncExternalStore } from 'react';

/** Temas de la identidad: Claro editorial (por defecto) y Grafito turquesa. */
export type Tema = 'light' | 'dark';

export const CLAVE_TEMA = 'csj-theme';
/** Color de la barra del navegador por tema (meta theme-color). */
export const COLOR_BARRA: Record<Tema, string> = { light: '#f6f4ef', dark: '#0d1015' };

const leerTema = (): Tema => (document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light');

function suscribir(avisar: () => void) {
  const observador = new MutationObserver(avisar);
  observador.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  return () => observador.disconnect();
}

/**
 * Tema activo, sincronizado con el atributo data-theme de <html>
 * (lo fija public/tema-inicial.js antes del primer pintado y lo cambia ThemeToggle).
 */
export function useTema(): Tema {
  return useSyncExternalStore(suscribir, leerTema, () => 'light');
}

/** Lee un token de color del sistema de diseño (para librerías que no aceptan CSS, como Leaflet). */
export function colorDeToken(token: string, respaldo: string): string {
  const valor = getComputedStyle(document.documentElement).getPropertyValue(token).trim();
  return valor || respaldo;
}
