import { useEffect, useState } from 'react';
import { Icon } from './Icon';

interface EventoInstalacion extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

/** HU-08.4: botón discreto de instalación; sólo existe cuando el navegador dispara `beforeinstallprompt`. */
export function InstalarApp() {
  const [evento, setEvento] = useState<EventoInstalacion | null>(null);

  useEffect(() => {
    const alOfrecer = (e: Event) => { e.preventDefault(); setEvento(e as EventoInstalacion); };
    const alInstalar = () => setEvento(null);
    window.addEventListener('beforeinstallprompt', alOfrecer);
    window.addEventListener('appinstalled', alInstalar);
    return () => { window.removeEventListener('beforeinstallprompt', alOfrecer); window.removeEventListener('appinstalled', alInstalar); };
  }, []);

  if (!evento) return null;
  const instalar = async () => {
    await evento.prompt();
    await evento.userChoice.catch(() => undefined);
    setEvento(null); // el aviso sólo se puede usar una vez
  };
  return <button className="button button--quiet button--sm install-button" type="button" onClick={() => void instalar()}><Icon name="download" size={16} />Instalar app</button>;
}
