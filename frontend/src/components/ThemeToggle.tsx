import { useEffect, useState } from 'react';
import { Icon } from './Icon';

type Tema = 'light' | 'dark';
const CLAVE = 'csj-theme';
const COLOR_BARRA: Record<Tema, string> = { light: '#f3f5f9', dark: '#0b1120' };

/** El script de index.html ya fijó data-theme antes del primer pintado; aquí sólo lo leemos. */
const temaActual = (): Tema => (document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light');

function aplicarTema(tema: Tema, animar: boolean) {
  const raiz = document.documentElement;
  if (animar) {
    raiz.classList.add('theme-switching');
    window.setTimeout(() => raiz.classList.remove('theme-switching'), 320);
  }
  raiz.setAttribute('data-theme', tema);
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', COLOR_BARRA[tema]);
}

const preferenciaGuardada = (): Tema | null => {
  try {
    const valor = localStorage.getItem(CLAVE);
    return valor === 'dark' || valor === 'light' ? valor : null;
  } catch { return null; }
};

export function ThemeToggle() {
  const [tema, setTema] = useState<Tema>(temaActual);

  // Sin preferencia guardada, seguir los cambios del sistema operativo.
  useEffect(() => {
    const consulta = window.matchMedia?.('(prefers-color-scheme: dark)');
    if (!consulta) return;
    const alCambiar = (e: MediaQueryListEvent) => {
      if (preferenciaGuardada()) return;
      const siguiente: Tema = e.matches ? 'dark' : 'light';
      aplicarTema(siguiente, true);
      setTema(siguiente);
    };
    consulta.addEventListener('change', alCambiar);
    return () => consulta.removeEventListener('change', alCambiar);
  }, []);

  const alternar = () => {
    const siguiente: Tema = tema === 'dark' ? 'light' : 'dark';
    aplicarTema(siguiente, true);
    try { localStorage.setItem(CLAVE, siguiente); } catch { /* almacenamiento no disponible: el cambio aplica sólo a esta visita */ }
    setTema(siguiente);
  };

  const oscuro = tema === 'dark';
  return (
    <button
      className={`theme-toggle${oscuro ? ' is-dark' : ''}`}
      type="button"
      onClick={alternar}
      aria-label={oscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
      title={oscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
    >
      <span className="theme-toggle__icons" aria-hidden="true">
        <Icon name="moon" size={20} className="theme-toggle__moon" />
        <Icon name="sun" size={20} className="theme-toggle__sun" />
      </span>
    </button>
  );
}
