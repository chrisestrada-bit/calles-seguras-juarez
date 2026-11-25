import { useId, useMemo, useState, type FormEvent, type KeyboardEvent } from 'react';
import { etiquetaColonia, filtrarColonias } from '../services/catalogos';
import { PATRON_FOLIO } from '../utils/enVivo';
import type { Colonia } from '../types/api';
import { Icon } from './Icon';

export interface CalleSugerida { calle: string; colonia: string }

interface Props {
  valor: string;
  onCambiar: (texto: string) => void;
  onEnviar: () => void;
  /** Catálogo de colonias activas (nombre y C.P.). */
  colonias: Colonia[];
  /** Calles que coinciden en los resultados vigentes de la búsqueda en vivo. */
  calles: CalleSugerida[];
  onElegirColonia: (colonia: Colonia) => void;
  onElegirCalle: (calle: string) => void;
}

type Opcion = { id: string; grupo: 'Folio' | 'Colonias' | 'Calles con reportes'; texto: string; detalle: string; icono: 'search' | 'pin' | 'road'; elegir: () => void };

/**
 * Buscador de la portada (HU-04.2) como combobox accesible (patrón WAI-ARIA 1.2):
 * sugiere el folio exacto, colonias por nombre o código postal (32xxx) y calles con reportes que coinciden.
 * Flechas para recorrer, Enter para elegir (o enviar si no hay opción activa) y Esc para cerrar.
 */
export function BuscadorCalle({ valor, onCambiar, onEnviar, colonias, calles, onElegirColonia, onElegirCalle }: Props) {
  const id = useId();
  const [abierto, setAbierto] = useState(false);
  const [activa, setActiva] = useState(-1);
  const q = valor.trim();

  const opciones = useMemo<Opcion[]>(() => {
    if (q.length < 2) return [];
    const lista: Opcion[] = [];
    const folio = q.match(PATRON_FOLIO)?.[0];
    if (folio) lista.push({ id: 'folio', grupo: 'Folio', texto: folio.toUpperCase(), detalle: 'Buscar este folio', icono: 'search', elegir: onEnviar });
    for (const c of filtrarColonias(colonias, q, 5)) {
      lista.push({ id: `colonia-${c.id}`, grupo: 'Colonias', texto: etiquetaColonia(c), detalle: c.sector.nombre, icono: 'pin', elegir: () => onElegirColonia(c) });
    }
    if (!/^\d+$/.test(q)) {
      for (const c of calles.slice(0, 5)) {
        lista.push({ id: `calle-${c.calle}-${c.colonia}`, grupo: 'Calles con reportes', texto: c.calle, detalle: c.colonia, icono: 'road', elegir: () => onElegirCalle(c.calle) });
      }
    }
    return lista;
  }, [q, colonias, calles, onEnviar, onElegirColonia, onElegirCalle]);

  const visible = abierto && opciones.length > 0;
  const idOpcion = (i: number) => `${id}-opcion-${i}`;

  const elegir = (opcion: Opcion) => { setAbierto(false); setActiva(-1); opcion.elegir(); };
  const alTeclear = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setAbierto(true); setActiva((a) => (opciones.length ? (a + 1) % opciones.length : -1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setAbierto(true); setActiva((a) => (opciones.length ? (a <= 0 ? opciones.length - 1 : a - 1) : -1)); }
    else if (e.key === 'Escape') { setAbierto(false); setActiva(-1); }
    else if (e.key === 'Enter' && visible && activa >= 0) { e.preventDefault(); elegir(opciones[activa]); }
  };
  const enviar = (e: FormEvent) => { e.preventDefault(); setAbierto(false); setActiva(-1); onEnviar(); };

  const estado = q.length < 2 ? '' : opciones.length === 0 ? 'Sin sugerencias; pulsa Consultar para buscar.' : `${opciones.length} ${opciones.length === 1 ? 'sugerencia' : 'sugerencias'}. Usa las flechas para recorrerlas.`;
  let grupoAnterior = '';

  return (
    <form className="consulta-calle reveal reveal--3" role="search" onSubmit={enviar}>
      <label htmlFor={`${id}-campo`}>¿Por qué calle vas a circular?</label>
      <div className="consulta-calle__caja">
        <div className="consulta-calle__campo">
          <Icon name="search" size={20} />
          <input
            id={`${id}-campo`} role="combobox" aria-expanded={visible} aria-controls={`${id}-lista`} aria-autocomplete="list"
            aria-activedescendant={visible && activa >= 0 ? idOpcion(activa) : undefined} aria-describedby={`${id}-ayuda ${id}-estado`}
            placeholder="Calle, colonia, C.P. o folio" value={valor} autoComplete="off"
            onChange={(e) => { onCambiar(e.target.value); setAbierto(true); setActiva(-1); }}
            onFocus={() => setAbierto(true)} onBlur={() => setAbierto(false)} onKeyDown={alTeclear}
          />
          <button className="button" type="submit">Consultar</button>
        </div>
        <ul id={`${id}-lista`} role="listbox" aria-label="Sugerencias de búsqueda" className="sugerencias" hidden={!visible}>
          {opciones.map((o, i) => {
            const encabezado = o.grupo !== grupoAnterior ? o.grupo : null;
            grupoAnterior = o.grupo;
            return (
              <li key={o.id} id={idOpcion(i)} role="option" aria-selected={i === activa} className={`sugerencia${i === activa ? ' is-activa' : ''}`}
                onMouseDown={(e) => e.preventDefault()} onClick={() => elegir(o)} onMouseEnter={() => setActiva(i)}>
                {encabezado && <span className="sugerencia__grupo" aria-hidden="true">{encabezado}</span>}
                <span className="sugerencia__fila"><Icon name={o.icono} size={16} /><span className="sugerencia__texto">{o.texto}</span><span className="sugerencia__detalle">{o.detalle}</span></span>
              </li>
            );
          })}
        </ul>
      </div>
      <p id={`${id}-ayuda`} className="consulta-calle__ayuda">Escribe una calle (3 letras o más), una colonia, un código postal o el folio completo.</p>
      <p id={`${id}-estado`} className="visually-hidden" role="status">{estado}</p>
    </form>
  );
}
