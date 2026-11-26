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

/** Navegador/sistema para elegir los pasos manuales de instalación. */
export type Plataforma = 'ios' | 'android-samsung' | 'android-firefox' | 'android-edge' | 'android' | 'escritorio-firefox' | 'escritorio-safari' | 'escritorio';

export function detectarPlataforma(agente: string = navigator.userAgent, puntosTactiles: number = navigator.maxTouchPoints): Plataforma {
  // iPadOS se presenta como Macintosh; la pantalla táctil lo delata.
  if (/iPhone|iPad|iPod/.test(agente) || (/Macintosh/.test(agente) && puntosTactiles > 1)) return 'ios';
  if (/Android/.test(agente)) {
    if (/SamsungBrowser/.test(agente)) return 'android-samsung';
    if (/Firefox/.test(agente)) return 'android-firefox';
    return /EdgA/.test(agente) ? 'android-edge' : 'android';
  }
  if (/Firefox/.test(agente)) return 'escritorio-firefox';
  if (/Safari/.test(agente) && !/Chrome|Chromium|Edg|OPR/.test(agente)) return 'escritorio-safari';
  return 'escritorio';
}

let evento: EventoInstalacion | null = null;
let guiaAbierta = false;
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
  avisar(); // ya se consumió: otro clic debe llevar a la guía aunque el diálogo no haya respondido
  try {
    await pendiente.prompt();
    const eleccion = await pendiente.userChoice;
    if (eleccion.outcome === 'accepted') recienInstalada = true;
  } catch { /* el navegador rechazó el diálogo: se muestran las instrucciones manuales */ }
  avisar();
}

const leerGuia = () => guiaAbierta;
/** La cabecera y el pie comparten la guía: cualquiera de los dos puede abrirla. */
function mostrarGuia(abierta: boolean): void { guiaAbierta = abierta; avisar(); }

export function useInstalacion() {
  return {
    estado: useSyncExternalStore(suscribir, leer),
    guiaAbierta: useSyncExternalStore(suscribir, leerGuia),
    instalar,
    mostrarGuia,
  };
}
