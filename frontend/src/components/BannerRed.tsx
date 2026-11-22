import { useEffect, useState } from 'react';
import { useAuth } from '../context/useAuth';
import { useEnLinea } from '../services/offline';
import { cargarCola, descartar, descartarAvisoEnviados, enviarComoDistinto, reintentar, sincronizar, useColaOffline } from '../services/colaOffline';
import { fechaHora } from '../utils/formato';
import { Icon, type IconName } from './Icon';

const REINTENTO_MS = 30_000;

/** HU-08.4: estado de red y cola de envío. Textos exactos: «Sin conexión», «Guardado para enviar», «Enviando», «No se pudo enviar». */
export function BannerRed() {
  const { usuario } = useAuth();
  const { enLinea, reconexiones } = useEnLinea();
  const cola = useColaOffline();
  const [abierto, setAbierto] = useState(false);
  const usuarioId = usuario?.id ?? null;

  useEffect(() => { cargarCola(usuarioId); }, [usuarioId]);
  const pendientes = cola.borradores.filter((b) => b.estado === 'pendiente');
  const fallidos = cola.borradores.filter((b) => b.estado === 'error' || b.estado === 'conflicto');
  const enviando = cola.sincronizando || cola.borradores.some((b) => b.estado === 'enviando');

  // Sincroniza al volver la red, al abrir la app con pendientes y cada 30 s mientras haya pendientes.
  useEffect(() => {
    if (!usuarioId || !enLinea || pendientes.length === 0) return;
    void sincronizar(usuarioId);
    const t = window.setInterval(() => void sincronizar(usuarioId), REINTENTO_MS);
    return () => window.clearInterval(t);
  }, [usuarioId, enLinea, reconexiones, pendientes.length]);

  let estado: { texto: string; icono: IconName; tono: 'warning' | 'info' | 'error' } | null = null;
  if (enviando) estado = { texto: 'Enviando', icono: 'clock', tono: 'info' };
  else if (!enLinea) estado = { texto: 'Sin conexión', icono: 'alert', tono: 'warning' };
  else if (fallidos.length > 0) estado = { texto: 'No se pudo enviar', icono: 'alert', tono: 'error' };
  else if (pendientes.length > 0) estado = { texto: 'Guardado para enviar', icono: 'inbox', tono: 'info' };

  if (!estado && cola.ultimosFolios.length === 0) return null;
  const detalle = !enLinea && pendientes.length > 0 ? `${pendientes.length} reporte(s) guardado(s) para enviar al volver la conexión.` : !enLinea ? 'Puedes seguir consultando lo último que guardamos y crear reportes: se enviarán al recuperar la red.' : '';

  return (
    <div className="net-banner-wrap">
      {estado && (
        <div className={`net-banner net-banner--${estado.tono}`} role={estado.tono === 'error' ? 'alert' : 'status'} aria-live={estado.tono === 'error' ? 'assertive' : 'polite'}>
          <Icon name={estado.icono} size={18} />
          <strong>{estado.texto}</strong>
          {detalle && <span>{detalle}</span>}
          {cola.borradores.length > 0 && (
            <button className="link-button" type="button" aria-expanded={abierto} aria-controls="cola-offline" onClick={() => setAbierto((v) => !v)}>
              {abierto ? 'Ocultar reportes' : `Ver reportes (${cola.borradores.length})`}
            </button>
          )}
        </div>
      )}
      {cola.ultimosFolios.length > 0 && (
        <div className="net-banner net-banner--ok" role="status">
          <Icon name="checkCircle" size={18} />
          <strong>Enviado</strong>
          <span>{cola.ultimosFolios.length === 1 ? 'Tu reporte guardado se envió: ' : 'Tus reportes guardados se enviaron: '}{cola.ultimosFolios.map((f) => <a key={f} href={`/reportes/${f}`}>{f} </a>)}</span>
          <button className="link-button" type="button" onClick={descartarAvisoEnviados}>Cerrar</button>
        </div>
      )}
      {abierto && cola.borradores.length > 0 && usuarioId && (
        <ul id="cola-offline" className="net-queue" aria-label="Reportes guardados en este dispositivo">
          {cola.borradores.map((b) => (
            <li key={b.id} className={`net-queue__item net-queue__item--${b.estado}`}>
              <div>
                <strong>{b.payload.tipo_dano}</strong> · {b.payload.calle}
                <span className="net-queue__meta">Guardado {fechaHora(b.creado_en)} · {b.estado === 'enviando' ? 'Enviando' : b.estado === 'pendiente' ? 'Guardado para enviar' : 'No se pudo enviar'}</span>
                {b.mensaje && <span className="net-queue__motivo">{b.mensaje}</span>}
                {b.candidatos && b.candidatos.length > 0 && <span className="net-queue__motivo">Reporte cercano: {b.candidatos.map((f) => <a key={f} href={`/reportes/${f}`}>{f} </a>)}</span>}
              </div>
              <div className="net-queue__acciones">
                {b.estado === 'conflicto' && <button className="button button--secondary button--sm" type="button" onClick={() => enviarComoDistinto(usuarioId, b.id)}>Enviar como daño distinto</button>}
                {b.estado === 'error' && <button className="button button--secondary button--sm" type="button" onClick={() => reintentar(usuarioId, b.id)}>Reintentar</button>}
                <button className="button button--quiet button--sm" type="button" onClick={() => descartar(usuarioId, b.id)}><Icon name="trash" size={16} />Descartar</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
