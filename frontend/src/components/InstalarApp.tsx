import { detectarPlataforma, useInstalacion, type Plataforma } from '../hooks/useInstalacion';
import { Icon } from './Icon';

const APARTADO = 'instalar-app';
const GUIA = 'instalar-app-pasos';

const PASOS: Record<Plataforma, { titulo: string; pasos: string[] }> = {
  ios: { titulo: 'En iPhone o iPad', pasos: ['Abre esta página en Safari.', 'Toca «Compartir» (cuadro con una flecha hacia arriba).', 'Elige «Agregar a pantalla de inicio».', 'Confirma con «Agregar».'] },
  'android-samsung': { titulo: 'En Samsung Internet', pasos: ['Abre el menú (tres líneas).', 'Elige «Agregar página a».', 'Toca «Pantalla de inicio» y confirma.'] },
  'android-firefox': { titulo: 'En Firefox para Android', pasos: ['Abre el menú (tres puntos).', 'Toca «Instalar» o «Agregar a pantalla de inicio».', 'Confirma para crear el acceso.'] },
  'android-edge': { titulo: 'En Edge para Android', pasos: ['Abre el menú (tres puntos).', 'Elige «Agregar al teléfono».', 'Confirma con «Instalar».'] },
  android: { titulo: 'En Chrome para Android', pasos: ['Abre el menú (tres puntos).', 'Toca «Instalar aplicación» o «Agregar a pantalla principal».', 'Confirma con «Instalar».'] },
  'escritorio-firefox': { titulo: 'En Firefox para computadora', pasos: ['Es posible que tu versión de Firefox no permita instalar la aplicación.', 'Abre esta misma dirección en Chrome o Edge.', 'En el menú del navegador, elige la opción para instalar el sitio como aplicación.'] },
  'escritorio-safari': { titulo: 'En Safari para Mac', pasos: ['Abre el menú «Archivo» o el botón «Compartir».', 'Elige «Agregar al Dock».', 'Confirma con «Agregar».'] },
  escritorio: { titulo: 'En Chrome o Edge para computadora', pasos: ['Busca el ícono de instalación en la barra de direcciones.', 'Si no aparece, abre el menú del navegador y busca «Instalar» (en Edge, dentro de «Aplicaciones»).', 'Confirma con «Instalar».'] },
};

/** Lleva al apartado del pie (estado e instrucciones) y le pone el foco. */
function irAlApartado() {
  const apartado = document.getElementById(APARTADO);
  if (!apartado) return;
  const sinMovimiento = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  apartado.focus({ preventScroll: true });
  apartado.scrollIntoView?.({ behavior: sinMovimiento ? 'auto' : 'smooth', block: 'center' });
}

/** Intenta la instalación nativa; si no se logra, abre los pasos del pie y lleva a ellos. */
function useInstalarOGuiar() {
  const instalacion = useInstalacion();
  const instalarOGuiar = async () => {
    if (await instalacion.instalar()) return;
    instalacion.mostrarGuia(true);
    irAlApartado();
  };
  return { ...instalacion, instalarOGuiar };
}

/**
 * HU-08.4: botón permanente junto a la marca. Con `beforeinstallprompt` abre el diálogo nativo;
 * sin él (o si se cancela) abre los pasos del pie y, ya instalada, lleva al estado, para que siempre responda.
 */
export function InstalarApp() {
  const { estado, instalarOGuiar } = useInstalarOGuiar();
  const alPulsar = () => { if (estado === 'instalada') irAlApartado(); else void instalarOGuiar(); };
  return (
    <button className="button button--secondary button--sm install-button" type="button" onClick={alPulsar} aria-label={estado === 'no-disponible' ? 'Cómo instalar la app' : undefined}>
      <Icon name="download" size={16} />
      {estado === 'no-disponible' ? <span>Cómo instalar<span className="install-button__resto"> la app</span></span> : 'Instalar app'}
    </button>
  );
}

/** HU-08.4: apartado del pie, siempre visible, que explica en qué estado está la instalación. */
export function SeccionInstalacion() {
  const { estado, guiaAbierta, mostrarGuia, instalarOGuiar } = useInstalarOGuiar();
  const guia = PASOS[detectarPlataforma()];
  return (
    <section id={APARTADO} className="instalacion" tabIndex={-1} aria-labelledby="instalacion-titulo">
      <h2 id="instalacion-titulo" className="instalacion__titulo">Calles Seguras en tu dispositivo</h2>
      <div role="status">
        {estado === 'instalada' && <p className="instalacion__lista"><Icon name="check" size={16} />La aplicación ya está instalada en este dispositivo.</p>}
        {estado === 'disponible' && <p>Instálala para abrirla desde tu pantalla de inicio.</p>}
        {estado === 'no-disponible' && <p>Tu navegador no ofrece en este momento la instalación automática. Puedes instalarla desde su menú.</p>}
      </div>
      {estado === 'disponible' && <button className="button button--secondary" type="button" onClick={() => void instalarOGuiar()}><Icon name="download" size={18} />Instalar aplicación</button>}
      {estado === 'no-disponible' && (
        <>
          <button className="button button--secondary" type="button" aria-expanded={guiaAbierta} aria-controls={GUIA} onClick={() => mostrarGuia(!guiaAbierta)}>
            <Icon name="download" size={18} />{guiaAbierta ? 'Ocultar los pasos' : 'Cómo instalar la app'}
          </button>
          <div id={GUIA} className="instalacion__guia" hidden={!guiaAbierta}>
            <h3>{guia.titulo}</h3>
            <ol>{guia.pasos.map((paso) => <li key={paso}>{paso}</li>)}</ol>
            <p>Los nombres de las opciones pueden variar según la versión del navegador.</p>
          </div>
        </>
      )}
    </section>
  );
}
