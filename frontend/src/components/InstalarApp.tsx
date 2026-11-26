import { useInstalacion } from '../hooks/useInstalacion';
import { Icon } from './Icon';

const APARTADO = 'instalar-app';

/** Lleva al apartado del pie (estado e instrucciones) y le pone el foco. */
function irAlApartado() {
  const apartado = document.getElementById(APARTADO);
  if (!apartado) return;
  const sinMovimiento = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  apartado.focus({ preventScroll: true });
  apartado.scrollIntoView?.({ behavior: sinMovimiento ? 'auto' : 'smooth', block: 'center' });
}

/**
 * HU-08.4: botón permanente junto a la marca. Con `beforeinstallprompt` abre el diálogo nativo;
 * sin él (o ya instalada) lleva a la guía del pie, para que siempre responda.
 */
export function InstalarApp() {
  const { estado, instalar } = useInstalacion();
  const alPulsar = () => { if (estado === 'disponible') void instalar(); else irAlApartado(); };
  return <button className="button button--secondary button--sm install-button" type="button" onClick={alPulsar}><Icon name="download" size={16} />Instalar app</button>;
}

/** HU-08.4: apartado del pie, siempre visible, que explica en qué estado está la instalación. */
export function SeccionInstalacion() {
  const { estado, instalar } = useInstalacion();
  return (
    <section id={APARTADO} className="instalacion" tabIndex={-1} aria-labelledby="instalacion-titulo">
      <h2 id="instalacion-titulo" className="instalacion__titulo">Calles Seguras en tu dispositivo</h2>
      <div role="status">
        {estado === 'instalada' && <p className="instalacion__lista"><Icon name="check" size={16} />La aplicación ya está instalada en este dispositivo.</p>}
        {estado === 'disponible' && <p>Instálala para abrirla desde tu pantalla de inicio.</p>}
        {estado === 'no-disponible' && <p>Tu navegador todavía no ofrece la instalación automática. En Chrome o Edge, busca «Instalar aplicación» en el menú del navegador; en iPhone o iPad, usa «Compartir» y después «Agregar a pantalla de inicio».</p>}
      </div>
      {estado === 'disponible' && <button className="button button--secondary" type="button" onClick={() => void instalar()}><Icon name="download" size={18} />Instalar aplicación</button>}
    </section>
  );
}
