import { useSyncExternalStore } from 'react';

/** HU-08.4: estado de instalación de la PWA. */
export type EstadoInstalacion = 'disponible' | 'instalada' | 'no-disponible';

interface EventoInstalacion extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

const MODO_APP = '(display-mode: standalone)';
const consultaModo = () => (typeof window.matchMedia === 'function' ? window.matchMedia(MODO_APP) : null);
const abiertaComoApp = () => Boolean(consultaModo()?.matches) || (navigator as Navigator & { standalone?: boolean }).standalone === true;

let evento: EventoInstalacion | null = null;
let recienInstalada = false;
const suscriptores = new Set<() => void>();
const avisar = () => suscriptores.forEach((s) => s());

// Se escucha desde que carga el módulo: el navegador puede disparar el evento antes de que React monte la cabecera.
window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); evento = e as EventoInstalacion; recienInstalada = false; avisar(); });
window.addEventListener('appinstalled', () => { evento = null; recienInstalada = true; avisar(); });
consultaModo()?.addEventListener?.('change', avisar);

const suscribir = (s: () => void) => { suscriptores.add(s); return () => { suscriptores.delete(s); }; };
const leer = (): EstadoInstalacion => (recienInstalada || abiertaComoApp() ? 'instalada' : evento ? 'disponible' : 'no-disponible');

/** Abre el diálogo nativo. El aviso del navegador sólo se puede usar una vez. */
async function instalar(): Promise<void> {
  const pendiente = evento;
  if (!pendiente) return;
  evento = null;
  try {
    await pendiente.prompt();
    const eleccion = await pendiente.userChoice;
    if (eleccion.outcome === 'accepted') recienInstalada = true;
  } catch { /* el navegador rechazó el diálogo: se muestran las instrucciones manuales */ }
  avisar();
}

export function useInstalacion() {
  return { estado: useSyncExternalStore(suscribir, leer), instalar };
}
