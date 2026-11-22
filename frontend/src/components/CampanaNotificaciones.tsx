import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import { fechaHora } from '../utils/formato';
import type { PaginaNotificaciones } from '../types/api';
import { Icon } from './Icon';

const SONDEO_MS = 60_000;

/** HU-08.2: campana con contador de no leídas. Al elegir un aviso se marca como leído y se abre el reporte. */
export function CampanaNotificaciones() {
  const [datos, setDatos] = useState<PaginaNotificaciones | null>(null);
  const [error, setError] = useState(false);
  const [abierta, setAbierta] = useState(false);
  const caja = useRef<HTMLDivElement>(null);

  const cargar = useCallback(() => {
    api.get<PaginaNotificaciones>('/api/v1/notificaciones?por_pagina=10')
      .then((r) => { setDatos(r); setError(false); })
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    cargar();
    const t = window.setInterval(cargar, SONDEO_MS);
    window.addEventListener('focus', cargar);
    return () => { window.clearInterval(t); window.removeEventListener('focus', cargar); };
  }, [cargar]);

  useEffect(() => {
    if (!abierta) return;
    const cerrarFuera = (e: MouseEvent) => { if (!caja.current?.contains(e.target as Node)) setAbierta(false); };
    const cerrarEsc = (e: KeyboardEvent) => { if (e.key === 'Escape') setAbierta(false); };
    document.addEventListener('mousedown', cerrarFuera);
    document.addEventListener('keydown', cerrarEsc);
    return () => { document.removeEventListener('mousedown', cerrarFuera); document.removeEventListener('keydown', cerrarEsc); };
  }, [abierta]);

  const noLeidas = datos?.no_leidas ?? 0;
  const abrirAviso = async (id: string, folio: string, leida: boolean) => {
    if (!leida) await api.patch(`/api/v1/notificaciones/${id}/leer`, {}).catch(() => undefined);
    window.location.assign(`/reportes/${encodeURIComponent(folio)}`);
  };
  const leerTodas = async () => { await api.patch('/api/v1/notificaciones/leer-todas', {}).catch(() => undefined); cargar(); };

  return (
    <div className="bell" ref={caja}>
      <button className="bell__button" type="button" aria-expanded={abierta} aria-controls="panel-avisos" onClick={() => setAbierta((v) => !v)}>
        <Icon name="bell" size={20} />
        <span className="visually-hidden">Avisos sobre mis reportes. {noLeidas === 0 ? 'No tienes avisos sin leer.' : `${noLeidas} sin leer.`}</span>
        {noLeidas > 0 && <span className="bell__count" aria-hidden="true">{noLeidas > 9 ? '9+' : noLeidas}</span>}
      </button>
      {abierta && (
        <div id="panel-avisos" className="bell__panel" role="region" aria-label="Avisos sobre mis reportes">
          <div className="bell__head">
            <h2>Avisos</h2>
            {noLeidas > 0 && <button className="link-button" type="button" onClick={() => void leerTodas()}>Marcar todos como leídos</button>}
          </div>
          {error && !datos && <p className="field-help" role="alert">No pudimos cargar tus avisos. Intenta de nuevo más tarde.</p>}
          {datos && datos.datos.length === 0 && <p className="field-help">Aún no tienes avisos. Te avisaremos cuando cambie el estado de tus reportes.</p>}
          {datos && datos.datos.length > 0 && (
            <ul className="bell__list">
              {datos.datos.map((n) => (
                <li key={n.id}>
                  <button type="button" className={`bell__item${n.leida ? '' : ' is-unread'}`} onClick={() => void abrirAviso(n.id, n.folio, n.leida)}>
                    {!n.leida && <span className="bell__dot" aria-hidden="true" />}
                    <span className="bell__msg">{!n.leida && <span className="visually-hidden">Sin leer. </span>}{n.mensaje}</span>
                    <time dateTime={n.created_at}>{fechaHora(n.created_at)}</time>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
