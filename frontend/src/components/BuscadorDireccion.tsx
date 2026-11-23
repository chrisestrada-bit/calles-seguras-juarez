import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { api, ApiError } from '../services/api';
import { Icon } from './Icon';
import type { GeocodingResponse, GeocodingResultado, Ubicacion } from '../types/api';

const MIN_CARACTERES = 3;
const ESPERA_MS = 400;
const enJuarez = (p: Ubicacion) => p.latitud >= 31.45 && p.latitud <= 31.8 && p.longitud >= -106.65 && p.longitud <= -106.25;

export type Punto = { ubicacion: Ubicacion; etiqueta: string } | null;

/** Campo de dirección con sugerencias (combobox + listbox, accesible con teclado) y GPS opcional. */
export function BuscadorPunto({ id, etiqueta, valor, onElegir, conGps }: { id: string; etiqueta: string; valor: Punto; onElegir: (p: Punto) => void; conGps?: boolean }) {
  const [texto, setTexto] = useState('');
  const [resultados, setResultados] = useState<GeocodingResultado[]>([]);
  const [abierto, setAbierto] = useState(false);
  const [activo, setActivo] = useState(-1);
  const [estado, setEstado] = useState('');
  const peticion = useRef(0);
  const listaId = `${id}-sugerencias`;

  const consultar = useCallback(async (consulta: string) => {
    const n = ++peticion.current;
    setEstado('Buscando…');
    try {
      const r = await api.get<GeocodingResponse>(`/api/v1/geocoding/buscar?q=${encodeURIComponent(consulta)}&limite=5`);
      if (n !== peticion.current) return;
      setResultados(r.datos); setActivo(-1); setAbierto(r.datos.length > 0);
      setEstado(r.datos.length ? `${r.datos.length} ${r.datos.length === 1 ? 'sugerencia disponible' : 'sugerencias disponibles'}.` : r.mensaje ?? 'Sin resultados dentro de Ciudad Juárez.');
    } catch (e) {
      if (n !== peticion.current) return;
      setResultados([]); setAbierto(false);
      setEstado(e instanceof ApiError ? e.message : 'No pudimos buscar la dirección.');
    }
  }, []);

  // Sugerencias al escribir (debounce); las respuestas obsoletas se descartan con `peticion`.
  useEffect(() => {
    const consulta = texto.trim();
    if (consulta.length < MIN_CARACTERES) return;
    const t = setTimeout(() => { void consultar(consulta); }, ESPERA_MS);
    return () => clearTimeout(t);
  }, [texto, consultar]);

  const cambiar = (v: string) => {
    setTexto(v);
    if (v.trim().length < MIN_CARACTERES) { peticion.current++; setResultados([]); setAbierto(false); setActivo(-1); }
  };
  const buscar = () => {
    const consulta = texto.trim();
    if (consulta.length < MIN_CARACTERES) { setEstado(`Escribe al menos ${MIN_CARACTERES} caracteres.`); return; }
    void consultar(consulta);
  };
  const elegir = (r: GeocodingResultado) => {
    peticion.current++;
    onElegir({ ubicacion: r.ubicacion, etiqueta: r.etiqueta });
    setResultados([]); setAbierto(false); setActivo(-1); setTexto(''); setEstado('');
  };
  const teclas = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown' && resultados.length) { e.preventDefault(); setAbierto(true); setActivo((i) => (i + 1) % resultados.length); }
    else if (e.key === 'ArrowUp' && resultados.length) { e.preventDefault(); setAbierto(true); setActivo((i) => (i <= 0 ? resultados.length - 1 : i - 1)); }
    else if (e.key === 'Escape' && abierto) { e.preventDefault(); setAbierto(false); setActivo(-1); }
    else if (e.key === 'Enter') { e.preventDefault(); if (abierto && activo >= 0) elegir(resultados[activo]); else buscar(); }
  };
  const gps = () => {
    if (!navigator.geolocation) { setEstado('Tu navegador no permite obtener la ubicación.'); return; }
    setEstado('Tu navegador te pedirá permiso para usar tu ubicación; sólo se usa como punto de origen.');
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      const u = { latitud: Number(coords.latitude.toFixed(6)), longitud: Number(coords.longitude.toFixed(6)) };
      if (!enJuarez(u)) { setEstado('Tu ubicación está fuera de Ciudad Juárez.'); return; }
      onElegir({ ubicacion: u, etiqueta: 'Mi ubicación' }); setEstado('');
    }, () => setEstado('No pudimos obtener tu ubicación.'));
  };
  const mostrar = abierto && resultados.length > 0;
  return (
    <fieldset className="trayecto-punto">
      <legend>{etiqueta}</legend>
      {valor && <p className="location-readout"><Icon name="pin" size={16} /><span>{valor.etiqueta} ({valor.ubicacion.latitud.toFixed(5)}, {valor.ubicacion.longitud.toFixed(5)})</span></p>}
      <label htmlFor={id}>Dirección, cruce o colonia</label>
      <div className="inline-form">
        <div className="autocomplete">
          <input
            id={id} value={texto} autoComplete="off" role="combobox" aria-expanded={mostrar} aria-controls={listaId} aria-autocomplete="list"
            aria-activedescendant={mostrar && activo >= 0 ? `${listaId}-${activo}` : undefined}
            onChange={(e) => cambiar(e.target.value)} onKeyDown={teclas} onBlur={() => setAbierto(false)}
            onFocus={() => { if (resultados.length) setAbierto(true); }}
            placeholder="Ej. Tecnológico y Ejército Nacional"
          />
          <ul id={listaId} className="autocomplete__lista" role="listbox" aria-label={`Sugerencias de ${etiqueta.toLowerCase()}`} hidden={!mostrar}>
            {resultados.map((r, i) => (
              <li
                key={`${r.etiqueta}-${r.ubicacion.latitud}-${r.ubicacion.longitud}`} id={`${listaId}-${i}`} role="option" aria-selected={i === activo}
                className={i === activo ? 'is-active' : ''} onMouseDown={(e) => e.preventDefault()} onClick={() => elegir(r)}
              >
                <Icon name="pin" size={18} /><span>{r.etiqueta}</span>
              </li>
            ))}
          </ul>
        </div>
        <button className="button button--secondary" type="button" onClick={buscar}><Icon name="search" size={18} />Buscar</button>
      </div>
      {conGps && <button className="button button--quiet button--sm" type="button" onClick={gps}><Icon name="locate" size={16} />Usar mi ubicación</button>}
      {estado && <p className="field-help" role="status">{estado}</p>}
    </fieldset>
  );
}
