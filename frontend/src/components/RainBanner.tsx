import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { PronosticoResponse } from '../types/api';

export function RainBanner() {
  const [pronostico, setPronostico] = useState<PronosticoResponse | null>(null);
  const [estado, setEstado] = useState<'cargando' | 'listo' | 'error'>('cargando');

  useEffect(() => {
    let activo = true;
    const cargar = async () => {
      try {
        const respuesta = await api.get<PronosticoResponse>('/api/v1/clima/pronostico');
        if (activo) { setPronostico(respuesta); setEstado('listo'); }
      } catch { if (activo) setEstado('error'); }
    };
    void cargar();
    return () => { activo = false; };
  }, []);

  if (estado === 'cargando') return <div className="rain-banner rain-banner--loading" role="status">Consultando el pronóstico de lluvia…</div>;
  if (estado === 'error' || !pronostico) return <div className="rain-banner rain-banner--error" role="status"><span aria-hidden="true">⚠️</span> Pronóstico no disponible. Consulta nuevamente más tarde.</div>;
  if (!pronostico.alerta_lluvia) return null;
  return <aside className="rain-banner rain-banner--alert" aria-label="Aviso de lluvia"><span className="rain-banner__icon" aria-hidden="true">🌧️</span><div><strong>Aviso de lluvia</strong><p>{pronostico.mensaje_alerta ?? 'Se esperan lluvias. Consulta las calles con riesgo de inundación antes de salir.'}</p></div><a href="/?zona=riesgo">Ver calles en riesgo</a></aside>;
}
