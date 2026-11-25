import { useInstalacion } from '../hooks/useInstalacion';
import { Icon } from './Icon';

/** HU-08.4: botón de la cabecera; aparece cuando el navegador ofrece instalar (`beforeinstallprompt`). */
export function InstalarApp() {
  const { estado, instalar } = useInstalacion();
  if (estado !== 'disponible') return null;
  return <button className="button button--secondary button--sm install-button" type="button" onClick={() => void instalar()}><Icon name="download" size={16} />Instalar aplicación</button>;
}

/** HU-08.4: apartado del pie, siempre visible, que explica en qué estado está la instalación. */
export function SeccionInstalacion() {
  const { estado, instalar } = useInstalacion();
  return (
    <section className="instalacion" aria-labelledby="instalacion-titulo">
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
