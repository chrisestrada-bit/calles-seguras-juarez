import { useEffect, useState } from 'react';
import { Logo } from './Logo';

const CLAVE = 'csj-splash-visto';
const DURACION_MS = 900;
const SALIDA_MS = 280;

/** Sólo una vez por sesión, nunca con movimiento reducido ni en navegadores automatizados (pruebas e2e). */
function debeMostrarse(): boolean {
  try {
    if (navigator.webdriver) return false;
    if (!window.matchMedia || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return false;
    return sessionStorage.getItem(CLAVE) !== '1';
  } catch { return false; }
}

/**
 * Pantalla de bienvenida breve (~900 ms) con el logotipo oficial a color del tema activo.
 * Se omite con clic, con el botón «Omitir» o con Esc; no bloquea la carga de la app.
 */
export function Splash() {
  const [fase, setFase] = useState<'visible' | 'saliendo' | 'oculto'>(() => (debeMostrarse() ? 'visible' : 'oculto'));

  useEffect(() => {
    if (fase !== 'visible') return;
    try { sessionStorage.setItem(CLAVE, '1'); } catch { /* sin almacenamiento: puede volver a verse en la siguiente carga */ }
    const salir = window.setTimeout(() => setFase('saliendo'), DURACION_MS);
    const alTeclear = (e: KeyboardEvent) => { if (e.key === 'Escape') setFase('saliendo'); };
    window.addEventListener('keydown', alTeclear);
    return () => { window.clearTimeout(salir); window.removeEventListener('keydown', alTeclear); };
  }, [fase]);

  useEffect(() => {
    if (fase !== 'saliendo') return;
    const fin = window.setTimeout(() => setFase('oculto'), SALIDA_MS);
    return () => window.clearTimeout(fin);
  }, [fase]);

  if (fase === 'oculto') return null;
  return (
    <div className={`splash${fase === 'saliendo' ? ' is-leaving' : ''}`} onClick={() => setFase('saliendo')}>
      <div className="splash__marca">
        <Logo variante="color" size={112} className="splash__logo" />
        <p className="splash__nombre">Calles Seguras <span>Juárez</span></p>
        <span className="splash__barra" aria-hidden="true" />
      </div>
      <button type="button" className="splash__omitir" onClick={(e) => { e.stopPropagation(); setFase('saliendo'); }}>Omitir</button>
    </div>
  );
}
