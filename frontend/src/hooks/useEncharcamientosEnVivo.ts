import { useEffect, useRef, useState } from 'react';
import { api, urlWebSocket } from '../services/api';
import type { EventoEnVivo, ReporteResumenPublico, RespuestaPaginada } from '../types/api';
import type { Vivos } from '../utils/enVivo';

export type EstadoEnVivo = 'conectando' | 'en_vivo' | 'reconectando';

/** Respaldo por sondeo HTTP: con el WebSocket caído, un encharcamiento nuevo aparece en <= 15 s (+ el viaje de red). */
export const INTERVALO_SONDEO_MS = 15_000;
const ESPERA_MIN_MS = 1_000;
const ESPERA_MAX_MS = 15_000;
const MAX_EVENTOS_VISTOS = 300;
const RUTA_SONDEO = '/api/v1/reportes?tipo_dano=Encharcamiento&por_pagina=50&orden=recientes';

/**
 * HU-08.3 + extra 4.5: encharcamientos en vivo mientras la consulta está abierta.
 * - WebSocket `/api/v1/ws/encharcamientos` con reconexión exponencial y vigilancia del latido del servidor.
 * - Si el canal cae, sondea la API cada 15 s hasta reconectar (respaldo garantizado <= 30 s).
 * - Los eventos se deduplican por `event_id` y se guardan por folio (nunca hay dos entradas del mismo reporte).
 */
export function useEncharcamientosEnVivo(activo: boolean) {
  const [estado, setEstado] = useState<EstadoEnVivo>('conectando');
  const [vivos, setVivos] = useState<Vivos>({});
  const vistos = useRef<string[]>([]);

  useEffect(() => {
    if (!activo) return;
    let cerrado = false;
    let socket: WebSocket | null = null;
    let espera = ESPERA_MIN_MS;
    let temporizadorReconexion: number | undefined;
    let vigilante: number | undefined;
    let sondeo: number | undefined;

    const aplicar = (folio: string, reporte: ReporteResumenPublico | null) => setVivos((actual) => ({ ...actual, [folio]: reporte }));

    const sondear = () => {
      api.get<RespuestaPaginada<ReporteResumenPublico>>(RUTA_SONDEO)
        .then((r) => { if (!cerrado) setVivos((actual) => ({ ...actual, ...Object.fromEntries(r.datos.map((d) => [d.folio, d])) })); })
        .catch(() => undefined); // sin red: se reintenta en el siguiente ciclo
    };
    const iniciarSondeo = () => { if (sondeo === undefined) { sondear(); sondeo = window.setInterval(sondear, INTERVALO_SONDEO_MS); } };
    const detenerSondeo = () => { window.clearInterval(sondeo); sondeo = undefined; };

    const alPerderCanal = () => {
      window.clearTimeout(vigilante);
      if (cerrado) return;
      setEstado('reconectando');
      iniciarSondeo();
      temporizadorReconexion = window.setTimeout(conectar, espera);
      espera = Math.min(espera * 2, ESPERA_MAX_MS);
    };

    const conectar = () => {
      if (cerrado) return;
      let ws: WebSocket;
      try { ws = new WebSocket(urlWebSocket('/api/v1/ws/encharcamientos')); } catch { alPerderCanal(); return; }
      socket = ws;
      const vigilar = (segundos: number) => {
        window.clearTimeout(vigilante);
        vigilante = window.setTimeout(() => ws.close(), segundos * 2500); // sin latido en 2.5 intervalos: reconectar
      };
      ws.onmessage = (mensaje) => {
        let evento: EventoEnVivo;
        try { evento = JSON.parse(String(mensaje.data)) as EventoEnVivo; } catch { return; }
        if (evento.tipo === 'hola') {
          espera = ESPERA_MIN_MS; setEstado('en_vivo'); detenerSondeo(); sondear(); // sondeo único al reconectar: cubre lo perdido
          vigilar(evento.heartbeat_segundos ?? 20);
          return;
        }
        if (evento.tipo === 'ping') { ws.send(JSON.stringify({ tipo: 'pong' })); vigilar(20); return; }
        if (!evento.event_id || vistos.current.includes(evento.event_id)) return; // deduplicación por event_id
        vistos.current = [...vistos.current.slice(-(MAX_EVENTOS_VISTOS - 1)), evento.event_id];
        if (evento.tipo === 'encharcamiento.retirado') aplicar(evento.folio, null);
        else if (evento.reporte) aplicar(evento.folio, evento.reporte);
      };
      ws.onclose = () => { if (socket === ws) alPerderCanal(); };
      ws.onerror = () => ws.close();
    };

    conectar();
    return () => {
      cerrado = true;
      window.clearTimeout(temporizadorReconexion);
      window.clearTimeout(vigilante);
      detenerSondeo();
      if (socket) { socket.onclose = null; socket.close(); }
    };
  }, [activo]);

  return { estado, vivos };
}
