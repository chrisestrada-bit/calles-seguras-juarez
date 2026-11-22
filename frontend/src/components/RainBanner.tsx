import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { PronosticoResponse } from '../types/api';
import { Icon } from './Icon';

/** Ícono climático animado (nube con lluvia o sol); decorativo, el texto lleva la información. */
function ClimaIcono({ lluvia }: { lluvia: boolean }) {
  return (
    <svg className="wx" width="32" height="32" viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      {lluvia ? (
        <>
          <g className="wx-cloud-group">
            <path className="wx-cloud-back" d="M20 9.5a5.5 5.5 0 0 1 5.4 6.6A3.6 3.6 0 0 1 24.5 23H21" />
            <path className="wx-cloud" d="M9 21.5a5 5 0 0 1-.4-10 7 7 0 0 1 13.3 1.6A4.2 4.2 0 0 1 21.5 21.5Z" />
          </g>
          <line className="wx-drop" x1="11" y1="24" x2="10" y2="27" />
          <line className="wx-drop" x1="15.5" y1="24" x2="14.5" y2="27" />
          <line className="wx-drop" x1="20" y1="24" x2="19" y2="27" />
        </>
      ) : (
        <>
          <g className="wx-sun-rays">
            {Array.from({ length: 8 }, (_, i) => <line key={i} x1="16" y1="3.5" x2="16" y2="6.5" transform={`rotate(${i * 45} 16 16)`} />)}
          </g>
          <circle className="wx-sun-core" cx="16" cy="16" r="6" />
        </>
      )}
    </svg>
  );
}

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

  if (estado === 'cargando') return <div className="rain-banner rain-banner--loading" role="status"><div className="rain-banner__inner"><span className="skeleton skeleton--dot" aria-hidden="true" /><span>Consultando el pronóstico de lluvia…</span></div></div>;
  if (estado === 'error' || !pronostico) return <div className="rain-banner rain-banner--error" role="status"><div className="rain-banner__inner"><Icon name="info" size={18} /><span>Pronóstico no disponible. Consulta nuevamente más tarde.</span></div></div>;

  const lluvia = pronostico.alerta_lluvia;
  const maxProb = pronostico.proximas_horas?.length ? Math.max(...pronostico.proximas_horas.map((h) => h.probabilidad_lluvia_pct)) : null;
  const actual = pronostico.actual;

  return (
    <aside className={`rain-banner ${lluvia ? 'rain-banner--alert' : 'rain-banner--clear'}`} aria-label={lluvia ? 'Aviso de lluvia' : 'Clima actual'}>
      <div className="rain-banner__inner">
        <span className="rain-banner__icon"><ClimaIcono lluvia={lluvia} /></span>
        <div className="rain-banner__body">
          <p className="rain-banner__title">
            {actual && <span className="rain-banner__temp tabular">{Math.round(actual.temperatura_c)} °C</span>}
            <span>{lluvia ? 'Aviso de lluvia' : pronostico.ubicacion || 'Ciudad Juárez'}</span>
            {lluvia
              ? <span className="rain-banner__chip rain-banner__chip--alert"><Icon name="rain" size={14} />Riesgo de encharcamientos</span>
              : <span className="rain-banner__chip rain-banner__chip--ok"><Icon name="checkCircle" size={14} />Sin aviso de lluvia</span>}
            {pronostico.desactualizado && <span className="rain-banner__chip rain-banner__chip--stale"><Icon name="clock" size={14} />Datos desactualizados</span>}
          </p>
          <p className="rain-banner__meta">
            {lluvia
              ? pronostico.mensaje_alerta ?? 'Se esperan lluvias. Consulta las calles con riesgo de inundación antes de salir.'
              : <>{actual?.descripcion ? `${actual.descripcion.charAt(0).toUpperCase()}${actual.descripcion.slice(1)}` : 'Condiciones estables'}{maxProb !== null && <> · Probabilidad de lluvia en las próximas horas: <span className="tabular">{Math.round(maxProb)} %</span></>}</>}
          </p>
        </div>
        {lluvia && <a className="rain-banner__link" href="/?zona=riesgo">Ver calles en riesgo <Icon name="arrowRight" size={16} /></a>}
      </div>
    </aside>
  );
}
