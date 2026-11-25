import { CLAVE_TEMA, COLOR_BARRA, useTema, type Tema } from '../hooks/useTema';
import { Icon } from './Icon';

/** El script public/tema-inicial.js ya fijó data-theme antes del primer pintado; aquí sólo se alterna. */
function aplicarTema(tema: Tema) {
  const raiz = document.documentElement;
  raiz.classList.add('theme-switching');
  window.setTimeout(() => raiz.classList.remove('theme-switching'), 320);
  raiz.setAttribute('data-theme', tema);
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', COLOR_BARRA[tema]);
}

/**
 * Interruptor accesible entre Claro editorial (por defecto) y Grafito turquesa.
 * La preferencia se guarda en localStorage; sin preferencia la app arranca en claro.
 */
export function ThemeToggle() {
  const oscuro = useTema() === 'dark';

  const alternar = () => {
    const siguiente: Tema = oscuro ? 'light' : 'dark';
    aplicarTema(siguiente);
    try { localStorage.setItem(CLAVE_TEMA, siguiente); } catch { /* almacenamiento no disponible: el cambio aplica sólo a esta visita */ }
  };

  return (
    <button
      className={`theme-toggle${oscuro ? ' is-dark' : ''}`}
      type="button"
      role="switch"
      aria-checked={oscuro}
      onClick={alternar}
      aria-label="Tema oscuro Grafito turquesa"
      title={oscuro ? 'Cambiar a Claro editorial' : 'Cambiar a Grafito turquesa (oscuro)'}
    >
      <span className="theme-toggle__icons" aria-hidden="true">
        <Icon name="moon" size={20} className="theme-toggle__moon" />
        <Icon name="sun" size={20} className="theme-toggle__sun" />
      </span>
    </button>
  );
}
